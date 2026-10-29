/* Lector de apuntes del paquete que se entrega al grupo.

   No lo carga el deck de trabajo: lo inyecta tools/empaquetar.py en el archivo
   único de salidas/, y solo si la sesión tiene apuntes escritos. Por eso aquí no
   hay nada del anotador ni del apuntador: esto lo abre un estudiante, con doble
   clic y sin conexión.

   Cada lámina puede llevar su apunte en un <aside class="apuntes">, oculto por el
   tema. Es lo único de los cuatro bloques de notas que viaja al paquete: el guion de
   orador y el guion corto se quedan en el deck fuente.

   El panel **arranca abierto**: el apunte es parte de lo que se entrega, no un
   extra que haya que descubrir. Va al costado, y la lámina se encoge para dejarle
   sitio, así que se lee sin perder de vista la diapositiva. Quien no lo quiera lo
   cierra con Cerrar, con la tecla A o con Escape, y el botón de abajo a la
   izquierda lo devuelve. La tecla T alterna entre las láminas y los apuntes completos. En pantalla estrecha, que es el caso del teléfono, el
   panel pasa a ocupar la mitad de abajo.

   Dentro del panel, "Ver todos" abre los apuntes completos: todas las láminas con
   su título, su apunte y una miniatura de la diapositiva al lado, de corrido, para
   leerlo o imprimirlo. La miniatura es un clon vivo de la lámina, así que nunca se
   desfasa del deck. Los apuntes completos terminan con la ficha de la sesión, que es su
   bibliografía y sus créditos, y que el deck lleva en un <aside class="ficha"> de
   la lámina de cierre. En esa lámina el panel muestra la ficha en lugar del hueco
   de apunte.

   Las marcas de cita, los superíndices que tools/citas.py numera, llevan al
   apuntes y dejan su referencia resaltada unos segundos. Funcionan desde la
   lámina, desde el panel y desde los propios apuntes. Al imprimir salen solo
   los apuntes, nunca las diapositivas. */
