-- =============================================================================
-- Proyecto 077 · Paso 2: esquema de la base de datos del MVP
-- =============================================================================
-- Sustituye a 02_crear_tabla.sql. Crea las 13 tablas del modelo
-- entidad-relación (SRS, 4.3) con las columnas del diccionario de datos
-- (SRS, 4.4), elimina la tabla de prueba ping, fija la zona horaria de la base
-- y deja a app_077 solo con los privilegios de 4.3.
--
-- Cómo se ejecuta, después del paso 1, conectado a la base de la aplicación
-- como el rol que será dueño de las tablas (en el equipo de desarrollo,
-- postgres):
--
--     psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f 02_crear_esquema.sql
--
-- Todo va en una sola transacción (BEGIN … COMMIT): si algo falla, la base
-- queda como estaba. Sirve en una base recién creada por el paso 1 y en una que
-- ya tiene ping. Si el esquema ya existe, se detiene sin cambiar nada. También
-- se detiene si la configuración regional de la base no pasa a minúsculas las
-- letras acentuadas, porque entonces no se cumpliría RD-03 (ver la condición
-- previa). No contiene contraseñas ni datos de usuarios.
--
-- Nombres de las restricciones (nota c del 4.3): _pk llave primaria, _fk llave
-- foránea, _uq unicidad (restricción o índice único), _ck CHECK, _ix índice.
-- Los NOT NULL conservan el nombre que les da PostgreSQL 18 (tabla_columna_not_null).
-- PostgreSQL evalúa los CHECK de una fila en orden alfabético de su nombre.
--
-- Las marcas «-- ⟦decidir⟧ recomendado: …» señalan lo que el SRS deja por
-- decidir: el script aplica la opción recomendada por las notas del 4.3 y del
-- 4.4, y cada marca dice qué cambiar si Ramon decide otra cosa. Todos los
-- comentarios «--» van entre sentencias, así que psql no los envía al servidor.
-- =============================================================================

\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

SET LOCAL search_path = public;

-- Condiciones previas: base de la aplicación, paso 1 hecho y esquema sin crear.
DO $$
BEGIN
    IF current_database() IN ('postgres', 'template0', 'template1') THEN
        RAISE EXCEPTION 'Conéctate a la base de la aplicación (la del paso 1), no a %.', current_database();
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_077') THEN
        RAISE EXCEPTION 'No existe el rol app_077: ejecuta antes el paso 1 (01_crear_base.sql).';
    END IF;
    IF to_regclass('public.usuario') IS NOT NULL THEN
        RAISE EXCEPTION 'El esquema del Proyecto 077 ya existe en la base %; este script no se vuelve a ejecutar.', current_database()
            USING ERRCODE = 'duplicate_table';
    END IF;
    -- RD-03: los índices únicos usan lower(), que depende de la configuración
    -- regional de la base (LC_CTYPE); con C o POSIX no pasa a minúsculas las
    -- letras acentuadas ni la eñe, y aceptaría «Educación» y «EDUCACIÓN» en la
    -- misma cuenta. 01_crear_base.sql no la fija: la base hereda la de template1.
    IF lower('ÁÉÍÓÚÜÑ') IS DISTINCT FROM 'áéíóúüñ' THEN
        RAISE EXCEPTION 'La configuración regional de la base % (LC_CTYPE %) no pasa a minúsculas las letras acentuadas: RD-03 aceptaría «Educación» y «EDUCACIÓN» en la misma cuenta.',
            current_database(), (SELECT datctype FROM pg_database WHERE datname = current_database())
            USING HINT = 'Crea la base con CREATE DATABASE … TEMPLATE template0 ENCODING ''UTF8'' LOCALE ''es-MX'' (en Linux, ''es_MX.UTF-8''), o con LOCALE_PROVIDER builtin BUILTIN_LOCALE ''C.UTF-8''.';
    END IF;
END
$$;

-- Tabla desechable de la prueba de extremo a extremo (nota c del 4.3).
DROP TABLE IF EXISTS ping;

-- RD-15: al comparar fechas rige la hora de la Ciudad de México. Se fija para
-- las sesiones nuevas de esta base, sin escribir su nombre.
DO $$
BEGIN
    EXECUTE format('ALTER DATABASE %I SET timezone TO %L',
                   current_database(), 'America/Mexico_City');
END
$$;

-- -----------------------------------------------------------------------------
-- Decisiones generales
--
-- ⟦decidir⟧ recomendado (4.3, «Números exactos», y nota a.2 del 4.3): numeric
--   SIN precisión ni escala, con la escala de RD-13 en un CHECK *_escala_ck y el
--   tamaño en un CHECK *_tamano_ck, para que la base rechace sin redondear
--   (RD-14); min_scale ignora los ceros finales, como pydantic. Si Ramon elige
--   numeric(p,s) (por ejemplo, precio numeric(18,7) e importe numeric(18,2)),
--   quitar los *_escala_ck y *_tamano_ck y decir en el SRS que la base redondea.
--   Los *_escala_ck se escriben «(min_scale(x) <= n) IS TRUE» porque min_scale
--   de 'NaN' e 'Infinity' es nulo y un CHECK nulo deja pasar la fila: así esos
--   valores, que no son decimales (RD-12), se rechazan aunque se quiten los topes.
--
-- ⟦decidir⟧ recomendado (4.3 y 4.4; ningún requisito los respalda, nota a.4 del
--   4.4): topes de tamaño, precio < 10^11 e importe < 10^16, para que
--   títulos × precio ± importe quepa en los 28 dígitos del motor (RD-12). Si
--   Ramon los quita, borrar transaccion_precio_tamano_ck,
--   precio_cierre_precio_tamano_ck y transaccion_importe_comisiones_tamano_ck.
-- -----------------------------------------------------------------------------

