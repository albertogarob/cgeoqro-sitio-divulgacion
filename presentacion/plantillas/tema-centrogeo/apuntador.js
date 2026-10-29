/* Apuntador para presentar sin que se note la lectura.
   Tecla T sobre el deck. Abre una ventana con el guion de la diapositiva
   actual en columna estrecha y tipografía grande.

   El motivo de la columna estrecha: lo que delata a quien lee no es mirar
   hacia abajo, es el barrido horizontal del ojo. En líneas de unos 40
   caracteres la vista abarca el renglón completo de un vistazo y el
   movimiento ocular es casi imperceptible en cámara.

   Hay dos clases de ventana y la tecla V alterna entre ellas, recordando la
   elección:

   Emergente, la de fábrica. Se puede mover y redimensionar a gusto, incluso
   maximizar, y su tamaño y su posición se recuerdan para la próxima vez. Lleva
   la barra con el about:blank, que Chrome no deja quitar por seguridad.

   Flotante. Es una ventana de imagen sobre imagen (Document Picture-in-Picture):
   no lleva barra de direcciones y se queda por encima de las demás ventanas,
   Zoom incluido. A cambio, su posición la decide el navegador y no se puede
   maximizar: tiene su propio tamaño máximo y su barra de título la dibuja el
   compositor de vídeo, así que al forzarla se ve rota.

   La ventana emergente se abre centrada y pegada al borde superior, debajo de la webcam,
   para que el ángulo entre el texto y el lente sea mínimo. La desviación que más
   se nota no es la vertical sino la horizontal: con la ventana en una esquina, a
   60 cm de un monitor de 24 pulgadas, la mirada se va unos 17 grados de lado,
   más del doble que los 8 que costaba mirar hacia abajo.

   Por lo mismo el renglón de lectura va pegado al margen superior, y el título
   de la lámina y los seis relojes al pie: el texto se lee todo el tiempo y lo
   demás se mira de vez en cuando, así que la mirada que baja es la ocasional, no
   la continua. Debajo del párrafo en curso queda todo lo que falta por decir,
   que es lo que evita trabarse; lo que se pierde de vista es lo ya dicho.

   Lee siempre el guion del deck, nunca la reescritura que viva en el navegador
   de la vista de revisión: lo que se presenta tiene que ser exactamente lo que
   está en el archivo, para no leer en clase algo que nunca se aplicó al HTML.

   Encima de los relojes van dos barras de avance: la de la lámina, que se llena
   según se recorre su guion y se pone ámbar si la lámina se pasa de su tiempo
   estimado, y la del deck entero. Las dos miden material recorrido, no tiempo,
   así que se calculan sobre la estimación sin corregir por el ritmo.

   El pie lleva seis relojes en tres grupos de dos, separados por un filete, en
   este orden, que lo fijó Alberto: hora y clase, el reloj de pared, o sea la hora
   del sistema y lo que falta para la hora de salida; lámina y sesión, los dos
   cronómetros, el tiempo en la diapositiva actual, que vuelve a cero en cada
   cambio y se enciende en color si la lámina declara duración con data-min y se
   pasa, y el tiempo desde que se abrió el apuntador; y guion y holgura, el ritmo,
   o sea lo que queda de guion y la resta de la clase menos el guion, que responde
   a la única pregunta que importa en mitad de la sesión, si voy tarde o voy
   sobrado. En una fila si la ventana da de sí, tres y tres si no; por debajo de
   800 px los filetes no se dibujan, así que el plegado no parte ningún grupo a la
   vista.

   A su izquierda, centrada a su altura, una marca dice en qué párrafo voy sobre
   el total de la lámina, y ese mismo avance en porciento.

   El párrafo que estoy leyendo va resaltado y el resto atenuado. Se avanza con
   las flechas arriba y abajo, o pinchando cualquier párrafo. Abajo en el último
   pasa a la lámina siguiente; arriba en el primero vuelve a la anterior, a su
   último párrafo.

   Lo que queda de guion se estima como en tools/tiempos.py, pero al párrafo:
   data-min donde está declarado, y palabras del guion hablado entre un ritmo de
   lectura donde no, contando desde el párrafo en curso y no desde el principio
   de la lámina. Ese ritmo no es una constante: se mide durante la propia sesión,
   dividiendo el tiempo real que llevo en los párrafos ya leídos entre lo que se
   tardaría en leerlos de corrido. Así recoge lo que me detengo a explicar de
   más, que es de donde sale el sobrecosto, y midiendo por párrafo converge en
   los primeros minutos. Las acotaciones entre corchetes y los bloques de
   data-min quedan fuera de la medida. El factor se guarda entre sesiones, así
   que la siguiente clase arranca con mi ritmo real.

   Las alarmas avisan a hora de reloj: el receso, los diez minutos finales, lo
   que haga falta. Cada una lleva su hora, el texto que se muestra al dispararse
   y, si se quiere, un sonido. Se editan con A y valen para todas las sesiones,
   como el horario, porque el receso cae a la misma hora cada clase. El pie dice
   cuál es la siguiente y cuánto falta.

   Viven en disco, en admin/alarmas.json, servido por tools/servir.py en GET y
   PUT de /alarmas. localStorage se queda de red de seguridad para cuando no hay
   servidor, igual que con las notas, y entonces el panel lo avisa en ámbar. El
   archivo se relee al abrir el apuntador y al abrir el panel, así que una
   edición a mano se recoge sola.

   El recorte en vivo se enciende con C. El deck marca con data-recorte qué
   láminas se pueden perder, y en cuáles cuesta perderlas: 1 se pierde sin que
   nadie se entere, 2 se pierde pero hay que decírselo al grupo. Con el recorte
   encendido, el apuntador arma solo el plan que cierra el retraso, abreviando lo
   que tiene guion corto escrito y saltando lo que no, y lo rehace en cada tic.
   La holgura y lo que falta de guion ya cuentan el plan puesto, así que los
   relojes dicen cómo va la clase de verdad, no cómo iría sin recortar. Cada
   lámina se puede fijar a mano desde el panel. Ver "Recorte en vivo", más abajo.

   Teclas dentro del apuntador:  V  flotante o emergente
                                 arriba y abajo  párrafo
                                 izquierda y derecha  diapositiva
                                 + y -  tamaño     N  invierte el color
                                 R  reinicia los cronómetros
                                 H  cambia el horario de la clase
                                 A  alarmas       C  recorte en vivo
                                 Esc  cierra aviso o panel */
