#!/usr/bin/env python3
r"""Prueba de regresión de la sincronía del guion con la lámina, la tecla Y.

    python3 tools/prueba-sincronia.py [sesiones/SNN-.../index.html]

Mide en Chrome headless lo que se ve en la lámina, no el estado interno de
nadie: la opacidad calculada de cada pieza y el filo de los dibujos. Es lo
único que dice si el grupo va a ver resaltado lo que Alberto está diciendo.

El camino que ejercita es el de verdad, de punta a punta: se abre el apuntador
con la tecla T, se mueve de párrafo con la flecha abajo DENTRO de su ventana, y
se mide la lámina. `window.open` se suplanta por un iframe, igual que en
`tools/prueba-revisar.py`, con el `document` como getter porque
`document.write` lo vuelve a abrir.

Lo que comprueba:

  * que apagada, que es como viene de fábrica, la lámina se vea intacta: ni la
    clase `sinc` en el `<html>` ni una sola pieza atenuada. Es la condición que
    permite que esto viva en el tema de las 30 sesiones;
  * que la tecla Y la encienda y la vuelva a apagar, con su aviso;
  * que lo resaltado sea EXACTAMENTE la pieza que nombra el `data-sinc` del
    párrafo en curso, y que las demás queden atenuadas;
  * que la flecha abajo mueva el resaltado al párrafo siguiente;
  * que un dibujo se resalte con su filo y no con la barra del costado;
  * que una lámina sin anclas no atenúe nada, aun encendida;
  * que al cambiar de lámina no quede resaltado nada de la anterior;
  * y que el encendido se recuerde en localStorage.
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
  var o={pasos:[]};
  function dormir(ms){return new Promise(function(r){setTimeout(r,ms)})}

  // La lámina en curso, medida: qué piezas hay, cuál está resaltada y con qué.
  function est(){
    var s=document.querySelector('.reveal section.present');
    if(!s) return {sid:null};
    var pz=[].slice.call(s.querySelectorAll('[data-pieza]'));
    return {
      sid:s.getAttribute('data-sid'),
      clase:document.documentElement.classList.contains('sinc'),
      piezas:pz.map(function(e){
        var c=getComputedStyle(e);
        var cu=s.querySelector('.cuerpo');
        var re=e.getBoundingClientRect();
        var off=parseFloat(c.outlineOffset)||0, an=parseFloat(c.outlineWidth)||0;
        var rc=cu?cu.getBoundingClientRect():null;
        return {n:e.getAttribute('data-pieza'), tag:e.tagName.toLowerCase(),
                op:Math.round(parseFloat(c.opacity)*100)/100,
                aqui:e.classList.contains('sinc-aqui'),
                filo:c.outlineStyle!=='none'&&parseFloat(c.outlineWidth)>0,
                ancho:an, color:c.outlineColor, recorta:cu?getComputedStyle(cu).overflow:null,
                // ¿cabe el recuadro entero dentro de lo que NO recorta?
                cabe:(!rc||getComputedStyle(cu).overflow!=='hidden')
                     ? true
                     : (re.right+off+an<=rc.right+0.5 && re.left-off-an>=rc.left-0.5),
                // el fondo del rojo diluido, y la viñeta en rojo vivo
                fondo:c.backgroundColor,
                punto:(e.tagName.toLowerCase()==='li'
                       ? getComputedStyle(e,'::marker').color : null),
                barra:getComputedStyle(e,'::before').content!=='none'};
      }),
      // Las líneas del bloque de código: cuál está encendida y con qué
      // opacidad. Es lo único que dice si el resaltado por líneas funciona.
      codigo:(function(){
        var pre=s.querySelector('pre[data-pieza]');
        if(!pre) return null;
        return {op:Math.round(parseFloat(getComputedStyle(pre).opacity)*100)/100,
                aqui:pre.classList.contains('sinc-aqui'),
                hay:pre.classList.contains('sinc-cl-hay'),
                lineas:[].slice.call(pre.querySelectorAll('.cl[data-cl]')).map(function(l){
                  var c=getComputedStyle(l);
                  return {n:l.getAttribute('data-cl'),
                          on:l.classList.contains('sinc-cl'),
                          op:Math.round(parseFloat(c.opacity)*100)/100,
                          fondo:c.backgroundColor};
                })};
      })(),
      aviso:(function(){var a=document.getElementById('sincAviso');
             return a?Math.round(parseFloat(getComputedStyle(a).opacity)*100)/100:null})(),
      guardado:(function(){try{return localStorage.getItem('sinc:activa')}catch(e){return 'x'}})()
    };
  }

  function teclaDeck(k,code){
    var e=new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true});
    Object.defineProperty(e,'keyCode',{get:function(){return code}});
    Object.defineProperty(e,'which',{get:function(){return code}});
    document.dispatchEvent(e);
  }

  window.addEventListener('load', async function(){
    await dormir(1800);
    try{localStorage.removeItem('sinc:activa')}catch(e){}

    /* Las transiciones se desactivan antes de medir, y no es cosmética: con
       --virtual-time-budget el reloj de las transiciones de Chrome headless no
       avanza, así que getComputedStyle devuelve el valor de PARTIDA y una
       opacidad que en pantalla acaba en 0.32 se lee como 1. Medido el 12 de
       octubre de 2026, depurando esta misma prueba: con la transición puesta
       daba 1, y quitándola 0.32, con el mismo CSS. Lo que se quiere medir aquí
       es el estado al que llega la lámina, no la animación. */
    var st=document.createElement('style');
    st.textContent='*{transition:none !important;animation:none !important}';
    document.head.appendChild(st);

    // La lámina con más anclas distintas: la que de verdad ejercita el motor.
    var secs=[].slice.call(document.querySelectorAll('.reveal .slides > section'));
    var mejor=null, mejorN=-1, conSvg=null, conCod=null;
    secs.forEach(function(s){
      var ps=[].slice.call(s.querySelectorAll('aside.notes p[data-sinc]'));
      var set={}; ps.forEach(function(p){set[p.getAttribute('data-sinc')]=1});
      var n=Object.keys(set).length;
      if(n>mejorN && s.querySelector('[data-pieza]')){mejorN=n; mejor=s}
      if(!conSvg && s.querySelector('svg[data-pieza]') && ps.length) conSvg=s;
      if(!conCod && s.querySelector('pre[data-pieza] .cl[data-cl]')
         && s.querySelector('aside.notes p[data-sinc-cl]')) conCod=s;
    });
    var sinAncla=secs.filter(function(s){
      return s.getAttribute('data-sid') && !s.querySelector('aside.notes p[data-sinc]')
             && s.querySelector('aside.notes p');
    })[0];
    o.hayLamina=!!mejor; o.haySvg=!!conSvg; o.haySinAncla=!!sinAncla;
    o.hayCodigo=!!conCod;
    if(!mejor){ fin(); return; }

    // El apuntador, con window.open suplantada por un iframe.
    var marco=document.createElement('iframe');
    marco.style.cssText='position:fixed;left:-3000px;width:600px;height:900px';
    document.body.appendChild(marco);
    var vent={closed:false, get document(){return marco.contentDocument},
              focus:function(){}, close:function(){vent.closed=true},
              scrollTo:function(){}, addEventListener:function(){},
              get scrollY(){return 0}, innerHeight:900};
    window.open=function(){vent.closed=false; return vent};

    function irA(sec){
      Reveal.slide([].indexOf.call(sec.parentNode.children,sec));
      return dormir(300);
    }
    function teclaAp(k){
      var d=marco.contentDocument;
      d.dispatchEvent(new KeyboardEvent('keydown',{key:k,bubbles:true,cancelable:true}));
      return dormir(160);
    }
    function parrAp(){
      var d=marco.contentDocument;
      var p=d.querySelector('#texto p.actual');
      return p?{i:[].indexOf.call(d.querySelectorAll('#texto p'),p),
                sinc:p.getAttribute('data-sinc')||'',
                cl:p.getAttribute('data-sinc-cl')||''}:null;
    }

    await irA(mejor);
    teclaDeck('t',84);
    await dormir(500);
    o.apuntadorAbierto=!!(marco.contentDocument&&marco.contentDocument.getElementById('texto'));
    if(!o.apuntadorAbierto){ fin(); return; }

    // 1. apagada de fábrica
    o.pasos.push(['apagada', est(), parrAp()]);

    // 2. encender con Y desde el deck
    teclaDeck('y',89);
    await dormir(250);
    o.pasos.push(['encendida', est(), parrAp()]);

    // 3. avanzar párrafos hasta dar con dos anclas distintas
    var vistos=[];
    for(var i=0;i<8;i++){
      await teclaAp('ArrowDown');
      var p=parrAp();
      if(!p) break;
      vistos.push(['paso'+i, est(), p]);
      if(p.sinc && vistos.filter(function(v){return v[2].sinc}).length>=3) break;
    }
    vistos.forEach(function(v){o.pasos.push(v)});

    // 4. un dibujo resaltado
    if(conSvg){
      await irA(conSvg);
      var d=marco.contentDocument;
      var ps=[].slice.call(d.querySelectorAll('#texto p'));
      var k=-1;
      for(var j=0;j<ps.length;j++){
        var sc=ps[j].getAttribute('data-sinc')||'';
        var tiene=sc.split(/\s+/).some(function(n){
          return conSvg.querySelector('svg[data-pieza="'+n+'"]')});
        if(tiene){k=j;break}
      }
      for(var m=0;m<k;m++) await teclaAp('ArrowDown');
      o.pasos.push(['dibujo', est(), parrAp()]);
    }

    // 4 bis. una lámina de código: el bloque no se atenúa nunca, y dentro se
    // encienden solo las líneas del párrafo en curso.
    if(conCod){
      await irA(conCod);
      var dc=marco.contentDocument;
      var pc=[].slice.call(dc.querySelectorAll('#texto p'));
      var kc=-1;
      for(var jc=0;jc<pc.length;jc++){
        if(pc[jc].getAttribute('data-sinc-cl')){kc=jc;break}
      }
      // Se recorre el guion ENTERO de la lámina de código, guardando el
      // estado en cada párrafo. Hace falta así porque la comprobación de que
      // el bloque nunca se atenúa solo vale en un párrafo que resalte OTRA
      // pieza con la sincronía ya encendida; medida antes de encenderla
      // pasaba en vacío, y la mutación que quitaba la regla no se cazaba.
      for(var mc=0;mc<pc.length;mc++){
        o.pasos.push(['cod'+mc, est(), parrAp()]);
        await teclaAp('ArrowDown');
      }
    }

    // 5. una lámina sin anclas, con la sincronía encendida
    if(sinAncla){ await irA(sinAncla); o.pasos.push(['sinAncla', est(), parrAp()]); }

    // 6. volver y comprobar que no arrastró nada
    await irA(mejor);
    o.pasos.push(['vuelta', est(), parrAp()]);

    // 7. apagar
    teclaDeck('y',89);
    await dormir(250);
    o.pasos.push(['apagada2', est(), parrAp()]);
    fin();
  });

  function fin(){
    var d=document.createElement('div'); d.id='diag';
    d.textContent=JSON.stringify(o); document.body.appendChild(d);
  }
})();
</script>"""


