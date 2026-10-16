"""Oraculo de 5.2, segundo camino: calculo independiente de la hoja, en Python con decimal.

Lee las entradas de entradas/*.csv, las valida contra 4.3 y 4.4, calcula las
cifras del conjunto de referencia y escribe (rutas relativas a la carpeta del oraculo):
  - esperados/*.csv      (cifras sin redondear: 28 digitos significativos)
  - rechazos_rf28.csv    (casos negativos N1 a N8 con el motivo esperado)
  - casos_positivos.csv  (caso positivo C1: T11 y T12 se aceptan)

No lee la hoja de calculo ni comparte codigo con genera_libro.py. Los algoritmos
son distintos a proposito: aqui el costo se lleva como costo total por par
portafolio-instrumento-intermediario y los dias se procesan en un ciclo; la hoja
usa un kardex con costo unitario y SUMIFS/MAXIFS.

Aritmetica (RD-12, RD-16, P-13): contexto explicito de 28 digitos significativos
(rounding ROUND_HALF_EVEN solo para ese limite) y ROUND_HALF_UP (mitad alejandose
de cero) unicamente para P de los CETES, a 7 decimales. Nada mas se redondea.

Uso: python -I -B <ruta del oraculo>/calcula_oraculo.py   (solo biblioteca estandar)
"""
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import (Context, Decimal, DivisionByZero, InvalidOperation, Overflow,
                     ROUND_FLOOR, ROUND_HALF_EVEN, ROUND_HALF_UP, setcontext)
from pathlib import Path

CONTEXTO = Context(prec=28, rounding=ROUND_HALF_EVEN,
                   traps=[InvalidOperation, DivisionByZero, Overflow])
setcontext(CONTEXTO)

D = Decimal
CERO, UNO, CIEN = D(0), D(1), D(100)
DIAS_ANIO = D(360)
SIETE_DECIMALES = D("0.0000001")
PLAZOS = (28, 91, 182, 364, 728)

RAIZ = Path(__file__).resolve().parent
ENT = RAIZ / "entradas"
ESP = RAIZ / "esperados"
ESP.mkdir(exist_ok=True)

errores = []


def falla(msg):
    errores.append(msg)


