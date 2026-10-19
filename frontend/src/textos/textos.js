// Textos fijos de la interfaz (SRS 4.5.1 y 4.5.2; decisiones H-6 y H-8 del 18/10/2026).
// Español de México, trato de tú. Este archivo no importa nada, para que lo use cualquier módulo.
//
// Las funciones de MENSAJES y AYUDAS reciben fechas ya formateadas (DD/MM/AAAA) o en AAAA-MM-DD;
// si llegan en AAAA-MM-DD, las reordenan como texto, igual que fecha() de formato.js.

function ddmmaaaa(texto) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto ?? '')
  return m ? `${m[3]}/${m[2]}/${m[1]}` : (texto ?? '')
}

const AVISO_ASESORIA = 'La información de este sistema no constituye asesoría de inversión.'
const AVISO_VALUACIONES =
  'Las valuaciones son estimaciones informativas, no precios oficiales, y no sustituyen el estado de cuenta de tu intermediario.'

/**
 * Avisos permanentes (RF-12 crit. 4; R-11): van antes de las cifras del tablero, las posiciones y
 * las transacciones. Es la lista de los dos textos, en orden, y también se leen por nombre.
 */
export const AVISOS = Object.freeze(
  Object.assign([AVISO_ASESORIA, AVISO_VALUACIONES], {
    titulo: 'Avisos',
    asesoria: AVISO_ASESORIA,
    valuaciones: AVISO_VALUACIONES,
  }),
)

/** Texto de la casilla de consentimiento (RF-12 crit. 1; P-63). Se muestra sin marcar. */
export const CASILLA_CONSENTIMIENTO =
  'Doy mi consentimiento para el tratamiento de mis datos personales, financieros y patrimoniales conforme al aviso de privacidad.'

/** Mensajes de estado y de resultado (N-04 a N-15 de 4.5.2) y textos de las vistas de consulta. */
export const MENSAJES = Object.freeze({
  // Navegación y sesión
  cuentaCreada: 'Tu cuenta quedó creada. Inicia sesión.', // N-04
  sesionCerrada: 'Cerraste tu sesión.', // N-06
  sesionTerminada: 'Inicia sesión para continuar.', // N-07
  portafolioInexistente: 'No existe el portafolio.', // N-08
  paginaInexistente: 'No existe esta página.', // V-12
  irAPortafolios: 'Ir a Portafolios',
  irAInicioSesion: 'Ir a Inicio de sesión',
  consentimientoRevocado: 'Revocaste tu consentimiento; tu cuenta quedó bloqueada.', // N-09
  revocarExplicacion:
    'Tu cuenta se bloqueará de inmediato y ya no podrás iniciar sesión. Mientras dure el bloqueo, tu correo no podrá registrarse de nuevo.', // N-09
  revocarConfirmar: 'Revocar mi consentimiento',

  // Portafolios, intermediarios y transacciones
  portafolioCreado: 'Se creó el portafolio.', // N-10
  portafolioRenombrado: 'Se cambió el nombre del portafolio.', // N-11
  portafolioEliminado: 'Se eliminaron el portafolio y sus transacciones; tus intermediarios se conservan.', // N-12
  eliminarConfirmar: 'Eliminar portafolio',
  escribeNombreParaConfirmar: 'Escribe el nombre del portafolio para confirmar.', // N-12
  intermediarioAgregado: 'Se agregó el intermediario.', // N-15
  transaccionRegistrada: 'Transacción registrada', // N-14
  registrarTransaccion: 'Registrar transacción',

  // Estados
  consultando: 'Consultando…',
  guardando: 'Guardando…',
  sinConexion: 'No se pudo conectar con el servidor. Intenta de nuevo.',
  cancelar: 'Cancelar',
  cerrar: 'Cerrar',
  consultar: 'Consultar',

  // Consultas (V-04 y V-05)
  sinDatos: (fechaCorte) => `Este portafolio no tiene transacciones hasta el ${ddmmaaaa(fechaCorte)}.`, // RF-11 crit. 3
  sinCaidas: 'No hubo caídas en el periodo',
  picoValle: (pico, valle) => `Del pico del ${ddmmaaaa(pico)} al valle del ${ddmmaaaa(valle)}`,
  periodo: (inicio, fin) => `Del ${ddmmaaaa(inicio)} al ${ddmmaaaa(fin)}`,
  alCorte: (fechaCorte) => `Al ${ddmmaaaa(fechaCorte)}`,
  sinAnualizar: 'sin anualizar',
  vencida: (vencimiento) => `Vencida el ${ddmmaaaa(vencimiento)}; liquidada a su valor nominal`, // RF-26a
  sinTitulos: 'Sin títulos al corte',
  estimado: 'estimado', // RF-26b; R-11
  demostracion: 'Datos de demostración', // RF-07 crit. 3
})

