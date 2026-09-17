// Lo que la ficha toca en disco, aparte y probado: comprobar que una imagen está de
// verdad dentro de la carpeta pública, escribir el recorrido sin poder dejarlo a medias
// y no pisar un archivo existente al exportar.
import { existsSync, mkdirSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { serializarRecorridoVerificado } from './ficha.mjs';

/**
 * ¿La imagen existe dentro de <raiz>/public? Confina la ruta: un "/../" en la ficha no
 * puede sacar la comprobación de la carpeta pública ni convertirse en un oráculo de qué
 * archivos hay en la máquina.
 */
export function existeImagenEn(raiz, ruta) {
  const publico = resolve(raiz, 'public');
  const destino = resolve(publico, '.' + ruta);
  const dentro = relative(publico, destino);
  if (dentro === '' || dentro.startsWith('..') || dentro.startsWith(sep) || resolve(publico, dentro) !== destino) {
    return false;
  }
  return existsSync(destino);
}

/**
 * Escribe el recorrido de forma que, o queda entero y legible, o no se toca el archivo
 * bueno: primero se comprueba que lo serializado se vuelve a leer igual, luego se
 * escribe en un temporal al lado y se renombra (el rename es atómico en el mismo
 * sistema de archivos).
 */
export function escribirRecorridoAtomico(ruta, rec) {
  const texto = serializarRecorridoVerificado(rec);
  const temporal = `${ruta}.tmp-${process.pid}`;
  try {
    writeFileSync(temporal, texto, 'utf8');
    renameSync(temporal, ruta);
  } catch (e) {
    rmSync(temporal, { force: true });
    throw e;
  }
  return texto;
}

/**
 * Prepara el destino de una ficha exportada. Se niega a pisar un archivo que ya existe
 * salvo que se lo pidan a propósito: la ficha exportada se manda por ahí y es fácil
 * apuntarla sin querer a un archivo que importa.
 */
export function prepararDestino(destino, { forzar = false } = {}) {
  const absoluto = resolve(destino);
  if (existsSync(absoluto) && !forzar) {
    throw new Error(`${absoluto} ya existe. Borra el archivo, elige otro nombre o añade --forzar.`);
  }
  mkdirSync(dirname(absoluto), { recursive: true });
  return absoluto;
}
