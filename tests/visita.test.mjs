// Pruebas del mensaje que resalta a distancia.
//
// El sitio queda escuchando mensajes de cualquiera que lo meta en un iframe, así que
// lo que acepta tiene que estar acotado: una clave exacta, un selector que sea cadena
// y con tope de largo, y nada más. Lo que no encaje se ignora sin hacer nada.
import test from 'node:test';
import assert from 'node:assert/strict';
import { peticionDeResaltado, hayQueAcercarse, desplazamientoDeseado, caminoDePenumbra,
         rectangulosDePenumbra, TIPO_RESALTAR, MAX_SELECTOR } from '../src/lib/visita.ts';

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

// ── La penumbra ──
//
// Dos averías vigila esto, y las dos se vieron en pantalla antes de existir la prueba.
// La primera: con una sombra enorme por contorno, cada contorno oscurecía a los demás,
// así que un punto que señalaba cuatro tarjetas las dejaba las cuatro apagadas. La
// segunda, al arreglar la primera con un rectángulo y agujeros recortados: dos huecos
// que se solapan, o uno dentro de otro, se CANCELAN con la regla par e impar, y la
// zona común volvía a quedarse oscura con el contorno rojo alrededor.
//
// Por eso lo que se mide aquí no es la forma del camino: es qué puntos de la pantalla
// quedan oscuros. Es la propiedad que le importa a quien mira la proyección.

const VENTANA = [1000, 800];

/** Si el punto (x, y) queda bajo la penumbra. */
function oscuro(trozos, x, y) {
  return trozos.some((r) => r.x0 <= x && x < r.x1 && r.y0 <= y && y < r.y1);
}

/** El área total que oscurece, para comprobar que no se pisa a sí misma. */
function area(trozos) {
  return trozos.reduce((a, r) => a + (r.x1 - r.x0) * (r.y1 - r.y0), 0);
}

/** Que ningún par de trozos se solape: si se pisaran, la zona común saldría doble. */
function seSolapan(trozos) {
  for (let i = 0; i < trozos.length; i++) {
    for (let j = i + 1; j < trozos.length; j++) {
      const a = trozos[i];
      const b = trozos[j];
      if (a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1) return true;
    }
  }
  return false;
}

test('las cuatro tarjetas señaladas quedan claras, y el resto oscuro', () => {
  const cuatro = [
    { top: 10, left: 10, width: 100, height: 50 },
    { top: 10, left: 200, width: 100, height: 50 },
    { top: 100, left: 10, width: 100, height: 50 },
    { top: 100, left: 200, width: 100, height: 50 },
  ];
  const trozos = rectangulosDePenumbra(cuatro, ...VENTANA);
  for (const h of cuatro) {
    assert.ok(!oscuro(trozos, h.left + h.width / 2, h.top + h.height / 2),
      `la tarjeta de (${h.left}, ${h.top}) salió apagada`);
  }
  assert.ok(oscuro(trozos, 600, 400), 'el resto de la página tiene que quedar en penumbra');
  assert.ok(oscuro(trozos, 150, 35), 'el espacio entre dos tarjetas también');
  assert.ok(!seSolapan(trozos), 'dos trozos de penumbra se pisan');
  assert.equal(area(trozos), 1000 * 800 - 4 * 100 * 50);
});

test('un hueco DENTRO de otro no se cancela, que es como volvía la avería', () => {
  // El caso: un selector que casa con un contenedor y con algo de dentro.
  const trozos = rectangulosDePenumbra([
    { top: 40, left: 40, width: 300, height: 200 },
    { top: 80, left: 80, width: 120, height: 60 },
  ], 800, 600);
  assert.ok(!oscuro(trozos, 140, 110), 'el hueco de dentro salió oscuro');
  assert.ok(!oscuro(trozos, 300, 60), 'el hueco de fuera salió oscuro');
  assert.ok(oscuro(trozos, 500, 400), 'lo de fuera tiene que estar en penumbra');
  assert.equal(area(trozos), 800 * 600 - 300 * 200, 'el hueco de dentro no añade área');
});

test('dos huecos que se solapan tampoco se cancelan en la zona común', () => {
  const trozos = rectangulosDePenumbra([
    { top: 320, left: 40, width: 200, height: 150 },
    { top: 400, left: 140, width: 200, height: 150 },
  ], 800, 600);
  assert.ok(!oscuro(trozos, 190, 430), 'el solape de los dos salió oscuro');
  assert.ok(!oscuro(trozos, 80, 350), 'el primero solo salió oscuro');
  assert.ok(!oscuro(trozos, 300, 520), 'el segundo solo salió oscuro');
  assert.ok(oscuro(trozos, 600, 100));
  // Dos rectángulos de 200x150 que se pisan en 100x70.
  assert.equal(area(trozos), 800 * 600 - (2 * 200 * 150 - 100 * 70));
});

