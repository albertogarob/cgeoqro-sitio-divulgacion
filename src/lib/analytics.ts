// Google Analytics 4. El ID de medición no es un secreto (viaja en el HTML de
// cualquier sitio que lo use), pero sí es específico de la instalación, así que se
// inyecta por variable de entorno y no se escribe en el código.
//
// ┌──────────────────────────────────────────────────────────────────────────────┐
// │ PUNTO DE CONFIGURACIÓN. Poner PUBLIC_GA_ID=G-XXXXXXXXXX en .env (local) y    │
// │ como secreto del repositorio con el mismo nombre (publicación).              │
// │ Sin ese valor no se carga nada de Analytics, ni en local ni en producción.   │
// │ Instrucciones paso a paso: docs/contacto-y-analytics.md                      │
// └──────────────────────────────────────────────────────────────────────────────┘

/** Forma de un ID de medición de GA4. Las propiedades viejas (UA-) no sirven aquí. */
const RE_ID_MEDICION = /^G-[A-Z0-9]{6,}$/;

export function idMedicionValido(id: string | undefined | null): boolean {
  return RE_ID_MEDICION.test((id ?? '').trim());
}

/**
 * Devuelve el ID si es utilizable y cadena vacía si no hay ninguno. Un valor presente
 * pero mal formado es un error de configuración: avisa en consola durante el build en
 * vez de cargar un Analytics que nunca va a registrar nada.
 */
export function idMedicion(bruto: string | undefined | null): string {
  const id = (bruto ?? '').trim();
  if (!id) return '';
  if (!idMedicionValido(id)) {
    console.warn(
      `[analytics] PUBLIC_GA_ID="${id}" no tiene la forma G-XXXXXXXXXX; no se carga Google Analytics.`
    );
    return '';
  }
  return id;
}

export interface DatosCapsulaAnalytics {
  capsula?: string;
  serie?: string;
  investigadores?: string[];
}

/**
 * Parámetros propios que acompañan a la vista de página. Permiten desglosar el
 * tráfico por cápsula, por serie y por investigador, que es lo que pidió el equipo:
 * que cada quien pueda reportar el tráfico de su propio contenido. En GA4 hay que
 * registrarlos además como dimensiones personalizadas de ámbito "evento".
 */
export function parametrosCapsula({ capsula, serie, investigadores = [] }: DatosCapsulaAnalytics): Record<string, string> {
  const params: Record<string, string> = {};
  if (capsula) params.capsula = capsula;
  if (serie) params.serie = serie;
  const autores = investigadores.filter(Boolean);
  // GA4 corta los valores de parámetro en 100 caracteres: con varios autores se
  // manda la lista recortada en lugar de un valor truncado a media palabra.
  if (autores.length) params.investigadores = recortarValor(autores.join(', '));
  return params;
}

/** Tope de GA4 para el valor de un parámetro de evento. */
const MAX_VALOR = 100;

export function recortarValor(valor: string, max = MAX_VALOR): string {
  if (valor.length <= max) return valor;
  const corte = valor.slice(0, max - 1);
  const coma = corte.lastIndexOf(',');
  return `${(coma > 0 ? corte.slice(0, coma) : corte).trimEnd()}…`;
}
