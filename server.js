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
// ── Campaigns and the Daily Needs Wall are GONE, deliberately ───────────────
//
// Both pages rendered invented families as real. campaigns.html showed six of
// them — "The Haddad family", "Amal and her four children" — each tagged
// "verification": "identity", under the heading "Families we have verified",
// with Support buttons pointing at chuffed.org. The needs wall listed invented
// needs with amounts and a "Fund these" button whose handler was an alert saying
// checkout was not connected. Nothing on either page said it was illustrative,
// and the generator re-dated the notes on every request so the wall always looked
// freshly posted.
//
// That is fabricated beneficiaries presented as verified, on a charity's site,
// beneath donate-shaped buttons. They come back when there are real families to
// put on them, which is not before October.
//
// ⚠ 410, NOT THE CATCH-ALL. The catch-all below answers any unknown path with the
// homepage and a 200, so deleting the files alone would leave these URLs looking
// fine — and anything that indexed them keeps serving the old snippet. 410 Gone
// says the content existed and was withdrawn, which is both true and what a
// search engine needs to drop it.
for (const gone of ['/campaigns.html', '/needs.html', '/data/needs.json', '/data/campaigns.json']) {
  app.get(gone, (_req, res) => res.status(410).type('text/plain').send('Gone.'));
}

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
