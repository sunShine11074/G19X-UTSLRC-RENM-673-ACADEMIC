# Proyecto 077 — Plataforma Inteligente de Gestión de Activos Financieros

Estadías profesionales · Universidad Tecnológica × PluriOne S.A. de C.V. (Develop Talent & Technology)
Autor: Ramón Ernesto Nieblas Mendívil

Plataforma web dirigida a inversionistas individuales que consolida instrumentos, posiciones y
transacciones de un portafolio y calcula sobre ellos métricas de rendimiento y riesgo mediante un
motor único de cálculo. **No emite recomendaciones de inversión.**

---

## Índice del paquete

| Documento | Estado | Ubicación | Entregable de empresa que alimenta |
|---|---|---|---|
| Definición del proyecto | ✅ v1 | [docs/](docs/) | Documento de requerimientos |
| Glosario del dominio financiero | 🔶 hecho, por integrar | `docs/glosario.md` | Manual técnico |
| SRS — Especificación de Requisitos | 🔄 esqueleto creado | [docs/](docs/) | Documento de requerimientos |
| Modelo E-R y diccionario de datos | ⏳ | SRS §4.3 y §4.4 | Documento de arquitectura |
| Wireframes y guía de estilo | ⏳ | SRS §4.5 | Documento de arquitectura |
| Registros de decisión (ADR) | ⏳ | `docs/adr/` | Documento de arquitectura |
| Matriz de riesgos | ⏳ | `docs/riesgos.md` | Plan del proyecto |
| Cronograma | ⏳ | `docs/cronograma.md` | Plan del proyecto |
| Conjunto de referencia (oráculo) | ⏳ | `backend/tests/fixtures/` | Reporte de QA |
| Consideraciones legales | ⏳ | `docs/legal.md` | Informe final |

---

## Fechas clave

| Fecha | Hito |
|---|---|
| Lunes 21 de septiembre | Revisión de planeación con la asesora académica |
| Lunes 28 de septiembre | Revisión de avance |
| **Lunes 5 de octubre** | **Entrega del MVP** |
| 5 de octubre – 20 de noviembre | Fase de refinamiento y pruebas de calidad |

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.13 · FastAPI · SQLAlchemy 2.x · Alembic (gestionado con `uv`) |
| Base de datos | PostgreSQL 18 |
| Frontend | React 19 · Vite · Apache ECharts |
| Cálculo financiero | NumPy · Pandas |

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

## Avisos

- Los datos utilizados durante el desarrollo son **sintéticos** y están marcados como tales en la
  interfaz. No corresponden a información real de mercado ni de clientes.
- La plataforma presenta información y análisis; **no constituye asesoría de inversión**.
- Este repositorio es privado y no contiene documentación confidencial del cliente.
