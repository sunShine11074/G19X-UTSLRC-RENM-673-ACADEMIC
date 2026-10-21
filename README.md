# Proyecto 077 — Plataforma Inteligente de Gestión de Activos Financieros

Estadías profesionales · Universidad Tecnológica × PluriOne S.A. de C.V. (Develop Talent & Technology)
Autor: Ramon Ernesto Nieblas Mendivil

Plataforma web dirigida a inversionistas individuales que consolida instrumentos, posiciones y
transacciones de un portafolio y calcula sobre ellos métricas de rendimiento y riesgo mediante un
motor único de cálculo. **No emite recomendaciones de inversión.**

---

## Índice del paquete

| Documento | Estado | Ubicación | Entregable de empresa que alimenta |
|---|---|---|---|
| Definición del proyecto | ✅ v1 | [docs/](docs/) | Documento de requerimientos |
| MVP ([`MVP.md`](docs/MVP.md)) y documento de requisitos del producto ([`PRD.md`](docs/PRD.md)) | ✅ v1.1 del 18 oct: dan el MVP por completo y verificado (la v1.0, que entró en el commit 358fdae, se escribió antes de terminar el cliente web). El PRD se sigue trabajando durante la estadía | [docs/](docs/) | Revisión del líder de proyecto (AC-06) |
| API, motor de cálculo y cliente web del MVP | ✅ hechos: API y motor (commit faf6b32) y cliente web con las pantallas V-01 a V-12 del SRS §4.5.2 (commit e636b78). Algunos detalles de presentación y accesibilidad (por ejemplo, el menú desplegable bajo 1280 px y los detalles del modo oscuro), que no quitan criterios de §3.2 ni RNF que se juzgan el 18 oct, quedan para la fase de refinamiento | [backend/](backend/) y [frontend/](frontend/) | Revisión del líder de proyecto (AC-01 a AC-04) |
| Glosario del dominio financiero | ✅ hecho | Documento aparte, enlazado en SRS §1.3 | Manual técnico |
| SRS — Especificación de Requisitos | 🔄 v0.3: §1 a §4.4, §4.5.1, §4.5.2, §5.1 y §5.2; pendientes §1.1, §4.5.3, §4.5.4, la matriz de §5.3 (solo tiene la fila de RF-01) y, en §3.1, la revisión del Diario Oficial de la Federación (AC-08) | [docs/](docs/) | Documento de requerimientos |
| Modelo E-R y diccionario de datos | ✅ en el SRS e implementado en `backend/02_crear_esquema.sql` | SRS §4.3 y §4.4 | Documento de arquitectura |
| Guía de estilo y mapa de navegación | ✅ hechos (18 oct) | SRS §4.5.1 y §4.5.2 | Documento de arquitectura |
| Wireframes y mockups | ⏳ | SRS §4.5.3 y §4.5.4 | Documento de arquitectura |
| Registros de decisión (ADR) | ⏳ | `docs/adr/` | Documento de arquitectura |
| Matriz de riesgos | ⏳ | `docs/riesgos.md` | Plan del proyecto |
| Cronograma | ⏳ | `docs/cronograma.md` | Plan del proyecto |
| Conjunto de referencia (oráculo) | ✅ congelado (commit 11097f8); su README conserva las notas previas al congelamiento, y la confirmación de la tasa a 28 días del 10/09/2026 sigue pendiente (SRS 3.1) | [backend/tests/oraculo/](backend/tests/oraculo/) y su [README](backend/tests/oraculo/README.md) · SRS §5.2 | Reporte de QA |
| Registro de resultados y recorrido de AC-04 | ✅ hechos el 18 oct: 271 pruebas aprobadas sobre el commit e636b78, inspección de AC-03 (3 de 3), CPNF-05 cumple (código de salida 0) y recorrido de AC-04 con 54 filas correctas, 0 fallas y 33 capturas. Pendiente la comprobación a mano de tres cifras de §5.2 | [backend/tests/resultados/2026-10-18/](backend/tests/resultados/2026-10-18/) y su [índice](backend/tests/resultados/2026-10-18/INDICE.md) | Reporte de QA |
| Consideraciones legales | ⏳ | `docs/legal.md` | Informe final |

---

## Fechas clave

