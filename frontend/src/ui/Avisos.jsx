// Avisos, avisos permanentes y línea de fuente (B3; SRS 4.5.1, «Componentes»; RF-12 crit. 4;
// RF-31 crit. 2 y 3; H-6). Contrato del Anexo A: Aviso({tipo}), AvisosPermanentes() y
// LineaFuente({fuente}).
import { AVISOS } from '../textos/textos.js'
import './datos.css'

// Textos de 4.5.1 por si textos.js aún no los tiene; rige textos.js.
const AVISOS_4_5_1 = [
  'La información de este sistema no constituye asesoría de inversión.',
  'Las valuaciones son estimaciones informativas, no precios oficiales, y no sustituyen el estado de cuenta de tu intermediario.',
]

function textoDe(valor) {
  if (typeof valor === 'string') return valor
  if (valor && typeof valor === 'object' && typeof valor.texto === 'string') return valor.texto
  return null
}

function avisosPermanentes() {
  const fuente = AVISOS ?? {}
  let lista
  if (Array.isArray(fuente)) lista = fuente
  else if (Array.isArray(fuente.permanentes)) lista = fuente.permanentes
  else if (fuente.asesoria || fuente.valuaciones) lista = [fuente.asesoria, fuente.valuaciones]
  else lista = Object.values(fuente)
  const textos = lista.map(textoDe).filter(Boolean)
  return textos.length > 0 ? textos : AVISOS_4_5_1
}

// Iconos decorativos de 16 px; toman el color de su variante (4.5.1, «Iconografía»).
function Icono({ tipo }) {
  const comun = {
    className: 'aviso-icono',
    viewBox: '0 0 16 16',
    width: 16,
    height: 16,
    'aria-hidden': true,
    focusable: 'false',
  }
  if (tipo === 'advertencia') {
    return (
      <svg {...comun}>
        <path d="M8 1.5 15 14.5H1z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
        <path d="M8 6v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="8" cy="12.25" r="0.9" fill="currentColor" />
      </svg>
    )
  }
  if (tipo === 'error') {
    return (
      <svg {...comun}>
        <circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M5.5 5.5l5 5m0-5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    )
  }
  if (tipo === 'exito') {
    return (
      <svg {...comun}>
        <circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path d="M5 8.25l2 2 4-4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    )
  }
  return (
    <svg {...comun}>
      <circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 7v4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="8" cy="4.75" r="0.9" fill="currentColor" />
    </svg>
  )
}

const TITULOS = { info: 'Información', advertencia: 'Advertencia', error: 'Error', exito: 'Listo' }

/**
 * Aviso estático: tipo 'info' (por omisión), 'advertencia', 'error' o 'exito'.
 * `titulo` es opcional; sin él, el tipo se nombra solo para el lector de pantalla.
 * Es estático (sin región viva); para anunciar un resultado se usa MensajeEstado.
 */
export function Aviso({ tipo = 'info', titulo, children, ...resto }) {
  return (
    <div className={`aviso aviso--${tipo}`} {...resto}>
      <Icono tipo={tipo} />
      <div className="aviso-cuerpo">
        {titulo ? (
          <p className="aviso-titulo">{titulo}</p>
        ) : (
          <span className="solo-lector">{TITULOS[tipo] ?? TITULOS.info}: </span>
        )}
        {children}
      </div>
    </div>
  )
}

/** Los dos avisos de 4.5.1 (RF-12 crit. 4), estáticos y antes de las cifras. */
export function AvisosPermanentes() {
  const textos = avisosPermanentes()
  return (
    <section className="avisos-permanentes" aria-label="Avisos">
      <Aviso tipo="info">
        {textos.map((t) => (
          <p key={t}>{t}</p>
        ))}
      </Aviso>
    </section>
  )
}

function ConEnlace({ texto, direccion }) {
  const i = direccion ? texto.indexOf(direccion) : -1
  if (i === -1) return texto
  return (
    <>
      {texto.slice(0, i)}
      <a href={direccion} target="_blank" rel="noopener noreferrer">
        {direccion}
      </a>
      {texto.slice(i + direccion.length)}
    </>
  )
}

/**
 * Línea de fuente (RF-31 crit. 2 y 3). `fuente` es la FuenteVista de la API
 * ({nombre, direccion, de_demostracion, atribucion, fecha_carga}) o un texto ya formado.
 * Con atribución, la muestra tal como llega («Fuente: Banco de México, https://www.banxico.org.mx»)
 * y convierte la dirección en enlace subrayado cuyo texto es la dirección (2.4.4).
 */
export function LineaFuente({ fuente, children }) {
  if (!fuente) return null
  if (typeof fuente === 'string') {
    return (
      <p className="linea-fuente">
        {fuente}
        {children}
      </p>
    )
  }
  const { nombre, direccion, atribucion } = fuente
  const texto = atribucion || (direccion ? `Fuente: ${nombre}, ${direccion}` : `Fuente: ${nombre}`)
  return (
    <p className="linea-fuente">
      <ConEnlace texto={texto} direccion={direccion} />
      {children}
    </p>
  )
}
