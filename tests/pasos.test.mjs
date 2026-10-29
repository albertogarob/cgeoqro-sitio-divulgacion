// Pruebas de las cuentas de los mandos del recorrido. El salto cuadra la caja del paso
// con la ventana: así el texto del paso queda donde la hoja de estilos lo coloque, y de
// paso el borde del paso queda muy por encima de la línea de disparo de scrollama y el
// del paso siguiente por debajo, que es lo que hace que se active el paso pedido y no
// otro. Apuntar a la propia línea de disparo era el fallo: el paso contaba como activo
// con su texto todavía por debajo del pliegue.
import test from 'node:test';
import assert from 'node:assert/strict';
import { contarParadas, duracionPaso, duracionViaje, esParadaDeCierre, esUltimaParada, estadoMandos, fraccionAvance, objetivoCierre, objetivoScroll, paradaVisibleEn, pasoDeFraccion, pasoDestino, pasoVisibleEn, suavizado, ultimaParada } from '../src/scripts/pasos.ts';

test('anterior y siguiente no se salen del relato', () => {
  assert.equal(pasoDestino(0, 14, -1), 0);
  assert.equal(pasoDestino(13, 14, 1), 13);
  assert.equal(pasoDestino(5, 14, 1), 6);
  assert.equal(pasoDestino(5, 14, -1), 4);
  assert.equal(pasoDestino(0, 1, 1), 0);
  assert.equal(pasoDestino(0, 0, 1), 0);
});

test('el salto activa el paso pedido y no el siguiente', () => {
  // Pasos de una pantalla de alto, como los pinta la hoja de estilos.
  const innerHeight = 900;
  const alto = innerHeight;
  const top = (i) => 1200 + i * alto;

  // Los dos umbrales que usan los recorridos de verdad.
  for (const offset of [0.72, 0.75]) {
    const linea = innerHeight * offset;
    for (const i of [1, 2, 7]) {
      const y = objetivoScroll({ topAbs: top(i) });
      // El paso pedido tiene que haber cruzado la línea de disparo DE VERDAD: quedarse
      // justo encima es el caso frontera, y no basta con un "<=".
      const margen = linea - (top(i) - y);
      assert.ok(margen > 0, `el paso ${i} se queda en la línea de disparo (margen ${margen})`);
      // El siguiente no la ha cruzado, que si no se vería el paso equivocado.
      assert.ok(top(i + 1) - y > linea, `el salto al paso ${i} se pasa al siguiente`);
      // Y el anterior se quedó atrás, para que scrollama lo dé por salido.
      assert.ok(top(i - 1) - y < linea, `el paso ${i} no deja atrás al anterior`);
    }
  }
});

test('el salto cuadra la caja del paso con la pantalla', () => {
  // Esto es lo que se rompió y nadie veía: apuntando a la línea de disparo, el paso ya
  // contaba como activo pero su caja quedaba casi entera por debajo del pliegue, así
  // que el salto cambiaba el gráfico y dejaba la pantalla sin texto que leer.
  //
  // Lo que se exige aquí es la condición que lo impide y que esta función sí decide:
  // que la caja del paso quede cuadrada con la ventana. Dónde cae exactamente el
  // subtítulo DENTRO de esa caja lo manda la hoja de estilos, no esta función, y se
  // comprueba en navegador, no aquí: una constante de maqueta copiada a mano en este
  // fichero seguiría en verde el día que el CSS cambiara.
  const innerHeight = 900;
  const alto = innerHeight;
  const top = (i) => 1200 + i * alto;

  for (const i of [0, 1, 5, 9]) {
    const y = objetivoScroll({ topAbs: top(i) });
    const arribaDeLaCaja = top(i) - y;
    const abajoDeLaCaja = arribaDeLaCaja + alto;
    assert.equal(arribaDeLaCaja, 0, `la caja del paso ${i} no empieza en el borde de la pantalla`);
    assert.ok(abajoDeLaCaja >= innerHeight, `la caja del paso ${i} no llena la pantalla`);
  }
});

test('el salto nunca pide un scroll negativo ni más del que existe', () => {
  assert.equal(objetivoScroll({ topAbs: -100 }), 0);
  assert.equal(objetivoScroll({ topAbs: 99999, maxScroll: 5000 }), 5000);
  // Y cuando cabe de sobra, el tope no toca el valor calculado.
  assert.equal(
    objetivoScroll({ topAbs: 3000, maxScroll: 50000 }),
    3000
  );
});

