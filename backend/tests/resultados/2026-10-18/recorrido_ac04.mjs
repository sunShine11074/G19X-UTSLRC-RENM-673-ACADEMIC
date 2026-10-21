#!/usr/bin/env node
// Recorrido de AC-04 (SRS 3.9.2): captura fechada de cada requisito imprescindible en el cliente web,
// con los datos de 5.2, en el equipo de desarrollo. Plan del 18/10/2026, sección F4.
//
// Requisitos: Node 24 (WebSocket y fetch globales; sin dependencias) y Microsoft Edge. Abre Edge sin
// interfaz con un perfil temporal y lo controla por el protocolo de DevTools (CDP). Localiza cada
// pantalla y cada control solo por su atributo data-recorrido (Anexo A del plan), espera a
// main[data-listo] antes de capturar y toma las capturas a 1280 × 720.
//
// Uso, desde la raíz del repositorio (pide la contraseña de la cuenta sin mostrarla):
//
//   node backend/tests/resultados/2026-10-18/recorrido_ac04.mjs --base http://localhost:5173 --correo oraculo@example.com --salida backend/tests/resultados/2026-10-18/ac04
//
// Opciones:
//   --base URL            Cliente web (por omisión, http://localhost:5173). Sin barra final.
//   --correo CORREO       Cuenta con 5.2 cargado (por omisión, oraculo@example.com).
//   --salida CARPETA      Dónde quedan las capturas y recorrido.csv (por omisión, la carpeta ac04 junto a este guion).
//   --clave-archivo RUTA  Solo para el ensayo en el entorno temporal: lee la contraseña de ese archivo.
//   --pasos 1,2,10        Solo esos pasos (para repetir los que fallaron). Por omisión, todos.
//   --edge RUTA           msedge.exe, si no está en su lugar habitual.
//   --puerto N            Puerto de DevTools (por omisión, 9223).
//
// Pasos, en el orden del plan (T4: nada que cambie las cifras de 5.2 antes de capturarlas):
//   1. V-04 de «Principal» (RF-07 a RF-11, RF-12 crit. 4, RF-26b, RF-30, RF-31) y las capturas de RNF-02.
//   2. V-05 al 14/10 (RF-06, RF-07, RF-08, RF-12 crit. 4, RF-26a, RF-26b, RF-30, RF-31).
//   3. RNF-02, consulta repetida: recarga V-04 y V-05 y compara las cadenas con las de los pasos 1 y 2.
//   4. V-06 de «Principal» (RF-05, consulta).
//   5. V-07 con la venta N1 de rechazos_rf28.csv, que la API rechaza (RF-28 crit. 3).
//   6. V-10 (RF-04).  7. V-09 (RF-25, consulta).
//   8. V-08: alta y cambio de nombre de «Recorrido AC-04 (desechable)», una compra válida en él (RF-05,
//      registro), Cancelar en el diálogo de eliminar y la eliminación confirmada (RF-03).
//   9. V-11 de la cuenta (RF-12 crit. 1), sin revocar.
//  10. En un contexto aislado, la cuenta B (recorrido-b-HHMM@example.com, clave aleatoria en memoria):
//      aviso sin sesión, registro sin y con consentimiento, inicio de sesión fallido y correcto,
//      «Casa A», portafolio ajeno e inexistente (RF-02 crit. 2; RNF-03) y revocación (RF-12 crit. 3).
//
// Si un paso falla, anota «falló» en recorrido.csv, guarda una captura de diagnóstico y sigue con el
// siguiente. recorrido.csv no lleva contraseñas ni rutas de usuario; si ya existe, se le agregan filas.
// Termina con código 0 si todo salió bien, 1 si algún paso falló y 2 si las opciones no son válidas.

import { spawn, spawnSync } from 'node:child_process'
import crypto from 'node:crypto'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { setTimeout as dormir } from 'node:timers/promises'

const CARPETA_GUION = path.dirname(fileURLToPath(import.meta.url))
const ANCHO = 1280
const ALTO = 720
const ESPERA_PANTALLA = 20000
const ALTO_MAXIMO_CAPTURA = 6000

// Datos de 5.2 (tests/oraculo): solo para anotar en el detalle si lo que se ve coincide.
const VALOR_5_2 = '$58,940.88' // «Principal» al 14/10/2026
const N1 = { tipo: 'venta', instrumento: 'DEMOACC', intermediario: 'Casa B', fecha: '2026-09-18', cantidad: '150', precio: '98.50', comisiones: '42.85' }
const COMPRA_VALIDA = { tipo: 'compra', instrumento: 'DEMOACC', intermediario: 'Casa A', fecha: '2026-10-01', cantidad: '10', precio: '105.35', comisiones: '3.05' }
const NOMBRE_DESECHABLE = 'Recorrido AC-04 (desechable)'
const ID_INEXISTENTE = '999999'

// ---------------------------------------------------------------------------------------------
// Opciones
// ---------------------------------------------------------------------------------------------

function leerOpciones(argumentos) {
  const op = {
    base: 'http://localhost:5173',
    correo: 'oraculo@example.com',
    salida: path.join(CARPETA_GUION, 'ac04'),
    claveArchivo: null,
    pasos: null,
    edge: null,
    puerto: 9223,
  }
  const conValor = { '--base': 'base', '--correo': 'correo', '--salida': 'salida', '--clave-archivo': 'claveArchivo', '--pasos': 'pasos', '--edge': 'edge', '--puerto': 'puerto' }
  for (let i = 0; i < argumentos.length; i++) {
    let nombre = argumentos[i]
    let valor
    const igual = nombre.indexOf('=')
    if (nombre.startsWith('--') && igual > 0) {
      valor = nombre.slice(igual + 1)
      nombre = nombre.slice(0, igual)
    }
    if (nombre === '--ayuda' || nombre === '-h' || nombre === '--help') {
      op.ayuda = true
      continue
    }
    const clave = conValor[nombre]
    if (!clave) throw new ErrorUso(`Opción desconocida: ${nombre}`)
    if (valor === undefined) {
      valor = argumentos[++i]
      if (valor === undefined || valor.startsWith('--')) throw new ErrorUso(`Falta el valor de ${nombre}`)
    }
    op[clave] = valor
  }
  op.base = op.base.replace(/\/+$/, '')
  if (!/^https?:\/\/[^/]+$/.test(op.base)) throw new ErrorUso('--base debe ser como http://localhost:5173, sin ruta ni barra final.')
  if (!/^[^@\s]+@[^@\s]+$/.test(op.correo)) throw new ErrorUso('--correo no parece un correo.')
  op.puerto = Number.parseInt(String(op.puerto), 10)
  if (!(op.puerto > 1024 && op.puerto < 65536)) throw new ErrorUso('--puerto debe estar entre 1025 y 65535.')
  if (op.pasos) {
    const lista = String(op.pasos).split(',').map((s) => Number.parseInt(s.trim(), 10))
    if (lista.some((n) => !(n >= 1 && n <= 10))) throw new ErrorUso('--pasos admite números del 1 al 10 separados por comas.')
    op.pasos = new Set(lista)
  }
  op.salida = path.resolve(op.salida)
  return op
}

class ErrorUso extends Error {}

// ---------------------------------------------------------------------------------------------
// Contraseña sin mostrarla
// ---------------------------------------------------------------------------------------------

function pedirClave(pregunta) {
  const entrada = process.stdin
  process.stderr.write(pregunta)
  if (!entrada.isTTY) {
    return new Promise((resolver, rechazar) => {
      let datos = ''
      entrada.setEncoding('utf8')
      const alDato = (trozo) => {
        datos += trozo
        const fin = datos.indexOf('\n')
        if (fin >= 0) {
          entrada.off('data', alDato)
          entrada.pause()
          process.stderr.write('\n')
          resolver(datos.slice(0, fin).replace(/\r$/, ''))
        }
      }
      entrada.on('data', alDato)
      entrada.once('end', () => resolver(datos.replace(/\r?\n$/, '')))
      entrada.once('error', rechazar)
    })
  }
  return new Promise((resolver, rechazar) => {
    let clave = ''
    const terminar = () => {
      entrada.off('data', alDato)
      entrada.setRawMode(false)
      entrada.pause()
      process.stderr.write('\n')
    }
    const alDato = (texto) => {
      for (const c of texto) {
        if (c === '\r' || c === '\n') {
          terminar()
          resolver(clave)
          return
        }
        if (c === '\u0003') {
          terminar()
          rechazar(new ErrorUso('Cancelado.'))
          return
        }
        if (c === '\u007f' || c === '\b') {
          clave = Array.from(clave).slice(0, -1).join('')
          continue
        }
        if (c < ' ') continue
        clave += c
      }
    }
    entrada.setRawMode(true)
    entrada.setEncoding('utf8')
    entrada.resume()
    entrada.on('data', alDato)
  })
}

