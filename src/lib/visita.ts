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

/** Caja de un elemento, con lo que hace falta para decidir si se ve. */
export interface Caja {
  top: number;
  bottom: number;
  height: number;
}

/**
 * Si hay que desplazar la página para ver lo que se acaba de resaltar.
 *
 * No basta con preguntar si está fuera de pantalla: lo que importa es cuánto de ello
 * se ve. Un bloque más alto que la ventana nunca cabe entero, así que se mide contra
 * lo que la ventana puede enseñar, no contra el tamaño del bloque.
 *
 * Y se mide para no mover la página cuando no hace falta: dentro del recorrido, la
 * banda de mandos y el crédito de la foto están siempre a la vista, y desplazarse ahí
 * se pelearía con el motor del recorrido, que lleva su propio scroll.
 */
export function hayQueAcercarse(caja: Caja, alto: number, minimo = 0.55): boolean {
  if (caja.height <= 0 || alto <= 0) return false;
  const visible = Math.max(0, Math.min(caja.bottom, alto) - Math.max(caja.top, 0));
  const alcanzable = Math.min(caja.height, alto);
  return visible / alcanzable < minimo;
}

/** Rectángulo de un elemento resaltado, en coordenadas de la ventana. */
export interface Hueco {
  top: number;
  left: number;
  width: number;
  height: number;
}

/**
 * El camino de la penumbra: la ventana entera menos un agujero por cada cosa resaltada.
 *
 * La penumbra se dibuja UNA vez, con agujeros, y no una por caja. Con una sombra de
 * gran extensión por caja, cada caja oscurecía todo lo que quedaba fuera de ella, o sea
 * también las demás cajas: cuando un selector casaba con cuatro tarjetas, las cuatro
 * resaltadas salían igual de apagadas que el resto de la página. Alberto lo vio en la
 * parada de cápsulas el 29 de octubre de 2026.
 *
 * El camino se interpreta con la regla par e impar, así que los subcaminos de dentro
 * recortan en vez de sumar. Devuelve cadena vacía si la ventana no tiene tamaño, y un
 * camino sin agujeros si ninguno de los que llegan es utilizable: quien lo use decide
 * si en ese caso vale la pena pintar penumbra.
 */
export function caminoDePenumbra(huecos: Hueco[], ancho: number, alto: number): string {
  if (!(ancho > 0) || !(alto > 0)) return '';
  const r = (n: number) => Math.round(n * 10) / 10;
  let d = `M0 0 H${r(ancho)} V${r(alto)} H0 Z`;
  for (const h of huecos) {
    const x0 = r(Math.max(0, h.left));
    const y0 = r(Math.max(0, h.top));
    const x1 = r(Math.min(ancho, h.left + h.width));
    const y1 = r(Math.min(alto, h.top + h.height));
    // Un agujero que la ventana recorta hasta menos de un píxel no se dibuja: el
    // camino quedaría con un subcamino degenerado y la regla par e impar no lo cuenta.
    if (x1 - x0 < 1 || y1 - y0 < 1) continue;
    d += ` M${x0} ${y0} H${x1} V${y1} H${x0} Z`;
  }
  return d;
}

/** Cuántos agujeros tiene un camino de penumbra. Cero significa que no hay nada que recortar. */
export function cuentaDeHuecos(camino: string): number {
  if (!camino) return 0;
  // El primer subcamino es la ventana; los demás son los agujeros.
  return Math.max(0, (camino.match(/M/g) ?? []).length - 1);
}
