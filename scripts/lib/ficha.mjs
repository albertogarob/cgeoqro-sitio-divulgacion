// Biblioteca de la "ficha de recorrido": el puente entre los archivos de recorrido
// (YAML, la fuente de verdad del sitio) y la hoja de cálculo que revisan los autores.
//
// Los autores SOLO corrigen: pueden cambiar el texto de un paso, su imagen y el
// crédito de la imagen. No pueden añadir, quitar ni reordenar pasos, ni tocar las
// columnas que amarran cada paso con su escena visual (visual, pos, tipo).
//
// Todo lo que hay aquí son funciones puras (salvo el parseo de YAML): la comprobación
// de que una imagen existe en disco se inyecta desde fuera para poder probarlas.
import yaml from 'js-yaml';

export const COLUMNAS = ['paso', 'visual', 'pos', 'tipo', 'texto', 'imagen', 'credito', 'comentarios'];
export const CAMPOS_EDITABLES = ['texto', 'imagen', 'credito'];
export const CAMPOS_BLOQUEADOS = ['visual', 'pos', 'tipo'];
export const LIMITE_TEXTO = 420;

/**
 * Reglas de escritura del sitio (ver CLAUDE.md), aplicables a cualquier texto visible:
 * el subtítulo de un paso, el título del recorrido o el crédito de una imagen.
 * Devuelve la lista de problemas encontrados, vacía si está limpio.
 */
export function revisarEscritura(texto, etiqueta, limite = LIMITE_TEXTO) {
  const problemas = [];
  if (!texto) {
    problemas.push(`${etiqueta}: quedó vacío.`);
    return problemas;
  }
  if (texto.includes('—')) problemas.push(`${etiqueta}: usa una raya larga. Usa comas, puntos o reescribe la frase.`);
  if (/\bqro\b/i.test(texto)) problemas.push(`${etiqueta}: dice "QRO". Escribe siempre "Querétaro".`);
  if (texto.length > limite) problemas.push(`${etiqueta}: tiene ${texto.length} caracteres y el máximo es ${limite}.`);
  return problemas;
}

const POSICIONES = ['left', 'right', 'center'];
const TIPOS = ['foto', 'figura', 'svg'];
const LADOS = ['izq', 'der'];
// Orden fijo de las claves al escribir un paso, para que el YAML sea estable.
const ORDEN_PASO = ['visual', 'pos', 'tipo', 'imagen', 'imagenLado', 'credito', 'texto'];

export const CABECERA_YAML = `# Recorrido de scrollytelling. Esta es la fuente de verdad del texto del relato.
# Lo editan los autores a través de la ficha en Drive, no a mano:
#   npm run ficha:exportar -- <recorrido>
#   npm run ficha:importar -- <recorrido> <ficha.csv>
# "visual" amarra cada paso con su escena en el componente Astro: no se cambia,
# no se reordena y no se borra sin tocar también el componente.
`;

// ---------------------------------------------------------------- CSV (RFC 4180)

/** Convierte una matriz de celdas en texto CSV. */
export function generarCsv(filas) {
  return filas.map((fila) => fila.map(celdaCsv).join(',')).join('\r\n') + '\r\n';
}