test('un hueco inútil EN MEDIO no se lleva por delante a los que vienen detrás', () => {
  // La primera tarjeta entra por el borde de arriba y queda en medio píxel, así que se
  // descarta. Las otras tres tienen que abrirse igual: si el bucle se cortara en la
  // primera en vez de saltársela, saldrían apagadas y nadie se enteraría.
  const trozos = rectangulosDePenumbra([
    { top: -49.5, left: 10, width: 100, height: 50 },
    { top: 10, left: 200, width: 100, height: 50 },
    { top: 100, left: 10, width: 100, height: 50 },
    { top: 100, left: 200, width: 100, height: 50 },
  ], ...VENTANA);
  assert.ok(!oscuro(trozos, 250, 35), 'la segunda tarjeta salió apagada');
  assert.ok(!oscuro(trozos, 60, 125), 'la tercera tarjeta salió apagada');
  assert.ok(!oscuro(trozos, 250, 125), 'la cuarta tarjeta salió apagada');
  assert.ok(oscuro(trozos, 60, 0.2), 'la primera no llegaba a un píxel: va en penumbra');
  assert.equal(area(trozos), 1000 * 800 - 3 * 100 * 50);
});

test('el umbral está en un píxel, y se clava por los dos lados', () => {
  // Justo por encima SÍ se abre: un subrayado o una barra fina son cosas que se señalan.
  const fino = rectangulosDePenumbra([{ top: 300, left: 100, width: 220, height: 1 }], ...VENTANA);
  assert.ok(!oscuro(fino, 200, 300.5), 'una barra de un píxel tiene que abrir su hueco');
  assert.equal(area(fino), 1000 * 800 - 220 * 1);
  const medio = rectangulosDePenumbra([{ top: 300, left: 100, width: 220, height: 1.5 }], ...VENTANA);
  assert.equal(area(medio), 1000 * 800 - 220 * 1.5);
  // Justo por debajo NO: un subcamino degenerado no abre nada y ensucia el camino.
  const cero = rectangulosDePenumbra([{ top: 300, left: 100, width: 220, height: 0.9 }], ...VENTANA);
  assert.deepEqual(cero, [], `no debería oscurecer nada: ${JSON.stringify(cero)}`);
});

test('el camino escribe los trozos, y sin trozos no hay camino ni capa', () => {
  assert.equal(
    caminoDePenumbra([{ top: 20, left: 30, width: 100, height: 40 }], 1000, 800),
    'M0 0 H1000 V20 H0 Z M0 20 H30 V60 H0 Z M130 20 H1000 V60 H130 Z M0 60 H1000 V800 H0 Z');
  // Dos huecos en la misma franja, que es donde se nota que las celdas se funden.
  assert.equal(
    caminoDePenumbra([{ top: 20, left: 30, width: 100, height: 40 },
                      { top: 20, left: 300, width: 100, height: 40 }], 1000, 800),
    'M0 0 H1000 V20 H0 Z M0 20 H30 V60 H0 Z M130 20 H300 V60 H130 Z M400 20 H1000 V60 H400 Z'
    + ' M0 60 H1000 V800 H0 Z');
  // Cadena vacía quiere decir que no se pinta capa ninguna.
  assert.equal(caminoDePenumbra([], ...VENTANA), '');
  assert.equal(caminoDePenumbra([{ top: 10, left: 10, width: 100, height: 50 }], 0, 800), '');
  assert.equal(caminoDePenumbra([{ top: 10, left: 10, width: 100, height: 50 }], 1000, 0), '');
});

test('una ventana o un hueco sin número no sacan un camino con NaN dentro', () => {
  // Si se colara, el navegador descarta el recorte entero y la capa taparía la pantalla.
  for (const camino of [
    caminoDePenumbra([{ top: 10, left: 10, width: 100, height: 50 }], NaN, 800),
    caminoDePenumbra([{ top: 10, left: 10, width: 100, height: 50 }], 1000, undefined),
    caminoDePenumbra([{ top: NaN, left: 10, width: 100, height: 50 }], ...VENTANA),
    caminoDePenumbra([{ top: 10, left: 10, width: NaN, height: 50 }], ...VENTANA),
  ]) {
    assert.doesNotMatch(camino, /NaN|undefined|Infinity/, `camino sucio: ${camino}`);
  }
});

test('un hueco de anchura o altura negativa se ignora', () => {
  assert.deepEqual(rectangulosDePenumbra([{ top: 100, left: 100, width: -50, height: 50 }], ...VENTANA), []);
  assert.deepEqual(rectangulosDePenumbra([{ top: 100, left: 100, width: 50, height: -50 }], ...VENTANA), []);
});

