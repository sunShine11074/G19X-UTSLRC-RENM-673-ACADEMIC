// V-07 Registrar transacción (P-C; 4.5.2; CU-05 y CU-12; RF-05 registro; RF-26a crit. 2 y 3;
// RF-28 crit. 3; RF-04; RF-25; RF-02). N-14 sin diálogo de revisión (H-4, nivel 1).
// - Los valores se envían tal como se capturaron: cantidad, precio e importe de comisiones como
//   cadenas, y los ids como los enteros que dio la API (Anexo A). La API valida y explica.
// - Un rechazo no registra nada y lo capturado se conserva. Los motivos de datos_invalidos van
//   junto a su campo y en el resumen; los demás (409 saldo negativo, vencimiento, intervalo…),
//   solo en el resumen (H-8).
// - Un intermediario nuevo se agrega en un diálogo sin perder lo capturado y queda elegido (N-15).
import { useMemo, useState } from 'react'
import { esPortafolioInexistente } from '../api/cliente.js'
import {
  crearIntermediario,
  listarInstrumentos,
  listarIntermediarios,
  listarPortafolios,
  registrarTransaccion,
  verIntervalo,
  verPortafolio,
} from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { fecha, textoClase } from '../formato/formato.js'
import { Enlace } from '../rutas/Enlace.jsx'
import { navegar, useRuta } from '../rutas/navegacion.js'
import { AYUDAS, MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { Boton } from '../ui/Boton.jsx'
import { Campo, CampoFecha } from '../ui/Campo.jsx'
import { DialogoFormulario } from '../ui/Dialogos.jsx'
import { EtiquetaDemo } from '../ui/EtiquetaDemo.jsx'
import { MensajeEstado } from '../ui/Mensajes.jsx'
import { NoEncontrado } from '../ui/NoEncontrado.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { ResumenError } from '../ui/ResumenError.jsx'
import { Select } from '../ui/Seleccion.jsx'
import './transacciones.css'

// Campo de la API → id del control en la página.
const CAMPOS = {
  tipo: 'tipo',
  intermediario_id: 'intermediario',
  instrumento_id: 'instrumento',
  fecha_concertacion: 'fecha',
  cantidad: 'cantidad',
  precio: 'precio',
  importe_comisiones: 'comisiones',
}

const VACIO = { tipo: 'compra', instrumento: '', intermediario: '', fecha: '', cantidad: '', precio: '', comisiones: '' }

function textoInstrumento(i) {
  const partes = [`${i.clave} · ${i.nombre} (${textoClase(i.clase_activo)})`]
  if (i.vencimiento && !i.nombre?.includes(fecha(i.vencimiento))) partes.push(`vence el ${fecha(i.vencimiento)}`)
  if (i.de_demostracion) partes.push(MENSAJES.demostracion ?? 'Datos de demostración')
  return partes.join(' · ')
}

// El id tal como llegó de la API (entero JSON), sin convertir el texto del <select>.
function idDe(lista, valor) {
  if (valor === '' || !Array.isArray(lista)) return null
  return lista.find((x) => String(x.id) === valor)?.id ?? null
}

function erroresDe(e) {
  if (!e) return { porCampo: {}, resumen: [] }
  if (e.codigo === 'datos_invalidos' && e.errores.length > 0) {
    const porCampo = {}
    const resumen = []
    for (const x of e.errores) {
      const campo = CAMPOS[x.campo] ?? null
      const mensaje = textoParaUsuario(x.mensaje)
      if (campo && !porCampo[campo]) porCampo[campo] = mensaje
      resumen.push({ campo, mensaje })
    }
    return { porCampo, resumen }
  }
  return { porCampo: {}, resumen: [{ campo: null, mensaje: textoParaUsuario(e.mensaje) }] }
}

function DialogoIntermediario({ abierto, alCrear, alCancelar }) {
  const [nombre, setNombre] = useState('')
  const [error, setError] = useState(null)
  const [esperando, setEsperando] = useState(false)

  async function enviar() {
    setEsperando(true)
    setError(null)
    try {
      const nuevo = await crearIntermediario(nombre)
      setNombre('')
      alCrear(nuevo)
    } catch (e) {
      const campo = e.errores?.find((x) => x.campo === 'nombre')
      setError(textoParaUsuario(campo?.mensaje ?? e.mensaje))
    } finally {
      setEsperando(false)
    }
  }

  return (
    <DialogoFormulario
      abierto={abierto}
      titulo="Agregar intermediario"
      textoConfirmar="Agregar"
      esperando={esperando}
      alEnviar={enviar}
      alCancelar={() => {
        setError(null)
        alCancelar()
      }}
    >
      <Campo
        id="nombre-intermediario"
        etiqueta="Nombre del intermediario"
        ayuda="Se guarda tal como lo escribas."
        autoComplete="off"
        value={nombre}
        error={error}
        onChange={(e) => setNombre(e.target.value)}
      />
    </DialogoFormulario>
  )
}

export default function V07RegistrarTransaccion() {
  const { params } = useRuta()
  const idRuta = params.id
  const portafolio = useConsulta(() => verPortafolio(idRuta), [idRuta])
  const portafolios = useConsulta(() => listarPortafolios(), [])
  const instrumentos = useConsulta(() => listarInstrumentos(), [])
  const intermediarios = useConsulta(() => listarIntermediarios(), [])
  const intervalo = useConsulta(() => verIntervalo(), [])

  const [valores, setValores] = useState(VACIO)
  const [portafolioElegido, setPortafolioElegido] = useState(idRuta ?? '')
  const [rechazo, setRechazo] = useState(null)
  const [esperando, setEsperando] = useState(false)
  const [dialogo, setDialogo] = useState(false)
  const [aviso, setAviso] = useState('')
  // Memorizado: ResumenError toma el foco cada vez que recibe una lista nueva.
  const { porCampo, resumen } = useMemo(() => erroresDe(rechazo), [rechazo])

  if (portafolio.error && esPortafolioInexistente(portafolio.error)) {
    return (
      <Plantilla titulo={MENSAJES.registrarTransaccion ?? 'Registrar transacción'} pantalla="V-07" listo>
        <NoEncontrado mensaje={MENSAJES.portafolioInexistente} />
      </Plantilla>
    )
  }

  const cambiar = (campo) => (e) => setValores((v) => ({ ...v, [campo]: e.target.value }))
  const listaInstrumentos = instrumentos.datos ?? []
  const listaIntermediarios = intermediarios.datos ?? []
  const listaPortafolios = portafolios.datos ?? []
  const instrumentoElegido = listaInstrumentos.find((i) => String(i.id) === valores.instrumento)
  const errorCarga = portafolio.error ?? instrumentos.error ?? intermediarios.error ?? portafolios.error
  const listo =
    !portafolio.cargando && !instrumentos.cargando && !intermediarios.cargando && !portafolios.cargando && !intervalo.cargando
  const ayudaFecha = intervalo.datos ? AYUDAS.entreFechas?.(intervalo.datos.inicio, intervalo.datos.fin) : undefined

  async function enviar(e) {
    e.preventDefault()
    if (esperando) return
    setEsperando(true)
    setRechazo(null)
    setAviso('')
    const destino = idDe(listaPortafolios, portafolioElegido) ?? idRuta
    const cuerpo = {
      intermediario_id: idDe(listaIntermediarios, valores.intermediario),
      instrumento_id: idDe(listaInstrumentos, valores.instrumento),
      tipo: valores.tipo,
      fecha_concertacion: valores.fecha,
      cantidad: valores.cantidad.trim(),
      precio: valores.precio.trim(),
      importe_comisiones: valores.comisiones.trim(),
    }
    try {
      await registrarTransaccion(destino, cuerpo)
      navegar(`/portafolios/${destino}/transacciones`, {
        estado: { mensaje: MENSAJES.transaccionRegistrada ?? 'Transacción registrada' },
      })
    } catch (err) {
      setRechazo(err)
      setEsperando(false)
    }
  }

  return (
    <Plantilla titulo={MENSAJES.registrarTransaccion ?? 'Registrar transacción'} pantalla="V-07" listo={listo}>
      <p className="transacciones__volver">
        <Enlace a={`/portafolios/${idRuta}/transacciones`}>Volver a Transacciones</Enlace>
      </p>
      <MensajeEstado tipo="exito">{aviso}</MensajeEstado>
      {errorCarga && <MensajeEstado tipo="error">{textoParaUsuario(errorCarga.mensaje)}</MensajeEstado>}
      <ResumenError errores={resumen} titulo="No se registró la transacción. Corrige lo siguiente y vuelve a enviarla:" />
      <form className="formulario-transaccion" onSubmit={enviar} noValidate aria-busy={esperando ? 'true' : undefined}>
        <div className="formulario-transaccion__rejilla">
          <Select
            id="portafolio"
            etiqueta="Portafolio"
            value={portafolioElegido}
            onChange={(e) => setPortafolioElegido(e.target.value)}
            opciones={
              listaPortafolios.length > 0
                ? listaPortafolios.map((p) => ({ valor: String(p.id), texto: p.nombre }))
                : portafolio.datos
                  ? [{ valor: String(portafolio.datos.id), texto: portafolio.datos.nombre }]
                  : []
            }
          />
          <Select
            id="tipo"
            etiqueta="Tipo"
            value={valores.tipo}
            onChange={cambiar('tipo')}
            error={porCampo.tipo}
            opciones={[
              { valor: 'compra', texto: 'Compra' },
              { valor: 'venta', texto: 'Venta' },
            ]}
          />
          <div className="formulario-transaccion__ancho">
            <Select
              id="instrumento"
              etiqueta="Instrumento"
              ayuda="Del catálogo; los CETES muestran su vencimiento."
              value={valores.instrumento}
              onChange={cambiar('instrumento')}
              error={porCampo.instrumento}
              marcador="Elige un instrumento"
              opciones={listaInstrumentos.map((i) => ({ valor: String(i.id), texto: textoInstrumento(i) }))}
            />
            {instrumentoElegido?.de_demostracion && (
              <p className="formulario-transaccion__demo">
                <EtiquetaDemo />
              </p>
            )}
          </div>
          <div className="formulario-transaccion__ancho formulario-transaccion__intermediario">
            <Select
              id="intermediario"
              etiqueta="Intermediario"
              value={valores.intermediario}
              onChange={cambiar('intermediario')}
              error={porCampo.intermediario}
              marcador={listaIntermediarios.length === 0 ? 'Agrega un intermediario' : 'Elige un intermediario'}
              opciones={listaIntermediarios.map((i) => ({ valor: String(i.id), texto: i.nombre }))}
            />
            <Boton variante="secundario" data-recorrido="agregar-intermediario" onClick={() => setDialogo(true)}>
              Agregar intermediario
            </Boton>
          </div>
          <CampoFecha
            id="fecha"
            etiqueta="Fecha de concertación"
            ayuda={ayudaFecha}
            valorIso={valores.fecha}
            alCambiar={(v) => setValores((x) => ({ ...x, fecha: v }))}
            error={porCampo.fecha}
          />
          <Campo
            id="cantidad"
            etiqueta="Títulos"
            ayuda={AYUDAS.cantidad}
            inputMode="numeric"
            autoComplete="off"
            value={valores.cantidad}
            onChange={cambiar('cantidad')}
            error={porCampo.cantidad}
          />
          <Campo
            id="precio"
            etiqueta="Precio por título (MXN)"
            ayuda={AYUDAS.precio}
            inputMode="decimal"
            autoComplete="off"
            value={valores.precio}
            onChange={cambiar('precio')}
            error={porCampo.precio}
          />
          <Campo
            id="comisiones"
            etiqueta="Importe de comisiones con IVA (MXN)"
            ayuda={AYUDAS.comisiones}
            inputMode="decimal"
            autoComplete="off"
            value={valores.comisiones}
            onChange={cambiar('comisiones')}
            error={porCampo.comisiones}
          />
        </div>
        <div className="formulario-transaccion__acciones">
          <Boton type="submit" variante="primario" data-recorrido="registrar" esperando={esperando} textoEspera="Registrando…">
            {MENSAJES.registrarTransaccion ?? 'Registrar transacción'}
          </Boton>
        </div>
      </form>
      <DialogoIntermediario
        abierto={dialogo}
        alCancelar={() => setDialogo(false)}
        alCrear={(nuevo) => {
          setDialogo(false)
          setValores((v) => ({ ...v, intermediario: String(nuevo.id) }))
          setAviso(MENSAJES.intermediarioAgregado ?? 'Se agregó el intermediario.')
          intermediarios.recargar()
        }}
      />
    </Plantilla>
  )
}
