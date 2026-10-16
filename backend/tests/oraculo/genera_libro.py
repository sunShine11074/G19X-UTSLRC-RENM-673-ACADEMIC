"""Genera oraculo_5_2.xlsx: el oraculo de 5.2 resuelto en hoja de calculo, con formulas visibles.

Primer camino del oraculo. Lee solo las ENTRADAS (entradas/*.csv) y las escribe
en azul; todas las cifras son formulas de Excel, en negro. Los rotulos de
estructura (que filas existen: dias, pares, fechas de corte) van en gris: salen de
los CSV y no se editan en la hoja. No calcula en Python ninguna cifra del oraculo.
Despues se recalcula con Excel:
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/recalc_excel.ps1 oraculo_5_2.xlsx

Funciones usadas: SUMIFS, COUNTIFS, COUNTIF, INDEX, MATCH, MAXIFS y MINIFS (con
_xlfn.; exigen Excel 2019, 2021, 2024 o Microsoft 365), MIN, MAX, ROUND, PRODUCT,
SUMPRODUCT, ABS, WEEKDAY, YEAR, LEFT, AND, OR, IF. Sin matrices dinamicas.
Uso: python -B <ruta del oraculo>/genera_libro.py
     (sin -I: openpyxl esta en el site-packages del usuario, que -I excluye)
"""
import csv
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent
ENT = RAIZ / "entradas"
SALIDA = RAIZ / "oraculo_5_2.xlsx"

# ---------------------------------------------------------------- estilos
AZUL = Font(name="Arial", size=10, color="0000FF")
NEGRO = Font(name="Arial", size=10, color="000000")
GRIS = Font(name="Arial", size=10, color="808080")      # rotulo de estructura (sale de los CSV; no se edita)
ENC = Font(name="Arial", size=10, bold=True)
TIT = Font(name="Arial", size=14, bold=True)
SEC = Font(name="Arial", size=11, bold=True)
NOTA = Font(name="Arial", size=9, italic=True, color="404040")
TEXTO = Font(name="Arial", size=10)
RELL_ENC = PatternFill("solid", fgColor="D9D9D9")
AJUSTE = Alignment(wrap_text=True, vertical="top")

FMT = {"fecha": "yyyy-mm-dd", "peso": "#,##0.0000", "unit": "#,##0.0000000", "p": "0.0000000",
       "tasa": "0.0000000000", "frac": "0.000000000000", "pct": "0.0000000000", "int": "#,##0",
       "gen": "General"}


