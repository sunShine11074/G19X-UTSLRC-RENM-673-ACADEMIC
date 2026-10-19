// V-10 Catálogo (P-B; SRS 4.5.2: CU-08; RF-04 crit. 1 a 3; E08). Solo lectura (RD-09).
// Clave, nombre y clase de activo de cada instrumento, en el orden de la API (por clave);
// vencimiento y valor nominal de los CETES, y la marca de demostración en los demás.
// Las cifras y fechas se forman con formato.js, sin convertirlas (RNF-02).
import { listarInstrumentos } from '../api/operaciones.js'
import { useConsulta } from '../api/useConsulta.js'
import { fecha, pesos, textoClase } from '../formato/formato.js'
import { MENSAJES, textoParaUsuario } from '../textos/textos.js'
import { EtiquetaDemo } from '../ui/EtiquetaDemo.jsx'
import { MensajeEstado } from '../ui/Mensajes.jsx'
import { Plantilla } from '../ui/Plantilla.jsx'
import { Tabla } from '../ui/Tabla.jsx'
import './catalogos.css'

const COLUMNAS = [
  { clave: 'clave', encabezado: 'Clave' },
  { clave: 'nombre', encabezado: 'Nombre' },
  { clave: 'clase', encabezado: 'Clase de activo' },
  { clave: 'vencimiento', encabezado: 'Vencimiento' },
  { clave: 'nominal', encabezado: 'Valor nominal (MXN)', cifra: true },
]

function SinDato() {
  return (
    <>
      <span aria-hidden="true">—</span>
      <span className="solo-lector">No aplica</span>
    </>
  )
}

export default function V10Catalogo() {
  const { datos, error, cargando } = useConsulta(() => listarInstrumentos(), [])

  const filas = (datos ?? []).map((i) => ({
    id: i.id,
    clave: i.clave,
    nombre: (
      <>
        {i.nombre}
        {i.de_demostracion && (
          <>
            {' '}
            <EtiquetaDemo />
          </>
        )}
      </>
    ),
    clase: textoClase(i.clase_activo),
    vencimiento: i.vencimiento ? fecha(i.vencimiento) : <SinDato />,
    nominal: i.valor_nominal ? pesos(i.valor_nominal) : <SinDato />,
  }))

  return (
    <Plantilla titulo="Catálogo de instrumentos" pantalla="V-10" listo={!cargando}>
      <div className="catalogos">
        <p className="catalogos-intro">
          Estos son los instrumentos con los que puedes registrar transacciones. El catálogo es de solo lectura.
        </p>
        <p className="catalogos-intro">
          Cada emisión de CETES es un instrumento propio, con su vencimiento y su valor nominal. Los instrumentos
          marcados con <EtiquetaDemo /> tienen una clave ficticia y precios sintéticos, que no son precios reales.
        </p>

        {error && !cargando ? (
          <MensajeEstado tipo="error">{textoParaUsuario(error.mensaje)}</MensajeEstado>
        ) : cargando && !datos ? (
          <p className="catalogos-cargando">{MENSAJES.consultando}</p>
        ) : (
          <Tabla
            titulo="Instrumentos disponibles, por clave"
            columnas={COLUMNAS}
            filas={filas}
            vacio="No hay instrumentos en el catálogo."
          />
        )}
      </div>
    </Plantilla>
  )
}
