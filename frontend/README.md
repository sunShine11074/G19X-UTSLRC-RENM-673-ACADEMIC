# Cliente web del Proyecto 077

Las 12 pantallas del SRS §4.5.2 (V-01 a V-12), escritas con React 19, Vite 8 y Recharts 3. El
cliente no calcula nada: muestra las cifras tal como las entrega la API, con formato de texto
(`src/formato/formato.js`), sin convertirlas a número.

- **Sistema de diseño:** «Proyecto 077 UI», con ocho temas (modo claro u oscuro y acento lima,
  azul, rojo o morado) que la persona elige en la barra superior. Los valores viven en
  `src/estilos/sistema/tokens.json`; `src/estilos/tokens.css` se genera desde ese archivo con
  `node scripts/tokens-a-css.mjs` y no se edita a mano.
- **Íconos y fuentes:** Font Awesome Free 7 (npm) y las fuentes Manrope, DM Sans y Google Sans
  Code, autoalojadas en `src/estilos/fuentes/` (SIL Open Font License 1.1).

Cómo instalarlo, arrancarlo y probarlo: ver el [README de la raíz](../README.md), pasos 3, 5 y 7.