-- usuario ---------------------------------------------------------------------
CREATE TABLE usuario (
    id               bigint GENERATED ALWAYS AS IDENTITY,
    correo           text   NOT NULL,
    contrasena_hash  text   NOT NULL,
    estado           text   NOT NULL,
    CONSTRAINT usuario_pk PRIMARY KEY (id),
    CONSTRAINT usuario_estado_ck CHECK (estado IN ('activa', 'bloqueada'))
);
-- RD-03: correo único sin distinguir mayúsculas ni espacios iniciales o
-- finales. INSERT … ON CONFLICT ((lower(btrim(correo)))) infiere este índice.
CREATE UNIQUE INDEX usuario_correo_uq ON usuario (lower(btrim(correo)));

-- version_aviso ---------------------------------------------------------------
-- ⟦decidir⟧ recomendado (4.4, version_aviso.vigente_desde; nota b del 4.3): la
--   versión se identifica por vigente_desde, sin atributo version, como dibuja
--   4.3. Si Ramon decide el atributo, agregarlo antes a 3.4.1, 4.3 y 4.4, y aquí
--   version text NOT NULL con CONSTRAINT version_aviso_version_uq UNIQUE (version).
CREATE TABLE version_aviso (
    id             bigint      GENERATED ALWAYS AS IDENTITY,
    texto          text        NOT NULL,
    vigente_desde  timestamptz NOT NULL,
    CONSTRAINT version_aviso_pk PRIMARY KEY (id),
    CONSTRAINT version_aviso_vigente_desde_uq UNIQUE (vigente_desde)
);

-- consentimiento --------------------------------------------------------------
-- ⟦decidir⟧ recomendado (nota a.5 del 4.3): medio es lista cerrada, solo 'web'.
--   Si Ramon decide texto libre, quitar consentimiento_medio_ck; si decide más
--   medios, agregarlos a la lista.
CREATE TABLE consentimiento (
    id                bigint      GENERATED ALWAYS AS IDENTITY,
    usuario_id        bigint      NOT NULL,
    version_aviso_id  bigint      NOT NULL,
    tipo              text        NOT NULL,
    momento           timestamptz NOT NULL DEFAULT now(),
    medio             text        NOT NULL,
    CONSTRAINT consentimiento_pk PRIMARY KEY (id),
    CONSTRAINT consentimiento_usuario_fk FOREIGN KEY (usuario_id)
        REFERENCES usuario (id) ON DELETE CASCADE,
    CONSTRAINT consentimiento_version_aviso_fk FOREIGN KEY (version_aviso_id)
        REFERENCES version_aviso (id) ON DELETE NO ACTION,
    CONSTRAINT consentimiento_tipo_ck CHECK (tipo IN ('otorgamiento', 'revocacion')),
    CONSTRAINT consentimiento_medio_ck CHECK (medio IN ('web'))
);
-- RD-23: la cascada desde usuario no recorre la tabla.
CREATE INDEX consentimiento_usuario_ix ON consentimiento (usuario_id);

-- portafolio ------------------------------------------------------------------
CREATE TABLE portafolio (
    id           bigint GENERATED ALWAYS AS IDENTITY,
    usuario_id   bigint NOT NULL,
    nombre       text   NOT NULL,
    divisa_base  text   NOT NULL,
    CONSTRAINT portafolio_pk PRIMARY KEY (id),
    CONSTRAINT portafolio_usuario_id_uq UNIQUE (usuario_id, id),
    CONSTRAINT portafolio_usuario_fk FOREIGN KEY (usuario_id)
        REFERENCES usuario (id) ON DELETE CASCADE,
    CONSTRAINT portafolio_nombre_ck CHECK (btrim(nombre) <> ''),
    CONSTRAINT portafolio_divisa_base_ck CHECK (divisa_base = 'MXN')
);
-- RD-03: nombre único en la cuenta sin distinguir mayúsculas ni espacios.
CREATE UNIQUE INDEX portafolio_nombre_uq ON portafolio (usuario_id, lower(btrim(nombre)));

-- intermediario ---------------------------------------------------------------
CREATE TABLE intermediario (
    id          bigint GENERATED ALWAYS AS IDENTITY,
    usuario_id  bigint NOT NULL,
    nombre      text   NOT NULL,
    CONSTRAINT intermediario_pk PRIMARY KEY (id),
    CONSTRAINT intermediario_usuario_id_uq UNIQUE (usuario_id, id),
    CONSTRAINT intermediario_usuario_fk FOREIGN KEY (usuario_id)
        REFERENCES usuario (id) ON DELETE CASCADE,
    CONSTRAINT intermediario_nombre_ck CHECK (btrim(nombre) <> '')
);
-- RD-03: nombre único en la cuenta sin distinguir mayúsculas ni espacios.
CREATE UNIQUE INDEX intermediario_nombre_uq ON intermediario (usuario_id, lower(btrim(nombre)));

