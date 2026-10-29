#!/usr/bin/env python3
r"""Prueba de regresión del mapa flotante de parcelas.

    python3 tools/prueba-parcelas.py [sesiones/SNN-.../index.html]

Mide en Chrome headless, no el estado interno de nadie. Corre igual sobre el
deck servido y sobre el paquete de `salidas/`, que es donde de verdad importa:
Alberto decidió el 8 de octubre de 2026 que el mapa **viaja al grupo**, así que
si `empaquetar.py` lo dejara fuera nadie se enteraría hasta que un estudiante
abriera el archivo.

Lo que comprueba, lámina por lámina:

  * que el deck declare su `<template id="mapa-parcelas">` y que el mapa exista;
  * que en una lámina que nombra parcelas salga el botón y el panel se abra;
  * que las casillas encendidas sean EXACTAMENTE las del `data-celdas` de esa
    lámina, que es lo que escribe `tools/parcelas.py`;
  * que en una lámina que no nombra ninguna el botón no salga y la tecla no
    abra nada, para que no aparezca una rejilla con todo apagado;
  * que el panel quepa entero en la ventana;
  * y que al cambiar de lámina las casillas cambien con ella.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SONDA = """<script>
setTimeout(function(){
  function est(){
    var b=document.querySelector('.mp-boton'), p=document.querySelector('.mp-panel');
    var s=document.querySelector('.reveal section.present');
    var r=p&&getComputedStyle(p).display!=='none'?p.getBoundingClientRect():null;
    return {boton:b?getComputedStyle(b).display:null,
            panel:p?getComputedStyle(p).display:null,
            sid:s?s.getAttribute('data-sid'):null,
            pide:s?(s.getAttribute('data-celdas')||''):'',
            on:[].slice.call(document.querySelectorAll('.mp-panel [data-celda].mp-on'))
                 .map(function(e){return e.getAttribute('data-celda')}).sort().join(' '),
            cabe:r?(r.left>=0&&r.top>=0&&r.right<=window.innerWidth&&r.bottom<=window.innerHeight):null};
  }
  var o={hayTemplate:!!document.getElementById('mapa-parcelas'),
         celdasDibujadas:document.querySelectorAll('.mp-panel [data-celda]').length,
         pasos:[]};
  var todas=[].slice.call(document.querySelectorAll('.reveal section[data-celdas]'));
  // La segunda tiene que pedir OTRAS casillas: con dos láminas iguales, la
  // comprobación de que las casillas cambian pasaría sin medir nada.
  var conCeldas=[todas[0]];
  for (var i=1;i<todas.length;i++){
    if (todas[i].getAttribute('data-celdas')!==todas[0].getAttribute('data-celdas')){
      conCeldas.push(todas[i]); break;
    }
  }
  if (conCeldas.length<2) conCeldas.push(todas[1]);
  var sinCeldas=[].slice.call(document.querySelectorAll('.reveal section:not([data-celdas])'))
                  .filter(function(s){return s.getAttribute('data-sid')});
  /* La pulsación va COMPLETA, con keyCode 77, que es por donde reveal engancha
     sus atajos. La primera versión de esta prueba mandaba un KeyboardEvent sin
     keyCode y por eso daba verde con la tecla rota: solo ejercitaba un camino
     que ningún teclado real toma. keyCode es de solo lectura, así que se
     define encima del evento ya construido. */
  function tecla(){
    var e=new KeyboardEvent('keydown',{key:'m',bubbles:true,cancelable:true});
    Object.defineProperty(e,'keyCode',{get:function(){return 77}});
    Object.defineProperty(e,'which',{get:function(){return 77}});
    document.dispatchEvent(e);
  }
  function ir(sec,cb){ Reveal.slide([].indexOf.call(sec.parentNode.children,sec)); setTimeout(cb,260); }
  function esc(){
    var llego=false;
    function espia(){llego=true;}
    document.addEventListener('keydown',espia);   // burbujeo sobre document, como reveal
    var e=new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true});
    document.body.dispatchEvent(e);               // desde body, como una tecla de verdad
    document.removeEventListener('keydown',espia);
    return {llego:llego, parado:!llego};
  }
  var paso=0;
  function sigue(){
    if(paso===0){ ir(conCeldas[0],function(){ tecla(); o.pasos.push(['abre',est()]); paso=1; sigue(); }); }
    else if(paso===1){ ir(conCeldas[1],function(){ o.pasos.push(['cambia',est()]); paso=2; sigue(); }); }
    else if(paso===2){ ir(sinCeldas[sinCeldas.length-1],function(){ tecla(); o.pasos.push(['sin',est()]); paso=3; sigue(); }); }
    else if(paso===3){ ir(conCeldas[0],function(){ o.pasos.push(['vuelve',est()]); paso=4; sigue(); }); }
    else if(paso===4){ o.escape=esc(); o.pasos.push(['escape',est()]); paso=5; sigue(); }
    else if(paso===5){ document.querySelector('.mp-boton').click();
                       o.pasos.push(['boton',est()]); paso=6; sigue(); }
    else if(paso===6){ document.querySelector('.mp-panel .mp-x').click();
                       o.pasos.push(['equis',est()]); paso=7; sigue(); }
    else { var d=document.createElement('div'); d.id='diag'; d.textContent=JSON.stringify(o);
           document.body.appendChild(d); }
  }
  sigue();
}, 2500);
</script>"""


def medir(ruta):
    """Mete la sonda como un script propio antes de `</body>`.

    Así vale igual para el deck servido y para el paquete, que ya no lleva el
    plugin de notas del que colgaba la primera versión de esta prueba."""
    p = pathlib.Path(ruta).resolve()
    txt = p.read_text(encoding="utf-8")
    if "</body>" not in txt:
        return None, "el archivo no tiene </body>"
    tmp = p.with_name("_parcelas.html")
    tmp.write_text(txt.replace("</body>", SONDA + "</body>"), encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="parcelas-")
    try:
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--user-data-dir=" + perfil, "--window-size=1600,900",
                            "--virtual-time-budget=20000", "--dump-dom", "file://" + str(tmp)],
                           capture_output=True, text=True, timeout=120)
        m = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace(chr(10), " "), re.S)
        return (json.loads(m.group(1)), None) if m else (None, "la sonda no devolvió nada")
    finally:
        tmp.unlink(missing_ok=True)
        shutil.rmtree(perfil, ignore_errors=True)


def main(ruta):
    d, err = medir(ruta)
    if err:
        print("FALLA  no se pudo medir: %s" % err)
        return 1
    fallos = 0

    def chk(ok, texto, detalle=""):
        nonlocal fallos
        print(("pasa  " if ok else "FALLA ") + texto + ("  [%s]" % detalle if detalle else ""))
        if not ok:
            fallos += 1

    chk(d["hayTemplate"], "el deck declara su template del mapa")
    chk(d["celdasDibujadas"] == 16, "el mapa dibuja las dieciséis casillas",
        "son %d" % d["celdasDibujadas"])
    pasos = dict((p[0], p[1]) for p in d["pasos"])
    a = pasos.get("abre", {})
    chk(a.get("boton") == "block", "el botón sale en una lámina que nombra parcelas")
    chk(a.get("panel") == "block", "y la tecla abre el mapa")
    chk(a.get("on") == " ".join(sorted(a.get("pide", "").split())),
        "enciende exactamente las parcelas de esa lámina",
        "pide %r, enciende %r" % (a.get("pide"), a.get("on")))
    chk(a.get("cabe") is True, "el panel cabe entero en la ventana")
    b = pasos.get("cambia", {})
    chk(b.get("panel") == "block", "sigue abierto al cambiar de lámina")
    chk(b.get("on") == " ".join(sorted(b.get("pide", "").split())),
        "y las casillas cambian con la lámina",
        "pide %r, enciende %r" % (b.get("pide"), b.get("on")))
    chk(b.get("on") != a.get("on") or b.get("pide") == a.get("pide"),
        "no se queda con las de la lámina anterior")
    c = pasos.get("sin", {})
    chk(c.get("boton") == "none", "el botón no sale donde no hay parcelas")
    chk(c.get("panel") == "none", "y la tecla no abre una rejilla vacía")
    v = pasos.get("vuelve", {})
    chk(v.get("panel") == "block",
        "y vuelve solo al regresar a una lámina con parcelas",
        "panel=%s" % v.get("panel"))
    chk(v.get("on") == " ".join(sorted(v.get("pide", "").split())),
        "con las casillas de la lámina a la que vuelve",
        "pide %r, enciende %r" % (v.get("pide"), v.get("on")))
    es = pasos.get("escape", {})
    chk(es.get("panel") == "none", "Escape cierra el mapa")
    chk(d.get("escape", {}).get("parado") is True,
        "y Escape no sigue viajando hasta reveal",
        "llegó al oyente de reveal=%s" % (not d.get("escape", {}).get("parado")))
    bo = pasos.get("boton", {})
    chk(bo.get("panel") == "block", "el botón Ver parcelas lo vuelve a abrir")
    eq = pasos.get("equis", {})
    chk(eq.get("panel") == "none", "y la × lo cierra")
    tot = 17
    print("las %d pruebas del mapa pasan" % tot if not fallos
          else "%d de %d fallan" % (fallos, tot))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "sesiones/S11-redes-bayesianas-e-inferencia/index.html"))
