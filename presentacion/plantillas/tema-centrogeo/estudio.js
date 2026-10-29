/* Lector de estudio: las notas con las que Alberto entiende el tema, con la
 * lámina delante. Tecla I sobre el deck.
 *
 * Alberto lo pidió el 1 de octubre de 2026, y con un diagnóstico concreto: es muy
 * visual, para entender el tema recurre a las diapositivas, y cuando algo no le
 * queda claro en la lámina la única salida que tenía era el guion de orador, que
 * está escrito para DECIRSE en voz alta y no para explicarle el tema a quien lo
 * lee. Esto es la otra salida.
 *
 * Enseña dos bloques de la lámina en curso, en este orden y rotulados, porque no
 * tienen el mismo destinatario y confundirlos es lo único que puede filtrar al
 * grupo algo que solo debe ver él:
 *
 *   <aside class="didactica">  la nota didáctica, SOLO de Alberto. Qué pasa en
 *                              esta lámina, de dónde sale el concepto, cómo se
 *                              explica y en qué orden. No viaja al paquete:
 *                              tools/empaquetar.py la quita y su auditoría se
 *                              niega a entregar el archivo si sobrevive.
 *   <aside class="apuntes">    el apunte de estudio, que SÍ recibe el grupo.
 *
 * Va en el deck de trabajo y nunca en el paquete, así que empaquetar.py también
 * quita este script, igual que hace con el apuntador, el anotador y el pincel.
 *
 * DOS FORMAS DE LEERLO, y Alberto pidió las dos pudiendo elegir:
 *
 *   Panel al costado. La lámina se ENCOGE para dejarle sitio en vez de taparse,
 *   que es lo que permite leer el texto y mirar el dibujo a la vez. Es la de
 *   fábrica y la que sirve con una sola pantalla.
 *
 *   Ventana aparte, para estudiar con dos monitores, con las diapositivas a
 *   pantalla completa en uno. Recuerda su tamaño y su posición, así que se
 *   coloca una vez y se abre igual el resto del cuatrimestre.
 *
 * La elección se recuerda en localStorage, como hace el apuntador con su tecla V,
 * y se cambia con el botón Ventana o Panel que llevan las dos vistas.
 *
 * Aquí la ventana es emergente y NO de imagen sobre imagen, al contrario que el
 * apuntador. La de imagen sobre imagen se queda por encima de todo y no se puede
 * maximizar, que es lo que hace falta para presentar; esto es para estudiar
 * sentado, donde lo que se quiere es una ventana grande en el otro monitor.
 *
 * Nada que ver con el apuntador, aunque los dos muestren texto al lado de la
 * lámina: el apuntador es el teleprompter, lee el guion párrafo a párrafo, mide
 * seis relojes y gobierna el recorte en vivo. Esto no tiene reloj ninguno.
 *
 * MathJax. Los dos bloques van ocultos en la lámina, así que la configuración del
 * deck los excluye con ignoreHtmlClass y no se componen al cargar. Se componen
 * aquí, al copiarlos, igual que hace el lector del paquete. Para la ventana hay
 * un paso más: MathJax solo trabaja sobre el documento donde vive, así que el
 * texto se compone primero en una fragua escondida de este documento y el
 * resultado se importa ya compuesto. Sin eso, en la ventana se leería el LaTeX
 * en crudo. La comprobación de si hace falta componer mira si queda un \( en el
 * texto: así funciona igual en un deck cuya configuración todavía no excluya la
 * clase nueva, donde el bloque llega compuesto de fábrica.
 *
 * El contenido de la ventana se escribe por el DOM y no con document.write, para
 * que la prueba pueda sustituir la ventana por un documento suelto. Ver el
 * comentario de escribirVentana.
 *
 * Su prueba de regresión es tools/prueba-estudio.py.
 */
