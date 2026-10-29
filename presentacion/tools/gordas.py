#!/usr/bin/env python3
"""Caza las láminas gordas de texto, midiendo en el navegador.

Alberto marcó 26 láminas de la sesión 12 con una sola palabra, "gorda", y pidió
la política: **prohibidas las láminas gordas en texto**. Este script es lo que
la hace exigible, porque una política sin medidor se olvida a la sesión
siguiente.

**Qué mide, y por qué en el navegador.** El largo de una viñeta no se puede
contar en caracteres: depende de la tipografía, de las negritas y, sobre todo,
de las expresiones que compone MathJax, que ocupan mucho más ancho que su
LaTeX. Así que se mide el alto renderizado de cada pieza en Chrome, lámina por
lámina, con el deck cargado de verdad.

**El criterio, medido el 13 de octubre de 2026 y no supuesto:**

  * **Ninguna viñeta pasa de dos líneas.** Es el corte que de verdad importa.
    A este cuerpo caben unos 45 caracteres por línea, así que una viñeta de
    tres líneas lleva texto de sobra y hay que partirla o recortarla.
  * **Como mucho 3 viñetas**, más la línea de motivación. La fórmula no
    cuenta, que no es grasa de texto sino el contenido de la lámina.
  * **El texto entero no pasa de 7 líneas en una lámina con dibujo**, video o
    código, ni de 8 en una de texto solo.

**Cuidado con las unidades, que costaron una medición entera.** El alto de una
viñeta dividido por la altura de renglón del cuerpo NO da el número de líneas:
una viñeta de una línea mide 0.8 y una de dos mide 1.6. El factor es 0.8, y
leer 1.6 como "un renglón y poco" deja pasar justo lo que se quería cazar.

**Qué queda fuera.** La portada, los separadores de sección, la agenda, el
repaso de la sesión anterior, el cierre, la de agradecimiento y la de
bibliografía. Son láminas estructurales: su largo es su función, no grasa. La
lista se declara en EXENTAS y por `data-sin-tope` en el `<section>`.

**Una trampa que costó tres mediciones.** Buscar un dibujo con
`querySelector('svg')` da falso positivo en casi toda lámina: MathJax compone
cada expresión como un `<svg>`, y el globo de una parcela lleva dentro la
rejilla del terreno, también en SVG. Hay que descontar los que viven dentro de
un `mjx-container` o de un `.gl-pop`.

Uso:

    python3 tools/gordas.py sesiones/SNN-.../index.html
    python3 tools/gordas.py sesiones/SNN-.../index.html --todas

Sin `--todas` solo lista las que se pasan. Devuelve 1 si queda alguna.
"""

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

# Láminas estructurales: su largo es su función.
EXENTAS = {
    "portada", "lo-que-veremos-hoy", "donde-quedamos", "lo-que-queda-de-hoy",
    "que-sigue", "bibliografia", "gracias", "cierre",
}

TOPE_VINETAS = 3
TOPE_LINEAS_CON_DIBUJO = 7
TOPE_LINEAS_SIN_DIBUJO = 8
TOPE_LINEAS_VINETA = 2
# Una línea de viñeta mide 0.8 veces la altura de renglón del cuerpo, medido
# en Chrome el 13 de octubre de 2026 contra capturas de la sesión 12.
POR_LINEA = 0.8

SONDA = r"""<script>
window.addEventListener('load', function(){ setTimeout(async function(){
  var out=[];
  var secs=[].slice.call(document.querySelectorAll('.reveal .slides > section'));
  for (var i=0;i<secs.length;i++){
    var s=secs[i];
    if (s.querySelector('section')) continue;
    Reveal.slide(i);
    await new Promise(function(r){setTimeout(r,90)});
    var cu=s.querySelector('.cuerpo');
    if(!cu) continue;
    var lh=parseFloat(getComputedStyle(cu).lineHeight)||32;
    // Un dibujo de verdad, descontando los SVG que pone MathJax por cada
    // expresion y la rejilla que vive dentro del globo de una parcela.
    var dib=[].slice.call(cu.querySelectorAll('svg,pre,video')).some(function(e){
      return !e.closest('mjx-container') && !e.closest('.gl-pop');
    });
    var lineas=0, vinetas=0, largas=[];
    [].slice.call(cu.querySelectorAll('li, p.motiva, p.formula')).forEach(function(e){
      if(e.classList.contains('formula')) return;   // la fórmula es contenido
      var n=Math.max(1, Math.round(e.getBoundingClientRect().height/lh/POR_LINEA));
      lineas+=n;
      if(e.tagName.toLowerCase()==='li'){
        vinetas++;
        if(n>TOPE_LINEAS_VINETA) largas.push([n, e.textContent.trim().slice(0,56)]);
      }
    });
    out.push({sid:s.getAttribute('data-sid')||s.id,
              lineas:lineas, vinetas:vinetas,
              dib:dib, largas:largas,
              exenta:s.hasAttribute('data-sin-tope')});
  }
  var d=document.createElement('div'); d.id='diag'; d.textContent=JSON.stringify(out);
  document.body.appendChild(d);
}, 1800)});
</script>"""


