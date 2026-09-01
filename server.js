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
