#!/usr/bin/env python3
"""
Translate the site copy, once per string, cached against a hash of the English.

WHY HASH-CACHED AND NOT JUST "TRANSLATE THE FILES"
The failure mode of a multilingual site is not bad translation, it is STALE
translation: someone edits an English sentence, ships it, and ten other languages
quietly keep saying the old thing. Nobody notices because nobody on the team reads
Korean.

So every cache entry stores a hash of the English it was translated from. Change the
English by one character and the hash changes, the entry is invalidated, and the next
build retranslates it. A translation can never outlive its source. This is the same
discipline as whatsapp-bot/translations.js, which caches the intake questions the
same way and for the same reason.

    python3 translate.py            # fill any gaps
    python3 translate.py --force    # retranslate everything
    python3 translate.py --lang ar  # one language

Needs ANTHROPIC_API_KEY. Reads it from the environment, or from
../../whatsapp-bot/.env if that is where it lives.
"""
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(HERE, "i18n")
SRC = os.path.join(I18N, "en.json")

MODEL = "claude-sonnet-4-6"
BATCH = 8           # blocks per request. Was 14; German and Russian expand ~25% over
                    # English and truncated the JSON mid-object at that size.

# The 11 target languages. RTL ones are marked because the layout has to mirror,
# not just the text swap.
LANGS = {
    "ar": ("Arabic", True),
    "ur": ("Urdu", True),
    "fr": ("French", False),
    "es": ("Spanish", False),
    "de": ("German", False),
    "it": ("Italian", False),
    "tr": ("Turkish", False),
    "ru": ("Russian", False),
    "ko": ("Korean", False),
    "id": ("Indonesian", False),
    "ms": ("Malay", False),
}

SYSTEM = """You translate website copy for a charity that funds families in Gaza and the West Bank.

The reader is a potential donor. The English is deliberately plain, direct and \
unsentimental — it does not use charity-appeal language, it does not exaggerate, and \
in several places it deliberately states what the charity does NOT do or cannot \
promise. Preserve that register exactly. Do not warm it up, do not add emotive \
language, and do not soften a limitation into a promise.

RULES
1. Return ONLY a JSON object mapping the same keys to translated strings. No prose \
around it, no markdown fence.
2. PRESERVE ALL HTML TAGS exactly as they appear, including attributes. Translate only \
the visible text between them. `<a href="/trust.html">check us</a>` keeps its href.
3. PRESERVE HTML ENTITIES (&mdash; &amp; &rarr; &middot; &nbsp;) as entities.
4. Do NOT translate: proper nouns (HEART Humanitarian Foundation, I Gift Aid, Chuffed, \
GoFundMe, WhatsApp, PayPal, Stripe, Pennsylvania, Gaza, the West Bank, IRS), the EIN \
42-2670441, registration numbers, or email addresses and URLs.
5. "501(c)(3)" is a US tax code reference. Keep it as-is; if your language needs a gloss, \
add one in that language after it, do not replace it.
6. Currency stays in US dollars with the $ sign.
7. Where the English is a short UI label (a button, a filter chip, a dropdown option), \
keep the translation short enough to fit the same control."""


def api_key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    env = os.path.join(os.path.dirname(os.path.dirname(HERE)), "whatsapp-bot", ".env")
    if os.path.exists(env):
        for line in open(env):
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ANTHROPIC_API_KEY not set and not found in whatsapp-bot/.env")


def h12(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def call(key, payload, lang_name):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 16000,
        "system": SYSTEM,
        "messages": [{
            "role": "user",
            "content": f"Translate every value into {lang_name}.\n\n"
                       + json.dumps(payload, ensure_ascii=False, indent=1),
        }],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read())
            text = "".join(b.get("text", "") for b in data.get("content", []))
            text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
            return json.loads(text)
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
            if attempt == 3:
                # Do NOT raise. One bad batch used to abort the entire run and take
                # every remaining language with it. Return nothing: the strings stay
                # uncached, the summary reports them, and the next run picks them up
                # because the hash still will not match.
                print(f"      GAVE UP on this batch: {type(e).__name__}")
                return {}
            print(f"      retry {attempt + 1} after {type(e).__name__}")
    return {}


def run(only=None, force=False):
    src = json.load(open(SRC, encoding="utf-8"))
    key = api_key()
    print(f"source: {len(src)} blocks\n")

    for code, (name, rtl) in LANGS.items():
        if only and code != only:
            continue
        path = os.path.join(I18N, f"{code}.json")
        cache = {} if force else (json.load(open(path, encoding="utf-8"))
                                  if os.path.exists(path) else {})

        # A stale entry is one whose stored hash no longer matches the English.
        todo = {k: v for k, v in src.items()
                if cache.get(k, {}).get("h") != h12(v)}
        # Entries whose English key has been deleted should not linger.
        for gone in [k for k in cache if k not in src]:
            del cache[gone]

        if not todo:
            print(f"  {code} {name:12s} up to date ({len(cache)} strings)")
            continue

        print(f"  {code} {name:12s} translating {len(todo)} of {len(src)}"
              f"{' (RTL)' if rtl else ''}")
        items = list(todo.items())
        for i in range(0, len(items), BATCH):
            chunk = dict(items[i:i + BATCH])
            got = call(key, chunk, name)
            if not got and len(chunk) > 1:
                # The batch failed to parse. Retry each string alone: a one-key
                # response is far less likely to break, and it isolates whichever
                # string is the problem instead of losing the whole batch.
                print(f"      batch failed, retrying {len(chunk)} strings individually")
                got = {}
                for k, v in chunk.items():
                    one = call(key, {k: v}, name)
                    if k in one:
                        got[k] = one[k]
                    else:
                        print(f"        still failing: {k}")
            for k, en in chunk.items():
                if k in got and isinstance(got[k], str) and got[k].strip():
                    cache[k] = {"t": got[k].strip(), "h": h12(en)}
            print(f"      {min(i + BATCH, len(items))}/{len(items)}")

        missing = [k for k in src if k not in cache]
        if missing:
            print(f"      WARNING: {len(missing)} strings came back empty: {missing[:3]}")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"      wrote {path}")


def report():
    src = json.load(open(SRC, encoding="utf-8"))
    print("\n── coverage ──")
    for code, (name, rtl) in LANGS.items():
        path = os.path.join(I18N, f"{code}.json")
        if not os.path.exists(path):
            print(f"  {code} {name:12s} NOT TRANSLATED")
            continue
        c = json.load(open(path, encoding="utf-8"))
        ok = sum(1 for k, v in src.items() if c.get(k, {}).get("h") == h12(v))
        flag = "" if ok == len(src) else f"  <-- {len(src) - ok} missing or stale"
        print(f"  {code} {name:12s} {ok}/{len(src)}{' RTL' if rtl else ''}{flag}")


if __name__ == "__main__":
    args = sys.argv[1:]
    only = args[args.index("--lang") + 1] if "--lang" in args else None
    run(only=only, force="--force" in args)
    report()
