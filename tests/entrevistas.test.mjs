// Pruebas del contenido de las entrevistas.
//
// Cinco entrevistas publicadas, y ninguna lleva etiqueta de borrador. Hubo un campo
// `esEjemplo` que pintaba una chapa amarilla en la tarjeta, un aviso en el índice, otro
// en la ficha y otro en el perfil, y cambiaba la descripción que viaja a WhatsApp. Se
// retiró el 29 de octubre de 2026 por decisión de Alberto: la etiqueta era lo que
// sobraba, no los textos.
//
// Esta prueba es lo que impide que la etiqueta vuelva a colarse sin querer.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import yaml from 'js-yaml';
import { primeraFrase } from '../src/lib/texto.ts';

const dir = new URL('../src/content/entrevistas/', import.meta.url);
const leer = (ruta) => readFileSync(new URL('../' + ruta, import.meta.url), 'utf8');

const dirInv = new URL('../src/content/investigadores/', import.meta.url);
const investigadores = new Set(
  readdirSync(dirInv).filter((f) => f.endsWith('.md')).map((f) => f.replace(/\.md$/, ''))
);

const entrevistas = readdirSync(dir).filter((f) => f.endsWith('.mdx')).map((f) => ({
  archivo: f,
  datos: yaml.load(readFileSync(new URL(f, dir), 'utf8').split('---')[1]),
}));

test('cada entrevista apunta a un investigador que existe, y solo una por persona', () => {
  assert.ok(entrevistas.length >= 1, 'no hay ninguna entrevista');
  const vistos = new Set();
  for (const { archivo, datos } of entrevistas) {
    assert.ok(datos?.investigador, `${archivo} no declara investigador`);
    assert.equal(datos.preguntas?.length, 3, `${archivo} no trae tres preguntas`);
    // La referencia tiene que resolver a un archivo de la colección de investigadores:
    // si no, la página se construye sin nombre y sin foto.
    assert.ok(investigadores.has(datos.investigador),
      `${archivo} apunta a "${datos.investigador}", que no está en src/content/investigadores`);
    assert.ok(!vistos.has(datos.investigador),
      `hay dos entrevistas de ${datos.investigador}; el perfil las listaría las dos`);
    vistos.add(datos.investigador);
  }
});

test('ninguna entrevista lleva la etiqueta de borrador', () => {
  // La chapa amarilla se retiró, así que el campo que la encendía no puede volver a
  // aparecer en el contenido ni en las vistas.
  for (const { archivo, datos } of entrevistas) {
    assert.equal(datos.esEjemplo, undefined,
      `${archivo} trae la marca de borrador, que se retiró del sitio`);
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
