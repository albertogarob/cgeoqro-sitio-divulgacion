// Motor común de los recorridos de scrollytelling. Lo usa ScrollyShell.astro; cada
// recorrido solo aporta su escena SVG y su configuración (cámara por paso, pasos en
// los que el mapa se atenúa), que viaja en el atributo data-config del contenedor.
import scrollama from 'scrollama';

interface ConfigScrolly {
  camaras?: Record<string, string>;
  dim?: number[];
  offset?: number;
}

function leerConfig(container: HTMLElement): ConfigScrolly {
  try {
    return JSON.parse(container.dataset.config ?? '{}') as ConfigScrolly;
  } catch {
    return {};
  }
}

// Los miles llevan separador: "1,183" se lee de un golpe y "1183" no.
const formatoNumero = new Intl.NumberFormat('es-MX');
// Animación en curso por elemento, para no dejar dos bucles escribiendo el mismo
// número cuando alguien sube y baja deprisa por el mismo paso.
const animaciones = new WeakMap<Element, number>();

function animarConteo(el: Element, hasta: number, dur = 1000) {
  // Un data-to que no sea un número (por ejemplo, ya formateado con coma) pintaría
  // literalmente "NaN" en pantalla. Mejor dejar el valor que ya hubiera.
  if (!Number.isFinite(hasta)) return;
  const previo = animaciones.get(el);
  if (previo !== undefined) cancelAnimationFrame(previo);
  let inicio = 0;
  function frame(t: number) {
    if (!inicio) inicio = t;
    const k = Math.min(1, (t - inicio) / dur);
    el.textContent = formatoNumero.format(Math.round(hasta * (1 - Math.pow(1 - k, 3))));
    if (k < 1) animaciones.set(el, requestAnimationFrame(frame));
    else animaciones.delete(el);
  }
  animaciones.set(el, requestAnimationFrame(frame));
}

/**
 * Lleva la vista al primer paso del recorrido, dejándolo justo debajo del navbar. La
 * usan tanto el botón flotante del escenario como la tarjeta de cierre de la cápsula.
 */
export function irAlInicioDelRecorrido() {
  const seccion = document.querySelector<HTMLElement>('.scrolly');
  if (!seccion) return;
  const header = document.querySelector<HTMLElement>('header');
  const suave = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const y = seccion.getBoundingClientRect().top + window.scrollY - (header ? header.offsetHeight : 64);
  window.scrollTo({ top: Math.max(0, y), behavior: suave ? 'smooth' : 'auto' });
}

export function initScrolly() {
  const container = document.querySelector<HTMLElement>('.scrolly');
  if (!container) return;

  const cfg = leerConfig(container);
  const header = document.querySelector<HTMLElement>('header');
  const camera = container.querySelector<SVGGElement>('.camera');
  const map = container.querySelector<SVGGElement>('.map');
  const layers = Array.from(container.querySelectorAll<SVGGElement>('.layer'));
  const onlys = Array.from(container.querySelectorAll<SVGGElement>('.only'));
  const medios = Array.from(container.querySelectorAll<HTMLElement>('.media'));
  const scrim = container.querySelector<HTMLElement>('.media-scrim');
  const creditoEl = container.querySelector<HTMLElement>('.stage-credito');
  const stepEls = Array.from(container.querySelectorAll<HTMLElement>('.step'));
  const total = stepEls.length;

  // Barra de avance y botón de volver al inicio.
  const progreso = container.querySelector<HTMLElement>('.scrolly-progreso');
  const relleno = container.querySelector<HTMLElement>('.scrolly-progreso .relleno');
  const actualEl = container.querySelector<HTMLElement>('.scrolly-progreso .actual');
  const botonInicio = container.querySelector<HTMLButtonElement>('.scrolly-inicio');

  const tipoDe: Record<number, string> = {};
  stepEls.forEach((e) => { tipoDe[Number(e.dataset.step)] = e.dataset.tipo ?? 'svg'; });
  const dim = new Set(cfg.dim ?? []);
  const camaras = cfg.camaras ?? {};

  function altoHeader() {
    return header ? header.offsetHeight : 64;
  }
  function setStageTop() {
    container!.style.setProperty('--stage-top', altoHeader() + 'px');
  }
  setStageTop();
  window.addEventListener('resize', setStageTop);

  function aplicar(step: number) {
    const tipo = tipoDe[step] ?? 'svg';
    const esFoto = tipo === 'foto';
    container!.dataset.step = String(step);
    container!.dataset.mode = tipo;

    // Sin cámara declarada, plano general. Nada de heredar la del primer paso: eso
    // contagiaría su encuadre a todos los pasos que no declaran el suyo.
    if (camera) camera.setAttribute('transform', camaras[String(step)] ?? 'translate(0,0) scale(1)');
    if (map) {
      map.classList.toggle('dim', dim.has(step));
      map.classList.toggle('hide', esFoto);
    }

    medios.forEach((m) => m.classList.toggle('on', Number(m.dataset.media) === step));
    if (scrim) scrim.classList.toggle('on', esFoto);
    const mediaActiva = medios.find((m) => Number(m.dataset.media) === step);
    if (creditoEl) {
      const cr = mediaActiva?.dataset.credito ?? '';
      creditoEl.textContent = cr;
      creditoEl.classList.toggle('on', Boolean(cr));
    }

    layers.forEach((l) => l.classList.toggle('on', step >= Number(l.dataset.from ?? '0')));
    // En un paso con foto a sangre se apagan los momentos ligados al mapa; solo
    // sobreviven los marcados como legibles sobre la foto (por ejemplo, el cierre).
    onlys.forEach((o) => {
      const n = Number(o.dataset.only);
      o.classList.toggle('on', n === step && (!esFoto || o.dataset.sobreFoto === 'si'));
    });
    const activo = onlys.find((o) => Number(o.dataset.only) === step && o.classList.contains('on'));
    if (activo) {
      activo.querySelectorAll<HTMLElement>('.count').forEach((c) => animarConteo(c, Number(c.dataset.to ?? '0')));
    }

    if (relleno) relleno.style.width = total > 1 ? `${((step + 1) / total) * 100}%` : '100%';
    if (actualEl) actualEl.textContent = String(step + 1);
    if (progreso) progreso.setAttribute('aria-valuenow', String(step + 1));
    // El botón de salida estorba en el primer paso, donde no hay nada a lo que volver.
    if (botonInicio) botonInicio.hidden = step < 1;
  }

  if (botonInicio) botonInicio.addEventListener('click', irAlInicioDelRecorrido);

  aplicar(0);

  const scroller = scrollama();
  scroller
    .setup({ step: '.scrolly .step', offset: cfg.offset ?? 0.75 })
    .onStepEnter((r: { element: HTMLElement }) => {
      stepEls.forEach((el) => el.classList.remove('activo'));
      r.element.classList.add('activo');
      aplicar(Number(r.element.dataset.step ?? '0'));
    });
  window.addEventListener('resize', scroller.resize);
}
