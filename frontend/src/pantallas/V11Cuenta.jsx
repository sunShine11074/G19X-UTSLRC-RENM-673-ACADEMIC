// V-11 Cuenta (/cuenta; CU-10; RF-12 crit. 1, como evidencia, y crit. 3; 4.5.2, N-09).
// - Correo, estado y el registro de consentimiento: tipo, momento, medio y versión del aviso.
// - «Revocar mi consentimiento» abre una confirmación expresa que explica el bloqueo; al
//   confirmar (E07: 204) vuelve a V-01 con su mensaje; Cancelar no cambia nada.
import { useState } from 'react'
import { revocarConsentimiento, verCuenta } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { fecha, momento, textoConsentimiento, textoEstado } from '../formato/formato.js'
import { Enlace } from '../rutas/Enlace.jsx'
import { navegar } from '../rutas/navegacion.js'
import { useSesion } from '../sesion/useSesion.js'
import { MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { Boton } from '../ui/Boton.jsx'
import { DialogoConfirmacion } from '../ui/Dialogos.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { ResumenError } from '../ui/ResumenError.jsx'
import './cuentas.css'

export default function V11Cuenta() {
  const { olvidar } = useSesion()
  const cuenta = useConsulta(() => verCuenta(), [])
  const [confirmando, setConfirmando] = useState(false)
  const [revocando, setRevocando] = useState(false)
  const [errorDialogo, setErrorDialogo] = useState(null)
  const [errores, setErrores] = useState([])

  const datos = cuenta.datos
  const registros = Array.isArray(datos?.consentimientos) ? datos.consentimientos : []
  const activa = datos?.estado === 'activa'

  async function revocar() {
    if (revocando) return
    setRevocando(true)
    setErrorDialogo(null)
    try {
      await revocarConsentimiento()
      // En el mismo paso: la ruta cambia y la sesión se descarta (la API ya borró la cookie).
      navegar('/sesion', { reemplazar: true, estado: { mensaje: MENSAJES.consentimientoRevocado } })
      olvidar?.()
    } catch (error) {
      setRevocando(false)
      if (error?.estado === 401) return // N-07: la sesión ya terminó; la guarda lleva a V-01.
      setErrorDialogo(textoParaUsuario(error?.mensaje))
    }
  }

  return (
    <Plantilla titulo="Cuenta" pantalla="V-11" listo={!cuenta.cargando}>
      <div className="cuentas cuentas--ancha">
        <ResumenError errores={errores} />
        {cuenta.cargando && !datos && (
          <p className="cuentas__estado" role="status">
            Consultando…
          </p>
        )}
        {cuenta.error && cuenta.error.estado !== 401 && (
          <p className="cuentas__aviso-error" role="alert">
            {textoParaUsuario(cuenta.error.mensaje)}
          </p>
        )}

        {datos && (
          <>
            <section aria-labelledby="v11-datos">
              <h2 id="v11-datos">Datos de la cuenta</h2>
              <dl className="cuentas__datos">
                <div>
                  <dt>Correo</dt>
                  <dd data-recorrido="correo-cuenta">{datos.correo}</dd>
                </div>
                <div>
                  <dt>Estado</dt>
                  <dd>{textoEstado(datos.estado)}</dd>
                </div>
              </dl>
            </section>

            <section aria-labelledby="v11-consentimiento">
              <h2 id="v11-consentimiento">Registro de consentimiento</h2>
              <div className="cuentas__tabla-region" role="region" aria-labelledby="v11-consentimiento" tabIndex={0}>
                <table className="cuentas__tabla" data-recorrido="consentimientos">
                  <caption className="visualmente-oculto">
                    Registro de consentimiento: tipo, momento, medio y versión del aviso de privacidad
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Registro</th>
                      <th scope="col">Momento (hora de la Ciudad de México)</th>
                      <th scope="col">Medio</th>
                      <th scope="col">Versión del aviso</th>
                    </tr>
                  </thead>
                  <tbody>
                    {registros.map((r, i) => (
                      <tr key={`${r.tipo}-${r.momento}-${i}`}>
                        <th scope="row">{textoConsentimiento(r.tipo)}</th>
                        <td className="cifra">{momento(r.momento)}</td>
                        <td>{textoConsentimiento(r.medio)}</td>
                        <td>
                          Versión {r.version_aviso_id}, vigente desde el{' '}
                          <span className="cifra">{fecha(String(r.aviso_vigente_desde ?? '').slice(0, 10))}</span>
                        </td>
                      </tr>
                    ))}
                    {registros.length === 0 && (
                      <tr>
                        <td colSpan={4}>No hay registros de consentimiento.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              <p>
                <Enlace a="/aviso-privacidad">Leer el aviso de privacidad</Enlace>
              </p>
            </section>

            {activa && (
              <section aria-labelledby="v11-revocar">
                <h2 id="v11-revocar">Revocar el consentimiento</h2>
                <p className="lectura">{MENSAJES.revocarExplicacion}</p>
                <Boton
                  variante="negativo"
                  data-recorrido="revocar"
                  onClick={() => {
                    setErrores([])
                    setErrorDialogo(null)
                    setConfirmando(true)
                  }}
                >
                  {MENSAJES.revocarConfirmar}
                </Boton>
              </section>
            )}
          </>
        )}

        <DialogoConfirmacion
          abierto={confirmando}
          titulo="¿Revocar tu consentimiento?"
          textoConfirmar={MENSAJES.revocarConfirmar}
          negativo
          esperando={revocando}
          textoEspera="Revocando…"
          error={errorDialogo}
          alConfirmar={revocar}
          alCancelar={() => {
            if (revocando) return
            setConfirmando(false)
            setErrorDialogo(null)
          }}
        >
          <p>{MENSAJES.revocarExplicacion}</p>
          <p>Esta acción no se puede deshacer desde la aplicación.</p>
        </DialogoConfirmacion>
      </div>
    </Plantilla>
  )
}
