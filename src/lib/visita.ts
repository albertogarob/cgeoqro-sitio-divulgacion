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
export function hayQueAcercarse(caja: Caja, alto: number, minimo = 0.55, techo = 0): boolean {
  const banda = alto - techo;
  if (caja.height <= 0 || banda <= 0) return false;
  const visible = Math.max(0, Math.min(caja.bottom, alto) - Math.max(caja.top, techo));
  const alcanzable = Math.min(caja.height, banda);
  return visible / alcanzable < minimo;
}

/**
 * Cuánto hay que desplazar la página para dejar lo resaltado en medio de la banda que
 * de verdad se ve. Positivo es hacia abajo.
 *
 * El `techo` es lo que tapa la cabecera pegada del sitio. Sin descontarlo, centrar en
 * la ventana deja el elemento justo detrás de la barra de navegación cuando el
 * elemento está cerca del principio de la página y no hay scroll de sobra para bajarlo
 * más. Alberto lo vio el 29 de octubre de 2026, con las etiquetas de formato de las
 * tarjetas del catálogo.
 */
export function desplazamientoDeseado(caja: Caja, alto: number, techo = 0): number {
  const banda = alto - techo;
  if (banda <= 0) return 0;
  const hueco = Math.max(0, banda - Math.min(caja.height, banda));
  return Math.round(caja.top - (techo + hueco / 2));
}

/** Rectángulo de un elemento resaltado, en coordenadas de la ventana. */
export interface Hueco {
  top: number;
  left: number;
  width: number;
  height: number;
}

interface Rect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/** Un decimal, que es toda la precisión que necesita un recorte en píxeles. */
const redondo = (n: number) => Math.round(n * 10) / 10;

/**
 * Los huecos, recortados a la ventana y sin los que no dan ni un píxel.
 *
 * Un rectángulo degenerado no abre nada y además ensucia lo que venga detrás, así que
 * se descarta aquí y no en mitad del dibujo.
 */
function huecosUtiles(huecos: Hueco[], ancho: number, alto: number): Rect[] {
  const utiles: Rect[] = [];
  for (const h of huecos) {
    const x0 = redondo(Math.max(0, h.left));
    const y0 = redondo(Math.max(0, h.top));
    const x1 = redondo(Math.min(ancho, h.left + h.width));
    const y1 = redondo(Math.min(alto, h.top + h.height));
    if (!(x1 - x0 >= 1) || !(y1 - y0 >= 1)) continue;
    utiles.push({ x0, y0, x1, y1 });
  }
  return utiles;
}

/**
 * La penumbra, troceada en rectángulos que no se pisan entre sí.
 *
 * Se parte la ventana por todas las coordenadas que aportan los huecos, y de la rejilla
 * resultante se queda lo que no cae dentro de ningún hueco. Después se funden las
 * celdas contiguas de cada franja, para no escribir cien rectángulos donde caben tres.
 *
 * Por qué así y no un rectángulo grande con agujeros recortados: **dos huecos que se
 * solapan, o uno dentro de otro, se cancelan** con la regla par e impar, y la zona
 * común vuelve a quedar tan oscura como el resto, con el contorno rojo alrededor. Es
 * la misma avería que la penumbra venía a arreglar, entrando por otra puerta. Troceada
 * así no hay regla de relleno de la que depender: lo que se pinta es exactamente lo que
 * tiene que quedar oscuro.
 */
export function rectangulosDePenumbra(huecos: Hueco[], ancho: number, alto: number): Rect[] {
  if (!(ancho > 0) || !(alto > 0)) return [];
  const utiles = huecosUtiles(huecos, ancho, alto);
  // Sin un solo hueco que abrir no hay penumbra: oscurecerlo todo marcaría la página
  // entera como "esto no es lo que hay que mirar", que es lo contrario de lo que se
  // quiere decir.
  if (!utiles.length) return [];

  const cortesX = [...new Set([0, redondo(ancho), ...utiles.flatMap((r) => [r.x0, r.x1])])].sort((a, b) => a - b);
  const cortesY = [...new Set([0, redondo(alto), ...utiles.flatMap((r) => [r.y0, r.y1])])].sort((a, b) => a - b);

  const trozos: Rect[] = [];
  for (let j = 0; j < cortesY.length - 1; j++) {
    const y0 = cortesY[j];
    const y1 = cortesY[j + 1];
    if (y1 <= y0) continue;
    let abierto: Rect | null = null;
    for (let i = 0; i < cortesX.length - 1; i++) {
      const x0 = cortesX[i];
      const x1 = cortesX[i + 1];
      if (x1 <= x0) continue;
      const tapada = utiles.some((r) => r.x0 <= x0 && x1 <= r.x1 && r.y0 <= y0 && y1 <= r.y1);
      if (tapada) {
        if (abierto) trozos.push(abierto);
        abierto = null;
        continue;
      }
      // Celda a oscuras: se alarga la franja que ya venía en vez de abrir otra.
      if (abierto && abierto.x1 === x0) abierto.x1 = x1;
      else {
        if (abierto) trozos.push(abierto);
        abierto = { x0, y0, x1, y1 };
      }
    }
    if (abierto) trozos.push(abierto);
  }
  return trozos;
}

/**
 * El camino que recorta la capa de penumbra, en coordenadas de la ventana.
 *
 * Cadena vacía significa que no hay nada que oscurecer, y quien lo use no debe pintar
 * la capa: ni cuando la ventana no tiene tamaño, ni cuando ningún hueco es utilizable.
 * Los subcaminos no se pisan entre sí, así que la regla de relleno da igual.
 */
export function caminoDePenumbra(huecos: Hueco[], ancho: number, alto: number): string {
  const trozos = rectangulosDePenumbra(huecos, ancho, alto);
  if (!trozos.length) return '';
  return trozos.map((r) => `M${r.x0} ${r.y0} H${r.x1} V${r.y1} H${r.x0} Z`).join(' ');
}
