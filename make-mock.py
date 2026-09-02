#!/usr/bin/env python3
"""
Regenerate the mock campaigns and needs that the site renders.

WHY A GENERATOR RATHER THAN CHECKED-IN JSON
The wall is built around time — a note expires 24 hours after it is posted, and the
default ordering is "expiring soonest". Hard-coded timestamps go stale within a day
and the demo then shows a board where everything expired last week, which is a worse
lie than showing nothing.

So the JSON carries ABSOLUTE ISO timestamps — exactly the shape real data will have,
so the client code does not have to change when it is wired up — and this script
rewrites them relative to now. Run it before showing the site to anyone.

    python3 make-mock.py

WHAT IS MOCK AND WHAT IS NOT
The names are invented and the situations are composites. The need CATEGORIES are
not invented: each maps to a field the intake bot already collects (see
whatsapp-bot/questions.js), so when this is wired to real applications the chips
already mean something.
"""
import json
import os
import random
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "public", "data")

# Seeded so a rebuild does not reshuffle everything and make the diff unreadable.
# The FRONT END still randomises campaign order per visit — that is the fair-exposure
# rule and it is deliberately not baked into the data.
random.seed(1857)

NOW = datetime.now(timezone.utc)


def iso(dt):
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ── the seven chips ──────────────────────────────────────────────────────────
# Each traceable to an intake field rather than invented:
#   medical   → health          education → schooling      shelter → rent
#   food      → food_fuel       infant    → infant_needs
#   winter    → seasonal, currently captured in free text
#   emergency → the urgent case that does not fit the others
CHIPS = ["medical", "education", "shelter", "food", "infant", "winter", "emergency"]

NEEDS = [
    ("Aisha",  "Baby formula and nappies for one month",                 45, "infant"),
    ("Mahmoud","Insulin and test strips, four weeks",                    60, "medical"),
    ("Rana",   "School bags and books for three children",               38, "education"),
    ("Yousef", "Tarpaulin and rope to close the roof before the rain",   55, "shelter"),
    ("Layla",  "Flour, oil and lentils for a family of seven",           50, "food"),
    ("Ibrahim","Blankets and two winter coats for the children",         64, "winter"),
    ("Nour",   "Antibiotics for a chest infection, and the clinic fare", 32, "medical"),
    ("Samir",  "Cooking gas cylinder refill",                            28, "food"),
    ("Hiba",   "Replacement glasses so Adam can see the board at school",42, "education"),
    ("Khalil", "One month of rent arrears to avoid eviction",           100, "shelter"),
    ("Maryam", "Infant paracetamol and a thermometer",                   18, "infant"),
    ("Tariq",  "Emergency stipend after the family's income stopped",    85, "emergency"),
    ("Dalia",  "Warm sleeping mats for two elderly parents",             58, "winter"),
    ("Omar",   "Wound dressings and antiseptic for a healing burn",      36, "medical"),
    ("Fatima", "Drinking water for two weeks",                           40, "food"),
    ("Zain",   "Exam fees so Lina can sit her final year",               75, "education"),
    ("Huda",   "Plastic sheeting to divide one room for privacy",        30, "shelter"),
    ("Bilal",  "Emergency stipend while waiting on a delayed transfer",  90, "emergency"),
    ("Sana",   "A fortnight of baby milk while her mother recovers",      52, "infant"),
    ("Adel",   "Two thermal blankets and a paraffin heater refill",       47, "winter"),
    ("Wafa",   "Bus fare to the hospital for six dialysis appointments",  34, "medical"),
    ("Jamil",  "Notebooks and pens for a class of thirty",                26, "education"),
    ("Rania",  "Rice, sugar and tinned fish to last the month",           44, "food"),
    ("Basel",  "Timber to prop a wall that shifted in the last strike",   68, "shelter"),
    ("Noor",   "Emergency fund after a lost identity card froze her aid", 72, "emergency"),
]

