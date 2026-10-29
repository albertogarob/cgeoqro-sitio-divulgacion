# -*- coding: utf-8 -*-
"""Prueba del reproductor por tramos, midiendo en Chrome headless.

Comprueba lo que de verdad importa y que ninguna otra herramienta ve: que la
barra espaciadora avance de tramo y no de lamina, que el video salte al inicio
del tramo, que al acabar SE CONGELE en vez de repetir, que la tira diga el
nombre y la posicion, y que la tecla V vuelva a empezar el tramo en curso.
"""
import re, subprocess, sys, pathlib, os

SONDA = """.then(async()=>{
  const out=[];
  try {
  await document.fonts.ready; await new Promise(r=>setTimeout(r,500));
  const ok=(q,c,d)=>out.push((c?"pasa  ":"FALLA ")+q+(d?"  ["+d+"]":""));
  const v=document.getElementById('reproductor');
  const barra=document.getElementById('repro-barra');
  const tira={ get textContent(){ return (barra.title||'') + ', ' +
      (document.getElementById('repro-cuenta').textContent||''); } };
  const esperar=ms=>new Promise(r=>setTimeout(r,ms));
  const tecla=k=>document.dispatchEvent(new KeyboardEvent('keydown',
      {key:k, keyCode:k===' '?32:k.toUpperCase().charCodeAt(0), which:k===' '?32:0, bubbles:true}));

  const secs=[...document.querySelectorAll('.slides > section[data-video]')];
  ok("hay laminas con video", secs.length>0, secs.length+" laminas");
  for (const sec of secs){
    const sid=sec.getAttribute('data-sid')||sec.id;
    const tr=[...sec.querySelectorAll('.tramo')];
    if(!tr.length){ out.push("pasa  "+sid+": sin tramos, modo antiguo"); continue; }
    ok(sid+": el primer tramo no es fragmento",
       !tr[0].classList.contains('fragment'));
    ok(sid+": los demas si lo son",
       tr.slice(1).every(e=>e.classList.contains('fragment')), (tr.length-1)+" fragmentos");
    ok(sid+": los tramos no se proyectan",
       getComputedStyle(tr[0]).position==='absolute' &&
       parseFloat(getComputedStyle(tr[0]).left) < -1000);

    Reveal.slide([...document.querySelectorAll('.slides > section')].indexOf(sec));
    await esperar(700);
    ok(sid+": al llegar, arranca el primer tramo",
       v.style.display==='block' && v.currentTime < parseFloat(tr[0].dataset.end),
       "t="+v.currentTime.toFixed(2));
    ok(sid+": la barra de controles esta visible",
       barra.classList.contains('visible'));
    ok(sid+": dice el nombre del tramo y su posicion",
       /, 1 de /.test(tira.textContent), tira.textContent);

    // Espacio: tiene que avanzar de TRAMO, no de lamina.
    const antes=Reveal.getIndices().h;
    tecla(' ');
    await esperar(600);
    ok(sid+": el espacio avanza de tramo, no de lamina",
       Reveal.getIndices().h===antes && /, 2 de /.test(tira.textContent),
       tira.textContent);
    const ini2=parseFloat(tr[1].dataset.start), fin2=parseFloat(tr[1].dataset.end);
    ok(sid+": y el video salta al inicio de ese tramo",
       v.currentTime>=ini2-0.6 && v.currentTime<fin2,
       "t="+v.currentTime.toFixed(2)+" tramo="+ini2+".."+fin2);

    // Al acabar el tramo tiene que quedarse quieto, no repetir.
    //
    // En Chrome headless el video NO se decodifica: se queda en readyState 1 y
    // el seek nunca termina, asi que dejarlo correr hasta el final del tramo no
    // prueba nada. Medido con una sonda: seeking sigue en true a los tres
    // segundos. Asi que se sombrea currentTime con una propiedad propia y se
    // empuja un timeupdate: eso ejercita el vigilante de verdad, que es el
    // codigo que decide parar, sin depender del decodificador.
    let falso=fin2-0.05, pausas=0;
    const pausaReal=v.pause.bind(v);
    Object.defineProperty(v,'currentTime',
      {configurable:true, get:()=>falso, set:x=>{falso=x;}});
    v.pause=()=>{ pausas++; pausaReal(); };
    falso=fin2+0.02;                       // lo cruza
    v.dispatchEvent(new Event('timeupdate'));
    await esperar(120);
    ok(sid+": al cruzar el final del tramo, para",
       pausas>0, "llamadas a pause="+pausas);
    ok(sid+": y se queda clavado dentro del tramo, no en el siguiente",
       falso>=ini2 && falso<=fin2, "t="+falso.toFixed(2)+" tramo="+ini2+".."+fin2);
    falso=fin2+0.5; pausas=0;
    v.dispatchEvent(new Event('timeupdate'));
    await esperar(120);
    ok(sid+": no vuelve a empezar solo (no repite)",
       falso<=fin2, "t="+falso.toFixed(2));

    // V: vuelve a empezar el tramo en curso.
    tecla('v');
    await esperar(400);
    ok(sid+": la tecla V repite el tramo en curso",
       falso < ini2+1.2 && falso>=ini2-0.6, "t="+falso.toFixed(2));
    delete v.currentTime; v.pause=pausaReal;

    // Retroceder: vuelve al tramo anterior.
    Reveal.prev(); await esperar(600);
    ok(sid+": al retroceder vuelve al tramo anterior",
       /, 1 de /.test(tira.textContent), tira.textContent);

    // ---- los controles ------------------------------------------------
    const bot=q=>barra.querySelector('button[data-rb="'+q+'"]');
    const clic=q=>bot(q).dispatchEvent(new MouseEvent('click',{bubbles:true}));
    ok(sid+": estan los seis botones",
       ['prev','play','next','rep','bucle','pantalla'].every(q=>!!bot(q)));
    ok(sid+": en el primer tramo, el de anterior esta apagado",
       bot('prev').disabled && !bot('next').disabled);
    const pista=document.getElementById('repro-pista');
    ok(sid+": la pista tiene una marca por frontera",
       document.querySelectorAll('#repro-marcas i').length === tr.length-1,
       document.querySelectorAll('#repro-marcas i').length+" marcas, "+tr.length+" tramos");
    ok(sid+": el tiempo sale en minutos y segundos",
       /^\d+:\d\d \/ \d+:\d\d$/.test(document.getElementById('repro-tiempo').textContent),
       document.getElementById('repro-tiempo').textContent);

    clic('next'); await esperar(500);
    ok(sid+": el boton de siguiente avanza de tramo",
       /, 2 de /.test(tira.textContent), tira.textContent);
    clic('prev'); await esperar(500);
    ok(sid+": el de anterior vuelve",
       /, 1 de /.test(tira.textContent), tira.textContent);

    // En el ultimo tramo el de siguiente se apaga, para no saltar de lamina.
    for (let k=1;k<tr.length;k++){ clic('next'); await esperar(260); }
    ok(sid+": en el ultimo tramo, el de siguiente esta apagado",
       bot('next').disabled && !bot('prev').disabled, tira.textContent);
    ok(sid+": y no se ha cambiado de lamina",
       (Reveal.getCurrentSlide().getAttribute('data-sid')||'')===sid);
    while (!bot('prev').disabled) { clic('prev'); await esperar(200); }

    // Pausa y reproduccion.
    //
    // El clic se manda sobre el nodo MAS PROFUNDO del boton, capturado antes de
    // esperar, que es lo que hace un raton de verdad: si algo rehace el icono
    // entre que se aprieta y se suelta, ese nodo queda desprendido y el clic se
    // pierde. Asi fallaba el boton para Alberto, y mandando el clic al <button>
    // la prueba no lo veia.
    //
    // En headless el repintado cuadro a cuadro no corre, asi que entre apretar
    // y soltar se empuja un timeupdate, que es lo que dispara el repintado. Sin
    // esto la prueba pasaba con el boton roto.
    const hondo = () => bot('play').querySelector('path') || bot('play');
    const clicHondo = async () => {
      const n = hondo();
      for (let k = 0; k < 3; k++) {
        v.dispatchEvent(new Event('timeupdate'));
        await esperar(60);
      }
      n.dispatchEvent(new MouseEvent('click', {bubbles:true}));
      await esperar(260);
    };
    const pausado0=v.paused;
    await clicHondo();
    ok(sid+": el boton de pausa cambia el estado", v.paused !== pausado0,
       "antes="+pausado0+" despues="+v.paused);
    await clicHondo();
    ok(sid+": y vuelve a cambiarlo", v.paused === pausado0);
    ok(sid+": el icono dice lo que hace el boton",
       (v.paused && bot('play').title.indexOf('Reproducir')>=0) ||
       (!v.paused && bot('play').title.indexOf('Pausar')>=0),
       "pausado="+v.paused+" title="+bot('play').title);

    // Pantalla completa: existe, y pedirla no rompe nada. Que el navegador la
    // conceda no se puede probar en headless sin gesto del usuario.
    ok(sid+": esta el boton de pantalla completa", !!bot('pantalla'));

    // Cambiar de lamina con la pantalla completa puesta dejaba la pantalla EN
    // BLANCO: lo que se ve a pantalla completa es la caja #repro-lleno, que
    // solo lleva el video y la barra, asi que la lamina nueva se queda detras.
    // Alberto lo vio en el aula el 6 de octubre de 2026.
    //
    // Headless no concede la pantalla completa sin gesto del usuario, asi que
    // se sombrean requestFullscreen, exitFullscreen y fullscreenElement. Lo
    // que se prueba no es que el navegador la conceda, es que al cambiar de
    // lamina se SALGA, que es justo lo que faltaba.
    {
      let fsel = null, salidas = 0;
      const defFs = Object.getOwnPropertyDescriptor(document, 'fullscreenElement') ||
                    Object.getOwnPropertyDescriptor(Document.prototype, 'fullscreenElement');
      const defReq = Element.prototype.requestFullscreen;
      Object.defineProperty(document, 'fullscreenElement',
        {configurable:true, get:()=>fsel});
      Element.prototype.requestFullscreen = function () {
        fsel = this;
        document.dispatchEvent(new Event('fullscreenchange'));
        return Promise.resolve();
      };
      document.exitFullscreen = function () {
        salidas++; fsel = null;
        document.dispatchEvent(new Event('fullscreenchange'));
        return Promise.resolve();
      };
      clic('pantalla'); await esperar(300);
      ok(sid+": pedir pantalla completa no rompe la barra",
         barra.classList.contains('visible') && !!bot('play'));
      const caja = document.getElementById('repro-lleno');
      ok(sid+": la pantalla completa mete el video y la barra en su caja",
         !!caja && caja.contains(v) && caja.contains(barra));
      ok(sid+": y el navegador la tiene como elemento a pantalla completa",
         document.fullscreenElement === caja);
      Reveal.next(); await esperar(500);
      ok(sid+": al cambiar de lamina se sale de pantalla completa",
         salidas >= 1, "salidas="+salidas);
      ok(sid+": y la caja de pantalla completa deja de existir",
         !document.getElementById('repro-lleno'));
      ok(sid+": el video vuelve a colgar del cuerpo, no de la caja",
         v.parentElement === document.body);
      Reveal.prev(); await esperar(500);
      delete document.exitFullscreen;
      Element.prototype.requestFullscreen = defReq;
      if (defFs) Object.defineProperty(document, 'fullscreenElement', defFs);
    }

    // El número de cada tramo, en su banda de la pista: es lo que ata el guion,
    // que habla de "el tramo tres", con lo que se ve.
    const bolas = [...document.querySelectorAll('#repro-nums i')];
    ok(sid+": la pista lleva el numero de cada tramo",
       bolas.length === tr.length &&
       bolas.map(e=>e.textContent).join(',') === tr.map((_,k)=>k+1).join(','),
       bolas.map(e=>e.textContent).join(','));
    ok(sid+": y marca el tramo en curso",
       bolas.filter(e=>e.classList.contains('aqui')).length === 1 &&
       bolas[0].classList.contains('aqui'),
       "marcados="+bolas.filter(e=>e.classList.contains('aqui')).map(e=>e.textContent).join(','));

    // Parado al final de un tramo, play pasa al SIGUIENTE, no reinicia.
    {
      const fin0 = parseFloat(tr[0].dataset.end);
      let f3 = fin0 - 0.02;
      Object.defineProperty(v,'currentTime',
        {configurable:true, get:()=>f3, set:x=>{f3=x;}});
      v.pause();
      f3 = fin0 + 0.02;
      clic('play'); await esperar(400);
      ok(sid+": al final de un tramo, play pasa al siguiente",
         /, 2 de /.test(tira.textContent), tira.textContent);
      delete v.currentTime;
      // Y en el ultimo no hay siguiente: ahi repite, para que play haga algo.
      while (!bot('next').disabled) { clic('next'); await esperar(220); }
      const iniN = parseFloat(tr[tr.length-1].dataset.start);
      const finN = parseFloat(tr[tr.length-1].dataset.end);
      let f4 = finN + 0.02;
      Object.defineProperty(v,'currentTime',
        {configurable:true, get:()=>f4, set:x=>{f4=x;}});
      v.pause();
      clic('play'); await esperar(400);
      ok(sid+": en el ultimo tramo, play lo repite y no cambia de lamina",
         f4 <= iniN + 0.6 && (Reveal.getCurrentSlide().getAttribute('data-sid')||'')===sid,
         "t="+f4.toFixed(2)+" inicio="+iniN);
      delete v.currentTime;
      while (!bot('prev').disabled) { clic('prev'); await esperar(200); }
    }

    // El nombre del tramo no se escribe en la barra, para que no la alargue.
    ok(sid+": el nombre del tramo va en el title, no escrito",
       (barra.title||'').length > 3 &&
       !document.getElementById('repro-nombre'), "title="+barra.title);

    // Y la barra no se sale de la lamina.
    // Contra la ventana, no contra .reveal: en el paquete .reveal mide otra
    // cosa y la comprobacion fallaba sin que nada estuviera mal.
    const rb=barra.getBoundingClientRect();
    ok(sid+": la barra cabe dentro de la pantalla",
       rb.left >= -1 && rb.right <= window.innerWidth+1,
       "barra="+Math.round(rb.left)+".."+Math.round(rb.right)+
       " ventana=0.."+window.innerWidth);
    ok(sid+": y nada de dentro la desborda",
       barra.scrollWidth <= barra.clientWidth+1,
       "contenido="+barra.scrollWidth+" caja="+barra.clientWidth);

    // El bucle: se enciende, y al cruzar el final vuelve a empezar en vez de
    // congelarse. Se mide sombreando currentTime, porque headless no decodifica.
    clic('bucle'); await esperar(250);
    ok(sid+": el boton de bucle se enciende",
       bot('bucle').classList.contains('encendido'));
    const ini1=parseFloat(tr[0].dataset.start), fin1=parseFloat(tr[0].dataset.end);
    let f2=ini1;
    Object.defineProperty(v,'currentTime',
      {configurable:true, get:()=>f2, set:x=>{f2=x;}});
    f2=fin1+0.02;
    v.dispatchEvent(new Event('timeupdate'));
    await esperar(150);
    ok(sid+": con el bucle encendido vuelve al principio del tramo",
       f2 <= ini1+0.2, "t="+f2.toFixed(2)+" inicio="+ini1);
    delete v.currentTime;
    clic('bucle'); await esperar(200);
    ok(sid+": y se apaga", !bot('bucle').classList.contains('encendido'));
  }
  } catch (err) { out.push("FALLA la sonda reventó: " + (err && err.message)); }
  const d=document.createElement('div'); d.id='diag';
  d.textContent=out.join(' || '); document.body.appendChild(d);
});"""