def lee(nombre):
    with open(ENT / nombre, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f(s):
    return date.fromisoformat(s)


def celda(ws, ref, valor, tipo="gen", fuente=None):
    c = ws[ref]
    c.value = valor
    if fuente is None:
        fuente = NEGRO if isinstance(valor, str) and valor.startswith("=") else AZUL
    c.font = fuente
    c.number_format = FMT[tipo]
    return c


def encabezados(ws, fila, nombres, col0=1):
    for i, n in enumerate(nombres):
        c = ws.cell(row=fila, column=col0 + i, value=n)
        c.font = ENC
        c.fill = RELL_ENC
        c.alignment = Alignment(wrap_text=True, vertical="center")


def titulo(ws, texto, nota):
    ws["A1"] = texto
    ws["A1"].font = TIT
    ws["A2"] = nota
    ws["A2"].font = NOTA


def anchos(ws, dic):
    for col, w in dic.items():
        ws.column_dimensions[col].width = w


def col(n):
    return get_column_letter(n)


def rng(hoja, c, r1, r2):
    """Rango absoluto con hoja, p. ej. Transacciones!$N$5:$N$20."""
    h = f"'{hoja}'" if (" " in hoja or not hoja.isascii()) else hoja
    return f"{h}!${c}${r1}:${c}${r2}"


# ---------------------------------------------------------------- entradas
param = {r["parametro"]: r for r in lee("parametros.csv")}
cortes = lee("cortes.csv")
periodos = lee("periodos.csv")
portafolios = lee("portafolios.csv")
intermediarios = lee("intermediarios.csv")
instrumentos = lee("instrumentos.csv")
fuentes = lee("fuentes_datos.csv")
licencias = lee("versiones_licencia.csv")
cargas = lee("cargas_datos.csv")
txs = lee("transacciones.csv")
precios = lee("precios.csv")
tasas = lee("tasas.csv")
dias_sin = lee("dias_sin_operaciones_2026.csv")
candidatos = lee("candidatos_rechazo.csv")

# filas de Precios y Tasas (se necesitan antes, en las formulas de Entradas)
P1_, P2_ = 5, 4 + len(precios)
TA1, TA2 = 5, 4 + len(tasas)

SERIE_INI = f(param["serie_inicio"]["valor"])
SERIE_FIN = f(param["serie_fin"]["valor"])
DIAS = [SERIE_INI + timedelta(k) for k in range((SERIE_FIN - SERIE_INI).days + 1)]
ORD_PORT = [p["nombre"] for p in portafolios]
ORD_INS = [i["clave"] for i in instrumentos]
ORD_INT = [i["nombre"] for i in intermediarios]
CETES = {i["clave"]: f(i["vencimiento"]) for i in instrumentos if i["clase_activo"] == "cetes"}
NO_CETES = [k for k in ORD_INS if k not in CETES]

# estructura (que filas existen; no son cifras): pares, filas de CETES, dias de periodos
PARES = sorted({(t["portafolio_nombre"], t["instrumento_clave"], t["intermediario_nombre"]) for t in txs},
               key=lambda q: (ORD_PORT.index(q[0]), ORD_INS.index(q[1]), ORD_INT.index(q[2])))
primera = {}
for t in txs:
    if t["instrumento_clave"] in CETES:
        k = t["instrumento_clave"]
        primera[k] = min(primera.get(k, f(t["fecha_concertacion"])), f(t["fecha_concertacion"]))
FILAS_CETES = [(d, k) for k in ORD_INS if k in primera for d in DIAS if primera[k] <= d < CETES[k]]

wb = Workbook()
ws_lee = wb.active
ws_lee.title = "Léeme"
ws_e = wb.create_sheet("Entradas")
ws_t = wb.create_sheet("Transacciones")
ws_p = wb.create_sheet("Precios")
ws_ta = wb.create_sheet("Tasas")
ws_c = wb.create_sheet("CETES")
ws_v = wb.create_sheet("Valuación diaria")
ws_po = wb.create_sheet("Posiciones")
ws_s = wb.create_sheet("Serie")
ws_pe = wb.create_sheet("Periodos")
ws_r = wb.create_sheet("Rechazos")
ws_co = wb.create_sheet("Comprobaciones")
ws_es = wb.create_sheet("Esperados")
VD = "Valuación diaria"

# =====================================================================
# Entradas: parametros, cortes, periodos, catalogos, fuentes, calendario
# =====================================================================
titulo(ws_e, "Entradas del oráculo (5.2)",
       "Azul: entrada escrita a mano (de entradas/*.csv). Negro: fórmula. Gris: rótulo de estructura. "
       "Las llaves sustitutas (id) las asigna la base; aquí cada fila se liga por llave natural. Una celda "
       "vacía en una columna que admite nulos (direccion, obligacion_suprimir) es NULL.")
fila = 4
ws_e.cell(row=fila, column=1, value="Parámetros (S-09, P-14)").font = SEC
fila += 1
encabezados(ws_e, fila, ["parámetro", "valor", "descripción"])
P = {}
for nombre in ("intervalo_semillas_inicio", "intervalo_semillas_fin", "serie_inicio", "serie_fin", "usuario_correo"):
    fila += 1
    r = param[nombre]
    celda(ws_e, f"A{fila}", nombre)
    v = r["valor"]
    if nombre != "usuario_correo":
        celda(ws_e, f"B{fila}", f(v), "fecha")
    else:
        celda(ws_e, f"B{fila}", v)
    celda(ws_e, f"C{fila}", r["descripcion"])
    P[nombre] = f"Entradas!$B${fila}"

fila += 2
ws_e.cell(row=fila, column=1, value="Fechas de corte").font = SEC
fila += 1
encabezados(ws_e, fila, ["fecha_corte", "motivo"])
c1 = fila + 1
for r in cortes:
    fila += 1
    celda(ws_e, f"A{fila}", f(r["fecha_corte"]), "fecha")
    celda(ws_e, f"B{fila}", r["motivo"])
R_CORTES = (c1, fila)

fila += 2
ws_e.cell(row=fila, column=1, value="Periodos de TWR y máxima caída").font = SEC
ws_e.cell(row=fila, column=3, value="Cambiar el inicio o el fin de un periodo exige editar entradas/periodos.csv y "
          "volver a correr genera_libro.py: los bloques diarios de Periodos tienen un largo fijo (Comprobaciones lo "
          "verifica).").font = NOTA
fila += 1
encabezados(ws_e, fila, ["periodo", "portafolio_nombre", "inicio", "fin", "propósito"])
FILA_PERIODO = {}
for r in periodos:
    fila += 1
    celda(ws_e, f"A{fila}", r["periodo"])
    celda(ws_e, f"B{fila}", r["portafolio_nombre"])
    celda(ws_e, f"C{fila}", f(r["inicio"]), "fecha")
    celda(ws_e, f"D{fila}", f(r["fin"]), "fecha")
    celda(ws_e, f"E{fila}", r["proposito"])
    FILA_PERIODO[r["periodo"]] = fila

fila += 2
ws_e.cell(row=fila, column=1, value="Portafolios (usuario de prueba, S-04)").font = SEC
fila += 1
encabezados(ws_e, fila, ["usuario_correo", "nombre", "divisa_base"])
for r in portafolios:
    fila += 1
    for j, k in enumerate(("usuario_correo", "nombre", "divisa_base")):
        celda(ws_e, f"{col(j + 1)}{fila}", r[k])

fila += 2
ws_e.cell(row=fila, column=1, value="Intermediarios (RF-25)").font = SEC
fila += 1
encabezados(ws_e, fila, ["usuario_correo", "nombre"])
for r in intermediarios:
    fila += 1
    celda(ws_e, f"A{fila}", r["usuario_correo"])
    celda(ws_e, f"B{fila}", r["nombre"])

fila += 2
ws_e.cell(row=fila, column=1, value="Instrumentos (instrumento y emision_cetes; RF-04)").font = SEC
fila += 1
encabezados(ws_e, fila, ["clave", "nombre", "clase_activo", "divisa", "de_demostracion", "vencimiento",
                         "valor_nominal", "¿clave válida? (RF-04, RD-04)", "¿marca congruente?"])
i1 = fila + 1
for r in instrumentos:
    fila += 1
    celda(ws_e, f"A{fila}", r["clave"])
    celda(ws_e, f"B{fila}", r["nombre"])
    celda(ws_e, f"C{fila}", r["clase_activo"])
    celda(ws_e, f"D{fila}", r["divisa"])
    celda(ws_e, f"E{fila}", r["de_demostracion"] == "true")
    if r["vencimiento"]:
        celda(ws_e, f"F{fila}", f(r["vencimiento"]), "fecha")
        celda(ws_e, f"G{fila}", float(r["valor_nominal"]), "peso")
    celda(ws_e, f"H{fila}",
          f'=IF(C{fila}="cetes",A{fila}="BI"&RIGHT(YEAR(F{fila}),2)&RIGHT("0"&MONTH(F{fila}),2)&RIGHT("0"&DAY(F{fila}),2),'
          f'NOT(AND(LEFT(A{fila},2)="BI",LEN(A{fila})=8,ISNUMBER(--MID(A{fila},3,6)))))')
    celda(ws_e, f"I{fila}", f'=E{fila}=(C{fila}<>"cetes")')
R_INS = (i1, fila)
INS_CLAVE = rng("Entradas", "A", *R_INS)
INS_CLASE = rng("Entradas", "C", *R_INS)
INS_VENC = rng("Entradas", "F", *R_INS)
INS_VN = rng("Entradas", "G", *R_INS)

fila += 2
ws_e.cell(row=fila, column=1, value="Fuentes de datos (fuente_datos; RF-31)").font = SEC
fila += 1
encabezados(ws_e, fila, ["nombre", "direccion", "de_demostracion"])
for r in fuentes:
    fila += 1
    celda(ws_e, f"A{fila}", r["nombre"])
    if r["direccion"]:
        celda(ws_e, f"B{fila}", r["direccion"])
    celda(ws_e, f"C{fila}", r["de_demostracion"] == "true")

fila += 2
ws_e.cell(row=fila, column=1, value="Versiones de licencia (version_licencia; RF-31 crit. 1; R-05; D-03)").font = SEC
fila += 1
encabezados(ws_e, fila, ["fuente_nombre", "version", "usos_permitidos", "obligacion_suprimir", "atribucion"])
l1 = fila + 1
for r in licencias:
    fila += 1
    celda(ws_e, f"A{fila}", r["fuente_nombre"])
    celda(ws_e, f"B{fila}", r["version"])
    celda(ws_e, f"C{fila}", r["usos_permitidos"])
    if r["obligacion_suprimir"]:
        celda(ws_e, f"D{fila}", r["obligacion_suprimir"])
    celda(ws_e, f"E{fila}", r["atribucion"])
R_LIC = (l1, fila)

fila += 2
ws_e.cell(row=fila, column=1, value="Cargas de datos (carga_datos; RF-07, RF-30, RF-31 crit. 1)").font = SEC
fila += 1
encabezados(ws_e, fila, ["carga", "fuente_nombre", "version", "origen", "fecha_inicial", "fecha_final", "resultado",
                         "observaciones_incorporadas", "observaciones_omitidas", "valores_sustituidos",
                         "filas de la semilla con esta carga", "primera fecha de sus datos",
                         "última fecha de sus datos", "¿cuadra con la semilla?"])
cg1 = fila + 1
PR_B, PR_E = rng("Precios", "B", P1_, P2_), rng("Precios", "E", P1_, P2_)
TA_B, TA_G = rng("Tasas", "B", TA1, TA2), rng("Tasas", "G", TA1, TA2)
for r in cargas:
    fila += 1
    celda(ws_e, f"A{fila}", r["carga"])
    celda(ws_e, f"B{fila}", r["fuente_nombre"])
    celda(ws_e, f"C{fila}", r["version"])
    celda(ws_e, f"D{fila}", r["origen"])
    celda(ws_e, f"E{fila}", f(r["fecha_inicial"]), "fecha")
    celda(ws_e, f"F{fila}", f(r["fecha_final"]), "fecha")
    celda(ws_e, f"G{fila}", r["resultado"])
    celda(ws_e, f"H{fila}", int(r["observaciones_incorporadas"]), "int")
    celda(ws_e, f"I{fila}", int(r["observaciones_omitidas"]), "int")
    celda(ws_e, f"J{fila}", r["valores_sustituidos"])
    celda(ws_e, f"K{fila}", f"=COUNTIF({PR_E},A{fila})+COUNTIF({TA_G},A{fila})", "int")
    celda(ws_e, f"L{fila}", f"=IF(COUNTIF({PR_E},A{fila})>0,_xlfn.MINIFS({PR_B},{PR_E},A{fila}),"
                            f"_xlfn.MINIFS({TA_B},{TA_G},A{fila}))", "fecha")
    celda(ws_e, f"M{fila}", f"=IF(COUNTIF({PR_E},A{fila})>0,_xlfn.MAXIFS({PR_B},{PR_E},A{fila}),"
                            f"_xlfn.MAXIFS({TA_B},{TA_G},A{fila}))", "fecha")
    celda(ws_e, f"N{fila}", f'=AND(H{fila}=K{fila},E{fila}=L{fila},F{fila}=M{fila},D{fila}="semilla",I{fila}>=0,'
                            f'COUNTIFS({rng("Entradas", "A", *R_LIC)},B{fila},{rng("Entradas", "B", *R_LIC)},C{fila})=1)')
R_CARGAS = (cg1, fila)

fila += 2
ws_e.cell(row=fila, column=1, value="Días sin operaciones de 2026 (DOF 10/12/2025, CNBV, art. 1; Grupo BMV)").font = SEC
ws_e.cell(row=fila, column=5, value="Calendario completo: los 104 sábados y domingos de 2026 y los festivos de las "
          "fracciones I a VIII (el 12/12 cae en sábado), 114 fechas.").font = NOTA
fila += 1
encabezados(ws_e, fila, ["fecha", "día", "tipo", "motivo"])
d1 = fila + 1
for r in dias_sin:
    fila += 1
    celda(ws_e, f"A{fila}", f(r["fecha"]), "fecha")
    celda(ws_e, f"B{fila}", r["dia_semana"])
    celda(ws_e, f"C{fila}", r["tipo"])
    celda(ws_e, f"D{fila}", r["motivo"])
R_DIAS_SIN = rng("Entradas", "A", d1, fila)
anchos(ws_e, {"A": 26, "B": 26, "C": 16, "D": 14, "E": 16, "F": 13, "G": 13, "H": 18, "I": 14, "J": 14, "K": 14,
              "L": 14, "M": 14, "N": 14})
ws_e.column_dimensions["C"].width = 18

# =====================================================================
# Transacciones: entradas + kardex por par (portafolio, instrumento, intermediario)
# =====================================================================
titulo(ws_t, "Transacciones (RF-05) y costo promedio por intermediario (RF-08)",
       "A–J: entradas (transaccion de 4.4). K–AF: fórmulas. El kardex (T–Z) procesa cada par portafolio|"
       "instrumento|intermediario en orden: fecha, compras antes que ventas (U = orden). Una venta no cambia el "
       "costo unitario; con saldo 0 se reinicia. AE–AF: la cuadrícula de Valuación diaria cubre el par y la fecha "
       "de la transacción (si se cambia un par a uno sin filas, AF da FALSO).")
T_ENC = ["ref", "portafolio_nombre", "intermediario_nombre", "instrumento_clave", "tipo", "fecha_concertacion",
         "cantidad", "precio", "importe_comisiones", "propósito",
         "clase_activo", "vencimiento", "signo", "cantidad con signo", "monto = títulos × precio",
         "costo por título (compra)", "ingreso por título (venta)", "aportación A", "retiro R",
         "llave del par", "orden (fecha, compras antes que ventas)", "saldo previo del par", "saldo después",
         "orden de la transacción previa del par", "costo unitario previo", "costo unitario después",
         "P de RF-26b ese día (CETES)", "¿precio = P?", "días al vencimiento", "¿importe < monto? (venta)",
         "títulos del par en Valuación diaria ese día", "¿cuadra con el historial?"]
encabezados(ws_t, 4, T_ENC)
T1, T2 = 5, 4 + len(txs)
for i, t in enumerate(txs):
    r = T1 + i
    celda(ws_t, f"A{r}", t["ref"])
    celda(ws_t, f"B{r}", t["portafolio_nombre"])
    celda(ws_t, f"C{r}", t["intermediario_nombre"])
    celda(ws_t, f"D{r}", t["instrumento_clave"])
    celda(ws_t, f"E{r}", t["tipo"])
    celda(ws_t, f"F{r}", f(t["fecha_concertacion"]), "fecha")
    celda(ws_t, f"G{r}", int(t["cantidad"]), "int")
    celda(ws_t, f"H{r}", float(t["precio"]), "unit")
    celda(ws_t, f"I{r}", float(t["importe_comisiones"]), "peso")
    celda(ws_t, f"J{r}", t["proposito"])
    celda(ws_t, f"K{r}", f"=INDEX({INS_CLASE},MATCH(D{r},{INS_CLAVE},0))")
    celda(ws_t, f"L{r}", f'=IF(K{r}="cetes",INDEX({INS_VENC},MATCH(D{r},{INS_CLAVE},0)),"")', "fecha")
    celda(ws_t, f"M{r}", f'=IF(E{r}="compra",1,-1)', "int")
    celda(ws_t, f"N{r}", f"=G{r}*M{r}", "int")
    celda(ws_t, f"O{r}", f"=G{r}*H{r}", "peso")
    celda(ws_t, f"P{r}", f'=IF(E{r}="compra",(O{r}+I{r})/G{r},"")', "unit")
    celda(ws_t, f"Q{r}", f'=IF(E{r}="venta",(O{r}-I{r})/G{r},"")', "unit")
    celda(ws_t, f"R{r}", f'=IF(E{r}="compra",O{r}+I{r},0)', "peso")
    celda(ws_t, f"S{r}", f'=IF(E{r}="venta",O{r}-I{r},0)', "peso")
    celda(ws_t, f"T{r}", f'=B{r}&"|"&D{r}&"|"&C{r}')
    celda(ws_t, f"U{r}", f'=F{r}*1000+IF(E{r}="venta",500,0)+ROWS($A${T1}:A{r})', "int")
    celda(ws_t, f"V{r}", f'=SUMIFS($N${T1}:$N${T2},$T${T1}:$T${T2},T{r},$U${T1}:$U${T2},"<"&U{r})', "int")
    celda(ws_t, f"W{r}", f"=V{r}+N{r}", "int")
    celda(ws_t, f"X{r}", f'=_xlfn.MAXIFS($U${T1}:$U${T2},$T${T1}:$T${T2},T{r},$U${T1}:$U${T2},"<"&U{r})', "int")
    celda(ws_t, f"Y{r}", f"=IF(X{r}=0,0,INDEX($Z${T1 - 1}:Z{r - 1},MATCH(X{r},$U${T1 - 1}:U{r - 1},0)))", "unit")
    celda(ws_t, f"Z{r}", f'=IF(E{r}="compra",(V{r}*Y{r}+G{r}*P{r})/W{r},IF(W{r}=0,0,Y{r}))', "unit")
    # AA-AC se llenan cuando existe la hoja CETES (rangos abajo)
R_T = {c: rng("Transacciones", c, T1, T2) for c in "ABCDEFGHIKLNORSTUWZ"}
anchos(ws_t, {"A": 6, "B": 12, "C": 11, "D": 11, "E": 8, "F": 12, "G": 9, "H": 12, "I": 11, "J": 40,
              "K": 9, "L": 12, "M": 6, "N": 9, "O": 14, "P": 14, "Q": 14, "R": 14, "S": 14, "T": 26, "U": 12,
              "V": 9, "W": 9, "X": 12, "Y": 14, "Z": 14, "AA": 13, "AB": 9, "AC": 10, "AD": 10})

# =====================================================================
# Precios: cierres sinteticos y cierre usado en cada dia natural
# =====================================================================
titulo(ws_p, "Precios de cierre sintéticos (RF-07) y cierre usado cada día",
       "Fuente: semilla sintética de demostración del 077 (no son precios reales; R-04, R-05). Solo días con "
       "operaciones de 2026; DEMOFIB no tiene cierre el 08/10 a propósito. I–M: último cierre igual o anterior "
       "a cada día natural (criterio 4 de RF-08); I y J son rótulos de estructura (gris).")
encabezados(ws_p, 4, ["instrumento_clave", "fecha", "precio", "fuente_nombre", "carga",
                      "día de la semana (1 = lunes)", "¿día con operaciones?"])
encabezados(ws_p, 4, ["fecha", "instrumento_clave", "fecha del cierre usado", "precio usado", "¿sin cierre ese día?"],
            col0=9)
for i, r in enumerate(precios):
    fr = P1_ + i
    celda(ws_p, f"A{fr}", r["instrumento_clave"])
    celda(ws_p, f"B{fr}", f(r["fecha"]), "fecha")
    celda(ws_p, f"C{fr}", float(r["precio"]), "unit")
    celda(ws_p, f"D{fr}", r["fuente_nombre"])
    celda(ws_p, f"E{fr}", r["carga"])
    celda(ws_p, f"F{fr}", f"=WEEKDAY(B{fr},2)", "int")
    celda(ws_p, f"G{fr}", f"=AND(F{fr}<=5,COUNTIF({R_DIAS_SIN},B{fr})=0)")
PU1 = 5
fr = PU1 - 1
for d in DIAS:
    for k in NO_CETES:
        fr += 1
        celda(ws_p, f"I{fr}", d, "fecha", fuente=GRIS)
        celda(ws_p, f"J{fr}", k, fuente=GRIS)
        celda(ws_p, f"K{fr}", f'=_xlfn.MAXIFS($B${P1_}:$B${P2_},$A${P1_}:$A${P2_},J{fr},$B${P1_}:$B${P2_},"<="&I{fr})',
              "fecha")
        celda(ws_p, f"L{fr}", f"=SUMIFS($C${P1_}:$C${P2_},$A${P1_}:$A${P2_},J{fr},$B${P1_}:$B${P2_},K{fr})", "unit")
        celda(ws_p, f"M{fr}", f'=IF(K{fr}<I{fr},"sí","no")')
PU2 = fr
PR_U = {k: rng("Precios", c, PU1, PU2) for k, c in (("fecha", "I"), ("ins", "J"), ("fcierre", "K"), ("precio", "L"))}
anchos(ws_p, {"A": 16, "B": 12, "C": 12, "D": 34, "E": 11, "F": 12, "G": 13, "H": 3, "I": 12, "J": 16, "K": 14,
              "L": 13, "M": 12})

# =====================================================================
# Tasas: semilla del CF107 (RF-30)
# =====================================================================
titulo(ws_ta, "Tasas de las subastas primarias de CETES (RF-30; tasa_referencia de 4.4)",
       "Fuente: Banco de México, SIE, cuadro CF107 (https://www.banxico.org.mx). Series de tasa SF43936, SF43939, "
       "SF43942, SF43945 y SF349785; de plazo SF43935, SF43938, SF43941, SF43944 y SF349778. Consulta: 15/10/2026. "
       "Fecha = colocación (D-02, R-14).")
encabezados(ws_ta, 4, ["plazo_nominal", "fecha_colocacion", "valor", "unidad", "plazo_efectivo", "fuente_nombre",
                       "carga", "serie de la tasa", "serie del plazo", "fuentes que coinciden (15/10/2026)",
                       "valuaciones de CETES que la usan"])
for i, r in enumerate(tasas):
    fr = TA1 + i
    celda(ws_ta, f"A{fr}", int(r["plazo_nominal"]), "int")
    celda(ws_ta, f"B{fr}", f(r["fecha_colocacion"]), "fecha")
    celda(ws_ta, f"C{fr}", float(r["valor"]), "tasa")
    ws_ta[f"C{fr}"].number_format = "0.00000"
    celda(ws_ta, f"D{fr}", r["unidad"])
    celda(ws_ta, f"E{fr}", int(r["plazo_efectivo"]), "int")
    celda(ws_ta, f"F{fr}", r["fuente_nombre"])
    celda(ws_ta, f"G{fr}", r["carga"])
    celda(ws_ta, f"H{fr}", r["serie_valor"])
    celda(ws_ta, f"I{fr}", r["serie_plazo"])
    celda(ws_ta, f"J{fr}", r["fuentes_coincidentes"])
TA = {c: rng("Tasas", c, TA1, TA2) for c in "ABCEFG"}
anchos(ws_ta, {"A": 9, "B": 12, "C": 10, "D": 16, "E": 9, "F": 16, "G": 10, "H": 10, "I": 10, "J": 70, "K": 14})

# =====================================================================
# CETES: valuacion por fecha y emision (RF-26b)
# =====================================================================
titulo(ws_c, "Valuación de CETES antes del vencimiento (RF-26b)",
       "Para cada plazo nominal rige la última colocación con fecha igual o anterior a la de valuación (F–J). "
       "Se interpola linealmente por plazo efectivo entre los dos nodos que encierran d; fuera del rango, la "
       "tasa del extremo. r sin redondear; P = ROUND(VN / (1 + r/100 × d/360); 7), mitad alejándose de cero.")
for c0, etiqueta in ((6, "Fecha de colocación vigente, por plazo nominal (días)"),
                     (11, "Tasa vigente (% anual)"), (16, "Plazo efectivo (días)")):
    ws_c.cell(row=3, column=c0, value=etiqueta).font = ENC
    ws_c.merge_cells(start_row=3, start_column=c0, end_row=3, end_column=c0 + 4)
encabezados(ws_c, 4, ["fecha", "instrumento_clave", "vencimiento", "valor nominal", "d (días por vencer)"])
for b in (6, 11, 16):
    for j, pn in enumerate((28, 91, 182, 364, 728)):
        c = ws_c.cell(row=4, column=b + j, value=pn)
        c.font = Font(name="Arial", size=10, color="808080", bold=True)
        c.fill = RELL_ENC
encabezados(ws_c, 4, ["plazo efectivo inferior", "plazo efectivo superior", "plazo nominal inferior",
                      "plazo nominal superior", "colocación inferior", "colocación superior", "tasa inferior",
                      "tasa superior", "caso", "r (% anual, sin redondear)", "P sin redondear",
                      "P (7 decimales)", "llave"], col0=21)
C1, C2 = 5, 4 + len(FILAS_CETES)
for i, (d, k) in enumerate(FILAS_CETES):
    r = C1 + i
    celda(ws_c, f"A{r}", d, "fecha", fuente=GRIS)
    celda(ws_c, f"B{r}", k, fuente=GRIS)
    celda(ws_c, f"C{r}", f"=INDEX({INS_VENC},MATCH(B{r},{INS_CLAVE},0))", "fecha")
    celda(ws_c, f"D{r}", f"=INDEX({INS_VN},MATCH(B{r},{INS_CLAVE},0))", "peso")
    celda(ws_c, f"E{r}", f"=C{r}-A{r}", "int")
    for j in range(5):
        cf, ct, cp = col(6 + j), col(11 + j), col(16 + j)
        celda(ws_c, f"{cf}{r}", f'=_xlfn.MAXIFS({TA["B"]},{TA["A"]},{cf}$4,{TA["B"]},"<="&$A{r})', "fecha")
        celda(ws_c, f"{ct}{r}", f"=SUMIFS({TA['C']},{TA['A']},{ct}$4,{TA['B']},{cf}{r})", "tasa")
        ws_c[f"{ct}{r}"].number_format = "0.00000"
        celda(ws_c, f"{cp}{r}", f"=SUMIFS({TA['E']},{TA['A']},{cp}$4,{TA['B']},{cf}{r})", "int")
    PE = f"$P{r}:$T{r}"
    celda(ws_c, f"U{r}", f'=IF($E{r}<=MIN({PE}),MIN({PE}),_xlfn.MAXIFS({PE},{PE},"<="&$E{r}))', "int")
    celda(ws_c, f"V{r}", f'=IF($E{r}>=MAX({PE}),MAX({PE}),_xlfn.MINIFS({PE},{PE},">="&$E{r}))', "int")
    celda(ws_c, f"W{r}", f"=INDEX($P$4:$T$4,MATCH(U{r},{PE},0))", "int")
    celda(ws_c, f"X{r}", f"=INDEX($P$4:$T$4,MATCH(V{r},{PE},0))", "int")
    celda(ws_c, f"Y{r}", f"=INDEX($F{r}:$J{r},MATCH(U{r},{PE},0))", "fecha")
    celda(ws_c, f"Z{r}", f"=INDEX($F{r}:$J{r},MATCH(V{r},{PE},0))", "fecha")
    celda(ws_c, f"AA{r}", f"=INDEX($K{r}:$O{r},MATCH(U{r},{PE},0))", "tasa")
    celda(ws_c, f"AB{r}", f"=INDEX($K{r}:$O{r},MATCH(V{r},{PE},0))", "tasa")
    ws_c[f"AA{r}"].number_format = ws_c[f"AB{r}"].number_format = "0.00000"
    celda(ws_c, f"AC{r}", f'=IF(E{r}<MIN({PE}),"extremo inferior",IF(E{r}>MAX({PE}),"extremo superior",'
                          f'IF(U{r}=V{r},"nodo","interpolación")))')
    celda(ws_c, f"AD{r}", f"=IF(U{r}=V{r},AA{r},AA{r}+(AB{r}-AA{r})*(E{r}-U{r})/(V{r}-U{r}))", "tasa")
    celda(ws_c, f"AE{r}", f"=D{r}/(1+AD{r}/100*E{r}/360)", "tasa")
    celda(ws_c, f"AF{r}", f"=ROUND(AE{r},7)", "p")
    celda(ws_c, f"AG{r}", f'=A{r}&"|"&B{r}')
CE = {c: rng("CETES", c, C1, C2) for c in ["A", "B", "E", "W", "X", "Y", "Z", "AA", "AC", "AD", "AF", "AG"]}
anchos(ws_c, {"A": 11, "B": 10, "C": 11, "D": 8, "E": 8, "U": 9, "V": 9, "W": 9, "X": 9, "Y": 11, "Z": 11,
              "AA": 9, "AB": 9, "AC": 16, "AD": 14, "AE": 14, "AF": 11, "AG": 16})
for j in range(15):
    ws_c.column_dimensions[col(6 + j)].width = 11 if j < 5 else 8

# columnas de Transacciones que dependen de CETES
for r in range(T1, T2 + 1):
    celda(ws_t, f"AA{r}", f'=IF(K{r}="cetes",SUMIFS({CE["AF"]},{CE["A"]},F{r},{CE["B"]},D{r}),"")', "p")
    celda(ws_t, f"AB{r}", f'=IF(K{r}="cetes",H{r}=AA{r},"")')
    celda(ws_t, f"AC{r}", f'=IF(K{r}="cetes",L{r}-F{r},"")', "int")
    celda(ws_t, f"AD{r}", f'=IF(E{r}="venta",I{r}<O{r},"")')
# en Tasas: cuantas valuaciones usan cada tasa
for fr in range(TA1, TA2 + 1):
    celda(ws_ta, f"K{fr}", f'=COUNTIFS({CE["Y"]},B{fr},{CE["W"]},A{fr})'
                           f'+COUNTIFS({CE["Z"]},B{fr},{CE["X"]},A{fr},{CE["AC"]},"interpolación")', "int")

# =====================================================================
# Valuacion diaria: cada dia natural x cada par (portafolio, instrumento, intermediario)
# =====================================================================
titulo(ws_v, "Valuación diaria por portafolio, instrumento e intermediario (RF-06, RF-08, RF-26a, RF-26b)",
       "A–D: rótulos de la fila. Títulos: suma de cantidades con signo hasta la fecha, inclusive (corte "
       "inclusivo); 0 desde el vencimiento. Costo unitario: el del kardex tras la última transacción del par. "
       "Precio: último cierre igual o anterior, o P de la hoja CETES. Q: liquidación al valor nominal el día "
       "del vencimiento (retiro, sin ISR).")
encabezados(ws_v, 4, ["fecha", "portafolio", "instrumento", "intermediario", "llave del par", "clase_activo",
                      "vencimiento", "valor nominal", "títulos", "orden de la última transacción",
                      "costo unitario promedio", "costo total", "fecha del precio", "precio usado (cierre o P)",
                      "valor de mercado", "resultado no realizado", "liquidación por vencimiento (retiro)",
                      "¿corte?", "llave de la fila"])
V1 = 5
r = V1 - 1
for d in DIAS:
    for (pt, k, it) in PARES:
        r += 1
        celda(ws_v, f"A{r}", d, "fecha", fuente=GRIS)
        celda(ws_v, f"B{r}", pt, fuente=GRIS)
        celda(ws_v, f"C{r}", k, fuente=GRIS)
        celda(ws_v, f"D{r}", it, fuente=GRIS)
        celda(ws_v, f"E{r}", f'=B{r}&"|"&C{r}&"|"&D{r}')
        celda(ws_v, f"F{r}", f"=INDEX({INS_CLASE},MATCH(C{r},{INS_CLAVE},0))")
        celda(ws_v, f"G{r}", f'=IF(F{r}="cetes",INDEX({INS_VENC},MATCH(C{r},{INS_CLAVE},0)),"")', "fecha")
        celda(ws_v, f"H{r}", f'=IF(F{r}="cetes",INDEX({INS_VN},MATCH(C{r},{INS_CLAVE},0)),"")', "peso")
        s = f'SUMIFS({R_T["N"]},{R_T["T"]},E{r},{R_T["F"]},"<="&A{r})'
        celda(ws_v, f"I{r}", f'=IF(F{r}="cetes",IF(A{r}>=G{r},0,{s}),{s})', "int")
        celda(ws_v, f"J{r}", f'=_xlfn.MAXIFS({R_T["U"]},{R_T["T"]},E{r},{R_T["F"]},"<="&A{r})', "int")
        celda(ws_v, f"K{r}", f'=IF(I{r}=0,0,INDEX({R_T["Z"]},MATCH(J{r},{R_T["U"]},0)))', "unit")
        celda(ws_v, f"L{r}", f"=I{r}*K{r}", "peso")
        hay = f'COUNTIFS({CE["A"]},A{r},{CE["B"]},C{r})'
        donde = f"{PR_U['fecha']},A{r},{PR_U['ins']},C{r}"
        celda(ws_v, f"M{r}", f'=IF(F{r}="cetes",IF({hay}=0,"",A{r}),SUMIFS({PR_U["fcierre"]},{donde}))', "fecha")
        celda(ws_v, f"N{r}", f'=IF(F{r}="cetes",IF({hay}=0,"",SUMIFS({CE["AF"]},{CE["A"]},A{r},{CE["B"]},C{r})),'
                             f'SUMIFS({PR_U["precio"]},{donde}))', "unit")
        celda(ws_v, f"O{r}", f"=IF(I{r}=0,0,I{r}*N{r})", "peso")
        celda(ws_v, f"P{r}", f"=O{r}-L{r}", "peso")
        celda(ws_v, f"Q{r}", f'=IF(F{r}="cetes",IF(A{r}=G{r},SUMIFS({R_T["N"]},{R_T["T"]},E{r},{R_T["F"]},"<"&A{r})*H{r},0),0)',
              "peso")
        celda(ws_v, f"R{r}", f'=IF(COUNTIF({rng("Entradas", "A", *R_CORTES)},A{r})>0,"sí","")')
        celda(ws_v, f"S{r}", f'=A{r}&"|"&E{r}')
V2 = r
VV = {c: rng(VD, c, V1, V2) for c in "ABEIKLMNOPQS"}

# Transacciones AE-AF: la cuadricula de Valuacion diaria cubre el par y la fecha de cada transaccion
for r in range(T1, T2 + 1):
    celda(ws_t, f"AE{r}", f"=SUMIFS({VV['I']},{VV['E']},T{r},{VV['A']},F{r})", "int")
    celda(ws_t, f"AF{r}", f'=AE{r}=SUMIFS($N${T1}:$N${T2},$T${T1}:$T${T2},T{r},$F${T1}:$F${T2},"<="&F{r})')
ws_t.column_dimensions["AE"].width = 12
ws_t.column_dimensions["AF"].width = 12
anchos(ws_v, {"A": 11, "B": 11, "C": 10, "D": 8, "E": 26, "F": 8, "G": 11, "H": 8, "I": 8, "J": 11, "K": 13,
              "L": 13, "M": 11, "N": 12, "O": 13, "P": 12, "Q": 13, "R": 7, "S": 32})
ws_v.freeze_panes = "E5"

# =====================================================================
# Serie diaria por portafolio (RF-09, RF-10, RF-11)
# =====================================================================
titulo(ws_s, "Serie diaria por día natural y portafolio (RF-09, RF-10, RF-11)",
       "V(t): valor al cierre de t. A(t): compras (títulos × precio + importe). R(t): ventas (títulos × precio − "
       "importe) y vencimientos (títulos × 10.00). r(t) = [V(t) + R(t)] / [V(t−1) + A(t)] − 1, y 0 si el "
       "denominador es 0. I(t) parte de 1 en el cierre base (10/09), que es el primer máximo.")
encabezados(ws_s, 4, ["fecha", "portafolio", "llave", "V(t) valor", "A(t) aportaciones", "R ventas",
                      "R vencimientos", "R(t) retiros", "V(t−1)", "denominador V(t−1) + A(t)",
                      "r(t) (fracción)", "r(t) (%)", "I(t) índice", "máximo acumulado", "caída I/máx − 1"])
S1 = 5
r = S1 - 1
for pt in ORD_PORT:
    for d in DIAS:
        r += 1
        base = f"A{r}={P['serie_inicio']}"
        celda(ws_s, f"A{r}", d, "fecha", fuente=GRIS)
        celda(ws_s, f"B{r}", pt, fuente=GRIS)
        celda(ws_s, f"C{r}", f'=A{r}&"|"&B{r}')
        celda(ws_s, f"D{r}", f"=SUMIFS({VV['O']},{VV['A']},A{r},{VV['B']},B{r})", "peso")
        celda(ws_s, f"E{r}", f"=SUMIFS({R_T['R']},{R_T['B']},B{r},{R_T['F']},A{r})", "peso")
        celda(ws_s, f"F{r}", f"=SUMIFS({R_T['S']},{R_T['B']},B{r},{R_T['F']},A{r})", "peso")
        celda(ws_s, f"G{r}", f"=SUMIFS({VV['Q']},{VV['A']},A{r},{VV['B']},B{r})", "peso")
        celda(ws_s, f"H{r}", f"=F{r}+G{r}", "peso")
        celda(ws_s, f"I{r}", f'=IF({base},"",D{r - 1})', "peso")
        celda(ws_s, f"J{r}", f'=IF({base},"",I{r}+E{r})', "peso")
        celda(ws_s, f"K{r}", f'=IF({base},"",IF(J{r}=0,0,(D{r}+H{r})/J{r}-1))', "frac")
        celda(ws_s, f"L{r}", f'=IF({base},"",K{r}*100)', "pct")
        celda(ws_s, f"M{r}", f"=IF({base},1,M{r - 1}*(1+K{r}))", "frac")
        celda(ws_s, f"N{r}", f"=IF({base},1,MAX(N{r - 1},M{r}))", "frac")
        celda(ws_s, f"O{r}", f"=M{r}/N{r}-1", "frac")
S2 = r
SS = {c: rng("Serie", c, S1, S2) for c in "ABCDHKM"}
anchos(ws_s, {"A": 11, "B": 11, "C": 18, "D": 14, "E": 13, "F": 12, "G": 13, "H": 12, "I": 14, "J": 14,
              "K": 17, "L": 15, "M": 16, "N": 16, "O": 17})
ws_s.freeze_panes = "C5"

# =====================================================================
# Periodos: TWR y maxima caida por periodo (RF-09, RF-10)
# =====================================================================
titulo(ws_pe, "TWR y máxima caída por periodo (RF-09, RF-10)",
       "Cada bloque toma r(t) de la Serie. I = 1 en el cierre previo al inicio (primer máximo). TWR = Π(1 + r) − 1, "
       "sin anualizar, por dos caminos (índice final y PRODUCT); T lo recalcula con la Serie y las fechas de "
       "Entradas. Máxima caída = mín(I/máx) − 1. Pico: la primera fecha, contando la fecha base con I = 1, en que "
       "I alcanzó el máximo vigente en el valle (con empates, la más antigua). Valle: la primera fecha con la "
       "caída mínima. Los bloques tienen un largo fijo: cambiar inicio o fin exige regenerar el libro.")
encabezados(ws_pe, 4, ["periodo", "portafolio", "inicio", "fin", "fecha base (cierre previo)", "días",
                       "V base", "V fin", "costo total al fin", "resultado no realizado al fin",
                       "TWR (índice final − 1)", "TWR (PRODUCT − 1)", "TWR (%)", "máxima caída (fracción)",
                       "máxima caída (%)", "fecha del valle", "máximo vigente en el valle", "fecha del pico",
                       "|diferencia entre los dos TWR|", "TWR por la Serie: I(fin) / I(base) − 1"])
PE1 = 5
PE2 = PE1 + len(periodos) - 1
fila_bloque = PE2 + 3
BLOQUES = {}
for i, per in enumerate(periodos):
    s = PE1 + i
    fe = FILA_PERIODO[per["periodo"]]
    ini, fin = f(per["inicio"]), f(per["fin"])
    n = (fin - ini).days + 1
    ws_pe.cell(row=fila_bloque, column=1, value=f"Periodo {per['periodo']}").font = SEC
    encabezados(ws_pe, fila_bloque + 1, ["fecha", "r(t)", "1 + r(t)", "I(t)", "máximo (con I = 1 inicial)",
                                         "caída I/máx − 1"])
    b1, b2 = fila_bloque + 2, fila_bloque + 1 + n
    for k in range(n):
        r = b1 + k
        celda(ws_pe, f"A{r}", f"=$C${s}" if k == 0 else f"=A{r - 1}+1", "fecha")
        celda(ws_pe, f"B{r}", f'=INDEX({SS["K"]},MATCH(A{r}&"|"&$B${s},{SS["C"]},0))', "frac")
        celda(ws_pe, f"C{r}", f"=1+B{r}", "frac")
        celda(ws_pe, f"D{r}", f"=C{r}" if k == 0 else f"=D{r - 1}*C{r}", "frac")
        celda(ws_pe, f"E{r}", f"=MAX(1,D{r})" if k == 0 else f"=MAX(E{r - 1},D{r})", "frac")
        celda(ws_pe, f"F{r}", f"=D{r}/E{r}-1", "frac")
    BLOQUES[per["periodo"]] = (b1, b2)
    celda(ws_pe, f"A{s}", f"=Entradas!$A${fe}")
    celda(ws_pe, f"B{s}", f"=Entradas!$B${fe}")
    celda(ws_pe, f"C{s}", f"=Entradas!$C${fe}", "fecha")
    celda(ws_pe, f"D{s}", f"=Entradas!$D${fe}", "fecha")
    celda(ws_pe, f"E{s}", f"=C{s}-1", "fecha")
    celda(ws_pe, f"F{s}", f"=D{s}-C{s}+1", "int")
    celda(ws_pe, f"G{s}", f"=SUMIFS({SS['D']},{SS['A']},E{s},{SS['B']},B{s})", "peso")
    celda(ws_pe, f"H{s}", f"=SUMIFS({SS['D']},{SS['A']},D{s},{SS['B']},B{s})", "peso")
    celda(ws_pe, f"I{s}", f"=SUMIFS({VV['L']},{VV['A']},D{s},{VV['B']},B{s})", "peso")
    celda(ws_pe, f"J{s}", f"=SUMIFS({VV['P']},{VV['A']},D{s},{VV['B']},B{s})", "peso")
    celda(ws_pe, f"K{s}", f"=D{b2}-1", "frac")
    celda(ws_pe, f"L{s}", f"=PRODUCT(C{b1}:C{b2})-1", "frac")
    celda(ws_pe, f"M{s}", f"=K{s}*100", "pct")
    celda(ws_pe, f"N{s}", f"=MIN(F{b1}:F{b2})", "frac")
    celda(ws_pe, f"O{s}", f"=N{s}*100", "pct")
    celda(ws_pe, f"P{s}", f'=IF(N{s}=0,"",INDEX(A{b1}:A{b2},MATCH(N{s},F{b1}:F{b2},0)))', "fecha")
    celda(ws_pe, f"Q{s}", f'=IF(N{s}=0,"",INDEX(E{b1}:E{b2},MATCH(N{s},F{b1}:F{b2},0)))', "frac")
    celda(ws_pe, f"R{s}", f'=IF(N{s}=0,"",IF(Q{s}=1,E{s},INDEX(A{b1}:A{b2},MATCH(Q{s},D{b1}:D{b2},0))))', "fecha")
    celda(ws_pe, f"S{s}", f"=ABS(K{s}-L{s})", "frac")
    celda(ws_pe, f"T{s}", f'=INDEX({SS["M"]},MATCH(D{s}&"|"&B{s},{SS["C"]},0))/'
                          f'INDEX({SS["M"]},MATCH(E{s}&"|"&B{s},{SS["C"]},0))-1', "frac")
    fila_bloque = b2 + 3
FILA_PER_RES = {per["periodo"]: PE1 + i for i, per in enumerate(periodos)}
anchos(ws_pe, {"A": 12, "B": 16, "C": 16, "D": 16, "E": 16, "F": 16, "G": 14, "H": 14, "I": 14, "J": 14,
               "K": 17, "L": 17, "M": 15, "N": 17, "O": 15, "P": 12, "Q": 16, "R": 12, "S": 14, "T": 17})

# =====================================================================
# Posiciones en cada corte (RF-06, RF-08, RF-26b, RF-31)
# =====================================================================
titulo(ws_po, "Posiciones en cada fecha de corte (RF-06, RF-08, RF-26b, RF-31)",
       "Tres tablas: por intermediario (cada par portafolio-instrumento-intermediario), consolidado por "
       "instrumento (suma de intermediarios) y totales del portafolio, comparados con V(t) de la Serie. "
       "Se incluyen los renglones en cero.")
ws_po.cell(row=3, column=1, value="Por intermediario").font = SEC
encabezados(ws_po, 4, ["fecha_corte", "portafolio", "instrumento", "intermediario", "fila en Valuación diaria",
                       "¿tiene transacciones al corte?", "títulos", "costo unitario promedio", "costo total",
                       "precio usado", "fecha del precio (cierre usado)", "¿hay valuación de CETES?",
                       "d", "r (% anual)", "colocación inferior", "colocación superior", "valor de mercado",
                       "resultado no realizado"])
PO1 = 5
r = PO1 - 1
for c in cortes:
    for (pt, k, it) in PARES:
        r += 1
        celda(ws_po, f"A{r}", f(c["fecha_corte"]), "fecha", fuente=GRIS)
        celda(ws_po, f"B{r}", pt, fuente=GRIS)
        celda(ws_po, f"C{r}", k, fuente=GRIS)
        celda(ws_po, f"D{r}", it, fuente=GRIS)
        celda(ws_po, f"E{r}", f'=MATCH(A{r}&"|"&B{r}&"|"&C{r}&"|"&D{r},{VV["S"]},0)', "int")
        celda(ws_po, f"F{r}", f'=IF(COUNTIFS({R_T["T"]},B{r}&"|"&C{r}&"|"&D{r},{R_T["F"]},"<="&A{r})>0,"sí","no")')
        celda(ws_po, f"G{r}", f"=INDEX({VV['I']},E{r})", "int")
        celda(ws_po, f"H{r}", f"=INDEX({VV['K']},E{r})", "unit")
        celda(ws_po, f"I{r}", f"=INDEX({VV['L']},E{r})", "peso")
        celda(ws_po, f"J{r}", f"=INDEX({VV['N']},E{r})", "unit")
        celda(ws_po, f"K{r}", f"=INDEX({VV['M']},E{r})", "fecha")
        celda(ws_po, f"L{r}", f'=COUNTIFS({CE["A"]},A{r},{CE["B"]},C{r})', "int")
        m = f'MATCH(A{r}&"|"&C{r},{CE["AG"]},0)'
        celda(ws_po, f"M{r}", f'=IF(L{r}=0,"",INDEX({CE["E"]},{m}))', "int")
        celda(ws_po, f"N{r}", f'=IF(L{r}=0,"",INDEX({CE["AD"]},{m}))', "tasa")
        celda(ws_po, f"O{r}", f'=IF(L{r}=0,"",INDEX({CE["Y"]},{m}))', "fecha")
        celda(ws_po, f"P{r}", f'=IF(L{r}=0,"",INDEX({CE["Z"]},{m}))', "fecha")
        celda(ws_po, f"Q{r}", f"=INDEX({VV['O']},E{r})", "peso")
        celda(ws_po, f"R{r}", f"=INDEX({VV['P']},E{r})", "peso")
PO2 = r
PO = {c: rng("Posiciones", c, PO1, PO2) for c in "ABCGIQR"}

fila = PO2 + 3
ws_po.cell(row=fila - 1, column=1, value="Consolidado por instrumento (suma de intermediarios)").font = SEC
encabezados(ws_po, fila, ["fecha_corte", "portafolio", "instrumento", "títulos", "costo total", "valor de mercado",
                          "resultado no realizado", "intermediarios con saldo"])
PI1 = fila + 1
CONSOL = []
for c in cortes:
    for pt in ORD_PORT:
        for k in ORD_INS:
            if any(p[0] == pt and p[1] == k for p in PARES):
                fila += 1
                CONSOL.append(fila)
                celda(ws_po, f"A{fila}", f(c["fecha_corte"]), "fecha", fuente=GRIS)
                celda(ws_po, f"B{fila}", pt, fuente=GRIS)
                celda(ws_po, f"C{fila}", k, fuente=GRIS)
                cond = f"{PO['A']},A{fila},{PO['B']},B{fila},{PO['C']},C{fila}"
                celda(ws_po, f"D{fila}", f"=SUMIFS({PO['G']},{cond})", "int")
                celda(ws_po, f"E{fila}", f"=SUMIFS({PO['I']},{cond})", "peso")
                celda(ws_po, f"F{fila}", f"=SUMIFS({PO['Q']},{cond})", "peso")
                celda(ws_po, f"G{fila}", f"=SUMIFS({PO['R']},{cond})", "peso")
                celda(ws_po, f"H{fila}", f'=COUNTIFS({cond},{PO["G"]},">0")', "int")
PI2 = fila
PIr = {c: rng("Posiciones", c, PI1, PI2) for c in "ABCDF"}

fila += 3
ws_po.cell(row=fila - 1, column=1, value="Totales del portafolio (comprobación: suma por intermediario = suma consolidada = V(t) de la Serie)").font = SEC
encabezados(ws_po, fila, ["fecha_corte", "portafolio", "costo total", "valor (suma por intermediario)",
                          "resultado no realizado", "valor (suma consolidada)", "V(t) de la Serie", "¿iguales?"])
PT1 = fila + 1
for c in cortes:
    for pt in ORD_PORT:
        fila += 1
        celda(ws_po, f"A{fila}", f(c["fecha_corte"]), "fecha", fuente=GRIS)
        celda(ws_po, f"B{fila}", pt, fuente=GRIS)
        cond = f"{PO['A']},A{fila},{PO['B']},B{fila}"
        celda(ws_po, f"C{fila}", f"=SUMIFS({PO['I']},{cond})", "peso")
        celda(ws_po, f"D{fila}", f"=SUMIFS({PO['Q']},{cond})", "peso")
        celda(ws_po, f"E{fila}", f"=SUMIFS({PO['R']},{cond})", "peso")
        celda(ws_po, f"F{fila}", f"=SUMIFS({PIr['F']},{PIr['A']},A{fila},{PIr['B']},B{fila})", "peso")
        celda(ws_po, f"G{fila}", f"=SUMIFS({SS['D']},{SS['A']},A{fila},{SS['B']},B{fila})", "peso")
        celda(ws_po, f"H{fila}", f"=AND(ABS(D{fila}-F{fila})<1E-9,ABS(D{fila}-G{fila})<1E-9)")
PT2 = fila
anchos(ws_po, {"A": 12, "B": 12, "C": 13, "D": 14, "E": 14, "F": 14, "G": 14, "H": 14, "I": 14, "J": 12, "K": 13,
               "L": 10, "M": 6, "N": 14, "O": 12, "P": 12, "Q": 14, "R": 14})

# =====================================================================
# Rechazos (RF-28, RF-26a crit. 2, RF-05 crit. 3, RF-09 crit. 3) y caso positivo C1
# =====================================================================
titulo(ws_r, "Rechazos esperados (RF-28, RF-26a, RF-05, RF-09) y caso positivo C1",
       "A–N: candidatos (entradas/candidatos_rechazo.csv), que se intentan registrar después de T01 a T16. "
       "S: saldo del par al cierre del día del candidato; T–AI: saldo al cierre de la fecha de cada transacción "
       "posterior del mismo par (fila 3), con el candidato. La regla se aplica en orden: intervalo, vencimiento, "
       "saldo negativo (RF-28, en cualquier fecha, compras antes que ventas).")
INI, FIN = P["intervalo_semillas_inicio"], P["intervalo_semillas_fin"]
R_ENC = ["id", "criterio", "caso", "portafolio_nombre", "intermediario_nombre", "instrumento_clave", "tipo",
         "fecha_concertacion", "cantidad", "precio", "importe_comisiones", "periodo_inicio", "periodo_fin",
         "motivo_esperado", "llave del par", "cantidad con signo", "¿fuera del intervalo de las semillas?",
         "¿CETES en o después del vencimiento?", "saldo al cierre del día del candidato"]
encabezados(ws_r, 4, R_ENC)
H1C = 20                                       # columna T: primera auxiliar
HCOLS = [col(H1C + j) for j in range(len(txs))]
HA, HZ = HCOLS[0], HCOLS[-1]
ws_r.cell(row=3, column=H1C - 1, value="fecha de la transacción →").font = NOTA
for j, hc in enumerate(HCOLS):
    celda(ws_r, f"{hc}3", f"=Transacciones!$F${T1 + j}", "fecha")
    celda(ws_r, f"{hc}4", f"=Transacciones!$A${T1 + j}", fuente=ENC)
    ws_r[f"{hc}4"].fill = RELL_ENC
    ws_r.column_dimensions[hc].width = 11
c_min, c_fneg, c_regla, c_res, c_fecha, c_saldo = (col(H1C + len(txs) + k) for k in range(6))
encabezados(ws_r, 4, ["saldo mínimo", "primera fecha con saldo negativo", "regla", "resultado_esperado",
                      "fecha_saldo_negativo", "saldo_resultante"], col0=H1C + len(txs))
RJ1 = 5
N_ = R_T["N"]
for i, cnd in enumerate(candidatos):
    r = RJ1 + i
    celda(ws_r, f"A{r}", cnd["id"])
    celda(ws_r, f"B{r}", cnd["criterio"])
    celda(ws_r, f"C{r}", cnd["caso"])
    celda(ws_r, f"D{r}", cnd["portafolio_nombre"])
    if cnd["caso"] == "transaccion":
        celda(ws_r, f"E{r}", cnd["intermediario_nombre"])
        celda(ws_r, f"F{r}", cnd["instrumento_clave"])
        celda(ws_r, f"G{r}", cnd["tipo"])
        celda(ws_r, f"H{r}", f(cnd["fecha_concertacion"]), "fecha")
        celda(ws_r, f"I{r}", int(cnd["cantidad"]), "int")
        celda(ws_r, f"J{r}", float(cnd["precio"]), "unit")
        celda(ws_r, f"K{r}", float(cnd["importe_comisiones"]), "peso")
    else:
        celda(ws_r, f"L{r}", f(cnd["periodo_inicio"]), "fecha")
        celda(ws_r, f"M{r}", f(cnd["periodo_fin"]), "fecha")
    celda(ws_r, f"N{r}", cnd["motivo_esperado"])
    es_tx = f'$C{r}="transaccion"'
    celda(ws_r, f"O{r}", f'=IF({es_tx},D{r}&"|"&F{r}&"|"&E{r},"")')
    celda(ws_r, f"P{r}", f'=IF({es_tx},IF(G{r}="compra",1,-1)*I{r},"")', "int")
    celda(ws_r, f"Q{r}", f'=IF({es_tx},OR(H{r}<{INI},H{r}>{FIN}),"")')
    celda(ws_r, f"R{r}", f'=IF({es_tx},AND(INDEX({INS_CLASE},MATCH(F{r},{INS_CLAVE},0))="cetes",'
                         f'H{r}>=INDEX({INS_VENC},MATCH(F{r},{INS_CLAVE},0))),"")')
    celda(ws_r, f"S{r}", f'=IF({es_tx},SUMIFS({N_},{R_T["T"]},O{r},{R_T["F"]},"<="&H{r})+P{r},"")', "int")
    for j, hc in enumerate(HCOLS):
        tr = T1 + j
        celda(ws_r, f"{hc}{r}", f'=IF($C{r}<>"transaccion","",IF(AND(Transacciones!$T${tr}=$O{r},'
                                f'Transacciones!$F${tr}>$H{r}),SUMIFS({N_},{R_T["T"]},$O{r},{R_T["F"]},'
                                f'"<="&Transacciones!$F${tr})+$P{r},""))', "int")
    celda(ws_r, f"{c_min}{r}", f'=IF({es_tx},MIN(S{r},{HA}{r}:{HZ}{r}),"")', "int")
    celda(ws_r, f"{c_fneg}{r}", f'=IF($C{r}<>"transaccion","",IF(S{r}<0,H{r},IF({c_min}{r}<0,'
                                f'_xlfn.MINIFS(${HA}$3:${HZ}$3,{HA}{r}:{HZ}{r},"<0"),"")))', "fecha")
    celda(ws_r, f"{c_regla}{r}",
          f'=IF($C{r}="periodo",IF(M{r}<L{r},"criterio 3 de RF-09: fecha final anterior a la inicial",'
          f'IF(OR(L{r}-1<{INI},M{r}>{FIN}),"criterio 3 de RF-09: fechas fuera de las semillas","")),'
          f'IF(Q{r},"RD-07 y criterio 3 de RF-05: fecha fuera del intervalo de las semillas",'
          f'IF(R{r},"criterio 2 de RF-26a: fecha igual o posterior al vencimiento de la emision",'
          f'IF({c_min}{r}<0,"RF-28: deja negativo el saldo del instrumento con el intermediario dentro del '
          f'portafolio",""))))')
    celda(ws_r, f"{c_res}{r}", f'=IF({c_regla}{r}="","aceptar","rechazar")')
    celda(ws_r, f"{c_fecha}{r}", f'=IF(LEFT({c_regla}{r},5)="RF-28",{c_fneg}{r},"")', "fecha")
    celda(ws_r, f"{c_saldo}{r}", f'=IF(LEFT({c_regla}{r},5)="RF-28",SUMIFS({N_},{R_T["T"]},O{r},{R_T["F"]},'
                                 f'"<="&{c_fneg}{r})+P{r},"")', "int")
RJ2 = RJ1 + len(candidatos) - 1

# caso positivo C1: T11 y T12 (ya cargadas) se aceptan porque las compras van antes que las ventas
fila = RJ2 + 3
ws_r.cell(row=fila, column=1, value="Caso positivo C1 (casos_positivos.csv): compras antes que ventas el mismo día").font = SEC
fila += 1
encabezados(ws_r, fila, ["id", "criterio", "refs", "portafolio_nombre", "intermediario_nombre", "instrumento_clave",
                         "fecha_concertacion", "regla", "llave del par", "saldo_previo", "compras_del_dia",
                         "ventas_del_dia", "saldo_resultante", "saldo_si_ventas_antes_que_compras",
                         "resultado_esperado"])
fila += 1
C1R = fila
celda(ws_r, f"A{fila}", "C1")
celda(ws_r, f"B{fila}", "RF-08 crit. 3 y RF-28 (caso positivo)")
celda(ws_r, f"C{fila}", "T11 y T12")
m11 = f'MATCH(LEFT(C{fila},3),{R_T["A"]},0)'
celda(ws_r, f"D{fila}", f"=INDEX({R_T['B']},{m11})")
celda(ws_r, f"E{fila}", f"=INDEX({R_T['C']},{m11})")
celda(ws_r, f"F{fila}", f"=INDEX({R_T['D']},{m11})")
celda(ws_r, f"G{fila}", f"=INDEX({R_T['F']},{m11})", "fecha")
celda(ws_r, f"H{fila}", "compras antes que ventas el mismo dia")
celda(ws_r, f"I{fila}", f'=D{fila}&"|"&F{fila}&"|"&E{fila}')
celda(ws_r, f"J{fila}", f'=SUMIFS({N_},{R_T["T"]},I{fila},{R_T["F"]},"<"&G{fila})', "int")
celda(ws_r, f"K{fila}", f'=SUMIFS({R_T["G"]},{R_T["T"]},I{fila},{R_T["F"]},G{fila},{R_T["E"]},"compra")', "int")
celda(ws_r, f"L{fila}", f'=SUMIFS({R_T["G"]},{R_T["T"]},I{fila},{R_T["F"]},G{fila},{R_T["E"]},"venta")', "int")
celda(ws_r, f"M{fila}", f"=J{fila}+K{fila}-L{fila}", "int")
celda(ws_r, f"N{fila}", f"=J{fila}-L{fila}", "int")
celda(ws_r, f"O{fila}", f'=IF(AND(MIN({R_T["W"]})>=0,MIN({VV["I"]})>=0,M{fila}>=0),"aceptar","rechazar")')
anchos(ws_r, {"A": 6, "B": 22, "C": 12, "D": 12, "E": 12, "F": 12, "G": 9, "H": 12, "I": 9, "J": 10, "K": 10,
              "L": 12, "M": 12, "N": 40, "O": 24, "P": 10, "Q": 12, "R": 12, "S": 12})
for c_ in (c_min, c_fneg, c_res, c_fecha, c_saldo):
    ws_r.column_dimensions[c_].width = 12
ws_r.column_dimensions[c_regla].width = 50
ws_r.freeze_panes = "B5"

# =====================================================================
# Comprobaciones por dos caminos (escenario, 7 f) y de las entradas
# =====================================================================
titulo(ws_co, "Comprobaciones",
       "Cada renglón compara una cifra del libro con otro camino (fórmula cerrada sobre las entradas) o comprueba "
       "una regla de las entradas. VERDADERO = se cumple.")
encabezados(ws_co, 4, ["n.º", "comprobación", "resultado", "valor del libro", "valor por otro camino",
                       "diferencia", "origen"])


def per(pid, colname):
    return f"Periodos!${colname}${FILA_PER_RES[pid]}"


def cierre(clave, fecha_ref):
    return f'SUMIFS({rng("Precios", "C", P1_, P2_)},{rng("Precios", "A", P1_, P2_)},"{clave}",{rng("Precios", "B", P1_, P2_)},{fecha_ref})'


def tx(ref, c):
    return f'INDEX({R_T[c]},MATCH("{ref}",{R_T["A"]},0))'


fila_corte = {c["fecha_corte"]: R_CORTES[0] + i for i, c in enumerate(cortes)}
CHK = []


def chk(texto, resultado, libro="", otro="", dif="", origen=""):
    CHK.append((texto, resultado, libro, otro, dif, origen))


chk("Encadenamiento: (1 + TWR P1-B)(1 + TWR P1-C) = 1 + TWR P1-A", "=ABS(F{r})<1E-12",
    f"=(1+{per('P1-B', 'K')})*(1+{per('P1-C', 'K')})", f"=1+{per('P1-A', 'K')}", "=D{r}-E{r}", "RF-09; escenario 7 f")
chk("TWR P2-A = 150 × cierre(14/10) / (150 × 103.60 + 45.07) − 1", "=ABS(F{r})<1E-12", f"={per('P2-A', 'K')}",
    f"={tx('T07', 'G')}*{cierre('DEMOACC', per('P2-A', 'D'))}/({tx('T07', 'G')}*{tx('T07', 'H')}+{tx('T07', 'I')})-1",
    "=D{r}-E{r}", "RF-09 crit. 2; factor 1 con denominador 0")
chk("TWR P2-C = cierre(14/10) / cierre(30/09) − 1 (sin flujos)", "=ABS(F{r})<1E-12", f"={per('P2-C', 'K')}",
    f"={cierre('DEMOACC', per('P2-C', 'D'))}/{cierre('DEMOACC', per('P2-C', 'E'))}-1", "=D{r}-E{r}", "RF-09 crit. 1")
chk("Máxima caída P2-C = cierre(05/10) / cierre(30/09) − 1", "=ABS(F{r})<1E-12", f"={per('P2-C', 'N')}",
    f"={cierre('DEMOACC', per('P2-C', 'P'))}/{cierre('DEMOACC', per('P2-C', 'E'))}-1", "=D{r}-E{r}",
    "RF-10; el máximo es el I = 1 inicial")
chk("Máxima caída P2-A = 90.4250 / 104.75 − 1 (pico 15/09, valle 23/09)", "=ABS(F{r})<1E-12",
    f"={per('P2-A', 'N')}", f"={cierre('DEMOACC', per('P2-A', 'P'))}/{cierre('DEMOACC', per('P2-A', 'R'))}-1",
    "=D{r}-E{r}", "RF-10 crit. 2: la caída medida es la de los precios")
chk("Pico de P2-A el 15/09 (primera fecha del máximo; I(16/09) empata porque el 16/09 no hay cierre)", f"={per('P2-A', 'R')}=DATE(2026,9,15)", f"={per('P2-A', 'R')}", "", "", "escenario 7 f")
chk("Valle de P2-A el 23/09", f"={per('P2-A', 'P')}=DATE(2026,9,23)", f"={per('P2-A', 'P')}", "", "", "escenario 7 f")
chk("Cada corte: suma por intermediario = suma consolidada = V(t) de la Serie",
    f"=AND({rng('Posiciones', 'H', PT1, PT2)})", "", "", "", "RF-06 crit. 3; RF-11 crit. 2; RNF-02")
chk("Días de compra de CETES (y T13): precio de la transacción = P de RF-26b de ese día",
    f"=AND({rng('Transacciones', 'AB', T1, T2)})", "", "", "", "RF-26b; P a 7 decimales")
chk("T13: precio = P(01/10, BI261008)", f"={tx('T13', 'H')}=SUMIFS({CE['AF']},{CE['A']},{tx('T13', 'F')},{CE['B']},\"BI261008\")",
    f"={tx('T13', 'H')}", f"=SUMIFS({CE['AF']},{CE['A']},{tx('T13', 'F')},{CE['B']},\"BI261008\")", "=D{r}-E{r}",
    "venta secundaria al P del día")
chk("R(08/10) de Principal = 20,000.00 exactos (2,000 × 10.00, sin ISR)", "=D{r}=E{r}",
    f'=SUMIFS({SS["H"]},{SS["A"]},Entradas!$A${fila_corte["2026-10-08"]},{SS["B"]},"Principal")', "=2000*10",
    "=D{r}-E{r}", "RF-26a crit. 1; S-14")
chk("RF-28: ningún saldo negativo tras cada transacción (orden compras antes que ventas)",
    f"=MIN({rng('Transacciones', 'W', T1, T2)})>=0", f"=MIN({rng('Transacciones', 'W', T1, T2)})", "", "", "RF-28; X-04")
chk("RF-28: ningún saldo negativo al cierre de ningún día natural", f"=MIN({VV['I']})>=0", f"=MIN({VV['I']})", "", "",
    "RF-28 crit. 2")
chk("Transacciones en orden creciente (requisito del kardex)",
    f"=SUMPRODUCT(--({rng('Transacciones', 'U', T1 + 1, T2)}<={rng('Transacciones', 'U', T1, T2 - 1)}))=0",
    "", "", "", "estructura de la hoja")
COLOC = f"CETES!$F${C1}:$J${C2}"
chk("Cada valuación de CETES tiene colocación vigente en los cinco plazos", f"=MIN({COLOC})>0",
    "", "", "", "RF-30 crit. 1")
chk("Ninguna valuación usa una colocación posterior a su fecha (R-14)",
    f"=SUMPRODUCT(--({CE['Y']}>{CE['A']}))+SUMPRODUCT(--({CE['Z']}>{CE['A']}))=0", "", "", "",
    "RF-26b crit. 3; R-14")
chk("La colocación del 15/10 no rige ninguna valuación", f"=COUNTIF({COLOC},DATE(2026,10,15))=0",
    "", "", "", "R-14")
chk("07/10 BI261008 (d = 1) usa la tasa a 28 días del 01/10 (6.01), no la del 08/10",
    f'=AND(INDEX({CE["Y"]},MATCH(DATE(2026,10,7)&"|BI261008",{CE["AG"]},0))=DATE(2026,10,1),'
    f'INDEX({CE["AA"]},MATCH(DATE(2026,10,7)&"|BI261008",{CE["AG"]},0))=6.01)', "", "", "", "RF-26b crit. 3")
chk("Precios solo en días con operaciones de 2026", f"=AND({rng('Precios', 'G', P1_, P2_)})", "", "", "",
    "RF-07 crit. 2; DOF 10/12/2025")
chk("Precios de cierre con 7 decimales o menos",
    f"=SUMPRODUCT(--(ABS({rng('Precios', 'C', P1_, P2_)}*10^7-ROUND({rng('Precios', 'C', P1_, P2_)}*10^7,0))>1E-6))=0",
    "", "", "", "RD-13")
chk("Precios de transacción con 7 decimales o menos e importes con 2 o menos",
    f"=SUMPRODUCT(--(ABS({R_T['H']}*10^7-ROUND({R_T['H']}*10^7,0))>1E-6))+"
    f"SUMPRODUCT(--(ABS({R_T['I']}*100-ROUND({R_T['I']}*100,0))>1E-6))=0", "", "", "", "RD-13; RF-05")
chk("Tasas con 5 decimales o menos", f"=SUMPRODUCT(--(ABS({TA['C']}*10^5-ROUND({TA['C']}*10^5,0))>1E-6))=0",
    "", "", "", "RD-13")
chk("Claves: CETES = BI + vencimiento AAMMDD; las demás no tienen esa forma", f"=AND({rng('Entradas', 'H', *R_INS)})",
    "", "", "", "RF-04; RD-04")
chk("Marca de demostración si y solo si no es CETES", f"=AND({rng('Entradas', 'I', *R_INS)})", "", "", "",
    "RF-04 crit. 3")
chk("Transacciones de CETES antes del vencimiento y a 728 días o menos",
    f"=SUMPRODUCT(({R_T['K']}=\"cetes\")*(({rng('Transacciones', 'AC', T1, T2)}<1)+({rng('Transacciones', 'AC', T1, T2)}>728)))=0",
    "", "", "", "RF-26a crit. 2; RD-05")
chk("Ventas con importe menor que títulos × precio", f"=AND({rng('Transacciones', 'AD', T1, T2)})", "", "", "",
    "RF-05 crit. 2")
chk("Transacciones dentro del intervalo de las semillas",
    f"=COUNTIFS({R_T['F']},\"<\"&{P['intervalo_semillas_inicio']})+COUNTIFS({R_T['F']},\">\"&{P['intervalo_semillas_fin']})=0",
    "", "", "", "RD-07; S-09")
chk("Cada plazo de la semilla de tasas empieza con una colocación anterior al intervalo",
    "=AND(" + ",".join(f"COUNTIFS({TA['A']},{pn},{TA['B']},\"<\"&{P['intervalo_semillas_inicio']})>0"
                       for pn in (28, 91, 182, 364, 728)) + ")", "", "", "", "RF-30 crit. 1; P-14")
r_p2 = S1 + len(DIAS)   # fila del cierre base (10/09) del Secundario
chk("P2: r = 0 del 11/09 al 13/09 (denominador 0, factor 1)",
    f"=AND(Serie!K{r_p2 + 1}=0,Serie!K{r_p2 + 2}=0,Serie!K{r_p2 + 3}=0)", "", "", "", "RF-09 (recomendado)")
chk("Serie de Principal: I(fin de P1-A) − 1 = TWR de P1-A en Periodos", "=ABS(F{r})<1E-12",
    f"=INDEX({SS['M']},MATCH({per('P1-A', 'D')}&\"|Principal\",{SS['C']},0))-1", f"={per('P1-A', 'K')}",
    "=D{r}-E{r}", "RF-11 crit. 2")
chk("P1-D no baja: máxima caída = 0", f"={per('P1-D', 'N')}=0", f"={per('P1-D', 'N')}", "", "", "RF-10 crit. 2")
chk("Forma esperada de P1-A: pico 16/09 (festivo) y valle 23/09",
    f"=AND({per('P1-A', 'R')}=DATE(2026,9,16),{per('P1-A', 'P')}=DATE(2026,9,23))", "", "", "",
    "escenario 7 h (orden de magnitud, no es cifra)")
chk("16/09: DEMOACC en Principal = 300 (200 Casa A + 100 Casa B), no 450",
    f'=SUMIFS({PIr["D"]},{PIr["A"]},Entradas!$A${fila_corte["2026-09-16"]},{PIr["B"]},"Principal",{PIr["C"]},"DEMOACC")=300',
    "", "", "", "RF-06 crit. 1 y 3; X-06")
chk("08/10: posición de BI261008 = 0 desde su vencimiento",
    f'=SUMIFS({PIr["D"]},{PIr["A"]},Entradas!$A${fila_corte["2026-10-08"]},{PIr["B"]},"Principal",{PIr["C"]},"BI261008")=0',
    "", "", "", "RF-26a crit. 1")
chk("Redondeo de Excel: ROUND(−0.125; 2) = −0.13 (mitad alejándose de cero)", "=ROUND(-0.125,2)=-0.13",
    "=ROUND(-0.125,2)", "", "", "RD-16; P-13")
chk("Redondeo de Excel: criterio 1 de RF-26b, P = 9.9027626",
    "=ROUND(10/(1+7.0698412698/100*50/360),7)=9.9027626", "=ROUND(10/(1+7.0698412698/100*50/360),7)", "", "",
    "RF-26b crit. 1")
FIN_BLOQUE = ",".join(f"Periodos!$A${BLOQUES[p_['periodo']][1]}={per(p_['periodo'], 'D')}" for p_ in periodos)
chk("Cada bloque diario de Periodos termina en el fin del periodo (si se cambia un fin en Entradas, hay que regenerar)",
    f"=AND({FIN_BLOQUE})", "", "", "", "estructura de la hoja")
chk("TWR del bloque = TWR por la Serie con las fechas de Entradas (I(fin) / I(base) − 1), en los seis periodos (libro: suma de |K − T|)",
    f"=SUMPRODUCT(--(ABS(Periodos!$K${PE1}:$K${PE2}-Periodos!$T${PE1}:$T${PE2})>1E-12))=0",
    f"=SUMPRODUCT(ABS(Periodos!$K${PE1}:$K${PE2}-Periodos!$T${PE1}:$T${PE2}))", "", "", "RF-09; estructura de la hoja")
chk("La cuadrícula de Valuación diaria cubre cada par y fecha de Transacciones",
    f"=AND({rng('Transacciones', 'AF', T1, T2)})", "", "", "", "estructura de la hoja")
chk("Calendario: 104 sábados y domingos de 2026, sin fechas repetidas ni fuera de 2026",
    f"=AND(SUMPRODUCT(--(WEEKDAY({R_DIAS_SIN},2)>=6))=104,SUMPRODUCT(--(YEAR({R_DIAS_SIN})<>2026))=0,"
    f"SUMPRODUCT(1/COUNTIF({R_DIAS_SIN},{R_DIAS_SIN}))=ROWS({R_DIAS_SIN}))", "", "", "",
    "RF-07 crit. 2; DOF 10/12/2025, art. 1")
chk("Cargas: incorporadas = filas de la semilla, intervalo = fechas de sus datos y licencia de su fuente",
    f"=AND({rng('Entradas', 'N', *R_CARGAS)})", "", "", "", "RF-31 crit. 1; RD-17; 4.4")
chk("Cada precio y cada tasa tiene la fuente de su carga",
    f"=SUMPRODUCT(--(COUNTIFS({rng('Entradas', 'A', *R_CARGAS)},{rng('Precios', 'E', P1_, P2_)},"
    f"{rng('Entradas', 'B', *R_CARGAS)},{rng('Precios', 'D', P1_, P2_)})=0))"
    f"+SUMPRODUCT(--(COUNTIFS({rng('Entradas', 'A', *R_CARGAS)},{TA['G']},{rng('Entradas', 'B', *R_CARGAS)},"
    f"{TA['F']})=0))=0", "", "", "", "RD-19; FK (carga_id, fuente_id)")
chk("Rechazos: N1 a N8 se rechazan", f'=COUNTIF({rng("Rechazos", c_res, RJ1, RJ2)},"rechazar")=ROWS({rng("Rechazos", c_res, RJ1, RJ2)})',
    "", "", "", "RF-28; RF-26a crit. 2; RF-05 crit. 3; RF-09 crit. 3")
chk("C1: T11 y T12 se aceptan (saldo 40); con la venta antes que la compra, el saldo sería negativo",
    f'=AND(Rechazos!$O${C1R}="aceptar",Rechazos!$M${C1R}>=0,Rechazos!$N${C1R}<0)', "", "", "", "RF-08 crit. 3; RF-28")
CO1 = 5
for i, (texto, res, libro, otro, dif, origen) in enumerate(CHK):
    r = CO1 + i
    celda(ws_co, f"A{r}", i + 1, "int", fuente=GRIS)
    celda(ws_co, f"B{r}", texto, fuente=TEXTO)
    celda(ws_co, f"C{r}", res.replace("{r}", str(r)))
    if libro:
        celda(ws_co, f"D{r}", libro.replace("{r}", str(r)), "frac")
    if otro:
        celda(ws_co, f"E{r}", otro.replace("{r}", str(r)), "frac")
    if dif:
        celda(ws_co, f"F{r}", dif.replace("{r}", str(r)), "frac")
    celda(ws_co, f"G{r}", origen, fuente=TEXTO)
CO2 = CO1 + len(CHK) - 1
for r in (CO1 + 5, CO1 + 6):   # pico y valle: mostrar como fecha
    ws_co[f"D{r}"].number_format = FMT["fecha"]
ws_co[f"B{CO2 + 2}"] = "TODAS LAS COMPROBACIONES"
ws_co[f"B{CO2 + 2}"].font = ENC
celda(ws_co, f"C{CO2 + 2}", f"=AND(C{CO1}:C{CO2})")
ws_co[f"C{CO2 + 2}"].font = Font(name="Arial", size=10, bold=True)
anchos(ws_co, {"A": 5, "B": 78, "C": 11, "D": 18, "E": 18, "F": 14, "G": 40})

# =====================================================================
# Esperados: las cifras que comparara pytest (referencias a las hojas de calculo)
# =====================================================================
titulo(ws_es, "Esperados: cifras finales del oráculo (lo que compara pytest)",
       "Cada sección empieza con «## nombre» y repite, con referencias, las cifras de las hojas de cálculo. "
       "Los CSV de esperados/ (y rechazos_rf28.csv y casos_positivos.csv, en la raíz del oráculo) tienen las "
       "mismas secciones y columnas, calculadas por el camino independiente en Python (decimal, 28 dígitos), "
       "y son los que lee pytest. Gris: rótulo constante (nivel).")
TIPO = {"monto": "peso", "costo_por_titulo": "unit", "ingreso_por_titulo": "unit", "aportacion": "peso",
        "retiro": "peso", "fecha": "fecha", "vencimiento": "fecha", "d": "int", "inf_plazo_nominal": "int",
        "inf_plazo_efectivo": "int", "inf_tasa": "tasa", "inf_fecha_colocacion": "fecha",
        "sup_plazo_nominal": "int", "sup_plazo_efectivo": "int", "sup_tasa": "tasa",
        "sup_fecha_colocacion": "fecha", "r_por_ciento_anual": "tasa", "p_sin_redondear": "tasa", "p": "p",
        "fecha_cierre": "fecha", "precio": "unit", "fecha_corte": "fecha", "titulos": "int",
        "costo_unitario": "unit", "costo_total": "peso", "fecha_precio": "fecha", "fecha_colocacion_inf": "fecha",
        "fecha_colocacion_sup": "fecha", "valor": "peso", "resultado_no_realizado": "peso",
        "aportaciones": "peso", "retiros_ventas": "peso", "retiros_vencimientos": "peso", "retiros": "peso",
        "r": "frac", "r_por_ciento": "pct", "indice": "frac", "maximo": "frac", "caida": "frac",
        "inicio": "fecha", "fin": "fecha", "fecha_base": "fecha", "dias": "int", "valor_base": "peso",
        "valor_fin": "peso", "costo_total_fin": "peso", "resultado_no_realizado_fin": "peso", "twr": "frac",
        "twr_por_ciento": "pct", "maxima_caida": "frac", "maxima_caida_por_ciento": "pct",
        "fecha_pico": "fecha", "fecha_valle": "fecha", "fecha_saldo_negativo": "fecha", "saldo_resultante": "int",
        "saldo_previo": "int", "compras_del_dia": "int", "ventas_del_dia": "int",
        "saldo_si_ventas_antes_que_compras": "int"}
fila = 4


def seccion(nombre, columnas, filas):
    """filas: lista de dict columna -> formula (o texto constante)."""
    global fila
    ws_es.cell(row=fila, column=1, value=f"## {nombre}").font = SEC
    fila += 1
    encabezados(ws_es, fila, columnas)
    for fx in filas:
        fila += 1
        for j, c in enumerate(columnas):
            v = fx.get(c)
            if v is None:
                continue
            celda(ws_es, f"{col(j + 1)}{fila}", v, TIPO.get(c, "gen"),
                  fuente=NEGRO if str(v).startswith("=") else GRIS)
    fila += 2


seccion("transacciones", ["ref", "tipo", "monto", "costo_por_titulo", "ingreso_por_titulo", "aportacion", "retiro"],
        [{"ref": f"=Transacciones!A{r}", "tipo": f"=Transacciones!E{r}", "monto": f"=Transacciones!O{r}",
          "costo_por_titulo": f"=Transacciones!P{r}", "ingreso_por_titulo": f"=Transacciones!Q{r}",
          "aportacion": f"=Transacciones!R{r}", "retiro": f"=Transacciones!S{r}"} for r in range(T1, T2 + 1)])
mapa = {"fecha": "A", "instrumento_clave": "B", "vencimiento": "C", "d": "E", "caso": "AC", "inf_plazo_nominal": "W",
        "inf_plazo_efectivo": "U", "inf_tasa": "AA", "inf_fecha_colocacion": "Y", "sup_plazo_nominal": "X",
        "sup_plazo_efectivo": "V", "sup_tasa": "AB", "sup_fecha_colocacion": "Z", "r_por_ciento_anual": "AD",
        "p_sin_redondear": "AE", "p": "AF"}
seccion("valuacion_cetes", list(mapa), [{k: f"=CETES!{c}{r}" for k, c in mapa.items()} for r in range(C1, C2 + 1)])
mapa = {"fecha": "I", "instrumento_clave": "J", "fecha_cierre": "K", "precio": "L", "sin_cierre_ese_dia": "M"}
seccion("precios_usados", list(mapa), [{k: f"=Precios!{c}{r}" for k, c in mapa.items()} for r in range(PU1, PU2 + 1)])
COLS_POS = ["nivel", "fecha_corte", "portafolio", "instrumento_clave", "intermediario", "tiene_transacciones",
            "titulos", "costo_unitario", "costo_total", "precio", "fecha_precio", "d", "r_por_ciento_anual",
            "fecha_colocacion_inf", "fecha_colocacion_sup", "valor", "resultado_no_realizado"]
mapa1 = {"fecha_corte": "A", "portafolio": "B", "instrumento_clave": "C", "intermediario": "D",
         "tiene_transacciones": "F", "titulos": "G", "costo_unitario": "H", "costo_total": "I", "precio": "J",
         "fecha_precio": "K", "d": "M", "r_por_ciento_anual": "N", "fecha_colocacion_inf": "O",
         "fecha_colocacion_sup": "P", "valor": "Q", "resultado_no_realizado": "R"}
filas_pos = [dict({"nivel": "intermediario"}, **{k: f"=Posiciones!{c}{r}" for k, c in mapa1.items()})
             for r in range(PO1, PO2 + 1)]
mapa2 = {"fecha_corte": "A", "portafolio": "B", "instrumento_clave": "C", "titulos": "D", "costo_total": "E",
         "valor": "F", "resultado_no_realizado": "G"}
filas_pos += [dict({"nivel": "instrumento"}, **{k: f"=Posiciones!{c}{r}" for k, c in mapa2.items()}) for r in CONSOL]
mapa3 = {"fecha_corte": "A", "portafolio": "B", "costo_total": "C", "valor": "D", "resultado_no_realizado": "E"}
filas_pos += [dict({"nivel": "portafolio"}, **{k: f"=Posiciones!{c}{r}" for k, c in mapa3.items()})
              for r in range(PT1, PT2 + 1)]
seccion("posiciones", COLS_POS, filas_pos)
mapa = {"fecha": "A", "portafolio": "B", "valor": "D", "aportaciones": "E", "retiros_ventas": "F",
        "retiros_vencimientos": "G", "retiros": "H", "r": "K", "r_por_ciento": "L", "indice": "M", "maximo": "N",
        "caida": "O"}
seccion("serie_diaria", list(mapa), [{k: f"=Serie!{c}{r}" for k, c in mapa.items()} for r in range(S1, S2 + 1)])
filas_idx = []
for per_ in periodos:
    pid = per_["periodo"]
    b1, b2 = BLOQUES[pid]
    for r in range(b1, b2 + 1):
        filas_idx.append({"periodo": f"=Periodos!$A${FILA_PER_RES[pid]}", "fecha": f"=Periodos!A{r}",
                          "r": f"=Periodos!B{r}", "indice": f"=Periodos!D{r}", "maximo": f"=Periodos!E{r}",
                          "caida": f"=Periodos!F{r}"})
seccion("indice_por_periodo", ["periodo", "fecha", "r", "indice", "maximo", "caida"], filas_idx)
mapa = {"periodo": "A", "portafolio": "B", "inicio": "C", "fin": "D", "fecha_base": "E", "dias": "F",
        "valor_base": "G", "valor_fin": "H", "costo_total_fin": "I", "resultado_no_realizado_fin": "J", "twr": "K",
        "twr_por_ciento": "M", "maxima_caida": "N", "maxima_caida_por_ciento": "O", "fecha_pico": "R",
        "fecha_valle": "P"}
seccion("indicadores", list(mapa), [{k: f"=Periodos!{c}{FILA_PER_RES[p['periodo']]}" for k, c in mapa.items()}
                                    for p in periodos])
mapa = {"id": "A", "resultado_esperado": c_res, "regla": c_regla, "fecha_saldo_negativo": c_fecha,
        "saldo_resultante": c_saldo}
seccion("rechazos_rf28", list(mapa), [{k: f"=Rechazos!{c}{r}" for k, c in mapa.items()} for r in range(RJ1, RJ2 + 1)])
mapa = {"id": "A", "saldo_previo": "J", "compras_del_dia": "K", "ventas_del_dia": "L", "saldo_resultante": "M",
        "saldo_si_ventas_antes_que_compras": "N", "resultado_esperado": "O"}
seccion("casos_positivos", list(mapa), [{k: f"=Rechazos!{c}{C1R}" for k, c in mapa.items()}])
for j in range(1, 18):
    ws_es.column_dimensions[col(j)].width = 15
ws_es.column_dimensions["A"].width = 18

# =====================================================================
# Leeme
# =====================================================================
L = []


def t(texto, estilo="texto"):
    L.append((estilo, texto))


t("Oráculo del conjunto de referencia (5.2) del Proyecto 077", "titulo")
t("Plataforma de gestión de activos financieros. Estadía de Ramon Ernesto Nieblas Mendivil en PluriOne S.A. de C.V. "
  "Construido el jueves 15 de octubre de 2026, antes de programar el motor; lo congela un commit en el repositorio.", "nota")
t("")
t("Qué es", "seccion")
t("Es el oráculo de la sección 5.2 del SRS: un escenario con un usuario de prueba (oraculo@example.com), dos "
  "portafolios (Principal y Secundario), dos intermediarios (Casa A y Casa B), tres instrumentos de demostración "
  "(DEMOACC, DEMOETF y DEMOFIB) y cuatro emisiones de CETES (BI261008, BI261105, BI261217 y BI270318), con las "
  "cifras que el motor único debe reproducir: costo y resultado no realizado por intermediario, valor de mercado, "
  "valuación de CETES (RF-26b), liquidación al vencimiento (RF-26a), serie diaria, TWR y máxima caída.")
t("Cada cifra de este libro es una fórmula visible que parte de las entradas, escritas en azul. Ninguna cifra se "
  "calculó fuera de la hoja y se pegó como valor. El libro lo arma genera_libro.py y lo recalcula Excel.")
t("Las mismas cifras se obtuvieron por un segundo camino independiente: calcula_oraculo.py, en Python con decimal "
  "de 28 dígitos y algoritmos distintos (costo total por par en un ciclo diario, en vez de kardex y SUMIFS). "
  "compara_vias.py las compara una por una; el resultado está en comparacion_vias.csv y en el README.")
t("pytest compara el motor contra esperados/*.csv, que tienen las cifras de Python sin redondear, con las "
  "tolerancias de RNF-01: 0.01 en importes y 0.001 puntos porcentuales en TWR y máxima caída; y comprueba los "
  "rechazos de rechazos_rf28.csv (hoja Rechazos).")
t("")
t("Cómo leerlo", "seccion")
t("Colores: azul = entrada escrita a mano (de entradas/*.csv); se puede cambiar su valor dentro de la estructura "
  "existente (precios, tasas, cantidades, importes, fechas de transacciones). Gris = rótulo de estructura (la fecha, "
  "el portafolio, el instrumento y el intermediario de cada fila de Valuación diaria, CETES, Serie, Precios y "
  "Posiciones): define qué filas existen y no se edita en la hoja; para agregar pares, fechas, cortes o periodos, o "
  "cambiar el inicio o el fin de un periodo, se cambian entradas/*.csv y se regenera el libro con genera_libro.py. "
  "Negro = fórmula. Fuente Arial en todo el libro.")
t("Unidades: importes en pesos (MXN), sin redondear (se muestran con 4 decimales). Tasas en por ciento anual. "
  "r(t), índices, TWR y caídas como fracción (0.01 = 1 %), con su equivalente en por ciento. P de CETES con 7 decimales.")
for nombre, desc in [
        ("Entradas", "Parámetros (intervalo, serie, usuario), cortes, periodos, portafolios, intermediarios, "
                     "instrumentos, fuentes, versiones de licencia, cargas y el calendario completo de días sin "
                     "operaciones de 2026 (114 fechas)."),
        ("Transacciones", "T01 a T16 (entradas) y, por fórmula: monto, costo o ingreso por título, aportación A, "
                          "retiro R y el kardex del costo promedio por par portafolio-instrumento-intermediario."),
        ("Precios", "Cierres sintéticos de demostración y el cierre usado en cada día natural (con su fecha)."),
        ("Tasas", "Las 32 colocaciones del CF107 del 27/08 al 15/10/2026, con plazo efectivo y fuentes."),
        ("CETES", "Por fecha y emisión: d, colocación, tasa y plazo efectivo vigentes en los cinco plazos, los dos "
                  "nodos usados, r, P sin redondear y P = ROUND(…; 7)."),
        ("Valuación diaria", "Cada día natural × cada par: títulos, costo unitario, costo total, precio o P, valor, "
                             "resultado y liquidación por vencimiento."),
        ("Posiciones", "Los cuatro cortes (13/09, 16/09, 08/10, 14/10): por intermediario, consolidado por "
                       "instrumento y totales, con la comparación contra V(t)."),
        ("Serie", "Por día natural y portafolio: V, A, R, r, I, máximo y caída (periodo completo, base 10/09)."),
        ("Periodos", "P1-A, P1-B, P1-C, P1-D, P2-A y P2-C: TWR por tres caminos (índice final, PRODUCT y la "
                     "Serie), máxima caída, pico y valle."),
        ("Rechazos", "N1 a N8 (candidatos que se rechazan, con su regla, la fecha del primer saldo negativo y el "
                     "saldo) y el caso positivo C1."),
        ("Comprobaciones", "Cifras por dos caminos y reglas de las entradas; la última fila debe decir VERDADERO."),
        ("Esperados", "Las cifras finales, por secciones con los nombres y columnas de los CSV de esperados/.")]:
    t(f"• {nombre}: {desc}")
t("")
t("Reglas aplicadas (y su origen)", "seccion")
for regla, origen in [
        ("Portafolio sin efectivo. Cada compra es una aportación A = títulos × precio + importe; cada venta, un "
         "retiro R = títulos × precio − importe; cada vencimiento de CETES, un retiro R = títulos × 10.00, sin ISR.",
         "RF-09 crit. 2; RF-26a crit. 1; P-09; P-16; S-14"),
        ("Fecha de concertación, corte inclusivo y compras antes que ventas el mismo día.",
         "RF-06 crit. 2; RF-08 crit. 3; P-09"),
        ("Posición = suma de los saldos por intermediario dentro del portafolio; sin emisiones vencidas (0 desde el "
         "vencimiento). Títulos enteros. Otro portafolio no cuenta.", "RF-06; RF-26a; 3.4.3; X-06; P-07"),
        ("Costo promedio ponderado por intermediario en cada portafolio: costo por título de una compra = "
         "(títulos × precio + importe) / títulos; una venta no cambia el costo unitario; con saldo 0 se reinicia. "
         "Resultado no realizado = valor − títulos × costo unitario.", "RF-05; RF-08; P-10; X-03"),
        ("Valor = títulos × último cierre igual o anterior a la fecha (días sin cierre: el último disponible).",
         "RF-08 crit. 4; P-09"),
        ("CETES: d = días naturales al vencimiento (≥ 1); en cada plazo nominal rige la última colocación con fecha "
         "igual o anterior a la de valuación, con su plazo efectivo; interpolación lineal por plazo efectivo y, fuera "
         "del rango, la tasa del extremo; r sin redondear; P = 10.00 / (1 + r/100 × d/360) a 7 decimales, mitad "
         "alejándose de cero; valor = títulos × P.", "RF-26b; P-11; R-14; RD-16"),
        ("TWR: r(t) = [V(t) + R(t)] / [V(t−1) + A(t)] − 1; TWR = Π[1 + r(t)] − 1, sin anualizar.", "RF-09; P-09"),
        ("Máxima caída: I(t) = Π[1 + r(s)], s ≤ t; mín{I(t) / máx[I(u), u ≤ t]} − 1, negativa o cero, sobre el "
         "índice del TWR y no sobre el valor.", "RF-10; P-09"),
        ("Sin redondeo salvo P (7 decimales). Importes con 4 decimales o más y por cientos con 6 o más; comparación "
         "sin redondear.", "RD-12; RD-16; P-13; RNF-01"),
        ("Ningún saldo de un instrumento con un intermediario, dentro del portafolio, queda negativo en ninguna fecha; "
         "ninguna transacción de una emisión en o después de su vencimiento.", "RF-28; RF-26a crit. 2"),
        ("Intervalo de las semillas: del 10/09 al 14/10/2026 (fijado al congelar 5.2). Semilla de tasas: colocaciones "
         "del 27/08 al 15/10, con una de cada plazo anterior al intervalo.", "S-09; P-14; RF-30 crit. 1")]:
    t(f"• {regla}  [{origen}]")
t("")
t("Recomendaciones de 3.2 aplicadas (los ⟦decidir: recomendado⟧, registrados como tales)", "seccion")
for rec in [
        "RF-09: serie diaria en días naturales (los fines de semana y el 16/09 tienen r ≠ 0 por los CETES).",
        "RF-09: factor 1 (r = 0) si el denominador V(t−1) + A(t) es 0 (P2 del 11/09 al 13/09).",
        "RF-04 crit. 3: claves ficticias con prefijo DEMO y marca de demostración.",
        "RF-05 crit. 2: importe con 2 decimales que admite 0 (CETES sin comisión); una venta con importe igual o "
        "mayor que títulos × precio se rechaza.",
        "RF-09 crit. 3: se rechazan un periodo con fin anterior al inicio y fechas fuera de las semillas "
        "(rechazos_rf28.csv, N7 y N8)."]:
    t(f"• {rec}")
t("")
t("Decisiones abiertas de 3.2 que el oráculo fija (⟦decidir⟧ sin recomendación; Ramon debe confirmarlas)", "seccion")
for rec in [
        "RF-09: la serie parte del cierre del día previo al inicio del periodo (bases V(10/09), V(30/09) y V(08/10)).",
        "RF-10: I = 1 al inicio como primer máximo (en P1-C y P2-C el pico es la fecha base)."]:
    t(f"• {rec}")
t("")
t("Decisiones y convenciones del oráculo", "seccion")
for dec in [
        "P-16 (delegada en Claude): precio por título e importe de comisiones con IVA por separado (S-08); "
        "liquidación al valor nominal antes del ISR (S-14); la reinversión se registra como compra (T16).",
        "Compras de CETES (T03, T04, T08, T09 y T16): compras en mercado secundario, concertadas ese día al P de "
        "RF-26b del día (P-09; 4.4, fecha de concertación). El día de la compra d es un nodo exacto (28, 91, 182 y "
        "28), así que P coincide con el precio de la colocación de esa semana. No se modelan como compras en "
        "subasta: su concertación sería el martes de la subasta y T03 y T04 caerían el 08/09, antes del intervalo "
        "de las semillas.",
        "Comisión sintética de 0.29 % (0.25 % más IVA de 16 %), redondeada al centavo, solo para generar los datos; "
        "el motor no la usa.",
        "Venta secundaria de CETES (T13) al P de RF-26b del día, sin comisión.",
        "DEMOFIB no tiene cierre el 08/10 (día hábil sin cierre de un instrumento): se valúa con el del 07/10.",
        "Costo unitario 0 cuando el saldo es 0. Si la máxima caída es 0, pico y valle quedan vacíos; si el máximo "
        "es el I = 1 inicial, el pico es la fecha base.",
        "Pico: la primera fecha (la más antigua, contando la fecha base con I = 1) en que I alcanza el máximo "
        "vigente en el valle. Valle: la primera fecha con la caída mínima. En P2-A, I(16/09) = I(15/09) porque el "
        "16/09 es festivo y Secundario no tiene CETES; por esta regla, el pico es el 15/09.",
        "Versión de licencia de la semilla sintética: propuesta del oráculo (RF-31 crit. 1 la deja ⟦decidir⟧). Las "
        "cargas registran 0 observaciones omitidas porque los CSV solo traen observaciones publicadas."]:
    t(f"• {dec}")
t("")
t("Fuentes", "seccion")
for fu in [
        "Tasas: Banco de México, Sistema de Información Económica, cuadro CF107 «Valores gubernamentales. Resultados "
        "de la subasta», https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=22&accion="
        "consultarCuadro&idCuadro=CF107&locale=es, y su JSON público consultaSerieGrafica.do; consultados el "
        "15/10/2026; copias en fuentes/ (cf107_5oct.html, cf107_6oct.html, cf107_15oct.html y sie_json/). "
        "Atribución: «Fuente: Banco de México, https://www.banxico.org.mx».",
        "Calendario: DOF del 10/12/2025, CNBV, días de 2026 en que las entidades financieras suspenden operaciones, "
        "art. 1 (https://dof.gob.mx/nota_detalle.php?codigo=5775684&fecha=10/12/2025), y Grupo BMV, Calendario de "
        "días festivos (https://www.bmv.com.mx/es/grupo-bmv/calendario-de-dias-festivos), consultado el 15/10/2026.",
        "Precios de DEMOACC, DEMOETF y DEMOFIB: sintéticos de demostración, no son precios reales (R-04, R-05, RF-07)."]:
    t(f"• {fu}")
t("")
t("Pendientes antes de congelar", "seccion")
for pe in [
        "Confirmar con una segunda fuente (CF107 con rango de fechas o API con token) la tasa a 28 días del "
        "10/09/2026, 6.25000 % con plazo efectivo 28: es la única de una sola fuente que mueve cifras (T03, T04 y "
        "BI261008 del 10/09 al 16/09). Las del 27/08 y 03/09 también tienen una sola fuente, pero no mueven cifras.",
        "Confirmar las dos decisiones abiertas de 3.2 que el oráculo fija (arriba) y la licencia de la semilla "
        "sintética; agregar a la ficha de RF-10 la regla del pico y del valle con empates.",
        "Revisar las fórmulas y congelar con un commit antes de programar el motor (este trabajo no tocó el "
        "repositorio)."]:
    t(f"• {pe}")
t("")
t("Cómo recalcular", "seccion")
t("Desde la carpeta del oráculo (la del README), con PYTHONIOENCODING=utf-8:  python -I -B calcula_oraculo.py  →  "
  "python -B genera_libro.py  →  powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/recalc_excel.ps1 "
  "oraculo_5_2.xlsx  →  python -B compara_vias.py. Los dos que usan openpyxl van sin -I (openpyxl está en el "
  "site-packages del usuario, que -I excluye); la carpeta no tiene archivos .py que tapen la biblioteca estándar. "
  "La hoja Comprobaciones debe terminar en VERDADERO.")

estilos = {"titulo": TIT, "seccion": SEC, "nota": NOTA, "texto": TEXTO}
for i, (est, texto) in enumerate(L):
    c = ws_lee.cell(row=i + 1, column=1, value=texto)
    c.font = estilos[est]
    c.alignment = AJUSTE
ws_lee.column_dimensions["A"].width = 150

for ws in (ws_t, ws_p, ws_ta, ws_c, ws_po, ws_pe, ws_r, ws_co):
    ws.freeze_panes = ws.freeze_panes or "A5"
ws_es.freeze_panes = "A4"
wb.save(SALIDA)
print(f"Libro escrito: {SALIDA}")
print(f"Transacciones {T1}-{T2}; Precios {P1_}-{P2_} y {PU1}-{PU2}; Tasas {TA1}-{TA2}; CETES {C1}-{C2}; "
      f"Valuación diaria {V1}-{V2}; Posiciones {PO1}-{PO2}, {PI1}-{PI2}, {PT1}-{PT2}; Serie {S1}-{S2}; "
      f"Comprobaciones {CO1}-{CO2}")