// ---------------------------------------------------------------------------------------------
// Edge y CDP
// ---------------------------------------------------------------------------------------------

function rutaEdge(indicada) {
  const candidatos = [
    indicada,
    process.env['ProgramFiles(x86)'] && path.join(process.env['ProgramFiles(x86)'], 'Microsoft/Edge/Application/msedge.exe'),
    process.env.ProgramFiles && path.join(process.env.ProgramFiles, 'Microsoft/Edge/Application/msedge.exe'),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Microsoft/Edge/Application/msedge.exe'),
  ].filter(Boolean)
  const encontrada = candidatos.find((r) => fs.existsSync(r))
  if (!encontrada) throw new ErrorUso('No se encontró msedge.exe; indícalo con --edge.')
  return encontrada
}

async function pedirJson(url, espera = 1000) {
  const control = new AbortController()
  const reloj = setTimeout(() => control.abort(), espera)
  try {
    const r = await fetch(url, { signal: control.signal })
    return r.ok ? await r.json() : null
  } catch {
    return null
  } finally {
    clearTimeout(reloj)
  }
}

async function abrirEdge(op) {
  const urlVersion = `http://127.0.0.1:${op.puerto}/json/version`
  if (await pedirJson(urlVersion)) {
    throw new ErrorUso(`El puerto ${op.puerto} ya tiene un navegador con DevTools; ciérralo o usa --puerto.`)
  }
  const perfil = fs.mkdtempSync(path.join(os.tmpdir(), 'p077-recorrido-'))
  const proceso = spawn(
    rutaEdge(op.edge),
    [
      '--headless=new',
      `--remote-debugging-port=${op.puerto}`,
      `--user-data-dir=${perfil}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-extensions',
      '--disable-sync',
      '--disable-background-networking',
      '--disable-component-update',
      '--disable-features=msEdgeSidebarV2,msUndersideButton,Translate',
      '--hide-scrollbars',
      '--force-color-profile=srgb',
      '--lang=es-MX',
      `--window-size=${ANCHO},${ALTO}`,
      'about:blank',
    ],
    { stdio: 'ignore', windowsHide: true },
  )
  const limite = Date.now() + 20000
  let version = null
  while (!version && Date.now() < limite) {
    await dormir(250)
    version = await pedirJson(urlVersion)
  }
  if (!version?.webSocketDebuggerUrl) {
    await cerrarEdge({ proceso, perfil })
    throw new Error('Edge no abrió DevTools en 20 s.')
  }
  const salio = new Promise((resolver) => proceso.once('exit', resolver))
  return { proceso, perfil, salio, ws: version.webSocketDebuggerUrl }
}

// Cierra Edge (primero con Browser.close; si no, lo termina) y borra el perfil temporal.
async function cerrarEdge({ proceso, perfil, salio }, cdp) {
  if (proceso && proceso.exitCode === null) {
    if (cdp) await cdp.enviar('Browser.close', {}, undefined, 3000).catch(() => {})
    await Promise.race([salio ?? Promise.resolve(), dormir(4000)])
    if (proceso.exitCode === null) {
      if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(proceso.pid), '/T', '/F'], { stdio: 'ignore' })
      else proceso.kill('SIGKILL')
      await Promise.race([salio ?? Promise.resolve(), dormir(4000)])
    }
  }
  cdp?.cerrar()
  if (perfil) {
    for (let intento = 0; intento < 20 && fs.existsSync(perfil); intento++) {
      try {
        fs.rmSync(perfil, { recursive: true, force: true })
      } catch {
        await dormir(250) // Edge todavía suelta archivos del perfil
      }
    }
    if (fs.existsSync(perfil)) console.error(`Aviso: no se pudo borrar el perfil temporal de Edge (${path.basename(perfil)} en la carpeta temporal).`)
  }
}

class Cdp {
  static conectar(url) {
    return new Promise((resolver, rechazar) => {
      const ws = new WebSocket(url)
      ws.onopen = () => resolver(new Cdp(ws))
      ws.onerror = () => rechazar(new Error('No se pudo conectar con Edge por DevTools.'))
    })
  }

  constructor(ws) {
    this.ws = ws
    this.siguiente = 1
    this.pendientes = new Map()
    ws.onmessage = (evento) => {
      const m = JSON.parse(typeof evento.data === 'string' ? evento.data : Buffer.from(evento.data).toString('utf8'))
      if (!m.id) return
      const p = this.pendientes.get(m.id)
      if (!p) return
      this.pendientes.delete(m.id)
      clearTimeout(p.reloj)
      if (m.error) p.rechazar(new Error(`${p.metodo}: ${m.error.message}`))
      else p.resolver(m.result)
    }
    ws.onclose = () => {
      for (const p of this.pendientes.values()) p.rechazar(new Error('Se cerró la conexión con Edge.'))
      this.pendientes.clear()
    }
  }

  enviar(metodo, params = {}, sessionId, espera = 30000) {
    const id = this.siguiente++
    const mensaje = { id, method: metodo, params }
    if (sessionId) mensaje.sessionId = sessionId
    return new Promise((resolver, rechazar) => {
      const reloj = setTimeout(() => {
        this.pendientes.delete(id)
        rechazar(new Error(`${metodo}: sin respuesta en ${espera / 1000} s`))
      }, espera)
      this.pendientes.set(id, { resolver, rechazar, reloj, metodo })
      this.ws.send(JSON.stringify(mensaje))
    })
  }

  cerrar() {
    try {
      this.ws.close()
    } catch {
      // ya estaba cerrada
    }
  }
}

// Funciones que se ejecutan dentro de la página. Solo buscan por data-recorrido (Anexo A); el id
// es un respaldo que se anota como aviso, porque Campo y Seleccion copian el id en data-recorrido.
const AYUDAS = String.raw`
const visible = (el) => !!el && el.isConnected && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
const sel = (clave) => '[data-recorrido="' + String(clave).replace(/["\\]/g, '\\$&') + '"]';
const dialogoAbierto = () => [...document.querySelectorAll('dialog[open]')].filter(visible).pop() || null;
const aviso = (texto) => { window.__avisosRecorrido = (window.__avisosRecorrido || []); if (!window.__avisosRecorrido.includes(texto)) window.__avisosRecorrido.push(texto); };
const normal = (s) => String(s ?? '').replace(/\s+/g, ' ').trim();
const minus = (s) => normal(s).toLowerCase();
const textoDe = (el) => normal(el ? (el.innerText ?? el.textContent) : '');
const abrirDetalles = (el) => { for (let p = el && el.parentElement; p; p = p.parentElement) if (p.tagName === 'DETAILS' && !p.open) p.open = true; };
const buscar = (clave, opciones = {}) => {
  const dlg = dialogoAbierto();
  let todos = [...document.querySelectorAll(sel(clave))];
  if (opciones.incluirOcultos) { todos.forEach(abrirDetalles); }
  todos = todos.filter(visible);
  if (dlg) { const dentro = todos.filter((e) => dlg.contains(e)); if (dentro.length || opciones.enDialogo) todos = dentro; }
  if (opciones.fila) {
    const f = minus(opciones.fila);
    todos = todos.filter((e) => {
      for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
        if (p.querySelectorAll(sel(clave)).length > 1) return false;
        if (minus(p.innerText).includes(f)) return true;
      }
      return false;
    });
  }
  if (todos.length) return todos[0];
  if (!opciones.fila) {
    const porId = document.getElementById(clave);
    if (porId && visible(porId) && (!dlg || dlg.contains(porId))) { aviso('sin data-recorrido: ' + clave); return porId; }
  }
  return null;
};
const control = (clave, opciones) => {
  const el = buscar(clave, opciones);
  if (!el) return null;
  if (el.matches('input,select,textarea,button')) return el;
  return el.querySelector('input,select,textarea') || el;
};
const exigir = (el, clave) => { if (!el) throw new Error('No se encontró ' + sel(clave) + ' visible'); return el; };
const fijarValor = (el, valor) => {
  const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, valor);
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
};
const hayError = () => {
  const r = document.querySelector(sel('resumen-error'));
  if (r && visible(r) && textoDe(r)) return textoDe(r);
  const alerta = [...document.querySelectorAll('[role="alert"]')].find((e) => visible(e) && textoDe(e));
  if (alerta) return textoDe(alerta);
  const invalido = [...document.querySelectorAll('[aria-invalid="true"]')].find(visible);
  if (invalido) {
    const ids = (invalido.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
    const textos = ids.map((i) => textoDe(document.getElementById(i))).filter(Boolean);
    return textos.join(' · ') || 'campo marcado como inválido';
  }
  return '';
};
`

class Pagina {
  static async abrir(cdp, base, contextoId) {
    const { targetId } = await cdp.enviar('Target.createTarget', { url: 'about:blank', ...(contextoId ? { browserContextId: contextoId } : {}) })
    const { sessionId } = await cdp.enviar('Target.attachToTarget', { targetId, flatten: true })
    const p = new Pagina(cdp, sessionId, targetId, base)
    await p.enviar('Page.enable')
    await p.enviar('Runtime.enable')
    await p.enviar('Emulation.setDeviceMetricsOverride', { width: ANCHO, height: ALTO, deviceScaleFactor: 1, mobile: false })
    await p.enviar('Emulation.setEmulatedMedia', {
      media: 'screen',
      features: [
        { name: 'prefers-color-scheme', value: 'light' },
        { name: 'prefers-reduced-motion', value: 'reduce' },
      ],
    })
    return p
  }

  constructor(cdp, sessionId, targetId, base) {
    Object.assign(this, { cdp, sessionId, targetId, base })
  }

  enviar(metodo, params, espera) {
    return this.cdp.enviar(metodo, params, this.sessionId, espera)
  }

  // Ejecuta fn(...args) en la página, con AYUDAS a la mano. fn no puede usar variables de Node.
  async llamar(fn, ...args) {
    const expresion = `(async () => { ${AYUDAS}; return await (${fn.toString()})(...${JSON.stringify(args)}); })()`
    const r = await this.enviar('Runtime.evaluate', { expression: expresion, awaitPromise: true, returnByValue: true, userGesture: true })
    if (r.exceptionDetails) {
      const d = r.exceptionDetails.exception?.description || r.exceptionDetails.text || 'error'
      throw new Error(String(d).split('\n')[0].replace(/^Error: /, ''))
    }
    return r.result?.value
  }

  // Carga la ruta en un documento nuevo (equivale a recargar) y espera a que el anterior se vaya,
  // para no leer la pantalla vieja.
  async ir(ruta) {
    await this.llamar(() => {
      window.__marcaRecorrido = true
    }).catch(() => {})
    const r = await this.enviar('Page.navigate', { url: this.base + ruta })
    if (r.errorText) throw new Error(`No se pudo abrir ${ruta}: ${r.errorText}`)
    await this.esperar(() => !window.__marcaRecorrido && document.readyState !== 'loading', `la carga de ${ruta}`, 15000)
  }

  // condicion() devuelve algo verdadero para terminar, o {falla: 'motivo'} para fallar de inmediato.
  async esperar(condicion, descripcion, espera = ESPERA_PANTALLA, ...args) {
    const limite = Date.now() + espera
    let ultimo
    while (Date.now() < limite) {
      try {
        ultimo = await this.llamar(condicion, ...args)
      } catch {
        ultimo = null // La página puede estar navegando; se reintenta.
      }
      if (ultimo && typeof ultimo === 'object' && 'falla' in ultimo) throw new Error(String(ultimo.falla))
      if (ultimo) return ultimo
      await dormir(150)
    }
    const diagnostico = await this.diagnostico().catch(() => '')
    throw new Error(`No apareció ${descripcion} en ${espera / 1000} s${diagnostico ? ` (${diagnostico})` : ''}`)
  }

  async diagnostico() {
    return this.llamar(() => {
      const m = document.querySelector('main')
      const error = document.querySelector(sel('error-pantalla'))
      const partes = [`ruta ${location.pathname}`]
      partes.push(m ? `main ${m.getAttribute('data-recorrido') || 'sin data-recorrido'}${m.hasAttribute('data-listo') ? ' listo' : ''}` : 'sin main')
      if (error) partes.push(`error de pantalla: ${textoDe(error).slice(0, 160)}`)
      else if (m) partes.push(`texto: ${textoDe(m).slice(0, 160)}`)
      return partes.join('; ')
    })
  }

  // Espera la pantalla y su data-listo. Si la pantalla llega pero no marca data-listo, captura igual
  // al cabo de la espera y lo devuelve como aviso (lo arregla el dueño de la pantalla).
  async esperarPantalla(id, { espera = ESPERA_PANTALLA, listo = true } = {}) {
    await this.esperar((v) => !!document.querySelector(`main[data-recorrido="${v}"]`), `la pantalla ${id}`, espera, id)
    let avisoListo = ''
    if (listo) {
      try {
        await this.esperar((v) => !!document.querySelector(`main[data-recorrido="${v}"][data-listo]`), `data-listo en ${id}`, espera, id)
      } catch {
        avisoListo = `${id} sin data-listo tras ${espera / 1000} s`
      }
    }
    await this.asentar()
    return avisoListo
  }

  async pantallaActual() {
    return this.llamar(() => document.querySelector('main')?.getAttribute('data-recorrido') || '')
  }

  async asentar() {
    await this.llamar(async () => {
      if (document.fonts?.ready) await document.fonts.ready
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))
    })
    await dormir(300)
  }

  async escribir(clave, valor, opciones = {}) {
    await this.llamar(
      (c, v, o) => {
        const el = exigir(control(c, o), c)
        el.scrollIntoView({ block: 'center' })
        el.focus()
        fijarValor(el, v)
        el.blur()
      },
      clave,
      valor,
      opciones,
    )
  }

  async escribirFecha(clave, iso) {
    await this.llamar(
      (c, v) => {
        const el = exigir(control(c), c)
        const [a, m, d] = v.split('-')
        el.scrollIntoView({ block: 'center' })
        el.focus()
        fijarValor(el, el.type === 'date' ? v : `${d}/${m}/${a}`)
        el.blur()
      },
      clave,
      iso,
    )
  }

  async valor(clave) {
    return this.llamar((c) => control(c)?.value ?? null, clave)
  }

  // Elige en un select (por texto o valor de la opción) o en un grupo de radios (por etiqueta o valor).
  async elegir(clave, texto) {
    return this.llamar(
      (c, t) => {
        const buscado = minus(t)
        let el = exigir(buscar(c), c)
        if (el.tagName !== 'SELECT' && !(el.tagName === 'INPUT' && el.type === 'radio')) el = el.querySelector('select') || el
        if (el.tagName === 'SELECT') {
          const opciones = [...el.options]
          const op =
            opciones.find((o) => minus(o.text) === buscado || minus(o.value) === buscado) ||
            opciones.find((o) => minus(o.text).startsWith(buscado)) ||
            opciones.find((o) => minus(o.text).includes(buscado))
          if (!op) throw new Error(`${sel(c)} no tiene la opción «${t}» (hay: ${opciones.map((o) => normal(o.text)).join(' | ')})`)
          if (el.value !== op.value) {
            el.focus()
            fijarValor(el, op.value)
            el.blur()
          }
          return normal(op.text)
        }
        let radios
        if (el.tagName === 'INPUT') radios = el.name ? [...document.querySelectorAll(`input[type="radio"][name="${el.name}"]`)] : [el]
        else radios = [...el.querySelectorAll('input[type="radio"]')]
        const etiqueta = (r) => minus(r.labels?.[0]?.textContent || r.closest('label')?.textContent || r.value)
        const r = radios.find((x) => etiqueta(x) === buscado || minus(x.value) === buscado) || radios.find((x) => etiqueta(x).includes(buscado))
        if (!r) throw new Error(`${sel(c)} no tiene la opción «${t}»`)
        if (!r.checked) r.click()
        return etiqueta(r)
      },
      clave,
      texto,
    )
  }

  async clic(clave, opciones = {}) {
    return this.llamar(
      (c, o) => {
        const el = exigir(buscar(c, o), c)
        el.scrollIntoView({ block: 'center' })
        el.focus()
        el.click()
        return textoDe(el)
      },
      clave,
      opciones,
    )
  }

  async marcar(clave, marcada) {
    return this.llamar(
      (c, m) => {
        const el = exigir(control(c), c)
        if (el.checked !== m) {
          el.scrollIntoView({ block: 'center' })
          el.click()
        }
        return el.checked
      },
      clave,
      marcada,
    )
  }

  async tecla(nombre, codigo) {
    const base = { key: nombre, code: nombre, windowsVirtualKeyCode: codigo, nativeVirtualKeyCode: codigo }
    await this.enviar('Input.dispatchKeyEvent', { type: 'rawKeyDown', ...base })
    await this.enviar('Input.dispatchKeyEvent', { type: 'keyUp', ...base })
  }

  async texto(clave) {
    return this.llamar((c) => {
      const el = buscar(c, { incluirOcultos: true })
      return el ? textoDe(el) : null
    }, clave)
  }

  async errorActual() {
    return this.llamar(() => hayError())
  }

  // Espera un mensaje de error distinto del que ya estaba (p. ej., el aviso de cuenta creada).
  async esperarErrorNuevo(antes, descripcion, espera = 15000) {
    return this.esperar(
      (previo) => {
        const e = hayError()
        return e && e !== previo ? e : ''
      },
      descripcion,
      espera,
      antes || '',
    )
  }

  async textoMain() {
    return this.llamar(() => textoDe(document.querySelector('main')))
  }

  async avisos() {
    return this.llamar(() => {
      const a = window.__avisosRecorrido || []
      window.__avisosRecorrido = []
      return a
    })
  }

  async rutaActual() {
    return this.llamar(() => location.pathname + location.search)
  }

  // GET de solo lectura a la API, con la sesión de esta página (mismo origen).
  async consultarApi(ruta) {
    return this.llamar(async (r) => {
      const respuesta = await fetch('/api' + r, { credentials: 'same-origin', headers: { Accept: 'application/json' } })
      if (!respuesta.ok) throw new Error(`GET /api${r} respondió ${respuesta.status}`)
      return respuesta.json()
    }, ruta)
  }

  // Captura de la ventana de 1280 × 720. Con `elemento`, la desplaza para centrarlo (abre los
  // <details> que lo contengan); con `completa`, captura la página entera a 1280 de ancho.
  async capturar(archivo, { elemento, completa = false } = {}) {
    if (elemento) {
      const hallado = await this.llamar((c) => {
        const el = buscar(c, { incluirOcultos: true })
        if (!el) return false
        abrirDetalles(el)
        el.scrollIntoView({ block: 'center' })
        return true
      }, elemento)
      if (!hallado) throw new Error(`No se encontró ${'[data-recorrido="' + elemento + '"]'} para capturarlo`)
    } else {
      await this.llamar(() => window.scrollTo(0, 0))
    }
    await this.asentar()
    let params = { format: 'png', fromSurface: true }
    if (completa && !elemento) {
      const metricas = await this.enviar('Page.getLayoutMetrics')
      const alto = Math.ceil((metricas.cssContentSize || metricas.contentSize).height)
      if (alto > ALTO) {
        params = { ...params, captureBeyondViewport: true, clip: { x: 0, y: 0, width: ANCHO, height: Math.min(alto, ALTO_MAXIMO_CAPTURA), scale: 1 } }
      }
    }
    const { data } = await this.enviar('Page.captureScreenshot', params, 60000)
    fs.writeFileSync(archivo, Buffer.from(data, 'base64'))
  }

  async cerrar() {
    await this.cdp.enviar('Target.closeTarget', { targetId: this.targetId }).catch(() => {})
  }
}

// ---------------------------------------------------------------------------------------------
// Registro: recorrido.csv y nombres de archivo
// ---------------------------------------------------------------------------------------------

const dos = (n) => String(n).padStart(2, '0')

function ahora() {
  const d = new Date()
  return {
    fecha: `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`,
    hhmm: `${dos(d.getHours())}${dos(d.getMinutes())}`,
    hora: `${dos(d.getHours())}:${dos(d.getMinutes())}:${dos(d.getSeconds())}`,
  }
}

function campoCsv(valor) {
  const t = String(valor ?? '')
  return /[",\r\n]/.test(t) ? `"${t.replace(/"/g, '""')}"` : t
}

