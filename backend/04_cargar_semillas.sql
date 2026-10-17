-- =============================================================================
-- Proyecto 077 · Paso 4: semillas del MVP (Instalación de semillas, SRS 4.2)
-- =============================================================================
-- GENERADO por backend/semillas/genera_semillas.py desde backend/tests/oraculo/entradas
-- (conjunto de referencia congelado, SRS 5.2). No se edita a mano: se cambia la fuente y se regenera.
--
-- Carga el aviso de privacidad de demostración (RF-12; P-20), las fuentes de datos y sus licencias
-- (RF-31), el catálogo (RF-04): 7 instrumentos, de ellos 4 emisiones de CETES;
-- 71 precios sintéticos de demostración (RF-07) del 10/09/2026 al 14/10/2026, y 32 tasas reales del
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
-- omisión del esquema, en vez del {} del oráculo (su forma sigue ⟦decidir⟧ en 4.4; P-34).
-- =============================================================================

\set ON_ERROR_STOP on
\encoding UTF8

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
VALUES ($aviso$AVISO DE PRIVACIDAD DE DEMOSTRACIÓN

Esta plataforma es un prototipo de demostración. No captures datos reales: regístrate con un correo ficticio (por ejemplo, nombre@example.com) y una contraseña que no uses en ningún otro sitio, y captura solo portafolios, intermediarios y transacciones ficticios.

Responsable del tratamiento: pendiente de designar. Este aviso es una versión de demostración y no sustituye a un aviso de privacidad definitivo.

Datos que se tratan: tu correo electrónico y tu contraseña, que se guarda solo en forma no reversible, y los datos financieros y patrimoniales que tú captures: portafolios, intermediarios y transacciones de compra y venta.

Finalidad: registrar tus compras y ventas para consolidar las posiciones que tienes con tus distintos intermediarios y calcular, solo para ti, el valor de mercado y el resultado no realizado de cada posición y de cada portafolio, y el rendimiento ponderado por tiempo y la máxima caída de cada portafolio. La información no constituye asesoría de inversión, y las valuaciones son estimaciones informativas, no precios oficiales. Tus datos no se transfieren a terceros ni se usan con fines publicitarios.

Consentimiento: para registrarte debes marcar la casilla con la que consientes expresamente el tratamiento de tus datos personales, financieros y patrimoniales descrito en este aviso. Se guardan el momento y el medio en que lo otorgaste, y la versión del aviso vigente en ese momento.

Revocación: puedes revocar tu consentimiento en cualquier momento desde tu cuenta. Al hacerlo, la revocación queda registrada, tu sesión termina, y tu cuenta y toda tu información quedan bloqueadas de inmediato. La revocación es definitiva: no podrás volver a iniciar sesión ni reactivar la cuenta. Tu información se suprime al concluir el bloqueo, cuyo plazo está pendiente de definir.

Derechos de acceso, rectificación, cancelación y oposición (ARCO): el medio para ejercerlos está pendiente de definir.

Cambios a este aviso: cada cambio se publica como una versión nueva, con la fecha desde la que rige.$aviso$, '2026-10-16 00:00:00-06')
ON CONFLICT (vigente_desde) DO NOTHING;

-- 2. Fuentes de datos (RF-31).
INSERT INTO fuente_datos (nombre, direccion, de_demostracion)
VALUES
    ('Banco de México', 'https://www.banxico.org.mx', false),
    ('Semilla sintetica de demostracion 077', NULL, true)
ON CONFLICT (nombre) DO NOTHING;

-- 3. Versiones de sus licencias (RF-31, crit. 1; R-05; D-03).
INSERT INTO version_licencia (fuente_id, version, usos_permitidos, obligacion_suprimir, atribucion)
SELECT f.id, v.version, v.usos, v.obligacion, v.atribucion
FROM (VALUES
    ('Banco de México', '1', 'Reproducir y utilizar la información que publica el Banco de México, con la sola condición de mencionar la fuente y su dirección de Internet (R-05; D-03)', NULL, 'Fuente: Banco de México, https://www.banxico.org.mx'),
    ('Semilla sintetica de demostracion 077', '1', 'Datos sintéticos creados para el Proyecto 077: uso libre dentro de la aplicación y sus pruebas, solo como datos de demostración', NULL, 'Datos de demostración: precios sintéticos, no son precios reales')
) AS v (fuente, version, usos, obligacion, atribucion)
JOIN fuente_datos f ON f.nombre = v.fuente
ON CONFLICT (fuente_id, version) DO NOTHING;

