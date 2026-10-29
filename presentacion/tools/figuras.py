#!/usr/bin/env python3
"""¿A qué escala se dibuja cada figura, y se leen sus rótulos? Medido en Chrome.

    python3 tools/figuras.py sesiones/SNN-.../index.html
    python3 tools/figuras.py sesiones/SNN-.../index.html --todas

**Por qué existe.** Alberto lo pidió el 20 de octubre de 2026, al revisar la
sesión 15: "la figura está muy pequeña... revisa la política sobre figuras
pequeñas y láminas atiborradas con una figura y bullets y corrige toda la
presentación". Era la segunda vez: el 8 de octubre, en la sesión 12, un diagrama
se había renderizado al 29 % con sus rótulos de 21 px en 6 px, y lo cazó una
captura de pantalla porque **ninguna herramienta lo detectaba**. Esta es esa
herramienta.

**Qué mide, y por qué no se puede razonar.** El navegador escala un SVG por
`min(ancho disponible / ancho del viewBox, alto de la franja / alto del
viewBox)`, y en una lámina `cuerpo tira` casi siempre manda el alto. Así que un
viewBox cuadradito se encoge hasta que sus rótulos no se leen, sin desbordar
nada. Lo que decide la legibilidad es **la escala**, que es el cociente entre lo
que se dibuja y el viewBox, y lo que de verdad importa es **el tamaño en píxeles
al que queda el rótulo más pequeño**.

Los umbrales salen de lo que Alberto ya aceptó, no de una opinión:

  * **escala**: de 0.6 a 0.71 es la banda de los diagramas aceptados en la
    sesión 11. Por debajo de 0.5 no se lee.
  * **rótulo más pequeño**: 13 px proyectados es el suelo. Un rótulo de 21 px a
    escala 0.62 da 13, que es el caso bueno medido.
  * **proporción del viewBox**: entre 3.5 y 4 a 1 para una tira. Más cuadrado
    que 2.5 a 1 y el alto manda tanto que no hay escala que lo salve.

**Y la regla de arriba, que es la que se incumple:** si el dibujo no se ve, lo
que sobra es TEXTO, no dibujo. Primero se quitan viñetas y solo después se baja
la franja. Por eso el informe dice, al lado de cada figura, cuántas viñetas la
acompañan: una figura pequeña con tres viñetas es texto de sobra, no un dibujo
mal hecho.

Devuelve 1 si alguna figura queda por debajo del suelo.
"""
import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

# Qué revisa, además de la escala: que ningún rótulo quede encimado con otro ni
# sobre una caja que no es la suya. Añadido el 21 de octubre de 2026, después de
# que Alberto lo reportara dos veces en la misma ronda.
ESCALA_BUENA = 0.60        # la banda de los diagramas que Alberto aceptó
ESCALA_SUELO = 0.50        # por debajo de aquí no se lee proyectado
ROTULO_SUELO = 13.0        # píxeles del rótulo más pequeño, ya escalado
PROPORCION_MIN = 2.5       # más cuadrado que esto y el alto manda siempre