class Registro {
  constructor(carpeta) {
    this.carpeta = carpeta
    this.csv = path.join(carpeta, 'recorrido.csv')
    this.usados = new Set()
    this.fallos = 0
    this.filas = 0
    fs.mkdirSync(carpeta, { recursive: true })
    if (!fs.existsSync(this.csv)) {
      fs.writeFileSync(this.csv, '\uFEFFrequisito,pantalla,archivo,hora,resultado,detalle\r\n', 'utf8')
    }
  }

  // Nombre como RF-11_V-04_2026-10-18_2122.png; con sufijo si hay varias de la misma pantalla.
  nombre(requisito, pantalla, sufijo) {
    const { fecha, hhmm } = ahora()
    const base = [requisito, pantalla || 'sin-pantalla', fecha, hhmm, sufijo].filter(Boolean).join('_')
    let nombre = `${base}.png`
    for (let i = 2; this.usados.has(nombre) || fs.existsSync(path.join(this.carpeta, nombre)); i++) nombre = `${base}_${i}.png`
    this.usados.add(nombre)
    return { nombre, ruta: path.join(this.carpeta, nombre) }
  }

  fila({ requisito, pantalla, archivo, resultado, detalle }) {
    const { hora } = ahora()
    const linea = [requisito, pantalla, archivo, hora, resultado, detalle].map(campoCsv).join(',')
    fs.appendFileSync(this.csv, linea + '\r\n', 'utf8')
    this.filas++
    if (resultado === 'falló' || resultado === 'no coincide') this.fallos++
    const marca = resultado === 'falló' || resultado === 'no coincide' ? '[FALLA]' : '[ok]'
    console.log(`   ${marca} ${requisito} · ${pantalla || '—'} · ${archivo || '—'} · ${resultado}${detalle ? ` · ${detalle}` : ''}`)
  }
}

