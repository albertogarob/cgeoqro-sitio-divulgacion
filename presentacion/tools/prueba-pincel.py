#!/usr/bin/env python3
"""Prueba de regresión del pincel del tema.

    python3 tools/prueba-pincel.py [sesiones/SNN-.../index.html]

Abre el deck en Chrome headless, sin ?review, porque el pincel es para dar la
clase y no para revisar, y comprueba lo que de verdad importa del trazo:

  - que la tecla D lo enciende y lo apaga, que Escape lo apaga sin abrir la
    vista general de reveal, y que apagado no estorba, o sea que el lienzo
    vuelve a pointer-events:none;
  - que el lápiz pinta, y del color elegido en la barra;
  - que la presión modula el ancho: el mismo grosor con presión alta deja un
    trazo más gordo que con presión baja;
  - que la punta de borrar borra, que Deshacer quita solo el último trazo, y
    que Limpiar deja la lámina en blanco;
  - que Ctrl+Z deshace igual que el botón, que no deshace con Shift, con Alt, con
    la tecla de Mac ni con el pincel apagado, que a media pincelada quita el
    trazo en curso, y que con el foco en una caja de texto no se queda con la
    tecla, porque ahí es de quien escribe;
  - que lo que se apoya con la mano no pinta, o sea que pointerType touch se
    ignora, y que el ratón pinta pero sin modular por presión, que no la tiene,
    y con el botón derecho no pinta;
  - que un trazo no se queda abierto: ni al cambiar de lámina con el lápiz
    apoyado, ni cuando un segundo lápiz empieza otro encima;
  - que cada lámina guarda sus trazos y los recupera al volver;
  - y que el trazo queda anclado a la lámina: al cambiar la escala, que es lo
    que pasa al redimensionar la ventana, al entrar en pantalla completa y al
    compartir pantalla en Zoom, la tinta sigue en la misma coordenada de lámina.

Las medidas se toman leyendo los píxeles del lienzo, no el estado interno del
script: si el trazo no se ve, la prueba falla aunque los datos estén bien.

Corre con un perfil de Chrome desechable, y no toca nada del disco: el pincel
no guarda trazos en ninguna parte.
"""
import re, subprocess, sys, pathlib, os, tempfile, shutil

RUTA = sys.argv[1] if len(sys.argv) > 1 else "sesiones/S01-presentacion-del-curso-y-evaluacion/index.html"