| Fecha | Hito |
|---|---|
| Lunes 21 de septiembre | Revisión de planeación con la asesora académica |
| Lunes 28 de septiembre | Revisión de avance |
| **Domingo 18 de octubre** | **Entrega del MVP (fecha final, inclusive)** |
| 19 de octubre – 20 de noviembre | Fase de refinamiento y pruebas de calidad |

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.13 · FastAPI · SQLAlchemy 2 · psycopg 3 (gestionado con `uv`) |
| Base de datos | PostgreSQL 18; esquema y semillas con scripts de `psql` (ver «Cómo ejecutarlo localmente») |
| Frontend | React 19 · Vite 8 · Recharts 3 (se construye con Node.js 24) |
| Cálculo financiero | `decimal` de Python con 28 dígitos; nunca punto flotante binario (RD-12) |

Principio de arquitectura: **una sola fuente de cálculo.** Los indicadores se calculan en el backend
y se exponen como JSON; ningún cliente recalcula.

---

## Estructura del repositorio

```
docs/        Documentación del proyecto
backend/     API y motor de cálculo
frontend/    Aplicación web
```

---

## Cómo ejecutarlo localmente

Esta sección explica cómo instalar el MVP en un equipo propio, crear la base, cargar las
semillas, arrancar la API y el cliente web, cargar el escenario de demostración y ejecutar las
pruebas (AC-05 del SRS 3.9.2). Los comandos son para Windows con PowerShell, el entorno del
equipo de desarrollo (SRS 3.6.3), y las rutas son relativas a la raíz del repositorio. Ningún
paso usa valores reales: las contraseñas se escriben solo en `backend/.env`, que git ignora, o
en una petición que no las muestra.

### 1. Requisitos

Versiones que pide el SRS 3.5:

| Pieza | Versión | Para qué |
|---|---|---|
| Python | 3.13, con su última corrección | La API. `backend/.python-version` fija la 3.13; si no está instalada, `uv python install 3.13`. |
| uv | Sin versión fija en 3.5 | Crea el entorno del backend con las versiones exactas de `backend/uv.lock`. |
| PostgreSQL | 18, con su última corrección, con `psql`, `initdb` y `pg_ctl` | La base de datos y el clúster temporal de las pruebas. |
| Node.js | 24, con su última corrección, con npm | Instalar, servir y compilar el cliente. |
| Navegador | Una versión vigente de un navegador basado en Chromium o de Firefox | Usar el cliente. El guion del recorrido de AC-04 usa Microsoft Edge. |
| Git | — | Clonar el repositorio. |

El MVP se probó el 18 de octubre de 2026 con uv 0.12.13, Python 3.13.5, Node.js 24.12.0
(npm 11.6.2) y PostgreSQL 18.6. El paso a la última corrección de cada uno queda para la fase
de refinamiento (SRS 3.1 y 3.6.3).

Si `psql` no está en el PATH, agrega `C:\Program Files\PostgreSQL\18\bin` o escribe la ruta
completa.

El repositorio es público, así que se clona sin pedir acceso ni iniciar sesión en GitHub. El
último argumento solo da nombre a la carpeta local:

```powershell
git clone https://github.com/sunShine11074/G19X-UTSLRC-RENM-673-ACADEMIC.git Proyecto-077
cd Proyecto-077
```

### 2. Base de datos

Los scripts de `backend/` se ejecutan en orden con `psql`, como el superusuario `postgres`
(`psql` pide su contraseña). Ninguno contiene contraseñas.

1. Crea la base `proyecto077` y el rol `app_077`, conectado a la base `postgres`:

   ```powershell
   psql -U postgres -d postgres -f backend/01_crear_base.sql
   ```

2. Fija la contraseña de `app_077`: abre `psql -U postgres -d postgres`, escribe
   `\password app_077`, teclea la contraseña dos veces (no se muestra) y sal con `\q`. La eliges
   tú y la anotas solo en `backend/.env` (paso 4).

3. Crea el esquema, pruébalo y carga las semillas, conectado a `proyecto077`:

   ```powershell
   psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/02_crear_esquema.sql
   psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/03_probar_esquema.sql
   psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/04_cargar_semillas.sql
   ```

   - `02_crear_esquema.sql` crea las 13 tablas del SRS (4.3 y 4.4), elimina la tabla de prueba
     `ping`, fija la zona `America/Mexico_City` y deja a `app_077` solo con los privilegios del
     4.3. Corre en una sola transacción y una sola vez. Antes comprueba que la configuración
     regional de la base pase a minúsculas las letras acentuadas (RD-03); si no, se detiene y su
     mensaje dice cómo crear la base con otra.
   - `03_probar_esquema.sql`, con las tablas vacías, prueba cada restricción y cada privilegio
     dentro de una transacción que se deshace.
   - `04_cargar_semillas.sql` carga el aviso de privacidad de demostración, las fuentes y sus
     licencias, el catálogo, los 71 precios sintéticos y las 32 tasas reales de CETES del Banco
     de México. Volver a ejecutarlo no duplica nada; si lo que ya hay en la base no coincide con
     las semillas, se detiene y no cambia nada.

