// V-02 Registro (/registro; CU-01; CU-09; RF-01; RF-12 crit. 1 y 2; 4.5.2, N-03 y N-04).
// - La casilla de consentimiento empieza sin marcar y nombra la versión vigente del aviso;
//   el aviso se lee en un diálogo sin salir del formulario (RF-12 crit. 1 y 2).
// - El formulario se envía tal cual: la API rechaza la falta de consentimiento (422) y el
//   motivo aparece junto a la casilla y en el resumen; no se crea nada (RF-01).
// - 201: vuelve a V-01 con «Tu cuenta quedó creada. Inicia sesión.» y el correo escrito (N-04).
// - 409 por correo: el motivo junto al correo. 409 porque cambió el aviso: lo recarga y
//   desmarca la casilla. Sin aviso vigente (503), el formulario se desactiva (N-03).
import { useState } from 'react'
import { verAviso, registrarCuenta } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { fecha } from '../formato/formato.js'
import { Enlace } from '../rutas/Enlace.jsx'
import { navegar } from '../rutas/navegacion.js'
import { AYUDAS, CASILLA_CONSENTIMIENTO, MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { Boton } from '../ui/Boton.jsx'
import { Campo, CampoContrasena } from '../ui/Campo.jsx'
import { DialogoInformativo } from '../ui/Dialogos.jsx'
import { PlantillaPublica } from '../ui/Plantilla.jsx'
import { ResumenError } from '../ui/ResumenError.jsx'
import { Casilla } from '../ui/Seleccion.jsx'
import './cuentas.css'

// Campo de la API → id del control en esta pantalla.
const CAMPOS = { correo: 'correo', contrasena: 'contrasena', consentimiento: 'casilla-consentimiento' }

function erroresDe(e) {
  if (e?.codigo === 'datos_invalidos' && Array.isArray(e.errores) && e.errores.length > 0) {
    return e.errores.map((x) => ({ campo: CAMPOS[x.campo] ?? null, mensaje: textoParaUsuario(x.mensaje) }))
  }
  if (e?.codigo === 'correo_registrado') return [{ campo: 'correo', mensaje: textoParaUsuario(e.mensaje) }]
  if (e?.codigo === 'aviso_cambio') return [{ campo: 'casilla-consentimiento', mensaje: textoParaUsuario(e.mensaje) }]
  return [{ campo: null, mensaje: textoParaUsuario(e?.mensaje) }]
}

// El texto del aviso llega como texto plano: se muestra en párrafos, nunca como HTML.
function Parrafos({ texto }) {
  const bloques = String(texto ?? '')
    .split(/\n\s*\n|\r\n\s*\r\n/)
    .map((b) => b.trim())
    .filter(Boolean)
  return bloques.map((b, i) => <p key={i}>{b}</p>)
}

export default function V02Registro() {
  const aviso = useConsulta(verAviso, [])
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [marcada, setMarcada] = useState(false)
  const [errores, setErrores] = useState([])
  const [enviando, setEnviando] = useState(false)
  const [verAvisoAbierto, setVerAvisoAbierto] = useState(false)

  const sinAviso = !!aviso.error
  const listo = !aviso.cargando
  const errorDe = (id) => errores.find((x) => x.campo === id)?.mensaje
  const vigenteDesde = aviso.datos?.vigente_desde ? fecha(aviso.datos.vigente_desde.slice(0, 10)) : null

  async function enviar(e) {
    e.preventDefault()
    if (enviando || sinAviso || !aviso.datos) return
    setEnviando(true)
    try {
      await registrarCuenta({
        correo,
        contrasena,
        consentimiento: marcada,
        version_aviso_id: aviso.datos.id,
      })
      navegar('/sesion', { reemplazar: true, estado: { mensaje: MENSAJES.cuentaCreada, correo } })
    } catch (error) {
      setErrores(erroresDe(error))
      if (error?.codigo === 'aviso_cambio') {
        setMarcada(false)
        aviso.recargar()
      }
      setEnviando(false)
    }
  }

  return (
    <PlantillaPublica titulo="Crear cuenta" pantalla="V-02" listo={listo}>
      <div className="cuentas">
        {sinAviso && (
          <p className="cuentas__aviso-error" role="alert">
            {textoParaUsuario(aviso.error.mensaje)}
          </p>
        )}
        <ResumenError errores={errores} titulo="No se creó la cuenta. Corrige lo siguiente:" />
        <form className="cuentas__formulario" noValidate onSubmit={enviar} aria-label="Crear cuenta">
          <fieldset className="cuentas__grupo" disabled={sinAviso}>
            <legend className="visualmente-oculto">Datos de la cuenta</legend>
            <Campo
              id="correo"
              etiqueta="Correo"
              type="email"
              inputMode="email"
              autoComplete="email"
              autoCapitalize="none"
              spellCheck="false"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              error={errorDe('correo')}
            />
            <CampoContrasena
              id="contrasena"
              etiqueta="Contraseña"
              ayuda={AYUDAS.contrasena}
              autoComplete="new-password"
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
              error={errorDe('contrasena')}
            />

            <div className="cuentas__consentimiento">
              <h2 className="cuentas__subtitulo">Consentimiento</h2>
              <p className="cuentas__version" data-recorrido="version-aviso">
                {vigenteDesde
                  ? `Aviso de privacidad vigente desde el ${vigenteDesde} (versión ${aviso.datos.id}).`
                  : aviso.cargando
                    ? 'Consultando el aviso de privacidad…'
                    : null}
              </p>
              <p>
                <Boton
                  variante="enlace"
                  data-recorrido="ver-aviso"
                  disabled={!aviso.datos}
                  onClick={() => setVerAvisoAbierto(true)}
                >
                  Leer el aviso de privacidad
                </Boton>
              </p>
              <Casilla
                id="casilla-consentimiento"
                etiqueta={CASILLA_CONSENTIMIENTO}
                marcada={marcada}
                alCambiar={setMarcada}
                error={errorDe('casilla-consentimiento')}
              />
            </div>

            <div className="acciones">
              <Boton type="submit" variante="primario" esperando={enviando} textoEspera="Creando la cuenta…" data-recorrido="crear-cuenta">
                Crear cuenta
              </Boton>
            </div>
          </fieldset>
        </form>

        <section className="cuentas__otras" aria-labelledby="v02-con-cuenta">
          <h2 id="v02-con-cuenta">¿Ya tienes cuenta?</h2>
          <p>
            <Enlace a="/sesion">Iniciar sesión</Enlace>
          </p>
        </section>

        <DialogoInformativo
          abierto={verAvisoAbierto}
          titulo="Aviso de privacidad"
          alCerrar={() => setVerAvisoAbierto(false)}
        >
          {vigenteDesde && <p className="cuentas__version">Vigente desde el {vigenteDesde}</p>}
          <div className="cuentas__aviso-texto" role="region" aria-label="Texto del aviso de privacidad" tabIndex={0}>
            <Parrafos texto={aviso.datos?.texto} />
          </div>
        </DialogoInformativo>
      </div>
    </PlantillaPublica>
  )
}
