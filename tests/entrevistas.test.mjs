// Pruebas del contenido de las entrevistas.
//
// Hubo cuatro entrevistas de muestra, redactadas por el equipo de divulgación y
// marcadas como borrador en el sitio. Se retiraron el 29 de octubre de 2026: la idea
// de publicar borradores para que el investigador los revise en línea pide un servidor
// con pantallas de edición y soporte a usuarios, y este sitio es estático. Se publica
// lo que el investigador ya dijo, y nada más.
//
// Esta prueba es lo que impide que vuelvan a colarse sin querer.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import yaml from 'js-yaml';
import { primeraFrase } from '../src/lib/texto.ts';

const dir = new URL('../src/content/entrevistas/', import.meta.url);
const leer = (ruta) => readFileSync(new URL('../' + ruta, import.meta.url), 'utf8');

const entrevistas = readdirSync(dir).filter((f) => f.endsWith('.mdx')).map((f) => ({
  archivo: f,
  datos: yaml.load(readFileSync(new URL(f, dir), 'utf8').split('---')[1]),
}));

test('se leyeron las entrevistas del repositorio', () => {
  assert.ok(entrevistas.length >= 1, 'no hay ninguna entrevista');
  for (const { archivo, datos } of entrevistas) {
    assert.ok(datos?.investigador, `${archivo} no declara investigador`);
    assert.equal(datos.preguntas?.length, 3, `${archivo} no trae tres preguntas`);
  }
});

test('ninguna entrevista se publica como borrador', () => {
  // Publicar un texto que el investigador no ha dicho, aunque vaya marcado, obliga a
  // un circuito de revisión que un sitio estático no tiene.
  for (const { archivo, datos } of entrevistas) {
    assert.equal(datos.esEjemplo, undefined,
      `${archivo} se marca como borrador: o se graba de verdad, o no se publica`);
  }
  // Y ninguna vista puede volver a leer esa marca.
  for (const vista of ['src/pages/entrevistas/index.astro',
                       'src/pages/entrevistas/[id].astro',
                       'src/pages/investigadores/[id].astro',
                       'src/content.config.ts']) {
    assert.doesNotMatch(leer(vista), /esEjemplo/, `${vista} todavía mira la marca de borrador`);
  }
});

test('el gancho de cada tarjeta cabe y no parte palabras', () => {
  // Las tarjetas del índice llaman a `primeraFrase` sin tope, así que es esa rama la
  // que hay que comprobar contra los textos de verdad.
  for (const { archivo, datos } of entrevistas) {
    const gancho = primeraFrase(datos.preguntas[0].respuesta);
    assert.ok(gancho.length > 20, `el gancho de ${archivo} se queda en "${gancho}"`);
    assert.ok(gancho.length <= 150, `el gancho de ${archivo} mide ${gancho.length}`);
    if (gancho.endsWith('…')) {
      const texto = gancho.slice(0, -1);
      assert.equal(datos.preguntas[0].respuesta.replace(/\s+/g, ' ').trim()[texto.length], ' ',
        `el gancho de ${archivo} parte una palabra por la mitad`);
    }
  }
});
