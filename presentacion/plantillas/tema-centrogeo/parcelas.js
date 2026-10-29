/* El mapa flotante del terreno, con el botón "Ver parcelas" y la tecla M.
 *
 * Alberto lo pidió el 8 de octubre de 2026: "hay alguna manera de poder tener a
 * la vista el dibujo de esta lámina en toda lámina que haga mención a alguna de
 * las celdas, ya sea en bullet, dibujos, animaciones o guión, pero que el dibujo
 * no esté en el cuerpo de dichas láminas? tal vez algo flotante que salga si le
 * doy click a algún botón tipo Ver parcelas".
 *
 * Ese mismo día decidió las tres cosas que lo definen: **viaja al paquete** que
 * recibe el grupo, **marca las casillas de la lámina en curso** y no siempre las
 * mismas, y **lo abre él**, con un botón o con la tecla, en vez de aparecer solo.
 * Dijo que no a llevarlo a las sesiones 6 a 10, así que de momento lo usa una.
 *
 * GENÉRICO A PROPÓSITO. El tema no sabe nada del terreno de la brigada: el deck
 * declara su propio mapa en un `<template id="mapa-parcelas">` con un dibujo
 * cuyas casillas llevan `data-celda="columna,fila"`, y aquí solo se saca a
 * flotar y se encienden las que toquen. Un deck que no declare el template no
 * carga nada: ni botón, ni tecla, ni panel. Por eso esto puede estar en el tema
 * sin tocar las otras 29 sesiones.
 *
 * Qué casillas enciende lo dice el atributo `data-celdas` del `<section>`, que
 * escribe `tools/parcelas.py` leyendo el HTML crudo. No se buscan aquí porque
 * MathJax se lleva el texto de las expresiones al componerlas, y después de eso
 * \(\mathrm{Soc}(2,2)\) ya no es texto con una coordenada dentro.
 *
 * El CSS se inyecta desde aquí, y no desde tema-centrogeo.css, para que todo lo
 * del mapa quepa en un solo archivo y el empaquetador lo arrastre entero.
 *
 * Su prueba de regresión es tools/prueba-parcelas.py.
 */
