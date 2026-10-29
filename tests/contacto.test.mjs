// Pruebas del contacto: que el bloque no se publique con media configuración, que el
// mensaje prellenado lleve de dónde viene, y que los enlaces salgan bien codificados.
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  asuntoContacto,
  mensajePrellenado,
  modoContacto,
  urlEnvio,
  urlFormularioPrellenado,
  urlMailto,
} from '../src/lib/contacto.ts';

const GOOGLE = {
  formId: '1FAIpQLSdAbCdEfGhIjKlMnOpQrStUvWxYz0123456789',
  entryCorreo: 'entry.1234567890',
  entryMensaje: 'entry.987654321',
  correoRespaldo: '',
};
const CORREO = { formId: '', entryCorreo: '', entryMensaje: '', correoRespaldo: 'divulgacion@ejemplo.org' };
const VACIO = { formId: '', entryCorreo: '', entryMensaje: '', correoRespaldo: '' };

const DATOS = {
  tituloCapsula: 'Predecir la sequía: mapas que se adelantan a la falta de agua',
  url: 'https://albertogarob.github.io/cgeoqro-sitio-divulgacion/capsulas/mapas-sequia/',
  investigadores: ['Rodrigo López Farías'],
};

test('distingue las tres situaciones de configuración', () => {
  assert.equal(modoContacto(GOOGLE), 'google');
  assert.equal(modoContacto(CORREO), 'correo');
  assert.equal(modoContacto(VACIO), 'ninguno');
});

test('media configuración de Google no cuenta como configurada', () => {
  assert.equal(modoContacto({ ...GOOGLE, entryMensaje: '' }), 'ninguno');
  assert.equal(modoContacto({ ...GOOGLE, formId: '' }), 'ninguno');
  // Un campo mal copiado (el número suelto, sin "entry.") no vale.
  assert.equal(modoContacto({ ...GOOGLE, entryCorreo: '1234567890' }), 'ninguno');
  assert.equal(modoContacto({ ...GOOGLE, entryCorreo: 'entry.abc' }), 'ninguno');
  // Con Google a medias pero correo puesto, cae al respaldo en vez de desaparecer.
  assert.equal(modoContacto({ ...GOOGLE, formId: '', correoRespaldo: 'a@b.org' }), 'correo');
});

test('los espacios de un pegado descuidado no invalidan la configuración', () => {
  const conEspacios = { ...GOOGLE, formId: `  ${GOOGLE.formId} `, entryCorreo: ' entry.1234567890 ' };
  assert.equal(modoContacto(conEspacios), 'google');
  assert.ok(urlEnvio(conEspacios).includes(`/d/e/${GOOGLE.formId}/formResponse`));
  assert.ok(!urlEnvio(conEspacios).includes(' '));
});

test('el mensaje prellenado dice de qué cápsula viene y de quién es la investigación', () => {
  const msg = mensajePrellenado(DATOS);
  assert.ok(msg.includes(DATOS.tituloCapsula));
  assert.ok(msg.includes(DATOS.url));
  assert.ok(msg.includes('Rodrigo López Farías'));
});

test('sin investigadores, el mensaje no deja una línea coja', () => {
  const msg = mensajePrellenado({ ...DATOS, investigadores: [] });
  assert.ok(!msg.includes('Investigación de:'));
  assert.ok(!/:\s*$/.test(msg));
  assert.equal(mensajePrellenado({ ...DATOS, investigadores: ['', undefined] }).includes('Investigación de:'), false);
});

test('las funciones de un modo no sirven en otro, y lo dicen', () => {
  assert.throws(() => urlEnvio(CORREO), /formulario de Google/);
  assert.throws(() => urlFormularioPrellenado('hola', VACIO), /formulario de Google/);
  assert.throws(() => urlMailto(DATOS, GOOGLE), /correo de respaldo/);
});

test('el enlace al formulario prellenado es una URL válida con el mensaje dentro', () => {
  const msg = mensajePrellenado(DATOS);
  const url = new URL(urlFormularioPrellenado(msg, GOOGLE));
  assert.equal(url.origin, 'https://docs.google.com');
  assert.equal(url.searchParams.get('usp'), 'pp_url');
  assert.equal(url.searchParams.get(GOOGLE.entryMensaje), msg);
});

test('el asunto del correo dice de dónde viene y lleva el título', () => {
  // Fijado literalmente: comparar el mailto contra la misma función que lo genera
  // dejaba pasar un asunto vacío.
  assert.equal(
    asuntoContacto('Predecir la sequía'),
    'Divulgación CentroGeo Querétaro: Predecir la sequía'
  );
});

test('el mailto lleva asunto y cuerpo, y codifica el espacio como %20', () => {
  const url = urlMailto(DATOS, CORREO);
  assert.ok(url.startsWith('mailto:divulgacion@ejemplo.org?'));
  assert.ok(!url.includes('+'), 'un "+" se vería literal en el cuerpo del correo');
  const params = new URLSearchParams(url.slice(url.indexOf('?') + 1));
  assert.equal(params.get('subject'), asuntoContacto(DATOS.tituloCapsula));
  assert.equal(params.get('body'), mensajePrellenado(DATOS));
});