Si `proyecto077` ya existía con un esquema anterior al 15 de octubre de 2026 (commit d4b445f)
y no tiene datos que conservar, bórrala desde `psql -U postgres -d postgres` con
`DROP DATABASE proyecto077;` y repite los pasos 1 y 3. El aviso de que `app_077` ya existe es
esperado, y su contraseña no cambia.

El 04 lo genera `backend/semillas/genera_semillas.py` a partir de las entradas del conjunto de
referencia (`backend/tests/oraculo/entradas`); si cambian, se regenera con
`python backend/semillas/genera_semillas.py`. Si cambias el texto del aviso
(`backend/semillas/aviso_privacidad_demo.md`), cambia también `AVISO_VIGENTE_DESDE` en el
generador: cada texto es una versión nueva (RF-12). Las marcas `⟦decidir⟧` de
`02_crear_esquema.sql` señalan las decisiones del SRS que siguen abiertas y dicen qué cambiar en
cada caso.

### 3. Dependencias

```powershell
cd backend
uv sync
cd ..\frontend
npm ci
cd ..
```

- `uv sync` crea `backend/.venv` con las versiones de `backend/uv.lock`, pytest incluido.
- `npm ci` instala exactamente lo de `frontend/package-lock.json` (React 19.3.0, Recharts
  3.10.1 y Vite 8). No uses `npm install`, que puede cambiar el lockfile.

### 4. Configuración de la API (`backend/.env`)

La API lee su configuración de `backend/.env`. Créalo a partir del ejemplo y llénalo con tus
propios valores:

```powershell
cd backend
Copy-Item .env.example .env
notepad .env
```

| Variable | Qué poner | Regla |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://app_077:CONTRASENA@localhost:5432/proyecto077`, con la contraseña del paso 2 en lugar de `CONTRASENA` | Obligatoria. Siempre con `app_077`: la API no arranca con un rol superusuario. Si la contraseña tiene `@`, `:`, `/` o `%`, escríbelos codificados para URL (por ejemplo, `@` como `%40`). |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes exactos, separados por coma y sin barra final. Agrega `http://localhost:8000` solo si vas a escribir desde `/docs`. |
| `SESION_CLAVE` | Una clave aleatoria nueva | Obligatoria y de 32 caracteres o más; sin ella la API no arranca. Genérala en `backend/` con `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"` y pégala solo aquí. Cambiarla cierra todas las sesiones. |
| `SESION_DURACION_MINUTOS` | `480` | De 5 a 1440; la sesión caduca y no se renueva. |
| `SESION_COOKIE_SEGURA` | `false` | `true` solo si la API se sirve con HTTPS. |
| `BANXICO_TOKEN` | Nada: `BANXICO_TOKEN=` | El MVP no la usa; las tasas de CETES vienen en las semillas. Si conservas el texto del ejemplo, la inspección CPNF-05 (paso 7) lo encuentra en `.env.example` y falla. |

Guarda `.env` en UTF-8, que es lo que hacen `Copy-Item` y el Bloc de notas. No lo reescribas
con `Set-Content` de PowerShell 5.1: lo guarda en ANSI y, como el archivo tiene acentos, la API
no arranca y lo dice con un mensaje. `backend/.env` nunca se versiona (`.gitignore`).

### 5. Arrancar la API y el cliente

Usa dos ventanas de PowerShell.

**API**, en `backend/`:

```powershell
uv run fastapi dev app/main.py
```

Escucha en `http://127.0.0.1:8000`. Para comprobarla, abre `http://127.0.0.1:8000/health`, que
responde `{"estado":"ok"}` sin tocar la base. La documentación interactiva queda en
`http://localhost:8000/docs`.

**Cliente web**, en `frontend/`:

```powershell
npm run dev
```

Abre **`http://localhost:5173`**, no `http://127.0.0.1:5173`.

- **Proxy.** El cliente hace todas sus peticiones a `/api` en su propio origen, y Vite las
  reenvía a la API en `http://127.0.0.1:8000` (`frontend/vite.config.js`). El proxy no usa
  `changeOrigin`, así que el encabezado `Origin` del navegador llega intacto a la API.
