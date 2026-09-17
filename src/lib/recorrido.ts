// Utilidades para que un componente de scrollytelling amarre su escena SVG a los
// pasos del recorrido por nombre (`visual`) en vez de por número de paso. Así, al
// insertar o mover un paso, los gráficos siguen enganchados donde deben.
export interface PasoRecorrido {
  visual: string;
  pos: 'left' | 'right' | 'center';
  tipo: 'foto' | 'figura' | 'svg';
  imagen?: string;
  imagenLado?: 'izq' | 'der';
  credito?: string;
  texto: string;
}

/** Índice del paso con esa clave visual. Falla en build si la clave no existe. */
export function indiceVisual(pasos: PasoRecorrido[], visual: string): number {
  const i = pasos.findIndex((p) => p.visual === visual);
  if (i < 0) {
    throw new Error(
      `El recorrido no tiene ningún paso con visual "${visual}", pero el componente lo usa. ` +
      'Revisa el archivo del recorrido en src/content/recorridos/.'
    );
  }
  return i;
}

/** Convierte un mapa {visual: valor} en {índice: valor}, validando cada clave. */
export function porIndice<T>(pasos: PasoRecorrido[], mapa: Record<string, T>): Record<number, T> {
  const salida: Record<number, T> = {};
  for (const [visual, valor] of Object.entries(mapa)) salida[indiceVisual(pasos, visual)] = valor;
  return salida;
}

/** Lista de claves visuales a lista de índices, validando cada clave. */
export function indices(pasos: PasoRecorrido[], visuales: string[]): number[] {
  return visuales.map((v) => indiceVisual(pasos, v));
}
