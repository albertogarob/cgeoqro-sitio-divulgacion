#!/usr/bin/env python3
r"""Prueba de regresión de las marcas de cambio en la revisión, la tecla X.

    python3 tools/prueba-vercambios.py [sesiones/SNN-.../index.html]

Mide en Chrome headless lo que se ve, no el estado interno de nadie. El apartado
`cambios` de notas.json se siembra sobre una copia del deck, así que la prueba no
toca el archivo de verdad ni necesita el servidor.

Lo que comprueba:

  * que la pieza del cuerpo que cambió salga marcada en la lámina, y solo ella;
  * que pasar el ratón por encima abra el globo con el texto de ANTES;
  * que la marca no mueva el texto de sitio, que es la condición que puso
    Alberto al elegir el globo en vez del tachado dentro de la viñeta;
  * que al cambiar de lámina la marca desaparezca y no arrastre a la siguiente;
  * que la ventana del guion enseñe las palabras nuevas y las quitadas;
  * que la tecla X abra la lista, con la lámina y su diff;
  * y que la barra cuente las láminas tocadas.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SONDA = r"""<script>
(function(){
  var o={pasos:{}};
  function dormir(ms){return new Promise(function(r){setTimeout(r,ms)})}
  function tecla(k,c){var e=new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true});
    Object.defineProperty(e,'keyCode',{get:function(){return c}});
    Object.defineProperty(e,'which',{get:function(){return c}});
    document.dispatchEvent(e)}
  function caja(e){var r=e.getBoundingClientRect();
    return {l:Math.round(r.left),t:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height)}}

  window.addEventListener('load', async function(){
    await dormir(1800);
    var st=document.createElement('style');
    st.textContent='*{transition:none !important;animation:none !important}';
    document.head.appendChild(st);

    var P=window.__P;
    var secs=[].slice.call(document.querySelectorAll('.reveal .slides > section'));
    var sec=secs.find(function(s){return s.getAttribute('data-sid')===P.sid});
    Reveal.slide([].indexOf.call(sec.parentNode.children,sec));
    await dormir(400);

    // dónde estaba el texto ANTES de marcar nada
    var pz=sec.querySelector('[data-pieza="'+P.pieza+'"]');
    var otra=sec.querySelector('[data-pieza="'+P.otra+'"]');
    o.antesDeMarcar={pz:caja(pz), otra:caja(otra)};

    o.pasos.marca={
      marcadas:[].slice.call(sec.querySelectorAll('.rv-cam'))
                 .map(function(e){return e.getAttribute('data-pieza')}),
      filo:getComputedStyle(pz).outlineStyle!=='none'&&parseFloat(getComputedStyle(pz).outlineWidth)>0,
      pzAhora:caja(pz), otraAhora:caja(otra),
      guardaAntes:(pz.dataset.rvAntes||'').slice(0,80)
    };

    // el globo
    pz.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));
    await dormir(200);
    var g=document.querySelector('.rv-cam-pop');
    o.pasos.globo={hay:!!g, texto:g?g.textContent.slice(0,90):null,
      cabe:g?(function(){var r=g.getBoundingClientRect();
        return r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight})():null};

    // cambiar de lámina no arrastra la marca
    Reveal.slide([].indexOf.call(sec.parentNode.children,sec)+1);
    await dormir(400);
    o.pasos.otraLamina={marcadas:document.querySelectorAll('.rv-cam').length,
                        globo:!!document.querySelector('.rv-cam-pop')};
    Reveal.slide([].indexOf.call(sec.parentNode.children,sec));
    await dormir(400);
    o.pasos.vuelta={marcadas:document.querySelectorAll('.rv-cam').length};

    // la barra
    var b=document.querySelector('.rv-barra');
    o.pasos.barra={texto:b?b.textContent:'', boton:!!document.querySelector('.rv-cam-b')};

    // la lista con la tecla X
    tecla('x',88);
    await dormir(400);
    var cap=document.querySelector('.rv-capa');
    o.pasos.lista={hay:!!cap,
      filas:document.querySelectorAll('.rv-cam-fila').length,
      idas:document.querySelectorAll('.rv-cam-ida').length,
      textoIda:(function(){var e=document.querySelector('.rv-cam-ida');
        return e?e.textContent.replace(/\s+/g,' ').trim():''})(),
      idaPincha:(function(){var e=document.querySelector('.rv-cam-ida');
        return e?e.dataset.i!==undefined:null})(),
      mas:document.querySelectorAll('.rv-cam-lista ins.rv-mas').length,
      menos:document.querySelectorAll('.rv-cam-lista del.rv-menos').length,
      visto:!!document.querySelector('button[data-rv="visto"]'),
      texto:cap?cap.textContent.slice(0,120):''};
    var es=new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true});
    document.dispatchEvent(es);
    await dormir(250);

    // la tecla Z: esconder y mostrar
    tecla('z',90);
    await dormir(400);
    o.pasos.escondidos={
      marcadas:document.querySelectorAll('.rv-cam').length,
      globo:!!document.querySelector('.rv-cam-pop'),
      chapa:!!document.querySelector('.rv-cam-b'),
      apagada:!!document.querySelector('.rv-cam-b.rv-cam-off'),
      barra:(document.querySelector('.rv-barra')||{}).textContent||'',
      guardado:(function(){try{return localStorage.getItem('cambios-ocultos:'+window.__DECK)}
                           catch(e){return 'x'}})()};
    // la lista sigue abriéndose a propósito
    tecla('x',88);
    await dormir(350);
    o.pasos.escondidos.lista=document.querySelectorAll('.rv-cam-fila').length;
    document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));
    await dormir(250);
    tecla('z',90);
    await dormir(400);
    o.pasos.devueltos={
      marcadas:document.querySelectorAll('.rv-cam').length,
      apagada:!!document.querySelector('.rv-cam-b.rv-cam-off'),
      guardado:(function(){try{return localStorage.getItem('cambios-ocultos:'+window.__DECK)}
                           catch(e){return 'x'}})()};

    // la ventana del guion
    var marco=document.createElement('iframe');
    marco.style.cssText='position:fixed;left:-3000px;width:720px;height:900px';
    document.body.appendChild(marco);
    var vent={closed:false, get document(){return marco.contentDocument},
              focus:function(){}, close:function(){}, scrollTo:function(){},
              addEventListener:function(){}, get scrollY(){return 0}, innerHeight:900};
    window.open=function(){return vent};
    tecla('g',71);
    await dormir(600);
    var d2=marco.contentDocument;
    tecla('z',90);                      // escondidas, desde el deck
    await dormir(400);
    o.pasos.guionEscondido={
      parrafos:d2?d2.querySelectorAll('#texto p.rv-cam-p').length:0,
      mas:d2?d2.querySelectorAll('#texto ins.rv-mas').length:0};
    tecla('z',90);                      // y de vuelta
    await dormir(400);
    // y ahora la misma tecla DESDE la ventana del guion, sin volver al deck
    d2.dispatchEvent(new KeyboardEvent('keydown',{key:'z',bubbles:true,cancelable:true}));
    await dormir(400);
    o.pasos.zDesdeGuion={
      parrafos:d2.querySelectorAll('#texto p.rv-cam-p').length,
      enLamina:document.querySelectorAll('.rv-cam').length};
    d2.dispatchEvent(new KeyboardEvent('keydown',{key:'z',bubbles:true,cancelable:true}));
    await dormir(400);
    o.pasos.zDesdeGuionVuelta={
      parrafos:d2.querySelectorAll('#texto p.rv-cam-p').length,
      enLamina:document.querySelectorAll('.rv-cam').length};
    // Un párrafo con matemáticas ya compuestas no se repinta: el diff es texto
    // plano y borraría el SVG de MathJax.
    (function(){
      var ps=[].slice.call(d2.querySelectorAll('#texto p'));
      var conMat=ps.filter(function(x){return x.querySelector('mjx-container')});
      o.pasos.mate={
        total:conMat.length,
        cambiados:conMat.filter(function(x){return x.classList.contains('rv-cam-p')}).length,
        conservan:conMat.filter(function(x){return x.querySelector('mjx-container')}).length,
        tags:d2.querySelectorAll('.rv-cam-tag').length};
    })();
    o.pasos.guion={abre:!!(d2&&d2.getElementById('texto')),
      parrafos:d2?d2.querySelectorAll('#texto p.rv-cam-p').length:0,
      mas:d2?d2.querySelectorAll('#texto ins.rv-mas').length:0,
      menos:d2?d2.querySelectorAll('#texto del.rv-menos').length:0,
      texto:d2?(d2.getElementById('texto')||{}).textContent.slice(0,0):''};

    var dv=document.createElement('div'); dv.id='diag';
    dv.textContent=JSON.stringify(o); document.body.appendChild(dv);
  });
})();
</script>"""


def medir(ruta):
    p = pathlib.Path(ruta).resolve()
    txt = p.read_text(encoding="utf-8")

    # ¿Qué lámina y qué piezas? La primera con al menos dos piezas y guion.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import anclas
    # La lámina tiene que traer, además de dos piezas y guion, **un párrafo con
    # matemáticas**: sin eso la comprobación de que el diff no borra las
    # fórmulas pasaría en vacío, que es como pasó la primera vez.
    elegida = None
    for ini, fin, attrs, cuerpo in anclas.laminas_de(txt):
        sid = (re.search(r'data-sid="([^"]+)"', attrs) or [None, None])[1]
        nums = re.findall(r'data-pieza="(\d+)"', anclas.sin_asides(cuerpo))
        m = re.search(r'<aside\b[^>]*class="[^"]*notes[^"]*"[^>]*>(.*?)</aside>',
                      cuerpo, re.S)
        gp = re.findall(r'<p\b[^>]*>(.*?)</p>', m.group(1), re.S) if m else []
        conMat = [i for i, t in enumerate(gp) if "\\(" in t]
        if sid and len(nums) >= 2 and len(gp) >= 2 and conMat:
            elegida = (sid, nums[0], nums[1], conMat[0], len(gp))
            break
    if not elegida:
        return None, ("el deck no tiene ninguna lámina con dos piezas, guion y "
                      "una expresión matemática en él")
    sid, pieza, otra, iMat, nGp = elegida
    # el párrafo del diff: uno SIN matemáticas, para medir el tachado; y además
    # se siembra un cambio en el que SÍ las tiene, para medir que no se pierden
    iTexto = next((i for i in range(nGp) if i != iMat), 0)

    cambios = {"sello": "prueba", "laminas": {sid: {
        "estado": "cambiada", "titulo": "la lámina de prueba",
        "piezas": [{"n": pieza, "dif": [["=", "El sensor "], ["-", "viejo "],
                                        ["+", "nuevo "], ["=", "del terreno."]]}],
        "guion": [{"i": iTexto, "dif": [["=", "Primero "], ["-", "lo de antes "],
                                       ["+", "lo de ahora "], ["=", "y ya."]]},
                  {"i": iMat, "dif": [["=", "Con "], ["-", "lo viejo"],
                                      ["+", "lo nuevo"]]}],
        "corto": []},
        # Una lámina que ya no está en el deck. Es el caso que destapó el bug
        # del 13 de octubre de 2026: la chapa la contaba y la lista no la
        # enseñaba, así que una sección retirada era invisible.
        "una-que-ya-no-esta": {"estado": "borrada",
                               "titulo": "La lámina que se fue"}}}
    semilla = ("<script>window.__P=%s;window.__CAMBIOS=%s;window.__DECK=%s;</script>"
               % (json.dumps({"sid": sid, "pieza": pieza, "otra": otra}),
                  json.dumps(cambios), json.dumps(p.parent.name)))

    # El anotador lee el apartado del documento que le llega. Sin servidor usa
    # localStorage, así que se le mete ahí por la puerta de adoptar().
    inyecta = """<script>
      (function(){
        var orig = window.fetch;
        window.fetch = function(u, o){
          if (String(u).indexOf('/notas/') === 0 && (!o || !o.method || o.method === 'GET')) {
            var d = {v:1, notas:{}, guiones:{}, cortos:{}, recortes:{}, orden:[],
                     nuevas:[], borradas:[], fusiones:[], pendientes:[],
                     cambios: window.__CAMBIOS};
            return Promise.resolve(new Response(JSON.stringify(d),
              {status:200, headers:{'Content-Type':'application/json'}}));
          }
          if (String(u).indexOf('/notas/') === 0 || String(u).indexOf('/foto/') === 0)
            return Promise.resolve(new Response('{"v":2}', {status:200}));
          return orig.apply(this, arguments);
        };
      })();
    </script>"""
    m = re.search(r'<script src="[^"]*revisar\.js"></script>', txt)
    if not m:
        return None, "el deck no carga revisar.js"
    txt = txt.replace(m.group(0), semilla + inyecta + m.group(0))

    tmp = p.with_name("_vercam.html")
    tmp.write_text(txt.replace("</body>", SONDA + "</body>"), encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="vercam-")
    try:
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--allow-file-access-from-files", "--user-data-dir=" + perfil,
                            "--window-size=1600,900", "--virtual-time-budget=40000",
                            "--dump-dom", "file://" + str(tmp) + "?review"],
                           capture_output=True, text=True, timeout=180)
        mm = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace(chr(10), " "), re.S)
        if not mm:
            return None, "la sonda no devolvió nada: " + r.stderr[-400:]
        return json.loads(mm.group(1)), None
    finally:
        tmp.unlink(missing_ok=True)
        shutil.rmtree(perfil, ignore_errors=True)


def main(ruta):
    d, err = medir(ruta)
    if err:
        print("FALLA  no se pudo medir: %s" % err)
        return 1
    fallos = [0]

    def chk(ok, texto, detalle=""):
        print(("pasa  " if ok else "FALLA ") + texto + ("  [%s]" % detalle if detalle else ""))
        if not ok:
            fallos[0] += 1

    p = d["pasos"]
    chk(len(p["marca"]["marcadas"]) == 1, "solo se marca la pieza que cambió",
        str(p["marca"]["marcadas"]))
    chk(p["marca"]["filo"], "y se marca con un filo alrededor")
    chk(p["marca"]["guardaAntes"].startswith("El sensor viejo"),
        "la pieza guarda el texto de antes", p["marca"]["guardaAntes"])
    # la condición que puso Alberto: la lámina no se mueve
    a, b = d["antesDeMarcar"], p["marca"]
    chk(a["pz"] == b["pzAhora"] and a["otra"] == b["otraAhora"],
        "la marca no mueve el texto de sitio, ni el suyo ni el de al lado",
        json.dumps([a, {"pz": b["pzAhora"], "otra": b["otraAhora"]}]))

    chk(p["globo"]["hay"], "pasar el ratón abre el globo")
    chk(p["globo"]["hay"] and "viejo" in (p["globo"]["texto"] or ""),
        "y el globo enseña lo que decía antes", p["globo"]["texto"])
    chk(p["globo"]["hay"] and "nuevo" not in (p["globo"]["texto"] or ""),
        "sin colar lo que dice ahora, que ya está en la lámina", p["globo"]["texto"])
    chk(p["globo"]["cabe"], "y el globo cabe entero en la pantalla")

    chk(p["otraLamina"]["marcadas"] == 0,
        "al cambiar de lámina la marca no se arrastra",
        str(p["otraLamina"]["marcadas"]))
    chk(not p["otraLamina"]["globo"], "ni el globo")
    chk(p["vuelta"]["marcadas"] == 1, "y al volver, la marca vuelve",
        str(p["vuelta"]["marcadas"]))

    chk(p["barra"]["boton"], "la barra trae la chapa de los cambios")
    chk("1 lámina con cambios" in p["barra"]["texto"],
        "diciendo cuántas láminas del deck se tocaron", p["barra"]["texto"][:110])
    # El bug del 13 de octubre de 2026: la chapa contaba las láminas borradas
    # junto a las vivas y la lista solo enseñaba las vivas, así que prometía
    # más de lo que daba y el cambio más gordo, una sección entera retirada,
    # no se veía en ninguna parte.
    chk("1 borrada" in p["barra"]["texto"],
        "y cuántas se fueron, contadas aparte", p["barra"]["texto"][:110])

    chk(p["lista"]["hay"], "la tecla X abre la lista")
    chk(p["lista"]["filas"] == 2, "con una fila por lámina tocada y por borrada",
        str(p["lista"]["filas"]))
    chk(p["lista"]["idas"] == 1, "la lámina borrada también sale en la lista",
        str(p["lista"]["idas"]))
    chk("La lámina que se fue" in p["lista"]["textoIda"],
        "con su título, para saber cuál se fue", p["lista"]["textoIda"][:70])
    chk(p["lista"]["idaPincha"] is False,
        "y sin destino al que ir, porque ya no existe",
        str(p["lista"]["idaPincha"]))
    chk(p["lista"]["mas"] >= 2 and p["lista"]["menos"] >= 2,
        "y el diff entero, lo añadido y lo quitado",
        "mas=%s menos=%s" % (p["lista"]["mas"], p["lista"]["menos"]))
    chk(p["lista"]["visto"], "con el botón de darlo por visto")

    # --- la tecla Z, que esconde y muestra sin olvidar
    e = p["escondidos"]
    chk(e["marcadas"] == 0, "la tecla Z esconde las marcas de la lámina",
        str(e["marcadas"]))
    chk(not e["globo"], "y con ellas el globo")
    chk(e["chapa"], "pero la chapa de la barra se queda, para saber que hay algo")
    chk(e["apagada"], "apagada, para que se vea que están escondidas")
    chk("escondidos" in e["barra"], "y la barra lo dice con todas las letras",
        e["barra"][:110])
    chk(e["guardado"] == "1", "el estado se recuerda en este deck", e["guardado"])
    # Dos filas: la lámina tocada y la borrada. La lista se abre a propósito,
    # así que enseña las dos aunque las marcas estén escondidas.
    chk(e["lista"] == 2, "la lista de la tecla X sigue abriéndose a propósito",
        str(e["lista"]))
    d2 = p["devueltos"]
    chk(d2["marcadas"] == 1, "la misma tecla las devuelve", str(d2["marcadas"]))
    chk(not d2["apagada"], "y la chapa vuelve a su color")
    chk(d2["guardado"] == "0", "y el estado también se recuerda", d2["guardado"])
    ge = p["guionEscondido"]
    chk(ge["parrafos"] == 0 and ge["mas"] == 0,
        "escondidas, la ventana del guion tampoco pinta el diff",
        "parrafos=%s mas=%s" % (ge["parrafos"], ge["mas"]))

    zg, zv = p["zDesdeGuion"], p["zDesdeGuionVuelta"]
    chk(zg["parrafos"] == 0 and zg["enLamina"] == 0,
        "la tecla Z también funciona desde la ventana del guion",
        "guion=%s lamina=%s" % (zg["parrafos"], zg["enLamina"]))
    chk(zv["parrafos"] == 2 and zv["enLamina"] == 1,
        "y desde ahí las devuelve, en las dos ventanas",
        "guion=%s lamina=%s" % (zv["parrafos"], zv["enLamina"]))

    mt = p["mate"]
    chk(mt["total"] >= 1, "la lámina medida trae matemáticas en su guion",
        str(mt["total"]))
    chk(mt["total"] == mt["conservan"],
        "ningún párrafo del guion pierde sus matemáticas compuestas",
        "con mjx=%s, conservan=%s" % (mt["total"], mt["conservan"]))
    chk(mt["cambiados"] >= 1 and mt["tags"] >= 1,
        "y el que cambió se marca con su etiqueta en vez de repintarse",
        "cambiados=%s tags=%s" % (mt["cambiados"], mt["tags"]))

    chk(p["guion"]["abre"], "la ventana del guion abre")
    chk(p["guion"]["parrafos"] == 2,
        "con los dos párrafos cambiados marcados, el de texto y el de fórmula",
        str(p["guion"]["parrafos"]))
    chk(p["guion"]["mas"] == 1 and p["guion"]["menos"] == 1,
        "y ahí sí se tacha: las palabras nuevas y las quitadas",
        "mas=%s menos=%s" % (p["guion"]["mas"], p["guion"]["menos"]))

    print()
    print("%d fallan" % fallos[0] if fallos[0] else "todas pasan")
    return 1 if fallos[0] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "sesiones/S12-razonamiento-en-el-tiempo/index.html"))
