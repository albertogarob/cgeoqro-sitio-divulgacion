#!/usr/bin/env python3
"""Mide si algún rótulo de un SVG del deck se sale de su viewBox.

Alberto reportó cuatro veces el mismo fallo al revisar la sesión 17: "el título
de la gráfica no se ve, se corta, igual que su footer", "el texto de la parte de
arriba sale cortado", "la etiqueta en la parte superior de la figura no se ve, se
corta, revisa todas las figuras porque muchas tienen el mismo problema", y una
cita que decía 'je' donde la lámina escribe 'eje'. Es UNA sola clase de fallo:
rótulos dibujados fuera del viewBox, que el navegador recorta sin avisar.

Ninguna herramienta del proyecto lo detectaba. figuras.py mide la escala y los
encimamientos DENTRO del dibujo; verifica.py mide el desborde del cuerpo de la
lámina, no del SVG. Esto mide la caja de cada <text> contra el viewBox, en
Chrome, que es quien recorta.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

if len(sys.argv) < 2:
    raise SystemExit("uso: python3 tools/recorte.py sesiones/SNN-.../index.html")
RUTA = pathlib.Path(sys.argv[1])
MARGEN = 1.0

SONDA = """plugins:[RevealNotes]});
Reveal.addEventListener('ready', function(){
  // TODAS LAS SECCIONES VISIBLES ANTES DE MEDIR. getBBox() devuelve ceros en un
  // subárbol con display:none, así que midiendo con reveal tal cual solo se mide
  // la lámina en pantalla y la sonda sale limpia mintiendo. Me pasó en el primer
  // intento del 27 de octubre de 2026.
  const st = document.createElement('style');
  st.textContent = '.reveal .slides section{display:block!important;' +
    'position:static!important;opacity:1!important;visibility:visible!important;' +
    'transform:none!important;height:720px!important;}' +
    '.reveal .slides{position:static!important;transform:none!important;' +
    'left:0!important;top:0!important;}';
  document.head.appendChild(st);
  const M = %s, out = [];
  document.querySelectorAll('section').forEach(sec => {
    const sid = sec.getAttribute('data-sid') || '?';
    sec.querySelectorAll('.cuerpo > svg').forEach(svg => {
      const vb = (svg.getAttribute('viewBox')||'0 0 0 0').split(/\\s+/).map(Number);
      const vx = vb[0], vy = vb[1], vw = vb[2], vh = vb[3];
      svg.querySelectorAll('text').forEach(t => {
        let b; try { b = t.getBBox(); } catch(e) { return; }
        if (!b.width && !b.height) return;
        const f = [];
        if (b.x < vx - M) f.push('izquierda ' + Math.round(vx - b.x));
        if (b.y < vy - M) f.push('arriba ' + Math.round(vy - b.y));
        if (b.x + b.width > vx + vw + M) f.push('derecha ' + Math.round(b.x + b.width - vx - vw));
        if (b.y + b.height > vy + vh + M) f.push('abajo ' + Math.round(b.y + b.height - vy - vh));
        if (f.length) out.push({sid: sid, txt: t.textContent.slice(0, 46), fuera: f.join(', ')});
      });
    });
  });
  const d = document.createElement('div'); d.id = 'rec';
  d.textContent = JSON.stringify(out); document.body.appendChild(d);
});""" % MARGEN

tmp = RUTA.with_name("_recorte.html")
tmp.write_text(RUTA.read_text(encoding="utf8")
               .replace("plugins:[RevealNotes]});", SONDA), encoding="utf8")
perfil = tempfile.mkdtemp(prefix="recorte-")
try:
    r = subprocess.run(
        ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
         "--allow-file-access-from-files", "--user-data-dir=" + perfil,
         "--window-size=1280,720", "--virtual-time-budget=120000",
         "--dump-dom", "file://" + str(tmp.resolve())],
        capture_output=True, text=True, timeout=500)
    m = re.search(r'<div id="rec">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
    if not m:
        sys.exit("recorte.py: Chrome no devolvió la medida.")
    datos = json.loads(m.group(1) or "[]")
finally:
    if tmp.exists():
        os.unlink(tmp)
    shutil.rmtree(perfil, ignore_errors=True)

if not datos:
    print("recorte.py: NINGÚN RÓTULO SE SALE DE SU VIEWBOX")
    raise SystemExit(0)
porsid = {}
for d in datos:
    porsid.setdefault(d["sid"], []).append(d)
for sid, ds in porsid.items():
    print("  %s" % sid)
    for d in ds:
        print("     se sale por %-22s %r" % (d["fuera"], d["txt"]))
print("recorte.py: %d rótulos recortados en %d láminas" % (len(datos), len(porsid)))
raise SystemExit(1)
