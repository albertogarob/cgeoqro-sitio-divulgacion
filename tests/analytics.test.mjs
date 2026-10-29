// Pruebas de Analytics: que un ID mal pegado no se cargue, y que los parámetros con
// los que se desglosa el tráfico por autor respeten el tope de GA4.
import test from 'node:test';
import assert from 'node:assert/strict';
import { idMedicion, idMedicionValido, parametrosCapsula, recortarValor } from '../src/lib/analytics.ts';

test('acepta un ID de GA4 y rechaza lo que no lo es', () => {
  assert.ok(idMedicionValido('G-ABC123XYZ'));
  assert.ok(!idMedicionValido('UA-12345-6'), 'las propiedades viejas no sirven');
  assert.ok(!idMedicionValido('G-abc123'), 'GA4 usa mayúsculas');
  assert.ok(!idMedicionValido('G-123'), 'demasiado corto');
  assert.ok(!idMedicionValido('G-XXXXXXXXXX '.trim() + '!'), 'con basura pegada');
  assert.ok(!idMedicionValido(''));
  assert.ok(!idMedicionValido(undefined));
});

test('sin ID no se carga nada, y un ID mal puesto tampoco', () => {
  const avisos = [];
  const original = console.warn;
  console.warn = (m) => avisos.push(m);
  try {
    assert.equal(idMedicion(''), '');
    assert.equal(idMedicion(undefined), '');
    assert.equal(avisos.length, 0, 'un hueco vacío no es un error que haya que avisar');
    assert.equal(idMedicion('UA-12345-6'), '');
    assert.equal(avisos.length, 1, 'un valor mal puesto sí tiene que avisar');
  } finally {
    console.warn = original;
  }
});

test('el ID bueno pasa limpio, con espacios de sobra incluidos', () => {
  assert.equal(idMedicion('  G-ABC123XYZ  '), 'G-ABC123XYZ');
});

test('los parámetros permiten desglosar por cápsula, serie y autor', () => {
  const p = parametrosCapsula({
    capsula: 'mapas-sequia',
    serie: 'agua',
    investigadores: ['Rodrigo López Farías'],
  });
  assert.deepEqual(p, {
    capsula: 'mapas-sequia',
    serie: 'agua',
    investigadores: 'Rodrigo López Farías',
  });
});

test('no manda parámetros vacíos, que en GA4 serían ruido', () => {
  assert.deepEqual(parametrosCapsula({}), {});
  assert.deepEqual(parametrosCapsula({ capsula: 'x', investigadores: ['', undefined] }), { capsula: 'x' });
});

test('una lista de autores que no cabe se corta por la coma, no a media palabra', () => {
  // Cinco autores suman 118 caracteres unidos por comas: por encima del tope de GA4.
  const muchos = [
    'Rodrigo López Farías', 'Sergio Ivvan Valdez Peña', 'Karol Yáñez Soria',
    'José Joaquín Piña Mondragón', 'Alberto Garcia-Robledo',
  ];
  assert.ok(muchos.join(', ').length > 100, 'el caso de prueba tiene que rebasar el tope');
  const p = parametrosCapsula({ investigadores: muchos });
  assert.ok(p.investigadores.length <= 100, `mide ${p.investigadores.length}`);
  assert.ok(p.investigadores.endsWith('…'));
  assert.ok(p.investigadores.includes('Rodrigo López Farías'));

  // La comprobación que de verdad importa: lo que queda es un prefijo de la lista y
  // termina justo donde la lista original tiene una coma, o sea en un nombre entero.
  const original = muchos.join(', ');
  const sinPuntos = p.investigadores.slice(0, -1);
  assert.ok(original.startsWith(sinPuntos), 'el recorte no es un prefijo de la lista');
  assert.equal(original[sinPuntos.length], ',', `cortó dentro de un nombre: "...${sinPuntos.slice(-14)}"`);
});

test('una lista de autores que cabe entera no se toca', () => {
  const cuatro = ['Rodrigo López Farías', 'Sergio Ivvan Valdez Peña', 'Karol Yáñez Soria', 'José Joaquín Piña Mondragón'];
  assert.ok(cuatro.join(', ').length <= 100);
  assert.equal(parametrosCapsula({ investigadores: cuatro }).investigadores, cuatro.join(', '));
});

test('un valor que cabe se queda igual', () => {
  assert.equal(recortarValor('corto'), 'corto');
  assert.equal(recortarValor('a'.repeat(100)), 'a'.repeat(100));
  assert.equal(recortarValor('a'.repeat(101)).length, 100);
});
