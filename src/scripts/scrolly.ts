// Motor común de los recorridos de scrollytelling. Lo usa ScrollyShell.astro; cada
// recorrido solo aporta su escena SVG y su configuración (cámara por paso, pasos en
// los que el mapa se atenúa), que viaja en el atributo data-config del contenedor.
import scrollama from 'scrollama';
import { contarParadas, duracionPaso, duracionViaje, esParadaDeCierre, esUltimaParada, estadoMandos, fraccionAvance, objetivoCierre, objetivoScroll, paradaVisibleEn, pasoDeFraccion, pasoDestino, suavizado, ultimaParada } from './pasos';

/**
 * El scroll se considera detenido cuando deja de haber eventos durante este rato. Solo
 * sirve para enterarnos de hasta dónde se ha desplazado el usuario por su cuenta: los
 * saltos propios saben por sí mismos cuándo terminan, porque los animamos nosotros.
 */
const ESPERA_ASENTADO = 160;
/** Petición de volver al principio, que el motor atiende si está en marcha. */
const EVENTO_INICIO = 'recorrido:inicio';
/** Petición de reproducir desde el primer paso, para el botón de play de la entrada. */
const EVENTO_REPRODUCIR = 'recorrido:reproducir';
/** Holgura en píxeles para dar un destino de scroll por alcanzado. */
const TOLERANCIA_SCROLL = 4;

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
  // Con el motor en marcha, el viaje lo hace él: así queda registrado como salto y un
  // clic en los mandos mientras viaja no se pierde. El motor lo confirma cancelando el
  // evento; si nadie responde (no se llegó a arrancar), se desplaza aquí mismo.
  if (!seccion.dispatchEvent(new CustomEvent(EVENTO_INICIO, { cancelable: true }))) return;
  const header = document.querySelector<HTMLElement>('header');
  const suave = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const y = seccion.getBoundingClientRect().top + window.scrollY - (header ? header.offsetHeight : 64);
  window.scrollTo({ top: Math.max(0, y), behavior: suave ? 'smooth' : 'auto' });
}

/**
 * Arranca el recorrido desde el primer paso. La usa el botón de play de la entrada de
 * la cápsula, para quien prefiere que el relato se cuente solo en vez de desplazarse.
 * Sin motor en marcha no hay nada que reproducir, así que al menos baja hasta ahí.
 */
