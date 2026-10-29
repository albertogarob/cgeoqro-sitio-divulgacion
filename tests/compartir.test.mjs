// Pruebas de los enlaces de compartir: que una URL inservible no llegue nunca a un
// botón, que el texto vaya codificado y que el recorte no parta palabras.
import test from 'node:test';
import assert from 'node:assert/strict';
import { enlacesCompartir, urlCompartible } from '../src/lib/compartir.ts';

const BASE = {
  url: 'https://albertogarob.github.io/cgeoqro-sitio-divulgacion/capsulas/mapas-sequia/',
  titulo: 'Predecir la sequía: mapas que se adelantan a la falta de agua',
  resumen: 'La sequía avanza despacio y sin avisar.',
};

test('rechaza una URL relativa, que compartida no lleva a ninguna parte', () => {
  assert.throws(() => urlCompartible('/capsulas/mapas-sequia/'), /URL absoluta/);
  assert.throws(() => enlacesCompartir({ ...BASE, url: '/capsulas/x/' }), /URL absoluta/);
});

test('rechaza esquemas que no son http ni https', () => {
  assert.throws(() => urlCompartible('javascript:alert(1)'), /http o https/);
  assert.throws(() => urlCompartible('file:///home/alberto/x.html'), /http o https/);
});

test('da una entrada por red, todas con destino absoluto', () => {
  const enlaces = enlacesCompartir(BASE);
  assert.deepEqual(enlaces.map((e) => e.red), ['whatsapp', 'facebook', 'x', 'linkedin']);
  for (const e of enlaces) {
    assert.match(e.href, /^https:\/\//, `${e.red} no apunta a https`);
    assert.ok(e.etiqueta.length > 0, `${e.red} sin etiqueta accesible`);
  }
});

test('la URL viaja codificada, no en claro, dentro del parámetro', () => {
  const [whatsapp, facebook] = enlacesCompartir(BASE);
  const codificada = encodeURIComponent(BASE.url);
  assert.ok(facebook.href.endsWith(codificada));
  assert.ok(whatsapp.href.includes(codificada));
  // Las dos partes del separador de parámetros de la URL compartida no deben
  // aparecer en claro: romperían el enlace de la red.
  assert.ok(!facebook.href.slice('https://www.facebook.com/sharer/sharer.php?u='.length).includes('&'));
});

test('el título con caracteres especiales no rompe el parámetro', () => {
  const [, , x] = enlacesCompartir({ ...BASE, titulo: 'Agua & sequía: ¿qué sigue? 100%' });
  assert.ok(x.href.includes(encodeURIComponent('Agua & sequía: ¿qué sigue? 100%')));
  assert.ok(!x.href.includes('100% '));
});

/** Tope de longitud del texto que se arrastra al compartir. */
const LIMITE = 240;

function textoCompartido(enlace) {
  return decodeURIComponent(enlace.href.split('text=')[1].split('%20https')[0]);
}

/**
 * Resumen armado para que el corte en seco caiga OBLIGATORIAMENTE dentro de una
 * palabra. Con palabras repetidas o con una lista cualquiera, el corte cae por
 * casualidad en una frontera y la prueba pasa sin comprobar nada: se verificó que así
 * era, y por eso el fixture se construye en vez de escribirse a mano.
 */
function resumenQueCruzaElLimiteAMitadDePalabra(titulo) {
  const prefijo = `${titulo}. `;
  let resumen = '';
  while ((prefijo + resumen).length < LIMITE - 20) resumen += 'uno dos tres ';
  return `${resumen}palabralarguisimaqueatraviesaellimite y mas texto detras`;
}

test('un resumen larguísimo se recorta sin partir palabras y marca el corte', () => {
  const resumen = resumenQueCruzaElLimiteAMitadDePalabra(BASE.titulo);
  const original = `${BASE.titulo}. ${resumen}`;

  // Precondición del caso: el corte en seco tiene que caer dentro de una palabra. Si
  // dejara de cumplirse, la prueba pasaría sin probar nada y hay que saberlo.
  assert.ok(
    original[LIMITE - 2] !== ' ' && original[LIMITE - 1] !== ' ',
    `el fixture ya no cruza el límite a mitad de palabra: "${original.slice(LIMITE - 8, LIMITE + 4)}"`
  );

  const [whatsapp] = enlacesCompartir({ ...BASE, resumen });
  const texto = textoCompartido(whatsapp);
  assert.ok(texto.length <= LIMITE, `el texto mide ${texto.length}`);
  assert.ok(texto.endsWith('…'), 'el recorte debe quedar marcado');

  // La comprobación que de verdad importa: lo que queda es un prefijo del original y
  // termina justo donde el original tiene un espacio, o sea en una palabra entera.
  const sinPuntos = texto.slice(0, -1);
  assert.ok(original.startsWith(sinPuntos), 'el recorte no es un prefijo del original');
  assert.equal(original[sinPuntos.length], ' ', `cortó dentro de una palabra: "...${sinPuntos.slice(-14)}"`);
});

test('el tope de longitud del texto compartido está fijado en 240', () => {
  const justo = 'x'.repeat(LIMITE - BASE.titulo.length - 2); // "titulo" + ". " + resumen
  const [cabe] = enlacesCompartir({ ...BASE, resumen: justo });
  assert.equal(textoCompartido(cabe).length, LIMITE);
  assert.ok(!textoCompartido(cabe).endsWith('…'), 'lo que cabe no se recorta');

  const [noCabe] = enlacesCompartir({ ...BASE, resumen: `${justo}x` });
  assert.ok(textoCompartido(noCabe).endsWith('…'), 'un carácter de más ya se recorta');
});

test('los espacios de sobra y los saltos de línea se normalizan', () => {
  const [whatsapp] = enlacesCompartir({ url: BASE.url, titulo: 'Uno', resumen: 'dos   tres\n\ncuatro' });
  assert.equal(textoCompartido(whatsapp), 'Uno. dos tres cuatro');
});

test('sin resumen, el texto compartido es el título a secas', () => {
  const [whatsapp] = enlacesCompartir({ url: BASE.url, titulo: 'Título corto' });
  assert.equal(textoCompartido(whatsapp), 'Título corto');
});

test('la URL se devuelve normalizada, no tal cual llegó', () => {
  assert.equal(urlCompartible('https://EJEMPLO.org/ruta'), 'https://ejemplo.org/ruta');
  assert.equal(urlCompartible('https://ejemplo.org'), 'https://ejemplo.org/');
});