def medir(ruta):
    p = pathlib.Path(ruta).resolve()
    txt = p.read_text(encoding="utf-8")
    if "</body>" not in txt:
        return None, "el archivo no tiene </body>"
    tmp = p.with_name("_sincronia.html")
    tmp.write_text(txt.replace("</body>", SONDA + "</body>"), encoding="utf-8")
    perfil = tempfile.mkdtemp(prefix="sincronia-")
    try:
        r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                            "--allow-file-access-from-files", "--user-data-dir=" + perfil,
                            "--window-size=1600,900", "--virtual-time-budget=40000",
                            "--dump-dom", "file://" + str(tmp)],
                           capture_output=True, text=True, timeout=180)
        m = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace(chr(10), " "), re.S)
        if not m:
            return None, "la sonda no devolvió nada: " + r.stderr[-500:]
        return json.loads(m.group(1)), None
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

    # Un deck sin anclas es un estado legítimo, no un fallo: las sesiones 1 a 11
    # se generaron antes de que esto existiera y `tools/anclas.py` no ha pasado
    # por ellas. Lo que sí hay que comprobar ahí es que el deck no se rompa.
    if not d.get("hayLamina"):
        print("no aplica  este deck no tiene anclas: tools/anclas.py no ha pasado por él")
        e0 = (d.get("pasos") or [[None, {"piezas": [], "clase": False}]])[0][1]
        chk(not e0.get("clase"), "y sin anclas no se enciende la clase de sincronía")
        print()
        print("sin anclas: el deck no se rompe, pero la sincronía no resalta nada")
        return 0
    chk(d.get("hayLamina"), "el deck trae láminas con anclas")
    chk(d.get("apuntadorAbierto"), "la tecla T abre el apuntador")
    pasos = {p[0]: (p[1], p[2]) for p in d.get("pasos", [])}
    if "apagada" not in pasos:
        print("FALLA  la sonda no llegó a medir ningún paso")
        return 1

    # --- apagada de fábrica: el deck intacto
    e0 = pasos["apagada"][0]
    chk(not e0["clase"], "apagada, el <html> no lleva la clase de sincronía")
    chk(all(p["op"] == 1 for p in e0["piezas"]),
        "apagada, ninguna pieza de la lámina está atenuada",
        str([(p["n"], p["op"]) for p in e0["piezas"] if p["op"] != 1]))
    chk(not any(p["aqui"] for p in e0["piezas"]),
        "apagada, ninguna pieza queda marcada")

    # --- encendida
    #
    # Ojo con qué se le exige aquí. La clase `sinc` se enciende cuando hay una
    # pieza que resaltar, no al pulsar la tecla: un párrafo sin ancla deja la
    # lámina intacta a propósito, que es lo que permite que esto viva en el
    # tema de las 30 sesiones. Así que al pulsar Y se comprueba la preferencia
    # y el aviso, y **la clase se comprueba en el primer paso cuyo párrafo sí
    # trae ancla**. La versión anterior la exigía ya en este punto y pasaba por
    # azar, según si el primer párrafo de la lámina elegida tenía ancla;
    # cuando la sesión 12 cambió de láminas, dejó de tenerla y salió en rojo
    # algo que funcionaba.
    e1, p1 = pasos["encendida"]
    chk(e1["guardado"] == "1", "la tecla Y la enciende y lo recuerda", e1["guardado"])
    chk(e1["aviso"] == 1, "con su aviso en pantalla", e1["aviso"])
    conAncla = [pasos[k] for k in pasos
                if k.startswith("paso") and (pasos[k][1] or {}).get("sinc")]
    chk(bool(conAncla) and conAncla[0][0]["clase"],
        "y en cuanto el párrafo trae ancla, el <html> lleva la clase",
        "pasos con ancla: %d" % len(conAncla))

    # --- lo resaltado es EXACTAMENTE lo que pide el párrafo
    revisados = 0
    tocados = 0
    puntos = [0]
    for nombre, (e, p) in pasos.items():
        if nombre in ("apagada", "apagada2", "sinAncla") or not p:
            continue
        if not e["clase"]:
            continue
        pide = set((p.get("sinc") or "").split())
        if not pide:
            continue
        marcadas = set(x["n"] for x in e["piezas"] if x["aqui"])
        chk(marcadas == pide,
            "en %s se resalta exactamente la pieza del párrafo" % nombre,
            "pide %s, marca %s" % (sorted(pide), sorted(marcadas)))
        # El bloque de código queda fuera: desde el 13 de octubre de 2026 no se
        # atenúa nunca, porque es lo que la lámina viene a enseñar y es lo que
        # Alberto señala mientras habla de las viñetas. Lo que sí se atenúa
        # dentro de él son sus líneas, y eso se comprueba aparte.
        atenuadas = [x["n"] for x in e["piezas"]
                     if not x["aqui"] and x["op"] == 1 and x["tag"] != "pre"]
        chk(not atenuadas, "en %s las demás piezas quedan atenuadas" % nombre,
            "sin atenuar: %s" % atenuadas)
        # El resaltado del texto: fondo del rojo diluido, viñeta en rojo vivo y
        # ninguna barra al costado, que es lo que Alberto rechazó el 12 de
        # octubre de 2026 por quedar pegada al círculo de la viñeta.
        txt = [x for x in e["piezas"] if x["tag"] in ("li", "p") and x["aqui"]]
        if txt:
            chk(all(x["fondo"].replace(" ", "").startswith("rgba(224,27,61")
                    for x in txt),
                "en %s la pieza de texto lleva el fondo del rojo vivo" % nombre,
                str([x["fondo"] for x in txt]))
            chk(not any(x["barra"] for x in txt),
                "en %s no lleva barra al costado" % nombre)
            tocados += 1
        lis = [x for x in txt if x["tag"] == "li"]
        if lis:
            chk(all(x["punto"].replace(" ", "") == "rgb(224,27,61)" for x in lis),
                "en %s la viñeta resaltada tiene su punto en rojo vivo" % nombre,
                str([x["punto"] for x in lis]))
            puntos[0] += 1
        revisados += 1
    chk(revisados >= 2, "se midieron al menos dos párrafos distintos",
        "fueron %d" % revisados)
    chk(tocados >= 1, "y al menos uno con una pieza de texto resaltada",
        "fueron %d" % tocados)
    chk(puntos[0] >= 1, "y al menos uno con una viñeta resaltada",
        "fueron %d" % puntos[0])

    # --- el resaltado se mueve con el párrafo
    conAncla = [(n, v) for n, v in pasos.items()
                if n.startswith("paso") and v[1] and (v[1].get("sinc") or "")]
    distintas = set(tuple(sorted(x["n"] for x in v[0]["piezas"] if x["aqui"]))
                    for n, v in conAncla)
    chk(len(distintas) >= 2, "el resaltado cambia al avanzar de párrafo",
        str(sorted(distintas)))

    # --- un dibujo lleva filo, no barra
    if "dibujo" in pasos:
        e, p = pasos["dibujo"]
        svgs = [x for x in e["piezas"] if x["tag"] == "svg" and x["aqui"]]
        chk(bool(svgs), "el dibujo de la lámina se resalta",
            str([(x["n"], x["tag"], x["aqui"]) for x in e["piezas"]]))
        if svgs:
            chk(all(x["filo"] for x in svgs), "y lleva su recuadro alrededor")
            chk(not any(x["barra"] for x in svgs), "y no la barra del costado")
            # El recuadro tiene que verse ENTERO. Alberto lo señaló el 12 de
            # octubre de 2026: con el cuerpo recortando y el dibujo llegando a
            # su borde, el lado derecho desaparecía.
            chk(all(x["recorta"] != "hidden" for x in svgs),
                "con la sincronía puesta, el cuerpo deja de recortar",
                str([x["recorta"] for x in svgs]))
            chk(all(x["cabe"] for x in svgs),
                "así que el recuadro se ve entero, sin cortarse por la derecha",
                str([(x["n"], x["cabe"]) for x in svgs]))
            chk(all(x["ancho"] >= 4 for x in svgs),
                "el trazo es grueso, de 4 px o más",
                str([x["ancho"] for x in svgs]))
            chk(all(x["color"].replace(" ", "") == "rgb(224,27,61)" for x in svgs),
                "y del rojo fuerte de los recuadros de los diagramas",
                str([x["color"] for x in svgs]))
        chk(not any(x["fondo"].replace(" ", "") not in
                    ("rgba(0,0,0,0)", "transparent") for x in svgs),
            "y el dibujo no lleva fondo, que se le vería por detrás",
            str([x["fondo"] for x in svgs]))
        otras = [x for x in e["piezas"] if x["tag"] in ("li", "p") and x["aqui"]]
        if otras:
            # Ni barra ni recuadro: Alberto rechazó la barra el 12 de octubre de
            # 2026 por quedar pegada al círculo de la viñeta, y el recuadro no
            # cabe con 3 px entre viñetas.
            chk(not any(x["barra"] for x in otras),
                "la pieza de texto NO lleva barra al costado")
            chk(all(x["fondo"].replace(" ", "").startswith("rgba(224,27,61")
                    for x in otras),
                "lleva el fondo del rojo de los recuadros, diluido",
                str([x["fondo"] for x in otras]))
        lis = [x for x in e["piezas"] if x["tag"] == "li" and x["aqui"]]
        if lis:
            chk(all(x["punto"].replace(" ", "") == "rgb(224,27,61)" for x in lis),
                "y su propia viñeta en el rojo vivo",
                str([x["punto"] for x in lis]))
        apagadas = [x for x in e["piezas"] if x["tag"] in ("li", "p") and not x["aqui"]]
        if apagadas:
            chk(not any(x["fondo"].replace(" ", "").startswith("rgba(224,27,61")
                        for x in apagadas),
                "y la pieza que no se está diciendo no lleva fondo",
                str([x["fondo"] for x in apagadas]))

    # --- el bloque de código: nunca atenuado, y con sus líneas encendidas
    if d.get("hayCodigo"):
        cods = [pasos[k][0] for k in pasos if k.startswith("cod")]
        cods = [e for e in cods if e and e.get("codigo")]
        # El momento que importa: la sincronía encendida y la pieza en curso NO
        # es el bloque de código. Ahí el bloque tiene que seguir a opacidad 1.
        otros = [e for e in cods if e["clase"] and not e["codigo"]["aqui"]]
        chk(bool(otros), "hay algún párrafo que resalta otra pieza de la lámina de código",
            "%d de %d" % (len(otros), len(cods)))
        chk(bool(otros) and all(e["codigo"]["op"] == 1 for e in otros),
            "el bloque de código no se atenúa aunque no sea la pieza en curso",
            "opacidades %s" % [e["codigo"]["op"] for e in otros])
        # El par (estado, párrafo) del primer paso cuyo párrafo pide líneas,
        # para comparar lo pedido con lo encendido EN ESE MISMO instante.
        par = next(((pasos[k][0], pasos[k][1]) for k in sorted(pasos)
                    if k.startswith("cod") and (pasos[k][1] or {}).get("cl")), None)
        ec = par[0] if par else None
        if ec and ec.get("codigo"):
            c = ec["codigo"]
            pedidas = par[1]["cl"].split()
            enc = [l["n"] for l in c["lineas"] if l["on"]]
            chk(bool(pedidas), "el guion ancla algún párrafo a líneas concretas",
                "data-sinc-cl=%r" % par[1]["cl"])
            chk(sorted(enc) == sorted(pedidas),
                "se encienden EXACTAMENTE las líneas que nombra el párrafo",
                "pide %s, enciende %s" % (pedidas, enc))
            chk(c["hay"], "el bloque se marca como que tiene líneas encendidas")
            apagadas = [l for l in c["lineas"] if not l["on"]]
            chk(bool(apagadas) and all(l["op"] < 0.6 for l in apagadas),
                "las demás líneas del bloque quedan atenuadas",
                "opacidades %s" % [l["op"] for l in apagadas][:6])
            fondos = [l["fondo"] for l in c["lineas"] if l["on"]]
            chk(all("rgba(224, 27, 61" in (f or "") for f in fondos) and bool(fondos),
                "la línea encendida lleva el fondo rojo de la sincronía",
                "fondos %s" % fondos)
        else:
            chk(False, "algún párrafo enciende líneas del bloque", "ninguno lo hizo")
    else:
        print("no aplica  este deck no tiene láminas de código con líneas ancladas")

    # --- una lámina sin anclas no se toca
    if "sinAncla" in pasos:
        e = pasos["sinAncla"][0]
        chk(not e["clase"], "una lámina sin anclas no atenúa nada, aun encendida")
        chk(all(p["op"] == 1 for p in e["piezas"]),
            "y sus piezas quedan a plena opacidad")

    # --- al volver no arrastra lo de la lámina anterior
    if "vuelta" in pasos:
        e, p = pasos["vuelta"]
        pide = set((p.get("sinc") or "").split()) if p else set()
        marcadas = set(x["n"] for x in e["piezas"] if x["aqui"])
        chk(marcadas <= pide or not marcadas,
            "al cambiar de lámina no queda resaltado nada ajeno",
            "marca %s, el párrafo pide %s" % (sorted(marcadas), sorted(pide)))

    # --- apagar lo deja como estaba
    e2 = pasos["apagada2"][0]
    chk(not e2["clase"], "la tecla Y la vuelve a apagar")
    chk(all(p["op"] == 1 for p in e2["piezas"]),
        "y la lámina queda otra vez intacta",
        str([(p["n"], p["op"]) for p in e2["piezas"] if p["op"] != 1]))
    chk(not any(p["aqui"] for p in e2["piezas"]), "sin ninguna pieza marcada")
    chk(e2["guardado"] == "0", "y el apagado se recuerda", e2["guardado"])

    print()
    print("%d fallan" % fallos[0] if fallos[0] else "todas pasan")
    return 1 if fallos[0] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "sesiones/S12-razonamiento-en-el-tiempo/index.html"))