-- instrumento -----------------------------------------------------------------
-- ⟦decidir⟧ recomendado (nota a.3 del 4.3): FK compuesta del subtipo. Por eso
--   instrumento tiene instrumento_id_clave_clase_uq, UNIQUE (id, clave,
--   clase_activo), a la que remite emision_cetes_instrumento_fk. Si Ramon
--   decide sin ella, quitar esta UNIQUE y ver la marca de emision_cetes.
CREATE TABLE instrumento (
    id               bigint  GENERATED ALWAYS AS IDENTITY,
    clave            text    NOT NULL,
    nombre           text    NOT NULL,
    divisa           text    NOT NULL,
    clase_activo     text    NOT NULL,
    de_demostracion  boolean NOT NULL,
    CONSTRAINT instrumento_pk PRIMARY KEY (id),
    CONSTRAINT instrumento_clave_uq UNIQUE (clave),
    CONSTRAINT instrumento_id_clave_clase_uq UNIQUE (id, clave, clase_activo),
    CONSTRAINT instrumento_clase_activo_ck CHECK (clase_activo IN ('accion', 'etf', 'fibra', 'cetes')),
    CONSTRAINT instrumento_clave_ck CHECK (clase_activo <> 'cetes' OR clave ~ '^BI[0-9]{6}$'),
    CONSTRAINT instrumento_divisa_ck CHECK (divisa = 'MXN'),
    CONSTRAINT instrumento_de_demostracion_ck CHECK (de_demostracion = (clase_activo <> 'cetes'))
);

-- emision_cetes ---------------------------------------------------------------
-- ⟦decidir⟧ recomendado (nota a.3 del 4.3): la FK del subtipo,
--   (instrumento_id, clave, clase_activo) → instrumento (id, clave,
--   clase_activo), sustituye a la FK simple; con emision_cetes_clase_activo_ck
--   y emision_cetes_clave_ck, solo un CETES tiene emisión y su clave
--   corresponde al vencimiento (RD-04). Si Ramon decide sin ella: quitar las
--   columnas clave y clase_activo con sus dos CHECK, usar
--   FOREIGN KEY (instrumento_id) REFERENCES instrumento (id), quitar
--   instrumento_id_clave_clase_uq, y RD-04 pasa a Catálogo de instrumentos.
--   Con la FK del subtipo, emision_cetes_vencimiento_uq es redundante (la clave
--   ya es única y corresponde al vencimiento); se conserva porque 4.3 la pide.
--   En emision_cetes_clave_ck, «vencimiento::timestamp» hace explícita la
--   conversión: sin ella, PostgreSQL convierte la fecha a timestamptz y el
--   CHECK dependería de la zona horaria de la sesión (RD-15).
-- ⟦decidir⟧ recomendado (4.4): CHECK de escala 2 en valor_nominal. Con
--   CHECK (valor_nominal = 10.00) sobra (nota a.4 del 4.4); si Ramon lo quita,
--   borrar emision_cetes_valor_nominal_escala_ck.
CREATE TABLE emision_cetes (
    instrumento_id  bigint  NOT NULL,
    clave           text    NOT NULL,
    clase_activo    text    NOT NULL,
    vencimiento     date    NOT NULL,
    valor_nominal   numeric NOT NULL,
    CONSTRAINT emision_cetes_pk PRIMARY KEY (instrumento_id),
    CONSTRAINT emision_cetes_instrumento_fk FOREIGN KEY (instrumento_id, clave, clase_activo)
        REFERENCES instrumento (id, clave, clase_activo) ON DELETE NO ACTION,
    CONSTRAINT emision_cetes_vencimiento_uq UNIQUE (vencimiento),
    CONSTRAINT emision_cetes_clase_activo_ck CHECK (clase_activo = 'cetes'),
    CONSTRAINT emision_cetes_clave_ck CHECK (clave = concat('BI', to_char(vencimiento::timestamp, 'YYMMDD'))),
    CONSTRAINT emision_cetes_valor_nominal_ck CHECK (valor_nominal = 10.00),
    CONSTRAINT emision_cetes_valor_nominal_escala_ck CHECK ((min_scale(valor_nominal) <= 2) IS TRUE)
);