// ---------------------------------------------------------------------------------------------
// Ejecución de los pasos
// ---------------------------------------------------------------------------------------------

// Un paso agrupa capturas; si algo falla, anota «falló» en los requisitos que no alcanzó a cubrir.
class Paso {
  constructor(ctx, numero, titulo, requisitos, pagina) {
    Object.assign(this, { ctx, numero, titulo, requisitos, pagina })
    this.cubiertos = new Set()
  }

  // Captura y anota una fila por cada requisito que muestra.
  async captura(requisitos, pantalla, opciones = {}) {
    const lista = [].concat(requisitos)
    const principal = lista[0].split(' ')[0]
    const { nombre, ruta } = this.ctx.registro.nombre(principal, pantalla, opciones.sufijo)
    await (opciones.pagina || this.pagina).capturar(ruta, opciones)
    const avisos = await (opciones.pagina || this.pagina).avisos().catch(() => [])
    const detalle = [opciones.detalle, ...avisos].filter(Boolean).join('; ')
    for (const r of lista) {
      this.ctx.registro.fila({ requisito: r, pantalla, archivo: nombre, resultado: opciones.resultado || 'correcto', detalle })
      this.cubiertos.add(r)
    }
    return nombre
  }

  anotar(requisito, pantalla, resultado, detalle, archivo = '') {
    this.ctx.registro.fila({ requisito, pantalla, archivo, resultado, detalle })
    this.cubiertos.add(requisito)
  }

  async fallo(error, pagina = this.pagina) {
    const mensaje = String(error?.message || error).replace(/\s+/g, ' ').slice(0, 400)
    let archivo = ''
    try {
      const pantalla = (await pagina.pantallaActual()) || 'sin-pantalla'
      const { nombre, ruta } = this.ctx.registro.nombre(`fallo-paso-${dos(this.numero)}`, pantalla)
      await pagina.capturar(ruta)
      archivo = nombre
    } catch {
      // sin captura de diagnóstico
    }
    const pendientes = this.requisitos.filter((r) => !this.cubiertos.has(r))
    for (const r of pendientes.length ? pendientes : [`paso ${this.numero}`]) {
      this.ctx.registro.fila({ requisito: r, pantalla: '', archivo, resultado: 'falló', detalle: `Paso ${this.numero}: ${mensaje}` })
    }
  }
}

