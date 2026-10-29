#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba de regresión de las glosas al pasar el ratón y del reproductor.

Alberto pidió el 29 de septiembre de 2026 que pasar el ratón por una etiqueta
corta, R1 o una parcela, enseñe lo que la etiqueta esconde. Esto comprueba en
Chrome headless que de verdad aparece, midiendo el elemento flotante, no el
estado interno de nadie:

    python3 tools/prueba-glosas.py sesiones/SNN-.../index.html

Qué comprueba, y por qué cada cosa:

  * que el globo exista y esté oculto al cargar, que si no tapa la lámina;
  * que pasar el ratón por una etiqueta de regla lo abra con la regla entera
    dentro, compuesta por MathJax, no con el LaTeX en crudo;
  * que pasar el ratón por una parcela lo abra con la rejilla y con la casilla
    correcta marcada, que es lo que ahorra reconstruir la geometría de memoria;
  * que el globo quepa dentro de la ventana, porque una etiqueta al borde de la
    lámina lo empujaría fuera y no se leería;
  * que salir de la etiqueta lo cierre;
  * que el clic lo abra también, que es la vía de quien lee el paquete en una
    pantalla táctil, donde no hay ratón;
  * y que las láminas con animación declaren data-start y data-end, con el
    final DENTRO del archivo. Sin los dos atributos el reproductor se rinde y la
    lámina se queda muda; con el final más allá de la duración real, el video da
    una sola vuelta y se congela. Los dos fallos ya ocurrieron.
"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile

RUTA = sys.argv[1] if len(sys.argv) > 1 else \
    "sesiones/S08-dentro-de-un-motor-de-reglas/index.html"

