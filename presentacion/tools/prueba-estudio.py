#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba de regresión del lector de estudio, el de la tecla I.

    python3 tools/prueba-estudio.py [sesiones/SNN-.../index.html]

Mide en Chrome headless, no el estado interno de nadie. Qué comprueba, y por qué
cada cosa:

  * QUE LA NOTA DIDÁCTICA NO SE PROYECTE. Es la primera y la más importante: el
    bloque va oculto por una regla propia del tema, y si esa regla falta, el
    texto con el que Alberto estudia aparece en la lámina delante del grupo. Se
    comprueba con la lámina EN PANTALLA, porque las demás están en display:none
    por obra de reveal y ahí cualquier cosa parece oculta. Se descubrió que
    hacía falta el 1 de octubre de 2026, borrando la regla a propósito: ninguna
    prueba del proyecto se enteró.
  * que la tecla I abra el panel y que se vea de verdad, midiendo su caja.
  * que la lámina SE ENCOJA en vez de taparse, que es lo que permite leer el
    texto y mirar el dibujo a la vez.
  * que el panel enseñe los dos bloques con su rótulo, el mío y el del grupo:
    ese rótulo es la única señal en pantalla de qué se queda conmigo.
  * que las expresiones matemáticas lleguen compuestas y no en LaTeX crudo.
  * que cambiar de lámina cambie el texto, y que una lámina sin notas lo diga.
  * que la sesión de corrido liste todas las láminas con nota y que pinchar una
    lleve a su diapositiva.
  * que Escape cierre y devuelva la lámina a su ancho.
  * LA VENTANA APARTE, con window.open sustituida por un documento suelto. Es
    el camino
    que más fácilmente se rompe, porque MathJax solo trabaja en el documento
    donde vive: el texto se compone en este documento y se importa al otro ya
    hecho. Si eso se estropea, en la ventana se lee el LaTeX en crudo.
  * que la elección entre panel y ventana se recuerde.

La sesión de prueba se siembra sobre el deck que se le pase: se le añaden dos
notas didácticas y, si no lo carga, el propio lector. Nada de eso toca el
archivo original, que se copia a un temporal al lado y se borra al terminar.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

RUTA = sys.argv[1] if len(sys.argv) > 1 else \
    "sesiones/S09-logica-difusa-y-control-difuso/index.html"

NOTA_CON_MATES = (
    '<aside class="didactica"><p>Nota didactica de prueba, la que solo veo yo. '
    "La parcela \\(\\mathrm{Par}(1,1)\\), la de la esquina de entrada, es el "
    "punto de partida.</p></aside>"
)
NOTA_SIMPLE = (
    '<aside class="didactica"><p>Segunda nota didactica de prueba, sin '
    "matematicas.</p></aside>"
)

