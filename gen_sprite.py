#!/usr/bin/env python3
"""Generate the Needs Wall illustration sprite.

Programmatic on purpose: 21 hand-authored SVGs drift in stroke weight and
composition, and the whole point is that they read as one set.

Register note: the motifs are TATREEZ (Palestinian cross-stitch) geometry — the
eight-pointed star, cypress, diamond lattice. Deliberately NOT the key, keffiyeh
or map. Those are the strongest Palestinian symbols and also the most political;
on a note about a gas cylinder they shift the register from "here is a thing you
can buy for a family" to "here is a cause", which is exactly what this page's
prose works to avoid.
"""
import math
OBJECTS = {
 "medical": [
   '<path d="M42 22h16v10h10v16H58v10H42V48H32V32h10z"/>',
   '<rect x="38" y="20" width="24" height="12" rx="2"/><path d="M42 32v26a8 8 0 0016 0V32"/><path d="M44 44h12"/>',
   '<path d="M34 20v14a16 16 0 0032 0V20"/><path d="M50 50v8a10 10 0 0020 0v-4"/><circle cx="70" cy="52" r="5"/>',
 ],
 "education": [
   '<path d="M26 34l24-10 24 10-24 10z"/><path d="M36 40v14c0 4 28 4 28 0V40"/>',
   '<path d="M28 26h18a6 6 0 016 6v28a6 6 0 00-6-6H28z"/><path d="M72 26H54a6 6 0 00-6 6v28a6 6 0 016-6h18z"/>',
   '<rect x="32" y="30" width="36" height="28" rx="4"/><path d="M42 30v-6h16v6"/><path d="M32 42h36"/>',
 ],
 "shelter": [
   '<path d="M50 20L24 44h8v22h36V44h8z"/><path d="M44 66V52h12v14"/>',
   '<path d="M50 24L28 68h44z"/><path d="M50 24v44"/><path d="M50 48q7 10 7 20"/><path d="M50 48q-7 10-7 20"/><path d="M28 68l-8 6M72 68l8 6"/>',
   '<path d="M22 40q28-16 56 0"/><path d="M22 40v24h56V40"/><path d="M36 64V50h12v14"/>',
 ],
 "food": [
   '<path d="M30 42h40v8a20 20 0 01-40 0z"/><path d="M26 42h48"/><path d="M30 50h-6a4 4 0 000 8h6M70 50h6a4 4 0 010 8h-6"/><path d="M50 34v8"/>',
   '<rect x="38" y="26" width="24" height="40" rx="10"/><path d="M46 26v-6h8v6"/><path d="M38 42h24"/>',
   '<path d="M38 30q12-8 24 0l6 36H32z"/><path d="M38 30q6 6 12 0t12 0"/><path d="M40 48h20"/>',
 ],
 "infant": [
   '<path d="M42 22h16v8H42z"/><path d="M40 30h20v28a10 10 0 01-20 0z"/><path d="M46 12v10"/>',
   '<path d="M40 26h20l10 8-6 8-4-3v25H40V39l-4 3-6-8z"/><path d="M44 64v-8h12v8"/>',
   '<circle cx="50" cy="46" r="16"/><circle cx="34" cy="28" r="8"/><circle cx="66" cy="28" r="8"/><path d="M44 44h.01M56 44h.01"/><path d="M45 54q5 4 10 0"/>',
 ],
 "winter": [
   '<path d="M38 24h24l6 14-8 4v22H40V42l-8-4z"/>',
   '<path d="M38 24h18v30h10a8 8 0 018 8v6H38z"/><path d="M38 34h18"/><path d="M38 62h36"/>',
   '<path d="M50 18v20M50 62v20M32 30l36 40M68 30L32 70"/><path d="M28 50h44"/>',
 ],
 "emergency": [
   '<path d="M50 18l30 52H20z"/><path d="M50 38v16M50 60v4"/>',
   '<path d="M36 30h28v8H36z"/><path d="M40 38v24h20V38"/><path d="M50 44v12M44 50h12"/>',
   '<rect x="24" y="34" width="52" height="32" rx="3"/><circle cx="50" cy="50" r="8"/><path d="M32 42h.01M68 58h.01"/>',
 ],
}

def band(v):
    o = []
    if v == 1:
        # qoub, the eight-pointed star. Drawn from an explicit point list — the
        # hand-written relative path this replaced rendered as teardrops.
        for cx in range(12, 100, 19):
            cy, R, r = 87, 7.0, 2.9
            pts = []
            for k in range(16):
                a = math.pi * k / 8 - math.pi / 2
                rad = R if k % 2 == 0 else r
                pts.append(f"{cx + rad*math.cos(a):.1f} {cy + rad*math.sin(a):.1f}")
            o.append('<path d="M' + 'L'.join(pts) + 'z"/>')
    elif v == 2:
        for x in range(6, 100, 15):
            o.append(f'<path d="M{x} 90l5-8 5 8z"/><path d="M{x+2} 96l3-5 3 5z"/>')
    else:
        for x in range(8, 100, 17):
            o.append(f'<path d="M{x} 86l5-5 5 5-5 5z"/>')
    return "".join(o)

# The three bands are defined ONCE and referenced, not repeated into 21 symbols —
# that alone was 60% of the sprite.
defs = "".join(f'<g id="tz{v}" fill="var(--illu-soft)">{band(v)}</g>' for v in (1, 2, 3))
sym = []
for chip, variants in OBJECTS.items():
    for i, obj in enumerate(variants, 1):
        sym.append(
          f'<symbol id="illu-{chip}-{i}" viewBox="0 0 100 100">'
          f'<use href="#tz{i}"/>'
          f'<g fill="none" stroke="currentColor" stroke-width="3.4" '
          f'stroke-linecap="round" stroke-linejoin="round">{obj}</g></symbol>')

print('<svg class="illu-sprite" width="0" height="0" aria-hidden="true" focusable="false" '
      'style="position:absolute"><defs>' + defs + '</defs>' + "".join(sym) + '</svg>')
