// Recortes de texto para las tarjetas. Viven aquí y no dentro de una página porque
// son justo lo que falla en silencio: un texto sin punto final, uno de una sola
// palabra, o uno tan largo que parte la maqueta.

/**
 * Abreviaturas que llevan punto sin terminar la frase. Sin esta lista, "lo midió el
 * Dr. López" se corta en "lo midió el Dr." y la tarjeta queda sin decir nada.
 */
const ABREVIATURAS = new Set([
  'dr', 'dra', 'sr', 'sra', 'srta', 'lic', 'ing', 'mtro', 'mtra',
  'av', 'núm', 'num', 'etc', 'vs', 'ej', 'p', 'fig', 'pág', 'pag',
]);

/**
 * Primera frase de un texto, para usarla como gancho en una tarjeta. Si la frase se
 * pasa de `max`, se corta en el último espacio y se cierra con puntos suspensivos,
 * para no partir una palabra por la mitad.
 *
 * Las entrevistas comparten las tres mismas preguntas, así que lo que distingue a una
 * de otra en la lista es cómo empieza la respuesta, no la pregunta.
 */
export function primeraFrase(texto: string, max = 150): string {
  const limpio = texto.trim().replace(/\s+/g, ' ');
  if (!limpio) return '';

  // Una frase acaba en punto, cierre de interrogación o de exclamación seguido de
  // espacio o de final. Exigir el espacio deja fuera los decimales ("1.5 grados"), y
  // la lista de arriba, junto con descartar las iniciales de una letra ("J. Piña"),
  // deja fuera las abreviaturas.
  let frase = limpio;
  const busca = /[.!?](\s|$)/g;
  let m: RegExpExecArray | null;
  while ((m = busca.exec(limpio)) !== null) {
    if (limpio[m.index] === '.') {
      const previa = (limpio.slice(0, m.index).split(/[\s(«"']/).pop() ?? '').toLowerCase();
      if (previa.length <= 1 || ABREVIATURAS.has(previa)) continue;
    }
    frase = limpio.slice(0, m.index + 1);
    break;
  }

  if (frase.length <= max) return frase;
  const corte = frase.slice(0, max);
  const espacio = corte.lastIndexOf(' ');
  // Ninguna de las dos ramas puede acabar en espacio: los espacios ya vienen
  // normalizados, así que `slice(0, espacio)` deja el espacio fuera, y la otra rama
  // solo entra cuando el último espacio está muy al principio.
  return `${espacio > max * 0.6 ? corte.slice(0, espacio) : corte}…`;
}