async function iniciarSesion(pagina, correo, clave) {
  await pagina.ir('/sesion')
  await pagina.esperarPantalla('V-01', { espera: 30000 }) // la primera carga de Vite puede tardar
  await pagina.escribir('correo', correo)
  await pagina.escribir('contrasena', clave)
  const antes = await pagina.errorActual()
  await pagina.clic('entrar')
  let resultado
  try {
    resultado = await pagina.esperar(
      (previo) => {
        const m = document.querySelector('main')?.getAttribute('data-recorrido')
        if (m && m !== 'V-01') return 'dentro'
        const e = hayError()
        return e && e !== previo ? 'error: ' + e : ''
      },
      'el resultado del inicio de sesión',
      20000,
      antes,
    )
  } catch (e) {
    // Si la redirección tras entrar no llega pero la sesión sí quedó abierta (E06: 200), se sigue:
    // cada paso abre su ruta directamente.
    const abierta = await pagina.consultarApi('/cuenta').then(() => true, () => false)
    if (!abierta) throw e
    console.log(`   aviso: la sesión quedó abierta pero la pantalla no cambió (${await pagina.diagnostico().catch(() => '')})`)
    resultado = 'dentro'
  }
  if (resultado !== 'dentro') throw new Error(`No se pudo iniciar sesión (${resultado.slice(0, 160)})`)
}

async function llenarTransaccion(pagina, datos, nombrePortafolio) {
  await pagina.elegir('tipo', datos.tipo)
  if (nombrePortafolio) {
    const hayPortafolio = await pagina.llamar(() => !!control('portafolio'))
    if (hayPortafolio) await pagina.elegir('portafolio', nombrePortafolio)
  }
  await pagina.elegir('instrumento', datos.instrumento)
  await pagina.elegir('intermediario', datos.intermediario)
  await pagina.escribirFecha('fecha', datos.fecha)
  await pagina.escribir('cantidad', datos.cantidad)
  await pagina.escribir('precio', datos.precio)
  await pagina.escribir('comisiones', datos.comisiones)
  await dormir(200)
}

const extraerPesos = (texto) => (String(texto ?? '').replace(/\u00a0/g, ' ').match(/-?\$\s?[\d,]+\.\d{2}/) || [''])[0].replace(/\s/g, '')

async function leerCifrasV04(pagina) {
  return {
    tarjeta: await pagina.texto('tarjeta-valor'),
    corte: await pagina.texto('etiqueta-corte'),
    ultima: await pagina.texto('ultima-fila'),
  }
}

function describirCifras(c) {
  return Object.entries(c)
    .map(([k, v]) => `${k} «${v ?? 'no encontrada'}»`)
    .join(', ')
}

// Abre un formulario cuyo campo puede estar en la pantalla o en un diálogo que abre el botón.
async function enviarConCampo(pagina, campo, valor, boton) {
  const campoVisible = await pagina.llamar((c) => !!control(c), campo)
  if (campoVisible) {
    await pagina.escribir(campo, valor)
    await pagina.clic(boton)
    return
  }
  await pagina.clic(boton)
  await pagina.esperar(() => !!dialogoAbierto(), 'el diálogo', 8000)
  await pagina.escribir(campo, valor, { enDialogo: true })
  const enDialogo = await pagina.llamar((b) => !!buscar(b, { enDialogo: true }), boton)
  await pagina.clic(enDialogo ? boton : 'confirmar', { enDialogo: true })
}

async function escribirEnDialogo(pagina, claves, valor) {
  await pagina.llamar(
    (lista, v) => {
      const dlg = dialogoAbierto()
      if (!dlg) throw new Error('No hay un diálogo abierto')
      let el = null
      for (const c of lista) {
        el = control(c, { enDialogo: true })
        if (el) break
      }
      el = el || [...dlg.querySelectorAll('input[type="text"], input:not([type]), textarea')].find(visible)
      if (!el) throw new Error('El diálogo no tiene un campo de texto')
      el.focus()
      fijarValor(el, v)
    },
    claves,
    valor,
  )
}

async function cerrarDialogo(pagina) {
  await pagina.tecla('Escape', 27)
  try {
    await pagina.esperar(() => !dialogoAbierto(), 'el cierre del diálogo', 3000)
  } catch {
    await pagina.clic('cancelar', { enDialogo: true })
    await pagina.esperar(() => !dialogoAbierto(), 'el cierre del diálogo', 5000)
  }
}

// ---------------------------------------------------------------------------------------------
// Los diez pasos
// ---------------------------------------------------------------------------------------------

async function paso1(ctx, paso) {
  const p = ctx.pagina
  await p.ir(`/portafolios/${ctx.idPrincipal}/tablero`)
  const aviso = await p.esperarPantalla('V-04')
  const cifras = await leerCifrasV04(p)
  ctx.cifras1 = cifras
  const coincide52 = extraerPesos(cifras.tarjeta) === VALOR_5_2 ? `valor al corte igual a 5.2 (${VALOR_5_2})` : `valor al corte distinto de 5.2 (${VALOR_5_2})`
  await paso.captura(['RF-11 crit. 1', 'RF-07 crit. 3', 'RF-08', 'RF-09', 'RF-10', 'RF-12 crit. 4', 'RF-31 crit. 2 y 3', 'RF-26b', 'RF-30'], 'V-04', {
    completa: true,
    detalle: [aviso, 'Principal, periodo por omisión', coincide52].filter(Boolean).join('; '),
  })
  await paso.captura('RF-11 crit. 2', 'V-04', { elemento: 'etiqueta-corte', sufijo: 'grafica', detalle: `etiqueta «${cifras.corte}»` })
  await paso.captura('RNF-02', 'V-04', { elemento: 'tarjeta-valor', sufijo: 'tarjeta', detalle: `tarjeta «${cifras.tarjeta}»` })
  await paso.captura('RNF-02', 'V-04', { elemento: 'etiqueta-corte', sufijo: 'etiqueta-corte', detalle: `etiqueta del corte «${cifras.corte}»` })
  await paso.captura('RNF-02', 'V-04', { elemento: 'ultima-fila', sufijo: 'ultima-fila', detalle: `última fila «${cifras.ultima}»` })
}

async function paso2(ctx, paso) {
  const p = ctx.pagina
  await p.ir(`/portafolios/${ctx.idPrincipal}/posiciones?fecha_corte=2026-10-14`)
  const aviso = await p.esperarPantalla('V-05')
  const total = await p.texto('total-valor')
  ctx.total1 = total
  await paso.captura(['RF-06', 'RF-08', 'RF-26a', 'RF-26b', 'RF-30', 'RF-31 crit. 2 y 3', 'RF-07 crit. 3', 'RF-12 crit. 4'], 'V-05', {
    completa: true,
    detalle: [aviso, 'Principal al 14/10/2026'].filter(Boolean).join('; '),
  })
  await paso.captura('RNF-02', 'V-05', { elemento: 'total-valor', sufijo: 'total', detalle: `total del valor «${total}»` })
}

async function paso3(ctx, paso) {
  const p = ctx.pagina
  await p.ir(`/portafolios/${ctx.idPrincipal}/tablero`) // documento nuevo: la misma consulta, otra vez
  await p.esperarPantalla('V-04')
  const cifras = await leerCifrasV04(p)
  await paso.captura('RNF-02', 'V-04', { completa: true, sufijo: 'repetida', detalle: `consulta repetida: ${describirCifras(cifras)}` })
  await p.ir(`/portafolios/${ctx.idPrincipal}/posiciones?fecha_corte=2026-10-14`)
  await p.esperarPantalla('V-05')
  const total = await p.texto('total-valor')
  await paso.captura('RNF-02', 'V-05', { elemento: 'total-valor', sufijo: 'repetida', detalle: `consulta repetida: total «${total}»` })

  const todas = [cifras.tarjeta, cifras.corte, cifras.ultima, total].map(extraerPesos)
  const primeras = ctx.cifras1 ? [ctx.cifras1.tarjeta, ctx.cifras1.corte, ctx.cifras1.ultima, ctx.total1].map(extraerPesos) : null
  const iguales = todas.every((c) => c && c === todas[0])
  const igualesALaPrimera = primeras ? primeras.every((c, i) => c === todas[i]) : null
  const detalle = [
    `cifras de la tarjeta, la etiqueta del corte, la última fila y el total: ${todas.map((c) => c || '—').join(' / ')}`,
    primeras ? `primera consulta: ${primeras.map((c) => c || '—').join(' / ')}` : 'sin la primera consulta (pasos 1 y 2 no corrieron en esta ejecución)',
    todas[0] === VALOR_5_2 ? `igual a 5.2 (${VALOR_5_2})` : `distinta de 5.2 (${VALOR_5_2})`,
  ].join('; ')
  paso.anotar('RNF-02 (consulta repetida)', 'V-04 y V-05', iguales && igualesALaPrimera !== false ? 'coincide' : 'no coincide', detalle)
}