test('la duración crece con el texto a un ritmo fijado, no solo entre topes', () => {
  // El valor concreto de la zona lineal queda clavado: si no, un ritmo de lectura diez
  // veces más lento dejaría una frase de tres palabras doce segundos en pantalla sin
  // que ninguna prueba se quejara.
  assert.equal(duracionPaso('palabra '.repeat(10)), 800 + 10 * 210);
  assert.equal(duracionPaso('palabra '.repeat(20)), 800 + 20 * 210);
  const corto = duracionPaso('palabra '.repeat(10));
  const largo = duracionPaso('palabra '.repeat(20));
  assert.ok(largo > corto, 'el paso largo debe durar más');
});

test('el ritmo de la reproducción es de lectura en pantalla, no de dictado', () => {
  // Un recorrido entero duraba casi tres minutos y se hacía eterno. Esto clava el
  // ritmo por arriba y por abajo: ni un dictado ni una ráfaga ilegible.
  const porPalabra = duracionPaso('palabra '.repeat(21)) - duracionPaso('palabra '.repeat(20));
  const palabrasPorMinuto = 60000 / porPalabra;
  assert.ok(palabrasPorMinuto > 240, `${Math.round(palabrasPorMinuto)} palabras por minuto se lee despacio`);
  assert.ok(palabrasPorMinuto < 330, `${Math.round(palabrasPorMinuto)} palabras por minuto no da tiempo a leer`);

  // Y el recorrido completo, con los pasos que de verdad tienen los recorridos de hoy
  // (entre 14 y 45 palabras, catorce pasos), tiene que caber en dos minutos.
  const pasos = [14, 18, 24, 28, 30, 31, 33, 36, 38, 40, 42, 44, 45, 45];
  const total = pasos.reduce((suma, n) => suma + duracionPaso('palabra '.repeat(n)), 0);
  assert.ok(total < 120000, `un recorrido entero duraría ${Math.round(total / 1000)} segundos`);
  assert.ok(total > 60000, `un recorrido entero duraría solo ${Math.round(total / 1000)} segundos`);
});

test('ningún paso pasa volando ni se eterniza', () => {
  assert.equal(duracionPaso('Una frase corta.'), 2500, 'tope de abajo');
  assert.equal(duracionPaso('palabra '.repeat(500)), 9000, 'tope de arriba');
  assert.equal(duracionPaso(''), 2500);
  assert.equal(duracionPaso('   '), 2500);
});

test('la duración sale entera aunque los parámetros no lo sean', () => {
  // setTimeout quiere un entero. Con los parámetros por omisión el resultado ya lo es,
  // así que el redondeo solo se ejercita pasándolos fraccionarios.
  const d = duracionPaso('una dos tres', { base: 2000.5, porPalabra: 100.25, min: 0, max: 99999 });
  assert.ok(Number.isInteger(d), `salió ${d}`);
  assert.equal(d, 2301); // 2000.5 + 3 × 100.25 = 2301.25
});

test('picar en la barra cae en el paso que muestra', () => {
  // Con 4 pasos, la barra se reparte en cuatro cuartos: [0, 0.25) es el paso 1,
  // [0.25, 0.5) el paso 2, y así. El borde de cada cuarto pertenece al paso que
  // empieza, no al que acaba.
  assert.equal(pasoDeFraccion(0, 4), 0);
  assert.equal(pasoDeFraccion(0.2, 4), 0);
  assert.equal(pasoDeFraccion(0.25, 4), 1, 'el borde del cuarto abre el paso siguiente');
  assert.equal(pasoDeFraccion(0.26, 4), 1);
  assert.equal(pasoDeFraccion(0.5, 4), 2);
  assert.equal(pasoDeFraccion(0.75, 4), 3);
  assert.equal(pasoDeFraccion(0.99, 4), 3);
  assert.equal(pasoDeFraccion(1, 4), 3, 'el extremo derecho no se sale del relato');
});

test('picar fuera de la barra no se sale del relato', () => {
  assert.equal(pasoDeFraccion(-0.5, 4), 0);
  assert.equal(pasoDeFraccion(2, 4), 3);
});

test('un recorrido sin pasos no revienta ni devuelve un índice imposible', () => {
  // No hay guarda explícita: el recorte es quien tiene que dar 0.
  assert.equal(pasoDestino(0, 0, 1), 0);
  assert.equal(pasoDestino(0, 0, -1), 0);
  assert.equal(pasoDeFraccion(0.5, 0), 0);
});

