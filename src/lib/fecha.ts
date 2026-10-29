// Fechas de publicación, siempre en el mismo huso.
//
// Las fechas del contenido vienen del frontmatter como "2026-10-29", y JavaScript las
// entiende como medianoche UTC. Al pintarlas con la zona horaria de la máquina, que
// aquí va seis horas por detrás, salía el día anterior: una entrevista fechada el 29
// se publicaba como "28/10/2026". Pasaba en todas, y nadie lo notaba porque el día
// equivocado también parece un día válido.

/** Día de publicación en formato corto (29/10/2026), leído como fecha, no como instante. */
export function fechaCorta(fecha: Date): string {
  return fecha.toLocaleDateString('es-MX', { timeZone: 'UTC' });
}

/** Día de publicación escrito con todas las letras (29 de octubre de 2026). */
export function fechaLarga(fecha: Date): string {
  return fecha.toLocaleDateString('es-MX', {
    timeZone: 'UTC',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}
