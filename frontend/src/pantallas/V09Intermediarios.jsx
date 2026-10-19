// V-09 Intermediarios (P-B; SRS 4.5.2: CU-04; RF-25; RF-02; E10 y E11; N-15).
// Lista y alta, sin modificar ni eliminar (RD-09). El nombre se guarda y se muestra tal como se
// capturó, sin cambiar mayúsculas (RF-25 crit. 1; RD-14). Con 409 (nombre repetido, sin
// distinguir mayúsculas; RD-03) o 422, el motivo junto al campo y se conserva lo escrito.
// data-recorrido: V-09, nombre-intermediario y crear-intermediario.
import { useEffect, useState } from 'react'
import { crearIntermediario, listarIntermediarios } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { Boton } from '../ui/Boton.jsx'
import { Campo } from '../ui/Campo.jsx'
import { MensajeEstado } from '../ui/Mensajes.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { Tabla } from '../ui/Tabla.jsx'
import './catalogos.css'

const COLUMNAS = [{ clave: 'nombre', encabezado: 'Nombre' }]

export default function V09Intermediarios() {
  const { datos, error, cargando, recargar } = useConsulta(() => listarIntermediarios(), [])
  const [nombre, setNombre] = useState('')
  const [errorCampo, setErrorCampo] = useState(null)
  const [errorGeneral, setErrorGeneral] = useState(null)
  const [esperando, setEsperando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  useEffect(() => {
    if (errorCampo) document.getElementById('nombre-intermediario')?.focus()
  }, [errorCampo])

  async function enviar(e) {
    e.preventDefault()
    if (esperando) return
    setEsperando(true)
    setErrorCampo(null)
    setErrorGeneral(null)
    setMensaje('')
    try {
      const nuevo = await crearIntermediario(nombre)
      setEsperando(false)
      setNombre('')
      setMensaje(`${MENSAJES.intermediarioAgregado.replace(/\.$/, '')}: «${nuevo.nombre}».`)
      recargar()
    } catch (err) {
      setEsperando(false)
      if (err?.estado === 401) return // N-07: la sesión lo atiende
      if (err?.codigo === 'datos_invalidos' && Array.isArray(err.errores) && err.errores.length > 0) {
        const delCampo = err.errores.filter((x) => x.campo === 'nombre')
        const otros = err.errores.filter((x) => x.campo !== 'nombre')
        if (delCampo.length > 0) setErrorCampo(delCampo.map((x) => textoParaUsuario(x.mensaje)).join(' '))
        if (otros.length > 0) setErrorGeneral(otros.map((x) => textoParaUsuario(x.mensaje)).join(' '))
      } else if (err?.codigo === 'nombre_duplicado') {
        setErrorCampo(textoParaUsuario(err.mensaje))
      } else {
        setErrorGeneral(textoParaUsuario(err?.mensaje))
      }
    }
  }

  const filas = (datos ?? []).map((i) => ({ id: i.id, nombre: i.nombre }))

  return (
    <Plantilla titulo="Intermediarios" pantalla="V-09" listo={!cargando}>
      <div className="catalogos">
        <p className="catalogos-intro">
          Registra las casas de bolsa o los bancos con los que mantienes tus inversiones. Cada nombre se guarda tal
          como lo escribes y, una vez registrado, no se puede modificar ni eliminar.
        </p>

        <section className="catalogos-seccion" aria-labelledby="titulo-agregar-intermediario">
          <h2 id="titulo-agregar-intermediario">Agregar un intermediario</h2>
          <form className="formulario-alta" noValidate onSubmit={enviar}>
            <Campo
              id="nombre-intermediario"
              etiqueta="Nombre del intermediario"
              ayuda="Hasta 120 caracteres. No puede repetir el nombre de otro de tus intermediarios, aunque cambien las mayúsculas."
              error={errorCampo}
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              autoComplete="off"
            />
            <div className="formulario-alta-boton">
              <Boton
                type="submit"
                variante="primaria"
                data-recorrido="crear-intermediario"
                esperando={esperando}
                textoEspera={MENSAJES.guardando}
              >
                Agregar intermediario
              </Boton>
            </div>
          </form>
          {errorGeneral && <MensajeEstado tipo="error">{errorGeneral}</MensajeEstado>}
          <MensajeEstado>{mensaje}</MensajeEstado>
        </section>

        <section className="catalogos-seccion">
          {error && !cargando ? (
            <MensajeEstado tipo="error">{textoParaUsuario(error.mensaje)}</MensajeEstado>
          ) : cargando && !datos ? (
            <p className="catalogos-cargando">{MENSAJES.consultando}</p>
          ) : (
            <Tabla
              titulo="Tus intermediarios"
              columnas={COLUMNAS}
              filas={filas}
              vacio="Todavía no registras intermediarios."
            />
          )}
        </section>
      </div>
    </Plantilla>
  )
}
