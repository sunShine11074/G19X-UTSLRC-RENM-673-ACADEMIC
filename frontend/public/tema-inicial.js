// Fija data-theme en <html> antes del primer pintado, para que la página no parpadee en otro tema
// (sistema «Proyecto 077 UI», ThemeControls). Es la misma regla que src/tema/tema.js: el modo y el
// acento guardados; si no hay, el modo del sistema operativo y el acento lima.
;(function () {
  var modo = null
  var acento = null
  try {
    modo = window.localStorage.getItem('p77-mode')
    acento = window.localStorage.getItem('p77-accent')
  } catch {
    // Sin almacenamiento: se usan los valores por omisión.
  }
  if (modo !== 'light' && modo !== 'dark') {
    modo = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  if (['lime', 'blue', 'red', 'purple'].indexOf(acento) === -1) acento = 'lime'
  document.documentElement.setAttribute('data-theme', modo + '-' + acento)
})()