def medir(deck):
    """Carga el deck en Chrome headless y devuelve la medida de cada lámina."""
    sonda = (SONDA.replace("TOPE_LINEAS_VINETA", repr(TOPE_LINEAS_VINETA))
                  .replace("POR_LINEA", repr(POR_LINEA)))
    tmp = deck.with_name("_gordas.html")
    tmp.write_text(deck.read_text(encoding="utf8").replace("</body>", sonda + "</body>"),
                   encoding="utf8")
    perfil = tempfile.mkdtemp(prefix="gordas-")
    try:
        r = subprocess.run(
            ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
             "--allow-file-access-from-files", "--user-data-dir=" + perfil,
             "--window-size=1280,720", "--virtual-time-budget=40000",
             "--dump-dom", "file://" + str(tmp)],
            capture_output=True, text=True, timeout=300)
        m = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
        if not m:
            sys.exit("gordas.py: Chrome no devolvió la medida. ¿Está instalado?")
        return json.loads(m.group(1))
    finally:
        tmp.unlink(missing_ok=True)
        shutil.rmtree(perfil, ignore_errors=True)


def tope_lineas(x):
    return TOPE_LINEAS_CON_DIBUJO if x["dib"] else TOPE_LINEAS_SIN_DIBUJO


def faltas(x):
    """Lista en prosa lo que esta lámina incumple. Vacía si cumple."""
    if x["sid"] in EXENTAS or x["exenta"]:
        return []
    mal = []
    for n, t in x["largas"]:
        mal.append("viñeta de %d líneas: %s" % (n, t))
    if x["vinetas"] > TOPE_VINETAS:
        mal.append("%d viñetas, el tope es %d" % (x["vinetas"], TOPE_VINETAS))
    tl = tope_lineas(x)
    if x["lineas"] > tl:
        mal.append("%d líneas de texto, el tope es %d%s"
                   % (x["lineas"], tl, " con dibujo" if x["dib"] else ""))
    return mal


def main():
    ap = argparse.ArgumentParser(description="Caza las láminas gordas de texto.")
    ap.add_argument("deck", help="sesiones/SNN-.../index.html")
    ap.add_argument("--todas", action="store_true",
                    help="lista también las que cumplen")
    a = ap.parse_args()

    deck = pathlib.Path(a.deck).resolve()
    if not deck.exists():
        sys.exit("gordas.py: no existe %s" % a.deck)

    medidas = medir(deck)
    gordas = [(x, faltas(x)) for x in medidas]
    malas = [(x, f) for x, f in gordas if f]

    if a.todas:
        print("%-48s %4s %7s %4s" % ("lámina", "dib", "líneas", "viñ"))
        for x in sorted(medidas, key=lambda y: -y["lineas"]):
            print("%-48s %4s %7d %4d %s"
                  % (x["sid"], "sí" if x["dib"] else "", x["lineas"], x["vinetas"],
                     "" if not faltas(x) else "GORDA"))
        print()

    for x, f in sorted(malas, key=lambda y: -y[0]["lineas"]):
        print("%s" % x["sid"])
        for linea in f:
            print("   %s" % linea)

    exentas = sum(1 for x in medidas if x["sid"] in EXENTAS or x["exenta"])
    print("gordas.py: %d láminas gordas, de %d medidas (%d exentas)"
          % (len(malas), len(medidas), exentas))
    if malas:
        print("   Ninguna viñeta pasa de dos líneas, y como mucho 3 viñetas "
              "por lámina.")
        return 1
    print("   NINGUNA LÁMINA GORDA DE TEXTO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
