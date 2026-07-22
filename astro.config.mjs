// @ts-check
import { defineConfig } from 'astro/config';

import mdx from '@astrojs/mdx';

// Lanzamiento inicial en GitHub Pages: build 100% estático, sin SSR/API routes.
// Repo: https://github.com/albertogarob/cgeoqro-sitio-divulgacion (privado).
// NOTA: GitHub Pages en repos privados de cuentas personales requiere plan
// GitHub Pro/Team/Enterprise. Con plan gratuito, hacer el repo público antes de
// que el workflow de deploy.yml pueda publicar el sitio.
export default defineConfig({
  site: 'https://albertogarob.github.io',
  base: '/cgeoqro-sitio-divulgacion',
  output: 'static',

  // GitHub Pages sirve /ruta/index.html; evita 404 por slash faltante
  trailingSlash: 'always',

  integrations: [mdx()]
});