-- transaccion -----------------------------------------------------------------
-- ⟦decidir⟧ recomendado (nota a.4 del 4.3; RF-05, crit. 2): importe con escala
--   2, que admite 0, y CHECK de la venta. Si Ramon decide otra escala, cambiar
--   el 2 de transaccion_importe_comisiones_escala_ck; si no admite 0, cambiar
--   «>= 0» por «> 0» en transaccion_importe_comisiones_ck; si no quiere el
--   CHECK de la venta, borrar transaccion_importe_venta_ck.
-- ⟦decidir⟧ recomendado (3.4.1 y 4.4, dominio tipo_transaccion, «ampliable por
--   S-07»): lista cerrada, 'compra' o 'venta'. Si S-07 agrega tipos (por
--   ejemplo, saldo inicial o traspaso), agregarlos a transaccion_tipo_ck y
--   revisar transaccion_importe_venta_ck, que, como lo escribe 4.3, aplica el
--   límite a todo tipo que no sea 'compra' (si solo debe valer en la venta,
--   escribirlo tipo <> 'venta' OR …, y cambiarlo también en 4.3).
-- La FK a portafolio va en cascada (RD-10) y la del intermediario, sin cascada
-- (RD-02; RD-09); las dos son compuestas con usuario_id (RD-01; RD-02).
CREATE TABLE transaccion (
    id                  bigint      GENERATED ALWAYS AS IDENTITY,
    usuario_id          bigint      NOT NULL,
    portafolio_id       bigint      NOT NULL,
    intermediario_id    bigint      NOT NULL,
    instrumento_id      bigint      NOT NULL,
    tipo                text        NOT NULL,
    fecha_concertacion  date        NOT NULL,
    cantidad            integer     NOT NULL,
    precio              numeric     NOT NULL,
    importe_comisiones  numeric     NOT NULL,
    registrada_en       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT transaccion_pk PRIMARY KEY (id),
    CONSTRAINT transaccion_portafolio_fk FOREIGN KEY (usuario_id, portafolio_id)
        REFERENCES portafolio (usuario_id, id) ON DELETE CASCADE,
    CONSTRAINT transaccion_intermediario_fk FOREIGN KEY (usuario_id, intermediario_id)
        REFERENCES intermediario (usuario_id, id) ON DELETE NO ACTION,
    CONSTRAINT transaccion_instrumento_fk FOREIGN KEY (instrumento_id)
        REFERENCES instrumento (id) ON DELETE NO ACTION,
    CONSTRAINT transaccion_tipo_ck CHECK (tipo IN ('compra', 'venta')),
    CONSTRAINT transaccion_fecha_concertacion_ck
        CHECK (fecha_concertacion <= (registrada_en AT TIME ZONE 'America/Mexico_City')::date),
    CONSTRAINT transaccion_cantidad_ck CHECK (cantidad > 0),
    CONSTRAINT transaccion_precio_ck CHECK (precio > 0),
    CONSTRAINT transaccion_precio_escala_ck CHECK ((min_scale(precio) <= 7) IS TRUE),
    CONSTRAINT transaccion_precio_tamano_ck CHECK (precio < 100000000000),
    CONSTRAINT transaccion_importe_comisiones_ck CHECK (importe_comisiones >= 0),
    CONSTRAINT transaccion_importe_comisiones_escala_ck CHECK ((min_scale(importe_comisiones) <= 2) IS TRUE),
    CONSTRAINT transaccion_importe_comisiones_tamano_ck CHECK (importe_comisiones < 10000000000000000),
    CONSTRAINT transaccion_importe_venta_ck CHECK (tipo = 'compra' OR importe_comisiones < cantidad * precio)
);
-- 3.4.8: lectura hasta la fecha de corte; sirve también a la cascada de RD-10.
CREATE INDEX transaccion_portafolio_fecha_ix ON transaccion (usuario_id, portafolio_id, fecha_concertacion);

-- fuente_datos ----------------------------------------------------------------
CREATE TABLE fuente_datos (
    id               bigint  GENERATED ALWAYS AS IDENTITY,
    nombre           text    NOT NULL,
    direccion        text,
    de_demostracion  boolean NOT NULL,
    CONSTRAINT fuente_datos_pk PRIMARY KEY (id),
    CONSTRAINT fuente_datos_nombre_uq UNIQUE (nombre)
);

-- version_licencia ------------------------------------------------------------
CREATE TABLE version_licencia (
    id                   bigint GENERATED ALWAYS AS IDENTITY,
    fuente_id            bigint NOT NULL,
    version              text   NOT NULL,
    usos_permitidos      text   NOT NULL,
    obligacion_suprimir  text,
    atribucion           text,
    CONSTRAINT version_licencia_pk PRIMARY KEY (id),
    CONSTRAINT version_licencia_fuente_id_uq UNIQUE (fuente_id, id),
    CONSTRAINT version_licencia_version_uq UNIQUE (fuente_id, version),
    CONSTRAINT version_licencia_fuente_fk FOREIGN KEY (fuente_id)
        REFERENCES fuente_datos (id) ON DELETE NO ACTION
);

-- carga_datos -----------------------------------------------------------------
-- ⟦decidir⟧ recomendado (nota a.5 del 4.3): resultado es lista cerrada,
--   'exitosa' o 'fallida'. Si Ramon decide texto libre, quitar
--   carga_datos_resultado_ck; si decide otros valores, cambiar la lista.
-- ⟦decidir⟧ recomendado (nota a.6 del 4.3; P-34): obtenida_en existe y es
--   obligatoria. Si P-34 no adopta la fecha de obtención, quitar la columna.
-- ⟦decidir⟧ elegido aquí, porque el SRS no recomienda nada (nota a.7 del 4.4):
--   valores_sustituidos vale '[]'::jsonb por omisión (en el MVP nada se
--   sustituye). Sin CHECK de forma, porque 4.4 dice «Sin CHECK sobre su forma»;
--   si Ramon quiere uno, agregar CONSTRAINT carga_datos_valores_sustituidos_ck
--   CHECK (jsonb_typeof(valores_sustituidos) = 'array'). Si prefiere no tener
--   valor por omisión, quitar el DEFAULT y que la Instalación escriba '[]'.
CREATE TABLE carga_datos (
    id                          bigint      GENERATED ALWAYS AS IDENTITY,
    fuente_id                   bigint      NOT NULL,
    version_licencia_id         bigint      NOT NULL,
    origen                      text        NOT NULL,
    obtenida_en                 timestamptz NOT NULL,
    incorporada_en              timestamptz NOT NULL DEFAULT now(),
    fecha_inicial               date        NOT NULL,
    fecha_final                 date        NOT NULL,
    resultado                   text        NOT NULL,
    observaciones_incorporadas  integer     NOT NULL,
    observaciones_omitidas      integer     NOT NULL,
    valores_sustituidos         jsonb       NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT carga_datos_pk PRIMARY KEY (id),
    CONSTRAINT carga_datos_id_fuente_uq UNIQUE (id, fuente_id),
    CONSTRAINT carga_datos_fuente_fk FOREIGN KEY (fuente_id)
        REFERENCES fuente_datos (id) ON DELETE NO ACTION,
    CONSTRAINT carga_datos_version_licencia_fk FOREIGN KEY (fuente_id, version_licencia_id)
        REFERENCES version_licencia (fuente_id, id) ON DELETE NO ACTION,
    CONSTRAINT carga_datos_origen_ck CHECK (origen IN ('semilla')),
    CONSTRAINT carga_datos_resultado_ck CHECK (resultado IN ('exitosa', 'fallida')),
    CONSTRAINT carga_datos_intervalo_ck CHECK (fecha_inicial <= fecha_final),
    CONSTRAINT carga_datos_observaciones_incorporadas_ck CHECK (observaciones_incorporadas >= 0),
    CONSTRAINT carga_datos_observaciones_omitidas_ck CHECK (observaciones_omitidas >= 0)
);