-- 4. Catálogo (RF-04; RD-04): instrumentos y, de los CETES, su emisión.
INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
VALUES
    ('DEMOACC', 'Acción de demostración', 'MXN', 'accion', true),
    ('DEMOETF', 'ETF de demostración', 'MXN', 'etf', true),
    ('DEMOFIB', 'FIBRA de demostración', 'MXN', 'fibra', true),
    ('BI261008', 'CETES con vencimiento el 08/10/2026', 'MXN', 'cetes', false),
    ('BI261105', 'CETES con vencimiento el 05/11/2026', 'MXN', 'cetes', false),
    ('BI261217', 'CETES con vencimiento el 17/12/2026', 'MXN', 'cetes', false),
    ('BI270318', 'CETES con vencimiento el 18/03/2027', 'MXN', 'cetes', false)
ON CONFLICT (clave) DO NOTHING;

INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
SELECT i.id, i.clave, i.clase_activo, v.vencimiento::date, v.valor_nominal::numeric
FROM (VALUES
    ('BI261008', '2026-10-08', '10.00'),
    ('BI261105', '2026-11-05', '10.00'),
    ('BI261217', '2026-12-17', '10.00'),
    ('BI270318', '2027-03-18', '10.00')
) AS v (clave, vencimiento, valor_nominal)
JOIN instrumento i ON i.clave = v.clave
ON CONFLICT (instrumento_id) DO NOTHING;

-- 5. Cargas (RD-17; RNF-09): una por fuente e intervalo; no se repite al volver a ejecutar.
INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial, fecha_final,
                         resultado, observaciones_incorporadas, observaciones_omitidas)
SELECT f.id, l.id, v.origen, v.obtenida_en::timestamptz, v.fecha_inicial::date, v.fecha_final::date,
       v.resultado, v.incorporadas, v.omitidas
