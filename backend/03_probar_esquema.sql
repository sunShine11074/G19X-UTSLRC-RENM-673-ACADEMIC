-- =============================================================================
-- Proyecto 077 · Paso 3: prueba automática del esquema
-- =============================================================================
-- Comprueba, contra el SRS (3.4, 4.3 y 4.4), la estructura que deja
-- 02_crear_esquema.sql, cada restricción de la base con casos positivos y
-- negativos, y cada privilegio de app_077 (con SET LOCAL ROLE app_077).
-- Cada caso nombra su regla (RD-nn, RF-nn o el apartado del SRS); los
-- negativos exigen el SQLSTATE esperado (23505, 23514, 23503, 23502, 42501,
-- 428C9, 22008, 22P02) y, cuando lo hay, el nombre de la restricción o la
-- columna.
--
-- Cómo se ejecuta, después del paso 2 y antes de la Instalación de semillas
-- (exige las 13 tablas vacías), conectado a la base de la aplicación como el
-- rol dueño de las tablas (en el equipo de desarrollo, postgres):
--
--     psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f 03_probar_esquema.sql
--
-- Todo ocurre dentro de BEGIN … ROLLBACK: no deja datos ni cambios, salvo que
-- las secuencias de identidad avanzan (no son transaccionales), así que los
-- id siguientes saltan valores, lo que 4.4 admite. Los datos de prueba usan
-- nombres, claves y fechas fijos que chocarían con las semillas; por eso, si
-- las tablas ya tienen filas, se detiene antes de probar nada. El primer caso
-- que falle detiene psql con error (código de salida 3) y dice qué esperaba y
-- qué obtuvo. Si todo pasa, imprime cuántos casos pasaron.
-- Los datos de prueba son ficticios (S-04).
-- =============================================================================

\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

SET LOCAL search_path = public;

-- Condición previa: las 13 tablas están vacías (justo después del paso 2 y
-- antes de la Instalación de semillas). Una tabla que falte la reporta la
-- sección A.
DO $$
DECLARE
    t   text;
    hay boolean;
BEGIN
    FOREACH t IN ARRAY ARRAY['usuario', 'version_aviso', 'consentimiento', 'portafolio',
                             'intermediario', 'instrumento', 'emision_cetes', 'transaccion',
                             'fuente_datos', 'version_licencia', 'carga_datos', 'precio_cierre',
                             'tasa_referencia']
    LOOP
        CONTINUE WHEN to_regclass(format('public.%I', t)) IS NULL;
        EXECUTE format('SELECT EXISTS (SELECT FROM public.%I)', t) INTO hay;
        IF hay THEN
            RAISE EXCEPTION 'La tabla % ya tiene filas: 03_probar_esquema.sql se ejecuta sobre el esquema vacío, justo después del paso 2 y antes de la Instalación de semillas.', t
                USING HINT = 'Para probar el esquema, ejecuta 02 y 03 en una base vacía aparte.';
        END IF;
    END LOOP;
END
$$;

-- -----------------------------------------------------------------------------
-- Herramientas de la prueba (temporales: desaparecen con el ROLLBACK)
-- -----------------------------------------------------------------------------
CREATE TEMP TABLE caso (
    n            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    clase        text NOT NULL,   -- estructura, positivo o negativo
    rol          text NOT NULL,   -- dueño o app_077
    regla        text NOT NULL,
    descripcion  text NOT NULL,
    sqlstate     text
);

-- Identificadores de los datos de prueba, por un nombre corto.
CREATE TEMP TABLE ids (clave text PRIMARY KEY, id bigint NOT NULL);
INSERT INTO pg_temp.ids VALUES ('inexistente', -1);

CREATE FUNCTION pg_temp.id(p_clave text) RETURNS bigint
LANGUAGE plpgsql AS $f$
DECLARE
    v bigint;
BEGIN
    SELECT id INTO v FROM pg_temp.ids WHERE clave = p_clave;
    IF v IS NULL THEN
        RAISE EXCEPTION 'Dato de prueba «%» no registrado', p_clave;
    END IF;
    RETURN v;
END
$f$;

CREATE FUNCTION pg_temp.registra(p_clase text, p_rol text, p_regla text,
                                 p_descripcion text, p_sqlstate text)
RETURNS void
LANGUAGE plpgsql AS $f$
DECLARE
    v_n integer;
BEGIN
    INSERT INTO pg_temp.caso (clase, rol, regla, descripcion, sqlstate)
    VALUES (p_clase, coalesce(p_rol, 'dueño'), p_regla, p_descripcion, p_sqlstate)
    RETURNING n INTO v_n;
    RAISE NOTICE 'ok % % [%] %: %', lpad(v_n::text, 3, '0'),
        rpad(p_clase || coalesce(' ' || p_sqlstate, ''), 15),
        coalesce(p_rol, 'dueño'), p_regla, p_descripcion;
END
$f$;

-- La sentencia debe aceptarse (positivo). Sus efectos se conservan.
CREATE FUNCTION pg_temp.acepta(p_regla text, p_descripcion text, p_sql text,
                               p_rol text DEFAULT NULL)
RETURNS void
LANGUAGE plpgsql AS $f$
DECLARE
    v_estado  text;
    v_mensaje text;
BEGIN
    BEGIN
        IF p_rol IS NOT NULL THEN
            EXECUTE format('SET LOCAL ROLE %I', p_rol);
        END IF;
        EXECUTE p_sql;
        RESET ROLE;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE, v_mensaje = MESSAGE_TEXT;
        RAISE EXCEPTION 'FALLA (%) %: se esperaba que se aceptara y falló con % (%)',
            p_regla, p_descripcion, v_estado, v_mensaje;
    END;
    PERFORM pg_temp.registra('positivo', p_rol, p_regla, p_descripcion, NULL);
END
$f$;

-- La sentencia debe rechazarse (negativo) con p_estado y, si se da, con la
-- restricción p_objeto (o la columna, si p_estado es 23502). No deja efectos.
CREATE FUNCTION pg_temp.rechaza(p_regla text, p_descripcion text, p_sql text,
                                p_estado text, p_objeto text DEFAULT NULL,
                                p_rol text DEFAULT NULL)
RETURNS void
LANGUAGE plpgsql AS $f$
DECLARE
    v_aceptada    boolean := false;
    v_estado      text;
    v_restriccion text;
    v_columna     text;
    v_mensaje     text;
    v_objeto      text;
BEGIN
    BEGIN
        IF p_rol IS NOT NULL THEN
            EXECUTE format('SET LOCAL ROLE %I', p_rol);
        END IF;
        EXECUTE p_sql;
        v_aceptada := true;
        RAISE EXCEPTION 'aceptada';   -- deshace la sentencia aceptada
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE,
                                v_restriccion = CONSTRAINT_NAME,
                                v_columna = COLUMN_NAME,
                                v_mensaje = MESSAGE_TEXT;
    END;
    IF v_aceptada THEN
        RAISE EXCEPTION 'FALLA (%) %: se esperaba el rechazo % y se aceptó',
            p_regla, p_descripcion, concat_ws(' ', p_estado, p_objeto);
    END IF;
    v_objeto := CASE WHEN v_estado = '23502' THEN v_columna ELSE v_restriccion END;
    IF v_estado <> p_estado OR (p_objeto IS NOT NULL AND v_objeto IS DISTINCT FROM p_objeto) THEN
        RAISE EXCEPTION 'FALLA (%) %: se esperaba % y hubo % (%)',
            p_regla, p_descripcion, concat_ws(' ', p_estado, p_objeto),
            concat_ws(' ', v_estado, nullif(v_objeto, '')), v_mensaje;
    END IF;
    PERFORM pg_temp.registra('negativo', p_rol, p_regla, p_descripcion, p_estado);
END
$f$;

-- La consulta p_sql (un solo valor boolean) debe dar verdadero.
CREATE FUNCTION pg_temp.verifica(p_regla text, p_descripcion text, p_sql text,
                                 p_rol text DEFAULT NULL)
RETURNS void
LANGUAGE plpgsql AS $f$
DECLARE
    v_ok      boolean;
    v_estado  text;
    v_mensaje text;
BEGIN
    BEGIN
        IF p_rol IS NOT NULL THEN
            EXECUTE format('SET LOCAL ROLE %I', p_rol);
        END IF;
        EXECUTE p_sql INTO v_ok;
        RESET ROLE;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE, v_mensaje = MESSAGE_TEXT;
        RAISE EXCEPTION 'FALLA (%) %: la comprobación falló con % (%)',
            p_regla, p_descripcion, v_estado, v_mensaje;
    END;
    IF v_ok IS NOT TRUE THEN
        RAISE EXCEPTION 'FALLA (%) %: la comprobación dio %',
            p_regla, p_descripcion, coalesce(v_ok::text, 'nulo');
    END IF;
    PERFORM pg_temp.registra('positivo', p_rol, p_regla, p_descripcion, NULL);
END
$f$;

-- Comparación de conjuntos: p_esperado y p_real devuelven una columna de
-- texto; lo que falte o sobre hace fallar el caso y se lista.
CREATE FUNCTION pg_temp.coincide(p_regla text, p_descripcion text,
                                 p_esperado text, p_real text)
RETURNS void
LANGUAGE plpgsql AS $f$
DECLARE
    v_dif text;
BEGIN
    EXECUTE format(
        'SELECT string_agg(d, E''\n'' ORDER BY d) FROM ('
        '  SELECT ''falta: '' || x AS d FROM ((%1$s) EXCEPT (%2$s)) f(x)'
        '  UNION ALL'
        '  SELECT ''sobra: '' || x FROM ((%2$s) EXCEPT (%1$s)) s(x)) t',
        p_esperado, p_real)
    INTO v_dif;
    IF v_dif IS NOT NULL THEN
        RAISE EXCEPTION E'FALLA (%) %:\n%', p_regla, p_descripcion, v_dif;
    END IF;
    PERFORM pg_temp.registra('estructura', NULL, p_regla, p_descripcion, NULL);
END
$f$;

-- INSERT de una transacción con los datos de prueba (por omisión, de Ana).
CREATE FUNCTION pg_temp.tx(p_tipo text, p_cantidad text, p_precio text, p_importe text,
                           p_fecha text DEFAULT $$DATE '2026-10-05'$$,
                           p_usuario text DEFAULT 'ana',
                           p_portafolio text DEFAULT 'p_ana',
                           p_intermediario text DEFAULT 'i_ana',
                           p_instrumento text DEFAULT 'demoacc')
RETURNS text
LANGUAGE plpgsql AS $f$
BEGIN
    RETURN format(
        'INSERT INTO transaccion (usuario_id, portafolio_id, intermediario_id, instrumento_id, '
        'tipo, fecha_concertacion, cantidad, precio, importe_comisiones) '
        'VALUES (%s, %s, %s, %s, %L, %s, %s, %s, %s)',
        pg_temp.id(p_usuario), pg_temp.id(p_portafolio), pg_temp.id(p_intermediario),
        pg_temp.id(p_instrumento), p_tipo, p_fecha, p_cantidad, p_precio, p_importe);
END
$f$;

