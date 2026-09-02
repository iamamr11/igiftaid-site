#!/usr/bin/env python3
"""
Pull the translatable copy out of src/*.html into i18n/en.json.

Imports BLOCK and NAVLINK from build_i18n rather than defining its own. They diverged
once — `option` was added here and not there, so every dropdown stayed English while
the text around it translated, silently and on all eleven languages at once.

    python3 extract.py
"""
import json
import os
import re

from build_i18n import BLOCK, NAVLINK, PAGES, SRC, I18N

# Strings the JavaScript builds at runtime. They never appear in the HTML, so nothing
# can extract them — they are declared here and translated like any other string.
UI = {
    "ui.chip.medical": "Medical", "ui.chip.education": "Education",
    "ui.chip.shelter": "Shelter", "ui.chip.food": "Food & Fuel",
    "ui.chip.infant": "Infant & Baby", "ui.chip.winter": "Winter",
    "ui.chip.emergency": "Emergency",
    "ui.expired": "expired",
    "ui.minsLeft": "{n} min left", "ui.hoursLeft": "{n}h left",
    "ui.needsOnWall.one": "{n} need on the wall",
    "ui.needsOnWall.other": "{n} needs on the wall",
    "ui.selected.one": "{n} need", "ui.selected.other": "{n} needs",
    "ui.clear": "Clear", "ui.fund": "Fund these",
    "ui.campaigns.one": "{n} campaign", "ui.campaigns.other": "{n} campaigns",
    "ui.raised": "${n} raised", "ui.ofGoal": "of ${n}",
    "ui.support": "Support this family", "ui.verified": "Identity verified",
    "ui.selectNote": "Select: {who}, {what}, ${amount}",
    "ui.turnOver": "Turn over",
    "ui.expiredKept": "Expired \u2014 still in your selection",
}


def main():
    out, seen = {}, set()

    nav = []
    for m in NAVLINK.finditer(open(os.path.join(SRC, "index.html"), encoding="utf-8").read()):
        t = m.group(2).strip()
        if t not in nav:
            nav.append(t)
    for i, t in enumerate(nav, 1):
        out[f"nav.{i:02d}"] = t

    for f in PAGES:
        h = open(os.path.join(SRC, f), encoding="utf-8").read()
        m = re.search(r"<main[^>]*>(.*?)</main>", h, re.S)
        body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", m.group(1) if m else "", flags=re.S)
        n = 0
        for mm in BLOCK.finditer(body):
            t = re.sub(r"\s+", " ", mm.group(3)).strip()
            if len(t) < 3 or t in seen or t in out.values():
                continue
            if re.fullmatch(r"[\d$.,\s&#;·—–-]*", t):
                continue
            if t.startswith("<") and t.endswith(">") and "</" not in t:
                continue
            seen.add(t)
            n += 1
            out[f"{f[:-5]}.{n:02d}"] = t
        print(f"  {f:20s} {n:3d} blocks")

    out.update(UI)
    with open(os.path.join(I18N, "en.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    words = sum(len(re.sub(r"<[^>]+>", " ", v).split()) for v in out.values())
    print(f"\n  {len(out)} keys, {words} words -> i18n/en.json")


if __name__ == "__main__":
    main()