(function () {
  if (typeof Reveal === "undefined") return;

  const LLAVE_MODO = "estudio:modo";
  const LLAVE_CAJA = "estudio:caja";
  const ANCHO = 560, ALTO = 820;

  const laminas = () => [...document.querySelectorAll(".reveal .slides > section")];
  const notaDe = (sec) => sec && sec.querySelector("aside.didactica");
  const apunteDe = (sec) => sec && sec.querySelector("aside.apuntes");
  const tituloDe = (sec) => {
    const h = sec && (sec.querySelector("h1,h2") || sec.querySelector(".titulo,.gracias"));
    return h ? h.textContent.trim() : "";
  };

  // Sin un solo bloque que leer no hay lector. Una sesión puede tener apuntes y
  // todavía ninguna nota didáctica, y entonces esto sirve igual: enseña el apunte
  // al lado de la lámina, que es algo que el deck de trabajo no sabía hacer.
  if (!laminas().some((s) => notaDe(s) || apunteDe(s))) return;

  const ESTILO = `
  .es-panel{position:fixed;top:0;right:0;bottom:0;width:440px;z-index:58;
    background:#FBFAF8;border-left:1px solid #DDD8CE;display:none;
    flex-direction:column;font:16px/1.62 'Noto Sans',system-ui,sans-serif;color:#2E2E2E}
  body.es-abierto .es-panel{display:flex}
  body.es-abierto .reveal{width:calc(100% - 440px)}
  .es-cab{padding:13px 18px 10px;border-bottom:1px solid #E4E0D8}
  .es-rot{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.09em;color:#8A8A8A}
  .es-tit{font-weight:600;font-size:17px;margin-top:6px;color:#A42145}
  .es-cuerpo{flex:1;overflow:auto;padding:14px 18px 22px}
  .es-cuerpo p{margin:0 0 12px}
  .es-cuerpo p:last-child{margin-bottom:0}
  .es-pie{display:flex;gap:8px;padding:10px 18px 14px;border-top:1px solid #E4E0D8}
  .es-pie button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:8px 12px;
    border:1px solid #D9C9CE;background:#fff;color:#A42145;border-radius:4px;cursor:pointer}
  .es-pie button:hover{background:#FCEEF2}
  .es-pie .es-cerrar{margin-left:auto;border-color:#DDD8CE;color:#7A7568}
  /* La fragua donde se compone el texto antes de llevarlo a la ventana. Tiene
     que estar en el documento y con ancho, porque MathJax mide para componer,
     pero fuera de la vista y sin estorbar al ratón. */
  .es-fragua{position:fixed;left:-10000px;top:0;width:760px;
    font:16px/1.6 'Noto Sans',system-ui,sans-serif;pointer-events:none}
  @media (max-width:980px){
    .es-panel{top:auto;left:0;width:auto;height:48%;border-left:0;border-top:1px solid #DDD8CE}
    body.es-abierto .reveal{width:100%;height:52%}
  }`;

  /* El rótulo de cada bloque dice de quién es, y eso no es decoración: es la
     única señal en pantalla de qué se queda conmigo y qué lee el grupo. */
  const CUERPO_ESTILO = `
  .es-marca{font:600 10px/1.3 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.08em;margin:0 0 7px;padding:4px 8px;border-radius:3px;display:inline-block}
  .es-marca.es-mia{background:#F3E2E7;color:#A42145}
  .es-marca.es-grupo{background:#F0EDE3;color:#7A7568}
  .es-bloque{margin:0 0 20px}
  .es-bloque:last-child{margin-bottom:0}
  .es-vacio{color:#8A8A8A;font-style:italic}
  .es-doc h2{font-size:16px;color:#A42145;margin:26px 0 8px;font-weight:600;cursor:pointer}
  .es-doc h2:first-child{margin-top:0}
  .es-doc h2 span{color:#8A8A8A;font-weight:400;margin-right:7px;font-variant-numeric:tabular-nums}
  .es-doc h2:hover{text-decoration:underline}
  .es-doc .es-sec{margin:30px 0 10px;padding-top:10px;border-top:2px solid #E7D395;
    font:600 13px/1.3 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.08em;color:#8A7A3A}
  .es-cuerpo cite[data-ref],.es-doc cite[data-ref]{font-style:normal;font-weight:600;
    font-size:.86em;vertical-align:baseline;color:#A42145;margin-left:.22em;white-space:nowrap}
  .es-cuerpo cite[data-ref]::before,.es-doc cite[data-ref]::before{content:"["}
  .es-cuerpo cite[data-ref]::after,.es-doc cite[data-ref]::after{content:"]"}`;

  document.head.insertAdjacentHTML("beforeend",
    "<style>" + ESTILO + CUERPO_ESTILO + "</style>");

  const panel = document.createElement("div");
  panel.className = "es-panel";
  panel.innerHTML =
    '<div class="es-cab"><div class="es-rot">Notas de estudio, solo para ti</div>' +
    '<div class="es-tit"></div></div>' +
    '<div class="es-cuerpo"></div>' +
    '<div class="es-pie">' +
    '<button type="button" data-es="todo">Toda la sesión</button>' +
    '<button type="button" data-es="ventana">Ventana aparte</button>' +
    '<button type="button" class="es-cerrar" data-es="cerrar">Cerrar</button></div>';
  document.body.appendChild(panel);

  const CSS_VENTANA =
    "body{margin:0;background:#FBFAF8;color:#2E2E2E;" +
    "font:17px/1.65 'Noto Sans',system-ui,sans-serif}" +
    "#cab{position:sticky;top:0;background:#FBFAF8;padding:14px 22px 10px;" +
    "border-bottom:1px solid #E4E0D8}" +
    "#rot{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;" +
    "letter-spacing:.09em;color:#8A8A8A}" +
    "#tit{font-weight:600;font-size:19px;margin-top:6px;color:#A42145}" +
    "#cuerpo{padding:16px 22px 28px}" +
    "#cuerpo p{margin:0 0 13px}" +
    "#pie{position:sticky;bottom:0;background:#FBFAF8;display:flex;gap:8px;" +
    "padding:10px 22px 14px;border-top:1px solid #E4E0D8}" +
    "#pie button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:9px 13px;" +
    "border:1px solid #D9C9CE;background:#fff;color:#A42145;border-radius:4px;cursor:pointer}" +
    "#pie button:hover{background:#FCEEF2}" +
    "#pie .der{margin-left:auto}" +
    CUERPO_ESTILO +
    CUERPO_ESTILO;

  const CUERPO_VENTANA =
    '<div id="cab"><div id="rot">Notas de estudio, solo para ti</div>' +
    '<div id="tit"></div></div><div id="cuerpo"></div>' +
    '<div id="pie"><button type="button" data-es="antes">Lámina anterior</button>' +
    '<button type="button" data-es="despues">Siguiente</button>' +
    '<button type="button" data-es="todo">Toda la sesión</button>' +
    '<button type="button" class="der" data-es="panel">Pasar a panel</button>' +
    "</div>";

  /* El contenido de la ventana se pone con el DOM y NO con document.write, y la
     razón es que así se puede probar. Con write, la única forma de simular la
     ventana en una prueba es un iframe, y un iframe recién insertado deja a
     Chrome headless esperando una navegación que no acaba: la prueba se colgaba
     en los 240 segundos del tiempo máximo sin medir nada. Escribiendo por el DOM
     sirve igual un documento suelto hecho con createHTMLDocument, que no navega.
     Las tres guardas de abajo son para eso: un documento recién creado puede no
     traer html, head ni body. */
  function escribirVentana(d) {
    if (!d.documentElement) d.appendChild(d.createElement("html"));
    if (!d.head) d.documentElement.insertBefore(d.createElement("head"),
                                                d.documentElement.firstChild);
    if (!d.body) d.documentElement.appendChild(d.createElement("body"));
    d.head.innerHTML = '<meta charset="utf-8"><title>Notas de estudio</title>' +
      "<style>" + CSS_VENTANA + "</style>";
    d.body.innerHTML = CUERPO_VENTANA;
  }

  let modo = localStorage.getItem(LLAVE_MODO) === "ventana" ? "ventana" : "panel";
  let win = null;
  let todo = false;

  /* ---------- el texto ---------- */

  function bloquesDe(sec) {
    const n = notaDe(sec), a = apunteDe(sec);
    let h = "";
    if (n) {
      h += '<div class="es-bloque"><div class="es-marca es-mia">' +
        "Para entenderlo y explicarlo, solo tú</div>" + n.innerHTML + "</div>";
    }
    if (a) {
      h += '<div class="es-bloque"><div class="es-marca es-grupo">' +
        "Apunte, esto lo recibe el grupo</div>" + a.innerHTML + "</div>";
    }
    // El hueco también informa: la portada, los separadores y la lámina de
    // cierre no llevan nota, y conviene que se vea que eso es lo normal.
    return h || '<p class="es-vacio">Esta lámina no lleva nota didáctica ni ' +
      "apunte. Las tienes todas seguidas en Toda la sesión.</p>";
  }

  function htmlTodo() {
    const partes = ['<div class="es-doc">'];
    laminas().forEach((sec, i) => {
      const t = tituloDe(sec);
      if (!notaDe(sec) && !apunteDe(sec)) {
        if (t && /\bseccion\b/.test(sec.className)) {
          partes.push('<div class="es-sec">' + t + "</div>");
        }
        return;
      }
      partes.push('<h2 data-ir="' + i + '" title="Ir a esta diapositiva"><span>' +
        (i + 1) + "</span>" + t + "</h2>" + bloquesDe(sec));
    });
    partes.push("</div>");
    return partes.join("");
  }

  function contenido() {
    return todo ? htmlTodo() : bloquesDe(Reveal.getCurrentSlide());
  }

  function encabezado() {
    if (todo) return "Toda la sesión, de corrido";
    const sec = Reveal.getCurrentSlide();
    const i = laminas().indexOf(sec);
    return (i >= 0 ? i + 1 + ". " : "") + (tituloDe(sec) || "Sin título");
  }

  /* ---------- MathJax ---------- */

  const haceFalta = (el) => /\\\(|\\\[/.test((el && el.textContent) || "");

  function componer(el) {
    if (!haceFalta(el) || !window.MathJax || !MathJax.typesetPromise) return;
    try { MathJax.typesetPromise([el]).catch(function () {}); } catch (e) {}
  }

  /* Compone el texto en este documento y entrega el nodo ya hecho, que es la
     única forma de llevárselo compuesto a otra ventana. */
  function fragua(html, listo) {
    const caja = document.createElement("div");
    caja.className = "es-fragua";
    caja.innerHTML = html;
    document.body.appendChild(caja);
    const acabar = () => listo(caja);
    if (!haceFalta(caja) || !window.MathJax || !MathJax.typesetPromise) { acabar(); return; }
    try { MathJax.typesetPromise([caja]).then(acabar).catch(acabar); }
    catch (e) { acabar(); }
  }

  /* ---------- el panel ---------- */

  const relayout = () => { try { Reveal.layout(); } catch (e) {} };

  function pintarPanel() {
    panel.querySelector(".es-tit").textContent = encabezado();
    const cuerpo = panel.querySelector(".es-cuerpo");
    cuerpo.innerHTML = contenido();
    cuerpo.scrollTop = 0;
    componer(cuerpo);
  }

  function abrirPanel() {
    document.body.classList.add("es-abierto");
    pintar();
    relayout();
  }

  function cerrarPanel() {
    if (!document.body.classList.contains("es-abierto")) return;
    document.body.classList.remove("es-abierto");
    relayout();
  }

  /* ---------- la ventana ---------- */

  function cajaGuardada() {
    try {
      const c = JSON.parse(localStorage.getItem(LLAVE_CAJA) || "null");
      return c && c.w > 200 && c.h > 200 ? c : null;
    } catch (e) { return null; }
  }

  function recordarCaja() {
    if (!win || win.closed || !win.outerWidth || !win.outerHeight) return;
    try {
      localStorage.setItem(LLAVE_CAJA, JSON.stringify(
        { w: win.outerWidth, h: win.outerHeight, x: win.screenX, y: win.screenY }));
    } catch (e) {}
  }

  function pintarVentana() {
    if (!win || win.closed) return;
    const d = win.document;
    const t = d.getElementById("tit"), cuerpo = d.getElementById("cuerpo");
    if (!t || !cuerpo) return;
    t.textContent = encabezado();
    fragua(contenido(), (caja) => {
      if (!win || win.closed) { caja.remove(); return; }
      cuerpo.innerHTML = "";
      // Sobre una lista FIJA de los hijos, no sobre caja.firstChild: importNode
      // COPIA el nodo y no lo saca del origen, así que un while sobre firstChild
      // no termina nunca y cuelga la pestaña. Pasó, y lo cazó la prueba de
      // regresión colgando a Chrome el 1 de octubre de 2026.
      [...caja.childNodes].forEach((n) => cuerpo.appendChild(d.importNode(n, true)));
      caja.remove();
      try { win.scrollTo(0, 0); } catch (e) {}
    });
  }

  function abrirVentana() {
    if (win && !win.closed) { win.focus(); pintarVentana(); return; }
    const c = cajaGuardada();
    const ancho = c ? c.w : ANCHO, alto = c ? c.h : ALTO;
    const izq = c && typeof c.x === "number" ? Math.max(0, c.x) : 60;
    const arriba = c && typeof c.y === "number" ? Math.max(0, c.y) : 40;
    const w = window.open("about:blank", "estudio",
      "width=" + ancho + ",height=" + alto + ",left=" + izq + ",top=" + arriba +
      ",menubar=no,toolbar=no,location=no");
    if (!w) {
      alert("El navegador bloqueó la ventana de estudio. Permite las ventanas " +
            "emergentes de esta página, o lee las notas en el panel.");
      ponerModo("panel");
      return;
    }
    escribirVentana(w.document);
    win = w;
    w.document.addEventListener("click", enClic);
    // Al cerrarla a mano se guarda dónde la dejó, que es lo que la hace abrirse
    // igual mañana. Y se suelta la referencia, o la tecla I creería que sigue viva.
    w.addEventListener("beforeunload", () => { recordarCaja(); win = null; });
    w.addEventListener("resize", recordarCaja);
    pintar();
  }

  function cerrarVentana() {
    if (!win || win.closed) { win = null; return; }
    recordarCaja();
    try { win.close(); } catch (e) {}
    win = null;
  }

  /* ---------- gobierno ---------- */

  const abierto = () =>
    document.body.classList.contains("es-abierto") || !!(win && !win.closed);

  /* El botón dice a dónde lleva, no dónde estás: con la sesión de corrido abierta
     tiene que ofrecer la vuelta a la lámina, o no hay forma de saber que se sale
     por ahí. */
  function rotularBotones() {
    const eti = todo ? "Solo esta lámina" : "Toda la sesión";
    const p = panel.querySelector('[data-es="todo"]');
    if (p) p.textContent = eti;
    if (win && !win.closed) {
      const v = win.document.querySelector('[data-es="todo"]');
      if (v) v.textContent = eti;
    }
  }

  function pintar() {
    if (document.body.classList.contains("es-abierto")) pintarPanel();
    if (win && !win.closed) pintarVentana();
    rotularBotones();
  }

  function abrir() {
    if (modo === "ventana") abrirVentana();
    else abrirPanel();
  }

  function cerrar() {
    cerrarPanel();
    cerrarVentana();
  }

  function ponerModo(m) {
    if (m === modo && abierto()) return;
    modo = m;
    try { localStorage.setItem(LLAVE_MODO, m); } catch (e) {}
    cerrar();
    abrir();
  }

  function ponerTodo(v) {
    todo = v;
    pintar();
  }

  function enClic(e) {
    const t = e.target;
    if (!t || !t.closest) return;
    const b = t.closest("[data-es]");
    if (b) {
      const que = b.dataset.es;
      if (que === "cerrar") cerrar();
      else if (que === "ventana") ponerModo("ventana");
      else if (que === "panel") ponerModo("panel");
      else if (que === "todo") ponerTodo(!todo);
      else if (que === "antes") { try { Reveal.prev(); } catch (e2) {} }
      else if (que === "despues") { try { Reveal.next(); } catch (e2) {} }
      return;
    }
    const h = t.closest("[data-ir]");
    if (h) {
      ponerTodo(false);
      try { Reveal.slide(parseInt(h.dataset.ir, 10)); } catch (e2) {}
      if (win && !win.closed) win.focus();
    }
  }

  document.addEventListener("click", enClic);

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || !abierto()) return;
    const tag = (e.target && e.target.tagName) || "";
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) return;
    e.preventDefault();
    e.stopPropagation();
    cerrar();
  }, true);

  Reveal.on("slidechanged", () => { if (!todo) pintar(); });

  if (Reveal.addKeyBinding) {
    Reveal.addKeyBinding(
      { keyCode: 73, key: "I", description: "Notas de estudio de esta lámina" },
      () => { if (abierto()) cerrar(); else abrir(); });
  }

  // Para la prueba de regresión y para la consola, que es más cómoda que simular
  // clics cuando algo no cuadra.
  window.estudio = {
    abrir: abrir, cerrar: cerrar, abierto: abierto,
    modo: () => modo, ponerModo: ponerModo,
    todo: () => todo, ponerTodo: ponerTodo,
    ventana: () => win,
  };
})();
