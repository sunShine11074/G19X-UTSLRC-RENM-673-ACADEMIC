"""Arma datos/dias_sin_operaciones_2026.csv: el calendario COMPLETO de 2026.

Fuente: DOF del 10/12/2025, CNBV, «Disposiciones de caracter general que senalan
los dias del ano 2026 en que las entidades financieras ... deberan cerrar sus
puertas y suspender sus operaciones», art. 1, fracciones I a IX (copia en
fuentes/dof_10dic2025_dias_inhabiles_2026.html). Los festivos se confirmaron con
el Calendario de dias festivos de Grupo BMV, consultado el 15/10/2026.

Una fila por fecha: los 104 sabados y domingos de 2026 (fr. IX) mas los festivos
de las fracciones I a VIII. El 12/12 es festivo y cae en sabado: aparece una vez,
como festivo. Total: 114 fechas.

No calcula ninguna cifra del oraculo. Despues se copia a entradas/ con
scripts/arma_entradas.py.
Uso: python -I -B <ruta del oraculo>/scripts/arma_calendario.py
"""
import csv
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos" / "dias_sin_operaciones_2026.csv"

DOF = ("DOF 10/12/2025, CNBV, Disposiciones de caracter general que señalan los dias del año 2026 en que las "
       "entidades financieras ... deberan cerrar sus puertas y suspender sus operaciones, art. 1 "
       "(https://dof.gob.mx/nota_detalle.php?codigo=5775684&fecha=10/12/2025)")
BMV = ("Grupo BMV, Calendario de Dias Festivos, Dias no laborables BMV 2026 "
       "(https://www.bmv.com.mx/es/grupo-bmv/calendario-de-dias-festivos), consultado 15/10/2026")

FESTIVOS = {
    date(2026, 1, 1): "Año Nuevo (art. 1, fr. I)",
    date(2026, 2, 2): "Primer lunes de febrero, conmemoración del 5 de febrero (fr. II)",
    date(2026, 3, 16): "Tercer lunes de marzo, conmemoración del 21 de marzo (fr. III)",
    date(2026, 4, 2): "Jueves Santo (fr. IV)",
    date(2026, 4, 3): "Viernes Santo (fr. IV)",
    date(2026, 5, 1): "Día del Trabajo (fr. V)",
    date(2026, 9, 16): "Día de la Independencia (fr. VI)",
    date(2026, 11, 2): "Día de Muertos (fr. VII)",
    date(2026, 11, 16): "Tercer lunes de noviembre, conmemoración del 20 de noviembre (fr. VII)",
    date(2026, 12, 12): "Día del empleado bancario (fr. VIII); cae en sábado",
    date(2026, 12, 25): "Navidad (fr. VIII)",
}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

filas = []
t = date(2026, 1, 1)
while t.year == 2026:
    if t in FESTIVOS:
        filas.append([t.isoformat(), DIAS[t.weekday()], "festivo", FESTIVOS[t], f"{DOF} ; {BMV}"])
    elif t.weekday() >= 5:
        filas.append([t.isoformat(), DIAS[t.weekday()], "fin de semana", "Sábados y domingos (art. 1, fr. IX)", DOF])
    t += timedelta(1)

fines = sum(1 for f in filas if f[2] == "fin de semana")
assert fines + sum(1 for t in FESTIVOS if t.weekday() >= 5) == 104, "2026 tiene 104 sabados y domingos"
assert len(filas) == 114, len(filas)

with open(SALIDA, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["fecha", "dia_semana", "tipo", "motivo", "fuente"])
    w.writerows(filas)
print(f"{SALIDA.name}: {len(filas)} fechas ({fines} de fin de semana y {len(FESTIVOS)} festivos, uno en sabado)")
