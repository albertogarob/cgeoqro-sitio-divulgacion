// Resaltado a distancia, para la visita guiada.
//
// El sitio se enseña dentro de un iframe en las láminas de la presentación. El deck y
// el sitio viven en orígenes distintos (uno es local y el otro está publicado), así
// que el deck no puede tocar el DOM de aquí: solo puede mandar un mensaje. Esto valida
// ese mensaje y devuelve qué hay que resaltar.
//
// Lo único que el mensaje puede pedir es dibujar un contorno sobre lo que case con un
// selector. No mueve nada, no escribe nada y no lee nada de la página.

/** Clave del mensaje. Un mensaje sin esta clave exacta se ignora entero. */
export const TIPO_RESALTAR = 'visita:resaltar';

/** Tope del selector, para no aceptar una cadena enorme de un remitente cualquiera. */
export const MAX_SELECTOR = 200;

export interface Resaltado {
  /** Lo que hay que resaltar. Cadena vacía significa apagar el resaltado. */
  selector: string;
  /** Si además hay que desplazar la página hasta lo resaltado. */
  acercar: boolean;
}

/**
 * Qué pide un mensaje recibido, o null si no es de los nuestros.
 *
 * Devuelve `selector: ''` cuando el mensaje pide apagar el resaltado, que es distinto
 * de que el mensaje no vaya con nosotros: lo primero se atiende, lo segundo se ignora.
 */
export function peticionDeResaltado(data: unknown): Resaltado | null {
  if (!data || typeof data !== 'object') return null;
  const m = data as Record<string, unknown>;
  if (m.tipo !== TIPO_RESALTAR) return null;

  const crudo = m.selector;
  if (crudo === null || crudo === undefined || crudo === '') return { selector: '', acercar: false };
  if (typeof crudo !== 'string') return null;

  const selector = crudo.trim();
  if (!selector || selector.length > MAX_SELECTOR) return null;
  return { selector, acercar: m.acercar === true };
}
