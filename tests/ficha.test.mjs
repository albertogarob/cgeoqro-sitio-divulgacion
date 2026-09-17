// Pruebas de la ficha de recorrido: el CSV que revisan los autores, el YAML que
// consume el sitio, y las reglas que impiden que una ficha mal editada entre al repo.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  CAMPOS_BLOQUEADOS,
  CAMPOS_EDITABLES,
  COLUMNAS,
  LIMITE_TEXTO,
  aplicarFicha,
  generarCsv,
  normalizarTexto,
  parsearCsv,
  parsearRecorrido,
  recorridoAFicha,
  revisarEscritura,
  rutaDeImagenValida,
  serializarRecorrido,
  serializarRecorridoVerificado,
} from '../scripts/lib/ficha.mjs';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DIR_RECORRIDOS = join(RAIZ, 'src', 'content', 'recorridos');
const DIR_COMPONENTES = join(RAIZ, 'src', 'components');

// Recorrido de juguete: un paso de cada tipo relevante.
function recorridoBase() {
  return {
    capsula: 'capsula-prueba',
    titulo: 'Título de prueba',
    pasos: [
      { visual: 'apertura', pos: 'center', tipo: 'foto', imagen: '/scrolly/a.jpg', credito: 'Foto: alguien (CC BY)', texto: 'Primer paso.' },
      { visual: 'dato', pos: 'right', tipo: 'svg', texto: 'Segundo paso.' },
      { visual: 'figura', pos: 'left', tipo: 'figura', imagen: '/scrolly/b.png', imagenLado: 'der', credito: 'Figura: artículo (CC BY-NC-SA)', texto: 'Tercer paso.' },
    ],
  };
}

/** Ficha del recorrido base, con los cambios indicados por número de paso. */
function fichaCon(cambios = {}) {
  const filas = recorridoAFicha(recorridoBase());
  for (const [paso, campos] of Object.entries(cambios)) {
    for (const [campo, valor] of Object.entries(campos)) {
      filas[Number(paso)][COLUMNAS.indexOf(campo)] = valor;
    }
  }
  return filas;
}

const siempreExiste = () => true;

// ------------------------------------------------------------------------- CSV

test('el CSV sobrevive comas, comillas, saltos de línea y acentos', () => {
  const filas = [
    ['a', 'con, coma', 'con "comillas"'],
    ['b', 'con\nsalto', 'acentuación ñ'],
  ];
  assert.deepEqual(parsearCsv(generarCsv(filas)), filas);
});

test('el CSV acepta LF, CRLF y BOM, sin inventar una fila final vacía', () => {
  assert.deepEqual(parsearCsv('a,b\r\nc,d\r\n'), [['a', 'b'], ['c', 'd']]);
  assert.deepEqual(parsearCsv('a,b\nc,d\n'), [['a', 'b'], ['c', 'd']]);
  assert.deepEqual(parsearCsv('﻿a,b\nc,d'), [['a', 'b'], ['c', 'd']]);
});

test('el CSV conserva las celdas vacías del final de una fila', () => {
  assert.deepEqual(parsearCsv('a,b,\n'), [['a', 'b', '']]);
  assert.deepEqual(parsearCsv('a,,c\n'), [['a', '', 'c']]);
});

test('el CSV falla, en vez de adivinar, cuando las comillas están mal', () => {
  assert.throws(() => parsearCsv('a,"sin cerrar\n'), /nunca se cerró/);
  assert.throws(() => parsearCsv('a,b"c\n'), /comilla en medio/);
});

// ------------------------------------------------------------------------ YAML

test('serializar y volver a leer devuelve el mismo recorrido', () => {
  const rec = recorridoBase();
  rec.pasos[0].texto = 'Comillas "dobles", una barra \\ y acentos: ¿qué tal?';
  assert.deepEqual(parsearRecorrido(serializarRecorrido(rec)), rec);
});

