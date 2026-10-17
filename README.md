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
| Glosario del dominio financiero | ✅ hecho | Documento aparte, enlazado en SRS §1.3 | Manual técnico |
| SRS — Especificación de Requisitos | 🔄 v0.3: §1 a §4.4 y §5.2; pendientes §4.5 y §5.3 | [docs/](docs/) | Documento de requerimientos |
| Modelo E-R y diccionario de datos | ✅ en el SRS e implementado en `backend/02_crear_esquema.sql` | SRS §4.3 y §4.4 | Documento de arquitectura |
| Wireframes y guía de estilo | ⏳ | SRS §4.5 | Documento de arquitectura |
| Registros de decisión (ADR) | ⏳ | `docs/adr/` | Documento de arquitectura |
| Matriz de riesgos | ⏳ | `docs/riesgos.md` | Plan del proyecto |
| Cronograma | ⏳ | `docs/cronograma.md` | Plan del proyecto |
| Conjunto de referencia (oráculo) | ✅ congelado (commit 11097f8) | [backend/tests/oraculo/](backend/tests/oraculo/) · SRS §5.2 | Reporte de QA |
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
| Base de datos | PostgreSQL 18; esquema y semillas con scripts de `psql` (ver «Base de datos local») |
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

## Base de datos local

Los scripts de `backend/` se ejecutan en orden con `psql`, como el superusuario `postgres`.
Ninguno contiene contraseñas.

1. `01_crear_base.sql`, conectado a la base `postgres`: crea la base `proyecto077` y el rol
   `app_077`. Después se fija la contraseña de `app_077` con `\password app_077` y se anota
   solo en `backend/.env`.
2. `02_crear_esquema.sql`, conectado a `proyecto077`: crea las 13 tablas del SRS (4.3 y 4.4),
   elimina la tabla de prueba `ping`, fija la zona `America/Mexico_City` y deja a `app_077`
   solo con los privilegios del 4.3. Corre en una sola transacción y una sola vez; antes
   comprueba que la configuración regional de la base pase a minúsculas las letras acentuadas
   (RD-03).
3. `03_probar_esquema.sql`, conectado a `proyecto077` y con las tablas vacías: prueba cada
   restricción y cada privilegio dentro de una transacción que se deshace.
4. `04_cargar_semillas.sql`, conectado a `proyecto077`: carga el aviso de privacidad de
   demostración, las fuentes y sus licencias, el catálogo, los precios sintéticos y las tasas
   reales de CETES del Banco de México. Volver a ejecutarlo no duplica nada; si lo que ya hay en
   la base no coincide con las semillas, se detiene y no cambia nada. Lo genera
   `backend/semillas/genera_semillas.py` a partir de las entradas del conjunto de referencia
   (`backend/tests/oraculo/entradas`); si cambian, se regenera con
   `python backend/semillas/genera_semillas.py`. Si cambias el texto del aviso
   (`backend/semillas/aviso_privacidad_demo.md`), cambia también `AVISO_VIGENTE_DESDE` en el
   generador: cada texto es una versión nueva (RF-12).

```
psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/02_crear_esquema.sql
psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/03_probar_esquema.sql
psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/04_cargar_semillas.sql
```

Las marcas `⟦decidir⟧` de `02_crear_esquema.sql` señalan las decisiones del SRS que siguen
abiertas y dicen qué cambiar en cada caso.

---

## Avisos

- Los precios utilizados durante el desarrollo son **sintéticos** y están marcados en la interfaz
  como datos de demostración. Las tasas de CETES son reales y provienen del Banco de México
  (Fuente: Banco de México, https://www.banxico.org.mx). No se usa información real de clientes.
- La plataforma presenta información y análisis; **no constituye asesoría de inversión**.
- Este repositorio es privado y no contiene documentación confidencial del cliente.
