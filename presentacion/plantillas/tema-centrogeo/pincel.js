/* Pincel para dibujar sobre la lámina, a mano alzada y en vivo.

   Tecla D sobre el deck. Enciende el lienzo y la barra de pinceles; Escape, la
   misma D o el botón Salir lo apagan. Ctrl+Z deshace el último trazo, igual que
   el botón Deshacer de la barra. Está pensado para la tableta gráfica:
   el trazo responde a la presión del lápiz, la punta de borrar borra, y lo que
   se apoya con la mano no pinta.

   Por qué el lienzo va dentro de .slides y no sobre la ventana: reveal escala
   la lámina de 1280x720 con un transform sobre .slides, así que un hijo de
   .slides hereda esa escala y queda anclado a la lámina. Los trazos se guardan
   en coordenadas de lámina, de 0 a 1280 y de 0 a 720, y se redibujan cuando
   cambia la escala. Así un trazo sigue donde se dejó al redimensionar la
   ventana, al entrar en pantalla completa y al compartir pantalla en Zoom, que
   es donde se notaría el desajuste.

   Ojo con .reveal .slides, que trae pointer-events:none de fábrica: el lienzo
   tiene que declarar pointer-events:auto para recibir el lápiz, y volver a
   none al apagarse para no estorbar al anotador ni a los enlaces de la lámina.

   Los trazos viven en memoria, en un Map indexado por el elemento de cada
   lámina, no por su id: reveal le quita el id a la lámina visible mientras está
   en pantalla. Cada lámina guarda los suyos, así que al volver a una lámina
   reaparece lo que se dibujó en ella. No se guardan en disco ni en
   localStorage: al recargar la página se pierden, y eso es a propósito, el
   dibujo es de la clase que se está dando.

   Nada de esto viaja al paquete del grupo: tools/empaquetar.py quita este
   script como quita el anotador y el apuntador, y su auditoría para si sobrevive.

   El ancho del trazo sale de la presión, event.pressure, con el grosor elegido
   como techo. Un lápiz sin presión reporta 0.5 constante, así que el trazo sale
   de ancho constante sin necesidad de detectar nada. El ratón dibuja con el
   grosor elegido, sin modular. */