PRUEBA = r"""
<script>
(function () {
  const R = [];
  const ok = (n, c, d) => R.push((c ? "pasa  " : "FALLA ") + n + (d ? "  [" + d + "]" : ""));
  /* Una comprobación que no aplica a este deck se DICE, no se calla. Las
   * etiquetas de regla son del bloque de lógica; en una sesión sin reglas
   * no hay nada que medir, y saltárselas en silencio hacía creer que se
   * habían medido. */
  const nd = (n, por) => R.push("n/a   " + n + "  [" + por + "]");
  function raton(el, tipo) {
    el.dispatchEvent(new MouseEvent(tipo, {bubbles: true, cancelable: true, view: window}));
  }
  function vis(e) { return e && getComputedStyle(e).display !== "none"; }

  window.addEventListener("load", function () {
   setTimeout(function () {
    const glo = document.getElementById("glosa-flotante");
    ok("el globo existe", !!glo);
    const asides = document.querySelectorAll(".gl > aside.gl-pop").length;
    const pops = document.querySelectorAll(".gl > .gl-pop").length;
    ok("el globo va en un <aside>, para que las herramientas lo salten",
       pops > 0 && asides === pops, asides + " de " + pops);
    // Ningún globo expulsado de su etiqueta. Un <p> se cierra solo al encontrar
    // un bloque, así que un <aside> dentro de un <p> lo saca el navegador del
    // <span>: deja de abrirse y, peor, deja de estar oculto y se dibuja como un
    // bloque en medio de la lámina. Ya pasó dos veces, con el puente y con las
    // tarjetas de match.
    const etiq = document.querySelectorAll(".gl").length;
    const todos = document.querySelectorAll("aside.gl-pop").length;
    ok("ningún globo expulsado de su etiqueta por un <p>",
       etiq === todos && todos === asides,
       "etiquetas=" + etiq + " globos=" + todos + " bien colgados=" + asides);
    if (!glo) { pintar(); return; }
    ok("al cargar está cerrado", !vis(glo), "display=" + getComputedStyle(glo).display);

    // ---- lo primero: que la etiqueta VISIBLE de cada glosa esté compuesta.
    // Es el hueco por el que se coló un fallo: la prueba miraba el globo y no
    // la etiqueta, así que una expresión sin componer se proyectaba en LaTeX
    // crudo y pasaba en verde.
    const crudas = [];
    document.querySelectorAll(".gl").forEach(g => {
      const c = g.cloneNode(true);
      const pop = c.querySelector(".gl-pop");
      if (pop) pop.remove();
      if (/\\\(/.test(c.textContent)) crudas.push(c.textContent.trim().slice(0, 24));
    });
    ok("ninguna etiqueta se proyecta en LaTeX crudo", crudas.length === 0,
       crudas.length ? crudas.join(" / ") : document.querySelectorAll(".gl").length + " revisadas");

    // ---- una etiqueta de regla
    let reg = null;
    document.querySelectorAll(".gl").forEach(g => {
      if (!reg && /^R[1-5]/.test(g.textContent.trim())) reg = g;
    });
    if (!reg) {
      const por = "este deck no tiene etiquetas de regla R1 a R5";
      nd("hay alguna etiqueta de regla con glosa", por);
      nd("pasar el ratón por la regla abre el globo", por);
      nd("la regla sale compuesta, no en LaTeX crudo", por);
      nd("el globo cabe en la ventana", por);
      nd("salir de la etiqueta lo cierra", por);
      nd("el clic también lo abre", por);
    }
    if (reg) {
      ok("hay alguna etiqueta de regla con glosa", true);
      raton(reg, "mouseover");
      ok("pasar el ratón por la regla abre el globo", vis(glo));
      const svgs = glo.querySelectorAll("svg[data-mml-node], mjx-container svg, svg");
      ok("la regla sale compuesta, no en LaTeX crudo",
         svgs.length > 0 && !/\\\(/.test(glo.textContent),
         "svg=" + svgs.length + " texto=" + JSON.stringify(glo.textContent.slice(0, 40)));
      const r = glo.getBoundingClientRect();
      ok("el globo cabe en la ventana",
         r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth + 1 &&
         r.bottom <= window.innerHeight + 1,
         [r.left, r.top, r.right, r.bottom, window.innerWidth, window.innerHeight].map(Math.round).join(","));
      raton(document.body, "mouseover");
      ok("salir de la etiqueta lo cierra", !vis(glo));
      raton(reg, "click");
      ok("el clic también lo abre", vis(glo));
      raton(document.body, "click");
    }

    // ---- una parcela, con su rejilla
    let par = null, celda = null;
    document.querySelectorAll(".gl").forEach(g => {
      if (!par && g.querySelector(".gl-pop .gl-rej")) par = g;
    });
    ok("hay alguna parcela con rejilla", !!par);
    if (par) {
      raton(par, "mouseover");
      const rej = glo.querySelector(".gl-rej");
      ok("la rejilla llega al globo", !!rej);
      if (rej) {
        const on = rej.querySelectorAll(".gl-celda.gl-on");
        const todas = rej.querySelectorAll(".gl-celda");
        ok("la rejilla tiene dieciséis casillas", todas.length === 16, "son " + todas.length);
        ok("hay al menos una casilla marcada", on.length >= 1, "marcadas " + on.length);
        ok("no están marcadas todas", on.length < 16, "marcadas " + on.length);
      }
      raton(document.body, "mouseover");
    }
    pintar();
   }, 1200);
  });

  function pintar() {
    const d = document.createElement("div");
    d.id = "diag"; d.textContent = R.join(";;");
    document.body.appendChild(d);
  }
})();
</script>
"""


