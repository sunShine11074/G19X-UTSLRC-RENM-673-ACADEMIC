// V-03 Aviso de privacidad (/aviso-privacidad; CU-09; RF-12 crit. 2).
// - Se lee con sesión y sin ella (E02 responde igual); el menú, solo con sesión.
// - El texto de la API se muestra en párrafos, nunca como HTML, hasta unos 70
//   caracteres por línea (1.4.10; 1.4.12), con su fecha de vigencia.
// - Explica cómo revocar el consentimiento (V-11; N-09).
import { verAviso } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { fecha } from '../formato/formato.js'
import { Enlace } from '../rutas/Enlace.jsx'
import { useSesion } from '../sesion/useSesion.js'
import { textoParaUsuario } from '../textos/textos.js'
import { Plantilla, PlantillaPublica } from '../ui/Plantilla.jsx'
import './cuentas.css'

function Parrafos({ texto }) {
  const bloques = String(texto ?? '')
    .split(/\n\s*\n/)
    .map((b) => b.trim())
    .filter(Boolean)
  return bloques.map((b, i) => <p key={i}>{b}</p>)
}

export default function V03AvisoPrivacidad() {
  const { cuenta } = useSesion()
  const aviso = useConsulta(verAviso, [])
  const Marco = cuenta ? Plantilla : PlantillaPublica
  const vigenteDesde = aviso.datos?.vigente_desde ? fecha(aviso.datos.vigente_desde.slice(0, 10)) : null

  return (
    <Marco titulo="Aviso de privacidad" pantalla="V-03" listo={!aviso.cargando}>
      <div className="cuentas cuentas--lectura">
        {aviso.cargando && (
          <p className="cuentas__estado" role="status">
            Consultando…
          </p>
        )}
        {aviso.error && (
          <p className="cuentas__aviso-error" role="alert">
            {textoParaUsuario(aviso.error.mensaje)}
          </p>
        )}
        {aviso.datos && (
          <article className="cuentas__aviso" aria-labelledby="v03-vigencia">
            <p id="v03-vigencia" className="cuentas__version" data-recorrido="version-aviso">
              Vigente desde el {vigenteDesde} (versión {aviso.datos.id})
            </p>
            <div className="cuentas__aviso-texto">
              <Parrafos texto={aviso.datos.texto} />
            </div>
          </article>
        )}

        <section className="cuentas__otras" aria-labelledby="v03-revocar">
          <h2 id="v03-revocar">Cómo revocar tu consentimiento</h2>
          <p>
            Puedes revocarlo en cualquier momento desde Cuenta. Al revocarlo, tu cuenta se bloquea de inmediato y ya
            no podrás iniciar sesión; mientras dure el bloqueo, tu correo no podrá registrarse de nuevo.
          </p>
          {cuenta ? (
            <p>
              <Enlace a="/cuenta">Ir a Cuenta</Enlace>
            </p>
          ) : (
            <p>
              <Enlace a="/sesion">Ir a Inicio de sesión</Enlace>
              {' · '}
              <Enlace a="/registro">Crear cuenta</Enlace>
            </p>
          )}
        </section>
      </div>
    </Marco>
  )
}