PRUEBA = r"""
<script>
(async function () {
 const R = [];
 const ok = (n, c, extra) => R.push((c ? "OK   " : "FALLA") + "  " + n + (extra !== undefined && !c ? "  [" + extra + "]" : ""));
 const dormir = (ms) => new Promise((r) => setTimeout(r, ms));
 const tecla = (k, code) => document.dispatchEvent(new KeyboardEvent("keydown",
   { key: k, keyCode: code, which: code, bubbles: true, cancelable: true }));
 const ctrlZ = (extra, destino) => (destino || document).dispatchEvent(
   new KeyboardEvent("keydown",
     Object.assign({ key: "z", keyCode: 90, which: 90, ctrlKey: true,
                     bubbles: true, cancelable: true }, extra || {})));
 const clic = (el) => el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
 const lienzo = () => document.querySelector(".pn-lienzo");
 const barra = () => document.querySelector(".pn-barra");
 const activo = () => document.body.classList.contains("pn-activo");

 // -- lectura del lienzo, en coordenadas de lámina -------------------------
 const punto = (x, y) => {
   const c = lienzo();
   const d = c.getContext("2d").getImageData(
     Math.min(c.width - 1, Math.max(0, Math.round(x / 1280 * c.width))),
     Math.min(c.height - 1, Math.max(0, Math.round(y / 720 * c.height))), 1, 1).data;
   return [d[0], d[1], d[2], d[3]];
 };
 const tinta = (x, y) => punto(x, y)[3] > 20;
 // píxeles pintados en una columna de 80 unidades de lámina: el espesor del trazo
 const espesor = (x, y) => {
   const c = lienzo();
   const cx = Math.round(x / 1280 * c.width);
   const y0 = Math.max(0, Math.round((y - 40) / 720 * c.height));
   const y1 = Math.min(c.height, Math.round((y + 40) / 720 * c.height));
   const d = c.getContext("2d").getImageData(cx, y0, 1, y1 - y0).data;
   let n = 0;
   for (let i = 3; i < d.length; i += 4) if (d[i] > 20) n++;
   return n;
 };

 // -- el lápiz de la tableta, sintético ------------------------------------
 const evento = (tipo, x, y, extra) => {
   const c = lienzo();
   const r = c.getBoundingClientRect();
   const base = { bubbles: true, cancelable: true, pointerId: 7, pointerType: "pen",
                  isPrimary: true, button: 0, buttons: 1, pressure: 0.5,
                  clientX: r.left + x / 1280 * r.width,
                  clientY: r.top + y / 720 * r.height };
   c.dispatchEvent(new PointerEvent(tipo, Object.assign(base, extra || {})));
 };
 // Un trazo recto de (x1,y1) a (x2,y2), en n muestras, con la presión y los
 // botones que se le pasen. Así se imita lo que manda la Wacom.
 const trazar = (x1, y1, x2, y2, extra, n) => {
   n = n || 8;
   evento("pointerdown", x1, y1, extra);
   for (let i = 1; i <= n; i++) {
     evento("pointermove", x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n, extra);
   }
   evento("pointerup", x2, y2, Object.assign({ buttons: 0, pressure: 0 }, extra || {}));
 };
 const boton = (que) => barra().querySelector('button[data-pn="' + que + '"]');
 const swatch = (v) => barra().querySelector('button[data-pn="color"][data-valor="' + v + '"]');
 const punta = (v) => barra().querySelector('button[data-pn="grosor"][data-valor="' + v + '"]');

 try {
  while (!window.Reveal || !Reveal.isReady()) await dormir(100);
  await dormir(400);

  // 1. antes de la tecla D no existe nada: el pincel no se monta solo
  ok("apagado no monta ni lienzo ni barra", !lienzo() && !barra() && !activo());

  // 2. la tecla D lo enciende
  tecla("d", 68);
  await dormir(150);
  ok("la tecla D enciende el pincel", activo() && !!lienzo() && !!barra());
  ok("y el lienzo recibe el lápiz",
     lienzo() && getComputedStyle(lienzo()).pointerEvents === "auto",
     lienzo() && getComputedStyle(lienzo()).pointerEvents);
  ok("y la barra se ve", barra() && getComputedStyle(barra()).display === "flex",
     barra() && getComputedStyle(barra()).display);
  const caja = getComputedStyle(lienzo());
  ok("la caja del lienzo mide la lámina, no la ventana",
     caja.width === "1280px" && caja.height === "720px",
     caja.width + "x" + caja.height);
  ok("y su mapa de píxeles va con la escala de reveal",
     Math.abs(lienzo().width - 1280 * Reveal.getScale() * Math.min(devicePixelRatio || 1, 2)) <= 2,
     lienzo().width + " con escala " + Reveal.getScale());

  // 3. el lápiz pinta, y del color de fábrica, que es el guinda institucional
  trazar(200, 200, 500, 200);
  ok("el lápiz pinta", tinta(350, 200));
  const c0 = punto(350, 200);
  ok("y del guinda de la plantilla", c0[0] > 130 && c0[0] < 200 && c0[1] < 90 && c0[2] < 110,
     c0.join(","));

  // 4. la presión modula el ancho, con el grosor como techo
  clic(punta("13"));
  await dormir(60);
  trazar(200, 300, 500, 300, { pressure: 1 });
  trazar(200, 400, 500, 400, { pressure: 0.1 });
  const gordo = espesor(350, 300), flaco = espesor(350, 400);
  ok("la presión alta deja trazo más gordo que la baja", gordo > flaco * 1.5,
     "gordo " + gordo + " flaco " + flaco);
  ok("y el grosor grueso pesa más que el fino",
     gordo > espesor(350, 200), "grueso " + gordo + " medio " + espesor(350, 200));

  // 5. la mano apoyada no pinta
  trazar(700, 500, 1000, 500, { pointerType: "touch" });
  ok("pointerType touch no pinta", !tinta(850, 500));

  // 6. el color se cambia en la barra
  clic(swatch("#111111"));
  await dormir(60);
  ok("el swatch elegido queda marcado",
     swatch("#111111").getAttribute("aria-pressed") === "true" &&
     swatch("#A42145").getAttribute("aria-pressed") === "false");
  trazar(200, 500, 500, 500, { pressure: 1 });
  const c1 = punto(350, 500);
  ok("y el trazo sale de ese color", c1[0] < 60 && c1[1] < 60 && c1[2] < 60, c1.join(","));

  // 7. la punta de borrar borra, y Deshacer devuelve lo borrado
  trazar(200, 500, 500, 500, { buttons: 32, button: 5, pressure: 1 });
  ok("la punta de borrar borra lo que hay debajo", !tinta(350, 500));
  clic(boton("deshacer"));
  await dormir(80);
  ok("Deshacer quita el último trazo, que era el borrado", tinta(350, 500));
  clic(boton("deshacer"));
  await dormir(80);
  ok("y otra vez quita el trazo negro", !tinta(350, 500));
  ok("sin tocar los anteriores", tinta(350, 200) && tinta(350, 300));

  // 8. el borrador de la barra, que es el mismo trazo en modo quitar
  clic(boton("borrador"));
  await dormir(60);
  ok("el botón Borrador queda marcado", boton("borrador").getAttribute("aria-pressed") === "true");
  trazar(200, 300, 500, 300, { pressure: 1 });
  ok("y borra sin necesidad de la punta", !tinta(350, 300));
  clic(swatch("#A42145"));
  await dormir(60);
  ok("elegir color suelta el borrador", boton("borrador").getAttribute("aria-pressed") === "false");

  // 9. cada lámina guarda lo suyo
  const suyo = tinta(350, 200);
  Reveal.next();
  await dormir(250);
  ok("al pasar de lámina el lienzo queda en blanco", !tinta(350, 200));
  trazar(800, 200, 1100, 200, { pressure: 1 });
  ok("y se puede dibujar en la nueva", tinta(950, 200));
  Reveal.prev();
  await dormir(250);
  ok("al volver reaparece lo de esa lámina", tinta(350, 200) === suyo && tinta(350, 200));
  ok("y no se cuela lo de la otra", !tinta(950, 200));

  // 10. el trazo queda anclado a la lámina, no a la ventana
  const antes = { escala: Reveal.getScale(), ancho: lienzo().width };
  const viewport = document.querySelector(".reveal-viewport") || document.body;
  viewport.style.width = "760px";
  Reveal.layout();
  await dormir(250);
  ok("al cambiar la escala cambia el mapa de píxeles",
     Reveal.getScale() !== antes.escala && lienzo().width !== antes.ancho,
     "escala " + antes.escala + " a " + Reveal.getScale());
  ok("y la tinta sigue en la misma coordenada de lámina", tinta(350, 200));
  ok("y no aparece donde nunca se dibujó", !tinta(350, 650));
  viewport.style.width = "";
  Reveal.layout();
  await dormir(250);
  ok("y al volver a la escala de antes también", tinta(350, 200));

  // 11. Limpiar deja la lámina en blanco, y solo esa
  clic(boton("limpiar"));
  await dormir(80);
  ok("Limpiar deja la lámina en blanco",
     !tinta(350, 200) && !tinta(350, 400) && !tinta(350, 500));
  Reveal.next();
  await dormir(250);
  ok("y no se lleva los trazos de la otra lámina", tinta(950, 200));
  Reveal.prev();
  await dormir(250);

  // 11b. el ratón dibuja sin modular por presión, y su botón derecho no pinta
  trazar(600, 100, 900, 100, { pointerType: "mouse", pressure: 1 });
  trazar(600, 150, 900, 150, { pointerType: "mouse", pressure: 0.1 });
  const m1 = espesor(750, 100), m2 = espesor(750, 150);
  ok("el ratón pinta", m1 > 0 && m2 > 0, m1 + " y " + m2);
  ok("y no modula por presión, que el ratón no la tiene",
     Math.abs(m1 - m2) <= 2, "presión 1 da " + m1 + " y presión 0.1 da " + m2);
  trazar(600, 200, 900, 200, { pointerType: "mouse", button: 2, buttons: 2 });
  ok("el botón derecho del ratón no pinta", !tinta(750, 200));

  // 11c. cambiar de lámina con el lápiz apoyado
  evento("pointerdown", 200, 250, { pressure: 1 });
  evento("pointermove", 400, 250, { pressure: 1 });
  Reveal.next();
  await dormir(250);
  evento("pointermove", 600, 250, { pressure: 1 });
  evento("pointerup", 600, 250, { buttons: 0, pressure: 0 });
  ok("cambiar de lámina a media pincelada no pinta en la nueva", !tinta(500, 250));
  Reveal.prev();
  await dormir(250);
  ok("y lo trazado antes se queda en la lámina donde empezó", tinta(300, 250));

  // 11d. un segundo lápiz en mitad del trazo, o un pointerId reasignado. Que el
  // primero se cierre en vez de quedarse abierto no se ve en los píxeles, así
  // que lo que se comprueba aquí es lo que sí se ve: que los dos trazos salen y
  // que son dos entradas distintas de la pila, no una.
  clic(boton("limpiar"));
  await dormir(80);
  evento("pointerdown", 200, 600, { pressure: 1 });
  evento("pointermove", 400, 600, { pressure: 1 });
  evento("pointerdown", 700, 600, { pointerId: 9, pressure: 1 });
  evento("pointermove", 900, 600, { pointerId: 9, pressure: 1 });
  evento("pointerup", 900, 600, { pointerId: 9, buttons: 0, pressure: 0 });
  ok("un segundo lápiz dibuja su trazo sin perder el anterior",
     tinta(300, 600) && tinta(800, 600));
  clic(boton("deshacer"));
  await dormir(80);
  ok("y Deshacer quita solo el segundo, o sea que son dos trazos",
     tinta(300, 600) && !tinta(800, 600));
  clic(boton("limpiar"));
  await dormir(80);

  // 11e. Ctrl+Z deshace, lo mismo que el botón
  trazar(200, 650, 400, 650, { pressure: 1 });
  trazar(600, 650, 800, 650, { pressure: 1 });
  ok("dos trazos puestos para deshacer", tinta(300, 650) && tinta(700, 650));
  ctrlZ();
  await dormir(80);
  ok("Ctrl+Z deshace el último trazo", tinta(300, 650) && !tinta(700, 650));
  ctrlZ();
  await dormir(80);
  ok("y repetido deshace el anterior", !tinta(300, 650));
  ctrlZ();
  await dormir(80);
  ok("Ctrl+Z sobre la lámina vacía no rompe nada", !tinta(300, 650) && activo());
  // Ctrl+Shift+Z no es rehacer, así que no debe tocar nada, ni deshacer de más
  trazar(200, 650, 400, 650, { pressure: 1 });
  ctrlZ({ shiftKey: true });
  await dormir(80);
  ok("Ctrl+Shift+Z no deshace", tinta(300, 650));
  ctrlZ({ altKey: true });
  await dormir(80);
  ok("Ctrl+Alt+Z tampoco, que en muchos teclados es AltGr", tinta(300, 650));
  // Solo Ctrl, que es lo que se pidió: la tecla de Mac no deshace
  ctrlZ({ ctrlKey: false, metaKey: true });
  await dormir(80);
  ok("Cmd+Z no deshace, el atajo es solo con Ctrl", tinta(300, 650));
  // Con el foco en una caja de texto la tecla es de quien escribe, no del pincel
  const campo = document.createElement("textarea");
  document.body.appendChild(campo);
  campo.focus();
  ctrlZ({}, campo);
  await dormir(80);
  ok("con el foco en un campo de texto, Ctrl+Z no toca los trazos", tinta(300, 650));
  const esc = new KeyboardEvent("keydown", { key: "Escape", keyCode: 27, which: 27,
                                             bubbles: true, cancelable: true });
  campo.dispatchEvent(esc);
  await dormir(80);
  ok("y Escape desde el campo no apaga el pincel, lo cierra quien lo abrió",
     activo() && !esc.defaultPrevented);
  campo.remove();
  document.body.focus();
  // y con el lápiz apoyado, deshacer quita el trazo en curso sin dejarlo abierto
  evento("pointerdown", 600, 650, { pressure: 1 });
  evento("pointermove", 800, 650, { pressure: 1 });
  ctrlZ();
  await dormir(80);
  ok("Ctrl+Z a media pincelada quita el trazo en curso",
     !tinta(700, 650) && tinta(300, 650));
  evento("pointermove", 900, 650, { pressure: 1 });
  evento("pointerup", 900, 650, { buttons: 0, pressure: 0 });
  ok("y lo que quedaba del trazo ya no pinta", !tinta(850, 650));

  // 12. apagar: con Escape, sin abrir la vista general, y con la tecla D.
  // El trazo de la lámina tiene que sobrevivir al apagado y a Ctrl+Z.
  tecla("Escape", 27);
  await dormir(200);
  ok("Escape apaga el pincel", !activo());
  ok("y no abre la vista general de reveal", !Reveal.isOverview());
  ok("y el lienzo deja de estorbar",
     getComputedStyle(lienzo()).pointerEvents === "none",
     getComputedStyle(lienzo()).pointerEvents);
  ok("la barra se esconde", getComputedStyle(barra()).display === "none");
  ctrlZ();
  await dormir(80);
  ok("y apagado Ctrl+Z no deshace nada", tinta(300, 650));
  trazar(600, 300, 900, 300, { pressure: 1 });
  ok("y apagado el lápiz no pinta", !tinta(750, 300));

  tecla("d", 68);
  await dormir(120);
  ok("la tecla D vuelve a encender", activo());
  tecla("d", 68);
  await dormir(120);
  ok("y la tecla D apaga", !activo());

  // 13. el botón Salir
  tecla("d", 68);
  await dormir(120);
  clic(boton("salir"));
  await dormir(120);
  ok("el botón Salir apaga", !activo());

  // 14. la vista general apaga el pincel y esconde el lienzo
  tecla("d", 68);
  await dormir(120);
  Reveal.toggleOverview(true);
  await dormir(400);
  ok("la vista general apaga el pincel", !activo());
  ok("y esconde el lienzo, que no seguiría a las láminas",
     lienzo().classList.contains("pn-oculto"));
  Reveal.toggleOverview(false);
  await dormir(400);
  ok("y al salir de ella el lienzo vuelve", !lienzo().classList.contains("pn-oculto"));

  // 15. el deck no se toca: ni el guion ni las láminas se enteran del pincel
  ok("el lienzo vive dentro de .slides, anclado a la lámina",
     lienzo().parentElement === document.querySelector(".reveal .slides"));
  ok("y no se cuela como una lámina más",
     document.querySelectorAll(".reveal .slides > section").length ===
     Reveal.getTotalSlides(),
     document.querySelectorAll(".reveal .slides > section").length + " de " + Reveal.getTotalSlides());
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
    m = re.search(r'<script src="[^"]*pincel\.js"></script>', s)
    if not m:
        print("el deck no carga pincel.js"); return 1
    s = s[:m.end()] + PRUEBA + s[m.end():]
    tmp = p.with_name("_prueba-pincel.html")
    tmp.write_text(s, encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="pn-perfil-")
    try:
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--allow-file-access-from-files", "--user-data-dir=" + perfil,
                            "--window-size=1400,800",
                            "--virtual-time-budget=60000", "--dump-dom",
                            "file://" + str(tmp)],
                           capture_output=True, text=True, timeout=120)
        d = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
        salida = d.group(1) if d else "(no se pudo medir)  " + r.stderr[-800:]
    finally:
        if tmp.exists(): os.unlink(tmp)
        shutil.rmtree(perfil, ignore_errors=True)
    lineas = [x.strip() for x in salida.split(";;")]
    print("\n".join(lineas))
    malas = [x for x in lineas if x.startswith("FALLA")]
    print("%d de %d fallan" % (len(malas), len(lineas)) if malas
          else "las %d pruebas del pincel pasan" % len(lineas))
    return 1 if malas or "no se pudo medir" in salida else 0


if __name__ == "__main__":
    sys.exit(main())
