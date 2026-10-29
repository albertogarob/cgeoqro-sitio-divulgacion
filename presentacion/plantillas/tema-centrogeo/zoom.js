/* Ampliar una figura al tamaño de la lámina, con un clic.
 *
 * Alberto lo pidió el 30 de septiembre de 2026, al revisar la sesión 9: "que al
 * dar click a una imagen en un slide ésta aparezca abarcando toda la página,
 * como un zoom out instantáneo. Y que los controles de dibujo con el cursor
 * sigan siendo funcionales en caso de que quiera dibujar sobre la imagen
 * zoomeada. La imagen debe aparecer zoomeada y opcionalmente un caption escrito
 * por nosotros. El caption debe poder esconderse en modo zoom out."
 *
 * Funciona en las 30 sesiones sin tocar ninguna: se activa sobre cualquier
 * <svg>, <img> o <video> que esté dentro del cuerpo de una lámina.
 *
 * CÓMO SE USA, desde una sesión:
 *   - nada. Toda figura del cuerpo es ampliable de fábrica.
 *   - para ponerle pie, se le añade data-pie="texto" a la figura.
 *   - para que una figura NO sea ampliable, data-zoom="no".
 *
 * EN LA LÁMINA:
 *   clic en la figura      la amplía
 *   clic fuera, o Escape   la cierra
 *   P                      esconde y devuelve el pie, estando ampliada
 *
 * DÓNDE VIVE LA CAPA, y por qué ahí. Cuelga de .reveal .slides, con las mismas
 * 1280 por 720 coordenadas de lámina que usa el lienzo del pincel, y con
 * z-index 15, que queda por encima del reproductor de video, que está en 12, y
 * por DEBAJO del lienzo del pincel, que está en 20. Así la tinta del lápiz cae
 * exactamente encima de la figura ampliada y se puede dibujar sobre ella.
 *
 * El lienzo del pincel lleva pointer-events:none mientras el pincel está
 * apagado, de modo que el clic para cerrar llega a esta capa; y lo lleva en
 * auto cuando está encendido, de modo que entonces el lápiz manda y la capa no
 * se cierra por accidente a media raya.
 */