-- =============================================================================
-- A. Estructura: tablas, columnas, restricciones, índices, nombres,
--    comentarios, zona horaria y privilegios
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.verifica('3.4; 4.3 (13 entidades)', 'la tabla desechable ping ya no existe',
        $$SELECT to_regclass('public.ping') IS NULL$$);

    PERFORM pg_temp.coincide('3.4.1; 4.3', 'las 13 tablas del modelo y ninguna otra en public',
        $$VALUES ('usuario'), ('version_aviso'), ('consentimiento'), ('portafolio'),
                 ('intermediario'), ('instrumento'), ('emision_cetes'), ('transaccion'),
                 ('fuente_datos'), ('version_licencia'), ('carga_datos'), ('precio_cierre'),
                 ('tasa_referencia')$$,
        $$SELECT relname::text FROM pg_class
          WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r', 'p', 'v', 'm', 'f')$$);

    PERFORM pg_temp.coincide('4.4', 'columnas: orden, tipo, nulos, identidad y valor por omisión',
        $$VALUES
          ('usuario|1|id|bigint|NOT NULL|always|'),
          ('usuario|2|correo|text|NOT NULL||'),
          ('usuario|3|contrasena_hash|text|NOT NULL||'),
          ('usuario|4|estado|text|NOT NULL||'),
          ('version_aviso|1|id|bigint|NOT NULL|always|'),
          ('version_aviso|2|texto|text|NOT NULL||'),
          ('version_aviso|3|vigente_desde|timestamp with time zone|NOT NULL||'),
          ('consentimiento|1|id|bigint|NOT NULL|always|'),
          ('consentimiento|2|usuario_id|bigint|NOT NULL||'),
          ('consentimiento|3|version_aviso_id|bigint|NOT NULL||'),
          ('consentimiento|4|tipo|text|NOT NULL||'),
          ('consentimiento|5|momento|timestamp with time zone|NOT NULL||now()'),
          ('consentimiento|6|medio|text|NOT NULL||'),
          ('portafolio|1|id|bigint|NOT NULL|always|'),
          ('portafolio|2|usuario_id|bigint|NOT NULL||'),
          ('portafolio|3|nombre|text|NOT NULL||'),
          ('portafolio|4|divisa_base|text|NOT NULL||'),
          ('intermediario|1|id|bigint|NOT NULL|always|'),
          ('intermediario|2|usuario_id|bigint|NOT NULL||'),
          ('intermediario|3|nombre|text|NOT NULL||'),
          ('instrumento|1|id|bigint|NOT NULL|always|'),
          ('instrumento|2|clave|text|NOT NULL||'),
          ('instrumento|3|nombre|text|NOT NULL||'),
          ('instrumento|4|divisa|text|NOT NULL||'),
          ('instrumento|5|clase_activo|text|NOT NULL||'),
          ('instrumento|6|de_demostracion|boolean|NOT NULL||'),
          ('emision_cetes|1|instrumento_id|bigint|NOT NULL||'),
          ('emision_cetes|2|clave|text|NOT NULL||'),
          ('emision_cetes|3|clase_activo|text|NOT NULL||'),
          ('emision_cetes|4|vencimiento|date|NOT NULL||'),
          ('emision_cetes|5|valor_nominal|numeric|NOT NULL||'),
          ('transaccion|1|id|bigint|NOT NULL|always|'),
          ('transaccion|2|usuario_id|bigint|NOT NULL||'),
          ('transaccion|3|portafolio_id|bigint|NOT NULL||'),
          ('transaccion|4|intermediario_id|bigint|NOT NULL||'),
          ('transaccion|5|instrumento_id|bigint|NOT NULL||'),
          ('transaccion|6|tipo|text|NOT NULL||'),
          ('transaccion|7|fecha_concertacion|date|NOT NULL||'),
          ('transaccion|8|cantidad|integer|NOT NULL||'),
          ('transaccion|9|precio|numeric|NOT NULL||'),
          ('transaccion|10|importe_comisiones|numeric|NOT NULL||'),
          ('transaccion|11|registrada_en|timestamp with time zone|NOT NULL||now()'),
          ('fuente_datos|1|id|bigint|NOT NULL|always|'),
          ('fuente_datos|2|nombre|text|NOT NULL||'),
          ('fuente_datos|3|direccion|text|NULL||'),
          ('fuente_datos|4|de_demostracion|boolean|NOT NULL||'),
          ('version_licencia|1|id|bigint|NOT NULL|always|'),
          ('version_licencia|2|fuente_id|bigint|NOT NULL||'),
          ('version_licencia|3|version|text|NOT NULL||'),
          ('version_licencia|4|usos_permitidos|text|NOT NULL||'),
          ('version_licencia|5|obligacion_suprimir|text|NULL||'),
          ('version_licencia|6|atribucion|text|NULL||'),
          ('carga_datos|1|id|bigint|NOT NULL|always|'),
          ('carga_datos|2|fuente_id|bigint|NOT NULL||'),
          ('carga_datos|3|version_licencia_id|bigint|NOT NULL||'),
          ('carga_datos|4|origen|text|NOT NULL||'),
          ('carga_datos|5|obtenida_en|timestamp with time zone|NOT NULL||'),
          ('carga_datos|6|incorporada_en|timestamp with time zone|NOT NULL||now()'),
          ('carga_datos|7|fecha_inicial|date|NOT NULL||'),
          ('carga_datos|8|fecha_final|date|NOT NULL||'),
          ('carga_datos|9|resultado|text|NOT NULL||'),
          ('carga_datos|10|observaciones_incorporadas|integer|NOT NULL||'),
          ('carga_datos|11|observaciones_omitidas|integer|NOT NULL||'),
          ('carga_datos|12|valores_sustituidos|jsonb|NOT NULL||''[]''::jsonb'),
          ('precio_cierre|1|id|bigint|NOT NULL|always|'),
          ('precio_cierre|2|instrumento_id|bigint|NOT NULL||'),
          ('precio_cierre|3|fecha|date|NOT NULL||'),
          ('precio_cierre|4|precio|numeric|NOT NULL||'),
          ('precio_cierre|5|carga_id|bigint|NOT NULL||'),
          ('precio_cierre|6|fuente_id|bigint|NOT NULL||'),
          ('tasa_referencia|1|id|bigint|NOT NULL|always|'),
          ('tasa_referencia|2|plazo_nominal|integer|NOT NULL||'),
          ('tasa_referencia|3|fecha_colocacion|date|NOT NULL||'),
          ('tasa_referencia|4|valor|numeric|NOT NULL||'),
          ('tasa_referencia|5|unidad|text|NOT NULL||'),
          ('tasa_referencia|6|plazo_efectivo|integer|NOT NULL||'),
          ('tasa_referencia|7|carga_id|bigint|NOT NULL||')$$,
        $$SELECT concat_ws('|', c.relname, a.attnum, a.attname,
                           format_type(a.atttypid, a.atttypmod),
                           CASE WHEN a.attnotnull THEN 'NOT NULL' ELSE 'NULL' END,
                           CASE a.attidentity WHEN 'a' THEN 'always' WHEN 'd' THEN 'by default' ELSE '' END,
                           coalesce(pg_get_expr(d.adbin, d.adrelid), ''))
          FROM pg_class c
          JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
          LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
          WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'$$);

    PERFORM pg_temp.coincide('4.3; 4.4', 'llaves primarias y restricciones UNIQUE',
        $$VALUES
          ('usuario|usuario_pk|PRIMARY KEY (id)'),
          ('version_aviso|version_aviso_pk|PRIMARY KEY (id)'),
          ('version_aviso|version_aviso_vigente_desde_uq|UNIQUE (vigente_desde)'),
          ('consentimiento|consentimiento_pk|PRIMARY KEY (id)'),
          ('portafolio|portafolio_pk|PRIMARY KEY (id)'),
          ('portafolio|portafolio_usuario_id_uq|UNIQUE (usuario_id, id)'),
          ('intermediario|intermediario_pk|PRIMARY KEY (id)'),
          ('intermediario|intermediario_usuario_id_uq|UNIQUE (usuario_id, id)'),
          ('instrumento|instrumento_pk|PRIMARY KEY (id)'),
          ('instrumento|instrumento_clave_uq|UNIQUE (clave)'),
          ('instrumento|instrumento_id_clave_clase_uq|UNIQUE (id, clave, clase_activo)'),
          ('emision_cetes|emision_cetes_pk|PRIMARY KEY (instrumento_id)'),
          ('emision_cetes|emision_cetes_vencimiento_uq|UNIQUE (vencimiento)'),
          ('transaccion|transaccion_pk|PRIMARY KEY (id)'),
          ('fuente_datos|fuente_datos_pk|PRIMARY KEY (id)'),
          ('fuente_datos|fuente_datos_nombre_uq|UNIQUE (nombre)'),
          ('version_licencia|version_licencia_pk|PRIMARY KEY (id)'),
          ('version_licencia|version_licencia_fuente_id_uq|UNIQUE (fuente_id, id)'),
          ('version_licencia|version_licencia_version_uq|UNIQUE (fuente_id, version)'),
          ('carga_datos|carga_datos_pk|PRIMARY KEY (id)'),
          ('carga_datos|carga_datos_id_fuente_uq|UNIQUE (id, fuente_id)'),
          ('precio_cierre|precio_cierre_pk|PRIMARY KEY (id)'),
          ('precio_cierre|precio_cierre_instrumento_fecha_fuente_uq|UNIQUE (instrumento_id, fecha, fuente_id)'),
          ('tasa_referencia|tasa_referencia_pk|PRIMARY KEY (id)'),
          ('tasa_referencia|tasa_referencia_plazo_fecha_uq|UNIQUE (plazo_nominal, fecha_colocacion)')$$,
        $$SELECT concat_ws('|', conrelid::regclass, conname, pg_get_constraintdef(oid))
          FROM pg_constraint
          WHERE connamespace = 'public'::regnamespace AND contype IN ('p', 'u')$$);

    PERFORM pg_temp.coincide('4.3 (Relaciones)', 'las 14 llaves foráneas con su acción al eliminar',
        $$VALUES
          ('consentimiento|consentimiento_usuario_fk|FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE'),
          ('consentimiento|consentimiento_version_aviso_fk|FOREIGN KEY (version_aviso_id) REFERENCES version_aviso(id)'),
          ('portafolio|portafolio_usuario_fk|FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE'),
          ('intermediario|intermediario_usuario_fk|FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE'),
          ('emision_cetes|emision_cetes_instrumento_fk|FOREIGN KEY (instrumento_id, clave, clase_activo) REFERENCES instrumento(id, clave, clase_activo)'),
          ('transaccion|transaccion_portafolio_fk|FOREIGN KEY (usuario_id, portafolio_id) REFERENCES portafolio(usuario_id, id) ON DELETE CASCADE'),
          ('transaccion|transaccion_intermediario_fk|FOREIGN KEY (usuario_id, intermediario_id) REFERENCES intermediario(usuario_id, id)'),
          ('transaccion|transaccion_instrumento_fk|FOREIGN KEY (instrumento_id) REFERENCES instrumento(id)'),
          ('version_licencia|version_licencia_fuente_fk|FOREIGN KEY (fuente_id) REFERENCES fuente_datos(id)'),
          ('carga_datos|carga_datos_fuente_fk|FOREIGN KEY (fuente_id) REFERENCES fuente_datos(id)'),
          ('carga_datos|carga_datos_version_licencia_fk|FOREIGN KEY (fuente_id, version_licencia_id) REFERENCES version_licencia(fuente_id, id)'),
          ('precio_cierre|precio_cierre_instrumento_fk|FOREIGN KEY (instrumento_id) REFERENCES instrumento(id)'),
          ('precio_cierre|precio_cierre_carga_fk|FOREIGN KEY (carga_id, fuente_id) REFERENCES carga_datos(id, fuente_id) ON DELETE CASCADE'),
          ('tasa_referencia|tasa_referencia_carga_fk|FOREIGN KEY (carga_id) REFERENCES carga_datos(id) ON DELETE CASCADE')$$,
        $$SELECT concat_ws('|', conrelid::regclass, conname, pg_get_constraintdef(oid))
          FROM pg_constraint
          WHERE connamespace = 'public'::regnamespace AND contype = 'f'$$);

    PERFORM pg_temp.coincide('4.3 (Restricciones e índices); 4.4', 'las 35 restricciones CHECK',
        $$VALUES
          ('usuario|usuario_estado_ck|CHECK ((estado = ANY (ARRAY[''activa''::text, ''bloqueada''::text])))'),
          ('consentimiento|consentimiento_tipo_ck|CHECK ((tipo = ANY (ARRAY[''otorgamiento''::text, ''revocacion''::text])))'),
          ('consentimiento|consentimiento_medio_ck|CHECK ((medio = ''web''::text))'),
          ('portafolio|portafolio_nombre_ck|CHECK ((btrim(nombre) <> ''''::text))'),
          ('portafolio|portafolio_divisa_base_ck|CHECK ((divisa_base = ''MXN''::text))'),
          ('intermediario|intermediario_nombre_ck|CHECK ((btrim(nombre) <> ''''::text))'),
          ('instrumento|instrumento_clase_activo_ck|CHECK ((clase_activo = ANY (ARRAY[''accion''::text, ''etf''::text, ''fibra''::text, ''cetes''::text])))'),
          ('instrumento|instrumento_clave_ck|CHECK (((clase_activo <> ''cetes''::text) OR (clave ~ ''^BI[0-9]{6}$''::text)))'),
          ('instrumento|instrumento_divisa_ck|CHECK ((divisa = ''MXN''::text))'),
          ('instrumento|instrumento_de_demostracion_ck|CHECK ((de_demostracion = (clase_activo <> ''cetes''::text)))'),
          ('emision_cetes|emision_cetes_clase_activo_ck|CHECK ((clase_activo = ''cetes''::text))'),
          ('emision_cetes|emision_cetes_clave_ck|CHECK ((clave = concat(''BI'', to_char((vencimiento)::timestamp without time zone, ''YYMMDD''::text))))'),
          ('emision_cetes|emision_cetes_valor_nominal_ck|CHECK ((valor_nominal = 10.00))'),
          ('emision_cetes|emision_cetes_valor_nominal_escala_ck|CHECK (((min_scale(valor_nominal) <= 2) IS TRUE))'),
          ('transaccion|transaccion_tipo_ck|CHECK ((tipo = ANY (ARRAY[''compra''::text, ''venta''::text])))'),
          ('transaccion|transaccion_fecha_concertacion_ck|CHECK ((fecha_concertacion <= ((registrada_en AT TIME ZONE ''America/Mexico_City''::text))::date))'),
          ('transaccion|transaccion_cantidad_ck|CHECK ((cantidad > 0))'),
          ('transaccion|transaccion_precio_ck|CHECK ((precio > (0)::numeric))'),
          ('transaccion|transaccion_precio_escala_ck|CHECK (((min_scale(precio) <= 7) IS TRUE))'),
          ('transaccion|transaccion_precio_tamano_ck|CHECK ((precio < (''100000000000''::bigint)::numeric))'),
          ('transaccion|transaccion_importe_comisiones_ck|CHECK ((importe_comisiones >= (0)::numeric))'),
          ('transaccion|transaccion_importe_comisiones_escala_ck|CHECK (((min_scale(importe_comisiones) <= 2) IS TRUE))'),
          ('transaccion|transaccion_importe_comisiones_tamano_ck|CHECK ((importe_comisiones < (''10000000000000000''::bigint)::numeric))'),
          ('transaccion|transaccion_importe_venta_ck|CHECK (((tipo = ''compra''::text) OR (importe_comisiones < ((cantidad)::numeric * precio))))'),
          ('carga_datos|carga_datos_origen_ck|CHECK ((origen = ''semilla''::text))'),
          ('carga_datos|carga_datos_resultado_ck|CHECK ((resultado = ANY (ARRAY[''exitosa''::text, ''fallida''::text])))'),
          ('carga_datos|carga_datos_intervalo_ck|CHECK ((fecha_inicial <= fecha_final))'),
          ('carga_datos|carga_datos_observaciones_incorporadas_ck|CHECK ((observaciones_incorporadas >= 0))'),
          ('carga_datos|carga_datos_observaciones_omitidas_ck|CHECK ((observaciones_omitidas >= 0))'),
          ('precio_cierre|precio_cierre_precio_ck|CHECK ((precio > (0)::numeric))'),
          ('precio_cierre|precio_cierre_precio_escala_ck|CHECK (((min_scale(precio) <= 7) IS TRUE))'),
          ('precio_cierre|precio_cierre_precio_tamano_ck|CHECK ((precio < (''100000000000''::bigint)::numeric))'),
          ('tasa_referencia|tasa_referencia_plazo_nominal_ck|CHECK ((plazo_nominal = ANY (ARRAY[28, 91, 182, 364, 728])))'),
          ('tasa_referencia|tasa_referencia_plazo_efectivo_ck|CHECK ((plazo_efectivo > 0))'),
          ('tasa_referencia|tasa_referencia_valor_escala_ck|CHECK (((min_scale(valor) <= 5) IS TRUE))')$$,
        $$SELECT concat_ws('|', conrelid::regclass, conname, pg_get_constraintdef(oid))
          FROM pg_constraint
          WHERE connamespace = 'public'::regnamespace AND contype = 'c'$$);

    PERFORM pg_temp.coincide('4.3 (Restricciones e índices); 3.4.8', 'índices únicos por expresión e índices de lectura y cascada',
        $$VALUES
          ('CREATE UNIQUE INDEX usuario_correo_uq ON public.usuario USING btree (lower(btrim(correo)))'),
          ('CREATE UNIQUE INDEX portafolio_nombre_uq ON public.portafolio USING btree (usuario_id, lower(btrim(nombre)))'),
          ('CREATE UNIQUE INDEX intermediario_nombre_uq ON public.intermediario USING btree (usuario_id, lower(btrim(nombre)))'),
          ('CREATE INDEX consentimiento_usuario_ix ON public.consentimiento USING btree (usuario_id)'),
          ('CREATE INDEX transaccion_portafolio_fecha_ix ON public.transaccion USING btree (usuario_id, portafolio_id, fecha_concertacion)'),
          ('CREATE INDEX precio_cierre_carga_ix ON public.precio_cierre USING btree (carga_id, fuente_id)'),
          ('CREATE INDEX tasa_referencia_carga_ix ON public.tasa_referencia USING btree (carga_id)')$$,
        $$SELECT pg_get_indexdef(i.indexrelid)
          FROM pg_index i JOIN pg_class c ON c.oid = i.indrelid
          WHERE c.relnamespace = 'public'::regnamespace
            AND NOT EXISTS (SELECT FROM pg_constraint k WHERE k.conindid = i.indexrelid)$$);

    PERFORM pg_temp.coincide('Convención del paso 2 (nombres)', 'nombres con sufijo _pk, _fk, _uq, _ck o _ix según su clase',
        $$SELECT NULL::text WHERE false$$,
        $$SELECT conname::text FROM pg_constraint
          WHERE connamespace = 'public'::regnamespace
            AND NOT ((contype = 'p' AND conname ~ '_pk$') OR (contype = 'f' AND conname ~ '_fk$')
                  OR (contype = 'u' AND conname ~ '_uq$') OR (contype = 'c' AND conname ~ '_ck$')
                  OR (contype = 'n' AND conname ~ '_not_null$'))
          UNION ALL
          SELECT ic.relname::text
          FROM pg_index i JOIN pg_class ic ON ic.oid = i.indexrelid
          WHERE ic.relnamespace = 'public'::regnamespace
            AND NOT EXISTS (SELECT FROM pg_constraint k WHERE k.conindid = i.indexrelid)
            AND NOT ((i.indisunique AND ic.relname ~ '_uq$') OR (NOT i.indisunique AND ic.relname ~ '_ix$'))$$);

    PERFORM pg_temp.coincide('4.4', 'cada tabla y cada columna tiene su comentario',
        $$SELECT NULL::text WHERE false$$,
        $$SELECT c.relname || coalesce('.' || a.attname, '')
          FROM pg_class c
          LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
          WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'
            AND (obj_description(c.oid, 'pg_class') IS NULL
                 OR (a.attnum IS NOT NULL AND col_description(c.oid, a.attnum) IS NULL))$$);

    PERFORM pg_temp.verifica('RD-15', 'la base fija la zona America/Mexico_City para sus sesiones',
        $$SELECT 'TimeZone=America/Mexico_City' = ANY (setconfig)
          FROM pg_db_role_setting
          WHERE setrole = 0
            AND setdatabase = (SELECT oid FROM pg_database WHERE datname = current_database())$$);

    PERFORM pg_temp.verifica('RD-15', 'esta sesión, abierta después del paso 2, usa America/Mexico_City',
        $$SELECT current_setting('TimeZone') = 'America/Mexico_City'$$);

    PERFORM pg_temp.coincide('4.3 (Privilegios de app_077)', 'app_077 tiene exactamente los privilegios de 4.3, ni uno más',
        $$VALUES
          ('usuario.SELECT'), ('version_aviso.SELECT'), ('consentimiento.SELECT'),
          ('portafolio.SELECT'), ('intermediario.SELECT'), ('instrumento.SELECT'),
          ('emision_cetes.SELECT'), ('transaccion.SELECT'), ('fuente_datos.SELECT'),
          ('version_licencia.SELECT'), ('carga_datos.SELECT'), ('precio_cierre.SELECT'),
          ('tasa_referencia.SELECT'),
          ('usuario.INSERT(correo)'), ('usuario.INSERT(contrasena_hash)'), ('usuario.INSERT(estado)'),
          ('usuario.UPDATE(estado)'), ('usuario.UPDATE(contrasena_hash)'),
          ('consentimiento.INSERT(usuario_id)'), ('consentimiento.INSERT(version_aviso_id)'),
          ('consentimiento.INSERT(tipo)'), ('consentimiento.INSERT(medio)'),
          ('portafolio.INSERT(usuario_id)'), ('portafolio.INSERT(nombre)'),
          ('portafolio.INSERT(divisa_base)'), ('portafolio.UPDATE(nombre)'), ('portafolio.DELETE'),
          ('intermediario.INSERT(usuario_id)'), ('intermediario.INSERT(nombre)'),
          ('transaccion.INSERT(usuario_id)'), ('transaccion.INSERT(portafolio_id)'),
          ('transaccion.INSERT(intermediario_id)'), ('transaccion.INSERT(instrumento_id)'),
          ('transaccion.INSERT(tipo)'), ('transaccion.INSERT(fecha_concertacion)'),
          ('transaccion.INSERT(cantidad)'), ('transaccion.INSERT(precio)'),
          ('transaccion.INSERT(importe_comisiones)'),
          ('esquema public.USAGE'), ('base.CONNECT')$$,
        $$SELECT c.relname || '.' || p
          FROM pg_class c,
               unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
                            'REFERENCES', 'TRIGGER', 'MAINTAIN']) p
          WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
            AND has_table_privilege('app_077', c.oid, p)
          UNION ALL
          SELECT c.relname || '.' || p || '(' || a.attname || ')'
          FROM pg_class c
          JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped,
               unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'REFERENCES']) p
          WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
            AND has_column_privilege('app_077', c.oid, a.attnum, p)
            AND NOT has_table_privilege('app_077', c.oid, p)
          UNION ALL
          SELECT c.relname || '.' || p
          FROM pg_class c, unnest(ARRAY['USAGE', 'SELECT', 'UPDATE']) p
          WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'S'
            AND has_sequence_privilege('app_077', c.oid, p)
          UNION ALL
          SELECT 'esquema public.' || p
          FROM unnest(ARRAY['USAGE', 'CREATE']) p
          WHERE has_schema_privilege('app_077', 'public', p)
          UNION ALL
          SELECT 'base.' || p
          FROM unnest(ARRAY['CONNECT', 'CREATE', 'TEMPORARY']) p
          WHERE has_database_privilege('app_077', current_database(), p)$$);

    PERFORM pg_temp.verifica('4.3 (Privilegios de app_077)', 'ningún privilegio por omisión otorga algo a app_077',
        $$SELECT NOT EXISTS (SELECT FROM pg_default_acl d, aclexplode(d.defaclacl) x
                             WHERE x.grantee = 'app_077'::regrole)$$);