test('los recorridos del repo ya están en el formato canónico', () => {
  const archivos = readdirSync(DIR_RECORRIDOS).filter((f) => f.endsWith('.yaml'));
  assert.ok(archivos.length > 0, 'no hay recorridos que revisar');
  for (const archivo of archivos) {
    const texto = readFileSync(join(DIR_RECORRIDOS, archivo), 'utf8');
    assert.equal(serializarRecorrido(parsearRecorrido(texto)), texto, `${archivo} no está en formato canónico`);
  }
});

test('todo el texto visible de los recorridos del repo cumple las reglas de escritura', () => {
  const archivos = readdirSync(DIR_RECORRIDOS).filter((f) => f.endsWith('.yaml'));
  assert.ok(archivos.length > 0, 'no hay recorridos que revisar');
  // Se acumulan todos los incumplimientos y se afirma una sola vez: si no, se arregla
  // uno y hay que volver a correr las pruebas para ver el siguiente.
  const problemas = [];
  for (const archivo of archivos) {
    const rec = parsearRecorrido(readFileSync(join(DIR_RECORRIDOS, archivo), 'utf8'));
    problemas.push(...revisarEscritura(rec.titulo, `${archivo} · titulo`, 160));
    for (const paso of rec.pasos) {
      problemas.push(...revisarEscritura(paso.texto, `${archivo} · ${paso.visual} · texto`));
      if (paso.credito) problemas.push(...revisarEscritura(paso.credito, `${archivo} · ${paso.visual} · credito`, 160));
    }
  }
  assert.deepEqual(problemas, []);
});