function celdaCsv(valor) {
  const s = valor === undefined || valor === null ? '' : String(valor);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

/**
 * Parsea texto CSV a una matriz de celdas. Acepta BOM, saltos CRLF o LF, comillas
 * dobles escapadas y saltos de línea dentro de una celda entrecomillada.
 */
export function parsearCsv(texto) {
  const src = texto.replace(/^﻿/, '');
  const filas = [];
  let fila = [];
  let celda = '';
  let entreComillas = false;
  let i = 0;
  let huboCelda = false;

  const cerrarCelda = () => { fila.push(celda); celda = ''; huboCelda = false; };
  const cerrarFila = () => { cerrarCelda(); filas.push(fila); fila = []; };

  while (i < src.length) {
    const c = src[i];
    if (entreComillas) {
      if (c === '"') {
        if (src[i + 1] === '"') { celda += '"'; i += 2; continue; }
        entreComillas = false; i++; continue;
      }
      celda += c; i++; continue;
    }
    if (c === '"') {
      if (celda !== '') throw new Error(`CSV mal formado: comilla en medio de una celda (posición ${i}).`);
      entreComillas = true; huboCelda = true; i++; continue;
    }
    if (c === ',') { cerrarCelda(); huboCelda = true; i++; continue; }
    if (c === '\r' || c === '\n') {
      const salto = c === '\r' && src[i + 1] === '\n' ? 2 : 1;
      cerrarFila(); i += salto; continue;
    }
    celda += c; huboCelda = true; i++;
  }
  if (entreComillas) throw new Error('CSV mal formado: se abrió una comilla que nunca se cerró.');
  // Una última celda pendiente (archivo sin salto final) sí cuenta; un salto final no
  // debe producir una fila vacía de más.
  if (huboCelda || celda !== '' || fila.length > 0) cerrarFila();
  return filas;
}

// ------------------------------------------------------------------------ YAML

/** Lee y valida un archivo de recorrido. Lanza si el archivo no cumple el formato. */
export function parsearRecorrido(texto) {
  const datos = yaml.load(texto);
  if (!datos || typeof datos !== 'object' || Array.isArray(datos)) {
    throw new Error('El recorrido debe ser un objeto YAML con las claves capsula, titulo y pasos.');
  }
  if (typeof datos.capsula !== 'string' || !datos.capsula) throw new Error('Falta "capsula" en el recorrido.');
  if (typeof datos.titulo !== 'string' || !datos.titulo) throw new Error('Falta "titulo" en el recorrido.');
  if (!Array.isArray(datos.pasos) || datos.pasos.length === 0) throw new Error('El recorrido no tiene pasos.');

  const vistos = new Set();
  const pasos = datos.pasos.map((p, i) => {
    const n = i + 1;
    if (!p || typeof p !== 'object' || Array.isArray(p)) throw new Error(`El paso ${n} no es un objeto.`);
    for (const campo of ['visual', 'pos', 'tipo', 'texto']) {
      if (typeof p[campo] !== 'string' || !p[campo].trim()) throw new Error(`El paso ${n} no tiene "${campo}".`);
    }
    if (vistos.has(p.visual)) throw new Error(`La clave visual "${p.visual}" está repetida (paso ${n}).`);
    vistos.add(p.visual);
    if (!POSICIONES.includes(p.pos)) throw new Error(`El paso ${n} tiene pos "${p.pos}"; debe ser ${POSICIONES.join(', ')}.`);
    if (!TIPOS.includes(p.tipo)) throw new Error(`El paso ${n} tiene tipo "${p.tipo}"; debe ser ${TIPOS.join(', ')}.`);
    if (p.imagenLado !== undefined && !LADOS.includes(p.imagenLado)) {
      throw new Error(`El paso ${n} tiene imagenLado "${p.imagenLado}"; debe ser ${LADOS.join(' o ')}.`);
    }
    if (p.imagenLado !== undefined && p.tipo !== 'figura') {
      throw new Error(`El paso ${n} es de tipo "${p.tipo}" y no usa imagenLado: ese campo solo aplica a las figuras a un costado.`);
    }
    // La regla de imagen y crédito no puede vivir solo en el importador: un YAML
    // editado a mano la esquivaría y el escenario saldría en blanco.
    if (p.tipo !== 'svg' && !p.imagen) {
      throw new Error(`El paso ${n} es de tipo "${p.tipo}" y no tiene imagen.`);
    }
    if (p.tipo === 'svg' && p.imagen) {
      throw new Error(`El paso ${n} es de tipo "svg" y no admite imagen.`);
    }
    if (p.imagen && !p.credito) {
      throw new Error(`El paso ${n} tiene imagen sin crédito ni licencia.`);
    }
    const paso = { visual: p.visual, pos: p.pos, tipo: p.tipo, texto: p.texto };
    if (p.imagen) paso.imagen = p.imagen;
    if (p.imagenLado) paso.imagenLado = p.imagenLado;
    if (p.credito) paso.credito = p.credito;
    return paso;
  });
  return { capsula: datos.capsula, titulo: datos.titulo, pasos };
}

/** Escribe un recorrido en el formato canónico (el mismo que produce el importador). */
export function serializarRecorrido(rec) {
  const lineas = [CABECERA_YAML.trimEnd(), '', `capsula: ${escalar(rec.capsula)}`, `titulo: ${escalar(rec.titulo)}`, 'pasos:'];
  for (const paso of rec.pasos) {
    let primera = true;
    for (const clave of ORDEN_PASO) {
      const valor = paso[clave];
      if (valor === undefined || valor === null || valor === '') continue;
      lineas.push(`${primera ? '  - ' : '    '}${clave}: ${escalar(valor)}`);
      primera = false;
    }
  }
  return lineas.join('\n') + '\n';
}

// Los escalares YAML entre comillas dobles no admiten caracteres de control literales:
// uno solo (un \x1b pegado desde un PDF) deja el archivo ilegible. Se escapan siempre,
// además de limpiarlos antes en normalizarTexto.
function escalar(valor) {
  const escapado = String(valor)
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/[\x00-\x1f\x7f]/g, (c) => '\\x' + c.charCodeAt(0).toString(16).padStart(2, '0'));
  return '"' + escapado + '"';
}

