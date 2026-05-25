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