- **Puerto fijo (`strictPort`).** Si el 5173 está ocupado, Vite se detiene con un error en
  lugar de pasar a otro puerto, que quedaría fuera de `CORS_ORIGINS`. Cierra el proceso que lo
  ocupa y vuelve a correr `npm run dev`.
- **Por qué `localhost` y no `127.0.0.1`.** La API rechaza con 403 «Origen no permitido» toda
  escritura, el inicio de sesión incluido, cuyo `Origin` no sea exactamente uno de
  `CORS_ORIGINS` (`http://localhost:5173`). Para el navegador, `http://127.0.0.1:5173` es otro
  origen, así que desde ahí ni siquiera se puede iniciar sesión. Además, la cookie de sesión es
  de cada host: una sesión abierta en `localhost` no existe en `127.0.0.1`.
- **Modo `temporal`.** `npm run dev -- --mode temporal` sirve en `http://127.0.0.1:5174`
  contra una API en `127.0.0.1:8001`. Es para el entorno desechable del equipo de desarrollo:
  el repositorio no incluye cómo levantar esa API, y las configuraciones de arranque del editor
  (`.claude/launch.json`) no se versionan. No hace falta para usar el MVP; basta con los dos
  comandos de arriba.

### 6. Cargar el escenario de demostración (SRS 5.2)

Con la API en marcha, en `backend/` y desde una ventana de PowerShell (el cargador pide la
contraseña con `getpass`, que necesita una consola interactiva):

```powershell
uv run python -m tests.referencia.cargador --url http://localhost:8000 --origen http://localhost:5173
```

- Registra la cuenta ficticia `oraculo@example.com` (otra, con `--correo`) y pide para ella una
  contraseña nueva de 15 caracteres o más, sin mostrarla. La API exige de 15 a 128 caracteres y
  que no sea el correo (RF-01).
- Luego inicia sesión y registra por la API, como lo haría un usuario, los dos portafolios
  («Principal» y «Secundario»), los dos intermediarios («Casa A» y «Casa B») y las
  transacciones T01 a T16. Al terminar solo imprime conteos.
- `--url` es la API (por omisión, `http://localhost:8000`) y `--origen` debe ser uno de
  `CORS_ORIGINS` (por omisión, `http://localhost:5173`).
- Si la API rechaza un paso, la carga se detiene con código de salida 1 y el mensaje dice qué
  paso falló, el estado que respondió la API y su motivo; por ejemplo, «La contraseña debe tener
  al menos 15 caracteres». Nunca muestra la contraseña.
- Si la cuenta ya existe, el registro responde 409 y la carga se detiene. Se corre una sola vez
  por base, o con otro `--correo`.

**Comprobación rápida.** Inicia sesión en `http://localhost:5173` con esa cuenta. En el tablero
de «Principal», con el periodo por omisión (del 11/09/2026 al 14/10/2026), deben aparecer el
rendimiento ponderado por tiempo de 4.39 %, la máxima caída de -6.68 % (del pico del 16/09/2026
al valle del 23/09/2026), el valor de mercado de $58,940.88 y el resultado no realizado de
$2,632.99. En Posiciones al 14/10/2026, el total del valor es el mismo, $58,940.88, y el costo,
$56,307.89. La misma comprobación por la API, sin el cliente, está en `docs/MVP.md`, sección
11.6.

### 7. Pruebas

**Backend**, en `backend/`. Las pruebas no leen `backend/.env` ni tocan la base de desarrollo:
cada corrida levanta su propio clúster temporal de PostgreSQL 18 en `127.0.0.1`, con
contraseñas aleatorias, ejecuta 02, 03 y 04, y al terminar lo detiene y lo borra. Necesitan los
binarios de PostgreSQL 18 (`initdb`, `pg_ctl` y `psql`) en el PATH, en la variable
`P077_PG_BIN` o en `C:/Program Files/PostgreSQL/18/bin`. Son opcionales `P077_PG_PUERTO`
(puerto del clúster temporal; si no, uno libre) y `P077_PG_LOCALE` (por omisión, `es-MX`).