CAMPAIGNS = [
    ("The Haddad family", "Rebuilding after the strike on Nuseirat",
     ["shelter", "food"], 4200, 1180,
     "Eight people sharing two rooms since their building came down. They need materials to "
     "make it weatherproof before winter, and food while the father looks for work."),
    ("Amal and her four children", "Cancer treatment and the journey to reach it",
     ["medical"], 6500, 3900,
     "Amal's treatment is available, but the travel and the permits cost more than the "
     "treatment does. This covers both, and the months she cannot work."),
    ("The Zaqout family", "Keeping three children in school",
     ["education", "food"], 2800, 640,
     "All three were in school before. Fees, books and transport are what stand between "
     "them and going back."),
    ("Nadia's household", "A winter that has already started",
     ["winter", "shelter"], 3100, 2750,
     "Six people, one of them ninety-one. Heating, bedding and closing the gaps in the "
     "walls before the temperature drops further."),
    ("The Barghouti family", "Insulin, and a fridge to keep it in",
     ["medical", "emergency"], 1900, 210,
     "Two diabetic adults in a house with intermittent power. The cost is the medicine, "
     "and a way to store it safely."),
    ("Reem and her mother", "Rent arrears and a way back to steady ground",
     ["shelter", "emergency"], 2400, 1990,
     "Reem was the only earner until the workshop closed. They are four months behind and "
     "have been given notice."),
]


def build_needs():
    """Emits one entry per need.

    The `image` key is OPTIONAL and appears only where a photo actually exists. Its
    absence is meaningful: the client falls through to a generated illustration, so a
    need with no photograph is a normal state rather than a missing asset.

    Add one by giving a NEEDS row a 5th element:

        ("Aisha", "Baby formula ...", 45, "infant",
         {"kind": "need", "src": "/img/needs/need-1000.jpg",
          "alt": "Two tins of infant formula and a pack of nappies"})

    `kind` is "need" or "family". Prefer "need" — a photograph of the thing being
    funded carries the tangibility that drives giving, without publishing an
    identifiable person from an active conflict zone. Use "family" only where the
    family has offered it and is comfortable with it.

    `alt` is CONTENT, like `need` itself, and is not routed through the i18n
    catalogue — translating descriptions of photographs nobody has taken yet would
    cost 12 languages per image for no reader benefit.
    """
    out = []
    for i, row in enumerate(NEEDS):
        family, need, amount, chip = row[:4]
        image = row[4] if len(row) > 4 else None
        # Spread across the last 22 hours so the board always has a mix of fresh notes
        # and ones close to expiry — that spread is what the "expiring soonest" default
        # sort exists to surface.
        hours_ago = round(random.uniform(0.4, 22.0), 1)
        posted = NOW - timedelta(hours=hours_ago)
        out.append({
            "id": f"need-{1000 + i}",
            "family": family,
            "need": need,
            "amount": amount,
            "currency": "USD",
            "chip": chip,
            "posted": iso(posted),
            # One per household per 24 hours, so expiry is always posted + 24h.
            "expires": iso(posted + timedelta(hours=24)),
        })
        if image:
            out[-1]["image"] = image
    return out


def build_campaigns():
    out = []
    for i, (family, title, chips, goal, raised, summary) in enumerate(CAMPAIGNS):
        out.append({
            "id": f"camp-{200 + i}",
            "slug": title.lower().replace(",", "").replace("'", "").replace(" ", "-")[:48],
            "family": family,
            "title": title,
            "summary": summary,
            "chips": chips,
            "goalUsd": goal,
            "raisedUsd": raised,
            "url": "https://chuffed.org/",
            # Mirrors the vetting rung in whatsapp-bot/disclaimer.js. "identity" is the
            # rung actually operational today; "identity+sanctions" needs Sumsub, which
            # vettingCheck.js still marks as a sandbox build.
            "verification": "identity",
            "opened": iso(NOW - timedelta(days=random.randint(4, 40))),
        })
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, data in (("needs.json", build_needs()), ("campaigns.json", build_campaigns())):
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"generated": iso(NOW), "chips": CHIPS, "items": data}, fh, indent=2)
            fh.write("\n")
        print(f"  {name:16s} {len(data):2d} items")
    print(f"\nwritten to {OUT}")