(function () {
  const plantilla = document.getElementById('mapa-parcelas');
  if (!plantilla) return;                      // deck sin mapa: no existe nada

  const CLAVE = 'mapa-parcelas';
  const CSS = `
  .mp-boton{position:fixed;left:16px;bottom:64px;z-index:60;display:none;
    font:600 14px/1 'Noto Sans',sans-serif;color:#A42145;background:#FBFAF8;
    border:1px solid #DDD8CE;border-radius:7px;padding:9px 13px;cursor:pointer}
  .mp-boton:hover{background:#F3EFE8}
  .mp-panel{position:fixed;z-index:61;display:none;width:260px;
    background:#FBFAF8;border:1px solid #DDD8CE;border-radius:9px;
    box-shadow:0 6px 24px rgba(0,0,0,.18);user-select:none}
  .mp-panel.mp-visible{display:block}
  .mp-cab{display:flex;align-items:center;gap:8px;padding:8px 10px;
    border-bottom:1px solid #E4E0D8;cursor:move;
    font:600 13px/1.2 'Noto Sans',sans-serif;color:#7A7568}
  .mp-cab .mp-x{margin-left:auto;cursor:pointer;border:0;background:none;
    font-size:17px;line-height:1;color:#7A7568;padding:0 2px}
  .mp-cuerpo{padding:10px}
  .mp-cuerpo svg{display:block;width:100%;height:auto}
  .mp-pie{padding:0 10px 9px;font:400 12px/1.35 'Noto Sans',sans-serif;color:#7A7568}
  /* La rejilla la dibuja el deck; el color lo pone el tema, para que el dibujo
     declarado quede reducido a geometría y a su data-celda. */
  .mp-cuerpo svg .mp-celda{fill:#FFFFFF;stroke:#9A9A9A;stroke-width:1.6}
  .mp-cuerpo svg .mp-celda.mp-on{fill:#F6DDE4;stroke:#9C2148;stroke-width:3}
  .mp-cuerpo svg text{font-family:'Noto Sans',sans-serif;fill:#9A9A9A;font-size:13px}
  .mp-cuerpo svg text.mp-eti{fill:#404040;font-weight:600;font-size:12px}
  `;
  const est = document.createElement('style');
  est.textContent = CSS;
  document.head.appendChild(est);

  const boton = document.createElement('button');
  boton.className = 'mp-boton';
  boton.type = 'button';
  boton.textContent = 'Ver parcelas';
  document.body.appendChild(boton);

  const panel = document.createElement('div');
  panel.className = 'mp-panel';
  panel.innerHTML =
    '<div class="mp-cab">El terreno<button class="mp-x" type="button" ' +
    'aria-label="Cerrar el mapa">&times;</button></div>' +
    '<div class="mp-cuerpo"></div>' +
    '<div class="mp-pie">Marcadas, las parcelas de esta lámina.</div>';
  document.body.appendChild(panel);
  panel.querySelector('.mp-cuerpo').appendChild(plantilla.content.cloneNode(true));

  /* La posición y el estado se recuerdan de una sesión a otra, como hace el
   * lector de notas de estudio con su modo. Si el sitio guardado se quedó fuera
   * de la ventana, por haber cambiado de pantalla, se devuelve a la esquina. */
  function guardado() {
    try { return JSON.parse(localStorage.getItem(CLAVE) || '{}'); }
    catch (e) { return {}; }
  }
  function guardar(o) {
    try { localStorage.setItem(CLAVE, JSON.stringify(o)); } catch (e) { /* vacío */ }
  }
  function colocar(x, y) {
    const w = panel.offsetWidth || 260, h = panel.offsetHeight || 260, m = 8;
    x = Math.max(m, Math.min(x, window.innerWidth - w - m));
    y = Math.max(m, Math.min(y, window.innerHeight - h - m));
    panel.style.left = x + 'px';
    panel.style.top = y + 'px';
    return { x: x, y: y };
  }

  function laminaActual() {
    return document.querySelector('.reveal .slides section.present') ||
           document.querySelector('.reveal .slides section');
  }
  function celdasDe(sec) {
    const v = sec && sec.getAttribute('data-celdas');
    return v ? v.trim().split(/\s+/) : [];
  }

  function pintar() {
    const sec = laminaActual();
    const cel = celdasDe(sec);
    panel.querySelectorAll('[data-celda]').forEach(function (c) {
      c.classList.toggle('mp-on', cel.indexOf(c.getAttribute('data-celda')) >= 0);
    });
    boton.style.display = cel.length ? 'block' : 'none';
    // Si la lámina no nombra ninguna parcela, el mapa no se queda enseñando las
    // de la anterior: se cierra, y vuelve solo al llegar a una que sí las nombre.
    if (!cel.length && abierto()) ocultar(true);
    else if (cel.length && guardado().abierto && !abierto()) mostrar(true);
  }

  function abierto() { return panel.classList.contains('mp-visible'); }
  function mostrar(silencioso) {
    panel.classList.add('mp-visible');
    const g = guardado();
    // Por omisión arriba a la derecha, que es la zona más despejada de las
    // láminas del tema: el banner institucional ocupa la esquina y debajo casi
    // nunca hay cuerpo. Desde ahí se arrastra a donde estorbe menos, y el
    // sitio se recuerda.
    const p = colocar(typeof g.x === 'number' ? g.x : window.innerWidth - 284,
                      typeof g.y === 'number' ? g.y : 104);
    if (!silencioso) guardar({ abierto: true, x: p.x, y: p.y });
    else guardar(Object.assign({}, g, { abierto: true, x: p.x, y: p.y }));
  }
  function ocultar(silencioso) {
    panel.classList.remove('mp-visible');
    const g = guardado();
    // Al cerrarse solo, por entrar en una lámina sin parcelas, NO se olvida que
    // Alberto lo quería abierto: vuelve cuando vuelva a hacer falta.
    guardar(Object.assign({}, g, { abierto: silencioso ? !!g.abierto : false }));
  }
  /* En una lámina que no nombra ninguna parcela el mapa no se abre: el botón
   * está escondido y la tecla tampoco hace nada, para que no aparezca una
   * rejilla con todo apagado y sin nada que mirar. Cerrarlo sí se puede
   * siempre. */
  function alternar() {
    if (abierto()) { ocultar(false); return; }
    if (!celdasDe(laminaActual()).length) return;
    mostrar(false);
  }

  boton.addEventListener('click', alternar);
  panel.querySelector('.mp-x').addEventListener('click', function () { ocultar(false); });

  /* Arrastrar por la cabecera. */
  let arr = null;
  panel.querySelector('.mp-cab').addEventListener('mousedown', function (e) {
    if (e.target.classList.contains('mp-x')) return;
    const r = panel.getBoundingClientRect();
    arr = { dx: e.clientX - r.left, dy: e.clientY - r.top };
    e.preventDefault();
  });
  document.addEventListener('mousemove', function (e) {
    if (!arr) return;
    colocar(e.clientX - arr.dx, e.clientY - arr.dy);
  });
  document.addEventListener('mouseup', function () {
    if (!arr) return;
    arr = null;
    const r = panel.getBoundingClientRect();
    guardar(Object.assign({}, guardado(), { x: r.left, y: r.top }));
  });

  /* La tecla se registra UNA sola vez. La primera versión la enganchaba aquí y
   * además con Reveal.addKeyBinding, así que una pulsación real disparaba las
   * dos y el panel se abría y se cerraba en el mismo golpe: la tecla no hacía
   * nada. Lo cazó un auditor el 8 de octubre de 2026, y la prueba no lo veía
   * porque mandaba un KeyboardEvent sin keyCode, que es el que reveal compara.
   * Cuando hay reveal manda reveal, que además la enseña en su ayuda; sin él,
   * este oyente es el único.
   */
  function porTeclado(e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (e.key === 'm' || e.key === 'M') { e.preventDefault(); alternar(); }
  }
  /* Escape cierra el mapa y NO sigue viajando: sin esto reveal lo recibe
   * también y abre la vista general de láminas, que no es lo que se pidió. */
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && abierto()) {
      e.preventDefault();
      e.stopPropagation();
      ocultar(false);
    }
  }, true);

  if (window.Reveal && Reveal.on) {
    Reveal.on('slidechanged', pintar);
    if (Reveal.addKeyBinding) {
      Reveal.addKeyBinding({ keyCode: 77, key: 'M', description: 'Ver el mapa de parcelas' },
                           alternar);
    } else {
      document.addEventListener('keydown', porTeclado);
    }
    if (Reveal.isReady && Reveal.isReady()) pintar();
    else Reveal.on('ready', pintar);
  } else {
    document.addEventListener('keydown', porTeclado);
    window.addEventListener('load', pintar);
  }
})();
