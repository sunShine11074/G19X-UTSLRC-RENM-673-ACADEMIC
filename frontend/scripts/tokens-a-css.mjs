// Convierte el tokens.json del sistema de diseño «Proyecto 077 UI» en src/estilos/tokens.css.
// El sistema cambia seguido: cuando haya un tokens.json nuevo, cópialo sobre
// src/estilos/sistema/tokens.json y vuelve a generar el CSS desde frontend/:
//
//   node scripts/tokens-a-css.mjs
//
// Reglas de la salida (README del sistema, «Temas»):
// - El tema es data-theme="<modo>-<acento>" en <html>; light-lime es el predeterminado y el
//   respaldo de cualquier valor desconocido.
// - Cada token de color va en el bloque más general en que su valor no cambia: :root (igual en los
//   ocho temas), un bloque por modo, un bloque por acento (igual en claro y oscuro) o, si no, uno
//   por tema. Los valores {nombre} del JSON se escriben como var(--nombre).
// - Los tamaños de letra pasan a rem (raíz de 16 px) para que crezcan con el tamaño de letra del
//   navegador (WCAG 1.4.4); espacios, radios y tamaños de controles se quedan en px.
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const entrada = path.join(raiz, 'src/estilos/sistema/tokens.json')
const salida = path.join(raiz, 'src/estilos/tokens.css')

const t = JSON.parse(fs.readFileSync(entrada, 'utf8'))
const temas = t.color.themes.map((x) => x.id)
const PREDETERMINADO = 'light-lime'
if (!temas.includes(PREDETERMINADO)) throw new Error(`tokens.json no tiene el tema ${PREDETERMINADO}`)
const modos = [...new Set(temas.map((id) => id.split('-')[0]))]
const acentos = [...new Set(temas.map((id) => id.split('-').slice(1).join('-')))]
const [modoBase, acentoBase] = PREDETERMINADO.split('-')

const valorCss = (v) => String(v).replace(/\{([a-z0-9-]+)\}/g, 'var(--$1)')
const rem = (px) => {
  const n = Number.parseFloat(px)
  if (!String(px).endsWith('px') || Number.isNaN(n)) throw new Error(`Tamaño de letra no está en px: ${px}`)
  return `${n / 16}rem`
}
const comentario = (texto) => (texto ? ` /* ${String(texto).replace(/\*\//g, '* /')} */` : '')
const igual = (lista) => lista.every((v) => v === lista[0])

// Reparte los tokens que cambian por tema (colores y sombras) en bloques.
const bloques = { raiz: [], modo: new Map(), acento: new Map(), tema: new Map() }
const agregar = (mapa, clave, linea) => mapa.set(clave, [...(mapa.get(clave) ?? []), linea])

function repartir({ name, value, usage }) {
  if (typeof value !== 'object') {
    bloques.raiz.push(`  --${name}: ${valorCss(value)};${comentario(usage)}`)
    return
  }
  const faltan = temas.filter((id) => !(id in value))
  if (faltan.length) throw new Error(`--${name} no tiene valor para ${faltan.join(', ')}`)
  const valores = temas.map((id) => value[id])
  const linea = (v, nota) => `  --${name}: ${valorCss(v)};${nota ? comentario(usage) : ''}`
  if (igual(valores)) {
    bloques.raiz.push(linea(valores[0], true))
  } else if (modos.every((m) => igual(temas.filter((id) => id.startsWith(`${m}-`)).map((id) => value[id])))) {
    modos.forEach((m, i) => agregar(bloques.modo, m, linea(value[`${m}-${acentoBase}`], i === 0)))
  } else if (acentos.every((a) => igual(modos.map((m) => value[`${m}-${a}`])))) {
    acentos.forEach((a, i) => agregar(bloques.acento, a, linea(value[`${modoBase}-${a}`], i === 0)))
  } else {
    temas.forEach((id, i) => agregar(bloques.tema, id, linea(value[id], i === 0)))
  }
}

t.color.tokens.forEach(repartir)
t.shadow.tokens.forEach(repartir)

