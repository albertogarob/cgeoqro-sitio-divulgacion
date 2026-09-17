#!/usr/bin/env node
// Ficha de recorrido: el ida y vuelta entre el sitio y los autores.
//
//   node scripts/ficha-recorrido.mjs exportar <recorrido> [--salida ruta.csv]
//   node scripts/ficha-recorrido.mjs importar <recorrido> <ficha.csv> [--aplicar]
//
// "exportar" saca una hoja de cálculo con un renglón por paso, que se sube a Drive y
// se comparte con el autor. "importar" trae de vuelta la hoja corregida: comprueba que
// solo cambió lo que el autor puede cambiar, enseña el antes y el después, y solo
// escribe el recorrido si todo está en orden. Ver docs/ficha-recorrido.md.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  aplicarFicha,
  generarCsv,
  parsearCsv,
  parsearRecorrido,
  recorridoAFicha,
} from './lib/ficha.mjs';
import { escribirRecorridoAtomico, existeImagenEn, prepararDestino } from './lib/archivo.mjs';

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DIR_RECORRIDOS = join(RAIZ, 'src', 'content', 'recorridos');
const DIR_FICHAS = join(RAIZ, 'fichas');

function salir(mensaje) {
  console.error(mensaje);
  process.exit(1);
}

function uso() {
  return [
    'Uso:',
    '  node scripts/ficha-recorrido.mjs exportar <recorrido> [--salida ruta.csv] [--forzar]',
    '  node scripts/ficha-recorrido.mjs importar <recorrido> <ficha.csv> [--aplicar]',
    '',
    'Recorridos disponibles: los archivos de src/content/recorridos/ (sin la extensión).',
  ].join('\n');
}

function rutaRecorrido(id) {
  if (!/^[a-z0-9-]+$/.test(id)) salir(`"${id}" no es un nombre de recorrido válido (solo minúsculas, números y guiones).`);
  const ruta = join(DIR_RECORRIDOS, `${id}.yaml`);
  if (!existsSync(ruta)) salir(`No existe el recorrido ${ruta}`);
  return ruta;
}

function leerRecorrido(id) {
  const ruta = rutaRecorrido(id);
  try {
    return { ruta, recorrido: parsearRecorrido(readFileSync(ruta, 'utf8')) };
  } catch (e) {
    return salir(`El recorrido ${ruta} no se pudo leer: ${e.message}`);
  }
}

function opcion(args, nombre) {
  const i = args.indexOf(nombre);
  if (i < 0) return null;
  const valor = args[i + 1];
  if (!valor || valor.startsWith('--')) salir(`Falta el valor de ${nombre}.`);
  return valor;
}

function exportar(args) {
  const id = args[0];
  if (!id || id.startsWith('--')) salir(uso());
  const { recorrido } = leerRecorrido(id);
  const pedido = opcion(args, '--salida') ?? join(DIR_FICHAS, `${id}-ficha.csv`);
  let destino;
  try {
    destino = prepararDestino(pedido, { forzar: args.includes('--forzar') });
  } catch (e) {
    return salir(e.message);
  }
  writeFileSync(destino, generarCsv(recorridoAFicha(recorrido)), 'utf8');
  console.log(`Ficha de "${recorrido.titulo}" (${recorrido.pasos.length} pasos): ${destino}`);
  console.log('Súbela a Drive como hoja de cálculo y compártela con quien va a revisar.');
  console.log('Recuerda: el autor solo corrige texto, imagen y crédito. Las demás columnas se quedan como están.');
}

function importar(args) {
  const [id, fichaRuta] = args;
  if (!id || !fichaRuta || id.startsWith('--') || fichaRuta.startsWith('--')) salir(uso());
  const { ruta, recorrido } = leerRecorrido(id);
  if (!existsSync(fichaRuta)) salir(`No existe la ficha ${fichaRuta}`);

  let filas;
  try {
    filas = parsearCsv(readFileSync(fichaRuta, 'utf8'));
  } catch (e) {
    return salir(`La ficha no se pudo leer: ${e.message}`);
  }

  const existeImagen = (r) => existeImagenEn(RAIZ, r);
  const { recorrido: nuevo, cambios, problemas } = aplicarFicha(recorrido, filas, existeImagen);

  if (cambios.length === 0 && problemas.length === 0) {
    console.log('La ficha no trae ningún cambio. El recorrido se queda como está.');
    return;
  }

  for (const c of cambios) {
    console.log(`\nPaso ${c.paso} (${c.visual}) · ${c.campo}`);
    console.log(`  antes:   ${c.antes || '(vacío)'}`);
    console.log(`  después: ${c.despues || '(vacío)'}`);
  }

  if (problemas.length) {
    console.error(`\n${problemas.length} problema(s) en la ficha. No se aplicó nada:`);
    for (const p of problemas) console.error(`  - ${p}`);
    process.exit(1);
  }

  console.log(`\n${cambios.length} cambio(s) sin problemas.`);
  if (!args.includes('--aplicar')) {
    console.log('Esto fue una revisión en seco. Vuelve a correrlo con --aplicar para escribirlos.');
    return;
  }
  try {
    escribirRecorridoAtomico(ruta, nuevo);
  } catch (e) {
    return salir(`No se escribió nada: ${e.message}`);
  }
  console.log(`Escrito ${ruta}. Corre "npm run build" y revisa el recorrido antes de publicar.`);
}

const [comando, ...args] = process.argv.slice(2);
if (comando === 'exportar') exportar(args);
else if (comando === 'importar') importar(args);
else salir(uso());
