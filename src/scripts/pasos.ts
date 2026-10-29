// Cuentas de los mandos del recorrido, separadas del motor para poder probarlas sin
// navegador.
//
// Los mandos mueven el scroll en vez de sustituirlo, pero el motor no se limita a
// esperar a que scrollama le diga dónde ha caído: anima el viaje él mismo y aplica el
// paso de destino al terminarlo. Lleva dos cuentas a propósito, el paso que se ve y el
// que se ha pedido, porque hacerlas depender de la confirmación de scrollama perdía
// clics. Lo de aquí son las cuentas puras de todo eso.

/**
 * Paso al que llevan los botones de anterior/siguiente, sin salirse del relato. Con
 * cero pasos devuelve 0, que es lo que ya sale del propio recorte.
 */
export function pasoDestino(actual: number, total: number, delta: number): number {
  return Math.max(0, Math.min(total - 1, actual + delta));
}

/**
 * Cuántas paradas tiene un recorrido: los pasos del relato más la tarjeta de cierre,
 * cuando la página la trae. La tarjeta no es un paso (no tiene gráfico ni la conoce
 * scrollama), pero sí es una parada: los mandos llegan a ella y el contador la cuenta.
 */
export function contarParadas(pasos: number, hayCierre: boolean): number {
  return Math.max(0, pasos) + (hayCierre ? 1 : 0);
}

/** Si una parada es la tarjeta de cierre, que va justo detrás del último paso. */
export function esParadaDeCierre(parada: number, pasos: number, hayCierre: boolean): boolean {
  return hayCierre && parada >= pasos;
}

/** Índice de la última parada. Con cero paradas devuelve 0, no un índice negativo. */
export function ultimaParada(paradas: number): number {
  return Math.max(0, paradas - 1);
}

/** Si una parada es la última del recorrido, donde la reproducción se detiene. */
export function esUltimaParada(parada: number, paradas: number): boolean {
  return parada >= ultimaParada(paradas);
}

/**
 * Qué botones van apagados. Se decide por la parada PEDIDA, no por la que se ve: si
 * dependiera de lo que confirma scrollama, dos clics seguidos contarían como uno.
 */
export function estadoMandos(paradaPedida: number, paradas: number): {
  atrasApagado: boolean;
  adelanteApagado: boolean;
} {
  return {
    atrasApagado: paradaPedida <= 0,
    adelanteApagado: esUltimaParada(paradaPedida, paradas),
  };
}

export interface ObjetivoScroll {
  /** Distancia del borde superior del paso al inicio del documento. */
  topAbs: number;
  /** Scroll máximo posible del documento, para no pedir lo imposible. */
  maxScroll?: number;
}

/**
 * Posición de scroll a la que lleva un salto al paso cuyo borde superior está en
 * `topAbs`: la que deja la caja del paso ocupando la pantalla entera.
 *
 * El destino NO es la línea de disparo de scrollama. Ahí el paso ya cuenta como
 * activo, pero su subtítulo todavía está por debajo del pliegue: los pasos miden una
 * pantalla de alto y el texto va centrado en ellos, así que apuntar a la línea de
 * disparo dejaba el gráfico cambiado y el texto sin ver, media pantalla más abajo. Esa
 * era la sensación de "salta y se queda en un punto intermedio".
 *
 * Dejar el paso cuadrado con la ventana cumple las dos cosas a la vez: el subtítulo
 * queda donde la hoja de estilos lo coloque dentro del paso, y el borde superior del
 * paso queda muy por encima de la línea de disparo, mientras que el del paso siguiente
 * queda por debajo (una pantalla más abajo, y la línea está como mucho a tres cuartos).
 */
export function objetivoScroll({ topAbs, maxScroll = Infinity }: ObjetivoScroll): number {
  return Math.max(0, Math.min(maxScroll, topAbs));
}

export interface ObjetivoCierre {
  /** Distancia del borde superior de la tarjeta de cierre al inicio del documento. */
  topAbs: number;
  /** Alto de la cabecera fija, que taparía la tarjeta si no se descuenta. */
  altoHeader: number;
  /** Scroll máximo posible del documento, para no pedir lo imposible. */
  maxScroll?: number;
}

/**
 * Posición de scroll de la última parada de la reproducción: la tarjeta de cierre,
 * con la ficha de quien firma el artículo y los botones de compartir.
 *
 * Aquí no se cuadra una caja con la pantalla, como en los pasos: la tarjeta no mide
 * una pantalla, así que lo que se busca es que su borde de arriba quede justo debajo
 * de la cabecera fija, y que se lea de corrido lo que venga detrás.
 */
export function objetivoCierre({ topAbs, altoHeader, maxScroll = Infinity }: ObjetivoCierre): number {
  return Math.max(0, Math.min(maxScroll, topAbs - altoHeader));
}

