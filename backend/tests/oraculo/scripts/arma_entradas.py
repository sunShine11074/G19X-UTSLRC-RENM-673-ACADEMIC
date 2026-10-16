"""Arma las entradas congelables del oraculo de 5.2 (oraculo/entradas/*.csv).

Toma el diseno (diseno/*.csv), las tasas reales del CF107 (datos/tasas_cf107.csv,
con sus fuentes) y el calendario de 2026 (datos/dias_sin_operaciones_2026.csv) y
escribe los CSV con las columnas de 4.4 donde existen, mas columnas auxiliares
(llaves naturales y documentacion). Las llaves sustitutas (id) las asigna la base;
aqui cada fila se liga por llave natural: correo, nombre de portafolio, nombre de
intermediario, clave de instrumento, nombre de fuente, version de licencia y carga.

No calcula ninguna cifra del oraculo: solo copia, filtra, cuenta filas y documenta
entradas. Uso: python -I -B <ruta del oraculo>/scripts/arma_entradas.py
"""
import csv
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DISENO = RAIZ / "diseno"
DATOS = RAIZ / "datos"
SALIDA = RAIZ / "entradas"
SALIDA.mkdir(exist_ok=True)

CORREO = "oraculo@example.com"
FUENTE_SINTETICA = "Semilla sintetica de demostracion 077"
FUENTE_BANXICO = "Banco de México"
SEMILLA_TASAS_DESDE = "2026-08-27"   # S-09, P-14 y criterio 1 de RF-30
SEMILLA_TASAS_HASTA = "2026-10-15"   # incluye a proposito la colocacion del 15/10 (R-14)


