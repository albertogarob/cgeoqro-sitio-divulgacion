/* Anotador de revisión para los decks del curso.
   Se activa solo si la URL lleva ?revisar, ?review, ?revision o ?rev,
   así nunca estorba al presentar.

   Teclas:  A  anota la diapositiva actual (cita el texto seleccionado, si hay)
            C  cambia el nivel de recorte de la diapositiva actual, entre
               núcleo, recorte 1 y recorte 2
            L  abre la lista de notas, de la lámina o del deck entero
            R  abre la rejilla de láminas, para cambiarlas de orden
               arrastrándolas con el ratón
            G  abre el guion de la lámina en una ventana aparte, la misma
               vista con la que se presenta, y se anota ahí con la tecla A
            E  exporta todas las notas y las copia al portapapeles

   El texto citado queda resaltado en amarillo, sobre la lámina y sobre el
   guion. Un clic en el resaltado abre su nota para editarla o eliminarla, y
   mientras tanto la deja seleccionada, pintada de naranja. La selección se
   quita al pinchar en otro sitio, al seleccionar otra nota, al cambiar de
   diapositiva o con Escape.

   G abre la vista de guion, que desde el 8 de octubre de 2026 es la misma con
   la que se da la clase, la de la tecla T: una ventana aparte, una lámina a la
   vez, columna estrecha, el párrafo en curso resaltado y el resto atenuado.
   Antes era el deck entero como manuscrito continuo dentro de esta página.
   Alberto lo pidió así para revisar el guion tal como lo va a leer. El detalle
   está en el comentario de abrirLector, más abajo.

   Lo que esa ventana añade a la de presentar: se anota con A, los resaltados
   de las notas se ven y se pinchan, lee la reescritura pendiente en vez del
   archivo, y lleva abajo una barra con lo que se puede cambiar de la lámina.

   En esa barra está el botón "Editar guion": el texto se vuelve editable y lo
   que se escriba se guarda como reescritura pendiente, sin tocar el deck. El
   export la incluye aparte, bajo "Guion reescrito", para aplicarla al HTML, que
   sigue siendo la fuente única.

   La barra lleva además el nivel de recorte de la lámina, con sus tres botones,
   y el guion corto, que se escribe y se corrige con el mismo editor que el
   largo. Los dos, el nivel y el guion corto, viajan como cambios pendientes
   junto a las notas, y salen en el export bajo "Guion corto" y "Nivel de
   recorte". Qué significa cada nivel está en el comentario de nivelDelDeck.

   La tecla L, y también el contador de la barra, abren la lista de notas,
   que alterna entre las de la diapositiva y las del deck entero. Pinchar una
   nota de la lista lleva a su diapositiva, o al punto del guion donde está,
   y la deja seleccionada. Es además la vía para editar las notas que no
   citan nada, que no tienen resaltado donde pinchar.

   Cuando las correcciones ya están aplicadas al HTML, junto al deck aparece un
   resueltas.js con la lista de lo corregido. El anotador lo carga al arrancar y
   borra esas notas él solo, así que basta con recargar para quedarse únicamente
   con lo pendiente. Lo mismo con las reescrituras del guion: la que el deck ya
   dice deja de contar como pendiente. Ver "resoluciones ya aplicadas" más abajo.

   La tecla R abre la rejilla: todas las láminas en miniatura, a pantalla
   completa, y arrastrando una con el ratón se cambia de sitio, como en
   PowerPoint, con una línea vertical que enseña entre qué dos láminas va a
   caer. Ctrl+Z deshace el último movimiento, y otra vez el anterior. El deck pasa a mostrar el orden nuevo en el acto, pero el HTML
   no se toca: el orden viaja como cambio pendiente junto a las notas, la barra
   lo dice mientras no esté aplicado, y se lleva al archivo con
   tools/reordenar.py. Ver "el orden de las láminas" más abajo.

   Las notas viven en disco, en sesiones/<deck>/notas.json, servido por
   tools/servir.py. localStorage es solo la red de seguridad para cuando no hay
   servidor, y entonces la barra lo avisa en amarillo. Ver "dónde viven las
   notas" más abajo.

   Sobreviven a recargas y a que yo reescriba el HTML, porque se guardan contra
   el id de cada diapositiva.
   El resaltado no se guarda: se vuelve a localizar en cada carga buscando la
   cita dentro del texto. Si edito la lámina y la frase cambia, la nota sigue
   ahí, pero deja de estar resaltada y la lista la marca como sin localizar. */