| Qué | Comando | Notas |
|---|---|---|
| Suite completa | `uv run --frozen pytest -q` | 271 pruebas; en el equipo de desarrollo, de menos de un minuto (53 s el 18/10/2026) a 7 minutos, según su carga. Las 3 de inspección quedan fuera por omisión. |
| Solo el motor de cálculo | `uv run --frozen pytest -m motor` | 143 pruebas, sin base de datos, en segundos. |
| Por marca | `uv run --frozen pytest -m api` | Marcas: `motor` (sin base), `bd` (con el clúster temporal), `api`, `referencia` (CPNF-01 y CPNF-02) y `no_funcional` (CPNF-03 y CPNF-04). `inspeccion` queda excluida salvo que se pida. |
| Un requisito por la API | `uv run --frozen pytest tests/api/test_cpf28_saldo.py` | Cada CPF de la API tiene su archivo `test_cpfNN_*.py` en `tests/api` o, para RF-01 y RF-12, en `tests/cuentas`. |
| Un requisito en el motor | `uv run --frozen pytest tests/motor/test_criterios_3_2.py -k rf08` | Con `rf05`, `rf06`, `rf09`, `rf10`, `rf26a`, `rf26b` o `rf28` en lugar de `rf08`. |
| Con evidencia guardada | `uv run --frozen pytest --registro-resultados --junitxml=tests/resultados/AAAA-MM-DD/junit.xml` | Guarda la evidencia en `backend/tests/resultados/AAAA-MM-DD/`, con la fecha de la Ciudad de México. La entrega del 18/10/2026 tiene la suya en `backend/tests/resultados/2026-10-18/`. |
| Inspección de AC-03 | `uv run --frozen pytest -m inspeccion tests/inspeccion/test_ac03.py` | 3 pruebas. |
| Inspección de RNF-05 (CPNF-05) | Ver abajo | Solo la corre quien tiene `backend/.env`, porque lo lee. |

CPNF-05 busca la contraseña de `DATABASE_URL`, `SESION_CLAVE` y `BANXICO_TOKEN` en todo el
historial de git, en el árbol de trabajo, en `frontend/dist` y en los registros, y comprueba
que git ignore `backend/.env`. Solo imprime conteos y termina con 0 si cumple y con 1 si no.
Antes conviene compilar el cliente (`npm run build`) para que revise un `dist` que exista. La
primera línea hace que PowerShell 5.1 escriba bien los acentos:

```powershell
$env:PYTHONIOENCODING='utf-8'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new()
uv run python tests/inspeccion/cpnf05_credenciales.py
```

La del 18/10/2026 terminó con 0, sin coincidencias; su salida está en
`backend/tests/resultados/2026-10-18/cpnf05.txt`.

**Cliente**, en `frontend/`:

```powershell
npm run lint
npm run build
node --test src/formato/formato.test.js
```

`npm run lint` corre oxlint con `.oxlintrc.json`; `npm run build` deja el cliente compilado en
`frontend/dist`, que no se versiona, y `node --test` prueba el módulo que da formato a cifras y
fechas sin convertirlas a número.

### 8. Recorrido de AC-04 con capturas

El guion `backend/tests/resultados/2026-10-18/recorrido_ac04.mjs` recorre las pantallas con los
datos de 5.2 y toma al menos una captura fechada por requisito imprescindible (AC-04). Necesita
Node.js 24 (no tiene dependencias), Microsoft Edge, la API y el cliente en marcha (paso 5) y el
escenario cargado (paso 6). Se ejecuta desde la raíz del repositorio:

```powershell
node backend/tests/resultados/2026-10-18/recorrido_ac04.mjs --base http://localhost:5173 --correo oraculo@example.com --salida backend/tests/resultados/2026-10-18/ac04
```

- Pide la contraseña de la cuenta sin mostrarla y abre Edge sin interfaz, con un perfil
  temporal que borra al terminar, y lo controla por el protocolo de DevTools.
- Encuentra cada pantalla y cada control por su atributo `data-recorrido`, espera a que lleguen
  los datos y captura a 1280×720.
- Deja en `--salida` los PNG (por ejemplo, `RF-11_V-04_2026-10-18_2108.png`) y
  `recorrido.csv`, con el requisito, la pantalla, el archivo, la hora, el resultado y un
  detalle, sin contraseñas ni rutas de usuario. Si `recorrido.csv` ya existe, le agrega filas.
- Si un paso falla, lo anota como «falló», guarda una captura de diagnóstico
  (`fallo-paso-NN_*.png`) y sigue con el siguiente. Si no logra iniciar sesión, anota una fila
  `inicio` con su captura `fallo-inicio_*.png` y no corre ningún paso. Las capturas de
  diagnóstico no son evidencia.
- Captura el tablero y las posiciones antes de escribir nada. Después sí escribe en la base:
  crea, renombra y elimina el portafolio «Recorrido AC-04 (desechable)», con una compra, y crea
  una cuenta ficticia `recorrido-b-<hhmm>@example.com`, con una clave aleatoria que solo vive en
  memoria, que termina con su consentimiento revocado. No cambia «Principal» ni «Secundario».
