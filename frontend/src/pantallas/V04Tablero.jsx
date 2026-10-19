// V-04 Tablero (B5 / P-D; 4.5.2; CU-07): selector de portafolio y periodo, los cuatro
// indicadores con su unidad y su fecha o periodo (RF-11 crit. 1; RNF-07), la gráfica con su
// tabla (RF-11 crit. 2), la procedencia (RF-31), la etiqueta de demostración (RF-07 crit. 3),
// los avisos (RF-12 crit. 4) y, sin transacciones, el estado sin datos (RF-11 crit. 3).
// Las cifras se muestran tal como llegan de E20, solo con formato.js (RNF-02; RD-16).
import { useEffect, useState } from 'react'
import { esPortafolioInexistente } from '../api/cliente.js'
import { verIntervalo, verTablero } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { Procedencia } from '../componentes/Procedencia.jsx'
import { fecha, pesos, porCiento, titulos } from '../formato/formato.js'
import { GraficaValor } from '../graficas/GraficaValor.jsx'
import { navegar, useRuta } from '../rutas/navegacion.js'
import { useSesion } from '../sesion/useSesion.js'
import { AYUDAS, MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { AvisosPermanentes, LineaFuente } from '../ui/Avisos.jsx'
import { Boton } from '../ui/Boton.jsx'
import { CampoFecha } from '../ui/Campo.jsx'
import { EtiquetaDemo } from '../ui/EtiquetaDemo.jsx'
import { EstadoSinDatos, MensajeEstado } from '../ui/Mensajes.jsx'
import { NoEncontrado } from '../ui/NoEncontrado.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { SelectorPortafolio } from '../ui/SelectorPortafolio.jsx'
import { TarjetaIndicador } from '../ui/TarjetaIndicador.jsx'
import './V04Tablero.css'

const ISO = /^\d{4}-\d{2}-\d{2}$/
const ERRORES_PERIODO = ['periodo_invertido', 'periodo_fuera_de_intervalo']
const FECHA_INVALIDA = 'Escribe una fecha válida con el formato DD/MM/AAAA.'

const soloIso = (v) => (typeof v === 'string' && ISO.test(v) ? v : undefined)

// Motivo del rechazo de E20 junto a las fechas (N-17), por campo.
function erroresDeFechas(error) {
  if (!error) return { inicio: null, fin: null, general: null }
  if (ERRORES_PERIODO.includes(error.codigo)) {
    return { inicio: null, fin: textoParaUsuario(error.mensaje), general: null }
  }
  if (error.codigo === 'datos_invalidos') {
    const de = (campo) => error.errores?.find((e) => e.campo === campo)?.mensaje
    const inicio = de('inicio')
    const fin = de('fin')
    if (inicio || fin) {
      return {
        inicio: inicio ? textoParaUsuario(inicio) : null,
        fin: fin ? textoParaUsuario(fin) : null,
        general: null,
      }
    }
  }
  return { inicio: null, fin: null, general: textoParaUsuario(error.mensaje) }
}

function Indicadores({ datos }) {
  const ind = datos.indicadores
  const caida = ind.maxima_caida
  return (
    <section className="v04-bloque" aria-labelledby="v04-indicadores">
      <div className="v04-encabezado-bloque">
        <h2 id="v04-indicadores">Indicadores del periodo</h2>
        {datos.contiene_datos_de_demostracion && <EtiquetaDemo />}
      </div>
      <div className="v04-tarjetas">
        <TarjetaValor titulo="Valor de mercado" importe={ind.valor_mercado} recorrido="tarjeta-valor" />
        <TarjetaValor titulo="Resultado no realizado" importe={ind.resultado_no_realizado} />
        <TarjetaPorCiento
          titulo="Rendimiento ponderado por tiempo (TWR)"
          indicador={ind.twr}
          unidad={MENSAJES.sinAnualizar}
        />
        <TarjetaPorCiento titulo="Máxima caída" indicador={caida}>
          <p className="tarjeta-fecha">
            {caida.fecha_pico && caida.fecha_valle
              ? MENSAJES.picoValle(caida.fecha_pico, caida.fecha_valle)
              : MENSAJES.sinCaidas}
          </p>
        </TarjetaPorCiento>
      </div>
    </section>
  )
}

// Importe al corte: cifra, unidad (la divisa base) y «Al DD/MM/AAAA». TarjetaIndicador (B3)
// pone data-recorrido en el elemento de la cifra.
function TarjetaValor({ titulo, importe, recorrido }) {
  return (
    <TarjetaIndicador
      titulo={titulo}
      valor={pesos(importe.valor)}
      unidad={importe.unidad}
      fecha={MENSAJES.alCorte(importe.fecha_corte)}
      data-recorrido={recorrido}
    />
  )
}

// Por ciento del periodo: «4.39 %» y «Del DD/MM/AAAA al DD/MM/AAAA».
function TarjetaPorCiento({ titulo, indicador, unidad, children }) {
  return (
    <TarjetaIndicador
      titulo={titulo}
      valor={porCiento(indicador.valor)}
      unidad={unidad}
      fecha={MENSAJES.periodo(indicador.inicio, indicador.fin)}
    >
      {children}
    </TarjetaIndicador>
  )
}

function ProcedenciaTablero({ datos }) {
  if (datos.procedencia.length === 0 && datos.fuentes_del_periodo.length === 0) return null
  // La etiqueta de demostración de cada valuación la pone Procedencia junto a su cifra.
  return (
    <section className="v04-bloque" aria-labelledby="v04-procedencia">
      <div className="v04-encabezado-bloque">
        <h2 id="v04-procedencia">Procedencia de las valuaciones al {fecha(datos.fecha_corte)}</h2>
      </div>
      {datos.procedencia.length > 0 && (
        <ul className="v04-procedencia">
          {datos.procedencia.map((p) => (
            <li key={p.instrumento.id}>
              <p className="v04-instrumento">
                <span className="v04-clave">{p.instrumento.clave}</span> · {p.instrumento.nombre} ·{' '}
                <span className="cifra">{titulos(p.titulos)}</span> {p.titulos === '1' ? 'título' : 'títulos'}
              </p>
              <Procedencia valuacion={p.valuacion} deDemostracion={p.instrumento.de_demostracion} />
            </li>
          ))}
        </ul>
      )}
      {datos.fuentes_del_periodo.length > 0 && (
        <div className="v04-fuentes">
          <h3>Fuentes de los datos del periodo</h3>
          {datos.fuentes_del_periodo.map((f) => (
            <LineaFuente key={`${f.nombre}-${f.fecha_carga}`} fuente={f} />
          ))}
        </div>
      )}
    </section>
  )
}

export default function V04Tablero() {
  const { params, consulta } = useRuta()
  const id = params.id
  const inicioQ = soloIso(consulta?.inicio)
  const finQ = soloIso(consulta?.fin)
  const clave = `${id}|${inicioQ ?? ''}|${finQ ?? ''}`

  // La primera consulta va sin fechas si la ruta no las trae (la API pone el periodo por omisión).
  const tablero = useConsulta(() => verTablero(id, { inicio: inicioQ, fin: finQ }), [id, inicioQ, finQ])
  const intervalo = useConsulta(() => verIntervalo(), [])

  // Lo que se escribe en el formulario vale solo para la ruta en que se escribió.
  const [edicion, setEdicion] = useState({ clave: null })
  const editado = edicion.clave === clave ? edicion : { clave }
  const fijar = (cambio) => setEdicion({ ...editado, ...cambio, clave })

  const datos = tablero.datos
  const error = tablero.error
  const porOmision = intervalo.datos?.por_omision

  // N-08: si el portafolio no existe (o es ajeno), deja de ser el activo.
  const { fijarPortafolioActivo } = useSesion()
  const inexistente = esPortafolioInexistente(error)
  useEffect(() => {
    if (inexistente) fijarPortafolioActivo?.(null)
  }, [inexistente, fijarPortafolioActivo])

  if (inexistente) {
    // N-08: V-12 en la misma ruta, con el mismo texto para lo ajeno y lo inexistente (RNF-03).
    return (
      <Plantilla titulo="No encontrado" pantalla="V-12" listo>
        <NoEncontrado mensaje={MENSAJES.portafolioInexistente} />
      </Plantilla>
    )
  }

  const valorInicio = editado.inicio ?? inicioQ ?? datos?.periodo?.inicio ?? porOmision?.inicio ?? ''
  const valorFin = editado.fin ?? finQ ?? datos?.periodo?.fin ?? porOmision?.fin ?? ''
  const idElegido = editado.portafolio ?? id
  const ayuda = porOmision ? AYUDAS.entreFechas(porOmision.inicio, porOmision.fin) : undefined

  const deApi = error && error.estado !== 401 ? erroresDeFechas(error) : { inicio: null, fin: null, general: null }
  const errorInicio = editado.errorInicio ?? deApi.inicio
  const errorFin = editado.errorFin ?? deApi.fin

  function consultar(e) {
    e.preventDefault()
    const errInicio = ISO.test(valorInicio) ? null : FECHA_INVALIDA
    const errFin = ISO.test(valorFin) ? null : FECHA_INVALIDA
    if (errInicio || errFin) {
      fijar({ errorInicio: errInicio, errorFin: errFin })
      return
    }
    fijar({ errorInicio: undefined, errorFin: undefined })
    const mismo = String(idElegido) === String(id)
    if (mismo && valorInicio === inicioQ && valorFin === finQ) {
      tablero.recargar()
      return
    }
    // N-17: «Consultar» reemplaza la entrada del historial (nivel 1 de recorte); N-16 abre el
    // tablero del otro portafolio con el mismo periodo.
    navegar(`/portafolios/${idElegido}/tablero?inicio=${valorInicio}&fin=${valorFin}`, { reemplazar: mismo })
  }

  const listo = !tablero.cargando && (!!datos || !!error)
  const conCifras = datos && !error

  return (
    <Plantilla titulo="Tablero" pantalla="V-04" listo={listo}>
      <form className="v04-consulta" onSubmit={consultar} noValidate aria-label="Portafolio y periodo">
        <SelectorPortafolio idActual={idElegido} alCambiar={(nuevo) => fijar({ portafolio: nuevo })} />
        <CampoFecha
          id="fecha-inicio"
          etiqueta="Inicio del periodo"
          valorIso={valorInicio}
          alCambiar={(v) => fijar({ inicio: v, errorInicio: undefined })}
          ayuda={ayuda}
          error={errorInicio}
          claseContenedor="v04-campo-fecha"
        />
        <CampoFecha
          id="fecha-fin"
          etiqueta="Fin del periodo y fecha de corte"
          valorIso={valorFin}
          alCambiar={(v) => fijar({ fin: v, errorFin: undefined })}
          ayuda={ayuda}
          error={errorFin}
          claseContenedor="v04-campo-fecha"
        />
        <div className="v04-accion">
          <Boton
            type="submit"
            variante="primario"
            esperando={tablero.cargando}
            textoEspera={MENSAJES.consultando}
            data-recorrido="consultar"
          >
            {MENSAJES.consultar}
          </Boton>
        </div>
      </form>

      {/* Resultado de la consulta para el lector de pantalla (4.1.3), sin duplicarlo en pantalla. */}
      <MensajeEstado>
        {tablero.cargando ? (
          MENSAJES.consultando
        ) : errorInicio || errorFin ? (
          <span className="solo-lector">{[errorInicio, errorFin].filter(Boolean).join(' ')}</span>
        ) : (
          ''
        )}
      </MensajeEstado>
      {deApi.general && <MensajeEstado tipo="error">{deApi.general}</MensajeEstado>}

      <AvisosPermanentes />

      {conCifras && (
        <p className="v04-resumen">
          {datos.portafolio.nombre} · {MENSAJES.periodo(datos.periodo.inicio, datos.periodo.fin)} · Corte:{' '}
          {fecha(datos.fecha_corte)}
        </p>
      )}

      {conCifras && datos.sin_datos && <EstadoSinDatos fechaCorte={datos.fecha_corte} idPortafolio={datos.portafolio.id} />}

      {conCifras && !datos.sin_datos && datos.indicadores && (
        <>
          <Indicadores datos={datos} />
          <div className="v04-bloque">
            <GraficaValor
              serie={datos.serie}
              fechaCorte={datos.fecha_corte}
              valorAlCorte={datos.valor_al_corte}
              nombrePortafolio={datos.portafolio.nombre}
              periodo={datos.periodo}
              deDemostracion={datos.contiene_datos_de_demostracion}
            />
          </div>
          <ProcedenciaTablero datos={datos} />
        </>
      )}
    </Plantilla>
  )
}