async function paso4(ctx, paso) {
  const p = ctx.pagina
  await p.ir(`/portafolios/${ctx.idPrincipal}/transacciones`)
  const aviso = await p.esperarPantalla('V-06')
  const filas = await p.llamar(() => document.querySelectorAll('main table tbody tr').length)
  await paso.captura(['RF-05 (consulta)', 'RF-12 crit. 4'], 'V-06', { completa: true, detalle: [aviso, `Principal: ${filas} filas en la tabla`].filter(Boolean).join('; ') })
}

async function paso5(ctx, paso) {
  const p = ctx.pagina
  const rutaE17 = `/portafolios/${ctx.idPrincipal}/transacciones`
  const antesE17 = (await p.consultarApi(rutaE17)).length
  await p.ir(`/portafolios/${ctx.idPrincipal}/transacciones/nueva`)
  const aviso = await p.esperarPantalla('V-07')
  await llenarTransaccion(p, N1, 'Principal')
  const antes = await p.errorActual()
  await p.clic('registrar')
  const motivo = await p.esperarErrorNuevo(antes, 'el motivo del rechazo')
  await dormir(300)
  const despuesE17 = (await p.consultarApi(rutaE17)).length
  const pantalla = await p.pantallaActual()
  if (pantalla !== 'V-07') throw new Error(`Después del rechazo la pantalla es ${pantalla}, no V-07`)
  const conservado = {
    cantidad: await p.valor('cantidad'),
    precio: await p.valor('precio'),
    comisiones: await p.valor('comisiones'),
  }
  const seConserva = conservado.cantidad === N1.cantidad && conservado.precio === N1.precio && conservado.comisiones === N1.comisiones
  const nada = antesE17 === despuesE17
  await paso.captura(['RF-28 crit. 3', 'RF-28 crit. 1'], 'V-07', {
    completa: true,
    detalle: [
      aviso,
      `N1 (venta de DEMOACC con Casa B el 18/09/2026, 150 títulos): «${motivo.slice(0, 200)}»`,
      nada ? `nada registrado (E17: ${antesE17} antes y después)` : `E17 pasó de ${antesE17} a ${despuesE17}`,
      seConserva ? 'lo capturado se conserva' : `lo capturado cambió: ${JSON.stringify(conservado)}`,
    ]
      .filter(Boolean)
      .join('; '),
    resultado: seConserva && nada ? 'correcto' : 'falló',
  })
}

async function paso6(ctx, paso) {
  const p = ctx.pagina
  await p.ir('/catalogo')
  const aviso = await p.esperarPantalla('V-10')
  await paso.captura(['RF-04'], 'V-10', { completa: true, detalle: aviso })
}

async function paso7(ctx, paso) {
  const p = ctx.pagina
  await p.ir('/intermediarios')
  const aviso = await p.esperarPantalla('V-09')
  await paso.captura(['RF-25 (consulta)'], 'V-09', { completa: true, detalle: aviso })
}

async function paso8(ctx, paso) {
  const p = ctx.pagina
  const { hhmm } = ahora()
  // Si quedó uno de otra ejecución, el nombre lleva la hora para no chocar (409).
  const previos = (await p.consultarApi('/portafolios')).filter((x) => x.nombre.startsWith('Recorrido AC-04'))
  const sufijo = previos.length ? ` ${hhmm}` : ''
  const nombre = `${NOMBRE_DESECHABLE}${sufijo}`
  const nuevoNombre = `Recorrido AC-04 (desechable, renombrado)${sufijo}`

  // Alta: según H-4, abre el tablero del portafolio nuevo, sin datos (RF-11 crit. 3).
  await p.ir('/portafolios')
  await p.esperarPantalla('V-08')
  await enviarConCampo(p, 'nombre-portafolio', nombre, 'crear-portafolio')
  await p.esperar((n) => {
    const m = document.querySelector('main')
    if (m?.getAttribute('data-recorrido') === 'V-04') return true
    if (dialogoAbierto() && hayError()) return { falla: `Rechazo del alta: ${hayError()}` }
    return m?.getAttribute('data-recorrido') === 'V-08' && !dialogoAbierto() && minus(m.innerText).includes(minus(n))
  }, 'el portafolio nuevo', 15000, nombre)
  const lista = await p.consultarApi('/portafolios')
  const nuevo = lista.find((x) => x.nombre === nombre)
  if (!nuevo) throw new Error(`E12 no lista «${nombre}» después del alta`)
  ctx.idDesechable = nuevo.id
  if ((await p.pantallaActual()) !== 'V-04') await p.ir(`/portafolios/${nuevo.id}/tablero`)
  const avisoAlta = await p.esperarPantalla('V-04')
  await paso.captura(['RF-03 (alta)', 'RF-11 crit. 3'], 'V-04', { completa: true, sufijo: 'alta', detalle: [avisoAlta, `«${nombre}» sin transacciones`].filter(Boolean).join('; ') })

  // Cambio de nombre en su diálogo.
  await p.ir('/portafolios')
  await p.esperarPantalla('V-08')
  await p.clic('renombrar', { fila: nombre })
  await p.esperar(() => !!dialogoAbierto(), 'el diálogo de cambio de nombre', 8000)
  await escribirEnDialogo(p, ['nombre-portafolio', 'nuevo-nombre', 'nombre'], nuevoNombre)
  await p.clic('confirmar', { enDialogo: true })
  await p.esperar((n) => {
    if (dialogoAbierto()) {
      const e = hayError()
      return e ? { falla: `Rechazo del cambio de nombre: ${e}` } : false
    }
    return minus(document.querySelector('main')?.innerText).includes(minus(n))
  }, 'el nombre nuevo en la lista', 10000, nuevoNombre)
  await paso.captura('RF-03 (cambio de nombre)', 'V-08', { completa: true, sufijo: 'cambio-nombre', detalle: `«${nombre}» → «${nuevoNombre}»` })

  // Una compra válida en el portafolio desechable (RF-05, registro).
  await p.ir(`/portafolios/${ctx.idDesechable}/transacciones/nueva`)
  await p.esperarPantalla('V-07')
  await llenarTransaccion(p, COMPRA_VALIDA, nuevoNombre)
  await paso.captura('RF-05 (registro, formulario)', 'V-07', { completa: true, sufijo: 'compra', detalle: 'compra de 10 DEMOACC con Casa A el 01/10/2026 a $105.35, comisiones $3.05' })
  await p.clic('registrar')
  await p.esperar(() => {
    const m = document.querySelector('main')?.getAttribute('data-recorrido')
    if (m === 'V-06') return true
    const e = hayError()
    return e ? { falla: `Rechazo al registrar la compra: ${e}` } : false
  }, 'V-06 después de registrar', 15000)
  const avisoV06 = await p.esperarPantalla('V-06')
  const mensaje = (await p.textoMain()).includes('Transacción registrada') ? 'con «Transacción registrada»' : 'sin el mensaje «Transacción registrada»'
  await paso.captura('RF-05 (registro)', 'V-06', { completa: true, sufijo: 'registrada', detalle: [avisoV06, mensaje].filter(Boolean).join('; ') })

  // Eliminar: primero Cancelar (crit. 3), luego con el nombre (crit. 1).
  await p.ir('/portafolios')
  await p.esperarPantalla('V-08')
  await p.clic('eliminar', { fila: nuevoNombre })
  await p.esperar(() => !!dialogoAbierto(), 'el diálogo de eliminar', 8000)
  await paso.captura('RF-03 crit. 1 (confirmación)', 'V-08', { sufijo: 'dialogo-eliminar', detalle: 'el diálogo pide escribir el nombre' })
  await p.clic('cancelar', { enDialogo: true })
  await p.esperar(() => !dialogoAbierto(), 'el cierre del diálogo', 5000)
  const sigue = (await p.consultarApi('/portafolios')).some((x) => x.id === ctx.idDesechable)
  await paso.captura('RF-03 crit. 3 (cancelar)', 'V-08', { sufijo: 'cancelado', detalle: sigue ? 'Cancelar no cambió nada: el portafolio sigue en E12' : 'el portafolio ya no está', resultado: sigue ? 'correcto' : 'falló' })

  await p.clic('eliminar', { fila: nuevoNombre })
  await p.esperar(() => !!dialogoAbierto(), 'el diálogo de eliminar', 8000)
  await escribirEnDialogo(p, ['confirmacion'], nuevoNombre)
  await p.clic('confirmar', { enDialogo: true })
  await p.esperar(() => {
    if (dialogoAbierto()) {
      const e = hayError()
      return e ? { falla: `Rechazo de la eliminación: ${e}` } : false
    }
    return true
  }, 'la eliminación', 10000)
  await p.asentar()
  const quedo = (await p.consultarApi('/portafolios')).some((x) => x.id === ctx.idDesechable)
  await paso.captura('RF-03 (eliminación)', 'V-08', {
    completa: true,
    sufijo: 'eliminado',
    detalle: quedo ? 'E12 todavía lista el portafolio' : 'eliminado; ya no aparece en E12',
    resultado: quedo ? 'falló' : 'correcto',
  })
  if (!quedo) ctx.idDesechable = null
}

