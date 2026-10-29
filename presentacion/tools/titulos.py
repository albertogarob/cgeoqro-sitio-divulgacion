#!/usr/bin/env python3
"""¿Cuántas líneas ocupa cada título del deck, medido en Chrome?

    python3 tools/titulos.py sesiones/SNN-.../index.html
    python3 tools/titulos.py sesiones/SNN-.../index.html --probar "Un título" "Otro"

**Alberto decidió el 13 de octubre de 2026 que los títulos son de UNA línea.**
Un título de dos líneas se ve entero, pero desborda su caja y rompe el aire de
las doce sesiones anteriores, donde ninguno pasa de 31 caracteres.

**Y el largo NO se puede contar en caracteres.** El tema pone `text-wrap:
balance` en el `h2`, así que Chrome reparte el texto en dos líneas parejas
mucho antes de llenar el ancho disponible, y además el `::before` del banner
reserva un 9% de la primera línea. El resultado es que un título de 32
caracteres puede partirse mientras otro de 31 cabe, según qué palabras lleve.
Por eso esto mide en el navegador, como `gordas.py` y por la misma razón.

Con `--probar` mide títulos candidatos sin tocar el deck: los va metiendo en el
`h2` de una lámina de contenido real y dice cuántas líneas ocupa cada uno. Es
la forma de reescribir un título sin generar el deck veinte veces.

Devuelve 1 si algún título del deck ocupa más de una línea.
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

SONDA = """plugins:[RevealNotes]}).then(async()=>{
  await document.fonts.ready; await new Promise(r=>setTimeout(r,400));
  const CAND = __CANDIDATOS__;
  const out=[]; const secs=[...document.querySelectorAll('.slides > section')];
  function lineas(h){
    const lh=parseFloat(getComputedStyle(h).lineHeight)||1;
    return Math.max(1, Math.round(h.scrollHeight/lh));
  }
  for (let i=0;i<secs.length;i++){
    Reveal.slide(i); await new Promise(r=>setTimeout(r,110));
    const h=secs[i].querySelector('h2'); if(!h) continue;
    const sec=secs[i].className.includes('seccion');
    if (CAND.length===0){
      out.push({sid:secs[i].getAttribute('data-sid'), sec:sec,
                t:h.textContent.trim(), n:h.textContent.trim().length,
                lineas:lineas(h)});
    } else if (!sec && out.length===0){
      // Una sola lámina de contenido basta: todas comparten la misma caja.
      const antes=h.innerHTML;
      for (const c of CAND){ h.textContent=c;
        await new Promise(r=>setTimeout(r,40));
        out.push({sid:'(prueba)', sec:false, t:c, n:c.length, lineas:lineas(h)}); }
      h.innerHTML=antes;
    }
  }
  const d=document.createElement('div'); d.id='diag';
  d.textContent=JSON.stringify(out); document.body.appendChild(d);
});"""


def medir(deck, candidatos):
    sonda = SONDA.replace("__CANDIDATOS__", json.dumps(candidatos, ensure_ascii=False))
    tmp = deck.with_name("_titulos.html")
    tmp.write_text(deck.read_text(encoding="utf8")
                   .replace("plugins:[RevealNotes]});", sonda), encoding="utf8")
    perfil = tempfile.mkdtemp(prefix="titulos-")
    try:
        r = subprocess.run(
            ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
             "--allow-file-access-from-files", "--user-data-dir=" + perfil,
             "--window-size=1280,720", "--virtual-time-budget=90000",
             "--dump-dom", "file://" + str(tmp)],
            capture_output=True, text=True, timeout=400)
        m = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
        if not m:
            sys.exit("titulos.py: Chrome no devolvió la medida.")
        return json.loads(m.group(1))
    finally:
        if tmp.exists():
            os.unlink(tmp)
        shutil.rmtree(perfil, ignore_errors=True)


def main(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("deck")
    p.add_argument("--probar", nargs="*", default=[],
                   help="títulos candidatos, en vez de los del deck")
    p.add_argument("--todos", action="store_true",
                   help="lista también los que caben en una línea")
    a = p.parse_args(argv[1:])
    d = medir(pathlib.Path(a.deck).resolve(), a.probar)
    largos = [x for x in d if x["lineas"] > 1]
    for x in d:
        if a.probar or a.todos or x["lineas"] > 1:
            marca = "CABE " if x["lineas"] == 1 else f"{x['lineas']} LÍNEAS"
            print(f"  {marca:8s} {x['n']:3d}c  {x['t']}")
    if a.probar:
        return 0
    print(f"titulos.py: {len(d)} títulos, {len(largos)} de más de una línea")
    if not largos:
        print("   TODOS LOS TÍTULOS CABEN EN UNA LÍNEA")
    return 1 if largos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
