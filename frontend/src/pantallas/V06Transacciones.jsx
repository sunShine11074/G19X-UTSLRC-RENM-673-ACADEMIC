// V-06 Transacciones (P-C; 4.5.2; CU-06; RF-05 consulta; RF-12 crit. 4; RF-07 crit. 3; RF-02).
// Lista las transacciones del portafolio tal como se capturaron, en el orden de E17 (fecha de
// concertación y luego id), con su costo o ingreso por título calculado por el motor.
// Las cifras se muestran con formato.js, sin convertirlas (RNF-02). Sin momento de registro (H-7).
// El selector N-16 quedó en el nivel 1 de recorte (solo en V-04).
// Una Card del sistema «Proyecto 077 UI» con el portafolio y «+ Registrar transacción» en su encabezado.
import { faPlus } from '@fortawesome/free-solid-svg-icons'
import { esPortafolioInexistente } from '../api/cliente.js'
import { listarTransacciones, verPortafolio } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { fecha, pesos, textoTipo, titulos } from '../formato/formato.js'
import { navegar, useRuta } from '../rutas/navegacion.js'
import { MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { AvisosPermanentes } from '../ui/Avisos.jsx'
import { Boton } from '../ui/Boton.jsx'
import { EtiquetaDemo } from '../ui/EtiquetaDemo.jsx'
import { MensajeEstado } from '../ui/Mensajes.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { PortafolioInexistente } from '../ui/PortafolioInexistente.jsx'
import { Tabla } from '../ui/Tabla.jsx'
import './transacciones.css'

const COLUMNAS = [
  { clave: 'fecha', encabezado: 'Concertación', fecha: true },
  { clave: 'tipo', encabezado: 'Tipo' },
  { clave: 'instrumento', encabezado: 'Instrumento' },
  { clave: 'intermediario', encabezado: 'Intermediario' },
  { clave: 'cantidad', encabezado: 'Títulos', cifra: true },
  { clave: 'precio', encabezado: 'Precio por título', cifra: true },
  { clave: 'comisiones', encabezado: 'Comisiones con IVA', cifra: true },
  { clave: 'porTitulo', encabezado: 'Costo o ingreso por título', cifra: true },
]

function filaDe(t) {
  return {
    id: t.id,
    fecha: fecha(t.fecha_concertacion),
    tipo: textoTipo(t.tipo),
    instrumento: (
      <>
        <span className="transacciones__clave">{t.instrumento?.clave}</span>
        <span className="transacciones__nombre">{t.instrumento?.nombre}</span>
      </>
    ),
    intermediario: t.intermediario?.nombre,
    cantidad: titulos(t.cantidad),
    precio: pesos(t.precio),
    comisiones: pesos(t.importe_comisiones),
    // En compras, el costo por título; en ventas, el ingreso por título (RF-05 crit. 1).
    porTitulo: pesos(t.costo_por_titulo ?? t.ingreso_por_titulo),
  }
}

export default function V06Transacciones() {
  const { params, estado } = useRuta()
  const id = params.id
  const portafolio = useConsulta(() => verPortafolio(id), [id])
  const lista = useConsulta(() => listarTransacciones(id), [id])

  // N-08: el portafolio ajeno o inexistente muestra V-12 en la misma ruta y deja de ser el activo.
  if (esPortafolioInexistente(portafolio.error)) return <PortafolioInexistente />

  const error = portafolio.error ?? lista.error
  const listo = !portafolio.cargando && !lista.cargando
  const transacciones = lista.datos ?? []
  const hayDemo = transacciones.some((t) => t.instrumento?.de_demostracion)
  const nombre = portafolio.datos?.nombre

  return (
    <Plantilla titulo="Transacciones" pantalla="V-06" listo={listo && !error}>
      <MensajeEstado tipo="exito">{estado?.mensaje ?? ''}</MensajeEstado>
      <AvisosPermanentes />
      <div className="p77-card">
        <div className="transacciones__barra p77-card__header">
          {nombre && (
            <p className="transacciones__portafolio">
              Portafolio: <strong>{nombre}</strong>
            </p>
          )}
          <Boton
            variante="primario"
            chico
            icono={faPlus}
            data-recorrido="registrar-transaccion"
            onClick={() => navegar(`/portafolios/${id}/transacciones/nueva`)}
          >
            {MENSAJES.registrarTransaccion ?? 'Registrar transacción'}
          </Boton>
        </div>
        {error && <MensajeEstado tipo="error">{textoParaUsuario(error.mensaje)}</MensajeEstado>}
        {!listo && !error && <p role="status">{MENSAJES.consultando ?? 'Consultando…'}</p>}
        {listo && !error && (
          <p className="transacciones__nota">
            Tal como se capturaron, en pesos mexicanos (MXN). En las compras, la última columna es el costo por título, con
            las comisiones incluidas; en las ventas, el ingreso por título.
          </p>
        )}
        {listo && !error && (
          <div className="transacciones__tabla">
            <Tabla
              titulo={
                <>
                  {nombre ? `Transacciones de «${nombre}»` : 'Transacciones'}
                  {hayDemo && (
                    <>
                      {' '}
                      <EtiquetaDemo />
                    </>
                  )}
                </>
              }
              columnas={COLUMNAS}
              filas={transacciones.map(filaDe)}
              vacio="Este portafolio no tiene transacciones."
            />
          </div>
        )}
      </div>
    </Plantilla>
  )
}