async function paso9(ctx, paso) {
  const p = ctx.pagina
  await p.ir('/cuenta')
  const aviso = await p.esperarPantalla('V-11')
  await paso.captura(['RF-12 crit. 1'], 'V-11', { completa: true, detalle: [aviso, 'cuenta del oráculo; no se revoca'].filter(Boolean).join('; ') })
}

async function paso10(ctx, paso) {
  const { browserContextId } = await ctx.cdp.enviar('Target.createBrowserContext', { disposeOnDetach: true })
  const b = await Pagina.abrir(ctx.cdp, ctx.op.base, browserContextId)
  paso.pagina = b
  try {
    const { hhmm } = ahora()
    const correoB = `recorrido-b-${hhmm}@example.com`
    const claveB = crypto.randomBytes(18).toString('base64url')
    const claveErronea = crypto.randomBytes(18).toString('base64url')

    // 10.1 Aviso sin sesión.
    await b.ir('/aviso-privacidad')
    let aviso = await b.esperarPantalla('V-03')
    await paso.captura('RF-12 crit. 2 (sin sesión)', 'V-03', { completa: true, sufijo: 'sin-sesion', detalle: [aviso, 'contexto aislado, sin sesión'].filter(Boolean).join('; ') })

    // 10.2 Registro: casilla sin marcar y el aviso en un diálogo.
    await b.ir('/registro')
    aviso = await b.esperarPantalla('V-02')
    const marcada = await b.llamar(() => !!control('casilla-consentimiento')?.checked)
    await paso.captura('RF-12 crit. 1 (casilla sin marcar)', 'V-02', { completa: true, sufijo: 'casilla', detalle: [aviso, marcada ? 'la casilla aparece marcada' : 'la casilla aparece sin marcar'].filter(Boolean).join('; '), resultado: marcada ? 'falló' : 'correcto' })
    await b.clic('ver-aviso')
    await b.esperar(() => {
      const d = dialogoAbierto()
      return !!d && textoDe(d).length > 200
    }, 'el diálogo con el aviso', 10000)
    await paso.captura('RF-12 crit. 2 (diálogo del aviso)', 'V-02', { sufijo: 'dialogo-aviso', detalle: 'el aviso se lee sin salir del formulario' })
    await cerrarDialogo(b)

    // 10.3 Rechazo sin consentimiento.
    await b.escribir('correo', correoB)
    await b.escribir('contrasena', claveB)
    await b.marcar('casilla-consentimiento', false)
    const antesRechazo = await b.errorActual()
    await b.clic('crear-cuenta')
    const motivo = await b.esperarErrorNuevo(antesRechazo, 'el rechazo sin consentimiento', 10000)
    await dormir(300)
    const sigueEnV02 = (await b.pantallaActual()) === 'V-02'
    await paso.captura(['RF-12 crit. 1 (rechazo sin consentimiento)', 'RF-01 crit. 1'], 'V-02', {
      completa: true,
      sufijo: 'rechazo',
      detalle: `«${motivo.slice(0, 200)}»${sigueEnV02 ? '' : '; ya no está en V-02'}`,
      resultado: sigueEnV02 ? 'correcto' : 'falló',
    })

    // 10.4 Alta con la casilla marcada: vuelve a V-01 con el mensaje y el correo escrito (N-04).
    // Si el rechazo anterior hubiera creado la cuenta, este alta daría 409 y fallaría aquí.
    await b.marcar('casilla-consentimiento', true)
    await b.clic('crear-cuenta')
    await b.esperar(() => {
      const m = document.querySelector('main')?.getAttribute('data-recorrido')
      if (m === 'V-01') return true
      const e = hayError()
      return e && !/casilla|consentimiento/i.test(e) ? { falla: `Rechazo del alta: ${e}` } : false
    }, 'V-01 después del alta', 15000)
    aviso = await b.esperarPantalla('V-01')
    const correoEscrito = await b.valor('correo')
    const textoAlta = await b.textoMain()
    await paso.captura('RF-01 (alta)', 'V-01', {
      completa: true,
      sufijo: 'cuenta-creada',
      detalle: [aviso, `cuenta ${correoB}`, textoAlta.includes('Tu cuenta quedó creada') ? 'con «Tu cuenta quedó creada. Inicia sesión.»' : 'sin el mensaje de cuenta creada', correoEscrito === correoB ? 'correo ya escrito' : 'el correo no quedó escrito']
        .filter(Boolean)
        .join('; '),
    })

    // 10.5 Contraseña errónea: mensaje único y la contraseña se vacía; luego entra.
    if (correoEscrito !== correoB) await b.escribir('correo', correoB)
    await b.escribir('contrasena', claveErronea)
    const antesEntrar = await b.errorActual()
    await b.clic('entrar')
    const mensaje = await b.esperarErrorNuevo(antesEntrar, 'el mensaje del inicio de sesión fallido')
    await dormir(300)
    const vacia = (await b.valor('contrasena')) === ''
    await paso.captura('RF-01 (contraseña errónea)', 'V-01', { completa: true, sufijo: 'rechazo', detalle: `«${mensaje.slice(0, 200)}»; ${vacia ? 'la contraseña se vació' : 'la contraseña no se vació'}`, resultado: vacia ? 'correcto' : 'falló' })
    await iniciarSesion(b, correoB, claveB)

    // 10.6 La cuenta B registra «Casa A», que ya existe en la cuenta del oráculo (RF-25 crit. 1).
    await b.ir('/intermediarios')
    await b.esperarPantalla('V-09')
    await enviarConCampo(b, 'nombre-intermediario', 'Casa A', 'crear-intermediario')
    await b.esperar(() => {
      const e = hayError()
      if (e) return { falla: `Rechazo de «Casa A»: ${e}` }
      if (dialogoAbierto()) return false
      return [...document.querySelectorAll('main td, main th, main li')].some((x) => textoDe(x) === 'Casa A')
    }, '«Casa A» en la lista', 10000)
    await paso.captura('RF-25 crit. 1', 'V-09', { completa: true, sufijo: 'casa-a-cuenta-b', detalle: 'la cuenta B registra «Casa A», que también existe en la cuenta del oráculo' })

    // 10.7 Portafolio ajeno e inexistente: el mismo texto (RF-02 crit. 2; RNF-03).
    const noEncontrado = () => {
      const m = document.querySelector('main')
      return !!m && (m.getAttribute('data-recorrido') === 'V-12' || minus(m.innerText).includes('no existe el portafolio')) && !document.querySelector('main [aria-busy="true"]')
    }
    let textoAjeno = null
    if (ctx.idPrincipal) {
      await b.ir(`/portafolios/${ctx.idPrincipal}/tablero`)
      await b.esperar(noEncontrado, '«No existe el portafolio.» (ajeno)', ESPERA_PANTALLA)
      await b.asentar()
      textoAjeno = await b.textoMain()
      await paso.captura('RF-02 crit. 2 (ajeno)', await b.pantallaActual(), { completa: true, sufijo: 'ajeno', detalle: `portafolio «Principal» del oráculo: «${textoAjeno.slice(0, 120)}»` })
    }
    await b.ir(`/portafolios/${ID_INEXISTENTE}/tablero`)
    await b.esperar(noEncontrado, '«No existe el portafolio.» (inexistente)', ESPERA_PANTALLA)
    await b.asentar()
    const textoInexistente = await b.textoMain()
    const mismo = textoAjeno !== null && textoAjeno === textoInexistente
    await paso.captura(['RNF-03', 'RF-02 crit. 2 (inexistente)'], await b.pantallaActual(), {
      completa: true,
      sufijo: 'inexistente',
      detalle: textoAjeno === null ? 'sin la comparación con el ajeno' : mismo ? 'mismo texto que el portafolio ajeno' : `texto distinto del ajeno: «${textoInexistente.slice(0, 120)}»`,
      resultado: mismo ? 'correcto' : 'falló',
    })

    // 10.8 Revocación de la cuenta B: queda bloqueada (RF-12 crit. 3).
    await b.ir('/cuenta')
    await b.esperarPantalla('V-11')
    await b.clic('revocar')
    await b.esperar(() => !!dialogoAbierto(), 'el diálogo de revocación', 8000)
    await paso.captura('RF-12 crit. 3 (confirmación)', 'V-11', { sufijo: 'dialogo-revocar', detalle: 'cuenta B' })
    await b.clic('confirmar', { enDialogo: true })
    await b.esperar(() => document.querySelector('main')?.getAttribute('data-recorrido') === 'V-01', 'V-01 después de revocar', 15000)
    aviso = await b.esperarPantalla('V-01')
    const textoRevocado = await b.textoMain()
    await paso.captura('RF-12 crit. 3 (revocación)', 'V-01', { completa: true, sufijo: 'revocado', detalle: [aviso, textoRevocado.includes('Revocaste tu consentimiento') ? 'con «Revocaste tu consentimiento; tu cuenta quedó bloqueada.»' : 'sin el mensaje de revocación'].filter(Boolean).join('; ') })
    await b.escribir('correo', correoB)
    await b.escribir('contrasena', claveB)
    const antesBloqueo = await b.errorActual()
    await b.clic('entrar')
    const bloqueada = await b.esperar(
      (previo) => {
        const m = document.querySelector('main')?.getAttribute('data-recorrido')
        if (m && m !== 'V-01') return 'entró'
        const e = hayError()
        return e && e !== previo ? e : ''
      },
      'el resultado del intento de entrar',
      15000,
      antesBloqueo,
    )
    await paso.captura('RF-12 crit. 3 (cuenta bloqueada)', await b.pantallaActual(), {
      completa: true,
      sufijo: 'bloqueada',
      detalle: bloqueada === 'entró' ? 'la cuenta revocada pudo entrar' : `ya no puede entrar: «${bloqueada.slice(0, 160)}»`,
      resultado: bloqueada === 'entró' ? 'falló' : 'correcto',
    })
  } catch (e) {
    await paso.fallo(e, b) // aquí, para que la captura de diagnóstico sea de la cuenta B
  } finally {
    await b.cerrar()
    await ctx.cdp.enviar('Target.disposeBrowserContext', { browserContextId }).catch(() => {})
  }
}