PRUEBA = r"""
<script>
(function () {
  const R = [];
  const ok = (n, c, d) => R.push((c ? "pasa  " : "FALLA ") + n +
    (d !== undefined && d !== null && d !== "" ? "  [" + d + "]" : ""));
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const caja = (e) => (e ? e.getBoundingClientRect() : { width: 0, height: 0 });
  const vis = (e) => {
    if (!e) return false;
    const s = getComputedStyle(e);
    return s.display !== "none" && s.visibility !== "hidden" && caja(e).width > 1;
  };
  const tecla = (k, code) => document.dispatchEvent(new KeyboardEvent("keydown",
    { key: k, keyCode: code, which: code, bubbles: true, cancelable: true }));
  const laminas = () => [...document.querySelectorAll(".reveal .slides > section")];
  const crudo = (t) => /\\\(|\\\[/.test(t || "");

  /* El div de resultados se arma con el DOM y no con una cadena: si el texto
     literal del marcador apareciera aquí, --dump-dom lo devolvería también como
     parte del <script> y el regex de main() encontraría ESE y no el de verdad.
     Pasó en el primer intento: la prueba imprimió el código fuente de pintar. */
  function pintar() {
    const d = document.createElement("div");
    d.id = "diag";
    d.textContent = R.join(";;");
    document.body.appendChild(d);
  }

  async function correr() {
    if (!window.estudio) {
      ok("el lector de estudio se carga", false, "window.estudio no existe");
      pintar();
      return;
    }
    ok("el lector de estudio se carga", true);

    const conNota = laminas()
      .map((s, i) => [s, i])
      .filter(([s]) => s.querySelector("aside.didactica"));
    ok("el deck de prueba trae notas didácticas sembradas",
       conNota.length >= 2, conNota.length + " láminas");
    if (!conNota.length) { pintar(); return; }

    /* ---- 1. que no se proyecte, que es lo único que no se puede fallar ---- */
    const [sec0, i0] = conNota[0];
    Reveal.slide(i0);
    await espera(400);
    const nota0 = sec0.querySelector("aside.didactica");
    ok("la lámina de la prueba está en pantalla",
       sec0.offsetHeight > 100, "alto=" + sec0.offsetHeight);
    ok("y su nota didáctica NO se proyecta",
       getComputedStyle(nota0).display === "none" && caja(nota0).height === 0,
       "display=" + getComputedStyle(nota0).display + " alto=" + caja(nota0).height);
    const apunte0 = sec0.querySelector("aside.apuntes");
    ok("ni el apunte de estudio, que tampoco se proyecta",
       !apunte0 || getComputedStyle(apunte0).display === "none",
       apunte0 ? getComputedStyle(apunte0).display : "la lámina no tiene apunte");

    /* ---- 2. el panel ---- */
    const anchoAntes = caja(document.querySelector(".reveal")).width;
    tecla("i", 73);
    await espera(500);
    const panel = document.querySelector(".es-panel");
    ok("la tecla I abre el panel", document.body.classList.contains("es-abierto"));
    ok("y el panel se ve de verdad, no solo en el DOM", vis(panel),
       "ancho=" + Math.round(caja(panel).width));
    const anchoDespues = caja(document.querySelector(".reveal")).width;
    ok("y la lámina se encoge en vez de taparse",
       anchoDespues > 100 && anchoDespues < anchoAntes - 200,
       Math.round(anchoAntes) + " -> " + Math.round(anchoDespues));

    const cuerpo = panel.querySelector(".es-cuerpo");
    ok("el panel trae la nota didáctica",
       /Nota didactica de prueba/.test(cuerpo.textContent));
    ok("y el apunte del grupo", /Apunte|apunte/.test(cuerpo.textContent) ||
       !apunte0, cuerpo.textContent.slice(0, 40));
    const marcas = [...cuerpo.querySelectorAll(".es-marca")];
    ok("los dos bloques van rotulados, el mío y el del grupo",
       marcas.length === (apunte0 ? 2 : 1) &&
       !!cuerpo.querySelector(".es-marca.es-mia"),
       marcas.map((m) => m.textContent.trim().slice(0, 18)).join(" / "));
    ok("el título dice en qué lámina estoy",
       /\S/.test(panel.querySelector(".es-tit").textContent),
       panel.querySelector(".es-tit").textContent.slice(0, 40));

    /* ---- 3. las matemáticas, compuestas y no en crudo ---- */
    const conMathJax = !!(window.MathJax && window.MathJax.typesetPromise);
    if (!conMathJax) {
      ok("las matemáticas del panel", true,
         "el deck no carga MathJax, no se puede medir");
    } else {
      ok("las expresiones del panel están compuestas",
         !!cuerpo.querySelector("mjx-container"),
         "mjx=" + cuerpo.querySelectorAll("mjx-container").length);
      ok("y no queda LaTeX sin componer en el panel", !crudo(cuerpo.textContent),
         cuerpo.textContent.slice(0, 60));
    }

    /* ---- 4. seguir a la lámina ---- */
    const [, i1] = conNota[1];
    Reveal.slide(i1);
    await espera(400);
    ok("cambiar de lámina cambia el texto",
       /Segunda nota didactica/.test(cuerpo.textContent),
       cuerpo.textContent.slice(0, 40));

    const sinNada = laminas().findIndex(
      (s) => !s.querySelector("aside.didactica") && !s.querySelector("aside.apuntes"));
    if (sinNada >= 0) {
      Reveal.slide(sinNada);
      await espera(400);
      ok("una lámina sin notas lo dice en vez de quedarse en blanco",
         !!cuerpo.querySelector(".es-vacio"), cuerpo.textContent.slice(0, 40));
    } else {
      ok("una lámina sin notas lo dice en vez de quedarse en blanco", true,
         "todas las láminas tienen nota, no se pudo probar");
    }

    /* ---- 5. toda la sesión de corrido ---- */
    const bTodo = panel.querySelector('[data-es="todo"]');
    bTodo.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await espera(600);
    const entradas = [...cuerpo.querySelectorAll(".es-doc h2")];
    const esperadas = laminas().filter(
      (s) => s.querySelector("aside.didactica") || s.querySelector("aside.apuntes")).length;
    ok("la sesión de corrido lista todas las láminas con nota",
       entradas.length === esperadas, entradas.length + " de " + esperadas);
    ok("y el botón ofrece la vuelta a la lámina",
       /Solo esta lámina/.test(bTodo.textContent), bTodo.textContent);
    if (entradas.length) {
      entradas[entradas.length - 1].dispatchEvent(new MouseEvent("click", { bubbles: true }));
      await espera(500);
      const quieta = laminas().indexOf(Reveal.getCurrentSlide());
      ok("pinchar una entrada lleva a su diapositiva",
         !cuerpo.querySelector(".es-doc") && quieta >= 0,
         "lámina " + (quieta + 1));
    }

    /* ---- 6. cerrar ---- */
    tecla("Escape", 27);
    await espera(400);
    ok("Escape cierra el panel", !document.body.classList.contains("es-abierto"));
    ok("y la lámina recupera su ancho",
       caja(document.querySelector(".reveal")).width > anchoDespues + 200,
       Math.round(caja(document.querySelector(".reveal")).width));

    /* ---- 7. la ventana aparte, con window.open sustituida ---- */
    const abrirDeVerdad = window.open;
    let pedidas = 0;
    let falsa = null;
    // Un documento suelto, sin navegación. Con un iframe, Chrome headless se
    // queda esperando una carga que no termina y la prueba muere en el tiempo
    // máximo sin medir nada: ocurrió en el primer intento. Por eso el lector
    // escribe su ventana por el DOM y no con document.write.
    window.open = function () {
      pedidas++;
      falsa = {
        document: document.implementation.createHTMLDocument("ventana de prueba"),
        closed: false,
        outerWidth: 620, outerHeight: 860, screenX: 11, screenY: 22,
        focus() {}, scrollTo() {}, addEventListener() {},
        close() { this.closed = true; },
      };
      return falsa;
    };
    window.estudio.ponerModo("ventana");
    await espera(900);
    window.open = abrirDeVerdad;
    ok("el botón de ventana pide una ventana aparte", pedidas === 1, pedidas);
    if (falsa) {
      const d = falsa.document;
      const vTit = d.getElementById("tit"), vCuerpo = d.getElementById("cuerpo");
      ok("la ventana se escribe con su cabecera y su pie",
         !!vTit && !!vCuerpo && !!d.querySelector('[data-es="panel"]'));
      ok("la ventana trae el texto de la lámina",
         !!vCuerpo && /Nota didactica|Segunda nota|apunte|Apunte/.test(vCuerpo.textContent),
         vCuerpo ? vCuerpo.textContent.trim().slice(0, 40) : "sin cuerpo");
      ok("y sus bloques van rotulados",
         !!vCuerpo && vCuerpo.querySelectorAll(".es-marca").length >= 1,
         vCuerpo ? vCuerpo.querySelectorAll(".es-marca").length : 0);
      // El punto del ejercicio: MathJax vive en el documento de al lado, así que
      // esto solo pasa si el texto se compuso aquí y se importó ya hecho.
      const conMates = laminas()[conNota[0][1]];
      Reveal.slide(conNota[0][1]);
      await espera(900);
      if (!conMathJax) {
        ok("las matemáticas de la ventana", true,
           "el deck no carga MathJax, no se puede medir");
      } else {
        ok("la ventana recibe las matemáticas compuestas, no el LaTeX",
           !!vCuerpo && !!vCuerpo.querySelector("mjx-container") &&
           !crudo(vCuerpo.textContent),
           vCuerpo ? "mjx=" + vCuerpo.querySelectorAll("mjx-container").length +
             " texto=" + vCuerpo.textContent.trim().slice(0, 30) : "sin cuerpo");
      }
      ok("con la ventana abierta el panel no estorba",
         !document.body.classList.contains("es-abierto"));
      void conMates;
    }
    ok("la elección de ventana queda recordada",
       localStorage.getItem("estudio:modo") === "ventana",
       localStorage.getItem("estudio:modo"));
    window.estudio.ponerModo("panel");
    await espera(400);
    ok("y se puede volver al panel",
       document.body.classList.contains("es-abierto") &&
       localStorage.getItem("estudio:modo") === "panel",
       localStorage.getItem("estudio:modo"));

    pintar();
  }

  window.addEventListener("load", function () {
    // MathJax y reveal tardan en estar listos; sin esta espera la primera
    // medida sale antes de que haya nada que medir.
    setTimeout(function () { correr().catch(function (e) {
      ok("la prueba termina sin excepciones", false, String(e && e.message || e));
      pintar();
    }); }, 1500);
  });
})();
</script>
"""