test('las imágenes que nombran los recorridos del repo existen de verdad', () => {
  const faltan = [];
  for (const archivo of readdirSync(DIR_RECORRIDOS).filter((f) => f.endsWith('.yaml'))) {
    const rec = parsearRecorrido(readFileSync(join(DIR_RECORRIDOS, archivo), 'utf8'));
    for (const paso of rec.pasos) {
      if (paso.imagen && !existsSync(join(RAIZ, 'public', paso.imagen.replace(/^\//, '')))) {
        faltan.push(`${archivo} · ${paso.visual}: falta public${paso.imagen}`);
      }
    }
  }
  assert.deepEqual(faltan, []);
});

test('cada paso animado del repo tiene escena en su componente', () => {
  // El build solo detecta el sentido "el componente pide un paso que ya no existe".
  // El inverso, un paso sin escena, se queda con el escenario anterior congelado y no
  // lo ve nadie. Esta prueba mira los dos sentidos, y sin arrancar Astro.
  const componentes = readdirSync(DIR_COMPONENTES)
    .filter((f) => f.startsWith('Scrolly') && f !== 'ScrollyShell.astro')
    .map((f) => ({ archivo: f, fuente: readFileSync(join(DIR_COMPONENTES, f), 'utf8') }));

  const problemas = [];
  for (const archivo of readdirSync(DIR_RECORRIDOS).filter((f) => f.endsWith('.yaml'))) {
    const id = archivo.replace(/\.yaml$/, '');
    const comp = componentes.find((c) => c.fuente.includes(`getEntry('recorridos', '${id}')`));
    assert.ok(comp, `ningún componente carga el recorrido "${id}"`);

    const rec = parsearRecorrido(readFileSync(join(DIR_RECORRIDOS, archivo), 'utf8'));
    const visuales = new Set(rec.pasos.map((p) => p.visual));

    // Todo v('x') del componente tiene que existir como paso.
    for (const [, clave] of comp.fuente.matchAll(/v\('([^']+)'\)/g)) {
      if (!visuales.has(clave)) problemas.push(`${comp.archivo}: pide el paso "${clave}", que no está en ${archivo}`);
    }
    // Y todo paso de gráfico animado tiene que estar nombrado en el componente.
    for (const paso of rec.pasos) {
      if (paso.tipo !== 'svg') continue;
      if (!comp.fuente.includes(`v('${paso.visual}')`)) {
        problemas.push(`${archivo}: el paso "${paso.visual}" es de gráfico animado y ${comp.archivo} no lo engancha con v('${paso.visual}')`);
      }
    }
  }
  assert.deepEqual(problemas, []);
});

test('un recorrido mal formado se rechaza con un mensaje que dice qué falta', () => {
  assert.throws(() => parsearRecorrido('pasos: []'), /capsula/);
  assert.throws(() => parsearRecorrido('capsula: "a"\ntitulo: "b"\npasos: []'), /no tiene pasos/);
  assert.throws(() => parsearRecorrido('capsula: "a"\ntitulo: "b"\npasos:\n  - visual: "x"\n    pos: "center"\n    tipo: "svg"'), /"texto"/);
  assert.throws(
    () => parsearRecorrido('capsula: "a"\ntitulo: "b"\npasos:\n  - {visual: "x", pos: "arriba", tipo: "svg", texto: "t"}'),
    /pos "arriba"/,
  );
  assert.throws(
    () => parsearRecorrido('capsula: "a"\ntitulo: "b"\npasos:\n  - {visual: "x", pos: "center", tipo: "video", texto: "t"}'),
    /tipo "video"/,
  );
  assert.throws(
    () => parsearRecorrido('capsula: "a"\ntitulo: "b"\npasos:\n  - {visual: "x", pos: "center", tipo: "svg", texto: "t"}\n  - {visual: "x", pos: "left", tipo: "svg", texto: "u"}'),
    /repetida/,
  );
});

test('las reglas de escritura valen para cualquier texto visible', () => {
  assert.deepEqual(revisarEscritura('Un texto correcto.', 'x'), []);
  assert.equal(revisarEscritura('', 'x').length, 1);
  assert.ok(revisarEscritura('Con raya — larga', 'x').some((p) => /raya larga/.test(p)));
  assert.ok(revisarEscritura('Sede QRO', 'x').some((p) => /Querétaro/.test(p)));
  assert.ok(revisarEscritura('x'.repeat(50), 'x', 40).some((p) => /máximo es 40/.test(p)));
});

test('un crédito con raya larga o con QRO se rechaza como el texto', () => {
  const conRaya = aplicarFicha(recorridoBase(), fichaCon({ 1: { credito: 'Foto: alguien — CC BY' } }), siempreExiste);
  assert.equal(conRaya.recorrido, null);
  assert.ok(conRaya.problemas.some((p) => /crédito.*raya larga/.test(p)));

  const conQro = aplicarFicha(recorridoBase(), fichaCon({ 1: { credito: 'Foto: CentroGeo QRO (CC BY)' } }), siempreExiste);
  assert.equal(conQro.recorrido, null);
  assert.ok(conQro.problemas.some((p) => /Querétaro/.test(p)));
});

test('el recorrido rechaza un paso de foto sin imagen o sin crédito', () => {
  const base = 'capsula: "a"\ntitulo: "b"\npasos:\n  - ';
  assert.throws(() => parsearRecorrido(base + '{visual: "x", pos: "center", tipo: "foto", texto: "t"}'), /no tiene imagen/);
  assert.throws(() => parsearRecorrido(base + '{visual: "x", pos: "center", tipo: "svg", imagen: "/a.jpg", credito: "c", texto: "t"}'), /no admite imagen/);
  assert.throws(() => parsearRecorrido(base + '{visual: "x", pos: "center", tipo: "foto", imagen: "/a.jpg", texto: "t"}'), /sin crédito/);
});

// ----------------------------------------------------------------- normalizar

test('normalizarTexto junta los saltos y espacios que trae una hoja de cálculo', () => {
  assert.equal(normalizarTexto('  hola\n  mundo  '), 'hola mundo');
  assert.equal(normalizarTexto(undefined), '');
});

// --------------------------------------------------------------- aplicarFicha

test('una ficha sin tocar no produce ningún cambio', () => {
  const rec = recorridoBase();
  const { recorrido, cambios, problemas } = aplicarFicha(rec, fichaCon(), siempreExiste);
  assert.deepEqual(problemas, []);
  assert.deepEqual(cambios, []);
  assert.deepEqual(recorrido, rec);
});

test('una corrección de texto se detecta y se aplica', () => {
  const { recorrido, cambios, problemas } = aplicarFicha(recorridoBase(), fichaCon({ 2: { texto: 'Segundo paso, corregido.' } }), siempreExiste);
  assert.deepEqual(problemas, []);
  assert.equal(cambios.length, 1);
  assert.deepEqual(cambios[0], { paso: 2, visual: 'dato', campo: 'texto', antes: 'Segundo paso.', despues: 'Segundo paso, corregido.' });
  assert.equal(recorrido.pasos[1].texto, 'Segundo paso, corregido.');
  assert.equal(recorrido.pasos[0].texto, 'Primer paso.');
});

test('el lado de una figura se conserva aunque no viaje en la ficha', () => {
  const { recorrido } = aplicarFicha(recorridoBase(), fichaCon({ 3: { texto: 'Otro texto.' } }), siempreExiste);
  assert.equal(recorrido.pasos[2].imagenLado, 'der');
});

test('el texto se rechaza si está vacío, lleva raya larga, dice QRO o no cabe', () => {
  const casos = [
    [{ texto: '   ' }, /quedó vacío/],
    [{ texto: 'Una frase con raya — larga.' }, /raya larga/],
    [{ texto: 'Sede de CentroGeo QRO.' }, /Querétaro/],
    [{ texto: 'x'.repeat(LIMITE_TEXTO + 1) }, /máximo/],
  ];
  for (const [cambio, patron] of casos) {
    const { recorrido, problemas } = aplicarFicha(recorridoBase(), fichaCon({ 2: cambio }), siempreExiste);
    assert.equal(recorrido, null);
    assert.ok(problemas.some((p) => patron.test(p)), `esperaba ${patron} y llegó ${JSON.stringify(problemas)}`);
  }
});

test('las columnas que amarran el paso con su gráfico no se pueden cambiar', () => {
  for (const campo of ['visual', 'pos', 'tipo']) {
    const valor = campo === 'visual' ? 'otro' : campo === 'pos' ? 'left' : 'foto';
    const { recorrido, problemas } = aplicarFicha(recorridoBase(), fichaCon({ 2: { [campo]: valor } }), siempreExiste);
    assert.equal(recorrido, null);
    assert.ok(problemas.some((p) => p.includes(`"${campo}"`)), `${campo}: ${JSON.stringify(problemas)}`);
  }
});

test('no se pueden añadir ni quitar pasos desde la ficha', () => {
  const conMas = fichaCon();
  conMas.push(['4', 'nuevo', 'left', 'svg', 'Paso inventado.', '', '', '']);
  assert.match(aplicarFicha(recorridoBase(), conMas, siempreExiste).problemas[0], /4 pasos y el recorrido tiene 3/);

  const conMenos = fichaCon().slice(0, 3);
  assert.match(aplicarFicha(recorridoBase(), conMenos, siempreExiste).problemas[0], /2 pasos y el recorrido tiene 3/);
});

test('las filas vacías del final de la hoja no cuentan como pasos', () => {
  const filas = fichaCon();
  filas.push(['', '', '', '', '', '', '', '']);
  filas.push(['', '', '', '', '', '', '', '']);
  const { problemas, cambios } = aplicarFicha(recorridoBase(), filas, siempreExiste);
  assert.deepEqual(problemas, []);
  assert.deepEqual(cambios, []);
});

test('si alguien reordena o renombra las columnas, la ficha se rechaza entera', () => {
  const filas = fichaCon();
  filas[0] = ['paso', 'visual', 'pos', 'tipo', 'imagen', 'texto', 'credito', 'comentarios'];
  const { recorrido, problemas } = aplicarFicha(recorridoBase(), filas, siempreExiste);
  assert.equal(recorrido, null);
  assert.equal(problemas.length, 1);
  assert.match(problemas[0], /encabezado/);
});

test('toda imagen necesita ruta del sitio, archivo en el repo y crédito', () => {
  // El paso 1 es de foto: el único problema posible aquí es el crédito que falta.
  const sinCredito = aplicarFicha(recorridoBase(), fichaCon({ 1: { credito: '' } }), siempreExiste);
  assert.equal(sinCredito.recorrido, null);
  assert.equal(sinCredito.problemas.length, 1);
  assert.match(sinCredito.problemas[0], /crédito/);

  const rutaRara = aplicarFicha(recorridoBase(), fichaCon({ 1: { imagen: 'scrolly/a.jpg' } }), siempreExiste);
  assert.equal(rutaRara.recorrido, null);
  assert.ok(rutaRara.problemas.some((p) => /no es una ruta válida/.test(p)));

  const noExiste = aplicarFicha(recorridoBase(), fichaCon({ 1: { imagen: '/scrolly/fantasma.jpg' } }), () => false);
  assert.equal(noExiste.recorrido, null);
  assert.ok(noExiste.problemas.some((p) => /no está en el repositorio/.test(p)));
});

test('el tipo de paso manda sobre la imagen: ni de más ni de menos', () => {
  const svgConImagen = aplicarFicha(recorridoBase(), fichaCon({ 2: { imagen: '/scrolly/a.jpg', credito: 'Foto: x (CC BY)' } }), siempreExiste);
  assert.equal(svgConImagen.recorrido, null);
  assert.ok(svgConImagen.problemas.some((p) => /no admite imagen/.test(p)));

  const fotoSinImagen = aplicarFicha(recorridoBase(), fichaCon({ 1: { imagen: '', credito: '' } }), siempreExiste);
  assert.equal(fotoSinImagen.recorrido, null);
  assert.ok(fotoSinImagen.problemas.some((p) => /se quedó sin imagen/.test(p)));
});

test('con un solo problema no se aplica nada, ni siquiera los cambios buenos', () => {
  const filas = fichaCon({ 1: { texto: 'Un primer paso mejor escrito.' }, 2: { texto: 'Con raya — larga.' } });
  const { recorrido, cambios, problemas } = aplicarFicha(recorridoBase(), filas, siempreExiste);
  assert.equal(recorrido, null);
  assert.ok(problemas.length > 0);
  assert.ok(cambios.some((c) => c.paso === 1), 'el cambio bueno sí se reporta, pero no se escribe');
});

test('el ruido de espacios de la hoja no cuenta como corrección', () => {
  const { cambios, problemas } = aplicarFicha(recorridoBase(), fichaCon({ 2: { texto: '  Segundo   paso.  ' } }), siempreExiste);
  assert.deepEqual(problemas, []);
  assert.deepEqual(cambios, []);
});

test('un texto con saltos de línea llega limpio al recorrido', () => {
  const { recorrido, cambios } = aplicarFicha(recorridoBase(), fichaCon({ 2: { texto: 'Segundo paso,\n  ahora en dos renglones.' } }), siempreExiste);
  assert.equal(cambios.length, 1);
  assert.equal(recorrido.pasos[1].texto, 'Segundo paso, ahora en dos renglones.');
});


// ------------------------------------------- huecos que encontró la auditoría de pruebas

test('la ficha exportada tiene exactamente las columnas de la plantilla y numera desde 1', () => {
  const rec = recorridoBase();
  const filas = recorridoAFicha(rec);
  assert.deepEqual(filas[0], COLUMNAS);
  assert.equal(filas.length, rec.pasos.length + 1);
  filas.forEach((fila) => assert.equal(fila.length, COLUMNAS.length, 'toda fila tiene tantas celdas como columnas'));
  assert.deepEqual(filas.slice(1).map((f) => f[COLUMNAS.indexOf('paso')]), ['1', '2', '3']);
  assert.ok(COLUMNAS.includes('comentarios'), 'la columna por la que el autor pide cosas debe existir');
  // La columna de comentarios sale vacía, lista para que el autor escriba en ella.
  filas.slice(1).forEach((f) => assert.equal(f[COLUMNAS.indexOf('comentarios')], ''));
});

test('las columnas editables y las bloqueadas son las que dice la documentación', () => {
  assert.deepEqual(CAMPOS_EDITABLES, ['texto', 'imagen', 'credito']);
  assert.deepEqual(CAMPOS_BLOQUEADOS, ['visual', 'pos', 'tipo']);
});

test('una ficha con una columna de más se rechaza entera', () => {
  const filas = fichaCon();
  filas[0] = [...COLUMNAS, 'notas'];
  const { recorrido, problemas } = aplicarFicha(recorridoBase(), filas, siempreExiste);
  assert.equal(recorrido, null);
  assert.equal(problemas.length, 1);
  assert.match(problemas[0], /encabezado/);
});

test('una ficha vacía da un mensaje, no un tropiezo', () => {
  const { recorrido, problemas } = aplicarFicha(recorridoBase(), [], siempreExiste);
  assert.equal(recorrido, null);
  assert.match(problemas[0], /vacía/);
});

test('el recorrido rechaza un titulo ausente y un imagenLado inventado', () => {
  assert.throws(
    () => parsearRecorrido('capsula: "a"\npasos:\n  - {visual: "x", pos: "center", tipo: "svg", texto: "t"}'),
    /titulo/,
  );
  assert.throws(
    () => parsearRecorrido('capsula: "a"\ntitulo: "b"\npasos:\n  - {visual: "x", pos: "center", tipo: "foto", imagen: "/a.jpg", imagenLado: "arriba", texto: "t"}'),
    /imagenLado "arriba"/,
  );
  // imagenLado solo coloca figuras a un costado: en una foto a sangre no significa nada.
  assert.throws(
    () => parsearRecorrido('capsula: "a"\ntitulo: "b"\npasos:\n  - {visual: "x", pos: "center", tipo: "foto", imagen: "/a.jpg", imagenLado: "izq", texto: "t"}'),
    /solo aplica a las figuras/,
  );
});

// --------------------------------------- huecos que encontró la auditoría de seguridad

test('un carácter de control pegado en la hoja no rompe el archivo del recorrido', () => {
  const sucio = 'Texto con escape \x1b[31m y un nulo \x00 dentro.';
  const { recorrido, problemas } = aplicarFicha(recorridoBase(), fichaCon({ 2: { texto: sucio } }), siempreExiste);
  assert.deepEqual(problemas, []);
  assert.ok(!/[\x00-\x1f\x7f]/.test(recorrido.pasos[1].texto), 'el texto guardado ya no tiene caracteres de control');
  // Y lo escrito se vuelve a leer igual: es lo que impide dejar el YAML ilegible.
  assert.deepEqual(parsearRecorrido(serializarRecorrido(recorrido)), recorrido);
});

test('serializar verifica el ida y vuelta y se niega a entregar algo ilegible', () => {
  const rec = recorridoBase();
  assert.equal(serializarRecorridoVerificado(rec), serializarRecorrido(rec));
  const roto = recorridoBase();
  roto.pasos[1].pos = 'arriba';
  assert.throws(() => serializarRecorridoVerificado(roto), /no se puede volver a leer/);
});

test('la ruta de una imagen no puede escaparse de la carpeta del sitio', () => {
  for (const buena of ['/scrolly/a.jpg', '/investigadores/foto.png', '/a/b/c.webp']) {
    assert.ok(rutaDeImagenValida(buena), buena);
  }
  for (const mala of ['/../secreto.txt', '/scrolly/../../etc/passwd', '//evil.com/x.jpg', '/a//b.jpg', '/a/./b.jpg', 'scrolly/a.jpg', '/a\\b.jpg', '', '/']) {
    assert.ok(!rutaDeImagenValida(mala), `debería rechazar ${JSON.stringify(mala)}`);
  }
  const conSalto = aplicarFicha(recorridoBase(), fichaCon({ 1: { imagen: '/../../../../etc/passwd' } }), siempreExiste);
  assert.equal(conSalto.recorrido, null);
  assert.ok(conSalto.problemas.some((p) => /no es una ruta válida/.test(p)));
});