const PASOS = [
  { n: 1, titulo: 'V-04 de «Principal» y RNF-02', fn: paso1, requisitos: ['RF-11 crit. 1', 'RF-07 crit. 3', 'RF-08', 'RF-09', 'RF-10', 'RF-12 crit. 4', 'RF-31 crit. 2 y 3', 'RF-26b', 'RF-30', 'RF-11 crit. 2', 'RNF-02'] },
  { n: 2, titulo: 'V-05 al 14/10', fn: paso2, requisitos: ['RF-06', 'RF-08', 'RF-26a', 'RF-26b', 'RF-30', 'RF-31 crit. 2 y 3', 'RF-07 crit. 3', 'RF-12 crit. 4', 'RNF-02'] },
  { n: 3, titulo: 'RNF-02, consulta repetida', fn: paso3, requisitos: ['RNF-02 (consulta repetida)'] },
  { n: 4, titulo: 'V-06 de «Principal»', fn: paso4, requisitos: ['RF-05 (consulta)', 'RF-12 crit. 4'] },
  { n: 5, titulo: 'V-07 con N1 rechazada', fn: paso5, requisitos: ['RF-28 crit. 3', 'RF-28 crit. 1'] },
  { n: 6, titulo: 'V-10, catálogo', fn: paso6, requisitos: ['RF-04'] },
  { n: 7, titulo: 'V-09, intermediarios', fn: paso7, requisitos: ['RF-25 (consulta)'] },
  { n: 8, titulo: 'V-08: portafolio desechable, compra y eliminación', fn: paso8, requisitos: ['RF-03 (alta)', 'RF-11 crit. 3', 'RF-03 (cambio de nombre)', 'RF-05 (registro, formulario)', 'RF-05 (registro)', 'RF-03 crit. 1 (confirmación)', 'RF-03 crit. 3 (cancelar)', 'RF-03 (eliminación)'] },
  { n: 9, titulo: 'V-11 de la cuenta', fn: paso9, requisitos: ['RF-12 crit. 1'] },
  {
    n: 10,
    titulo: 'Cuenta B en un contexto aislado',
    fn: paso10,
    requisitos: [
      'RF-12 crit. 2 (sin sesión)',
      'RF-12 crit. 1 (casilla sin marcar)',
      'RF-12 crit. 2 (diálogo del aviso)',
      'RF-12 crit. 1 (rechazo sin consentimiento)',
      'RF-01 crit. 1',
      'RF-01 (alta)',
      'RF-01 (contraseña errónea)',
      'RF-25 crit. 1',
      'RF-02 crit. 2 (ajeno)',
      'RNF-03',
      'RF-02 crit. 2 (inexistente)',
      'RF-12 crit. 3 (confirmación)',
      'RF-12 crit. 3 (revocación)',
      'RF-12 crit. 3 (cuenta bloqueada)',
    ],
  },
]

// ---------------------------------------------------------------------------------------------
// Principal
// ---------------------------------------------------------------------------------------------

async function principal() {
  let op
  try {
    op = leerOpciones(process.argv.slice(2))
  } catch (e) {
    console.error(e.message)
    return 2
  }
  if (op.ayuda) {
    const texto = fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n')
    console.log(texto.slice(1, texto.findIndex((l) => l.startsWith('import '))).map((l) => l.replace(/^\/\/ ?/, '')).join('\n'))
    return 0
  }
  if (typeof WebSocket !== 'function') {
    console.error('Este guion necesita Node 22 o posterior (WebSocket global); se probó con Node 24.')
    return 2
  }

  let clave
  try {
    clave = op.claveArchivo ? fs.readFileSync(op.claveArchivo, 'utf8').replace(/\r?\n$/, '') : await pedirClave(`Contraseña de ${op.correo} (no se muestra): `)
  } catch (e) {
    console.error(e instanceof ErrorUso ? e.message : 'No se pudo leer la contraseña.')
    return 2
  }
  if (!clave) {
    console.error('La contraseña está vacía.')
    return 2
  }

  const registro = new Registro(op.salida)
  const inicio = ahora()
  console.log(`Recorrido de AC-04 · ${inicio.fecha} ${inicio.hora} · ${op.base} · salida en ${path.relative(process.cwd(), op.salida) || '.'}`)

  let edge
  let cdp
  const limpiar = async () => {
    const e = edge
    edge = null
    if (e) await cerrarEdge(e, cdp)
    else cdp?.cerrar()
  }
  process.once('SIGINT', () => {
    limpiar().finally(() => process.exit(130))
  })

  let pagina
  try {
    edge = await abrirEdge(op)
    cdp = await Cdp.conectar(edge.ws)
    pagina = await Pagina.abrir(cdp, op.base)
    const ctx = { op, cdp, pagina, registro, idPrincipal: null }

    console.log('Inicio de sesión de la cuenta y portafolios (E12, solo lectura)…')
    await iniciarSesion(pagina, op.correo, clave)
    const portafolios = await pagina.consultarApi('/portafolios')
    ctx.idPrincipal = portafolios.find((x) => x.nombre === 'Principal')?.id ?? null
    if (!ctx.idPrincipal) throw new Error('La cuenta no tiene el portafolio «Principal» de 5.2.')

    for (const p of PASOS) {
      if (op.pasos && !op.pasos.has(p.n)) continue
      console.log(`Paso ${p.n}: ${p.titulo}`)
      const paso = new Paso(ctx, p.n, p.titulo, p.requisitos, pagina)
      try {
        await p.fn(ctx, paso)
      } catch (e) {
        await paso.fallo(e, paso.pagina)
      }
    }
  } catch (e) {
    let archivo = ''
    if (pagina) {
      try {
        const { nombre, ruta } = registro.nombre('fallo-inicio', (await pagina.pantallaActual()) || 'sin-pantalla')
        await pagina.capturar(ruta)
        archivo = nombre
      } catch {
        // sin captura de diagnóstico
      }
    }
    registro.fila({ requisito: 'inicio', pantalla: '', archivo, resultado: 'falló', detalle: String(e?.message || e).replace(/\s+/g, ' ').slice(0, 400) })
  } finally {
    clave = null
    await limpiar()
  }

  const fin = ahora()
  console.log(`Terminó a las ${fin.hora}: ${registro.filas} filas en recorrido.csv, ${registro.fallos} con falla.`)
  return registro.fallos ? 1 : 0
}

process.exitCode = await principal()