def sembrar(fuente):
    """El deck de prueba: el original más dos notas didácticas y, si le falta, el
    lector. Se devuelve el HTML, no se escribe nada todavía."""
    s = fuente.read_text(encoding="utf-8")
    avisos = []

    # La configuración que llevarán las sesiones nuevas: con la clase excluida,
    # MathJax no compone el bloque al cargar y el lector tiene que componerlo él.
    # Es el camino difícil, y es el que hay que probar.
    if "ignoreHtmlClass:'apuntes|ficha'" in s:
        s = s.replace("ignoreHtmlClass:'apuntes|ficha'",
                      "ignoreHtmlClass:'apuntes|ficha|didactica'")
        avisos.append("se le puso la clase didactica a ignoreHtmlClass")

    if "estudio.js" not in s:
        m = re.search(r'src="([^"]*)apuntador\.js"', s)
        base = m.group(1) if m else "../../plantillas/tema-centrogeo/"
        s = s.replace("</body>", '<script src="%sestudio.js"></script>\n</body>'
                      % base, 1)
        avisos.append("se le añadió el lector, que el deck todavía no carga")

    # Las notas van en las dos primeras láminas que tengan título y apunte, para
    # que la prueba pueda comparar los dos bloques uno al lado del otro.
    puestas = [0]
    nota = [NOTA_CON_MATES, NOTA_SIMPLE]

    def repl(m):
        entero, attrs, cuerpo = m.group(0), m.group(1), m.group(2)
        if puestas[0] >= 2 or "<h2" not in cuerpo or 'class="apuntes"' not in cuerpo:
            return entero
        # La nota que ya tenga la lámina se SUSTITUYE en la copia temporal, en vez
        # de respetarla. Así el fixture es siempre el mismo y la prueba mide lo
        # mismo en un deck recién creado y en uno con sus cuarenta notas escritas.
        # Respetándola, en un deck ya anotado no se sembraba nada, la prueba
        # buscaba su propio texto de muestra, no lo encontraba, y caían cuatro
        # comprobaciones sin que el lector tuviera nada roto.
        cuerpo = re.sub(r'<aside class="didactica">.*?</aside>', "", cuerpo,
                        flags=re.S)
        texto = nota[puestas[0]]
        puestas[0] += 1
        return "<section" + attrs + ">" + cuerpo + texto + "</section>"

    s = re.sub(r"<section\b([^>]*)>(.*?)</section>", repl, s, flags=re.S)
    if puestas[0] < 2:
        avisos.append("OJO: solo se pudieron sembrar %d notas" % puestas[0])
    return s, avisos


