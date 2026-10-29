/* El reproductor de las animaciones de una sesión, con sus controles.
 *
 * Una lámina con animación la declara con data-video, y la parte en TRAMOS.
 * Cada tramo es un fragmento de reveal:
 *
 *   <section data-video="videos/mundos.mp4" data-min="4">
 *     <h2>Cómo se reparte la creencia</h2>
 *     <span class="tramo"          data-start="0"     data-end="20.55">Los cuatro mundos</span>
 *     <span class="tramo fragment" data-start="20.55" data-end="32.25">La unidad se reparte</span>
 *     <span class="tramo fragment" data-start="32.25" data-end="42.9">La suma de los mundos</span>
 *   </section>
 *
 * El primer tramo NO lleva `fragment`: así arranca solo al llegar a la lámina.
 * Los demás sí, y entonces la barra espaciadora los va sacando, y solo cuando
 * se acaban pasa a la lámina siguiente.
 *
 * LOS CONTROLES. Debajo del video hay una barra con seis botones:
 *
 *   tramo anterior | pausa o reproduce | tramo siguiente | repetir este tramo |
 *   bucle de este tramo | pantalla completa
 *
 * y una pista de progreso sobre el video entero, con las MARCAS de cada tramo,
 * el tramo en curso resaltado, el tiempo transcurrido y el total, y el número
 * de tramo. Se puede pinchar en la pista para saltar, y el salto arrastra
 * también el fragmento de reveal.
 *
 * El NOMBRE del tramo no se escribe en la barra: la alargaba hasta salirse de
 * la lámina. Va en el title de la propia barra, al pasar el ratón.
 *
 * Pantalla completa es de la CAJA, no del documento: dentro van el video y la
 * barra, así que los controles siguen estando. La tecla F de reveal, que pone
 * el deck entero, sigue haciendo lo suyo.
 *
 * Los botones de tramo anterior y siguiente NO cambian de lámina: en el primer
 * tramo y en el último se apagan, para que un clic de más en clase no salte a
 * otra diapositiva.
 *
 * AL ACABAR UN TRAMO EL VIDEO PARA. No sigue de largo al tramo siguiente, y no
 * repite salvo que el bucle esté encendido. El corte lo vigilan tres cosas, y
 * hacen falta las tres: el aviso timeupdate del navegador, que llega cada
 * doscientos y pico milisegundos; un repaso cuadro a cuadro; y un temporizador
 * puesto al tiempo que falta, que es el que salva si la pestaña se ralentiza.
 *
 * Todo esto viaja al paquete del grupo, para que al repasar avancen a su ritmo.
 *
 * MODO ANTIGUO, de una sola pasada en bucle y sin controles. Si la lámina no
 * declara tramos y trae data-start y data-end en el propio <section>, se
 * comporta como antes. Las sesiones 2, 6, 7 y 8 llevan su copia embebida de esa
 * versión y algún día se migran a esta.
 *
 * DOS FALLOS YA PAGADOS, los dos los vio Alberto:
 *
 *  * **pintar() no puede tocar el DOM en cada cuadro.** La primera versión
 *    rehacía el icono del botón de pausa sesenta veces por segundo, así que
 *    entre que se apretaba el ratón y se soltaba el nodo ya era otro, y el clic
 *    se perdía: el botón "no funcionaba". Ahora cada pieza se repinta solo si
 *    su valor cambió.
 *  * **insistir() no puede resucitar una pausa del usuario.** Reintentaba
 *    colocar y reproducir durante dos segundos después de montar, así que una
 *    pausa dada en ese rato se deshacía sola.
 *
 * Sus pruebas son tools/prueba-tramos.py, que mide los botones, la pista, el
 * avance, la congelación y la pantalla completa, y corre igual sobre el deck y
 * sobre el paquete; y tools/prueba-glosas.py, que comprueba con ffprobe que los
 * tramos encajen sin huecos y que el último no pase de la duración real.
 *
 * OJO al probar: en Chrome headless el video NO se decodifica, se queda en
 * readyState 1 y el seek no termina nunca. Lo que dependa de que corra de
 * verdad hay que probarlo sombreando currentTime y empujando un timeupdate.
 *
 * Los límites de los tramos se sacan del render de Manim, imprimiendo
 * self.renderer.time en cada frontera, no de sumar los run_time a mano.
 */