/**
 * Serializa comprobando que lo escrito se puede volver a leer y da el mismo recorrido.
 * Es la última red antes de pisar el archivo bueno: si algo no cuadra, lanza en vez de
 * dejar en disco un recorrido que ni Astro ni este script pueden abrir.
 */
export function serializarRecorridoVerificado(rec) {
  const texto = serializarRecorrido(rec);
  let releido;
  try {
    releido = parsearRecorrido(texto);
  } catch (e) {
    throw new Error(`El recorrido serializado no se puede volver a leer: ${e.message}`);
  }
  // Se comparan las dos serializaciones, no los objetos: así la comprobación no depende
  // del orden en que cada uno trajera sus claves.
  if (serializarRecorrido(releido) !== texto) {
    throw new Error('El recorrido serializado no coincide con el original. No se escribe nada.');
  }
  return texto;
}

// --------------------------------------------------------------- ficha <-> YAML

/** Matriz de la ficha (encabezado + una fila por paso) a partir de un recorrido. */
export function recorridoAFicha(rec) {
  const filas = [COLUMNAS.slice()];
  rec.pasos.forEach((p, i) => {
    filas.push([String(i + 1), p.visual, p.pos, p.tipo, p.texto, p.imagen ?? '', p.credito ?? '', '']);
  });
  return filas;
}

/**
 * Normaliza un texto de celda: sin caracteres de control (los arrastran los pegados
 * desde un PDF o un terminal, y rompen el YAML), sin saltos de línea, sin espacios
 * dobles ni al borde.
 */
