> ## ⚠ NOT ON RAILWAY ANY MORE — moved to the VPS on 2026-09-13
>
> This served from Railway behind Cloudflare, which is why it did not look like
> Railway from outside. It was the last public thing on infrastructure belonging to
> the account HEART is being separated from, and a Railway tidy-up could have taken
> the public site dark with the cause looking like DNS.
>
> **Nothing runs now.** Caddy on the VPS serves `public/` directly — no Node, no
> container. `server.js` is kept because it is still the readable statement of what
> the site does, and the Caddy block reproduces its three behaviours deliberately:
> `/chat` as a **302** (not 301, so the published address can move), **410** on the
> four withdrawn paths, and the homepage with **200** for anything unknown.
>
> **To deploy:** build, then `rsync -a --delete public/ heartbeat:/srv/igiftaid/www-igiftaid/`
> and `ssh heartbeat 'chown -R caddy:caddy /srv/igiftaid/www-igiftaid'`.
> Pushing to `main` no longer publishes anything.
>
> Two other things in this file are stale: it calls the site "coming-soon" (it is
> five pages, now three) and says copy lives in `public/index.html`. **Edit `src/`** —
> the English pages at `public/` root are generated too, and a direct edit there is
> silently reverted by the next build.

# iGiftAid coming-soon site

Static single-page site served by a tiny Express app. Deployed on Railway, fronted by `igiftaid.org` (Namecheap DNS). `.com` and `.net` 301-redirect to `.org`.

## Local

```
npm install
npm start
# http://localhost:3000
```

## Deploy

Railway auto-builds via Nixpacks on push. Start command: `node server.js`. Listens on `process.env.PORT`.

## Edit

- Copy / structure: `public/index.html`
- Styles + brand tokens: `public/styles.css` (colors at `:root`)
- Logo: `public/logo.png` · Favicon: `public/favicon.png`

Brand source: `~/Downloads/iGiftAid – Brand Identity Guide.pdf`.
