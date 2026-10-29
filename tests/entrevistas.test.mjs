// Pruebas del contenido de las entrevistas y de su marca de "muestra".
//
// Cuatro de las entrevistas del repositorio las redactó el equipo de divulgación y las
// puso en boca de investigadores reales, para enseñar cómo se verá la sección. Que
// aparezcan marcadas no es un detalle de estilo: sin la marca, el sitio presenta como
// declaración de una persona algo que esa persona no ha dicho.
//
// La marca se cayó dos veces durante la revisión (en el perfil del investigador y en
// los metadatos que se comparten en redes), así que aquí se sujetan las dos mitades:
// el valor en el contenido y el hecho de que cada vista lo lea.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import yaml from 'js-yaml';
import { primeraFrase } from '../src/lib/texto.ts';

const dir = new URL('../src/content/entrevistas/', import.meta.url);
const leer = (ruta) => readFileSync(new URL('../' + ruta, import.meta.url), 'utf8');

const archivos = readdirSync(dir).filter((f) => f.endsWith('.mdx'));
const entrevistas = archivos.map((f) => {
  const texto = readFileSync(new URL(f, dir), 'utf8');
  const bloque = texto.split('---')[1];
  return { archivo: f, datos: yaml.load(bloque) };
});

/**
 * Las que redactamos nosotros, con nombre y apellido. Si alguna se graba de verdad y
 * el investigador la revisa, se quita de aquí Y se le quita `esEjemplo` del archivo:
 * las dos cosas juntas, que es la fricción que esta lista existe para poner.
 */
const REDACTADAS_POR_NOSOTROS = [
  'rodrigo-lopez-farias.mdx',
  'karol-yanez-soria.mdx',
  'sergio-ivvan-valdez-pena.mdx',
  'jose-joaquin-pina-mondragon.mdx',
];

test('se leyeron las entrevistas del repositorio', () => {
  assert.ok(entrevistas.length >= 5, `solo se leyeron ${entrevistas.length} entrevistas`);
  for (const { archivo, datos } of entrevistas) {
    assert.ok(datos?.investigador, `${archivo} no declara investigador`);
    assert.equal(datos.preguntas?.length, 3, `${archivo} no trae tres preguntas`);
  }
});

test('las entrevistas que redactamos nosotros van marcadas como muestra', () => {
  for (const archivo of REDACTADAS_POR_NOSOTROS) {
    const e = entrevistas.find((x) => x.archivo === archivo);
    assert.ok(e, `falta ${archivo}: si se borró, quítalo también de la lista de arriba`);
    assert.equal(e.datos.esEjemplo, true,
      `${archivo} la escribimos nosotros y tiene que ir marcada como muestra`);
  }
});

test('todas las vistas que enseñan una entrevista leen la marca', () => {
  // El agujero que hubo: el índice y la ficha avisaban, pero el perfil del
  // investigador enlazaba la entrevista inventada sin decir nada.
  const vistas = [
    'src/pages/entrevistas/index.astro',
    'src/pages/entrevistas/[id].astro',
    'src/pages/investigadores/[id].astro',
  ];
  for (const vista of vistas) {
    assert.match(leer(vista), /esEjemplo/,
      `${vista} enseña entrevistas y no mira si son de muestra`);
  }
});

test('la marca viaja también en lo que se comparte en redes', () => {
  // Un enlace pegado en WhatsApp se lee sin abrir la página: si el aviso vive solo
  // dentro, el texto inventado circula como declaración real.
  const ficha = leer('src/pages/entrevistas/[id].astro');
  const desde = ficha.indexOf('const descripcion');
  assert.ok(desde !== -1, 'la ficha no arma una descripción propia');
  const bloque = ficha.slice(desde, desde + 420);
  assert.match(bloque, /esEjemplo/, 'la descripción compartida no distingue las de muestra');
  assert.match(bloque, /muestra/i, 'la descripción compartida no dice que es una muestra');
  assert.match(ficha, /description=\{descripcion\}/, 'la descripción no llega al layout');
});

test('el gancho de cada tarjeta cabe y no parte palabras', () => {
  // Las tarjetas del índice llaman a `primeraFrase` sin tope, así que es esa rama la
  // que hay que comprobar contra los textos de verdad, no contra uno inventado.
  for (const { archivo, datos } of entrevistas) {
    const gancho = primeraFrase(datos.preguntas[0].respuesta);
    assert.ok(gancho.length > 20, `el gancho de ${archivo} se queda en "${gancho}"`);
    assert.ok(gancho.length <= 150, `el gancho de ${archivo} mide ${gancho.length}`);
    if (gancho.endsWith('…')) {
      const texto = gancho.slice(0, -1);
      assert.equal(datos.preguntas[0].respuesta.replace(/\s+/g, ' ').trim()[texto.length], ' ',
        `el gancho de ${archivo} parte una palabra por la mitad`);
    }
  }
});
