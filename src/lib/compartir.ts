// Enlaces de "compartir en redes" de una cápsula. Vive aparte del componente para
// poder probarlo: una URL relativa o un texto sin escapar rompen el compartido en
// silencio, y eso solo se ve cuando alguien ya pegó el enlace en WhatsApp.

export interface DatosCompartir {
  /** URL canónica absoluta de la cápsula (con esquema y dominio). */
  url: string;
  titulo: string;
  /** Resumen corto; se usa donde la red acepta texto además del enlace. */
  resumen?: string;
}

export interface EnlaceRed {
  /** Clave corta de la red, para el icono y las métricas de Analytics. */
  red: string;
  /** Texto accesible del enlace ("Compartir en WhatsApp"). */
  etiqueta: string;
  href: string;
}

/** Tope del texto que se arrastra al compartir, para no generar enlaces gigantes. */
const MAX_TEXTO = 240;

function recortar(texto: string, max = MAX_TEXTO): string {
  const limpio = texto.trim().replace(/\s+/g, ' ');
  if (limpio.length <= max) return limpio;
  // Corta en el último espacio para no partir una palabra por la mitad.
  const corte = limpio.slice(0, max - 1);
  const espacio = corte.lastIndexOf(' ');
  return `${(espacio > max * 0.6 ? corte.slice(0, espacio) : corte).trimEnd()}…`;
}

/**
 * Comprueba que la URL sea absoluta http(s). Una ruta relativa se compartiría como
 * texto suelto y el enlace no llevaría a ninguna parte, así que falla en build.
 */
export function urlCompartible(url: string): string {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    throw new Error(`Para compartir hace falta una URL absoluta, llegó "${url}".`);
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error(`Para compartir hace falta una URL http o https, llegó "${url}".`);
  }
  return parsed.toString();
}

export function enlacesCompartir({ url, titulo, resumen = '' }: DatosCompartir): EnlaceRed[] {
  const u = encodeURIComponent(urlCompartible(url));
  const t = encodeURIComponent(recortar(titulo));
  const conResumen = encodeURIComponent(recortar(resumen ? `${titulo}. ${resumen}` : titulo));

  return [
    {
      red: 'whatsapp',
      etiqueta: 'Compartir en WhatsApp',
      href: `https://api.whatsapp.com/send?text=${conResumen}%20${u}`,
    },
    {
      red: 'facebook',
      etiqueta: 'Compartir en Facebook',
      href: `https://www.facebook.com/sharer/sharer.php?u=${u}`,
    },
    {
      red: 'x',
      etiqueta: 'Compartir en X',
      href: `https://x.com/intent/tweet?url=${u}&text=${t}`,
    },
    {
      red: 'linkedin',
      etiqueta: 'Compartir en LinkedIn',
      href: `https://www.linkedin.com/sharing/share-offsite/?url=${u}`,
    },
  ];
}
