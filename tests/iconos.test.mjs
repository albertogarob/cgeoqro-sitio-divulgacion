// Pruebas de los iconos de los botones de compartir. Lo que vigilan es que ninguna red
// se quede sin logotipo: el componente pinta un botón por cada red que devuelve
// `enlacesCompartir`, y si la clave de esa red no tiene icono, lo que se publica es un
// botón mudo. Eso no se nota al mirar el código, se nota al mirar la página.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { atributosIcono, iconos, icono, CAJA_ICONO } from '../src/lib/iconos.ts';
import { enlacesCompartir } from '../src/lib/compartir.ts';

const componente = readFileSync(new URL('../src/components/CompartirCapsula.astro', import.meta.url), 'utf8');
const redes = enlacesCompartir({ url: 'https://ejemplo.mx/c/', titulo: 'Título', resumen: 'Resumen' });

test('cada red de compartir tiene su icono', () => {
  assert.ok(redes.length >= 4, `solo salieron ${redes.length} redes`);
  for (const r of redes) {
    assert.doesNotThrow(() => icono(r.red), `la red "${r.red}" no tiene icono`);
  }
});

test('los dos botones que no son de ninguna marca se pintan con trazo', () => {
  // Copiar el enlace y la hoja de compartir del teléfono son dibujos de contorno: con
  // relleno saldrían como una mancha. Se comprueba por los atributos que de verdad se
  // pintan, no por la bandera: la bandera solo vale lo que valga quien la lee.
  for (const clave of ['copiar', 'nativo']) {
    const attrs = atributosIcono(clave);
    assert.equal(attrs.fill, 'none', `"${clave}" saldría relleno`);
    assert.equal(attrs.stroke, 'currentColor', `"${clave}" no tiene con qué dibujar el contorno`);
    assert.ok(attrs['stroke-width'], `"${clave}" no declara el grosor del trazo`);
  }
});

test('los logotipos se pintan con relleno y no con trazo', () => {
  // Un logotipo de marca dibujado con trazo sale hueco y desfigurado: el trazado es
  // la silueta, no el contorno.
  for (const r of redes) {
    const attrs = atributosIcono(r.red);
    assert.equal(attrs.fill, 'currentColor', `el logotipo de "${r.red}" no se rellena`);
    assert.equal(attrs.stroke, undefined, `el logotipo de "${r.red}" saldría contorneado`);
  }
});

test('el componente deja que la bandera decida, en vez de escribirlo a mano', () => {
  // Escrito a mano botón por botón, la bandera `trazo` no protegía de nada: se podía
  // añadir una red de contorno, marcarla, y seguir saliendo rellena. Para que la
  // bandera mande, el marcado no puede traer ni un `fill` ni un `stroke` propios.
  const sueltos = componente.match(/\s(fill|stroke|stroke-width)="/g) ?? [];
  assert.deepEqual(sueltos, [],
    'el componente escribe el relleno o el trazo a mano, así que la bandera no manda');
  const porBandera = componente.match(/\{\.\.\.atributosIcono\(/g) ?? [];
  assert.equal(porBandera.length, 3, `${porBandera.length} iconos piden sus atributos, esperaba 3`);
});

test('ningún trazado está vacío ni trae caracteres que no sean de un trazado', () => {
  for (const [clave, ic] of Object.entries(iconos)) {
    assert.match(ic.d, /^M/, `el trazado de "${clave}" no empieza con un movimiento`);
    assert.ok(ic.d.length > 40, `el trazado de "${clave}" es sospechosamente corto`);
    assert.doesNotMatch(ic.d, /[^MmLlHhVvCcSsQqTtAaZz0-9.,\-\s]/,
      `el trazado de "${clave}" trae algo que no es un comando ni un número`);
  }
});

test('pedir un icono que no existe falla diciendo dónde se arregla', () => {
  assert.throws(() => icono('mastodon'), /src\/lib\/iconos\.ts/);
});

test('el componente de compartir pinta un icono en cada botón', () => {
  // Las redes salen de un bucle, así que basta con que el bucle pida el icono de la
  // red que está pintando; los otros dos botones van escritos uno a uno.
  assert.match(componente, /icono\(r\.red\)\.d/, 'los botones de red no piden su icono');
  assert.match(componente, /icono\('copiar'\)\.d/, 'el botón de copiar no pide su icono');
  assert.match(componente, /icono\('nativo'\)\.d/, 'el botón de compartir no pide su icono');
  // Y todos en la misma caja, o unos saldrían el doble de grandes que otros.
  const cajas = componente.match(/viewBox=\{CAJA_ICONO\}/g) ?? [];
  assert.equal(cajas.length, 3, `hay ${cajas.length} iconos con la caja común, esperaba 3`);
  assert.equal(CAJA_ICONO, '0 0 24 24');
});