END
$prueba$;

-- =============================================================================
-- B. Datos de prueba: cada alta es un caso positivo (la Instalación escribe
--    como dueño; la aplicación, como app_077)
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.acepta('RF-12; 4.3, nota a.8', 'la Instalación carga la versión 1 del aviso',
        $$INSERT INTO version_aviso (texto, vigente_desde)
          VALUES ('Aviso de privacidad de demostración, versión 1.', '2026-10-01 00:00:00-06')$$);
    INSERT INTO pg_temp.ids SELECT 'aviso1', id FROM version_aviso;

    PERFORM pg_temp.acepta('RF-01, crit. 1', 'alta de Ana sin id',
        $$INSERT INTO usuario (correo, contrasena_hash, estado)
          VALUES ('ana@example.com', 'hash-ficticio-1', 'activa')$$, 'app_077');
    PERFORM pg_temp.acepta('RF-01, crit. 1', 'alta de Beto sin id',
        $$INSERT INTO usuario (correo, contrasena_hash, estado)
          VALUES ('beto@example.com', 'hash-ficticio-2', 'activa')$$, 'app_077');
    INSERT INTO pg_temp.ids SELECT 'ana', id FROM usuario WHERE correo = 'ana@example.com';
    INSERT INTO pg_temp.ids SELECT 'beto', id FROM usuario WHERE correo = 'beto@example.com';

    PERFORM pg_temp.acepta('RF-12, crit. 1; RD-11', 'otorgamiento de Ana sin momento, por web',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio)
                 VALUES (%s, %s, 'otorgamiento', 'web')$$, pg_temp.id('ana'), pg_temp.id('aviso1')), 'app_077');
    PERFORM pg_temp.acepta('RF-12, crit. 1; RD-11', 'otorgamiento de Beto sin momento, por web',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio)
                 VALUES (%s, %s, 'otorgamiento', 'web')$$, pg_temp.id('beto'), pg_temp.id('aviso1')), 'app_077');

    PERFORM pg_temp.acepta('RF-03, crit. 1', 'portafolio «Retiro» de Ana en MXN',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, 'Retiro', 'MXN')$$,
               pg_temp.id('ana')), 'app_077');
    PERFORM pg_temp.acepta('RF-03, crit. 2; RD-03', 'otro usuario sí puede usar «Retiro»',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, 'Retiro', 'MXN')$$,
               pg_temp.id('beto')), 'app_077');
    INSERT INTO pg_temp.ids SELECT 'p_ana', id FROM portafolio WHERE usuario_id = pg_temp.id('ana');
    INSERT INTO pg_temp.ids SELECT 'p_beto', id FROM portafolio WHERE usuario_id = pg_temp.id('beto');

    PERFORM pg_temp.acepta('RF-25, crit. 1', 'intermediario «Casa A» de Ana',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, 'Casa A')$$,
               pg_temp.id('ana')), 'app_077');
    PERFORM pg_temp.acepta('RF-25, crit. 2; RD-03', 'otra cuenta sí puede usar «Casa A»',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, 'Casa A')$$,
               pg_temp.id('beto')), 'app_077');
    INSERT INTO pg_temp.ids SELECT 'i_ana', id FROM intermediario WHERE usuario_id = pg_temp.id('ana');
    INSERT INTO pg_temp.ids SELECT 'i_beto', id FROM intermediario WHERE usuario_id = pg_temp.id('beto');

    PERFORM pg_temp.acepta('RF-31; RF-07, crit. 3; 4.3, nota a.7', 'fuente de la semilla sintética, de demostración, sin dirección',
        $$INSERT INTO fuente_datos (nombre, direccion, de_demostracion)
          VALUES ('Semilla sintética del Proyecto 077', NULL, true)$$);
    PERFORM pg_temp.acepta('RF-31, crit. 2', 'fuente Banco de México con su dirección',
        $$INSERT INTO fuente_datos (nombre, direccion, de_demostracion)
          VALUES ('Banco de México', 'https://www.banxico.org.mx', false)$$);
    INSERT INTO pg_temp.ids SELECT 'f_semilla', id FROM fuente_datos WHERE nombre = 'Semilla sintética del Proyecto 077';
    INSERT INTO pg_temp.ids SELECT 'f_banxico', id FROM fuente_datos WHERE nombre = 'Banco de México';

    PERFORM pg_temp.acepta('RF-31, crit. 1; 4.3, nota a.7', 'versión 1 de la licencia de la semilla, sin supresión ni atribución (nulos)',
        format($$INSERT INTO version_licencia (fuente_id, version, usos_permitidos, obligacion_suprimir, atribucion)
                 VALUES (%s, '1', 'Solo para demostración y pruebas', NULL, NULL)$$, pg_temp.id('f_semilla')));
    PERFORM pg_temp.acepta('RF-31, crit. 1 y 2', 'versión 1 de los términos del Banco de México, con atribución',
        format($$INSERT INTO version_licencia (fuente_id, version, usos_permitidos, obligacion_suprimir, atribucion)
                 VALUES (%s, '1', 'Uso con atribución', NULL, 'Fuente: Banco de México, https://www.banxico.org.mx')$$,
               pg_temp.id('f_banxico')));
    INSERT INTO pg_temp.ids SELECT 'l_semilla', id FROM version_licencia WHERE fuente_id = pg_temp.id('f_semilla');
    INSERT INTO pg_temp.ids SELECT 'l_banxico', id FROM version_licencia WHERE fuente_id = pg_temp.id('f_banxico');

    PERFORM pg_temp.acepta('RD-17; RF-07, crit. 1; RF-31, crit. 1', 'carga de precios de la semilla, sin incorporada_en ni valores_sustituidos',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', '2026-10-01 09:00:00-06', '2026-01-02', '2026-10-09', 'exitosa', 3, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')));
    PERFORM pg_temp.acepta('RD-17; RF-30, crit. 2', 'carga de tasas del SIE con observaciones omitidas',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', '2026-10-01 09:00:00-06', '2025-12-01', '2026-10-09', 'exitosa', 2, 1)$$,
               pg_temp.id('f_banxico'), pg_temp.id('l_banxico')));
    INSERT INTO pg_temp.ids SELECT 'c_precios', id FROM carga_datos WHERE fuente_id = pg_temp.id('f_semilla');
    INSERT INTO pg_temp.ids SELECT 'c_tasas', id FROM carga_datos WHERE fuente_id = pg_temp.id('f_banxico');

    PERFORM pg_temp.acepta('RF-04, crit. 1 y 3', 'acción, ETF y FIBRA de demostración con clave ficticia',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion) VALUES
            ('DEMOACC1', 'Acción de demostración 1', 'MXN', 'accion', true),
            ('DEMOETF1', 'ETF de demostración 1', 'MXN', 'etf', true),
            ('DEMOFIB1', 'FIBRA de demostración 1', 'MXN', 'fibra', true)$$);
    PERFORM pg_temp.acepta('RF-04, crit. 2; RD-04', 'CETES BI261112, sin marca de demostración',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('BI261112', 'CETES con vencimiento el 12/11/2026', 'MXN', 'cetes', false)$$);
    INSERT INTO pg_temp.ids SELECT 'demoacc', id FROM instrumento WHERE clave = 'DEMOACC1';
    INSERT INTO pg_temp.ids SELECT 'demoetf', id FROM instrumento WHERE clave = 'DEMOETF1';
    INSERT INTO pg_temp.ids SELECT 'demofib', id FROM instrumento WHERE clave = 'DEMOFIB1';
    INSERT INTO pg_temp.ids SELECT 'bi261112', id FROM instrumento WHERE clave = 'BI261112';

    PERFORM pg_temp.acepta('RF-04, crit. 2; RD-04; 3.4.2', 'emisión de BI261112: vencimiento 12/11/2026 y valor nominal 10.00',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261112', 'cetes', '2026-11-12', 10.00)$$, pg_temp.id('bi261112')));

    PERFORM pg_temp.acepta('RF-07, crit. 1; RD-17', 'precios de cierre de la semilla, ligados a su carga y su fuente',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id) VALUES
                   (%1$s, '2026-10-01', 50.0000000, %3$s, %4$s),
                   (%2$s, '2026-10-01', 12.3456789, %3$s, %4$s)$$,
               pg_temp.id('demoacc'), pg_temp.id('demofib'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')));

    PERFORM pg_temp.acepta('RF-30, crit. 1; RD-18', 'tasa a 28 días con plazo nominal y efectivo',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (28, '2026-10-01', 7.12345, 'por ciento anual', 28, %s)$$, pg_temp.id('c_tasas')));

    PERFORM pg_temp.acepta('RF-05, crit. 1', 'compra de 100 títulos a 50.00 con importe de 14.50',
        pg_temp.tx('compra', '100', '50.00', '14.50'), 'app_077');
    PERFORM pg_temp.acepta('RF-05, crit. 1', 'venta de 100 títulos a 55.00 con importe de 15.95',
        pg_temp.tx('venta', '100', '55.00', '15.95', $$DATE '2026-10-06'$$), 'app_077');
    PERFORM pg_temp.acepta('RF-05', 'compra de un ETF (para probar su eliminación)',
        pg_temp.tx('compra', '10', '20.00', '0', p_instrumento => 'demoetf'), 'app_077');
    PERFORM pg_temp.acepta('RF-05, crit. 1; RD-02', 'compra de Beto en su portafolio y con su intermediario (para probar RD-23)',
        pg_temp.tx('compra', '5', '20.00', '1.00', p_usuario => 'beto', p_portafolio => 'p_beto',
                   p_intermediario => 'i_beto'), 'app_077');
END
$prueba$;

-- =============================================================================
-- C. usuario
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.rechaza('RD-03; RF-01, crit. 2', 'correo repetido con mayúscula y espacio final',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('Ana@example.com ', 'h', 'activa')$$,
        '23505', 'usuario_correo_uq', 'app_077');
    PERFORM pg_temp.rechaza('RD-03', 'correo repetido en mayúsculas con espacio inicial',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES (' ANA@EXAMPLE.COM', 'h', 'activa')$$,
        '23505', 'usuario_correo_uq', 'app_077');
    PERFORM pg_temp.verifica('RD-03; 4.3, nota c', 'ON CONFLICT ((lower(btrim(correo)))) infiere el índice y no inserta',
        $$WITH alta AS (
              INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('ANA@example.com', 'h', 'activa')
              ON CONFLICT ((lower(btrim(correo)))) DO NOTHING
              RETURNING id)
          SELECT count(*) = 0 FROM alta$$, 'app_077');
    PERFORM pg_temp.acepta('RD-14', 'correo nuevo con mayúsculas y espacios',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES (' Carla@Example.com ', 'h', 'activa')$$,
        'app_077');
    PERFORM pg_temp.acepta('RF-01, crit. 1; RD-14', 'correo con letras acentuadas',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('josé@example.com', 'h', 'activa')$$,
        'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-01, crit. 2', 'correo repetido con mayúsculas acentuadas',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('JOSÉ@EXAMPLE.COM', 'h', 'activa')$$,
        '23505', 'usuario_correo_uq', 'app_077');
    PERFORM pg_temp.verifica('RD-14', 'el correo se recupera tal como se capturó',
        $$SELECT EXISTS (SELECT FROM usuario WHERE correo = ' Carla@Example.com ')$$, 'app_077');
    PERFORM pg_temp.rechaza('3.4.1; RD-23', 'estado fuera de la lista (suspendida)',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('dora@example.com', 'h', 'suspendida')$$,
        '23514', 'usuario_estado_ck', 'app_077');
    PERFORM pg_temp.rechaza('4.4 (nulos)', 'correo nulo',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES (NULL, 'h', 'activa')$$,
        '23502', 'correo', 'app_077');
    PERFORM pg_temp.rechaza('4.4 (nulos); RNF-04', 'contraseña nula',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('dora@example.com', NULL, 'activa')$$,
        '23502', 'contrasena_hash', 'app_077');
    PERFORM pg_temp.rechaza('4.4 (nulos)', 'estado nulo',
        $$INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('dora@example.com', 'h', NULL)$$,
        '23502', 'estado', 'app_077');
    PERFORM pg_temp.rechaza('4.4 (llaves)', 'id explícito: la identidad es GENERATED ALWAYS',
        $$INSERT INTO usuario (id, correo, contrasena_hash, estado) VALUES (999, 'dora@example.com', 'h', 'activa')$$,
        '428C9', NULL, 'app_077');
    PERFORM pg_temp.rechaza('4.3 (Privilegios de app_077)', 'id con OVERRIDING SYSTEM VALUE: INSERT sin id',
        $$INSERT INTO usuario (id, correo, contrasena_hash, estado) OVERRIDING SYSTEM VALUE
          VALUES (999, 'dora@example.com', 'h', 'activa')$$,
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('4.4 (llaves)', 'id explícito tampoco lo acepta el dueño sin OVERRIDING',
        $$INSERT INTO usuario (id, correo, contrasena_hash, estado) VALUES (999, 'dora@example.com', 'h', 'activa')$$,
        '428C9');
    PERFORM pg_temp.acepta('RNF-04; P-06', 'la aplicación actualiza la contraseña (rehash)',
        format($$UPDATE usuario SET contrasena_hash = 'hash-ficticio-1b' WHERE id = %s$$, pg_temp.id('ana')),
        'app_077');
    PERFORM pg_temp.rechaza('4.3 (Privilegios de app_077); RD-14', 'la aplicación no modifica el correo',
        format($$UPDATE usuario SET correo = 'ana2@example.com' WHERE id = %s$$, pg_temp.id('ana')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-23; 4.3 (Relaciones)', 'la aplicación no suprime cuentas (lo hace el administrador)',
        format($$DELETE FROM usuario WHERE id = %s$$, pg_temp.id('ana')),
        '42501', NULL, 'app_077');
END
$prueba$;

-- =============================================================================
-- D. version_aviso y consentimiento
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.rechaza('RF-12, crit. 1', 'dos versiones del aviso con el mismo inicio de vigencia',
        $$INSERT INTO version_aviso (texto, vigente_desde) VALUES ('Otra', '2026-10-01 00:00:00-06')$$,
        '23505', 'version_aviso_vigente_desde_uq');
    PERFORM pg_temp.rechaza('RF-12, crit. 1; 4.4 (nulos)', 'versión del aviso sin texto',
        $$INSERT INTO version_aviso (texto, vigente_desde) VALUES (NULL, '2026-12-01 00:00:00-06')$$,
        '23502', 'texto');
    PERFORM pg_temp.acepta('RF-12', 'la Instalación agrega la versión 2 con otra vigencia',
        $$INSERT INTO version_aviso (texto, vigente_desde)
          VALUES ('Aviso de privacidad de demostración, versión 2.', '2026-12-01 00:00:00-06')$$);
    PERFORM pg_temp.rechaza('4.3, nota a.8; 4.3 (Privilegios de app_077)', 'la aplicación no agrega versiones del aviso',
        $$INSERT INTO version_aviso (texto, vigente_desde) VALUES ('X', '2027-01-01 00:00:00-06')$$,
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RF-12; 4.3 (Privilegios de app_077)', 'la aplicación no modifica el aviso',
        $$UPDATE version_aviso SET texto = 'X'$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RF-12; 4.3 (Privilegios de app_077)', 'la aplicación no elimina el aviso',
        $$DELETE FROM version_aviso$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RF-12, crit. 1; RD-02', 'no se elimina una versión citada por un consentimiento',
        format($$DELETE FROM version_aviso WHERE id = %s$$, pg_temp.id('aviso1')),
        '23503', 'consentimiento_version_aviso_fk');

    PERFORM pg_temp.verifica('RD-15; RF-12, crit. 1', 'la base fijó el momento de cada otorgamiento',
        $$SELECT count(*) = 2 AND bool_and(momento = now()) FROM consentimiento$$, 'app_077');
    PERFORM pg_temp.rechaza('3.4.1; RD-11', 'tipo fuera de la lista (aceptacion)',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio) VALUES (%s, %s, 'aceptacion', 'web')$$,
               pg_temp.id('ana'), pg_temp.id('aviso1')),
        '23514', 'consentimiento_tipo_ck', 'app_077');
    PERFORM pg_temp.rechaza('3.4.1; 4.3, nota a.5', 'medio fuera de la lista (telefono)',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio) VALUES (%s, %s, 'otorgamiento', 'telefono')$$,
               pg_temp.id('ana'), pg_temp.id('aviso1')),
        '23514', 'consentimiento_medio_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-15; 4.3 (Privilegios de app_077)', 'la aplicación no fija el momento',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio, momento)
                 VALUES (%s, %s, 'otorgamiento', 'web', '2026-01-01 00:00:00-06')$$,
               pg_temp.id('ana'), pg_temp.id('aviso1')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-01', 'consentimiento de un usuario inexistente',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio) VALUES (%s, %s, 'otorgamiento', 'web')$$,
               pg_temp.id('inexistente'), pg_temp.id('aviso1')),
        '23503', 'consentimiento_usuario_fk', 'app_077');
    PERFORM pg_temp.rechaza('RF-12, crit. 1', 'consentimiento con una versión del aviso inexistente',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio) VALUES (%s, %s, 'otorgamiento', 'web')$$,
               pg_temp.id('ana'), pg_temp.id('inexistente')),
        '23503', 'consentimiento_version_aviso_fk', 'app_077');
    PERFORM pg_temp.rechaza('RD-11', 'la aplicación no modifica consentimientos',
        $$UPDATE consentimiento SET medio = 'web'$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-11', 'la aplicación no elimina consentimientos',
        $$DELETE FROM consentimiento$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.acepta('RF-12, crit. 3; RD-11', 'Beto revoca su consentimiento',
        format($$INSERT INTO consentimiento (usuario_id, version_aviso_id, tipo, medio) VALUES (%s, %s, 'revocacion', 'web')$$,
               pg_temp.id('beto'), pg_temp.id('aviso1')),
        'app_077');
    PERFORM pg_temp.acepta('RD-23; RF-12, crit. 3', 'la cuenta de Beto pasa a bloqueada',
        format($$UPDATE usuario SET estado = 'bloqueada' WHERE id = %s$$, pg_temp.id('beto')),
        'app_077');
END
$prueba$;

-- =============================================================================
-- E. portafolio
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.rechaza('RD-03; RF-03, crit. 2', 'nombre « retiro » repetido en la cuenta',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, ' retiro ', 'MXN')$$, pg_temp.id('ana')),
        '23505', 'portafolio_nombre_uq', 'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-03, crit. 2', 'nombre vacío',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, '', 'MXN')$$, pg_temp.id('ana')),
        '23514', 'portafolio_nombre_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-03, crit. 2', 'nombre de solo espacios',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, '   ', 'MXN')$$, pg_temp.id('ana')),
        '23514', 'portafolio_nombre_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-08; RF-03, crit. 1', 'divisa base distinta de MXN',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, 'Dólares', 'USD')$$, pg_temp.id('ana')),
        '23514', 'portafolio_divisa_base_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-01', 'portafolio de un usuario inexistente',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, 'Retiro', 'MXN')$$, pg_temp.id('inexistente')),
        '23503', 'portafolio_usuario_fk', 'app_077');
    PERFORM pg_temp.rechaza('4.4 (nulos); RD-08', 'divisa base nula',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, 'Otro', NULL)$$, pg_temp.id('ana')),
        '23502', 'divisa_base', 'app_077');
    PERFORM pg_temp.acepta('RF-03, crit. 1; RD-14', 'segundo portafolio « Educación », con espacios',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, ' Educación ', 'MXN')$$, pg_temp.id('ana')),
        'app_077');
    INSERT INTO pg_temp.ids SELECT 'p_ana2', id FROM portafolio WHERE nombre = ' Educación ';
    PERFORM pg_temp.rechaza('RD-03; RF-03, crit. 2', '«EDUCACIÓN» repetido en la cuenta (mayúsculas acentuadas)',
        format($$INSERT INTO portafolio (usuario_id, nombre, divisa_base) VALUES (%s, 'EDUCACIÓN', 'MXN')$$, pg_temp.id('ana')),
        '23505', 'portafolio_nombre_uq', 'app_077');
    PERFORM pg_temp.verifica('RD-14', 'el nombre se recupera tal como se capturó',
        format($$SELECT nombre = ' Educación ' FROM portafolio WHERE id = %s$$, pg_temp.id('p_ana2')), 'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-03, crit. 2', 'renombrar a «RETIRO», ya usado en la cuenta',
        format($$UPDATE portafolio SET nombre = 'RETIRO' WHERE id = %s$$, pg_temp.id('p_ana2')),
        '23505', 'portafolio_nombre_uq', 'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-03, crit. 2', 'renombrar a un nombre vacío',
        format($$UPDATE portafolio SET nombre = '  ' WHERE id = %s$$, pg_temp.id('p_ana2')),
        '23514', 'portafolio_nombre_ck', 'app_077');
    PERFORM pg_temp.acepta('RF-03, crit. 1', 'renombrar a «Universidad» (solo cambia el nombre)',
        format($$UPDATE portafolio SET nombre = 'Universidad' WHERE id = %s$$, pg_temp.id('p_ana2')),
        'app_077');
    PERFORM pg_temp.rechaza('RD-08; RF-03, crit. 1', 'la aplicación no cambia la divisa base',
        format($$UPDATE portafolio SET divisa_base = 'MXN' WHERE id = %s$$, pg_temp.id('p_ana2')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-01; RF-02', 'la aplicación no cambia el dueño de un portafolio',
        format($$UPDATE portafolio SET usuario_id = %s WHERE id = %s$$, pg_temp.id('beto'), pg_temp.id('p_ana2')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.acepta('RF-28; 4.3 (Aplicación)', 'SELECT … FOR UPDATE del portafolio antes de registrar',
        format($$SELECT id FROM portafolio WHERE id = %s FOR UPDATE$$, pg_temp.id('p_ana')),
        'app_077');
END
$prueba$;

-- =============================================================================
-- F. intermediario
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.rechaza('RD-03; RF-25, crit. 2', '«casa a» repetido en la cuenta',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, 'casa a')$$, pg_temp.id('ana')),
        '23505', 'intermediario_nombre_uq', 'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-25, crit. 2', '« Casa A » repetido en la cuenta',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, ' Casa A ')$$, pg_temp.id('ana')),
        '23505', 'intermediario_nombre_uq', 'app_077');
    PERFORM pg_temp.acepta('RF-25, crit. 1; RD-14', 'intermediario «Casa Ñandú» de Ana, con letras acentuadas',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, 'Casa Ñandú')$$, pg_temp.id('ana')),
        'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-25, crit. 2', '«CASA ÑANDÚ» repetido en la cuenta (mayúsculas acentuadas)',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, 'CASA ÑANDÚ')$$, pg_temp.id('ana')),
        '23505', 'intermediario_nombre_uq', 'app_077');
    PERFORM pg_temp.rechaza('RD-03; RF-25, crit. 2', 'nombre vacío',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, '')$$, pg_temp.id('ana')),
        '23514', 'intermediario_nombre_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-01', 'intermediario de un usuario inexistente',
        format($$INSERT INTO intermediario (usuario_id, nombre) VALUES (%s, 'Casa Z')$$, pg_temp.id('inexistente')),
        '23503', 'intermediario_usuario_fk', 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RF-25, crit. 3', 'la aplicación no modifica intermediarios',
        format($$UPDATE intermediario SET nombre = 'Casa B' WHERE id = %s$$, pg_temp.id('i_ana')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RF-25, crit. 3', 'la aplicación no elimina intermediarios',
        format($$DELETE FROM intermediario WHERE id = %s$$, pg_temp.id('i_ana')),
        '42501', NULL, 'app_077');