FROM (VALUES
    ('Semilla sintetica de demostracion 077', '1', 'semilla', '2026-10-15 00:00:00-06', '2026-09-10', '2026-10-14', 'exitosa', 71, 0),
    ('Banco de México', '1', 'semilla', '2026-10-15 00:00:00-06', '2026-08-27', '2026-10-15', 'exitosa', 32, 0)
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
    ('DEMOACC', '2026-09-10', '100.20'),
    ('DEMOACC', '2026-09-11', '101.85'),
    ('DEMOACC', '2026-09-14', '103.40'),
    ('DEMOACC', '2026-09-15', '104.75'),
    ('DEMOACC', '2026-09-17', '102.10'),
    ('DEMOACC', '2026-09-18', '98.65'),
    ('DEMOACC', '2026-09-21', '95.30'),
    ('DEMOACC', '2026-09-22', '92.15'),
    ('DEMOACC', '2026-09-23', '90.4250'),
    ('DEMOACC', '2026-09-24', '92.80'),
    ('DEMOACC', '2026-09-25', '96.15'),
    ('DEMOACC', '2026-09-28', '99.70'),
    ('DEMOACC', '2026-09-29', '103.25'),
    ('DEMOACC', '2026-09-30', '107.10'),
    ('DEMOACC', '2026-10-01', '105.35'),
    ('DEMOACC', '2026-10-02', '103.90'),
    ('DEMOACC', '2026-10-05', '101.65'),
    ('DEMOACC', '2026-10-06', '102.80'),
    ('DEMOACC', '2026-10-07', '104.95'),
    ('DEMOACC', '2026-10-08', '107.40'),
    ('DEMOACC', '2026-10-09', '109.15'),
    ('DEMOACC', '2026-10-12', '110.30'),
    ('DEMOACC', '2026-10-13', '109.20'),
    ('DEMOACC', '2026-10-14', '111.05'),
    ('DEMOETF', '2026-09-10', '50.10'),
    ('DEMOETF', '2026-09-11', '50.62'),
    ('DEMOETF', '2026-09-14', '51.05'),
    ('DEMOETF', '2026-09-15', '51.48'),
    ('DEMOETF', '2026-09-17', '50.71'),
    ('DEMOETF', '2026-09-18', '49.34'),
    ('DEMOETF', '2026-09-21', '48.02'),
    ('DEMOETF', '2026-09-22', '46.87'),
    ('DEMOETF', '2026-09-23', '46.15'),
    ('DEMOETF', '2026-09-24', '46.93'),
    ('DEMOETF', '2026-09-25', '48.06'),
    ('DEMOETF', '2026-09-28', '49.21'),
    ('DEMOETF', '2026-09-29', '50.37'),
    ('DEMOETF', '2026-09-30', '51.64'),
    ('DEMOETF', '2026-10-01', '51.12'),
    ('DEMOETF', '2026-10-02', '50.58'),
    ('DEMOETF', '2026-10-05', '49.83'),
    ('DEMOETF', '2026-10-06', '50.24'),
    ('DEMOETF', '2026-10-07', '50.96'),
    ('DEMOETF', '2026-10-08', '51.77'),
    ('DEMOETF', '2026-10-09', '52.31'),
    ('DEMOETF', '2026-10-12', '52.68'),
    ('DEMOETF', '2026-10-13', '52.29'),
    ('DEMOETF', '2026-10-14', '52.95'),
    ('DEMOFIB', '2026-09-10', '24.8000'),
    ('DEMOFIB', '2026-09-11', '25.0150'),
    ('DEMOFIB', '2026-09-14', '25.2375'),
    ('DEMOFIB', '2026-09-15', '25.4100'),
    ('DEMOFIB', '2026-09-17', '24.9650'),
    ('DEMOFIB', '2026-09-18', '24.3025'),
    ('DEMOFIB', '2026-09-21', '23.6400'),
    ('DEMOFIB', '2026-09-22', '23.1175'),
    ('DEMOFIB', '2026-09-23', '22.8500'),
    ('DEMOFIB', '2026-09-24', '23.1250'),
    ('DEMOFIB', '2026-09-25', '23.6800'),
    ('DEMOFIB', '2026-09-28', '24.1100'),
    ('DEMOFIB', '2026-09-29', '24.5525'),
    ('DEMOFIB', '2026-09-30', '25.0300'),
    ('DEMOFIB', '2026-10-01', '24.8450'),
    ('DEMOFIB', '2026-10-02', '24.6125'),
    ('DEMOFIB', '2026-10-05', '24.3700'),
    ('DEMOFIB', '2026-10-06', '24.5150'),
    ('DEMOFIB', '2026-10-07', '24.8875'),
    ('DEMOFIB', '2026-10-09', '25.2400'),
    ('DEMOFIB', '2026-10-12', '25.4650'),
    ('DEMOFIB', '2026-10-13', '25.3100'),
    ('DEMOFIB', '2026-10-14', '25.6225')
) AS v (clave, fecha, precio)
JOIN instrumento i ON i.clave = v.clave
JOIN fuente_datos f ON f.nombre = 'Semilla sintetica de demostracion 077'
JOIN carga_datos c ON c.fuente_id = f.id AND c.origen = 'semilla'
                  AND c.fecha_inicial = '2026-09-10' AND c.fecha_final = '2026-10-14'
ON CONFLICT (instrumento_id, fecha, fuente_id) DO NOTHING;

