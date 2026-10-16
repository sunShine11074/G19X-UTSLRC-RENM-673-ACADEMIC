"""Extrae las observaciones del cuadro CF107 (SIE, Banxico) de un HTML guardado.

Identifica cada serie por su codigo (id="tablaObservaciones_..._<SERIE>"),
no por su posicion. Une el numero partido "6.15<span ...>000</span>" -> "6.15000".
Uso: python -I parse_cf107.py <archivo.html> [<archivo2.html> ...]
Imprime JSON {archivo: {serie: [[fecha, valor_texto], ...], "_hint": {...}}}
"""
import sys, re, json, html as htmlmod

SERIES = ["SF43936", "SF43939", "SF43942", "SF43945", "SF349785",
          "SF43935", "SF43938", "SF43941", "SF43944", "SF349778"]

def parse(path):
    raw = open(path, "rb").read()
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:
        txt = raw.decode("latin-1")
    out = {}
    hints = {}
    descs = {}
    for s in SERIES:
        pat = re.compile(r'<table[^>]*id="tablaObservaciones_[^"]*_' + s + r'"[^>]*>(.*?)</table>', re.S)
        ms = pat.findall(txt)
        if len(ms) != 1:
            out[s] = {"error": "tablas encontradas: %d" % len(ms)}
            continue
        body = ms[0]
        fechas = re.findall(r'<th[^>]*>\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s*</th>', body)
        celdas = re.findall(r'<td[^>]*tdObservacion[^>]*>(.*?)</td>', body, re.S)
        vals = []
        for c in celdas:
            c2 = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', c, flags=re.S)
            c2 = re.sub(r'<[^>]+>', '', c2)
            c2 = htmlmod.unescape(c2).strip().replace(",", "")
            vals.append(c2)
        if len(fechas) != len(vals):
            out[s] = {"error": "fechas %d vs valores %d" % (len(fechas), len(vals))}
            continue
        out[s] = [[f, v] for f, v in zip(fechas, vals)]
        h = re.search(r"h\('" + s + r"','([^']*)','([^']*)','([^']*)','([^']*)','([^']*)'", txt)
        if h:
            hints[s] = {"frecuencia": htmlmod.unescape(h.group(1)), "unidad": h.group(2),
                        "inicio": h.group(4), "fin": h.group(5)}
        # descripcion de la fila (td.tdDescripcion antes del contenedor de la serie)
        d = re.search(r'tdDescripcion">\s*([^<]*?)\s*</td>\s*<td id="tdContainerDescripcion_[^"]*_' + s + '"', txt, re.S)
        if d:
            descs[s] = htmlmod.unescape(d.group(1)).strip()
    out["_hint"] = hints
    out["_desc"] = descs
    return out

if __name__ == "__main__":
    res = {}
    for p in sys.argv[1:]:
        res[p] = parse(p)
    print(json.dumps(res, ensure_ascii=False, indent=1))
