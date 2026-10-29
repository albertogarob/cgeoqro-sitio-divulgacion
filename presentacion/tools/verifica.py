#!/usr/bin/env python3
"""Verifica que ninguna diapositiva desborde ni se encime.

    python3 tools/verifica.py sesiones/S01-.../index.html

Carga el deck en Chrome headless, espera a que las fuentes estén listas, y
comprueba dos cosas en cada diapositiva:

  1. Que ningún bloque de texto desborde su caja. Se tolera un margen del 35%
     del tamaño de fuente, porque con interlineado ajustado los descendentes
     de Noto Sans sobresalen del renglón sin que eso sea un desborde real.
  2. Que el título no se encime con el cuerpo, cosa que pasa cuando un título
     ocupa tres líneas.

Hay que correrlo antes de dar por buena una sesión: el desborde recorta texto
en silencio y no se nota hasta estar frente al grupo.
"""
import re, shutil, subprocess, sys, pathlib, tempfile, os

SONDA = """plugins:[RevealNotes]}).then(async()=>{
  await document.fonts.ready; await new Promise(r=>setTimeout(r,700));
  const out=[];
  document.querySelectorAll('.slides > section').forEach(sec=>{
    sec.querySelectorAll('h2,.cuerpo,.titulo,.bajada,.gracias').forEach(el=>{
      const fs=parseFloat(getComputedStyle(el).fontSize);
      const o=el.scrollHeight-el.clientHeight;
      if(o > fs*0.35) out.push(sec.id+' DESBORDA '+(el.tagName=='H2'?'titulo':el.className)+' +'+o+'px');
    });
    const h=sec.querySelector('h2'), c=sec.querySelector('.cuerpo');
    if(h&&c){ const a=h.getBoundingClientRect(), b=c.getBoundingClientRect();
      if(a.bottom > b.top+2) out.push(sec.id+' COLISION titulo/cuerpo '+Math.round(a.bottom-b.top)+'px'); }
  });
  const d=document.createElement('div'); d.id='diag';
  d.textContent = out.length? out.join(' | ') : 'SIN DESBORDES NI COLISIONES';
  document.body.appendChild(d);
});"""

def main(ruta):
    p = pathlib.Path(ruta).resolve()
    s = p.read_text(encoding="utf-8").replace("plugins:[RevealNotes]});", SONDA)
    tmp = p.with_name("_verifica.html")
    tmp.write_text(s, encoding="utf-8")
    # Perfil desechable: sin él, Chrome usa el de siempre, y entonces esto choca
    # con el navegador abierto y con otra corrida en paralelo sobre otro deck.
    perfil = tempfile.mkdtemp(prefix="verifica-")
    try:
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--user-data-dir=" + perfil,
                            "--virtual-time-budget=15000", "--dump-dom", "file://" + str(tmp)],
                           capture_output=True, text=True, timeout=90)
        m = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
        salida = m.group(1) if m else "(no se pudo medir)"
    finally:
        if tmp.exists(): os.unlink(tmp)
        shutil.rmtree(perfil, ignore_errors=True)
    print(salida)
    return 0 if "SIN DESBORDES" in salida else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "index.html"))