SONDA = """plugins:[RevealNotes]}).then(async()=>{
  await document.fonts.ready; await new Promise(r=>setTimeout(r,500));
  const out=[]; const secs=[...document.querySelectorAll('.slides > section')];
  for (let i=0;i<secs.length;i++){
    Reveal.slide(i); await new Promise(r=>setTimeout(r,140));
    const sec=secs[i];
    // Solo el svg que ES la figura de la lamina: hijo directo del cuerpo. Los
    // de MathJax tambien son svg, y viven dentro de un <p>.
    const svg=sec.querySelector('.cuerpo > svg');
    if(!svg) continue;
    const vb=(svg.getAttribute('viewBox')||'').trim().split(/\\s+/).map(Number);
    const r=svg.getBoundingClientRect();
    // La escala de verdad: lo dibujado entre el viewBox. Se toma el minimo de
    // los dos ejes, que es lo que el navegador aplica al preservar la relacion.
    // OJO: hay que dividir por la escala con la que reveal dibuja el deck. Sin
    // headless y sin esto, la medida sale un 20% baja y la herramienta pide
    // figuras mas grandes de lo necesario. La escala que la politica fija esta
    // en unidades del deck, el lienzo de 1280 por 720, no en pixeles de la
    // ventana: "rotulos de 21 px proyectados a 13" habla del font-size del CSS.
    const Z = (Reveal.getScale && Reveal.getScale()) || 1;
    const esc = (vb.length===4 && vb[2]>0 && vb[3]>0)
      ? Math.min(r.width/vb[2], r.height/vb[3])/Z : null;
    // El rotulo mas pequeno, ya escalado: es lo que de verdad se lee o no.
    let min=null;
    for (const t of svg.querySelectorAll('text')){
      if (!t.textContent.trim()) continue;
      const fs=parseFloat(getComputedStyle(t).fontSize);
      if (!fs) continue;
      const px=fs*(esc||1);
      if (min===null || px<min) min=px;
    }
    // --- ENCIMADOS DENTRO DEL DIBUJO ---------------------------------------
    // Ninguna otra herramienta ve esto: un rotulo encima de otro, o encima de
    // una caja que no es la suya, no desborda nada. Alberto lo reporto dos
    // veces el 21 de octubre de 2026, "este texto se encima a otro texto" y
    // "este texto se encima al dibujo".
    const TOL = 2;                 // unidades del viewBox que se toleran
    const txt = [...svg.querySelectorAll('text')].filter(t=>t.textContent.trim());
    const caja = e => { try { return e.getBBox(); } catch(_) { return null; } };
    const corta = (a,b) => a && b &&
      Math.min(a.x+a.width, b.x+b.width) - Math.max(a.x, b.x) > TOL &&
      Math.min(a.y+a.height, b.y+b.height) - Math.max(a.y, b.y) > TOL;
    const choques=[];
    const bb = txt.map(caja);
    for (let i=0;i<txt.length;i++) for (let j=i+1;j<txt.length;j++){
      if (corta(bb[i], bb[j]))
        choques.push('"'+txt[i].textContent.trim().slice(0,30)+'" con "'+
                     txt[j].textContent.trim().slice(0,30)+'"');
    }
    // Y un rotulo encima de una caja que no es la suya. El rotulo propio de una
    // caja va CENTRADO dentro de ella, asi que se reconoce por eso y no cuenta.
    for (let i=0;i<txt.length;i++){
      const a=bb[i]; if(!a) continue;
      const cx=a.x+a.width/2, cy=a.y+a.height/2;
      for (const r of svg.querySelectorAll('rect')){
        const b=caja(r); if(!corta(a,b)) continue;
        const dentro = cx>=b.x && cx<=b.x+b.width && cy>=b.y && cy<=b.y+b.height;
        if (!dentro)
          choques.push('"'+txt[i].textContent.trim().slice(0,30)+
                       '" encima de una caja del dibujo');
      }
    }
    const cu=sec.querySelector('.cuerpo');
    const cr=cu?cu.getBoundingClientRect():{height:0};
    out.push({choques:[...new Set(choques)].slice(0,6), zoom:Z,
              cuerpo:Math.round(cr.height/Z),
              maxh:svg?getComputedStyle(svg).maxHeight:'',
              sid:sec.getAttribute('data-sid'),
              clase:(sec.querySelector('.cuerpo')||{}).className||'',
              vbw:vb[2]||0, vbh:vb[3]||0,
              w:Math.round(r.width), h:Math.round(r.height),
              esc:esc, rot:min,
              vinetas:sec.querySelectorAll('.cuerpo > ul > li').length,
              motiva:sec.querySelectorAll('.cuerpo > p.motiva').length,
              formulas:sec.querySelectorAll('.cuerpo > p.formula').length});
  }
  const d=document.createElement('div'); d.id='diag';
  d.textContent=JSON.stringify(out); document.body.appendChild(d);
});"""


def medir(deck):
    tmp = deck.with_name("_figuras.html")
    tmp.write_text(deck.read_text(encoding="utf8")
                   .replace("plugins:[RevealNotes]});", SONDA), encoding="utf8")
    perfil = tempfile.mkdtemp(prefix="figuras-")
    try:
        r = subprocess.run(
            ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
             "--allow-file-access-from-files", "--user-data-dir=" + perfil,
             "--window-size=1280,720", "--virtual-time-budget=120000",
             "--dump-dom", "file://" + str(tmp)],
            capture_output=True, text=True, timeout=500)
        m = re.search(r'<div id="diag">(.*?)</div>',
                      r.stdout.replace("\n", " "), re.S)
        if not m:
            sys.exit("figuras.py: Chrome no devolvió la medida.")
        return json.loads(m.group(1))
    finally:
        if tmp.exists():
            os.unlink(tmp)
        shutil.rmtree(perfil, ignore_errors=True)