(function () {
  if (typeof Reveal === "undefined") return;

  const secs = [...document.querySelectorAll(".reveal .slides > section")];
  const apunteDe = (sec) => sec && sec.querySelector("aside.apuntes");
  if (!secs.some(apunteDe)) return;          // sesión sin apuntes, no hay lector

  const tituloDe = (sec) => {
    const h = sec.querySelector("h1,h2") || sec.querySelector(".titulo,.gracias");
    return h ? h.textContent.trim() : "";
  };
  const deck = (document.title || "Apuntes").trim();
  // La ficha de la sesión, con su bibliografía y sus créditos, va en la lámina de
  // cierre y cierra también los apuntes completos.
  const ficha = document.querySelector(".reveal .slides aside.ficha");

  const CSS = `
  .ap-boton{position:fixed;left:16px;bottom:16px;z-index:60;
    font:600 13px/1 'Noto Sans',system-ui,sans-serif;letter-spacing:.03em;
    padding:9px 14px;border:0;border-radius:4px;cursor:pointer;
    background:#A42145;color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.25)}
  .ap-boton:hover{background:#6E152E}
  .ap-boton[hidden]{display:none}
  .ap-panel{position:fixed;top:0;right:0;bottom:0;width:380px;z-index:59;
    background:#FBFAF8;border-left:1px solid #DDD8CE;display:none;
    flex-direction:column;font:16px/1.6 'Noto Sans',system-ui,sans-serif;color:#2E2E2E}
  body.ap-abierto .ap-panel{display:flex}
  body.ap-abierto .reveal{width:calc(100% - 380px)}
  .ap-cab{padding:14px 18px 10px;border-bottom:1px solid #E4E0D8}
  .ap-eti{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.09em;color:#8A8A8A}
  .ap-tit{font-weight:600;font-size:17px;margin-top:6px;color:#A42145}
  .ap-cuerpo{flex:1;overflow:auto;padding:14px 18px 20px}
  .ap-cuerpo p{margin:0 0 12px}
  .ap-cuerpo p:last-child{margin-bottom:0}
  .ap-cuerpo .ap-vacio{color:#8A8A8A;font-style:italic}
  .ap-pie{display:flex;gap:8px;padding:10px 18px 14px;border-top:1px solid #E4E0D8}
  .ap-pie button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:8px 12px;
    border:1px solid #D9C9CE;background:#fff;color:#A42145;border-radius:4px;cursor:pointer}
  .ap-pie button:hover{background:#FCEEF2}
  .ap-pie .ap-cerrar{margin-left:auto;border-color:#DDD8CE;color:#7A7568}
  /* El estado va en el body con OTRO nombre, ap-completo: si se llamara igual que
     el panel, esta misma regla le pondría display:none al body y la página entera
     se quedaría en blanco. */
  .ap-todos{position:fixed;inset:0;z-index:61;background:#FBFAF8;overflow:auto;
    display:none;padding:36px 0 60px}
  body.ap-completo .ap-todos{display:block}
  .ap-doc{max-width:1140px;margin:0 auto;padding:0 24px;
    font:17px/1.7 'Noto Sans',system-ui,sans-serif;color:#2E2E2E}
  .ap-bl{display:flex;gap:24px;align-items:flex-start;margin:0 0 26px}
  .ap-texto{flex:1;min-width:0;max-width:760px;order:1}
  /* La miniatura es un clon vivo de la lámina dentro de su propio .reveal, para
     que herede el tema entero, fondo incluido, y no se desfase nunca del deck. */
  .ap-mini{flex:none;order:2;position:relative;width:320px;height:180px;overflow:hidden;
    border:1px solid #DDD8CE;border-radius:3px;background:#fff;cursor:pointer;
    box-shadow:0 1px 4px rgba(0,0,0,.08)}
  .ap-mini:hover{border-color:#A42145;box-shadow:0 2px 10px rgba(164,33,69,.25)}
  .ap-mini > .reveal{position:absolute!important;left:0;top:0;
    width:1280px!important;height:720px!important;min-width:0!important;
    transform:scale(.25);transform-origin:0 0;overflow:hidden}
  .ap-mini .slides{position:absolute!important;left:0!important;top:0!important;
    width:1280px!important;height:720px!important;transform:none!important;
    zoom:1!important;margin:0!important;padding:0!important;text-align:left}
  .ap-mini .slides > section{position:absolute!important;left:0!important;top:0!important;
    display:block!important;opacity:1!important;visibility:visible!important;
    transform:none!important;filter:none!important;pointer-events:none;z-index:auto}
  .ap-mini .fragment{opacity:1!important;visibility:visible!important}
  .ap-mini aside{display:none!important}
  @media (max-width:1100px){
    .ap-bl{flex-direction:column;gap:14px}
    .ap-mini{order:0;width:100%;max-width:480px;height:270px}
  }
  .ap-doc h1{font-size:24px;color:#A42145;margin:0 0 6px;font-weight:600}
  .ap-doc .ap-intro{color:#7A7568;font-size:14px;margin:0 0 28px}
  .ap-texto h2{font-size:18px;color:#A42145;margin:0 0 6px;font-weight:600;cursor:pointer}
  .ap-texto h2 span{color:#8A8A8A;font-weight:400;margin-right:8px;font-variant-numeric:tabular-nums}
  .ap-texto h2:hover{text-decoration:underline}
  .ap-doc .ap-seccion{margin:38px 0 0;padding-top:14px;border-top:2px solid #E7D395;
    font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:#8A7A3A;font-weight:600}
  .ap-texto p{margin:0 0 12px}
  .ap-ficha{margin:34px 0 0;padding:20px 0 0;border-top:2px solid #E7D395}
  .ap-ficha h3{font:600 13px/1.4 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.08em;color:#8A7A3A;margin:0 0 8px}
  .ap-ficha ul{margin:0 0 20px;padding-left:20px}
  .ap-ficha li{margin:0 0 7px}
  .ap-ficha p{margin:0 0 8px}
  .ap-cuerpo cite[data-ref],.ap-doc cite[data-ref]{font-style:normal;font-weight:600;
    font-size:.86em;vertical-align:baseline;line-height:inherit;color:#A42145;
    margin-left:.22em;white-space:nowrap;cursor:pointer}
  .ap-cuerpo cite[data-ref]::before,.ap-doc cite[data-ref]::before{content:"["}
  .ap-cuerpo cite[data-ref]::after,.ap-doc cite[data-ref]::after{content:"]"}
  .ap-cuerpo cite[data-ref]:hover,.ap-doc cite[data-ref]:hover{background:#FFE873}
  .ap-ficha ol{margin:0 0 20px;padding-left:26px}
  .ap-ficha li{margin:0 0 7px}
  .ap-ficha li.ap-resalta{background:#FFE873;border-radius:3px;
    box-shadow:0 0 0 6px #FFE873}
  .ap-ficha a{color:#A42145;text-decoration:underline}
  .ap-ficha a:hover{background:#FCEEF2}
  .ap-cuerpo .ap-ficha{margin:0;padding:0;border:0}
  .ap-cuerpo .ap-ficha h3{font-size:11px;margin:14px 0 6px}
  .ap-cuerpo .ap-ficha h3:first-child{margin-top:0}
  .ap-cuerpo .ap-ficha ul{margin:0 0 12px;padding-left:18px;font-size:15px}
  .ap-barra{position:fixed;right:18px;top:18px;z-index:62;display:flex;gap:8px}
  .ap-barra button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:9px 13px;
    border:1px solid #D9C9CE;background:#fff;color:#A42145;border-radius:4px;cursor:pointer}
  .ap-barra button:hover{background:#FCEEF2}
  body:not(.ap-completo) .ap-barra{display:none}
  @media (max-width:900px){
    .ap-panel{top:auto;left:0;width:auto;height:46%;border-left:0;border-top:1px solid #DDD8CE}
    body.ap-abierto .reveal{width:100%;height:54%}
    .ap-boton{bottom:auto;top:12px;left:12px;padding:8px 12px}
  }
  /* Impresión: un documento de texto, no un deck. Reveal trae su propia hoja de
     impresión que pone la página en 1280 por 720 y el cuerpo en veinte puntos, y
     eso es lo que salía antes. Se desactiva entera poniéndole al html la clase
     print-pdf, que es la puerta que el propio reveal deja: todas sus reglas de
     impresión están escritas como html:not(.print-pdf). Lo hace el lector al
     imprimir y lo deshace al terminar. */
  @media print{
    @page{size:letter;margin:20mm 18mm 18mm}
    html,body{width:auto!important;height:auto!important;overflow:visible!important;
      margin:0!important;padding:0!important;background:#fff!important}
    /* body > .reveal y no .reveal a secas: cada miniatura lleva dentro su propio
       .reveal, y esconderlos a todos dejaba lo impreso con las cajas
       vacías. El deck es el que cuelga directo del body. */
    body > .reveal,.ap-panel,.ap-boton,.ap-barra{display:none!important}
    .ap-todos{display:block!important;position:static!important;inset:auto!important;
      width:auto!important;height:auto!important;overflow:visible!important;
      padding:0!important;background:#fff!important}
    .ap-doc{max-width:none!important;margin:0!important;padding:0!important;
      font:10.5pt/1.5 'Noto Sans',system-ui,sans-serif;color:#1A1A1A}
    .ap-doc h1{font-size:19pt;line-height:1.25;margin:0 0 2mm}
    .ap-doc .ap-intro{font-size:9pt;color:#555;margin:0 0 6mm;padding-bottom:3mm;
      border-bottom:1px solid #C9C3B6}
    .ap-doc .ap-seccion{font-size:11pt;margin:8mm 0 3mm;padding-top:3mm;
      border-top:1px solid #E7D395;break-after:avoid;page-break-after:avoid}
    /* flow-root para que el bloque contenga la miniatura flotada y no se parta */
    .ap-bl{display:flow-root!important;break-inside:avoid;page-break-inside:avoid;
      margin:0 0 6mm}
    .ap-texto{max-width:none!important}
    .ap-texto h2{font-size:11.5pt;margin:0 0 1.5mm;break-after:avoid;page-break-after:avoid}
    .ap-texto h2 span{color:#8A8A8A}
    .ap-texto p{margin:0 0 2mm;text-align:justify;hyphens:auto}
    /* la miniatura va flotada a la derecha, como una figura de Word */
    .ap-mini{float:right;width:62mm;height:34.9mm;margin:0 0 3mm 6mm;
      box-shadow:none;border:1px solid #C9C3B6;break-inside:avoid}
    /* Al imprimir, todo el clon en flujo normal y escalado con zoom: Chrome no
       pinta lo posicionado en absoluto dentro de una caja recortada. La lámina se
       queda en relativo, que es lo que el tema usa de referencia para colocar sus
       cajas por dentro. */
    .ap-mini > .reveal{transform:none!important;zoom:.183;position:static!important;
      overflow:visible!important}
    .ap-mini .slides{position:static!important;transform:none!important;
      width:1280px!important;height:720px!important}
    .ap-mini .slides > section{position:relative!important;left:auto!important;
      top:auto!important;width:1280px!important;height:720px!important;
      display:block!important;opacity:1!important;visibility:visible!important}
    .ap-mini *{print-color-adjust:exact;-webkit-print-color-adjust:exact}
    .ap-ficha{margin:10mm 0 0;padding:4mm 0 0;border-top:1px solid #C9C3B6;
      break-inside:avoid;page-break-inside:avoid;font-size:9.5pt}
    .ap-ficha h3{font-size:10pt;margin:0 0 2mm}
    .ap-ficha ul,.ap-ficha ol{margin:0 0 5mm;padding-left:7mm}
    .ap-ficha li{margin:0 0 1.5mm}
    .ap-ficha a{color:#1A1A1A;text-decoration:none}
  }`;

  document.head.insertAdjacentHTML("beforeend", "<style>" + CSS + "</style>");

  const boton = document.createElement("button");
  boton.type = "button";
  boton.className = "ap-boton";
  boton.textContent = "Apuntes";
  boton.title = "Apuntes de esta lámina, tecla A";

  const panel = document.createElement("div");
  panel.className = "ap-panel";
  panel.innerHTML =
    '<div class="ap-cab"><div class="ap-eti">Apuntes</div>' +
    '<div class="ap-tit"></div></div>' +
    '<div class="ap-cuerpo"></div>' +
    '<div class="ap-pie"><button type="button" data-ap="todos" title="tecla T">' +
    "Ver todos</button>" +
    '<button type="button" class="ap-cerrar" data-ap="cerrar">Cerrar</button></div>';

  const todos = document.createElement("div");
  todos.className = "ap-todos";

  const barra = document.createElement("div");
  barra.className = "ap-barra";
  barra.innerHTML = '<button type="button" data-ap="imprimir">Imprimir</button>' +
                    '<button type="button" data-ap="volver" title="tecla T">' +
                    "Volver a las láminas</button>";

  document.body.append(boton, panel, todos, barra);

  // La lámina se encoge para dejarle sitio al panel, no se tapa. Reveal recalcula
  // su escala solo si se le pide.
  const relayout = () => { try { Reveal.layout(); } catch (e) {} };

  // Las expresiones matemáticas de un apunte las compone MathJax aquí y no al
  // cargar el deck: la configuración lo excluye con ignoreHtmlClass 'apuntes',
  // porque dentro de la lámina ese bloque está oculto y componerlo sería gasto
  // tirado. Al copiarlo al panel deja de estar bajo esa clase, así que basta
  // pedirle a MathJax que lo componga. Sin esto el grupo lee el LaTeX en crudo.
  function componer(el) {
    if (!el || !window.MathJax || !MathJax.typesetPromise) return;
    try { MathJax.typesetPromise([el]).catch(function () {}); } catch (e) {}
  }

  function pintarPanel() {
    const sec = Reveal.getCurrentSlide();
    const a = apunteDe(sec);
    panel.querySelector(".ap-tit").textContent = tituloDe(sec) || deck;
    // El hueco también informa: en la portada y en los separadores no hay apunte,
    // y conviene que se vea que eso es lo normal y no una falla.
    panel.querySelector(".ap-cuerpo").innerHTML = a ? a.innerHTML
      : ficha && /\bcierre\b/.test(sec.className)
        ? '<div class="ap-ficha">' +
          ficha.innerHTML.replace(/\sid="ref-([^"]+)"/g, ' data-ref-id="$1"') + "</div>"
        : '<p class="ap-vacio">Esta lámina no lleva apunte. Los tienes todos juntos ' +
          "en Ver todos, aquí abajo.</p>";
    componer(panel.querySelector(".ap-cuerpo"));
  }

  function miniatura(sec, i) {
    const clon = sec.cloneNode(true);
    clon.removeAttribute("id");
    clon.removeAttribute("data-sid");
    clon.classList.remove("present", "past", "future", "stack");
    clon.style.display = "block";
    // nada de notas, ni de medios pesados: la miniatura es una foto, no un deck
    clon.querySelectorAll("aside, script, iframe, video, audio").forEach((x) => x.remove());
    const caja = document.createElement("div");
    caja.className = "ap-mini";
    caja.title = "Ir a esta diapositiva";
    caja.dataset.ir = i;
    const lienzo = document.createElement("div");
    lienzo.className = "reveal";
    const pista = document.createElement("div");
    pista.className = "slides";
    pista.appendChild(clon);
    lienzo.appendChild(pista);
    caja.appendChild(lienzo);
    return caja;
  }

  /* Las miniaturas son clones de láminas enteras, así que solo se montan cuando
     los apuntes se van a ver o a imprimir. Al cargar basta con el texto, que es lo
     que hace falta para que un Ctrl+P no salga en blanco. */
  function pintarTodos(conMiniaturas) {
    const partes = ['<div class="ap-doc"><h1>' + deck + "</h1>" +
      '<p class="ap-intro">Apuntes de estudio, una entrada por lámina. ' +
      "Pincha un título o su miniatura para ir a esa diapositiva.</p>"];
    secs.forEach((sec, i) => {
      const a = apunteDe(sec);
      const t = tituloDe(sec);
      if (!a) {
        // los separadores de bloque los ordenan aunque no lleven apunte
        if (t && /\bseccion\b/.test(sec.className)) {
          partes.push('<div class="ap-seccion">' + t + "</div>");
        }
        return;
      }
      partes.push('<div class="ap-bl"><div class="ap-hueco" data-i="' + i + '"></div>' +
        '<div class="ap-texto"><h2 data-ir="' + i + '"><span>' + (i + 1) + "</span>" + t +
        "</h2>" + a.innerHTML + "</div></div>");
    });
    if (ficha) {
      partes.push('<div class="ap-ficha">' +
        ficha.innerHTML.replace(/\sid="ref-([^"]+)"/g, ' data-ref-id="$1"') + "</div>");
    }
    partes.push("</div>");
    todos.innerHTML = partes.join("");
    componer(todos);
    if (!conMiniaturas) return;
    [...todos.querySelectorAll(".ap-hueco")].forEach((h) => {
      const i = parseInt(h.dataset.i, 10);
      h.replaceWith(miniatura(secs[i], i));
    });
  }

  const abrir = () => {
    document.body.classList.add("ap-abierto");
    boton.hidden = true;
    pintarPanel();
    relayout();
  };
  const cerrar = () => {
    document.body.classList.remove("ap-abierto");
    boton.hidden = false;
    relayout();
  };
  const abrirTodos = () => { pintarTodos(true); document.body.classList.add("ap-completo"); };

  /* Una marca de cita lleva a los apuntes, a su referencia, y la deja resaltada un
     momento. La ficha se copia dentro de ellos, así que sus id viajarían por
     duplicado: al copiarla se cambian por data-ref-id, que no choca con nada. */
  let apagarResalte = null;
  function irAReferencia(clave) {
    abrirTodos();
    const li = todos.querySelector('[data-ref-id="' + clave + '"]');
    if (!li) return;
    li.scrollIntoView({ block: "center" });
    clearTimeout(apagarResalte);
    [...todos.querySelectorAll(".ap-resalta")].forEach((x) => x.classList.remove("ap-resalta"));
    li.classList.add("ap-resalta");
    apagarResalte = setTimeout(() => li.classList.remove("ap-resalta"), 4000);
  }
  const cerrarTodos = () => { document.body.classList.remove("ap-completo"); todos.scrollTop = 0; };

  boton.addEventListener("click", abrir);

  document.addEventListener("click", (e) => {
    const b = e.target.closest && e.target.closest("button[data-ap]");
    if (b) {
      const que = b.dataset.ap;
      if (que === "cerrar") cerrar();
      else if (que === "todos") abrirTodos();
      else if (que === "volver") cerrarTodos();
      else if (que === "imprimir") { antesDeImprimir(); window.print(); }
      return;
    }
    const c = e.target.closest && e.target.closest("cite[data-ref]");
    if (c) { irAReferencia(c.dataset.ref); return; }
    const h = e.target.closest && e.target.closest("[data-ir]");
    if (h) { cerrarTodos(); Reveal.slide(parseInt(h.dataset.ir, 10)); abrir(); }
  });

  document.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = (e.target && e.target.tagName) || "";
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) return;
    if (e.key === "t" || e.key === "T") {
      e.preventDefault();
      if (document.body.classList.contains("ap-completo")) cerrarTodos();
      else abrirTodos();
      return;
    }
    if (e.key === "a" || e.key === "A") {
      e.preventDefault();
      if (document.body.classList.contains("ap-completo")) cerrarTodos();
      else if (document.body.classList.contains("ap-abierto")) cerrar();
      else abrir();
    } else if (e.key === "Escape") {
      if (document.body.classList.contains("ap-completo")) cerrarTodos();
      else if (document.body.classList.contains("ap-abierto")) cerrar();
    }
  }, true);

  Reveal.on("slidechanged", () => {
    if (document.body.classList.contains("ap-abierto")) pintarPanel();
  });

  // Al imprimir salen los apuntes y no las láminas, así que tiene que estar escrito
  // aunque nadie lo haya abierto: un Ctrl+P a secas imprimiría hojas en blanco.
  const antesDeImprimir = () => {
    pintarTodos(true);
    document.documentElement.classList.add("print-pdf");
  };
  window.addEventListener("beforeprint", antesDeImprimir);
  window.addEventListener("afterprint", () => {
    document.documentElement.classList.remove("print-pdf");
  });
  pintarTodos(false);

  // Abierto de entrada, en cuanto reveal sabe en qué lámina está. Si ya estaba
  // listo antes de llegar aquí, "ready" no vuelve a dispararse: hay que mirarlo.
  try {
    if (Reveal.isReady && Reveal.isReady()) abrir();
    else Reveal.on("ready", abrir);
  } catch (e) { Reveal.on("ready", abrir); }
})();
