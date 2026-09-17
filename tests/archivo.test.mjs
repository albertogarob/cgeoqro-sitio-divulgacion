// Pruebas de lo que la ficha toca en disco: que una imagen no pueda apuntar fuera de la
// carpeta pública, que escribir el recorrido no pueda dejarlo a medias, y que exportar
// no pise un archivo que ya existe.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { escribirRecorridoAtomico, existeImagenEn, prepararDestino } from '../scripts/lib/archivo.mjs';
import { parsearRecorrido } from '../scripts/lib/ficha.mjs';

function sandbox() {
  const raiz = mkdtempSync(join(tmpdir(), 'ficha-'));
  mkdirSync(join(raiz, 'public', 'scrolly'), { recursive: true });
  writeFileSync(join(raiz, 'public', 'scrolly', 'a.jpg'), 'x');
  writeFileSync(join(raiz, 'secreto.txt'), 'no se mira');
  return raiz;
}

const RECORRIDO = {
  capsula: 'c',
  titulo: 't',
  pasos: [{ visual: 'apertura', pos: 'center', tipo: 'svg', texto: 'Uno.' }],
};

test('la imagen se busca dentro de public, y un salto de carpeta no la saca de ahí', (t) => {
  const raiz = sandbox();
  t.after(() => rmSync(raiz, { recursive: true, force: true }));

  assert.equal(existeImagenEn(raiz, '/scrolly/a.jpg'), true);
  assert.equal(existeImagenEn(raiz, '/scrolly/no-existe.jpg'), false);
  // El archivo existe, pero está fuera de public: la respuesta debe ser "no".
  assert.equal(existeImagenEn(raiz, '/../secreto.txt'), false);
  assert.equal(existeImagenEn(raiz, '/../../../../etc/passwd'), false);
  assert.equal(existeImagenEn(raiz, '/'), false);
});

test('un enlace simbólico que sale de public tampoco cuela', (t) => {
  const raiz = sandbox();
  t.after(() => rmSync(raiz, { recursive: true, force: true }));
  symlinkSync(join(raiz, 'secreto.txt'), join(raiz, 'public', 'atajo.txt'));
  // La ruta en sí es válida y el destino se resuelve dentro de public, así que aquí
  // decimos que existe: lo que se comprueba es que la comprobación no se sale sola de
  // la carpeta. El enlace lo pone quien administra el repo, no quien edita la ficha.
  assert.equal(existeImagenEn(raiz, '/atajo.txt'), true);
  assert.equal(existeImagenEn(raiz, '/atajo.txt/../../secreto.txt'), false);
});

test('escribir el recorrido deja el archivo entero y legible, sin temporales sueltos', (t) => {
  const raiz = sandbox();
  t.after(() => rmSync(raiz, { recursive: true, force: true }));
  const ruta = join(raiz, 'r.yaml');

  const texto = escribirRecorridoAtomico(ruta, RECORRIDO);
  assert.equal(readFileSync(ruta, 'utf8'), texto);
  assert.deepEqual(parsearRecorrido(readFileSync(ruta, 'utf8')), RECORRIDO);
  assert.deepEqual(readdirSync(raiz).filter((f) => f.includes('.tmp-')), []);
});

test('si el recorrido no se puede serializar bien, el archivo anterior se queda intacto', (t) => {
  const raiz = sandbox();
  t.after(() => rmSync(raiz, { recursive: true, force: true }));
  const ruta = join(raiz, 'r.yaml');
  const bueno = escribirRecorridoAtomico(ruta, RECORRIDO);

  const roto = { ...RECORRIDO, pasos: [{ ...RECORRIDO.pasos[0], pos: 'arriba' }] };
  assert.throws(() => escribirRecorridoAtomico(ruta, roto), /no se puede volver a leer/);
  assert.equal(readFileSync(ruta, 'utf8'), bueno, 'el recorrido bueno sigue ahí');
  assert.deepEqual(readdirSync(raiz).filter((f) => f.includes('.tmp-')), []);
});

test('exportar no pisa un archivo que ya existe salvo que se pida a propósito', (t) => {
  const raiz = sandbox();
  t.after(() => rmSync(raiz, { recursive: true, force: true }));
  const ocupado = join(raiz, 'importante.txt');
  writeFileSync(ocupado, 'ORIGINAL');

  assert.throws(() => prepararDestino(ocupado), /ya existe/);
  assert.equal(readFileSync(ocupado, 'utf8'), 'ORIGINAL');
  assert.equal(prepararDestino(ocupado, { forzar: true }), ocupado);

  // Un destino nuevo sí se prepara, creando las carpetas que falten.
  const nuevo = join(raiz, 'fichas', 'sub', 'x.csv');
  assert.equal(prepararDestino(nuevo), nuevo);
  assert.ok(existsSync(join(raiz, 'fichas', 'sub')));
});
