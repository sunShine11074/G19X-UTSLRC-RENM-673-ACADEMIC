"""Arma datos/tasas_cf107.csv y datos/tasas_cf107_fuentes.csv a partir de:
  - fuentes/cf107_5oct.html (pagina del cuadro CF107 guardada el 5 oct),
  - fuentes/cf107_6oct.html (guardada el 6 oct),
  - fuentes/cf107_15oct.html (pagina publica del cuadro, consultada el 15 oct),
  - fuentes/sie_json/<serie>.json (consultaSerieGrafica.do, datos publicos de la grafica, 15 oct).
Cada serie se identifica por su codigo. Compara todas las fuentes y reporta discrepancias.
Todas las rutas son relativas a la carpeta del oraculo (la que contiene scripts/).
Uso: python -I -B <ruta del oraculo>/scripts/arma_tasas.py [<desde AAAA-MM-DD>, por omision 2026-07-01]
"""
import csv
import datetime as dt
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_cf107 import parse  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / "fuentes"
DATOS = RAIZ / "datos"

PARES = [(28, "SF43936", "SF43935"), (91, "SF43939", "SF43938"), (182, "SF43942", "SF43941"),
         (364, "SF43945", "SF43944"), (728, "SF349785", "SF349778")]

DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-07-01"
HTMLS = [("cf107_5oct.html (5 oct)", FUENTES / "cf107_5oct.html"),
         ("cf107_6oct.html (6 oct)", FUENTES / "cf107_6oct.html"),
         ("cf107_15oct.html (pagina publica, 15 oct)", FUENTES / "cf107_15oct.html")]

def iso(f):  # dd/mm/aaaa -> aaaa-mm-dd
    return f[6:10] + "-" + f[3:5] + "-" + f[0:2]

# obs[serie][fecha] = {fuente: Decimal|None}
obs = {}
for nombre, p in HTMLS:
    d = parse(p)
    for _, st, sp in PARES:
        for s in (st, sp):
            for f, v in d[s]:
                val = None if v == "N/E" else Decimal(v)
                obs.setdefault(s, {}).setdefault(iso(f), {})[nombre] = val

JS = "consultaSerieGrafica.do (JSON publico, 15 oct)"
for _, st, sp in PARES:
    for s in (st, sp):
        j = json.load(open(FUENTES / "sie_json" / (s + ".json"), encoding="utf-8"))
        assert j["serie"] == s, (j["serie"], s)
        for f, v in j["valores"]:
            if f < DESDE:
                continue
            val = None if v == -989898.0 else Decimal(repr(v))
            obs.setdefault(s, {}).setdefault(f, {})[JS] = val

# comparar fuentes
discrep = []
for s, porf in obs.items():
    for f, src in porf.items():
        vals = set(src.values())
        if len(vals) > 1:
            discrep.append((s, f, src))

filas = []
for plazo, st, sp in PARES:
    fechas = sorted(set(obs[st]) | set(obs[sp]))
    for f in fechas:
        if f < DESDE:
            continue
        t = obs[st].get(f, {})
        p = obs[sp].get(f, {})
        tv = [v for v in t.values() if v is not None]
        pv = [v for v in p.values() if v is not None]
        if not tv and not pv:
            continue
        if not tv or not pv:
            discrep.append(("par incompleto", plazo, f, t, p))
            continue
        tasa = tv[0]
        pe = pv[0]
        fuentes = sorted(set(k for k, v in t.items() if v is not None) & set(k for k, v in p.items() if v is not None))
        filas.append({
            "fecha_colocacion": f, "plazo_nominal": plazo,
            "tasa": format(tasa.quantize(Decimal("0.00001")), "f"),  # 5 decimales, como el cuadro CF107 ("6.15" + "000" oculto)
            "plazo_efectivo": int(pe),
            "serie_tasa": st, "serie_plazo": sp,
            "_fuentes": fuentes,
        })

filas.sort(key=lambda r: (r["fecha_colocacion"], r["plazo_nominal"]))
out = DATOS / "tasas_cf107.csv"
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["fecha_colocacion", "plazo_nominal", "tasa", "plazo_efectivo", "serie_tasa", "serie_plazo"])
    for r in filas:
        w.writerow([r["fecha_colocacion"], r["plazo_nominal"], r["tasa"], r["plazo_efectivo"], r["serie_tasa"], r["serie_plazo"]])

out2 = DATOS / "tasas_cf107_fuentes.csv"
with open(out2, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["fecha_colocacion", "plazo_nominal", "fuentes_coincidentes"])
    for r in filas:
        w.writerow([r["fecha_colocacion"], r["plazo_nominal"], " | ".join(r["_fuentes"])])
print("filas:", len(filas), "->", out, "y", out2)
for r in filas:
    print(r["fecha_colocacion"], dt.date.fromisoformat(r["fecha_colocacion"]).strftime("%a"), r["plazo_nominal"], r["tasa"], r["plazo_efectivo"], "|", "; ".join(r["_fuentes"]))
print("discrepancias:", len(discrep))
for x in discrep:
    print("  ", x)