-- precio_cierre ---------------------------------------------------------------
CREATE TABLE precio_cierre (
    id              bigint  GENERATED ALWAYS AS IDENTITY,
    instrumento_id  bigint  NOT NULL,
    fecha           date    NOT NULL,
    precio          numeric NOT NULL,
    carga_id        bigint  NOT NULL,
    fuente_id       bigint  NOT NULL,
    CONSTRAINT precio_cierre_pk PRIMARY KEY (id),
    CONSTRAINT precio_cierre_instrumento_fecha_fuente_uq UNIQUE (instrumento_id, fecha, fuente_id),
    CONSTRAINT precio_cierre_instrumento_fk FOREIGN KEY (instrumento_id)
        REFERENCES instrumento (id) ON DELETE NO ACTION,
    CONSTRAINT precio_cierre_carga_fk FOREIGN KEY (carga_id, fuente_id)
        REFERENCES carga_datos (id, fuente_id) ON DELETE CASCADE,
    CONSTRAINT precio_cierre_precio_ck CHECK (precio > 0),
    CONSTRAINT precio_cierre_precio_escala_ck CHECK ((min_scale(precio) <= 7) IS TRUE),
    CONSTRAINT precio_cierre_precio_tamano_ck CHECK (precio < 100000000000)
);
-- RD-24: suprimir una carga sin recorrer la tabla.
CREATE INDEX precio_cierre_carga_ix ON precio_cierre (carga_id, fuente_id);

-- tasa_referencia -------------------------------------------------------------
-- ⟦decidir⟧ recomendado (RD-13, ⟦confirmar en la API⟧): escala 5 en valor. Si
--   la API del SIE trae otra escala, cambiar el 5 de
--   tasa_referencia_valor_escala_ck.
-- Plazos nominales de RF-30, con 728 días (P-15, opción A).
CREATE TABLE tasa_referencia (
    id                bigint  GENERATED ALWAYS AS IDENTITY,
    plazo_nominal     integer NOT NULL,
    fecha_colocacion  date    NOT NULL,
    valor             numeric NOT NULL,
    unidad            text    NOT NULL,
    plazo_efectivo    integer NOT NULL,
    carga_id          bigint  NOT NULL,
    CONSTRAINT tasa_referencia_pk PRIMARY KEY (id),
    CONSTRAINT tasa_referencia_plazo_fecha_uq UNIQUE (plazo_nominal, fecha_colocacion),
    CONSTRAINT tasa_referencia_carga_fk FOREIGN KEY (carga_id)
        REFERENCES carga_datos (id) ON DELETE CASCADE,
    CONSTRAINT tasa_referencia_plazo_nominal_ck CHECK (plazo_nominal IN (28, 91, 182, 364, 728)),
    CONSTRAINT tasa_referencia_plazo_efectivo_ck CHECK (plazo_efectivo > 0),
    CONSTRAINT tasa_referencia_valor_escala_ck CHECK ((min_scale(valor) <= 5) IS TRUE)
);
-- RD-24: suprimir una carga sin recorrer la tabla.
CREATE INDEX tasa_referencia_carga_ix ON tasa_referencia (carga_id);

-- -----------------------------------------------------------------------------
-- Comentarios (diccionario de datos, 4.4)
-- -----------------------------------------------------------------------------
COMMENT ON TABLE usuario IS 'Cuenta: correo, contraseña no reversible y estado; ningún otro dato de identificación (3.4.1; RF-01; RF-12).';
COMMENT ON COLUMN usuario.id IS 'Llave sustituta de la cuenta; la asigna la base (4.3).';
COMMENT ON COLUMN usuario.correo IS 'Correo tal como se capturó (RD-14); único sin distinguir mayúsculas ni espacios iniciales o finales (RD-03).';
COMMENT ON COLUMN usuario.contrasena_hash IS 'Contraseña en forma no reversible (Argon2id con pwdlib), distinta por cuenta; la calcula la aplicación (RNF-04; P-06).';
COMMENT ON COLUMN usuario.estado IS 'activa o bloqueada; pasa a bloqueada al revocar el consentimiento y no vuelve a activa (RD-23).';

COMMENT ON TABLE version_aviso IS 'Versiones del aviso de privacidad, con su texto y el momento desde el que rigen (RF-12; P-05).';
COMMENT ON COLUMN version_aviso.id IS 'Llave sustituta; no es un número de versión publicado (4.4).';
COMMENT ON COLUMN version_aviso.texto IS 'Texto íntegro del aviso en esa versión, que prueba qué aceptó cada usuario (RF-12; RD-14).';
COMMENT ON COLUMN version_aviso.vigente_desde IS 'Momento desde el que rige, único; rige la de mayor vigente_desde no posterior a cada momento (RF-12, crit. 1).';

