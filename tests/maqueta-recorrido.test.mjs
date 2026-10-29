// Guardia de la maqueta del recorrido. El motor de los mandos salta a una posición de
// scroll calculada midiendo dónde empieza cada paso; si lo que mide una caja depende
// del modo del escenario (foto, figura o gráfico), aplicar un paso mueve de sitio todos
// los de abajo, el salto cae a destiempo y scrollama y el motor se pelean por cuál es
// el paso activo. Eso pasó: un clic en "siguiente" encadenaba 2 -> 1 -> 2 -> 1 -> 2 sin
// que el scroll se moviera un píxel.
//
// La condición que lo hace imposible es que NINGUNA regla que dependa de `data-mode`
// toque una métrica de caja, ni en el paso ni en nada de dentro. El hueco que el modo
// sí necesita se pone con una transformación, que no participa en el flujo.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const fuente = readFileSync(new URL('../src/components/ScrollyShell.astro', import.meta.url), 'utf8');

/** Reglas CSS de un texto, como pares selector/declaraciones. */
function reglas(texto) {
  const i = texto.indexOf('<style>');
  // Saltando la etiqueta, no solo colocándose en ella: si no, el selector de la
  // primera regla sale con "<style>" pegado delante y no se puede buscar por su nombre.
  const estilos = i === -1 ? texto : texto.slice(i + '<style>'.length, texto.lastIndexOf('</style>'));
  const sinComentarios = estilos.replace(/\/\*[\s\S]*?\*\//g, '');
  const salida = [];
  for (const trozo of sinComentarios.split('}')) {
    const j = trozo.indexOf('{');
    if (j === -1) continue;
    const selector = trozo.slice(0, j).replace(/\s+/g, ' ').trim();
    if (!selector || selector.startsWith('@')) continue;
    salida.push({ selector, cuerpo: trozo.slice(j + 1).trim() });
  }
  return salida;
}

// Propiedades que cambian lo que mide una caja. Van las físicas y las lógicas: el
// auditor de pruebas coló `padding-block-end: 12vh` por delante de la versión anterior
// de esta lista, que solo miraba las físicas, y la regresión pasó en verde.
const LADOS = ['', '-top', '-bottom', '-block', '-block-start', '-block-end'];
const METRICAS = new RegExp(
  '(^|[;\\s])(' +
  [
    ...LADOS.map((l) => 'padding' + l),
    ...LADOS.map((l) => 'margin' + l),
    ...LADOS.map((l) => 'border' + l + '-width'),
    'border', 'border-top', 'border-bottom', 'border-block', 'border-block-start', 'border-block-end',
    'height', 'min-height', 'max-height',
    'block-size', 'min-block-size', 'max-block-size',
    'aspect-ratio',
  ].join('|') +
  ')\\s*:',
);

/** Reglas de un CSS que dependen del modo del escenario y tocan la caja. */
function culpables(texto) {
  return reglas(texto)
    .filter((r) => r.selector.includes('data-mode') && METRICAS.test(r.cuerpo))
    .map((r) => r.selector + ' { ' + r.cuerpo + ' }');
}

const todas = reglas(fuente);

test('el componente trae reglas que se pueden leer', () => {
  // Si el troceado se rompe, el resto de las pruebas pasarían en verde sin comprobar
  // nada: esta es la que impide que eso ocurra en silencio.
  assert.ok(todas.length > 20, `solo se leyeron ${todas.length} reglas`);
  assert.ok(todas.some((r) => r.selector === '.step'), 'no apareció la regla .step');
  // Y ningún selector puede traer marcado pegado delante. Es el fallo que tuvo el
  // troceado: se colocaba EN la etiqueta <style> en vez de saltarla, y el selector de
  // la primera regla salía como "<style> .scrolly", imposible de buscar por su nombre.
  // Buscar una regla concreta no basta para cazarlo: solo falla si la rota resulta ser
  // justo la que esa prueba busca.
  const conMarcado = todas.filter((r) => r.selector.includes('<') || r.selector.includes('>'));
  assert.deepEqual(conMarcado.map((r) => r.selector), [],
    'un selector trae marcado pegado: el troceado no está saltando la etiqueta de estilo');
  assert.ok(todas.some((r) => r.selector.includes('data-mode')), 'no apareció ninguna regla por modo');
});

test('el paso mide su alto con el relleno dentro', () => {
  const paso = todas.find((r) => r.selector === '.step');
  assert.match(paso.cuerpo, /box-sizing\s*:\s*border-box/,
    '.step tiene que declarar box-sizing: border-box, o su relleno vertical le suma alto');
});

test('el modo del escenario no cambia lo que mide ninguna caja', () => {
  assert.deepEqual(culpables(fuente), [],
    'una regla por modo toca una métrica de caja: eso desplaza el relato en cada cambio de modo');
});

test('la guardia caza el caso que de verdad ocurrió y sus disfraces', () => {
  // Prueba de la prueba, sobre un CSS propio: así no depende de cómo esté escrito hoy
  // el componente, y no falla con un mensaje falso cada vez que alguien edita esa regla.
  const casos = [
    ["el relleno que lo rompió", ".scrolly[data-mode='svg'] .step[data-pos='center'] { align-items: flex-end; padding-bottom: 7vh; }"],
    ["el mismo relleno en lógico", ".scrolly[data-mode='foto'] .step { padding-block-end: 12vh; }"],
    ["un alto mínimo por modo", ".scrolly[data-mode='svg'] .step { min-height: 120vh; }"],
    ["su versión lógica", ".scrolly[data-mode='svg'] .step { min-block-size: 120vh; }"],
    ["un margen por modo", ".scrolly[data-mode='figura'] .step { margin-bottom: 4vh; }"],
    ["un borde por modo", ".scrolly[data-mode='svg'] .step { border-bottom-width: 30px; }"],
    // Y dentro del paso, que también desplaza el relato si crece lo bastante.
    ["un relleno en el subtítulo", ".scrolly[data-mode='svg'] .step .caption { padding-bottom: 40vh; }"],
    ["un margen en el subtítulo", ".scrolly[data-mode='svg'] .step .caption { margin-bottom: 7vh; }"],
  ];
  for (const [nombre, css] of casos) {
    assert.equal(culpables('<style>' + css + '</style>').length, 1, `la guardia no caza ${nombre}`);
  }
});

test('la guardia deja pasar lo que no toca la caja', () => {
  // Que no sea una guardia que se queja de todo: el modo sí puede cambiar colores,
  // alineación y transformaciones, que es como se pone hoy el hueco del subtítulo.
  const inocentes = [
    ".scrolly[data-mode='svg'] .step[data-pos='center'] { align-items: flex-end; }",
    ".scrolly[data-mode='svg'] .step[data-pos='center'] .caption { --alza: -7vh; }",
    ".scrolly[data-mode='foto'] .caption { background: rgba(0,0,0,0.8); }",
    ".scrolly[data-mode='foto'] .step { transform: translateY(-7vh); }",
  ];
  for (const css of inocentes) {
    assert.deepEqual(culpables('<style>' + css + '</style>'), [], `la guardia se queja de ${css}`);
  }
});

test('el hueco del subtítulo sobre el gráfico sigue puesto, y es una transformación', () => {
  const regla = todas.find((r) => r.selector.includes('data-mode') && r.selector.endsWith('.caption'));
  assert.ok(regla, 'nadie separa el subtítulo del gráfico en los pasos centrados');
  assert.match(regla.cuerpo, /--alza\s*:\s*-?\d/, 'el hueco tiene que venir de --alza');
  // Y `--alza` tiene que llegar de verdad a una transformación, no quedarse declarada.
  const subtitulo = todas.find((r) => r.selector === '.caption');
  assert.match(subtitulo.cuerpo, /transform\s*:[^;]*var\(--alza\)/, '--alza no se usa en ninguna transformación');
  const activo = todas.find((r) => r.selector === '.step.activo .caption');
  assert.match(activo.cuerpo, /transform\s*:[^;]*var\(--alza\)/, 'el paso activo pierde el hueco');
});

test('la banda de mandos no ocupa sitio en la maqueta', () => {
  // Los mandos van en una banda ancha al pie del escenario, como los de un video. La
  // franja que los sostiene tiene que seguir midiendo cero y la banda tiene que estar
  // sacada del flujo: si la banda empujara algo, movería de sitio todos los pasos de
  // abajo, que es exactamente la avería que esta guardia existe para impedir.
  const franja = todas.find((r) => r.selector === '.scrolly-chrome');
  assert.ok(franja, 'no apareció la franja de los mandos');
  assert.match(franja.cuerpo, /position\s*:\s*sticky/, '.scrolly-chrome tiene que ir pegajosa');
  assert.match(franja.cuerpo, /height\s*:\s*0/, '.scrolly-chrome tiene que medir cero de alto');
  // Y pegada abajo, no arriba: pegada arriba se soltaba una pantalla por detrás del
  // escenario, y la banda acababa flotando sobre el texto que sigue al recorrido.
  assert.match(franja.cuerpo, /bottom\s*:\s*0/,
    '.scrolly-chrome tiene que pegarse al borde de abajo, o la banda sobrevive al recorrido');
  assert.doesNotMatch(franja.cuerpo, /(^|[;\s])top\s*:/,
    'pegada también arriba, la franja no se soltaría donde debe');

  const banda = todas.find((r) => r.selector === '.scrolly-cine');
  assert.ok(banda, 'no apareció la banda de mandos');
  assert.match(banda.cuerpo, /position\s*:\s*absolute/, 'la banda tiene que estar fuera del flujo');
});

test('los pasos reservan sitio para la banda, y el mismo en todos los modos', () => {
  // Sin esa reserva, el subtítulo de los pasos que van pegados abajo queda debajo de
  // los mandos. La reserva es una sola medida para todos los modos: una que dependiera
  // del modo volvería a desplazar el relato en cada cambio de paso.
  //
  // Las tres comprobaciones miran el VALOR y el LADO, no que el nombre de la variable
  // aparezca. Con solo mirar el nombre, poner la reserva a cero o mandarla al lado de
  // arriba rompía la pantalla sin que esto se enterara.
  const paso = todas.find((r) => r.selector === '.step');
  assert.match(paso.cuerpo, /padding-bottom\s*:\s*var\(--mandos-alto\)/,
    'la reserva tiene que ir en el relleno de ABAJO del paso, en su propia declaración');

  // Todas las medidas declaradas, incluidas las de las consultas de medios.
  const medidas = [...fuente.matchAll(/--mandos-alto\s*:\s*([\d.]+)rem/g)].map((m) => Number(m[1]));
  assert.ok(medidas.length >= 2, `solo se declaró ${medidas.length} vez el alto de la banda`);
  // La banda mide 84 px en escritorio y 85 en teléfono, medidos en el navegador.
  for (const rem of medidas) {
    assert.ok(rem >= 5.5, `una reserva de ${rem}rem no cubre los 85 px que mide la banda`);
  }

  // Y el crédito de la imagen, que vive en esa misma esquina, también la esquiva: la
  // reserva ENTERA más un poco, no multiplicada por nada.
  const credito = todas.find((r) => r.selector === '.stage-credito');
  assert.match(credito.cuerpo, /bottom\s*:\s*calc\(var\(--mandos-alto\)\s*\+\s*[\d.]+[a-z]+\)/,
    'el crédito de la imagen quedaría tapado por la banda');
});
