// Pruebas del mensaje que resalta a distancia.
//
// El sitio queda escuchando mensajes de cualquiera que lo meta en un iframe, así que
// lo que acepta tiene que estar acotado: una clave exacta, un selector que sea cadena
// y con tope de largo, y nada más. Lo que no encaje se ignora sin hacer nada.
import test from 'node:test';
import assert from 'node:assert/strict';
import { peticionDeResaltado, TIPO_RESALTAR, MAX_SELECTOR } from '../src/lib/visita.ts';

test('un mensaje bien formado dice qué resaltar', () => {
  assert.deepEqual(
    peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: '.cap-grid' }),
    { selector: '.cap-grid', acercar: false },
  );
  assert.deepEqual(
    peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: '.turnos', acercar: true }),
    { selector: '.turnos', acercar: true },
  );
});

test('el selector vacío apaga el resaltado, y eso no es ignorar el mensaje', () => {
  // Son dos cosas distintas: `{selector: ''}` se atiende apagando; `null` de vuelta
  // significa que el mensaje no iba con nosotros y no se toca nada.
  for (const vacio of ['', null, undefined]) {
    assert.deepEqual(peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: vacio }),
      { selector: '', acercar: false }, `con ${String(vacio)}`);
  }
});

test('cualquier mensaje que no sea el nuestro se ignora', () => {
  const ajenos = [
    null, undefined, 'hola', 42, [],
    {},
    { tipo: 'otra-cosa', selector: '.cap-grid' },
    { tipo: TIPO_RESALTAR.toUpperCase(), selector: '.cap-grid' },
    { selector: '.cap-grid' },
  ];
  for (const m of ajenos) {
    assert.equal(peticionDeResaltado(m), null, `debería ignorar ${JSON.stringify(m)}`);
  }
});

test('un selector que no sea cadena, o que sea enorme, se ignora', () => {
  // Es un oyente abierto: lo que acepta tiene que estar acotado.
  for (const malo of [42, true, {}, [], () => {}]) {
    assert.equal(peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: malo }), null);
  }
  const enorme = '.x'.repeat(MAX_SELECTOR);
  assert.ok(enorme.length > MAX_SELECTOR);
  assert.equal(peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: enorme }), null);
  // Y justo en el tope sí pasa.
  const alJusto = '.' + 'a'.repeat(MAX_SELECTOR - 1);
  assert.equal(alJusto.length, MAX_SELECTOR);
  assert.deepEqual(peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: alJusto }),
    { selector: alJusto, acercar: false });
});

test('el selector se recorta de espacios, y uno de puro espacio se ignora', () => {
  assert.deepEqual(peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: '  .cruce  ' }),
    { selector: '.cruce', acercar: false });
  assert.equal(peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: '   ' }), null);
});

test('acercar solo es cierto si viene exactamente true', () => {
  // Para que un "1" o un "sí" no acaben moviendo la página del recorrido, que tiene
  // su propio motor de scroll y se pelearía con él.
  for (const casi of [1, 'true', 'sí', {}]) {
    assert.equal(peticionDeResaltado({ tipo: TIPO_RESALTAR, selector: '.x', acercar: casi }).acercar,
      false, `con ${JSON.stringify(casi)}`);
  }
});