COMMENT ON TABLE consentimiento IS 'Otorgamientos y revocaciones del consentimiento; no se modifican ni se eliminan salvo por RD-23 (RD-11; RF-12).';
COMMENT ON COLUMN consentimiento.id IS 'Llave sustituta del registro de consentimiento (4.3).';
COMMENT ON COLUMN consentimiento.usuario_id IS 'Cuenta que otorga o revoca; se suprime con ella (RD-01; RD-23).';
COMMENT ON COLUMN consentimiento.version_aviso_id IS 'Versión del aviso a la que remite el otorgamiento o la revocación (RF-12, crit. 1).';
COMMENT ON COLUMN consentimiento.tipo IS 'otorgamiento o revocacion (3.4.1; RD-11).';
COMMENT ON COLUMN consentimiento.momento IS 'Momento del otorgamiento o la revocación; lo fija la base (RD-15).';
COMMENT ON COLUMN consentimiento.medio IS 'Medio por el que se otorgó o se revocó; lista cerrada, en el MVP solo web (3.4.1; RF-12, crit. 1; 4.3, CHECK de lista cerrada).';

COMMENT ON TABLE portafolio IS 'Portafolios de cada usuario, sin efectivo, posiciones ni indicadores (RF-03; 3.4.3).';
COMMENT ON COLUMN portafolio.id IS 'Llave sustituta; no cambia al renombrar (RF-03).';
COMMENT ON COLUMN portafolio.usuario_id IS 'Usuario dueño, el único que lo consulta y opera (RD-01; RF-02).';
COMMENT ON COLUMN portafolio.nombre IS 'Nombre tal como se capturó, no vacío y único en la cuenta sin distinguir mayúsculas ni espacios (RD-03; RD-14).';
COMMENT ON COLUMN portafolio.divisa_base IS 'Divisa base; en el MVP, solo MXN (RD-08; P-02).';

COMMENT ON TABLE intermediario IS 'Intermediarios de cada usuario; no se modifican ni se eliminan (RD-09) y se suprimen con su cuenta (RD-23).';
COMMENT ON COLUMN intermediario.id IS 'Llave sustituta del intermediario (4.3).';
COMMENT ON COLUMN intermediario.usuario_id IS 'Usuario que lo registró, el único que lo consulta y usa (RD-01; RD-02).';
COMMENT ON COLUMN intermediario.nombre IS 'Nombre tal como se capturó, no vacío y único en la cuenta sin distinguir mayúsculas ni espacios (RD-03; RF-25).';

COMMENT ON TABLE instrumento IS 'Catálogo común de acciones, ETF, FIBRA y emisiones de CETES; nadie lo modifica (RF-04; RD-09).';
COMMENT ON COLUMN instrumento.id IS 'Llave sustituta; el inversionista reconoce el instrumento por su clave (4.3).';
COMMENT ON COLUMN instrumento.clave IS 'Clave única; en un CETES, BI y el vencimiento en AAMMDD, y en las demás, ficticia (RD-04; RF-04).';
COMMENT ON COLUMN instrumento.nombre IS 'Nombre que el catálogo muestra junto a la clave (RF-04).';
COMMENT ON COLUMN instrumento.divisa IS 'Divisa del instrumento; en el MVP, solo MXN (RD-08; P-02).';
COMMENT ON COLUMN instrumento.clase_activo IS 'accion, etf, fibra o cetes, excluyentes entre sí (RF-04, crit. 1; P-14).';
COMMENT ON COLUMN instrumento.de_demostracion IS 'Verdadero si y solo si no es CETES: clave ficticia de demostración (RF-04, crit. 3; P-21).';

COMMENT ON TABLE emision_cetes IS 'Subtipo del instrumento de clase CETES: vencimiento y valor nominal de cada emisión (3.4.2; RD-04).';
COMMENT ON COLUMN emision_cetes.instrumento_id IS 'Instrumento CETES que detalla; llave primaria y parte de la FK del subtipo (3.4.2).';
COMMENT ON COLUMN emision_cetes.clave IS 'Clave del instrumento, repetida para que la base compruebe que corresponde al vencimiento (RD-04).';
COMMENT ON COLUMN emision_cetes.clase_activo IS 'Siempre cetes, repetida para que solo un CETES tenga emisión (RD-04; técnico, 4.3).';
COMMENT ON COLUMN emision_cetes.vencimiento IS 'Fecha de vencimiento, una emisión por fecha; desde ella se rechazan sus transacciones (RD-04; RF-26a).';
COMMENT ON COLUMN emision_cetes.valor_nominal IS 'Valor nominal por título, 10.00 pesos (RD-06; RD-13; RF-26b).';

