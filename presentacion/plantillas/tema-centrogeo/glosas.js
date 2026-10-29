/* Las glosas al pasar el ratón, y la red de seguridad de MathJax.
 *
 * Alberto lo pidió el 29 de septiembre de 2026: pasar el ratón por una etiqueta
 * corta tiene que enseñar lo que la etiqueta esconde, sin sacarla de la lámina.
 * Estrenado en la sesión 8 y subido al tema el 30 de septiembre, para que las
 * 29 sesiones lo hereden al recargar. El CSS va en tema-centrogeo.css.
 *
 * Su prueba de regresión es tools/prueba-glosas.py, que mide el globo en Chrome
 * headless y corre igual sobre el deck y sobre el paquete de salidas/.
 *
 * Cada etiqueta con glosa lleva su contenido escrito dentro del documento, en
 * un .gl-pop que está fuera de la pantalla. Se escribe ahí y no se arma con
 * JavaScript para que MathJax lo componga al cargar, como compone todo lo demás.
 * Al pasar el ratón se clona a #glosa-flotante, que cuelga de <body> y se
 * coloca con coordenadas de ventana.
 *
 * Se clona en vez de moverse para que la etiqueta conserve el suyo y el globo
 * se pueda volver a abrir. El clon funciona porque MathJax está configurado con
 * fontCache local, así que cada expresión compuesta lleva sus trazos dentro y
 * no depende de un catálogo compartido.
 *
 * Responde también al clic y al foco del teclado, para quien lee el paquete en
 * una pantalla táctil, donde no hay ratón que pasar.
 */

/* Red de seguridad de MathJax.
 *
 * El 29 de septiembre de 2026 Alberto vio una expresión proyectada en LaTeX
 * crudo, en la lámina de lo que se queda esperando, y no se pudo reproducir en
 * Chrome headless ni servida ni desde el paquete. Como la causa no se pudo
 * aislar, esto no la arregla: la compensa. Cuando MathJax termina, se busca en
 * el cuerpo de las láminas cualquier resto de LaTeX sin componer, o sea la
 * marca de apertura que MathJax debería haberse llevado, y se manda componer
 * otra vez solo esos elementos.
 *
 * Es barato porque en el caso normal no encuentra nada y no hace nada.
 */
(function () {
  function rescatar() {
    if (!window.MathJax || !MathJax.typesetPromise) return;
    const sueltos = [];
    document.querySelectorAll('.reveal .cuerpo, .reveal .cuerpo *').forEach(function (el) {
      for (const n of el.childNodes) {
        if (n.nodeType === 3 && n.nodeValue.indexOf('\\(') >= 0 &&
            sueltos.indexOf(el) < 0) sueltos.push(el);
      }
    });
    if (!sueltos.length) return;
    console.warn('MathJax dejó ' + sueltos.length +
                 ' elemento(s) sin componer; se recomponen', sueltos);
    MathJax.typesetPromise(sueltos).catch(function (e) { console.error(e); });
  }
  if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
    MathJax.startup.promise.then(rescatar);
  } else {
    window.addEventListener('load', function () { setTimeout(rescatar, 1500); });
  }
})();

(function () {
  const glo = document.createElement('div');
  glo.id = 'glosa-flotante';
  document.body.appendChild(glo);
  let abierta = null;

  function cerrar() { glo.classList.remove('visible'); abierta = null; }

  function abrir(gl) {
    const fuente = gl.querySelector(':scope > .gl-pop');
    if (!fuente) return;
    glo.innerHTML = '';
    glo.appendChild(fuente.cloneNode(true));
    glo.classList.add('visible');
    abierta = gl;
    // Colocar sobre la etiqueta, y si no cabe arriba, debajo. El globo ya está
    // visible, así que su tamaño real ya se puede medir.
    const r = gl.getBoundingClientRect();
    const g = glo.getBoundingClientRect();
    const m = 8;
    let x = r.left + r.width / 2 - g.width / 2;
    x = Math.max(m, Math.min(x, window.innerWidth - g.width - m));
    let y = r.top - g.height - m;
    if (y < m) y = r.bottom + m;
    glo.style.left = x + 'px';
    glo.style.top = y + 'px';
  }

  document.addEventListener('mouseover', function (e) {
    const gl = e.target.closest ? e.target.closest('.gl') : null;
    if (gl) { if (gl !== abierta) abrir(gl); }
    else if (abierta && !glo.contains(e.target)) cerrar();
  });
  document.addEventListener('click', function (e) {
    const gl = e.target.closest ? e.target.closest('.gl') : null;
    if (gl) { e.stopPropagation(); (gl === abierta) ? cerrar() : abrir(gl); }
    else cerrar();
  });
  document.addEventListener('focusin', function (e) {
    const gl = e.target.closest ? e.target.closest('.gl') : null;
    if (gl) abrir(gl);
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') cerrar(); });
  if (window.Reveal && Reveal.on) Reveal.on('slidechanged', cerrar);
})();
