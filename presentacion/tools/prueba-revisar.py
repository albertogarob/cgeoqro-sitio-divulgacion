#!/usr/bin/env python3
"""Prueba de regresión del anotador y del apuntador del tema.

    python3 tools/prueba-revisar.py [sesiones/SNN-.../index.html]

Abre el deck en Chrome headless con ?review, siembra notas de mentira en
localStorage y comprueba el ciclo completo de revisión: que la cita quede
resaltada en amarillo, que el clic abra su nota y la deje seleccionada en
naranja, que la lista lleve a la lámina o al punto del guion donde vive cada
nota, que la selección se suelte al pinchar fuera, al cambiar de lámina y con
Escape, y que el <aside class="notes"> original nunca se toque, para que el
PDF y el apuntador salgan limpios. Del apuntador comprueba que lee el guion
del deck, que sus tres relojes van, hora, sesión y lámina, y que las alarmas a
hora de reloj se editan, se guardan, se disparan una sola vez y avisan sin
tapar el guion.

Comprueba además el cierre del ciclo: que un resueltas.js junto al deck, cargado
desde file://, se lleve al arrancar las notas ya corregidas y las reescrituras
ya aplicadas, sin tocar lo que sigue pendiente.

Las citas de prueba se sacan del propio deck, así que sirve con cualquiera.
Corre con un perfil de Chrome desechable: no pisa las notas reales.
"""
import re, subprocess, sys, pathlib, os, json, tempfile, shutil

RUTA = sys.argv[1] if len(sys.argv) > 1 else "sesiones/S01-presentacion-del-curso-y-evaluacion/index.html"

# Se inyecta ANTES de revisar.js: elige dos láminas con viñetas, una de ellas con
# guion, y deja sembradas las notas. El anotador se encuentra el terreno puesto.
SEMILLA = """<script>
window.confirm = () => true;
window.__P = (function () {
  const plano = (s) => s.replace(/\\s+/g, " ").trim();
  const secs = [...document.querySelectorAll(".reveal .slides > section")];
  const sec = secs.find((s) => s.querySelectorAll(".cuerpo li").length >= 2 &&
                               s.querySelector("aside.notes p"));
  if (!sec) return null;
  const otra = secs.find((s) => s !== sec && s.querySelector(".cuerpo li") &&
                                plano(s.querySelector(".cuerpo li").textContent).length > 15);
  const lis = [...sec.querySelectorAll(".cuerpo li")];
  const fuerte = sec.querySelector(".cuerpo li strong");
  const citaA = plano((fuerte || lis[0]).textContent).slice(0, 40);
  const cand = lis.find((l) => plano(l.textContent).length > 15 && !plano(l.textContent).includes(citaA));
  const citaB = cand ? plano(cand.textContent).slice(0, 40) : null;
  const parr = [...sec.querySelectorAll("aside.notes p")].find((x) => plano(x.textContent).length > 40);
  const citaG = parr ? plano(parr.textContent).slice(0, 40) : null;
  const citaC = otra ? plano(otra.querySelector(".cuerpo li").textContent).slice(0, 40) : null;
  const sid = sec.dataset.sid || sec.id;
  const sid2 = otra ? (otra.dataset.sid || otra.id) : null;
  const notas = [
    { cita: citaA, texto: "primera nota", ambito: "lamina", ts: "2026-09-01T10:00" },
    { cita: citaA, texto: "segunda nota sobre la misma cita", ambito: "lamina", ts: "2026-09-01T10:01" },
    { cita: citaB, texto: "aclarar esto", ambito: "lamina", ts: "2026-09-01T10:02" },
    { cita: citaG, texto: "acortar esta parte", ambito: "guion", ts: "2026-09-01T10:03" },
    { cita: "", texto: "nota sin cita", ambito: "lamina", ts: "2026-09-01T10:04" },
    { cita: "frase que no existe en ningun deck", texto: "cita huerfana", ambito: "lamina", ts: "2026-09-01T10:05" },
  ].filter((x) => x.cita !== null);
  // Una lámina donde alguna palabra se repita, para probar que el ordinal de la
  // cita manda: dos notas sobre la misma palabra tienen que resaltar apariciones
  // distintas, no juntarse las dos en la primera.
  let rep = null;
  for (const s of secs) {
    const sid3 = s.dataset.sid || s.id;
    if (!sid3 || s === sec || s === otra) continue;
    const copia = s.cloneNode(true);
    [...copia.querySelectorAll("aside")].forEach((a) => a.remove());
    const cuenta = {};
    for (const w of plano(copia.textContent).split(/[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+/)) {
      if (w.length < 5) continue;
      cuenta[w] = (cuenta[w] || 0) + 1;
      if (cuenta[w] === 2) { rep = { sid: sid3, palabra: w }; break; }
    }
    if (rep) break;
  }

  const todo = { [sid]: notas };
  if (rep) todo[rep.sid] = [
    { nid: "nREP0", cita: rep.palabra, nth: 0, texto: "la primera vez", ambito: "lamina", ts: "2026-09-01T10:10" },
    { nid: "nREP1", cita: rep.palabra, nth: 1, texto: "la segunda vez", ambito: "lamina", ts: "2026-09-01T10:11" },
  ];
  // La segunda lámina lleva además la nota que resueltas.js tiene que borrar al
  // arrancar. Va aquí y no en la primera para no descuadrar sus conteos.
  if (sid2) todo[sid2] = [
    { cita: citaC, texto: "nota de otra lamina", ambito: "lamina", ts: "2026-09-01T10:06" },
    { cita: "", texto: "nota ya corregida", ambito: "lamina", ts: "2026-09-01T10:07" },
  ];
  try { localStorage.setItem("revision:" + __DECK__, JSON.stringify(todo)); }
  catch (e) { window.__err = "localStorage: " + e.message; }

  // Dos reescrituras pendientes del guion, cada una por su vía: la de la primera
  // lámina ya es palabra por palabra lo que dice el deck, así que el anotador la
  // suelta sin que nadie se lo pida; la de la segunda solo se va porque
  // resueltas.js la nombra, que es el caso de haberla aplicado retocándola.
  const ps = [...sec.querySelectorAll("aside.notes p")];
  const guionSid = (ps.length ? ps.map((x) => x.innerHTML.trim()) : []).join("\\n\\n");
  const g = { [sid]: { texto: guionSid, ts: "2026-09-01T10:08" } };
  if (sid2) g[sid2] = { texto: "reescritura que apliqué retocada", ts: "2026-09-01T10:09" };
  try { localStorage.setItem("guion:" + __DECK__, JSON.stringify(g)); } catch (e) {}

  // Lo que el resueltas.js de prueba se encuentra al cargarse desde el disco.
  window.__RESUELTAS_PRUEBA = {
    sello: "prueba-2026-09-02",
    notas: sid2 ? [{ id: sid2, texto: "  nota   ya corregida " }] : [],
    guiones: sid2 ? [sid2] : [],
  };
  return { sid, sid2, citaA, citaB, citaC, citaG, rep, n: notas.length };
})();
</script>
"""