(function () {
  const video = document.getElementById('reproductor');
  if (!video) return;
  let fuente = '';
  let turno = 0;          // invalida los avisos de carga que llegan tarde
  let reloj = 0;          // el repaso cuadro a cuadro
  let corte = 0;          // el temporizador puesto al final del tramo
  let actual = null;      // { lista, i, ini, fin }
  let bucle = false;      // el bucle del tramo en curso, a voluntad
  let pausaManual = false;  // el usuario le dio a pausa: no se le lleva la contraria

  /* ---- la caja y la barra de controles ---------------------------------- */

  function icono(d) {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + d + '"/></svg>';
  }
  const ICO = {
    prev: 'M18 5v14l-9-7 9-7z M7 5h2.2v14H7z',
    play: 'M8 5l11 7-11 7z',
    pausa: 'M7 5h3.4v14H7z M13.6 5H17v14h-3.4z',
    next: 'M6 5l9 7-9 7z M14.8 5H17v14h-2.2z',
    rep: 'M12 5V2.2L8.2 6 12 9.8V7a5 5 0 1 1-5 5H5a7 7 0 1 0 7-7z',
    bucle: 'M7 7h10v3l4-4-4-4v3H5v6h2V7z M17 17H7v-3l-4 4 4 4v-3h12v-6h-2v4z',
    lleno: 'M4 9V4h5v2H6v3H4z M15 4h5v5h-2V6h-3V4z M4 15h2v3h3v2H4v-5z M18 15h2v5h-5v-2h3v-3z',
    salir: 'M9 4v5H4V7h3V4h2z M15 4h2v3h3v2h-5V4z M4 15h5v5H7v-3H4v-2z M15 15h5v2h-3v3h-2v-5z'
  };

  const barra = document.createElement('div');
  barra.id = 'repro-barra';
  barra.innerHTML =
    '<button data-rb="prev" title="Tramo anterior">' + icono(ICO.prev) + '</button>' +
    '<button data-rb="play" title="Pausar o reproducir">' + icono(ICO.pausa) + '</button>' +
    '<button data-rb="next" title="Tramo siguiente">' + icono(ICO.next) + '</button>' +
    '<button data-rb="rep" title="Repetir este tramo">' + icono(ICO.rep) + '</button>' +
    '<button data-rb="bucle" title="Repetir este tramo en bucle">' + icono(ICO.bucle) + '</button>' +
    '<div id="repro-pista"><div id="repro-tramo"></div><div id="repro-llena"></div>' +
    '<div id="repro-marcas"></div><div id="repro-nums"></div></div>' +
    '<span id="repro-tiempo">0:00 / 0:00</span>' +
    '<span id="repro-cuenta"></span>' +
    '<button data-rb="pantalla" title="Pantalla completa">' + icono(ICO.lleno) + '</button>';
  document.body.appendChild(barra);

  /* La caja del video y la barra se colocan EN PIXELES, calculados a partir de
     la lámina de verdad. Estaban en porcentajes contra la ventana, y reveal
     escala y centra el deck cuando la ventana no mide 1280 por 720: la barra se
     salía por la derecha y se montaba sobre el margen de abajo. Lo vio Alberto.
     No se pueden colgar de .reveal .slides, que sería lo natural, porque ese
     contenedor lleva un transform y crea su propio contexto de apilado: la
     mezcla multiplicativa del video dejaría de alcanzar el fondo y el video se
     pintaría como un rectángulo blanco. */
  function colocar_caja() {
    if (document.fullscreenElement) return;      // ahí manda el CSS de la caja
    const s = Reveal.getCurrentSlide && Reveal.getCurrentSlide();
    const cont = document.querySelector('.reveal .slides');
    const r = (s || cont) && (s || cont).getBoundingClientRect();
    if (!r || !r.width) return;
    const e = Reveal.getScale ? (Reveal.getScale() || 1) : 1;
    // La geometría del tema, en unidades de lámina: el cuerpo empieza al 25% y
    // el sello de la esquina llega al 17% del ancho.
    const x = r.left, y = r.top, W = r.width, H = r.height;
    video.style.left = (x + W * 0.0241) + 'px';
    video.style.width = (W * 0.9519) + 'px';
    video.style.top = (y + H * 0.25) + 'px';
    video.style.height = (H * 0.59) + 'px';
    video.style.transform = 'none';
    barra.style.left = (x + W * 0.20) + 'px';
    barra.style.width = (W * 0.77) + 'px';
    barra.style.top = (y + H * 0.855) + 'px';
    barra.style.height = (48 * e) + 'px';
    barra.style.fontSize = (16 * e) + 'px';
  }

  const pista = barra.querySelector('#repro-pista');
  const llena = barra.querySelector('#repro-llena');
  const marcas = barra.querySelector('#repro-marcas');
  const nums = barra.querySelector('#repro-nums');
  const resalte = barra.querySelector('#repro-tramo');
  const reloj_t = barra.querySelector('#repro-tiempo');
  const cuenta = barra.querySelector('#repro-cuenta');
  const boton = {};
  barra.querySelectorAll('button').forEach(b => { boton[b.dataset.rb] = b; });

  // Lo último pintado, para no tocar el DOM si no cambió. Es lo que arregla el
  // botón de pausa: rehacer su icono en cada cuadro se comía el clic.
  const ult = { play: null, ancho: null, tiempo: null, cuenta: null,
                prev: null, next: null, bucle: null, lleno: null };

  function mmss(s) {
    if (!isFinite(s) || s < 0) s = 0;
    return Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');
  }

  function dur() {
    // La duración real no está hasta que el archivo carga; mientras tanto vale
    // el final del último tramo, que es lo que la lámina declara.
    if (isFinite(video.duration) && video.duration > 0) return video.duration;
    if (actual) return parseFloat(
      actual.lista[actual.lista.length - 1].getAttribute('data-end')) || 1;
    return 1;
  }

  function pintarMarcas() {
    if (!actual) { marcas.innerHTML = ''; nums.innerHTML = ''; return; }
    const D = dur();
    let h = '', n = '';
    actual.lista.forEach((t, k) => {
      const a = parseFloat(t.getAttribute('data-start'));
      const b = parseFloat(t.getAttribute('data-end'));
      if (k) h += '<i style="left:' + (100 * a / D).toFixed(3) + '%"></i>';
      // El NUMERO de tramo, centrado en su banda. Alberto habla en el guion de
      // "el tramo tres", así que la pista tiene que decir cuál es cuál sin que
      // haya que contar bandas.
      n += '<i style="left:' + (100 * (a + b) / 2 / D).toFixed(3) + '%">' +
           (k + 1) + '</i>';
    });
    marcas.innerHTML = h;
    nums.innerHTML = n;
    // La marca del tramo en curso se pone aquí también: pintarMarcas() rehace
    // los números y borraría la clase hasta el siguiente cambio de tramo.
    [...nums.children].forEach((e, k) => e.classList.toggle('aqui', k === actual.i));
    resalte.style.left = (100 * actual.ini / D).toFixed(3) + '%';
    resalte.style.width = (100 * (actual.fin - actual.ini) / D).toFixed(3) + '%';
  }

  function pintar() {
    if (!actual) return;
    const D = dur();
    const a = (100 * Math.min(video.currentTime, D) / D).toFixed(2) + '%';
    if (a !== ult.ancho) { llena.style.width = a; ult.ancho = a; }
    const t = mmss(video.currentTime) + ' / ' + mmss(D);
    if (t !== ult.tiempo) { reloj_t.textContent = t; ult.tiempo = t; }
    const c = (actual.i + 1) + ' de ' + actual.lista.length;
    if (c !== ult.cuenta) {
      cuenta.textContent = c; ult.cuenta = c;
      // El número del tramo en curso va marcado en la pista.
      [...nums.children].forEach((e, k) => e.classList.toggle('aqui', k === actual.i));
    }
    const n = (actual.lista[actual.i].textContent || '').trim();
    if (n !== ult.nombre) { barra.title = n; ult.nombre = n; }
    if (video.paused !== ult.play) {
      boton.play.innerHTML = icono(video.paused ? ICO.play : ICO.pausa);
      boton.play.title = video.paused ? 'Reproducir' : 'Pausar';
      ult.play = video.paused;
    }
    const p = actual.i === 0, s = actual.i === actual.lista.length - 1;
    if (p !== ult.prev) { boton.prev.disabled = p; ult.prev = p; }
    if (s !== ult.next) { boton.next.disabled = s; ult.next = s; }
    if (bucle !== ult.bucle) {
      boton.bucle.classList.toggle('encendido', bucle); ult.bucle = bucle;
    }
    const f = !!document.fullscreenElement;
    if (f !== ult.lleno) {
      boton.pantalla.innerHTML = icono(f ? ICO.salir : ICO.lleno);
      boton.pantalla.title = f ? 'Salir de pantalla completa' : 'Pantalla completa';
      ult.lleno = f;
    }
  }

  /* ---- reproducción ----------------------------------------------------- */

  function reproducir() {
    pausaManual = false;
    const p = video.play();
    if (p && p.catch) p.catch(() => {});
  }

  function parar() {
    cancelAnimationFrame(reloj);
    clearTimeout(corte);
  }

  function ocultar() {
    video.pause();
    parar();
    video.style.display = 'none';
    barra.classList.remove('visible');
    actual = null;
  }

  function tramos(lamina) {
    return [...lamina.querySelectorAll('.tramo[data-start][data-end]')];
  }

  /* Cuál es el tramo en curso: el primero más los fragmentos ya mostrados. Se
     lee del DOM y no de un contador propio, para que al retroceder, o al llegar
     desde la rejilla, salga el que toca. */
  function cual(lista) {
    let i = 0;
    for (let k = 1; k < lista.length; k++) {
      if (lista[k].classList.contains('visible')) i = k;
    }
    return i;
  }

  /* Reproduce de `ini` a `fin` y PARA. `repite` solo lo usa el modo antiguo; en
     el modo por tramos manda `bucle`, que enciende y apaga su botón. */
  function correr(ini, fin, repite) {
    const mio = ++turno;
    video.style.display = 'block';
    parar();
    pausaManual = false;

    function alFinal() {
      if (repite || bucle) { video.currentTime = ini; reproducir(); return false; }
      video.pause();
      // Clavado en el final del tramo: si el navegador se pasa unos
      // milisegundos, se vería ya el primer cuadro del tramo siguiente.
      try { video.currentTime = Math.max(ini, fin - 0.04); } catch (e) {}
      pintar();
      return true;
    }
    function revisar() {
      if (mio !== turno) return false;
      pintar();
      if (video.currentTime < fin) return false;
      return alFinal();
    }
    video.ontimeupdate = revisar;
    (function vigilar() {
      if (mio !== turno) return;
      if (revisar()) return;
      reloj = requestAnimationFrame(vigilar);
    })();
    // Red de seguridad: si la pestaña se ralentiza, ni timeupdate ni el repaso
    // cuadro a cuadro llegan a tiempo, y el video se iría de largo.
    function armar() {
      clearTimeout(corte);
      if (mio !== turno || video.paused) return;
      const falta = (fin - video.currentTime) * 1000;
      corte = setTimeout(() => {
        if (mio !== turno || video.paused) return;
        if (video.currentTime >= fin - 0.05) alFinal(); else armar();
      }, Math.max(40, falta + 30));
    }

    function colocar() {
      if (mio !== turno) return;
      try { video.currentTime = ini; } catch (e) { return; }
      reproducir();
      armar();
    }
    // No basta con esperar loadedmetadata: al volver a un archivo ya visto, el
    // aviso puede no repetirse, y entonces arrancaría desde cero. Pero si el
    // usuario ya le dio a pausa, no se le lleva la contraria.
    function insistir(intentos) {
      if (mio !== turno || intentos <= 0 || pausaManual) return;
      if (Math.abs(video.currentTime - ini) < 0.5) { reproducir(); armar(); return; }
      colocar();
      setTimeout(() => insistir(intentos - 1), 250);
    }
    video.addEventListener('loadedmetadata',
                           () => { colocar(); pintarMarcas(); }, { once: true });
    colocar();
    setTimeout(() => insistir(8), 60);
  }

  function montar(lamina) {
    if (!lamina) { ocultar(); return; }
    const src = lamina.getAttribute('data-video');
    if (!src) { ocultar(); return; }
    if (src !== fuente) { fuente = src; video.src = src; video.load(); }

    const lista = tramos(lamina);
    if (lista.length) {
      const i = cual(lista);
      const ini = parseFloat(lista[i].getAttribute('data-start'));
      const fin = parseFloat(lista[i].getAttribute('data-end'));
      if (isNaN(ini) || isNaN(fin)) { ocultar(); return; }
      actual = { lista: lista, i: i, ini: ini, fin: fin };
      barra.classList.add('visible');
      colocar_caja();
      pintarMarcas();
      correr(ini, fin, false);
      pintar();
      return;
    }

    // Modo antiguo: un solo fragmento, en bucle y sin controles.
    const ini = parseFloat(lamina.getAttribute('data-start'));
    const fin = parseFloat(lamina.getAttribute('data-end'));
    if (isNaN(ini) || isNaN(fin)) { ocultar(); return; }
    barra.classList.remove('visible');
    actual = null;
    correr(ini, fin, lamina.getAttribute('data-loop') !== 'no');
  }

  /* ---- lo que hacen los botones ----------------------------------------- */

  function repetir() { if (actual) correr(actual.ini, actual.fin, false); }

  // El salto de tramo arrastra el fragmento de reveal, que es quien manda: así
  // la lámina y el video nunca discrepan sobre en qué tramo van.
  function aTramo(j) {
    if (!actual) return;
    j = Math.max(0, Math.min(actual.lista.length - 1, j));
    let guarda = 0;
    while (cual(tramos(Reveal.getCurrentSlide())) < j && guarda++ < 20) {
      if (Reveal.nextFragment) Reveal.nextFragment(); else break;
    }
    guarda = 0;
    while (cual(tramos(Reveal.getCurrentSlide())) > j && guarda++ < 20) {
      if (Reveal.prevFragment) Reveal.prevFragment(); else break;
    }
    montar(Reveal.getCurrentSlide());
  }

  /* La caja de pantalla completa se crea al pedirla y se deshace al salir. No
     existe el resto del tiempo a propósito: una caja permanente con z-index
     crea su propio contexto de apilado y la mezcla multiplicativa del video
     deja de alcanzar el fondo de la lámina, que se pintaba en blanco opaco. */
  let lleno = null;
  function pantalla() {
    if (document.fullscreenElement) {
      if (document.exitFullscreen) document.exitFullscreen();
      return;
    }
    lleno = document.createElement('div');
    lleno.id = 'repro-lleno';
    document.body.appendChild(lleno);
    lleno.appendChild(video);
    lleno.appendChild(barra);
    const p = lleno.requestFullscreen ? lleno.requestFullscreen() : null;
    if (p && p.catch) p.catch(() => { deshacer(); });
  }
  function deshacer() {
    if (!lleno) return;
    document.body.appendChild(video);
    document.body.appendChild(barra);
    lleno.remove();
    lleno = null;
  }
  document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) { deshacer(); colocar_caja(); }
    pintar();
  });

  barra.addEventListener('click', (e) => {
    const b = e.target.closest ? e.target.closest('button[data-rb]') : null;
    if (!b || b.disabled) return;
    e.stopPropagation();
    const q = b.dataset.rb;
    if (q === 'prev') aTramo(actual ? actual.i - 1 : 0);
    else if (q === 'next') aTramo(actual ? actual.i + 1 : 0);
    else if (q === 'rep') repetir();
    else if (q === 'pantalla') pantalla();
    else if (q === 'bucle') {
      bucle = !bucle;
      if (bucle && video.paused) repetir();
      pintar();
    } else if (q === 'play') {
      if (video.paused) {
        // Parado al final del tramo, play pasa al SIGUIENTE: es lo que se
        // espera de un reproductor, y para volver a ver el que acaba está el
        // botón de repetir. En el último tramo no hay siguiente, así que ahí
        // repite, para que darle a play no se quede sin hacer nada.
        if (actual && video.currentTime >= actual.fin - 0.1) {
          if (actual.i < actual.lista.length - 1) aTramo(actual.i + 1);
          else repetir();
        } else reproducir();
      } else { video.pause(); pausaManual = true; clearTimeout(corte); }
      pintar();
    }
  });

  // Pinchar en la pista salta a ese punto del video, y de paso al tramo que lo
  // contiene, para que el fragmento de la lámina siga en su sitio.
  pista.addEventListener('click', (e) => {
    if (!actual) return;
    e.stopPropagation();
    const r = pista.getBoundingClientRect();
    const t = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * dur();
    let j = 0;
    actual.lista.forEach((s, k) => {
      if (t >= parseFloat(s.getAttribute('data-start')) - 0.001) j = k;
    });
    if (j !== actual.i) aTramo(j);
    try { video.currentTime = t; } catch (err) {}
    reproducir();
    pintar();
  });

  /* ---- enganches -------------------------------------------------------- */

  // getCurrentSlide() lee el estado vigente. e.currentSlide puede venir
  // desfasado si algo navega durante el propio evento de arranque. Y hace falta
  // montar TAMBIEN fuera del evento: al abrir el deck directamente en una
  // lámina de video, el aviso de 'ready' ya ha pasado o la navegación del ancla
  // llega después, y la lámina se quedaba sin video y sin barra.
  /* Cambiar de lámina con la pantalla completa puesta dejaba la pantalla EN
     BLANCO: lo que el navegador muestra a pantalla completa es la caja
     #repro-lleno, que solo contiene el video y la barra, así que la lámina
     nueva queda detrás y, si no lleva video, la caja se queda vacía. Alberto lo
     vio en el aula el 6 de octubre de 2026, pasando de un video a la lámina
     siguiente con la flecha derecha. Al cambiar de lámina se sale de pantalla
     completa primero; el aviso de 'fullscreenchange' deshace la caja y vuelve a
     colocar el video en su sitio. */
  function salirDeLleno() {
    if (!lleno) return;
    // Se deshace la caja AQUI MISMO, sin esperar al aviso del navegador:
    // exitFullscreen() es asincrona, y si se esperase a ella, montar() de la
    // lamina nueva correria con el video todavia dentro de la caja.
    deshacer();
    if (document.fullscreenElement && document.exitFullscreen) {
      document.exitFullscreen().catch(() => {});
    }
  }

  const arranque = () => { salirDeLleno(); montar(Reveal.getCurrentSlide()); };
  Reveal.on('ready', arranque);
  if (Reveal.isReady && Reveal.isReady()) arranque();
  setTimeout(arranque, 400);
  Reveal.on('slidechanged', arranque);
  Reveal.on('resize', colocar_caja);
  window.addEventListener('resize', colocar_caja);
  Reveal.on('fragmentshown', arranque);
  Reveal.on('fragmenthidden', arranque);

  // V, de "ver otra vez": lo mismo que el botón de repetir, para no soltar el
  // mando a distancia. Es la única tecla que añade esta pieza, y se comprobó
  // que está libre: la V del apuntador vive en su propia ventana.
  if (Reveal.addKeyBinding) {
    Reveal.addKeyBinding(
      { keyCode: 86, key: 'V', description: 'Ver otra vez este tramo del video' },
      repetir);
  }
})();