test('el paso visible se deduce de la posición de la pantalla', () => {
  const innerHeight = 900;
  const offset = 0.75;
  const linea = innerHeight * offset; // 675
  const tops = [1000, 1900, 2800, 3700, 4600];
  const en = (scrollY) => pasoVisibleEn({ tops, scrollY, innerHeight, offset });

  // Antes de que el primer paso cruce la línea, el paso es el primero igualmente.
  assert.equal(en(0), 0);
  assert.equal(en(1000 - linea - 1), 0);
  // Justo al cruzarla, sigue siendo el primero; y al cruzar el segundo, el segundo.
  assert.equal(en(1000 - linea), 0);
  assert.equal(en(1900 - linea), 1);
  assert.equal(en(1900 - linea - 1), 0, 'un píxel antes todavía no ha cruzado');
  assert.equal(en(2800 - linea), 2);
  assert.equal(en(4600 - linea), 4);
  // Más allá del último, no se inventa un paso que no existe.
  assert.equal(en(99999), 4);
});

test('el paso deducido concuerda con el destino que calcula el salto', () => {
  // Las dos cuentas tienen que cerrar: saltar al paso i y luego preguntar qué paso se
  // ve desde ahí debe devolver i. Si una se desvía de la otra, el motor oscila.
  const innerHeight = 900;
  const tops = [1000, 1900, 2800, 3700, 4600];
  // Con los dos umbrales que usan los recorridos de verdad: el destino no depende del
  // umbral, pero el paso que se deduce sí, así que tienen que cerrar con los dos.
  for (const offset of [0.72, 0.75]) {
    for (let i = 0; i < tops.length; i++) {
      const y = objetivoScroll({ topAbs: tops[i] });
      assert.equal(pasoVisibleEn({ tops, scrollY: y, innerHeight, offset }), i,
        `el paso ${i} no cierra con umbral ${offset}`);
    }
  }
});

test('la barra de avance cuenta el paso en curso como recorrido', () => {
  // En el primer paso la barra ya tiene que pintar algo: vacía se lee como "esto no
  // ha empezado", que es justo la queja que trajo estos mandos.
  assert.equal(fraccionAvance(0, 14), 1 / 14);
  assert.ok(fraccionAvance(0, 14) > 0);
  assert.equal(fraccionAvance(13, 14), 1);
  assert.equal(fraccionAvance(6, 14), 7 / 14);
  // Nunca se sale de [0, 1], ni pidiendo un paso de más ni con un recorrido vacío.
  assert.equal(fraccionAvance(20, 14), 1);
  assert.equal(fraccionAvance(-5, 14), 0);
  // Con cero pasos solo se exige que no se salga del tramo. El valor concreto sale de
  // una división por cero y no es un contrato: clavarlo aquí bloquearía el día que
  // alguien decida, con razón, que un recorrido vacío pinta la barra a cero.
  const vacio = fraccionAvance(0, 0);
  assert.ok(vacio >= 0 && vacio <= 1, `con cero pasos la barra se sale del tramo: ${vacio}`);
});

test('la barra en reproducción apunta al paso siguiente, no al actual', () => {
  // Es la cuenta que hace pintarBarra para que la barra corra mientras se lee un
  // paso. Si ambas dieran lo mismo, la barra no se movería y volvería a parecer
  // muerta: el salto entre paso y paso tiene que ser visible.
  const total = 14;
  for (const step of [0, 5, 12]) {
    const avance = fraccionAvance(step + 1, total) - fraccionAvance(step, total);
    assert.ok(avance > 0, `el paso ${step} no hace avanzar la barra`);
    // Con tolerancia: son fracciones en coma flotante, y 7/14 - 6/14 no da 1/14 exacto.
    assert.ok(Math.abs(avance - 1 / total) < 1e-12, `avance inesperado: ${avance}`);
  }
});

test('el viaje de un salto dura lo bastante poco para encadenar clics', () => {
  const innerHeight = 900;
  // Un paso de distancia: medio segundo largo, no más. Si durara más que el intervalo
  // entre dos clics con prisa, el segundo clic tendría que esperar al primero, que es
  // justo lo que dejaba la pantalla a medio camino.
  const unPaso = duracionViaje(innerHeight, { innerHeight });
  assert.ok(unPaso >= 300 && unPaso <= 600, `un paso dura ${unPaso} ms`);
  // Y un viaje de punta a punta del relato no se eterniza.
  assert.ok(duracionViaje(13 * innerHeight, { innerHeight }) <= 900);
  // La dirección no cambia la duración: subir cuesta lo mismo que bajar.
  assert.equal(duracionViaje(-3 * innerHeight, { innerHeight }), duracionViaje(3 * innerHeight, { innerHeight }));
  // Quedarse donde estás no dura nada apreciable.
  assert.ok(duracionViaje(0, { innerHeight }) <= 300);
  // Crece con la distancia hasta el tope, nunca al revés.
  let previo = 0;
  for (const pantallas of [0, 0.5, 1, 2, 4, 8, 20]) {
    const d = duracionViaje(pantallas * innerHeight, { innerHeight });
    assert.ok(d >= previo, `la duración bajó en ${pantallas} pantallas`);
    previo = d;
  }
});

