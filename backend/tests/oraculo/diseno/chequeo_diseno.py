"""Chequeo CUALITATIVO del diseno del escenario de 5.2 (no es el oraculo).

Solo verifica propiedades del diseno: saldos no negativos (RF-28), forma de la
caida y la recuperacion del indice, dias sin cierre, valores de d y nodos de la
curva usados por cada valuacion de CETES. Las cifras del oraculo se calculan
aparte, a mano, en la hoja de calculo.
Uso: python -I chequeo_diseno.py <ruta tasas_cf107.csv>
"""
import csv
import sys
from datetime import date, timedelta
from decimal import Decimal as D, ROUND_HALF_UP, getcontext

getcontext().prec = 28

def f(s):
    d, m, a = s.split("/")
    return date(int(a), int(m), int(d))

# ---- tasas
tasas = []  # (fecha_col, plazo_nom, tasa, plazo_ef)
with open(sys.argv[1], encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        y, m, d = r["fecha_colocacion"].split("-")
        tasas.append((date(int(y), int(m), int(d)), int(r["plazo_nominal"]), D(r["tasa"]), int(r["plazo_efectivo"])))

def curva(t):
    nodos = {}
    for fc, pn, ta, pe in tasas:
        if fc <= t and (pn not in nodos or fc > nodos[pn][0]):
            nodos[pn] = (fc, ta, pe)
    return sorted(((pe, ta, pn, fc) for pn, (fc, ta, pe) in nodos.items()))

def tasa_d(t, dd):
    c = curva(t)
    if dd <= c[0][0]:
        return c[0][1], "extremo inf (%d, col %s)" % (c[0][2], c[0][3]), c
    if dd >= c[-1][0]:
        return c[-1][1], "extremo sup", c
    for (p1, r1, n1, f1), (p2, r2, n2, f2) in zip(c, c[1:]):
        if p1 <= dd <= p2:
            if dd == p1:
                return r1, "nodo %d (ef %d, col %s)" % (n1, p1, f1), c
            if dd == p2:
                return r2, "nodo %d (ef %d, col %s)" % (n2, p2, f2), c
            return r1 + (r2 - r1) * D(dd - p1) / D(p2 - p1), "interp %d(ef %d)-%d(ef %d), col %s/%s" % (n1, p1, n2, p2, f1, f2), c

def P(t, venc):
    dd = (venc - t).days
    r, como, _ = tasa_d(t, dd)
    p = (D(10) / (1 + r / 100 * D(dd) / 360)).quantize(D("0.0000001"), ROUND_HALF_UP)
    return p, dd, como

# ---- catalogo
VENC = {"BI261008": f("08/10/2026"), "BI261105": f("05/11/2026"),
        "BI261217": f("17/12/2026"), "BI270318": f("18/03/2027")}

dias_hab = ["10/09", "11/09", "14/09", "15/09", "17/09", "18/09", "21/09", "22/09", "23/09", "24/09", "25/09",
            "28/09", "29/09", "30/09", "01/10", "02/10", "05/10", "06/10", "07/10", "08/10", "09/10", "12/10",
            "13/10", "14/10"]
ACC = "100.20 101.85 103.40 104.75 102.10 98.65 95.30 92.15 90.4250 92.80 96.15 99.70 103.25 107.10 105.35 103.90 101.65 102.80 104.95 107.40 109.15 110.30 109.20 111.05".split()
ETF = "50.10 50.62 51.05 51.48 50.71 49.34 48.02 46.87 46.15 46.93 48.06 49.21 50.37 51.64 51.12 50.58 49.83 50.24 50.96 51.77 52.31 52.68 52.29 52.95".split()
FIB = "24.8000 25.0150 25.2375 25.4100 24.9650 24.3025 23.6400 23.1175 22.8500 23.1250 23.6800 24.1100 24.5525 25.0300 24.8450 24.6125 24.3700 24.5150 24.8875 - 25.2400 25.4650 25.3100 25.6225".split()
cierres = {"DEMOACC": {}, "DEMOETF": {}, "DEMOFIB": {}}
for i, dh in enumerate(dias_hab):
    t = f(dh + "/2026")
    assert t.weekday() < 5 and t != f("16/09/2026")
    cierres["DEMOACC"][t] = D(ACC[i])
    cierres["DEMOETF"][t] = D(ETF[i])
    if FIB[i] != "-":
        cierres["DEMOFIB"][t] = D(FIB[i])

def cierre(ins, t):
    fs = [x for x in cierres[ins] if x <= t]
    u = max(fs)
    return cierres[ins][u], u

# ---- transacciones: id, port, inter, ins, tipo, fecha, titulos, precio, importe
def pcol(fc, venc):
    return P(f(fc), VENC[venc])[0]

TX = [
    ("T01", "P1", "Casa A", "DEMOACC", "compra", "10/09/2026", 200, D("99.95"), D("57.97")),
    ("T02", "P1", "Casa B", "DEMOETF", "compra", "10/09/2026", 100, D("50.05"), D("14.51")),
    ("T03", "P1", "Casa A", "BI261008", "compra", "10/09/2026", 1500, pcol("10/09/2026", "BI261008"), D("0")),
    ("T04", "P1", "Casa B", "BI261008", "compra", "10/09/2026", 1000, pcol("10/09/2026", "BI261008"), D("0")),
    ("T05", "P1", "Casa A", "DEMOFIB", "compra", "11/09/2026", 400, D("24.9825"), D("28.98")),
    ("T06", "P1", "Casa B", "DEMOACC", "compra", "14/09/2026", 100, D("103.10"), D("29.90")),
    ("T07", "P2", "Casa A", "DEMOACC", "compra", "14/09/2026", 150, D("103.60"), D("45.07")),
    ("T08", "P1", "Casa A", "BI261217", "compra", "17/09/2026", 1000, pcol("17/09/2026", "BI261217"), D("0")),
    ("T09", "P1", "Casa B", "BI270318", "compra", "17/09/2026", 500, pcol("17/09/2026", "BI270318"), D("0")),
    ("T10", "P1", "Casa A", "DEMOFIB", "venta", "22/09/2026", 400, D("23.2075"), D("26.92")),
    ("T11", "P1", "Casa B", "DEMOETF", "compra", "25/09/2026", 60, D("47.90"), D("8.33")),
    ("T12", "P1", "Casa B", "DEMOETF", "venta", "25/09/2026", 120, D("48.10"), D("16.74")),
    ("T13", "P1", "Casa A", "BI261008", "venta", "01/10/2026", 500, P(f("01/10/2026"), VENC["BI261008"])[0], D("0")),
    ("T14", "P1", "Casa A", "DEMOACC", "venta", "02/10/2026", 80, D("104.20"), D("24.17")),
    ("T15", "P1", "Casa A", "DEMOFIB", "compra", "05/10/2026", 300, D("24.4125"), D("21.24")),
    ("T16", "P1", "Casa B", "BI261105", "compra", "08/10/2026", 1000, pcol("08/10/2026", "BI261105"), D("0")),
]
for tx in TX:
    monto = tx[6] * tx[7]
    if tx[3] not in VENC:
        assert tx[8] == (monto * D("0.0029")).quantize(D("0.01"), ROUND_HALF_UP), (tx[0], monto * D("0.0029"))
    assert tx[7] == tx[7].quantize(D("0.0000001"))

# ---- saldos por portafolio/intermediario/instrumento y costo promedio
def estado(port, t):
    s = {}
    for tid, p, it, ins, tp, fe, n, pr, imp in sorted(TX, key=lambda x: (f(x[5]), 0 if x[4] == "compra" else 1)):
        if p != port or f(fe) > t:
            continue
        k = (ins, it)
        n0, c0 = s.get(k, (0, D(0)))
        if tp == "compra":
            cu = (n * pr + imp) / n
            s[k] = (n0 + n, (n0 * c0 + n * cu) / (n0 + n))
        else:
            assert n0 - n >= 0, ("RF-28", tid)
            s[k] = (n0 - n, c0 if n0 - n > 0 else D(0))
    for (ins, it) in list(s):
        if ins in VENC and t >= VENC[ins]:
            s[(ins, it)] = (0, s[(ins, it)][1])
    return s

def valor(port, t, detalle=False):
    tot = D(0)
    for (ins, it), (n, cu) in sorted(estado(port, t).items()):
        if n == 0:
            continue
        if ins in VENC:
            p, dd, como = P(t, VENC[ins])
            extra = "d=%d %s" % (dd, como)
        else:
            p, u = cierre(ins, t)
            extra = "cierre del %s" % u
        tot += n * p
        if detalle:
            print("   %-8s %-6s n=%5d cu=%.4f p=%.7f %s" % (ins, it, n, cu, p, extra))
    return tot

def flujos(port, t):
    A = D(0); R = D(0)
    for tid, p, it, ins, tp, fe, n, pr, imp in TX:
        if p == port and f(fe) == t:
            if tp == "compra":
                A += n * pr + imp
            else:
                R += n * pr - imp
    for ins, v in VENC.items():
        if v == t:
            est = estado(port, t - timedelta(1))
            R += sum(n for (i2, _), (n, _) in est.items() if i2 == ins) * D(10)
    return A, R

# saldos nunca negativos (estado() lo comprueba en cada fecha)
t = f("10/09/2026")
while t <= f("14/10/2026"):
    estado("P1", t); estado("P2", t)
    t += timedelta(1)

for corte in ["13/09/2026", "16/09/2026", "07/10/2026", "08/10/2026", "14/10/2026"]:
    print("corte", corte)
    valor("P1", f(corte), True)

def serie(port, ini, fin):
    t = f(ini) - timedelta(1)
    Vp = valor(port, t)
    I = D(1); mx = D(1); mdd = D(0); pico = valle = None; picoc = t
    filas = []
    t += timedelta(1)
    while t <= f(fin):
        V = valor(port, t); A, R = flujos(port, t)
        den = Vp + A
        r = (V + R) / den - 1 if den != 0 else D(0)
        I *= 1 + r
        if I > mx:
            mx = I; picoc = t
        dd = I / mx - 1
        if dd < mdd:
            mdd = dd; pico = picoc; valle = t
        filas.append((t, V, A, R, r, I, dd))
        Vp = V; t += timedelta(1)
    return I - 1, mdd, pico, valle, filas

for port, ini, fin in [("P1", "11/09/2026", "14/10/2026"), ("P1", "11/09/2026", "30/09/2026"),
                       ("P1", "01/10/2026", "14/10/2026"), ("P2", "11/09/2026", "14/10/2026"),
                       ("P2", "01/10/2026", "14/10/2026")]:
    twr, mdd, pico, valle, filas = serie(port, ini, fin)
    print(port, ini, fin, "TWR~%.2f%%" % (twr * 100), "MDD~%.2f%%" % (mdd * 100), "pico", pico, "valle", valle)
    if port == "P1" and ini == "11/09/2026" and fin == "14/10/2026":
        for t, V, A, R, r, I, dd in filas:
            print("  ", t, t.strftime("%a"), "V=%.0f A=%.0f R=%.0f I=%.4f dd=%.4f" % (V, A, R, I, dd))
