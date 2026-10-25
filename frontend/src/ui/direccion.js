// Dirección de una variación para la Delta (sistema «Proyecto 077 UI»), solo con el texto de la API
// (RNF-02: nada se convierte a número).
// - direccion(cifra): con «-», 'baja'; solo ceros ('0', '0.00', '-0.00'), 'igual'; si no, 'sube'.
// - conSigno(texto, cifra): agrega «+» al texto ya formado de lo que sube; el «-» ya viene de
//   formato.js (RD-16).

export function direccion(cifra) {
  const texto = String(cifra ?? '').trim()
  if (/^[+-]?0*(\.0*)?$/.test(texto)) return 'igual'
  return texto.startsWith('-') ? 'baja' : 'sube'
}

export function conSigno(texto, cifra) {
  if (typeof texto !== 'string' || direccion(cifra) !== 'sube' || texto.startsWith('+')) return texto
  return `+${texto}`
}