p = pathlib.Path(sys.argv[1]).resolve()
# El deck arranca con plugins:[RevealNotes] y el paquete con plugins:[], porque
# empaquetar.py quita el guion de orador. La sonda se engancha a los dos.
texto = p.read_text(encoding="utf-8")
for ancla in ("plugins:[RevealNotes]});", "plugins:[]});"):
    if ancla in texto:
        texto = texto.replace(ancla, ancla[:-1] + SONDA, 1)
        break
else:
    print("  FALLA no encuentro dónde enganchar la sonda"); sys.exit(1)
s = texto
tmp = p.with_name("_tramos.html"); tmp.write_text(s, encoding="utf-8")
try:
    r = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                        "--autoplay-policy=no-user-gesture-required",
                        "--window-size=1280,720", "--virtual-time-budget=90000",
                        "--dump-dom", "file://" + str(tmp)],
                       capture_output=True, text=True, timeout=300)
    m = re.search(r'<div id="diag">(.*?)</div>', r.stdout.replace("\n", " "), re.S)
    salida = m.group(1) if m else "FALLA no se pudo medir: la sonda no dejó resultado"
finally:
    if tmp.exists(): os.unlink(tmp)
mal = 0
partes = salida.split(" || ")
if len(partes) < 10:
    print("  FALLA la sonda no llegó al final: solo", len(partes), "comprobaciones")
    mal += 1
for x in partes:
    print("  ", x)
    if x.startswith("FALLA"): mal += 1
print(f"\n{mal} fallan" if mal else "\ntodas pasan")
sys.exit(1 if mal else 0)