COMMENT ON TABLE transaccion IS 'Compras y ventas que captura RF-05; el costo o ingreso por título se calcula y no se guarda (3.4.3).';
COMMENT ON COLUMN transaccion.id IS 'Llave sustituta de la transacción (4.3).';
COMMENT ON COLUMN transaccion.usuario_id IS 'Usuario del portafolio, repetido para que portafolio e intermediario sean del mismo usuario (RD-01; RD-02).';
COMMENT ON COLUMN transaccion.portafolio_id IS 'Portafolio de la transacción; al eliminarlo se eliminan sus transacciones (RD-10).';
COMMENT ON COLUMN transaccion.intermediario_id IS 'Intermediario de la operación, del mismo usuario (RD-02; RF-25; RF-28).';
COMMENT ON COLUMN transaccion.instrumento_id IS 'Instrumento comprado o vendido (RF-04; RD-08).';
COMMENT ON COLUMN transaccion.tipo IS 'compra o venta; el sentido lo da el tipo (RF-05; RD-06).';
COMMENT ON COLUMN transaccion.fecha_concertacion IS 'Fecha en que se pactó; no posterior a la del registro en la Ciudad de México (RD-07; RD-15).';
COMMENT ON COLUMN transaccion.cantidad IS 'Número entero de títulos, mayor que 0 (RD-06; RD-13).';
COMMENT ON COLUMN transaccion.precio IS 'Precio por título sin comisiones: mayor que 0, menor que 10^11 y con 7 decimales o menos, sin redondear (RD-06; RD-13; RD-14).';
COMMENT ON COLUMN transaccion.importe_comisiones IS 'Comisiones con su IVA: 0 o más, menor que 10^16, 2 decimales o menos y, en una venta, menor que títulos × precio (RF-05).';
COMMENT ON COLUMN transaccion.registrada_en IS 'Momento del registro; lo fija la base (RD-07; RD-15).';

COMMENT ON TABLE fuente_datos IS 'Fuentes de los precios y las tasas (RF-07, crit. 3; RF-31).';
COMMENT ON COLUMN fuente_datos.id IS 'Llave sustituta de la fuente (4.3).';
COMMENT ON COLUMN fuente_datos.nombre IS 'Nombre único con que se presenta la fuente junto a cada dato (RF-31; R-05).';
COMMENT ON COLUMN fuente_datos.direccion IS 'Dirección de Internet de la fuente, que acompaña su nombre en la atribución; admite nulo (RF-31, crit. 2).';
COMMENT ON COLUMN fuente_datos.de_demostracion IS 'Indica si sus datos son de demostración, como la semilla sintética (RF-07, crit. 3; RF-31, crit. 3).';

COMMENT ON TABLE version_licencia IS 'Versiones de los términos de uso de cada fuente, que amparan las cargas (RF-31, crit. 1; R-05; RD-24).';
COMMENT ON COLUMN version_licencia.id IS 'Llave sustituta de la versión (4.3).';
COMMENT ON COLUMN version_licencia.fuente_id IS 'Fuente cuyos términos describe (RF-31).';
COMMENT ON COLUMN version_licencia.version IS 'Identificador de la versión, sin repetirse en su fuente (técnico, 4.3; RF-31).';
COMMENT ON COLUMN version_licencia.usos_permitidos IS 'Usos que permiten los términos (R-05).';
COMMENT ON COLUMN version_licencia.obligacion_suprimir IS 'Obligación de suprimir los datos; nulo si la versión no la impone (RD-24; R-05).';
COMMENT ON COLUMN version_licencia.atribucion IS 'Atribución que exigen los términos; nulo si la versión no la exige (R-05; RF-31, crit. 2).';

COMMENT ON TABLE carga_datos IS 'Cargas de precios o tasas, que dan a cada dato fuente, fecha de carga y licencia (RD-17; RF-31, crit. 1).';
COMMENT ON COLUMN carga_datos.id IS 'Llave sustituta de la carga (4.3).';
COMMENT ON COLUMN carga_datos.fuente_id IS 'Fuente de los datos, la misma de su versión de licencia (RF-31, crit. 1; RD-19).';
COMMENT ON COLUMN carga_datos.version_licencia_id IS 'Versión de los términos que ampara la carga, de la misma fuente (RF-31, crit. 1).';
COMMENT ON COLUMN carga_datos.origen IS 'Vía de los datos; en el MVP, solo semilla (3.4.1; RF-07; RF-30).';
COMMENT ON COLUMN carga_datos.obtenida_en IS 'Momento en que se obtuvieron los datos de la fuente (RD-15; P-34).';
COMMENT ON COLUMN carga_datos.incorporada_en IS 'Momento en que la carga incorporó sus datos, que es la fecha de carga de RF-31; lo fija la base (RD-15).';
COMMENT ON COLUMN carga_datos.fecha_inicial IS 'Primera fecha de los datos que cubre la carga, no posterior a fecha_final (técnico, 4.3).';
COMMENT ON COLUMN carga_datos.fecha_final IS 'Última fecha de los datos que cubre la carga (técnico, 4.3).';
COMMENT ON COLUMN carga_datos.resultado IS 'Resultado de la carga; lista cerrada: exitosa o fallida (3.4.1; 4.3, CHECK de lista cerrada).';
COMMENT ON COLUMN carga_datos.observaciones_incorporadas IS 'Observaciones incorporadas como precios o tasas, 0 o más (RNF-09).';
COMMENT ON COLUMN carga_datos.observaciones_omitidas IS 'Observaciones omitidas, como las N/E o sin plazo efectivo, 0 o más (RD-18; RD-20).';
COMMENT ON COLUMN carga_datos.valores_sustituidos IS 'Valores anteriores que la carga sustituyó, con cada cifra como cadena JSON; vacío por omisión (RD-12; RD-21; P-34).';