END
$prueba$;

-- =============================================================================
-- G. instrumento y emision_cetes (catálogo)
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.rechaza('RD-04; RF-04, crit. 1', 'clave repetida en el catálogo',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('DEMOACC1', 'Otra', 'MXN', 'accion', true)$$,
        '23505', 'instrumento_clave_uq');
    PERFORM pg_temp.rechaza('3.4.1; RF-04, crit. 1', 'clase de activo fuera de la lista (bono)',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('DEMOBON1', 'Bono', 'MXN', 'bono', true)$$,
        '23514', 'instrumento_clase_activo_ck');
    PERFORM pg_temp.rechaza('RD-04; RF-04, crit. 2', 'CETES con clave de cinco dígitos (BI26111)',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('BI26111', 'CETES', 'MXN', 'cetes', false)$$,
        '23514', 'instrumento_clave_ck');
    PERFORM pg_temp.rechaza('RD-04; RF-04, crit. 2', 'CETES con clave ficticia (DEMO0001)',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('DEMO0001', 'CETES', 'MXN', 'cetes', false)$$,
        '23514', 'instrumento_clave_ck');
    PERFORM pg_temp.rechaza('RD-08', 'instrumento en USD',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('DEMOUSD1', 'Acción en dólares', 'USD', 'accion', true)$$,
        '23514', 'instrumento_divisa_ck');
    PERFORM pg_temp.rechaza('RF-04, crit. 3; P-21', 'acción sin marca de demostración',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('DEMOACC9', 'Acción', 'MXN', 'accion', false)$$,
        '23514', 'instrumento_de_demostracion_ck');
    PERFORM pg_temp.rechaza('RF-04, crit. 3', 'CETES con marca de demostración',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('BI261126', 'CETES', 'MXN', 'cetes', true)$$,
        '23514', 'instrumento_de_demostracion_ck');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no agrega instrumentos',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('DEMOACC9', 'Acción', 'MXN', 'accion', true)$$,
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RF-04, crit. 3', 'la aplicación no modifica el catálogo',
        $$UPDATE instrumento SET nombre = 'X'$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no elimina instrumentos',
        $$DELETE FROM instrumento$$, '42501', NULL, 'app_077');

    PERFORM pg_temp.acepta('RD-04; 4.4, nota a.6', 'el formato BI solo se exige a los CETES: acción con clave BI261126',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('BI261126', 'Acción con clave de forma de emisión', 'MXN', 'accion', true)$$);
    PERFORM pg_temp.acepta('RF-04, crit. 2', 'CETES BI261119',
        $$INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
          VALUES ('BI261119', 'CETES con vencimiento el 19/11/2026', 'MXN', 'cetes', false)$$);
    INSERT INTO pg_temp.ids SELECT 'acc_bi', id FROM instrumento WHERE clave = 'BI261126';
    INSERT INTO pg_temp.ids SELECT 'bi261119', id FROM instrumento WHERE clave = 'BI261119';

    PERFORM pg_temp.rechaza('RD-04; 3.4.2', 'emisión con clase de activo distinta de cetes',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261126', 'accion', '2026-11-26', 10.00)$$, pg_temp.id('acc_bi')),
        '23514', 'emision_cetes_clase_activo_ck');
    PERFORM pg_temp.rechaza('RD-04; 3.4.2', 'solo un CETES tiene emisión: la acción BI261126 no',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261126', 'cetes', '2026-11-26', 10.00)$$, pg_temp.id('acc_bi')),
        '23503', 'emision_cetes_instrumento_fk');
    PERFORM pg_temp.rechaza('RD-04', 'la clave de la emisión debe ser la de su instrumento',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261126', 'cetes', '2026-11-26', 10.00)$$, pg_temp.id('bi261119')),
        '23503', 'emision_cetes_instrumento_fk');
    PERFORM pg_temp.rechaza('RD-04; RF-04, crit. 2', 'la clave debe corresponder al vencimiento (BI261119 con 20/11/2026)',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261119', 'cetes', '2026-11-20', 10.00)$$, pg_temp.id('bi261119')),
        '23514', 'emision_cetes_clave_ck');
    PERFORM pg_temp.rechaza('RD-06; RF-04, crit. 2', 'valor nominal distinto de 10.00 (10.50)',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261119', 'cetes', '2026-11-19', 10.50)$$, pg_temp.id('bi261119')),
        '23514', 'emision_cetes_valor_nominal_ck');
    PERFORM pg_temp.rechaza('RD-06', 'valor nominal 0',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261119', 'cetes', '2026-11-19', 0)$$, pg_temp.id('bi261119')),
        '23514', 'emision_cetes_valor_nominal_ck');
    PERFORM pg_temp.acepta('RD-13; RF-04, crit. 2', 'emisión de BI261119 con valor nominal 10 (igual a 10.00)',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261119', 'cetes', '2026-11-19', 10)$$, pg_temp.id('bi261119')));
    PERFORM pg_temp.rechaza('3.4.2 (identificadora)', 'una segunda emisión del mismo instrumento',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261112', 'cetes', '2026-11-12', 10.00)$$, pg_temp.id('bi261112')),
        '23505', 'emision_cetes_pk');
    PERFORM pg_temp.rechaza('RD-04 (restricción aislada)', 'una emisión por vencimiento, sin emision_cetes_clave_ck',
        format($$ALTER TABLE emision_cetes DROP CONSTRAINT emision_cetes_clave_ck;
                 INSERT INTO instrumento (clave, nombre, divisa, clase_activo, de_demostracion)
                 VALUES ('BI261113', 'CETES', 'MXN', 'cetes', false);
                 INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 SELECT id, clave, clase_activo, '2026-11-12', 10.00 FROM instrumento WHERE clave = 'BI261113'$$),
        '23505', 'emision_cetes_vencimiento_uq');
    PERFORM pg_temp.rechaza('RD-13 (restricción aislada)', 'valor nominal con 3 decimales, sin emision_cetes_valor_nominal_ck',
        format($$ALTER TABLE emision_cetes DROP CONSTRAINT emision_cetes_valor_nominal_ck;
                 UPDATE emision_cetes SET valor_nominal = 10.001 WHERE instrumento_id = %s$$, pg_temp.id('bi261112')),
        '23514', 'emision_cetes_valor_nominal_escala_ck');
    PERFORM pg_temp.rechaza('RD-04; 4.3 (Redundancia controlada)', 'la clave de un CETES con emisión no diverge de ella',
        format($$UPDATE instrumento SET clave = 'BI261113' WHERE id = %s$$, pg_temp.id('bi261112')),
        '23503', 'emision_cetes_instrumento_fk');
    PERFORM pg_temp.rechaza('3.4.2; RD-02', 'no se elimina un instrumento con emisión',
        format($$DELETE FROM instrumento WHERE id = %s$$, pg_temp.id('bi261119')),
        '23503', 'emision_cetes_instrumento_fk');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no agrega emisiones',
        format($$INSERT INTO emision_cetes (instrumento_id, clave, clase_activo, vencimiento, valor_nominal)
                 VALUES (%s, 'BI261126', 'cetes', '2026-11-26', 10.00)$$, pg_temp.id('acc_bi')),
        '42501', NULL, 'app_077');