PRUEBA = """<script>
const R = [];
const ok = (n, c, extra) => R.push((c ? "OK   " : "FALLA") + "  " + n + (extra && !c ? "  [" + extra + "]" : ""));
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
const clic = (el) => el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
const cerrarCapa = () => { const c = document.querySelector(".rv-capa"); if (c) clic(c); };
const tecla = (k, code) => document.dispatchEvent(new KeyboardEvent("keydown",
  { key: k, keyCode: code, which: code, bubbles: true, cancelable: true }));
const todas = () => JSON.parse(localStorage.getItem("revision:" + __DECK__) || "{}");
const notas = () => todas()[P.sid] || [];
const total = () => Object.values(todas()).reduce((a, b) => a + b.length, 0);
// Cuenta NOTAS seleccionadas, no fragmentos de resaltado. Una cita que cruza una
// etiqueta, por ejemplo "De 1943 a <strong>Dartmouth</strong>: la gestación", no
// cabe en un solo <mark>: el anotador la pinta en varios, todos con el mismo
// data-nid, y los selecciona juntos. Contar elementos daba 3 donde hay 1 nota, y
// empezó a fallar cuando los decks pasaron a llevar cuatro o cinco palabras
// resaltadas por lámina.
const selEn = (raiz) => [...new Set([...raiz.querySelectorAll("mark.rv-hl.rv-sel")]
  .map((m) => m.dataset.nid))];
const seleccion = () => selEn(document);
const items = () => [...document.querySelectorAll(".rv-capa .rv-item")];
const P = window.__P;

(async () => {
 try {
  if (!P) throw new Error("el deck no tiene ninguna lamina con viñetas y guion");
  if (window.__err) R.push("FALLA  " + window.__err);
  await dormir(1200);
  const secs = [...document.querySelectorAll(".slides > section")];
  const sec = secs.find((s) => s.dataset.sid === P.sid);
  const sec2 = secs.find((s) => s.dataset.sid === P.sid2);
  const marcaDe = (cita) => [...sec.querySelectorAll("mark.rv-hl")]
    .find((m) => cita.includes(m.textContent.trim()));

  // Un deck de verdad ya viene clasificado y con sus guiones cortos escritos.
  // La prueba los quita todos y pone los suyos, para valer igual en cualquier
  // sesión y no depender de cómo esté clasificada.
  secs.forEach((s) => {
    delete s.dataset.recorte;
    [...s.querySelectorAll("aside.corto, aside.apuntes, aside.ficha")].forEach((x) => x.remove());
  });

  // Dos láminas del final marcadas en el propio HTML, como si el recorte ya
  // estuviera aplicado al deck: el apuntador lee el archivo, no lo que el
  // anotador tenga pendiente. Una con guion corto escrito y otra sin él.
  const sueltas = secs.filter((s) => s !== sec && s !== sec2 &&
                                     s.querySelector("aside.notes p") && !s.dataset.min);
  const recA = sueltas[sueltas.length - 3], recB = sueltas[sueltas.length - 2];
  if (recA && recB) {
    recA.dataset.recorte = "1";
    recB.dataset.recorte = "2";
    const ac = document.createElement("aside");
    ac.className = "corto";
    ac.innerHTML = "<p>Version corta de esta lamina, dos frases y a la siguiente.</p>";
    recA.appendChild(ac);
  }

  // 0. resueltas.js: al arrancar se lleva lo que ya está corregido en el deck
  const gPend = () => JSON.parse(localStorage.getItem("guion:" + __DECK__) || "{}");
  const enOtra = () => (todas()[P.sid2] || []).map((x) => x.texto);
  ok("resueltas.js borra la nota ya corregida",
     !enOtra().includes("nota ya corregida"), enOtra().join(" | "));
  ok("y no se lleva por delante las demas de esa lamina",
     enOtra().includes("nota de otra lamina"), enOtra().join(" | "));
  ok("ni las de la lamina que no nombra", notas().length === P.n, "quedan " + notas().length);
  ok("suelta la reescritura que el deck ya dice", !gPend()[P.sid],
     JSON.stringify(Object.keys(gPend())));
  ok("y la que resueltas.js da por aplicada", !gPend()[P.sid2],
     JSON.stringify(Object.keys(gPend())));
  ok("deja constancia del sello, para no volver a borrar",
     localStorage.getItem("resueltas:" + __DECK__) === "prueba-2026-09-02",
     localStorage.getItem("resueltas:" + __DECK__));
  const av = document.querySelector(".rv-aviso");
  ok("lo avisa en pantalla", !!av && /3 correcciones/.test(av.textContent),
     av ? av.textContent : "(sin aviso)");

  if (av) av.remove();

  // 0b. el ordinal de la cita: dos notas sobre la misma palabra repetida tienen
  // que caer en apariciones distintas, no amontonarse en la primera
  if (P.rep) {
    const laminaRep = secs.find((s) => s.dataset.sid === P.rep.sid);
    const marcas = [...laminaRep.querySelectorAll("mark.rv-hl")]
      .filter((m) => m.textContent.trim() === P.rep.palabra);
    ok("la cita repetida resalta dos veces, no una",
       marcas.length === 2, "marcas=" + marcas.length + " palabra=" + P.rep.palabra);
    ok("y cada aparicion es de su nota, en orden",
       marcas.length === 2 && marcas[0].dataset.nid === "nREP0" &&
       marcas[1].dataset.nid === "nREP1",
       marcas.map((m) => m.dataset.nid).join(" | "));
    ok("ninguna queda marcada como repetida",
       marcas.every((m) => !m.dataset.n), marcas.map((m) => m.dataset.n).join(" | "));
  } else {
    R.push("OK     (este deck no tiene ninguna palabra repetida que probar)");
  }

  // 0c. abierto con doble clic no hay servidor, y eso se avisa sin perder nada
  ok("la barra avisa de que no hay servidor", !!document.querySelector(".rv-off"));
  ok("y aun así las notas están", total() > 0, "total=" + total());

  // 1. el resaltado aparece donde estaba la cita
  const marcas = [...sec.querySelectorAll("mark.rv-hl")];
  const textos = marcas.map((m) => m.textContent);
  ok("hay resaltados en la lamina", marcas.length >= 2, "marcas=" + marcas.length);
  ok("resalta la cita de la vineta", textos.some((t) => P.citaA.includes(t.trim())), textos.join(" | "));
  ok("resalta la segunda cita", textos.some((t) => P.citaB.includes(t.trim())), textos.join(" | "));
  ok("el resaltado sale amarillo",
     getComputedStyle(marcas[0]).backgroundColor === "rgb(255, 232, 115)",
     getComputedStyle(marcas[0]).backgroundColor);
  ok("no resalta dentro del guion oculto", !sec.querySelector("aside.notes mark.rv-hl"));
  ok("la cita huerfana no inventa resaltado", !textos.some((t) => t.includes("frase que no existe")));

  // 1b. la tecla X ya no borra nada
  const antesX = notas().length;
  tecla("x", 88);
  await dormir(200);
  ok("la tecla X ya no borra las notas", notas().length === antesX,
     notas().length + " de " + antesX);

  // 2. dos notas sobre la misma cita comparten un resaltado
  const compartida = marcaDe(P.citaA);
  ok("la cita repetida acumula dos nid",
     compartida.dataset.nid.trim().split(" ").length === 2, compartida.dataset.nid);
  ok("y lo anuncia con un contador", compartida.dataset.n === "2", compartida.dataset.n);

  // 3. el clic abre la nota, y la deja seleccionada mientras se edita
  const suelta = marcaDe(P.citaB);
  clic(suelta);
  await dormir(200);
  ok("el clic abre la caja de edicion", !!document.querySelector(".rv-capa textarea"));
  ok("la caja trae el texto de la nota",
     document.querySelector(".rv-capa textarea").value === "aclarar esto",
     document.querySelector(".rv-capa textarea").value);
  ok("y muestra la cita", !!document.querySelector(".rv-capa .rv-cita"));
  ok("la nota en edicion queda seleccionada", suelta.classList.contains("rv-sel"));
  ok("la seleccion se pinta naranja",
     getComputedStyle(suelta).backgroundColor === "rgb(255, 158, 44)",
     getComputedStyle(suelta).backgroundColor);
  ok("solo hay una nota seleccionada", seleccion().length === 1, "sel=" + seleccion().length);
  cerrarCapa();
  await dormir(150);
  ok("al cerrar la caja sigue seleccionada", seleccion().length === 1, "sel=" + seleccion().length);

  // marcar sin dejar la caja abierta, que es lo que piden las pruebas siguientes
  const marcar = async (m) => { clic(m); await dormir(180); cerrarCapa(); await dormir(120); };

  // 4. un clic en cualquier otro punto la suelta
  clic(sec.querySelector("h2") || sec);
  await dormir(120);
  ok("el clic fuera deselecciona", seleccion().length === 0, "sel=" + seleccion().length);

  // 5. Escape tambien la suelta
  await marcar(suelta);
  tecla("Escape", 27); await dormir(120);
  ok("Escape deselecciona", seleccion().length === 0, "sel=" + seleccion().length);

  // 6. cambiar de lamina la suelta
  await marcar(suelta);
  Reveal.slide(secs.indexOf(sec) + 1 < secs.length ? secs.indexOf(sec) + 1 : 0);
  await dormir(400);
  ok("cambiar de lamina deselecciona", seleccion().length === 0, "sel=" + seleccion().length);

  // 7. editar y guardar
  clic(suelta);
  await dormir(200);
  const ta = document.querySelector(".rv-capa textarea");
  ok("la caja vuelve a abrirse en la lamina de la nota",
     !!ta && Reveal.getCurrentSlide().dataset.sid === P.sid, Reveal.getCurrentSlide().dataset.sid);
  ta.value = "texto corregido";
  clic([...document.querySelectorAll(".rv-capa button")].find((b) => b.dataset.rv === "guardar"));
  await dormir(250);
  ok("la caja se cierra al guardar", !document.querySelector(".rv-capa"));
  ok("el texto quedo guardado", notas().some((x) => x.texto === "texto corregido"),
     JSON.stringify(notas().map((x) => x.texto)));
  ok("sigue resaltado despues de editar", !!marcaDe(P.citaB));
  ok("y sigue seleccionada despues de guardar", seleccion().length === 1, "sel=" + seleccion().length);

  // 8. el resaltado compartido abre la lista de sus dos notas
  // (tras guardar, refrescar() rehace los <mark>: hay que volver a buscarlos)
  clic(marcaDe(P.citaA));
  await dormir(200);
  ok("el resaltado compartido abre la lista", items().length === 2, "items=" + items().length);
  clic(document.querySelector(".rv-capa"));     // cerrar pinchando el fondo
  await dormir(150);

  // 9. la tecla L abre la lista, con sus dos pestañas
  Reveal.slide(secs.indexOf(sec));
  await dormir(350);
  tecla("l", 76);
  await dormir(250);
  ok("la tecla L abre la lista", !!document.querySelector(".rv-capa"));
  ok("lista todas las notas de la lamina", items().length === P.n, "items=" + items().length);
  const etiquetas = items().map((x) => x.querySelector(".rv-eti").textContent);
  ok("avisa de la cita que ya no aparece",
     etiquetas.some((t) => t.includes("sin localizar")), etiquetas.join(" | "));
  ok("distingue la nota sin cita", etiquetas.some((t) => t.includes("sin cita")), etiquetas.join(" | "));

  // 9b. editar desde la lista tambien selecciona la nota
  const conCita = items().find((x) => x.querySelector(".rv-eti").textContent.includes("resaltada"));
  clic(conCita.querySelector('button[data-rv="editar"]'));
  await dormir(250);
  ok("editar desde la lista abre la caja", !!document.querySelector(".rv-capa textarea"));
  ok("y deja la nota seleccionada", seleccion().length === 1, "sel=" + seleccion().length);
  cerrarCapa();
  await dormir(150);

  // 10. la pestaña del deck entero, y pinchar una nota lleva a su lamina
  tecla("l", 76);
  await dormir(250);
  clic([...document.querySelectorAll(".rv-capa button")].find((b) => b.dataset.rv === "modo-deck"));
  await dormir(250);
  ok("la pestaña del deck lista todas las notas", items().length === total(), "items=" + items().length);
  ok("agrupa por lamina", document.querySelectorAll(".rv-capa .rv-grupo").length >= 2,
     "grupos=" + document.querySelectorAll(".rv-capa .rv-grupo").length);
  if (P.sid2) {
    const ajena = items().find((x) => x.dataset.sid === P.sid2);
    clic(ajena);
    await dormir(400);
    ok("la lista se cierra al pinchar una nota", !document.querySelector(".rv-capa"));
    ok("pinchar la nota lleva a su lamina",
       Reveal.getCurrentSlide().dataset.sid === P.sid2, Reveal.getCurrentSlide().dataset.sid);
    ok("y la deja seleccionada alla", selEn(sec2).length === 1, "sel=" + selEn(sec2).length);
    ok("la navegacion propia no se autodeselecciona", seleccion().length === 1);
  }

  // 11. eliminar desde la lista
  Reveal.slide(secs.indexOf(sec));
  await dormir(350);
  const badge = document.querySelector(".rv-barra .rv-n");
  ok("la barra trae contador pinchable", !!badge, document.querySelector(".rv-barra").textContent);
  clic(badge);
  await dormir(250);
  const huerfana = items().find((x) => x.querySelector(".rv-txt").textContent === "cita huerfana");
  clic(huerfana.querySelector('button[data-rv="eliminar"]'));
  await dormir(300);
  ok("se elimina la nota", notas().length === P.n - 1, "quedan " + notas().length);

  /* 12. la vista de guion es una ventana aparte, la misma con la que se
     presenta. Se le suplanta window.open por un iframe, como al apuntador, y
     desde aquí se la maneja como si fuera la ventana de verdad. */
  const marcoG = document.createElement("iframe");
  document.body.appendChild(marcoG);
  /* El confirm de la ventana del guion, suplantado igual que el del deck. Hace
     falta desde el 12 de octubre de 2026, cuando la pregunta pasó a salir en la
     ventana que la dispara: sin esto, headless se queda esperando un diálogo
     que nadie va a contestar y la prueba muere por tiempo. Se vuelve a poner
     cada vez porque document.write reabre el documento. */
  const confirmaG = () => {
    try { marcoG.contentWindow.confirm = () => true; } catch (e) {}
  };
  confirmaG();
  const ventG = { closed: false, get document() { return marcoG.contentDocument; },
                  focus() {}, close() { ventG.closed = true; },
                  scrollTo() {}, addEventListener() {}, innerHeight: 900 };
  let rasgosG = "";
  window.open = (u, n2, f) => { rasgosG = f || ""; ventG.closed = false; return ventG; };
  const dg = () => (ventG.closed ? null : ventG.document);
  const abiertaG = () => !ventG.closed && !!ventG.document.getElementById("texto");
  const teclaG = (k) => dg().dispatchEvent(new KeyboardEvent("keydown",
      { key: k, bubbles: true, cancelable: true }));

  tecla("l", 76);
  await dormir(250);
  const deGuion = items().find((x) => x.querySelector(".rv-eti").textContent.includes("guion"));
  clic(deGuion);
  await dormir(500);
  ok("la nota de guion abre la ventana del guion", abiertaG(), "rasgos=" + rasgosG);
  if (abiertaG()) {
    const G = dg();
    ok("y es una ventana emergente con su caja", rasgosG.includes("width="), rasgosG);
    ok("y lleva el deck a la lamina de la nota",
       Reveal.getCurrentSlide().dataset.sid === P.sid,
       Reveal.getCurrentSlide().dataset.sid);
    ok("y queda seleccionada en el guion",
       G.querySelectorAll("mark.rv-hl.rv-sel").length === 1,
       "sel=" + G.querySelectorAll("mark.rv-hl.rv-sel").length);
    ok("la lamina ya no tiene nada seleccionado",
       sec.querySelectorAll("mark.rv-hl.rv-sel").length === 0);

    // 12b. la ventana trae la columna de lectura, no el manuscrito entero
    const ps = [...G.querySelectorAll("#texto p")];
    ok("el guion sale en parrafos", ps.length > 0, "ps=" + ps.length);
    ok("el primer parrafo va en curso", ps.length && ps[0].classList.contains("actual"));
    ok("la marca del costado dice por donde va",
       (G.getElementById("mPos") || {}).textContent === "1/" + ps.length,
       (G.getElementById("mPos") || {}).textContent);
    ok("el titulo nombra la lamina y su sitio en el deck",
       /^\\d+ de \\d+\\./.test((G.getElementById("tit") || {}).textContent || ""),
       (G.getElementById("tit") || {}).textContent);
    ok("solo enseña una lamina, no el deck entero",
       !G.querySelector(".rv-bl") && !G.querySelector(".rv-mini"));
    ok("el pie cuenta las notas de la lamina",
       /nota/.test((G.getElementById("rvMeta") || {}).textContent || ""),
       (G.getElementById("rvMeta") || {}).textContent);
    if (ps.length > 1) {
      teclaG("ArrowDown");
      await dormir(150);
      ok("la flecha abajo pasa al siguiente parrafo",
         [...G.querySelectorAll("#texto p")][1].classList.contains("actual"));
      ok("y la marca lo dice", (G.getElementById("mPos") || {}).textContent === "2/" + ps.length,
         (G.getElementById("mPos") || {}).textContent);
    }

    const mg = [...G.querySelectorAll("#texto mark.rv-hl")];
    ok("el guion resalta su cita", mg.some((m) => P.citaG.includes(m.textContent.trim())),
       mg.map((m) => m.textContent).join(" | "));
    ok("no arrastra al guion las citas de lamina",
       !mg.some((m) => P.citaA.includes(m.textContent.trim())), mg.length + " marcas");
    const mgs = mg.find((m) => P.citaG.includes(m.textContent.trim()));
    clic(mgs);
    await dormir(250);
    const t2 = G.querySelector(".rv-capa textarea");
    ok("el clic en el guion abre su nota, en la misma ventana",
       t2 && t2.value === "acortar esta parte", t2 && t2.value);
    ok("y no la abre en la ventana del deck", !document.querySelector(".rv-capa"));
    ok("y sigue seleccionada en el guion",
       G.querySelectorAll("mark.rv-hl.rv-sel").length === 1,
       "sel=" + G.querySelectorAll("mark.rv-hl.rv-sel").length);
    ok("y la caja dice que la nota es del guion",
       /guion/.test(G.querySelector(".rv-capa h3").textContent),
       G.querySelector(".rv-capa h3").textContent);
    const capaG = G.querySelector(".rv-capa");
    if (capaG) capaG.remove();

    // 12c. anotar desde la ventana deja la nota con ambito guion
    const parr = [...G.querySelectorAll("#texto p")][0];
    const rg = G.createRange();
    rg.selectNodeContents(parr.firstChild || parr);
    const selG = marcoG.contentWindow.getSelection();
    selG.removeAllRanges(); selG.addRange(rg);
    teclaG("a");
    await dormir(250);
    const cajaA = G.querySelector(".rv-capa");
    ok("A anota desde la ventana del guion", !!cajaA);
    if (cajaA) {
      const ta2 = cajaA.querySelector("textarea");
      ta2.value = "nota escrita desde la ventana";
      ta2.dispatchEvent(new KeyboardEvent("keydown",
        { key: "Enter", ctrlKey: true, bubbles: true, cancelable: true }));
      await dormir(350);
      const mias = (JSON.parse(localStorage.getItem("revision:" + __DECK__) || "{}")[P.sid] || [])
        .filter((x) => x.texto === "nota escrita desde la ventana");
      ok("la nota se guarda con ambito guion",
         mias.length === 1 && mias[0].ambito === "guion", JSON.stringify(mias));
      ok("y la caja se cierra", !G.querySelector(".rv-capa"));
    }

    // con la ventana abierta, A sobre el deck sigue anotando la lamina
    window.getSelection().removeAllRanges();
    tecla("a", 65);
    await dormir(250);
    const cajaL = document.querySelector(".rv-capa");
    ok("con la ventana abierta, A sobre el deck anota la lamina",
       !!cajaL && /esta diapositiva/.test(cajaL.querySelector("h3").textContent),
       cajaL && cajaL.querySelector("h3").textContent);
    if (cajaL) cajaL.remove();

    // desde la ventana abierta, una nota de lamina la cierra y marca alla
    tecla("l", 76);
    await dormir(250);
    const deLamina = items().find((x) => x.querySelector(".rv-eti").textContent.includes("lámina") &&
                                         x.querySelector(".rv-eti").textContent.includes("resaltada"));
    clic(deLamina);
    await dormir(400);
    ok("una nota de lamina cierra la ventana del guion", !abiertaG());
    ok("y queda seleccionada en la lamina", seleccion().length === 1, "sel=" + seleccion().length);
    tecla("g", 71); await dormir(300);
    tecla("g", 71); await dormir(300);
    ok("cerrar la ventana deselecciona", seleccion().length === 0, "sel=" + seleccion().length);

    // 12d. la ventana sigue al deck: una lamina a la vez
    if (P.sid2) {
      tecla("g", 71);
      await dormir(400);
      ok("G abre la ventana por la lamina en curso",
         dg().getElementById("texto").textContent.replace(/\\s+/g, " ").includes(P.citaG.slice(0, 25)),
         dg().getElementById("texto").textContent.slice(0, 50));
      Reveal.slide(secs.findIndex((x) => (x.dataset.sid || x.id) === P.sid2));
      await dormir(450);
      ok("al cambiar de lamina la ventana cambia con ella",
         !dg().getElementById("texto").textContent.replace(/\\s+/g, " ").includes(P.citaG.slice(0, 25)),
         dg().getElementById("texto").textContent.slice(0, 50));
      Reveal.slide(secs.indexOf(sec));
      await dormir(450);
      ok("y al volver, vuelve el guion de esta",
         dg().getElementById("texto").textContent.replace(/\\s+/g, " ").includes(P.citaG.slice(0, 25)),
         dg().getElementById("texto").textContent.slice(0, 50));
      teclaG("Escape");
      await dormir(250);
      ok("Escape cierra la ventana desde dentro", !abiertaG());
    }
  }

  // 12e. nivel de recorte: C recorre los tres estados y lo deja pendiente
  const xPend = () => JSON.parse(localStorage.getItem("recorte:" + __DECK__) || "{}");
  const chapa = () => sec.querySelector(":scope > .rv-nivel");
  Reveal.slide(secs.indexOf(sec));
  await dormir(300);
  ok("sin marcar, la lamina se etiqueta como nucleo, en gris",
     !!chapa() && /núcleo/.test(chapa().textContent) &&
     chapa().classList.contains("rv-n0"), chapa() && chapa().textContent);
  ok("y la chapa de una de nucleo tambien dice si le falta el guion corto",
     /núcleo, sin corto/.test(chapa().textContent), chapa().textContent);
  ok("y las marcadas en el deck llevan su nivel",
     /recorte 1/.test(recA.querySelector(":scope > .rv-nivel").textContent),
     recA.dataset.sid);
  tecla("c", 67);
  await dormir(300);
  ok("C marca la lamina como recorte 1",
     !!chapa() && /recorte 1/.test(chapa().textContent), chapa() && chapa().textContent);
  ok("y lo deja pendiente, sin tocar el deck",
     (xPend()[P.sid] || {}).nivel === 1 && !sec.dataset.recorte, JSON.stringify(xPend()));
  ok("la chapa avisa de que todavia no tiene guion corto",
     /sin corto/.test(chapa().textContent), chapa().textContent);
  ok("la barra cuenta el recorte pendiente",
     /1 recorte/.test(document.querySelector(".rv-barra").textContent),
     document.querySelector(".rv-barra").textContent);
  tecla("c", 67);
  await dormir(300);
  ok("otra C la sube a recorte 2",
     /recorte 2/.test(chapa().textContent), chapa() && chapa().textContent);
  tecla("c", 67);
  await dormir(300);
  ok("y la tercera la devuelve a nucleo",
     /núcleo/.test(chapa().textContent) && !xPend()[P.sid],
     chapa().textContent + " " + JSON.stringify(xPend()));
  tecla("c", 67);          // se queda en 1 para lo que viene
  await dormir(300);
  ok("recorrer los niveles deja un solo aviso, no una torre",
     document.querySelectorAll('.rv-aviso[data-clave="nivel"]').length === 1,
     "avisos=" + document.querySelectorAll('.rv-aviso[data-clave="nivel"]').length);
  ok("y los avisos viven en una columna, sin pisarse",
     !!document.querySelector(".rv-avisos > .rv-aviso") &&
     getComputedStyle(document.querySelector(".rv-avisos")).flexDirection === "column",
     getComputedStyle(document.querySelector(".rv-avisos") || document.body).flexDirection);

  // 13. reescribir el guion de una lamina, desde la barra de la ventana
  const guiones = () => JSON.parse(localStorage.getItem("guion:" + __DECK__) || "{}");
  const asideOriginal = sec.querySelector("aside.notes").innerHTML;
  Reveal.slide(secs.indexOf(sec));
  await dormir(300);
  tecla("g", 71);
  await dormir(450);
  const G2 = dg();
  ok("la ventana abre por la lamina en curso", abiertaG());
  ok("y su barra trae el boton de editar el guion",
     !!G2.querySelector('#rvAcc button[data-rv="editar-guion"]'));
  ok("uno solo, que la ventana enseña una lamina",
     G2.querySelectorAll('button[data-rv="editar-guion"]').length === 1,
     "botones=" + G2.querySelectorAll('button[data-rv="editar-guion"]').length);
  clic(G2.querySelector('button[data-rv="editar-guion"]'));
  await dormir(300);
  const te = G2.querySelector("textarea.rv-edicion");
  ok("el boton abre el guion en un area de texto", !!te);
  ok("el area trae el guion del deck",
     te && te.value.replace(/\\s+/g, " ").includes(P.citaG.slice(0, 30)),
     te && te.value.slice(0, 70));
  ok("y mientras se escribe no se ve el guion debajo",
     G2.getElementById("texto").style.display === "none",
     G2.getElementById("texto").style.display);

  te.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true }));
  await dormir(300);
  ok("Escape cancela la edicion", !G2.querySelector("textarea.rv-edicion"));
  ok("y no cierra la ventana", abiertaG());
  ok("y devuelve el guion a la vista", G2.getElementById("texto").style.display !== "none");
  ok("cancelar no guarda nada", !guiones()[P.sid]);

  clic(G2.querySelector('button[data-rv="editar-guion"]'));
  await dormir(300);
  G2.querySelector("textarea.rv-edicion").value =
    "Primer parrafo reescrito.\\n\\nSegundo parrafo reescrito.";
  clic(G2.querySelector('button[data-rv="guion-guardar"]'));
  await dormir(450);
  ok("el guion reescrito se guarda", !!guiones()[P.sid], JSON.stringify(Object.keys(guiones())));
  ok("la ventana muestra el texto nuevo",
     G2.getElementById("texto").textContent.includes("Segundo parrafo reescrito"),
     G2.getElementById("texto").textContent.slice(0, 60));
  ok("en parrafos, no en un solo bloque",
     G2.querySelectorAll("#texto p").length === 2,
     "p=" + G2.querySelectorAll("#texto p").length);
  ok("y se marca como reescrito",
     /reescrito/.test(G2.getElementById("rvEti").textContent),
     G2.getElementById("rvEti").textContent);
  ok("el guion del deck no se toca",
     sec.querySelector("aside.notes").innerHTML === asideOriginal);
  ok("la barra del deck cuenta el guion pendiente",
     /guion/.test(document.querySelector(".rv-barra").textContent),
     document.querySelector(".rv-barra").textContent);

  tecla("e", 69);
  await dormir(350);
  const prev = document.querySelector(".rv-capa .rv-prev");
  ok("el export lleva el guion reescrito aparte",
     !!prev && prev.textContent.includes("## Guion reescrito") &&
     prev.textContent.includes("Segundo parrafo reescrito"),
     prev && prev.textContent.slice(-80));
  cerrarCapa();
  await dormir(200);

  // 13d. el guion corto y el nivel de recorte, en la misma barra
  const cPend = () => JSON.parse(localStorage.getItem("corto:" + __DECK__) || "{}");
  ok("la barra trae los tres niveles de recorte",
     G2.querySelectorAll('#rvAcc button[data-rv="nivel"]').length === 3,
     "botones=" + G2.querySelectorAll('#rvAcc button[data-rv="nivel"]').length);
  ok("con el nivel puesto resaltado",
     (G2.querySelector("#rvAcc button.rv-on") || {}).dataset.n === "1",
     (G2.querySelector("#rvAcc button.rv-on") || {}).dataset.n);
  ok("y el pie dice qué significa ese nivel",
     /sin avisar al grupo/.test(G2.getElementById("rvMeta").textContent),
     G2.getElementById("rvMeta").textContent.slice(0, 90));
  ok("el hueco del guion corto está, todavia vacio",
     !!G2.querySelector("#rvCorto .rv-vacio"));
  clic(G2.querySelector('button[data-rv="editar-corto"]'));
  await dormir(300);
  const tc = G2.querySelector("#rvCorto textarea.rv-edicion");
  ok("el boton abre el guion corto en su propia area de texto", !!tc);
  ok("y arranca vacio, que todavia no hay nada escrito", tc && tc.value === "", tc && tc.value);
  if (tc) tc.value = "Version corta de esta lamina.";
  clic(G2.querySelector('#rvCorto button[data-rv="guion-guardar"]'));
  await dormir(450);
  ok("el guion corto se guarda", !!cPend()[P.sid], JSON.stringify(Object.keys(cPend())));
  ok("la ventana lo muestra en parrafos",
     !!G2.querySelector("#rvCorto p") &&
     G2.getElementById("rvCorto").textContent.includes("Version corta de esta lamina"),
     G2.getElementById("rvCorto").textContent.slice(0, 60));
  ok("el deck no se toca", !sec.querySelector("aside.corto"));
  ok("la barra del deck cuenta el guion corto pendiente",
     /1 corto/.test(document.querySelector(".rv-barra").textContent),
     document.querySelector(".rv-barra").textContent);
  ok("y la chapa de la lamina ya no dice que le falte",
     !!chapa() && /, corto/.test(chapa().textContent), chapa() && chapa().textContent);
  clic(G2.querySelector('#rvAcc button[data-rv="nivel"][data-n="2"]'));
  await dormir(350);
  ok("los botones de nivel cambian el recorte desde la ventana",
     (xPend()[P.sid] || {}).nivel === 2, JSON.stringify(xPend()));
  clic(G2.querySelector('#rvAcc button[data-rv="nivel"][data-n="1"]'));
  await dormir(350);

  confirmaG();
  // 13d bis. el boton Eliminar de una nota abierta EN la ventana del guion.
  // Alberto lo dio por roto el 12 de octubre de 2026: el confirm salia en la
  // ventana de atras y desde el guion parecia que no hacia nada.
  {
    const antes = notas().length;
    const marca = G2.querySelector('.rv-marca[data-nid]');
    ok("hay una marca de nota en la ventana del guion", !!marca);
    if (marca) {
      const nid = marca.dataset.nid;
      clic(marca);
      await dormir(300);
      const caja = G2.querySelector(".rv-capa");
      ok("al pincharla se abre su caja dentro de esa ventana", !!caja);
      // El confirm tiene que preguntarse en ESTA ventana, no en la del deck.
      let dondePregunto = null;
      const wG = G2.defaultView || marcoG.contentWindow;
      const cDeck = window.confirm, cG = wG.confirm;
      window.confirm = () => { dondePregunto = "deck"; return true; };
      wG.confirm = () => { dondePregunto = "guion"; return true; };
      const bel = caja && caja.querySelector('button[data-rv="eliminar"]');
      ok("y la caja trae su boton Eliminar", !!bel);
      if (bel) clic(bel);
      await dormir(350);
      window.confirm = cDeck; wG.confirm = cG;
      ok("la pregunta sale en la ventana del guion, no detras",
         dondePregunto === "guion", "preguntó en: " + dondePregunto);
      ok("y la nota se borra de verdad",
         notas().length === antes - 1 && !notas().some((x) => x.nid === nid),
         "antes " + antes + ", ahora " + notas().length);
    }
  }

  // 13e. la sincronia del guion con la lamina, gobernada desde esta ventana.
  // El motor vive en apuntador.js y aqui solo se comprueba el mando: que el
  // boton y la tecla Y la alternen, y que el parrafo en curso de ESTA ventana
  // sea el que manda. Lo que se ve en la lamina lo mide prueba-sincronia.py.
  const sincOn = () => localStorage.getItem("sinc:activa") === "1";
  try { localStorage.removeItem("sinc:activa"); } catch (e) {}
  clic(G2.querySelector('#rvAcc button[data-rv="sinc"]'));
  await dormir(250);
  ok("el boton de la barra enciende la sincronia", sincOn(),
     localStorage.getItem("sinc:activa"));
  ok("y el boton se queda marcado como encendido",
     !!G2.querySelector('#rvAcc button[data-rv="sinc"].rv-on'),
     (G2.querySelector('#rvAcc button[data-rv="sinc"]') || {}).className);
  ok("la ventana de revision es la fuente del parrafo en curso",
     !!window.ApuntadorSync && ApuntadorSync.activa() === true);
  G2.dispatchEvent(new KeyboardEvent("keydown",
    { key: "y", bubbles: true, cancelable: true }));
  await dormir(250);
  ok("la tecla Y dentro de la ventana la apaga", !sincOn(),
     localStorage.getItem("sinc:activa"));
  ok("y el boton vuelve a decir que esta apagada",
     !G2.querySelector('#rvAcc button[data-rv="sinc"].rv-on') &&
     /Apagada/.test(G2.getElementById("rvAcc").textContent),
     G2.getElementById("rvAcc").textContent.slice(0, 120));
  ok("apagada, el deck no lleva la clase de sincronia",
     !document.documentElement.classList.contains("sinc"),
     document.documentElement.className);

  tecla("e", 69);
  await dormir(400);
  const prev2 = document.querySelector(".rv-capa .rv-prev");
  ok("el export lleva el guion corto y el nivel aparte",
     !!prev2 && prev2.textContent.includes("## Guion corto") &&
     prev2.textContent.includes("## Nivel de recorte") &&
     prev2.textContent.includes('data-recorte="1"') &&
     prev2.textContent.includes("Version corta de esta lamina"),
     prev2 && prev2.textContent.slice(-140));
  cerrarCapa();
  await dormir(200);

  // 13b. el apuntador sigue leyendo el guion del deck, no la reescritura
  Reveal.slide(secs.indexOf(sec));
  await dormir(300);
  const marco = document.createElement("iframe");
  document.body.appendChild(marco);
  const falso = { closed: false, document: marco.contentDocument,
                  focus() {}, close() {}, scrollTo() {}, addEventListener() {},
                  prompt: () => null };
  let rasgos = "";
  window.open = (u, n2, f) => { rasgos = f || ""; return falso; };
  try {
    localStorage.removeItem("apuntador:flotante");           // sin preferencia: la emergente
    localStorage.setItem("apuntador:caja", JSON.stringify({ w: 900, h: 1000, x: 40, y: 20 }));
  } catch (e) {}
  tecla("t", 84);
  await dormir(350);
  const suelo = falso.document.getElementById("texto");
  ok("el apuntador se abre", !!suelo);
  ok("y por defecto en la ventana emergente", rasgos.includes("width="), rasgos);
  ok("con el tamaño y el sitio donde se dejó",
     rasgos.includes("width=900") && rasgos.includes("height=1000") &&
     rasgos.includes("left=40") && rasgos.includes("top=20"), rasgos);
  ok("y lee el guion del deck, no la reescritura",
     !!suelo && !suelo.textContent.includes("Segundo parrafo reescrito") &&
     suelo.textContent.replace(/\\s+/g, " ").includes(P.citaG.slice(0, 25)),
     suelo && suelo.textContent.slice(0, 60));

  const dd = falso.document;
  // el reloj virtual del headless congela las transiciones a medio camino, y las
  // medidas de posición saldrían del fotograma equivocado
  const quieto = dd.createElement("style");
  quieto.textContent = "#marca,#barras b{transition:none!important}";
  dd.head.appendChild(quieto);
  const seg = (t) => String(t).split(":").reverse()
    .reduce((a, x, i) => a + parseFloat(x) * Math.pow(60, i), 0);
  const hh = dd.getElementById("hora").textContent;
  const ahora = new Date();
  ok("el apuntador da la hora del sistema",
     hh.length === 8 && hh[2] === ":" && hh[5] === ":" &&
     hh.slice(0, 5) === ("0" + ahora.getHours()).slice(-2) + ":" + ("0" + ahora.getMinutes()).slice(-2),
     hh);
  ok("y lleva el cronometro de la sesion",
     dd.getElementById("total").textContent.includes(":"),
     dd.getElementById("total").textContent);
  const antesTotal = seg(dd.getElementById("total").textContent);
  Reveal.slide(secs.indexOf(sec) + 1 < secs.length ? secs.indexOf(sec) + 1 : 0);
  await dormir(300);
  ok("el reloj de la lamina vuelve a cero al cambiar de diapositiva",
     dd.getElementById("lamina").textContent === "0:00",
     dd.getElementById("lamina").textContent);
  await dormir(1400);
  ok("y sigue corriendo solo", seg(dd.getElementById("lamina").textContent) >= 1,
     dd.getElementById("lamina").textContent);
  dd.dispatchEvent(new KeyboardEvent("keydown", { key: "r", bubbles: true }));
  await dormir(200);
  ok("R reinicia los cronometros",
     seg(dd.getElementById("total").textContent) <= 1 && antesTotal >= 0,
     dd.getElementById("total").textContent + ", antes " + antesTotal);

  // los tres relojes de ritmo
  ok("la fila de ritmo esta completa",
     !!dd.getElementById("guion") && !!dd.getElementById("clase") && !!dd.getElementById("holgura"));
  const gFalta = parseInt(dd.getElementById("guion").textContent, 10) * 60;
  ok("estima lo que le queda al guion, en minutos", gFalta > 60,
     dd.getElementById("guion").textContent);
  const cTexto = dd.getElementById("clase").textContent;
  const cQueda = seg(cTexto.replace("-", "")) * (cTexto[0] === "-" ? -1 : 1);
  const hTexto = dd.getElementById("holgura").textContent;
  const hQueda = seg(hTexto.slice(1)) * (hTexto[0] === "-" ? -1 : 1);
  ok("la holgura es la resta de la clase menos el guion",
     Math.abs(hQueda - (cQueda - gFalta)) <= 31, hTexto + " frente a " + Math.round(cQueda - gFalta));
  ok("y viene con su veredicto",
     ["holgado", "al día", "apura", "recorta"].includes(dd.getElementById("veredicto").textContent),
     dd.getElementById("veredicto").textContent);
  // el cursor de parrafo
  Reveal.slide(secs.indexOf(sec));
  await dormir(350);
  const pTecla = (k) => dd.dispatchEvent(
    new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }));
  const ps = () => [...dd.querySelectorAll("#texto p")];
  const actual = () => ps().findIndex((x) => x.classList.contains("actual"));
  ok("el apuntador marca el parrafo en curso", actual() === 0, "i=" + actual());
  ok("y solo uno", ps().filter((x) => x.classList.contains("actual")).length === 1);
  const faltaAntes = parseInt(dd.getElementById("guion").textContent, 10);
  pTecla("ArrowDown");
  await dormir(200);
  ok("abajo avanza un parrafo", actual() === 1, "i=" + actual());
  pTecla("ArrowUp");
  await dormir(200);
  ok("arriba retrocede un parrafo", actual() === 0, "i=" + actual());
  clic(ps()[2]);
  await dormir(200);
  ok("el clic pone en curso el parrafo pinchado", actual() === 2, "i=" + actual());
  // las acotaciones de escena, al margen y fuera del recorrido
  {
    const conAcot = secs.find((x) => {
      const n = x.querySelectorAll("aside.notes p");
      return [...n].some((q) => /^\s*\[/.test(q.textContent)) &&
             [...n].some((q) => !/^\s*\[/.test(q.textContent));
    });
    if (conAcot) {
      Reveal.slide(secs.indexOf(conAcot));
      await dormir(400);
      const enHtml = [...conAcot.querySelectorAll("aside.notes p")];
      const solas = enHtml.filter(
        (q) => /^\s*\[/.test(q.textContent) &&
               !q.textContent.replace(/\[[^\]]*\]/g, "").trim()).length;
      const paradas = dd.querySelectorAll("#texto p").length;
      ok("una acotacion que es su propio parrafo deja de ser una parada",
         paradas === enHtml.length - solas,
         "html=" + enHtml.length + " solas=" + solas + " paradas=" + paradas);
      ok("ninguna acotacion queda en la columna de lectura",
         dd.getElementById("texto").textContent.indexOf("[") < 0,
         dd.getElementById("texto").textContent.slice(0, 70));
      const margs = [...dd.querySelectorAll(".acot-marg")];
      ok("las acotaciones estan en la franja del margen", margs.length > 0,
         "n=" + margs.length);
      if (margs.length) {
        const pm = margs[0].closest("p");
        const rm = margs[0].getBoundingClientRect();
        const rp = pm.getBoundingClientRect();
        ok("la franja cae a la DERECHA del parrafo, no dentro",
           rm.left >= rp.right - 1,
           "marg=" + Math.round(rm.left) + " parrafo acaba en " + Math.round(rp.right));
        ok("y arranca a la altura de su parrafo",
           Math.abs(rm.top - rp.top) < 40,
           "marg=" + Math.round(rm.top) + " parrafo=" + Math.round(rp.top));
        ok("en letra mas chica que la del guion",
           parseFloat(getComputedStyle(margs[0]).fontSize) <
           parseFloat(getComputedStyle(pm).fontSize) * 0.7,
           getComputedStyle(margs[0]).fontSize + " vs " + getComputedStyle(pm).fontSize);
      }
      Reveal.slide(secs.indexOf(sec));
      await dormir(350);
    }
  }
  // la marca al costado del parrafo en curso
  ok("hay marca al costado del parrafo", !!dd.getElementById("marca"));
  ok("dice en que parrafo voy sobre el total de la lamina",
     dd.getElementById("mPos").textContent === (actual() + 1) + "/" + ps().length,
     dd.getElementById("mPos").textContent);
  ok("y el avance de la lamina en porciento",
     dd.getElementById("mPct").textContent ===
       Math.round(100 * (actual() + 1) / ps().length) + "%",
     dd.getElementById("mPct").textContent);
  const centro = (el) => { const r = el.getBoundingClientRect(); return r.top + r.height / 2; };
  ok("centrada a la altura del parrafo",
     Math.abs(centro(dd.getElementById("marca")) - centro(ps()[actual()])) < 3,
     Math.round(centro(dd.getElementById("marca"))) + " frente a " +
     Math.round(centro(ps()[actual()])));

  // las dos barras de avance
  const ancho = (id) => parseFloat(dd.getElementById(id).style.width) || 0;
  ok("hay dos barras de avance",
     !!dd.getElementById("avLamina") && !!dd.getElementById("avTotal"));
  const lamAntes = ancho("avLamina"), totAntes = ancho("avTotal");
  clic(ps()[ps().length - 1]);
  await dormir(250);
  ok("la barra de la lamina avanza al recorrer sus parrafos",
     ancho("avLamina") > lamAntes, ancho("avLamina") + " frente a " + lamAntes);
  ok("y se llena entera en el ultimo parrafo", ancho("avLamina") === 100,
     "" + ancho("avLamina"));
  ok("va por numero de parrafo, no por peso del texto",
     Math.abs(ancho("avLamina") - 100 * (actual() + 1) / ps().length) < 0.2,
     ancho("avLamina") + " con " + (actual() + 1) + " de " + ps().length);
  ok("la barra del deck tambien avanza, pero poco",
     ancho("avTotal") > totAntes && ancho("avTotal") - totAntes < 20,
     ancho("avTotal") + " frente a " + totAntes);
  ok("y no se sale de la escala", ancho("avTotal") > 0 && ancho("avTotal") <= 100,
     "" + ancho("avTotal"));

  await dormir(250);
  // El apuntador muestra lo que falta de guion en minutos enteros, a proposito:
  // es una estimacion y no tiene sentido fingir precision. Recorrer los parrafos
  // de una lamina puede consumir menos de medio minuto, asi que en un deck largo
  // el numero redondea igual antes y despues. Aqui solo se exige que no suba. La
  // bajada de verdad la comprueba avTotal, dos lineas mas arriba, que va sin
  // redondear. Antes esta prueba exigia una bajada estricta y fallaba segun el
  // largo del deck, no segun el comportamiento del apuntador.
  const faltaDespues = parseInt(dd.getElementById("guion").textContent, 10);
  ok("avanzar parrafos no aumenta lo que le queda al guion", faltaDespues <= faltaAntes,
     faltaDespues + " frente a " + faltaAntes);

  pTecla("ArrowDown");
  await dormir(400);
  ok("abajo en el ultimo parrafo pasa a la lamina siguiente",
     Reveal.getCurrentSlide().dataset.sid !== P.sid, Reveal.getCurrentSlide().dataset.sid);
  ok("y el cursor empieza por el primer parrafo", actual() === 0, "i=" + actual());
  pTecla("ArrowUp");
  await dormir(350);
  ok("arriba en el primero vuelve a la lamina anterior",
     Reveal.getCurrentSlide().dataset.sid === P.sid, Reveal.getCurrentSlide().dataset.sid);
  ok("y se coloca en su ultimo parrafo", actual() === ps().length - 1,
     actual() + " de " + ps().length);

  falso.prompt = () => "09:00-11:00";
  dd.dispatchEvent(new KeyboardEvent("keydown", { key: "h", bubbles: true }));
  await dormir(300);
  ok("H cambia el horario de la clase",
     dd.getElementById("pos").textContent.includes("09:00 a 11:00"),
     dd.getElementById("pos").textContent);

  // ---- alarmas a hora de reloj
  const hm = (atras) => {
    const f = new Date(Date.now() - atras);
    return ("0" + f.getHours()).slice(-2) + ":" + ("0" + f.getMinutes()).slice(-2);
  };
  const guardadas = () => { try { return JSON.parse(localStorage.getItem("apuntador:alarmas") || "[]"); }
                            catch (e) { return []; } };
  const filas = () => [...dd.querySelectorAll("#alLista .al")];
  const avisos = () => [...dd.querySelectorAll("#aviso div")];
  const evento = (tipo) => new (dd.defaultView || window).Event(tipo, { bubbles: true });
  try { localStorage.removeItem("apuntador:alarmas"); } catch (e) {}

  pTecla("a");
  await dormir(200);
  ok("A abre el panel de alarmas", dd.body.classList.contains("editando"));
  ok("y arranca sin ninguna", !!dd.querySelector("#alLista .alVacio") && filas().length === 0,
     filas().length);
  clic(dd.getElementById("alMas"));
  await dormir(200);
  ok("el boton añade una alarma", filas().length === 1, filas().length);
  ok("con una hora de reloj ya puesta",
     /^\d\d:\d\d$/.test(filas()[0].querySelector(".alH").value),
     filas()[0].querySelector(".alH").value);
  ok("y con los sonidos a elegir",
     filas()[0].querySelectorAll(".alS option").length >= 4,
     filas()[0].querySelectorAll(".alS option").length);

  const horaVieja = hm(3600000);
  filas()[0].querySelector(".alH").value = horaVieja;
  filas()[0].querySelector(".alT").value = "Receso";
  filas()[0].querySelector(".alS").value = "timbre";
  filas()[0].querySelector(".alT").dispatchEvent(evento("input"));
  await dormir(200);
  ok("la alarma se guarda con su hora, su nombre y su sonido",
     guardadas().length === 1 && guardadas()[0].h === horaVieja &&
     guardadas()[0].t === "Receso" && guardadas()[0].s === "timbre",
     JSON.stringify(guardadas()));

  // escribir en el panel no puede mover el guion por debajo
  const parrAntes = actual();
  const campo = filas()[0].querySelector(".alT");
  campo.focus();
  campo.dispatchEvent(new KeyboardEvent("keydown",
    { key: "ArrowDown", bubbles: true, cancelable: true }));
  await dormir(200);
  ok("escribir en el panel no mueve el parrafo en curso", actual() === parrAntes,
     actual() + " frente a " + parrAntes);
  campo.blur();

  pTecla("Escape");
  await dormir(200);
  ok("Escape cierra el panel", !dd.body.classList.contains("editando"));

  // tres alarmas: una de hace diez minutos, la de la hora en curso y una futura
  try {
    localStorage.setItem("apuntador:alarmas", JSON.stringify([
      { h: hm(600000), t: "Alarma vieja", s: "ninguno" },
      { h: hm(0), t: "Receso", s: "ninguno" },
      { h: hm(-1800000), t: "Cierre", s: "ninguno" },
    ]));
  } catch (e) {}
  await dormir(1400);
  ok("la alarma de la hora en curso se dispara", avisos().length === 1, avisos().length);
  ok("y muestra el texto de la alarma",
     avisos().length === 1 && avisos()[0].querySelector("b").textContent === "Receso",
     avisos().length ? avisos()[0].textContent : "sin aviso");
  ok("la de hace diez minutos no resucita",
     !avisos().some((x) => x.textContent.includes("vieja")));
  ok("y el borde destella",
     dd.getElementById("destello").classList.contains("destella"));
  ok("el pie anuncia la siguiente y cuanto falta",
     /Cierre/.test(dd.getElementById("prox").textContent) &&
     /\d+ min/.test(dd.getElementById("prox").textContent),
     dd.getElementById("prox").textContent);
  await dormir(1300);
  ok("y no vuelve a sonar en el siguiente tictac", avisos().length === 1, avisos().length);
  clic(avisos()[0]);
  await dormir(200);
  ok("el clic cierra el aviso", avisos().length === 0, avisos().length);

  pTecla("a");
  await dormir(200);
  ok("el panel lista las alarmas guardadas, ordenadas por hora",
     filas().length === 3 &&
     filas().map((f) => f.querySelector(".alH").value).join() ===
       filas().map((f) => f.querySelector(".alH").value).sort().join(),
     filas().map((f) => f.querySelector(".alH").value).join(" "));
  clic(filas()[0].querySelector(".alX"));
  await dormir(200);
  ok("quitar borra la alarma, del panel y del disco",
     filas().length === 2 && guardadas().length === 2,
     filas().length + " en el panel, " + guardadas().length + " guardadas");
  clic(dd.getElementById("alFin"));
  await dormir(200);
  ok("el boton cerrar tambien cierra el panel", !dd.body.classList.contains("editando"));
  pTecla("Escape");
  await dormir(150);

  // 14b. alarmas que cruzan la medianoche
  // Una hora de reloj no dice de qué día es. Esto mueve el reloj de la página a
  // un día y una hora fijos, en vez de esperar a que den las once de la noche,
  // para probar los dos lados del cruce sin depender de cuándo se corra.
  const RelojReal = Date;
  function fijarReloj(dias, hh, mm, ss) {
    const f = new RelojReal();
    const blanco = new RelojReal(f.getFullYear(), f.getMonth(), f.getDate() + dias,
                                 hh, mm, ss, 0).getTime();
    const salto = blanco - f.getTime();
    const D = function (...a) {
      return a.length ? new RelojReal(...a) : new RelojReal(RelojReal.now() + salto);
    };
    D.prototype = RelojReal.prototype;
    D.now = () => RelojReal.now() + salto;
    D.parse = RelojReal.parse;
    D.UTC = RelojReal.UTC;
    window.Date = D;
  }
  const soltarReloj = () => { window.Date = RelojReal; };
  const ponAlarmas = (v) => {
    try { localStorage.setItem("apuntador:alarmas", JSON.stringify(v)); } catch (e) {}
  };
  const cuantos = (txt) => avisos().filter((x) => x.textContent.includes(txt)).length;
  const pie = () => dd.getElementById("prox").textContent;

  try {
    // a) son las 23:39 y hay una alarma a las 00:03: el pie tiene que anunciarla.
    // La magnitud importa tanto como el nombre: si se resolviera contra el día
    // equivocado saldrian 1464 min en vez de 24.
    fijarReloj(0, 23, 39, 0);
    ponAlarmas([{ h: "00:03", t: "Cierre nocturno", s: "ninguno" }]);
    await dormir(1400);
    ok("el pie anuncia la alarma de despues de medianoche",
       /Cierre nocturno/.test(pie()), pie() || "(pie vacio)");
    ok("y cuenta los minutos que faltan hasta ella, no las horas de ayer",
       /\\b24 min\\b/.test(pie()), pie() || "(pie vacio)");

    // b) pero el pie no se asoma más allá: a media tarde, la alarma de la mañana
    // siguiente está a casi un día y no se anuncia, que si no el pie se pasaría
    // la tarde entera con una cuenta de cuatro cifras de minutos
    fijarReloj(0, 15, 0, 0);
    ponAlarmas([{ h: "08:55", t: "Aviso de la manana", s: "ninguno" }]);
    await dormir(1400);
    ok("a media tarde el pie no anuncia la alarma de manana", pie() === "",
       pie() || "(pie vacio)");

    // c) el disparo a través de la medianoche, en dos tiempos, que es la única
    // forma de ejercitar el control de duplicados: primero suena a las 23:59:30
    // y después se cruza la medianoche, donde no debe volver a sonar.
    // Los márgenes son estrechos a propósito y conviene saberlo: la gracia son
    // 90 s, y a las 00:00:02 la alarma de las 23:59 lleva 62 s, o sea que la
    // prueba tolera 28 s de atasco de la máquina antes de fallar sin motivo.
    avisos().forEach((x) => x.remove());
    fijarReloj(0, 23, 59, 30);
    ponAlarmas([
      { h: "23:59", t: "Nocturna", s: "ninguno" },
      { h: "23:56", t: "Cuatro minutos antes", s: "ninguno" },
    ]);
    await dormir(1400);
    ok("la alarma de las 23:59 suena a las 23:59:30",
       cuantos("Nocturna") === 1,
       avisos().map((x) => x.textContent).join(" | ") || "(sin aviso)");
    fijarReloj(1, 0, 0, 2);
    await dormir(1400);
    ok("y pasada la medianoche sigue sonada, no vuelve a sonar",
       cuantos("Nocturna") === 1,
       avisos().map((x) => x.textContent).join(" | ") || "(sin aviso)");
    // la de las 23:56 queda a 4 min del reloj nuevo, fuera de la gracia: sirve de
    // tope, para que ampliar la ventana o soltar la gracia no pase inadvertido
    ok("y la que quedo fuera de la gracia no suena al cruzar",
       cuantos("Cuatro minutos antes") === 0,
       avisos().map((x) => x.textContent).join(" | ") || "(sin aviso)");

    // d) y una que nadie habia oido todavia: puesta ya cruzada la medianoche,
    // su hora es la de ayer y tiene que sonar igual. Es el disparo que el
    // apuntador se comia entero antes del arreglo.
    ponAlarmas([{ h: "23:59", t: "Madrugada", s: "ninguno" }]);
    await dormir(1400);
    ok("una alarma de anoche sin sonar todavia suena pasada la medianoche",
       cuantos("Madrugada") === 1,
       avisos().map((x) => x.textContent).join(" | ") || "(sin aviso)");
  } finally {
    soltarReloj();
    ponAlarmas([]);
    avisos().forEach((x) => x.remove());
  }
  ok("la prueba devuelve el reloj de verdad al terminar",
     Math.abs(Date.now() - RelojReal.now()) < 1000,
     Date.now() - RelojReal.now() + " ms de desfase");
  await dormir(150);

  // 15. recorte en vivo: el panel, el plan y el guion corto en la ventana
  Reveal.slide(secs.indexOf(sec));
  await dormir(350);
  pTecla("c");
  await dormir(300);
  ok("C abre el panel de recorte en el apuntador", dd.body.classList.contains("recortando"));
  const filasRec = () => [...dd.querySelectorAll(".recF")];
  const filaDe = (r) => filasRec().find((f) =>
    f.querySelector("button[data-sid]").dataset.sid === (r.dataset.sid || r.id));
  ok("el panel lista las laminas que el deck marca",
     filasRec().length === 3, "filas=" + filasRec().length);
  ok("la primera fila es la lamina en curso, aunque sea nucleo",
     filasRec()[0].classList.contains("aqui") && /núcleo/.test(filasRec()[0].textContent),
     filasRec()[0].textContent);
  ok("y se puede abreviar a mano si tiene guion corto",
     !!filaDe(sec).querySelector('button[data-rec="corta"][disabled]'),
     "el deck no le puso aside.corto, asi que corta va deshabilitado");
  ok("y distingue la que tiene guion corto de la que no",
     /sin corto/.test(filaDe(recB).textContent) && !/sin corto/.test(filaDe(recA).textContent),
     filasRec().map((f) => f.textContent).join(" | "));
  ok("arranca apagado",
     dd.querySelector('#recModo button[data-modo="0"]').classList.contains("on"));
  ok("y con el panel abierto los relojes se siguen viendo",
     parseInt(getComputedStyle(dd.getElementById("pie")).zIndex, 10) >
       parseInt(getComputedStyle(dd.getElementById("recorte")).zIndex, 10) &&
     parseFloat(dd.getElementById("recorte").style.paddingBottom) > 0,
     "pie=" + getComputedStyle(dd.getElementById("pie")).zIndex +
     " panel=" + getComputedStyle(dd.getElementById("recorte")).zIndex +
     " hueco=" + dd.getElementById("recorte").style.paddingBottom);
  ok("y entonces no recorta nada",
     filasRec().every((f) => !f.classList.contains("plan")),
     filasRec().map((f) => f.className).join(" | "));

  const guionRec = () => parseInt(dd.getElementById("guion").textContent, 10);
  const antesRec = guionRec();
  // la clase se acaba en dos minutos: hay que recortar todo lo que se pueda
  const dosDig = (n) => ("0" + n).slice(-2);
  const hhmm2 = (d) => dosDig(d.getHours()) + ":" + dosDig(d.getMinutes());
  ok("apagado, el panel dice cuánto devolvería encenderlo",
     /^Sin recortar nada/.test(dd.getElementById("recResumen").textContent) &&
     /devuelven hasta/.test(dd.getElementById("recResumen").textContent),
     dd.getElementById("recResumen").textContent);

  // Fuera del horario de la clase el retraso son las horas que hace que terminó,
  // y no significa nada. El panel lo dice en vez de dar un número absurdo. En la
  // primera hora del día el horario de hace rato cae en el día anterior y la
  // comprobación no aplica, así que ahí se da por buena.
  const hace = (min) => new Date(Date.now() - min * 60000);
  const mismoDia = hace(90).getDate() === new Date().getDate();
  localStorage.setItem("apuntador:horario", hhmm2(hace(180)) + "-" + hhmm2(hace(90)));
  await dormir(1300);
  ok("fuera del horario, el panel avisa de que es un ensayo",
     !mismoDia || /ensayo/.test(dd.getElementById("recEstado").textContent),
     dd.getElementById("recEstado").textContent);

  localStorage.setItem("apuntador:horario",
    hhmm2(new Date()) + "-" + hhmm2(new Date(Date.now() + 120000)));
  clic(dd.querySelector('#recModo button[data-modo="1"]'));
  await dormir(400);
  ok("con solo el nivel 1 encendido, el plan no toca la de nivel 2",
     filaDe(recA).classList.contains("plan") && !filaDe(recB).classList.contains("plan"),
     filasRec().map((f) => f.className).join(" | "));
  ok("ni la de nucleo en la que se esta",
     !filaDe(sec).classList.contains("plan"), filaDe(sec).className);
  clic(dd.querySelector('#recModo button[data-modo="2"]'));
  await dormir(400);
  ok("la frase lleva el modo elegido y su propia holgura",
     /^Recortando los niveles 1 y 2 irías tarde /.test(
       dd.getElementById("recResumen").textContent) &&
     /y sin recortar nada /.test(dd.getElementById("recResumen").textContent),
     dd.getElementById("recResumen").textContent.slice(0, 110));
  ok("con los dos niveles encendidos entran las dos",
     filaDe(recA).classList.contains("plan") && filaDe(recB).classList.contains("plan"),
     filasRec().map((f) => f.textContent).join(" | "));
  ok("y lo que falta de guion baja", guionRec() < antesRec,
     guionRec() + " frente a " + antesRec);
  ok("la cabecera del panel dice cómo va la clase, no el recorte",
     /la clase (termina en|terminó hace)|sin horario/.test(
       dd.getElementById("recEstado").textContent),
     dd.getElementById("recEstado").textContent);
  ok("el modo se recuerda en disco",
     (JSON.parse(localStorage.getItem("apuntador:recorte:" + __DECK__) || "{}")).modo === 2,
     localStorage.getItem("apuntador:recorte:" + __DECK__));

  // fijar una lamina a mano: el plan la respeta
  clic(filaDe(recA).querySelector('button[data-rec="corta"]'));
  await dormir(400);
  ok("fijar una lamina a corta la deja abreviada",
     /abreviada/.test(filaDe(recA).textContent), filaDe(recA).textContent);
  ok("y el boton queda marcado",
     filaDe(recA).querySelector('button[data-rec="corta"]').classList.contains("on"));
  clic(filaDe(recB).querySelector('button[data-rec="fuera"]'));
  await dormir(400);
  ok("y fijar la otra a fuera la deja fuera",
     /fuera/.test(filaDe(recB).textContent), filaDe(recB).textContent);
  pTecla("c");
  await dormir(250);
  ok("C vuelve a cerrar el panel", !dd.body.classList.contains("recortando"));

  Reveal.slide(secs.indexOf(recA));
  await dormir(400);
  ok("en la lamina abreviada el apuntador lee el guion corto",
     dd.getElementById("texto").textContent.includes("Version corta de esta lamina"),
     dd.getElementById("texto").textContent.slice(0, 70));
  ok("y lo avisa con su banderin",
     /Guion corto/.test(dd.getElementById("rec").textContent),
     dd.getElementById("rec").textContent);
  Reveal.slide(secs.indexOf(recB));
  await dormir(400);
  ok("en la que se salta el banderin lo dice",
     /Saltar/.test(dd.getElementById("rec").textContent) &&
     dd.getElementById("rec").classList.contains("fuera"),
     dd.getElementById("rec").textContent);
  ok("y avisa de que hay que decirselo al grupo, por ser nivel 2",
     /retoma/.test(dd.getElementById("rec").textContent),
     dd.getElementById("rec").textContent);
  pTecla("ArrowDown");
  await dormir(400);
  ok("la flecha abajo no la recorre, pasa a la siguiente",
     Reveal.getCurrentSlide() !== recB, (Reveal.getCurrentSlide() || {}).dataset.sid);

  // se deja como estaba, que lo que viene detras no es de recorte. Hay que
  // volver antes a una lamina anterior: el panel solo lista lo que queda por dar.
  Reveal.slide(secs.indexOf(sec));
  await dormir(350);
  pTecla("c");
  await dormir(250);
  clic(filaDe(recA).querySelector('button[data-rec="auto"]'));
  await dormir(250);
  clic(filaDe(recB).querySelector('button[data-rec="auto"]'));
  await dormir(250);
  clic(dd.querySelector('#recModo button[data-modo="0"]'));
  await dormir(250);
  pTecla("c");
  await dormir(200);
  localStorage.setItem("apuntador:horario", "09:00-11:00");
  await dormir(350);
  ok("apagado y sin nada fijado, el banderin desaparece",
     !dd.getElementById("rec").textContent.trim(),
     dd.getElementById("rec").textContent);

  // si el navegador ofrece ventana sin barra de direcciones, esa manda
  const marcoPip = document.createElement("iframe");
  document.body.appendChild(marcoPip);
  const pip = { closed: false, document: marcoPip.contentDocument, focus() {}, close() {},
                scrollTo() {}, addEventListener() {}, prompt: () => null, innerHeight: 620 };
  Object.defineProperty(window, "documentPictureInPicture",
    { value: { requestWindow: () => Promise.resolve(pip) }, configurable: true });
  // V alterna de clase de ventana y cierra la actual
  dd.dispatchEvent(new KeyboardEvent("keydown", { key: "v", bubbles: true, cancelable: true }));
  await dormir(200);
  ok("V cambia la clase de ventana",
     localStorage.getItem("apuntador:flotante") === "1",
     localStorage.getItem("apuntador:flotante"));
  falso.closed = true;
  tecla("t", 84);
  await dormir(500);
  ok("y entonces se abre la ventana sin barra",
     !!pip.document.getElementById("texto"));
  ok("y le inyecta el estilo y el guion",
     !!pip.document.querySelector("style") &&
     pip.document.getElementById("texto").textContent.length > 20,
     (pip.document.getElementById("texto") || {}).textContent);

  clic(dg().querySelector('#rvAcc button[data-rv="revertir-guion"]'));
  await dormir(400);
  ok("revertir descarta la reescritura", !guiones()[P.sid]);
  ok("y vuelve el guion del deck",
     dg().getElementById("texto").textContent.replace(/\\s+/g, " ")
       .includes(P.citaG.slice(0, 25)),
     dg().getElementById("texto").textContent.slice(0, 50));

  tecla("g", 71);
  await dormir(250);
  ok("y G cierra la ventana del guion", !abiertaG());

  // 14. el aside original queda intacto: el PDF y el apuntador no se enteran
  ok("los aside.notes quedan intactos", !document.querySelector(".slides aside.notes mark.rv-hl"));
 } catch (e) { R.push("FALLA  excepcion: " + e.message); }
 const div = document.createElement("div");
 div.id = "diag";
 div.textContent = R.join(" ;; ");
 document.body.appendChild(div);
})();
</script>
"""