COMMENT ON TABLE precio_cierre IS 'Cierre de cada instrumento por fecha y fuente; en el MVP, de la semilla sintética (RF-07; RD-19).';
COMMENT ON COLUMN precio_cierre.id IS 'Llave sustituta del precio (4.3).';
COMMENT ON COLUMN precio_cierre.instrumento_id IS 'Instrumento del precio; nunca una emisión de CETES, lo que comprueba la aplicación (RD-04).';
COMMENT ON COLUMN precio_cierre.fecha IS 'Fecha del cierre; uno por instrumento, fecha y fuente (RD-15; RD-19).';
COMMENT ON COLUMN precio_cierre.precio IS 'Precio de cierre por título: mayor que 0, menor que 10^11 y con 7 decimales o menos (RD-06; RD-13; RD-14).';
COMMENT ON COLUMN precio_cierre.carga_id IS 'Carga de la que proviene; al suprimirla se suprime el precio (RD-17; RD-24).';
COMMENT ON COLUMN precio_cierre.fuente_id IS 'Fuente del precio, la de su carga (técnico, 4.3; RD-19).';

COMMENT ON TABLE tasa_referencia IS 'Tasas de las subastas primarias de CETES del CF107 del SIE, con su plazo efectivo (RF-30; RD-18).';
COMMENT ON COLUMN tasa_referencia.id IS 'Llave sustituta de la tasa (4.3).';
COMMENT ON COLUMN tasa_referencia.plazo_nominal IS 'Plazo de la subasta en días: 28, 91, 182, 364 o 728 (RF-30; P-15).';
COMMENT ON COLUMN tasa_referencia.fecha_colocacion IS 'Fecha de colocación; una tasa por plazo y fecha, aunque sea posterior a su carga (RD-19; RD-20).';
COMMENT ON COLUMN tasa_referencia.valor IS 'Tasa en por ciento anual tal como se publica, con 5 decimales o menos (RD-13; RD-14).';
COMMENT ON COLUMN tasa_referencia.unidad IS 'Unidad en que la fuente publica el valor; en el CF107, por ciento anual (RNF-09).';
COMMENT ON COLUMN tasa_referencia.plazo_efectivo IS 'Plazo en días de la colocación, mayor que 0; sin él la tasa no se carga (RD-06; RD-18).';
COMMENT ON COLUMN tasa_referencia.carga_id IS 'Carga de la que proviene; al suprimirla se suprime la tasa (RD-17; RD-24).';

-- -----------------------------------------------------------------------------
-- Privilegios de app_077
--
-- ⟦decidir⟧ recomendado (fila «Privilegios de app_077» del 4.3 y nota a.1 del
--   4.3): las tablas son del rol que ejecuta los scripts; app_077 pierde CREATE
--   en public y solo puede:
--     · SELECT en las 13 tablas (en catálogo, datos de mercado y aviso, nada más);
--     · INSERT sin id ni momentos en usuario, consentimiento, portafolio,
--       intermediario y transaccion;
--     · UPDATE solo de portafolio.nombre, usuario.estado y usuario.contrasena_hash;
--     · DELETE solo de portafolio.
--   Las cascadas de RD-10 no exigen DELETE en transaccion, y la identidad no
--   exige privilegios sobre su secuencia. En la base, app_077 conserva CONNECT
--   (paso 1) y pierde TEMPORARY, que PUBLIC tiene por omisión en cada base y le
--   permitiría crear tablas y funciones temporales, algo que la aplicación no
--   ofrece; el dueño y los superusuarios no lo pierden. Si Ramon decide los
--   privilegios amplios de antes, sustituir esta sección por
--     GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_077;
--   y entonces «la base fija los momentos» deja de ser garantía (nota a.9 del 4.4);
--   si solo quiere permitir tablas temporales, borrar el bloque DO que revoca
--   TEMPORARY y el caso de 03 que lo prueba.
-- -----------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_077;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_077;
REVOKE CREATE ON SCHEMA public FROM app_077;
GRANT USAGE ON SCHEMA public TO app_077;

-- Sin escribir el nombre de la base, como la zona horaria.
DO $$
BEGIN
    EXECUTE format('REVOKE TEMPORARY ON DATABASE %I FROM PUBLIC', current_database());
END
$$;

GRANT SELECT ON usuario, version_aviso, consentimiento, portafolio, intermediario,
                instrumento, emision_cetes, transaccion, fuente_datos,
                version_licencia, carga_datos, precio_cierre, tasa_referencia
    TO app_077;

-- RF-01 (alta), RF-12 y RD-23 (bloqueo al revocar), RNF-04 y P-06 (rehash).
GRANT INSERT (correo, contrasena_hash, estado) ON usuario TO app_077;
GRANT UPDATE (estado, contrasena_hash) ON usuario TO app_077;

-- RF-12 y RD-11: se registran sin momento, que fija la base, y no se modifican.
GRANT INSERT (usuario_id, version_aviso_id, tipo, medio) ON consentimiento TO app_077;

-- RF-03: crear, renombrar y eliminar (RD-10). UPDATE (nombre) permite además
-- SELECT … FOR UPDATE del portafolio (RF-28).
GRANT INSERT (usuario_id, nombre, divisa_base) ON portafolio TO app_077;
GRANT UPDATE (nombre) ON portafolio TO app_077;
GRANT DELETE ON portafolio TO app_077;

-- RF-25 y RD-09: se registran y no se modifican ni se eliminan.
GRANT INSERT (usuario_id, nombre) ON intermediario TO app_077;

-- RF-05, RD-07 y RD-09: se registran sin momento y no se modifican ni se eliminan.
GRANT INSERT (usuario_id, portafolio_id, intermediario_id, instrumento_id, tipo,
              fecha_concertacion, cantidad, precio, importe_comisiones)
    ON transaccion TO app_077;

COMMIT;