/**
 * Cuánto se queda la reproducción automática en un paso. Se calcula del propio texto,
 * a ritmo de lectura en pantalla (unas 285 palabras por minuto) más un margen para
 * mirar el gráfico. Un paso de una línea no debe durar lo mismo que uno de cinco.
 *
 * El ritmo era el de la lectura en voz alta, 180 palabras por minuto, y se quedaba
 * largo: un recorrido entero tardaba cerca de tres minutos y 15 de los 41 pasos que
 * hay hoy chocaban contra el tope, con lo cual duraban todos lo mismo y la cuenta no
 * servía de nada. Con estos números un recorrido dura algo más de minuto y medio y
 * los pasos en el tope bajan a 7 de 41, entre uno y cuatro por recorrido. Quien
 * quiera ir más despacio, ahí está el botón de pausa.
 */
export function duracionPaso(texto: string, { base = 800, porPalabra = 210, min = 2500, max = 9000 } = {}): number {
  const palabras = texto.trim() ? texto.trim().split(/\s+/).length : 0;
  return Math.round(Math.max(min, Math.min(max, base + palabras * porPalabra)));
}

/** Paso al que corresponde un clic sobre la barra de avance, dada su fracción. */
export function pasoDeFraccion(fraccion: number, total: number): number {
  // La barra se pinta con el paso ya completado, así que el tramo del paso i va de
  // i/total a (i+1)/total: la fracción se traduce multiplicando por el total. Recortar
  // la fracción antes sobra: el recorte de abajo ya devuelve el mismo paso para
  // cualquier valor finito, incluidos los infinitos.
  return Math.max(0, Math.min(total - 1, Math.floor(fraccion * total)));
}

/**
 * Cuánto dura el viaje de un salto, en milisegundos, según la distancia que recorre.
 * Ni instantáneo, que pierde el hilo de dónde estabas, ni eterno: dos clics seguidos
 * en "siguiente" tienen que poder encadenarse sin que el segundo espere al primero.
 */
export function duracionViaje(distancia: number, { innerHeight = 900, base = 240, porPantalla = 260, max = 900 } = {}): number {
  const pantallas = Math.abs(distancia) / Math.max(1, innerHeight);
  return Math.round(Math.min(max, base + pantallas * porPantalla));
}

/**
 * Suavizado del viaje: arranca despacio, acelera y frena, sin pasarse del destino.
 * Fuera del tramo [0, 1] devuelve los extremos, para que un cuadro que llegue tarde
 * no pinte una posición imposible.
 */
export function suavizado(k: number): number {
  // NaN hay que atajarlo aparte: Math.min y Math.max lo propagan en vez de recortarlo,
  // y un NaN aquí dejaría el bucle de animación sin final, porque ninguna comparación
  // con NaN es cierta. Se da el viaje por terminado, que es la salida segura. Los
  // infinitos sí los recorta el propio Math, así que no necesitan trato especial.
  if (Number.isNaN(k)) return 1;
  const t = Math.min(1, Math.max(0, k));
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

/**
 * Fracción de la barra de avance que corresponde a estar en el paso `step` de `total`.
 * El paso en curso se cuenta como recorrido, así que el primero ya pinta algo: una
 * barra vacía en el paso 1 se lee como "esto no ha empezado".
 */
export function fraccionAvance(step: number, total: number): number {
  return Math.min(1, Math.max(0, (step + 1) / total));
}

/**
 * Parada que corresponde a una posición de scroll, contando la tarjeta de cierre como
 * una más al final del relato. Devuelve `tops.length` cuando la tarjeta ya cruzó la
 * línea de disparo, que es el índice que le toca como última parada.
 *
 * Sin `topCierre` (una página que embeba un recorrido sin tarjeta) se comporta igual
 * que `pasoVisibleEn`, y la última parada es el último paso.
 */
export function paradaVisibleEn({ tops, topCierre, scrollY, innerHeight, offset }: {
  tops: number[];
  /** Borde superior de la tarjeta de cierre, o undefined si no la hay. */
  topCierre?: number;
  scrollY: number;
  innerHeight: number;
  offset: number;
}): number {
  const linea = scrollY + innerHeight * offset;
  if (topCierre !== undefined && topCierre <= linea) return tops.length;
  return pasoVisibleEn({ tops, scrollY, innerHeight, offset });
}

/**
 * Paso que corresponde a una posición de scroll: el último cuyo borde superior ya
 * cruzó la línea de disparo. Es la misma geometría que usa scrollama, calculada por
 * nuestra cuenta para poder reengancharnos cuando sus avisos no llegan (pestaña en
 * segundo plano, cambio de tamaño de la ventana) y la pantalla se quedaría contando
 * un paso que ya no es el que se ve.
 */
export function pasoVisibleEn({ tops, scrollY, innerHeight, offset }: {
  /** Borde superior de cada paso, medido desde el inicio del documento. */
  tops: number[];
  scrollY: number;
  innerHeight: number;
  offset: number;
}): number {
  const linea = scrollY + innerHeight * offset;
  let paso = 0;
  for (let i = 0; i < tops.length; i++) {
    if (tops[i] <= linea) paso = i;
    else break;
  }
  return paso;
}
