// V-08 Portafolios (P-B; SRS 4.5.2: CU-03; RF-03; RF-02; E12, E13, E15 y E16; N-08, N-10 a N-12).
// Lista con enlaces al tablero, las posiciones y las transacciones de cada portafolio; alta
// (divisa MXN), cambio de nombre y eliminación en diálogos.
// - Crear (N-10): diálogo con el nombre; E13: 201 → tablero del nuevo, que pasa a ser el activo
//   (H-4). Con 409 o 422, el motivo junto al campo.
// - Cambiar el nombre (N-11): diálogo; E15: 200 → la lista actualizada.
// - Eliminar (N-12; RF-03 crit. 3): diálogo que pide escribir el nombre; E16: 204 → mensaje de
//   RD-10. Con 422, el motivo en el diálogo. Cancelar (o Esc) no cambia nada.
// - 404 desde un diálogo (N-08): se cierra, se avisa y se recarga la lista.
// data-recorrido: V-08, crear-portafolio, nombre-portafolio, renombrar, eliminar, confirmacion,
// y en los diálogos confirmar y cancelar. Cada botón de fila lleva además data-portafolio con el
// nombre tal como se guardó, para ubicar la fila sin depender del orden.
import { useEffect, useRef, useState } from 'react'
import { esPortafolioInexistente } from '../api/cliente.js'
import { crearPortafolio, eliminarPortafolio, listarPortafolios, renombrarPortafolio } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { Enlace } from '../rutas/Enlace.jsx'
import { navegar } from '../rutas/navegacion.js'
import { useSesion } from '../sesion/useSesion.js'
import { MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { Boton } from '../ui/Boton.jsx'
import { Campo } from '../ui/Campo.jsx'
import { DialogoFormulario } from '../ui/Dialogos.jsx'
import { MensajeEstado } from '../ui/Mensajes.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { Tabla } from '../ui/Tabla.jsx'
import './catalogos.css'

const AYUDA_NOMBRE =
  'Hasta 120 caracteres. No puede repetir el nombre de otro de tus portafolios, aunque cambien las mayúsculas.'

const COLUMNAS = [
  { clave: 'nombre', encabezado: 'Portafolio' },
  { clave: 'divisa', encabezado: 'Divisa base' },
  { clave: 'vistas', encabezado: 'Consultar' },
  { clave: 'acciones', encabezado: 'Acciones' },
]

// Reparte el error de la API entre el campo del diálogo y el motivo general.
function repartirError(e, campoApi) {
  if (e?.codigo === 'datos_invalidos' && Array.isArray(e.errores) && e.errores.length > 0) {
    const delCampo = e.errores.filter((x) => x.campo === campoApi)
    const otros = e.errores.filter((x) => x.campo !== campoApi)
    return {
      campo: delCampo.length > 0 ? delCampo.map((x) => textoParaUsuario(x.mensaje)).join(' ') : null,
      general: otros.length > 0 ? otros.map((x) => textoParaUsuario(x.mensaje)).join(' ') : null,
    }
  }
  if (e?.codigo === 'nombre_duplicado' || e?.codigo === 'confirmacion_invalida') {
    return { campo: textoParaUsuario(e.mensaje), general: null }
  }
  return { campo: null, general: textoParaUsuario(e?.mensaje) }
}

export default function V08Portafolios() {
  const { datos, error, cargando, recargar } = useConsulta(() => listarPortafolios(), [])
  const { portafolioActivo, fijarPortafolioActivo } = useSesion()
  const portafolios = datos ?? []

  // dialogo: null | {tipo: 'crear'} | {tipo: 'renombrar' | 'eliminar', portafolio}
  const [dialogo, setDialogo] = useState(null)
  const [valor, setValor] = useState('')
  const [errorCampo, setErrorCampo] = useState(null)
  const [errorGeneral, setErrorGeneral] = useState(null)
  const [esperando, setEsperando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  const idCampo = dialogo?.tipo === 'eliminar' ? 'confirmacion' : 'nombre-portafolio'

  // Tras eliminar, la fila desaparece: cuando llega la lista nueva, el foco pasa a «Crear portafolio»
  // en lugar de perderse.
  const enfocarCrear = useRef(false)
  useEffect(() => {
    if (enfocarCrear.current && !cargando) {
      enfocarCrear.current = false
      document.querySelector('[data-recorrido="crear-portafolio"]')?.focus()
    }
  }, [cargando, datos])

  // Tras un rechazo, el foco vuelve al campo, que ya muestra su motivo.
  useEffect(() => {
    if (errorCampo) document.getElementById(idCampo)?.focus()
  }, [errorCampo, idCampo])

  function abrir(nuevo, valorInicial = '') {
    setMensaje('')
    setErrorCampo(null)
    setErrorGeneral(null)
    setValor(valorInicial)
    setDialogo(nuevo)
  }

  function cerrar() {
    if (esperando) return
    setDialogo(null)
    setErrorCampo(null)
    setErrorGeneral(null)
  }

  // N-08: el portafolio del diálogo ya no existe (o es ajeno).
  function portafolioDesaparecido(id) {
    setDialogo(null)
    setMensaje(MENSAJES.portafolioInexistente)
    if (portafolioActivo != null && String(portafolioActivo) === String(id)) fijarPortafolioActivo(null)
    recargar()
  }

  async function enviar() {
    if (!dialogo || esperando) return
    setEsperando(true)
    setErrorCampo(null)
    setErrorGeneral(null)
    const { tipo, portafolio } = dialogo
    try {
      if (tipo === 'crear') {
        const nuevo = await crearPortafolio(valor)
        setEsperando(false)
        setDialogo(null)
        fijarPortafolioActivo(nuevo.id)
        navegar(`/portafolios/${nuevo.id}/tablero`)
        return
      }
      if (tipo === 'renombrar') {
        await renombrarPortafolio(portafolio.id, valor)
        setEsperando(false)
        setDialogo(null)
        setMensaje(MENSAJES.portafolioRenombrado)
        recargar()
        return
      }
      if (tipo === 'eliminar') {
        await eliminarPortafolio(portafolio.id, valor)
        setEsperando(false)
        setDialogo(null)
        setMensaje(MENSAJES.portafolioEliminado)
        if (portafolioActivo != null && String(portafolioActivo) === String(portafolio.id)) {
          const primero = portafolios.find((p) => p.id !== portafolio.id)
          fijarPortafolioActivo(primero ? primero.id : null)
        }
        enfocarCrear.current = true
        recargar()
        return
      }
    } catch (e) {
      setEsperando(false)
      if (e?.estado === 401) return // N-07: la sesión lo atiende
      if (tipo !== 'crear' && esPortafolioInexistente(e)) {
        portafolioDesaparecido(portafolio.id)
        return
      }
      const { campo, general } = repartirError(e, tipo === 'eliminar' ? 'confirmacion' : 'nombre')
      setErrorCampo(campo)
      setErrorGeneral(general)
    }
  }

  const filas = portafolios.map((p) => ({
    id: p.id,
    nombre: <Enlace a={`/portafolios/${p.id}/tablero`}>{p.nombre}</Enlace>,
    divisa: p.divisa_base,
    vistas: (
      <span className="acciones-fila">
        <Enlace a={`/portafolios/${p.id}/tablero`} aria-label={`Tablero de ${p.nombre}`}>
          Tablero
        </Enlace>
        <Enlace a={`/portafolios/${p.id}/posiciones`} aria-label={`Posiciones de ${p.nombre}`}>
          Posiciones
        </Enlace>
        <Enlace a={`/portafolios/${p.id}/transacciones`} aria-label={`Transacciones de ${p.nombre}`}>
          Transacciones
        </Enlace>
      </span>
    ),
    acciones: (
      <span className="acciones-fila">
        <Boton
          variante="secundaria"
          data-recorrido="renombrar"
          data-portafolio={p.nombre}
          aria-label={`Cambiar el nombre de ${p.nombre}`}
          onClick={() => abrir({ tipo: 'renombrar', portafolio: p }, p.nombre)}
        >
          Cambiar el nombre
        </Boton>
        <Boton
          variante="secundaria"
          data-recorrido="eliminar"
          data-portafolio={p.nombre}
          aria-label={`Eliminar ${p.nombre}`}
          onClick={() => abrir({ tipo: 'eliminar', portafolio: p })}
        >
          Eliminar
        </Boton>
      </span>
    ),
  }))

  return (
    <Plantilla titulo="Portafolios" pantalla="V-08" listo={!cargando}>
      <div className="catalogos">
        <p className="catalogos-intro">
          Cada portafolio agrupa tus transacciones y se consulta por separado. Su divisa base es el peso
          mexicano (MXN).
        </p>

        <div className="catalogos-acciones">
          <Boton variante="primaria" data-recorrido="crear-portafolio" onClick={() => abrir({ tipo: 'crear' })}>
            Crear portafolio
          </Boton>
        </div>

        <MensajeEstado>{mensaje}</MensajeEstado>

        {error && !cargando ? (
          <MensajeEstado tipo="error">{textoParaUsuario(error.mensaje)}</MensajeEstado>
        ) : cargando && !datos ? (
          <p className="catalogos-cargando">{MENSAJES.consultando}</p>
        ) : (
          <Tabla
            titulo="Tus portafolios"
            columnas={COLUMNAS}
            filas={filas}
            vacio="Todavía no tienes portafolios. Crea el primero para registrar tus transacciones."
          />
        )}
      </div>

      <DialogoFormulario
        abierto={dialogo?.tipo === 'crear'}
        titulo="Crear portafolio"
        textoConfirmar="Crear portafolio"
        esperando={esperando}
        textoEspera={MENSAJES.guardando}
        error={errorGeneral}
        alEnviar={enviar}
        alCancelar={cerrar}
      >
        <Campo
          id="nombre-portafolio"
          etiqueta="Nombre del portafolio"
          ayuda={AYUDA_NOMBRE}
          error={errorCampo}
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          autoComplete="off"
        />
        <p className="catalogos-nota">Divisa base: MXN (peso mexicano), la única disponible en esta versión.</p>
      </DialogoFormulario>

      <DialogoFormulario
        abierto={dialogo?.tipo === 'renombrar'}
        titulo={dialogo?.tipo === 'renombrar' ? `Cambiar el nombre de «${dialogo.portafolio.nombre}»` : ''}
        textoConfirmar="Guardar el nombre"
        esperando={esperando}
        textoEspera={MENSAJES.guardando}
        error={errorGeneral}
        alEnviar={enviar}
        alCancelar={cerrar}
      >
        <Campo
          id="nombre-portafolio"
          etiqueta="Nombre nuevo"
          ayuda={AYUDA_NOMBRE}
          error={errorCampo}
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          autoComplete="off"
        />
        <p className="catalogos-nota">Solo cambia el nombre; la divisa base y las transacciones no cambian.</p>
      </DialogoFormulario>

      <DialogoFormulario
        abierto={dialogo?.tipo === 'eliminar'}
        titulo={dialogo?.tipo === 'eliminar' ? `Eliminar el portafolio «${dialogo.portafolio.nombre}»` : ''}
        textoConfirmar={MENSAJES.eliminarConfirmar}
        negativo
        esperando={esperando}
        textoEspera="Eliminando…"
        error={errorGeneral}
        alEnviar={enviar}
        alCancelar={cerrar}
      >
        <p>
          Se eliminarán el portafolio y todas sus transacciones. Tus intermediarios se conservan. Esta acción no
          se puede deshacer.
        </p>
        <Campo
          id="confirmacion"
          etiqueta={MENSAJES.escribeNombreParaConfirmar}
          ayuda={dialogo?.tipo === 'eliminar' ? `Nombre: ${dialogo.portafolio.nombre}` : undefined}
          error={errorCampo}
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          autoComplete="off"
        />
      </DialogoFormulario>
    </Plantilla>
  )
}
