// Plantilla y PlantillaPublica (Anexo A; 4.5.1, «Navegación»; 4.5.2) con el sistema «Proyecto 077 UI»:
// NavRail + TopBar + cuadrícula de Cards, siempre en las mismas posiciones (3.2.3).
// - Primer enlace: «Saltar al contenido» (2.4.1), visible al recibir el foco.
// - Regiones: menú (rail, solo con sesión), contenido principal y pie (1.3.1).
// - <main data-recorrido={pantalla}> lleva data-listo cuando `listo` es verdadero, para
//   que el guion del recorrido capture solo cuando ya llegaron los datos.
// - Un solo h1 por pantalla: el `titulo`, en la barra superior dentro de <main>. Al cambiar de
//   pantalla el foco va a ese h1 (no en la primera que se abre) y el título del documento lo
//   repite (2.4.2).
// - Los hijos van en la cuadrícula (.rejilla): cada uno ocupa el ancho completo salvo que lleve
//   una clase ancho-3 … ancho-8 (de 12 columnas).
import { useEffect, useRef } from 'react'
import logo from '../assets/logo-077.png'
import { useRuta } from '../rutas/navegacion.js'
import { BarraSuperior } from './BarraSuperior.jsx'
import { ControlesTema } from './ControlesTema.jsx'
import { MenuPrincipal } from './MenuPrincipal.jsx'
import '../estilos/plantilla.css'

// La primera pantalla que abre la aplicación no mueve el foco; las siguientes, sí.
let rutaInicial = null
let yaNavego = false

function useTituloYFoco(titulo) {
  const refTitulo = useRef(null)
  const { ruta } = useRuta()

  useEffect(() => {
    document.title = titulo ? `${titulo} · Proyecto 077` : 'Proyecto 077'
  }, [titulo])

  useEffect(() => {
    if (rutaInicial === null) rutaInicial = ruta
    if (!yaNavego && ruta === rutaInicial) return
    yaNavego = true
    refTitulo.current?.focus()
    // Solo al montar la pantalla (cada ruta monta la suya).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return refTitulo
}

function SaltarAlContenido() {
  return (
    <a
      href="#contenido"
      className="saltar"
      onClick={(e) => {
        // Sin cambiar el hash, para no perder el estado del historial (4.5.2, N-04).
        const destino = document.getElementById('contenido')
        if (!destino) return
        e.preventDefault()
        destino.focus()
        destino.scrollIntoView?.()
      }}
    >
      Saltar al contenido
    </a>
  )
}

function Pie() {
  return (
    <footer className="plantilla__pie">
      <p>Proyecto 077 · Herramienta informativa con datos de demostración.</p>
    </footer>
  )
}

function Contenido({ titulo, pantalla, listo, conControles, children }) {
  const refTitulo = useTituloYFoco(titulo)
  return (
    <main
      id="contenido"
      tabIndex={-1}
      className="plantilla__contenido"
      data-recorrido={pantalla}
      data-listo={listo ? '' : undefined}
    >
      {titulo && <BarraSuperior titulo={titulo} refTitulo={refTitulo} conControles={conControles} />}
      <div className="rejilla">{children}</div>
    </main>
  )
}

export function Plantilla({ titulo, pantalla, listo, children }) {
  return (
    <div className="plantilla">
      <SaltarAlContenido />
      <MenuPrincipal pantalla={pantalla} />
      <div className="plantilla__area">
        <Contenido titulo={titulo} pantalla={pantalla} listo={listo} conControles>
          {children}
        </Contenido>
        <Pie />
      </div>
    </div>
  )
}

// Sin sesión no hay rail: la marca y los controles de tema van en un encabezado propio.
export function PlantillaPublica({ titulo, pantalla, listo, children }) {
  return (
    <div className="plantilla plantilla--publica">
      <SaltarAlContenido />
      <div className="plantilla__area">
        <header className="encabezado-publico">
          <p className="marca">
            <span className="marca__logo">
              <img src={logo} width="36" height="36" alt="" />
            </span>
            <span className="marca__texto">
              <span className="marca__nombre">Proyecto 077</span>
              <span className="marca__lema">Consolidación de inversiones</span>
            </span>
          </p>
          <ControlesTema />
        </header>
        <Contenido titulo={titulo} pantalla={pantalla} listo={listo} conControles={false}>
          {children}
        </Contenido>
        <Pie />
      </div>
    </div>
  )
}

export default Plantilla