- Termina con código 0 si todo salió bien, 1 si algún paso falló y 2 si las opciones no son
  válidas.

Opciones (`--ayuda` imprime el encabezado del guion, que las explica):

| Opción | Por omisión | Para qué |
|---|---|---|
| `--base URL` | `http://localhost:5173` | El cliente web, sin ruta ni barra final. |
| `--correo CORREO` | `oraculo@example.com` | La cuenta con 5.2 cargado (paso 6). |
| `--salida CARPETA` | La carpeta `ac04` junto al guion | Dónde quedan las capturas y `recorrido.csv`. |
| `--pasos 1,2,10` | Todos (del 1 al 10) | Repetir solo los pasos que fallaron; sus filas se agregan a `recorrido.csv`. |
| `--edge RUTA` | Su lugar habitual en Windows | `msedge.exe`, si está en otro lugar. |
| `--puerto N` | `9223` | Puerto de DevTools, de 1025 a 65535; debe estar libre. |
| `--clave-archivo RUTA` | — | Solo para ensayar contra un entorno desechable: lee la contraseña de ese archivo. Con una cuenta propia no se usa. |

El recorrido del 18/10/2026, contra la base de desarrollo con 5.2 cargado, terminó a las
21:09:10 con 54 filas correctas, 0 fallas y 33 capturas. Las dos primeras filas de su
`recorrido.csv` (20:14 y 21:07) son intentos de inicio de sesión fallidos, cada uno con su
captura de diagnóstico; el recorrido completo de las 21:08 los supera.

### 9. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| La API no arranca: «backend/.env no está guardado en UTF-8» | Se reescribió con `Set-Content` de PowerShell 5.1. Vuelve a crearlo con `Copy-Item` y edítalo con el Bloc de notas (paso 4). |
| La API no arranca por `SESION_CLAVE` | Falta o tiene menos de 32 caracteres. Genérala como dice el paso 4. |
| La API no arranca: «DATABASE_URL usa un rol superusuario» | `DATABASE_URL` debe usar `app_077`, nunca `postgres`. |
| 403 «Origen no permitido» al iniciar sesión o al guardar | El cliente se abrió en otro host o puerto. Abre `http://localhost:5173` y revisa que `CORS_ORIGINS` lo tenga, exacto y sin barra final. |
| Vite se detiene porque el puerto 5173 está ocupado | Es `strictPort`. Cierra el otro proceso (por ejemplo, otro `npm run dev`) y vuelve a intentarlo. |
| El cliente dice «No se pudo conectar con el servidor» | La API no está en marcha en `127.0.0.1:8000`, así que el proxy no tiene a dónde reenviar. |
| 403 al escribir desde `/docs` | Agrega `http://localhost:8000` a `CORS_ORIGINS` y vuelve a arrancar la API. |
| El cargador responde 409 | La cuenta ya existe en esa base: inicia sesión con ella o usa otro `--correo`. |
| `02` se detiene por la configuración regional | Su mensaje dice cómo crear la base con otra. |
| pytest no encuentra PostgreSQL | Define `P077_PG_BIN` con la carpeta `bin` de PostgreSQL 18. |
| CPNF-05 termina con 1 | Si no hay credenciales en el repositorio, revisa que `BANXICO_TOKEN` no conserve el texto del ejemplo (paso 4). |

---

## Avisos

- Los precios utilizados durante el desarrollo son **sintéticos** y están marcados en la interfaz
  como datos de demostración. Las tasas de CETES son reales y provienen del Banco de México
  (Fuente: Banco de México, https://www.banxico.org.mx). No se usa información real de clientes.
- La plataforma presenta información y análisis; **no constituye asesoría de inversión**.
- Este repositorio es **público**: cualquiera puede leerlo y clonarlo sin pedir acceso. Todo lo
  que entra en un commit queda publicado, con su historial, aunque un commit posterior lo borre;
  antes de cada commit conviene revisar con `git status` qué se va a incluir.
- No contiene documentación confidencial del cliente ni credenciales. Las credenciales viven
  solo en `backend/.env`, que git ignora, y la inspección CPNF-05 del 18/10/2026 no encontró
  ninguna en el historial de git, el índice, el árbol de trabajo, `frontend/dist` ni los
  registros (`backend/tests/resultados/2026-10-18/cpnf05.txt`).
