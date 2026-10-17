"""Genera backend/04_cargar_semillas.sql, la Instalación de semillas del MVP (SRS, 4.2).

Las semillas salen de las entradas del conjunto de referencia congelado (backend/tests/oraculo/entradas,
SRS 5.2), para que la base y el oráculo usen exactamente los mismos datos: el catálogo (RF-04), los
precios sintéticos (RF-07), las tasas reales del CF107 (RF-30) y su procedencia (RF-31). Agrega la versión
de demostración del aviso de privacidad (RF-12; P-20), sin la cual nadie puede registrarse (CU-01).

Antes de escribir, valida las reglas que la base no puede comprobar sola (4.3, «Aplicación: Cargas de
datos de mercado»): ningún precio de CETES (RD-04), precios solo en días con operaciones de 2026 y dentro del
intervalo de las semillas (RF-07, crit. 2), cada plazo con una colocación anterior al intervalo (RF-30,
crit. 1), sin repetidos (RD-19) y conteos de cada carga iguales a sus filas. Si algo falla, no escribe nada.

Uso, desde la raíz del repositorio:  python backend/semillas/genera_semillas.py
"""
import csv
import hashlib
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ENTRADAS = RAIZ / "backend" / "tests" / "oraculo" / "entradas"
AVISO = Path(__file__).with_name("aviso_privacidad_demo.md")
SALIDA = RAIZ / "backend" / "04_cargar_semillas.sql"

# Diferencias con las entradas del oráculo, que no cambian ninguna cifra de 5.2 (02_crear_esquema.sql):
# - carga_datos.resultado es lista cerrada ('exitosa', 'fallida'); el oráculo escribe «completa».
# - carga_datos.obtenida_en es obligatoria (P-34, recomendado): fecha en que se construyó la semilla sintética
#   y en que se consultó el CF107 (15/10/2026); la hora no se registró y se fija a las 00:00 de la Ciudad de México.
# - carga_datos.valores_sustituidos toma el valor por omisión del esquema ('[]') en vez del {} del oráculo: la
#   primera carga no sustituye nada, y su forma sigue ⟦decidir⟧ en 4.4 (P-34).
RESULTADO = {"completa": "exitosa"}
OBTENIDA_EN = {"C-PRECIOS": "2026-10-15 00:00:00-06", "C-TASAS": "2026-10-15 00:00:00-06"}
AVISO_VIGENTE_DESDE = "2026-10-16 00:00:00-06"
PLAZOS = {28, 91, 182, 364, 728}