/** Ayudas visibles bajo los campos (4.5.1, «Componentes»; H-8). */
export const AYUDAS = Object.freeze({
  contrasena: 'Al menos 15 caracteres',
  fecha: 'DD/MM/AAAA',
  cantidad: 'Número entero',
  precio: 'Hasta 7 decimales, con punto decimal y sin comas',
  comisiones: 'Hasta 2 decimales; puede ser 0',
  entreFechas: (inicio, fin) => `Entre el ${ddmmaaaa(inicio)} y el ${ddmmaaaa(fin)}`,
})

/**
 * Mensajes técnicos de la API que se sustituyen en el cliente (P-85, opción A; H-8). La clave es el
 * mensaje exacto que envía la API (en el sobre o en `errores[].mensaje`); el valor, el texto que se
 * muestra. Lo que no está aquí se muestra tal como llega. Usa textoParaUsuario().
 */
export const MENSAJES_TECNICOS = Object.freeze({
  'Escribe una fecha válida con el formato AAAA-MM-DD.': 'Escribe una fecha válida con el formato DD/MM/AAAA.',
  'Escribe una cifra sin signo, separadores ni exponente.': 'Escribe la cifra solo con dígitos y, si hace falta, un punto decimal; sin comas ni signos.',
  'Envía esta cifra como texto, por ejemplo "50.00".': 'Escribe la cifra con punto decimal, por ejemplo 50.00.',
  'Identificador inválido.': 'Elige una opción de la lista.',
  'Dato inválido.': 'Revisa este dato.',
  'Este dato no se puede enviar.': 'No se pudo enviar el formulario. Intenta de nuevo.',
  'El cuerpo no es JSON válido.': 'No se pudo enviar el formulario. Intenta de nuevo.',
  'El cuerpo debe ser un objeto JSON.': 'No se pudo enviar el formulario. Intenta de nuevo.',
  'Debe ser true o false.': 'Marca o desmarca la casilla.',
  'Origen no permitido.': 'No se pudo completar la solicitud. Abre la aplicación desde su dirección habitual e intenta de nuevo.',
  'No existe el recurso.': 'No existe esta página.',
  'Ocurrió un error inesperado.': 'Ocurrió un error inesperado. Intenta de nuevo más tarde.',
})

/** El mensaje que se muestra para un mensaje de la API: su sustituto, si es técnico, o el mismo. */
export function textoParaUsuario(mensaje) {
  if (typeof mensaje !== 'string') return MENSAJES.sinConexion
  return Object.hasOwn(MENSAJES_TECNICOS, mensaje) ? MENSAJES_TECNICOS[mensaje] : mensaje
}

/** Textos de los valores fijos que envía la API (4.5.1, «Textos de los valores fijos»). Los usa formato.js. */
export const VALORES_FIJOS = Object.freeze({
  clase: Object.freeze({ accion: 'Acción', etf: 'ETF', fibra: 'FIBRA', cetes: 'CETES' }),
  tipo: Object.freeze({ compra: 'Compra', venta: 'Venta' }),
  caso: Object.freeze({
    nodo: 'tasa de un solo plazo',
    'interpolación': 'calculada entre dos plazos',
    'extremo inferior': 'tasa del plazo más corto',
    'extremo superior': 'tasa del plazo más largo',
  }),
  estado: Object.freeze({ activa: 'Activa', bloqueada: 'Bloqueada' }),
  consentimiento: Object.freeze({ otorgamiento: 'Otorgado', revocacion: 'Revocado', web: 'sitio web' }),
})