(function () {
  // Acepta cualquiera de las variantes razonables, para no fallar por la palabra exacta.
  if (!/[?&](revisar|revision|revisi[oó]n|review|rev)\b/i.test(location.search)) return;

  const DECK = location.pathname.split("/").filter(Boolean).slice(-2)[0] || "deck";

  // reveal.js, con hash activo, le quita el atributo id a la lámina visible
  // para que el navegador no salte por anclaje, y se lo devuelve al salir.
  // Por eso el id se captura una sola vez, ahora, y se consulta por índice.
  const PISTA = document.querySelector(".reveal .slides");
  // El id se guarda contra el elemento, no contra su posición: desde que la
  // rejilla puede cambiar el orden, la posición deja de identificar la lámina y
  // SECS hay que volver a leerlo del DOM. El elemento, en cambio, es el mismo
  // antes y después de moverlo, y con él viajan sus notas.
  const SID = new WeakMap();
  let SECS = [...document.querySelectorAll(".reveal .slides > section")];
  SECS.forEach((x, i) => SID.set(x, x.dataset.sid || x.id || "diapositiva-" + (i + 1)));
  let IDS = SECS.map((x) => SID.get(x));
  // El orden que dice el HTML, capturado antes de aplicar ningún cambio
  // pendiente. Es contra este contra el que se mide si el orden está pendiente.
  const ORDEN_DECK = IDS.slice();
  const idDe = (sec) => (sec && SID.get(sec)) || (sec && sec.id) || "diapositiva-1";
  // Vuelve a leer las láminas del DOM, en el orden en que están ahora.
  const releer = () => {
    SECS = [...PISTA.querySelectorAll(":scope > section")];
    IDS = SECS.map(idDe);
  };
  const LLAVE = "revision:" + DECK;
  const LLAVE_G = "guion:" + DECK;
  const LLAVE_C = "corto:" + DECK;
  const LLAVE_X = "recorte:" + DECK;
  const LLAVE_D = "orden:" + DECK;
  const LLAVE_N = "nuevas:" + DECK;
  const LLAVE_B = "borradas:" + DECK;
  const LLAVE_F = "fusiones:" + DECK;
  const LLAVE_OFF = "sinservidor:" + DECK;
  /* Si las marcas de cambio están escondidas. Es una preferencia de vista, no
     un "ya lo vi": lo que cambió sigue guardado y vuelve con la misma tecla.
     Va por deck y no global porque una sesión puede estar ya revisada y la de
     al lado no. */
  const LLAVE_OC = "cambios-ocultos:" + DECK;
  const RUTA = "/notas/" + DECK;
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const plano = (s) => String(s).replace(/\s+/g, " ").trim();
  const nuevoNid = () => "n" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  const copia = (o) => JSON.parse(JSON.stringify(o));
  const sello = () => new Date().toISOString().slice(0, 16);

  /* Dónde viven las notas.

     En disco, en sesiones/<deck>/notas.json, servido por tools/servir.py. Eso es
     lo que permite leerlas con cat desde cualquier sesión, sin depender de que
     haya una extensión conectada al navegador ni de copiar y pegar nada.

     localStorage se queda como red de seguridad. Si el deck se abrió con doble
     clic, o el servidor está apagado, las notas se guardan ahí y la barra lo
     avisa en rojo; en cuanto aparece el servidor, se suben solas.

     EST es la copia en memoria de la que leen todas las vistas. El archivo lleva
     un contador de versión: si alguien escribió entre medias, el servidor
     contesta 409 con lo vigente y reaplicamos nuestro cambio encima, en vez de
     pisar lo que ya no habíamos visto. */
  const EST = { v: 0, notas: {}, guiones: {}, cortos: {}, recortes: {},
                orden: [], nuevas: [], borradas: [], fusiones: [], cambios: {} };
  let SERVIDOR = false;          // ¿hay servidor detrás?
  // lo último que sabemos que está en disco
  let ULTIMO = { notas: {}, guiones: {}, cortos: {}, recortes: {},
                 orden: [], nuevas: [], borradas: [], fusiones: [] };

  /* Los tres apartados que van por lámina, contra su id, y que viajan con las
     notas en el mismo archivo: el guion reescrito, el guion corto y el nivel de
     recorte. Los tres son cambios pendientes de aplicar al HTML, que sigue
     siendo la fuente única, y los tres se sueltan solos en cuanto el deck ya
     los dice. Se tratan en bloque para no repetir tres veces la misma lógica. */
  const MAPAS = ["guiones", "cortos", "recortes"];
  const LLAVES = { guiones: LLAVE_G, cortos: LLAVE_C, recortes: LLAVE_X };

  const espejo = () => {
    try {
      localStorage.setItem(LLAVE, JSON.stringify(EST.notas));
      MAPAS.forEach((k) => localStorage.setItem(LLAVES[k], JSON.stringify(EST[k])));
      localStorage.setItem(LLAVE_D, JSON.stringify(EST.orden));
      localStorage.setItem(LLAVE_N, JSON.stringify(EST.nuevas));
      localStorage.setItem(LLAVE_B, JSON.stringify(EST.borradas));
      localStorage.setItem(LLAVE_F, JSON.stringify(EST.fusiones));
    } catch {}
  };

  const guardar = (o) => { EST.notas = o || {}; espejo(); sincronizar(); };
  const guardarMapa = (k, o) => { EST[k] = o || {}; espejo(); sincronizar(); };
  const guardarGuiones = (o) => guardarMapa("guiones", o);
  const guardarCortos = (o) => guardarMapa("cortos", o);
  const guardarRecortes = (o) => guardarMapa("recortes", o);
  const leerGuiones = () => EST.guiones;
  const leerCortos = () => EST.cortos;
  const leerRecortes = () => EST.recortes;
  const leerOrden = () => EST.orden;
  const leerNuevas = () => EST.nuevas;
  const leerBorradas = () => EST.borradas;
  const leerFusiones = () => EST.fusiones;
  // Los tres se guardan de una vez: un cambio suele tocar dos, y guardarlos por
  // separado mandaría al servidor un estado a medias entre los dos envíos.
  const guardarDeck = (o) => {
    if (o.orden) EST.orden = o.orden;
    if (o.nuevas) EST.nuevas = o.nuevas;
    if (o.borradas) EST.borradas = o.borradas;
    if (o.fusiones) EST.fusiones = o.fusiones;
    espejo();
    sincronizar();
  };

  function leer() {
    const d = EST.notas;
    // Las notas de antes no traían identificador propio. Se lo ponemos al vuelo,
    // que es lo que permite que un resaltado sepa a qué nota corresponde.
    let faltaban = false;
    Object.values(d).forEach((lista) => (lista || []).forEach((x) => {
      if (!x.nid) { x.nid = nuevoNid(); faltaban = true; }
    }));
    if (faltaban) guardar(d);
    return d;
  }

  /* ---------- lo que cambió desde la última vez que miró ----------

     Alberto pidió el 12 de octubre de 2026 ver los cambios **donde están**,
     marcados en la propia lámina y en la propia ventana del guion, en vez de
     leerse un reporte mío. El cálculo no se hace aquí: lo hace
     `tools/cambios.py` comparando el deck con su foto, y por la misma razón que
     las parcelas y las anclas, porque cuando el deck llega al navegador MathJax
     ya se llevó el texto de las expresiones.

     Aquí solo se pinta: una marca en la pieza tocada, con el texto de antes en
     un globo al pasar el ratón, y el guion con las palabras nuevas y las
     quitadas. Lo eligió así él mismo: la lámina tiene que seguir viéndose como
     se va a proyectar, y un tachado dentro de una viñeta la desborda. */

  /* **Dos cuentas, no una.** Una lámina borrada queda registrada en
     `cambios.laminas` con su título y su estado, pero ya no está en el deck:
     no se le puede marcar una pieza, ni navegar a ella, ni aparecía en la
     lista, que se construye recorriendo IDS. Contándolas juntas, la chapa
     prometía 40 láminas y la lista enseñaba 36, y las cuatro que faltaban eran
     justo el cambio más gordo del día, una sección entera retirada. Lo cazó
     Alberto el 13 de octubre de 2026 mirando la barra. */
  const camLaminas = () => EST.cambios.laminas || {};
  const camBorradas = () =>
    Object.keys(camLaminas()).filter((sid) => IDS.indexOf(sid) < 0);
  const camVivas = () =>
    Object.keys(camLaminas()).filter((sid) => IDS.indexOf(sid) >= 0);
  const hayCambios = () => Object.keys(camLaminas()).length;
  const camOcultos = () => {
    try { return localStorage.getItem(LLAVE_OC) === "1"; } catch (e) { return false; }
  };
  // Escondidos, nadie los pinta: ni la lámina, ni la ventana del guion, ni la
  // rejilla. La lista de la tecla X sí los sigue enseñando, porque esa se abre
  // a propósito.
  const cambiosDe = (sid) =>
    (camOcultos() ? null : (EST.cambios.laminas || {})[sid] || null);

  /* La tecla Z esconde y muestra las marcas. Alberto la pidió el 13 de octubre
     de 2026. Está pegada a la X, que es la que abre la lista, para que las dos
     se recuerden juntas.

     No es lo mismo que "ya lo vi": aquello toma la foto nueva y olvida, esto
     solo deja de pintarlas. Por eso la chapa de la barra se queda, diciendo que
     están escondidas: si desapareciera todo, no habría manera de saber que hay
     algo que mirar. */
  function alternarCambios() {
    if (!hayCambios()) return;
    try { localStorage.setItem(LLAVE_OC, camOcultos() ? "0" : "1"); } catch (e) {}
    marcarCambios();
    cerrarGloboCambio();
    pintarBarra();
    if (docLector() && !edicionGuion) pintarLector(true);
    if (rejilla && !tirando) pintarRejillaEstado();
  }

  // El texto de antes y el de ahora, reconstruidos del diff para el globo.
  const difAntes = (dif) => dif.filter(([op]) => op !== "+").map(([, t]) => t).join("");

  function difHTML(dif, doc) {
    const d = doc || document;
    const cont = d.createElement("span");
    dif.forEach(([op, t]) => {
      if (op === "=") { cont.appendChild(d.createTextNode(t)); return; }
      const e = d.createElement(op === "+" ? "ins" : "del");
      e.className = op === "+" ? "rv-mas" : "rv-menos";
      e.textContent = t;
      cont.appendChild(e);
    });
    return cont;
  }

  /* Las marcas sobre la lámina en curso. Se ponen y se quitan enteras en cada
     cambio de diapositiva: así nunca queda una marca de la lámina anterior. */
  function marcarCambios() {
    [...document.querySelectorAll(".rv-cam")].forEach((x) => {
      x.classList.remove("rv-cam");
      delete x.dataset.rvAntes;
    });
    const sec = document.querySelector(".reveal section.present");
    if (!sec) return;
    const c = cambiosDe(sec.dataset.sid || sec.id);
    if (!c) return;
    (c.piezas || []).forEach((p) => {
      if (!p.n) return;
      const el = sec.querySelector('[data-pieza="' + p.n + '"]');
      if (!el) return;
      el.classList.add("rv-cam");
      el.dataset.rvAntes = difAntes(p.dif).trim() || "(no estaba)";
    });
  }

  // El globo con el texto de antes, al pasar el ratón por una pieza marcada.
  let globoCam = null;
  function globoCambio(el) {
    cerrarGloboCambio();
    globoCam = document.createElement("div");
    globoCam.className = "rv-cam-pop";
    globoCam.innerHTML = "<b>antes decía</b>";
    const p = document.createElement("p");
    p.textContent = el.dataset.rvAntes;
    globoCam.appendChild(p);
    document.body.appendChild(globoCam);
    const r = el.getBoundingClientRect(), g = globoCam.getBoundingClientRect();
    let top = r.top - g.height - 10;
    if (top < 6) top = Math.min(r.bottom + 10, innerHeight - g.height - 6);
    globoCam.style.top = Math.max(6, top) + "px";
    globoCam.style.left =
      Math.max(6, Math.min(r.left, innerWidth - g.width - 6)) + "px";
  }
  function cerrarGloboCambio() {
    if (globoCam) { globoCam.remove(); globoCam = null; }
  }

  /* La lista de lo que cambió, con la tecla X. Es la hermana de la lista de
     notas: enseña el deck entero de un vistazo y lleva a cada sitio. */
  let panelCam = null;

  function abrirCambios() {
    // `isConnected` y no solo "no es nulo": Escape cierra la capa por su cuenta,
    // sin pasar por cerrarCambios(), y la referencia se quedaba apuntando a un
    // nodo ya sacado del documento. Entonces la X siguiente creía que estaba
    // abierta y no la reabría. Lo cazó tools/prueba-vercambios.py.
    if (panelCam && panelCam.isConnected) { cerrarCambios(); return; }
    panelCam = null;
    if (!hayCambios()) return;
    const lam = EST.cambios.laminas || {};
    const filas = IDS.filter((sid) => lam[sid]).map((sid) => {
      const c = lam[sid], i = IDS.indexOf(sid);
      const trozos = [];
      (c.piezas || []).forEach((x) => trozos.push(["lámina", x.dif]));
      (c.guion || []).forEach((x) => trozos.push(["guion", x.dif]));
      (c.corto || []).forEach((x) => trozos.push(["corto", x.dif]));
      return '<div class="rv-cam-fila" data-i="' + i + '">' +
        '<b>' + (i + 1) + ". " + esc(c.titulo || sid) + "</b>" +
        (c.estado !== "cambiada" ? '<i class="rv-cam-et">' + c.estado + "</i>" : "") +
        (c.movida ? '<i class="rv-cam-et">movida de la ' + c.movida[0] +
          " a la " + c.movida[1] + "</i>" : "") +
        (c.recorte ? '<i class="rv-cam-et">recorte: ' + (c.recorte[0] || "núcleo") +
          " a " + (c.recorte[1] || "núcleo") + "</i>" : "") +
        trozos.map(([donde, dif]) => '<p><i>' + donde + "</i> " +
          dif.map(([op, t]) => op === "=" ? '<span class="rv-cam-ig">' + esc(t) + "</span>"
                : op === "+" ? '<ins class="rv-mas">' + esc(t) + "</ins>"
                : '<del class="rv-menos">' + esc(t) + "</del>").join("") + "</p>").join("") +
        "</div>";
    }).join("");
    const idas = camBorradas().map((sid) => {
      const c = lam[sid];
      return '<div class="rv-cam-fila rv-cam-ida">' +
        "<b>" + esc(c.titulo || sid) + "</b>" +
        '<i class="rv-cam-et">' + (c.estado || "borrada") + "</i>" +
        "<p>Ya no está en el deck, así que no se puede ir a ella.</p></div>";
    }).join("");
    const vivas = camVivas().length, fuera = camBorradas().length;
    panelCam = capa(
      '<h3>Lo que cambió desde la última vez que lo viste</h3>' +
      '<p class="rv-ayuda">' + vivas + ' lámina' + (vivas === 1 ? "" : "s") +
      " en el deck" + (fuera ? " y " + fuera + " que se fueron" : "") +
      '. En la lámina, la pieza tocada queda marcada y el texto de antes sale en ' +
      'un globo al pasar el ratón. En la ventana del guion, las palabras nuevas ' +
      'y las quitadas. Pincha una lámina para ir a ella.</p>' +
      '<div class="rv-cam-lista">' + filas + idas + "</div>" +
      '<div class="rv-bot"><button type="button" data-rv="esconder">' +
      (camOcultos() ? "Mostrar las marcas" : "Esconder las marcas") + "</button>" +
      '<button type="button" data-rv="visto">Ya lo vi, borra las marcas</button>' +
      '<button type="button" data-rv="cerrar">Cerrar</button></div>',
      (caja) => {
        caja.addEventListener("click", (e) => {
          const f = e.target.closest(".rv-cam-fila");
          const b = e.target.closest("button[data-rv]");
          if (b && b.dataset.rv === "visto") { darPorVisto(); return; }
          if (b && b.dataset.rv === "esconder") {
            alternarCambios(); cerrarCambios(); return;
          }
          if (b && b.dataset.rv === "cerrar") { cerrarCambios(); return; }
          if (f && f.dataset.i !== undefined) {
            navPropia = true; Reveal.slide(parseInt(f.dataset.i, 10));
            navPropia = false; cerrarCambios();
          }
        });
      });
  }

  function cerrarCambios() {
    if (panelCam) { panelCam.remove(); panelCam = null; }
  }

  /* "Ya lo vi": el servidor copia el deck de ahora como foto nueva y borra las
     marcas, las dos cosas juntas. Sin servidor solo se borran aquí, y la foto la
     toma tools/cambios.py en su pasada siguiente, que es lo que se le dice. */
  function darPorVisto() {
    cerrarCambios();
    // Lo escondido era de esta tanda: la siguiente se ve, o no se vería nunca.
    try { localStorage.removeItem(LLAVE_OC); } catch (e) {}
    if (!SERVIDOR) {
      EST.cambios = {};
      marcarCambios();
      pintarBarra();
      if (docLector()) pintarLector(true);
      aviso("Marcas borradas solo en este navegador. Sin servidor no se puede " +
            "tomar la foto nueva, así que la próxima comparación puede repetirlas.");
      return;
    }
    fetch(RUTA.replace("/notas/", "/foto/"), { method: "PUT", cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((j) => {
        EST.v = j.v;
        EST.cambios = {};
        marcarCambios();
        pintarBarra();
        if (docLector()) pintarLector(true);
      })
      .catch(() => aviso("No pude tomar la foto. ¿Sigue levantado tools/servir.py?"));
  }

  /* ---------- sincronización con el disco ---------- */

  function desdeLocal() {
    try { EST.notas = JSON.parse(localStorage.getItem(LLAVE)) || {}; } catch { EST.notas = {}; }
    MAPAS.forEach((k) => {
      try { EST[k] = JSON.parse(localStorage.getItem(LLAVES[k])) || {}; } catch { EST[k] = {}; }
    });
    try { EST.orden = JSON.parse(localStorage.getItem(LLAVE_D)) || []; } catch { EST.orden = []; }
    try { EST.nuevas = JSON.parse(localStorage.getItem(LLAVE_N)) || []; } catch { EST.nuevas = []; }
    try { EST.borradas = JSON.parse(localStorage.getItem(LLAVE_B)) || []; } catch { EST.borradas = []; }
    try { EST.fusiones = JSON.parse(localStorage.getItem(LLAVE_F)) || []; } catch { EST.fusiones = []; }
    ["orden", "nuevas", "borradas", "fusiones"].forEach((k) => {
      if (!Array.isArray(EST[k])) EST[k] = [];
    });
  }

  const instantanea = () => {
    const o = { notas: EST.notas, orden: EST.orden, nuevas: EST.nuevas,
                borradas: EST.borradas, fusiones: EST.fusiones };
    MAPAS.forEach((k) => { o[k] = EST[k]; });
    return copia(o);
  };

  function adoptar(d) {
    EST.v = d.v || 0;
    EST.notas = d.notas || {};
    MAPAS.forEach((k) => { EST[k] = d[k] || {}; });
    EST.orden = Array.isArray(d.orden) ? d.orden : [];
    EST.nuevas = Array.isArray(d.nuevas) ? d.nuevas.filter((x) => x && x.id) : [];
    EST.borradas = Array.isArray(d.borradas) ? d.borradas.filter((x) => typeof x === "string") : [];
    EST.fusiones = Array.isArray(d.fusiones)
      ? d.fusiones.filter((x) => x && x.id && Array.isArray(x.partes)) : [];
    // Lo que cambió desde la última vez que Alberto miró. Lo escribe
    // tools/cambios.py comparando el deck con su foto de referencia, y aquí
    // solo se pinta: el anotador no lo calcula ni lo modifica, salvo para
    // darlo por visto, que va por la ruta /foto del servidor.
    EST.cambios = (d.cambios && d.cambios.laminas) ? d.cambios : {};
    ULTIMO = instantanea();
    espejo();
  }

  function sinServidor() {
    SERVIDOR = false;
    try { localStorage.setItem(LLAVE_OFF, "1"); } catch {}
    pintarBarra();
  }

  const porNid = (notas) => {
    const m = new Map();
    Object.keys(notas || {}).forEach((id) => (notas[id] || []).forEach((x) => m.set(x.nid, { id, x })));
    return m;
  };
  const quitar = (notas, nid) => Object.keys(notas).forEach((id) => {
    notas[id] = notas[id].filter((x) => x.nid !== nid);
    if (!notas[id].length) delete notas[id];
  });

  // Nuestro cambio, reaplicado sobre lo que hay ahora en disco. Se calcula
  // comparando con ULTIMO, que es lo que había cuando empezamos a tocar.
  function reaplicar(srv) {
    const antes = porNid(ULTIMO.notas), ahora = porNid(EST.notas);
    antes.forEach((_, nid) => { if (!ahora.has(nid)) quitar(srv.notas, nid); });
    ahora.forEach(({ id, x }, nid) => {
      const a = antes.get(nid);
      if (a && JSON.stringify(a.x) === JSON.stringify(x)) return;
      quitar(srv.notas, nid);
      (srv.notas[id] = srv.notas[id] || []).push(x);
    });
    MAPAS.forEach((k) => {
      srv[k] = srv[k] || {};
      Object.keys(ULTIMO[k]).forEach((id) => { if (!EST[k][id]) delete srv[k][id]; });
      Object.keys(EST[k]).forEach((id) => {
        if (JSON.stringify(ULTIMO[k][id]) !== JSON.stringify(EST[k][id])) srv[k][id] = EST[k][id];
      });
    });
    // Los tres apartados del deck entero, no por lámina: el orden, las láminas
    // por escribir y las marcadas para borrar. No hay manera de fundir dos, así
    // que manda el que los tocó; si no los tocamos nosotros, se respeta el disco.
    // Van juntos porque una lámina nueva es a la vez un id en `orden` y una
    // entrada en `nuevas`: separarlos dejaría una de las dos sin la otra.
    if (["orden", "nuevas", "borradas", "fusiones"].some(
          (k) => JSON.stringify(ULTIMO[k]) !== JSON.stringify(EST[k]))) {
      srv.orden = EST.orden;
      srv.nuevas = EST.nuevas;
      srv.borradas = EST.borradas;
      srv.fusiones = EST.fusiones;
    }
    adoptar(srv);
    refrescar();
  }

  let enVuelo = false, pendiente = false, choques = 0;
  function sincronizar() {
    if (!SERVIDOR) { pintarBarra(); return; }
    if (enVuelo) { pendiente = true; return; }
    enVuelo = true;
    fetch(RUTA, {
      method: "PUT", cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.assign({ v: EST.v }, instantanea())),
    })
      .then((r) => r.json().then((j) => ({ ok: r.ok, code: r.status, j })))
      .then(({ ok, code, j }) => {
        if (ok) { EST.v = j.v; ULTIMO = instantanea(); choques = 0; return; }
        if (code === 409 && ++choques <= 3) { reaplicar(j); pendiente = true; return; }
        throw new Error("http " + code);
      })
      .catch(() => sinServidor())
      .then(() => {
        enVuelo = false;
        if (pendiente) { pendiente = false; sincronizar(); }
      });
  }

  function cargar() {
    return fetch(RUTA, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        SERVIDOR = true;
        TS_DECK = d.deck || null;
        const huerfanas = localStorage.getItem(LLAVE_OFF);
        const mias = EST.notas, mios = {};
        const miOrden = { orden: EST.orden, nuevas: EST.nuevas, borradas: EST.borradas,
                          fusiones: EST.fusiones };
        MAPAS.forEach((k) => { mios[k] = EST[k]; });
        adoptar(d);
        // Notas tomadas mientras no había servidor: se suben en vez de perderse.
        if (huerfanas) {
          const hay = porNid(EST.notas);
          let n = 0;
          porNid(mias).forEach(({ id, x }, nid) => {
            if (hay.has(nid)) return;
            (EST.notas[id] = EST.notas[id] || []).push(x); n++;
          });
          MAPAS.forEach((k) => Object.keys(mios[k]).forEach((id) => {
            if (!EST[k][id]) { EST[k][id] = mios[k][id]; n++; }
          }));
          if (miOrden.orden.length && !EST.orden.length) {
            EST.orden = miOrden.orden;
            EST.nuevas = miOrden.nuevas;
            EST.borradas = miOrden.borradas;
            EST.fusiones = miOrden.fusiones;
            n++;
          }
          localStorage.removeItem(LLAVE_OFF);
          if (n) { sincronizar(); aviso("Se subieron al disco " + n + " apunte" + (n === 1 ? "" : "s") + " que estaban solo en este navegador."); }
        }
      })
      .catch(() => { SERVIDOR = false; });
  }

  // Si el archivo cambia por fuera, por ejemplo porque acabo de aplicar las
  // correcciones, la vista se pone al día sola en unos segundos.
  function vigilar() {
    setInterval(() => {
      if (!SERVIDOR || enVuelo || pendiente || document.hidden) return;
      fetch(RUTA, { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((d) => {
          if (TS_DECK && d.deck && d.deck !== TS_DECK) ofrecerRecarga();
          if (d.v === EST.v) return;
          const antes = Object.values(EST.notas).reduce((a, x) => a + x.length, 0);
          adoptar(d);
          aplicarOrden();
          refrescar();
          const ahora = totalNotas();
          aviso(ahora < antes
            ? (antes - ahora) + " nota" + (antes - ahora === 1 ? "" : "s") + " ya corregida" +
              (antes - ahora === 1 ? "" : "s") + ", fuera. " +
              (ahora ? "Quedan " + ahora + "." : "No queda ninguna.")
            : "Las notas cambiaron en disco. Actualizado.");
        })
        .catch(() => sinServidor());
    }, 4000);
  }
  function buscarNota(nid) {
    const d = leer();
    for (const id of Object.keys(d)) {
      const i = (d[id] || []).findIndex((x) => x.nid === nid);
      if (i >= 0) return { datos: d, id, i, nota: d[id][i] };
    }
    return null;
  }
  function eliminarNota(nid) {
    const r = buscarNota(nid);
    if (!r) return false;
    r.datos[r.id].splice(r.i, 1);
    if (!r.datos[r.id].length) delete r.datos[r.id];
    guardar(r.datos);
    return true;
  }

  /* Reescrituras del guion. Viajan junto a las notas, en el mismo archivo pero
     en su propio apartado, y no tocan el <aside class="notes"> del deck: eso lo
     aplico yo al HTML, que es la fuente única. Mientras tanto la vista de guion
     muestra la versión reescrita. */
  // El texto de trabajo es un párrafo por bloque, separados por un renglón en
  // blanco. Se toma el innerHTML de cada <p>, no su texto, para no perder por el
  // camino un <em> o un <strong> si algún guion los llega a llevar.
  const guionATexto = (aside) => {
    const ps = [...aside.querySelectorAll("p")];
    return (ps.length ? ps.map((x) => x.innerHTML.trim()) : [aside.innerHTML.trim()]).join("\n\n");
  };
  const textoAGuion = (t) => String(t).split(/\n\s*\n/).map((x) => x.trim()).filter(Boolean)
    .map((x) => "<p>" + x + "</p>").join("") || "<p><em>(sin guion)</em></p>";
  const guionDelDeck = (i) => {
    const a = SECS[i] && SECS[i].querySelector("aside.notes");
    return a ? guionATexto(a) : "";
  };

  /* El guion corto y el nivel de recorte.

     El guion corto es la versión de treinta o cuarenta segundos de una lámina,
     escrita de antemano, que el apuntador lee en su lugar cuando la sesión va
     tarde. Vive en el deck en un <aside class="corto"> al lado del guion largo,
     y se reescribe igual que el largo, con su propio botón en la barra de la
     ventana del guion.

     El nivel de recorte dice cuánto cuesta perder la lámina, y nada más:

       sin marca  núcleo. No se recorta nunca: o la sesión no cumple su objetivo,
                  o la siguiente se rompe porque la da por vista.
       1          se pierde y nadie se entera. Repite o refuerza algo ya dicho.
                  Se puede cortar sin avisar al grupo y sin deber nada.
       2          se pierde, pero hay que decirlo. El contenido importa y no es
                  hoy, así que al cortarla se anuncia y queda pendiente.

     Que se abrevie o que se salte no lo decide el nivel, lo decide si la lámina
     tiene guion corto escrito. El apuntador abrevia siempre que puede y solo
     salta cuando no hay versión corta o cuando abreviando no le alcanza. */
  const cortoDelDeck = (i) => {
    const a = SECS[i] && SECS[i].querySelector("aside.corto");
    return a ? guionATexto(a) : "";
  };
  const cortoDe = (i) => {
    const c = leerCortos()[IDS[i]];
    return c ? c.texto : cortoDelDeck(i);
  };
  const hayCorto = (i) => !!plano(cortoDe(i));

  const nivelValido = (n) => (n === 1 || n === 2 ? n : 0);
  const nivelDelDeck = (i) =>
    nivelValido(SECS[i] ? parseInt(SECS[i].dataset.recorte || "", 10) : 0);
  // El vigente para la vista: el pendiente si lo hay, si no el que dice el deck.
  const nivelDe = (i) => {
    const x = leerRecortes()[IDS[i]];
    return x ? nivelValido(x.nivel | 0) : nivelDelDeck(i);
  };
  const NOMBRE_NIVEL = ["núcleo", "recorte 1", "recorte 2"];
  const QUE_ES_NIVEL = [
    "Núcleo: no se recorta nunca.",
    "Recorte 1: se puede quitar sin avisar al grupo, porque repite o refuerza algo ya dicho.",
    "Recorte 2: se puede quitar, pero hay que decirlo en clase y queda pendiente para después.",
  ];

  // Guardar el nivel es guardar un cambio pendiente, no tocar el deck: si vuelve
  // a coincidir con lo que el HTML ya dice, deja de estar pendiente.
  function ponerNivel(i, n) {
    const x = leerRecortes();
    if (nivelValido(n) === nivelDelDeck(i)) delete x[IDS[i]];
    else x[IDS[i]] = { nivel: nivelValido(n), ts: new Date().toISOString().slice(0, 16) };
    guardarRecortes(x);
  }

  /* El orden de las láminas.

     La rejilla, tecla R, deja arrastrar las miniaturas para cambiarlas de sitio.
     Lo que se guarda es la lista completa de ids en el orden nuevo, una sola por
     deck y no un apartado por lámina, porque mover una lámina cambia la posición
     de todas las que hay entre su sitio viejo y el nuevo.

     Es un cambio pendiente más, como el guion reescrito o el nivel de recorte:
     el HTML sigue siendo la fuente única y no se toca desde el navegador. La
     diferencia es que este sí se ve en el acto, porque el DOM se reordena
     también, para poder recorrer el deck en el orden nuevo antes de aplicarlo.
     Mientras no esté aplicado, la barra lo dice y la rejilla marca en naranja las
     láminas que cambiaron de sitio. Se lleva al archivo con tools/reordenar.py,
     y en cuanto el HTML lo dice, deja de estar pendiente él solo.

     ORDEN_DECK es el orden del HTML, capturado al cargar. EST.orden, si lo hay,
     es el pendiente. Vacío quiere decir que no hay nada pendiente. */
  const mismos = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);

  /* Las láminas por escribir y las marcadas para borrar.

     Una lámina nueva es un encargo, no una lámina: un id inventado, una
     descripción de lo que debe llevar, y su sitio en el orden. Mientras está
     pendiente se ve en el deck como una lámina de verdad, marcada, para que la
     rejilla y el minutaje cuenten con ella; al aplicarse, entra en el HTML como
     un <section> con data-pendiente que después hay que escribir.

     Una lámina borrada sigue en el HTML hasta que se aplica. Mientras tanto se
     saca del DOM, para que el deck enseñe cómo va a quedar, y se guarda aparte
     para poder devolverla. En la rejilla no desaparece: se queda tachada, que es
     lo que permite arrepentirse sin buscarla. */
  /* Las fusiones: dos o más láminas que hay que combinar en una.

     Aquí no se combina nada. Combinar es trabajo de contenido, no de un script:
     hay que decidir qué viñetas sobreviven y refundir el guion, el guion corto y
     los apuntes. Lo que guarda la rejilla es el encargo, con sus partes en el
     orden en que se quieren leer y una nota opcional; si la nota está vacía, el
     criterio lo pongo yo al escribirla.

     A diferencia de las borradas, las partes **no salen del deck**: se quedan
     todas, marcadas, hasta que la fusión esté escrita. Así se puede recorrer el
     deck viendo qué se va a juntar con qué, al precio de que el minutaje siga
     contando tres láminas donde va a haber una hasta que se escriba.

     La primera parte es el ancla: es la que se queda al final, en su sitio, y la
     que lleva la nota. Las partes pueden no ser contiguas. */
  const idsNuevas = () => leerNuevas().map((x) => x.id);
  const laFusion = (id) => leerFusiones().find((f) => f.partes.includes(id)) || null;
  const enFusion = (id) => !!laFusion(id);
  // Una fusión que ya no tiene al menos dos partes deja de contar: se quedó coja.
  const partesVivas = (f) => f.partes.filter((id) => ORDEN_DECK.includes(id) || esNueva(id));

  /* Y una que el deck ya dice tampoco cuenta como pendiente, igual que pasa con
     el guion reescrito o el nivel de recorte: cuando reordenar.py la aplica, el
     ancla queda con data-combinar nombrando a las demás. A partir de ahí el
     encargo vive en el HTML y lo que falta es escribir la lámina única, que no
     es cosa de la rejilla. */
  const seccionDe = (id) => [...PISTA.querySelectorAll(":scope > section")]
    .find((x) => idDe(x) === id) || GUARDADAS.get(id) || null;
  const fusionAplicada = (f) => {
    const a = seccionDe(f.partes[0]);
    if (!a || !a.dataset.combinar) return false;
    const dice = a.dataset.combinar.split(/\s+/).filter(Boolean).join(" ");
    return dice === f.partes.slice(1).join(" ");
  };
  const fusionesVivas = () =>
    leerFusiones().filter((f) => partesVivas(f).length > 1 && !fusionAplicada(f));
  const esNueva = (id) => leerNuevas().some((x) => x.id === id);
  const esBorrada = (id) => leerBorradas().includes(id);
  const laNueva = (id) => leerNuevas().find((x) => x.id === id) || null;
  const GUARDADAS = new Map();     // las láminas sacadas del DOM, por si vuelven

  // Un orden pendiente puede haberse quedado viejo: que yo haya insertado o
  // borrado láminas en el HTML mientras él seguía guardado. En vez de tirarlo,
  // se concilia: se respeta el orden pendiente de las que siguen existiendo, y
  // las que no menciona se meten detrás de la vecina que las precede en el deck.
  // Las láminas por escribir cuentan como existentes aunque no estén en el HTML.
  function conciliar(orden) {
    const extras = idsNuevas();
    const hay = new Set(ORDEN_DECK.concat(extras));
    const r = [];
    orden.forEach((id) => { if (hay.has(id) && !r.includes(id)) r.push(id); });
    ORDEN_DECK.forEach((id, i) => {
      if (r.includes(id)) return;
      let j = -1;
      for (let k = i - 1; k >= 0 && j < 0; k--) j = r.indexOf(ORDEN_DECK[k]);
      r.splice(j + 1, 0, id);
    });
    extras.forEach((id) => { if (!r.includes(id)) r.push(id); });
    return r;
  }

  // El orden completo, con las borradas incluidas: es lo que enseña la rejilla,
  // y lo que se guarda, para que una lámina que se devuelve vuelva a su sitio.
  const ordenCompleto = () =>
    (leerOrden().length || idsNuevas().length ? conciliar(leerOrden()) : ORDEN_DECK.slice());
  // El orden que hay que ver en el deck: el completo menos lo que se va a borrar.
  const ordenVigente = () => ordenCompleto().filter((id) => !esBorrada(id));
  // Pendiente es lo que el HTML todavía no dice. Una lámina por escribir cuyo id
  // ya está en el deck, o una borrada que ya no existe, están aplicadas: contarlas
  // dejaría la revisión pendiente para siempre.
  const nuevasVivas = () => leerNuevas().filter((x) => !ORDEN_DECK.includes(x.id));
  const borradasVivas = () => leerBorradas().filter((id) => ORDEN_DECK.includes(id));
  const ordenPendiente = () => !mismos(ordenVigente(), ORDEN_DECK) ||
                               !!nuevasVivas().length || !!borradasVivas().length ||
                               !!fusionesVivas().length;

  /* Cuáles cambiaron de sitio de verdad.

     Compararlas posición a posición contra el deck exagera: subir una lámina al
     principio corre una casilla a todas las demás, y la cuenta diría que se
     movió el deck entero. Lo que se marca es lo que no cabe en la subsecuencia
     común más larga con el orden del deck, que son exactamente las que hubo que
     sacar de la fila y volver a meter en otro sitio. */
  function lasMovidas(quiero) {
    const a = ORDEN_DECK, b = quiero, n = a.length, m = b.length;
    const d = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
    for (let i = n - 1; i >= 0; i--)
      for (let j = m - 1; j >= 0; j--)
        d[i][j] = a[i] === b[j] ? d[i + 1][j + 1] + 1
                                : Math.max(d[i + 1][j], d[i][j + 1]);
    const quedan = new Set();
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (a[i] === b[j]) { quedan.add(a[i]); i++; j++; }
      else if (d[i + 1][j] >= d[i][j + 1]) i++;
      else j++;
    }
    return new Set(b.filter((x) => !quedan.has(x)));
  }
  // Una lámina por escribir no está "movida": está por escribir, y lleva su
  // propia marca. Se descuenta para que la cuenta de movidas no la sume dos veces.
  const cuantasMovidas = () =>
    [...lasMovidas(ordenVigente())].filter((id) => !esNueva(id)).length;

  /* Deshacer, con Ctrl+Z.

     La pila guarda el orden que había antes de cada cambio, y vive en memoria:
     se pierde al recargar, como los trazos del pincel. No se guarda en disco a
     propósito, porque lo que importa conservar es el orden vigente, no el
     camino que se siguió para llegar a él.

     Ctrl+Z es también la tecla del pincel, así que se cede cuando el pincel
     está encendido, que es lo que dice la clase pn-activo del body, y cuando el
     foco está en una caja de texto, que entonces es de quien escribe. */
  const PILA = [];
  const TOPE_PILA = 100;

  // Se apuntan los tres a la vez: insertar una lámina toca el orden y la lista
  // de nuevas, y borrar una toca el orden y la de borradas. Deshacer a medias
  // dejaría un id en el orden sin su encargo, o al revés.
  function recordar() {
    PILA.push({ orden: ordenCompleto(), nuevas: copia(leerNuevas()),
                borradas: leerBorradas().slice(), fusiones: copia(leerFusiones()) });
    if (PILA.length > TOPE_PILA) PILA.shift();
  }

  // Guardar el orden nuevo. Si vuelve a ser el del deck y no hay nada más
  // pendiente, deja de estar pendiente del todo.
  // `apuntar` es lo que distingue un cambio, que se puede deshacer, de deshacerlo.
  // Formar, romper y describir una fusión. El ancla es la primera parte, y el
  // orden de las partes es el orden en que se quieren leer al combinarlas.
  function combinar(ids, texto) {
    const limpio = ids.filter((id, i) => ids.indexOf(id) === i && !esBorrada(id));
    if (limpio.length < 2) return null;
    const id = "fusion-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
    recordar();
    // una lámina no puede estar en dos fusiones a la vez: se saca de la anterior
    const resto = leerFusiones()
      .map((f) => Object.assign({}, f, { partes: f.partes.filter((x) => !limpio.includes(x)) }))
      .filter((f) => f.partes.length > 1);
    guardarDeck({ fusiones: resto.concat([{ id, partes: limpio, texto: texto || "",
                                            ts: sello() }]) });
    aplicarOrden();
    return id;
  }

  function romperFusion(id) {
    if (!leerFusiones().some((f) => f.id === id)) return;
    recordar();
    guardarDeck({ fusiones: leerFusiones().filter((f) => f.id !== id) });
    aplicarOrden();
  }

  // Saca una lámina de su fusión. Si se queda con una sola parte, la fusión se
  // deshace entera: combinar una lámina consigo misma no quiere decir nada.
  function sacarDeFusion(sid) {
    const f = laFusion(sid);
    if (!f) return;
    recordar();
    const partes = f.partes.filter((x) => x !== sid);
    guardarDeck({ fusiones: partes.length > 1
      ? leerFusiones().map((y) => (y.id === f.id ? Object.assign({}, y, { partes }) : y))
      : leerFusiones().filter((y) => y.id !== f.id) });
    aplicarOrden();
  }

  function ponerOrden(nuevo, apuntar) {
    if (apuntar !== false) recordar();
    const limpio = mismos(nuevo, ORDEN_DECK) && !leerNuevas().length && !leerBorradas().length;
    guardarDeck({ orden: limpio ? [] : nuevo.slice() });
    aplicarOrden();
  }

  function deshacerOrdenUno() {
    /* Con un arrastre a medias, Ctrl+Z lo cancela y no hace nada más. Dos
       razones: reconstruir la malla debajo de un arrastre dejaba la lámina
       agarrada apuntando a una rejilla que ya no existe, y al soltar se
       duplicaba en el orden guardado; y deshacer además el movimiento anterior
       sería devolver dos cosas cuando la mano solo pedía soltar una. */
    if (tirando) {
      soltar(true);
      aviso("Arrastre cancelado. Ctrl+Z otra vez deshace el movimiento anterior.", "orden");
      return;
    }
    if (!PILA.length) { aviso("No queda nada que deshacer en el orden.", "orden"); return; }
    const antes = PILA.pop();
    guardarDeck({ nuevas: antes.nuevas, borradas: antes.borradas,
                  fusiones: antes.fusiones || [] });
    ponerOrden(antes.orden, false);
    if (rejilla) reconstruirRejilla();
    pintarBarra();
    aviso(ordenPendiente()
      ? "Deshecho. Quedan " + cuantasMovidas() + " lámina" +
        (cuantasMovidas() === 1 ? "" : "s") + " fuera de su sitio" +
        (PILA.length ? ", y " + PILA.length + " paso" + (PILA.length === 1 ? "" : "s") +
         " más por deshacer." : ".")
      : "Deshecho. El deck vuelve a estar en el orden que dice el HTML.", "orden");
  }

  const enCampo = (el) => !!el && (el.isContentEditable === true ||
                          /^(?:input|textarea|select)$/i.test(el.tagName || ""));

  /* La lámina por escribir, tal como se ve en el deck mientras no se aplica.
     Es una lámina de verdad, con su id, para que la rejilla la clone como a las
     demás y para que ocupe su sitio en el recorrido. La marca data-pendiente es
     la que después lleva el HTML, y la que hace que empaquetar.py se niegue a
     entregar un deck con láminas sin escribir. */
  function crearPendiente(x) {
    const sec = document.createElement("section");
    sec.id = x.id;
    sec.dataset.sid = x.id;
    sec.dataset.pendiente = "1";
    sec.className = "guinda-linea rv-pendiente";
    sec.innerHTML = '<h2>Lámina por escribir</h2><div class="cuerpo">' +
                    '<p class="rv-encargo"></p></div>';
    SID.set(sec, x.id);
    return sec;
  }

  const pintaEncargo = (sec, texto) => {
    const p = sec.querySelector(".rv-encargo");
    if (p) p.textContent = plano(texto) || "Sin descripción todavía.";
  };

  // El DOM al día con las láminas por escribir: se crean las que faltan, se
  // actualiza su texto, y se van las que ya no están.
  function sincronizarNuevas() {
    const quiero = new Map(leerNuevas().map((x) => [x.id, x]));
    [...PISTA.querySelectorAll(":scope > section[data-pendiente]")].forEach((sec) => {
      const id = idDe(sec);
      // las que ya están en el HTML no son pendientes de este navegador
      if (!quiero.has(id) && !ORDEN_DECK.includes(id)) sec.remove();
    });
    quiero.forEach((x, id) => {
      if (ORDEN_DECK.includes(id)) return;          // ya aplicada al HTML
      let sec = [...PISTA.querySelectorAll(":scope > section")].find((y) => idDe(y) === id);
      if (!sec) { sec = crearPendiente(x); PISTA.appendChild(sec); }
      pintaEncargo(sec, x.texto);
    });
  }

  // Las marcadas para borrar salen del DOM y se guardan; las que dejan de estarlo
  // vuelven. Colocarlas en su sitio es cosa del reordenado, que va justo después.
  function sincronizarBorradas() {
    [...PISTA.querySelectorAll(":scope > section")].forEach((sec) => {
      const id = idDe(sec);
      if (esBorrada(id)) { GUARDADAS.set(id, sec); sec.remove(); }
    });
    [...GUARDADAS.keys()].forEach((id) => {
      if (esBorrada(id)) return;
      PISTA.appendChild(GUARDADAS.get(id));
      GUARDADAS.delete(id);
    });
  }

  // Lleva el DOM a lo que hay pendiente: las láminas por escribir puestas, las
  // borradas fuera, y todo en su orden. Devuelve si hubo algo que cambiar.
  // Reveal.sync() rehace los fondos y la navegación; después se vuelve a la misma
  // lámina, que ahora está en otra posición.
  function aplicarOrden() {
    if (deckViejo) return false;   // el HTML cambió por debajo: manda recargar
    sincronizarNuevas();
    sincronizarBorradas();
    const quiero = ordenVigente();
    releer();
    if (mismos(IDS, quiero)) { pintarPendientes(); return false; }
    let actual = null;
    try { actual = Reveal.getCurrentSlide(); } catch (e) { actual = null; }
    const antes = actual ? IDS.indexOf(idDe(actual)) : -1;
    const por = new Map(SECS.map((x) => [idDe(x), x]));
    quiero.forEach((id) => { const x = por.get(id); if (x) PISTA.appendChild(x); });
    releer();
    pintarPendientes();
    try { Reveal.sync(); } catch (e) {}
    // Si la lámina en la que estaba se acaba de borrar, se cae a la que ocupa
    // ahora su sitio, en vez de saltar al principio del deck.
    let i = actual ? SECS.indexOf(actual) : -1;
    if (i < 0 && antes >= 0) i = Math.min(antes, SECS.length - 1);
    if (i >= 0) { navPropia = true; try { Reveal.slide(i); } finally { navPropia = false; } }
    return true;
  }

  // La marca de "por escribir" sobre la propia lámina, que se ve también en la
  // vista general y en la miniatura de la rejilla.
  function pintarPendientes() {
    SECS.forEach((sec) => {
      const hay = sec.dataset.pendiente === "1";
      sec.classList.toggle("rv-pendiente", hay);
      // Las partes de una fusión se quedan en el deck, marcadas, hasta que la
      // lámina combinada esté escrita.
      // La marca se pinta tanto si la fusión está pendiente como si el deck ya
      // la dice: en los dos casos esa lámina todavía no está combinada.
      const f = laFusion(idDe(sec));
      const enDeckYa = !!(sec.dataset.combinar || sec.dataset.combinarEn);
      const cuenta = f && partesVivas(f).length > 1;
      sec.classList.toggle("rv-fusion", !!cuenta || enDeckYa);
      if (cuenta) sec.dataset.fusion = (f.partes.indexOf(idDe(sec)) + 1) + " de " + f.partes.length;
      else if (enDeckYa) sec.dataset.fusion = "ya marcada en el deck";
      else delete sec.dataset.fusion;
    });
  }

  // El orden pendiente se suelta cuando el HTML ya lo dice, igual que las
  // reescrituras del guion. forzado es la lista explícita de resueltas.js.
  function purgarOrden(forzado) {
    if (!leerOrden().length && !leerNuevas().length && !leerBorradas().length &&
        !leerFusiones().length) return 0;
    if (!forzado && ordenPendiente()) return 0;
    guardarDeck({ orden: [], nuevas: [], borradas: [], fusiones: [] });
    return 1;
  }

  /* Resoluciones ya aplicadas al deck. Cuando las correcciones están hechas en
     el HTML, junto al deck queda un resueltas.js con esta forma:

       window.RV_RESUELTAS = {
         sello: "2026-09-02T18:40",              // identifica esta tanda
         notas: [{ id: "evaluacion", texto: "subir tareas a 60" }],
         guiones: ["la-pregunta-de-fondo"],      // reescrituras aplicadas
         cortos: ["alphazero"],                  // guiones cortos aplicados
         recortes: ["alphazero"],                // niveles de recorte aplicados
         orden: true                             // el orden de las láminas, ya aplicado
       };

     Se carga como <script> y no con fetch porque los decks se abren con doble
     clic, y Chrome no deja que una página file:// lea otro archivo con fetch,
     pero sí cargar un script suyo.

     Las notas se reconocen por su lámina y su texto, comparados con los espacios
     colapsados, o por su nid si el archivo lo trae. El sello es lo que impide
     que el mismo archivo siga borrando en cargas posteriores: una nota nueva que
     repita el texto sobre la misma lámina no es la que ya se corrigió. */
  const LLAVE_R = "resueltas:" + DECK;
  const firma = (id, texto) => id + " " + plano(texto);

  // Una reescritura del guion deja de estar pendiente en cuanto el deck ya la
  // dice. Lo segundo, la lista explícita, hace falta porque al aplicarla pude
  // retocarla, y entonces los textos ya no coinciden palabra por palabra.
  function purgarGuiones(forzados) {
    const g = leerGuiones();
    let n = 0;
    Object.keys(g).forEach((id) => {
      const i = IDS.indexOf(id);
      const aplicado = i >= 0 && plano(g[id].texto) === plano(guionDelDeck(i));
      if (aplicado || forzados.includes(id)) { delete g[id]; n++; }
    });
    if (n) guardarGuiones(g);
    return n;
  }

  function purgarCortos(forzados) {
    const c = leerCortos();
    let n = 0;
    Object.keys(c).forEach((id) => {
      const i = IDS.indexOf(id);
      const aplicado = i >= 0 && plano(c[id].texto) === plano(cortoDelDeck(i));
      if (aplicado || forzados.includes(id)) { delete c[id]; n++; }
    });
    if (n) guardarCortos(c);
    return n;
  }

  function purgarRecortes(forzados) {
    const x = leerRecortes();
    let n = 0;
    Object.keys(x).forEach((id) => {
      const i = IDS.indexOf(id);
      const aplicado = i >= 0 && nivelValido(x[id].nivel | 0) === nivelDelDeck(i);
      if (aplicado || forzados.includes(id)) { delete x[id]; n++; }
    });
    if (n) guardarRecortes(x);
    return n;
  }

  function borrarNotas(lista) {
    const fuera = new Set(lista.filter((x) => x && x.id).map((x) => firma(x.id, x.texto || "")));
    const nids = new Set(lista.map((x) => x && x.nid).filter(Boolean));
    const d = leer();
    let n = 0;
    Object.keys(d).forEach((id) => {
      const quedan = d[id].filter((x) => !(nids.has(x.nid) || fuera.has(firma(id, x.texto))));
      n += d[id].length - quedan.length;
      if (quedan.length) d[id] = quedan; else delete d[id];
    });
    if (n) guardar(d);
    return n;
  }

  // r es lo que traiga resueltas.js, o null si no hay archivo, que es lo normal.
  // Aun sin archivo hay algo que hacer: soltar las reescrituras que el deck ya dice.
  function resolver(r) {
    const fresco = !!(r && r.sello) && localStorage.getItem(LLAVE_R) !== r.sello;
    let n = fresco ? borrarNotas(Array.isArray(r.notas) ? r.notas : []) : 0;
    n += purgarGuiones(fresco && Array.isArray(r.guiones) ? r.guiones : []);
    n += purgarCortos(fresco && Array.isArray(r.cortos) ? r.cortos : []);
    n += purgarRecortes(fresco && Array.isArray(r.recortes) ? r.recortes : []);
    n += purgarOrden(fresco && r.orden === true);
    if (fresco) { try { localStorage.setItem(LLAVE_R, r.sello); } catch {} }
    if (!n) return;
    refrescar();
    const t = totalNotas();
    aviso(n + (n === 1 ? " corrección ya aplicada, borrada. " : " correcciones ya aplicadas, borradas. ") +
          (t ? "Quedan " + t + (t === 1 ? " nota." : " notas.") : "No queda ninguna nota."));
  }

  function cargarResueltas() {
    const s = document.createElement("script");
    s.src = "resueltas.js";
    s.onload = () => { s.remove(); resolver(window.RV_RESUELTAS); };
    s.onerror = () => { s.remove(); resolver(null); };
    document.head.appendChild(s);
  }

  // El deck cambia por fuera cuando aplico las correcciones. Las notas se ponen
  // al día solas, pero las láminas no: hay que recargar para verlas. Recargar no
  // cuesta nada, porque las notas ya no viven en la página, y reveal vuelve a la
  // misma lámina por el hash. Aun así lo decide él, no vaya a ser que esté
  // escribiendo una nota justo en ese momento.
  let TS_DECK = null, avisoRecarga = null, deckViejo = false;

  function ofrecerRecarga() {
    // Desde aquí, lo que se ve ya no es lo que dice el archivo. Si lo aplicado
    // fue justamente el orden, notas.json ya no lo trae como pendiente, y
    // reordenar la pantalla con lo que este navegador cargó al abrir sería
    // devolverla al orden viejo. Se deja quieta hasta que se recargue.
    deckViejo = true;
    if (avisoRecarga) return;
    avisoRecarga = document.createElement("div");
    avisoRecarga.className = "rv-recarga";
    avisoRecarga.innerHTML = "El deck cambió en disco: las correcciones ya están aplicadas." +
      '<button type="button">Recargar</button>';
    avisoRecarga.querySelector("button").addEventListener("click", () => location.reload());
    document.body.appendChild(avisoRecarga);
  }

  /* Los avisos se apilan en una columna anclada por abajo, así que dos seguidos
     se leen los dos en vez de pisarse. Los que llevan clave sustituyen al
     anterior de su misma clave: recorrer los tres niveles con C deja un aviso,
     el vigente, y no una torre de tres. */
  let pilaAvisos = null;
  function aviso(txt, clave) {
    if (!pilaAvisos) {
      pilaAvisos = document.createElement("div");
      pilaAvisos.className = "rv-avisos";
      document.body.appendChild(pilaAvisos);
    }
    if (clave) {
      const viejo = pilaAvisos.querySelector('[data-clave="' + clave + '"]');
      if (viejo) viejo.remove();
    }
    const a = document.createElement("div");
    a.className = "rv-aviso";
    if (clave) a.dataset.clave = clave;
    a.textContent = txt;
    a.title = "clic para cerrar";
    a.addEventListener("click", () => a.remove());
    pilaAvisos.appendChild(a);
    // por encima de tres, la pila empieza a tapar la lámina: se va el más viejo
    while (pilaAvisos.children.length > 3) pilaAvisos.firstElementChild.remove();
    setTimeout(() => a.remove(), 12000);
  }

  const css = `
  .rv-barra{position:fixed;left:12px;bottom:12px;z-index:9998;background:#A42145;color:#fff;
    font:600 12px/1.4 'Noto Sans',system-ui,sans-serif;padding:5px 10px;border-radius:4px;
    letter-spacing:.02em;box-shadow:0 2px 8px rgba(0,0,0,.25)}
  .rv-barra b{font-weight:600}
  .rv-barra .rv-n{background:#fff;color:#A42145;border:0;border-radius:3px;padding:1px 6px;
    margin-left:6px;font:600 12px/1.4 'Noto Sans',system-ui,sans-serif;cursor:pointer}
  .rv-barra .rv-n:hover{background:#FFE873}
  .rv-barra .rv-g{background:#E7D395;color:#5A4A16;border-radius:3px;padding:1px 6px;margin-left:6px}
  .rv-barra .rv-x{background:#B4690E;color:#fff;border-radius:3px;padding:1px 6px;margin-left:6px}
  /* La marca de nivel vive dentro de la lámina, no en el marco, para que en la
     vista general (Escape) se vea de un golpe cómo está repartido el deck. Va
     abajo a la derecha, encima del número de lámina: arriba se encimaría con el
     logotipo institucional, que en este tema ocupa esa esquina. */
  .rv-nivel{position:absolute;bottom:34px;right:12px;z-index:12;
    font:600 11px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.05em;padding:5px 9px;border-radius:3px;cursor:pointer;
    background:#E7D395;color:#5A4A16;box-shadow:0 1px 5px rgba(0,0,0,.3);white-space:nowrap}
  .rv-nivel.rv-n2{background:#B4690E;color:#fff}
  .rv-nivel.rv-n0{background:rgba(240,238,234,.92);color:#7A7568;box-shadow:none;
    font-weight:400}
  .rv-nivel:hover{outline:2px solid #A42145}
  .rv-nivel .rv-pt{display:inline-block;width:6px;height:6px;border-radius:50%;
    background:#A42145;margin-left:6px;vertical-align:middle}
  /* En la vista general de reveal la lámina va reducida a la quinta parte, así
     que la chapa hay que agrandarla para que siga leyéndose. Es ahí donde se ve
     de un golpe cómo quedó clasificado el deck entero. */
  .reveal.overview .rv-nivel{font-size:52px;padding:18px 26px;border-radius:12px;
    bottom:40px;right:40px;letter-spacing:.02em}
  .reveal.overview .rv-nivel .rv-pt{width:26px;height:26px;margin-left:22px}
  .rv-barra .rv-off{background:#FFD400;color:#5A2A00;border-radius:3px;padding:1px 6px;margin-left:8px;
    text-transform:uppercase;letter-spacing:.04em;cursor:help}
  .rv-recarga{position:fixed;left:12px;top:12px;z-index:9998;background:#A42145;color:#fff;
    font:600 12px/1.4 'Noto Sans',system-ui,sans-serif;padding:7px 12px;border-radius:4px;
    letter-spacing:.02em;box-shadow:0 2px 8px rgba(0,0,0,.25);max-width:52vw}
  .rv-recarga button{margin-left:10px;font:600 11px/1 'Noto Sans',system-ui,sans-serif;
    color:#A42145;background:#fff;border:0;border-radius:3px;padding:4px 10px;cursor:pointer}
  .rv-recarga button:hover{background:#FFE873}
  /* La columna va anclada por abajo y crece hacia arriba, encima de la barra.
     El contenedor no intercepta clics; cada aviso sí, para poder cerrarlo. */
  .rv-avisos{position:fixed;left:12px;bottom:46px;z-index:9998;display:flex;
    flex-direction:column;align-items:flex-start;gap:6px;max-width:52vw;
    pointer-events:none}
  .rv-aviso{background:#155B4E;color:#fff;pointer-events:auto;
    font:600 12px/1.4 'Noto Sans',system-ui,sans-serif;padding:6px 11px;border-radius:4px;
    letter-spacing:.02em;box-shadow:0 2px 8px rgba(0,0,0,.25);cursor:pointer}
  .rv-barra button{margin-left:10px;font:600 11px/1 'Noto Sans',system-ui,sans-serif;color:#fff;
    background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.5);border-radius:3px;
    padding:3px 8px;cursor:pointer}
  .rv-barra button:hover{background:rgba(255,255,255,.32)}
  .rv-caja .rv-acciones{margin-top:14px;display:flex;gap:10px;justify-content:flex-end}
  .rv-caja .rv-acciones button{font:600 13px/1 'Noto Sans',system-ui,sans-serif;padding:8px 14px;
    border-radius:4px;cursor:pointer;border:1px solid #CCC;background:#F2F2F2;color:#333}
  .rv-caja .rv-acciones button.rv-peligro{background:#A42145;border-color:#A42145;color:#fff}
  .rv-caja .rv-acciones button.rv-primario{background:#A42145;border-color:#A42145;color:#fff}
  .rv-caja .rv-acciones .rv-izq{margin-right:auto;color:#A42145;background:#fff;border-color:#D9B6C1}
  .rv-capa{position:fixed;inset:0;z-index:9999;background:rgba(20,20,20,.55);
    display:flex;align-items:center;justify-content:center}
  .rv-caja{background:#fff;width:min(720px,90vw);border-radius:6px;padding:18px 20px;
    font:14px/1.5 'Noto Sans',system-ui,sans-serif;color:#333;box-shadow:0 8px 40px rgba(0,0,0,.4)}
  .rv-caja h3{margin:0 0 4px;font-size:15px;color:#A42145}
  .rv-caja .rv-id{font:12px ui-monospace,monospace;color:#666;margin-bottom:10px}
  .rv-caja .rv-cita{border-left:3px solid #E7D395;padding:6px 10px;margin:0 0 10px;
    background:#FAF7EF;font-style:italic;color:#555;max-height:120px;overflow:auto}
  .rv-caja textarea{width:100%;height:120px;box-sizing:border-box;
    font:14px/1.5 'Noto Sans',system-ui,sans-serif;
    padding:8px;border:1px solid #CCC;border-radius:4px;resize:vertical}
  .rv-caja .rv-pie{margin-top:10px;font-size:12px;color:#777;display:flex;justify-content:space-between}
  .rv-caja .rv-lista{max-height:56vh;overflow:auto;margin:0 -4px;padding:0 4px}
  .rv-caja .rv-item{border:1px solid #E4E0D8;border-radius:4px;padding:10px 12px;margin-bottom:10px;
    cursor:pointer}
  .rv-caja .rv-item:hover{background:#FAF7EF;border-color:#E7D395}
  .rv-caja .rv-item.rv-fuera{cursor:default}
  .rv-caja .rv-item.rv-fuera:hover{background:#fff;border-color:#E4E0D8}
  .rv-caja .rv-grupo{font:600 11px/1.4 ui-monospace,monospace;color:#A42145;
    letter-spacing:.03em;margin:16px 0 6px;padding-bottom:3px;border-bottom:1px solid #EDE9E1}
  .rv-caja .rv-grupo:first-child{margin-top:0}
  .rv-caja .rv-tabs{display:flex;gap:8px;margin:0 0 12px}
  .rv-caja .rv-tabs button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:6px 10px;
    border:1px solid #CCC;background:#F2F2F2;color:#555;border-radius:3px;cursor:pointer}
  .rv-caja .rv-tabs button.rv-on{background:#A42145;border-color:#A42145;color:#fff}
  .rv-caja .rv-item .rv-eti{font:600 11px/1.4 'Noto Sans',system-ui,sans-serif;color:#8A8A8A;
    text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}
  .rv-caja .rv-item .rv-cita{margin-bottom:8px}
  .rv-caja .rv-item .rv-txt{white-space:pre-wrap;color:#2E2E2E}
  .rv-caja .rv-item .rv-acc{margin-top:8px;display:flex;gap:8px;justify-content:flex-end}
  .rv-caja .rv-item .rv-acc button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:5px 10px;
    border:1px solid #CCC;background:#F2F2F2;color:#333;border-radius:3px;cursor:pointer}
  .rv-caja .rv-item .rv-acc button[data-rv="eliminar"]{color:#A42145;background:#fff;border-color:#D9B6C1}
  .rv-mini{flex:none;position:relative;width:400px;height:225px;overflow:hidden;
    border:1px solid #DDD8CE;border-radius:3px;background:#fff;cursor:pointer;
    box-shadow:0 1px 4px rgba(0,0,0,.08)}
  .rv-mini:hover{border-color:#A42145;box-shadow:0 2px 10px rgba(164,33,69,.25)}
  .rv-mini > .reveal{position:absolute;left:0;top:0;width:1280px;height:720px;
    transform:scale(.3125);transform-origin:0 0;overflow:hidden}
  .rv-mini .slides{position:absolute!important;left:0!important;top:0!important;
    width:1280px!important;height:720px!important;transform:none!important;
    zoom:1!important;margin:0!important;padding:0!important;text-align:left}
  .rv-mini .slides > section{position:absolute!important;left:0!important;top:0!important;
    display:block!important;opacity:1!important;visibility:visible!important;
    transform:none!important;filter:none!important;pointer-events:none;z-index:auto}
  .rv-mini .fragment{opacity:1!important;visibility:visible!important}
  .rv-mini aside.notes{display:none!important}
  .rv-mini mark.rv-mini-hl{background:#FFE873;color:#1A1A1A;border-radius:2px}
  @media (max-width:1120px){ .rv-mini{order:-1} }
  .rv-caja .rv-prev{max-height:50vh;overflow:auto;white-space:pre-wrap;font:12px/1.5 ui-monospace,monospace;
    background:#F4F4F4;padding:10px;border-radius:4px}
  mark.rv-hl,.reveal mark.rv-hl{background:#FFE873;color:#1A1A1A;
    padding:0 .06em;border-radius:2px;border-bottom:2px solid #E8B800;cursor:pointer;
    box-decoration-break:clone;-webkit-box-decoration-break:clone}
  mark.rv-hl:hover,.reveal mark.rv-hl:hover{background:#FFD400}
  mark.rv-hl.rv-sel,.reveal mark.rv-hl.rv-sel{background:#FF9E2C;
    border-bottom-color:#8C4A00;box-shadow:0 0 0 3px rgba(255,158,44,.35)}
  mark.rv-hl[data-n]::after{content:attr(data-n);font:600 .6em/1 'Noto Sans',system-ui,sans-serif;
    vertical-align:super;margin-left:.15em;color:#A42145}
  /* ---------- la rejilla de láminas, tecla R ---------- */
  /* Todas las miniaturas a pantalla completa, en una malla que fluye, y cada una
     se arrastra con el ratón para cambiarla de sitio. La que se arrastra se
     queda en su sitio, atenuada, una copia sigue al cursor, y entre las dos
     láminas donde caería se dibuja una línea vertical, como en PowerPoint. */
  .rv-rejilla{position:fixed;inset:0;z-index:9997;background:#FBFAF8;overflow:auto;
    padding:60px 20px 56px;font:14px/1.5 'Noto Sans',system-ui,sans-serif;color:#2E2E2E}
  .rv-rj-barra{position:fixed;left:0;right:0;top:0;min-height:46px;z-index:2;
    display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:6px 16px;
    background:#A42145;color:#fff;font:600 13px/1.4 'Noto Sans',system-ui,sans-serif;
    box-shadow:0 2px 8px rgba(0,0,0,.25);box-sizing:border-box}
  .rv-rj-barra .rv-rj-est{font-weight:400;opacity:.92;flex:1;min-width:200px}
  .rv-rj-barra .rv-rj-pend{background:#B4690E;color:#fff;border-radius:3px;padding:2px 7px;
    margin-right:6px;text-transform:uppercase;letter-spacing:.04em;font-size:11px}
  .rv-rj-barra button{font:600 11px/1 'Noto Sans',system-ui,sans-serif;color:#fff;
    background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.5);border-radius:3px;
    padding:6px 10px;cursor:pointer}
  .rv-rj-barra button:hover{background:rgba(255,255,255,.32)}
  .rv-rj-barra button[disabled]{opacity:.4;cursor:default}
  .rv-rj-lienzo{position:relative;display:flex;flex-wrap:wrap;gap:16px;
    align-content:flex-start;align-items:flex-start;max-width:1560px;margin:0 auto}
  .rv-rj-cel{box-sizing:border-box;width:236px;padding:4px;border:2px solid transparent;
    border-radius:5px;cursor:grab;user-select:none;-webkit-user-select:none;background:#fff}
  .rv-rj-cel:hover{border-color:#E7D395}
  .rv-rj-cel.rv-rj-movida{border-color:#B4690E;background:#FFF6EA}
  .rv-rj-cel.rv-rj-nueva{border-color:#155B4E;background:#EEF6F3;border-style:dashed}
  .rv-rj-cel.rv-rj-borrada{border-color:#A42145;background:#F6EEF1}
  .rv-rj-cel.rv-rj-fusionada{border-color:#3C6E9F;background:#EEF3F8}
  /* La selección de Ctrl+clic, que es lo que se va a combinar. */
  .rv-rj-cel.rv-rj-sel{border-color:#3C6E9F;background:#E2ECF5;
    box-shadow:0 0 0 2px rgba(60,110,159,.35)}
  /* Ojo con el orden: display:block le gana a [hidden] del navegador, así que la
     chapa necesita su propia regla para poder esconderse. */
  .rv-rj-fus[hidden]{display:none}
  /* Lo que cambió desde la última foto. En la rejilla, un filo verde. */
  .rv-rj-cel.rv-rj-cam{box-shadow:inset 0 0 0 3px #1D7A5F}

  /* --- marcas de cambio sobre la lámina -------------------------------
     La pieza tocada se marca con un filo verde y una esquina doblada, y el
     texto de antes sale en un globo al pasar el ratón. Alberto lo eligió así
     el 12 de octubre de 2026 frente a tachar dentro de la viñeta: la lámina
     tiene que seguir viéndose como se va a proyectar, y un tachado la
     desbordaría. Por eso aquí no se toca el flujo: ni borde, ni padding, ni
     nada que mueva el texto de sitio. */
  .reveal section [data-pieza].rv-cam{
    outline:3px solid #1D7A5F; outline-offset:4px; border-radius:3px;
    cursor:help}
  .rv-cam-pop{position:fixed;z-index:10000;max-width:430px;
    background:#0E3D31;color:#EAF5F1;border-radius:6px;padding:9px 12px;
    font:400 14px/1.45 Verdana,Geneva,sans-serif;
    box-shadow:0 6px 22px rgba(0,0,0,.3);pointer-events:none}
  .rv-cam-pop b{display:block;font-size:11px;letter-spacing:.06em;
    text-transform:uppercase;opacity:.7;margin-bottom:4px}
  .rv-cam-pop p{margin:0;white-space:pre-wrap}

  /* La chapa de la barra, en verde para no confundirla con lo que está
     pendiente de aplicar, que va en ámbar. */
  .rv-barra .rv-cam-b{background:#1D7A5F;color:#fff;border:0;border-radius:3px;
    padding:1px 7px;margin-left:6px;cursor:pointer;font:inherit}
  .rv-barra .rv-cam-b:hover{background:#25946F}
  /* Escondidas, la chapa se queda pero apagada: si desapareciera del todo no
     habría forma de saber que hay algo esperando a que lo mires. */
  .rv-barra .rv-cam-b.rv-cam-off{background:transparent;color:#fff;
    border:1px solid rgba(255,255,255,.55);opacity:.85}
  .rv-barra .rv-cam-b.rv-cam-off:hover{background:rgba(255,255,255,.14)}

  /* La lista de la tecla X. */
  .rv-cam-lista{max-height:52vh;overflow:auto;margin:6px 0 10px}
  .rv-cam-fila{border-top:1px solid #E4E0D8;padding:8px 2px;cursor:pointer}
  .rv-cam-fila:hover{background:#FAF7F2}
  .rv-cam-ida{cursor:default;opacity:.72}
  .rv-cam-ida:hover{background:none}
  .rv-cam-fila b{display:block;margin-bottom:3px}
  .rv-cam-et{display:inline-block;background:#E7D395;color:#5A4A16;border-radius:3px;
    padding:0 6px;margin:0 0 4px;font-style:normal;font-size:12px}
  .rv-cam-fila p{margin:2px 0;font-size:13px;line-height:1.45}
  .rv-cam-fila p>i{display:inline-block;min-width:52px;color:#8A8A8A;
    font-style:normal;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
  .rv-cam-ig{opacity:.5}
  ins.rv-mas{background:#D9F2E6;color:#0E3D31;text-decoration:none;
    border-radius:2px;padding:0 1px}
  del.rv-menos{background:#F6DADF;color:#7A1228;border-radius:2px;padding:0 1px}
  .rv-rj-fus{display:block;flex:0 0 100%;margin-top:2px;padding:3px 6px;border:0;
    border-radius:3px;background:#3C6E9F;color:#fff;cursor:pointer;
    font:600 10px/1.3 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.04em;text-align:left}
  .rv-rj-fus:hover{background:#2E5880}
  .rv-rj-barra .rv-rj-comb{background:#3C6E9F;border-color:#3C6E9F}
  .rv-rj-barra .rv-rj-comb:hover{background:#4E82B6}
  /* La lámina que espera a que la combinen, sobre el propio deck. */
  .reveal .slides > section.rv-fusion{outline:3px dashed #3C6E9F;outline-offset:-14px}
  .reveal .slides > section.rv-fusion::after{content:"por combinar, " attr(data-fusion);
    position:absolute;left:12px;bottom:34px;z-index:12;background:#3C6E9F;color:#fff;
    font:600 11px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.05em;padding:5px 9px;border-radius:3px}
  .rv-rj-cel.rv-rj-borrada .rv-mini{opacity:.35;filter:grayscale(1)}
  .rv-rj-cel.rv-rj-borrada .rv-rj-pie{text-decoration:line-through}
  .rv-rj-cel.rv-rj-nueva .rv-rj-mov{background:#CDE5DD;color:#0E4034}
  .rv-rj-cel.rv-rj-borrada .rv-rj-mov{background:#A42145;color:#fff}
  /* Los dos botones de cada lámina: añadir una detrás, y borrarla. Discretos
     hasta que el ratón entra en la celda, para que la malla se lea como una
     malla de miniaturas y no como un panel de mandos. */
  .rv-rj-bts{margin-left:auto;display:flex;gap:4px;opacity:0;transition:opacity .12s}
  .rv-rj-cel:hover .rv-rj-bts,.rv-rj-cel.rv-rj-borrada .rv-rj-bts{opacity:1}
  .rv-rj-bt{font:600 13px/1 'Noto Sans',system-ui,sans-serif;width:22px;height:22px;
    padding:0;border:1px solid #DDD8CE;background:#fff;color:#7A7568;border-radius:3px;
    cursor:pointer}
  .rv-rj-bt:hover{border-color:#155B4E;color:#155B4E}
  .rv-rj-bt-x:hover{border-color:#A42145;color:#A42145}
  .rv-rj-mas{box-sizing:border-box;width:236px;min-height:180px;border:2px dashed #C9C3B6;
    border-radius:5px;background:#fff;color:#7A7568;cursor:pointer;display:flex;
    flex-direction:column;align-items:center;justify-content:center;gap:8px;
    font:600 12px/1.3 'Noto Sans',system-ui,sans-serif;padding:8px}
  .rv-rj-mas span{font-size:30px;line-height:1;color:#155B4E}
  .rv-rj-mas:hover{border-color:#155B4E;color:#155B4E;background:#F4FAF8}
  /* La lámina por escribir, sobre el propio deck: se ve que está ahí y que no
     está escrita, sin imitar una lámina de verdad. */
  .reveal .slides > section.rv-pendiente{outline:3px dashed #155B4E;outline-offset:-14px}
  .reveal .slides > section.rv-pendiente .rv-encargo{white-space:pre-wrap}
  .reveal .slides > section.rv-pendiente h2::after{content:" (pendiente)";
    font-size:.5em;letter-spacing:.06em;text-transform:uppercase;color:#155B4E;
    vertical-align:middle}
  .rv-rj-cel.rv-rj-actual{border-color:#A42145}
  /* La que se está arrastrando se queda en su sitio, atenuada: lo que enseña
     dónde va a caer es la línea, como en PowerPoint. */
  .rv-rj-cel.rv-rj-tirando{opacity:.4}
  .rv-rj-linea{position:absolute;width:4px;border-radius:2px;background:#A42145;
    box-shadow:0 0 0 1px rgba(255,255,255,.85);pointer-events:none;z-index:5}
  /* Los remates de arriba y de abajo, que es lo que la hace leerse como una
     marca de inserción y no como el borde de una lámina. */
  .rv-rj-linea::before,.rv-rj-linea::after{content:"";position:absolute;left:-4px;
    width:12px;height:4px;border-radius:2px;background:#A42145}
  .rv-rj-linea::before{top:-4px}
  .rv-rj-linea::after{bottom:-4px}
  .rv-rj-cel .rv-mini{width:224px;height:126px;cursor:inherit}
  .rv-rj-cel .rv-mini > .reveal{transform:scale(.175)}
  .rv-rj-cel .rv-mini:hover{border-color:#DDD8CE;box-shadow:0 1px 4px rgba(0,0,0,.08)}
  .rv-rj-cab{display:flex;align-items:center;gap:6px;margin-bottom:4px;flex-wrap:wrap}
  .rv-rj-num{font:600 12px/1 ui-monospace,monospace;color:#fff;background:#A42145;
    border-radius:3px;padding:4px 7px;min-width:12px;text-align:center}
  .rv-rj-mov{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
    letter-spacing:.04em;color:#8C4A00;background:#FFE0B8;border-radius:3px;padding:4px 6px}
  .rv-rj-notas{font:600 10px/1 'Noto Sans',system-ui,sans-serif;color:#5A4A16;
    background:#E7D395;border-radius:3px;padding:4px 6px;margin-left:auto}
  .rv-rj-pie{font:11px/1.3 ui-monospace,monospace;color:#7A7568;margin-top:4px;
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .rv-rj-fantasma{position:fixed;z-index:10000;pointer-events:none;opacity:.92;
    box-shadow:0 10px 30px rgba(0,0,0,.35);border-color:#A42145!important;
    background:#fff;cursor:grabbing}
  .rv-rejilla .rv-ayuda{position:fixed;right:16px;bottom:16px;background:#A42145;color:#fff;
    font:600 12px/1.4 'Noto Sans',system-ui,sans-serif;padding:6px 11px;border-radius:4px;z-index:3}
  .rv-barra .rv-orden{background:#B4690E;color:#fff;border:0;border-radius:3px;padding:2px 7px;
    margin-left:6px;font:600 12px/1.4 'Noto Sans',system-ui,sans-serif;cursor:pointer}
  .rv-barra .rv-orden:hover{background:#D07C12}`;
  document.head.insertAdjacentHTML("beforeend", "<style>" + css + "</style>");

  const barra = document.createElement("div");
  barra.className = "rv-barra";
  document.body.appendChild(barra);

  const idActual = () => {
    let sec = null;
    try { sec = Reveal.getCurrentSlide(); } catch (e) { sec = null; }
    return idDe(sec || SECS[0]);
  };
  const totalNotas = () => Object.values(leer()).reduce((a, x) => a + x.length, 0);
  const pintarBarra = () => {
    const n = (leer()[idActual()] || []).length, t = totalNotas();
    const m = Object.keys(leerGuiones()).length;
    const c = Object.keys(leerCortos()).length;
    const x = Object.keys(leerRecortes()).length;
    const o = ordenPendiente() ? cuantasMovidas() : 0;
    const nn = nuevasVivas().length, nb = borradasVivas().length;
    const nf = fusionesVivas().length;
    barra.innerHTML = "REVISIÓN <b>" + idActual() + "</b>" +
      (n ? '<button type="button" class="rv-n" data-rv="lista" title="Ver y editar las notas de esta diapositiva">' + n + "</button>" : "") +
      (m ? '<span class="rv-g" title="guiones reescritos, pendientes de exportar">' + m +
           " guion" + (m === 1 ? "" : "es") + "</span>" : "") +
      (c ? '<span class="rv-g" title="guiones cortos escritos o reescritos, pendientes de aplicar al deck">' +
           c + " corto" + (c === 1 ? "" : "s") + "</span>" : "") +
      (x ? '<span class="rv-x" title="niveles de recorte cambiados, pendientes de aplicar al deck">' +
           x + " recorte" + (x === 1 ? "" : "s") + "</span>" : "") +
      (o || nn || nb || nf ? '<button type="button" class="rv-x rv-orden" data-rv="rejilla" ' +
           'title="El deck se está viendo con cambios que el HTML todavía no dice. ' +
           'Se aplican al archivo con tools/reordenar.py. Clic o tecla R para ver la rejilla.">' +
           "sin aplicar: " +
           [o ? o + " movida" + (o === 1 ? "" : "s") : "",
            nn ? nn + " por escribir" : "",
            nb ? nb + " por borrar" : "",
            nf ? nf + " por combinar" : ""].filter(Boolean).join(", ") + "</button>" : "") +
      (hayCambios() ? '<button type="button" class="rv-cam-b' +
           (camOcultos() ? " rv-cam-off" : "") + '" data-rv="cambios" ' +
           'title="Lo que cambió en el deck desde la última vez que lo diste por visto. ' +
           'Clic o tecla X para verlo, tecla Z para esconder las marcas.">' +
           camVivas().length + " lámina" + (camVivas().length === 1 ? "" : "s") +
           " con cambios" +
           (camBorradas().length ? " y " + camBorradas().length + " borrada" +
             (camBorradas().length === 1 ? "" : "s") : "") +
           (camOcultos() ? ", escondidos" : "") + "</button>" : "") +
      (SERVIDOR ? "" : '<span class="rv-off" title="Este deck no lo está sirviendo tools/servir.py, ' +
        'así que las notas se guardan solo en este navegador y nadie más las ve. ' +
        'Ciérralo y ábrelo por la liga que da servir.py.">sin servidor</span>') +
      '<span style="opacity:.7;margin-left:12px">A anotar, C recorte, L notas, G guion, ' +
      "R orden, E exportar" +
      (hayCambios() ? ", X cambios, Z " + (camOcultos() ? "mostrar" : "esconder") : "") +
      "</span>" +
      (t ? '<button type="button" data-rv="purgar">Borrar todas (' + t + ")</button>" : "");
  };
  barra.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-rv]");
    if (!b) return;
    e.stopPropagation();
    if (b.dataset.rv === "purgar") purgar();
    if (b.dataset.rv === "lista") abrirLista("lamina");
    if (b.dataset.rv === "rejilla") abrirRejilla();
    if (b.dataset.rv === "cambios") abrirCambios();
  });

  /* ---------- nivel de recorte, sobre la lámina ---------- */

  // La marca se inyecta dentro de cada <section>, así se ve tanto en la lámina
  // como en la vista general y en la miniatura del guion. La llevan todas, para
  // poder recorrer el deck viendo en qué quedó clasificada cada lámina; las de
  // núcleo en gris, que es el color de lo que no se toca.
  function pintarNiveles() {
    SECS.forEach((sec, i) => {
      const n = nivelDe(i), enDeck = nivelDelDeck(i);
      let b = sec.querySelector(":scope > .rv-nivel");
      if (!b) {
        b = document.createElement("div");
        b.className = "rv-nivel";
        b.addEventListener("click", (e) => { e.stopPropagation(); ciclarNivel(i); });
        sec.appendChild(b);
      }
      // La chapa dice también si la lámina ya tiene su guion corto escrito, sea
      // de núcleo o no: el núcleo no se pierde, pero se puede contar corto, y
      // así la vuelta al deck es la lista de lo que falta por escribir. Callan
      // solo la portada, el cierre y los separadores, que no lo necesitan.
      const exenta = !n && SIN_CORTO.test(sec.className);
      b.className = "rv-nivel rv-n" + n;
      b.innerHTML = NOMBRE_NIVEL[n] +
                    (hayCorto(i) ? ", corto" : exenta ? "" : ", sin corto") +
                    (n === enDeck ? "" : '<span class="rv-pt"></span>');
      b.title = QUE_ES_NIVEL[n] +
        (hayCorto(i) ? "  Tiene guion corto escrito."
                     : exenta ? "  No necesita guion corto."
                              : "  Todavía sin guion corto: se escribe con G.") +
        (n === enDeck ? "" : "  Cambio pendiente de aplicar al deck, el HTML todavía dice " +
                             NOMBRE_NIVEL[enDeck] + ".") +
        "  Clic o tecla C para cambiar el nivel.";
    });
  }

  // C recorre los tres estados de la lámina en curso. El aviso dice qué acaba de
  // significar, que es lo que cuesta recordar entre una sesión y la siguiente.
  function ciclarNivel(cual) {
    const i = typeof cual === "number" ? cual : IDS.indexOf(idActual());
    if (i < 0) return;
    const n = (nivelDe(i) + 1) % 3;
    ponerNivel(i, n);
    pintarNiveles();
    pintarBarra();
    aviso(IDS[i] + ". " + QUE_ES_NIVEL[n] +
      (n && !hayCorto(i)
        ? " Todavía no tiene guion corto, así que en clase solo se podrá saltar entera. Se escribe con G."
        : ""), "nivel");
  }

  /* La caja flotante de las notas. `doc` dice en qué documento se monta: por
     omisión el del deck, y el de la ventana del guion cuando se anota desde
     ahí, que es donde está el cursor. El Escape se escucha en ese mismo
     documento, o cerrar la caja desde la otra ventana no funcionaría. */
  function capa(html, alMontar, doc) {
    const d = doc || document;
    const c = d.createElement("div");
    c.className = "rv-capa";
    c.innerHTML = '<div class="rv-caja">' + html + "</div>";
    d.body.appendChild(c);
    const cerrar = () => { c.remove(); d.removeEventListener("keydown", esc2, true); pintarBarra(); };
    const esc2 = (e) => { if (e.key === "Escape") { e.stopPropagation(); cerrar(); } };
    d.addEventListener("keydown", esc2, true);
    c.addEventListener("click", (e) => { if (e.target === c) cerrar(); });
    alMontar(c, cerrar);
    return c;
  }

  /* ---------- resaltado en amarillo de las citas ---------- */

  // Ni el guion oculto de las láminas ni los adornos de la vista de guion
  // son texto citable: buscar ahí produciría resaltados fantasma.
  const FUERA = "aside.notes, aside.corto, aside.apuntes, aside.ficha, .rv-cab, .rv-tit, .rv-mini, .rv-marca, " +
                ".rv-acc-g, .rv-nivel, .rv-niv, .rv-corto-cab, script, style";
  const ubicadas = new Set();   // nid de las notas cuya cita se pudo localizar

  function limpiarResaltado(raiz) {
    [...raiz.querySelectorAll("mark.rv-hl")].forEach((m) => {
      const p = m.parentNode;
      while (m.firstChild) p.insertBefore(m.firstChild, m);
      m.remove();
      p.normalize();
    });
  }

  // El recorrido se pide al documento de la raíz, que no siempre es esta
  // página: el guion se resalta dentro de la ventana de la tecla G.
  function nodosDe(raiz) {
    const out = [];
    const w = (raiz.ownerDocument || document).createTreeWalker(raiz, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        if (!n.nodeValue) return NodeFilter.FILTER_REJECT;
        for (let p = n.parentElement; p; p = p.parentElement) {
          if (p.classList && p.classList.contains("rv-hl")) return NodeFilter.FILTER_REJECT;
          if (p.matches && p.matches(FUERA)) return NodeFilter.FILTER_REJECT;
          if (p === raiz) break;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    while (w.nextNode()) out.push(w.currentNode);
    return out;
  }

  // Texto de la raíz con los espacios ya colapsados, y un mapa que devuelve,
  // para cada carácter, en qué nodo de texto y en qué posición vive.
  function indice(nodos) {
    let txt = "";
    const mapa = [];
    nodos.forEach((nodo) => {
      const v = nodo.nodeValue;
      for (let i = 0; i < v.length; i++) {
        if (/\s/.test(v[i])) {
          if (txt && txt[txt.length - 1] !== " ") { txt += " "; mapa.push({ nodo, off: i }); }
        } else { txt += v[i]; mapa.push({ nodo, off: i }); }
      }
    });
    return { txt, mapa };
  }

  // La aparición número `nth` de la cita, no la primera. Sin eso, citar una sola
  // palabra que se repite en la lámina resaltaría siempre la de más arriba.
  // Si el texto cambió y ya no hay tantas apariciones, se queda en la última.
  function nEsima(txt, aguja, nth) {
    if (!aguja) return -1;
    const k = Math.max(0, nth | 0);
    let i = txt.indexOf(aguja), veces = 0, ultima = -1;
    while (i >= 0) {
      if (veces === k) return i;
      ultima = i; veces++;
      i = txt.indexOf(aguja, i + 1);
    }
    return ultima;
  }

  function localizar(txt, cita, nth) {
    const c = plano(cita);
    if (!c) return null;
    let i = nEsima(txt, c, nth);
    if (i >= 0) return [i, i + c.length];
    i = nEsima(txt.toLowerCase(), c.toLowerCase(), nth);
    if (i >= 0) return [i, i + c.length];
    // Último intento, ignorando del todo los espacios, por si el HTML pega dos
    // elementos sin separación y la selección del navegador sí metió un espacio.
    const pos = [];
    let compacto = "";
    for (let k = 0; k < txt.length; k++) if (txt[k] !== " ") { compacto += txt[k]; pos.push(k); }
    const cc = c.replace(/\s+/g, "");
    const j = nEsima(compacto.toLowerCase(), cc.toLowerCase(), nth);
    if (j >= 0 && cc) return [pos[j], pos[j + cc.length - 1] + 1];
    return null;
  }

  // Cuál de las apariciones de la cita es la que se acaba de seleccionar. Se
  // calcula al anotar, sobre el texto limpio, y viaja con la nota en `nth`.
  function ordinalDe(raiz, rango, cita) {
    const c = plano(cita || "");
    if (!raiz || !rango || !c) return 0;
    const { txt, mapa } = indice(nodosDe(raiz));
    let desde = -1;
    for (let k = 0; k < mapa.length; k++) {
      if (mapa[k].nodo === rango.startContainer && mapa[k].off >= rango.startOffset) { desde = k; break; }
    }
    if (desde < 0) return 0;
    let n = 0, i = txt.indexOf(c);
    while (i >= 0 && i < desde) { n++; i = txt.indexOf(c, i + 1); }
    return n;
  }

  // Envuelve el tramo [ini, fin) en <mark>, un mark por nodo de texto tocado,
  // para no partir elementos por la mitad.
  function envolver(mapa, ini, fin, nids) {
    const nid = Array.isArray(nids) ? nids.join(" ") : nids;
    const cuantos = String(nid).split(" ").filter(Boolean).length;
    const tramos = new Map();
    for (let k = ini; k < fin; k++) {
      const p = mapa[k];
      const t = tramos.get(p.nodo);
      if (!t) tramos.set(p.nodo, { a: p.off, b: p.off + 1 });
      else { t.a = Math.min(t.a, p.off); t.b = Math.max(t.b, p.off + 1); }
    }
    [...tramos.entries()].forEach(([nodo, t]) => {
      if (!nodo.parentNode) return;
      const medio = t.a > 0 ? nodo.splitText(t.a) : nodo;
      if (t.b - t.a < medio.nodeValue.length) medio.splitText(t.b - t.a);
      const m = (nodo.ownerDocument || document).createElement("mark");
      m.className = "rv-hl";
      m.dataset.nid = nid;
      if (cuantos > 1) m.dataset.n = cuantos;
      medio.parentNode.replaceChild(m, medio);
      m.appendChild(medio);
    });
  }

  function resaltar(raiz, notas) {
    const conCita = notas.filter((x) => x.cita);
    if (!conCita.length) return;
    // El texto se indexa una sola vez, sin marcar, para que las posiciones de
    // todas las notas se calculen sobre el mismo original.
    const { txt, mapa } = indice(nodosDe(raiz));
    const tramos = new Map();
    conCita.forEach((x) => {
      const r = localizar(txt, x.cita, x.nth);
      if (!r) return;
      // Dos notas sobre el mismo tramo comparten un solo resaltado.
      const k = r[0] + ":" + r[1];
      if (tramos.has(k)) tramos.get(k).nids.push(x.nid);
      else tramos.set(k, { ini: r[0], fin: r[1], nids: [x.nid] });
    });
    // De atrás hacia delante: envolver parte los nodos de texto, y así lo que
    // queda por colocar sigue estando donde dice el mapa.
    const puestos = [];
    [...tramos.values()].sort((a, b) => b.ini - a.ini).forEach((t) => {
      if (puestos.some((p) => t.ini < p.fin && p.ini < t.fin)) return;   // se solapa: se deja sin ubicar
      envolver(mapa, t.ini, t.fin, t.nids);
      puestos.push(t);
      t.nids.forEach((n) => ubicadas.add(n));
    });
  }

  function resaltarLaminas() {
    const d = leer();
    SECS.forEach((sec, i) => {
      limpiarResaltado(sec);
      const notas = (d[IDS[i]] || []).filter(
        (x) => x.ambito !== "guion" && x.ambito !== "corto" && x.cita);
      if (notas.length) resaltar(sec, notas);
    });
  }

  function refrescar() {
    ubicadas.clear();
    if (seleccionada && !buscarNota(seleccionada)) seleccionada = null;
    resaltarLaminas();
    pintarNiveles();
    marcarCambios();
    if (docLector() && !edicionGuion) pintarLector(true);   // no pisar lo que se escribe
    if (rejilla && !tirando) {
      // Si el orden cambió por fuera, por ejemplo desde otra pestaña, no basta
      // con repintar números: la malla se quedaría en el orden viejo y el
      // siguiente arrastre lo escribiría encima del nuevo.
      const enMalla = [...rejilla.querySelectorAll(".rv-rj-cel")].map((c) => c.dataset.sid);
      if (mismos(enMalla, ordenVigente())) pintarRejillaEstado();
      else reconstruirRejilla();
    }
    pintarSeleccion();
    pintarBarra();
  }

  /* ---------- la nota seleccionada ---------- */

  let seleccionada = null;   // nid de la nota activa, una a lo sumo
  let navPropia = false;     // para que mi propia navegación no deseleccione al llegar

  function pintarSeleccion() {
    // Las dos ventanas: la del deck y la del guion, que es otro documento.
    [document, docLector()].filter(Boolean).forEach((d) => {
      d.querySelectorAll(".rv-sel").forEach((m) => m.classList.remove("rv-sel"));
    });
    if (!seleccionada) return;
    [document, docLector()].filter(Boolean).forEach((d) =>
      d.querySelectorAll('mark.rv-hl[data-nid~="' + seleccionada + '"], ' +
                               '.rv-marca[data-nid="' + seleccionada + '"]')
        .forEach((m) => m.classList.add("rv-sel")));
  }

  function deseleccionar() {
    if (!seleccionada) return;
    seleccionada = null;
    pintarSeleccion();
  }

  // Lleva a donde vive la nota y la deja marcada en naranja. Las notas sin cita,
  // o cuya cita ya no aparece, llevan igual a su sitio, aunque no haya qué pintar.
  function seleccionar(nid) {
    const r = buscarNota(nid);
    if (!r) return;
    const i = IDS.indexOf(r.id);
    if (i < 0) return;               // la diapositiva ya no existe
    const esGuion = enGuion(r.nota.ambito);
    seleccionada = nid;
    if (esGuion) {
      // La ventana del guion enseña una lámina a la vez, así que primero hay
      // que llevar el deck a la suya; la ventana se repinta sola al cambiar.
      if (IDS[Reveal.getIndices().h] !== r.id || !docLector()) {
        navPropia = true;
        try { Reveal.slide(i); } finally { navPropia = false; }
      }
      if (!docLector()) abrirLector(); else pintarLector(true);
      pintarSeleccion();
      const d = docLector();
      const destino = d && (d.querySelector("mark.rv-hl.rv-sel") ||
                            d.querySelector(".rv-marca.rv-sel"));
      // solo se desplaza si hace falta: pinchar algo que ya se ve no debe saltar
      if (destino && destino.scrollIntoView) {
        const c = destino.getBoundingClientRect();
        const alto = (lector && lector.innerHeight) || 800;
        if (c.top < 60 || c.bottom > alto - 60) destino.scrollIntoView({ block: "center" });
      }
    } else {
      if (docLector()) cerrarLector();   // antes de marcar, que cerrar deselecciona
      seleccionada = nid;
      navPropia = true;
      try { Reveal.slide(i); } finally { navPropia = false; }
      pintarSeleccion();
    }
    pintarBarra();
  }

  // Un clic sobre el resaltado abre su nota, y la deja seleccionada mientras se
  // edita. Un clic en cualquier otro punto de la lámina o del guion deshace la
  // selección. Si lo que hubo fue un arrastre para seleccionar texto, no pasa
  // nada: se está citando, no editando.
  const nidsDe = (m) => (m.dataset.nid || "").split(" ").filter(Boolean);
  const arrastre = () => {
    const sel = window.getSelection();
    return !!(sel && !sel.isCollapsed && String(sel).trim());
  };

  document.addEventListener("click", (e) => {
    if (!e.target.closest) return;
    if (e.target.closest(".rv-capa, .rv-barra")) return;
    const m = e.target.closest("mark.rv-hl, .rv-marca[data-nid]");
    if (!m) { if (!arrastre()) deseleccionar(); return; }
    if (arrastre()) return;
    e.preventDefault();
    e.stopPropagation();
    const nids = nidsDe(m);
    if (nids.length === 1) editar(nids[0]);
    else if (nids.length) abrirLista("citas", nids);
  }, true);

  // Escape suelta la selección antes de cerrar nada más.
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || !seleccionada) return;
    if (document.querySelector(".rv-capa")) return;
    e.stopPropagation();
    deseleccionar();
  }, true);

  /* ---------- alta, edición y listado de notas ---------- */

  // Tres ámbitos: lo que se ve en la lámina, el guion hablado y el guion corto.
  const DE_AMBITO = (a) =>
    a === "guion" ? "el guion" : a === "corto" ? "el guion corto" : "esta diapositiva";
  const ETI_AMBITO = (a) => (a === "guion" ? "guion" : a === "corto" ? "guion corto" : "lámina");
  const enGuion = (a) => a === "guion" || a === "corto";

  /* desdeLector dice que la tecla A se pulsó dentro de la ventana del guion, y
     es lo que decide el ámbito: ahí se anota el guion, o el guion corto si lo
     seleccionado estaba en su bloque. Desde la página del deck se anota la
     lámina, esté la ventana abierta o no. */
  function anotar(desdeLector) {
    const dl = desdeLector ? docLector() : null;
    const sel = dl ? dl.getSelection() : window.getSelection();
    const id = idActual();
    let ambito = "lamina";
    if (dl) {
      const n = sel && sel.anchorNode
        ? (sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement)
        : null;
      ambito = n && n.closest("#rvCorto") ? "corto" : "guion";
    }
    const cita = plano(String(sel || "")).slice(0, 400);
    // Qué aparición de la cita es esta. Se mide ahora, con la selección todavía
    // viva: al abrir la caja de texto el navegador se la lleva.
    const raiz = dl
      ? dl.getElementById(ambito === "corto" ? "rvCorto" : "texto")
      : SECS[IDS.indexOf(id)];
    const nth = ordinalDe(raiz, sel && sel.rangeCount ? sel.getRangeAt(0) : null, cita);
    capa(
      "<h3>Nota sobre " + DE_AMBITO(ambito) + "</h3>" +
      '<div class="rv-id">' + id + "</div>" +
      (cita ? '<div class="rv-cita">' + esc(cita) + "</div>" : "") +
      "<textarea placeholder=\"Qué hay que cambiar\"></textarea>" +
      '<div class="rv-pie"><span>Ctrl+Enter guarda, Escape cancela</span></div>',
      (c, cerrar) => {
        const ta = c.querySelector("textarea");
        ta.focus();
        ta.addEventListener("keydown", (e) => {
          e.stopPropagation();
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            const txt = ta.value.trim();
            if (txt) {
              const d = leer();
              (d[id] = d[id] || []).push({ nid: nuevoNid(), cita, nth, texto: txt, ambito,
                ts: new Date().toISOString().slice(0, 16) });
              guardar(d);
            }
            if (sel) sel.removeAllRanges();
            cerrar();
            refrescar();
          }
        });
      }, dl);
  }

  /* Una nota del guion se edita dentro de la ventana del guion, si está
     abierta: es donde se la acaba de pinchar. */
  /* El `confirm` del navegador sale en la ventana que lo llama. Si la caja de la
     nota está en la ventana del guion y se pregunta con el `confirm` del deck,
     el diálogo aparece DETRÁS, en la otra ventana, y desde la del guion parece
     que el botón no hace nada. Alberto lo señaló el 12 de octubre de 2026: "el
     botón Eliminar en la pantalla de Guión no funciona". Sí funcionaba: la
     pregunta estaba en la ventana de atrás, esperando. */
  const preguntar = (doc, texto) => {
    const w = doc && doc.defaultView ? doc.defaultView : window;
    if (w !== window && typeof w.confirm === "function") {
      try { w.focus(); } catch (e) {}
    }
    return w.confirm(texto);
  };

  function editar(nid) {
    const r = buscarNota(nid);
    if (!r) return;
    const x = r.nota;
    seleccionar(nid);   // la nota en edición queda marcada, se abra desde donde se abra
    const doc = enGuion(x.ambito) ? docLector() : null;
    capa(
      "<h3>Nota sobre " + DE_AMBITO(x.ambito) + "</h3>" +
      '<div class="rv-id">' + r.id + (x.ts ? ", " + x.ts : "") + "</div>" +
      (x.cita ? '<div class="rv-cita">' + esc(x.cita) + "</div>" : "") +
      "<textarea></textarea>" +
      '<div class="rv-acciones">' +
      '<button type="button" class="rv-izq" data-rv="eliminar">Eliminar</button>' +
      '<button type="button" data-rv="cancelar">Cancelar</button>' +
      '<button type="button" class="rv-primario" data-rv="guardar">Guardar</button>' +
      "</div>" +
      '<div class="rv-pie"><span>Ctrl+Enter guarda, Escape cancela</span>' +
      "<span>" + (x.cita && !ubicadas.has(x.nid) ? "la cita ya no aparece en el deck" : "") + "</span></div>",
      (c, cerrar) => {
        const ta = c.querySelector("textarea");
        ta.value = x.texto;                       // por valor, no por HTML
        ta.focus();
        ta.setSelectionRange(ta.value.length, ta.value.length);
        const aplicar = () => {
          const t = ta.value.trim();
          const s = buscarNota(nid);
          if (s) {
            if (t) { s.nota.texto = t; guardar(s.datos); }
            else { eliminarNota(nid); }
          }
          cerrar();
          refrescar();
        };
        ta.addEventListener("keydown", (e) => {
          e.stopPropagation();
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) aplicar();
        });
        c.addEventListener("click", (e) => {
          const b = e.target.closest("button[data-rv]");
          if (!b) return;
          if (b.dataset.rv === "guardar") aplicar();
          else if (b.dataset.rv === "eliminar") {
            if (!preguntar(doc, "¿Eliminar esta nota?")) return;
            eliminarNota(nid); cerrar(); refrescar();
          } else cerrar();
        });
      }, doc);
  }

  // modo: "lamina" las de la diapositiva actual, "deck" todas, "citas" las que
  // comparten un mismo resaltado.
  function itemsDe(modo, nids) {
    const d = leer(), out = [];
    const meter = (id) => (d[id] || []).forEach((x) => {
      if (modo !== "citas" || nids.includes(x.nid)) out.push({ id, x });
    });
    if (modo === "lamina") meter(idActual());
    else {
      IDS.forEach(meter);
      Object.keys(d).filter((k) => !IDS.includes(k)).forEach(meter);   // láminas que ya no existen
    }
    return out;
  }

  function abrirLista(modo, nids, doc) {
    let items = itemsDe(modo, nids);
    if (!items.length && modo === "lamina") { modo = "deck"; items = itemsDe(modo); }
    if (!items.length) return;
    const titulo = modo === "citas" ? "Notas sobre esta cita"
                 : modo === "lamina" ? "Notas de esta diapositiva" : "Todas las notas del deck";
    const nLamina = itemsDe("lamina").length, nDeck = itemsDe("deck").length;
    const tabs = modo === "citas" ? "" :
      '<div class="rv-tabs">' +
      '<button type="button" data-rv="modo-lamina"' + (modo === "lamina" ? ' class="rv-on"' : "") +
        ">Esta diapositiva (" + nLamina + ")</button>" +
      '<button type="button" data-rv="modo-deck"' + (modo === "deck" ? ' class="rv-on"' : "") +
        ">Todo el deck (" + nDeck + ")</button></div>";
    let grupo = null;
    capa(
      "<h3>" + titulo + "</h3>" +
      '<div class="rv-id">' + (modo === "lamina" ? idActual() : DECK) + "</div>" +
      tabs +
      '<div class="rv-lista">' + items.map(({ id, x }) => {
        const viva = IDS.includes(id);
        const cab = (modo !== "lamina" && id !== grupo)
          ? '<div class="rv-grupo">' + id + (viva ? "" : ", la diapositiva ya no existe") + "</div>" : "";
        grupo = id;
        return cab +
          '<div class="rv-item' + (viva ? "" : " rv-fuera") + '" data-nid="' + x.nid +
            '" data-sid="' + id + '">' +
          '<div class="rv-eti">' + ETI_AMBITO(x.ambito) +
            (x.cita ? (ubicadas.has(x.nid) ? ", resaltada" : ", cita sin localizar") : ", sin cita") +
          "</div>" +
          (x.cita ? '<div class="rv-cita">' + esc(x.cita) + "</div>" : "") +
          '<div class="rv-txt">' + esc(x.texto) + "</div>" +
          '<div class="rv-acc"><button type="button" data-rv="editar">Editar</button>' +
          '<button type="button" data-rv="eliminar">Eliminar</button></div>' +
          "</div>";
      }).join("") + "</div>" +
      '<div class="rv-pie"><span>Escape cierra</span>' +
      "<span>pincha una nota para ir a ella</span></div>",
      (c, cerrar) => {
        c.addEventListener("click", (e) => {
          const b = e.target.closest("button[data-rv]");
          if (b) {
            if (b.dataset.rv === "modo-lamina") { cerrar(); abrirLista("lamina"); return; }
            if (b.dataset.rv === "modo-deck") { cerrar(); abrirLista("deck"); return; }
            const nid = b.closest(".rv-item").dataset.nid;
            if (b.dataset.rv === "editar") { cerrar(); editar(nid); }
            else if (preguntar(doc, "¿Eliminar esta nota?")) {
              eliminarNota(nid); cerrar(); refrescar();
            }
            return;
          }
          const it = e.target.closest(".rv-item");
          if (!it || it.classList.contains("rv-fuera")) return;
          cerrar();
          seleccionar(it.dataset.nid);
        });
      }, doc);
  }

  /* ---------- export, guion completo y borrados ---------- */

  function md() {
    const d = leer(), orden = IDS;
    const filas = ["## Notas de revisión, " + DECK, ""];
    let n = 0;
    orden.forEach((id) => (d[id] || []).forEach((x) => {
      n++;
      filas.push("- **" + id + "**" + (enGuion(x.ambito) ? "  (" + ETI_AMBITO(x.ambito) + ")" : "") +
                 (x.cita ? '  (cita: "' + x.cita + '")' : ""));
      filas.push("  " + x.texto.replace(/\n/g, "\n  "));
    }));
    Object.keys(d).filter((id) => !orden.includes(id)).forEach((id) =>
      (d[id] || []).forEach((x) => { n++; filas.push("- **" + id + "** (diapositiva ya no existe)"); filas.push("  " + x.texto); }));
    const g = leerGuiones(), c = leerCortos(), x = leerRecortes();
    const reescritos = orden.filter((id) => g[id]);
    const cortos = orden.filter((id) => c[id]);
    const niveles = orden.filter((id) => x[id]);
    const cuerpo = n ? filas.join("\n") : "Sin notas todavía.";
    const partes = [cuerpo];
    if (reescritos.length) {
      const gf = ["", "## Guion reescrito, " + DECK, "",
                  "Aplicar tal cual al <aside class=\"notes\"> de cada lámina.", ""];
      reescritos.forEach((id) => { gf.push("### " + id, "", g[id].texto.trim(), ""); });
      partes.push(gf.join("\n"));
    }
    if (cortos.length) {
      const cf = ["", "## Guion corto, " + DECK, "",
                  "Aplicar tal cual al <aside class=\"corto\"> de cada lámina, " +
                  "creándolo si no existe.", ""];
      cortos.forEach((id) => { cf.push("### " + id, "", c[id].texto.trim(), ""); });
      partes.push(cf.join("\n"));
    }
    if (niveles.length) {
      const xf = ["", "## Nivel de recorte, " + DECK, "",
                  "Poner data-recorte en el <section> de cada lámina, " +
                  "o quitarlo donde diga núcleo.", ""];
      niveles.forEach((id) => {
        const k = nivelValido(x[id].nivel | 0);
        xf.push("- **" + id + "**: " + (k ? 'data-recorte="' + k + '", ' : "") + NOMBRE_NIVEL[k]);
      });
      xf.push("");
      partes.push(xf.join("\n"));
    }
    if (ordenPendiente()) {
      const v = ordenVigente();
      // Movida es lo que dice lasMovidas, no lo que no coincide de posición: si
      // no, una lámina subida al principio marcaría como movidas a todas las que
      // se corrieron detrás, y el export diría una cosa y la rejilla otra.
      const mov = lasMovidas(v);
      const df = ["", "## Orden de las láminas, " + DECK, "",
                  "El deck se reordenó en la rejilla y el HTML todavía no lo dice. " +
                  "Se aplica con tools/reordenar.py, o moviendo a mano cada <section> " +
                  "al sitio que dice esta lista.", ""];
      v.forEach((id, i) => {
        const antes = ORDEN_DECK.indexOf(id);
        df.push((i + 1) + ". **" + id + "**" +
                (mov.has(id) ? "  (estaba en la " + (antes + 1) + ")" : ""));
      });
      df.push("");
      partes.push(df.join("\n"));
    }
    return { texto: partes.join("\n"), n, m: reescritos.length,
             c: cortos.length, x: niveles.length, o: ordenPendiente() ? cuantasMovidas() : 0 };
  }

  function exportar() {
    const { texto, n, m, c, x, o } = md();
    const mas = [];
    if (m) mas.push(m + " guion" + (m === 1 ? "" : "es") + " reescrito" + (m === 1 ? "" : "s"));
    if (c) mas.push(c + " guion" + (c === 1 ? "" : "es") + " corto" + (c === 1 ? "" : "s"));
    if (x) mas.push(x + " nivel" + (x === 1 ? "" : "es") + " de recorte");
    if (o) mas.push("el orden de las láminas");
    capa(
      "<h3>" + n + " nota" + (n === 1 ? "" : "s") + " de revisión" +
      (mas.length ? " y " + mas.join(", ") : "") +
      "</h3>" +
      '<div class="rv-id">Se intentó copiar al portapapeles. Si no, selecciona y copia.</div>' +
      '<div class="rv-prev">' + esc(texto) + "</div>" +
      '<div class="rv-pie"><span>Escape cierra</span><span>Pégalo en el chat</span></div>',
      () => { navigator.clipboard && navigator.clipboard.writeText(texto).catch(() => {}); });
  }

  /* ---------- la vista de guion: una ventana aparte, como la de presentar ----------

     Desde el 8 de octubre de 2026 la vista de guion de la revisión es la misma
     que la de dar la clase, la de la tecla T: ventana aparte, una lámina a la
     vez, columna estrecha, párrafo en curso resaltado y el resto atenuado.
     Antes era el deck entero como manuscrito continuo dentro de la propia
     página. Alberto lo pidió así para revisar el guion tal como lo va a leer.

     Lo que la de presentar no hace y esta sí:

       * anotar. Se selecciona texto y se pulsa A, igual que sobre la lámina. La
         nota queda con ámbito guion, o corto si lo seleccionado estaba en el
         guion corto, y la caja para escribirla se abre dentro de esta misma
         ventana, que es donde está el cursor.
       * enseñar los resaltados de las notas ya puestas, y abrirlas al pincharlas.
       * la barra de abajo: reescribir el guion, escribir el guion corto y
         cambiar el nivel de recorte de la lámina. Era lo único que vivía en la
         vista vieja y que no tenía otro sitio adonde ir.
       * leer la reescritura pendiente. El apuntador lee siempre el archivo, a
         propósito, para no decir en clase algo que nunca se aplicó al HTML;
         revisando es justo al revés, lo que hay que ver es lo que se escribió.

     Lo que la de presentar hace y esta no: los relojes, las alarmas, las barras
     de avance y el recorte en vivo. Revisando no hay clase que cronometrar.

     El CSS de la columna NO está copiado aquí: lo publica apuntador.js en
     window.ApuntadorTema.lecturaCSS, para que las dos vistas no se separen con
     el tiempo. Si un deck no cargara el apuntador, la ventana abre igual, sin
     estilar la columna. */

  let lector = null;          // la ventana del guion, o null si está cerrada
  let parrGuion = 0;          // párrafo en curso dentro de la lámina
  let alFinal = false;        // se entra a la lámina anterior por su último párrafo
  let edicionGuion = null;    // { sid, cual } del bloque que se está reescribiendo

  const LECTOR_ANCHO = 720, LECTOR_ALTO = 900;   // la franja de acotaciones pide 138 px

  const docLector = () => (lector && !lector.closed && lector.document ? lector.document : null);

  // Lo propio de esta ventana: la barra de abajo, los banderines, el guion
  // corto y el editor. El resto del aspecto sale de dos sitios: la columna de
  // lectura, del apuntador, y las cajas de nota y los resaltados, del CSS de
  // esta misma página, que se inyecta entero porque sus demás reglas no tienen
  // a qué agarrarse aquí.
  const CSS_LECTOR = `
    #col{padding-bottom:40vh}
    #tit{margin:0 0 10px}
    #rvEti{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}
    #rvEti span{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.05em;background:#E7D395;color:#5A4A16;padding:4px 7px;border-radius:3px}
    #rvCorto{margin:18px 0 0;padding:10px 12px;background:#FAF7EF;color:#2E2E2E;
      border:1px solid #EDE4CE;border-radius:4px;font-size:.62em;line-height:1.5}
    body.oscuro #rvCorto{background:#1C1A16;border-color:#3A352A;color:#E6E2D8}
    #rvCorto:empty{display:none}
    #rvCorto .rv-corto-cab{display:flex;align-items:center;gap:8px;flex-wrap:wrap;
      font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.06em;color:#8A7A3A;margin-bottom:8px}
    #rvCorto .rv-dura{text-transform:none;letter-spacing:0;font-weight:400;color:#7A7568}
    #rvCorto .rv-vacio{color:#8A8A8A;font-style:italic;margin:0}
    #rvCorto p{margin:0 0 8px}
    #rvCorto p:last-child{margin-bottom:0}
    /* La barra de abajo: lo que se puede cambiar de esta lámina, y el pie que
       dice dónde estoy. Va fija, como el pie del apuntador, para que no haya
       que buscarla al final de un guion largo. */
    #rvPie{position:fixed;left:0;right:0;bottom:0;z-index:14;background:var(--bg);
      border-top:1px solid var(--tenue);padding:8px 14px 9px;
      font-family:'Noto Sans',system-ui,sans-serif}
    #rvAcc{display:flex;flex-wrap:wrap;gap:6px;align-items:center;max-width:760px;margin:0 auto}
    #rvAcc button{font:600 11px/1 'Noto Sans',system-ui,sans-serif;padding:6px 10px;
      border:1px solid var(--tenue);background:var(--bg);color:var(--fg);
      border-radius:3px;cursor:pointer}
    #rvAcc button:hover{border-color:var(--acento);color:var(--acento)}
    #rvAcc .rv-cual{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.06em;color:var(--tenue);margin-left:8px}
    #rvAcc button.rv-on{background:#E7D395;border-color:#D8BE6E;color:#5A4A16}
    #rvAcc button.rv-on[data-n="2"]{background:#B4690E;border-color:#B4690E;color:#fff}
    #rvAcc button.rv-on[data-n="0"]{background:#EDE9E1;border-color:#DDD8CE;color:#3A3A3A}
    #rvMeta{max-width:760px;margin:7px auto 0;font-size:12px;color:var(--tenue);
      display:flex;flex-wrap:wrap;gap:4px 14px;letter-spacing:.03em}
    #rvMeta b{color:var(--acento);font-weight:600}
    #rvMeta .rv-porque{flex:1 1 100%}
    /* La nota puesta sobre el guion, debajo del párrafo que cita. */
    .rv-marca{background:#FCEEF2;border-left:3px solid #A42145;padding:3px 9px;
      font-size:.56em;line-height:1.45;color:#A42145;margin:8px 0 0;
      border-radius:0 3px 3px 0;cursor:pointer}
    .rv-marca:hover{background:#F8DFE7}
    .rv-marca.rv-sel{background:#FFF0DC;border-left-color:#FF9E2C;color:#8C4A00}
    textarea.rv-edicion{width:100%;box-sizing:border-box;min-height:46vh;
      font:15px/1.6 'Noto Sans',system-ui,sans-serif;color:#2E2E2E;padding:10px 12px;
      border:1px solid #C9C3B6;border-radius:4px;background:#fff;resize:vertical}
    textarea.rv-edicion.rv-corta{min-height:22vh}
    .rv-acc-guion{display:flex;align-items:center;gap:10px;justify-content:flex-end;
      margin-top:10px;flex-wrap:wrap}
    .rv-acc-guion .rv-pista{margin-right:auto;font-size:12px;color:var(--tenue)}
    .rv-acc-guion button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:7px 12px;
      border:1px solid #CCC;background:#F2F2F2;color:#333;border-radius:3px;cursor:pointer}
    .rv-acc-guion button.rv-primario{background:#A42145;border-color:#A42145;color:#fff}
    #rvEdicion{font-size:.62em}
    #rvEdicion:empty{display:none}`;

  const CUERPO_LECTOR =
    '<div id="col">' +
    '<div id="marca"><b id="mPos"></b><i id="mPct"></i></div>' +
    '<div id="tit"></div><div id="rvEti"></div>' +
    '<div id="texto"></div><div id="rvEdicion"></div><div id="rvCorto"></div></div>' +
    '<div id="rvPie"><div id="rvAcc"></div><div id="rvMeta"></div></div>';

  function htmlLector() {
    const base = (window.ApuntadorTema && window.ApuntadorTema.lecturaCSS) || "";
    return '<!doctype html><html lang="es"><head><meta charset="utf-8">' +
      "<title>Guion, " + esc(DECK) + "</title><style>" + base + css + CSS_LECTOR +
      "</style></head><body>" + CUERPO_LECTOR + "</body></html>";
  }

  function cajaLector() {
    let c = null;
    try { c = JSON.parse(localStorage.getItem("lector:caja") || "null"); } catch (e) {}
    if (!c || !(c.w > 200) || !(c.h > 200)) c = { w: LECTOR_ANCHO, h: LECTOR_ALTO, x: null, y: null };
    const pant = (window.screen && window.screen.availWidth) || c.w;
    if (typeof c.x !== "number") c.x = Math.max(0, Math.round(pant / 2 - c.w / 2));
    if (typeof c.y !== "number") c.y = 0;
    return c;
  }

  function recordarCajaLector() {
    if (!lector || lector.closed || !lector.outerWidth || !lector.outerHeight) return;
    const c = JSON.stringify({ w: lector.outerWidth, h: lector.outerHeight,
                               x: lector.screenX, y: lector.screenY });
    try { localStorage.setItem("lector:caja", c); } catch (e) {}
  }

  function abrirLector() {
    if (docLector()) { cerrarLector(); return; }
    if (rejilla) cerrarRejilla();
    const c = cajaLector();
    const w = window.open("about:blank", "guionrevision",
      "width=" + c.w + ",height=" + c.h + ",left=" + c.x + ",top=" + c.y +
      ",menubar=no,toolbar=no,location=no");
    if (!w) {
      aviso("El navegador bloqueó la ventana del guion. Permite las ventanas emergentes.", "lector");
      return;
    }
    w.document.write(htmlLector());
    w.document.close();
    montarLector(w);
  }

  function montarLector(w) {
    lector = w;
    const d = w.document;
    const col = d.getElementById("col");
    if (col) col.style.fontSize = (parseFloat(localStorage.getItem("lector:tam") || "22")) + "px";
    if (localStorage.getItem("lector:oscuro") === "1") d.body.classList.add("oscuro");

    d.addEventListener("click", (e) => {
      const t = e.target;
      if (!t || !t.closest) return;
      if (t.closest(".rv-capa")) return;          // la caja de nota se arregla sola
      const b = t.closest("button[data-rv]");
      if (b) {
        const cual = b.dataset.cual === "corto" ? "corto" : "largo";
        const sid = idActual();
        if (b.dataset.rv === "editar-guion") editarGuion(sid, "largo");
        else if (b.dataset.rv === "editar-corto") editarGuion(sid, "corto");
        else if (b.dataset.rv === "revertir-guion") revertirGuion(sid, "largo");
        else if (b.dataset.rv === "revertir-corto") revertirGuion(sid, "corto");
        else if (b.dataset.rv === "guion-guardar") guardarGuion(sid, cual);
        else if (b.dataset.rv === "guion-cancelar") cancelarEdicion();
        else if (b.dataset.rv === "sinc") {
          sinc("alternar");
          pintarAccLector(IDS.indexOf(sid), !!leerGuiones()[sid]);
        }
        else if (b.dataset.rv === "nivel") {
          if (edicionGuion) return;               // no mover el terreno bajo lo que se escribe
          ponerNivel(IDS.indexOf(sid), parseInt(b.dataset.n, 10));
          pintarNiveles(); pintarLector(true); pintarBarra();
        }
        return;
      }
      // un resaltado abre su nota; una marca de nota, la suya
      const m = t.closest("mark.rv-hl, .rv-marca[data-nid]");
      if (m && !arrastreEn(d)) {
        const nids = nidsDe(m);
        if (nids.length === 1) editar(nids[0]);
        else if (nids.length) abrirLista("citas", nids, d);
        return;
      }
      if (m) return;
      if (!arrastreEn(d)) deseleccionar();
      // pinchar un párrafo lo pone en curso, sin desplazar la ventana
      const p = t.closest("#texto p");
      if (!p) return;
      const i = parrafosLector().indexOf(p);
      if (i >= 0) { parrGuion = i; marcarParrafo(false); }
    });

    d.addEventListener("keydown", (e) => {
      const tag = (e.target && e.target.tagName) || "";
      if (/^(INPUT|SELECT|TEXTAREA)$/.test(tag)) {
        // con el foco en una caja de texto las teclas son texto, salvo Escape
        if (e.key === "Escape" && !d.querySelector(".rv-capa") && edicionGuion) {
          e.preventDefault(); cancelarEdicion();
        }
        return;
      }
      if (d.querySelector(".rv-capa")) return;    // manda la caja de nota
      if (e.key === "Escape") { e.preventDefault(); cerrarLector(); return; }
      if (e.key === "a" || e.key === "A") { e.preventDefault(); anotar(true); return; }
      if (e.key === "g" || e.key === "G") { e.preventDefault(); cerrarLector(); return; }
      if (e.key === "c" || e.key === "C") {
        if (edicionGuion) return;
        e.preventDefault(); ciclarNivel(); pintarLector(true); return;
      }
      if (e.key === "y" || e.key === "Y") {
        e.preventDefault(); sinc("alternar"); pintarAccLector(IDS.indexOf(idActual()),
          !!leerGuiones()[idActual()]); return;
      }
      // La Z también desde aquí: las marcas de cambio se ven en esta ventana
      // tanto como en la lámina, así que esconderlas tiene que poder pedirse
      // sin volver al deck. Alberto lo pidió el 13 de octubre de 2026.
      if (e.key === "z" || e.key === "Z") {
        e.preventDefault(); alternarCambios(); return;
      }
      if (e.key === "ArrowDown") { e.preventDefault(); moverParrafo(1); return; }
      if (e.key === "ArrowUp") { e.preventDefault(); moverParrafo(-1); return; }
      if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); Reveal.next(); return; }
      if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); Reveal.prev(); return; }
      const c2 = d.getElementById("col");
      const tam = (c2 && parseFloat(c2.style.fontSize)) || 22;
      if (e.key === "+" || e.key === "=") c2.style.fontSize = Math.min(tam + 2, 64) + "px";
      else if (e.key === "-") c2.style.fontSize = Math.max(tam - 2, 12) + "px";
      else if (e.key === "n" || e.key === "N") d.body.classList.toggle("oscuro");
      else return;
      try {
        localStorage.setItem("lector:tam", parseFloat(d.getElementById("col").style.fontSize));
        localStorage.setItem("lector:oscuro", d.body.classList.contains("oscuro") ? "1" : "0");
      } catch (e2) {}
    });

    sinc("registrar", () => parrafosLector()[parrGuion] || null);
    parrGuion = 0;
    pintarLector(false);
    pintarBarra();
  }

  function cerrarLector() {
    if (!lector) return;
    if (edicionGuion &&
        !preguntar(docLector(), "Hay un guion sin guardar. ¿Descartar los cambios?")) return;
    edicionGuion = null;
    recordarCajaLector();
    const w = lector;
    lector = null;
    sinc("registrar", null);
    sinc("reiniciar");
    deseleccionar();
    try { if (!w.closed) w.close(); } catch (e) {}
    pintarBarra();
  }

  const parrafosLector = () => {
    const d = docLector();
    return d ? [...d.querySelectorAll("#texto p")] : [];
  };

  /* Puente a la sincronía del guion con la lámina, que vive en apuntador.js por
     una razón de propagación: un archivo nuevo del tema no llega a los 30 decks
     sin tocar las 30 páginas, y revisar.js ya lee de ahí el CSS de la columna.

     Se llama siempre por aquí y nunca directo, porque un deck que no cargue el
     apuntador tiene que seguir revisándose igual: entonces esto no hace nada y
     la ventana del guion funciona sin resaltar la lámina. */
  function sinc(que, arg) {
    const S = window.ApuntadorSync;
    if (!S || typeof S[que] !== "function") return que === "activa" ? false : undefined;
    return S[que](arg);
  }

  // Hubo arrastre para seleccionar texto en ese documento: entonces se está
  // citando, no pinchando, y el clic no debe abrir ni cerrar ninguna nota.
  const arrastreEn = (d) => {
    const s = d && d.getSelection ? d.getSelection() : null;
    return !!(s && !s.isCollapsed && String(s).trim());
  };

  function marcarParrafo(desplazar) {
    const d = docLector();
    if (!d) return;
    const ps = parrafosLector();
    if (parrGuion >= ps.length) parrGuion = Math.max(0, ps.length - 1);
    ps.forEach((x, i) => x.classList.toggle("actual", i === parrGuion));
    sinc("aplicar", ps[parrGuion]);     // la lámina resalta la pieza del párrafo
    const marca = d.getElementById("marca"), x = ps[parrGuion];
    if (marca) {
      if (!x) marca.style.visibility = "hidden";
      else {
        marca.style.visibility = "visible";
        d.getElementById("mPos").textContent = (parrGuion + 1) + "/" + ps.length;
        d.getElementById("mPct").textContent =
          Math.round(((parrGuion + 1) / ps.length) * 100) + "%";
        marca.style.top = (x.offsetTop + x.offsetHeight / 2 - marca.offsetHeight / 2) + "px";
      }
    }
    if (!x || desplazar === false || !lector || !lector.scrollTo) return;
    const arriba = x.getBoundingClientRect().top + (lector.scrollY || lector.pageYOffset || 0);
    lector.scrollTo(0, Math.max(0, arriba - 12));
  }

  // Abajo en el último párrafo pasa a la lámina siguiente; arriba en el primero
  // vuelve a la anterior, y entra por su último párrafo.
  function moverParrafo(paso) {
    const ps = parrafosLector();
    const n = parrGuion + paso;
    if (!ps.length || n >= ps.length) { Reveal.next(); return; }
    if (n < 0) { alFinal = true; Reveal.prev(); return; }
    parrGuion = n;
    marcarParrafo(true);
  }

  /* El guion corto se enseña en todas las láminas, no solo en las marcadas: el
     núcleo no se pierde nunca, pero contarlo corto no es perderlo, y esa salida
     no existe si no está escrita. Donde falta, el hueco lo dice.

     Se quedan fuera la portada, el cierre y los separadores de bloque, cuyo
     guion ya son dos frases, salvo que estén marcados o ya lo traigan. */
  const SIN_CORTO = /\b(portada|cierre|seccion)\b/;

  // Cuánto se tarda en decir un texto, al ritmo de lectura de tools/tiempos.py.
  const PPM_REV = 135;
  const palabrasDe = (t) =>
    plano(String(t).replace(/<[^>]+>/g, " ").replace(/\[[^\]]*\]/g, " "))
      .split(/\s+/).filter(Boolean).length;
  const segundosDe = (t) => Math.round((palabrasDe(t) / PPM_REV) * 60);

  function tocaCorto(i) {
    return !!(nivelDe(i) || cortoDe(i) || !SECS[i] || !SIN_CORTO.test(SECS[i].className));
  }

  function pintarLector(conservar) {
    const d = docLector();
    if (!d) return;
    const i = IDS.indexOf(idActual());
    if (i < 0) return;
    const sec = SECS[i], sid = IDS[i];
    const g = leerGuiones()[sid], notas = leer()[sid] || [];
    const h = sec.querySelector("h1,h2") || sec.querySelector(".titulo,.gracias");
    d.getElementById("tit").textContent =
      (i + 1) + " de " + SECS.length + ".  " + (h ? h.textContent.trim() : sid);

    // Banderines: lo que esta lámina tiene pendiente de aplicar al HTML.
    const chips = [];
    if (g) chips.push('<span title="reescrito el ' + esc(g.ts) +
                      ', pendiente de aplicar al deck">guion reescrito</span>');
    if (leerCortos()[sid]) chips.push('<span>guion corto pendiente</span>');
    if (nivelDe(i) !== nivelDelDeck(i))
      chips.push('<span>nivel pendiente: ' + NOMBRE_NIVEL[nivelDe(i)] + "</span>");
    d.getElementById("rvEti").innerHTML = chips.join("");

    // El guion: la reescritura si la hay, que es lo que se está revisando.
    const aside = sec.querySelector("aside.notes");
    d.getElementById("texto").innerHTML = g ? textoAGuion(g.texto)
      : aside ? aside.innerHTML : "<p><em>(sin guion)</em></p>";
    // Las acotaciones de escena salen de la columna y se van a la franja del
    // costado, igual que en la vista de presentar: es la misma función, y por
    // eso las dos no se pueden desfasar.
    if (window.ApuntadorTema && ApuntadorTema.alMargen) ApuntadorTema.alMargen(d);
    pintarCambiosGuion(d, sid);

    // El guion corto, debajo, con su propio editor.
    const cuerpoCorto = d.getElementById("rvCorto");
    if (!tocaCorto(i)) cuerpoCorto.innerHTML = "";
    else {
      const texto = cortoDe(i);
      const largo = segundosDe(g ? g.texto : guionDelDeck(i)), corto = segundosDe(texto);
      cuerpoCorto.innerHTML = '<div class="rv-corto-cab">guion corto' +
        (texto ? '<span class="rv-dura">unos ' + corto + " s, frente a " + largo +
                 " s del largo</span>" : "") + "</div>" +
        (texto ? textoAGuion(texto)
               : '<p class="rv-vacio">Sin guion corto. Mientras no lo tenga, en clase esta ' +
                 (nivelDe(i) ? "lámina solo se puede saltar entera, no abreviar."
                             : "lámina no se puede abreviar a mano.") + "</p>");
    }

    // Las notas de esta lámina sobre el guion y sobre el guion corto, cada una
    // debajo de su bloque, y sus citas resaltadas sobre el texto.
    const marca = (x) =>
      '<div class="rv-marca" data-nid="' + x.nid + '">nota: ' + esc(x.texto) + "</div>";
    const deGuion = notas.filter((x) => x.ambito === "guion");
    const deCorto = notas.filter((x) => x.ambito === "corto");
    d.getElementById("texto").insertAdjacentHTML("beforeend", deGuion.map(marca).join(""));
    if (cuerpoCorto.innerHTML) cuerpoCorto.insertAdjacentHTML("beforeend", deCorto.map(marca).join(""));
    if (deGuion.length) resaltar(d.getElementById("texto"), deGuion);
    if (deCorto.length) resaltar(cuerpoCorto, deCorto);

    pintarAccLector(i, !!g);
    d.getElementById("rvMeta").innerHTML =
      "<span><b>" + notas.length + "</b> nota" + (notas.length === 1 ? "" : "s") +
      " en esta lámina</span><span>guion de <b>" +
      segundosDe(g ? g.texto : guionDelDeck(i)) + " s</b></span>" +
      '<span class="rv-porque">' + QUE_ES_NIVEL[nivelDe(i)] + "</span>" +
      "<span>A anota lo seleccionado &nbsp; flechas recorren &nbsp; G o Escape cierra</span>";

    if (!conservar) parrGuion = alFinal ? Math.max(0, parrafosLector().length - 1) : 0;
    alFinal = false;
    marcarParrafo(!conservar);
    pintarSeleccion();
    recordarCajaLector();
  }

  // La barra de abajo: reescribir, el guion corto y el nivel de recorte. Es lo
  // que la vista vieja llevaba dentro de cada bloque y aquí no cabría.
  /* El guion de la ventana, con lo que cambió desde la última foto: las
     palabras nuevas marcadas y las quitadas tachadas, dentro del propio
     párrafo. Aquí sí se tacha, al revés que en la lámina: esta ventana es para
     leer y comparar, no se proyecta, y nada se desborda.

     Se pinta DESPUÉS de sacar las acotaciones al margen, porque esa función
     reescribe los párrafos y borraría las marcas. */
  function pintarCambiosGuion(d, sid) {
    const c = cambiosDe(sid);
    const cont = d.getElementById("texto");
    if (!cont || !c || !(c.guion || []).length) return;
    const ps = [...cont.querySelectorAll("p")];
    (c.guion || []).forEach((g) => {
      const p = ps[g.i];
      if (!p) return;
      p.classList.add("rv-cam-p");
      /* **Un párrafo con matemáticas no se repinta.** El diff que llega de
         `tools/cambios.py` es texto plano, así que sustituir el párrafo por él
         borraría el SVG que MathJax ya dejó compuesto y la expresión se leería
         como "P Soc t Soc t-1". Alberto lo cazó el 13 de octubre de 2026,
         leyendo el guion de la tabla de transición.

         En esos párrafos se marca que cambiaron y el texto de antes va al
         `title`, que es lo que se puede enseñar sin tocar el contenido. */
      if (p.querySelector("mjx-container")) {
        const t = d.createElement("i");
        t.className = "rv-cam-tag";
        t.textContent = "cambiado";
        t.title = "Antes decía: " + difAntes(g.dif).trim();
        p.appendChild(t);
        return;
      }
      const marg = p.querySelector(".acot-marg");
      const nuevo = difHTML(g.dif, d);
      p.innerHTML = "";
      while (nuevo.firstChild) p.appendChild(nuevo.firstChild);
      if (marg) p.appendChild(marg);
    });
  }

  function pintarAccLector(i, hayReescrito) {
    const d = docLector();
    if (!d) return;
    const sid = IDS[i], n = nivelDe(i);
    const bot = [
      '<button type="button" data-rv="editar-guion">Editar guion</button>',
      hayReescrito ? '<button type="button" data-rv="revertir-guion">Revertir</button>' : "",
      tocaCorto(i) ? '<button type="button" data-rv="editar-corto">' +
        (cortoDe(i) ? "Editar guion corto" : "Escribir guion corto") + "</button>" : "",
      leerCortos()[sid] ? '<button type="button" data-rv="revertir-corto" data-cual="corto">' +
        "Revertir corto</button>" : "",
      '<span class="rv-cual">sincronía</span>',
      '<button type="button" data-rv="sinc"' +
        (sinc("activa") ? ' class="rv-on"' : "") + ">" +
        (sinc("activa") ? "Encendida" : "Apagada") + "</button>",
      '<span class="rv-cual">recorte</span>',
      [0, 1, 2].map((k) => '<button type="button" data-rv="nivel" data-n="' + k + '"' +
        (k === n ? ' class="rv-on"' : "") + ">" + NOMBRE_NIVEL[k] + "</button>").join(""),
    ];
    d.getElementById("rvAcc").innerHTML = bot.join("");
  }

  // Miniatura de la lámina: un clon dentro de su propio .reveal, para que herede
  // el tema completo, fondos incluidos, y reducido con una transformación. No se
  // reconstruye nada a mano, así que nunca se desfasa del deck. La usa la rejilla.
  function vistaPrevia(sec, alPinchar) {
    const clon = sec.cloneNode(true);
    clon.removeAttribute("id");
    clon.removeAttribute("data-sid");
    clon.classList.remove("present", "past", "future", "stack");
    clon.style.display = "block";
    clon.querySelectorAll("aside, script, iframe, video, audio")
        .forEach((x) => x.remove());
    // Los resaltados viajan en el clon. Se dejan a la vista, pero inertes: el que
    // se pincha es el del guion, no el de la miniatura.
    clon.querySelectorAll("mark.rv-hl").forEach((m) => {
      m.className = "rv-mini-hl";
      m.removeAttribute("data-nid");
      m.removeAttribute("data-n");
    });
    const caja = document.createElement("div");
    caja.className = "rv-mini";
    caja.title = "Ir a esta diapositiva";
    // El índice se mira al pinchar, no al construir: entre una cosa y la otra la
    // lámina puede haber cambiado de sitio en la rejilla.
    caja.addEventListener("click", alPinchar || (() => {
      const i = SECS.indexOf(sec);
      if (i >= 0) Reveal.slide(i);
    }));
    const lienzo = document.createElement("div");
    lienzo.className = "reveal";
    const pista = document.createElement("div");
    pista.className = "slides";
    pista.appendChild(clon);
    lienzo.appendChild(pista);
    caja.appendChild(lienzo);
    return caja;
  }

  /* ---------- reescribir el guion de la lámina, dentro de la ventana ---------- */

  // El guion largo y el corto se escriben igual, con el mismo editor. Solo
  // cambia en qué hueco se abre y en qué apartado se guarda.
  function editarGuion(sid, cual) {
    const d = docLector();
    if (!d || edicionGuion || sid !== idActual()) return;
    const corto = cual === "corto";
    const i = IDS.indexOf(sid);
    const hueco = d.getElementById(corto ? "rvCorto" : "rvEdicion");
    if (!hueco) return;
    const g = leerGuiones()[sid];
    edicionGuion = { sid, cual: corto ? "corto" : "largo" };
    if (!corto) d.getElementById("texto").style.display = "none";
    hueco.innerHTML = (corto ? '<div class="rv-corto-cab">guion corto</div>' : "") +
      '<textarea class="rv-edicion' + (corto ? " rv-corta" : "") + '"></textarea>' +
      '<div class="rv-acc-guion">' +
      '<span class="rv-pista">' + (corto
        ? "Lo que se dice de esta lámina cuando la sesión va tarde, en dos o tres frases. "
        : "") +
      "Un renglón en blanco separa párrafos. Ctrl+Enter guarda, Escape cancela.</span>" +
      '<button type="button" data-rv="guion-cancelar">Cancelar</button>' +
      '<button type="button" class="rv-primario" data-rv="guion-guardar"' +
      (corto ? ' data-cual="corto"' : "") + ">Guardar</button></div>";
    const ta = hueco.querySelector("textarea");
    ta.value = corto ? cortoDe(i) : (g ? g.texto : guionDelDeck(i));
    ta.addEventListener("keydown", (e) => {
      e.stopPropagation();
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) guardarGuion(sid, cual);
      else if (e.key === "Escape") cancelarEdicion();
    });
    ta.focus();
    ta.setSelectionRange(0, 0);
  }

  function guardarGuion(sid, cual) {
    const d = docLector();
    const ta = d && d.querySelector("textarea.rv-edicion");
    if (!ta) return;
    const corto = cual === "corto";
    const i = IDS.indexOf(sid);
    const texto = ta.value.trim();
    const ts = new Date().toISOString().slice(0, 16);
    const m = corto ? leerCortos() : leerGuiones();
    // Si vuelve a coincidir con el deck, deja de ser un cambio pendiente.
    if (!texto || texto === (corto ? cortoDelDeck(i) : guionDelDeck(i))) delete m[sid];
    else m[sid] = { texto, ts };
    if (corto) guardarCortos(m); else guardarGuiones(m);
    edicionGuion = null;
    if (d.getElementById("texto")) d.getElementById("texto").style.display = "";
    if (d.getElementById("rvEdicion")) d.getElementById("rvEdicion").innerHTML = "";
    pintarNiveles();        // la chapa de la lámina dice si ya tiene guion corto
    pintarLector(true);
    pintarBarra();
  }

  function cancelarEdicion() {
    if (!edicionGuion) return;
    edicionGuion = null;
    const d = docLector();
    if (d) {
      if (d.getElementById("texto")) d.getElementById("texto").style.display = "";
      if (d.getElementById("rvEdicion")) d.getElementById("rvEdicion").innerHTML = "";
    }
    pintarLector(true);
  }

  function revertirGuion(sid, cual) {
    const corto = cual === "corto";
    const m = corto ? leerCortos() : leerGuiones();
    if (!m[sid]) return;
    if (!preguntar(docLector(), "¿Descartar el guion " + (corto ? "corto" : "reescrito") + " de " + sid +
                 " y volver al del deck?")) return;
    delete m[sid];
    if (corto) guardarCortos(m); else guardarGuiones(m);
    pintarNiveles();
    pintarLector(true);
    pintarBarra();
  }

  /* ---------- la rejilla: cambiar el orden arrastrando ---------- */

  let rejilla = null;      // la capa, si está abierta
  const SELECCION = new Set();   // láminas marcadas con Ctrl+clic, para combinarlas
  let anclaSel = null;           // la última pinchada, para el rango con Shift
  let tirando = null;      // el arrastre en curso
  let autoScroll = null;   // el temporizador que desplaza al arrimarse al borde

  function celda(sid, sec) {
    const c = document.createElement("div");
    c.className = "rv-rj-cel";
    c.dataset.sid = sid;
    const n = (leer()[sid] || []).length;
    const cab = document.createElement("div");
    cab.className = "rv-rj-cab";
    cab.innerHTML = '<span class="rv-rj-num"></span><span class="rv-rj-mov" hidden></span>' +
      (n ? '<span class="rv-rj-notas">' + n + " nota" + (n === 1 ? "" : "s") + "</span>" : "") +
      '<button type="button" class="rv-rj-fus" data-rj="fusion" hidden></button>' +
      '<span class="rv-rj-bts">' +
      '<button type="button" class="rv-rj-bt" data-rj="mas" ' +
      'title="Insertar una lámina por escribir después de esta">+</button>' +
      '<button type="button" class="rv-rj-bt rv-rj-bt-x" data-rj="quitar"></button>' +
      "</span>";
    c.appendChild(cab);
    // El clic sin arrastre lleva a la lámina y cierra la rejilla, y en una lámina
    // por escribir abre su encargo. Lo decide mouseup, que es quien sabe si hubo
    // arrastre; la miniatura no navega por su cuenta. El título tampoco, que el
    // de la celda dice algo más útil.
    const mini = vistaPrevia(sec, () => {});
    mini.removeAttribute("title");
    c.appendChild(mini);
    const pie = document.createElement("div");
    pie.className = "rv-rj-pie";
    pie.textContent = sid;
    c.appendChild(pie);
    return c;
  }

  // El botón del final, para añadir una lámina detrás de la última.
  function celdaMas() {
    const c = document.createElement("button");
    c.type = "button";
    c.className = "rv-rj-mas";
    c.dataset.rj = "mas-final";
    c.innerHTML = "<span>+</span>Lámina nueva al final";
    return c;
  }

  // Dónde está cada lámina ahora mismo: en el deck, o guardada por estar
  // marcada para borrar. Las dos se pintan en la rejilla.
  const nodoDe = (id) => {
    const enDeck = [...PISTA.querySelectorAll(":scope > section")].find((x) => idDe(x) === id);
    return enDeck || GUARDADAS.get(id) || null;
  };

  // Números, marcas de movida y texto de la barra, sin rehacer las miniaturas.
  function pintarRejillaEstado() {
    if (!rejilla) return;
    const celdas = [...rejilla.querySelectorAll(".rv-rj-cel")];
    let actual = null;
    try { actual = idDe(Reveal.getCurrentSlide()); } catch (e) { actual = null; }
    const mov = lasMovidas(celdas.filter((c) => !esBorrada(c.dataset.sid))
                                 .map((c) => c.dataset.sid));
    // La numeración salta las borradas: enseña la posición que tendrá cada
    // lámina cuando el cambio se aplique, que es lo que se está decidiendo.
    let pos = 0;
    celdas.forEach((c) => {
      const sid = c.dataset.sid;
      const antes = ORDEN_DECK.indexOf(sid);
      const nueva = esNueva(sid), fuera = esBorrada(sid);
      const movida = !nueva && !fuera && mov.has(sid);
      if (!fuera) pos++;
      c.classList.toggle("rv-rj-movida", movida);
      c.classList.toggle("rv-rj-nueva", nueva);
      c.classList.toggle("rv-rj-borrada", fuera);
      c.classList.toggle("rv-rj-actual", !movida && !nueva && !fuera && sid === actual);
      c.querySelector(".rv-rj-num").textContent = fuera ? "" : pos;
      const m = c.querySelector(".rv-rj-mov");
      m.hidden = !(movida || nueva || fuera);
      m.textContent = fuera ? "se borra" : nueva ? "por escribir" : "antes " + (antes + 1);
      const f = laFusion(sid);
      // El mismo criterio que la barra: una fusión que el HTML ya dice está
      // aplicada, y lo que queda de ella no es un pendiente de la rejilla sino
      // la marca del propio deck.
      const sec = nodoDe(sid);
      const yaEnDeck = !!(sec && (sec.dataset.combinar || sec.dataset.combinarEn));
      const viva = f && fusionesVivas().some((y) => y.id === f.id);
      c.classList.toggle("rv-rj-fusionada", !!viva || yaEnDeck);
      c.classList.toggle("rv-rj-sel", SELECCION.has(sid));
      // Las láminas tocadas desde la última foto, de un vistazo.
      c.classList.toggle("rv-rj-cam", !!cambiosDe(sid));
      const fb = c.querySelector('[data-rj="fusion"]');
      fb.hidden = !viva && !yaEnDeck;
      if (!viva && yaEnDeck) {
        fb.textContent = "ya marcada para combinar";
        fb.title = "El HTML ya lleva la marca. Lo que falta es escribir la lámina única.";
      } else if (viva) {
        fb.textContent = "combina " + (f.partes.indexOf(sid) + 1) + " de " + f.partes.length;
        fb.title = "Se combina con: " +
          f.partes.filter((y) => y !== sid).join(", ") +
          (plano(f.texto) ? ".  Nota: " + plano(f.texto) : ".  Sin nota: el criterio lo pongo yo.") +
          "  Clic para editarla o deshacerla.";
      }
      const x = c.querySelector('[data-rj="quitar"]');
      x.textContent = fuera ? "↺" : "×";
      x.title = fuera ? "No borrarla después de todo"
                      : nueva ? "Quitar esta lámina por escribir"
                              : "Borrar esta lámina del deck";
      c.title = fuera
        ? "Marcada para borrar. Se irá del HTML al aplicar el cambio."
        : nueva
          ? "Lámina por escribir. Pulsa para escribir qué debe contener."
          : movida
            ? "Estaba en la posición " + (antes + 1) + " y ahora va en la " + pos +
              ". El HTML todavía no lo dice."
            : "Posición " + pos + ", la misma que dice el HTML.";
    });
    const o = [...mov].filter((id) => !esNueva(id)).length;
    const est = rejilla.querySelector(".rv-rj-est");
    const partes = [];
    if (o) partes.push(o + " lámina" + (o === 1 ? "" : "s") + " fuera de su sitio");
    const nn = nuevasVivas().length, nb = borradasVivas().length;
    const nf = fusionesVivas().length;
    if (nn) partes.push(nn + " por escribir");
    if (nb) partes.push(nb + " por borrar");
    if (nf) partes.push(nf + " por combinar");
    est.innerHTML = partes.length
      ? '<span class="rv-rj-pend">sin aplicar</span>' + partes.join(", ") +
        ". El HTML todavía no lo dice: se aplica con tools/reordenar.py."
      : "El deck está como dice el HTML.";
    const d = rejilla.querySelector('[data-rj="deshacer"]');
    // Pendiente es también una lámina por escribir o una marcada para borrar, no
    // solo una movida: si no, el botón se quedaba muerto justo en el caso
    // corriente de haber pedido una lámina y nada más.
    if (d) d.disabled = !ordenPendiente();
    const cb = rejilla.querySelector('[data-rj="combinar"]');
    if (cb) {
      cb.hidden = SELECCION.size < 2;
      cb.textContent = "Combinar en una (" + SELECCION.size + ")";
      cb.title = "Pedir que estas " + SELECCION.size + " láminas se combinen en una sola. " +
                 "Ctrl+clic selecciona, contiguas o no.";
    }
    const u = rejilla.querySelector('[data-rj="atras"]');
    if (u) {
      u.disabled = !PILA.length;
      u.textContent = PILA.length ? "Deshacer (" + PILA.length + ")" : "Deshacer";
    }
  }

  function pintarRejilla() {
    releer();
    rejilla = document.createElement("div");
    rejilla.className = "rv-rejilla";
    rejilla.tabIndex = -1;          // para que las flechas desplacen la malla
    const barra2 = document.createElement("div");
    barra2.className = "rv-rj-barra";
    barra2.innerHTML = "<b>Orden de las láminas, " + esc(DECK) + "</b>" +
      '<span class="rv-rj-est"></span>' +
      '<button type="button" class="rv-rj-comb" data-rj="combinar" hidden></button>' +
      '<button type="button" data-rj="atras" title="Deshacer el último movimiento. ' +
      'También con Ctrl+Z.">Deshacer</button>' +
      '<button type="button" data-rj="deshacer" title="Descartar el orden, las láminas ' +
      'por escribir y las marcadas para borrar, y dejar el deck como dice el HTML.">' +
      "Descartar los cambios</button>" +
      '<button type="button" data-rj="cerrar">Cerrar</button>';
    barra2.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-rj]");
      if (!b) return;
      if (b.dataset.rj === "cerrar") cerrarRejilla();
      if (b.dataset.rj === "atras") deshacerOrdenUno();
      if (b.dataset.rj === "combinar") combinarSeleccion();
      if (b.dataset.rj === "deshacer") deshacerOrden();
    });
    const lienzo = document.createElement("div");
    lienzo.className = "rv-rj-lienzo";
    ordenCompleto().forEach((id) => {
      const sec = nodoDe(id);
      if (sec) lienzo.appendChild(celda(id, sec));
    });
    lienzo.appendChild(celdaMas());
    lienzo.addEventListener("mousedown", alAgarrar);
    lienzo.addEventListener("click", alPulsarBoton);
    rejilla.appendChild(barra2);
    rejilla.appendChild(lienzo);
    const ayuda = document.createElement("div");
    ayuda.className = "rv-ayuda";
    ayuda.textContent = "Arrastra para mover. + inserta, × borra, Ctrl+clic selecciona " +
                        "para combinar. Ctrl+Z deshace. R o Escape cierra.";
    rejilla.appendChild(ayuda);
    document.body.appendChild(rejilla);
    pintarRejillaEstado();
    rejilla.focus({ preventScroll: true });
    const yo = rejilla.querySelector(".rv-rj-actual");
    if (yo) yo.scrollIntoView({ block: "center" });
  }

  function abrirRejilla() {
    if (rejilla) { cerrarRejilla(); return; }
    if (docLector()) cerrarLector();
    pintarRejilla();
    // Una lámina sin data-sid ni id lleva un identificador inventado al vuelo,
    // que no sobrevive a tools/ids.py: el orden guardado contra él se pierde al
    // aplicarlo. Vale más decirlo antes de arrastrar nada.
    const sin = SECS.filter((x) => !x.dataset.sid && !x.id).length;
    if (sin) aviso(sin + (sin === 1 ? " lámina no tiene identificador" :
                          " láminas no tienen identificador") +
                   ". Corre python3 tools/ids.py antes de reordenar, o el orden " +
                   "no se podrá aplicar al HTML.", "orden-sin-id");
    document.addEventListener("keydown", escRejilla, true);
  }

  function cerrarRejilla(destino) {
    if (!rejilla) return;
    if (tirando) soltar(true);
    rejilla.remove();
    rejilla = null;
    SELECCION.clear();
    anclaSel = null;
    document.removeEventListener("keydown", escRejilla, true);
    if (typeof destino === "number" && destino >= 0) {
      navPropia = true;
      try { Reveal.slide(destino); } finally { navPropia = false; }
    }
  }

  const escRejilla = (e) => {
    if (!rejilla || document.querySelector(".rv-capa")) return;
    if (e.key === "Escape") {
      e.stopPropagation();
      if (tirando) soltar(true); else cerrarRejilla();
    }
    // las flechas y el espacio desplazan la rejilla, no cambian de diapositiva
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "PageUp", "PageDown",
         "Home", "End", " "].includes(e.key)) e.stopPropagation();
  };

  function deshacerOrden() {
    if (!ordenPendiente()) return;
    if (!confirm("¿Descartar todo lo que esta rejilla tiene sin aplicar, el orden, " +
                 "las láminas por escribir, las marcadas para borrar y las que se iban a " +
                 "combinar, y dejar el deck como dice el HTML?")) return;
    recordar();
    guardarDeck({ nuevas: [], borradas: [], fusiones: [] });
    ponerOrden(ORDEN_DECK.slice(), false);
    reconstruirRejilla();
    pintarBarra();
    aviso("Descartado. El deck vuelve a estar como dice el HTML. Ctrl+Z lo devuelve.", "orden");
  }

  // Después de un cambio que viene de fuera del arrastre, la malla se rehace
  // entera: las miniaturas son clones, y así nunca se desfasan del deck.
  function reconstruirRejilla() {
    if (!rejilla) return;
    const y = rejilla.scrollTop;
    rejilla.remove();
    rejilla = null;
    pintarRejilla();
    rejilla.scrollTop = y;
  }

  /* ---------- insertar, borrar y describir ---------- */

  const nuevoId = () => "nueva-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);

  // Inserta una lámina por escribir detrás de `despues`, o al final si es null,
  // y abre en el acto la caja donde se dice qué debe contener.
  function insertarNueva(despues) {
    const id = nuevoId();
    const orden = ordenCompleto();
    const i = despues ? orden.indexOf(despues) : orden.length - 1;
    orden.splice(i + 1, 0, id);
    recordar();
    guardarDeck({ nuevas: leerNuevas().concat([{ id, texto: "", ts: sello() }]) });
    ponerOrden(orden, false);          // ya se apuntó arriba, los dos son un paso
    reconstruirRejilla();
    pintarBarra();
    editarEncargo(id, true);
  }

  // La marca de borrar se pone y se quita. Una lámina por escribir no se marca:
  // se quita del todo, que para eso todavía no existe en el HTML.
  // La lista de fusiones sin una lámina, deshaciendo la que se quede con una
  // sola parte. Se calcula aparte para poder guardarla en el mismo paso que el
  // borrado: si no, el encargo quedaría apuntando a una lámina que se va.
  const fusionesSin = (id) => leerFusiones()
    .map((f) => (f.partes.includes(id)
      ? Object.assign({}, f, { partes: f.partes.filter((x) => x !== id) }) : f))
    .filter((f) => f.partes.length > 1);

  function alternarBorrada(id) {
    if (esNueva(id)) {
      recordar();
      guardarDeck({ nuevas: leerNuevas().filter((x) => x.id !== id),
                    fusiones: fusionesSin(id) });
      ponerOrden(ordenCompleto().filter((x) => x !== id), false);
      reconstruirRejilla();
      pintarBarra();
      aviso("Lámina por escribir retirada. Ctrl+Z la devuelve.", "orden");
      return;
    }
    const fuera = esBorrada(id);
    const n = (leer()[id] || []).length;
    if (!fuera && n &&
        !confirm("Esa lámina tiene " + n + " nota" + (n === 1 ? "" : "s") +
                 " de revisión, que se irán con ella al aplicar el borrado.\n\n" +
                 "¿Marcarla para borrar de todos modos?")) return;
    const enGrupo = !fuera && enFusion(id);
    recordar();
    guardarDeck({ borradas: fuera ? leerBorradas().filter((x) => x !== id)
                                  : leerBorradas().concat([id]),
                  // una lámina que se va no puede seguir en una combinación
                  fusiones: fuera ? leerFusiones() : fusionesSin(id) });
    aplicarOrden();
    reconstruirRejilla();
    pintarBarra();
    aviso(fuera ? "Ya no se borrará."
                : "Marcada para borrar. Se va del HTML al aplicar el cambio, y Ctrl+Z lo deshace." +
                  (enGrupo ? " También sale de la combinación en la que estaba." : ""),
          "orden");
  }

  // Qué debe contener la lámina por escribir. Es texto y nada más: lo lee quien
  // después la escriba, no se proyecta ni viaja al paquete.
  function editarEncargo(id, recienCreada) {
    const x = laNueva(id);
    if (!x) return;
    capa(
      "<h3>Qué debe contener esta lámina</h3>" +
      '<div class="rv-id">' + esc(id) + "</div>" +
      "<p>Descríbela en texto, con el detalle que quieras: es el encargo que voy a leer " +
      "para escribirla. No se proyecta ni llega al grupo.</p>" +
      "<textarea>" + esc(x.texto || "") + "</textarea>" +
      '<div class="rv-acciones">' +
      (recienCreada ? "" : '<button type="button" class="rv-izq" data-rv="quitar">Quitar la lámina</button>') +
      '<button type="button" data-rv="cancelar">Cancelar</button>' +
      '<button type="button" class="rv-primario" data-rv="guardar">Guardar</button>' +
      "</div>",
      (c, cerrar) => {
        const t = c.querySelector("textarea");
        t.focus();
        const guardar = () => {
          const texto = t.value.trim();
          if (texto === (laNueva(id) || {}).texto) { cerrar(); return; }
          recordar();
          guardarDeck({ nuevas: leerNuevas().map(
            (y) => (y.id === id ? { id, texto, ts: sello() } : y)) });
          aplicarOrden();
          reconstruirRejilla();
          pintarBarra();
          cerrar();
        };
        t.addEventListener("keydown", (e) => {
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); guardar(); }
        });
        c.addEventListener("click", (e) => {
          const b = e.target.closest("button[data-rv]");
          if (!b) return;
          if (b.dataset.rv === "guardar") guardar();
          else if (b.dataset.rv === "quitar") { cerrar(); alternarBorrada(id); }
          else cerrar();
        });
      });
  }

  /* La selección para combinar. Ctrl+clic marca y desmarca una lámina, Shift+clic
     marca el tramo desde la última, y un clic normal la suelta y hace lo de
     siempre. Las láminas de una selección no tienen por qué ser contiguas. */
  function alternarSeleccion(sid) {
    if (SELECCION.has(sid)) SELECCION.delete(sid);
    else if (esBorrada(sid)) {
      aviso("Esa lámina está marcada para borrar: devuélvela con ↺ si quieres combinarla.",
            "orden");
      return;
    } else SELECCION.add(sid);
    anclaSel = sid;
    pintarRejillaEstado();
  }

  function rangoSeleccion(sid) {
    const ids = [...rejilla.querySelectorAll(".rv-rj-cel")].map((c) => c.dataset.sid);
    const a = ids.indexOf(anclaSel), b = ids.indexOf(sid);
    if (a < 0 || b < 0) return alternarSeleccion(sid);
    ids.slice(Math.min(a, b), Math.max(a, b) + 1)
       .forEach((x) => { if (!esBorrada(x)) SELECCION.add(x); });
    pintarRejillaEstado();
  }

  const soltarSeleccion = () => {
    if (!SELECCION.size) return false;
    SELECCION.clear();
    anclaSel = null;
    pintarRejillaEstado();
    return true;
  };

  // Combina lo seleccionado, en el orden en que está en la rejilla: es el orden
  // en que se van a leer al escribir la lámina única.
  function combinarSeleccion() {
    if (SELECCION.size < 2) return;
    const ids = [...rejilla.querySelectorAll(".rv-rj-cel")]
      .map((c) => c.dataset.sid).filter((x) => SELECCION.has(x));
    const fuera = ids.filter((x) => esBorrada(x));
    if (fuera.length) {
      aviso("Hay láminas marcadas para borrar en la selección. Quítalas de la selección " +
            "o devuélvelas antes de combinar.", "orden");
      return;
    }
    const id = combinar(ids, "");
    if (!id) return;
    SELECCION.clear();
    anclaSel = null;
    reconstruirRejilla();
    pintarBarra();
    editarFusion(id, null, true);
  }

  /* Qué hacer con la fusión: escribir su nota, sacar una lámina o deshacerla.
     La nota es opcional. Vacía quiere decir que el criterio lo pongo yo. */
  function editarFusion(fid, sid, recienCreada) {
    const f = leerFusiones().find((y) => y.id === fid);
    if (!f) return;
    const lista = f.partes.map((x, i) =>
      "<li>" + (i ? "" : "<strong>") + esc(x) + (i ? "" : "</strong>, la que se queda") +
      "</li>").join("");
    capa(
      "<h3>Combinar " + f.partes.length + " láminas en una</h3>" +
      '<div class="rv-id">' + esc(fid) + "</div>" +
      "<p>Se van a leer en este orden, y la lámina resultante se queda en el sitio de la " +
      "primera:</p><ol>" + lista + "</ol>" +
      "<p>Si quieres, di con qué criterio combinarlas. Si lo dejas vacío, lo decido yo " +
      "al escribirla.</p>" +
      "<textarea>" + esc(f.texto || "") + "</textarea>" +
      '<div class="rv-acciones">' +
      '<button type="button" class="rv-izq" data-rv="romper">Deshacer la combinación</button>' +
      (sid ? '<button type="button" data-rv="sacar">Sacar esta lámina</button>' : "") +
      '<button type="button" data-rv="cancelar">' + (recienCreada ? "Dejarlo así" : "Cancelar") +
      "</button>" +
      '<button type="button" class="rv-primario" data-rv="guardar">Guardar</button>' +
      "</div>",
      (c, cerrar) => {
        const t = c.querySelector("textarea");
        t.focus();
        const guardar = () => {
          const texto = t.value.trim();
          if (texto === (f.texto || "")) { cerrar(); return; }
          recordar();
          guardarDeck({ fusiones: leerFusiones().map(
            (y) => (y.id === fid ? Object.assign({}, y, { texto, ts: sello() }) : y)) });
          reconstruirRejilla();
          pintarBarra();
          cerrar();
        };
        t.addEventListener("keydown", (e) => {
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); guardar(); }
        });
        c.addEventListener("click", (e) => {
          const b = e.target.closest("button[data-rv]");
          if (!b) return;
          if (b.dataset.rv === "guardar") return guardar();
          if (b.dataset.rv === "romper") { romperFusion(fid); cerrar(); }
          else if (b.dataset.rv === "sacar") { sacarDeFusion(sid); cerrar(); }
          else return cerrar();
          reconstruirRejilla();
          pintarBarra();
        });
      });
  }

  // Los botones de la rejilla. Van en click y no en mousedown, que ese lo tiene
  // el arrastre.
  function alPulsarBoton(e) {
    const b = e.target.closest("button[data-rj]");
    if (!b) return;
    e.stopPropagation();
    if (b.dataset.rj === "mas-final") return insertarNueva(null);
    const cel = b.closest(".rv-rj-cel");
    if (!cel) return;
    if (b.dataset.rj === "mas") insertarNueva(cel.dataset.sid);
    if (b.dataset.rj === "quitar") alternarBorrada(cel.dataset.sid);
    if (b.dataset.rj === "fusion") {
      const f = laFusion(cel.dataset.sid);
      if (f) editarFusion(f.id, cel.dataset.sid);
    }
  }

  /* El arrastre. Se hace con eventos de ratón y no con arrastrar y soltar del
     navegador, para poder dibujar la marca de destino a mano.

     La lámina agarrada no se mueve de su sitio mientras se arrastra: se atenúa,
     una copia sigue al cursor, y entre las dos láminas donde caería se dibuja
     una línea vertical, como en PowerPoint. La malla no se recoloca hasta que
     se suelta, así que nada baila debajo del cursor mientras se decide.

     La copia no recibe eventos, para que elementFromPoint vea lo que hay debajo. */
  function alAgarrar(e) {
    if (e.button !== 0) return;
    if (e.target.closest("button")) return;      // los botones son de alPulsarBoton
    const cel = e.target.closest(".rv-rj-cel");
    if (!cel) return;
    e.preventDefault();          // sin selección de texto mientras se arrastra
    /* El destino se guarda como "esta lámina, por este lado", y no como "delante
       de esta otra": así la línea se dibuja siempre pegada a la lámina que hay
       bajo el cursor. Con la otra forma, soltar a la derecha de la última de una
       fila dibujaba la línea al principio de la fila siguiente, que es el mismo
       sitio pero no se lee igual. */
    tirando = { cel, x0: e.clientX, y0: e.clientY, movido: false,
                ancla: cel, derecha: true, x: e.clientX, y: e.clientY,
                dx: 0, dy: 0, fantasma: null, linea: null,
                ctrl: e.ctrlKey || e.metaKey, shift: e.shiftKey };
    document.addEventListener("mousemove", alMover, true);
    document.addEventListener("mouseup", alSoltar, true);
  }

  function arrancarArrastre() {
    const t = tirando, r = t.cel.getBoundingClientRect();
    t.dx = t.x0 - r.left;
    t.dy = t.y0 - r.top;
    const f = t.cel.cloneNode(true);
    f.classList.add("rv-rj-fantasma");
    f.style.width = r.width + "px";
    f.style.left = r.left + "px";
    f.style.top = r.top + "px";
    document.body.appendChild(f);
    t.fantasma = f;
    t.cel.classList.add("rv-rj-tirando");
    const l = document.createElement("div");
    l.className = "rv-rj-linea";
    rejilla.querySelector(".rv-rj-lienzo").appendChild(l);
    t.linea = l;
    t.movido = true;
    pintarLinea();
    // El desplazamiento al arrimarse al borde va por temporizador y no por
    // movimiento del ratón: si no, quedarse quieto arriba del todo no desplaza.
    autoScroll = setInterval(() => {
      if (!tirando || !rejilla) return;
      const h = window.innerHeight, y = tirando.y;
      const v = y < 110 ? -14 : y > h - 90 ? 14 : 0;
      if (!v) return;
      const antes = rejilla.scrollTop;
      rejilla.scrollTop += v;
      if (rejilla.scrollTop !== antes) colocar(tirando.x, tirando.y);
    }, 30);
  }

  function alMover(e) {
    if (!tirando) return;
    tirando.x = e.clientX;
    tirando.y = e.clientY;
    if (!tirando.movido) {
      if (Math.abs(e.clientX - tirando.x0) + Math.abs(e.clientY - tirando.y0) < 5) return;
      arrancarArrastre();
    }
    tirando.fantasma.style.left = e.clientX - tirando.dx + "px";
    tirando.fantasma.style.top = e.clientY - tirando.dy + "px";
    colocar(e.clientX, e.clientY);
  }

  /* Dónde caería ahora mismo, sin mover nada todavía: se guarda como la lámina
     que hay bajo el cursor (`ancla`) y por qué lado (`derecha`). El corte es su
     centro horizontal: a la izquierda, delante de ella; a la derecha, detrás. Si
     el cursor está en un hueco entre láminas, se conserva la última marca en vez
     de parpadear. */
  function colocar(x, y) {
    if (!tirando || !rejilla) return;
    const bajo = document.elementFromPoint(x, y);
    const dest = bajo && bajo.closest && bajo.closest(".rv-rj-cel");
    const lienzo = rejilla.querySelector(".rv-rj-lienzo");
    if (!dest || !lienzo.contains(dest)) return;
    const r = dest.getBoundingClientRect();
    tirando.ancla = dest;
    tirando.derecha = x >= r.left + r.width / 2;
    pintarLinea();
  }

  // Delante de qué lámina caería, o null para el final de la fila.
  const destinoDe = (t) => (t.derecha ? t.ancla.nextElementSibling : t.ancla);

  // La línea, en el hueco que hay antes de la lámina de destino. Las medidas se
  // toman contra el lienzo, no contra la ventana, para que valgan igual con la
  // rejilla desplazada.
  function pintarLinea() {
    const t = tirando;
    if (!t || !t.linea || !rejilla) return;
    const lienzo = rejilla.querySelector(".rv-rj-lienzo");
    if (!t.ancla || !lienzo.contains(t.ancla)) return;
    const rl = lienzo.getBoundingClientRect();
    const r = t.ancla.getBoundingClientRect();
    t.linea.style.left = (t.derecha ? r.right - rl.left + 6 : r.left - rl.left - 10) + "px";
    t.linea.style.top = r.top - rl.top + "px";
    t.linea.style.height = r.height + "px";
  }

  function alSoltar(e) {
    if (!tirando) return;
    const cel = tirando.cel, hubo = tirando.movido;
    const ctrl = tirando.ctrl, shift = tirando.shift;
    soltar(false);
    if (hubo) return;
    const sid = cel.dataset.sid;
    // Ctrl y Shift son para seleccionar, no para navegar
    if (ctrl) return alternarSeleccion(sid);
    if (shift) return rangoSeleccion(sid);
    if (soltarSeleccion()) return;
    // No hubo arrastre: fue un clic. En una lámina por escribir abre su encargo;
    // en una marcada para borrar no lleva a ninguna parte, que ya no está en el
    // deck; en las demás, va a ella y cierra la rejilla.
    if (esNueva(sid)) return editarEncargo(sid);
    if (esBorrada(sid)) {
      aviso("Esa lámina está marcada para borrar. El botón ↺ la devuelve.", "orden");
      return;
    }
    cerrarRejilla(IDS.indexOf(sid));
  }

  // cancelar: quitar la marca y no mover nada, que la lámina no se había movido.
  function soltar(cancelar) {
    if (!tirando) return;
    const t = tirando;
    document.removeEventListener("mousemove", alMover, true);
    document.removeEventListener("mouseup", alSoltar, true);
    if (autoScroll) { clearInterval(autoScroll); autoScroll = null; }
    tirando = null;
    if (!t.movido) return;
    if (t.fantasma) t.fantasma.remove();
    if (t.linea) t.linea.remove();
    t.cel.classList.remove("rv-rj-tirando");
    const lienzo = rejilla && rejilla.querySelector(".rv-rj-lienzo");
    if (cancelar || !lienzo || !lienzo.contains(t.cel)) { pintarRejillaEstado(); return; }
    // aquí es donde la lámina se mueve de verdad, al soltarla
    const destino = destinoDe(t);
    if (destino !== t.cel && (!destino || lienzo.contains(destino))) {
      lienzo.insertBefore(t.cel, destino || null);
    }
    const nuevo = [...lienzo.querySelectorAll(".rv-rj-cel")].map((c) => c.dataset.sid);
    const cambio = !mismos(nuevo, IDS);
    if (cambio) ponerOrden(nuevo);
    pintarRejillaEstado();
    pintarBarra();
    if (cambio) {
      aviso(ordenPendiente()
        ? "Orden cambiado, pendiente de aplicar al HTML con tools/reordenar.py. " +
          "Ctrl+Z lo deshace."
        : "El orden vuelve a ser el que dice el HTML.", "orden");
    }
  }

  function purgar() {
    const t = totalNotas();
    if (!t) return;
    capa(
      "<h3>Borrar todas las notas</h3>" +
      '<div class="rv-id">' + DECK + "</div>" +
      "<p>Se van a borrar <strong>" + t + " nota" + (t === 1 ? "" : "s") +
      "</strong> de este deck. No hay manera de recuperarlas.</p>" +
      "<p>Si todavía no me las has pasado, cancela y exporta primero con la tecla E.</p>" +
      (Object.keys(leerGuiones()).length
        ? "<p>Los guiones reescritos no se tocan: se descartan uno a uno, con Revertir.</p>" : "") +
      '<div class="rv-acciones">' +
      '<button type="button" data-rv="cancelar">Cancelar</button>' +
      '<button type="button" class="rv-peligro" data-rv="confirmar">Borrar las ' + t + "</button>" +
      "</div>",
      (c, cerrar) => {
        c.querySelector('[data-rv="cancelar"]').focus();
        c.addEventListener("click", (e) => {
          const b = e.target.closest("button[data-rv]");
          if (!b) return;
          if (b.dataset.rv === "confirmar") { guardar({}); }
          cerrar();
          refrescar();
        });
      });
  }

  Reveal.addKeyBinding({ keyCode: 65, key: "A", description: "Anotar esta diapositiva" },
                       () => anotar(false));
  Reveal.addKeyBinding({ keyCode: 67, key: "C", description: "Nivel de recorte de esta diapositiva" },
                       () => ciclarNivel());
  Reveal.addKeyBinding({ keyCode: 69, key: "E", description: "Exportar notas de revisión" }, exportar);
  Reveal.addKeyBinding({ keyCode: 71, key: "G", description: "Ver el guion de esta lámina" },
                       abrirLector);
  Reveal.addKeyBinding({ keyCode: 76, key: "L", description: "Lista de notas" }, () => abrirLista("lamina"));
  Reveal.addKeyBinding(
    { keyCode: 88, key: "X", description: "Lo que cambió desde la última vez" },
    () => abrirCambios());
  Reveal.addKeyBinding(
    { keyCode: 90, key: "Z", description: "Esconder o mostrar las marcas de cambio" },
    () => alternarCambios());
  Reveal.addKeyBinding({ keyCode: 82, key: "R", description: "Rejilla: cambiar el orden de las láminas" },
                       abrirRejilla);

  /* Ctrl+Z deshace el último movimiento de láminas. Va en fase de captura,
     porque reveal y el pincel también escuchan, y cede la tecla cuando no es
     suya: con el foco en una caja de texto, que entonces es de quien escribe; y
     con el pincel encendido, que es cuando Ctrl+Z deshace un trazo.

     La excepción es la rejilla abierta, y ahí la tecla es suya aunque el pincel
     esté encendido: la rejilla tapa la lámina entera, así que debajo no se está
     dibujando nada, y el pincel queda además invisible, de modo que ceder la
     tecla dejaba a la rejilla anunciando un atajo que no hacía nada.

     Fuera de la rejilla, sin nada que deshacer, tampoco se queda con ella: es
     peor una tecla que no hace nada que una que no es tuya. */
  document.addEventListener("keydown", (e) => {
    if (!(e.ctrlKey || e.metaKey) || e.shiftKey || e.altKey) return;
    if (e.key !== "z" && e.key !== "Z") return;
    if (enCampo(e.target)) return;
    if (!rejilla && document.body.classList.contains("pn-activo")) return;
    if (!PILA.length && !rejilla) return;
    e.preventDefault();
    e.stopPropagation();
    deshacerOrdenUno();
  }, true);
  // El globo con el texto de antes. Por ratón y por clic, que es la vía en
  // pantalla táctil, igual que las glosas del contenido.
  document.addEventListener("mouseover", (e) => {
    const el = e.target && e.target.closest ? e.target.closest(".rv-cam") : null;
    if (el) globoCambio(el);
  });
  document.addEventListener("mouseout", (e) => {
    const el = e.target && e.target.closest ? e.target.closest(".rv-cam") : null;
    if (el && !el.contains(e.relatedTarget)) cerrarGloboCambio();
  });
  document.addEventListener("click", (e) => {
    const el = e.target && e.target.closest ? e.target.closest(".rv-cam") : null;
    if (el) globoCambio(el); else cerrarGloboCambio();
  }, true);

  Reveal.on("slidechanged", () => {
    pintarBarra();
    marcarCambios();
    cerrarGloboCambio();
    if (!navPropia) deseleccionar();
    // La ventana del guion enseña una lámina a la vez: sigue al deck.
    if (docLector() && !edicionGuion) pintarLector(false);
  });
  // Si al llegar aquí reveal todavía no había terminado de arrancar, el orden se
  // aplicó sobre el DOM pero sin resincronizar. Se repite al estar listo.
  Reveal.on("ready", () => { aplicarOrden(); pintarBarra(); });
  // Se arranca con lo que haya en este navegador, para pintar sin esperar, y en
  // cuanto contesta el servidor manda lo que diga el disco.
  desdeLocal();
  // El orden pendiente se aplica antes de pintar nada: el deck se ve siempre en
  // el orden que va a tener, aunque el HTML todavía no lo diga.
  aplicarOrden();
  resaltarLaminas();
  pintarNiveles();
  pintarBarra();
  cargar().then(() => {
    aplicarOrden();       // lo que diga el disco manda sobre lo que hubiera aquí
    refrescar();
    cargarResueltas();
    vigilar();
  });
  // red de seguridad: si "ready" ya había disparado antes de registrarnos,
  // el primer pintado se hizo sin diapositiva actual.
  setTimeout(pintarBarra, 400);
})();
