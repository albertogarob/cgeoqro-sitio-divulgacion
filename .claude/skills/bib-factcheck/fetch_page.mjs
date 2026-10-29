#!/usr/bin/env node
/*
 * fetch_page.mjs, ayudante de descarga con Chromium sin ventana para el skill bib-factcheck.
 *
 * Last-resort retrieval when WebSearch/WebFetch are blocked, paywalled, or JS-gated
 * (IEEE Xplore, ACM DL, Springer, ScienceDirect, …). Spawns a hidden Chromium via
 * Playwright, loads the URL, and prints the page's bibliographic <meta> tags plus the
 * visible text to stdout. It only READS pages; it never edits REF.bib or infers anything.
 *
 * Usage:  node fetch_page.mjs "<url>" [maxChars]
 * If Chromium is missing:  npx playwright install chromium
 */
import { chromium } from 'playwright';

const url = process.argv[2];
const maxChars = parseInt(process.argv[3] || '20000', 10);
if (!url) {
  console.error('usage: node fetch_page.mjs "<url>" [maxChars]');
  process.exit(2);
}

const browser = await chromium.launch({ headless: true });
try {
  const ctx = await browser.newContext({
    userAgent:
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
  });
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
  // Let citation meta + late-rendered content settle.
  await page.waitForTimeout(2500);

  // High-signal bibliographic metadata first (Highwire / Dublin Core / OpenGraph).
  const meta = await page.evaluate(() => {
    const wanted = (n) =>
      /^(citation_|dc\.|DC\.|prism\.|og:|article:)/i.test(n);
    const out = {};
    for (const m of document.querySelectorAll('meta[name], meta[property]')) {
      const n = m.getAttribute('name') || m.getAttribute('property') || '';
      if (wanted(n)) {
        const v = (m.getAttribute('content') || '').trim();
        if (v) (out[n] ??= []).push(v);
      }
    }
    return out;
  });

  const title = await page.title();
  const bodyText = await page.evaluate(() => document.body?.innerText || '');

  console.log('URL: ' + url);
  console.log('TITLE: ' + title);
  console.log('--- BIBLIOGRAPHIC META ---');
  console.log(JSON.stringify(meta, null, 2));
  console.log('--- PAGE TEXT (truncated) ---');
  console.log(bodyText.replace(/\n{3,}/g, '\n\n').slice(0, maxChars));
} catch (err) {
  console.error('fetch_page error: ' + (err && err.message ? err.message : err));
  process.exitCode = 1;
} finally {
  await browser.close();
}
