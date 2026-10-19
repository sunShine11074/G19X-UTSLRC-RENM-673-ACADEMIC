// V-01 Inicio de sesión (/sesion; CU-02; RF-01; 4.5.2, N-03, N-05 y N-06).
// - Con 401, el mensaje único de la API, sin decir qué falló, y la contraseña se vacía (N-05).
// - Muestra el mensaje que trae el estado del historial (N-04, N-06, N-07 y N-09) y, tras
//   el registro, deja el correo ya escrito (3.3.7).
// - Tras iniciar sesión, la guarda de rutas lleva al tablero (N-01 y N-02).
import { useState } from 'react'
import { Enlace } from '../rutas/Enlace.jsx'
import { useRuta } from '../rutas/navegacion.js'
import { useSesion } from '../sesion/useSesion.js'
import { textoParaUsuario } from '../textos/textos.js'
import { Boton } from '../ui/Boton.jsx'
import { Campo, CampoContrasena } from '../ui/Campo.jsx'
import { PlantillaPublica } from '../ui/Plantilla.jsx'
import { ResumenError } from '../ui/ResumenError.jsx'
import './cuentas.css'

// Campo de la API → id del control en esta pantalla.
const CAMPOS = { correo: 'correo', contrasena: 'contrasena' }

function erroresDe(e) {
  if (e?.codigo === 'datos_invalidos' && Array.isArray(e.errores) && e.errores.length > 0) {
    return e.errores.map((x) => ({ campo: CAMPOS[x.campo] ?? null, mensaje: textoParaUsuario(x.mensaje) }))
  }
  return [{ campo: null, mensaje: textoParaUsuario(e?.mensaje) }]
}

export default function V01InicioSesion() {
  const { estado } = useRuta()
  const { iniciar } = useSesion()
  const [correo, setCorreo] = useState(estado?.correo ?? '')
  const [contrasena, setContrasena] = useState('')
  const [errores, setErrores] = useState([])
  const [enviando, setEnviando] = useState(false)
  const mensaje = errores.length === 0 ? estado?.mensaje : null

  const errorDe = (id) => errores.find((x) => x.campo === id)?.mensaje

  async function enviar(e) {
    e.preventDefault()
    if (enviando) return
    setEnviando(true)
    try {
      const cuenta = await iniciar(correo, contrasena)
      // Con la cuenta, la guarda de rutas (N-01) lleva al destino y esta pantalla se desmonta.
      if (!cuenta) {
        setContrasena('')
        setErrores([{ campo: null, mensaje: 'No se pudo iniciar sesión. Intenta de nuevo.' }])
        setEnviando(false)
      }
    } catch (error) {
      setContrasena('')
      setErrores(erroresDe(error))
      setEnviando(false)
    }
  }

  return (
    <PlantillaPublica titulo="Iniciar sesión" pantalla="V-01" listo>
      <div className="cuentas">
        {mensaje && (
          <p className="cuentas__mensaje" role="status" data-recorrido="mensaje">
            {mensaje}
          </p>
        )}
        <ResumenError errores={errores} />
        <form className="cuentas__formulario" noValidate onSubmit={enviar} aria-label="Iniciar sesión">
          <Campo
            id="correo"
            etiqueta="Correo"
            type="email"
            inputMode="email"
            autoComplete="username"
            autoCapitalize="none"
            spellCheck="false"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            error={errorDe('correo')}
          />
          <CampoContrasena
            id="contrasena"
            etiqueta="Contraseña"
            autoComplete="current-password"
            value={contrasena}
            onChange={(e) => setContrasena(e.target.value)}
            error={errorDe('contrasena')}
          />
          <div className="acciones">
            <Boton type="submit" variante="primario" esperando={enviando} textoEspera="Iniciando sesión…" data-recorrido="entrar">
              Iniciar sesión
            </Boton>
          </div>
        </form>

        <section className="cuentas__otras" aria-labelledby="v01-sin-cuenta">
          <h2 id="v01-sin-cuenta">¿Todavía no tienes cuenta?</h2>
          <p>
            <Enlace a="/registro" data-recorrido="crear-cuenta">
              Crear cuenta
            </Enlace>
          </p>
          <p>
            <Enlace a="/aviso-privacidad" data-recorrido="ver-aviso">
              Leer el aviso de privacidad
            </Enlace>
          </p>
        </section>
      </div>
    </PlantillaPublica>
  )
}