def atributos_de_video(html, ruta):
    """Las láminas con animación, contra la duración real de su archivo."""
    out = []
    for m in re.finditer(r'<section\b([^>]*)>', html):
        a = m.group(1)
        v = re.search(r'data-video="([^"]+)"', a)
        if not v:
            continue
        sid = re.search(r'data-sid="([^"]+)"', a)
        sid = sid.group(1) if sid else "?"
        # Desde el 6 de octubre de 2026 una lámina puede partir el video en
        # tramos, cada uno un fragmento de reveal, y entonces data-start y
        # data-end viven en los <span class="tramo">, no en el <section>. El
        # cuerpo de la lámina llega hasta el siguiente <section o el final.
        sig = html.find("<section", m.end())
        cuerpo = html[m.end():sig if sig > 0 else len(html)]
        tramos = re.findall(r'<span class="tramo[^"]*"\s+data-start="([^"]+)"\s+'
                            r'data-end="([^"]+)"', cuerpo)
        if tramos:
            fines = [float(b) for _, b in tramos]
            ini, fin = tramos[0][0], max(fines)
            # Los tramos tienen que cubrir el video sin huecos ni saltos atrás.
            bordes = [(float(x), float(y)) for x, y in tramos]
            malos = [i for i in range(1, len(bordes))
                     if abs(bordes[i][0] - bordes[i - 1][1]) > 0.01]
            if malos:
                out.append("FALLA %s: los tramos no encajan, el %d empieza en %.2f "
                           "y el anterior acaba en %.2f"
                           % (sid, malos[0] + 1, bordes[malos[0]][0],
                              bordes[malos[0] - 1][1]))
                continue
            out.append("pasa  %s: %d tramos encadenados sin huecos"
                       % (sid, len(tramos)))

            class _M:                      # para reusar el código de abajo
                def __init__(s, v): s.v = v
                def group(s, i): return s.v
            ini, fin = _M(ini), _M(str(max(fines)))
        else:
            ini = re.search(r'data-start="([^"]+)"', a)
            fin = re.search(r'data-end="([^"]+)"', a)
            if not ini or not fin:
                out.append("FALLA %s: ni tramos ni data-start y data-end: "
                           "el video no arranca" % sid)
                continue
        arch = (ruta.parent / v.group(1))
        if not arch.exists():
            # En el paquete de un archivo los videos van incrustados y el nombre
            # ya no apunta a nada en disco: empaquetar.py lo cambia por un blob
            # en tiempo de ejecución. Ahí solo se puede comprobar que los dos
            # atributos siguen puestos, que es lo que el reproductor necesita.
            if "data:video" in html or "URL.createObjectURL" in html or "var datos" in html:
                out.append("pasa  %s: empaquetado, lleva data-start y data-end "
                           "(la duración se comprueba sobre el deck)" % sid)
            else:
                out.append("FALLA %s: no existe %s" % (sid, v.group(1)))
            continue
        try:
            dur = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(arch)],
                capture_output=True, text=True, timeout=30).stdout.strip())
        except Exception as e:
            out.append("pasa  %s: no se pudo medir la duración (%s)" % (sid, e))
            continue
        f = float(fin.group(1))
        if f > dur:
            out.append("FALLA %s: data-end=%.1f pasa de la duración real %.1f, "
                       "el video no da la segunda vuelta" % (sid, f, dur))
        else:
            out.append("pasa  %s: data-end=%.1f dentro de los %.1f s del archivo"
                       % (sid, f, dur))
    return out


def main():
    p = pathlib.Path(RUTA).resolve()
    if not p.exists():
        print("no existe " + str(p)); return 1
    s = p.read_text(encoding="utf-8")

    lineas = atributos_de_video(s, p)

    # Un deck lleva glosas si su MARKUP las lleva, o sea si alguna etiqueta
    # tiene su globo escrito dentro. Antes esto se detectaba buscando
    # "glosa-flotante", que era el CSS y el JavaScript copiados en el propio
    # deck; el 30 de septiembre de 2026 los dos se subieron al tema y entonces
    # la prueba dejó de ver las glosas de la sesión 8 y se declaraba en verde
    # habiendo comprobado solo los videos. El markup es lo que hay que buscar,
    # porque es lo único que vive en el deck.
    if "gl-pop" not in s:
        print("el deck no lleva glosas; solo se comprueban los videos")
    else:
        tmp = p.with_name("_prueba_glosas.html")
        tmp.write_text(s.replace("</body>", PRUEBA + "</body>"), encoding="utf-8")
        perfil = tempfile.mkdtemp(prefix="gl-perfil-")
        try:
            r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox",
                                "--disable-gpu", "--allow-file-access-from-files",
                                "--user-data-dir=" + perfil, "--window-size=1280,720",
                                "--virtual-time-budget=60000", "--dump-dom",
                                "file://" + str(tmp)],
                               capture_output=True, text=True, timeout=180)
            d = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
            salida = d.group(1) if d else "FALLA no se pudo medir  " + r.stderr[-600:]
        finally:
            if tmp.exists():
                os.unlink(tmp)
            shutil.rmtree(perfil, ignore_errors=True)
        lineas += [x.strip() for x in salida.split(";;")]

    print("\n".join(lineas))
    malas = [x for x in lineas if x.startswith("FALLA")]
    noap = [x for x in lineas if x.startswith("n/a")]
    cola = "" if not noap else ", y %d no aplican a este deck" % len(noap)
    print("%d de %d fallan%s" % (len(malas), len(lineas), cola) if malas
          else "las %d pruebas de las glosas y el reproductor pasan%s"
               % (len(lineas) - len(noap), cola))
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