def main():
    p = pathlib.Path(RUTA).resolve()
    if not p.exists():
        print("no existe " + str(p)); return 1
    s = p.read_text(encoding="utf-8")
    m = re.search(r'<script src="[^"]*revisar\.js"></script>', s)
    if not m:
        print("el deck no carga revisar.js"); return 1
    deck = json.dumps(p.parent.name)
    s = s.replace(m.group(0),
                  SEMILLA.replace("__DECK__", deck) + m.group(0) + PRUEBA.replace("__DECK__", deck))
    tmp = p.with_name("_prueba.html")
    tmp.write_text(s, encoding="utf-8")
    # El resueltas.js tiene que estar en el disco, junto al deck, porque lo que se
    # prueba es justamente que un file:// pueda cargar el de al lado. Toma sus
    # datos de la semilla, así no hay que repetir aquí los ids de las láminas.
    res = p.with_name("resueltas.js")
    guardado = res.read_text(encoding="utf-8") if res.exists() else None
    res.write_text("/* archivo de prueba: lo escribe y lo borra tools/prueba-revisar.py */\n"
                   "window.RV_RESUELTAS = window.__RESUELTAS_PRUEBA || null;\n", encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="rv-perfil-")   # desechable, no pisa las notas reales
    try:
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--allow-file-access-from-files", "--user-data-dir=" + perfil,
                            "--virtual-time-budget=60000", "--dump-dom",
                            "file://" + str(tmp) + "?review"],
                           capture_output=True, text=True, timeout=120)
        d = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
        salida = d.group(1) if d else "(no se pudo medir)  " + r.stderr[-800:]
    finally:
        if tmp.exists(): os.unlink(tmp)
        if guardado is None: res.unlink(missing_ok=True)
        else: res.write_text(guardado, encoding="utf-8")
        shutil.rmtree(perfil, ignore_errors=True)
    lineas = [x.strip() for x in salida.split(";;")]
    print("\n".join(lineas))
    malas = [x for x in lineas if x.startswith("FALLA")]
    print("%d de %d fallan" % (len(malas), len(lineas)) if malas
          else "las %d pruebas del anotador y el apuntador pasan" % len(lineas))
    return 1 if malas or "no se pudo medir" in salida else 0

if __name__ == "__main__":
    sys.exit(main())