def lee(nombre):
    with open(ENT / nombre, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f(s):
    return date.fromisoformat(s)


def decimales(s):
    s = s.strip()
    return len(s.split(".")[1]) if "." in s else 0


# Columnas que son fracciones o por cientos: se escriben con al menos 10 decimales.
# Las demas cifras decimales (pesos, precios, tasas), con al menos 4. Solo se agregan
# ceros a la derecha de un valor exacto: nunca se redondea (P-13).
COLUMNAS_FRACCION = {"r", "r_por_ciento", "indice", "maximo", "caida", "twr", "twr_por_ciento",
                     "maxima_caida", "maxima_caida_por_ciento", "r_por_ciento_anual", "p_sin_redondear"}


def txt(x, minimo=4):
    """Cifra a texto sin notacion cientifica y sin redondear."""
    if x is None:
        return ""
    if isinstance(x, bool):
        return "sí" if x else "no"
    if isinstance(x, Decimal):
        if x.as_tuple().exponent > -minimo:
            x = x.quantize(D(1).scaleb(-minimo))   # solo agrega ceros: el valor tiene menos decimales
        return format(x, "f")
    if isinstance(x, date):
        return x.isoformat()
    return str(x)


def escribe(ruta, columnas, filas):
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(columnas)
        for fila in filas:
            w.writerow([txt(fila[c], 10 if c in COLUMNAS_FRACCION else 4) for c in columnas])


# =====================================================================
# 1. Entradas
# =====================================================================
param = {r["parametro"]: r["valor"] for r in lee("parametros.csv")}
INT_INI, INT_FIN = f(param["intervalo_semillas_inicio"]), f(param["intervalo_semillas_fin"])
SERIE_INI, SERIE_FIN = f(param["serie_inicio"]), f(param["serie_fin"])
DIAS = [SERIE_INI + timedelta(k) for k in range((SERIE_FIN - SERIE_INI).days + 1)]

portafolios = [r["nombre"] for r in lee("portafolios.csv")]
intermediarios = [r["nombre"] for r in lee("intermediarios.csv")]
instrumentos = {}
for r in lee("instrumentos.csv"):
    instrumentos[r["clave"]] = r
ORDEN_INS = list(instrumentos)
cetes = {k for k, r in instrumentos.items() if r["clase_activo"] == "cetes"}
VENC = {k: f(instrumentos[k]["vencimiento"]) for k in cetes}
VN = {k: D(instrumentos[k]["valor_nominal"]) for k in cetes}

filas_calendario = lee("dias_sin_operaciones_2026.csv")
sin_operaciones = {f(r["fecha"]) for r in filas_calendario}

filas_fuente = lee("fuentes_datos.csv")
filas_licencia = lee("versiones_licencia.csv")
filas_carga = lee("cargas_datos.csv")

tasas = []
filas_tasa = lee("tasas.csv")
for r in filas_tasa:
    tasas.append({"pn": int(r["plazo_nominal"]), "fecha": f(r["fecha_colocacion"]),
                  "valor": D(r["valor"]), "pe": int(r["plazo_efectivo"]), "_txt": r["valor"],
                  "unidad": r["unidad"]})

cierres = defaultdict(dict)  # clave -> {fecha: precio}
filas_precio = lee("precios.csv")
for r in filas_precio:
    cierres[r["instrumento_clave"]][f(r["fecha"])] = D(r["precio"])

txs = []
for i, r in enumerate(lee("transacciones.csv")):
    txs.append({"ref": r["ref"], "port": r["portafolio_nombre"], "inter": r["intermediario_nombre"],
                "ins": r["instrumento_clave"], "tipo": r["tipo"], "fecha": f(r["fecha_concertacion"]),
                "n": int(r["cantidad"]), "p": D(r["precio"]), "imp": D(r["importe_comisiones"]),
                "_p": r["precio"], "_imp": r["importe_comisiones"], "_n": r["cantidad"], "seq": i})

cortes = [f(r["fecha_corte"]) for r in lee("cortes.csv")]
periodos = [{"id": r["periodo"], "port": r["portafolio_nombre"], "ini": f(r["inicio"]),
             "fin": f(r["fin"])} for r in lee("periodos.csv")]

# =====================================================================
# 2. Validacion de las entradas (4.3, 4.4, RF-04, RF-05, RF-07, RF-28, RF-30)
# =====================================================================
claves_vistas = set()
for k, r in instrumentos.items():
    if k in claves_vistas:
        falla(f"clave repetida {k}")
    claves_vistas.add(k)
    if r["clase_activo"] not in ("accion", "etf", "fibra", "cetes"):
        falla(f"{k}: clase_activo fuera del dominio")
    if r["divisa"] != "MXN":
        falla(f"{k}: divisa distinta de MXN")
    if (r["de_demostracion"] == "true") != (r["clase_activo"] != "cetes"):
        falla(f"{k}: de_demostracion incongruente con la clase")
    if r["clase_activo"] == "cetes":
        v = f(r["vencimiento"])
        if k != "BI" + v.strftime("%y%m%d"):
            falla(f"{k}: la clave no es BI + vencimiento AAMMDD")
        if D(r["valor_nominal"]) != D("10.00") or decimales(r["valor_nominal"]) > 2:
            falla(f"{k}: valor nominal distinto de 10.00")
    else:
        if re.fullmatch(r"BI[0-9]{6}", k):
            falla(f"{k}: clave ficticia con forma de emision de CETES")
        if not k.startswith("DEMO"):
            falla(f"{k}: sin el prefijo DEMO recomendado")

if len({n.strip().lower() for n in intermediarios}) != len(intermediarios):
    falla("intermediarios repetidos")
if len({n.strip().lower() for n in portafolios}) != len(portafolios):
    falla("portafolios repetidos")

vistos = set()
for ta in tasas:
    if ta["pn"] not in PLAZOS:
        falla(f"tasa con plazo nominal {ta['pn']} fuera del dominio")
    if ta["pe"] <= 0:
        falla("tasa sin plazo efectivo positivo")
    if decimales(ta["_txt"]) > 5:
        falla("tasa con mas de 5 decimales")
    if (ta["pn"], ta["fecha"]) in vistos:
        falla("tasa repetida por plazo y colocacion")
    vistos.add((ta["pn"], ta["fecha"]))
for pn in PLAZOS:
    if not any(ta["pn"] == pn and ta["fecha"] < INT_INI for ta in tasas):
        falla(f"plazo {pn} sin colocacion anterior al intervalo (criterio 1 de RF-30)")

for r in filas_precio:
    k, t, s = r["instrumento_clave"], f(r["fecha"]), r["precio"]
    if k not in instrumentos or k in cetes:
        falla(f"precio de {k}: instrumento inexistente o CETES (RD-04)")
    if D(s) <= 0 or decimales(s) > 7:
        falla(f"precio de {k} {t}: no positivo o con mas de 7 decimales")
    if t.weekday() >= 5 or t in sin_operaciones:
        falla(f"precio de {k} en dia sin operaciones {t}")
    if not (INT_INI <= t <= INT_FIN):
        falla(f"precio de {k} fuera del intervalo {t}")

# calendario completo de 2026 (RF-07 crit. 2; 4.3): todos los sabados y domingos, sin fechas repetidas
if len(sin_operaciones) != len(filas_calendario):
    falla("calendario con fechas repetidas")
fines_2026 = {date(2026, 1, 1) + timedelta(k) for k in range(365)
              if (date(2026, 1, 1) + timedelta(k)).weekday() >= 5}
if len(fines_2026) != 104 or not fines_2026 <= sin_operaciones:
    falla("el calendario no contiene todos los sabados y domingos de 2026")
if any(t.year != 2026 for t in sin_operaciones):
    falla("calendario con fechas fuera de 2026")

# fuente_datos, version_licencia y carga_datos (4.4; RF-31 crit. 1; RD-17, RD-19)
if list(filas_fuente[0]) != ["nombre", "direccion", "de_demostracion"]:
    falla("fuentes_datos.csv no tiene exactamente las columnas de fuente_datos de 4.4")
fuentes = {r["nombre"]: r for r in filas_fuente}
if len(fuentes) != len(filas_fuente):
    falla("fuente repetida (UNIQUE (nombre))")
if any(r["de_demostracion"] not in ("true", "false") for r in filas_fuente):
    falla("de_demostracion fuera de true/false")
licencias = {}
for r in filas_licencia:
    k = (r["fuente_nombre"], r["version"])
    if r["fuente_nombre"] not in fuentes or not r["version"].strip() or not r["usos_permitidos"].strip():
        falla(f"version de licencia {k}: fuente inexistente o version/usos_permitidos vacios (NOT NULL)")
    if k in licencias:
        falla(f"version de licencia repetida {k} (UNIQUE (fuente_id, version))")
    licencias[k] = r
cargas = {}
for r in filas_carga:
    c = r["carga"]
    if c in cargas:
        falla(f"carga repetida {c}")
    cargas[c] = r
    if (r["fuente_nombre"], r["version"]) not in licencias:
        falla(f"carga {c}: su version de licencia no es de su fuente (FK (fuente_id, version_licencia_id))")
    if r["origen"] != "semilla":
        falla(f"carga {c}: origen fuera del dominio origen_carga")
    if not f(r["fecha_inicial"]) <= f(r["fecha_final"]):
        falla(f"carga {c}: fecha_inicial > fecha_final")
    if int(r["observaciones_incorporadas"]) < 0 or int(r["observaciones_omitidas"]) < 0 or not r["resultado"].strip():
        falla(f"carga {c}: conteos negativos o resultado vacio")
    if not isinstance(json.loads(r["valores_sustituidos"]), dict):
        falla(f"carga {c}: valores_sustituidos no es un objeto JSON")
for nombre_csv, filas_dato, col_fecha in (("precios.csv", filas_precio, "fecha"),
                                          ("tasas.csv", filas_tasa, "fecha_colocacion")):
    for r in filas_dato:
        cg = cargas.get(r["carga"])
        if cg is None or cg["fuente_nombre"] != r["fuente_nombre"]:
            falla(f"{nombre_csv}: fila sin carga o con fuente distinta de la de su carga (FK (carga_id, fuente_id))")
        elif not f(cg["fecha_inicial"]) <= f(r[col_fecha]) <= f(cg["fecha_final"]):
            falla(f"{nombre_csv}: fecha {r[col_fecha]} fuera del intervalo de su carga {r['carga']}")
for c, cg in cargas.items():
    n = sum(1 for r in filas_precio + filas_tasa if r["carga"] == c)
    if int(cg["observaciones_incorporadas"]) != n:
        falla(f"carga {c}: observaciones_incorporadas = {cg['observaciones_incorporadas']}, filas = {n}")
if any(fuentes.get(r["fuente_nombre"], {}).get("de_demostracion") != "true" for r in filas_precio):
    falla("precio cuya fuente no es de demostracion (RF-07 crit. 3)")
if any(fuentes.get(r["fuente_nombre"], {}).get("de_demostracion") != "false" for r in filas_tasa):
    falla("tasa cuya fuente se marca como de demostracion")

for tx in txs:
    if tx["port"] not in portafolios or tx["inter"] not in intermediarios or tx["ins"] not in instrumentos:
        falla(f"{tx['ref']}: referencia inexistente")
    if tx["tipo"] not in ("compra", "venta"):
        falla(f"{tx['ref']}: tipo fuera del dominio")
    if not re.fullmatch(r"[0-9]+", tx["_n"]) or tx["n"] <= 0:
        falla(f"{tx['ref']}: titulos no enteros o no positivos")
    if tx["p"] <= 0 or decimales(tx["_p"]) > 7:
        falla(f"{tx['ref']}: precio no positivo o con mas de 7 decimales")
    if tx["imp"] < 0 or decimales(tx["_imp"]) > 2:
        falla(f"{tx['ref']}: importe negativo o con mas de 2 decimales")
    if tx["tipo"] == "venta" and tx["imp"] >= tx["n"] * tx["p"]:
        falla(f"{tx['ref']}: venta con importe >= titulos x precio")
    if not (INT_INI <= tx["fecha"] <= INT_FIN):
        falla(f"{tx['ref']}: fecha fuera del intervalo de las semillas")
    if tx["ins"] in cetes:
        dv = (VENC[tx["ins"]] - tx["fecha"]).days
        if dv < 1:
            falla(f"{tx['ref']}: transaccion de CETES en o despues del vencimiento (RF-26a)")
        if dv > 728:
            falla(f"{tx['ref']}: mas de 728 dias al vencimiento (RD-05)")


def saldos_negativos(lista):
    """RF-28: recorre cada dia natural del intervalo con compras antes que ventas y
    devuelve (fecha, par, saldo) del primer saldo negativo, o None."""
    saldo = defaultdict(int)
    for t in [INT_INI + timedelta(k) for k in range((INT_FIN - INT_INI).days + 1)]:
        dia = sorted((x for x in lista if x["fecha"] == t),
                     key=lambda x: (0 if x["tipo"] == "compra" else 1, x["seq"]))
        for x in dia:
            par = (x["port"], x["ins"], x["inter"])
            saldo[par] += x["n"] if x["tipo"] == "compra" else -x["n"]
        for par, s in saldo.items():
            if s < 0:
                return t, par, s
    return None


neg = saldos_negativos(txs)
if neg:
    falla(f"RF-28: saldo negativo {neg}")

if errores:
    print("ENTRADAS INVALIDAS:")
    for e in errores:
        print("  -", e)
    sys.exit(1)

# =====================================================================
# 3. Valuacion de CETES (RF-26b)
# =====================================================================


def curva_vigente(t):
    """Para cada plazo nominal, la ultima colocacion con fecha igual o anterior a t."""
    vigente = {}
    for ta in tasas:
        if ta["fecha"] <= t:
            actual = vigente.get(ta["pn"])
            if actual is None or ta["fecha"] > actual["fecha"]:
                vigente[ta["pn"]] = ta
    if set(vigente) != set(PLAZOS):
        raise ValueError(f"curva incompleta el {t}: {sorted(vigente)}")
    return sorted(vigente.values(), key=lambda x: (x["pe"], x["pn"]))


distancia_minima_al_empate = None


def valua_cetes(t, clave):
    global distancia_minima_al_empate
    d = (VENC[clave] - t).days
    if d < 1:
        raise ValueError("valuacion en o despues del vencimiento")
    nodos = curva_vigente(t)
    if d < nodos[0]["pe"]:
        inf = sup = nodos[0]
        caso = "extremo inferior"
    elif d > nodos[-1]["pe"]:
        inf = sup = nodos[-1]
        caso = "extremo superior"
    else:
        iguales = [n for n in nodos if n["pe"] == d]
        if iguales:
            inf = sup = iguales[0]
            caso = "nodo"
        else:
            inf = max((n for n in nodos if n["pe"] < d), key=lambda n: n["pe"])
            sup = min((n for n in nodos if n["pe"] > d), key=lambda n: n["pe"])
            caso = "interpolación"
    if inf is sup:
        r = inf["valor"]
    else:
        r = inf["valor"] + (sup["valor"] - inf["valor"]) * D(d - inf["pe"]) / D(sup["pe"] - inf["pe"])
    p_sin = VN[clave] / (UNO + r / CIEN * D(d) / DIAS_ANIO)
    p = p_sin.quantize(SIETE_DECIMALES, rounding=ROUND_HALF_UP)
    # distancia de p_sin al empate mas cercano, en unidades del 7o decimal
    u = p_sin / SIETE_DECIMALES
    frac = u - u.to_integral_value(rounding=ROUND_FLOOR)
    dist = abs(frac - D("0.5"))
    if distancia_minima_al_empate is None or dist < distancia_minima_al_empate[0]:
        distancia_minima_al_empate = (dist, t, clave)
    return {"fecha": t, "instrumento_clave": clave, "vencimiento": VENC[clave], "d": d, "caso": caso,
            "inf_plazo_nominal": inf["pn"], "inf_plazo_efectivo": inf["pe"], "inf_tasa": inf["valor"],
            "inf_fecha_colocacion": inf["fecha"],
            "sup_plazo_nominal": sup["pn"], "sup_plazo_efectivo": sup["pe"], "sup_tasa": sup["valor"],
            "sup_fecha_colocacion": sup["fecha"],
            "r_por_ciento_anual": r, "p_sin_redondear": p_sin, "p": p}


# filas de valuacion: cada emision desde su primera compra hasta el dia previo al vencimiento
primera = {}
for tx in txs:
    if tx["ins"] in cetes:
        primera[tx["ins"]] = min(primera.get(tx["ins"], tx["fecha"]), tx["fecha"])
valuacion = {}
for clave in ORDEN_INS:
    if clave in primera:
        for t in DIAS:
            if primera[clave] <= t < VENC[clave]:
                valuacion[(t, clave)] = valua_cetes(t, clave)


def cierre_usado(clave, t):
    previas = [x for x in cierres[clave] if x <= t]
    if not previas:
        raise ValueError(f"sin cierre de {clave} al {t}")
    u = max(previas)
    return u, cierres[clave][u]


# =====================================================================
# 4. Posiciones dia por dia (RF-06, RF-08, RF-26a)
# =====================================================================
idx_port = {p: i for i, p in enumerate(portafolios)}
idx_ins = {k: i for i, k in enumerate(ORDEN_INS)}
idx_int = {n: i for i, n in enumerate(intermediarios)}
pares = sorted({(x["port"], x["ins"], x["inter"]) for x in txs},
               key=lambda q: (idx_port[q[0]], idx_ins[q[1]], idx_int[q[2]]))

titulos = {par: 0 for par in pares}
costo_total = {par: CERO for par in pares}       # costo total del saldo (no el unitario)
foto = {}                                         # (t, par) -> dict del dia
A = defaultdict(lambda: CERO)                     # (port, t) aportaciones
R_ventas = defaultdict(lambda: CERO)              # (port, t) retiros por ventas
R_venc = defaultdict(lambda: CERO)                # (port, t) retiros por vencimiento
calc_tx = {}

for t in DIAS:
    del_dia = sorted((x for x in txs if x["fecha"] == t),
                     key=lambda x: (0 if x["tipo"] == "compra" else 1, x["seq"]))
    for x in del_dia:
        par = (x["port"], x["ins"], x["inter"])
        monto = x["n"] * x["p"]
        if x["tipo"] == "compra":
            titulos[par] += x["n"]
            costo_total[par] += monto + x["imp"]
            A[(x["port"], t)] += monto + x["imp"]
            calc_tx[x["ref"]] = {"ref": x["ref"], "tipo": x["tipo"], "monto": monto,
                                 "costo_por_titulo": (monto + x["imp"]) / x["n"], "ingreso_por_titulo": None,
                                 "aportacion": monto + x["imp"], "retiro": CERO}
        else:
            antes = titulos[par]
            despues = antes - x["n"]
            if despues < 0:
                raise ValueError(f"{x['ref']}: saldo negativo")
            costo_total[par] = CERO if despues == 0 else costo_total[par] * D(despues) / D(antes)
            titulos[par] = despues
            R_ventas[(x["port"], t)] += monto - x["imp"]
            calc_tx[x["ref"]] = {"ref": x["ref"], "tipo": x["tipo"], "monto": monto,
                                 "costo_por_titulo": None, "ingreso_por_titulo": (monto - x["imp"]) / x["n"],
                                 "aportacion": CERO, "retiro": monto - x["imp"]}
    liquidacion = {}
    for par in pares:
        port, ins, inter = par
        if ins in cetes and VENC[ins] == t:
            liquidacion[par] = titulos[par] * VN[ins]       # RF-26a: valor nominal, sin ISR
            R_venc[(port, t)] += liquidacion[par]
            titulos[par] = 0
            costo_total[par] = CERO
    for par in pares:
        port, ins, inter = par
        n = titulos[par]
        if ins in cetes:
            v = valuacion.get((t, ins))
            precio = v["p"] if v else None
            fecha_precio = t if v else None
        else:
            fecha_precio, precio = cierre_usado(ins, t)
        if n > 0 and precio is None:
            raise ValueError(f"sin precio para {par} el {t}")
        valor = CERO if n == 0 else n * precio
        ct = costo_total[par]
        foto[(t, par)] = {"titulos": n, "costo_total": ct, "costo_unitario": CERO if n == 0 else ct / n,
                          "precio": precio, "fecha_precio": fecha_precio, "valor": valor,
                          "resultado": valor - ct, "liquidacion": liquidacion.get(par, CERO),
                          "cetes": valuacion.get((t, ins)) if ins in cetes else None}

# =====================================================================
# 5. Serie diaria, TWR y maxima caida (RF-09, RF-10)
# =====================================================================
serie = {}
for port in portafolios:
    previo = None
    I = UNO
    maximo = UNO
    for t in DIAS:
        V = sum((foto[(t, par)]["valor"] for par in pares if par[0] == port), CERO)
        a, rv, rven = A[(port, t)], R_ventas[(port, t)], R_venc[(port, t)]
        fila = {"fecha": t, "portafolio": port, "valor": V, "aportaciones": a, "retiros_ventas": rv,
                "retiros_vencimientos": rven, "retiros": rv + rven}
        if t == SERIE_INI:
            fila.update({"r": None, "r_por_ciento": None, "indice": UNO, "maximo": UNO, "caida": CERO})
        else:
            den = previo + a
            r = CERO if den == 0 else (V + rv + rven) / den - UNO
            I = I * (UNO + r)
            maximo = max(maximo, I)
            fila.update({"r": r, "r_por_ciento": r * CIEN, "indice": I, "maximo": maximo,
                         "caida": I / maximo - UNO})
        serie[(t, port)] = fila
        previo = V

indices, indicadores = [], []
for per in periodos:
    port = per["port"]
    base = per["ini"] - timedelta(1)
    if not (SERIE_INI <= base and per["fin"] <= SERIE_FIN and per["ini"] <= per["fin"]):
        raise ValueError(f"periodo {per['id']} fuera de la serie")
    I, maximo, fecha_max = UNO, UNO, base
    mdd, pico, valle = CERO, None, None
    t = per["ini"]
    while t <= per["fin"]:
        r = serie[(t, port)]["r"]
        I = I * (UNO + r)
        if I > maximo:
            maximo, fecha_max = I, t
        caida = I / maximo - UNO
        if caida < mdd:
            mdd, pico, valle = caida, fecha_max, t
        indices.append({"periodo": per["id"], "fecha": t, "r": r, "indice": I, "maximo": maximo, "caida": caida})
        t += timedelta(1)
    fin = per["fin"]
    indicadores.append({
        "periodo": per["id"], "portafolio": port, "inicio": per["ini"], "fin": fin, "fecha_base": base,
        "dias": (fin - per["ini"]).days + 1,
        "valor_base": serie[(base, port)]["valor"], "valor_fin": serie[(fin, port)]["valor"],
        "costo_total_fin": sum((foto[(fin, par)]["costo_total"] for par in pares if par[0] == port), CERO),
        "resultado_no_realizado_fin": sum((foto[(fin, par)]["resultado"] for par in pares if par[0] == port), CERO),
        "twr": I - UNO, "twr_por_ciento": (I - UNO) * CIEN,
        "maxima_caida": mdd, "maxima_caida_por_ciento": mdd * CIEN,
        "fecha_pico": pico, "fecha_valle": valle})

# =====================================================================
# 6. Cortes (RF-06, RF-08, RF-26b, RF-31)
# =====================================================================
posiciones = []
for corte in cortes:
    for par in pares:
        port, ins, inter = par
        x = foto[(corte, par)]
        c = x["cetes"]
        posiciones.append({
            "nivel": "intermediario", "fecha_corte": corte, "portafolio": port, "instrumento_clave": ins,
            "intermediario": inter,
            "tiene_transacciones": any(tx["fecha"] <= corte and (tx["port"], tx["ins"], tx["inter"]) == par for tx in txs),
            "titulos": x["titulos"], "costo_unitario": x["costo_unitario"], "costo_total": x["costo_total"],
            "precio": x["precio"], "fecha_precio": x["fecha_precio"],
            "d": c["d"] if c else None, "r_por_ciento_anual": c["r_por_ciento_anual"] if c else None,
            "fecha_colocacion_inf": c["inf_fecha_colocacion"] if c else None,
            "fecha_colocacion_sup": c["sup_fecha_colocacion"] if c else None,
            "valor": x["valor"], "resultado_no_realizado": x["resultado"]})
    for port in portafolios:
        for ins in ORDEN_INS:
            del_ins = [p for p in pares if p[0] == port and p[1] == ins]
            if not del_ins:
                continue
            posiciones.append({
                "nivel": "instrumento", "fecha_corte": corte, "portafolio": port, "instrumento_clave": ins,
                "intermediario": None, "tiene_transacciones": None,
                "titulos": sum(foto[(corte, p)]["titulos"] for p in del_ins), "costo_unitario": None,
                "costo_total": sum((foto[(corte, p)]["costo_total"] for p in del_ins), CERO),
                "precio": None, "fecha_precio": None, "d": None, "r_por_ciento_anual": None,
                "fecha_colocacion_inf": None, "fecha_colocacion_sup": None,
                "valor": sum((foto[(corte, p)]["valor"] for p in del_ins), CERO),
                "resultado_no_realizado": sum((foto[(corte, p)]["resultado"] for p in del_ins), CERO)})
        del_port = [p for p in pares if p[0] == port]
        posiciones.append({
            "nivel": "portafolio", "fecha_corte": corte, "portafolio": port, "instrumento_clave": None,
            "intermediario": None, "tiene_transacciones": None, "titulos": None, "costo_unitario": None,
            "costo_total": sum((foto[(corte, p)]["costo_total"] for p in del_port), CERO),
            "precio": None, "fecha_precio": None, "d": None, "r_por_ciento_anual": None,
            "fecha_colocacion_inf": None, "fecha_colocacion_sup": None,
            "valor": sum((foto[(corte, p)]["valor"] for p in del_port), CERO),
            "resultado_no_realizado": sum((foto[(corte, p)]["resultado"] for p in del_port), CERO)})

precios_usados = []
for t in DIAS:
    for ins in ORDEN_INS:
        if ins in cetes:
            continue
        u, pr = cierre_usado(ins, t)
        precios_usados.append({"fecha": t, "instrumento_clave": ins, "fecha_cierre": u, "precio": pr,
                               "sin_cierre_ese_dia": u < t})

# =====================================================================
# 7. Comprobaciones por dos caminos (escenario, 7 f)
# =====================================================================
ind = {x["periodo"]: x for x in indicadores}
tx_ref = {x["ref"]: x for x in txs}
chk = []


def comprueba(nombre, ok, detalle=""):
    chk.append((nombre, ok, detalle))


lhs = (UNO + ind["P1-B"]["twr"]) * (UNO + ind["P1-C"]["twr"])
comprueba("(1+TWR P1-B)(1+TWR P1-C) = 1+TWR P1-A", abs(lhs - (UNO + ind["P1-A"]["twr"])) < D("1e-24"),
          f"dif {lhs - (UNO + ind['P1-A']['twr'])}")
t07 = tx_ref["T07"]
acc_fin = cierres["DEMOACC"][f("2026-10-14")]
esperado = D(150) * acc_fin / (t07["n"] * t07["p"] + t07["imp"]) - UNO
comprueba("TWR P2-A = 150 x 111.05 / (150 x 103.60 + 45.07) - 1", abs(ind["P2-A"]["twr"] - esperado) < D("1e-24"),
          f"dif {ind['P2-A']['twr'] - esperado}")
esperado = acc_fin / cierres["DEMOACC"][f("2026-09-30")] - UNO
comprueba("TWR P2-C = 111.05 / 107.10 - 1", abs(ind["P2-C"]["twr"] - esperado) < D("1e-24"))
esperado = cierres["DEMOACC"][f("2026-10-05")] / cierres["DEMOACC"][f("2026-09-30")] - UNO
comprueba("MDD P2-C = 101.65 / 107.10 - 1", abs(ind["P2-C"]["maxima_caida"] - esperado) < D("1e-24"))
esperado = cierres["DEMOACC"][f("2026-09-23")] / cierres["DEMOACC"][f("2026-09-15")] - UNO
comprueba("MDD P2-A = 90.4250 / 104.75 - 1, pico 15/09, valle 23/09",
          abs(ind["P2-A"]["maxima_caida"] - esperado) < D("1e-24")
          and ind["P2-A"]["fecha_pico"] == f("2026-09-15") and ind["P2-A"]["fecha_valle"] == f("2026-09-23"))
comprueba("R(08/10) de P1 = 20,000.00 exactos", serie[(f("2026-10-08"), "Principal")]["retiros"] == D("20000"))
for ref in ("T03", "T04", "T08", "T09", "T16", "T13"):
    x = tx_ref[ref]
    comprueba(f"{ref}: precio = P de RF-26b del dia", valuacion[(x["fecha"], x["ins"])]["p"] == x["p"],
              f"{valuacion[(x['fecha'], x['ins'])]['p']} vs {x['p']}")
for corte in cortes:
    for port in portafolios:
        tot = [p for p in posiciones if p["nivel"] == "portafolio" and p["fecha_corte"] == corte and p["portafolio"] == port][0]
        suma = sum((p["valor"] for p in posiciones if p["nivel"] == "intermediario" and p["fecha_corte"] == corte
                    and p["portafolio"] == port), CERO)
        comprueba(f"corte {corte} {port}: total = suma por intermediario = V(t)",
                  tot["valor"] == suma == serie[(corte, port)]["valor"])
v7 = valuacion[(f("2026-10-07"), "BI261008")]
comprueba("07/10 BI261008 (d = 1) usa la tasa a 28 dias del 01/10 (6.01)",
          v7["d"] == 1 and v7["inf_fecha_colocacion"] == f("2026-10-01") and v7["inf_tasa"] == D("6.01"))
comprueba("la colocacion del 15/10 no rige ninguna valuacion",
          all(v["inf_fecha_colocacion"] < f("2026-10-15") and v["sup_fecha_colocacion"] < f("2026-10-15")
              for v in valuacion.values()))
comprueba("P2: r = 0 del 11/09 al 13/09 (denominador 0)",
          all(serie[(f(s), "Secundario")]["r"] == 0 for s in ("2026-09-11", "2026-09-12", "2026-09-13")))

# =====================================================================
# 8. Rechazos esperados (RF-28, RF-26a, RF-05, RF-09)
# =====================================================================


def evalua_transaccion(c):
    """Aplica a una transaccion candidata las reglas de rechazo, en orden."""
    if not (INT_INI <= c["fecha"] <= INT_FIN):
        return "rechazar", "RD-07 y criterio 3 de RF-05: fecha fuera del intervalo de las semillas", None, None
    if c["ins"] in cetes and c["fecha"] >= VENC[c["ins"]]:
        return "rechazar", "criterio 2 de RF-26a: fecha igual o posterior al vencimiento de la emision", None, None
    neg = saldos_negativos(txs + [c])
    if neg:
        t, par, s = neg
        return "rechazar", "RF-28: deja negativo el saldo del instrumento con el intermediario dentro del portafolio", t, s
    return "aceptar", "", None, None


rechazos = []
for cnd in lee("candidatos_rechazo.csv"):     # entradas: N1 a N8 (no se cargan; se intentan registrar)
    fila_r = dict(cnd)
    if cnd["caso"] == "transaccion":
        c = {"ref": cnd["id"], "port": cnd["portafolio_nombre"], "inter": cnd["intermediario_nombre"],
             "ins": cnd["instrumento_clave"], "tipo": cnd["tipo"], "fecha": f(cnd["fecha_concertacion"]),
             "n": int(cnd["cantidad"]), "p": D(cnd["precio"]), "imp": D(cnd["importe_comisiones"]), "seq": 10_000}
        res, regla, t_neg, s_neg = evalua_transaccion(c)
    elif cnd["caso"] == "periodo":
        a, b = f(cnd["periodo_inicio"]), f(cnd["periodo_fin"])
        if b < a:
            regla = "criterio 3 de RF-09: fecha final anterior a la inicial"
        elif not (INT_INI <= a - timedelta(1) and b <= INT_FIN):
            regla = "criterio 3 de RF-09: fechas fuera de las semillas"
        else:
            regla = ""
        res, t_neg, s_neg = ("rechazar" if regla else "aceptar"), None, None
    else:
        raise ValueError(f"caso desconocido en candidatos_rechazo.csv: {cnd['caso']}")
    fila_r.update({"resultado_esperado": res, "regla": regla, "fecha_saldo_negativo": t_neg,
                   "saldo_resultante": s_neg})
    rechazos.append(fila_r)

for x in rechazos:
    comprueba(f"{x['id']} se rechaza", x["resultado_esperado"] == "rechazar", x["regla"])

# caso positivo C1 (archivo aparte: no es una transaccion por registrar). T11 y T12, ya cargadas, se
# aceptan porque las compras van antes que las ventas el mismo dia; con la venta primero, T12 dejaria
# el saldo en negativo.
t11, t12 = tx_ref["T11"], tx_ref["T12"]
par_c1 = (t11["port"], t11["ins"], t11["inter"])
dia_c1 = t11["fecha"]
saldo_previo = sum(x["n"] if x["tipo"] == "compra" else -x["n"] for x in txs
                   if (x["port"], x["ins"], x["inter"]) == par_c1 and x["fecha"] < dia_c1)
compras_c1 = sum(x["n"] for x in txs if (x["port"], x["ins"], x["inter"]) == par_c1 and x["fecha"] == dia_c1
                 and x["tipo"] == "compra")
ventas_c1 = sum(x["n"] for x in txs if (x["port"], x["ins"], x["inter"]) == par_c1 and x["fecha"] == dia_c1
                and x["tipo"] == "venta")
positivos = [{
    "id": "C1", "criterio": "RF-08 crit. 3 y RF-28 (caso positivo)", "refs": f"{t11['ref']} y {t12['ref']}",
    "portafolio_nombre": par_c1[0], "intermediario_nombre": par_c1[2], "instrumento_clave": par_c1[1],
    "fecha_concertacion": dia_c1, "saldo_previo": saldo_previo, "compras_del_dia": compras_c1,
    "ventas_del_dia": ventas_c1, "saldo_resultante": saldo_previo + compras_c1 - ventas_c1,
    "saldo_si_ventas_antes_que_compras": saldo_previo - ventas_c1,
    "resultado_esperado": "aceptar" if saldos_negativos(txs) is None else "rechazar",
    "regla": "compras antes que ventas el mismo dia",
    "motivo_esperado": f"{t11['ref']} y {t12['ref']} (ya cargadas) se aceptan: {saldo_previo} + {compras_c1} - "
                       f"{ventas_c1} = {saldo_previo + compras_c1 - ventas_c1}; un validador que aplique la venta "
                       f"antes que la compra veria {saldo_previo} - {ventas_c1} = {saldo_previo - ventas_c1} y "
                       f"rechazaria {t12['ref']}"}]
comprueba("C1: T11 y T12 se aceptan (saldo 40) y con la venta primero el saldo seria negativo",
          positivos[0]["resultado_esperado"] == "aceptar" and positivos[0]["saldo_resultante"] >= 0
          and positivos[0]["saldo_si_ventas_antes_que_compras"] < 0)

# =====================================================================
# 9. Salidas
# =====================================================================
escribe(ESP / "transacciones.csv",
        ["ref", "tipo", "monto", "costo_por_titulo", "ingreso_por_titulo", "aportacion", "retiro"],
        [calc_tx[x["ref"]] for x in txs])
escribe(ESP / "valuacion_cetes.csv",
        ["fecha", "instrumento_clave", "vencimiento", "d", "caso", "inf_plazo_nominal", "inf_plazo_efectivo",
         "inf_tasa", "inf_fecha_colocacion", "sup_plazo_nominal", "sup_plazo_efectivo", "sup_tasa",
         "sup_fecha_colocacion", "r_por_ciento_anual", "p_sin_redondear", "p"],
        list(valuacion.values()))
escribe(ESP / "precios_usados.csv", ["fecha", "instrumento_clave", "fecha_cierre", "precio", "sin_cierre_ese_dia"],
        precios_usados)
escribe(ESP / "posiciones.csv",
        ["nivel", "fecha_corte", "portafolio", "instrumento_clave", "intermediario", "tiene_transacciones",
         "titulos", "costo_unitario", "costo_total", "precio", "fecha_precio", "d", "r_por_ciento_anual",
         "fecha_colocacion_inf", "fecha_colocacion_sup", "valor", "resultado_no_realizado"], posiciones)
escribe(ESP / "serie_diaria.csv",
        ["fecha", "portafolio", "valor", "aportaciones", "retiros_ventas", "retiros_vencimientos", "retiros",
         "r", "r_por_ciento", "indice", "maximo", "caida"],
        [serie[(t, p)] for p in portafolios for t in DIAS])
escribe(ESP / "indice_por_periodo.csv", ["periodo", "fecha", "r", "indice", "maximo", "caida"], indices)
escribe(ESP / "indicadores.csv",
        ["periodo", "portafolio", "inicio", "fin", "fecha_base", "dias", "valor_base", "valor_fin",
         "costo_total_fin", "resultado_no_realizado_fin", "twr", "twr_por_ciento", "maxima_caida",
         "maxima_caida_por_ciento", "fecha_pico", "fecha_valle"], indicadores)
escribe(RAIZ / "rechazos_rf28.csv",
        ["id", "criterio", "caso", "portafolio_nombre", "intermediario_nombre", "instrumento_clave", "tipo",
         "fecha_concertacion", "cantidad", "precio", "importe_comisiones", "periodo_inicio", "periodo_fin",
         "resultado_esperado", "regla", "fecha_saldo_negativo", "saldo_resultante", "motivo_esperado"], rechazos)
escribe(RAIZ / "casos_positivos.csv",
        ["id", "criterio", "refs", "portafolio_nombre", "intermediario_nombre", "instrumento_clave",
         "fecha_concertacion", "saldo_previo", "compras_del_dia", "ventas_del_dia", "saldo_resultante",
         "saldo_si_ventas_antes_que_compras", "resultado_esperado", "regla", "motivo_esperado"], positivos)

# =====================================================================
# 10. Resumen en consola
# =====================================================================
print("Entradas validas: %d transacciones, %d precios, %d tasas" % (len(txs), len(filas_precio), len(tasas)))
print("Valuaciones de CETES: %d; distancia minima de P al empate: %s unidades del 7o decimal (%s, %s)"
      % (len(valuacion), format(distancia_minima_al_empate[0], ".6f"), distancia_minima_al_empate[1],
         distancia_minima_al_empate[2]))
print("\nCortes (valor | costo total | resultado):")
for p in posiciones:
    if p["nivel"] == "portafolio":
        print("  %s %-10s %14s %14s %12s" % (p["fecha_corte"], p["portafolio"], format(p["valor"], ",.4f"),
                                             format(p["costo_total"], ",.4f"), format(p["resultado_no_realizado"], ",.4f")))
print("\nIndicadores:")
for x in indicadores:
    print("  %-5s %s..%s  TWR %12s %%  MDD %12s %%  pico %s  valle %s" % (
        x["periodo"], x["inicio"], x["fin"], format(x["twr_por_ciento"], ".6f"),
        format(x["maxima_caida_por_ciento"], ".6f"), x["fecha_pico"], x["fecha_valle"]))
print("\nComprobaciones:")
for nombre, ok, det in chk:
    print("  [%s] %s %s" % ("OK" if ok else "FALLA", nombre, ("" if ok else det)))
if not all(ok for _, ok, _ in chk):
    sys.exit(2)