test('un hueco que se sale de la ventana se recorta a la ventana, por los cuatro lados', () => {
  // Por arriba y por la izquierda.
  const alto = rectangulosDePenumbra([{ top: -30, left: -40, width: 200, height: 100 }], 1000, 800);
  assert.equal(area(alto), 1000 * 800 - 160 * 70, 'el hueco no puede contar lo que cae fuera');
  assert.ok(!oscuro(alto, 10, 10));
  assert.ok(oscuro(alto, 200, 10));
  // Por abajo y por la derecha: un elemento a medio salir por el pie de la ventana, que
  // es lo que pasa cuando se resalta algo en el borde del scroll.
  const bajo = rectangulosDePenumbra([{ top: 760, left: 900, width: 300, height: 300 }], 1000, 800);
  assert.equal(area(bajo), 1000 * 800 - 100 * 40, 'el hueco se cuela por debajo de la ventana');
  assert.ok(!oscuro(bajo, 950, 780));
  assert.ok(oscuro(bajo, 850, 780), 'a la izquierda del hueco sigue habiendo penumbra');
  // Y uno que cae entero fuera no abre nada.
  assert.deepEqual(rectangulosDePenumbra([{ top: 900, left: 20, width: 100, height: 50 }], 1000, 800), []);
});

test('las coordenadas se redondean a un decimal, para no escribir un camino kilométrico', () => {
  const camino = caminoDePenumbra([{ top: 20.666, left: 30.333, width: 100.5, height: 40.25 }], 1000, 800);
  // Los cuatro filos del hueco, que es donde la penumbra se detiene.
  for (const filo of ['V20.7', 'H30.3', 'H130.8', 'V60.9']) {
    assert.ok(camino.includes(filo), `falta el filo ${filo} en ${camino}`);
  }
  assert.doesNotMatch(camino, /\d\.\d\d/, 'quedó más de un decimal');
});

// ── Acercarse sin quedar detrás de la cabecera pegada ──
//
// El sitio lleva una barra de navegación pegada arriba. Centrar lo resaltado en la
// ventana lo dejaba justo detrás de ella cuando el elemento está cerca del principio
// de la página y no queda scroll de sobra. Por eso las dos cuentas reciben el `techo`,
// que es lo que esa barra tapa.

test('lo que queda detrás de la cabecera cuenta como no visible', () => {
  // Una caja entera dentro de los primeros 90 píxeles, que es donde está la barra.
  const tapada = { top: 20, bottom: 70, height: 50 };
  assert.equal(hayQueAcercarse(tapada, 800, 0.55, 0), false, 'sin techo se da por vista');
  assert.equal(hayQueAcercarse(tapada, 800, 0.55, 90), true, 'con techo hay que moverla');
  // Y una que empieza justo debajo de la barra sigue contando como vista.
  assert.equal(hayQueAcercarse({ top: 100, bottom: 150, height: 50 }, 800, 0.55, 90), false);
});

test('el desplazamiento deja lo resaltado en medio de lo que de verdad se ve', () => {
  // Banda útil de 90 a 800, o sea 710 de alto; una caja de 110 queda centrada con
  // 300 por arriba, así que su top debe acabar en 90 + 300 = 390.
  const caja = { top: 500, bottom: 610, height: 110 };
  assert.equal(desplazamientoDeseado(caja, 800, 90), 110);
  // Sin techo, la misma caja se centra en la ventana entera: top en 345.
  assert.equal(desplazamientoDeseado(caja, 800, 0), 155);
  // Hacia arriba también: una caja por encima del pliegue devuelve negativo.
  assert.equal(desplazamientoDeseado({ top: -200, bottom: -90, height: 110 }, 800, 90), -590);
});

test('una caja más alta que la banda se pega al techo en vez de centrarse', () => {
  // Si no cabe, no hay hueco que repartir: lo mejor es enseñar su principio.
  assert.equal(desplazamientoDeseado({ top: 300, bottom: 1500, height: 1200 }, 800, 90), 210);
  assert.equal(desplazamientoDeseado({ top: 90, bottom: 1290, height: 1200 }, 800, 90), 0);
});

test('sin banda útil no se mueve nada', () => {
  // Una cabecera que se comiera la ventana entera no puede mandar a ningún sitio.
  assert.equal(desplazamientoDeseado({ top: 10, bottom: 60, height: 50 }, 800, 800), 0);
  assert.equal(desplazamientoDeseado({ top: 10, bottom: 60, height: 50 }, 800, 900), 0);
  assert.equal(hayQueAcercarse({ top: 10, bottom: 60, height: 50 }, 800, 0.55, 800), false);
});