END
$prueba$;

-- =============================================================================
-- H. transaccion
-- =============================================================================
DO $prueba$
DECLARE
    hoy_cdmx    constant text := $$(now() AT TIME ZONE 'America/Mexico_City')::date$$;
    manana_cdmx constant text := $$(now() AT TIME ZONE 'America/Mexico_City')::date + 1$$;
BEGIN
    PERFORM pg_temp.rechaza('RD-02; RF-02, crit. 2', 'portafolio de Ana con el intermediario de Beto',
        pg_temp.tx('compra', '1', '10.00', '0', p_intermediario => 'i_beto'),
        '23503', 'transaccion_intermediario_fk', 'app_077');
    PERFORM pg_temp.rechaza('RD-01; RD-02', 'transacción de Beto en el portafolio de Ana',
        pg_temp.tx('compra', '1', '10.00', '0', p_usuario => 'beto', p_intermediario => 'i_beto'),
        '23503', 'transaccion_portafolio_fk', 'app_077');
    PERFORM pg_temp.rechaza('3.4.2', 'instrumento inexistente',
        pg_temp.tx('compra', '1', '10.00', '0', p_instrumento => 'inexistente'),
        '23503', 'transaccion_instrumento_fk', 'app_077');
    PERFORM pg_temp.rechaza('3.4.1; RF-05', 'tipo fuera de la lista (dividendo)',
        pg_temp.tx('dividendo', '1', '10.00', '0'), '23514', 'transaccion_tipo_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-06; RF-05, crit. 2', 'cantidad 0',
        pg_temp.tx('compra', '0', '10.00', '0'), '23514', 'transaccion_cantidad_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-06; RF-05, crit. 2', 'cantidad negativa',
        pg_temp.tx('compra', '-5', '10.00', '0'), '23514', 'transaccion_cantidad_ck', 'app_077');
    -- Un numeric 1.5 (un Decimal de psycopg o un literal sin comillas) se asigna
    -- a integer redondeado a 2, sin error: con integer (4.4), el rechazo de
    -- títulos no enteros sin redondear (RF-05; RD-14) es de la API.
    PERFORM pg_temp.rechaza('4.4 (cantidad integer); RD-13', 'el texto «1.5» no es un integer válido',
        pg_temp.tx('compra', $$'1.5'$$, '10.00', '0'), '22P02', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-06; RF-05, crit. 2', 'precio 0',
        pg_temp.tx('compra', '1', '0', '0'), '23514', 'transaccion_precio_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-06; RF-05, crit. 2', 'precio negativo',
        pg_temp.tx('compra', '1', '-1.00', '0'), '23514', 'transaccion_precio_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-13; RD-14; RF-05, crit. 2', 'precio con 8 decimales, sin redondear',
        pg_temp.tx('compra', '1', '50.12345678', '0'), '23514', 'transaccion_precio_escala_ck', 'app_077');
    PERFORM pg_temp.acepta('RD-13', 'precio con 7 decimales',
        pg_temp.tx('compra', '1', '50.1234567', '0'), 'app_077');
    PERFORM pg_temp.acepta('RD-13; 4.3, nota a.2', 'precio 50.12345670: 8 escritos, 7 significativos',
        pg_temp.tx('compra', '2', '50.12345670', '0'), 'app_077');
    PERFORM pg_temp.verifica('RD-14', 'ese precio se recupera sin alteración (50.12345670)',
        $$SELECT EXISTS (SELECT FROM transaccion WHERE cantidad = 2 AND precio::text = '50.12345670')$$, 'app_077');
    PERFORM pg_temp.rechaza('RD-12', 'precio NaN (no es un decimal)',
        pg_temp.tx('compra', '1', $$'NaN'$$, '0'), '23514', 'transaccion_precio_escala_ck', 'app_077');
    PERFORM pg_temp.rechaza('RD-12', 'precio Infinity (no es un decimal)',
        pg_temp.tx('compra', '1', $$'Infinity'$$, '0'), '23514', 'transaccion_precio_escala_ck', 'app_077');
    PERFORM pg_temp.rechaza('4.3 (tope 10^11)', 'precio de 10^11',
        pg_temp.tx('compra', '1', '100000000000', '0'), '23514', 'transaccion_precio_tamano_ck', 'app_077');
    PERFORM pg_temp.acepta('4.3 (tope 10^11)', 'precio de 99,999,999,999.9999999',
        pg_temp.tx('compra', '1', '99999999999.9999999', '0'), 'app_077');
    PERFORM pg_temp.rechaza('RF-05, crit. 2', 'importe negativo',
        pg_temp.tx('compra', '1', '10.00', '-0.01'), '23514', 'transaccion_importe_comisiones_ck', 'app_077');
    PERFORM pg_temp.acepta('RF-05, crit. 2; 4.3, nota a.4', 'importe 0',
        pg_temp.tx('compra', '1', '10.00', '0'), 'app_077');
    PERFORM pg_temp.rechaza('RD-13; RF-05, crit. 2', 'importe con 3 decimales',
        pg_temp.tx('compra', '1', '10.00', '14.505'), '23514', 'transaccion_importe_comisiones_escala_ck', 'app_077');
    PERFORM pg_temp.rechaza('4.3 (tope 10^16)', 'importe de 10^16',
        pg_temp.tx('compra', '1', '10.00', '10000000000000000'), '23514', 'transaccion_importe_comisiones_tamano_ck', 'app_077');
    PERFORM pg_temp.acepta('4.3 (tope 10^16)', 'importe de 9,999,999,999,999,999.99',
        pg_temp.tx('compra', '1', '10.00', '9999999999999999.99'), 'app_077');
    PERFORM pg_temp.rechaza('RF-05, crit. 2; 4.3, nota a.4', 'venta con importe igual a títulos × precio',
        pg_temp.tx('venta', '1', '10.00', '10.00'), '23514', 'transaccion_importe_venta_ck', 'app_077');
    PERFORM pg_temp.acepta('RF-05, crit. 2', 'venta con importe menor que títulos × precio',
        pg_temp.tx('venta', '1', '10.00', '9.99'), 'app_077');
    PERFORM pg_temp.acepta('RF-05', 'compra con importe mayor que títulos × precio (el límite es solo de la venta)',
        pg_temp.tx('compra', '1', '10.00', '10.01'), 'app_077');
    PERFORM pg_temp.rechaza('RD-07; RF-05, crit. 3', 'fecha de concertación de mañana en la Ciudad de México',
        pg_temp.tx('compra', '1', '10.00', '0', manana_cdmx), '23514', 'transaccion_fecha_concertacion_ck', 'app_077');
    PERFORM pg_temp.acepta('RD-07', 'fecha de concertación de hoy en la Ciudad de México',
        pg_temp.tx('compra', '3', '10.00', '0', hoy_cdmx), 'app_077');
    PERFORM pg_temp.rechaza('RD-15; RD-07', 'registrada el 15/10 a las 05:30 UTC (14/10 en la CDMX) con fecha del 15/10',
        format($$INSERT INTO transaccion (usuario_id, portafolio_id, intermediario_id, instrumento_id, tipo,
                     fecha_concertacion, cantidad, precio, importe_comisiones, registrada_en)
                 VALUES (%s, %s, %s, %s, 'compra', '2026-10-15', 1, 10.00, 0, '2026-10-15 05:30:00+00')$$,
               pg_temp.id('ana'), pg_temp.id('p_ana'), pg_temp.id('i_ana'), pg_temp.id('demoacc')),
        '23514', 'transaccion_fecha_concertacion_ck');
    PERFORM pg_temp.acepta('RD-15; RD-07', 'registrada el 15/10 a las 05:30 UTC con fecha del 14/10',
        format($$INSERT INTO transaccion (usuario_id, portafolio_id, intermediario_id, instrumento_id, tipo,
                     fecha_concertacion, cantidad, precio, importe_comisiones, registrada_en)
                 VALUES (%s, %s, %s, %s, 'compra', '2026-10-14', 1, 10.00, 0, '2026-10-15 05:30:00+00')$$,
               pg_temp.id('ana'), pg_temp.id('p_ana'), pg_temp.id('i_ana'), pg_temp.id('demoacc')));
    PERFORM pg_temp.rechaza('RD-14; RF-05, crit. 2', 'fecha inválida 31/11/2026',
        pg_temp.tx('compra', '1', '10.00', '0', $$'2026-11-31'$$), '22008', NULL, 'app_077');
    PERFORM pg_temp.rechaza('4.4 (nulos)', 'precio nulo',
        pg_temp.tx('compra', '1', 'NULL', '0'), '23502', 'precio', 'app_077');
    PERFORM pg_temp.verifica('RD-15; RD-07', 'la base fijó registrada_en en cada transacción de la aplicación',
        $$SELECT bool_and(registrada_en = now()) FROM transaccion WHERE fecha_concertacion <> '2026-10-14'$$, 'app_077');
    PERFORM pg_temp.verifica('RF-05, crit. 1; RD-14', 'la compra y la venta se consultan sin alteración',
        $$SELECT count(*) = 2 FROM transaccion
          WHERE (tipo, cantidad, precio::text, importe_comisiones::text) IN
                (('compra', 100, '50.00', '14.50'), ('venta', 100, '55.00', '15.95'))$$, 'app_077');
    PERFORM pg_temp.rechaza('RD-07; RD-15; 4.3 (Privilegios de app_077)', 'la aplicación no fija registrada_en',
        format($$INSERT INTO transaccion (usuario_id, portafolio_id, intermediario_id, instrumento_id, tipo,
                     fecha_concertacion, cantidad, precio, importe_comisiones, registrada_en)
                 VALUES (%s, %s, %s, %s, 'compra', '2026-10-05', 1, 10.00, 0, '2027-01-01 00:00:00-06')$$,
               pg_temp.id('ana'), pg_temp.id('p_ana'), pg_temp.id('i_ana'), pg_temp.id('demoacc')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('4.4 (llaves)', 'id explícito en una transacción',
        format($$INSERT INTO transaccion (id, usuario_id, portafolio_id, intermediario_id, instrumento_id, tipo,
                     fecha_concertacion, cantidad, precio, importe_comisiones)
                 VALUES (999, %s, %s, %s, %s, 'compra', '2026-10-05', 1, 10.00, 0)$$,
               pg_temp.id('ana'), pg_temp.id('p_ana'), pg_temp.id('i_ana'), pg_temp.id('demoacc')),
        '428C9', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RF-39 (diferido)', 'la aplicación no modifica transacciones',
        $$UPDATE transaccion SET cantidad = 1$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RD-22', 'la aplicación no elimina transacciones',
        $$DELETE FROM transaccion$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-22', 'la aplicación no vacía la tabla (TRUNCATE)',
        $$TRUNCATE transaccion$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-02; RD-09', 'no se elimina un intermediario con transacciones',
        format($$DELETE FROM intermediario WHERE id = %s$$, pg_temp.id('i_ana')),
        '23503', 'transaccion_intermediario_fk');
    PERFORM pg_temp.rechaza('3.4.2; RD-02', 'no se elimina un instrumento con transacciones',
        format($$DELETE FROM instrumento WHERE id = %s$$, pg_temp.id('demoetf')),
        '23503', 'transaccion_instrumento_fk');
END
$prueba$;

-- =============================================================================
-- I. fuente_datos, version_licencia y carga_datos
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.rechaza('RF-31', 'fuente con nombre repetido',
        $$INSERT INTO fuente_datos (nombre, direccion, de_demostracion) VALUES ('Banco de México', NULL, false)$$,
        '23505', 'fuente_datos_nombre_uq');
    PERFORM pg_temp.rechaza('RF-31', 'versión repetida dentro de su fuente',
        format($$INSERT INTO version_licencia (fuente_id, version, usos_permitidos) VALUES (%s, '1', 'X')$$,
               pg_temp.id('f_banxico')),
        '23505', 'version_licencia_version_uq');
    PERFORM pg_temp.rechaza('3.4.1', 'versión de una fuente inexistente',
        format($$INSERT INTO version_licencia (fuente_id, version, usos_permitidos) VALUES (%s, '1', 'X')$$,
               pg_temp.id('inexistente')),
        '23503', 'version_licencia_fuente_fk');
    PERFORM pg_temp.rechaza('RF-31, crit. 1', 'carga con la licencia de otra fuente',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'exitosa', 0, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_banxico')),
        '23503', 'carga_datos_version_licencia_fk');
    PERFORM pg_temp.rechaza('3.4.2', 'carga de una fuente inexistente (fallan sus dos FK)',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'exitosa', 0, 0)$$,
               pg_temp.id('inexistente'), pg_temp.id('l_semilla')),
        '23503');
    PERFORM pg_temp.rechaza('3.4.1; RF-30', 'origen fuera de la lista del MVP (captura)',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'captura', now(), '2026-01-01', '2026-01-31', 'exitosa', 0, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '23514', 'carga_datos_origen_ck');
    PERFORM pg_temp.rechaza('3.4.2 (restricción aislada)', 'carga de una fuente inexistente, sin carga_datos_version_licencia_fk',
        format($$ALTER TABLE carga_datos DROP CONSTRAINT carga_datos_version_licencia_fk;
                 INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'exitosa', 0, 0)$$,
               pg_temp.id('inexistente'), pg_temp.id('l_semilla')),
        '23503', 'carga_datos_fuente_fk');
    PERFORM pg_temp.rechaza('3.4.1; 4.3, nota a.5', 'resultado fuera de la lista (parcial)',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'parcial', 0, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '23514', 'carga_datos_resultado_ck');
    PERFORM pg_temp.acepta('3.4.1; 4.3, nota a.5', 'carga con resultado fallida',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'fallida', 0, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')));
    PERFORM pg_temp.rechaza('3.4.1', 'intervalo con fecha inicial posterior a la final',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-02-01', '2026-01-31', 'exitosa', 0, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '23514', 'carga_datos_intervalo_ck');
    PERFORM pg_temp.rechaza('3.4.1; RNF-09', 'observaciones incorporadas negativas',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'exitosa', -1, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '23514', 'carga_datos_observaciones_incorporadas_ck');
    PERFORM pg_temp.rechaza('RD-18; RD-20', 'observaciones omitidas negativas',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'exitosa', 0, -1)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '23514', 'carga_datos_observaciones_omitidas_ck');
    PERFORM pg_temp.rechaza('P-34; 4.3, nota a.6', 'carga sin fecha de obtención',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', NULL, '2026-01-01', '2026-01-31', 'exitosa', 0, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '23502', 'obtenida_en');
    PERFORM pg_temp.rechaza('RD-21; 4.4', 'valores_sustituidos nulo',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas,
                                          valores_sustituidos)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'exitosa', 0, 0, NULL)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '23502', 'valores_sustituidos');
    PERFORM pg_temp.verifica('RD-21; RD-15; RF-31, crit. 1', 'por omisión, valores_sustituidos = [] e incorporada_en = now()',
        $$SELECT bool_and(valores_sustituidos = '[]'::jsonb AND incorporada_en = now()) FROM carga_datos$$, 'app_077');
    PERFORM pg_temp.rechaza('RF-31, crit. 1; RD-02', 'no se elimina la versión de licencia que ampara una carga',
        format($$DELETE FROM version_licencia WHERE id = %s$$, pg_temp.id('l_banxico')),
        '23503', 'carga_datos_version_licencia_fk');
    PERFORM pg_temp.acepta('3.4.1', 'una fuente con una versión de licencia y sin cargas',
        $$INSERT INTO fuente_datos (nombre, direccion, de_demostracion) VALUES ('Fuente sin cargas', NULL, true);
          INSERT INTO version_licencia (fuente_id, version, usos_permitidos)
          SELECT id, '1', 'Solo pruebas' FROM fuente_datos WHERE nombre = 'Fuente sin cargas'$$);
    PERFORM pg_temp.rechaza('3.4.1; RD-02', 'no se elimina una fuente con versiones de licencia',
        $$DELETE FROM fuente_datos WHERE nombre = 'Fuente sin cargas'$$,
        '23503', 'version_licencia_fuente_fk');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no agrega fuentes',
        $$INSERT INTO fuente_datos (nombre, direccion, de_demostracion) VALUES ('Otra', NULL, true)$$,
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no agrega versiones de licencia',
        format($$INSERT INTO version_licencia (fuente_id, version, usos_permitidos) VALUES (%s, '2', 'X')$$,
               pg_temp.id('f_banxico')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; 3.4.8', 'la aplicación no registra cargas',
        format($$INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                          fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
                 VALUES (%s, %s, 'semilla', now(), '2026-01-01', '2026-01-31', 'exitosa', 0, 0)$$,
               pg_temp.id('f_semilla'), pg_temp.id('l_semilla')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RD-24', 'la aplicación no suprime cargas',
        $$DELETE FROM carga_datos$$, '42501', NULL, 'app_077');
END
$prueba$;

-- =============================================================================
-- J. precio_cierre
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.acepta('RD-19', 'una fuente de prueba con su licencia y su carga',
        $$INSERT INTO fuente_datos (nombre, direccion, de_demostracion) VALUES ('Fuente de prueba', NULL, true);
          INSERT INTO version_licencia (fuente_id, version, usos_permitidos)
          SELECT id, '1', 'Solo pruebas' FROM fuente_datos WHERE nombre = 'Fuente de prueba';
          INSERT INTO carga_datos (fuente_id, version_licencia_id, origen, obtenida_en, fecha_inicial,
                                   fecha_final, resultado, observaciones_incorporadas, observaciones_omitidas)
          SELECT f.id, l.id, 'semilla', now(), '2026-10-01', '2026-10-01', 'exitosa', 1, 0
          FROM fuente_datos f JOIN version_licencia l ON l.fuente_id = f.id
          WHERE f.nombre = 'Fuente de prueba'$$);
    INSERT INTO pg_temp.ids SELECT 'f_prueba', id FROM fuente_datos WHERE nombre = 'Fuente de prueba';
    INSERT INTO pg_temp.ids SELECT 'c_prueba', id FROM carga_datos WHERE fuente_id = pg_temp.id('f_prueba');

    PERFORM pg_temp.rechaza('RD-19; RF-07, crit. 1', 'dos precios del mismo instrumento, fecha y fuente',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-01', 51.00, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')),
        '23505', 'precio_cierre_instrumento_fecha_fuente_uq');
    PERFORM pg_temp.acepta('RD-19', 'mismo instrumento y fecha, de otra fuente',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-01', 51.00, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_prueba'), pg_temp.id('f_prueba')));
    PERFORM pg_temp.rechaza('RD-17; RD-19', 'la fuente del precio debe ser la de su carga',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-02', 51.00, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_prueba')),
        '23503', 'precio_cierre_carga_fk');
    PERFORM pg_temp.rechaza('RD-06; RF-07, crit. 2', 'precio de cierre 0',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-02', 0, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')),
        '23514', 'precio_cierre_precio_ck');
    PERFORM pg_temp.rechaza('RD-13; RD-14; RF-07, crit. 2', 'precio de cierre con 8 decimales',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-02', 50.12345678, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')),
        '23514', 'precio_cierre_precio_escala_ck');
    PERFORM pg_temp.acepta('RD-13; 4.3, nota c', 'precio de cierre 50.12345670 (8 escritos, 7 significativos)',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-02', 50.12345670, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')));
    PERFORM pg_temp.verifica('RD-14', 'ese precio de cierre se recupera sin alteración',
        $$SELECT precio::text = '50.12345670' FROM precio_cierre WHERE fecha = '2026-10-02'$$, 'app_077');
    PERFORM pg_temp.rechaza('4.3 (tope 10^11)', 'precio de cierre de 10^11',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-05', 100000000000, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')),
        '23514', 'precio_cierre_precio_tamano_ck');
    PERFORM pg_temp.rechaza('RD-12', 'precio de cierre NaN',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-05', 'NaN', %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')),
        '23514', 'precio_cierre_precio_escala_ck');
    PERFORM pg_temp.rechaza('3.4.1', 'precio de un instrumento inexistente',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-05', 1.00, %s, %s)$$,
               pg_temp.id('inexistente'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')),
        '23503', 'precio_cierre_instrumento_fk');
    PERFORM pg_temp.rechaza('RD-02', 'no se elimina un instrumento con precios',
        format($$DELETE FROM instrumento WHERE id = %s$$, pg_temp.id('demofib')),
        '23503', 'precio_cierre_instrumento_fk');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no agrega precios',
        format($$INSERT INTO precio_cierre (instrumento_id, fecha, precio, carga_id, fuente_id)
                 VALUES (%s, '2026-10-05', 1.00, %s, %s)$$,
               pg_temp.id('demoacc'), pg_temp.id('c_precios'), pg_temp.id('f_semilla')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no modifica precios',
        $$UPDATE precio_cierre SET precio = 1$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no elimina precios',
        $$DELETE FROM precio_cierre$$, '42501', NULL, 'app_077');
END
$prueba$;

-- =============================================================================
-- K. tasa_referencia
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.rechaza('RF-30; P-15', 'plazo nominal fuera de la lista (30 días)',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (30, '2026-10-01', 7.00000, 'por ciento anual', 30, %s)$$, pg_temp.id('c_tasas')),
        '23514', 'tasa_referencia_plazo_nominal_ck');
    PERFORM pg_temp.acepta('RF-30; P-15 (opción A)', 'tasa a 728 días',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (728, '2026-10-01', 7.50000, 'por ciento anual', 728, %s)$$, pg_temp.id('c_tasas')));
    PERFORM pg_temp.rechaza('RD-19; RF-30, crit. 3', 'dos tasas del mismo plazo y fecha de colocación',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (28, '2026-10-01', 7.00000, 'por ciento anual', 28, %s)$$, pg_temp.id('c_tasas')),
        '23505', 'tasa_referencia_plazo_fecha_uq');
    PERFORM pg_temp.rechaza('RD-06; RD-18', 'plazo efectivo 0',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (91, '2026-10-01', 7.00000, 'por ciento anual', 0, %s)$$, pg_temp.id('c_tasas')),
        '23514', 'tasa_referencia_plazo_efectivo_ck');
    PERFORM pg_temp.rechaza('RD-18; RF-30, crit. 2', 'tasa sin plazo efectivo',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (91, '2026-10-01', 7.00000, 'por ciento anual', NULL, %s)$$, pg_temp.id('c_tasas')),
        '23502', 'plazo_efectivo');
    PERFORM pg_temp.rechaza('RD-20; RF-30, crit. 2', 'tasa sin valor (N/E)',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (91, '2026-10-01', NULL, 'por ciento anual', 91, %s)$$, pg_temp.id('c_tasas')),
        '23502', 'valor');
    PERFORM pg_temp.rechaza('RD-13; RD-14', 'tasa con 6 decimales',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (91, '2026-10-01', 7.123456, 'por ciento anual', 91, %s)$$, pg_temp.id('c_tasas')),
        '23514', 'tasa_referencia_valor_escala_ck');
    PERFORM pg_temp.rechaza('RD-12; RD-20', 'tasa NaN (no es un decimal)',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (91, '2026-10-01', 'NaN', 'por ciento anual', 91, %s)$$, pg_temp.id('c_tasas')),
        '23514', 'tasa_referencia_valor_escala_ck');
    PERFORM pg_temp.acepta('RD-13', 'tasa con 5 decimales',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (91, '2026-10-01', 7.12345, 'por ciento anual', 91, %s)$$, pg_temp.id('c_tasas')));
    PERFORM pg_temp.acepta('RD-20', 'tasa con fecha de colocación posterior a su carga',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (182, '2026-10-16', 7.30000, 'por ciento anual', 182, %s)$$, pg_temp.id('c_tasas')));
    PERFORM pg_temp.rechaza('RD-17', 'tasa de una carga inexistente',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (364, '2026-10-01', 7.00000, 'por ciento anual', 364, %s)$$, pg_temp.id('inexistente')),
        '23503', 'tasa_referencia_carga_fk');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no agrega tasas',
        format($$INSERT INTO tasa_referencia (plazo_nominal, fecha_colocacion, valor, unidad, plazo_efectivo, carga_id)
                 VALUES (364, '2026-10-01', 7.00000, 'por ciento anual', 364, %s)$$, pg_temp.id('c_tasas')),
        '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no modifica tasas',
        $$UPDATE tasa_referencia SET valor = 1$$, '42501', NULL, 'app_077');