export function normalizarTexto(valor) {
  return String(valor ?? '')
    .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Comprueba que la ruta de una imagen es del sitio y no se escapa de la carpeta
 * pública: una sola barra inicial (dos serían otro dominio), sin segmentos "..", sin
 * barras invertidas ni caracteres raros.
 */
export function rutaDeImagenValida(ruta) {
  if (typeof ruta !== 'string' || !ruta.startsWith('/') || ruta.startsWith('//')) return false;
  if (ruta.includes('\\') || ruta.includes('\0')) return false;
  const partes = ruta.slice(1).split('/');
  if (partes.some((p) => p === '' || p === '.' || p === '..')) return false;
  return true;
}

/**
 * Aplica una ficha editada sobre el recorrido original.
 *
 * Devuelve { recorrido, cambios, problemas }. Si hay problemas, `recorrido` es null:
 * una ficha con errores no se aplica a medias.
 *
 * @param {object} rec recorrido original (fuente de verdad)
 * @param {string[][]} filas matriz de la ficha editada, con encabezado
 * @param {(ruta: string) => boolean} existeImagen comprobación de que la imagen está en el repo
 */
export function aplicarFicha(rec, filas, existeImagen = () => true) {
  const problemas = [];
  const cambios = [];
  if (!filas.length) return { recorrido: null, cambios, problemas: ['La ficha está vacía.'] };

  const encabezado = filas[0].map((c) => normalizarTexto(c).toLowerCase());
  if (encabezado.length !== COLUMNAS.length || COLUMNAS.some((c, i) => encabezado[i] !== c)) {
    problemas.push(`El encabezado de la ficha cambió. Debe ser exactamente: ${COLUMNAS.join(', ')}.`);
    return { recorrido: null, cambios, problemas };
  }

  const cuerpo = filas.slice(1).filter((f) => f.some((c) => normalizarTexto(c) !== ''));
  if (cuerpo.length !== rec.pasos.length) {
    problemas.push(
      `La ficha trae ${cuerpo.length} pasos y el recorrido tiene ${rec.pasos.length}. ` +
      'Los autores corrigen pasos, no los añaden ni los quitan: si hace falta un paso nuevo, pídelo en la columna de comentarios.'
    );
    return { recorrido: null, cambios, problemas };
  }

  const pasos = [];
  cuerpo.forEach((fila, i) => {
    const original = rec.pasos[i];
    const n = i + 1;
    const celda = (nombre) => normalizarTexto(fila[COLUMNAS.indexOf(nombre)]);

    for (const campo of CAMPOS_BLOQUEADOS) {
      if (celda(campo) !== original[campo]) {
        problemas.push(`Paso ${n}: la columna "${campo}" no se puede cambiar (decía "${original[campo]}", llegó "${celda(campo)}").`);
      }
    }

    const texto = celda('texto');
    const imagen = celda('imagen');
    const credito = celda('credito');

    problemas.push(...revisarEscritura(texto, `Paso ${n}: el texto`));
    // El crédito también es texto visible, encima de la foto.
    if (credito) problemas.push(...revisarEscritura(credito, `Paso ${n}: el crédito`, 160));

    if (imagen && !rutaDeImagenValida(imagen)) {
      problemas.push(
        `Paso ${n}: la imagen "${imagen}" no es una ruta válida del sitio. Debe empezar con una sola "/" ` +
        'y quedarse dentro de la carpeta de imágenes, por ejemplo /scrolly/mi-foto.jpg.'
      );
    } else if (imagen && !existeImagen(imagen)) {
      problemas.push(`Paso ${n}: la imagen "${imagen}" no está en el repositorio. Súbela a public${imagen} antes de importar la ficha.`);
    }
    if (imagen && !credito) {
      problemas.push(`Paso ${n}: toda imagen lleva crédito y licencia. Sin eso no se publica.`);
    }
    if (!imagen && original.tipo !== 'svg') {
      problemas.push(`Paso ${n}: este paso es de tipo "${original.tipo}" y se quedó sin imagen.`);
    }
    if (imagen && original.tipo === 'svg') {
      problemas.push(`Paso ${n}: este paso es de gráfico animado (tipo "svg") y no admite imagen. Pídelo en la columna de comentarios.`);
    }

    const nuevo = { visual: original.visual, pos: original.pos, tipo: original.tipo, texto };
    if (imagen) nuevo.imagen = imagen;
    if (original.imagenLado) nuevo.imagenLado = original.imagenLado;
    if (credito) nuevo.credito = credito;
    pasos.push(nuevo);

    for (const campo of CAMPOS_EDITABLES) {
      const antes = original[campo] ?? '';
      const despues = nuevo[campo] ?? '';
      if (antes !== despues) cambios.push({ paso: n, visual: original.visual, campo, antes, despues });
    }
  });

  if (problemas.length) return { recorrido: null, cambios, problemas };
  return { recorrido: { capsula: rec.capsula, titulo: rec.titulo, pasos }, cambios, problemas };
}