-- 7. Tasas de las subastas primarias de CETES del CF107 (RF-30; RD-18; RD-19).
--    Fuente: Banco de México, https://www.banxico.org.mx
INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
SELECT v.plazo, v.fecha::date, v.valor::numeric, v.unidad, v.efectivo, c.id
FROM (VALUES
    (28, '2026-08-27', '6.13000', 'por ciento anual', 28),
    (91, '2026-08-27', '6.60000', 'por ciento anual', 91),
    (182, '2026-08-27', '6.72000', 'por ciento anual', 175),
    (728, '2026-08-27', '7.87000', 'por ciento anual', 707),
    (28, '2026-09-03', '6.49000', 'por ciento anual', 28),
    (91, '2026-09-03', '6.54000', 'por ciento anual', 91),
    (182, '2026-09-03', '6.69000', 'por ciento anual', 182),
    (364, '2026-09-03', '7.00000', 'por ciento anual', 350),
    (28, '2026-09-10', '6.25000', 'por ciento anual', 28),
    (91, '2026-09-10', '6.56000', 'por ciento anual', 91),
    (182, '2026-09-10', '6.78000', 'por ciento anual', 175),
    (728, '2026-09-10', '7.94000', 'por ciento anual', 693),
    (28, '2026-09-17', '6.25000', 'por ciento anual', 28),
    (91, '2026-09-17', '6.66000', 'por ciento anual', 91),
    (182, '2026-09-17', '6.90000', 'por ciento anual', 182),
    (364, '2026-09-17', '7.24000', 'por ciento anual', 363),
    (28, '2026-09-24', '6.15000', 'por ciento anual', 28),
    (91, '2026-09-24', '6.59000', 'por ciento anual', 91),
    (182, '2026-09-24', '6.91000', 'por ciento anual', 175),
    (728, '2026-09-24', '8.01000', 'por ciento anual', 679),
    (28, '2026-10-01', '6.01000', 'por ciento anual', 28),
    (91, '2026-10-01', '6.73000', 'por ciento anual', 91),
    (182, '2026-10-01', '7.01000', 'por ciento anual', 182),
    (364, '2026-10-01', '7.44000', 'por ciento anual', 349),
    (28, '2026-10-08', '6.09000', 'por ciento anual', 28),
    (91, '2026-10-08', '6.78000', 'por ciento anual', 91),
    (182, '2026-10-08', '6.91000', 'por ciento anual', 175),
    (728, '2026-10-08', '7.98000', 'por ciento anual', 721),
    (28, '2026-10-15', '6.25000', 'por ciento anual', 28),
    (91, '2026-10-15', '6.55000', 'por ciento anual', 91),
    (182, '2026-10-15', '6.79000', 'por ciento anual', 182),
    (364, '2026-10-15', '7.11000', 'por ciento anual', 364)
) AS v (plazo, fecha, valor, unidad, efectivo)
JOIN fuente_datos f ON f.nombre = 'Banco de México'
JOIN carga_datos c ON c.fuente_id = f.id AND c.origen = 'semilla'
                  AND c.fecha_inicial = '2026-08-27' AND c.fecha_final = '2026-10-15'
ON CONFLICT (plazo_nominal, fecha_colocacion) DO NOTHING;

