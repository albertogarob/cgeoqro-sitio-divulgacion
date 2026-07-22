// @ts-check
import { defineConfig } from 'astro/config';

import mdx from '@astrojs/mdx';

// Lanzamiento inicial en GitHub Pages: build 100% estático, sin SSR/API routes.
// TODO: reemplazar `site` y `base` con la URL real una vez creado el repositorio en GitHub.
// - Si es un "project site" (github.com/<org>/<repo>): site = 'https://<org>.github.io', base = '/<repo>'
// - Si es un "user/org site" (repo nombrado <org>.github.io): site = 'https://<org>.github.io', base = '/'
export default defineConfig({
  site: 'https://centrogeo-qro.github.io',
  base: '/cgeoqro-sitio-divulgacion',
  output: 'static',

  // GitHub Pages sirve /ruta/index.html; evita 404 por slash faltante
  trailingSlash: 'always',

  integrations: [mdx()]
});