(function () {
  let win = null;
  let esPip = false;        // la ventana sin barra, si el navegador la da
  let inicio = null;        // arranque de la sesión
  let desdeLamina = null;   // entrada en la diapositiva actual
  let reloj = null;         // intervalo que refresca la cabecera
  let enCurso = null;       // índice de la lámina en curso
  let parr = 0;             // párrafo en curso dentro de esa lámina
  let desdeParrafo = null;  // entrada en ese párrafo
  let pendiente = false;    // hay un párrafo abierto sin contabilizar
  let alUltimo = false;     // al retroceder de lámina, colocarse en su último párrafo
  let consumido = 0;        // tiempo real en los párrafos ya leídos
  let leido = 0;            // lo que costaría leerlos de corrido

  const PPM = 135;          // palabras por minuto de lectura pura
  const RITMO0 = 1.3;       // factor de arranque, hasta tener medida propia
  const HORARIO0 = "08:00-10:00";

  const laminas = () => { try { return Reveal.getSlides(); } catch (e) { return []; } };

  // Estimación de cada lámina, al modo de tools/tiempos.py: duración declarada,
  // o palabras del guion hablado, sin las acotaciones entre corchetes.
  const cache = new Map();
  const cuentaPalabras = (t) => t.replace(/\[[^\]]*\]/g, " ").split(/\s+/).filter(Boolean).length;
  const palabrasPorParrafo = (a) => {
    if (!a) return [];
    const ps = [...a.querySelectorAll("p")];
    return ps.length ? ps.map((y) => cuentaPalabras(y.textContent))
                     : [cuentaPalabras(a.textContent)];
  };
  function estimacion(sec) {
    if (cache.has(sec)) return cache.get(sec);
    const min = parseFloat((sec && sec.dataset.min) || "");
    let x;
    if (min > 0) x = { fijo: min * 60000, palabras: 0, parrafos: [] };
    else {
      const parrafos = palabrasPorParrafo(sec && sec.querySelector("aside.notes"));
      x = { fijo: 0, palabras: parrafos.reduce((b, c) => b + c, 0),
            parrafos: parrafos.length ? parrafos : [0] };
    }
    // La versión corta de la lámina, si la tiene escrita, y su nivel de recorte.
    x.cortos = palabrasPorParrafo(sec && sec.querySelector("aside.corto"));
    x.corto = x.cortos.reduce((b, c) => b + c, 0);
    x.nivel = nivelDe(sec);
    cache.set(sec, x);
    return x;
  }
  const msDe = (palabras) => palabras / PPM * 60000;

  /* Recorte en vivo.

     El nivel de cada lámina lo declara el deck con data-recorte, y dice cuánto
     cuesta perderla: 1 se pierde y nadie se entera, 2 se pierde pero hay que
     decirlo en clase y queda pendiente. Sin marca es núcleo y no se toca nunca.

     Que una lámina se abrevie o se salte no lo decide el nivel, lo decide si
     tiene guion corto escrito, en su <aside class="corto">. Con guion corto se
     puede contar en cuarenta segundos; sin él, la única salida es saltarla.

     El plan se arma solo, en este orden, que es el del coste de perder cada cosa:
     abreviar las de nivel 1, saltar las de nivel 1, abreviar las de nivel 2 y
     saltar las de nivel 2. Dentro de cada grupo entra primero la que más tiempo
     devuelve, para tocar el menor número de láminas. Se recorta solo lo que hace
     falta para cerrar el retraso, y se devuelve lo recortado cuando sobra tiempo,
     con dos minutos de margen para que el plan no baile de un segundo a otro.

     El modo lo enciende Alberto con la tecla C: apagado, solo nivel 1, o niveles
     1 y 2. Lo de nivel 2 no entra solo aunque haga falta: hay que decírselo al
     grupo, y esa es su decisión, no la del programa. */
  const nivelDe = (sec) => {
    const n = sec ? parseInt(sec.dataset.recorte || "", 10) : 0;
    return n === 1 || n === 2 ? n : 0;
  };
  const DECK = location.pathname.split("/").filter(Boolean).slice(-2)[0] || "deck";
  const LLAVE_REC = "apuntador:recorte:" + DECK;

  let modo = 0;                 // 0 apagado, 1 solo nivel 1, 2 niveles 1 y 2
  const forzado = new Map();    // sid -> "completa" | "corta" | "fuera", a mano
  const plan = new Map();       // índice de lámina -> "corta" | "fuera", automático
  let pasos = [];               // el orden en que se recortó, para deshacerlo igual

  const sidDe = (i) => {
    const sec = laminas()[i];
    return (sec && (sec.dataset.sid || sec.id)) || "lamina-" + i;
  };
  let sinPlan = false;          // para medir cuánto duraría sin recortar nada
  const estado = (i) => {
    if (sinPlan) return "completa";
    const f = forzado.get(sidDe(i));
    if (f) return f;
    return plan.get(i) || "completa";
  };
  const medirSinPlan = (fn) => {
    sinPlan = true;
    try { return fn(); } finally { sinPlan = false; }
  };
  const puedeAbreviar = (i) => estimacion(laminas()[i]).corto > 0;

  // Lo que dura una lámina según lo que se haya decidido para ella. Abreviada
  // dura lo que su guion corto, aunque declare duración fija: un bloque de
  // discusión abreviado es contarlo, no tenerlo.
  const duracion = (x, est, f) =>
    est === "fuera" ? 0
    : est === "corta" ? msDe(x.corto) * f
    : (x.fijo || msDe(x.palabras) * f);

  // Los párrafos que de verdad se van a leer, que son los que se ven y los que
  // cuentan para medir el ritmo.
  const parrafosDe = (x, est) => (est !== "completa" && x.corto > 0 ? x.cortos : x.parrafos);

  function guardarModo() {
    try {
      localStorage.setItem(LLAVE_REC, JSON.stringify(
        { modo, forzado: Object.fromEntries(forzado) }));
    } catch (e) {}
  }
  function cargarModo() {
    try {
      const d = JSON.parse(localStorage.getItem(LLAVE_REC) || "null");
      if (!d) return;
      modo = d.modo === 1 || d.modo === 2 ? d.modo : 0;
      Object.keys(d.forzado || {}).forEach((k) => forzado.set(k, d.forzado[k]));
    } catch (e) {}
  }

  const ritmoGuardado = () => parseFloat(localStorage.getItem("apuntador:ritmo") || "") || RITMO0;

  // Mi ritmo real: tiempo consumido entre tiempo de lectura de los párrafos ya
  // leídos. Las acotaciones y los bloques de duración fija no cuentan, que no
  // dependen de cómo hable.
  function ritmo() {
    if (leido < 60000) return ritmoGuardado();           // todavía no hay con qué medir
    return Math.min(3, Math.max(0.5, consumido / leido));
  }

  function recordarRitmo() {
    if (leido < 180000) return;                          // tres minutos de guion, mínimo
    const suave = ritmoGuardado() * 0.5 + ritmo() * 0.5;
    try { localStorage.setItem("apuntador:ritmo", suave.toFixed(2)); } catch (e) {}
  }

  // Cierra la cuenta del párrafo en curso. Solo suma una vez, y solo si el
  // párrafo tiene palabras que leer.
  function cerrarParrafo() {
    if (pendiente && desdeParrafo !== null && enCurso !== null) {
      const x = estimacion(laminas()[enCurso]);
      const est = estado(enCurso);
      // Los bloques de duración fija no miden el ritmo, salvo que se estén
      // contando abreviados, que entonces sí es guion hablado.
      const ps = x ? parrafosDe(x, est) : [];
      const pal = x && (!x.fijo || est !== "completa") ? (ps[parr] || 0) : 0;
      if (pal > 0) { consumido += Date.now() - desdeParrafo; leido += msDe(pal); }
      recordarRitmo();
    }
    pendiente = false;
    desdeParrafo = Date.now();
  }

  function abrirParrafo(i) {
    parr = i;
    desdeParrafo = Date.now();
    pendiente = true;
  }

  // Lo que queda de la lámina en curso, desde el párrafo en curso y según lo
  // que el plan haya decidido para ella.
  function faltaLamina(i, p, enParrafo, enLamina, f) {
    const sec = laminas()[i];
    const x = sec && estimacion(sec);
    if (!x) return 0;
    const est = estado(i);
    if (est === "fuera") return 0;                 // no se va a contar
    if (est === "completa" && x.fijo) return Math.max(0, x.fijo - enLamina);
    const ps = parrafosDe(x, est);
    let ms = 0;
    for (let j = p; j < ps.length; j++) {
      const t = msDe(ps[j]) * f;
      ms += j === p ? Math.max(0, t - enParrafo) : t;
    }
    return ms;
  }

  // Lo que queda de guion desde el párrafo en curso, con el ritmo aplicado solo
  // a lo que se habla. Con f = 1 sale el material sin corregir, que es lo que
  // miden las barras de avance: material recorrido, no tiempo.
  function faltaGuion(k, p, enParrafo, enLamina, f) {
    const ls = laminas();
    if (f === undefined) f = ritmo();
    let ms = faltaLamina(k, p, enParrafo, enLamina, f);
    for (let i = k + 1; i < ls.length; i++) ms += duracion(estimacion(ls[i]), estado(i), f);
    return ms;
  }

  /* El plan, rehecho en cada tic: el ritmo y la hora cambian, así que lo que
     hace falta recortar cambia con ellos. Recorta mientras vaya tarde y devuelve
     lo último recortado en cuanto sobre tiempo con margen. */
  function mejorCandidato(desde, f) {
    const ls = laminas();
    let mejor = null;
    for (let i = desde; i < ls.length; i++) {
      const x = estimacion(ls[i]);
      if (!x.nivel || x.nivel > modo) continue;
      if (forzado.has(sidDe(i))) continue;         // decidido a mano, no se toca
      const est = plan.get(i) || "completa";
      if (est === "fuera") continue;               // ya no queda nada que quitarle
      const opciones = [];
      if (est === "completa" && x.corto > 0) opciones.push({ a: "corta", grado: (x.nivel - 1) * 2 });
      opciones.push({ a: "fuera", grado: (x.nivel - 1) * 2 + 1 });
      opciones.forEach((o) => {
        const ahorro = duracion(x, est, f) - duracion(x, o.a, f);
        if (ahorro <= 0) return;
        const c = { i, a: o.a, antes: est, grado: o.grado, ahorro };
        if (!mejor || c.grado < mejor.grado ||
            (c.grado === mejor.grado && c.ahorro > mejor.ahorro)) mejor = c;
      });
    }
    return mejor;
  }

  function ajustarPlan(k, p, enParrafo, enLamina) {
    // lo ya recorrido sale del plan: recortar hacia atrás no devuelve tiempo
    // La lámina en curso conserva lo suyo: si el plan dijo que se salta, hay que
    // verlo al llegar a ella. Solo sale del plan cuando ya quedó atrás.
    [...plan.keys()].forEach((i) => { if (i < k) plan.delete(i); });
    pasos = pasos.filter((x) => plan.has(x.i));
    if (!modo) { plan.clear(); pasos = []; return; }
    const fin = finDeClase();
    if (fin === null) return;
    const f = ritmo();
    const holgura = () => fin - Date.now() - faltaGuion(k, p, enParrafo, enLamina, f);
    let guardia = 0;
    while (holgura() < -20000 && guardia++ < 300) {
      const c = mejorCandidato(k + 1, f);
      if (!c) break;
      pasos.push({ i: c.i, a: c.a, antes: c.antes });
      plan.set(c.i, c.a);
    }
    // Se devuelve de uno en uno, y solo si después de devolverlo todavía sobran
    // dos minutos: si no, el plan bailaría de un segundo a otro.
    while (pasos.length) {
      const u = pasos[pasos.length - 1];
      if (u.i === k) break;              // no cambiar la lámina que se está dando
      const x = estimacion(laminas()[u.i]);
      const cuesta = duracion(x, u.antes, f) - duracion(x, u.a, f);
      if (holgura() < cuesta + 120000) break;
      pasos.pop();
      if (u.antes === "completa") plan.delete(u.i); else plan.set(u.i, u.antes);
    }
  }

  // Lo que todavía se podría recuperar recortando de aquí al final todo lo que
  // el modo permite. Sirve para decir qué compraría encender cada nivel, y para
  // saber cuándo el plan ya se quedó sin nada que quitar.
  function potencialPlan(k, f, hasta) {
    const ls = laminas();
    let ms = 0, n = 0;
    for (let i = k + 1; i < ls.length; i++) {
      const x = estimacion(ls[i]);
      if (!x.nivel || x.nivel > hasta || forzado.has(sidDe(i))) continue;
      n++;
      ms += duracion(x, estado(i), f);      // lo que aún ocupa, o sea lo recuperable
    }
    return { n, ms };
  }

  // Lo que el plan recorta de aquí al final, en láminas y en tiempo.
  function resumenPlan(k, f) {
    const ls = laminas();
    let cortas = 0, fueras = 0, ahorro = 0;
    for (let i = k + 1; i < ls.length; i++) {
      const est = estado(i);
      if (est === "completa") continue;
      const x = estimacion(ls[i]);
      ahorro += duracion(x, "completa", f) - duracion(x, est, f);
      if (est === "corta") cortas++; else fueras++;
    }
    return { cortas, fueras, ahorro };
  }

  let totalDeck = null;
  function baseDeck() {
    if (totalDeck === null) {
      totalDeck = laminas().reduce((a, sec) => {
        const x = estimacion(sec);
        return a + (x.fijo || msDe(x.palabras));
      }, 0);
    }
    return totalDeck;
  }
  const porciento = (parte, todo) =>
    (todo > 0 ? Math.max(0, Math.min(100, (parte / todo) * 100)) : 100).toFixed(1) + "%";

  const horario = () => localStorage.getItem("apuntador:horario") || HORARIO0;
  function finDeClase() {
    const m = /(\d{1,2}):(\d{2})\s*[-a]+\s*(\d{1,2}):(\d{2})/.exec(horario());
    const f = new Date();
    if (!m) return null;
    f.setHours(+m[3], +m[4], 0, 0);
    return f.getTime();
  }

  const dos = (n) => (n < 10 ? "0" : "") + n;
  // m:ss mientras dure menos de una hora, h:mm:ss a partir de ahí
  const cuenta = (ms) => {
    const s = Math.max(0, Math.floor(ms / 1000));
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
    return (h ? h + ":" + dos(m) : String(m)) + ":" + dos(s % 60);
  };

  /* Alarmas. El aviso aparece dentro del pie, que crece hacia arriba, y no
     encima del texto: interrumpe sin tapar el renglón que se está leyendo en voz
     alta. El destello del borde es lo que se ve por el rabillo del ojo sin
     apartar la mirada del lente.

     El sonido lo sintetiza el navegador con osciladores, así que no hay archivo
     que vendorizar y suena igual sin conexión. Sale por las bocinas del equipo:
     si se comparte pantalla con audio, el grupo lo oye. */
  const SONIDOS = {
    ninguno: { etiqueta: "Sin sonido", notas: [] },
    // [frecuencia, arranque en segundos, duración, forma, ganancia]
    campana: { etiqueta: "Campana", notas: [
      [880, 0, 1.7, "sine", .28], [1760, 0, 1.1, "sine", .10],
      [880, .6, 1.6, "sine", .20], [1760, .6, 1.0, "sine", .07]] },
    timbre: { etiqueta: "Timbre", notas: [
      [659, 0, .7, "sine", .3], [523, .38, 1.1, "sine", .3]] },
    doble: { etiqueta: "Doble pitido", notas: [
      [700, 0, .16, "triangle", .28], [700, .28, .16, "triangle", .28]] },
    suave: { etiqueta: "Suave", notas: [
      [392, 0, 1.2, "sine", .22], [523, .22, 1.4, "sine", .18]] },
  };

  let ctx = null;
  // El contexto se crea en la ventana del deck, que es donde hay gestos del
  // usuario: sin uno de por medio el navegador lo deja suspendido y no suena.
  function audio() {
    try {
      const A = window.AudioContext || window.webkitAudioContext;
      if (!A) return null;
      if (!ctx) ctx = new A();
      if (ctx.state === "suspended") ctx.resume();
      return ctx;
    } catch (e) { return null; }
  }
  function sonar(nombre) {
    const s = SONIDOS[nombre];
    if (!s || !s.notas.length) return;
    const a = audio();
    if (!a) return;
    const t0 = a.currentTime + .03;
    try {
      s.notas.forEach((n) => {
        const o = a.createOscillator(), g = a.createGain();
        o.type = n[3] || "sine";
        o.frequency.value = n[0];
        g.gain.setValueAtTime(.0001, t0 + n[1]);
        g.gain.exponentialRampToValueAtTime(n[4] || .25, t0 + n[1] + .012);
        g.gain.exponentialRampToValueAtTime(.0001, t0 + n[1] + n[2]);
        o.connect(g); g.connect(a.destination);
        o.start(t0 + n[1]); o.stop(t0 + n[1] + n[2] + .05);
      });
    } catch (e) {}
  }

  function alarmas() {
    try {
      const a = JSON.parse(localStorage.getItem("apuntador:alarmas") || "[]");
      if (!Array.isArray(a)) return [];
      return a.filter((x) => x && normalizaHora(x.h))
              .sort((p, q) => (normalizaHora(p.h) < normalizaHora(q.h) ? -1 : 1));
    } catch (e) { return []; }
  }
  /* Dónde viven las alarmas.

     En disco, en admin/alarmas.json, contra GET y PUT de /alarmas. Así
     sobreviven a un borrado de datos de Chrome y viajan con el proyecto, y se
     pueden leer y editar con cualquier editor. Son globales, no de una sesión.

     localStorage se queda de espejo. Sin servidor, que es el deck abierto con
     doble clic, las alarmas siguen funcionando pero solo en ese navegador, y el
     panel lo dice en ámbar. Si el disco no tiene ninguna y el navegador sí, las
     que había se suben en vez de perderse. */
  const RUTA_ALARMAS = "/alarmas";
  let srvAlarmas = false;          // ¿hay servidor detrás?

  function espejoAlarmas(a) {
    try { localStorage.setItem("apuntador:alarmas", JSON.stringify(a)); } catch (e) {}
  }
  function guardarAlarmas(a) { espejoAlarmas(a); subirAlarmas(a); }

  function subirAlarmas(a) {
    if (!srvAlarmas) return;
    fetch(RUTA_ALARMAS, {
      method: "PUT", cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alarmas: a }),
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      // el servidor devuelve lo que quedó en disco, ya filtrado y ordenado
      .then((d) => { if (Array.isArray(d.alarmas)) espejoAlarmas(d.alarmas); })
      .catch(() => { srvAlarmas = false; pintarFuente(); });
  }

  function cargarAlarmas() {
    return fetch(RUTA_ALARMAS, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        srvAlarmas = true;
        const suyas = Array.isArray(d.alarmas) ? d.alarmas : [];
        // capturadas sin servidor: se suben en vez de perderse
        if (!suyas.length && alarmas().length) subirAlarmas(alarmas());
        else espejoAlarmas(suyas);
      })
      .catch(() => { srvAlarmas = false; })
      .then(() => { pintarFuente(); pintarProxima(); });
  }

  // El panel dice siempre dónde acaban las alarmas, que es lo que distingue
  // tenerlas guardadas en el proyecto de tenerlas solo en este navegador.
  function pintarFuente() {
    if (!win || win.closed) return;
    const x = win.document.getElementById("alFuente");
    if (!x) return;
    x.className = srvAlarmas ? "" : "off";
    x.textContent = srvAlarmas
      ? "Se guardan en admin/alarmas.json, con el resto del proyecto."
      : "Sin servidor: se guardan solo en este navegador. Abre el deck por la liga de servir.py para que queden en el proyecto.";
  }
  function normalizaHora(h) {
    const m = /^\s*(\d{1,2}):(\d{2})/.exec(h || "");
    if (!m || +m[1] > 23 || +m[2] > 59) return "";
    return dos(+m[1]) + ":" + dos(+m[2]);
  }
  const hhmm = (ms) => { const f = new Date(ms); return dos(f.getHours()) + ":" + dos(f.getMinutes()); };
  // La hora de hoy, en milisegundos. Null si no es una hora.
  function hoyALas(h) {
    const n = normalizaHora(h);
    if (!n) return null;
    const f = new Date();
    f.setHours(+n.slice(0, 2), +n.slice(3), 0, 0);
    return f.getTime();
  }

  // Los tres instantes en que esa hora de reloj cae cerca de ahora: ayer, hoy y
  // mañana. Una hora suelta no dice de qué día es, y a las 23:39 la alarma de
  // las 00:03 es la de mañana, no una de hoy que ya pasó. Se cuenta por
  // calendario y no sumando 24 h: el día en que cambia el horario de verano
  // dura 23 o 25 horas, y sumando se desplazaría una hora la ocurrencia, que
  // acabaría cayendo en la misma fecha que la de hoy y compartiendo su llave.
  function cercaDeHoy(h) {
    const n = normalizaHora(h);
    if (!n) return [];
    return [-1, 0, 1].map((d) => {
      const f = new Date();
      f.setDate(f.getDate() + d);
      f.setHours(+n.slice(0, 2), +n.slice(3), 0, 0);
      return f.getTime();
    });
  }

  const GRACIA = 90000;     // margen para no resucitar alarmas viejas al reabrir
  const sonadas = new Set();
  function revisarAlarmas() {
    const ahora = Date.now();
    alarmas().forEach((a) => {
      // Las tres ocurrencias distan 24 h y la gracia es de minuto y medio, así
      // que a lo sumo una cae dentro: la de ayer sirve para el minuto después
      // de medianoche, cuando la de hoy todavía está por delante.
      const t = cercaDeHoy(a.h).find((x) => ahora >= x && ahora - x <= GRACIA);
      if (t === undefined) return;
      // El día sale de la ocurrencia y no del reloj: si no, la alarma de las
      // 23:59:30 sonaría otra vez a las 00:00:05 con la llave del día nuevo.
      const llave = new Date(t).toDateString() + "@" + normalizaHora(a.h) + "@" + (a.t || "");
      if (sonadas.has(llave)) return;
      sonadas.add(llave);
      disparar(a);
    });
  }

  function disparar(a) {
    sonar(a.s);
    if (!win || win.closed) return;
    const d = win.document, caja = d.getElementById("aviso");
    if (!caja) return;
    const x = d.createElement("div");
    const b = d.createElement("b"), i = d.createElement("i");
    b.textContent = a.t || "Alarma";
    i.textContent = normalizaHora(a.h) + ", clic para cerrar";
    x.appendChild(b); x.appendChild(i);
    caja.appendChild(x);
    destellar();
    setTimeout(() => { if (x.parentNode) x.remove(); }, 45000);
  }

  function destellar() {
    if (!win || win.closed) return;
    const x = win.document.getElementById("destello");
    if (!x) return;
    x.classList.remove("destella");
    void x.offsetWidth;                 // reinicia la animación si ya corría
    x.classList.add("destella");
    setTimeout(() => x.classList.remove("destella"), 3600);
  }

  // Cuánto se asoma el pie al día siguiente. La alarma de madrugada tiene que
  // anunciarse desde la noche anterior, pero sin este techo el pie se pasaría
  // la tarde entera anunciando la primera alarma de mañana, a veintitrés horas
  // vista y con la cuenta en cuatro cifras de minutos.
  const ASOMO = 7200000;

  // La siguiente alarma que queda por delante, para el pie. Si la de hoy a esa
  // hora ya pasó, vale la de mañana mientras esté dentro del asomo: así una
  // alarma a las 00:03 se anuncia a las 23:39, y a las 15:00 el pie calla.
  function proxima() {
    const ahora = Date.now();
    let mejor = null;
    alarmas().forEach((a) => {
      const [, hoy, manana] = cercaDeHoy(a.h);
      if (hoy === undefined) return;
      const t = hoy > ahora ? hoy : manana - ahora <= ASOMO ? manana : null;
      if (t === null) return;
      if (!mejor || t < mejor.t) mejor = { t: t, a: a };
    });
    return mejor;
  }
  function pintarProxima() {
    if (!win || win.closed) return;
    const x = win.document.getElementById("prox");
    if (!x) return;
    const p = proxima();
    if (!p) { x.textContent = ""; x.className = ""; return; }
    const falta = p.t - Date.now();
    x.textContent = "próxima " + (p.a.t || "alarma") + " en " +
      (falta >= 600000 ? Math.round(falta / 60000) + " min" : cuenta(falta));
    x.className = falta < 120000 ? "cerca" : "";
  }

  // El panel de edición. Vive dentro de la ventana del apuntador y no en un
  // diálogo, porque las ventanas flotantes no abren diálogos.
  function filaAlarma(d, x) {
    const f = d.createElement("div");
    f.className = "al";
    const hora = d.createElement("input");
    hora.type = "time"; hora.className = "alH"; hora.value = normalizaHora(x.h);
    const tit = d.createElement("input");
    tit.type = "text"; tit.className = "alT"; tit.value = x.t || "";
    tit.placeholder = "Qué avisa";
    const sel = d.createElement("select");
    sel.className = "alS";
    Object.keys(SONIDOS).forEach((k) => {
      const o = d.createElement("option");
      o.value = k; o.textContent = SONIDOS[k].etiqueta;
      if ((x.s || "ninguno") === k) o.selected = true;
      sel.appendChild(o);
    });
    const oir = d.createElement("button");
    oir.className = "alP"; oir.textContent = "oír"; oir.type = "button";
    const quita = d.createElement("button");
    quita.className = "alX"; quita.textContent = "quitar"; quita.type = "button";
    const pie = d.createElement("div");
    pie.className = "alPie";
    [sel, oir, quita].forEach((e) => pie.appendChild(e));
    [hora, tit, pie].forEach((e) => f.appendChild(e));
    return f;
  }

  function pintarAlarmas() {
    if (!win || win.closed) return;
    const d = win.document, lista = d.getElementById("alLista");
    if (!lista) return;
    lista.innerHTML = "";
    const a = alarmas();
    if (!a.length) {
      const p = d.createElement("p");
      p.className = "alVacio";
      p.textContent = "Todavía no hay alarmas.";
      lista.appendChild(p);
    }
    a.forEach((x) => lista.appendChild(filaAlarma(d, x)));
    const h = d.getElementById("alHorario");
    if (h) h.textContent = "clase " + horario().replace("-", " a ");
    pintarFuente();
  }

  // Lo que dice el panel manda: se lee entero y se guarda ordenado por hora.
  function leerAlarmas() {
    if (!win || win.closed) return;
    const d = win.document;
    if (!d.getElementById("alLista")) return;
    const a = [...d.querySelectorAll("#alLista .al")].map((f) => ({
      h: normalizaHora(f.querySelector(".alH").value),
      t: f.querySelector(".alT").value.trim(),
      s: f.querySelector(".alS").value,
    })).filter((x) => x.h);
    a.sort((p, q) => (p.h < q.h ? -1 : p.h > q.h ? 1 : 0));
    guardarAlarmas(a);
    pintarProxima();
  }

  function nuevaAlarma() {
    leerAlarmas();                       // no perder lo que se venía escribiendo
    const a = alarmas();
    const ultima = a.length ? hoyALas(a[a.length - 1].h) : null;
    const fin = finDeClase();
    const base = ultima !== null ? ultima + 600000
               : fin !== null ? fin - 600000 : Date.now() + 600000;
    a.push({ h: hhmm(base), t: "", s: "campana" });
    a.sort((p, q) => (p.h < q.h ? -1 : p.h > q.h ? 1 : 0));
    guardarAlarmas(a);
    pintarAlarmas();
    const campos = win.document.querySelectorAll("#alLista .al");
    const nueva = [...campos].find((f) => f.querySelector(".alH").value === hhmm(base));
    if (nueva) nueva.querySelector(".alT").focus();
  }

  const panelAbierto = () =>
    !!(win && !win.closed && win.document.body.classList.contains("editando"));
  function abrirPanel() {
    if (!win || win.closed) return;
    pintarAlarmas();
    win.document.body.classList.add("editando");
    huecoDelPie(win.document.getElementById("alarmas"));
    // por si el archivo cambió por fuera; solo se repinta si de verdad cambió,
    // no vaya a ser que borre lo que se está escribiendo
    const antes = JSON.stringify(alarmas());
    cargarAlarmas().then(() => {
      if (panelAbierto() && JSON.stringify(alarmas()) !== antes) pintarAlarmas();
    });
  }
  function cerrarPanel() {
    if (!win || win.closed) return;
    leerAlarmas();
    win.document.body.classList.remove("editando");
  }

  /* ---------- panel de recorte ---------- */

  const panelRecAbierto = () =>
    !!(win && !win.closed && win.document.body.classList.contains("recortando"));
  const algunPanel = () => panelAbierto() || panelRecAbierto();

  function abrirRec() {
    if (!win || win.closed) return;
    firmaRec = null;                       // que se pinte entero al abrir
    win.document.body.classList.add("recortando");
    tictac();
  }
  function cerrarRec() {
    if (!win || win.closed) return;
    win.document.body.classList.remove("recortando");
  }

  function ponerModo(n) {
    modo = n === 1 || n === 2 ? n : 0;
    if (!modo) { plan.clear(); pasos = []; }
    guardarModo();
    firmaRec = null;
    tictac();
  }

  // Fijar una lámina a mano: el plan la respeta y no vuelve a tocarla. "auto" la
  // devuelve al plan. Si es la que se está dando, hay que repintar el guion,
  // porque el texto que se lee cambia.
  function forzar(sid, que) {
    const i = laminas().findIndex((sec, j) => sidDe(j) === sid);
    if (i < 0) return;
    if (que === "auto") forzado.delete(sid); else forzado.set(sid, que);
    plan.delete(i);
    pasos = pasos.filter((x) => x.i !== i);
    guardarModo();
    firmaRec = null;
    if (i === enCurso) pintar(); else tictac();
  }

  const tituloDe = (sec) => {
    const h = sec.querySelector("h1,h2") || sec.querySelector(".titulo,.gracias");
    return h ? h.textContent.trim() : (sec.dataset.sid || sec.id || "");
  };

  const ESTADO = { completa: "entera", corta: "abreviada", fuera: "se salta" };

  let firmaRec = null;

  // El pie se queda encima del panel, así que hay que dejarle su hueco al final
  // o el último renglón del panel se lee a medias. La altura del pie cambia con
  // el ancho de la ventana y con los avisos, así que se mide cada vez.
  function huecoDelPie(panel) {
    if (!win || win.closed || !panel) return;
    const pie = win.document.getElementById("pie");
    const px = ((pie ? pie.offsetHeight : 0) + 14) + "px";
    if (panel.style.paddingBottom !== px) panel.style.paddingBottom = px;
  }

  function pintarRecorte(k) {
    if (!win || win.closed) return;
    const d = win.document, ls = laminas(), f = ritmo();

    // El banderín sobre el guion, que se ve siempre, con el panel cerrado.
    const banda = d.getElementById("rec");
    if (banda && ls[k]) {
      const est = estado(k), x = estimacion(ls[k]);
      if (est === "completa") { banda.textContent = ""; banda.className = ""; }
      else {
        banda.className = est === "fuera" ? "fuera" : "";
        banda.innerHTML = "<b>" + (est === "fuera" ? "Saltar esta lámina" : "Guion corto") + "</b><i>" +
          (x.nivel ? "Recorte " + x.nivel + ". " : "") +
          (est === "fuera"
            ? (x.nivel === 2 ? "Decir al grupo que se retoma más adelante. " : "") +
              "La flecha abajo pasa ya a la siguiente."
            : "Se cuenta abreviada.") +
          (forzado.has(sidDe(k)) ? " Fijada a mano." : "") + "</i>";
      }
    }
    if (!panelRecAbierto()) return;
    huecoDelPie(d.getElementById("recorte"));

    const enParrafo = desdeParrafo === null ? 0 : Date.now() - desdeParrafo;
    const enLamina = desdeLamina === null ? 0 : Date.now() - desdeLamina;
    const fin = finDeClase();
    const conPlan = faltaGuion(k, parr, enParrafo, enLamina, f);
    const crudo = medirSinPlan(() => faltaGuion(k, parr, enParrafo, enLamina, f));
    const resta = fin === null ? null : fin - Date.now();
    const hol = resta === null ? null : resta - conPlan;
    const holCrudo = resta === null ? null : resta - crudo;
    const r = resumenPlan(k, f);
    const pot = potencialPlan(k, f, modo || 2);
    const potTodo = potencialPlan(k, f, 2);
    const dura = (ms) => ms >= 60000 ? Math.round(ms / 60000) + " min"
                                     : Math.round(ms / 1000) + " s";
    const cuantas = (n) => "<b>" + n + "</b> lámina" + (n === 1 ? "" : "s");

    // Fuera del horario de la clase la holgura no significa nada: si la clase
    // terminó hace horas, el retraso son esas horas. Conviene decirlo, o el
    // número parece congelado cuando en realidad no viene al caso.
    const ensayo = resta !== null && resta < -30 * 60000;
    d.getElementById("recEstado").textContent =
      resta === null ? "sin horario de clase"
      : ensayo ? "la clase terminó hace " + cuenta(-resta) + ", así que esto es un ensayo"
      : resta >= 0 ? "la clase termina en " + cuenta(resta)
      : "la clase terminó hace " + cuenta(-resta);

    /* La primera frase lleva el modo que está puesto y lo que se iría con él, no
       una cifra fija: al pulsar otro botón cambia el nombre y cambia el número,
       que es lo que deja ver de un vistazo qué compra cada nivel. */
    const NOMBRE_MODO = ["Sin recortar nada", "Recortando solo el nivel 1",
                         "Recortando los niveles 1 y 2"];
    const comoVas = (ms) => (ms < 0 ? "irías tarde <b>" : "te sobrarían <b>") +
                            cuenta(Math.abs(ms)) + "</b>";

    let resumen;
    if (r.cortas || r.fueras) {
      resumen = "El plan " +
        [r.cortas ? "abrevia <b>" + r.cortas + "</b>" : "",
         r.fueras ? "salta <b>" + r.fueras + "</b>" : ""].filter(Boolean).join(" y ") +
        " de aquí al final, y devuelve <b>" + dura(r.ahorro) + "</b>.";
      if (hol !== null && hol < 0) {
        // Con solo el nivel 1 encendido, lo que queda de nivel 2 sigue ahí: no es
        // que no haya más que recortar, es que hace falta encenderlo.
        resumen += pot.ms > 30000
          ? " Sigues tarde, y quedan <b>" + dura(pot.ms) + "</b> por recortar."
          : modo === 1 && potTodo.ms > 30000
            ? " Sigues tarde, y del nivel 1 ya no queda nada. El nivel 2 devolvería <b>" +
              dura(potTodo.ms) + "</b> más."
            : " Sigues tarde, y ya no queda nada más marcado que recortar.";
      }
    } else if (!modo) {
      resumen = "El recorte está apagado: nada se abrevia ni se salta." +
        (pot.n ? " De aquí al final hay " + cuantas(pot.n) + " marcada" +
                 (pot.n === 1 ? "" : "s") + ", que devuelven hasta <b>" + dura(pot.ms) + "</b>."
               : " De aquí al final no hay ninguna lámina marcada, así que encenderlo no " +
                 "cambiaría nada. Se marcan al revisar el deck, con la tecla C.");
    } else if (!pot.n) {
      resumen = "De aquí al final no queda ninguna lámina marcada de los niveles encendidos, " +
                "así que no hay nada que recortar.";
    } else {
      resumen = "No hace falta recortar todavía: lo que queda cabe en la clase. Hay " +
                cuantas(pot.n) + " marcada" + (pot.n === 1 ? "" : "s") + " esperando, por si " +
                "el ritmo cambia.";
    }
    const cabeza = hol === null
      ? "Pon el horario de la clase con H para calcular la holgura. "
      : NOMBRE_MODO[modo] + " " + comoVas(hol) +
        (modo ? ", y sin recortar nada <b>" + cuenta(Math.abs(holCrudo)) + "</b>" : "") + ". ";
    d.getElementById("recResumen").innerHTML = cabeza + resumen;

    [...d.querySelectorAll("#recModo button")].forEach((b) =>
      b.classList.toggle("on", parseInt(b.dataset.modo, 10) === modo));

    // La lista solo se repinta cuando cambia de verdad: si no, un clic caería
    // sobre un botón que el tic acaba de sustituir.
    // La lámina en curso va siempre, tenga nivel o no: es la única manera de
    // abreviar a mano una de núcleo el día que la clase se tuerza de verdad. El
    // núcleo no se pierde, pero contarlo corto no es perderlo. Las demás solo
    // aparecen si están marcadas, que son las que el plan puede tocar.
    const filas = [];
    for (let i = k; i < ls.length; i++) {
      const x = estimacion(ls[i]);
      if (!x.nivel && i !== k) continue;
      filas.push({ i, x, est: estado(i), forz: forzado.get(sidDe(i)) || "auto",
                   aqui: i === k });
    }
    const firma = modo + "|" + k + "|" +
      filas.map((y) => y.i + y.est + y.forz).join(",");
    if (firma === firmaRec) return;
    firmaRec = firma;
    const lista = d.getElementById("recLista");
    if (!filas.length) {
      lista.innerHTML = '<p class="recVacio">De aquí al final no queda ninguna lámina ' +
        "marcada para recortar. Se marcan al revisar el deck, con la tecla C.</p>";
      return;
    }
    const soloAqui = filas.length === 1 && filas[0].aqui && !filas[0].x.nivel;
    const bot = (sid, que, texto, on, off) =>
      '<button type="button" data-rec="' + que + '" data-sid="' + sid + '"' +
      (on ? ' class="on"' : "") + (off ? " disabled" : "") + ">" + texto + "</button>";
    lista.innerHTML = filas.map((y) => {
      const sid = sidDe(y.i);
      return '<div class="recF' + (y.est === "completa" ? "" : " plan") +
        (y.aqui ? " aqui" : "") + '">' +
        '<span class="recN">' + (y.aqui ? "aquí" : y.i + 1) + "</span>" +
        '<span class="recT">' + tituloDe(ls[y.i]) + "</span>" +
        '<span class="recE' + (y.x.nivel === 2 ? " n2" : y.x.nivel ? "" : " sc") + '">' +
        (y.x.nivel ? "recorte " + y.x.nivel : "núcleo") + "</span>" +
        (y.x.corto > 0 ? '<span class="recE sc">' + Math.round(msDe(y.x.corto) * f / 1000) + " s</span>"
                       : '<span class="recE sc">sin corto</span>') +
        '<span class="recE es">' + ESTADO[y.est] + "</span>" +
        '<span class="recA">' +
        bot(sid, "auto", "auto", y.forz === "auto", false) +
        bot(sid, "completa", "entera", y.forz === "completa", false) +
        bot(sid, "corta", "corta", y.forz === "corta", y.x.corto === 0) +
        bot(sid, "fuera", "fuera", y.forz === "fuera", false) +
        "</span></div>";
    }).join("") +
      (soloAqui ? '<p class="recVacio">De aquí al final no queda ninguna lámina marcada. ' +
        "Arriba está la que se está dando, que se puede abreviar a mano si tiene guion " +
        "corto escrito.</p>" : "");
  }

  /* El CSS va partido en dos, y la primera mitad la comparte el anotador.

     La vista de guion de la revisión, la de la tecla G con ?revisar, es esta
     misma columna de lectura: Alberto la pidió así el 8 de octubre de 2026,
     para revisar el guion tal como lo va a leer en clase. Para que las dos no
     se separen con el tiempo, el CSS de la columna es EL MISMO y no una copia:
     se publica en window.ApuntadorTema y revisar.js lo lee de ahí.

     Lo que queda en CSS_CLASE es lo que solo hace falta dando la clase: el pie
     con los relojes, las barras de avance, los avisos, el destello, el panel de
     recorte en vivo y el de alarmas. Revisando no hay clase que cronometrar. */
  const CSS_LECTURA = `
    /* El guion llega ya compuesto: si el deck no excluye las notas, MathJax deja
       en su innerHTML el SVG de cada fórmula, y esa ventana lo pinta sin tener
       que cargar MathJax. Lo único que falta aquí es esta regla, que en el deck
       la pone el propio MathJax: sin ella, la copia para lectores de pantalla se
       vería al lado de la fórmula y cada expresión saldría dos veces. */
    mjx-assistive-mml{position:absolute!important;top:0;left:0;clip:rect(1px,1px,1px,1px);
      padding:1px 0 0 0!important;border:0!important;height:1px!important;
      width:1px!important;overflow:hidden!important;display:block!important}
    mjx-container{display:inline-block;line-height:0}
    mjx-container svg{vertical-align:middle}
    :root{--bg:#FFFFFF;--fg:#111111;--tenue:#8A8A8A;--acento:#A42145;
      --ambar:#B4690E;--rojo:#A42145;--riel:#E4E0D8}
    body.oscuro{--bg:#111111;--fg:#F2F2F2;--tenue:#7A7A7A;--acento:#E7D395;
      --ambar:#E7A33C;--rojo:#FF8095;--riel:#2E2E2E}
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--fg);
      font-family:'Noto Sans',system-ui,sans-serif;overflow-x:hidden}
    :root{--franja:124px}
    #col{max-width:calc(22em + 54px + 138px);margin:0 auto;padding:12px 16px 92vh;
      position:relative}
    /* Si la ventana es estrecha no hay sitio para la franja: la acotación pasa
       a verse debajo de su párrafo, en pequeño, que es peor pero cabe. */
    @media (max-width:640px){
      :root{--franja:auto}
      #col{max-width:calc(22em + 54px)}
      #texto{padding-right:0 !important}
      .acot-marg{position:static;width:auto;margin:.2em 0 .6em;display:block}
    }
    /* Marca al costado del párrafo en curso: en qué diapositiva voy y cuánto
       llevo de ella. Vive en el margen que le abre #texto, no empuja el texto. */
    #texto{padding-left:54px;padding-right:138px}
    #marca{position:absolute;left:0;width:44px;text-align:right;color:var(--tenue);
      font:600 13px/1.3 ui-monospace,'SF Mono',Menlo,monospace;font-variant-numeric:tabular-nums;
      transition:top .15s linear}
    #marca i{display:block;font-style:normal;font-size:11px;opacity:.8}
    #texto p{margin:0 0 .85em;line-height:1.45;text-wrap:pretty;cursor:pointer;
      opacity:.45;border-left:3px solid transparent;padding-left:.6em;
      transition:opacity .12s}
    /* Las acotaciones de escena NO van en la columna de lectura. Alberto lo
       pidió el 12 de octubre de 2026: "esta pantalla de guión es para lectura
       en vivo, pero este párrafo no lo puedo leer en voz alta". Una acotación
       metida delante de la frase obliga a descifrarla y saltarla en voz alta, y
       una acotación que es su propio párrafo se lleva una parada entera.

       Van a una franja al costado derecho, alineadas con su párrafo. Ahí no
       estorban al leer, se consultan cuando hacen falta, y al repasar el guion
       antes de clase se ven todas. La franja la abre el padding de #texto, y
       cada acotación cuelga de su propio párrafo con position:absolute, así que
       sigue a su párrafo sola, sin que nadie recalcule posiciones. */
    #texto p.acot{color:var(--tenue);font-size:.72em;font-style:italic;
      border-left-color:var(--tenue)}
    #texto p{position:relative}
    .acot-marg{position:absolute;left:100%;margin-left:14px;top:.1em;width:var(--franja);
      color:var(--tenue);font-size:.46em;line-height:1.35;font-style:italic;
      text-align:left;border-left:2px solid var(--riel);padding-left:7px;
      pointer-events:none;text-wrap:pretty}
    #texto p.actual .acot-marg{color:var(--acento);border-left-color:var(--acento)}
    .rv-cam-tag{display:inline-block;margin-left:.5em;padding:0 .4em;
      font:600 .42em/1.6 inherit;font-style:normal;vertical-align:middle;
      background:#D9F2E6;color:#0E3D31;border-radius:3px;cursor:help}
    .acot-marg b{display:block;font-style:normal;font-weight:600;
      letter-spacing:.04em;text-transform:uppercase;font-size:.85em;opacity:.75}
    #texto p.actual{opacity:1;border-left-color:var(--acento)}
    #tit{font-weight:600;color:var(--acento);margin:0 0 6px;font-size:11px;
      text-transform:uppercase;letter-spacing:.06em}
`;

  const CSS_CLASE = `
    /* --- La lámina en curso, dentro del apuntador. Tecla M. --------------
       Para presentar con una sola pantalla: se comparte la ventana del deck
       y se mira esta, que lleva el guion y además la lámina. Va arriba
       porque es lo que se mira de reojo, y el guion queda debajo, que es lo
       que se lee de continuo.
       La lámina se dibuja dentro de un iframe con srcdoc, no clonada en este
       documento, y es a propósito: así el CSS del tema y el de reveal no se
       mezclan con el de esta ventana. Clonándola, las reglas de reveal sobre
       body y section se comían la maquetación del apuntador. */
    /* AL COSTADO por omisión. La ventana del apuntador es ancha y baja, y lo
       que escasea es el alto: una franja horizontal arriba se come justo los
       renglones de guion que hacen falta. El hueco que sobra es el lateral. */
    #mini{position:fixed;left:12px;top:12px;z-index:15;background:var(--bg);
      padding:0;display:none}
    body.conMini #mini{display:block}
    body.conMini #col{margin-left:var(--miniHueco,0px)}
    /* Solo si la ventana es estrecha vuelve arriba, que es mejor que no caber. */
    body.conMini.miniArriba #mini{left:0;right:0;top:0;padding:6px 8px 4px;
      border-bottom:1px solid var(--riel)}
    body.conMini.miniArriba #col{margin-left:auto}
    #miniCaja{position:relative;margin:0 auto;border:1px solid var(--riel);
      background:#fff;overflow:hidden}
    #miniCaja iframe{position:absolute;left:0;top:0;width:1280px;height:720px;
      border:0;display:block;transform-origin:0 0}
    #miniPie{text-align:center;font-size:11px;color:var(--tenue);
      margin-top:3px;letter-spacing:.2px}
    /* Con la lámina al costado, los relojes bajan con ella y forman un solo
       panel a la izquierda. La rejilla de seis columnas se fuerza a tres: la
       media query mira el ancho de la VENTANA, no el del panel, y en 430 px
       seis relojes no caben. Esta regla es más específica y gana sin importar
       el orden. */
    body.conMini:not(.miniArriba) #pie{left:12px;right:auto;bottom:auto;
      border-top:0;border:1px solid var(--riel);border-radius:6px;padding:8px 10px 9px}
    body.conMini:not(.miniArriba) #banda{max-width:none}
    body.conMini:not(.miniArriba) #relojes{grid-template-columns:repeat(3,minmax(0,1fr));
      gap:7px 10px}
    body.conMini:not(.miniArriba) #relojes .t.grupo::before{display:none}
    /* El pie va por encima de los paneles, no debajo: mientras se elige el
       recorte o se editan las alarmas hay que seguir viendo los relojes, que es
       justo lo que se está decidiendo. Los paneles se apartan dejándole hueco. */
    #pie{position:fixed;left:0;right:0;bottom:0;background:var(--bg);z-index:14;
      border-top:1px solid var(--tenue);padding:6px 14px 7px}
    #banda{max-width:760px;margin:0 auto}
    #barras{display:grid;grid-template-columns:auto 1fr;gap:5px 10px;align-items:center;
      margin:0 0 9px}
    #barras i{font:600 9px/1 'Noto Sans',system-ui,sans-serif;font-style:normal;
      text-transform:uppercase;letter-spacing:.09em;color:var(--tenue)}
    #barras span{display:block;height:5px;border-radius:3px;background:var(--riel);overflow:hidden}
    #barras b{display:block;height:100%;width:0;background:var(--acento);
      transition:width .3s linear}
    #barras b.total{opacity:.5}
    #barras b.aviso{background:var(--ambar)}
    /* Una sola rejilla de columnas iguales: seis relojes en fila cuando la
       ventana da de sí, tres y tres cuando no, siempre a la misma distancia. */
    /* Tres grupos de dos: el reloj de pared, los cronómetros, y el ritmo. Columnas iguales y
       equidistantes siempre; los filetes que separan los grupos se dibujan dentro
       del hueco, sin ocupar sitio, para no romper esa equidistancia. En una fila
       si la ventana da de sí; si no, tres y tres, que caen en los mismos grupos y
       los filetes sobran. */
    #relojes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px 16px}
    @media (min-width:800px){
      #relojes{gap:7px 14px;grid-template-columns:repeat(6,minmax(0,1fr))}
      #relojes .t.grupo::before{content:"";position:absolute;left:-7px;top:1px;bottom:4px;
        width:1px;background:var(--tenue);opacity:.6}
    }
    #relojes .t{display:flex;flex-direction:column;align-items:flex-start;min-width:0;
      position:relative}
    #relojes b{font:600 21px/1 ui-monospace,'SF Mono',Menlo,monospace;color:var(--fg);
      font-variant-numeric:tabular-nums}
    #relojes i{font:600 9px/1.9 'Noto Sans',system-ui,sans-serif;font-style:normal;
      text-transform:uppercase;letter-spacing:.09em;color:var(--tenue)}
    #relojes b.pasado{color:var(--acento)}
    #relojes b.aviso,#relojes i.aviso{color:var(--ambar)}
    #relojes b.tarde,#relojes i.tarde{color:var(--rojo)}
    #meta{display:flex;flex-wrap:wrap;gap:6px;justify-content:space-between;margin-top:6px;
      font-size:12px;color:var(--tenue);letter-spacing:.03em}
    #meta b{color:var(--acento);font-weight:600}
    #meta #prox{color:var(--fg);opacity:.85}
    #meta #prox.cerca{color:var(--ambar);font-weight:600;opacity:1}
    /* El aviso va dentro del pie, que al llenarse crece hacia arriba. Así no
       tapa el renglón que se está leyendo, y los relojes siguen donde estaban. */
    #aviso{margin:-6px -14px 8px}
    #aviso:empty{display:none;margin:0}
    #aviso div{background:var(--acento);color:var(--bg);cursor:pointer;
      padding:11px 14px 12px;display:flex;flex-wrap:wrap;align-items:baseline;
      justify-content:space-between;gap:4px 12px;animation:entra .22s ease-out}
    #aviso div+div{border-top:1px solid var(--bg)}
    #aviso b{font:600 22px/1.15 'Noto Sans',system-ui,sans-serif}
    #aviso i{font-style:normal;font-size:11px;letter-spacing:.06em;
      text-transform:uppercase;opacity:.8}
    @keyframes entra{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
    /* El destello del borde: se ve por el rabillo del ojo sin bajar la mirada. */
    #destello{position:fixed;inset:0;pointer-events:none;z-index:9;opacity:0}
    #destello.destella{animation:pulso 1.2s ease-out 3}
    @keyframes pulso{0%{opacity:0;box-shadow:inset 0 0 0 12px var(--acento)}
      18%{opacity:1}100%{opacity:0;box-shadow:inset 0 0 0 12px var(--acento)}}
    /* El banderín de recorte, encima del guion: dice de un vistazo que esta
       lámina va abreviada o que se salta, que es lo que no se puede olvidar
       justo antes de hablar. */
    #rec{margin:0 0 14px;padding:9px 12px;border-radius:4px;
      background:var(--ambar);color:#fff;
      font:600 13px/1.35 'Noto Sans',system-ui,sans-serif;letter-spacing:.02em}
    #rec:empty{display:none;margin:0;padding:0}
    #rec.fuera{background:var(--rojo)}
    #rec b{display:block;font-size:15px;text-transform:uppercase;letter-spacing:.07em;
      margin-bottom:3px}
    #rec i{font-style:normal;opacity:.9;font-weight:400}
    /* Panel de recorte y panel de alarmas: tapan la ventana entera mientras se
       editan, que es cuando no se está presentando. */
    #recorte{position:fixed;inset:0;z-index:12;background:var(--bg);overflow:auto;
      padding:16px 16px 24px;display:none}
    body.recortando #recorte{display:block}
    #recTit{font:600 12px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.09em;color:var(--acento);margin:0 0 12px;
      display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
    #recTit i{font-style:normal;color:var(--tenue);letter-spacing:.06em}
    #recModo{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 12px}
    #recModo button{font:600 12px/1 'Noto Sans',system-ui,sans-serif;padding:8px 11px;
      cursor:pointer;border-radius:4px;border:1px solid var(--tenue);
      background:var(--bg);color:var(--tenue)}
    #recModo button.on{border-color:var(--acento);background:var(--acento);color:var(--bg)}
    #recResumen{font-size:13px;line-height:1.5;margin:0 0 12px;color:var(--fg)}
    #recResumen b{color:var(--acento)}
    .recF{display:flex;flex-wrap:wrap;gap:6px;align-items:center;
      padding:9px 0;border-bottom:1px solid var(--riel);font-size:13px}
    .recF .recN{color:var(--tenue);font-variant-numeric:tabular-nums;min-width:2.2em}
    .recF.aqui .recN{color:var(--acento);font-weight:600;font-variant-numeric:normal}
    .recF.aqui{border-bottom-width:2px;border-bottom-color:var(--tenue)}
    .recF .recT{flex:1 1 12em;min-width:8em}
    .recF .recE{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.06em;padding:4px 6px;border-radius:3px;background:var(--riel);color:var(--fg)}
    .recF .recE.n2{background:var(--ambar);color:#fff}
    .recF .recE.sc{background:transparent;color:var(--tenue);border:1px solid var(--riel)}
    .recF .recE.es{background:transparent;color:var(--tenue);border:1px dashed var(--riel)}
    .recF.plan .recE.es{background:var(--acento);color:var(--bg);border-color:var(--acento)}
    .recF .recA{margin-left:auto;display:flex;gap:5px}
    .recF button{font:600 10px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.06em;padding:6px 7px;cursor:pointer;border-radius:4px;
      border:1px solid var(--riel);background:var(--bg);color:var(--tenue)}
    .recF button:hover:not([disabled]){border-color:var(--acento);color:var(--acento)}
    .recF button.on{border-color:var(--acento);background:var(--acento);color:var(--bg)}
    .recF button[disabled]{opacity:.35;cursor:default}
    .recF.plan{background:rgba(180,105,14,.09)}
    #recPie{display:flex;gap:8px;margin:14px 0 10px}
    #recAyuda{color:var(--tenue);font-size:12px;line-height:1.5;margin:0}
    #recAyuda b{color:var(--fg)}
    #recorte .recVacio{color:var(--tenue);font-size:13px;margin:0}
    /* Panel de alarmas: tapa la ventana entera mientras se edita, que es cuando
       no se está presentando. */
    #alarmas{position:fixed;inset:0;z-index:12;background:var(--bg);overflow:auto;
      padding:16px 16px 24px;display:none}
    body.editando #alarmas,body.recortando #recorte{scroll-padding-bottom:150px}
    body.editando #alarmas{display:block}
    #alTit{font:600 12px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.09em;color:var(--acento);margin:0 0 14px;
      display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
    #alTit i{font-style:normal;color:var(--tenue);letter-spacing:.06em}
    .al{display:flex;flex-wrap:wrap;gap:7px;align-items:center;
      padding:10px 0;border-bottom:1px solid var(--riel)}
    .al .alPie{flex:1 1 100%;display:flex;gap:7px;align-items:center}
    .al .alP{margin-left:auto}
    .alVacio{color:var(--tenue);font-size:13px;margin:0 0 6px}
    #alarmas input,#alarmas select{font-family:inherit;font-size:15px;padding:5px 6px;
      color:var(--fg);background:var(--bg);border:1px solid var(--tenue);border-radius:4px}
    #alarmas .alH{width:7.4em;font-variant-numeric:tabular-nums}
    #alarmas .alT{flex:1 1 10em;min-width:7em}
    #alarmas .alS{max-width:14em}
    #alarmas button{font:600 11px/1 'Noto Sans',system-ui,sans-serif;text-transform:uppercase;
      letter-spacing:.07em;padding:7px 9px;cursor:pointer;border-radius:4px;
      border:1px solid var(--tenue);background:var(--bg);color:var(--tenue)}
    #alarmas button:hover{border-color:var(--acento);color:var(--acento)}
    #alPie{display:flex;gap:8px;margin:14px 0 10px}
    #alPie #alMas{border-color:var(--acento);color:var(--acento)}
    #alAyuda{color:var(--tenue);font-size:12px;line-height:1.5;margin:0}
    #alFuente{font-size:12px;line-height:1.5;margin:0 0 8px;color:var(--tenue)}
    #alFuente.off{color:var(--ambar);font-weight:600}`;

  const CSS = CSS_LECTURA + CSS_CLASE;

  /* ================== Sincronía del guion con la lámina ==================

     Mientras se lee un párrafo del guion, la lámina resalta la pieza de la que
     ese párrafo habla: la viñeta, el dibujo, la fórmula o el video. Alberto la
     pidió el 12 de octubre de 2026 con dos objetivos: que el grupo asocie lo
     que oye con un elemento de la lámina, y que él vea a qué elemento está
     asociado lo que está diciendo.

     El emparejamiento NO se calcula aquí. Lo escribe `tools/anclas.py` en el
     HTML, como `data-pieza` en el elemento y `data-sinc` en el párrafo, por la
     misma razón que `parcelas.py` escribe sus celdas: MathJax se lleva el texto
     de las expresiones al componerlas y en tiempo de ejecución ya no hay nada
     que comparar. Aquí solo se lee el atributo y se pinta.

     Vive en este archivo, y no en uno nuevo, porque los 30 decks enlazan estos
     ficheros por ruta relativa y **un archivo nuevo no se propaga**: habría que
     tocar las 30 páginas. Como revisar.js ya lee de aquí, la ventana de
     revisión usa el mismo motor y las dos vistas no se pueden desfasar.

     Se gobierna con la tecla Y, y se recuerda entre sesiones: apagada, el deck
     queda exactamente como si esto no existiera, porque toda la pinta cuelga de
     la clase `sinc` en el `<html>`. */

  /* Saca las acotaciones de escena de la columna de lectura y las pone en la
     franja del costado, cada una colgada de su párrafo.

     Dos casos, y el segundo es el que de verdad molesta. Un párrafo que es SOLO
     acotación se lleva una parada entera del recorrido, con su pausa y su
     resaltado, sin tener nada que leer: desaparece, y su texto se pega a la
     acotación del párrafo siguiente. Y una acotación metida DELANTE de la frase
     obliga a descifrarla y saltarla mientras se habla: se saca de la frase y la
     frase queda limpia.

     Lo usan las dos vistas de lectura, la de presentar y la de revisar, así que
     vive aquí y se publica. Se llama después de poner el innerHTML y antes de
     contar los párrafos: los que desaparecen no son paradas. */
  const RE_ACOT = /\[[^\]<>]*\]/g;

  function alMargen(doc) {
    const cont = doc.getElementById("texto");
    if (!cont) return;
    const ps = [...cont.querySelectorAll("p")];
    let arrastra = [];                 // acotaciones de párrafos que se van
    const fuera = [];
    ps.forEach((p) => {
      const sueltas = [];
      const limpio = p.innerHTML.replace(RE_ACOT, (m) => {
        sueltas.push(m.slice(1, -1).trim());
        return " ";
      });
      const prosa = limpio.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim();
      if (!prosa) {
        // nada que leer: esta parada no existe, y su acotación viaja
        arrastra = arrastra.concat(sueltas);
        fuera.push(p);
        return;
      }
      p.innerHTML = limpio.replace(/\s{2,}/g, " ").trim();
      const todas = arrastra.concat(sueltas);
      arrastra = [];
      if (!todas.length) return;
      const caja = doc.createElement("span");
      caja.className = "acot-marg";
      caja.innerHTML = "<b>en escena</b>" +
        todas.map((t) => "<span>" + t + "</span>").join("<br>");
      p.appendChild(caja);
    });
    // Lo que arrastre el final no tiene párrafo detrás: se cuelga del último.
    if (arrastra.length && ps.length) {
      const ult = ps.filter((x) => fuera.indexOf(x) < 0).pop();
      if (ult) {
        const caja = ult.querySelector(".acot-marg") || (() => {
          const c = doc.createElement("span");
          c.className = "acot-marg";
          c.innerHTML = "<b>en escena</b>";
          ult.appendChild(c);
          return c;
        })();
        caja.innerHTML += arrastra.map((t) => "<br><span>" + t + "</span>").join("");
      }
    }
    fuera.forEach((x) => x.remove());
  }

  const SINC_LLAVE = "sinc:activa";
  let sincUltima = null;              // la pieza resaltada, para no perderla
  let sincUltimasLineas = null;       // y las líneas de código, igual
  let sincFuente = null;              // quién sabe el párrafo en curso

  const sincActiva = () => {
    try { return localStorage.getItem(SINC_LLAVE) === "1"; } catch (e) { return false; }
  };

  function sincPintar(nums, cls) {
    const sec = window.Reveal && Reveal.getCurrentSlide ? Reveal.getCurrentSlide() : null;
    if (!sec) return;
    const piezas = [...sec.querySelectorAll("[data-pieza]")];
    // Sin anclas en la lámina no se atenúa nada: una lámina sin sincronía se
    // tiene que ver igual que siempre.
    const hay = !!(piezas.length && nums && nums.length);
    document.documentElement.classList.toggle("sinc", sincActiva() && hay);
    piezas.forEach((x) => {
      x.classList.toggle("sinc-aqui", hay && nums.indexOf(x.dataset.pieza) >= 0);
    });
    sincLineas(sec, hay ? cls : null);
    espejarEnMini(hay, nums);
  }

  /* El mismo resaltado, dentro de la lámina del apuntador.

     El iframe lleva srcdoc, así que es del mismo origen y se le puede tocar el
     documento. Se copian las dos marcas que usa el tema, la clase `sinc` en el
     <html> y `sinc-aqui` en la pieza, y el CSS que ya viaja dentro hace el
     resto. Sin esto, el resaltado se veía en la ventana del deck, que es
     justo la que quien presenta no está mirando. */
  function espejarEnMini(hay, nums) {
    if (!win || win.closed) return;
    const marco = win.document.getElementById("miniFrame");
    const d = marco && marco.contentDocument;
    if (!d || !d.documentElement) return;
    d.documentElement.classList.toggle("sinc", !!hay);
    [...d.querySelectorAll("[data-pieza]")].forEach((x) => {
      x.classList.toggle("sinc-aqui", !!hay && nums.indexOf(x.dataset.pieza) >= 0);
    });
  }

  /* Las LÍNEAS del bloque de código que enciende el párrafo en curso.

     Alberto lo pidió el 13 de octubre de 2026: "no se puede hacer un
     highlighting para líneas o bloques individuales de código. eso sería mucho
     mejor". Los números los escribe `tools/anclas.py` en `data-sinc-cl` del
     párrafo, emparejando los nombres que el párrafo dice con los que aparecen
     en cada línea; `tools/codigo.py` numera las líneas con `data-cl`.

     Si el párrafo no nombra ninguna línea en concreto, no se marca ninguna y el
     bloque se lee entero, que es como se comportaba antes. */
  function sincLineas(sec, cls) {
    const quiere = (cls || []).map(String);
    [...sec.querySelectorAll("pre")].forEach((pre) => {
      const lineas = [...pre.querySelectorAll(".cl[data-cl]")];
      if (!lineas.length) return;
      const alguna = quiere.length > 0;
      pre.classList.toggle("sinc-cl-hay", alguna);
      lineas.forEach((l) => l.classList.toggle(
        "sinc-cl", alguna && quiere.indexOf(l.dataset.cl) >= 0));
    });
  }

  /* Lo que llaman las dos vistas de lectura al cambiar de párrafo. El párrafo se
     pasa tal cual, para leerle su `data-sinc`; si no lo lleva, se conserva lo
     que hubiera resaltado, porque una acotación de escena en medio del guion no
     debe apagar la lámina. */
  function sincAplicar(parrafo) {
    if (!sincActiva()) { sincApagar(); return; }
    const marca = parrafo && parrafo.dataset ? parrafo.dataset.sinc : "";
    if (marca) {
      sincUltima = marca.split(/\s+/).filter(Boolean);
      // Las líneas van con su párrafo: se renuevan solo cuando el párrafo trae
      // ancla, igual que las piezas, para que una acotación de escena en medio
      // no apague el bloque.
      const cl = parrafo.dataset.sincCl || "";
      sincUltimasLineas = cl.split(/\s+/).filter(Boolean);
    }
    sincPintar(sincUltima, sincUltimasLineas);
  }

  function sincApagar() {
    document.documentElement.classList.remove("sinc");
    [...document.querySelectorAll(".sinc-aqui")].forEach((x) =>
      x.classList.remove("sinc-aqui"));
    [...document.querySelectorAll(".sinc-cl")].forEach((x) =>
      x.classList.remove("sinc-cl"));
    [...document.querySelectorAll(".sinc-cl-hay")].forEach((x) =>
      x.classList.remove("sinc-cl-hay"));
  }

  // Al cambiar de lámina se empieza de cero: lo resaltado en la anterior no
  // tiene nada que ver con las piezas de la nueva.
  function sincReiniciar() {
    sincUltima = null;
    sincUltimasLineas = null;
    if (sincActiva()) sincPintar(null, null); else sincApagar();
  }

  function sincAlternar() {
    const nueva = !sincActiva();
    try { localStorage.setItem(SINC_LLAVE, nueva ? "1" : "0"); } catch (e) {}
    if (!nueva) sincApagar();
    sincAviso(nueva);
    if (sincFuente) sincAplicar(sincFuente());   // resalta ya, sin esperar
    return nueva;
  }

  // Un aviso corto sobre la lámina, para saber que se encendió o se apagó sin
  // tener que buscar un indicador.
  function sincAviso(encendida) {
    let n = document.getElementById("sincAviso");
    if (!n) {
      n = document.createElement("div");
      n.id = "sincAviso";
      document.body.appendChild(n);
    }
    n.textContent = encendida ? "sincronía encendida" : "sincronía apagada";
    n.className = "ver";
    clearTimeout(n.__t);
    n.__t = setTimeout(() => { n.className = ""; }, 1400);
  }

  /* Lo único que este archivo publica hacia fuera. revisar.js se carga después
     que este, así que al abrir su ventana ya está puesto; si algún deck viejo
     no cargara el apuntador, el anotador lo encuentra vacío y su ventana sale
     sin estilar, pero abre igual. */
  window.ApuntadorTema = { lecturaCSS: CSS_LECTURA, alMargen: alMargen };
  window.ApuntadorSync = {
    aplicar: sincAplicar,
    reiniciar: sincReiniciar,
    alternar: sincAlternar,
    activa: sincActiva,
    // La vista de lectura que esté abierta registra aquí cómo preguntarle por
    // su párrafo en curso, y así encender la sincronía resalta en el acto.
    registrar: (f) => { sincFuente = f; },
    pedirParrafo: () => { if (sincFuente) sincAplicar(sincFuente()); },
  };

  const CUERPO = `
    <div id="mini"><div id="miniCaja"><iframe id="miniFrame" title="La lámina en curso"></iframe></div>
      <div id="miniPie"></div></div>
    <div id="col"><div id="marca"><b id="mPos"></b><i id="mPct"></i></div>
      <div id="rec"></div><div id="texto"></div></div>
    <div id="recorte">
      <div id="recTit">Recorte en vivo <i id="recEstado"></i></div>
      <div id="recModo">
        <button type="button" data-modo="0">Apagado</button>
        <button type="button" data-modo="1">Solo nivel 1</button>
        <button type="button" data-modo="2">Niveles 1 y 2</button>
      </div>
      <p id="recResumen"></p>
      <div id="recLista"></div>
      <div id="recPie"><button type="button" id="recFin">Cerrar</button></div>
      <p id="recAyuda">El plan se arma solo con lo que falta: abrevia lo que tiene
        guion corto y salta lo que no, empezando siempre por el <b>nivel 1</b>, que
        se pierde sin que nadie se entere. El <b>nivel 2</b> solo entra si lo
        enciendes aquí, porque cortarlo obliga a decirle al grupo que se retoma
        después. Cada lámina se puede fijar a mano, y entonces el plan la respeta.
        La primera fila es <b>la lámina que se está dando</b>, esté marcada o no:
        el núcleo no se pierde nunca, pero contarlo corto no es perderlo.
        C cierra este panel.</p>
    </div>
    <div id="destello"></div>
    <div id="alarmas">
      <div id="alTit">Alarmas <i id="alHorario"></i></div>
      <div id="alLista"></div>
      <div id="alPie">
        <button type="button" id="alMas">Añadir alarma</button>
        <button type="button" id="alFin">Cerrar</button>
      </div>
      <p id="alFuente"></p>
      <p id="alAyuda">Cada alarma se dispara a su hora de reloj y muestra su texto
        sobre los relojes. El sonido sale por las bocinas del equipo, así que si
        compartes pantalla con audio el grupo lo oye. Las alarmas valen para todas
        las sesiones. A cierra este panel.</p>
    </div>
    <div id="pie"><div id="aviso"></div><div id="banda">
      <div id="barras">
        <i>lámina</i><span><b id="avLamina"></b></span>
        <i>total</i><span><b id="avTotal" class="total"></b></span>
      </div>
      <div id="tit"></div>
      <div id="relojes">
        <span class="t"><b id="hora">--:--:--</b><i>hora</i></span>
        <span class="t"><b id="clase">--:--</b><i>clase</i></span>
        <span class="t grupo"><b id="lamina">0:00</b><i>lámina</i></span>
        <span class="t"><b id="total">0:00</b><i>sesión</i></span>
        <span class="t grupo"><b id="guion">--:--</b><i>guion</i></span>
        <span class="t"><b id="holgura">--:--</b><i id="veredicto">holgura</i></span>
      </div>
      <div id="meta"><span id="pos"></span><span id="prox"></span>
        <span>+ - tamaño &nbsp; N color &nbsp; R relojes &nbsp; H horario
          &nbsp; C recorte &nbsp; A alarmas &nbsp; V ventana
          &nbsp; Y sincronía</span></div>
    </div></div>`;
  const HTML = `<!doctype html><html lang="es"><head><meta charset="utf-8">
    <title>Apuntador</title><style>${CSS}</style></head><body>${CUERPO}</body></html>`;

  // La hora, el cronómetro de la sesión y el tiempo en la lámina, cada segundo.
  function tictac() {
    if (!win || win.closed) { clearInterval(reloj); reloj = null; return; }
    recordarCaja();
    pintarMarca();   // por si cambió el tamaño de letra o el de la ventana
    const d = win.document, ahora = new Date();
    const h = d.getElementById("hora");
    if (!h) return;
    revisarAlarmas();
    pintarProxima();
    h.textContent = dos(ahora.getHours()) + ":" + dos(ahora.getMinutes()) + ":" + dos(ahora.getSeconds());
    d.getElementById("total").textContent = cuenta(Date.now() - inicio);

    const enLamina = Date.now() - desdeLamina;
    const l = d.getElementById("lamina");
    l.textContent = cuenta(enLamina);
    const sec = Reveal.getCurrentSlide();
    const min = sec ? parseFloat(sec.dataset.min || "") : NaN;
    l.className = min > 0 && enLamina > min * 60000 ? "pasado" : "";

    // Segunda fila: lo que falta de guion, lo que falta de clase, y la resta.
    const k = laminas().indexOf(sec) < 0 ? 0 : laminas().indexOf(sec);
    const enParrafo = desdeParrafo === null ? 0 : Date.now() - desdeParrafo;
    ajustarPlan(k, parr, enParrafo, enLamina);
    pintarRecorte(k);
    const falta = faltaGuion(k, parr, enParrafo, enLamina);

    // Barras de avance. La de la lámina va por número de párrafo, que es como se
    // recorre: en el quinto de ocho, cinco octavos. La del deck va sobre la
    // estimación sin corregir por el ritmo, que es material recorrido, no tiempo.
    const x = estimacion(sec);
    const cuantos = parrafos().length || (x ? x.parrafos.length : 0);
    const totalLamina = x ? (x.fijo || msDe(x.palabras)) : 0;
    const bl = d.getElementById("avLamina");
    bl.style.width = porciento(cuantos ? parr + 1 : 0, cuantos || 1);
    // si la lámina ya se pasó de su tiempo estimado, la barra avisa
    bl.className = totalLamina > 0 && enLamina > totalLamina * ritmo() ? "aviso" : "";
    d.getElementById("avTotal").style.width =
      porciento(baseDeck() - faltaGuion(k, parr, enParrafo, enLamina, 1), baseDeck());
    const fin = finDeClase();
    // el guion es una estimación: en minutos redondos, sin fingir precisión
    d.getElementById("guion").textContent = Math.round(falta / 60000) + " min";
    const clase = fin === null ? null : fin - Date.now();
    d.getElementById("clase").textContent = clase === null ? "--:--"
      : (clase < 0 ? "-" : "") + cuenta(Math.abs(clase));
    const hol = d.getElementById("holgura"), ver = d.getElementById("veredicto");
    if (clase === null) { hol.textContent = "--:--"; hol.className = ""; ver.textContent = "holgura"; ver.className = ""; return; }
    const holgura = clase - falta;
    hol.textContent = (holgura < 0 ? "-" : "+") + cuenta(Math.abs(holgura));
    const aviso = holgura >= 180000 ? ["holgado", ""]
                : holgura >= -180000 ? ["al día", ""]
                : holgura >= -600000 ? ["apura", "aviso"] : ["recorta", "tarde"];
    ver.textContent = aviso[0];
    hol.className = aviso[1];
    ver.className = aviso[1];
  }

  // ---------------------------------------------------------------------
  // La lámina en curso dentro del apuntador. Tecla M.
  // ---------------------------------------------------------------------

  const MINI = "apuntador:mini";
  const conMini = () => localStorage.getItem(MINI) === "1";

  // El iframe se arma con el <head> del deck entero, así que trae el tema, las
  // reglas propias del deck y, en el paquete de un archivo, las imágenes ya en
  // data: URI. El <base> es para la versión servida, donde el tema pide sus
  // fondos y sus tipografías por ruta relativa.
  function srcdocDeLamina(sec) {
    const copia = sec.cloneNode(true);
    copia.querySelectorAll("aside").forEach((a) => a.remove());
    copia.removeAttribute("id");
    // Las reglas de resaltado del tema piden section.present. Sin esta
    // clase el espejo del resaltado no pintaría nada dentro del iframe.
    copia.classList.add("present");
    const cabeza = [...document.querySelectorAll('link[rel="stylesheet"], style')]
      .map((n) => n.outerHTML).join("");
    return '<!doctype html><html lang="es"><head><meta charset="utf-8">' +
      '<base href="' + location.href.replace(/"/g, "&quot;") + '">' + cabeza +
      "<style>html,body{margin:0;padding:0;overflow:hidden;background:#fff}" +
      ".reveal .slides{position:static;left:auto;top:auto;transform:none;" +
      "width:1280px;height:720px;padding:0;text-align:left}" +
      ".reveal .slides>section{display:block!important;position:relative!important;" +
      "opacity:1!important;visibility:visible!important;transform:none!important;" +
      "left:0!important;top:0!important}</style></head><body>" +
      '<div class="reveal"><div class="slides">' + copia.outerHTML +
      "</div></div></body></html>";
  }

  // La caja se dimensiona a lo ancho de la ventana, entre 240 y 560 px, y el
  // guion baja justo lo que ocupe. Se recalcula al redimensionar porque la
  // ventana del apuntador se mueve y se estira todo el rato.
  function medirMini() {
    if (!win || win.closed) return;
    const d = win.document;
    const caja = d.getElementById("miniCaja"), panel = d.getElementById("mini");
    const col = d.getElementById("col");
    if (!caja || !panel || !col) return;
    if (!d.body.classList.contains("conMini")) { col.style.paddingTop = ""; return; }
    const v = win.innerWidth || 720;
    // Al costado mientras quepa la lámina junto a la columna de lectura; por
    // debajo de 980 px no cabe y se pone arriba.
    const alLado = v >= 980;
    d.body.classList.toggle("miniArriba", !alLado);
    const ancho = alLado
      ? Math.max(240, Math.min(520, Math.round(v * 0.30)))
      : Math.max(240, Math.min(560, Math.round((v - 24) * 0.62)));
    caja.style.width = ancho + "px";
    caja.style.height = Math.round(ancho * 720 / 1280) + "px";
    const marco = d.getElementById("miniFrame");
    if (marco) marco.style.transform = "scale(" + (ancho / 1280) + ")";
    const pie = d.getElementById("pie");
    if (alLado) {
      d.body.style.setProperty("--miniHueco", (ancho + 30) + "px");
      col.style.paddingTop = "";
      // El pie cuelga de la miniatura: mismo ancho y pegado debajo.
      if (pie) {
        pie.style.top = (12 + panel.offsetHeight + 10) + "px";
        pie.style.width = ancho + "px";
      }
    } else {
      d.body.style.removeProperty("--miniHueco");
      col.style.paddingTop = (panel.offsetHeight + 10) + "px";
      if (pie) { pie.style.top = ""; pie.style.width = ""; }
    }
  }

  function pintarMini() {
    if (!win || win.closed) return;
    const d = win.document;
    if (!d.body.classList.contains("conMini")) return;
    const marco = d.getElementById("miniFrame");
    const sec = Reveal.getCurrentSlide();
    if (!marco || !sec) return;
    marco.srcdoc = srcdocDeLamina(sec);
    // El iframe nace limpio, así que el resaltado se repone cuando acaba de
    // cargar. Sin esto, cambiar de lámina apagaba la sincronía en la copia.
    marco.onload = () => { if (window.ApuntadorSync) ApuntadorSync.pedirParrafo(); };
    const pie = d.getElementById("miniPie");
    if (pie) {
      const i = Reveal.getSlides().indexOf(sec) + 1;
      pie.textContent = "lámina " + i + " de " + Reveal.getTotalSlides() +
        "  ·  lo que se está proyectando";
    }
    medirMini();
  }

  function alternarMini() {
    if (!win || win.closed) return;
    const puesto = win.document.body.classList.toggle("conMini");
    localStorage.setItem(MINI, puesto ? "1" : "0");
    if (!puesto) {
      const pie = win.document.getElementById("pie");
      if (pie) { pie.style.top = ""; pie.style.width = ""; }
    }
    if (puesto) pintarMini(); else medirMini();
  }

  function pintar() {
    if (!win || win.closed) return;
    sincReiniciar();                // lo resaltado era de la lámina anterior
    const sec = Reveal.getCurrentSlide();
    cerrarParrafo();                 // lo que se leyó de la lámina que se deja
    enCurso = laminas().indexOf(sec);
    desdeLamina = Date.now();
    const d = win.document;
    const h = sec.querySelector("h1,h2") || sec.querySelector(".titulo,.gracias");
    d.getElementById("tit").textContent = h ? h.textContent.trim() : sec.id;
    // Con la lámina recortada se lee su guion corto, que para eso está escrito.
    const est = estado(enCurso);
    const notas = sec.querySelector("aside.notes");
    const corto = sec.querySelector("aside.corto");
    const fuente = est !== "completa" && corto ? corto : notas;
    d.getElementById("texto").innerHTML = fuente ? fuente.innerHTML : "<p>(sin guion)</p>";
    // las acotaciones de escena salen de la columna y se van al margen
    alMargen(d);
    const ps = [...d.querySelectorAll("#texto p")];
    const ultimo = alUltimo;          // se venía de la lámina siguiente, hacia atrás
    abrirParrafo(ultimo && ps.length ? ps.length - 1 : 0);
    alUltimo = false;
    const i = Reveal.getSlides().indexOf(sec) + 1;
    d.getElementById("pos").innerHTML = "<b>" + i + "</b> de " + Reveal.getTotalSlides() +
      "&nbsp;&nbsp; clase " + horario().replace("-", " a ");
    pintarMini();         // la lámina que se está proyectando, si está puesta
    win.scrollTo(0, 0);   // arriba del todo, que la cabecera no tape el primer renglón
    marcar(ultimo);       // si se entra por el final, hay que bajar hasta él
    tictac();
  }

  const parrafos = () => (win && !win.closed ? [...win.document.querySelectorAll("#texto p")] : []);

  // Deja el párrafo en curso pegado al margen superior, para que la mirada se
  // aparte lo menos posible del lente de la webcam, que está justo encima. Los
  // doce píxeles son aire: el texto tocando el borde se lee peor.
  function marcar(desplazar) {
    const ps = parrafos();
    ps.forEach((x, i) => x.classList.toggle("actual", i === parr));
    pintarMarca();
    sincAplicar(ps[parr]);          // la lámina resalta la pieza de este párrafo
    const x = ps[parr];
    if (!x || desplazar === false) return;
    const arriba = x.getBoundingClientRect().top + (win.scrollY || win.pageYOffset || 0);
    win.scrollTo(0, Math.max(0, arriba - 12));
  }

  // La marca del costado: párrafo sobre el total de la lámina, y ese mismo avance
  // en porciento, centrada a la altura del párrafo en curso.
  function pintarMarca() {
    if (!win || win.closed) return;
    const d = win.document, marca = d.getElementById("marca");
    if (!marca) return;
    const ps = parrafos(), x = ps[parr];
    if (!x) { marca.style.visibility = "hidden"; return; }
    marca.style.visibility = "visible";
    d.getElementById("mPos").textContent = (parr + 1) + "/" + ps.length;
    d.getElementById("mPct").textContent = Math.round(((parr + 1) / ps.length) * 100) + "%";
    marca.style.top = (x.offsetTop + x.offsetHeight / 2 - marca.offsetHeight / 2) + "px";
  }

  function mover(paso) {
    const ps = parrafos();
    // Lo que el plan salta se pasa de una vez: no hay nada que leer ahí.
    if (paso > 0 && enCurso !== null && estado(enCurso) === "fuera") {
      cerrarParrafo(); Reveal.next(); return;
    }
    const n = parr + paso;
    if (!ps.length || n >= ps.length) { cerrarParrafo(); Reveal.next(); return; }
    if (n < 0) { alUltimo = true; cerrarParrafo(); Reveal.prev(); return; }
    cerrarParrafo();
    abrirParrafo(n);
    marcar();
    tictac();
  }

  // 720 y no 560 desde el 12 de octubre de 2026: la franja de acotaciones del
  // costado ocupa 138 px, y por debajo de 640 se repliega debajo del párrafo.
  const ANCHO = 720, ALTO = 620;
  // La llave vieja llegó a significar lo contrario, cuando la flotante era la de
  // fábrica. Se borra al cargar para que nadie arrastre una preferencia con la
  // semántica cambiada: sin elección explícita manda la emergente, que es la que
  // se redimensiona.
  try { localStorage.removeItem("apuntador:ventana"); } catch (e) {}
  const flotante = () => localStorage.getItem("apuntador:flotante") === "1";

  // Tamaño y posición de la ventana emergente, tal como se hayan dejado. Así se
  // adapta una vez a la pantalla y se abre igual el resto del cuatrimestre.
  function cajaGuardada() {
    try {
      const c = JSON.parse(localStorage.getItem("apuntador:caja") || "null");
      return c && c.w > 200 && c.h > 200 ? c : null;
    } catch (e) { return null; }
  }
  function recordarCaja() {
    if (!win || win.closed || esPip || !win.outerWidth || !win.outerHeight) return;
    const c = JSON.stringify({ w: win.outerWidth, h: win.outerHeight,
                               x: win.screenX, y: win.screenY });
    if (c !== localStorage.getItem("apuntador:caja")) {
      try { localStorage.setItem("apuntador:caja", c); } catch (e) {}
    }
  }

  // Ventana de imagen sobre imagen: sin barra de direcciones y por encima de todo
  // lo demás. Hay que pedirla en el mismo gesto de la tecla, sin esperar a nada,
  // o el navegador la rechaza por falta de interacción del usuario.
  function ventanaSinBarra() {
    if (!window.documentPictureInPicture || !documentPictureInPicture.requestWindow) return null;
    try { return documentPictureInPicture.requestWindow({ width: ANCHO, height: ALTO }); }
    catch (e) { return null; }
  }

  // Ventana emergente normal, el respaldo. Centrada bajo la webcam, que es donde
  // menos se desvía la mirada, y corta, para que el pie no quede lejos del lente.
  function ventanaEmergente() {
    const c = cajaGuardada();
    const ancho = c ? c.w : ANCHO, alto = c ? c.h : ALTO;
    const izq = c && typeof c.x === "number" ? Math.max(0, c.x)
      : Math.max(0, Math.round(((window.screen && window.screen.availWidth) || ancho) / 2 - ancho / 2));
    const arriba = c && typeof c.y === "number" ? Math.max(0, c.y) : 0;
    const w = window.open("about:blank", "apuntador",
      "width=" + ancho + ",height=" + alto + ",left=" + izq +
      ",top=" + arriba + ",menubar=no,toolbar=no,location=no");
    if (!w) { alert("El navegador bloqueó la ventana del apuntador. Permite las ventanas emergentes."); return null; }
    w.document.write(HTML);
    w.document.close();
    return w;
  }

  function abrir() {
    audio();                       // dentro del gesto de la tecla, o queda mudo
    cargarAlarmas();               // lo que diga el disco manda
    if (win && !win.closed) { win.focus(); return; }
    const pip = flotante() ? ventanaSinBarra() : null;
    if (pip) { pip.then((w) => montar(w, true)).catch(() => montar(ventanaEmergente(), false)); return; }
    montar(ventanaEmergente(), false);
  }

  function montar(w, sinBarra) {
    if (!w) return;
    win = w;
    esPip = !!sinBarra;
    if (esPip) {
      win.document.head.innerHTML =
        '<meta charset="utf-8"><title>Apuntador</title><style>' + CSS + "</style>";
      win.document.body.innerHTML = CUERPO;
    }
    const guardado = parseFloat(localStorage.getItem("apuntador:tam") || "26");
    win.document.getElementById("col").style.fontSize = guardado + "px";
    if (localStorage.getItem("apuntador:oscuro") === "1") win.document.body.classList.add("oscuro");
    // La vista de la lámina, tal como se dejó la última vez. Se mide al
    // redimensionar porque esta ventana se mueve y se estira constantemente.
    if (conMini()) win.document.body.classList.add("conMini");
    win.addEventListener("resize", medirMini);
    cargarModo();                             // el recorte, tal como se dejó
    if (!inicio) inicio = Date.now();         // la sesión arranca al abrir el apuntador
    desdeLamina = Date.now();
    clearInterval(reloj);
    reloj = setInterval(tictac, 1000);
    // el panel de alarmas y el aviso, antes que el guion
    win.document.addEventListener("click", (e) => {
      const t = e.target;
      if (!t || !t.closest) return;
      const av = t.closest("#aviso div");
      if (av) { av.remove(); return; }
      const b = t.closest("button");
      if (b) {
        if (b.id === "alMas") nuevaAlarma();
        else if (b.id === "alFin") cerrarPanel();
        else if (b.id === "recFin") cerrarRec();
        else if (b.dataset.modo) ponerModo(parseInt(b.dataset.modo, 10));
        else if (b.dataset.rec) forzar(b.dataset.sid, b.dataset.rec);
        else if (b.classList.contains("alX")) { b.closest(".al").remove(); leerAlarmas(); pintarAlarmas(); }
        else if (b.classList.contains("alP")) sonar(b.closest(".al").querySelector(".alS").value);
        return;
      }
      // pinchar un párrafo lo pone en curso, sin desplazar la ventana
      const x = t.closest("#texto p");
      if (!x) return;
      const i = parrafos().indexOf(x);
      if (i < 0) return;
      cerrarParrafo();
      abrirParrafo(i);
      marcar(false);
      tictac();
    });
    ["input", "change"].forEach((ev) =>
      win.document.addEventListener(ev, (e) => {
        if (e.target && e.target.closest && e.target.closest("#alLista")) leerAlarmas();
      }));
    win.document.addEventListener("keydown", (e) => {
      // con un campo del panel enfocado, las teclas son texto y no atajos
      const tag = (e.target && e.target.tagName) || "";
      const enCampo = /^(INPUT|SELECT|TEXTAREA)$/.test(tag);
      if (e.key === "Escape") {
        if (enCampo) e.target.blur();
        if (panelRecAbierto()) { cerrarRec(); return; }
        if (panelAbierto()) { cerrarPanel(); return; }
        const av = win.document.getElementById("aviso");
        if (av) av.innerHTML = "";
        return;
      }
      if (enCampo) return;
      if (e.key === "a" || e.key === "A") {
        if (panelRecAbierto()) return;
        if (panelAbierto()) cerrarPanel(); else abrirPanel();
        return;
      }
      if (e.key === "c" || e.key === "C") {
        if (panelAbierto()) return;
        if (panelRecAbierto()) cerrarRec(); else abrirRec();
        return;
      }
      if (algunPanel()) return;
      const col = win.document.getElementById("col");
      const tam = parseFloat(col.style.fontSize) || 26;
      if (e.key === "+" || e.key === "=") { col.style.fontSize = Math.min(tam + 2, 64) + "px"; }
      else if (e.key === "-") { col.style.fontSize = Math.max(tam - 2, 14) + "px"; }
      else if (e.key === "n" || e.key === "N") { win.document.body.classList.toggle("oscuro"); }
      else if (e.key === "r" || e.key === "R") {
        inicio = Date.now(); desdeLamina = Date.now(); tictac(); return;
      }
      else if (e.key === "h" || e.key === "H") {
        // la ventana sin barra no abre diálogos: se pregunta en la del deck
        const v = (esPip ? window : win).prompt("Horario de la clase, de tal hora a tal hora", horario());
        if (v) { try { localStorage.setItem("apuntador:horario", v.trim()); } catch (e2) {} }
        pintar(); return;
      }
      else if (e.key === "v" || e.key === "V") {
        // cambia de clase de ventana; la nueva se abre con T, que hace falta el
        // gesto del usuario en la ventana del deck para pedirla
        try {
          if (flotante()) localStorage.removeItem("apuntador:flotante");
          else localStorage.setItem("apuntador:flotante", "1");
        } catch (e2) {}
        const w = win;
        win = null;
        clearInterval(reloj);
        reloj = null;
        w.close();
        return;
      }
      else if (e.key === "m" || e.key === "M") { alternarMini(); return; }
      else if (e.key === "y" || e.key === "Y") { sincAlternar(); return; }
      else if (e.key === "ArrowDown") { e.preventDefault(); mover(1); return; }
      else if (e.key === "ArrowUp") { e.preventDefault(); mover(-1); return; }
      else if (e.key === "ArrowRight" || e.key === "PageDown") { Reveal.next(); return; }
      else if (e.key === "ArrowLeft" || e.key === "PageUp") { Reveal.prev(); return; }
      else return;
      localStorage.setItem("apuntador:tam", parseFloat(win.document.getElementById("col").style.fontSize));
      localStorage.setItem("apuntador:oscuro", win.document.body.classList.contains("oscuro") ? "1" : "0");
    });
    pintar();
  }

  // el contexto de audio se crea con la tecla T, que es un gesto del usuario, y
  // se despierta con cada tecla del deck: sin gesto de por medio no suena nada
  document.addEventListener("keydown", () => {
    try { if (ctx && ctx.state === "suspended") ctx.resume(); } catch (e) {}
  });
  cargarAlarmas();                 // al cargar el deck, para saber ya si hay servidor
  Reveal.addKeyBinding({ keyCode: 84, key: "T", description: "Apuntador para leer el guion" }, abrir);
  /* La sincronía se enciende desde el deck y desde las dos vistas de lectura.
     El envoltorio es obligatorio: addKeyBinding le pasa el evento al callback, y
     sincAlternar no espera argumento hoy, pero el fallo ya ocurrió una vez con
     anotar() y no se repite. */
  Reveal.addKeyBinding(
    { keyCode: 89, key: "Y", description: "Sincronizar el guion con la lámina" },
    () => sincAlternar());
  ApuntadorSync.registrar(() => parrafos()[parr] || null);
  Reveal.on("slidechanged", () => { sincReiniciar(); pintar(); });
  window.addEventListener("beforeunload", () => {
    clearInterval(reloj);
    if (win && !win.closed) win.close();
  });
})();
