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
  // El número va fijo a propósito, y es la lección del 29 de octubre de 2026: ese día
  // se borraron cuatro entrevistas por una lectura equivocada de una nota, y la suite
  // se quedó en verde porque solo exigía que hubiera alguna. Si publicas una nueva,
  // sube este número a mano; si baja sin querer, la prueba lo dice.
  assert.equal(entrevistas.length, 5,
    `hay ${entrevistas.length} entrevistas y se esperaban 5: ${entrevistas.map((e) => e.archivo).join(', ')}`);
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

test('el gancho de cada tarjeta es la primera frase entera de la respuesta', () => {
  // Esto comprueba el CONTENIDO contra la función, no la función: la rama de recorte
  // con puntos suspensivos vive en tests/texto.test.mjs, con textos hechos a propósito,
  // porque ninguna respuesta de verdad llega hoy al tope y aquí nunca se ejecutaría.
  for (const { archivo, datos } of entrevistas) {
    const respuesta = datos.preguntas[0].respuesta.replace(/\s+/g, ' ').trim();
    const gancho = primeraFrase(respuesta);
    assert.ok(gancho.length > 20, `el gancho de ${archivo} se queda en "${gancho}"`);
    // Sale de la RESPUESTA, no de la pregunta: las tres preguntas son las mismas en
    // todas las entrevistas y no distinguirían una tarjeta de otra.
    assert.ok(respuesta.startsWith(gancho),
      `el gancho de ${archivo} no es el principio de su respuesta: "${gancho}"`);
    // Y es una frase entera, con su cierre, no media frase cortada.
    assert.match(gancho, /[.!?…]$/, `el gancho de ${archivo} acaba a medias: "${gancho}"`);
    // Si la respuesta tiene más de una frase, el gancho tiene que haberla cortado: una
    // respuesta entera en la tarjeta desborda la tarjeta.
    if (respuesta.length > gancho.length) {
      assert.ok(gancho.length < respuesta.length,
        `el gancho de ${archivo} se trae la respuesta entera`);
    }
    // Y cabe en la tarjeta. El tope real de hoy es 139 caracteres; se deja en 150, que
    // es el que aplica la propia función, para que crecer un texto se note aquí.
    assert.ok(gancho.length <= 150, `el gancho de ${archivo} mide ${gancho.length}`);
  }
});