// Selectores: el predeterminado también aplica sin data-theme o con un valor desconocido.
const selModo = (m) => (m === modoBase ? `:root,\n:root[data-theme^='${m}']` : `:root[data-theme^='${m}']`)
const selAcento = (a) => (a === acentoBase ? `:root,\n:root[data-theme$='-${a}']` : `:root[data-theme$='-${a}']`)
const selTema = (id) => (id === PREDETERMINADO ? `:root,\n:root[data-theme='${id}']` : `:root[data-theme='${id}']`)
const bloque = (selector, lineas) => `${selector} {\n${lineas.join('\n')}\n}\n`

const fuentes = t.type.fonts
  .map(
    (f) => `@font-face {
  font-family: '${f.family}';
  src: url('./fuentes/${path.basename(f.file)}') format('woff2');
  font-weight: ${f.weight};
  font-style: ${f.style};
  font-display: swap;
}\n`,
  )
  .join('\n')

const familias = Object.entries(t.type.families).map(([k, v]) => `  --font-${k}: ${v};`)
const estilos = t.type.groups.flatMap((g) => g.styles)
const tipos = estilos.map((s) => {
  const familia = t.type.groups.find((g) => g.styles.includes(s)).family
  return `  --${s.name}: ${s.fontWeight} ${rem(s.fontSize)}/${rem(s.lineHeight)} var(--font-${familia});${comentario(s.usage)}`
})
const clases = estilos.map((s) => `.${s.name} {\n  font: var(--${s.name});\n}\n`).join('\n')

const fijos = ['spacing', 'radius', 'size', 'duration', 'easing', 'zIndex'].flatMap((grupo) => [
  `\n  /* ${grupo}${t[grupo].note ? `: ${t[grupo].note}` : ''} */`,
  ...t[grupo].tokens.map((x) => `  --${x.name}: ${x.value};${comentario(x.usage)}`),
])
const puntos = t.breakpoint.tokens.map((x) => ` *   ${x.name}: ${x.value} (${x.usage})`).join('\n')

const css = `/*
 * Tokens del sistema de diseño «${t.name}» (versión ${t.version}).
 * ARCHIVO GENERADO por scripts/tokens-a-css.mjs desde src/estilos/sistema/tokens.json: no lo
 * edites a mano; cambia el JSON y vuelve a generarlo (node scripts/tokens-a-css.mjs).
 *
 * - Tema activo: data-theme="<modo>-<acento>" en <html> (${temas.join(', ')}).
 *   Sin atributo, o con un valor desconocido, rige ${PREDETERMINADO}.
 * - Nunca escribas un color fijo en un componente: usa var(--…).
 * - Tipografía: font: var(--t-…) en CSS, o la clase .t-… en el marcado.
 * - Puntos de corte (las variables no sirven dentro de @media; escribe el valor):
${puntos}
 */

${fuentes}
:root {
  /* Familias */
${familias.join('\n')}

  /* Estilos de texto (peso tamaño/interlineado familia) */
${tipos.join('\n')}
${fijos.join('\n')}

  /* Color y sombras iguales en los ocho temas */
${bloques.raiz.join('\n')}
}

/* ---- Por modo ---- */
${[...bloques.modo].map(([m, l]) => bloque(selModo(m), l)).join('\n')}
:root[data-theme^='dark'] {
  color-scheme: dark;
}

/* ---- Por acento (los colores de cada acento ya cambian con el modo) ---- */
${[...bloques.acento].map(([a, l]) => bloque(selAcento(a), l)).join('\n')}
/* ---- Por tema ---- */
${[...bloques.tema].map(([id, l]) => bloque(selTema(id), l)).join('\n')}
/* ---- Clases de texto ---- */
${clases}`

fs.writeFileSync(salida, css.replace(/\n{3,}/g, '\n\n'), 'utf8')
console.log(`Listo: ${path.relative(raiz, salida)} (${temas.length} temas, ${t.color.tokens.length} colores).`)