test('el suavizado del viaje arranca, frena y no se pasa del destino', () => {
  assert.equal(suavizado(0), 0);
  assert.equal(suavizado(1), 1);
  assert.equal(suavizado(0.5), 0.5);
  // Nunca se sale del tramo, ni con un cuadro que llegue tarde o antes de tiempo.
  for (const k of [-5, -0.1, 0, 0.25, 0.5, 0.75, 1, 1.1, 99]) {
    const v = suavizado(k);
    assert.ok(v >= 0 && v <= 1, `suavizado(${k}) = ${v} se sale del tramo`);
  }
  // Monótono: la pantalla nunca retrocede a mitad de un viaje.
  let previo = -1;
  for (let k = 0; k <= 1.0001; k += 0.05) {
    const v = suavizado(k);
    assert.ok(v >= previo, `el viaje retrocede en k=${k}`);
    previo = v;
  }
  // Arranca despacio y frena: en el primer cuarto se recorre menos que un cuarto.
  assert.ok(suavizado(0.25) < 0.25, 'no arranca despacio');
  assert.ok(suavizado(0.75) > 0.75, 'no frena al final');
});

test('ningún valor raro deja el viaje sin final', () => {
  // Math.min y Math.max NO recortan NaN, lo propagan. Y un NaN aquí no es un pixel mal
  // puesto: ninguna comparación con NaN es cierta, así que el bucle de animación no
  // encontraría nunca su condición de parada y seguiría pidiendo cuadros para siempre.
  // Por eso NaN tiene que salir como viaje terminado.
  assert.equal(suavizado(NaN), 1, 'un NaN dejaría el viaje sin condición de parada');
  // Los infinitos sí los recorta Math, cada uno a su extremo.
  assert.equal(suavizado(Infinity), 1);
  assert.equal(suavizado(-Infinity), 0);
  // Y lo que de verdad protege el bucle: el resultado siempre es un número finito.
  for (const k of [NaN, Infinity, -Infinity, -0, 1e308, -1e308]) {
    assert.ok(Number.isFinite(suavizado(k)), `suavizado(${k}) no es finito`);
  }
  // La duración tampoco puede salir en NaN: sería una división por NaN en el motor.
  assert.ok(Number.isFinite(duracionViaje(0, { innerHeight: 0 })), 'duracionViaje no sobrevive a una ventana de alto cero');
});

test('la última parada deja la tarjeta de cierre justo debajo de la cabecera', () => {
  // La tarjeta no mide una pantalla, así que aquí no se cuadra ninguna caja: lo que
  // se busca es que su borde de arriba asome entero por debajo de la cabecera fija.
  const altoHeader = 64;
  const topAbs = 12600;
  const y = objetivoCierre({ topAbs, altoHeader });
  assert.equal(y, topAbs - altoHeader);
  // Desde ahí, el borde de la tarjeta cae justo donde acaba la cabecera.
  assert.equal(topAbs - y, altoHeader);
});

test('la última parada no pide un scroll negativo ni más del que existe', () => {
  // Una cabecera más alta que la propia tarjeta no puede mandar la página hacia atrás.
  assert.equal(objetivoCierre({ topAbs: 30, altoHeader: 64 }), 0);
  // Y la tarjeta es lo último de la página: su destino casi siempre topa con el final.
  assert.equal(objetivoCierre({ topAbs: 12600, altoHeader: 64, maxScroll: 9000 }), 9000);
  assert.equal(objetivoCierre({ topAbs: 0, altoHeader: 0, maxScroll: 0 }), 0);
});

test('sin cabecera, la última parada es el borde mismo de la tarjeta', () => {
  assert.equal(objetivoCierre({ topAbs: 4321, altoHeader: 0 }), 4321);
});

test('la tarjeta de cierre cuenta como la parada siguiente al último paso', () => {
  const innerHeight = 900;
  const offset = 0.75;
  const tops = [1200, 2100, 3000, 3900];
  // La tarjeta va justo detrás del último paso, más la línea de créditos.
  const topCierre = 5100;
  const parada = (scrollY) => paradaVisibleEn({ tops, topCierre, scrollY, innerHeight, offset });

  // Mientras la tarjeta no cruce la línea de disparo, manda el paso de siempre.
  assert.equal(parada(0), 0);
  assert.equal(parada(2400), 2);
  assert.equal(parada(3300), 3);
  // En cuanto la cruza, la parada es la de cierre, que es `tops.length`.
  const alBorde = topCierre - innerHeight * offset;
  assert.equal(parada(alBorde - 1), 3, 'un píxel antes todavía es el último paso');
  assert.equal(parada(alBorde), 4, 'justo en la línea ya es la tarjeta de cierre');
  assert.equal(parada(alBorde + 2000), 4, 'más abajo sigue siendo la tarjeta');
});