export function reproducirRecorrido() {
  const seccion = document.querySelector<HTMLElement>('.scrolly');
  if (!seccion) return;
  if (!seccion.dispatchEvent(new CustomEvent(EVENTO_REPRODUCIR, { cancelable: true }))) return;
  irAlInicioDelRecorrido();
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

  // Los mandos y la tarjeta de cierre viven fuera de la sección de los pasos, colgados
  // del bloque entero, para que la banda siga en pantalla al llegar a la tarjeta.
  const bloque = container.closest<HTMLElement>('.scrolly-bloque') ?? document.body;

  // Barra de avance y botón de volver al inicio.
  const relleno = bloque.querySelector<HTMLElement>('.scrolly-cine .relleno');
  const actualEl = bloque.querySelector<HTMLElement>('.scrolly-cine .actual');
  const totalEl = bloque.querySelector<HTMLElement>('.scrolly-cine .total');
  const botonInicio = bloque.querySelector<HTMLButtonElement>('.scrolly-inicio');

  // Mandos de reproducción: anterior, reproducir/pausa, siguiente, y la propia barra
  // de avance, en la que se puede picar para saltar a una parada.
  const barra = bloque.querySelector<HTMLElement>('.scrolly-cine .barra');
  const botonAnterior = bloque.querySelector<HTMLButtonElement>('.mando-anterior');
  const botonSiguiente = bloque.querySelector<HTMLButtonElement>('.mando-siguiente');
  const botonPlay = bloque.querySelector<HTMLButtonElement>('.mando-play');

  // La tarjeta de cierre (ficha de quien firma el artículo y botones de compartir) es
  // UNA PARADA MÁS del recorrido, la última: "siguiente" llega a ella desde el último
  // paso, el contador la cuenta y la reproducción automática termina ahí. Si la página
  // no la trae, el recorrido se acaba en el último paso y nada más cambia.
  const cierre = bloque.querySelector<HTMLElement>('[data-recorrido-cierre]');
  // Las cuentas de las paradas viven en pasos.ts, con el resto de la aritmética del
  // recorrido, para poder probarlas sin navegador. Aquí solo se atan al DOM.
  const hayCierre = Boolean(cierre);
  /** Número de paradas: los pasos del relato más la tarjeta de cierre, si la hay. */
  const paradas = contarParadas(total, hayCierre);
  /** Índice de la parada de cierre. Vale `total`, justo detrás del último paso. */
  const CIERRE = total;
  const esCierre = (parada: number) => esParadaDeCierre(parada, total, hayCierre);
  const offsetDisparo = cfg.offset ?? 0.75;
  // Duración de cada paso en reproducción automática, sacada de su propio texto.
  const duraciones = stepEls.map((el) => duracionPaso(el.querySelector('.caption')?.textContent ?? ''));
  const suave = () => !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  // Tres cuentas distintas a propósito.
  //
  // `pasoVisible` es el paso del RELATO que scrollama dice que se está viendo, y manda
  // en los gráficos; nunca vale la parada de cierre, porque la tarjeta no es un paso y
  // scrollama no la conoce.
  //
  // `paradaVisible` es dónde está el lector contando la tarjeta de cierre, y es lo que
  // pintan el contador y la barra.
  //
  // `paradaPedida` es a dónde apuntan los mandos, y avanza en el momento del clic: si
  // dependiera de la confirmación de scrollama, dos clics seguidos contarían como uno
  // y una devolución de llamada perdida dejaría los botones atascados.
  let pasoVisible = 0;
  let paradaVisible = 0;
  let paradaPedida = 0;
  // Viaje propio en curso, o null si la pantalla está quieta o la mueve el usuario.
  // Mientras haya uno, los pasos que scrollama va cantando por el camino pintan los
  // gráficos pero no mueven a dónde apuntan los mandos: manda el destino.
  let viaje: { desde: number; hasta: number; t0: number; dur: number } | null = null;
  let cuadro: number | undefined;
  let asentar: number | undefined;
  // Si ya se pintó algún paso. Arranca en falso para que el primer `aplicar(0)` pinte
  // de verdad, aunque `pasoVisible` ya valga 0.
  let aplicado = false;
  let reproduciendo = false;
  let temporizador: number | undefined;

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

  /**
   * ¿El centro de la pantalla cae dentro del recorrido? Se anota cada vez que el scroll
   * se para, no se pregunta en el momento: cuando llega un cambio de tamaño el
   * navegador ya ha movido todo de sitio, y la respuesta sería sobre la pantalla nueva
   * en vez de sobre la que el usuario estaba mirando.
   */
  let recorridoALaVista = false;
  // Tamaño de la ventana la última vez que la pantalla quedó encuadrada en un paso.
  let anchoEncuadrado = window.innerWidth;
  let altoEncuadrado = window.innerHeight;
  function anotarSiSeVeElRecorrido() {
    const caja = container!.getBoundingClientRect();
    const medio = window.innerHeight / 2;
    recorridoALaVista = caja.top <= medio && caja.bottom >= medio;
    anchoEncuadrado = window.innerWidth;
    altoEncuadrado = window.innerHeight;
  }

  /**
   * Cambiar el alto de la ventana mueve de sitio todos los pasos, y el navegador deja
   * el scroll más o menos donde estaba: quien estaba leyendo un paso acaba en otro
   * sitio, o directamente fuera del relato, con ese paso todavía declarado activo y su
   * texto a dos pantallas de allí. Medido: girar la ventana de 900 a 620 de alto en el
   * paso 13 dejaba la pantalla 2347 px más abajo, en la banda de créditos.
   *
   * Pasa con el giro del teléfono y con un cambio de tamaño de la ventana, así que hay
   * que reencuadrar. Con tres cautelas, para no reencuadrar a quien no lo ha pedido.
   */
  function alCambiarElTamano() {
    setStageTop();
    if (!viaje) {
      // Cuánto ha cambiado la pantalla DESDE EL ÚLTIMO ENCUADRE, no desde el cambio de
      // tamaño anterior: así un arrastre lento del borde de la ventana acaba contando,
      // y una barra de direcciones que sube y baja alrededor del mismo alto, nunca.
      const cambioDeAncho = window.innerWidth !== anchoEncuadrado;
      const cambioGrandeDeAlto = Math.abs(window.innerHeight - altoEncuadrado) > altoEncuadrado * 0.25;
      // En el teléfono la barra de direcciones aparece y desaparece MIENTRAS se hace
      // scroll, y se lleva por delante unos diez puntos porcentuales del alto.
      // Reencuadrar ahí sería pelearse con el dedo del usuario, así que solo se
      // reencuadra cuando el cambio es de los que rehacen la pantalla de verdad: un
      // giro del teléfono, o arrastrar el borde de la ventana.
      if (!cambioDeAncho && !cambioGrandeDeAlto) return;
      // Y si no estaba leyendo el recorrido sino el texto de alrededor, no se le
      // arrastra a ninguna parte.
      if (!recorridoALaVista) return;
      irAPaso(paradaVisible);
      return;
    }
    const destino = destinoDeParada(paradaPedida);
    if (destino === null) return;
    // Si el destino no se ha movido, no se toca el viaje: en el teléfono los cambios de
    // tamaño llegan en ráfaga, y reiniciar la cuenta en cada uno lo dejaría sin avanzar.
    if (Math.abs(destino - viaje.hasta) <= TOLERANCIA_SCROLL) return;
    viaje.desde = window.scrollY;
    viaje.hasta = destino;
    viaje.t0 = performance.now();
    viaje.dur = duracionViaje(destino - viaje.desde, { innerHeight: window.innerHeight });
  }
  window.addEventListener('resize', alCambiarElTamano);

  /**
   * Posición de scroll a la que lleva cada parada, o null si esa parada no existe.
   * Un paso del relato se cuadra con la pantalla; la tarjeta de cierre no mide una
   * pantalla, así que a ella se llega dejando su borde justo debajo de la cabecera.
   */
  function destinoDeParada(parada: number): number | null {
    const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    if (esCierre(parada)) {
      return objetivoCierre({
        topAbs: cierre!.getBoundingClientRect().top + window.scrollY,
        altoHeader: altoHeader(),
        maxScroll,
      });
    }
    const el = stepEls[parada];
    if (!el) return null;
    return objetivoScroll({ topAbs: el.getBoundingClientRect().top + window.scrollY, maxScroll });
  }

  /**
   * Lleva la vista a la parada pedida. Normalmente es scrollama quien luego marca el
   * paso como activo; si al acabar el viaje no lo ha hecho (pestaña en segundo plano,
   * por ejemplo), lo aplicamos nosotros al cerrar el salto. La tarjeta de cierre no la
   * canta nadie: esa siempre la aplica el cierre del salto.
   */
  function irAPaso(parada: number) {
    const y = destinoDeParada(parada);
    if (y === null) return;
    paradaPedida = parada;
    pintarMandos();
    viajarA(y);
  }

  /**
   * Desplaza la pantalla hasta `y` con una animación propia, no con la del navegador.
   *
   * `scrollTo({ behavior: 'smooth' })` reinicia su curva en cada llamada: pulsando
   * "siguiente" dos o tres veces seguidas se quedaba casi parado, dejaba de emitir
   * eventos de scroll, y el detector de "scroll detenido" daba el salto por
   * interrumpido y devolvía los mandos al paso que se veía. Resultado: los clics se
   * perdían y la pantalla acababa a medio camino entre dos pasos.
   *
   * Animándolo aquí sabemos en todo momento si hay un viaje en marcha, se puede
   * reapuntar a mitad de camino sin frenarlo, y acaba clavado en el destino.
   */
  function viajarA(y: number) {
    const desde = window.scrollY;
    if (Math.abs(y - desde) <= TOLERANCIA_SCROLL || !suave()) {
      cancelarViaje();
      window.scrollTo({ top: y, behavior: 'auto' });
      cerrarSalto();
      return;
    }
    viaje = { desde, hasta: y, t0: performance.now(), dur: duracionViaje(y - desde, { innerHeight: window.innerHeight }) };
    if (cuadro === undefined) cuadro = requestAnimationFrame(avanzarViaje);
  }

  function avanzarViaje(ahora: number) {
    cuadro = undefined;
    if (!viaje) return;
    const k = viaje.dur > 0 ? (ahora - viaje.t0) / viaje.dur : 1;
    const y = viaje.desde + (viaje.hasta - viaje.desde) * suavizado(k);
    // Un destino imposible no se persigue: se corta en vez de dejar el bucle de
    // animación pidiendo cuadros para siempre contra una posición que no existe.
    if (!Number.isFinite(y)) {
      cancelarViaje();
      cerrarSalto();
      return;
    }
    window.scrollTo({ top: Math.round(y), behavior: 'auto' });
    if (k >= 1) {
      viaje = null;
      cerrarSalto();
      return;
    }
    cuadro = requestAnimationFrame(avanzarViaje);
  }

  function cancelarViaje() {
    if (cuadro !== undefined) cancelAnimationFrame(cuadro);
    cuadro = undefined;
    viaje = null;
  }

  /** Da por terminado un salto y aplica la parada pedida si scrollama no la cantó. */
  function cerrarSalto() {
    if (paradaVisible !== paradaPedida) aplicarParada(paradaPedida);
    anotarSiSeVeElRecorrido();
  }

  /**
   * Deja las cuentas y los mandos en una parada, sin tocar los gráficos. Lo que hace
   * falta cuando la parada cambia pero el paso que se ve es el mismo.
   */
  function asentarParada(parada: number) {
    paradaVisible = parada;
    // Mientras un viaje propio sigue en marcha, las paradas que scrollama va cantando
    // por el camino no tocan a dónde apuntan los mandos: manda el destino. En cuanto
    // el viaje acaba, la parada que se ve vuelve a mandar también sobre ellos, venga
    // de un salto o de que el usuario se desplazara a mano.
    if (!viaje) paradaPedida = parada;
    pintarCuentas(parada);
    pintarMandos();
    // El reloj de la reproducción se reengancha a la parada que de verdad está activa.
    programarAvance(parada);
  }

  /**
   * Deja el recorrido en una parada. Si es un paso del relato, lo pinta entero
   * (gráficos incluidos); si es la tarjeta de cierre, el escenario ya no se ve, así
   * que solo se mueven las cuentas y los mandos.
   */
  function aplicarParada(parada: number) {
    if (esCierre(parada)) {
      if (paradaVisible === CIERRE) return;
      asentarParada(CIERRE);
      return;
    }
    // Volver de la tarjeta de cierre al último paso no cambia ni un gráfico, porque ya
    // son los de ese paso: `aplicar` se daría por hecho y saldría sin tocar nada, y el
    // contador se quedaría marcando la tarjeta. Las cuentas sí hay que moverlas.
    if (aplicado && parada === pasoVisible && paradaVisible !== parada) {
      asentarParada(parada);
      return;
    }
    aplicar(parada);
  }

  /**
   * Abandona el viaje en marcha. A partir de aquí manda el paso que se esté viendo: es
   * lo que pasa cuando el usuario se desplaza por su cuenta a mitad de un salto.
   */
  function soltarSalto() {
    cancelarViaje();
    if (paradaPedida === paradaVisible) return;
    paradaPedida = paradaVisible;
    pintarMandos();
  }

  // El scroll se considera detenido cuando deja de haber eventos durante un momento.
  window.addEventListener('scroll', () => {
    if (asentar !== undefined) clearTimeout(asentar);
    asentar = window.setTimeout(alDetenerseElScroll, ESPERA_ASENTADO);
  }, { passive: true });

  function alDetenerseElScroll() {
    asentar = undefined;
    // Con un viaje propio en marcha no hay nada que deducir: el destino ya se sabe, y
    // es el propio viaje el que lo aplica al terminar. Antes se intentaba adivinar aquí
    // si el salto había llegado o lo habían interrumpido, y esa adivinanza era justo
    // la que perdía los clics cuando la animación del navegador se atascaba.
    if (viaje) return;
    // Sin salto en vuelo, el paso lo manda la posición de la pantalla. Normalmente
    // scrollama ya lo ha cantado y esto no cambia nada; cuando sus avisos no llegan,
    // es lo que evita que el contador y los gráficos se queden en otro paso.
    const parada = paradaVisibleEn({
      tops: stepEls.map((el) => el.getBoundingClientRect().top + window.scrollY),
      topCierre: cierre ? cierre.getBoundingClientRect().top + window.scrollY : undefined,
      scrollY: window.scrollY,
      innerHeight: window.innerHeight,
      offset: offsetDisparo,
    });
    if (parada !== paradaVisible) aplicarParada(parada);
    anotarSiSeVeElRecorrido();
  }

  function avanzar(delta: number) {
    const destino = pasoDestino(paradaPedida, paradas, delta);
    if (destino !== paradaPedida || destino !== paradaVisible) irAPaso(destino);
    return destino;
  }

  /** Estado de los botones. Se guía por la parada pedida para no poder atascarse. */
  function pintarMandos() {
    const estado = estadoMandos(paradaPedida, paradas);
    if (botonAnterior) botonAnterior.disabled = estado.atrasApagado;
    if (botonSiguiente) botonSiguiente.disabled = estado.adelanteApagado;
  }

  /**
   * Pinta la barra de avance. Parada marca el paso de golpe; en reproducción corre
   * hacia el paso siguiente durante lo que dura el actual. Ese avance continuo es lo
   * que deja ver que el relato está en marcha mientras se lee un paso largo: sin él,
   * pulsar reproducir parecía no hacer nada hasta el primer salto.
   */
  function pintarBarra(parada: number, corriendo: boolean) {
    if (!relleno) return;
    if (corriendo && !esUltimaParada(parada, paradas)) {
      // Hay que plantar la barra en la parada actual y recalcular antes de lanzarla
      // hacia la siguiente: en un solo recálculo el navegador funde los dos cambios y
      // la barra arrancaría su viaje desde la parada anterior.
      relleno.style.transition = 'none';
      relleno.style.width = `${fraccionAvance(parada, paradas) * 100}%`;
      void relleno.offsetWidth;
      relleno.style.transition = `width ${duraciones[parada] ?? 6000}ms linear`;
      relleno.style.width = `${fraccionAvance(parada + 1, paradas) * 100}%`;
    } else {
      relleno.style.transition = '';
      relleno.style.width = `${fraccionAvance(parada, paradas) * 100}%`;
    }
  }

  /** Barra, contador y etiquetas del deslizador, que van siempre juntos. */
  function pintarCuentas(parada: number) {
    pintarBarra(parada, false);
    if (actualEl) actualEl.textContent = String(parada + 1);
    if (barra) {
      barra.setAttribute('aria-valuenow', String(parada + 1));
      barra.setAttribute('aria-valuetext', `Paso ${parada + 1} de ${paradas}`);
    }
  }

  function pararTemporizador() {
    if (temporizador !== undefined) {
      clearTimeout(temporizador);
      temporizador = undefined;
    }
  }

  function pintarPlay() {
    if (!botonPlay) return;
    botonPlay.setAttribute('aria-pressed', String(reproduciendo));
    botonPlay.setAttribute('aria-label', reproduciendo ? 'Pausar el recorrido' : 'Reproducir el recorrido');
    botonPlay.title = reproduciendo ? 'Pausar' : 'Reproducir';
    botonPlay.dataset.estado = reproduciendo ? 'pausa' : 'play';
  }

  function pausar() {
    if (!reproduciendo) return;
    reproduciendo = false;
    pararTemporizador();
    pintarPlay();
    // La barra venía corriendo hacia la parada siguiente: se devuelve a la real.
    pintarBarra(paradaVisible, false);
  }

  function reproducir(desde = paradaVisible) {
    // Un recorrido de una sola parada no tiene nada que reproducir, y dejar el botón
    // en pausa para siempre es peor que no hacer nada.
    if (reproduciendo || paradas <= 1) return;
    reproduciendo = true;
    pintarPlay();
    // Desde la última parada, reproducir vuelve a empezar: si no, el botón no haría
    // nada y parecería roto. El reloj lo arranca `aplicar` al llegar al paso 0.
    if (esUltimaParada(desde, paradas)) {
      irAPaso(0);
      return;
    }
    // Encuadrar la parada actual antes de ponerse a contar. Sin esto, pulsar
    // reproducir con la pantalla a medio camino entre dos pasos, o todavía por encima
    // del recorrido, no movía absolutamente nada durante los segundos que dura el paso.
    irAPaso(desde);
    // El reloj se arranca aquí y no en `aplicar`: cuando ya estábamos encuadrados en
    // esta parada, `irAPaso` no vuelve a aplicarla y nadie programaría el avance.
    programarAvance(desde);
  }

  /**
   * Agenda el salto a la parada siguiente según lo que dura la que se está viendo. En
   * la última, que es la tarjeta de cierre cuando la hay, se detiene: ahí se acabó.
   */
  function programarAvance(parada: number) {
    pararTemporizador();
    if (!reproduciendo) return;
    if (esUltimaParada(parada, paradas)) {
      pausar();
      return;
    }
    pintarBarra(parada, true);
    temporizador = window.setTimeout(() => {
      temporizador = undefined;
      if (reproduciendo) avanzar(1);
    }, duraciones[parada] ?? 6000);
  }

  function aplicar(step: number) {
    // Aplicar dos veces el mismo paso no cambia nada en pantalla, pero reinicia el
    // reloj de la reproducción y el viaje de la barra. Y scrollama canta el mismo paso
    // más de una vez al cruzarlo, así que el paso duraba de más en automático.
    if (aplicado && step === pasoVisible) return;
    aplicado = true;
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

    // El resaltado del subtítulo se pinta aquí, con todo lo demás del paso: si se
    // quedara solo en la devolución de llamada de scrollama, un salto que ella no
    // confirme movería el gráfico y dejaría el texto apagado.
    stepEls.forEach((el) => el.classList.toggle('activo', Number(el.dataset.step) === step));

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

    // El botón de salida estorba en el primer paso, donde no hay nada a lo que volver.
    if (botonInicio) botonInicio.hidden = step < 1;

    pasoVisible = step;
    asentarParada(step);
  }

  if (botonInicio) {
    botonInicio.addEventListener('click', () => {
      pausar();
      // Por el mismo carril que los mandos, no por `irAlInicioDelRecorrido`: ese
      // desplaza la página sin que el motor sepa que hay un viaje en marcha, y los
      // clics en "siguiente" que llegaran mientras viajaba se perdían, porque al
      // pararse el scroll lejos del destino el salto se daba por interrumpido.
      irAPaso(0);
    });
  }

  // La tarjeta de cierre de la cápsula vive fuera de la sección y pide volver al
  // principio por este evento, para que su viaje también sea un salto del motor.
  container.addEventListener(EVENTO_INICIO, (ev) => {
    ev.preventDefault();
    pausar();
    irAPaso(0);
  });

  // Play de la entrada de la cápsula: baja al primer paso y lo cuenta solo.
  container.addEventListener(EVENTO_REPRODUCIR, (ev) => {
    ev.preventDefault();
    pausar();
    reproducir(0);
  });

  botonAnterior?.addEventListener('click', () => { pausar(); avanzar(-1); });
  botonSiguiente?.addEventListener('click', () => { pausar(); avanzar(1); });
  botonPlay?.addEventListener('click', () => (reproduciendo ? pausar() : reproducir()));

  // Picar en la barra salta al paso correspondiente; con la barra enfocada, las
  // flechas la mueven paso a paso (es un slider, no un adorno).
  if (barra) {
    barra.addEventListener('click', (ev) => {
      const r = barra.getBoundingClientRect();
      if (r.width <= 0) return;
      pausar();
      irAPaso(pasoDeFraccion((ev.clientX - r.left) / r.width, paradas));
    });
    barra.addEventListener('keydown', (ev) => {
      const paso = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1 }[ev.key];
      if (paso === undefined && ev.key !== 'Home' && ev.key !== 'End') return;
      ev.preventDefault();
      pausar();
      if (ev.key === 'Home') irAPaso(0);
      else if (ev.key === 'End') irAPaso(ultimaParada(paradas));
      else avanzar(paso!);
    });
  }

  // Flechas del teclado mientras el escenario está a la vista. No se tocan la barra
  // espaciadora ni las teclas de página: ésas son del navegador y quitarlas molesta.
  document.addEventListener('keydown', (ev) => {
    if (ev.key !== 'ArrowLeft' && ev.key !== 'ArrowRight') return;
    if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
    const activo = document.activeElement as HTMLElement | null;
    // Si el foco está escribiendo en algún sitio, las flechas son suyas.
    if (activo && (activo.isContentEditable || /^(input|textarea|select)$/i.test(activo.tagName))) return;
    if (activo && activo.classList.contains('barra')) return; // ya lo lleva su propio manejador
    // Sin escenario no hay nada en pantalla que gobernar con las flechas. La guarda
    // es barata y evita que un armazón distinto reviente en cada pulsación.
    const stage = container!.querySelector('.scrolly-stage');
    if (!stage) return;
    const r = stage.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight) return; // el recorrido no está en pantalla
    ev.preventDefault();
    pausar();
    avanzar(ev.key === 'ArrowRight' ? 1 : -1);
  });

  // Si el usuario toma el control, la reproducción se para y el viaje en marcha se
  // abandona. Va colgado de la ventana entera, no de la sección: la rueda girada sobre
  // la línea de créditos, que vive fuera, también es el usuario tomando el mando. Los
  // viajes propios no disparan rueda ni toque, así que esto no se dispara a sí mismo.
  const soltarMando = () => {
    pausar();
    soltarSalto();
  };
  window.addEventListener('wheel', soltarMando, { passive: true });
  window.addEventListener('touchstart', soltarMando, { passive: true });

  // Las teclas que desplazan la página se dejan al navegador, pero son igual de
  // claramente el usuario tomando el mando que la rueda.
  const TECLAS_DE_SCROLL = [' ', 'Spacebar', 'PageDown', 'PageUp', 'Home', 'End', 'ArrowUp', 'ArrowDown'];
  window.addEventListener('keydown', (ev) => {
    if (TECLAS_DE_SCROLL.includes(ev.key) && !ev.defaultPrevented) soltarMando();
  });

  // El marcado no sabe si la página trae tarjeta de cierre, así que el total del
  // contador y del deslizador se fija aquí.
  if (totalEl) totalEl.textContent = String(paradas);
  if (barra) barra.setAttribute('aria-valuemax', String(paradas));

  aplicar(0);

  const scroller = scrollama();
  scroller
    .setup({ step: '.scrolly .step', offset: cfg.offset ?? 0.75 })
    .onStepEnter((r: { element: HTMLElement }) => {
      aplicar(Number(r.element.dataset.step ?? '0'));
    });
  window.addEventListener('resize', scroller.resize);
}