def clases_sin_regla(deck):
    """Clases usadas dentro de un SVG del deck que no tienen NINGUNA regla CSS.

    Es la comprobación que cazó los nodos negros de la sesión 15 el 21 de
    octubre de 2026. **Un `rect` de SVG sin regla de relleno se dibuja negro**,
    y eso no desborda, no se encima y no cambia ninguna escala: el navegador no
    tiene nada que reportar y la figura sale con cajas negras. Alberto lo vio en
    pantalla: "hay nodos que aparecen completamente en negro ¿qué pedo?".

    La causa típica es portar una figura de otra sesión sin portar su CSS, que
    es exactamente lo que había pasado. Por eso se comprueba estáticamente, sin
    navegador, contra el `<style>` del propio deck más el CSS del tema.
    """
    s = deck.read_text(encoding="utf8")
    usadas = set()
    for svg in re.findall(r"<svg\b.*?</svg>", s, re.S):
        for c in re.findall(r'class="([^"]+)"', svg):
            usadas.update(c.split())
    estilo = "".join(re.findall(r"<style>(.*?)</style>", s, re.S))
    # El CSS del tema se busca subiendo por los padres hasta encontrarlo, en
    # vez de contar niveles: así la comprobación también vale sobre una copia
    # en otro sitio, que es como se prueba sembrando el defecto.
    css = estilo
    rel = pathlib.Path("plantillas") / "tema-centrogeo" / "tema-centrogeo.css"
    for base in deck.parents:
        if (base / rel).exists():
            css += (base / rel).read_text(encoding="utf8")
            break
    definidas = set(re.findall(r"\.([A-Za-z][\w-]*)", css))
    return sorted(c for c in usadas if c not in definidas)


def dictamen(f):
    """Qué le pasa a esta figura, o None si está bien."""
    if not f["esc"]:
        return "sin viewBox"
    malos = []
    if f["esc"] < ESCALA_SUELO:
        malos.append("escala %.2f, por debajo del suelo de %.2f"
                     % (f["esc"], ESCALA_SUELO))
    elif f["esc"] < ESCALA_BUENA:
        malos.append("escala %.2f, por debajo de la banda buena de %.2f"
                     % (f["esc"], ESCALA_BUENA))
    if f.get("choques"):
        malos.append("hay texto encimado: %s" % "; ".join(f["choques"]))
    if f["rot"] and f["rot"] < ROTULO_SUELO:
        malos.append("el rótulo más pequeño queda en %.1f px, el suelo es %.0f"
                     % (f["rot"], ROTULO_SUELO))
    # La proporción solo se reporta si ADEMÁS la figura no se lee: es el medio
    # para que quepa, no el fin. Un lienzo cuadrado al que se le dio franja de
    # sobra cumple su trabajo, y avisar ahí sería ruido.
    prop = f["vbw"] / f["vbh"] if f["vbh"] else 0
    if malos and prop and prop < PROPORCION_MIN:
        malos.append("y el viewBox es de %.2f a 1, demasiado cuadrado para una "
                     "tira: por eso el alto manda tanto" % prop)
    return "; ".join(malos) if malos else None


def main(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("deck")
    p.add_argument("--todas", action="store_true",
                   help="lista también las figuras que están bien")
    a = p.parse_args(argv[1:])
    deck = pathlib.Path(a.deck).resolve()
    huerfanas = clases_sin_regla(deck)
    if huerfanas:
        print("  CLASES DE SVG SIN NINGUNA REGLA CSS: %s"
              % ", ".join(huerfanas))
        print("     un rect sin regla de relleno se dibuja NEGRO, y eso no lo "
              "detecta ninguna otra comprobación")
    figs = medir(deck)
    malas = []
    for f in figs:
        d = dictamen(f)
        if d:
            malas.append(f)
        if d or a.todas:
            prop = f["vbw"] / f["vbh"] if f["vbh"] else 0
            texto = f["vinetas"] + f["motiva"] + f["formulas"]
            print("  %-34s escala %.2f  rótulo %4.1f px  viewBox %d x %d "
                  "(%.1f:1)  %d piezas de texto  [cuerpo %d px, alto %d px, "
                  "max-height %s]"
                  % (f["sid"], f["esc"] or 0, f["rot"] or 0, f["vbw"], f["vbh"],
                     prop, texto, f.get("cuerpo", 0),
                     round(f["h"] / (f.get("zoom") or 1)),
                     f.get("maxh", "")))
            if d:
                print("     %s" % d)
                if f["vinetas"] >= 2:
                    print("     y la acompañan %d viñetas: lo que sobra es "
                          "texto, no dibujo" % f["vinetas"])
    print("figuras.py: %d figuras, %d con algún defecto%s"
          % (len(figs), len(malas),
             ", y %d clase sin regla CSS" % len(huerfanas)
             if huerfanas else ""))
    if not malas and not huerfanas:
        print("   TODAS LAS FIGURAS SE LEEN PROYECTADAS")
    return 1 if (malas or huerfanas) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