test('sin tarjeta de cierre, la última parada sigue siendo el último paso', () => {
  // Es el caso de una página que embeba un recorrido sin tarjeta: nada debe cambiar.
  const comun = { tops: [1200, 2100, 3000, 3900], innerHeight: 900, offset: 0.75 };
  for (const scrollY of [0, 2400, 3300, 9000]) {
    assert.equal(
      paradaVisibleEn({ ...comun, scrollY }),
      pasoVisibleEn({ ...comun, scrollY }),
      `sin tarjeta, la parada en ${scrollY} tiene que ser el paso de siempre`,
    );
  }
});

test('la tarjeta de cierre suma una parada, y sin ella no sobra ninguna', () => {
  assert.equal(contarParadas(14, true), 15);
  assert.equal(contarParadas(14, false), 14);
  assert.equal(contarParadas(1, true), 2);
  assert.equal(contarParadas(0, true), 1);
  assert.equal(contarParadas(0, false), 0);
  // Un número de pasos imposible no puede devolver un total negativo.
  assert.equal(contarParadas(-3, false), 0);
});

test('la parada de cierre es la que va justo detrás del último paso', () => {
  const pasos = 14;
  // Con tarjeta: los pasos son 0..13 y la tarjeta es la 14.
  assert.equal(esParadaDeCierre(13, pasos, true), false, 'el último paso no es la tarjeta');
  assert.equal(esParadaDeCierre(14, pasos, true), true, 'la 14 es la tarjeta');
  assert.equal(esParadaDeCierre(0, pasos, true), false);
  // Sin tarjeta no hay ninguna parada de cierre, pida lo que pida.
  for (const parada of [0, 13, 14, 99]) {
    assert.equal(esParadaDeCierre(parada, pasos, false), false, `sin tarjeta, ${parada} no puede serlo`);
  }
});

test('la reproducción se detiene en la última parada, no un paso antes', () => {
  // Este es el fallo que de verdad importa: con `total` en vez de `paradas`, la
  // reproducción paraba en el último paso y nunca llegaba a la tarjeta de cierre.
  const paradas = 15;
  assert.equal(esUltimaParada(13, paradas), false, 'el último paso del relato no es el final');
  assert.equal(esUltimaParada(14, paradas), true, 'la tarjeta de cierre sí lo es');
  assert.equal(esUltimaParada(0, 1), true, 'un recorrido de una parada ya está en el final');
});

test('los botones se apagan solo en los extremos del recorrido', () => {
  const paradas = 15;
  assert.deepEqual(estadoMandos(0, paradas), { atrasApagado: true, adelanteApagado: false });
  assert.deepEqual(estadoMandos(1, paradas), { atrasApagado: false, adelanteApagado: false });
  // En el último paso del relato "siguiente" tiene que seguir encendido: lleva a la
  // tarjeta de cierre. Apagarlo ahí dejaba la última parada inalcanzable.
  assert.deepEqual(estadoMandos(13, paradas), { atrasApagado: false, adelanteApagado: false });
  assert.deepEqual(estadoMandos(14, paradas), { atrasApagado: false, adelanteApagado: true });
  // Y sin tarjeta, el último paso sí es el final.
  assert.deepEqual(estadoMandos(13, 14), { atrasApagado: false, adelanteApagado: true });
});

test('el viaje de un salto tiene sus números clavados, no solo un rango', () => {
  // El rango de la otra prueba admitía dejar el viaje casi sin depender de la
  // distancia. Estos dos valores son los que de verdad gobiernan la sensación.
  assert.equal(duracionViaje(0, { innerHeight: 900 }), 240, 'la base del viaje');
  assert.equal(duracionViaje(900, { innerHeight: 900 }), 240 + 260, 'una pantalla de distancia');
  assert.equal(duracionViaje(1800, { innerHeight: 900 }), 240 + 2 * 260, 'dos pantallas');
});

test('la última parada de un recorrido vacío no es un índice imposible', () => {
  assert.equal(ultimaParada(15), 14);
  assert.equal(ultimaParada(1), 0);
  // La tecla Fin de un recorrido sin pasos no puede pedir la parada -1.
  assert.equal(ultimaParada(0), 0);
});
