// V-05 Posiciones al corte (P-E; SRS 4.5.2; CU-06).
// RF-06; RF-08; RF-26a; RF-26b; RF-30; RF-31 crit. 2 y 3; RF-07 crit. 3; RF-12 crit. 4; RNF-02.
// Ruta: /portafolios/:id/posiciones?fecha_corte=AAAA-MM-DD. Operaciones: E09 y E19.
// - Sin fecha en la ruta, la API usa su corte por omisión (el fin del intervalo de datos).
// - «Consultar» reemplaza la entrada del historial (N-17; nivel 1 de recorte).
// - El selector de portafolio (N-16) queda solo en V-04 (nivel 1 de recorte).
// - Toda cifra es el texto de la API con formato.js: nada se suma ni se redondea (RNF-02). El
//   total sale de `totales`, nunca de sumar filas, y usa el mismo pesos() que V-04.
import { useState } from 'react'
import { esPortafolioInexistente } from '../api/cliente.js'
import { verIntervalo, verPosiciones } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { Procedencia } from '../componentes/Procedencia.jsx'
import { aIso, fecha, pesos, textoClase, titulos } from '../formato/formato.js'
import { conConsulta, navegar, useRuta } from '../rutas/navegacion.js'
import { AYUDAS, MENSAJES, MENSAJES_TECNICOS, textoParaUsuario } from '../textos/textos.js'
import { AvisosPermanentes } from '../ui/Avisos.jsx'
import { Boton } from '../ui/Boton.jsx'
import { CampoFecha } from '../ui/Campo.jsx'
import { EtiquetaDemo } from '../ui/EtiquetaDemo.jsx'
import { MensajeEstado } from '../ui/Mensajes.jsx'
import { NoEncontrado } from '../ui/NoEncontrado.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { Tabla } from '../ui/Tabla.jsx'
import './V05Posiciones.css'

const TITULO = 'Posiciones'
const PATRON_ISO = /^\d{4}-\d{2}-\d{2}$/
const FECHA_INVALIDA = MENSAJES_TECNICOS['Escribe una fecha válida con el formato AAAA-MM-DD.']
// Rechazos de E19 que se muestran junto a la fecha de corte (N-17).
const CODIGOS_DE_FECHA = new Set(['fecha_fuera_de_intervalo', 'datos_invalidos'])

const COLUMNAS = [
  { clave: 'instrumento', encabezado: 'Instrumento' },
  { clave: 'titulos', encabezado: 'Títulos', cifra: true },
  { clave: 'costo', encabezado: 'Costo (MXN)', cifra: true },
  { clave: 'valor', encabezado: 'Valor de mercado (MXN)', cifra: true },
  { clave: 'resultado', encabezado: 'Resultado no realizado (MXN)', cifra: true },
]

function errorDeFecha(error) {
  if (!error || error.estado !== 422 || !CODIGOS_DE_FECHA.has(error.codigo)) return null
  if (error.codigo === 'datos_invalidos') {
    const delCampo = error.errores.find((e) => e.campo === 'fecha_corte') ?? error.errores[0]
    return textoParaUsuario(delCampo?.mensaje ?? error.mensaje)
  }
  return textoParaUsuario(error.mensaje)
}

function CeldaInstrumento({ p }) {
  const i = p.instrumento
  let nota = null
  if (p.vencida) nota = MENSAJES.vencida(i.vencimiento)
  else if (p.titulos === '0') nota = MENSAJES.sinTitulos
  // La clase solo se agrega si el nombre no la dice ya («CETES con vencimiento…»).
  const clase = textoClase(i.clase_activo)
  const nombre = i.nombre.toLowerCase().includes(clase.toLowerCase()) ? i.nombre : `${i.nombre} · ${clase}`
  return (
    <span className="v05-instrumento">
      <span className="v05-instrumento__clave">{i.clave}</span>
      <span className="v05-instrumento__nombre">{nombre}</span>
      {nota && (
        <span className="v05-instrumento__nota">{nota}</span>
      )}
    </span>
  )
}

function CeldaValor({ p }) {
  const estimado = p.valuacion?.tipo === 'estimacion_cetes'
  return (
    <>
      {estimado && (
        <>
          <span className="v05-estimado">{MENSAJES.estimado}</span>{' '}
        </>
      )}
      <span className="cifra">{pesos(p.valor)}</span>
    </>
  )
}

function filaDe(p) {
  return {
    id: p.instrumento.id,
    instrumento: <CeldaInstrumento p={p} />,
    titulos: titulos(p.titulos),
    costo: pesos(p.costo_total),
    valor: <CeldaValor p={p} />,
    resultado: pesos(p.resultado_no_realizado),
  }
}

