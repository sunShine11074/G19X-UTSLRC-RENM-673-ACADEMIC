// LimiteError({children}) (Anexo A): atrapa el error de una pantalla y lo muestra
// dentro de la plantilla, sin desmontar la raíz ni las demás rutas.
// Si la propia plantilla fallara, un segundo límite muestra el mensaje sin ella.
import { Component } from 'react'
import { useSesion } from '../sesion/useSesion.js'
import { Plantilla, PlantillaPublica } from '../ui/Plantilla.jsx'

function TextoError({ error }) {
  return (
    <div role="alert" data-recorrido="error-pantalla" className="limite-error">
      <p>Recarga la página o vuelve a intentarlo más tarde.</p>
      {import.meta.env.DEV && <pre>{String(error?.message ?? error)}</pre>}
    </div>
  )
}

function MarcoError({ error }) {
  const { cuenta } = useSesion()
  const Marco = cuenta ? Plantilla : PlantillaPublica
  return (
    <Marco titulo="No se pudo mostrar esta pantalla." pantalla="error" listo>
      <TextoError error={error} />
    </Marco>
  )
}

class LimiteSimple extends Component {
  constructor(props) {
    super(props)
    this.state = { fallo: false }
  }

  static getDerivedStateFromError() {
    return { fallo: true }
  }

  render() {
    if (this.state.fallo) {
      return (
        <main id="contenido">
          <h1>No se pudo mostrar esta pantalla.</h1>
          <TextoError error={this.props.error} />
        </main>
      )
    }
    return this.props.children
  }
}

export class LimiteError extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null, clave: props.clave }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  // Al cambiar de ruta se vuelve a intentar.
  static getDerivedStateFromProps(props, state) {
    if (props.clave !== state.clave) return { error: null, clave: props.clave }
    return null
  }

  render() {
    if (this.state.error) {
      return (
        <LimiteSimple error={this.state.error}>
          <MarcoError error={this.state.error} />
        </LimiteSimple>
      )
    }
    return this.props.children
  }
}

export default LimiteError