(function () {
  const ANCHO = 1280, ALTO = 720;
  const CSS = `
.zm-capa { position:absolute; left:0; top:0; width:${ANCHO}px; height:${ALTO}px;
  z-index:15; display:none; background:rgba(247,245,242,.97);
  pointer-events:auto; cursor:zoom-out; }
.zm-capa.zm-abierta { display:flex; flex-direction:column;
  align-items:center; justify-content:center; }
/* box-sizing: border-box es obligatorio aqui. Con el content-box de fabrica,
   width:100% mas el relleno daba una caja MAS ANCHA que la capa, 1055 contra
   1026, y la figura se salia por los lados. Alberto lo vio en la lamina del
   terreno difusificado el 1 de octubre de 2026. */
.zm-caja { box-sizing:border-box; flex:1 1 auto; min-height:0; width:100%;
  display:flex; align-items:center; justify-content:center; padding:14px 18px 6px; }
.zm-caja > * { max-width:100%; max-height:100%; width:auto; height:auto;
  display:block; }
.zm-caja > svg { width:100%; height:100%; }
.zm-pie { flex:0 0 auto; max-width:88%; margin:0 0 22px;
  font-family:inherit; font-size:21px; line-height:1.3; color:#3a3a3a;
  text-align:center; }
.zm-capa.zm-sin-pie .zm-pie { display:none; }
.zm-ayuda { position:absolute; right:16px; top:12px; font-family:inherit;
  font-size:13px; color:#8a8a8a; }
/* La figura ampliable se anuncia al pasar el ratón, sin moverla de sitio. */
.reveal .cuerpo [data-zm] { cursor:zoom-in; }
#reproductor[data-zm] { cursor:zoom-in; }
`;

  let capa = null, caja = null, pie = null, origen = null;

  function montar() {
    if (capa) return;
    document.head.insertAdjacentHTML("beforeend", "<style>" + CSS + "</style>");
    capa = document.createElement("div");
    capa.className = "zm-capa";
    capa.innerHTML = '<div class="zm-caja"></div><p class="zm-pie"></p>' +
                     '<div class="zm-ayuda"></div>';
    document.querySelector(".reveal .slides").appendChild(capa);
    caja = capa.querySelector(".zm-caja");
    pie = capa.querySelector(".zm-pie");
    capa.addEventListener("click", cerrar);
  }

  function ampliables(lamina) {
    if (!lamina) return [];
    return Array.from(lamina.querySelectorAll(".cuerpo svg, .cuerpo img, .cuerpo video"))
      .filter(el => el.getAttribute("data-zoom") !== "no" &&
                    !el.closest("[data-zoom='no']") &&
                    // Las fórmulas compuestas por MathJax son <svg> y no son figuras.
                    !el.closest("mjx-container"));
  }

  function marcar(lamina) {
    ampliables(lamina).forEach(el => el.setAttribute("data-zm", "1"));
    // El reproductor tambien se amplia, y lleva su marca para que ensene el
    // cursor de lupa como cualquier otra figura.
    const v = document.getElementById("reproductor");
    if (v) v.setAttribute("data-zm", "1");
  }

  function abrir(el, esVideo) {
    montar();
    origen = el;
    caja.innerHTML = "";
    const copia = el.cloneNode(true);
    copia.removeAttribute("data-zm");
    copia.removeAttribute("style");
    caja.appendChild(copia);
    // Un video clonado arranca parado: se le pide que siga donde iba.
    if (copia.tagName === "VIDEO") {
      copia.muted = true; copia.loop = true;
      copia.removeAttribute("id");          // el id es del reproductor de la lamina
      copia.style.cssText = "width:100%;height:100%;object-fit:contain;" +
                            "mix-blend-mode:multiply;display:block";
      // El tramo que la lamina declara, para que el clon de vueltas ahi mismo
      // y no siga hasta el final del archivo.
      const ini = lam ? parseFloat(lam.getAttribute("data-start")) : NaN;
      const fin = lam ? parseFloat(lam.getAttribute("data-end")) : NaN;
      try { copia.currentTime = el.currentTime || (isNaN(ini) ? 0 : ini); } catch (e) {}
      if (!isNaN(ini) && !isNaN(fin)) {
        copia.addEventListener("timeupdate", function () {
          if (copia.currentTime >= fin) copia.currentTime = ini;
        });
      }
      const p = copia.play(); if (p && p.catch) p.catch(() => {});
    }
    const lam = window.Reveal && Reveal.getCurrentSlide && Reveal.getCurrentSlide();
    const texto = (esVideo && lam ? lam.getAttribute("data-pie-video") : null)
                  || el.getAttribute("data-pie") || "";
    pie.textContent = texto;
    pie.style.display = texto ? "" : "none";
    // La ayuda solo ofrece la P cuando hay pie que esconder. Prometerla sin pie
    // hacía parecer que la tecla estaba rota.
    capa.querySelector(".zm-ayuda").textContent =
      texto ? "Escape cierra, P esconde el pie" : "Escape cierra";
    capa.classList.remove("zm-sin-pie");
    capa.classList.add("zm-abierta");
  }

  function cerrar() {
    if (!capa || !capa.classList.contains("zm-abierta")) return;
    capa.classList.remove("zm-abierta");
    caja.innerHTML = "";
    origen = null;
  }

  function abierta() {
    return !!(capa && capa.classList.contains("zm-abierta"));
  }

  function reproductor(el) {
    return el && el.id === "reproductor" &&
           getComputedStyle(el).display !== "none";
  }

  document.addEventListener("click", function (e) {
    if (abierta()) return;              // el clic de cerrar lo atiende la capa
    const el = e.target.closest ? e.target.closest("svg, img, video") : null;
    if (!el) return;
    // El reproductor de las animaciones cuelga de <body> y no del cuerpo de la
    // lamina, asi que hay que admitirlo aparte. Su pie lo pone la lamina que
    // lo usa, en data-pie-video, porque el elemento de video es uno solo y
    // compartido por todas las laminas con animacion.
    const esVideo = reproductor(el);
    if (!esVideo && !el.closest(".cuerpo")) return;
    if (el.getAttribute("data-zoom") === "no" || el.closest("[data-zoom='no']")) return;
    if (el.closest("mjx-container")) return;
    e.preventDefault();
    e.stopPropagation();
    abrir(el, esVideo);
  }, true);

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && abierta()) {
      cerrar();
      // Hay que frenarlo: si no, reveal recibe el mismo Escape y abre su vista
      // general de miniaturas justo después de cerrar la figura ampliada. La
      // rama de la P ya lo frenaba, y esta no: era una incoherencia.
      e.preventDefault(); e.stopPropagation();
      if (e.stopImmediatePropagation) e.stopImmediatePropagation();
      return;
    }
    if ((e.key === "p" || e.key === "P") && abierta() &&
        !e.ctrlKey && !e.metaKey && !e.altKey) {
      capa.classList.toggle("zm-sin-pie");
      e.preventDefault(); e.stopPropagation();
    }
  }, true);

  function alCambiar() {
    cerrar();
    // Se marcan TODAS las figuras del deck, no solo las de la lámina en curso:
    // el atributo solo pinta el cursor de lupa, y marcarlo lámina a lámina lo
    // dejaba sin poner en las que reveal todavía no había mostrado.
    marcar(document);
  }

  if (window.Reveal && Reveal.on) {
    Reveal.on("ready", alCambiar);
    Reveal.on("slidechanged", cerrar);
  } else {
    window.addEventListener("load", () => marcar(document));
  }
})();
