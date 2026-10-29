#!/usr/bin/env python3
"""Como verifica.py, pero navegando a cada lámina antes de medirla.

verifica.py mide todas las secciones de una sola pasada. Reveal deja en
display:none todas menos la actual y sus vecinas, así que en las ocultas
scrollHeight y clientHeight valen cero y nunca detecta nada. Esta versión
va lámina por lámina con Reveal.slide().
"""
import re, subprocess, sys, pathlib, os, json

SONDA = """plugins:[RevealNotes]}).then(async()=>{
  await document.fonts.ready; await new Promise(r=>setTimeout(r,400));
  const out=[]; const secs=[...document.querySelectorAll('.slides > section')];
  for (let i=0;i<secs.length;i++){
    Reveal.slide(i);
    await new Promise(r=>setTimeout(r,120));
    const sec=secs[i];
    sec.querySelectorAll('h2,.cuerpo,.titulo,.bajada,.gracias').forEach(el=>{
      if (getComputedStyle(el).display==='none') return;
      const fs=parseFloat(getComputedStyle(el).fontSize);
      const o=el.scrollHeight-el.clientHeight;
      if(o > fs*0.35) out.push(sec.id+' DESBORDA '+(el.tagName=='H2'?'titulo':el.className)+' +'+o+'px');
    });
    const h=sec.querySelector('h2'), c=sec.querySelector('.cuerpo');
    if(h&&c&&getComputedStyle(c).display!=='none'){
      const a=h.getBoundingClientRect(), b=c.getBoundingClientRect();
      if(a.bottom > b.top+2) out.push(sec.id+' COLISION titulo/cuerpo '+Math.round(a.bottom-b.top)+'px');
    }
  }
  const d=document.createElement('div'); d.id='diag';
  d.textContent = out.length? out.join(' | ') : 'SIN DESBORDES NI COLISIONES';
  document.body.appendChild(d);
});"""

def main(ruta):
    p = pathlib.Path(ruta).resolve()
    s = p.read_text(encoding="utf-8").replace("plugins:[RevealNotes]});", SONDA)
    tmp = p.with_name("_verifica2.html"); tmp.write_text(s, encoding="utf-8")
    try:
        r = subprocess.run(["google-chrome","--headless=new","--no-sandbox","--disable-gpu",
                            "--window-size=1280,720","--virtual-time-budget=60000","--dump-dom",
                            "file://"+str(tmp)], capture_output=True, text=True, timeout=180)
        m = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n"," "), re.S)
        salida = m.group(1) if m else "(no se pudo medir)"
    finally:
        if tmp.exists(): os.unlink(tmp)
    for parte in salida.split(" | "): print(" ", parte)
    return 0 if "SIN DESBORDES" in salida else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
