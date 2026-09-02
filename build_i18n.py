#!/usr/bin/env python3
"""
Render the donor-facing pages in every translated language.

HOW IT WORKS, AND WHY THIS WAY
The English pages are the source of truth and are edited by hand. This does a
SUBSTITUTION pass over them rather than rebuilding them from a catalogue: it re-runs
the exact block regex that translate.py's extractor used, and swaps each block's text
for its translation. Because the matching logic is identical, a block that was
extracted is a block that gets replaced — the two cannot drift apart.

The alternative, rebuilding pages from string keys, means every markup change has to
be made in a template instead of in the page, and the English file stops being the
thing you can just open and read.

    python3 build_i18n.py

Output: public/<lang>/{index,campaigns,needs,how-it-works,trust}.html
English stays at the root.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, "public")
# ⚠ SOURCE AND OUTPUT ARE SEPARATE DIRECTORIES, and must stay that way.
#
# The English pages used to live in public/ and be written back over themselves. Two
# things went wrong: open(...,"w") truncated each file before render() could read it,
# destroying all five; and once that was fixed, every run re-injected the hreflang
# block, the switcher and the hint banner, so they doubled on each build.
#
# public/{privacy,terms,data-deletion}.html are NOT here — they are generated from the
# HEART site by crypto-payout-system/heart-site/build_igiftaid.py and are not translated.
SRC = os.path.join(HERE, "src")
I18N = os.path.join(HERE, "i18n")

# THE ONE definition. extract.py imports it from here rather than keeping its own
# copy, because it already diverged once: `option` was added to the extractor and not
# to this, so every dropdown silently stayed English while everything around it
# translated. Two copies of a regex that must agree is two copies too many.
BLOCK = re.compile(r'<(h1|h2|h3|p|li|button|label|option)(\s[^>]*)?>(.*?)</\1>', re.S)
NAVLINK = re.compile(r'(<a class="navlink"[^>]*>)([^<]+)</a>')

PAGES = ["index.html", "campaigns.html", "needs.html", "how-it-works.html", "trust.html"]

# Legal pages are deliberately NOT translated — a mistranslated liability clause is
# worse than an English one, and two versions of a policy raise the question of which
# governs. Links to them always point at the English root.
UNTRANSLATED = {"privacy.html", "terms.html", "data-deletion.html"}

LANGS = {
    "en": ("English", "English", False),
    "ar": ("Arabic", "العربية", True),
    "ur": ("Urdu", "اردو", True),
    "fr": ("French", "Français", False),
    "es": ("Spanish", "Español", False),
    "de": ("German", "Deutsch", False),
    "it": ("Italian", "Italiano", False),
    "tr": ("Turkish", "Türkçe", False),
    "ru": ("Russian", "Русский", False),
    "ko": ("Korean", "한국어", False),
    "id": ("Indonesian", "Bahasa Indonesia", False),
    "ms": ("Malay", "Bahasa Melayu", False),
}

SITE = "https://www.igiftaid.org"


def switcher(cur):
    """Rendered into every page. A plain <details> so it works with JavaScript off —
    the whole site is static and there is no reason for the language picker to be the
    one thing that needs a script to open."""
    mark = ' aria-current="true"'
    items = "".join(
        f'<a href="{path_for(code, "index.html")}" hreflang="{code}" lang="{code}"'
        f'{mark if code == cur else ""}>{native}</a>'
        for code, (_, native, _) in LANGS.items())
    label = LANGS[cur][1]
    return (f'<details class="lang-wrap"><summary class="lang-btn" '
            f'aria-label="Change language">&#127760; {label}</summary>'
            f'<div class="lang-menu">{items}</div></details>')


def path_for(code, page):
    """URL for a page in a language. English lives at the root, not /en/, because it
    is the canonical version and moving it would break every link already shared."""
    if page in UNTRANSLATED:
        return "/" + page
    return f"/{page}" if code == "en" else f"/{code}/{page}"


def alternates(page):
    """hreflang tells a search engine these are the same page in different languages
    rather than duplicate content. x-default points at English."""
    out = [f'<link rel="alternate" hreflang="x-default" href="{SITE}/{page}">']
    for code in LANGS:
        out.append(f'<link rel="alternate" hreflang="{code}" '
                   f'href="{SITE}{path_for(code, page)}">')
    return "\n  ".join(out)


HINT = '''<div class="lang-hint" id="langHint" hidden>
  <span id="langHintText"></span>
  <button type="button" id="langHintNo">No thanks</button>
</div>
<script>
(function () {
  // SUGGEST, never redirect. Auto-redirecting on browser language breaks a shared
  // link: someone in Germany sending an Arabic reader a campaign URL should not have
  // it forced into German. So this offers, once, and remembers being dismissed.
  var LANGS = %s, HERE = '%s';
  var NATIVE = %s, OFFER = %s;
  try {
    if (localStorage.getItem('iga_lang_set')) return;
  } catch (e) { return; }
  var want = null;
  (navigator.languages || [navigator.language || '']).some(function (l) {
    var c = String(l).slice(0, 2).toLowerCase();
    if (LANGS.indexOf(c) !== -1) { want = c; return true; }
    return false;
  });
  if (!want || want === HERE) return;
  var bar = document.getElementById('langHint');
  document.getElementById('langHintText').innerHTML =
    OFFER[want] + ' <a href="' + (want === 'en' ? '/' : '/' + want + '/') +
    '" onclick="try{localStorage.setItem(\\'iga_lang_set\\',\\'1\\')}catch(e){}">' +
    NATIVE[want] + '</a>';
  bar.hidden = false;
  document.getElementById('langHintNo').addEventListener('click', function () {
    try { localStorage.setItem('iga_lang_set', '1'); } catch (e) {}
    bar.hidden = true;
  });
  // An explicit pick from the switcher is remembered too, so the offer stops.
  document.querySelectorAll('.lang-menu a').forEach(function (a) {
    a.addEventListener('click', function () {
      try { localStorage.setItem('iga_lang_set', '1'); } catch (e) {}
    });
  });
})();
</script>'''

# "View this page in ..." pre-translated, because showing the offer in a language the
# reader does not speak defeats the point of the offer.
OFFER = {
    "en": "View this page in", "ar": "اعرض هذه الصفحة بـ", "ur": "یہ صفحہ دیکھیں",
    "fr": "Voir cette page en", "es": "Ver esta página en", "de": "Diese Seite ansehen auf",
    "it": "Vedi questa pagina in", "tr": "Bu sayfayı şu dilde görüntüle",
    "ru": "Посмотреть эту страницу на", "ko": "이 페이지를 다음 언어로 보기",
    "id": "Lihat halaman ini dalam", "ms": "Lihat halaman ini dalam",
}


def load(code):
    if code == "en":
        return {}
    p = os.path.join(I18N, f"{code}.json")
    if not os.path.exists(p):
        return None
    return {k: v["t"] for k, v in json.load(open(p, encoding="utf-8")).items()}


def render(page, code, src_en, trans):
    html = open(os.path.join(SRC, page), encoding="utf-8").read()
    _, native, rtl = LANGS[code]

    if code != "en":
        # Map English TEXT to translation, not key to position — a repeated string was
        # deduped during extraction and would otherwise only be replaced once.
        by_text = {src_en[k]: trans[k] for k in src_en if k in trans}
        head, sep, rest = html.partition("<main")
        body, sep2, tail = rest.partition("</main>")

        def sub(m):
            txt = re.sub(r"\s+", " ", m.group(3)).strip()
            if txt in by_text:
                return f"<{m.group(1)}{m.group(2) or ''}>{by_text[txt]}</{m.group(1)}>"
            return m.group(0)

        html = head + sep + BLOCK.sub(sub, body) + sep2 + tail

        # Nav labels live outside <main> and are <a>, not a BLOCK tag, so they need
        # their own pass — otherwise the menu stays in English on every page.
        def navsub(m):
            txt = m.group(2).strip()
            return f'{m.group(1)}{by_text.get(txt, txt)}</a>' if txt in by_text else m.group(0)
        html = NAVLINK.sub(navsub, html)

        # In-language navigation: a reader who switched to Arabic should stay in
        # Arabic when they click through. Legal pages are excluded above.
        for p in PAGES:
            html = html.replace(f'href="/{p}"', f'href="/{code}/{p}"')
        html = html.replace('href="/"', f'href="/{code}/"')
        # Assets are language-neutral and must not be prefixed.
        for a in ("styles.css", "logo.png", "favicon.png", "favicon-32.png", "data/"):
            html = html.replace(f'href="/{code}/{a}', f'href="/{a}').replace(
                f'src="/{code}/{a}', f'src="/{a}')

    rtl_attr = ' dir="rtl"' if rtl else ""
    html = html.replace('<html lang="en">', f'<html lang="{code}"{rtl_attr}>', 1)
    html = html.replace('<link rel="stylesheet"',
                        alternates(page) + '\n  <link rel="stylesheet"', 1)
    # The switcher goes at the end of the nav bar.
    html = html.replace("</div>\n</nav>", f"  {switcher(code)}\n  </div>\n</nav>", 1)
    # Runtime strings for the JS. Only the ui.* keys — no point shipping the prose
    # blocks twice, they are already substituted into the HTML.
    if code != "en":
        ui = {k: v for k, v in trans.items() if k.startswith("ui.")}
        if ui:
            html = html.replace(
                "</head>",
                "  <script>window.I18N=" + json.dumps(ui, ensure_ascii=False)
                + ";</script>\n</head>", 1)

    hint = HINT % (json.dumps(list(LANGS)), code, json.dumps(
        {c: n for c, (_, n, _) in LANGS.items()}, ensure_ascii=False),
        json.dumps(OFFER, ensure_ascii=False))
    html = html.replace("</body>", hint + "\n</body>", 1)
    return html


def main():
    src_en = json.load(open(os.path.join(I18N, "en.json"), encoding="utf-8"))
    made, skipped = 0, []
    for code in LANGS:
        trans = load(code)
        if trans is None:
            skipped.append(code)
            continue
        if code != "en":
            covered = sum(1 for k in src_en if k in trans)
            if covered < len(src_en):
                print(f"  {code}: only {covered}/{len(src_en)} strings — "
                      f"untranslated blocks will stay English")
        out = PUB if code == "en" else os.path.join(PUB, code)
        rendered = {page: render(page, code, src_en, trans) for page in PAGES}
        os.makedirs(out, exist_ok=True)
        for page, html in rendered.items():
            if not html.strip():
                sys.exit(f"ABORT: {code}/{page} rendered empty — refusing to write")
            with open(os.path.join(out, page), "w", encoding="utf-8") as fh:
                fh.write(html)
            made += 1
    print(f"\n  {made} pages across {len(LANGS) - len(skipped)} languages")
    if skipped:
        print(f"  not yet translated: {', '.join(skipped)} — run translate.py")


if __name__ == "__main__":
    main()
