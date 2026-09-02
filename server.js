const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// ─── the chat link ───────────────────────────────────────────────────────────
//
// WHY THIS IS A REDIRECT AND NOT A wa.me LINK ON THE PAGE.
//
// A `wa.me/<number>` link printed on the site, or baked into a QR code, embeds
// the number. The moment the number changes, every link and every printed code
// already in the world points at a dead account, and there is no way to reach
// the people holding them. Owning the redirect means the published address is
// always igiftaid.org/chat and only this one hop moves.
//
// It also keeps the number off the page entirely, so it is not scraped into the
// spam lists that harvest tel: links and visible digits.
//
// Set WHATSAPP_NUMBER in Railway to switch: digits only, country code first, no
// "+" and no spaces — that is the format wa.me expects. Changing it is an env
// var edit and a restart, not a deploy.
const WHATSAPP_NUMBER = (process.env.WHATSAPP_NUMBER || '447821863240').replace(/\D/g, '');

// 302, NOT 301. Browsers cache a 301 indefinitely, so anyone who followed the
// link before a number change would keep resolving to the old account with no
// way for us to correct it. The whole point of this route is that it can move.
app.get('/chat', (_req, res) => {
  res.redirect(302, `https://wa.me/${WHATSAPP_NUMBER}`);
});

// ─── the Daily Needs Wall's timestamps ───────────────────────────────────────
//
// The mock notes carry absolute `posted` and `expires` times and a note lives for
// 24 hours, so a file generated yesterday leaves an almost-empty wall today — it
// had 18 notes and showed 3. Regenerating the file only resets that clock; it does
// not stop it.
//
// So the window slides at serve time. Every timestamp is shifted by the age of the
// file, which preserves the SPREAD the generator built — some notes nearly fresh,
// some close to expiry, which is the whole point of the "expiring soonest" default
// — while anchoring it to now. The file on disk stays the fixture; only what is
// served moves.
//
// This is mock data. When real needs arrive from the bot this route goes away and
// the timestamps are whatever the family's message actually carried.
const fs = require('fs');
const NEEDS_JSON = path.join(__dirname, 'public', 'data', 'needs.json');

app.get('/data/needs.json', (_req, res) => {
  let doc;
  try {
    doc = JSON.parse(fs.readFileSync(NEEDS_JSON, 'utf8'));
  } catch (e) {
    return res.status(500).json({ items: [] });
  }
  const gen = Date.parse(doc.generated);
  const shift = Number.isFinite(gen) ? Date.now() - gen : 0;
  if (shift > 0) {
    const move = (iso) => new Date(Date.parse(iso) + shift).toISOString().replace(/\.\d{3}Z$/, 'Z');
    doc.generated = move(doc.generated);
    doc.items = (doc.items || []).map((n) => ({ ...n, posted: move(n.posted), expires: move(n.expires) }));
  }
  // No caching: the whole point is that the answer depends on when you asked.
  res.setHeader('Cache-Control', 'no-store');
  res.json(doc);
});

app.use(express.static(path.join(__dirname, 'public'), {
  maxAge: '60s',
  setHeaders: (res, filePath) => {
    if (filePath.endsWith('.html') || filePath.endsWith('.css') || filePath.endsWith('.png')) {
      res.setHeader('Cache-Control', 'no-cache');
    }
  },
}));

// Catch-all: any unmatched path serves the homepage with a 200 rather than a
// 404. Worth knowing when testing — a typo'd or deleted page looks fine to
// curl, so check the CONTENT of a page, not just its status code.
app.get('*', (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`iGiftAid site running on http://localhost:${PORT}`);
  console.log(`  /chat → https://wa.me/${WHATSAPP_NUMBER}`);
});
