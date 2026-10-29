// Pruebas del contrato de la tarjeta de cierre, que es la última parada del recorrido:
// la ficha de quien firma el artículo y los botones de compartir.
//
// El contrato cruza cuatro archivos y ninguna de sus roturas hace ruido:
//
//  - la página marca la tarjeta y la monta en el hueco "cierre" del recorrido;
//  - cada escena reenvía ese hueco hasta el armazón;
//  - el armazón lo pinta dentro del alcance de los mandos;
//  - el motor la busca por la marca y la cuenta como una parada más.
//
// Si falla cualquiera de los cuatro, el recorrido simplemente se acaba un paso antes y
// nadie se entera hasta verlo.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';

// AVISO sobre el alcance de este archivo: las comprobaciones que miran `scrolly.ts`
// leen su TEXTO, no ejecutan el motor, que necesita un navegador. Cazan que una
// llamada se escriba mal; no cazan que la lógica de alrededor esté mal. Por eso las
// cuentas de las paradas viven en `src/scripts/pasos.ts` y se prueban de verdad en
// `tests/pasos.test.mjs`: lo que se puede ejecutar, se ejecuta, y aquí se queda solo
// el cableado. Se midió rompiendo el motor a propósito: trece mutaciones pasaban en
// verde cuando la aritmética estaba aquí dentro.

/** Una línea normalizada en espacios, para no atarse a cómo esté formateada. */
const lineas = (fuente) => fuente.split('\n').map((l) => l.trim().replace(/\s+/g, ' '));

/** ¿Está esta línea exacta (ya normalizada) en el archivo? */
const traeLinea = (fuente, linea) => lineas(fuente).includes(linea);

const leer = (ruta) => readFileSync(new URL('../' + ruta, import.meta.url), 'utf8');
const pagina = leer('src/pages/capsulas/[id].astro');
const motor = leer('src/scripts/scrolly.ts');
const armazon = leer('src/components/ScrollyShell.astro');

const MARCA = 'data-recorrido-cierre';

test('la página marca una sola tarjeta de cierre y la monta dentro del recorrido', () => {
  const secciones = pagina.match(new RegExp(`<section[^>]*\\s${MARCA}`, 'g')) ?? [];
  assert.equal(secciones.length, 1, `hay ${secciones.length} secciones marcadas, esperaba 1`);
  // Dentro del recorrido, no detrás: fuera, la banda de mandos desaparece justo al
  // llegar a la tarjeta y la última parada se queda sin reproductor. El orden de los
  // atributos da igual, que genera el mismo HTML.
  const etiqueta = (pagina.match(/<section[^>]*>/g) ?? []).find((t) => t.includes(MARCA));
  assert.ok(etiqueta, 'no se encontró la etiqueta de la tarjeta');
  assert.ok(etiqueta.includes('slot="cierre"'),
    'la tarjeta no se monta en el hueco "cierre" del recorrido');
  const recorrido = pagina.slice(pagina.indexOf('<ScrollyComp>'), pagina.indexOf('</ScrollyComp>'));
  assert.ok(recorrido.includes(MARCA), 'la tarjeta quedó fuera del recorrido');
});

test('todas las escenas reenvían el hueco de cierre hasta el armazón', () => {
  // Una escena que no lo reenvíe deja ese recorrido sin última parada, en silencio.
  //
  // Las escenas se reconocen por IMPORTAR el armazón, no por escribir su nombre en el
  // marcado: con lo segundo, renombrarlo al importarlo sacaba esa escena de la
  // revisión sin que nadie se enterara. Y se cuentan: saltarse una en silencio es
  // justo lo que esta prueba tiene que impedir.
  const archivos = readdirSync(new URL('../src/components/', import.meta.url))
    .filter((f) => f.endsWith('.astro') && f !== 'ScrollyShell.astro');
  const escenas = archivos.filter((f) => /import\s+\w+\s+from\s+'\.\/ScrollyShell\.astro'/.test(leer('src/components/' + f)));
  assert.ok(escenas.length >= 3, `solo se encontraron ${escenas.length} escenas, esperaba al menos 3`);
  const reenvian = escenas.filter((f) => /<slot name="cierre" slot="cierre"\s*\/>/.test(leer('src/components/' + f)));
  assert.deepEqual(
    escenas.filter((f) => !reenvian.includes(f)),
    [],
    'estas escenas no reenvían el hueco de cierre y se quedarían sin última parada',
  );
  assert.match(armazon, /<slot name="cierre"\s*\/>/, 'el armazón no pinta el hueco de cierre');
});

test('la banda de mandos alcanza la tarjeta de cierre', () => {
  // Las dos cosas van juntas: la tarjeta se pinta fuera de la sección de los pasos, y
  // la franja de los mandos cuelga del bloque entero. Si los mandos volvieran dentro
  // de la sección, desaparecerían justo al llegar a la última parada.
  const finSeccion = armazon.indexOf('</section>');
  assert.ok(finSeccion !== -1);
  assert.ok(armazon.indexOf('<slot name="cierre"') > finSeccion,
    'la tarjeta de cierre se pinta dentro de la sección de los pasos');
  assert.ok(armazon.indexOf('class="scrolly-chrome"') > finSeccion,
    'los mandos volvieron dentro de la sección y no llegarán a la tarjeta');
  // Y en este orden: primero la tarjeta, después los mandos. Al revés, los mandos
  // dejan de ser lo último del bloque y vuelven a soltarse antes de tiempo.
  assert.ok(armazon.indexOf('<slot name="cierre"') < armazon.indexOf('class="scrolly-chrome"'),
    'los mandos tienen que ir detrás de la tarjeta de cierre');
});