def escribe(nombre, columnas, filas):
    with open(SALIDA / nombre, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(columnas)
        w.writerows(filas)
    print(f"{nombre}: {len(filas)} filas")


def lee(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---- parametros, cortes y periodos (fijados por el escenario; S-09 y P-14)
escribe("parametros.csv", ["parametro", "valor", "descripcion"], [
    ["intervalo_semillas_inicio", "2026-09-10", "Primer dia del intervalo de las semillas de precios (S-09, P-14); dia de las primeras compras"],
    ["intervalo_semillas_fin", "2026-10-14", "Ultimo dia del intervalo de las semillas de precios (S-09, P-14)"],
    ["serie_inicio", "2026-09-10", "Cierre base de la serie diaria: V(10/09), I = 1"],
    ["serie_fin", "2026-10-14", "Ultimo dia de la serie diaria"],
    ["usuario_correo", CORREO, "Usuario de prueba con datos ficticios (S-04)"],
])
escribe("cortes.csv", ["fecha_corte", "motivo"], [
    ["2026-09-13", "Domingo: se valua con los cierres del 11/09 (criterio 4 de RF-08); P2 aun sin posicion"],
    ["2026-09-16", "Festivo (DOF 10/12/2025): se valua con los cierres del 15/09; DEMOACC en dos intermediarios (OE-5)"],
    ["2026-10-08", "Vencimiento de BI261008 y reinversion T16; DEMOFIB sin cierre ese dia (usa el del 07/10)"],
    ["2026-10-14", "Corte final del periodo"],
])
escribe("periodos.csv", ["periodo", "portafolio_nombre", "inicio", "fin", "proposito"], [
    ["P1-A", "Principal", "2026-09-11", "2026-10-14", "Periodo completo (base V(10/09))"],
    ["P1-B", "Principal", "2026-09-11", "2026-09-30", "Primer tramo; encadenamiento con P1-C"],
    ["P1-C", "Principal", "2026-10-01", "2026-10-14", "Segundo tramo (base V(30/09)); r(01/10) < 0, el maximo es I = 1"],
    ["P1-D", "Principal", "2026-10-09", "2026-10-12", "Serie que no baja: maxima caida 0 (criterio 2 de RF-10)"],
    ["P2-A", "Secundario", "2026-09-11", "2026-10-14", "Factor 1 con denominador 0 del 11/09 al 13/09; comprobacion por dos caminos"],
    ["P2-C", "Secundario", "2026-10-01", "2026-10-14", "Sin flujos (criterio 1 de RF-09)"],
])

# ---- usuario, portafolios, intermediarios
escribe("usuarios.csv", ["correo"], [[CORREO]])
escribe("portafolios.csv", ["usuario_correo", "nombre", "divisa_base"], [
    [CORREO, "Principal", "MXN"], [CORREO, "Secundario", "MXN"]])
escribe("intermediarios.csv", ["usuario_correo", "nombre"], [[CORREO, "Casa A"], [CORREO, "Casa B"]])

# ---- instrumentos (instrumento + emision_cetes)
ins = lee(DISENO / "instrumentos.csv")
nombres = {"DEMOACC": "Acción de demostración", "DEMOETF": "ETF de demostración",
           "DEMOFIB": "FIBRA de demostración"}
filas = []
for r in ins:
    nombre = nombres.get(r["clave"], r["nombre"])
    filas.append([r["clave"], nombre, r["clase_activo"], r["divisa"], r["de_demostracion"],
                  r["vencimiento"], r["valor_nominal"]])
escribe("instrumentos.csv", ["clave", "nombre", "clase_activo", "divisa", "de_demostracion",
                             "vencimiento", "valor_nominal"], filas)

# ---- fuentes de datos (fuente_datos de 4.4: nombre, direccion, de_demostracion; RF-31).
# La celda vacia de direccion es NULL (la semilla sintetica no tiene direccion de Internet).
escribe("fuentes_datos.csv", ["nombre", "direccion", "de_demostracion"], [
    [FUENTE_BANXICO, "https://www.banxico.org.mx", "false"],
    [FUENTE_SINTETICA, "", "true"],
])

# ---- versiones de licencia (version_licencia de 4.4; RF-31 crit. 1, R-05, D-03).
# obligacion_suprimir vacia = NULL (la version no impone obligacion de suprimir; confirmar).
VERSION = "1"
escribe("versiones_licencia.csv", ["fuente_nombre", "version", "usos_permitidos", "obligacion_suprimir",
                                   "atribucion"], [
    [FUENTE_BANXICO, VERSION,
     "Reproducir y utilizar la información que publica el Banco de México, con la sola condición de "
     "mencionar la fuente y su dirección de Internet (R-05; D-03)", "",
     "Fuente: Banco de México, https://www.banxico.org.mx"],
    [FUENTE_SINTETICA, VERSION,
     "Datos sintéticos creados para el Proyecto 077: uso libre dentro de la aplicación y sus pruebas, "
     "solo como datos de demostración", "",
     "Datos de demostración: precios sintéticos, no son precios reales"],
])
CARGA_PRECIOS, CARGA_TASAS = "C-PRECIOS", "C-TASAS"

# ---- transacciones
PROPOSITO = {
    "T01": "OE-5 (DEMOACC con Casa A); su costo difiere del de Casa B",
    "T02": "Saldo previo del caso de compra y venta el mismo dia (T11 y T12)",
    "T03": "CETES en dos intermediarios (Casa A); compra en mercado secundario concertada el 10/09 al P de RF-26b del dia (d = 28, nodo de la colocacion a 28 dias del 10/09)",
    "T04": "CETES en dos intermediarios (Casa B); compra en mercado secundario concertada el 10/09 al P de RF-26b del dia (d = 28, nodo de la colocacion a 28 dias del 10/09)",
    "T05": "Primer flujo dentro del periodo",
    "T06": "OE-5 (DEMOACC con Casa B)",
    "T07": "X-06: mismo instrumento e intermediario que en Principal, otro portafolio",
    "T08": "Interpolacion entre 28 y 91 dias; compra en mercado secundario concertada el 17/09 al P de RF-26b del dia (d = 91, nodo de la colocacion a 91 dias del 17/09)",
    "T09": "Interpolacion entre 91 y 182 o 175 efectivos; compra en mercado secundario concertada el 17/09 al P de RF-26b del dia (d = 182, nodo de la colocacion a 182 dias del 17/09)",
    "T10": "Venta total: el saldo queda en 0 y el costo se reinicia",
    "T11": "Compra y venta el mismo dia (compras antes que ventas)",
    "T12": "Venta de 120 > saldo previo de 100; solo es valida aplicando antes T11",
    "T13": "Venta parcial de CETES antes del vencimiento, al P de RF-26b del 01/10 (d = 7, tasa a 28 dias del 01/10)",
    "T14": "Venta parcial (80 de 200)",
    "T15": "Recompra tras saldo 0: el costo se reinicia",
    "T16": "Reinversion registrada como compra (S-14), en mercado secundario concertada el 08/10 al P de RF-26b del dia (d = 28, nodo de la colocacion a 28 dias del 08/10)",
}
tx = lee(DISENO / "transacciones.csv")
filas = []
for r in tx:
    filas.append([r["id"], CORREO, r["portafolio"], r["intermediario"], r["instrumento"], r["tipo"],
                  r["fecha_concertacion"], r["cantidad"], r["precio"], r["importe_comisiones"],
                  PROPOSITO[r["id"]], r["regla_del_precio"]])
escribe("transacciones.csv", ["ref", "usuario_correo", "portafolio_nombre", "intermediario_nombre",
                              "instrumento_clave", "tipo", "fecha_concertacion", "cantidad", "precio",
                              "importe_comisiones", "proposito", "regla_del_precio"], filas)

# ---- precios de cierre (formato largo, columnas de precio_cierre)
pre = lee(DISENO / "precios_cierre.csv")
filas = []
for clave in ("DEMOACC", "DEMOETF", "DEMOFIB"):
    for r in pre:
        if r[clave].strip():
            filas.append([clave, r["fecha"], r[clave], FUENTE_SINTETICA, CARGA_PRECIOS])
escribe("precios.csv", ["instrumento_clave", "fecha", "precio", "fuente_nombre", "carga"], filas)
filas_precios = filas

# ---- tasas (columnas de tasa_referencia), semilla del 27/08 al 15/10
fuentes = {(r["fecha_colocacion"], r["plazo_nominal"]): r["fuentes_coincidentes"]
           for r in lee(DATOS / "tasas_cf107_fuentes.csv")}
filas = []
for r in lee(DATOS / "tasas_cf107.csv"):
    if SEMILLA_TASAS_DESDE <= r["fecha_colocacion"] <= SEMILLA_TASAS_HASTA:
        filas.append([r["plazo_nominal"], r["fecha_colocacion"], r["tasa"], "por ciento anual",
                      r["plazo_efectivo"], FUENTE_BANXICO, CARGA_TASAS, r["serie_tasa"], r["serie_plazo"],
                      fuentes[(r["fecha_colocacion"], r["plazo_nominal"])]])
escribe("tasas.csv", ["plazo_nominal", "fecha_colocacion", "valor", "unidad", "plazo_efectivo",
                      "fuente_nombre", "carga", "serie_valor", "serie_plazo", "fuentes_coincidentes"], filas)
filas_tasas = filas

# ---- cargas (carga_datos de 4.4; RF-07, RF-30 y RF-31 crit. 1). Una carga por fuente, origen 'semilla'.
# Intervalo = primera y ultima fecha de los datos de la carga; incorporadas = filas del CSV.
# Omitidas = 0: los CSV de la semilla solo contienen observaciones publicadas (el JSON del SIE no lista
# las semanas sin subasta de 364 y 728 dias; la pagina del CF107 las muestra como N/E).
# valores_sustituidos = {} (nada se sustituye dentro del intervalo de la semilla; RD-21).
# incorporada_en la fija la base (now()); obtenida_en solo existe si P-34 la adopta.
escribe("cargas_datos.csv", ["carga", "fuente_nombre", "version", "origen", "fecha_inicial", "fecha_final",
                             "resultado", "observaciones_incorporadas", "observaciones_omitidas",
                             "valores_sustituidos"], [
    [CARGA_PRECIOS, FUENTE_SINTETICA, VERSION, "semilla", min(f[1] for f in filas_precios),
     max(f[1] for f in filas_precios), "completa", len(filas_precios), 0, "{}"],
    [CARGA_TASAS, FUENTE_BANXICO, VERSION, "semilla", min(f[1] for f in filas_tasas),
     max(f[1] for f in filas_tasas), "completa", len(filas_tasas), 0, "{}"],
])

# ---- candidatos de rechazo (no se cargan: pytest los intenta registrar despues de T01 a T16).
# Los leen los dos caminos (calcula_oraculo.py y la hoja Rechazos), que derivan la regla, la fecha del
# primer saldo negativo y el saldo resultante.
escribe("candidatos_rechazo.csv", ["id", "criterio", "caso", "portafolio_nombre", "intermediario_nombre",
                                   "instrumento_clave", "tipo", "fecha_concertacion", "cantidad", "precio",
                                   "importe_comisiones", "periodo_inicio", "periodo_fin", "motivo_esperado"], [
    ["N1", "RF-28 crit. 1", "transaccion", "Principal", "Casa B", "DEMOACC", "venta", "2026-09-18", "150", "98.50",
     "42.85", "", "", "El saldo con Casa B es 100 aunque la posicion consolidada sea 300; su contraparte aceptada "
                      "es T14 (80 <= 200)"],
    ["N2", "RF-28 crit. 2", "transaccion", "Principal", "Casa A", "DEMOFIB", "venta", "2026-09-15", "100", "25.40",
     "7.37", "", "", "El 15/09 quedaria en 300 y el 14/10 en 200, pero el 22/09, con T10, seria -100"],
    ["N3", "RF-28 crit. 3 y X-06", "transaccion", "Principal", "Casa A", "DEMOACC", "venta", "2026-10-09", "150",
     "109.00", "47.42", "", "", "El saldo del Principal con Casa A es 120; los 150 del Secundario con Casa A no "
                                "cuentan"],
    ["N4", "RF-26a crit. 2", "transaccion", "Principal", "Casa B", "BI261008", "venta", "2026-10-08", "100",
     "10.0000000", "0.00", "", "", "La fecha es igual al vencimiento de la emision"],
    ["N5", "RF-05 crit. 3 (opcional)", "transaccion", "Principal", "Casa A", "DEMOACC", "compra", "2026-09-09", "10",
     "100.00", "2.90", "", "", "Compra fechada el 09/09, antes del intervalo de las semillas"],
    ["N6", "RF-05 crit. 3 (opcional)", "transaccion", "Principal", "Casa A", "DEMOACC", "compra", "2026-10-15", "10",
     "111.00", "3.22", "", "", "Compra fechada el 15/10, despues del intervalo de las semillas"],
    ["N7", "RF-09 crit. 3 (opcional)", "periodo", "Principal", "", "", "", "", "", "", "", "2026-10-14",
     "2026-09-11", "Fecha final anterior a la inicial"],
    ["N8", "RF-09 crit. 3 (opcional)", "periodo", "Principal", "", "", "", "", "", "", "", "2026-09-11",
     "2026-10-15", "El periodo termina despues del intervalo de las semillas"],
])

# ---- calendario (para validar que no haya precios en dias sin operaciones)
shutil.copyfile(DATOS / "dias_sin_operaciones_2026.csv", SALIDA / "dias_sin_operaciones_2026.csv")
print("dias_sin_operaciones_2026.csv: copiado de datos/")