(function () {
  "use strict";
  if (!window.Reveal || !Reveal.addKeyBinding) return;

  const ANCHO = 1280, ALTO = 720;        // el lienzo de reveal, en coordenadas de lámina
  const COLORES = [["guinda", "#A42145"], ["verde", "#155B4E"], ["dorado", "#E7D395"],
                   ["negro", "#111111"], ["blanco", "#FFFFFF"]];
  const GROSORES = [["fino", 3], ["medio", 6], ["grueso", 13]];
  const BORRADOR = 3.5;                  // el borrador, veces el grosor elegido
  const PISO = 0.35, RANGO = 0.65;       // ancho = grosor * (PISO + RANGO * presión)
  const TOPE_DPR = 2;                    // más resolución de respaldo no se ve y cuesta
  const TOPE_PUNTOS = 20000;             // techo de un trazo, ver cerrar() y anadir()

  const CSS = `
.pn-lienzo { position: absolute; left: 0; top: 0; width: ${ANCHO}px; height: ${ALTO}px;
  z-index: 20; pointer-events: none; }
body.pn-activo .pn-lienzo { pointer-events: auto; cursor: crosshair; touch-action: none; }
.pn-lienzo.pn-oculto { display: none; }
.pn-barra { position: fixed; left: 50%; bottom: 14px; transform: translateX(-50%);
  z-index: 9990; display: none; align-items: center; gap: 14px; padding: 7px 12px;
  border-radius: 10px; background: rgba(22, 22, 22, 0.93);
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.4);
  font-family: 'Noto Sans', 'Segoe UI', system-ui, sans-serif; }
body.pn-activo .pn-barra { display: flex; }
.pn-grupo { display: flex; align-items: center; gap: 6px; }
.pn-grupo + .pn-grupo { border-left: 1px solid rgba(255, 255, 255, 0.28); padding-left: 14px; }
.pn-barra button { font: inherit; font-size: 14px; color: #fff; background: transparent;
  border: 1px solid transparent; border-radius: 6px; padding: 5px 9px; cursor: pointer;
  line-height: 1; }
.pn-barra button:hover { background: rgba(255, 255, 255, 0.14); }
.pn-barra button:focus-visible { outline: 2px solid #E7D395; outline-offset: 1px; }
.pn-barra button[aria-pressed="true"] { border-color: #E7D395; background: rgba(231, 211, 149, 0.22); }
.pn-color, .pn-grosor { padding: 4px; width: 30px; height: 30px; display: flex;
  align-items: center; justify-content: center; }
.pn-color span { width: 18px; height: 18px; border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.55); display: block; }
.pn-grosor span { background: #fff; border-radius: 50%; display: block; }
.pn-salir { font-weight: 700; }
`;

  // Los trazos de cada lámina, indexados por su elemento. Ver la nota de arriba.
  const trazos = new Map();
  let color = COLORES[0][1], grosor = GROSORES[1][1];
  let borrando = false, activo = false;
  let lienzo = null, ctx = null, barra = null;
  let trazo = null, puntero = null;

  const lamina = () => Reveal.getCurrentSlide();

  function pila() {
    const sec = lamina();
    if (!sec) return [];
    if (!trazos.has(sec)) trazos.set(sec, []);
    return trazos.get(sec);
  }

  // -- el lienzo -------------------------------------------------------------

  function montar() {
    if (lienzo) return;
    document.head.insertAdjacentHTML("beforeend", "<style>" + CSS + "</style>");
    lienzo = document.createElement("canvas");
    lienzo.className = "pn-lienzo";
    lienzo.setAttribute("aria-hidden", "true");
    document.querySelector(".reveal .slides").appendChild(lienzo);
    ctx = lienzo.getContext("2d");
    lienzo.addEventListener("pointerdown", abajo);
    lienzo.addEventListener("pointermove", mueve);
    lienzo.addEventListener("pointerup", arriba);
    lienzo.addEventListener("pointercancel", arriba);
    // El lápiz no debe abrir el menú contextual con el botón lateral.
    lienzo.addEventListener("contextmenu", (e) => e.preventDefault());
    montarBarra();
    dimensionar();
  }

  /* La caja del lienzo mide siempre 1280x720 en coordenadas de lámina, pero su
     mapa de píxeles se ajusta a lo que ocupa en pantalla, escala de reveal por
     densidad del monitor, para que el trazo no salga pixelado en el proyector.
     Cambiar width o height borra el lienzo y reinicia el contexto, así que
     después hay que redibujar. */
  function dimensionar() {
    if (!lienzo) return;
    const escala = (typeof Reveal.getScale === "function" && Reveal.getScale()) || 1;
    const dpr = Math.min(window.devicePixelRatio || 1, TOPE_DPR);
    const px = Math.max(1, Math.round(ANCHO * escala * dpr));
    const py = Math.max(1, Math.round(ALTO * escala * dpr));
    if (lienzo.width !== px || lienzo.height !== py) {
      lienzo.width = px;
      lienzo.height = py;
    }
    redibujar();
  }

  function redibujar() {
    if (!ctx) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, lienzo.width, lienzo.height);
    // de coordenadas de lámina a píxeles del lienzo
    ctx.setTransform(lienzo.width / ANCHO, 0, 0, lienzo.height / ALTO, 0, 0);
    for (const t of pila()) pintar(t);
  }

  const ancho = (t, p) => (t.borrador ? t.grosor * BORRADOR
                           : t.lapiz ? t.grosor * (PISO + RANGO * p) : t.grosor);

  function preparar(t) {
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.globalCompositeOperation = t.borrador ? "destination-out" : "source-over";
    ctx.strokeStyle = t.borrador ? "#000" : t.color;
    ctx.fillStyle = ctx.strokeStyle;
  }

  /* Un trazo es una polilínea con un ancho por punto, así que se dibuja segmento
     a segmento con el ancho medio de sus dos extremos. Con las puntas y las
     uniones redondeadas la costura no se ve. El borrador es el mismo trazo con
     destination-out, que quita lo que haya debajo y deja pasar lo que se dibuje
     después. */
  function pintar(t) {
    const pts = t.puntos;
    if (!pts.length) return;
    ctx.save();
    preparar(t);
    if (pts.length === 1) {
      ctx.beginPath();
      ctx.arc(pts[0].x, pts[0].y, ancho(t, pts[0].p) / 2, 0, Math.PI * 2);
      ctx.fill();
    } else {
      for (let i = 1; i < pts.length; i++) segmento(t, pts[i - 1], pts[i]);
    }
    ctx.restore();
  }

  function segmento(t, a, b) {
    ctx.beginPath();
    ctx.lineWidth = (ancho(t, a.p) + ancho(t, b.p)) / 2;
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }

  // -- el lápiz --------------------------------------------------------------

  function punto(e) {
    const r = lienzo.getBoundingClientRect();
    return {
      x: (e.clientX - r.left) / r.width * ANCHO,
      y: (e.clientY - r.top) / r.height * ALTO,
      p: e.pressure > 0 ? Math.min(e.pressure, 1) : 0.5,
    };
  }

  const esBorrador = (e) => e.pointerType === "eraser" || e.button === 5 ||
                            (e.buttons & 32) !== 0;

  /* Cierra el trazo en curso, si lo hay, y suelta la captura del lápiz. Se llama
     desde tres sitios, y en los tres por el mismo motivo: un trazo que se queda
     abierto no vuelve a recibir ningún evento, porque mueve() y arriba() solo
     atienden al pointerId que lo empezó, así que se queda para siempre en la
     pila de su lámina sin poder cerrarse. Pasaba al cambiar de lámina con el
     lápiz apoyado, al apagar el pincel a media pincelada, y con un segundo
     lápiz o un pointerId que la tableta reasigna en mitad del trazo. */
  function cerrar() {
    if (!trazo) return;
    if (!trazo.puntos.length) {
      const p = pila();
      if (p[p.length - 1] === trazo) p.pop();
    }
    if (puntero !== null) {
      try { lienzo.releasePointerCapture(puntero); } catch (err) { /* ya no estaba */ }
    }
    trazo = null;
    puntero = null;
  }

  function abajo(e) {
    if (!activo || !ctx) return;
    if (e.pointerType === "touch") return;            // la mano apoyada no pinta
    if (e.pointerType === "mouse" && e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    cerrar();                                         // nunca dos trazos a la vez
    puntero = e.pointerId;
    try { lienzo.setPointerCapture(e.pointerId); } catch (err) { /* sin captura se sigue */ }
    trazo = { color: color, grosor: grosor, borrador: borrando || esBorrador(e),
              lapiz: e.pointerType === "pen", puntos: [] };
    pila().push(trazo);
    ctx.save();
    preparar(trazo);
    anadir(e);
    ctx.restore();
  }

  function mueve(e) {
    if (!ctx || !trazo || e.pointerId !== puntero) return;
    e.preventDefault();
    e.stopPropagation();
    ctx.save();
    preparar(trazo);
    anadir(e);
    ctx.restore();
  }

  /* getCoalescedEvents devuelve las muestras que el navegador agrupó en un solo
     pointermove: sin ellas un trazo rápido sale poligonal, y la tableta manda
     muchas más muestras que fotogramas hay. Los eventos sintéticos de las
     pruebas no la traen, de ahí la comprobación. */
  function anadir(e) {
    let lista = [e];
    if (typeof e.getCoalescedEvents === "function") {
      const c = e.getCoalescedEvents();
      if (c && c.length) lista = c;
    }
    for (const ev of lista) {
      const pts = trazo.puntos;
      // Un trazo de 20000 puntos son más de cien segundos de lápiz apoyado sin
      // levantarlo, que no es una anotación sino un fallo del driver. Lo ya
      // dibujado se queda en pantalla; lo que se deja de guardar es lo que
      // vendría después.
      if (pts.length >= TOPE_PUNTOS) return;
      const q = punto(ev);
      const prev = pts[pts.length - 1];
      pts.push(q);
      if (prev) segmento(trazo, prev, q);
      else {
        ctx.beginPath();
        ctx.arc(q.x, q.y, ancho(trazo, q.p) / 2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  function arriba(e) {
    if (!trazo || e.pointerId !== puntero) return;
    cerrar();
  }

  // -- la barra --------------------------------------------------------------

  function montarBarra() {
    const swatch = (n, v, i) =>
      '<button type="button" class="pn-color" data-pn="color" data-valor="' + v + '"' +
      ' title="Color ' + n + '" aria-label="Color ' + n + '" aria-pressed="' + (i === 0) + '">' +
      '<span style="background: ' + v + '"></span></button>';
    const punta = (n, v, i) =>
      '<button type="button" class="pn-grosor" data-pn="grosor" data-valor="' + v + '"' +
      ' title="Trazo ' + n + '" aria-label="Trazo ' + n + '" aria-pressed="' + (i === 1) + '">' +
      '<span style="width: ' + (4 + i * 5) + 'px; height: ' + (4 + i * 5) + 'px"></span></button>';
    barra = document.createElement("div");
    barra.className = "pn-barra";
    barra.setAttribute("role", "toolbar");
    barra.setAttribute("aria-label", "Pincel");
    barra.innerHTML =
      '<div class="pn-grupo">' + COLORES.map((c, i) => swatch(c[0], c[1], i)).join("") + "</div>" +
      '<div class="pn-grupo">' + GROSORES.map((g, i) => punta(g[0], g[1], i)).join("") + "</div>" +
      '<div class="pn-grupo">' +
      '<button type="button" data-pn="borrador" aria-pressed="false" title="Borrador">Borrador</button>' +
      '<button type="button" data-pn="deshacer" title="Deshacer el último trazo, Ctrl+Z">Deshacer</button>' +
      '<button type="button" data-pn="limpiar" title="Limpiar esta lámina">Limpiar</button>' +
      '<button type="button" class="pn-salir" data-pn="salir" title="Salir del pincel, tecla D">Salir</button>' +
      "</div>";
    document.body.appendChild(barra);
    barra.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-pn]");
      if (!b) return;
      const que = b.dataset.pn;
      if (que === "color") {
        color = b.dataset.valor;
        borrando = false;
        marcar("color", b);
        marcar("borrador", null);
      } else if (que === "grosor") {
        grosor = parseFloat(b.dataset.valor);
        marcar("grosor", b);
      } else if (que === "borrador") {
        borrando = !borrando;
        b.setAttribute("aria-pressed", String(borrando));
      } else if (que === "deshacer") {
        deshacer();
      } else if (que === "limpiar") {
        trazos.set(lamina(), []);
        redibujar();
      } else if (que === "salir") {
        apagar();
      }
      // Sin esto el botón se queda con el foco y la barra espaciadora lo vuelve
      // a pulsar en vez de pasar de lámina.
      b.blur();
    });
  }

  function marcar(grupo, cual) {
    barra.querySelectorAll('button[data-pn="' + grupo + '"]').forEach((b) => {
      b.setAttribute("aria-pressed", String(b === cual));
    });
  }

  /* Deshacer, con dos vías de entrada: el botón de la barra y Ctrl+Z. Cierra
     antes el trazo en curso, así que deshacer con el lápiz apoyado quita el
     trazo que se estaba dibujando y no deja ninguno abierto. */
  function deshacer() {
    cerrar();
    pila().pop();
    redibujar();
  }

  // -- encendido y apagado ---------------------------------------------------

  function encender() {
    montar();
    activo = true;
    document.body.classList.add("pn-activo");
    dimensionar();
  }

  function apagar() {
    cerrar();
    activo = false;
    borrando = false;
    document.body.classList.remove("pn-activo");
    if (barra) marcar("borrador", null);
  }

  const alternar = () => (activo ? apagar() : encender());

  Reveal.addKeyBinding({ keyCode: 68, key: "D", description: "Dibujar sobre la lámina" }, alternar);

  /* Con el foco en una caja de texto las teclas son de quien escribe, no del
     pincel: el anotador abre un textarea para cada nota y para reescribir el
     guion, y el apuntador tiene campos para sus alarmas. Sin esta guarda, el
     pincel encendido se quedaba con el Ctrl+Z de la caja, y de paso borraba un
     trazo que nadie había pedido borrar. */
  const enCampo = (el) => !!el && (el.isContentEditable === true ||
                          /^(?:input|textarea|select)$/i.test(el.tagName || ""));

  /* Las dos teclas del pincel van en fase de captura y solo mientras está
     encendido. Escape, porque si no reveal abre la vista general y el anotador
     suelta su selección antes de que llegue aquí. Ctrl+Z, que es lo que la mano
     hace sola. Se descartan las variantes con Shift y con Alt: no hay rehacer
     que ofrecer, y quedarse con la tecla sin hacer nada sería peor que dejarla
     pasar. */
  document.addEventListener("keydown", (e) => {
    if (!activo) return;
    if (enCampo(e.target) || enCampo(document.activeElement)) return;
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      apagar();
      return;
    }
    if (e.ctrlKey && !e.shiftKey && !e.altKey && (e.key === "z" || e.key === "Z")) {
      e.preventDefault();
      e.stopPropagation();
      deshacer();
    }
  }, true);

  // Cambiar de lámina con el lápiz apoyado cerraba el trazo en la lámina vieja
  // y lo seguía pintando en la nueva. Se cierra antes de redibujar.
  Reveal.on("slidechanged", () => { cerrar(); redibujar(); });
  Reveal.on("resize", dimensionar);
  window.addEventListener("resize", dimensionar);
  // En la vista general las láminas se escalan y se mueven: el lienzo no las
  // sigue, así que se esconde y el pincel se apaga.
  Reveal.on("overviewshown", () => {
    apagar();
    if (lienzo) lienzo.classList.add("pn-oculto");
  });
  Reveal.on("overviewhidden", () => {
    if (lienzo) lienzo.classList.remove("pn-oculto");
    dimensionar();
  });
})();