def leer(nombre):
    with open(ENTRADAS / nombre, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def decimales(valor):
    exp = Decimal(valor).normalize().as_tuple().exponent
    return max(0, -exp)


def lit(valor):
    """Literal SQL de texto, o NULL si está vacío."""
    if valor is None or valor == "":
        return "NULL"
    return "'" + str(valor).replace("'", "''") + "'"


errores = []


def exigir(condicion, mensaje):
    if not condicion:
        errores.append(mensaje)


parametros = {p["parametro"]: p["valor"] for p in leer("parametros.csv")}
inicio = date.fromisoformat(parametros["intervalo_semillas_inicio"])
fin = date.fromisoformat(parametros["intervalo_semillas_fin"])
sin_operaciones = {date.fromisoformat(d["fecha"]) for d in leer("dias_sin_operaciones_2026.csv")}

instrumentos = leer("instrumentos.csv")
fuentes = leer("fuentes_datos.csv")
licencias = leer("versiones_licencia.csv")
cargas = {c["carga"]: c for c in leer("cargas_datos.csv")}
precios = leer("precios.csv")
tasas = leer("tasas.csv")
aviso = AVISO.read_text(encoding="utf-8-sig").strip()

# Catálogo (RF-04; RD-04; P-14)
claves = [i["clave"] for i in instrumentos]
exigir(len(claves) == len(set(claves)), "claves de instrumento repetidas")
clase_de = {}
for i in instrumentos:
    clase_de[i["clave"]] = i["clase_activo"]
    exigir(i["clase_activo"] in {"accion", "etf", "fibra", "cetes"}, f"{i['clave']}: clase inválida")
    exigir(i["divisa"] == "MXN", f"{i['clave']}: divisa distinta de MXN (P-02)")
    es_cetes = i["clase_activo"] == "cetes"
    exigir((i["de_demostracion"] == "true") == (not es_cetes), f"{i['clave']}: marca de demostración incorrecta (RF-04)")
    if es_cetes:
        venc = date.fromisoformat(i["vencimiento"])
        exigir(i["clave"] == "BI" + venc.strftime("%y%m%d"), f"{i['clave']}: la clave no corresponde al vencimiento (RD-04)")
        exigir(Decimal(i["valor_nominal"]) == Decimal("10.00"), f"{i['clave']}: valor nominal distinto de 10.00")
    else:
        exigir(not re.fullmatch(r"BI\d{6}", i["clave"]), f"{i['clave']}: clave ficticia con forma de emisión")

# Fuentes y licencias (RF-31). Lo que se copia sin comillas al SQL debe ser true, false o un entero.
for fila in instrumentos + fuentes:
    exigir(fila["de_demostracion"] in {"true", "false"}, f"{fila.get('clave') or fila['nombre']}: de_demostracion no es true ni false")
nombres_fuente = {f["nombre"] for f in fuentes}
exigir(len(nombres_fuente) == len(fuentes), "fuentes de datos repetidas")
versiones = {(lic["fuente_nombre"], lic["version"]) for lic in licencias}
exigir(len(versiones) == len(licencias), "versiones de licencia repetidas")
exigir(len(cargas) == len(leer("cargas_datos.csv")), "cargas repetidas")
for lic in licencias:
    exigir(lic["fuente_nombre"] in nombres_fuente, f"licencia de una fuente desconocida: {lic['fuente_nombre']}")
for nombre, c in cargas.items():
    exigir(c["fuente_nombre"] in nombres_fuente, f"{nombre}: fuente desconocida")
    exigir((c["fuente_nombre"], c["version"]) in versiones, f"{nombre}: su versión de licencia no existe")
    exigir(re.fullmatch(r"[0-9]+", c["observaciones_omitidas"]) is not None, f"{nombre}: observaciones omitidas inválidas")
    exigir(c["valores_sustituidos"] in {"", "{}", "[]"}, f"{nombre}: trae valores sustituidos, que el script no carga")
    exigir(c["origen"] == "semilla", f"{nombre}: origen distinto de semilla")
    exigir(c["resultado"] in RESULTADO, f"{nombre}: resultado sin equivalente en el esquema: {c['resultado']}")
    exigir(nombre in OBTENIDA_EN, f"{nombre}: falta su fecha de obtención")
    exigir(date.fromisoformat(c["fecha_inicial"]) <= date.fromisoformat(c["fecha_final"]), f"{nombre}: intervalo invertido")
cp = cargas.get("C-PRECIOS", {})
exigir((cp.get("fecha_inicial"), cp.get("fecha_final")) == (inicio.isoformat(), fin.isoformat()),
       "C-PRECIOS: su intervalo no es el de las semillas (parametros.csv)")

# Precios sintéticos (RF-07, crit. 2; RD-04; RD-06; RD-13; RD-19)
vistos = set()
for p in precios:
    clave, fecha = p["instrumento_clave"], date.fromisoformat(p["fecha"])
    exigir(clave in clase_de, f"precio de un instrumento desconocido: {clave}")
    exigir(clase_de.get(clave) != "cetes", f"{clave} {fecha}: precio de una emisión de CETES (RD-04)")
    exigir(inicio <= fecha <= fin, f"{clave} {fecha}: fuera del intervalo de las semillas")
    exigir(fecha not in sin_operaciones, f"{clave} {fecha}: día sin operaciones de 2026")
    exigir(Decimal(p["precio"]) > 0 and decimales(p["precio"]) <= 7, f"{clave} {fecha}: precio inválido")
    exigir((clave, fecha) not in vistos, f"{clave} {fecha}: precio repetido (RD-19)")
    exigir(p["carga"] == "C-PRECIOS" and p["fuente_nombre"] == cargas["C-PRECIOS"]["fuente_nombre"], f"{clave} {fecha}: carga o fuente inesperada")
    vistos.add((clave, fecha))

# Tasas reales del CF107 (RF-30; RD-13; RD-18; RD-19)
vistas = set()
for t in tasas:
    plazo, fecha = int(t["plazo_nominal"]), date.fromisoformat(t["fecha_colocacion"])
    exigir(plazo in PLAZOS, f"plazo nominal inválido: {plazo}")
    exigir(int(t["plazo_efectivo"]) > 0, f"{plazo} {fecha}: sin plazo efectivo (RD-18)")
    exigir(decimales(t["valor"]) <= 5, f"{plazo} {fecha}: más de 5 decimales (RD-13)")
    exigir((plazo, fecha) not in vistas, f"{plazo} {fecha}: tasa repetida (RD-19)")
    exigir(t["carga"] == "C-TASAS" and t["fuente_nombre"] == cargas["C-TASAS"]["fuente_nombre"], f"{plazo} {fecha}: carga o fuente inesperada")
    vistas.add((plazo, fecha))
for plazo in PLAZOS:
    exigir(any(p == plazo and f < inicio for p, f in vistas), f"el plazo {plazo} no tiene una colocación anterior al intervalo (RF-30, crit. 1)")

# Conteos de cada carga (RNF-09)
exigir(int(cargas["C-PRECIOS"]["observaciones_incorporadas"]) == len(precios), "C-PRECIOS: el conteo no coincide con los precios")
exigir(int(cargas["C-TASAS"]["observaciones_incorporadas"]) == len(tasas), "C-TASAS: el conteo no coincide con las tasas")
exigir(aviso != "" and "$aviso$" not in aviso + "$", "aviso de privacidad vacío, con el delimitador $aviso$ o terminado en $aviso")

if errores:
    raise SystemExit("No se generó el script; las entradas violan estas reglas:\n- " + "\n- ".join(errores))


def filas(valores):
    return ",\n".join("    (" + ", ".join(v) + ")" for v in valores)


def huella(lineas):
    """md5 de las líneas unidas con saltos de línea: la misma cadena que arma en SQL la comprobación final."""
    return hashlib.md5("\n".join(lineas).encode("utf-8")).hexdigest()


huella_precios = huella(f"{p['instrumento_clave']} {date.fromisoformat(p['fecha']).isoformat()} {Decimal(p['precio']):f}"
                        for p in sorted(precios, key=lambda p: (p["instrumento_clave"], date.fromisoformat(p["fecha"]))))
huella_tasas = huella(f"{int(t['plazo_nominal'])} {date.fromisoformat(t['fecha_colocacion']).isoformat()} {Decimal(t['valor']):f} {t['unidad']} {int(t['plazo_efectivo'])}"
                      for t in sorted(tasas, key=lambda t: (int(t["plazo_nominal"]), date.fromisoformat(t["fecha_colocacion"]))))
huella_aviso = huella([aviso])


cps, cts = cargas["C-PRECIOS"], cargas["C-TASAS"]
sql = f"""-- =============================================================================
-- Proyecto 077 · Paso 4: semillas del MVP (Instalación de semillas, SRS 4.2)
-- =============================================================================
-- GENERADO por backend/semillas/genera_semillas.py desde backend/tests/oraculo/entradas
-- (conjunto de referencia congelado, SRS 5.2). No se edita a mano: se cambia la fuente y se regenera.
--
-- Carga el aviso de privacidad de demostración (RF-12; P-20), las fuentes de datos y sus licencias
-- (RF-31), el catálogo (RF-04): {len(instrumentos)} instrumentos, de ellos {sum(1 for i in instrumentos if i['clase_activo'] == 'cetes')} emisiones de CETES;
-- {len(precios)} precios sintéticos de demostración (RF-07) del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y}, y {len(tasas)} tasas reales del
-- CF107 del Banco de México (RF-30). No carga usuarios: las cuentas de prueba se crean con la aplicación.
--
-- Cómo se ejecuta, después del paso 2 (y del 3, que exige las tablas vacías), como el dueño de las tablas:
--
--     psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/04_cargar_semillas.sql
--
-- Va en una sola transacción. Volver a ejecutarlo no duplica ni altera nada (RF-07, crit. 1; RD-19):
-- cada fila se inserta solo si no existe. Al final comprueba que cada carga tenga sus filas, que sus precios
-- y tasas y el texto del aviso sean los de las entradas y que el catálogo esté completo; si no, se deshace todo.
-- Diferencias con las entradas del oráculo, que no cambian ninguna cifra de 5.2: resultado «completa» →
-- 'exitosa' (lista cerrada del esquema); obtenida_en, que el esquema exige y el oráculo no trae, = 15/10/2026
-- 00:00 de la Ciudad de México (la hora no se registró; P-34), y valores_sustituidos = '[]', el valor por
-- omisión del esquema, en vez del {{}} del oráculo (su forma sigue ⟦decidir⟧ en 4.4; P-34).
-- =============================================================================

\\set ON_ERROR_STOP on
\\encoding UTF8

BEGIN;

SET LOCAL search_path = public;

DO $$
BEGIN
    IF to_regclass('public.carga_datos') IS NULL THEN
        RAISE EXCEPTION 'No existe el esquema del Proyecto 077: ejecuta antes 02_crear_esquema.sql.';
    END IF;
END
$$;

-- 1. Aviso de privacidad de demostración (RF-12; P-20). Texto en backend/semillas/aviso_privacidad_demo.md.
INSERT INTO version_aviso (texto, vigente_desde)
VALUES ($aviso${aviso}$aviso$, {lit(AVISO_VIGENTE_DESDE)})
ON CONFLICT (vigente_desde) DO NOTHING;

-- 2. Fuentes de datos (RF-31).
INSERT INTO fuente_datos (nombre, direccion, de_demostracion)
VALUES
{filas([lit(f['nombre']), lit(f['direccion']), f['de_demostracion']] for f in fuentes)}
ON CONFLICT (nombre) DO NOTHING;

-- 3. Versiones de sus licencias (RF-31, crit. 1; R-05; D-03).
INSERT INTO version_licencia (fuente_id, version, usos_permitidos, obligacion_suprimir, atribucion)
SELECT f.id, v.version, v.usos, v.obligacion, v.atribucion
FROM (VALUES
{filas([lit(l['fuente_nombre']), lit(l['version']), lit(l['usos_permitidos']), lit(l['obligacion_suprimir']), lit(l['atribucion'])] for l in licencias)}
) AS v (fuente, version, usos, obligacion, atribucion)
JOIN fuente_datos f ON f.nombre = v.fuente
ON CONFLICT (fuente_id, version) DO NOTHING;

-- 4. Catálogo (RF-04; RD-04): instrumentos y, de los CETES, su emisión.
INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
VALUES
{filas([lit(i['clave']), lit(i['nombre']), lit(i['divisa']), lit(i['clase_activo']), i['de_demostracion']] for i in instrumentos)}
ON CONFLICT (clave) DO NOTHING;

INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
SELECT i.id, i.clave, i.clase_activo, v.vencimiento::date, v.valor_nominal::numeric
FROM (VALUES
{filas([lit(i['clave']), lit(i['vencimiento']), lit(i['valor_nominal'])] for i in instrumentos if i['clase_activo'] == 'cetes')}
) AS v (clave, vencimiento, valor_nominal)
JOIN instrumento i ON i.clave = v.clave
ON CONFLICT (instrumento_id) DO NOTHING;

-- 5. Cargas (RD-17; RNF-09): una por fuente e intervalo; no se repite al volver a ejecutar.
INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial, fecha_final,
                         resultado, observaciones_incorporadas, observaciones_omitidas)
SELECT f.id, l.id, v.origen, v.obtenida_en::timestamptz, v.fecha_inicial::date, v.fecha_final::date,
       v.resultado, v.incorporadas, v.omitidas
FROM (VALUES
{filas([lit(c['fuente_nombre']), lit(c['version']), lit(c['origen']), lit(OBTENIDA_EN[n]), lit(c['fecha_inicial']), lit(c['fecha_final']), lit(RESULTADO[c['resultado']]), c['observaciones_incorporadas'], c['observaciones_omitidas']] for n, c in cargas.items())}
) AS v (fuente, version, origen, obtenida_en, fecha_inicial, fecha_final, resultado, incorporadas, omitidas)
JOIN fuente_datos f ON f.nombre = v.fuente
JOIN version_licencia l ON l.fuente_id = f.id AND l.version = v.version
WHERE NOT EXISTS (
    SELECT 1 FROM carga_datos c
    WHERE c.fuente_id = f.id AND c.origen = v.origen
      AND c.fecha_inicial = v.fecha_inicial::date AND c.fecha_final = v.fecha_final::date
);

-- 6. Precios de cierre sintéticos (RF-07; RD-19), ligados a su carga.
INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
SELECT i.id, v.fecha::date, v.precio::numeric, c.id, c.fuente_id
FROM (VALUES
{filas([lit(p['instrumento_clave']), lit(p['fecha']), lit(p['precio'])] for p in precios)}
) AS v (clave, fecha, precio)
JOIN instrumento i ON i.clave = v.clave
JOIN fuente_datos f ON f.nombre = {lit(cps['fuente_nombre'])}
JOIN carga_datos c ON c.fuente_id = f.id AND c.origen = 'semilla'
                  AND c.fecha_inicial = {lit(cps['fecha_inicial'])} AND c.fecha_final = {lit(cps['fecha_final'])}
ON CONFLICT (instrumento_id, fecha, fuente_id) DO NOTHING;

-- 7. Tasas de las subastas primarias de CETES del CF107 (RF-30; RD-18; RD-19).
--    Fuente: Banco de México, https://www.banxico.org.mx
INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
SELECT v.plazo, v.fecha::date, v.valor::numeric, v.unidad, v.efectivo, c.id
FROM (VALUES
{filas([t['plazo_nominal'], lit(t['fecha_colocacion']), lit(t['valor']), lit(t['unidad']), t['plazo_efectivo']] for t in tasas)}
) AS v (plazo, fecha, valor, unidad, efectivo)
JOIN fuente_datos f ON f.nombre = {lit(cts['fuente_nombre'])}
JOIN carga_datos c ON c.fuente_id = f.id AND c.origen = 'semilla'
                  AND c.fecha_inicial = {lit(cts['fecha_inicial'])} AND c.fecha_final = {lit(cts['fecha_final'])}
ON CONFLICT (plazo_nominal, fecha_colocacion) DO NOTHING;

-- 8. Comprobación: si falta algo o no coincide con las entradas, la transacción se deshace. Cuenta lo que
--    quedó ligado a la carga de cada semilla (no a su fuente) y compara una huella (md5) de sus filas y del
--    aviso, para no dar por buenas filas de otra carga, cargas repetidas, otros valores ni otro texto del aviso.
DO $$
DECLARE
    c_precios bigint[] := ARRAY(SELECT c.id FROM carga_datos c JOIN fuente_datos f ON f.id = c.fuente_id
                                WHERE f.nombre = {lit(cps['fuente_nombre'])} AND c.origen = 'semilla'
                                  AND c.fecha_inicial = {lit(cps['fecha_inicial'])} AND c.fecha_final = {lit(cps['fecha_final'])});
    c_tasas   bigint[] := ARRAY(SELECT c.id FROM carga_datos c JOIN fuente_datos f ON f.id = c.fuente_id
                                WHERE f.nombre = {lit(cts['fuente_nombre'])} AND c.origen = 'semilla'
                                  AND c.fecha_inicial = {lit(cts['fecha_inicial'])} AND c.fecha_final = {lit(cts['fecha_final'])});
    n_precios bigint := (SELECT count(*) FROM precio_cierre WHERE carga_id = ANY (c_precios));
    n_tasas   bigint := (SELECT count(*) FROM tasa_referencia WHERE carga_id = ANY (c_tasas));
    h_precios text := (SELECT md5(convert_to(string_agg(i.clave || ' ' || to_char(p.fecha::timestamp, 'YYYY-MM-DD') || ' ' || p.precio::text,
                                                        chr(10) ORDER BY i.clave COLLATE "C", p.fecha), 'UTF8'))
                       FROM precio_cierre p JOIN instrumento i ON i.id = p.instrumento_id WHERE p.carga_id = ANY (c_precios));
    h_tasas   text := (SELECT md5(convert_to(string_agg(t.plazo_nominal || ' ' || to_char(t.fecha_colocacion::timestamp, 'YYYY-MM-DD') || ' ' || t.valor::text
                                                        || ' ' || t.unidad || ' ' || t.plazo_efectivo, chr(10) ORDER BY t.plazo_nominal, t.fecha_colocacion), 'UTF8'))
                       FROM tasa_referencia t WHERE t.carga_id = ANY (c_tasas));
    n_catalogo bigint := (SELECT count(*) FROM instrumento WHERE (clave, clase_activo) IN ({", ".join(f"({lit(i['clave'])}, {lit(i['clase_activo'])})" for i in instrumentos)}));
    n_emisiones bigint := (SELECT count(*) FROM emision_cetes WHERE clave IN ({", ".join(lit(i['clave']) for i in instrumentos if i['clase_activo'] == 'cetes')}));
    h_aviso   text := (SELECT md5(convert_to(texto, 'UTF8')) FROM version_aviso WHERE vigente_desde = {lit(AVISO_VIGENTE_DESDE)}::timestamptz);
BEGIN
    IF h_aviso IS DISTINCT FROM {lit(huella_aviso)} THEN
        RAISE EXCEPTION 'La base ya tiene otro texto del aviso vigente desde %.', {lit(AVISO_VIGENTE_DESDE)}
            USING HINT = 'Un texto nuevo es una versión nueva del aviso (RF-12): cambia AVISO_VIGENTE_DESDE en backend/semillas/genera_semillas.py y regenera este script.';
    END IF;
    IF cardinality(c_precios) <> 1 OR cardinality(c_tasas) <> 1 THEN
        RAISE EXCEPTION 'Hay % cargas de precios y % de tasas con la fuente y el intervalo de las semillas; debe haber una de cada una.',
            cardinality(c_precios), cardinality(c_tasas)
            USING HINT = 'Revisa carga_datos; si sobra una carga, recrea la base y ejecuta de nuevo los pasos 2 a 4.';
    END IF;
    IF n_precios <> {len(precios)} OR n_tasas <> {len(tasas)} OR n_catalogo <> {len(instrumentos)}
       OR n_emisiones <> {sum(1 for i in instrumentos if i['clase_activo'] == 'cetes')}
       OR h_precios IS DISTINCT FROM {lit(huella_precios)} OR h_tasas IS DISTINCT FROM {lit(huella_tasas)} THEN
        RAISE EXCEPTION 'Semillas incompletas o distintas de las entradas: % precios y % tasas en sus cargas (iguales a las entradas: %, %), % instrumentos, % emisiones.',
            n_precios, n_tasas, h_precios IS NOT DISTINCT FROM {lit(huella_precios)}, h_tasas IS NOT DISTINCT FROM {lit(huella_tasas)},
            n_catalogo, n_emisiones
            USING HINT = 'Las semillas solo cambian con una versión nueva de 5.2 (RD-21): recrea la base y ejecuta de nuevo los pasos 2 a 4.';
    END IF;
    RAISE NOTICE 'Semillas listas: % precios, % tasas, % instrumentos (% emisiones de CETES), {len(cargas)} cargas y el aviso de demostración.',
        n_precios, n_tasas, n_catalogo, n_emisiones;
END
$$;

COMMIT;
"""
SALIDA.write_text(sql, encoding="utf-8", newline="\n")
print(f"Generado {SALIDA.relative_to(RAIZ)}: {len(instrumentos)} instrumentos, {len(precios)} precios, {len(tasas)} tasas, aviso de {len(aviso.split())} palabras.")
