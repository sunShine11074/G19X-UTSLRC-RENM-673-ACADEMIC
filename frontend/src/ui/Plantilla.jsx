// Plantilla y PlantillaPublica (Anexo A; 4.5.1, «Navegación»; 4.5.2).
// - Primer enlace: «Saltar al contenido» (2.4.1), visible al recibir el foco.
// - Regiones: encabezado, menú (solo con sesión), contenido principal y pie (1.3.1).
// - <main data-recorrido={pantalla}> lleva data-listo cuando `listo` es verdadero, para
//   que el guion del recorrido capture solo cuando ya llegaron los datos.
// - Un solo h1 por pantalla: el `titulo`.
import { MenuPrincipal } from './MenuPrincipal.jsx'
import '../estilos/plantilla.css'

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

function Encabezado() {
  return (
    <header className="plantilla__encabezado">
      <div className="plantilla__encabezado-interior">
        <p className="marca">
          <span className="marca__nombre">Proyecto 077</span>
          <span className="marca__lema">Consolidación de inversiones</span>
        </p>
      </div>
    </header>
  )
}

function Pie() {
  return (
    <footer className="plantilla__pie">
      <div className="plantilla__pie-interior">
        <p>Proyecto 077 · Herramienta informativa con datos de demostración.</p>
      </div>
    </footer>
  )
}

function Contenido({ titulo, pantalla, listo, children }) {
  return (
    <main
      id="contenido"
      tabIndex={-1}
      className="plantilla__contenido"
      data-recorrido={pantalla}
      data-listo={listo ? '' : undefined}
    >
      {titulo && <h1>{titulo}</h1>}
      {children}
    </main>
  )
}

export function Plantilla({ titulo, pantalla, listo, children }) {
  return (
    <div className="plantilla">
      <SaltarAlContenido />
      <Encabezado />
      <div className="plantilla__cuerpo">
        <MenuPrincipal pantalla={pantalla} />
        <Contenido titulo={titulo} pantalla={pantalla} listo={listo}>
          {children}
        </Contenido>
      </div>
      <Pie />
    </div>
  )
}

export function PlantillaPublica({ titulo, pantalla, listo, children }) {
  return (
    <div className="plantilla plantilla--publica">
      <SaltarAlContenido />
      <Encabezado />
      <div className="plantilla__cuerpo plantilla__cuerpo--publica">
        <Contenido titulo={titulo} pantalla={pantalla} listo={listo}>
          {children}
        </Contenido>
      </div>
      <Pie />
    </div>
  )
}

export default Plantilla