-- 8. Comprobación: si falta algo o no coincide con las entradas, la transacción se deshace. Cuenta lo que
--    quedó ligado a la carga de cada semilla (no a su fuente) y compara una huella (md5) de sus filas y del
--    aviso, para no dar por buenas filas de otra carga, cargas repetidas, otros valores ni otro texto del aviso.
DO $$
DECLARE
    c_precios bigint[] := ARRAY(SELECT c.id FROM carga_datos c JOIN fuente_datos f ON f.id = c.fuente_id
                                WHERE f.nombre = 'Semilla sintetica de demostracion 077' AND c.origen = 'semilla'
                                  AND c.fecha_inicial = '2026-09-10' AND c.fecha_final = '2026-10-14');
    c_tasas   bigint[] := ARRAY(SELECT c.id FROM carga_datos c JOIN fuente_datos f ON f.id = c.fuente_id
                                WHERE f.nombre = 'Banco de México' AND c.origen = 'semilla'
                                  AND c.fecha_inicial = '2026-08-27' AND c.fecha_final = '2026-10-15');
    n_precios bigint := (SELECT count(*) FROM precio_cierre WHERE carga_id = ANY (c_precios));
    n_tasas   bigint := (SELECT count(*) FROM tasa_referencia WHERE carga_id = ANY (c_tasas));
    h_precios text := (SELECT md5(convert_to(string_agg(i.clave || ' ' || to_char(p.fecha::timestamp, 'YYYY-MM-DD') || ' ' || p.precio::text,
                                                        chr(10) ORDER BY i.clave COLLATE "C", p.fecha), 'UTF8'))
                       FROM precio_cierre p JOIN instrumento i ON i.id = p.instrumento_id WHERE p.carga_id = ANY (c_precios));
    h_tasas   text := (SELECT md5(convert_to(string_agg(t.plazo_nominal || ' ' || to_char(t.fecha_colocacion::timestamp, 'YYYY-MM-DD') || ' ' || t.valor::text
                                                        || ' ' || t.unidad || ' ' || t.plazo_efectivo, chr(10) ORDER BY t.plazo_nominal, t.fecha_colocacion), 'UTF8'))
                       FROM tasa_referencia t WHERE t.carga_id = ANY (c_tasas));
    n_catalogo bigint := (SELECT count(*) FROM instrumento WHERE (clave, clase_activo) IN (('DEMOACC', 'accion'), ('DEMOETF', 'etf'), ('DEMOFIB', 'fibra'), ('BI261008', 'cetes'), ('BI261105', 'cetes'), ('BI261217', 'cetes'), ('BI270318', 'cetes')));
    n_emisiones bigint := (SELECT count(*) FROM emision_cetes WHERE clave IN ('BI261008', 'BI261105', 'BI261217', 'BI270318'));
    h_aviso   text := (SELECT md5(convert_to(texto, 'UTF8')) FROM version_aviso WHERE vigente_desde = '2026-10-16 00:00:00-06'::timestamptz);
BEGIN
    IF h_aviso IS DISTINCT FROM 'b00c17f34657d28740dc9605a7323676' THEN
        RAISE EXCEPTION 'La base ya tiene otro texto del aviso vigente desde %.', '2026-10-16 00:00:00-06'
            USING HINT = 'Un texto nuevo es una versión nueva del aviso (RF-12): cambia AVISO_VIGENTE_DESDE en backend/semillas/genera_semillas.py y regenera este script.';
    END IF;
    IF cardinality(c_precios) <> 1 OR cardinality(c_tasas) <> 1 THEN
        RAISE EXCEPTION 'Hay % cargas de precios y % de tasas con la fuente y el intervalo de las semillas; debe haber una de cada una.',
            cardinality(c_precios), cardinality(c_tasas)
            USING HINT = 'Revisa carga_datos; si sobra una carga, recrea la base y ejecuta de nuevo los pasos 2 a 4.';
    END IF;
    IF n_precios <> 71 OR n_tasas <> 32 OR n_catalogo <> 7
       OR n_emisiones <> 4
       OR h_precios IS DISTINCT FROM 'a848c98e152d2685e0b8e93640339990' OR h_tasas IS DISTINCT FROM 'ca0ec06cc4c7c8b9e70a175d3f3a7c57' THEN
        RAISE EXCEPTION 'Semillas incompletas o distintas de las entradas: % precios y % tasas en sus cargas (iguales a las entradas: %, %), % instrumentos, % emisiones.',
            n_precios, n_tasas, h_precios IS NOT DISTINCT FROM 'a848c98e152d2685e0b8e93640339990', h_tasas IS NOT DISTINCT FROM 'ca0ec06cc4c7c8b9e70a175d3f3a7c57',
            n_catalogo, n_emisiones
            USING HINT = 'Las semillas solo cambian con una versión nueva de 5.2 (RD-21): recrea la base y ejecuta de nuevo los pasos 2 a 4.';
    END IF;
    RAISE NOTICE 'Semillas listas: % precios, % tasas, % instrumentos (% emisiones de CETES), 2 cargas y el aviso de demostración.',
        n_precios, n_tasas, n_catalogo, n_emisiones;
END
$$;

COMMIT;