test('el motor engancha las cuentas de las paradas, en vez de rehacerlas', () => {
  // Las cuentas están probadas de verdad en tests/pasos.test.mjs. Lo que se comprueba
  // aquí es que el motor las USE: rehacer la aritmética a mano aquí dentro es lo que
  // dejaba pasar en verde trece roturas distintas.
  assert.match(motor, new RegExp(`querySelector<HTMLElement>\\('\\[${MARCA}\\]'\\)`),
    'el motor no busca la tarjeta de cierre por su marca');
  assert.ok(traeLinea(motor, 'const paradas = contarParadas(total, hayCierre);'),
    'el motor no usa la cuenta de paradas');
  assert.ok(traeLinea(motor, 'const estado = estadoMandos(paradaPedida, paradas);'),
    'el estado de los botones no sale de la cuenta probada');
  // Y nadie puede volver a escribir el final del recorrido a mano.
  const aMano = lineas(motor).filter((l) => /(paradas|total) - 1\b/.test(l) && !l.startsWith('//'));
  assert.deepEqual(aMano, [],
    'alguien rehízo a mano el final del recorrido: eso va en esUltimaParada');
});

test('el cableado del motor apunta a las cuentas correctas', () => {
  // Cinco líneas que no se pueden ejecutar sin navegador y que, cambiadas, rompen el
  // recorrido en silencio. Cada una se clava entera.
  const exigidas = [
    ['el contador anuncia las paradas, no los pasos',
     'if (totalEl) totalEl.textContent = String(paradas);'],
    ['los mandos avanzan desde la parada PEDIDA, o se pierden los clics seguidos',
     'const destino = pasoDestino(paradaPedida, paradas, delta);'],
    ['con un viaje en marcha manda el destino, no lo que cante scrollama',
     'if (!viaje) paradaPedida = parada;'],
    ['el destino del cierre se mide desde el inicio del documento',
     'topAbs: cierre!.getBoundingClientRect().top + window.scrollY,'],
    ['el play de la entrada arranca en el primer paso',
     'reproducir(0);'],
    ['la tarjeta de cierre va justo detrás del último paso',
     'const CIERRE = total;'],
  ];
  for (const [porque, linea] of exigidas) {
    assert.ok(traeLinea(motor, linea), `${porque} (falta la línea: ${linea})`);
  }
});

test('el viaje a la tarjeta de cierre descuenta la cabecera', () => {
  // `objetivoCierre` está probada aparte, con números. Lo que se comprueba aquí es que
  // el motor la llame con el alto real de la cabecera: con un cero, la tarjeta aparece
  // con su título metido debajo del encabezado fijo.
  //
  // Es una comprobación sobre el TEXTO del archivo, no sobre el motor corriendo: el
  // motor necesita un navegador y estas pruebas no lo tienen.
  const desde = motor.indexOf('function destinoDeParada');
  assert.ok(desde !== -1, 'no existe destinoDeParada');
  const cuerpo = motor.slice(desde, motor.indexOf('\n  }', desde));
  assert.match(cuerpo, /objetivoCierre\(\{/, 'la parada de cierre no usa su propio destino');
  assert.match(cuerpo, /altoHeader:\s*altoHeader\(\)/,
    'el viaje al cierre no descuenta el alto real de la cabecera');
});

test('la tarjeta de cierre lleva dentro la ficha del autor y los botones de compartir', () => {
  const desde = pagina.indexOf(MARCA);
  const hasta = pagina.indexOf('</section>', desde);
  assert.ok(desde !== -1 && hasta > desde, 'no se pudo acotar la sección de cierre');
  const tarjeta = pagina.slice(desde, hasta);
  assert.match(tarjeta, /<AutorCapsula\b/, 'la tarjeta de cierre no trae la ficha del autor');
  assert.match(tarjeta, /<CompartirCapsula\b/, 'la tarjeta de cierre no trae los botones de compartir');
});

test('ni la ficha del autor ni los botones de compartir se pintan dos veces', () => {
  // Fuera del recorrido los dos bloques siguen al pie de la página, pero entonces la
  // tarjeta de cierre no existe: los dos caminos se excluyen por `cierreDelRecorrido`.
  for (const comp of ['CompartirCapsula', 'AutorCapsula']) {
    const veces = pagina.match(new RegExp(`<${comp}\\b`, 'g')) ?? [];
    assert.equal(veces.length, 2, `<${comp}> aparece ${veces.length} veces, esperaba 2`);
  }
  const guarda = pagina.indexOf('{!cierreDelRecorrido && (');
  assert.ok(guarda !== -1, 'falta la guarda que separa los dos caminos');
  const alPie = pagina.slice(guarda, pagina.indexOf('<ContactoCapsula'));
  assert.match(alPie, /<CompartirCapsula\b/, 'el camino sin recorrido se quedó sin compartir');
  assert.match(alPie, /<AutorCapsula\b/, 'el camino sin recorrido se quedó sin ficha del autor');
  assert.match(pagina, /const cierreDelRecorrido = Boolean\(ScrollyComp\)/,
    'la guarda tiene que depender de si la cápsula es un recorrido');
});

test('el botón de play de la entrada arranca el recorrido desde el principio', () => {
  assert.match(pagina, /class="hint-play"/, 'la entrada no trae botón de play');
  assert.match(pagina, /reproducirRecorrido/, 'el botón de play no llama a nadie');
  assert.match(motor, /export function reproducirRecorrido/, 'el motor no expone cómo arrancar');
  // Y tiene que arrancar en el primer paso, no donde se hubiera quedado la pantalla.
  const manejador = motor.slice(motor.indexOf("addEventListener(EVENTO_REPRODUCIR"));
  assert.match(manejador.slice(0, 220), /reproducir\(0\)/,
    'el play de la entrada no arranca desde el primer paso');
});
