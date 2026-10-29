// Pruebas del recorte de texto de las tarjetas.
//
// Se midieron rompiendo `primeraFrase` a propósito, 16 veces: con la primera versión
// de este archivo, 8 de las 16 roturas pasaban en verde. Cada prueba de abajo lleva
// apuntada la rotura concreta que caza, para que no se aflojen sin darse cuenta.
import test from 'node:test';
import assert from 'node:assert/strict';
import { primeraFrase } from '../src/lib/texto.ts';

test('devuelve la primera frase y se para en el punto', () => {
  assert.equal(
    primeraFrase('Estudio redes. Una red puede ser mucha cosa.'),
    'Estudio redes.',
  );
  assert.equal(primeraFrase('Una pregunta, ¿no? Y luego otra.'), 'Una pregunta, ¿no?');
  assert.equal(primeraFrase('¡Claro que sí! Siempre.'), '¡Claro que sí!');
});

test('una abreviatura no corta la frase', () => {
  assert.equal(
    primeraFrase('Lo midió el Dr. López en 2024. Después lo repitió.'),
    'Lo midió el Dr. López en 2024.',
  );
  // Y una palabra corta que NO es abreviatura sí la corta: sin esto, la guarda se
  // puede aflojar a tragarse cualquier palabra de dos letras.
  assert.equal(primeraFrase('Lo vimos en TV. Y luego en la radio.'), 'Lo vimos en TV.');
});

test('una inicial suelta no corta la frase', () => {
  // Es el caso que destrozaba la tarjeta: sin esta guarda, el gancho de una entrevista
  // que empezara nombrando a alguien se quedaba en "J.".
  assert.equal(
    primeraFrase('J. Piña lo demostró en 2019. Luego vino el resto.'),
    'J. Piña lo demostró en 2019.',
  );
});

test('un decimal no corta la frase aunque su parte entera sea larga', () => {
  // Con una parte entera de dos cifras, la única guarda que protege el decimal es
  // exigir un espacio detrás del punto. Con "1.5" no se notaría: el "1" cae también
  // bajo la guarda de las iniciales y la prueba pasaría por partida doble.
  assert.equal(
    primeraFrase('Subió 12.5 grados en dos décadas. Ya se nota.'),
    'Subió 12.5 grados en dos décadas.',
  );
});

test('un paréntesis o una comilla delante no esconden la abreviatura', () => {
  // La palabra previa al punto se busca saltando también paréntesis y comillas,
  // porque las respuestas del frontmatter empiezan entrecomilladas.
  assert.equal(primeraFrase('(Ej. de prueba) sigue. Fin.'), '(Ej. de prueba) sigue.');
  assert.equal(primeraFrase('"Dr. López lo vio. Y lo dijo."'), '"Dr. López lo vio.');
});

test('los saltos de línea y los espacios de más se normalizan', () => {
  // Sin normalizar, el salto viaja al HTML y además cuenta como espacio para decidir
  // dónde acaba la frase, así que cambia el corte.
  assert.equal(primeraFrase('Texto\n\ncon   saltos. Y otra frase.'), 'Texto con saltos.');
});

test('un texto sin punto final se devuelve entero', () => {
  assert.equal(primeraFrase('Sin punto final'), 'Sin punto final');
});

test('una frase larguísima se corta en un espacio, sin partir palabras', () => {
  // El texto tiene palabras de distinto largo a propósito: con palabras todas del
  // mismo tamaño, el corte bruto cae justo en un espacio por casualidad y la prueba
  // pasa aunque el corte por palabra esté roto.
  const original = 'Las redes complejas describen sistemas enormes con pocas reglas sencillas.';
  const max = 40;
  const salida = primeraFrase(original, max);

  assert.ok(salida.length <= max, `salieron ${salida.length} caracteres, el tope es ${max}`);
  assert.ok(salida.endsWith('…'), 'una frase recortada tiene que avisar de que lo está');

  const texto = salida.slice(0, -1);
  assert.ok(original.startsWith(texto), 'lo recortado tiene que ser el principio del original');
  assert.equal(original[texto.length], ' ', 'el corte tiene que caer en un espacio, no dentro de una palabra');
  assert.doesNotMatch(texto, /\s$/, 'no puede quedar un espacio pegado a los puntos suspensivos');
});

test('ni un texto vacío ni uno de puro espacio revientan', () => {
  assert.equal(primeraFrase(''), '');
  assert.equal(primeraFrase('   \n  '), '');
});

test('una sola palabra larguísima se corta aunque no haya espacio donde hacerlo', () => {
  // Sin el respaldo, el corte en el último espacio devolvería la cadena vacía.
  const salida = primeraFrase('a'.repeat(300), 20);
  assert.equal(salida.length, 21);
  assert.match(salida, /^a+…$/);
});

test('el tope por omisión también recorta, que es como se usa en el sitio', () => {
  // Las tarjetas llaman a la función sin pasar tope, así que esa rama tiene que
  // estar ejercitada aquí y no solo con un tope inventado para la prueba.
  const larga = `${'palabra '.repeat(40)}final.`;
  const salida = primeraFrase(larga);
  assert.ok(salida.length <= 150, `salieron ${salida.length} caracteres`);
  assert.ok(salida.endsWith('…'));
  assert.ok(salida.length > 100, 'con el tope por omisión tiene que caber bastante texto');
});