END
$prueba$;

-- =============================================================================
-- L. Privilegios generales de app_077
-- =============================================================================
DO $prueba$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['usuario', 'version_aviso', 'consentimiento', 'portafolio',
                             'intermediario', 'instrumento', 'emision_cetes', 'transaccion',
                             'fuente_datos', 'version_licencia', 'carga_datos', 'precio_cierre',
                             'tasa_referencia']
    LOOP
        PERFORM pg_temp.acepta('4.3 (Privilegios de app_077)', format('la aplicación lee %s', t),
            format('SELECT * FROM %I', t), 'app_077');
    END LOOP;
    PERFORM pg_temp.rechaza('4.3 (Privilegios de app_077)', 'la aplicación no crea tablas en public',
        $$CREATE TABLE public.intrusa (id integer)$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('4.3 (Privilegios de app_077)', 'la aplicación no crea tablas temporales',
        $$CREATE TEMP TABLE intrusa_temporal (id integer)$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('4.3 (Privilegios de app_077)', 'la aplicación no altera tablas ni quita restricciones',
        $$ALTER TABLE transaccion DROP CONSTRAINT transaccion_precio_ck$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('4.3 (Privilegios de app_077)', 'la aplicación no usa las secuencias de identidad',
        $$SELECT nextval(pg_get_serial_sequence('usuario', 'id'))$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no modifica emisiones',
        $$UPDATE emision_cetes SET valor_nominal = 10$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09', 'la aplicación no elimina emisiones',
        $$DELETE FROM emision_cetes$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RF-31', 'la aplicación no modifica fuentes',
        $$UPDATE fuente_datos SET direccion = NULL$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RD-24', 'la aplicación no elimina fuentes',
        $$DELETE FROM fuente_datos$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RF-31', 'la aplicación no modifica versiones de licencia',
        $$UPDATE version_licencia SET atribucion = NULL$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RD-24', 'la aplicación no elimina versiones de licencia',
        $$DELETE FROM version_licencia$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RD-21', 'la aplicación no modifica cargas',
        $$UPDATE carga_datos SET resultado = 'fallida'$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-09; RD-24', 'la aplicación no elimina tasas',
        $$DELETE FROM tasa_referencia$$, '42501', NULL, 'app_077');
    PERFORM pg_temp.rechaza('RD-23; RD-11', 'la aplicación no vacía cuentas (TRUNCATE … CASCADE)',
        $$TRUNCATE usuario CASCADE$$, '42501', NULL, 'app_077');
END
$prueba$;

-- =============================================================================
-- M. Eliminación y supresión en cascada (al final, porque borran datos)
-- =============================================================================
DO $prueba$
BEGIN
    PERFORM pg_temp.acepta('RD-10; RF-03, crit. 3', 'la aplicación elimina el portafolio «Retiro» de Ana con sus transacciones',
        format($$DELETE FROM portafolio WHERE id = %s$$, pg_temp.id('p_ana')), 'app_077');
    PERFORM pg_temp.verifica('RD-10', 'sin transacciones del portafolio y con los intermediarios de Ana',
        format($$SELECT NOT EXISTS (SELECT FROM transaccion WHERE portafolio_id = %1$s)
                    AND EXISTS (SELECT FROM intermediario WHERE id = %2$s)$$,
               pg_temp.id('p_ana'), pg_temp.id('i_ana')), 'app_077');

    PERFORM pg_temp.acepta('RD-23; 4.3 (Relaciones)', 'supresión de Beto, con una transacción: primero sus portafolios y después la cuenta',
        format($$DELETE FROM portafolio WHERE usuario_id = %1$s;
                 DELETE FROM usuario WHERE id = %1$s$$, pg_temp.id('beto')));
    PERFORM pg_temp.verifica('RD-23', 'no queda nada de Beto: cuenta, consentimientos, portafolios, transacciones ni intermediarios',
        format($$SELECT NOT EXISTS (SELECT FROM usuario WHERE id = %1$s)
                    AND NOT EXISTS (SELECT FROM consentimiento WHERE usuario_id = %1$s)
                    AND NOT EXISTS (SELECT FROM portafolio WHERE usuario_id = %1$s)
                    AND NOT EXISTS (SELECT FROM transaccion WHERE usuario_id = %1$s)
                    AND NOT EXISTS (SELECT FROM intermediario WHERE usuario_id = %1$s)$$,
               pg_temp.id('beto')));

    -- A Ana ya no le quedan transacciones (se eliminaron con «Retiro»), así que
    -- suprimir su cuenta ejerce las cascadas desde usuario con filas.
    PERFORM pg_temp.acepta('RD-23; 4.3 (Relaciones)', 'suprimir la cuenta de Ana suprime en cascada su portafolio restante, sus intermediarios y sus consentimientos',
        format($$DELETE FROM usuario WHERE id = %s$$, pg_temp.id('ana')));
    PERFORM pg_temp.verifica('RD-23', 'no quedan el portafolio «Universidad», los intermediarios ni los consentimientos de Ana',
        format($$SELECT NOT EXISTS (SELECT FROM portafolio WHERE id = %1$s)
                    AND NOT EXISTS (SELECT FROM portafolio WHERE usuario_id = %2$s)
                    AND NOT EXISTS (SELECT FROM intermediario WHERE usuario_id = %2$s)
                    AND NOT EXISTS (SELECT FROM consentimiento WHERE usuario_id = %2$s)$$,
               pg_temp.id('p_ana2'), pg_temp.id('ana')));

    PERFORM pg_temp.acepta('RD-24', 'supresión por carga: la carga de precios de la semilla',
        format($$DELETE FROM carga_datos WHERE id = %s$$, pg_temp.id('c_precios')));
    PERFORM pg_temp.verifica('RD-24', 'sus precios se suprimieron en cascada y los de otra fuente siguen',
        format($$SELECT NOT EXISTS (SELECT FROM precio_cierre WHERE carga_id = %1$s)
                    AND EXISTS (SELECT FROM precio_cierre WHERE carga_id = %2$s)$$,
               pg_temp.id('c_precios'), pg_temp.id('c_prueba')));
    PERFORM pg_temp.acepta('RD-24', 'supresión por carga: la carga de tasas',
        format($$DELETE FROM carga_datos WHERE id = %s$$, pg_temp.id('c_tasas')));
    PERFORM pg_temp.verifica('RD-24', 'sus tasas se suprimieron en cascada',
        $$SELECT NOT EXISTS (SELECT FROM tasa_referencia)$$);
    PERFORM pg_temp.acepta('RD-24', 'supresión por fuente: cargas, versiones y fuente, en ese orden',
        format($$DELETE FROM carga_datos WHERE fuente_id = %1$s;
                 DELETE FROM version_licencia WHERE fuente_id = %1$s;
                 DELETE FROM fuente_datos WHERE id = %1$s$$, pg_temp.id('f_prueba')));
    PERFORM pg_temp.verifica('RD-24', 'no quedan precios de esa fuente',
        format($$SELECT NOT EXISTS (SELECT FROM precio_cierre WHERE fuente_id = %s)$$, pg_temp.id('f_prueba')));
END
$prueba$;

-- =============================================================================
-- Resultado
-- =============================================================================
SELECT count(*)                                     AS casos_aprobados,
       count(*) FILTER (WHERE clase = 'estructura') AS de_estructura,
       count(*) FILTER (WHERE clase = 'positivo')   AS positivos,
       count(*) FILTER (WHERE clase = 'negativo')   AS negativos,
       count(*) FILTER (WHERE rol = 'app_077')      AS como_app_077
FROM pg_temp.caso;

DO $$
BEGIN
    RAISE NOTICE 'RESULTADO: pasaron los % casos de prueba; no se guardaron datos (ROLLBACK; solo avanzaron las secuencias de identidad).',
        (SELECT count(*) FROM pg_temp.caso);
END
$$;

ROLLBACK;
