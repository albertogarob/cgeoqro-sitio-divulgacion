// Pruebas del mensaje que resalta a distancia.
//
// El sitio queda escuchando mensajes de cualquiera que lo meta en un iframe, así que
// lo que acepta tiene que estar acotado: una clave exacta, un selector que sea cadena
// y con tope de largo, y nada más. Lo que no encaje se ignora sin hacer nada.
import test from 'node:test';
import assert from 'node:assert/strict';
import { peticionDeResaltado, hayQueAcercarse, caminoDePenumbra, cuentaDeHuecos,
         TIPO_RESALTAR, MAX_SELECTOR } from '../src/lib/visita.ts';

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

test('no se acerca a lo que ya se está viendo', () => {
  const alto = 700;
  // Un bloque de 200 px, entero dentro de la ventana.
  assert.equal(hayQueAcercarse({ top: 100, bottom: 300, height: 200 }, alto), false);
  // Pegado al borde de arriba, pero entero.
  assert.equal(hayQueAcercarse({ top: 0, bottom: 200, height: 200 }, alto), false);
});

test('se acerca a lo que está fuera de la pantalla', () => {
  const alto = 700;
  assert.equal(hayQueAcercarse({ top: 900, bottom: 1100, height: 200 }, alto), true, 'más abajo');
  assert.equal(hayQueAcercarse({ top: -400, bottom: -200, height: 200 }, alto), true, 'más arriba');
  // Y a lo que asoma apenas: visible 20 de 200, un 10 %.
  assert.equal(hayQueAcercarse({ top: 680, bottom: 880, height: 200 }, alto), true);
});

test('un bloque más alto que la ventana se mide contra la ventana, no contra sí mismo', () => {
  // Es el caso de la rejilla de cápsulas: nunca cabe entera, y exigirlo haría que la
  // página se moviera siempre.
  const alto = 700;
  // Llena la ventana de arriba abajo: se está viendo todo lo que se puede ver.
  assert.equal(hayQueAcercarse({ top: -300, bottom: 1200, height: 1500 }, alto), false);
  // Y si solo asoma su borde, sí hay que acercarse.
  assert.equal(hayQueAcercarse({ top: 620, bottom: 2120, height: 1500 }, alto), true);
});

test('una caja sin alto, o una ventana sin alto, no mueven nada', () => {
  assert.equal(hayQueAcercarse({ top: 0, bottom: 0, height: 0 }, 700), false);
  assert.equal(hayQueAcercarse({ top: 10, bottom: 50, height: 40 }, 0), false);
});

// ── La penumbra, que es una sola capa con agujeros ──
//
// El fallo que estas pruebas vigilan: con una sombra enorme por caja, cada caja
// oscurecía todo lo de fuera de ella, incluidas las otras cajas, así que un selector
// que casaba con cuatro tarjetas las dejaba las cuatro tan apagadas como el resto.

const VENTANA = [1000, 800];

test('cada cosa resaltada abre su propio agujero, y las cuatro a la vez', () => {
  const cuatro = [
    { top: 10, left: 10, width: 100, height: 50 },
    { top: 10, left: 200, width: 100, height: 50 },
    { top: 100, left: 10, width: 100, height: 50 },
    { top: 100, left: 200, width: 100, height: 50 },
  ];
  assert.equal(cuentaDeHuecos(caminoDePenumbra(cuatro, ...VENTANA)), 4);
  assert.equal(cuentaDeHuecos(caminoDePenumbra(cuatro.slice(0, 1), ...VENTANA)), 1);
});

test('el camino abre la ventana entera y después recorta', () => {
  const camino = caminoDePenumbra([{ top: 20, left: 30, width: 100, height: 40 }], 1000, 800);
  assert.equal(camino, 'M0 0 H1000 V800 H0 Z M30 20 H130 V60 H30 Z');
});

test('un agujero que se sale de la ventana se recorta a la ventana', () => {
  // La caja de un elemento a medio entrar por abajo, o medio salido por arriba: el
  // agujero no puede pedir coordenadas de fuera, que el recorte las ignora y deja la
  // penumbra entera.
  const camino = caminoDePenumbra([{ top: -30, left: -40, width: 200, height: 100 }], 1000, 800);
  assert.equal(camino, 'M0 0 H1000 V800 H0 Z M0 0 H160 V70 H0 Z');
  const abajo = caminoDePenumbra([{ top: 760, left: 900, width: 300, height: 300 }], 1000, 800);
  assert.equal(abajo, 'M0 0 H1000 V800 H0 Z M900 760 H1000 V800 H900 Z');
});

test('un agujero que la ventana deja en menos de un píxel no se dibuja', () => {
  // Pedir un subcamino degenerado no abre nada y además ensucia el camino.
  const camino = caminoDePenumbra([{ top: 799.5, left: 10, width: 100, height: 50 }], 1000, 800);
  assert.equal(cuentaDeHuecos(camino), 0, `no debería abrir agujero: ${camino}`);
  assert.equal(cuentaDeHuecos(caminoDePenumbra([{ top: 10, left: 10, width: 0.4, height: 50 }], 1000, 800)), 0);
});

test('sin ventana no hay camino, y sin camino no hay agujeros', () => {
  assert.equal(caminoDePenumbra([{ top: 10, left: 10, width: 100, height: 50 }], 0, 800), '');
  assert.equal(caminoDePenumbra([{ top: 10, left: 10, width: 100, height: 50 }], 1000, 0), '');
  assert.equal(caminoDePenumbra([], ...VENTANA), 'M0 0 H1000 V800 H0 Z');
  assert.equal(cuentaDeHuecos(''), 0);
  assert.equal(cuentaDeHuecos(caminoDePenumbra([], ...VENTANA)), 0);
});

test('las coordenadas se redondean a un decimal, para no escribir un camino kilométrico', () => {
  const camino = caminoDePenumbra([{ top: 20.666, left: 30.333, width: 100.5, height: 40.25 }], 1000, 800);
  assert.equal(camino, 'M0 0 H1000 V800 H0 Z M30.3 20.7 H130.8 V60.9 H30.3 Z');
  assert.doesNotMatch(camino, /\d\.\d\d/, 'quedó más de un decimal');
});