function TablaPosiciones({ datos }) {
  const pie = {
    id: 'total',
    instrumento: 'Total',
    titulos: '',
    costo: pesos(datos.totales.costo_total),
    valor: (
      <span className="cifra" data-recorrido="total-valor">
        {pesos(datos.totales.valor)}
      </span>
    ),
    resultado: pesos(datos.totales.resultado_no_realizado),
  }
  const titulo = (
    <>
      Posiciones al {fecha(datos.fecha_corte)}
      {datos.contiene_datos_de_demostracion && (
        <>
          {' '}
          <EtiquetaDemo />
        </>
      )}
    </>
  )
  return (
    <Tabla
      titulo={titulo}
      columnas={COLUMNAS}
      filas={datos.posiciones.map(filaDe)}
      pie={pie}
      vacio={`Este portafolio no tiene transacciones hasta el ${fecha(datos.fecha_corte)}.`}
      idFila={(f) => f.id}
    />
  )
}

function Procedencias({ posiciones }) {
  const conValuacion = posiciones.filter((p) => p.valuacion)
  if (conValuacion.length === 0) return null
  return (
    <section className="v05-procedencias" aria-labelledby="v05-procedencias-titulo">
      <h2 id="v05-procedencias-titulo">Valuación y fuente de cada posición</h2>
      <ul className="v05-procedencias__lista">
        {conValuacion.map((p) => (
          <li key={p.instrumento.id} className="v05-procedencias__elemento">
            <h3 className="v05-procedencias__instrumento">
              {p.instrumento.clave} · {p.instrumento.nombre}
            </h3>
            <Procedencia
              valuacion={p.valuacion}
              deDemostracion={p.valuacion.fuente?.de_demostracion === true || p.de_demostracion === true}
            />
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function V05Posiciones() {
  const { params, consulta } = useRuta()
  const id = params.id
  const fechaRuta = consulta.fecha_corte
  const fechaRutaValida = fechaRuta === undefined || PATRON_ISO.test(fechaRuta)
  const claveRuta = `${id}|${fechaRuta ?? ''}`

  const intervalo = useConsulta(() => verIntervalo(), [])
  const posiciones = useConsulta(
    () => (fechaRutaValida ? verPosiciones(id, fechaRuta) : Promise.resolve(null)),
    [id, fechaRuta ?? ''],
  )

  // Lo escrito en la fecha y el error local se olvidan al cambiar la ruta (Atrás, Adelante, menú).
  const [edicion, setEdicion] = useState({ clave: null, valor: null, error: null })
  const propia = edicion.clave === claveRuta
  const datos = posiciones.datos
  const valorCampo = propia && edicion.valor !== null ? edicion.valor : (fechaRuta ?? datos?.fecha_corte ?? '')

  if (esPortafolioInexistente(posiciones.error)) {
    return (
      <Plantilla titulo={TITULO} pantalla="V-05" listo>
        <NoEncontrado mensaje={MENSAJES.portafolioInexistente} />
      </Plantilla>
    )
  }

  const errorFecha =
    (propia ? edicion.error : null) ?? (fechaRutaValida ? errorDeFecha(posiciones.error) : FECHA_INVALIDA)
  const errorGeneral = posiciones.error && !errorDeFecha(posiciones.error) ? textoParaUsuario(posiciones.error.mensaje) : null
  const mostrarCifras = Boolean(datos) && !errorFecha
  const listo = !posiciones.cargando && !intervalo.cargando
  const rango = intervalo.datos ? AYUDAS.entreFechas(intervalo.datos.inicio, intervalo.datos.fin) : undefined

  function alCambiar(valor) {
    setEdicion({ clave: claveRuta, valor, error: null })
  }

  function consultar(e) {
    e.preventDefault()
    const iso = aIso(valorCampo)
    if (!iso) {
      setEdicion({ clave: claveRuta, valor: valorCampo, error: FECHA_INVALIDA })
      return
    }
    if (iso === fechaRuta) {
      setEdicion({ clave: claveRuta, valor: null, error: null })
      posiciones.recargar()
      return
    }
    navegar(conConsulta(`/portafolios/${id}/posiciones`, { fecha_corte: iso }), { reemplazar: true })
  }

  return (
    <Plantilla titulo={TITULO} pantalla="V-05" listo={listo}>
      {mostrarCifras && (
        <p className="v05-encabezado">
          {datos.portafolio.nombre} · Corte: {fecha(datos.fecha_corte)}
        </p>
      )}

      <AvisosPermanentes />

      <form className="v05-consulta" onSubmit={consultar} noValidate>
        <CampoFecha
          id="fecha-corte"
          etiqueta="Fecha de corte"
          valorIso={valorCampo}
          alCambiar={alCambiar}
          ayuda={rango}
          error={errorFecha ?? undefined}
        />
        <Boton
          type="submit"
          variante="primario"
          esperando={posiciones.cargando}
          textoEspera={MENSAJES.consultando}
          data-recorrido="consultar"
        >
          {MENSAJES.consultar}
        </Boton>
      </form>

      <MensajeEstado tipo={errorGeneral ? 'error' : undefined}>
        {posiciones.cargando ? MENSAJES.consultando : (errorGeneral ?? '')}
      </MensajeEstado>

      {mostrarCifras && (
        <>
          <TablaPosiciones datos={datos} />
          <Procedencias posiciones={datos.posiciones} />
        </>
      )}
    </Plantilla>
  )
}