def main():
    p = pathlib.Path(RUTA).resolve()
    if not p.exists():
        print("no existe " + str(p))
        return 1

    s, avisos = sembrar(p)
    for a in avisos:
        print("aviso: " + a)

    tmp = p.with_name("_prueba_estudio.html")
    tmp.write_text(s.replace("</body>", PRUEBA + "</body>", 1), encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="es-perfil-")
    try:
        r = corre_chrome(tmp, perfil)
    finally:
        if tmp.exists():
            os.unlink(tmp)
        shutil.rmtree(perfil, ignore_errors=True)

    if r is None:
        print("FALLA Chrome no devolvió el DOM en 240 segundos. Suele ser un "
              "bucle que no termina en el lector: medir con la consola.")
        return 1
    d = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
    salida = d.group(1) if d else "FALLA no se pudo medir  " + r.stderr[-700:]

    lineas = [x.strip() for x in salida.split(";;") if x.strip()]
    print("\n".join(lineas))
    malas = [x for x in lineas if x.startswith("FALLA")]
    print("%d de %d fallan" % (len(malas), len(lineas)) if malas
          else "las %d pruebas del lector de estudio pasan" % len(lineas))
    return 1 if malas else 0


def corre_chrome(tmp, perfil):
    """Devuelve None si Chrome no termina, que es lo que pasa cuando el lector
    entra en un bucle infinito: el primer intento de esta prueba murió así y la
    traza de Python no decía nada útil."""
    try:
        return subprocess.run(["google-chrome", "--headless=new", "--no-sandbox",
                            "--disable-gpu", "--allow-file-access-from-files",
                            "--user-data-dir=" + perfil, "--window-size=1280,720",
                            "--virtual-time-budget=60000", "--dump-dom",
                            "file://" + str(tmp)],
                          capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return None


if __name__ == "__main__":
    sys.exit(main())
