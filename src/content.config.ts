import { defineCollection, reference, z } from 'astro:content';
import { glob } from 'astro/loaders';

// Esquema de referencia: docs/content-collections.md
// Política de derechos de autor obligatoria: ver CLAUDE.md. Ninguna colección
// almacena texto verbatim ni imágenes originales de los papers.

const investigadores = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/investigadores' }),
  schema: z.object({
    nombre: z.string(),
    tratamiento: z.string().optional(), // "Dr." / "Dra." para anteponer al nombre
    fotoUrl: z.string().optional(),
    bioBreve: z.string(),
    lineasInvestigacion: z.array(z.string()),
    sede: z.literal('Querétaro'),
    carpetaDrive: z.string().url(),
  }),
});

const papers = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/papers' }),
  schema: z.object({
    titulo: z.string(),
    investigador: reference('investigadores'),
    editorial: z.string(),
    anioPublicacion: z.number(),
    doi: z.string().optional(),
    driveFileId: z.string(),
    estadoPipeline: z.enum(['pendiente', 'en_produccion', 'publicado']),
    temasClave: z.array(z.string()),
  }),
});

const series = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/series' }),
  schema: z.object({
    nombre: z.string(),
    descripcion: z.string(),
    colorAcento: z.string().optional(), // pendiente de identidad visual institucional
    imagenPortada: z.string().optional(), // foto representativa de banner (ruta bajo /public)
    imagenCredito: z.string().optional(), // crédito de la foto si la licencia lo exige
  }),
});

const capsulas = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/capsulas' }),
  schema: z.object({
    titulo: z.string(),
    serie: reference('series'),
    paperFuente: reference('papers'),
    investigadores: z.array(reference('investigadores')),
    formatos: z.array(z.enum(['video', 'audio', 'infografia', 'texto'])),
    // Imagen real de portada para la tarjeta (foto de stock CC o del material de la
    // cápsula). Ruta bajo /public. Si falta, la tarjeta usa el thumbnail SVG.
    imagenPortada: z.string().optional(),
    // Crédito de la imagen de portada, si su licencia lo exige (ej. CC BY-SA). Se
    // muestra discreto en la página de la cápsula.
    imagenCredito: z.string().optional(),
    videoUrl: z.string().url().optional(),
    audioUrl: z.string().url().optional(),
    // Página canónica externa del recurso (ej. Google Sites de origen), distinta de
    // la URL de embed. Se usa como respaldo cuando el embed falla (ver CLAUDE.md,
    // limitación de cuota diaria de Google Drive).
    fuenteExternaUrl: z.string().url().optional(),
    // Clave de un componente de scrollytelling dedicado a renderizar en lugar del
    // cuerpo estándar (ej. "utopias"). Ver src/components/Scrolly*.astro.
    scrolly: z.string().optional(),
    resumenCorto: z.string(),
    fechaPublicacion: z.date(),
    revisadoPor: z.string(),
    // Crédito de producción del recurso (ej. video hecho por otro equipo). Se muestra
    // en "Fuente y créditos".
    creditoProduccion: z.string().optional(),
  }),
});

const entrevistas = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/entrevistas' }),
  schema: z.object({
    investigador: reference('investigadores'),
    preguntas: z.array(z.object({ pregunta: z.string(), respuesta: z.string() })).length(3),
    paperRelacionado: reference('papers').optional(),
    fechaPublicacion: z.date(),
    // Video opcional de la entrevista, en modo cine arriba de las preguntas. Usar
    // siempre YouTube (no listado o público), no Google Drive: ver CLAUDE.md sobre
    // los permisos scoped-al-Site de Drive. Puede ser un video con avatar de IA
    // generado desde un guion propio (parafraseado, sin texto verbatim del paper).
    videoUrl: z.string().url().optional(),
    // Nota de producción del video (ej. "Avatar generado con IA a partir de un guion
    // de divulgación propio"). Se muestra bajo el reproductor.
    videoNota: z.string().optional(),
    // Entrevista de muestra: la redactó el equipo de divulgación para enseñar cómo se
    // verá la sección, y el investigador todavía NO la ha dicho ni revisado. El sitio
    // lo avisa en la tarjeta y en la página, porque son palabras puestas en boca de
    // una persona real. Se quita en cuanto la entrevista se graba de verdad.
    esEjemplo: z.boolean().default(false),
  }),
});

// Recorridos de scrollytelling: los pasos del relato (texto + imagen), fuera del
// componente Astro para que los autores puedan corregirlos desde la ficha en Drive.
// Ver docs/ficha-recorrido.md. La clave `visual` de cada paso amarra el paso con su
// escena SVG dentro del componente: no se renombra ni se reordena a la ligera.
const recorridos = defineCollection({
  loader: glob({ pattern: '**/*.yaml', base: './src/content/recorridos' }),
  schema: z.object({
    capsula: reference('capsulas'),
    titulo: z.string(),
    pasos: z.array(z.object({
      visual: z.string(),
      pos: z.enum(['left', 'right', 'center']),
      tipo: z.enum(['foto', 'figura', 'svg']),
      // Ruta bajo /public de la foto o figura del paso. Los pasos de tipo "svg" no
      // llevan imagen: su visual es un gráfico animado del componente.
      imagen: z.string().optional(),
      imagenLado: z.enum(['izq', 'der']).optional(),
      // Crédito y licencia, obligatorio cuando hay imagen (ver política en CLAUDE.md).
      credito: z.string().optional(),
      texto: z.string(),
    })).min(1)
      .superRefine((pasos, ctx) => {
        const vistos = new Set<string>();
        pasos.forEach((p, i) => {
          if (vistos.has(p.visual)) {
            ctx.addIssue({ code: 'custom', message: `La clave visual "${p.visual}" está repetida (paso ${i + 1}).`, path: [i, 'visual'] });
          }
          vistos.add(p.visual);
          if (p.tipo === 'svg' && p.imagen) {
            ctx.addIssue({ code: 'custom', message: `El paso ${i + 1} es de tipo svg y no admite imagen.`, path: [i, 'imagen'] });
          }
          if (p.tipo !== 'svg' && !p.imagen) {
            ctx.addIssue({ code: 'custom', message: `El paso ${i + 1} es de tipo ${p.tipo} y necesita imagen.`, path: [i, 'imagen'] });
          }
          if (p.imagenLado && p.tipo !== 'figura') {
            ctx.addIssue({ code: 'custom', message: `El paso ${i + 1} es de tipo ${p.tipo}: imagenLado solo aplica a las figuras a un costado.`, path: [i, 'imagenLado'] });
          }
          if (p.imagen && !p.credito) {
            ctx.addIssue({ code: 'custom', message: `El paso ${i + 1} tiene imagen sin crédito ni licencia.`, path: [i, 'credito'] });
          }
        });
      }),
  }),
});

export const collections = { investigadores, papers, series, capsulas, entrevistas, recorridos };
