# PRD del Proyecto 077

Plataforma Inteligente de Gestión de Activos Financieros: documento de requisitos del producto (PRD), desde el MVP del 18 de octubre de 2026 hasta lo posterior a la estadía.

| Dato | Valor |
|---|---|
| Proyecto | 077 — Plataforma Inteligente de Gestión de Activos Financieros |
| Documento | `docs/PRD.md`: requisitos del producto en su conjunto, por fases, con la forma de verificar cada uno |
| Versión del documento | 1.0 |
| Fecha | Domingo 18 de octubre de 2026 |
| Autor | Ramon Ernesto Nieblas Mendivil, estudiante en estadía del TSU en Desarrollo de Software Multiplataforma (Universidad Tecnológica de San Luis Río Colorado). Analista y arquitecto, desarrollador del servidor y del cliente, y responsable de pruebas del proyecto (SRS 3.7). |
| Empresa | PluriOne S.A. de C.V. (Develop Talent & Technology) |
| Líder de proyecto | Edgar Loeffelmann Ibarra: revisión del MVP y aprobación del entregable (SRS 1.2) |
| Especificación de referencia | SRS versión 0.3 (en elaboración), tal como está en el commit `268a2c2` |
| Estado del producto al 18/10/2026 | MVP: servidor completo (API, motor de cálculo, base de datos y datos semilla), verificado con 271 pruebas automatizadas; la interfaz web está pendiente (MVP.md, sección 12). Fase de refinamiento: empieza el lunes 19 de octubre de 2026; ninguno de sus 17 requisitos está implementado. |

## Propósito y uso de este documento

Este archivo es el documento de requisitos del producto (PRD) del Proyecto 077. Describe el producto completo: qué problema atiende, para quién, qué hace en cada fase, con qué calidad y qué datos, y cómo se acepta. El líder de proyecto pidió que la carpeta `docs/` contenga dos archivos Markdown, uno del MVP y otro del PRD (SRS 2.5.1, S-01, y 3.9.2, AC-06), y el 18 de octubre de 2026 fijó sus nombres: `MVP.md` y `PRD.md` (este archivo). Solo queda por confirmar con él si `docs/` debe tener exactamente esos dos (sección 14.3). Su plataforma los usará, entre otras cosas, como criterios para evaluar la aplicación.

Relación con los demás documentos:

- `docs/MVP.md` detalla el MVP, la entrega del 18 de octubre de 2026: criterios de aceptación numerados, fórmulas, datos, API, instalación y estado. Este documento no lo repite: para cada requisito del MVP da lo esencial y remite a su sección (por ejemplo, «MVP.md 3.7»).
- `docs/2 (SRS) Especificación de Requisitos de Software.md` (en adelante, el SRS) es la especificación completa. Este documento la resume sin cambiarla y remite a ella por apartado e identificador; por ejemplo, «SRS 2.6.1, RF-19» es el requisito RF-19 del apartado 2.6.1. Si algo de aquí difiere del SRS, prevalece el SRS.
- `docs/1 Definición del proyecto.md` (en adelante, la Definición) fija el problema, el objetivo general, los objetivos específicos OE-1 a OE-5 y la clasificación MoSCoW de todos los requisitos.

Cómo usarlo para evaluar la aplicación y su evolución:

1. La sección 5 dice qué entra en cada fase del producto y con qué reglas se recorta si falta capacidad.
2. La sección 6 es el catálogo de los 35 requisitos funcionales. Cada uno tiene identificador, enunciado, prioridad, fase o fecha objetivo, objetivo específico, dependencias, criterio o método de verificación y estado al 18/10/2026. Los criterios numerados de los 18 del MVP están en MVP.md, sección 3.
3. La sección 7 da los 12 requisitos no funcionales, con su métrica, su valor objetivo, su prueba y su fecha de verificación; la 8, los requisitos de datos, y la 9, los de experiencia de usuario.
4. La sección 13 da la hoja de ruta semana a semana, y la 14, los criterios de aceptación de cada entrega (AC-01 a AC-13) con la evidencia que pide cada uno. Para evaluar la evolución, cada requisito se compara con su fecha objetivo y, al cierre de la estadía, con AC-10.
5. La sección 15 lista los riesgos y lo que sigue abierto. Lo abierto se presenta como abierto: su valor final se fijará en el SRS y se registrará en su apartado 3.1.

### Convenciones

| Identificador | Qué es | Dónde se define |
|---|---|---|
| RF-nn | Requisito funcional: algo que el sistema hace | SRS 3.2 (MVP) y 2.6 (fases posteriores) |
| RNF-nn | Requisito no funcional: una cualidad medible | SRS 3.3 |
| RD-nn | Regla de los datos: integridad, precisión, procedencia o conservación | SRS 3.4 |
| CPF-nn y CPNF-nn | Caso de prueba funcional y no funcional; lleva el número de su requisito | SRS 3.2 y 3.3; Definición |
| AC-nn | Criterio de aceptación de una entrega | SRS 3.9 |
| CU-nn | Caso de uso: CU-01 a CU-12 del MVP; CU-13 a CU-21 de la fase de refinamiento | SRS 4.1 |
| V-nn | Pantalla del cliente web | SRS 4.5.2 |
| Enn | Operación de la API | SRS 4.5.2; MVP.md 7.4 |
| R-nn, X-nn, S-nn y D-nn | Restricción, exclusión de alcance, suposición y dependencia | SRS 2.4, 2.4.7 y 2.5 |
| OE-n | Objetivo específico | Definición |
| SRS 5.2 | Conjunto de datos de referencia (el «oráculo»); MVP.md lo resume en su sección 5.8 | SRS 5.2 y `backend/tests/oraculo/` |

Prioridad, según la clasificación MoSCoW de la Definición:

- M, imprescindible: obligatorio para el MVP del 18 de octubre.
- S, debería incluirse, y C, opcional: requisitos de la fase de refinamiento con categoría MoSCoW.
- Diferido: requisito con fecha en la fase de refinamiento al que la Definición no da categoría MoSCoW.
- W, no se incluirá: las exclusiones, que nunca entran (sección 12).

Estado de una decisión. El SRS señala lo abierto con las marcas ⟦decidir⟧ y ⟦confirmar⟧; este documento no las usa y lo rotula así:

- Decidido: lo fija el SRS o la Definición sin marca abierta.
- Propuesta, por decidir: el SRS da un valor como propuesta.
- Abierto: el SRS deja la decisión sin tomar.
- Por confirmar: depende de una respuesta del líder de proyecto, de la empresa o de la asesora académica.
- Adoptado, por confirmar: valor que el código aplica donde el SRS deja una decisión abierta (igual que en MVP.md).

Estado de implementación al 18/10/2026. Las cuatro primeras categorías son las de MVP.md 12:

- Hecho y verificado: implementado, verificado por pruebas automatizadas y sin partes de interfaz pendientes.
- Hecho sin interfaz: el motor y la API cumplen los criterios y sus pruebas pasan; faltan las pantallas.
- Pendiente en parte: una parte está hecha y verificada, y al menos un criterio pide algo que solo puede dar la interfaz o está en conflicto.
- Pendiente: algo que un criterio exige y hoy no existe.
- Sin implementar: requisito posterior al MVP del que no hay código en el repositorio.

Fuentes. Además de los documentos de `docs/`, este documento usa el README, el código y el historial de git. Unos pocos datos vienen del registro de decisiones del estudiante, un archivo de trabajo que no está en el control de versiones; se cita como «registro de decisiones» solo cuando el dato no está en el SRS.

## Contenido

1. [Visión del producto](#1-visión-del-producto)
2. [Problema e impacto](#2-problema-e-impacto)
3. [Objetivos y métricas de éxito](#3-objetivos-y-métricas-de-éxito)
4. [Usuarios y partes interesadas](#4-usuarios-y-partes-interesadas)
5. [Alcance del producto por fases](#5-alcance-del-producto-por-fases)
6. [Requisitos funcionales](#6-requisitos-funcionales)
7. [Requisitos no funcionales](#7-requisitos-no-funcionales)
8. [Requisitos de datos](#8-requisitos-de-datos)
9. [Experiencia de usuario](#9-experiencia-de-usuario)
10. [Arquitectura y tecnologías](#10-arquitectura-y-tecnologías)
11. [Restricciones, marco legal, supuestos y dependencias](#11-restricciones-marco-legal-supuestos-y-dependencias)
12. [Fuera del alcance](#12-fuera-del-alcance)
13. [Hoja de ruta y entregas](#13-hoja-de-ruta-y-entregas)
14. [Criterios de aceptación](#14-criterios-de-aceptación)
15. [Riesgos y preguntas abiertas](#15-riesgos-y-preguntas-abiertas)
16. [Documentos relacionados y registro de cambios](#16-documentos-relacionados-y-registro-de-cambios)

---

## 1. Visión del producto

### 1.1 Qué es

El Proyecto 077 es una plataforma web de gestión de activos financieros para el inversionista individual (SRS 2.1). Reúne en un solo lugar los instrumentos, las posiciones y las transacciones de su portafolio, incluidas las que mantiene con distintos intermediarios en México y las de CETES, y con esa información mide el rendimiento y el riesgo del portafolio en su conjunto (Definición, «Descripción» y objetivo general).

Presenta los resultados en un tablero operativo. A partir de la fase de refinamiento los acompañará una explicación en lenguaje natural de los indicadores, generada con plantillas y sin servicio externo de inteligencia artificial (SRS 2.1; SRS 2.6.2, RF-14).

### 1.2 Propiedad central: un motor único de cálculo

Decidido (SRS 2.1; README, «Principio de arquitectura»):

- Todas las métricas salen de un solo motor de cálculo, en el servidor. Ninguna vista ni ningún cliente recalcula.
- Por eso cualquier cifra es idéntica en todas las vistas donde aparece (RNF-02) y se puede reproducir contra el conjunto de referencia del SRS 5.2 (RNF-01).
- El sistema solo guarda hechos: lo que captura el usuario y lo que publican las fuentes. Posiciones, valores e indicadores se derivan en cada consulta (SRS 3.4.3).

Para describir el producto, este documento usa el objetivo general de la Definición, más completo que el texto actual del SRS 2.1.

### 1.3 Lo que el producto no hace

Decidido:

- No emite recomendaciones de inversión individualizadas ni genera o sugiere composiciones de portafolio (SRS 2.4.1, R-01).
- No recibe, transmite ni ejecuta órdenes: solo registra las operaciones que el usuario ya hizo con su intermediario (R-02).
- Sus valuaciones son estimaciones informativas: no son precios oficiales ni sustituyen los estados de cuenta del intermediario (R-11).
- No ofrece datos de mercado en tiempo real (R-13).
- Muestra a la vista que la información no constituye asesoría de inversión y que las valuaciones son estimaciones (RF-12).

### 1.4 Valor para PluriOne

Según la Definición («Valor para PluriOne»), la plataforma amplía el portafolio de soluciones FinTech de la empresa con un producto propio:

- construido sobre una arquitectura documentada y extensible;
- con un motor de cálculo que puede reutilizarse en desarrollos posteriores;
- con una capa de analítica avanzada preparada para una fase siguiente.

### 1.5 Qué lo distingue

Según la Definición («Impacto» y «Justificación técnica»):

1. Consolida las posiciones con distintos intermediarios en México, incluidos los CETES. Cada emisión de CETES es un instrumento propio (RF-04), vence a su valor nominal (RF-26a), se valúa con una estimación (RF-26b) y usa las tasas reales del Banco de México (RF-30).
2. Es código propio, sin las obligaciones de la licencia AGPL-3.0 de las alternativas de código abierto (sección 2.3).
3. Sus cifras se validan contra un conjunto de referencia resuelto de forma independiente (OE-5; RNF-01).

### 1.6 Cómo crece el producto

El producto se construye en tres fases: el MVP, la fase de refinamiento y la fase posterior a la estadía (sección 5). La medición crece así (SRS 2.6.1 y 2.6.2):

- Rendimiento: en el MVP, el rendimiento ponderado por tiempo (TWR, RF-09); en la fase de refinamiento se agrega el rendimiento ponderado por dinero (XIRR, RF-19).
- Riesgo: en el MVP, la máxima caída (RF-10); en la fase de refinamiento, la volatilidad anualizada (RF-20), el índice de Sharpe (RF-17), la simulación Monte Carlo (RF-21) y, como opcional, el valor en riesgo histórico (RF-16).

### 1.7 Términos

Los términos del MVP (portafolio, intermediario, instrumento, CETES, posición, valor de mercado, resultado no realizado, TWR, máxima caída, datos semilla, SIE, FIX y otros) están en MVP.md 1.5, y las siglas técnicas que no aparecen aquí (por ejemplo, HTTPS, LGPL, MPL y LTS), en la tabla de acrónimos del SRS 1.3. El glosario completo del dominio financiero es un documento aparte, enlazado en el SRS 1.3. Este documento agrega:

| Término | Significado en este documento |
|---|---|
| PRD | Documento de requisitos del producto (*product requirements document*). |
| Fase de refinamiento | Del lunes 19 de octubre al viernes 20 de noviembre de 2026. El desarrollo termina el domingo 15 de noviembre; la semana del 16 se reserva para la capacitación, la entrega y el cierre (SRS 2.6 y 3.9.4). |
| Fase posterior a la estadía | Lo que la fase de refinamiento no alcance. No tiene fecha; su responsable y su calendario dependen de la empresa, por confirmar (SRS 2.6.3). |
| Rendimiento ponderado por dinero (XIRR) | Rendimiento que, a diferencia del TWR, sí depende del monto y la fecha de las aportaciones y los retiros del inversionista (RF-19). |
| Volatilidad anualizada | Medida de cuánto varían los rendimientos diarios, llevada a un año (RF-20). |
| Índice de Sharpe | Rendimiento por encima de una tasa libre de riesgo, por unidad de volatilidad; en RF-17 la tasa libre de riesgo es la de CETES a 28 días. |
| Valor en riesgo histórico | Estimación de la pérdida posible del portafolio a partir de sus rendimientos pasados (RF-16). |
| Simulación Monte Carlo | Generación de muchos escenarios hipotéticos con un modelo probabilístico (RF-21). No es una recomendación. |
| Índice de referencia | Índice con el que se compara el rendimiento del portafolio (RF-18). |
| S&P/BMV IPC | Índice de precios y cotizaciones de la Bolsa Mexicana de Valores; su histórico requiere una licencia de S&P Dow Jones Indices (R-06). |
| Aplicación web progresiva | Sitio web que se puede instalar en el teléfono como una aplicación (RF-24). |
| CSV | Archivo de texto con valores separados por comas (RF-33). |
| WCAG 2.2, nivel AA | Pautas de accesibilidad para el contenido web del W3C, en su nivel intermedio (SRS 4.5.1). |
| CDS | Coinbase Design System, base de la guía de estilo del cliente web, con un tema propio (SRS 4.5.1). |
| ADR | Registro de una decisión de arquitectura (*architecture decision record*). |
| DOF | Diario Oficial de la Federación. |
| LMV y LFPDPPP | Ley del Mercado de Valores y Ley Federal de Protección de Datos Personales en Posesión de los Particulares. |
| BMV y SHCP | Bolsa Mexicana de Valores y Secretaría de Hacienda y Crédito Público. |
| AMIB e INEGI | Asociación Mexicana de Instituciones Bursátiles e Instituto Nacional de Estadística y Geografía, fuentes de las cifras de la sección 2.4. |
| UDI | Unidad de inversión; RF-32 no la carga. |
| OWASP | OWASP Foundation, cuyo mínimo de costo para guardar contraseñas exige RNF-04. |
| REST | Transferencia de estado representacional (*representational state transfer*), el estilo de la API. |
| NVDA | Lector de pantalla libre para Windows (*NonVisual Desktop Access*). |

---

## 2. Problema e impacto

### 2.1 El problema del inversionista

Según la Definición («Descripción»):

1. Dispersión: la información del inversionista individual suele estar repartida entre estados de cuenta, hojas de cálculo y notas propias, y cada visión completa lo obliga a pasar cifras de un documento a otro.
2. Dificultad de método: el rendimiento observado mezcla lo que rindió el mercado con lo que el inversionista aportó o retiró, y separar esos dos efectos exige cálculos distintos.
3. Sin medida de riesgo: sin una medida consistente y actualizada del riesgo, las decisiones se apoyan en la intuición y los reportes se rehacen a mano cada vez.

### 2.2 Una brecha estructural

Quien invierte con más de un intermediario recibe de cada uno un estado de cuenta separado, con su propia posición y su propio rendimiento. Ni la Ley del Mercado de Valores (arts. 191 y 203) ni la Ley de Fondos de Inversión (art. 61 Bis) prevén un estado de cuenta que integre a distintos intermediarios (Definición, «Impacto»).

### 2.3 Por qué las alternativas solo resuelven en parte

Según la Definición («Impacto» y «Justificación técnica»):

| Alternativa | Licencia | Limitación |
|---|---|---|
| Consolidación manual en hojas de cálculo | — | Expuesta a errores: las auditorías reunidas por Panko (2008) los encontraron en 88 % de 113 hojas. |
| Ghostfolio | AGPL-3.0 | Gestiona portafolios, pero no documenta una fuente de precios para valores gubernamentales mexicanos como los CETES. |
| Wealthfolio | AGPL-3.0 | Da seguimiento a emisoras de la BMV y calcula el TWR, pero no documenta una fuente de precios para los CETES. |
| Firefly III | AGPL-3.0 | No gestiona inversiones. |
| Maybe | AGPL-3.0 | Su repositorio está archivado desde 2025. |
| OpenBB | AGPL-3.0 | Es una plataforma de datos para análisis, no de seguimiento de portafolios. |

La AGPL-3.0 obliga a ofrecer el código fuente de cualquier versión modificada a quienes usan el programa por red. Derivar el producto de una de esas herramientas es incompatible con mantener cerrado el código de un producto propio de la empresa. Decisión: desarrollo propio, tomando esas implementaciones como referencia de diseño (Definición, «Justificación técnica»).

### 2.4 Tamaño del segmento

Según la Definición («Impacto»):

| Indicador | Dato | Fuente que cita la Definición |
|---|---|---|
| Clientes de fondos de inversión | 2,119,566 en 2015; 16,352,095 al primer trimestre de 2026 | AMIB (2026), p. 55 |
| Fondos disponibles | 567 en 2015; 636 en el mismo periodo | AMIB (2026), p. 55 |
| Proporción de la población de 18 a 70 años con un fondo de inversión o un depósito a plazo | 2.1 % en 2021; 3.4 % en 2024 | INEGI (2025), p. 8 |
| Cuenta promedio en casa de bolsa | 0.4 millones de pesos al primer trimestre de 2026 | AMIB (2026), p. 35 |

La Definición lo lee así: el mercado creció en número de clientes, no en variedad de productos; la cifra de clientes no equivale a personas, porque suma los de fondos de deuda y los de renta variable, y la cuenta promedio refleja el predominio de cuentas de escala individual y no institucional.

### 2.5 Criticidad

Las cifras orientan decisiones sobre el patrimonio del usuario, así que un error de cálculo puede inducirlo a decidir mal. Además, las fuentes externas no garantizan la exactitud de sus datos: el Banco de México declina la responsabilidad por la precisión de su información, y la BMV, por su veracidad y sus errores (SRS 2.4.4, R-10). Lo atienden RNF-01, RNF-02 y el conjunto de referencia del SRS 5.2.

### 2.6 Cómo responde el producto

Consolida las posiciones que el inversionista mantiene con distintos intermediarios, incluidas las de CETES, y mide su rendimiento y su riesgo con un motor único de cálculo cuyas cifras se validan contra un conjunto de datos de referencia (Definición, «Impacto»).

---

## 3. Objetivos y métricas de éxito

### 3.1 Objetivo general

Según la Definición:

> Desarrollar una plataforma web que consolide las posiciones y transacciones de un inversionista individual con distintos intermediarios en México, incluidas las de CETES, para medir el rendimiento ponderado por tiempo y el riesgo del portafolio en su conjunto.

### 3.2 Objetivos específicos

Los enunciados son los de la Definición. Los requisitos de cada objetivo salen de la columna OE del SRS 3.2 y de las tablas MoSCoW de la Definición. La Definición no asigna objetivo a los 11 requisitos diferidos del SRS 2.6.1 (RF-17, RF-19 a RF-24, RF-32 a RF-34 y RF-39), y este documento tampoco se los asigna.

| OE | Enunciado (Definición) | Requisitos que lo atienden | Cómo se comprueba | Estado al 18/10/2026 |
|---|---|---|---|---|
| OE-1 | Especificar los requisitos funcionales, no funcionales y lógicos de datos de la plataforma, junto con el glosario del dominio, para delimitar qué se consolida y qué se mide. | El SRS | Con el propio SRS: 18 requisitos funcionales con criterio de aceptación (3.2), RNF-01 a RNF-12 (3.3), las reglas RD-01 a RD-24 (3.4) y el glosario aparte (1.3). Las fuentes no fijan una meta numérica. La versión 1.0 del SRS será la vigente al concluir la última revisión del MVP, y se registrará como «revisada», no «aprobada» (SRS 3.9.5; abierto). | El SRS está en la versión 0.3, en elaboración. Siguen vacíos el 1.1, la tabla de términos del 1.3, las fichas detalladas de RF-06, RF-08, RF-09 y RF-10, el 4.5.3, el 4.5.4 y el 5.3, salvo la fila de RF-01 (SRS 3.1). |
| OE-2 | Diseñar la arquitectura web, el modelo de datos y la interfaz de la plataforma, y registrar sus decisiones técnicas, para que todas las vistas obtengan sus cifras de un motor único de cálculo. | El SRS, sección 4 | Con el SRS 4.1 (casos de uso), 4.2 (componentes), 4.3 (modelo entidad-relación), 4.4 (diccionario de datos), 4.5.1 (guía de estilo) y 4.5.2 (mapa de navegación), y con los registros de decisión (ADR). El fin del objetivo se observa con RNF-02 (cifras idénticas entre vistas) y RNF-10 (cambiar una fuente sin tocar el motor). Las fuentes no fijan una meta numérica. | Integrados 4.1 a 4.4, 4.5.1 y 4.5.2. Vacíos 4.5.3 (wireframes) y 4.5.4 (mockups). No existe ningún ADR (README, «Índice del paquete»). La interfaz web no está construida (MVP.md 1.4). |
| OE-3 | Implementar el registro de portafolios, intermediarios y transacciones sobre un catálogo de instrumentos que incluya las emisiones de CETES, con validación de saldos por intermediario y aislamiento por usuario, para consolidar las posiciones y las transacciones del portafolio en su conjunto. | M: RF-01 a RF-06, RF-12, RF-25 y RF-28. S: RF-15 y RF-27. | El CPF de cada requisito; RNF-03 (aislamiento entre cuentas) y RNF-04 (contraseñas no reversibles). | RF-01 a RF-06, RF-25 y RF-28: hechos sin interfaz. RF-12: pendiente en parte. RF-15 y RF-27: sin implementar. |
| OE-4 | Implementar el motor de cálculo del valor de mercado, del rendimiento ponderado por tiempo y de la máxima caída –incluidos el vencimiento y la valuación de los CETES– y su presentación en un tablero, para medir el rendimiento y el riesgo del portafolio en su conjunto. | M: RF-07 a RF-11, RF-26a, RF-26b, RF-30 y RF-31. S: RF-13 y RF-14. C: RF-16 y RF-18. | El CPF de cada requisito; RNF-01, que fija la tolerancia de RF-08, RF-09, RF-10 y RF-26b. | RF-30: hecho y verificado. RF-08, RF-09, RF-10, RF-26a y RF-26b: hechos sin interfaz. RF-07, RF-11 y RF-31: pendientes en parte. RF-13, RF-14, RF-16 y RF-18: sin implementar. |
| OE-5 | Comparar los resultados del motor con un conjunto de referencia resuelto de forma independiente, que incluya un instrumento en dos intermediarios y una emisión de CETES que venza en el periodo, para demostrar que difieren a lo más un centavo en importes y 0.001 puntos porcentuales en rendimiento y máxima caída. | RNF-01 | CPNF-01 sobre el SRS 5.2, con diferencia de 0.01 o menos en importes y de 0.001 puntos porcentuales o menos en TWR y máxima caída, y AC-03: el commit que congela el SRS 5.2 es anterior al primer commit del motor. El SRS 5.2 incluye DEMOACC con Casa A y Casa B y la emisión BI261008, que vence el 08/10/2026. | El SRS 5.2 se congeló con `11097f8` (15/10) antes de `b3391fd` (17/10), el primer commit del motor. CPNF-01 pasa en el motor (27 pruebas) y por la API desde la base, sin red (3 pruebas). Falta guardar la tabla de diferencias (MVP.md 6.1 y 12.2). |

Notas:

- La documentación técnica, el manual de usuario y el plan de mantenimiento no son necesarios para el objetivo general, así que no forman un objetivo específico: son actividades del cronograma y entregables (Definición), y se exigen al cierre en AC-12 (SRS 3.9.4).
- El conjunto de referencia se resolvió por dos caminos que no comparten código con el motor ni entre sí: un libro de Excel con fórmulas visibles y un programa en Python con `decimal`. Difieren a lo más 1.6 × 10⁻¹¹ pesos en importes y 4.2 × 10⁻¹⁴ puntos porcentuales en TWR y máxima caída (SRS 5.2, «Construcción»). Según el SRS 5.2, se elaboró con apoyo de Claude Code, de Anthropic, y lo revisó el estudiante (por confirmar).

### 3.3 Métricas de éxito

Solo se incluyen metas que fijan las fuentes. El detalle de cada requisito no funcional está en la sección 7, y el de cada criterio de aceptación, en la sección 14.

| Métrica | Origen | Valor objetivo | Fecha | Estado al 18/10/2026 |
|---|---|---|---|---|
| Exactitud del cálculo sobre el SRS 5.2 | OE-5; RNF-01; R-10 | Diferencia de 0.01 o menos en importes y de 0.001 puntos porcentuales o menos en TWR y máxima caída; títulos iguales; cada rechazo esperado (N1 a N8) con su motivo y sin cambiar cifras (SRS 5.2) | 18/10/2026 | Pasa en el motor y por la API; falta guardar la tabla de diferencias |
| Integridad del conjunto de referencia | AC-03 | El commit que congela el SRS 5.2 es anterior al primero del motor | 18/10/2026 | Cumplido en git; el conjunto de referencia (`backend/tests/oraculo/`) no cambió desde `11097f8` (MVP.md 12.2) |
| Cifras idénticas entre vistas y en consultas repetidas | OE-2; RNF-02 | 0 cifras distintas para el SRS 5.2 | 18/10/2026 | La comparación automática por la API pasa (17 pruebas); la demostración con capturas necesita las pantallas V-04 y V-05 |
| Imprescindibles que cumplen su criterio | AC-01 | 18 de 18, cada uno con su CPF aprobado y registrado | 18/10/2026 | 1 hecho y verificado, 13 hechos sin interfaz y 4 pendientes en parte (RF-07, RF-11, RF-12 y RF-31); falta el registro de resultados (MVP.md 12.1 y 12.2) |
| Seguridad del MVP | AC-02; RNF-03 a RNF-05 | Valores objetivo de la sección 7 | 18/10/2026 | RNF-03 y RNF-04 pasan; no consta la ejecución de CPNF-05 |
| Calidad al cierre | AC-09; RNF-06 a RNF-12 | Valores objetivo de la sección 7 | A más tardar el 13/11/2026 | Por verificar |
| Requisitos de la fase de refinamiento | AC-10 | Cada requisito de SRS 2.6 que se incorpore a SRS 3.2 cumple su criterio y aprueba su CPF; los no entregados constan en SRS 3.1 y 2.6.3 como posteriores a la estadía | 20/11/2026 | Ninguno implementado; la fase empieza el 19/10/2026 |
| Observaciones del líder | AC-11 | Cada una resuelta o registrada en SRS 3.1 como trasladada | 20/11/2026 | La revisión del MVP aún no ocurre |

### 3.4 Lo que las fuentes no fijan como métrica

- Adopción, uso, retención, satisfacción y negocio: no hay metas. Durante la estadía no hay pruebas con usuarios reales, solo cuentas de prueba con datos ficticios (SRS 3.9; S-04).
- Exactitud de los precios y cercanía de la valuación de los CETES al mercado secundario: por decisión del estudiante, que el SRS deja por confirmar con el líder, la aceptación no las evalúa; los precios son sintéticos y van marcados (SRS 3.9; S-05; S-13).
- Accesibilidad: el nivel AA de WCAG 2.2 es una meta de diseño del estudiante, no un requisito verificable; agregar un requisito de accesibilidad está abierto (SRS 4.5.1; sección 9.3).
- Desempeño: RNF-06 todavía no tiene valor objetivo; el tiempo máximo T se fija tras medir la línea base el 30/10/2026 (SRS 3.3).
- Exactitud en el tablero: el criterio 1 de RF-11 pide la tolerancia de RNF-01 (0.001 puntos porcentuales), pero el tablero presenta los por cientos con 2 decimales (RD-13). La tolerancia se cumple en las cifras del motor (CPNF-01), no en lo que muestra el tablero. Hay dos salidas, sin decidir: aplicar la tolerancia a las cifras del motor o presentar 3 decimales (MVP.md 3.8 y 12.5).

---

## 4. Usuarios y partes interesadas

### 4.1 Usuario: el inversionista

El producto tiene un único perfil, el inversionista, en todas sus fases (SRS 2.3). Las cinco dimensiones del perfil y sus consecuencias están en el SRS 2.3; MVP.md 2.1 resume cuatro. En breve:

- Es una persona física, mayor de edad, que administra su propio patrimonio repartido entre varios instrumentos e intermediarios. Por eso el aislamiento es horizontal, entre cuentas equivalentes, sin operación para varias organizaciones (RF-02; X-02).
- Sabe qué es comprar y vender y distingue una ganancia de una pérdida, pero no se supone que conozca el TWR ni la máxima caída. Por eso cada indicador va con su unidad y una definición en la misma pantalla (RNF-07).
- Usa aplicaciones web y banca en línea sin dificultad, pero no se supone que construya hojas de cálculo ni manipule datos en lote. Por eso las transacciones se capturan en un formulario guiado (RF-05).
- Consulta de forma esporádica y registra sus transacciones cuando ocurren. Por eso el tablero debe entenderse sin recordar sesiones anteriores.
- No hay administradores, operadores, supervisores ni grupos: no hay jerarquía de privilegios ni matriz de roles.

La frase «nunca por carga de archivo» del SRS 2.3 choca con RF-33, que prevé importar precios desde un archivo CSV; cómo se resuelve está abierto (sección 6.9).

### 4.2 Suposiciones sobre el usuario, sus datos y su equipo

| ID | Suposición (SRS 2.5) | Estado |
|---|---|---|
| S-04 | Durante la estadía solo hay cuentas de prueba, con correos y datos ficticios, creadas por el estudiante, los evaluadores o quienes reciban la capacitación; ningún inversionista registra datos reales. | Por confirmar con la empresa, incluida la capacitación |
| S-07 | El usuario registra cada posición desde su primera compra, sin posiciones de origen irreconstruible ni traspasos entre intermediarios. | Qué hacer con el saldo inicial y los traspasos está abierto (sección 6.12) |
| S-08 | El usuario obtiene de su comprobante o estado de cuenta los títulos, el precio por título y las comisiones con su IVA. | Decidido |
| S-09 | En el MVP opera sobre el catálogo semilla, con fechas dentro del intervalo de las semillas, sin dar de alta instrumentos. | Intervalo fijado en el SRS 5.2: del 10/09/2026 al 14/10/2026 |
| S-10 | Mientras RF-23 siga diferido, todo se pacta y se liquida en la divisa base, que en el MVP solo puede ser MXN. | Decidido |
| S-11 | Usa una versión estable vigente de un navegador basado en Chromium o de Firefox (SRS 3.5). | La definición de «vigente» está por confirmar (sección 10.6) |

Equipo del usuario (SRS 3.6.1): cualquier equipo con un navegador del SRS 3.5; el sistema no agrega requisitos de procesador, memoria ni sistema operativo, porque ninguna métrica se calcula en el cliente. Resolución mínima de escritorio: 1280 × 720 px CSS. Resolución mínima en móvil: 360 px, abierta (sección 9.4). Durante la estadía, navegador y servidor comparten equipo y no hace falta Internet.

### 4.3 Otros actores

- Instalador: rol técnico sin cuenta ni pantallas, que no es un perfil del SRS 2.3. Carga los datos semilla (CU-11). Si se muestra como actor o la carga se trata como precondición está abierto (SRS 4.1).
- SIE del Banco de México: actor secundario solo en la fase de refinamiento (CU-14, al que da inicio la tarea diaria de RF-32 y RF-34). En el MVP no es actor: solo sirvió para construir la semilla de tasas (SRS 4.1; R-08).

### 4.4 Escenarios de uso

- MVP: el recorrido típico, con los casos CU-01 a CU-12, está en MVP.md 2.2, y el escenario de demostración del SRS 5.2, en MVP.md 2.3 y 5.8.
- Fase de refinamiento: el SRS 4.1 agrega estos casos de uso, con las fechas del SRS 2.6.1 y 2.6.2.

| CU | Qué puede hacer el usuario | RF | Fecha objetivo |
|---|---|---|---|
| CU-13 | Modificar o eliminar una transacción registrada; incluye la validación de saldo de CU-12 | RF-39 | Por fijar (abierto) |
| CU-14 | Ver actualizadas las tasas y las emisiones nuevas de CETES; lo inicia la tarea diaria y el SIE es actor secundario | RF-32; RF-34 | Semana del 19 de octubre |
| CU-15 | Capturar o importar precios de cierre, privados de su autor | RF-33 | Semana del 26 de octubre |
| CU-16 | Consultar el desglose por intermediario | RF-27 | Semana del 19 de octubre (propuesta, por decidir) |
| CU-17 | Consultar la distribución por clase de activo | RF-13 | Semana del 19 de octubre (propuesta, por decidir) |
| CU-18 | Exportar el portafolio y sus transacciones | RF-15 | Semana del 26 de octubre (propuesta, por decidir) |
| CU-19 | Leer la explicación de los indicadores; extiende CU-07 | RF-14 | Semana del 2 de noviembre (decidido) |
| CU-20 | Simular escenarios por Monte Carlo | RF-21 | Semana del 26 de octubre |
| CU-21 | Simular composiciones alternativas que él mismo define | RF-22 | Semana del 2 de noviembre |

Sin caso de uso propio (SRS 4.1): los indicadores de RF-16 a RF-20 se presentarían en CU-07 (abierto); RF-23 amplía CU-03 y CU-05, y RF-24 es otro canal para los mismos casos.

Entorno durante la estadía: no hay servidor de producción. El sistema se ejecuta, se prueba y se demuestra en el equipo de desarrollo (S-03). Si entra RF-24, el teléfono usará la red local con HTTPS (SRS 3.6.1).

### 4.5 Partes interesadas

Personas, por rol (SRS 1.2, 3.7 y 3.9.1; sin datos de contacto):

| Rol | Persona | Responsabilidad (SRS 1.2) | Participación en el producto |
|---|---|---|---|
| Desarrollador y analista | Ramon Ernesto Nieblas Mendivil | Análisis, diseño, desarrollo y documentación del sistema | Una sola persona en cuatro roles: analista y arquitecto, desarrollador del servidor, desarrollador del cliente y responsable de pruebas (SRS 3.7). Como responsable de pruebas aporta la evidencia en un registro fechado, pero no decide la aceptación (SRS 3.9.1). Definió el alcance funcional y las tecnologías con la libertad que dio el líder (S-01). |
| Líder de proyecto | Edgar Loeffelmann Ibarra | Revisión del MVP y aprobación del entregable | Fijó la entrega del MVP a más tardar el 18 de octubre y que `docs/` contenga un archivo del MVP y otro del PRD (S-01; AC-06). Revisa el MVP después del 18 de octubre, en el repositorio que indique, y una segunda vez si encuentra inconsistencias o carencias (SRS 3.9.1). Por confirmar: si su revisión cubre `docs/`, la fecha, el medio, la hora de corte y si su conformidad queda por escrito. |
| Asesor empresarial | Persona de la empresa nombrada en el SRS 1.2 | Seguimiento administrativo de la estadía | No revisa el sistema ni el SRS y no interviene en la aceptación (SRS 3.9.1). |
| Asesora académica | Persona de la universidad nombrada en el SRS 1.2 | Seguimiento académico y evaluación de la memoria de estadías | Revisa la memoria y, quizá, el desarrollo o la terminación del proyecto el 20 de noviembre. Por confirmar: qué revisa, con qué evidencia y si interviene en la conformidad del cierre (SRS 3.9.1 y 3.9.4). |

Organización y usuarios:

- PluriOne S.A. de C.V. recibe un producto FinTech propio (Definición). Le corresponde confirmar o decidir:
  - si habrá datos reales y quién sería el responsable del tratamiento (S-04);
  - el plazo del bloqueo tras la revocación del consentimiento (RD-23);
  - si cuenta con una opinión jurídica sobre el art. 225 de la LMV (S-15);
  - si acepta RF-24 solo para Android o como aplicación web progresiva (S-06);
  - si ofrecerá el sistema solo como servicio web o lo entregará para instalarse, y el periodo del plan de mantenimiento (D-05 y D-06);
  - quién genera el *token* del SIE si hay un servidor de la empresa (D-01);
  - quién hace la fase posterior a la estadía y con qué calendario (SRS 2.6.3);
  - si contrata licencias de precios reales o del S&P/BMV IPC (X-07; R-06);
  - si la diferencia de la valuación de los CETES frente al mercado secundario es aceptable (S-13);
  - si existe una identidad visual de PluriOne para el tema del cliente (SRS 4.5.1).
- Inversionista individual: el usuario final (SRS 2.3). Durante la estadía solo hay cuentas de prueba (S-04).

Terceros que condicionan el producto (SRS 2.4 y 2.5.4):

| Tercero | Qué condiciona |
|---|---|
| Banco de México (SIE) | Fuente de las tasas de CETES y, desde la fase de refinamiento, del tipo de cambio FIX. Exige citar la fuente y su dirección, y limita las consultas a 10,000 diarias por *token* (R-05, R-08, R-15; D-01 a D-03). |
| CNBV | Quien da asesoría de inversión individualizada debe registrarse ante ella (R-01). Los precios oficiales de valuación están reservados a los proveedores de precios que autoriza, hoy PiP y Valmer (R-11). |
| BMV | Prohíbe reproducir y extraer su contenido sin autorización escrita, y licencia sus datos con contrato y pago, incluso los de cierre (R-05, R-13). |
| S&P Dow Jones Indices | Licencia el histórico del S&P/BMV IPC (R-06; condiciona RF-18). |
| SHCP | Fija el programa trimestral de subastas de CETES (R-14). |

---

## 5. Alcance del producto por fases

### 5.1 Fases

| Fase | Fechas | Qué entra | Cómo se acepta |
|---|---|---|---|
| MVP | A más tardar el domingo 18 de octubre de 2026, inclusive (SRS 3.8) | Los 18 imprescindibles del SRS 3.2 (detalle en MVP.md) | AC-01 a AC-08 (sección 14.3) |
| Fase de refinamiento | Del lunes 19 de octubre al viernes 20 de noviembre de 2026; el desarrollo termina el domingo 15 de noviembre (SRS 2.6 y 3.8) | Los 11 diferidos del SRS 2.6.1, los 4 que deberían incluirse y los 2 opcionales del SRS 2.6.2. Antes que ellos: los imprescindibles que se trasladen por S-02, la revisión del MVP y la corrección de sus observaciones (SRS 2.6.3) | AC-09 a AC-13, al cierre (sección 14.5) |
| Capacitación, entrega y cierre (última semana de la fase de refinamiento, no una fase aparte) | Semana del 16 de noviembre; la estadía termina el viernes 20 de noviembre de 2026 (SRS 3.9.4) | Capacitación, entrega y cierre. La documentación técnica, el manual de usuario y el plan de mantenimiento se hacen en las semanas del 2 y del 9 de noviembre (SRS 2.6.3) | AC-09 a AC-13 |
| Posterior a la estadía | Sin fecha; su responsable y su calendario dependen de la empresa (por confirmar) | Lo que la fase de refinamiento no alcance, en el orden de la sección 5.3, con sus dependientes (SRS 2.6.3) | Sin criterios en el SRS |

### 5.2 Requisitos por grupo

| Grupo | RF | Cuántos | Prioridad | Fase | Fuente |
|---|---|---|---|---|---|
| Imprescindibles | RF-01 a RF-12, RF-25, RF-26a, RF-26b, RF-28, RF-30 y RF-31 | 18 | M | MVP | Definición; SRS 3.2 |
| Deberían incluirse | RF-13, RF-14, RF-15 y RF-27 | 4 | S | Fase de refinamiento. La fecha de RF-14 está decidida; las demás son propuestas | Definición; SRS 2.6.2 |
| Opcionales | RF-16 y RF-18 | 2 | C | Semana del 9 de noviembre si hay margen; si no, posterior a la estadía (propuesta) | Definición; SRS 2.6.2 |
| Diferidos con fecha | RF-17, RF-19 a RF-24, RF-32 a RF-34 y RF-39 | 11 | Diferido, sin categoría MoSCoW | Fase de refinamiento; la fecha de RF-39 está por fijar | Definición; SRS 2.6.1 |
| Total de requisitos funcionales | | 35 | | | |
| No se incluirá | Ningún RF: son las exclusiones X-01 a X-07 y lo que excluyen R-01, R-02 y R-13 | — | W | Nunca | Definición; SRS 2.4.7 |

La numeración no es continua: el SRS y la Definición no tienen RF-29 ni RF-35 a RF-38. Los cuatro últimos son identificadores que el registro de decisiones propone para el saldo inicial, los traspasos, los eventos corporativos y la recuperación de contraseña, sin decisión (sección 6.12).

### 5.3 Reglas de prioridad y de recorte

- Lo que va primero en la fase de refinamiento: los imprescindibles que S-02 pase a la fase, la revisión del MVP (D-07) y, si el líder encuentra inconsistencias o carencias, su corrección antes de la segunda revisión. Esas correcciones consumen el margen de la fase (SRS 2.6.3 y 3.9.3).
- Orden de recorte, decidido: MoSCoW estricto. De los requisitos del SRS 2.6.2 se recortan primero los opcionales (C), RF-16 y RF-18; los que deberían incluirse (S), RF-27, RF-13, RF-15 y RF-14, forman el compromiso que se conserva (SRS 2.6.3).
- Abierto: el lugar de los diferidos del SRS 2.6.1 en ese orden y el orden entre ellos, porque no tienen categoría MoSCoW (SRS 2.6.3).
- Arrastre: con cada requisito que se recorta pasan los que dependen de él; por ejemplo, RF-17 y RF-21 con RF-20, y RF-23 y RF-34 con RF-32 (SRS 2.6.3; S-02).
- Revisión: el orden se revisa al cierre de cada semana, y cada cambio se registra en el SRS 3.1 (SRS 2.6 y 2.6.3).
- Imprescindibles que no cumplen a tiempo: su paso a la fase de refinamiento se acuerda con el líder y se registra en el SRS 3.1 antes de la revisión (SRS 3.9.2; S-02). Al 18/10/2026 no consta ese acuerdo (MVP.md 12.1).

### 5.4 Cómo cambian las capacidades por fase

| Capacidad | MVP | Fase de refinamiento |
|---|---|---|
| Rendimiento | TWR (RF-09) | Se agrega el XIRR (RF-19) |
| Riesgo | Máxima caída (RF-10) | Se agregan volatilidad (RF-20), índice de Sharpe (RF-17), Monte Carlo (RF-21) y, como opcional, valor en riesgo histórico (RF-16) |
| Datos de mercado | Semillas fijas, con intervalo del 10/09 al 14/10/2026 (S-09): precios sintéticos (RF-07) y tasas reales (RF-30), estas con colocaciones del 27/08 al 15/10/2026 (SRS 5.2) | Actualización diaria desde el SIE (RF-32), emisiones nuevas de CETES (RF-34) y precios que captura el usuario (RF-33) |
| Divisas | Solo MXN (S-10) | Varias divisas; con el FIX, solo el dólar (RF-23) |
| Transacciones | Registrar y consultar (RF-05) | Modificar y eliminar (RF-39, fecha por fijar) |
| Presentación | Tablero y posiciones (RF-06, RF-08, RF-11) | Desglose por intermediario (RF-27), distribución por clase de activo (RF-13), explicación en lenguaje natural (RF-14) y, como opcional, comparación con un índice (RF-18) |
| Simulación | — | Escenarios Monte Carlo (RF-21) y composiciones definidas por el usuario (RF-22) |
| Salida de datos | — | Exportación del portafolio y sus transacciones (RF-15) |
| Canales | Cliente web | Aplicación móvil con paridad de indicadores (RF-24) |

---

## 6. Requisitos funcionales

### 6.1 Cómo leer el catálogo

- Las áreas A a G son las de MVP.md 3.1; las áreas H (simulación) e I (exportación y otros canales) se agregan aquí para requisitos que no son del MVP. La agrupación es de este documento: el SRS lista los requisitos por identificador.
- Los enunciados son textuales del SRS 3.2 (MVP) o del SRS 2.6 (fases posteriores), que resumen los de la Definición sin cambiar su alcance.
- Requisitos del MVP: cada ficha da lo esencial y remite a MVP.md para los criterios numerados, la verificación, los valores adoptados y el estado; los criterios son los del SRS 3.2.
- Requisitos posteriores al MVP: ninguno tiene todavía criterio de aceptación. Al entrar en desarrollo, cada uno pasará al SRS 3.2 con su criterio de aceptación y su caso de prueba (SRS 2.6), y al cierre se acepta con AC-10. Por eso su ficha da el método de verificación previsto: el CPF que asigna la Definición, cuando lo asigna, y los métodos, dependencias y condiciones que ya fija el SRS.
- Los cálculos de los requisitos posteriores usan el motor del MVP y solo valen en las fechas que cubren las semillas, ampliadas después por RF-32 y RF-33 (SRS 2.6).
- Ningún requisito posterior al MVP tiene código al 18/10/2026. Las únicas menciones en el código son las de RF-39: `backend/app/api/rutas_transacciones.py` declara que no existen operaciones para modificar ni eliminar transacciones, y `backend/03_probar_esquema.sql` comprueba que el rol de la API no puede modificarlas (RD-09; RF-39, diferido).

### 6.2 Resumen del catálogo

| RF | Requisito | Área | Prioridad | Fase y fecha objetivo | OE | Prueba | Estado al 18/10/2026 | Detalle |
|---|---|---|---|---|---|---|---|---|
| RF-01 | Registro e inicio de sesión | A | M | MVP | OE-3 | CPF-01 | Hecho sin interfaz | 6.3; MVP.md 3.3 |
| RF-02 | Aislamiento por usuario | A | M | MVP | OE-3 | CPF-02 | Hecho sin interfaz | 6.3; MVP.md 3.3 |
| RF-12 | Consentimiento, aviso de privacidad y advertencias | A | M | MVP | OE-3 | CPF-12 | Pendiente en parte | 6.3; MVP.md 3.3 |
| RF-03 | Gestión de portafolios | B | M | MVP | OE-3 | CPF-03 | Hecho sin interfaz | 6.4; MVP.md 3.4 |
| RF-25 | Intermediarios | B | M | MVP | OE-3 | CPF-25 | Hecho sin interfaz | 6.4; MVP.md 3.4 |
| RF-04 | Catálogo de instrumentos | C | M | MVP | OE-3 | CPF-04 | Hecho sin interfaz | 6.5; MVP.md 3.5 |
| RF-34 | Emisiones de CETES posteriores a la semilla | C | Diferido | Semana del 19 de octubre | — | — | Sin implementar | 6.5 |
| RF-05 | Registro y consulta de transacciones | D | M | MVP | OE-3 | CPF-05 | Hecho sin interfaz | 6.6; MVP.md 3.6 |
| RF-28 | Saldo no negativo por intermediario | D | M | MVP | OE-3 | CPF-28 | Hecho sin interfaz | 6.6; MVP.md 3.6 |
| RF-23 | Transacciones en más de una divisa | D | Diferido | Semana del 2 de noviembre | — | — | Sin implementar | 6.6 |
| RF-39 | Modificar y eliminar transacciones | D | Diferido | Por fijar | — | — | Sin implementar | 6.6 |
| RF-06 | Posición vigente | E | M | MVP | OE-3 | CPF-06 | Hecho sin interfaz | 6.7; MVP.md 3.7 |
| RF-08 | Valor de mercado y resultado no realizado | E | M | MVP | OE-4 | CPF-08 | Hecho sin interfaz | 6.7; MVP.md 3.7 |
| RF-26a | Vencimiento de los CETES | E | M | MVP | OE-4 | CPF-26a | Hecho sin interfaz | 6.7; MVP.md 3.7 |
| RF-26b | Valor estimado de los CETES | E | M | MVP | OE-4 | CPF-26b | Hecho sin interfaz | 6.7; MVP.md 3.7 |
| RF-27 | Desglose por intermediario | E | S | Semana del 19 de octubre (propuesta) | OE-3 | CPF-27 | Sin implementar | 6.7 |
| RF-13 | Distribución por clase de activo | E | S | Semana del 19 de octubre (propuesta) | OE-4 | CPF-13 | Sin implementar | 6.7 |
| RF-09 | Rendimiento ponderado por tiempo (TWR) | F | M | MVP | OE-4 | CPF-09 | Hecho sin interfaz | 6.8; MVP.md 3.8 |
| RF-10 | Máxima caída | F | M | MVP | OE-4 | CPF-10 | Hecho sin interfaz | 6.8; MVP.md 3.8 |
| RF-11 | Tablero | F | M | MVP | OE-4 | CPF-11 | Pendiente en parte | 6.8; MVP.md 3.8 |
| RF-19 | Rendimiento ponderado por dinero (XIRR) | F | Diferido | Semana del 19 de octubre | — | — | Sin implementar | 6.8 |
| RF-20 | Volatilidad anualizada | F | Diferido | Semana del 19 de octubre | — | — | Sin implementar | 6.8 |
| RF-17 | Índice de Sharpe | F | Diferido | Semana del 26 de octubre | — | — | Sin implementar | 6.8 |
| RF-14 | Explicación en lenguaje natural | F | S | Semana del 2 de noviembre (decidida) | OE-4 | CPF-14 | Sin implementar | 6.8 |
| RF-16 | Valor en riesgo histórico | F | C | Semana del 9 de noviembre si hay margen (propuesta) | OE-4 | CPF-16 | Sin implementar | 6.8 |
| RF-18 | Comparación contra un índice de referencia | F | C | Igual que RF-16 (propuesta) | OE-4 | CPF-18 | Sin implementar | 6.8 |
| RF-07 | Precios de cierre sintéticos | G | M | MVP | OE-4 | CPF-07 | Pendiente en parte | 6.9; MVP.md 3.9 |
| RF-30 | Tasas reales de CETES | G | M | MVP | OE-4 | CPF-30 | Hecho y verificado | 6.9; MVP.md 3.9 |
| RF-31 | Procedencia de cada dato | G | M | MVP | OE-4 | CPF-31 | Pendiente en parte | 6.9; MVP.md 3.9 |
| RF-32 | Actualización diaria desde el SIE | G | Diferido | Semana del 19 de octubre | — | — | Sin implementar | 6.9 |
| RF-33 | Captura o importación de precios de cierre | G | Diferido | Semana del 26 de octubre | — | — | Sin implementar | 6.9 |
| RF-21 | Escenarios por Monte Carlo | H | Diferido | Semana del 26 de octubre | — | — | Sin implementar | 6.10 |
| RF-22 | Composiciones alternativas | H | Diferido | Semana del 2 de noviembre | — | — | Sin implementar | 6.10 |
| RF-15 | Exportación | I | S | Semana del 26 de octubre (propuesta) | OE-3 | CPF-15 | Sin implementar | 6.11 |
| RF-24 | Aplicación móvil | I | Diferido | Semanas del 2 y del 9 de noviembre | — | — | Sin implementar | 6.11 |

Áreas: A, cuenta, consentimiento y aislamiento; B, portafolios e intermediarios; C, catálogo; D, transacciones; E, posiciones y valuación; F, indicadores y tablero; G, datos de mercado y procedencia; H, simulación; I, exportación y otros canales. Un guion en OE o Prueba significa que la Definición no los asigna.

### 6.3 Área A. Cuenta, consentimiento y aislamiento

#### RF-01 — Registro e inicio de sesión

- Enunciado (SRS 3.2): «El sistema deberá permitir a una persona registrarse con correo y contraseña, e iniciar sesión con esas credenciales.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-01. Casos de uso: CU-01 y CU-02. Pantallas: V-01 y V-02.
- Relación con otros requisitos: el registro exige el consentimiento de RF-12; reglas RD-03 y RD-11; la contraseña se guarda conforme a RNF-04.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle, verificación y valores adoptados: MVP.md 3.3.
- Estado al 18/10/2026: hecho sin interfaz; faltan V-01 y V-02.
- Abierto: la política de contraseña y el mensaje de error del inicio de sesión (el código aplica valores adoptados, por confirmar). El cierre de sesión no tiene requisito propio (SRS 4.1).

#### RF-02 — Aislamiento por usuario

- Enunciado (SRS 3.2): «El sistema deberá restringir el acceso de cada usuario autenticado exclusivamente a los portafolios, intermediarios, transacciones y posiciones de su propiedad.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-02. Casos de uso: CU-03 a CU-07. Pantalla: V-12.
- Relación con otros requisitos: reglas RD-01 y RD-02; RNF-03; exclusión X-02.
- Criterio de aceptación: SRS 3.2, criterios 1 y 2. Detalle: MVP.md 3.3.
- Estado al 18/10/2026: hecho sin interfaz; falta V-12.

#### RF-12 — Consentimiento, aviso de privacidad y advertencias

- Enunciado (SRS 3.2): «El sistema deberá recabar el consentimiento expreso del usuario para el tratamiento de sus datos personales, financieros y patrimoniales, poner a su disposición el aviso de privacidad, permitirle revocar el consentimiento en cualquier momento y mostrar de forma visible que la información no constituye asesoría de inversión y que las valuaciones son estimaciones informativas, no precios oficiales.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-12. Casos de uso: CU-01, CU-02, CU-09 y CU-10, y los avisos en CU-06 y CU-07. Pantallas: V-02, V-03 y V-11, y los avisos en V-04 a V-06.
- Relación con otros requisitos: reglas RD-11, RD-15 y RD-23; restricciones R-03 y R-11.
- Criterio de aceptación: SRS 3.2, criterios 1 a 4. Detalle: MVP.md 3.3.
- Estado al 18/10/2026: pendiente en parte; faltan los criterios 1, 2 y 4, que dependen de la interfaz (casilla sin marcar, lectura del aviso y avisos visibles).
- Abierto: el plazo de supresión tras la revocación (por decidir con la empresa) y los textos de los avisos y de la casilla de consentimiento.

### 6.4 Área B. Portafolios e intermediarios

#### RF-03 — Gestión de portafolios

- Enunciado (SRS 3.2): «El sistema deberá permitir crear, consultar, modificar y eliminar portafolios identificados por nombre y divisa base.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-03. Caso de uso: CU-03. Pantalla: V-08.
- Relación con otros requisitos: reglas RD-03, RD-08 (solo MXN) y RD-10; exclusión X-06.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle: MVP.md 3.4.
- Estado al 18/10/2026: hecho sin interfaz; falta V-08, con el diálogo de confirmación.

#### RF-25 — Intermediarios

- Enunciado (SRS 3.2): «El sistema deberá permitir a cada usuario registrar y consultar los intermediarios con los que mantiene sus inversiones, identificados por un nombre único dentro de su cuenta.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-25. Caso de uso: CU-04. Pantalla: V-09.
- Relación con otros requisitos: reglas RD-03, RD-09 (los intermediarios no se modifican ni se eliminan) y RD-10; exclusión X-05.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle: MVP.md 3.4.
- Estado al 18/10/2026: hecho sin interfaz; falta V-09.

### 6.5 Área C. Catálogo de instrumentos

#### RF-04 — Catálogo de instrumentos

- Enunciado (SRS 3.2): «El sistema deberá permitir consultar el catálogo de instrumentos disponibles con su clave, nombre y clase de activo; cada emisión de CETES será un instrumento propio, identificado por su clave de emisión (BI seguida de su fecha de vencimiento en formato AAMMDD), con su valor nominal y su fecha de vencimiento.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-04. Casos de uso: CU-08; también en CU-05 y CU-11 (SRS 4.1). Pantalla: V-10.
- Relación con otros requisitos: reglas RD-04 y RD-09; cuatro clases excluyentes (acción, ETF, FIBRA y CETES); suposición S-09.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y catálogo semilla: MVP.md 3.5 y 5.1.
- Estado al 18/10/2026: hecho sin interfaz; falta V-10.
- Adoptado, por confirmar: el prefijo «DEMO» de las claves ficticias y que la consulta del catálogo exija sesión.

#### RF-34 — Emisiones de CETES posteriores a la semilla

- Enunciado (SRS 2.6.1): «Incorporar al catálogo de RF-04 las emisiones de CETES colocadas después de la semilla, con el vencimiento que resulta de su colocación y su plazo publicados en el SIE.» El SRS deja por confirmar, con una emisión real, cómo se deriva la clave.
- Prioridad y fase: diferido; semana del 19 de octubre, la de RF-32 (decidido). Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-32 (fecha de colocación y plazo de cada emisión) y RF-04 (clave de emisión y vencimiento).
- Condiciones: S-09 y S-14 (sin él no se registran compras ni reinversiones de CETES colocados después de la semilla); S-12; D-01 a D-03; R-14.
- Caso de uso: CU-14, Actualizar series del SIE.
- Diseño previsto: la tarea diaria del SIE da de alta las emisiones nuevas (SRS 4.2); no cambia la estructura de la base, porque la tarea inserta el instrumento y la emisión en una misma transacción y la llave del subtipo valida la clave (SRS 4.3).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Abierto: cómo se deriva la clave, y el límite de RD-05 (728 días en el SRS, abierto; el código aplica 730, adoptado, por confirmar), que debe fijarse antes de RF-34. Si se recorta RF-32, RF-34 pasa con él (SRS 2.6.3).

### 6.6 Área D. Transacciones

#### RF-05 — Registro y consulta de transacciones

- Enunciado (SRS 3.2): «El sistema deberá permitir registrar y consultar las transacciones de compra y venta del portafolio, con su intermediario, instrumento, fecha de concertación, cantidad de títulos, precio por título e importe de las comisiones de la operación con su IVA, y calcular con ellos el costo por título de cada compra, como (títulos × precio + importe) / títulos, y el ingreso por título de cada venta, como (títulos × precio − importe) / títulos.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-05. Casos de uso: CU-05 (registro) y CU-06 (consulta). Pantallas: V-06 y V-07.
- Relación con otros requisitos: usa el catálogo (RF-04) y los intermediarios (RF-25); reglas RD-02, RD-06, RD-07, RD-09, RD-10, RD-13, RD-14 y RD-15; restricción R-02 y exclusión X-01 (captura manual).
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y fórmulas: MVP.md 3.6 y 4.3.
- Estado al 18/10/2026: hecho sin interfaz; faltan V-06 y V-07.

#### RF-28 — Saldo no negativo por intermediario

- Enunciado (SRS 3.2): «El sistema deberá rechazar el registro de una transacción que deje negativo, en cualquier fecha, el saldo de un instrumento con un intermediario dentro del portafolio, aunque la posición consolidada sea suficiente.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-28. Caso de uso: CU-12, incluido en CU-05. Pantalla: V-07.
- Relación con otros requisitos: limitado al registro; la modificación y la eliminación pasan a RF-39. Exclusiones X-04 y X-06.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle: MVP.md 3.6.
- Estado al 18/10/2026: hecho sin interfaz; falta mostrar el motivo del rechazo en V-07.

#### RF-23 — Transacciones en más de una divisa

- Enunciado (SRS 2.6.1): «Registrar transacciones en más de una divisa.»
- Prioridad y fase: diferido; semana del 2 de noviembre. Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-03, RF-05, RF-08 a RF-10, RF-32 (FIX diario) y el FIX histórico, que se carga una sola vez desde el SIE al desarrollar RF-23.
- Condiciones: S-10 deja de aplicarse; D-01 a D-03, R-08 y R-15 (carga única del FIX histórico); X-03. El conjunto de referencia del SRS 5.2 se amplía con operaciones en otra divisa. Parte de un MVP que solo admite pesos, y con el FIX solo cubre el dólar.
- Casos de uso: no tiene uno propio; amplía CU-03 y CU-05. Agrega la divisa a V-07 y V-08 (SRS 4.5.2).
- Diseño previsto: tabla `tipo_cambio` (par, fecha, valor y carga, con un solo valor por par y fecha); se sustituyen las restricciones de divisa y se reescribe RD-08; su ficha dirá si la transacción guarda el tipo de cambio (SRS 4.3).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Abierto: quién invoca la carga del FIX histórico, el rol de escritura de la tarea y la escala del tipo de cambio (SRS 4.2 y 4.3). Si se recorta RF-32, RF-23 pasa con él.

#### RF-39 — Modificar y eliminar transacciones

- Enunciado (SRS 2.6.1): «Permitir que el usuario modifique y elimine transacciones registradas, y rechazar la modificación o la eliminación que deje negativo, en cualquier fecha, el saldo de un instrumento con un intermediario dentro del portafolio, como hace RF-28 con el registro.»
- Prioridad y fase: diferido; fecha por fijar en el plan de la fase de refinamiento (abierto). Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-05 (las transacciones que se modifican o eliminan) y RF-28 (la regla que se revalida).
- Condiciones: X-04; RD-09 y RD-10. Mientras no entre, un error de captura solo se corrige eliminando el portafolio con todas sus transacciones.
- Caso de uso: CU-13, que incluye CU-12. Pantalla prevista: «Modificar transacción»; eliminar es un diálogo de confirmación en V-06 (SRS 4.5.2).
- Diseño previsto: reutiliza la regla de saldo de Transacciones (SRS 4.2); la base permite modificar y eliminar transacciones, y RF-28 se revalida con el portafolio bloqueado (SRS 4.3).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar; hoy la API responde 405 a esos métodos.
- Abierto: la fecha, entre una semana de la fase de refinamiento o después de la estadía.

### 6.7 Área E. Posiciones y valuación, con CETES

#### RF-06 — Posición vigente

- Enunciado (SRS 3.2): «El sistema deberá determinar, a una fecha de corte, la posición de cada instrumento del portafolio como la suma de sus saldos con cada intermediario, derivados del historial de transacciones registradas.»
- Prioridad y fase: M; MVP. Objetivo: OE-3. Prueba: CPF-06. Casos de uso: CU-06 y CU-07. Pantallas: V-05 y V-04.
- Relación con otros requisitos: se deriva de RF-05; regla de cálculo del SRS 3.2 (concertación, corte inclusivo, sin efectivo y sin emisiones vencidas); RNF-02; exclusión X-06.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle: MVP.md 3.7.
- Estado al 18/10/2026: hecho sin interfaz; falta V-05. Su ficha detallada en el SRS 3.2 sigue vacía.

#### RF-08 — Valor de mercado y resultado no realizado

- Enunciado (SRS 3.2): «El sistema deberá calcular el valor de mercado y el resultado no realizado de cada posición y del portafolio a una fecha dada, con el costo asignado por costo promedio ponderado dentro de cada intermediario.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-08. Casos de uso: CU-06 y CU-07. Pantallas: V-05 y V-04.
- Relación con otros requisitos: usa RF-06, los precios de RF-07 y la valuación de CETES de RF-26b; exclusión X-03 (sin efectos fiscales); RNF-01.
- Criterio de aceptación: SRS 3.2, criterios 1 a 4. Detalle y fórmulas: MVP.md 3.7 y 4.3.
- Estado al 18/10/2026: hecho sin interfaz; faltan V-05 y V-04. Su ficha detallada en el SRS 3.2 sigue vacía.

#### RF-26a — Vencimiento de los CETES

- Enunciado (SRS 3.2): «El sistema deberá liquidar a su valor nominal, en su fecha de vencimiento, los títulos de cada emisión de CETES que sigan en posición, tratar ese importe como un retiro del portafolio y rechazar transacciones de la emisión con fecha igual o posterior a su vencimiento.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-26a. Casos de uso: CU-05, CU-06 y CU-07. Pantallas: V-05 y V-07.
- Relación con otros requisitos: RF-09 cuenta el retiro; suposición S-14 (sin descontar ISR); regla RD-05.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle: MVP.md 3.7.
- Estado al 18/10/2026: hecho sin interfaz; faltan su presentación en V-05 y el motivo de rechazo en V-07.

#### RF-26b — Valor estimado de los CETES

- Enunciado (SRS 3.2): «El sistema deberá estimar el valor de las posiciones en CETES antes de su vencimiento con P = VN / (1 + r·d/360), donde d son los días naturales por vencer y r la tasa de referencia más reciente, interpolada linealmente a d días.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-26b. Casos de uso: CU-06 y CU-07. Pantallas: V-05 y V-04.
- Relación con otros requisitos: usa las tasas de RF-30; restricción R-14 (rige la última colocación con fecha igual o anterior a la de valuación); regla RD-16; suposiciones S-12 y S-13; RNF-01.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y fórmula: MVP.md 3.7 y 4.3.
- Estado al 18/10/2026: hecho sin interfaz; falta su presentación en V-05 con el rótulo de estimación.
- Abierto: si RF-26b tiene ficha propia en el SRS 3.2.

#### RF-27 — Desglose por intermediario

- Enunciado (SRS 2.6.2): «Presentar, a una fecha de corte, la cantidad de títulos y el valor de mercado de cada instrumento desglosados por intermediario, de modo que su suma coincida con la posición y el valor consolidados.»
- Prioridad y fase: S; semana del 19 de octubre (propuesta, por decidir). Objetivo: OE-3. Prueba: CPF-27 (Definición).
- Depende de: RF-06, RF-08, RF-25 y RF-26b.
- Condiciones: X-05 (sin rendimiento ni riesgo por intermediario); S-07; R-11; X-06.
- Regla que da el enunciado: la suma de los desgloses coincide con la posición y el valor consolidados.
- Caso de uso: CU-16. Pantalla prevista: «Posiciones por intermediario», como pestaña de V-05 (SRS 4.5.2); sus gráficas, con Recharts (SRS 4.2).
- Verificación prevista: CPF-27, con el criterio que se fije al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Abierto: la fecha y la presentación.

#### RF-13 — Distribución por clase de activo

- Enunciado (SRS 2.6.2): «Presentar la distribución del portafolio por clase de activo.»
- Prioridad y fase: S; semana del 19 de octubre (propuesta, por decidir). Objetivo: OE-4. Prueba: CPF-13 (Definición).
- Depende de: RF-04 (clase de activo), RF-06, RF-08 y RF-26b.
- Condiciones: S-09; S-10; R-11 (el peso de los CETES es estimado); X-06.
- Método: el SRS no fija otro que la clasificación por clase de activo de RF-04.
- Caso de uso: CU-17. Pantalla prevista: «Posiciones por clase de activo», como pestaña de V-05 o sección del tablero (abierto, SRS 4.5.2); sus gráficas, con Recharts (SRS 4.2).
- Verificación prevista: CPF-13, con el criterio que se fije al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Abierto: la fecha y la presentación.

### 6.8 Área F. Indicadores y tablero

#### RF-09 — Rendimiento ponderado por tiempo (TWR)

- Enunciado (SRS 3.2): «El sistema deberá calcular el rendimiento ponderado por tiempo (TWR) del portafolio para un periodo determinado.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-09. Caso de uso: CU-07. Pantalla: V-04.
- Relación con otros requisitos: usa los importes de RF-05, la valuación de RF-08 y el retiro de RF-26a; RNF-01.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y fórmula: MVP.md 3.8 y 4.3.
- Estado al 18/10/2026: hecho sin interfaz; falta V-04. Su ficha detallada en el SRS 3.2 sigue vacía.
- Abierto en el SRS, adoptado por el conjunto de referencia y por el código: el factor 1 con denominador 0, la serie en días naturales y el día base (MVP.md 4.3).

#### RF-10 — Máxima caída

- Enunciado (SRS 3.2): «El sistema deberá calcular la máxima caída del rendimiento acumulado ponderado por tiempo del portafolio dentro de un periodo determinado.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-10. Caso de uso: CU-07. Pantalla: V-04.
- Relación con otros requisitos: se mide sobre el índice de RF-09; RNF-01.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y fórmula: MVP.md 3.8 y 4.3.
- Estado al 18/10/2026: hecho sin interfaz; falta V-04. Su ficha detallada en el SRS 3.2 sigue vacía.
- Abierto en el SRS, adoptado por el conjunto de referencia: el índice 1 como primer máximo y la regla de pico y valle.

#### RF-11 — Tablero

- Enunciado (SRS 3.2): «El sistema deberá presentar un tablero con los indicadores calculados y la evolución del valor del portafolio en el tiempo.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-11. Caso de uso: CU-07. Pantalla: V-04.
- Relación con otros requisitos: presenta RF-08 a RF-10 con la serie de RF-09; RNF-01, RNF-02 y RNF-07.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle: MVP.md 3.8.
- Estado al 18/10/2026: pendiente en parte; falta la gráfica (criterio 2), y el criterio 1 está en conflicto con los 2 decimales de RD-13 (sección 3.4).

#### RF-19 — Rendimiento ponderado por dinero (XIRR)

- Enunciado (SRS 2.6.1): «Calcular el rendimiento ponderado por dinero (XIRR) del portafolio.»
- Prioridad y fase: diferido; semana del 19 de octubre. Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-05, RF-08, RF-26a (cada vencimiento es un retiro), RF-26b (CETES al inicio y al final) y los flujos externos de RF-09.
- Condiciones: S-07 (sin saldos iniciales ni traspasos); S-14 (la reinversión se registra como compra); X-05.
- Método, decidido (SRS 2.6.1): base de 365 días; en periodos de menos de un año presenta el rendimiento del periodo sin anualizar, conforme a la disposición 2.A.12 de las normas del CFA Institute que cita el SRS.
- Presentación: sin caso de uso propio; se presentaría en CU-07, en V-04 (abierto).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2. Su ficha fijará qué se muestra si el cálculo no converge y la tolerancia frente al SRS 5.2. Al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.

#### RF-20 — Volatilidad anualizada

- Enunciado (SRS 2.6.1): «Calcular la volatilidad anualizada del portafolio.»
- Prioridad y fase: diferido; semana del 19 de octubre. Objetivo y prueba: la Definición no los asigna.
- Depende de: la serie diaria de rendimientos de RF-09 y la valuación de RF-08 y RF-26b.
- Condiciones: S-09 (cobertura de la semilla); X-05; S-02 (su retraso arrastra a RF-17 y RF-21).
- Método, decidido (SRS 2.6.1): desviación estándar muestral de la serie diaria, anualizada con un factor de 252 días.
- Presentación: se presentaría en CU-07, en V-04 (abierto).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.

#### RF-17 — Índice de Sharpe

- Enunciado (SRS 2.6.1): «Calcular el índice de Sharpe del portafolio con la tasa de CETES a 28 días como tasa libre de riesgo.»
- Prioridad y fase: diferido; semana del 26 de octubre. Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-20, RF-30 y la serie de RF-09; de RF-32, solo si el periodo rebasa la semilla de tasas.
- Condiciones: R-14 (en días sin subasta, la última tasa publicada); D-02; S-05.
- Método, decidido (SRS 2.6.1): con los rendimientos excedentes de cada subperiodo sobre la tasa libre de riesgo.
- Presentación: se presentaría en CU-07, en V-04 (abierto).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar. Si se recorta RF-20, RF-17 pasa con él.

#### RF-14 — Explicación en lenguaje natural

- Enunciado (SRS 2.6.2): «Generar una explicación en lenguaje natural de los indicadores calculados.»
- Prioridad y fase: S; semana del 2 de noviembre (decidido). Objetivo: OE-4. Prueba: CPF-14 (Definición).
- Depende de: los indicadores ya entregados que explica (RF-08 a RF-10, RF-26b y los diferidos disponibles), sin recalcularlos, y RF-12.
- Método, decidido (SRS 2.6.2): plantillas, sin servicio externo de inteligencia artificial. Por eso no tiene costo (R-07), no agrega una segunda interfaz externa (R-08) y no envía cifras a terceros (R-09, retirada).
- Condiciones: R-01 y S-15. Su criterio de aceptación deberá impedir juicios sobre la conveniencia de una inversión, y si la empresa cuenta con una opinión jurídica sobre el art. 225 de la LMV, RF-14 se ajustará a ella.
- Caso de uso: CU-19, que extiende CU-07 en su punto «resultados». Pantalla prevista: una sección del tablero (SRS 4.5.2).
- Verificación prevista: CPF-14, con el criterio que se fije al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Por confirmar con la empresa: si existe esa opinión jurídica.

#### RF-16 — Valor en riesgo histórico

- Enunciado (SRS 2.6.2): «Calcular el valor en riesgo histórico del portafolio.»
- Prioridad y fase: C; semana del 9 de noviembre si hay margen; si no, posterior a la estadía (propuesta, por decidir). Objetivo: OE-4. Prueba: CPF-16 (Definición).
- Depende de: la serie de rendimientos de RF-09 y la valuación de RF-08 y RF-26b.
- Condiciones: S-09 (cobertura de la ventana); S-05; R-10; X-05.
- Método: el SRS no fija la ventana ni el nivel de confianza.
- Presentación: se presentaría en CU-07, en V-04 (abierto).
- Verificación prevista: CPF-16, con el criterio que se fije al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar. Es de los primeros que se recortan, junto con RF-18 (SRS 2.6.3).

#### RF-18 — Comparación contra un índice de referencia

- Enunciado (SRS 2.6.2): «Comparar el rendimiento del portafolio contra un índice de referencia sintético o propio.»
- Prioridad y fase: C; igual que RF-16 (propuesta, por decidir). Objetivo: OE-4. Prueba: CPF-18 (Definición).
- Depende de: RF-09 (mismo periodo y convención), RF-31, y RF-07 o RF-30 para el índice.
- Condiciones: R-05 y R-06 (el histórico del S&P/BMV IPC requiere licencia de S&P Dow Jones Indices); R-01. Durante la estadía el índice es sintético o propio.
- Método: el SRS no fija cómo se construye el índice sintético.
- Presentación: en V-04 (abierto).
- Verificación prevista: CPF-18, con el criterio que se fije al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar. Es de los primeros que se recortan, junto con RF-16.
- Abierto: si se plantea a la empresa la licencia del IPC; solo importa si RF-18 se conserva.

### 6.9 Área G. Datos de mercado y procedencia

#### RF-07 — Precios de cierre sintéticos

- Enunciado (SRS 3.2): «El sistema deberá incorporar los precios de cierre históricos de los instrumentos desde un conjunto de datos semilla sintético, con fecha fija, y señalarlos en la interfaz como datos de demostración.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-07. Casos de uso: CU-11, CU-06 y CU-07. Pantallas: V-04 y V-05.
- Relación con otros requisitos: reglas RD-04, RD-13, RD-17, RD-19 y RD-21; restricciones R-04, R-05 y R-13; exclusión X-07; suposición S-05.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y datos: MVP.md 3.9 y 5.2.
- Estado al 18/10/2026: pendiente en parte; falta el criterio 3, la marca de demostración en V-04 y V-05.
- Desviación por registrar en el SRS: la carga la hace un script SQL, no el componente «Cargas» que describe el SRS 4.2 (MVP.md 3.9).

#### RF-30 — Tasas reales de CETES

- Enunciado (SRS 3.2): «El sistema deberá incorporar, desde un conjunto de datos semilla construido con las series que publica el Banco de México en su Sistema de Información Económica (SIE), las tasas de rendimiento de las subastas primarias de CETES a 28, 91, 182, 364 y 728 días, con el plazo efectivo de cada colocación.»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-30. Caso de uso: CU-11. Sin pantalla propia.
- Relación con otros requisitos: reglas RD-13 y RD-18 a RD-20; restricción R-14; dependencia D-02.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y datos: MVP.md 3.9 y 5.3.
- Estado al 18/10/2026: hecho y verificado.
- Pendiente: confirmar con una segunda fuente la tasa a 28 días del 10/09/2026, la única con una sola fuente que afecta las cifras del SRS 5.2.

#### RF-31 — Procedencia de cada dato

- Enunciado (SRS 3.2): «El sistema deberá registrar, para cada precio y cada tasa almacenados, su fuente, su fecha de carga y su licencia, y mostrar junto a cada dato externo su fuente y la fecha del dato; en el caso de las tasas, «Fuente: Banco de México, https://www.banxico.org.mx».»
- Prioridad y fase: M; MVP. Objetivo: OE-4. Prueba: CPF-31. Casos de uso: CU-06, CU-07 y CU-11. Pantallas: V-04 y V-05.
- Relación con otros requisitos: regla RD-17; restricción R-05; dependencia D-03.
- Criterio de aceptación: SRS 3.2, criterios 1 a 3. Detalle y fuentes: MVP.md 3.9 y 5.5.
- Estado al 18/10/2026: pendiente en parte; faltan los criterios 2 y 3, la línea de fuente junto a cada dato en V-04 y V-05.
- Abierto: la licencia y el nombre de la fuente de la semilla sintética (el código aplica la versión «1», adoptada, por confirmar).

#### RF-32 — Actualización diaria desde el SIE

- Enunciado (SRS 2.6.1): «Actualizar a diario y de forma automática, desde el SIE del Banco de México, las tasas de CETES, las series de plazo del CF107 y el tipo de cambio FIX, en una sola consulta de hasta 20 series; los cálculos leen siempre de la base de datos, nunca del API.»
- Prioridad y fase: diferido; semana del 19 de octubre. Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-30 (series de tasas y de plazo de CETES; la del FIX es nueva) y RF-31.
- Condiciones: R-08, R-14 y R-15; S-12; D-01 a D-03; S-03 (sin servidor, solo se ejecuta con el equipo encendido).
- Alcance decidido: carga también las series de plazo del CF107 y no carga la UDI (SRS 3.1).
- Caso de uso: CU-14, al que da inicio la tarea diaria; el SIE es actor secundario. Sin pantalla.
- Diseño previsto (SRS 4.2): una «Tarea diaria del SIE» y un «Adaptador del SIE»; el *token* viaja solo en el encabezado Bmx-Token.
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2. Además, RNF-05 se verifica de nuevo el 30/10/2026, RNF-08 se prueba también con error y con el límite excedido, y RNF-09 compara lo que almacenan RF-30 y RF-32 (SRS 3.3). Al cierre, AC-09 y AC-10.
- Efecto en el producto: amplía el intervalo de las semillas. Hasta que llegue, no se pueden registrar transacciones posteriores al 14/10/2026 (MVP.md 12.4).
- Estado al 18/10/2026: sin implementar.
- Abierto: el disparador de la tarea, el cliente HTTP, el rol con el que escribe (el rol de la API no puede escribir cargas, precios ni tasas), los valores de origen de las cargas, si se conserva el script SQL de semillas o se sustituye por el componente «Cargas», y la regla RD-21 con la fecha de obtención de cada carga (SRS 3.4.1, 4.2 y 4.3). Si se recorta, pasan con él RF-23 y RF-34.

#### RF-33 — Captura o importación de precios de cierre

- Enunciado (SRS 2.6.1): «Permitir que el usuario capture precios de cierre o los importe de un archivo CSV, por ejemplo los de sus estados de cuenta.»
- Prioridad y fase: diferido; semana del 26 de octubre. Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-04; RF-07 (convivencia con la semilla: en los portafolios de su autor prevalece el precio capturado, que se distingue del de la semilla por su fuente; RD-19); RF-31, y RF-02, porque esos precios son privados de su autor y solo valúan sus portafolios.
- Condiciones: X-01 (solo precios); X-07; R-05; R-12; S-04 y S-05 (solo archivos ficticios durante la estadía).
- Caso de uso: CU-15. Pantalla prevista: «Precios de cierre» (SRS 4.5.2).
- Diseño previsto: el precio de cierre guarda a su autor (SRS 4.3).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Abierto: la importación en CSV contradice la frase «nunca por carga de archivo» del SRS 2.3; debe resolverse antes de la semana del 26 de octubre.

### 6.10 Área H. Simulación

#### RF-21 — Escenarios por Monte Carlo

- Enunciado (SRS 2.6.1): «Simular escenarios del portafolio por el método Monte Carlo.»
- Prioridad y fase: diferido; semana del 26 de octubre. Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-08 y RF-20, porque el modelo es paramétrico; RF-26a y RF-26b si el horizonte incluye CETES.
- Condiciones: R-01 y S-15 (escenario hipotético, no recomendación; se ajusta a la opinión jurídica de la empresa si existe); R-11; S-05.
- Método, decidido (SRS 2.6.1): paramétrico.
- Caso de uso: CU-20. Pantalla prevista: «Escenarios Monte Carlo» (SRS 4.5.2).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar. Si se recorta RF-20, RF-21 pasa con él.

#### RF-22 — Composiciones alternativas

- Enunciado (SRS 2.6.1): «Simular composiciones alternativas del portafolio definidas por el usuario y compararlas con el portafolio real por rendimiento y riesgo, sin que el sistema genere ni sugiera composiciones.»
- Prioridad y fase: diferido; semana del 2 de noviembre. Objetivo y prueba: la Definición no los asigna.
- Depende de: RF-04, RF-08 a RF-10, RF-26a y RF-26b.
- Condiciones: R-01 y S-15 (si la opinión jurídica de la empresa concluye que es asesoría, se elimina o se rediseña); R-11; S-05; X-06.
- Caso de uso: CU-21. Pantalla prevista: «Composiciones alternativas» (SRS 4.5.2).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Abierto: si se guardan las composiciones; si se guardan, se agregan antes al SRS 3.4.1.

### 6.11 Área I. Exportación y otros canales

#### RF-15 — Exportación

- Enunciado (SRS 2.6.2): «Exportar el portafolio y sus transacciones a un archivo.»
- Prioridad y fase: S; semana del 26 de octubre (propuesta, por decidir). Objetivo: OE-3. Prueba: CPF-15 (Definición).
- Depende de: RF-03, RF-05 y RF-25; RF-07, RF-08, RF-26b y RF-31 si incluye valores, precios o tasas.
- Condiciones: R-12; R-05 y D-03 (atribución de las tasas y marca de demostración); X-03.
- Requisito de calidad previsto, decidido: al redactar su ficha se agregará al SRS 3.3 un requisito no funcional de integridad que neutralice fórmulas en el archivo exportado (SRS 2.6.2).
- Caso de uso: CU-18. Pantalla prevista: un botón «Exportar» en V-06 (SRS 4.5.2).
- Verificación prevista: CPF-15, con el criterio que se fije al pasar al SRS 3.2; al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Abierto: la fecha y el formato del archivo.

#### RF-24 — Aplicación móvil

- Enunciado (SRS 2.6.1): «Ofrecer una aplicación móvil con paridad de indicadores.»
- Prioridad y fase: diferido; semanas del 2 y del 9 de noviembre. Objetivo y prueba: la Definición no los asigna.
- Depende de: los indicadores entregados al 1 de noviembre, RF-01, RF-02, RF-12 y RF-31.
- Condiciones: S-06 y R-07 (solo Android o aplicación web progresiva); S-11 y SRS 3.6.1 (resolución móvil abierta). Sin servidor, el teléfono usa la red local, donde instalar una aplicación web progresiva exige HTTPS y una aplicación nativa de Android bloquea por omisión el tráfico sin cifrar.
- Diseño previsto: otro canal para los mismos casos de uso (SRS 4.1), otro cliente de la API (SRS 4.2) y el mismo mapa de pantallas (SRS 4.5.2).
- Verificación prevista: criterio y prueba por definir al pasar al SRS 3.2. Si entra, se verifica por la red local (SRS 3.9.4). Al cierre, AC-10.
- Estado al 18/10/2026: sin implementar.
- Por confirmar con la empresa: Android o aplicación web progresiva frente a iOS; si se exige iOS, RF-24 no cabe en la estadía (S-06). Abierto: si se conserva la resolución móvil de 360 px (SRS 3.6.1).

### 6.12 Propuestas sin requisito en el SRS

Estas capacidades no tienen requisito en el SRS ni en la Definición; no forman parte del alcance vigente y no se evalúan como requisitos (MVP.md 9.6; SRS 2.5.2 y 3.4.1):

| Capacidad | Situación |
|---|---|
| Saldo inicial y traspasos de títulos entre intermediarios | Rige S-07. Agregar tipos de transacción, declarar una exclusión o fijar una fecha está abierto. |
| Eventos corporativos (dividendos, distribuciones de FIBRA y divisiones de acciones) | El SRS 3.4.1 dice «No se guardan eventos corporativos», con esa decisión abierta. |
| Recuperar o cambiar la contraseña | Sin requisito. S-04 advierte que probablemente haría falta con datos reales. |
| Límite de intentos de inicio de sesión | Sin requisito. |
| Rectificación de datos (derechos ARCO) | Cómo se rectifica mientras RD-09 impida editar está abierto (SRS 3.4.7). |
| Inicio de sesión con Microsoft Entra ID | Sin requisito; no está en la Definición ni en el SRS 3.5. |
| HTTPS y cifrado en tránsito | Sin requisito mientras no haya servidor; S-03 prevé agregarlos al SRS 3.3 si lo hay. |

La supresión de los datos al concluir el bloqueo no está en esta lista porque el SRS sí la exige: no tiene un RF propio, pero la pide la regla RD-23 (SRS 3.4.7; sección 8.3), con un plazo por confirmar con la empresa. Ningún componente del SRS 4.2 la ejecuta (abierto, SRS 4.3), y el MVP solo bloquea la cuenta (MVP.md 3.3).

La recomendación que consta en el registro de decisiones es tratar el saldo inicial, los traspasos, los eventos corporativos y la recuperación o el cambio de contraseña como requisitos posteriores a la estadía, con la recuperación de contraseña antes de usar datos reales, y excluir Microsoft Entra ID salvo que la empresa lo exija. No hay decisión.

---

## 7. Requisitos no funcionales

### 7.1 Marco

- Modelo: ISO/IEC 25010:2023. Cada requisito atiende una subcaracterística, salvo RNF-03, que atiende dos; es singular y verificable y enuncia su condición, la propiedad observable, la métrica y el valor. Un umbral sin base queda pendiente de medir la línea base, con responsable y fecha (SRS 3.3).
- Calendario: RNF-01 a RNF-05 se verifican con el MVP, a más tardar el 18/10/2026; los demás, del 23/10 al 13/11/2026. Cada uno se prueba con el CPNF del mismo número, y el resultado y la fecha se guardan en el registro de resultados como evidencia del SRS 3.9.
- Aceptación: AC-03 cubre RNF-01; AC-02, RNF-02 a RNF-05, y AC-09, RNF-06 a RNF-12 y RNF-05 de nuevo si se entrega RF-32 (SRS 3.9.2 y 3.9.4).
- Métodos de verificación (SRS 5.1): inspección (revisión del código o la configuración), análisis (razonamiento sobre el diseño o datos existentes), demostración (ejecución observada) y prueba (ejecución automatizada con resultado esperado).

### 7.2 Catálogo

| ID | Característica (ISO/IEC 25010:2023) | Qué exige (SRS 3.3) | Métrica y valor objetivo | Método y prueba | Fecha de verificación | Estado al 18/10/2026 |
|---|---|---|---|---|---|---|
| RNF-01 | Adecuación funcional: corrección funcional | Cada importe, TWR y máxima caída del SRS 5.2 dentro de la tolerancia de OE-5 respecto del valor resuelto de forma independiente | Diferencia absoluta máxima: ≤ 0.01 en importes; ≤ 0.001 puntos porcentuales en rendimiento y máxima caída | Prueba CPNF-01: pytest compara sin redondear las cifras del motor con las del SRS 5.2 congelado y genera la tabla de diferencias | 18/10/2026 | Pasa en el motor (27 pruebas) y por la API desde la base, sin red (3); falta guardar la tabla de diferencias |
| RNF-02 | Adecuación funcional: corrección funcional | Cada cifra idéntica, dígito por dígito, en todas las vistas y en cada consulta repetida, sin cambios en los datos | Cifras distintas para el SRS 5.2: 0 | Demostración CPNF-02: comparar como texto, con capturas, el tablero y las posiciones, y repetir cada consulta | 18/10/2026 | La comparación automática por la API pasa (17 pruebas); la demostración con capturas necesita V-04 y V-05 |
| RNF-03 | Seguridad: confidencialidad e integridad | Sin sesión o con sesión ajena, rechazar sin consultar, registrar, modificar ni eliminar nada y sin revelar si la información existe | Solicitudes aceptadas: 0; respuestas que distinguen lo ajeno de lo inexistente: 0 | Prueba CPNF-03: con dos usuarios, recorrer el esquema OpenAPI sin sesión y con sesión ajena | 18/10/2026 | Pasa |
| RNF-04 | Seguridad: confidencialidad | Ninguna contraseña legible en la base, sus respaldos, los registros ni las respuestas; forma no reversible, distinta por cuenta y con un costo no menor que el mínimo de OWASP | Contraseñas legibles: 0; cuentas con igual valor almacenado: 0; parámetros de costo bajo el mínimo: 0 (Argon2id: m ≥ 19 MiB, t ≥ 2, p = 1) | Prueba CPNF-04, con un respaldo de pg_dump | 18/10/2026 | Pasa |
| RNF-05 | Seguridad: confidencialidad | Ninguna credencial vigente (de la base, el *token* del SIE o la clave de las sesiones) en el historial del repositorio, los archivos del navegador, las direcciones de las solicitudes ni los registros | Apariciones de una credencial que todavía autentica, por lugar: 0 | Inspección CPNF-05: búsqueda del valor vigente de cada credencial en todo el historial, la compilación del cliente y los registros, con gitleaks como complemento | 18/10/2026 y 30/10/2026 (con RF-32) | No consta su ejecución; `backend/.env` está excluido del control de versiones y ningún commit lo incluye |
| RNF-06 | Eficiencia de desempeño: comportamiento temporal | Con el volumen de referencia, en el equipo de desarrollo y un navegador del SRS 3.5, el tablero completo en a lo más T segundos | Percentil 95 del tiempo hasta que el último indicador y la gráfica son visibles, en 30 cargas con caché vacía (percentil, número de cargas y caché, abiertos). T se fija tras medir la línea base (responsable: Ramon; 30/10/2026). Volumen de referencia por fijar antes del 23/10/2026 | Prueba CPNF-06: un script siembra el volumen y Playwright carga y cronometra el tablero; se registran además los picos de procesador y memoria, que fijan los mínimos del SRS 3.6.2 y 3.6.3 | 06/11/2026 | Sin valor objetivo todavía |
| RNF-07 | Capacidad de interacción: autodescriptividad | Junto a cada indicador, su unidad y su fecha de corte o periodo, y acceso a su definición sin salir de la pantalla | Indicadores con unidad, fecha o periodo y definición, por pantalla: 100 %; definiciones distintas del glosario del SRS 1.3: 0 | Demostración CPNF-07: lista de verificación por indicador y pantalla, en una sesión nueva y con capturas | 23/10/2026; su aceptación cae en AC-09 | Por verificar; la tabla de términos del SRS 1.3 está vacía |
| RNF-08 | Fiabilidad: tolerancia a fallos | Si la fuente de tasas falla o bloquea el *token*, seguir calculando y presentando con las últimas tasas almacenadas | Pruebas del motor y del tablero aprobadas sin la fuente: 100 %; consultas a la fuente durante un cálculo: 0 | Prueba CPNF-08: CPNF-01 y los casos de RF-11 sin red, con un sustituto de la fuente que falla si se invoca; con RF-32, también error y límite excedido | 30/10/2026 | Adelantado en el MVP: CPNF-01 corre sin red |
| RNF-09 | Compatibilidad: interoperabilidad | Registrar cada observación de la fuente de tasas con el valor, la unidad y la fecha publicados, sin registrar como valor las observaciones sin dato | Observaciones distintas de una descarga independiente: 0; observaciones sin dato registradas como valor: 0 | Prueba CPNF-09: comparar lo que almacenan RF-30 y RF-32 con la exportación de cada serie del sitio del SIE | 30/10/2026 | Por verificar |
| RNF-10 | Mantenibilidad: modularidad | Agregar, activar o desactivar una fuente de precios o de tasas sin modificar el motor ni sus pruebas contra el SRS 5.2 | Archivos del motor o de sus pruebas modificados: 0; casos de CPNF-01 fallidos: 0 | Análisis CPNF-10: diferencias de la carpeta del motor al agregar un adaptador de una fuente ficticia y desactivarlo por configuración (X-07), con CPNF-01 aprobado | 06/11/2026 | Adelantado en el MVP: el motor está aislado en su carpeta y lee precios y tasas solo por su interfaz de datos de mercado |
| RNF-11 | Flexibilidad: adaptabilidad | En cada navegador del SRS 3.5 y cada resolución del SRS 3.6.1, cada pantalla completa y operable, sin desplazamiento horizontal ni contenido recortado | Pantallas con desplazamiento horizontal, contenido recortado o funciones incompletas, por navegador y resolución: 0 | Demostración CPNF-11: recorrido de cada pantalla en Chromium y Firefox y en el modo adaptable de DevTools, con capturas fechadas | 13/11/2026 | Por verificar |
| RNF-12 | Flexibilidad: instalabilidad | Siguiendo solo el manual técnico, en un equipo limpio con cada plataforma del SRS 3.6.2, instalar, restaurar la base entregada y reproducir las cifras del SRS 5.2 | Pasos ajenos al manual: 0; cifras distintas del SRS 5.2: 0 | Demostración CPNF-12: instalación en Windows Server 2025 y Ubuntu Server 24.04 LTS limpios, con registro fechado y CPNF-01; en GitHub Actions si alcanzan los minutos gratuitos (si no, abierto) | 13/11/2026 | Por verificar |

### 7.3 Características declaradas no aplicables

Según el SRS 3.3:

- Protección (*safety*): no aplica. Ninguna salida de la plataforma pone en peligro la vida, la salud, la propiedad o el medio ambiente: no controla procesos físicos, no ejecuta órdenes (R-02) y no recomienda inversiones (R-01). El riesgo de una cifra errónea (R-10) es de corrección funcional y lo atienden RNF-01, RNF-02 y el SRS 5.2.
- Compatibilidad, coexistencia: no se especifica en esta versión, porque durante la estadía no hay entorno de operación. Si hay servidor, el SRS 3.6.2 identificará los productos con que lo comparte y se agregará el requisito.

### 7.4 Requisitos de calidad previstos o en discusión

- Integridad de la exportación (decidido): al redactar la ficha de RF-15 se agregará al SRS 3.3 un requisito que neutralice fórmulas en el archivo exportado (SRS 2.6.2).
- Con servidor de producción: si S-03 deja de cumplirse, el SRS 3.3 incorporará requisitos de cifrado en tránsito y de respaldo (SRS 2.5.1). Decisión vigente: sin servidor durante la estadía.
- Accesibilidad (abierto): el SRS 3.3 no tiene un requisito de accesibilidad; WCAG 2.2 AA es una meta de diseño (SRS 4.5.1). Según el registro de decisiones, la propuesta es agregar un RNF-13 verificable con axe, Playwright, NVDA y el script de contraste, a más tardar el 13 de noviembre; no hay decisión.
- Parámetros de RNF-06 y plan alterno de RNF-12 (abierto): fijar el volumen, el percentil, el número de cargas y la caché antes del 23/10/2026, y qué hacer si no alcanzan los minutos de GitHub Actions.

---

## 8. Requisitos de datos

### 8.1 Principios

Según el SRS 3.4:

- Se guardan solo hechos: lo que captura el usuario y lo que publican las fuentes. El motor único deriva lo demás (SRS 3.4.3; RNF-02).
- La posición no se captura ni se almacena: se deriva del historial de transacciones según su fecha de concertación, incluidas las de la fecha de corte (RF-06). El saldo con un intermediario se deriva dentro de cada portafolio (RF-28; X-06).
- No se guardan importes, costos, valores, indicadores ni la valuación o la liquidación de los CETES.
- El modelo entidad-relación (SRS 4.3) y el diccionario de datos (SRS 4.4) se derivan del SRS 3.4 y solo pueden contener entidades nombradas ahí.

### 8.2 Entidades

| Entidad (SRS 3.4.1) | Información | Requisitos |
|---|---|---|
| Usuario (cuenta) | Correo, contraseña solo en forma no reversible y estado (activa o bloqueada). Ningún otro dato de identificación (LFPDPPP, art. 12). | RF-01; RF-02; RF-12 |
| Consentimiento y versión del aviso de privacidad | Momento, medio y versión del aviso de cada otorgamiento y revocación; cada versión del aviso, con su texto y su vigencia. | RF-12; R-03 |
| Portafolio | Usuario, nombre y divisa base; sin efectivo, posiciones ni indicadores. | RF-03 |
| Intermediario | Usuario y nombre tal como se capturó. | RF-25 |
| Instrumento | Clave, nombre, divisa y clase de activo (acción, ETF, FIBRA o CETES); los que no son CETES, con clave ficticia y marca de demostración. | RF-04; RF-07; RF-13; S-09 |
| Emisión de CETES | Instrumento con clave de emisión, vencimiento y valor nominal de 10.00 pesos. | RF-04; RF-26a; RF-26b |
| Transacción | Portafolio, intermediario, instrumento, tipo (compra o venta; ampliable por S-07, abierto), fecha de concertación, títulos, precio por título, importe de las comisiones con su IVA y momento de registro. | RF-05; S-07; S-08 |
| Fuente de datos y licencia, por versión | Nombre, dirección, si sus datos son de demostración; por versión de sus términos: usos permitidos, obligación de suprimir y atribución. | RF-07; RF-31; R-05; D-03 |
| Carga de datos | Fuente, versión de la licencia, origen (semilla, tarea diaria, carga única del FIX histórico o captura), fechas de obtención (abierto) e incorporación, intervalo, resultado, observaciones incorporadas y omitidas, y valores sustituidos. | RF-30; RF-31; RNF-09 |
| Precio de cierre | Instrumento, fecha, precio por título y carga. | RF-07; RF-08; R-13 |
| Tasa de referencia | Plazo nominal, fecha de colocación, valor y unidad publicados, plazo efectivo en días y carga. | RF-26b; RF-30; RNF-09; D-02 |

Implementación en el MVP: 13 tablas en `backend/02_crear_esquema.sql`, con cifras `numeric` cuya escala controlan restricciones de la base, zona horaria de la Ciudad de México y un rol de privilegios mínimos para la API (MVP.md 7.3). Hoy el esquema solo admite el origen «semilla» en las cargas.

### 8.3 Reglas de los datos

| ID | Regla, en breve (SRS 3.4.4 a 3.4.7) | Origen |
|---|---|---|
| RD-01 | Cada portafolio, intermediario y consentimiento pertenece a un solo usuario; cada transacción, al usuario de su portafolio. | RF-02; RNF-03 |
| RD-02 | El portafolio y el intermediario de una transacción son del mismo usuario; no se elimina información de la que otra dependa, salvo por RD-10, RD-23 y RD-24. | RF-05; RF-25; RF-31 |
| RD-03 | Sin distinguir mayúsculas ni espacios al inicio o al final, el correo es único en el sistema, y los nombres de intermediario y de portafolio, en la cuenta. | RF-01; RF-03; RF-25 |
| RD-04 | Cada clave del catálogo es única; la de una emisión corresponde a su vencimiento, y ninguna emisión tiene precios de cierre. | RF-04; RF-07; RF-26b |
| RD-05 | Ninguna transacción de CETES está a más de 728 días naturales de su vencimiento (abierto: si se admiten además los días entre la subasta y la colocación). | RF-26b; RF-30; S-12 |
| RD-06 | Cantidades, precios, valor nominal y plazos mayores que cero; el sentido lo da el tipo de transacción. | RF-05; X-04 |
| RD-07 | La fecha de una transacción no es posterior a su registro y cae en el intervalo que cubren los datos de mercado. | R-02; S-09 |
| RD-08 | La divisa del instrumento es la divisa base del portafolio; en el MVP, solo el peso. | RF-03; S-10 |
| RD-09 | Los usuarios no modifican el catálogo ni los datos de mercado, ni modifican o eliminan intermediarios; en el MVP tampoco transacciones, salvo al eliminar su portafolio. | RF-05; RF-25; RF-28; RF-39 |
| RD-10 | Al eliminar un portafolio, con confirmación expresa, se eliminan sus transacciones y se conservan los intermediarios. | RF-03; RF-25 |
| RD-11 | Ninguna cuenta existe sin su consentimiento registrado; los registros de consentimiento y revocación no se modifican ni se eliminan, salvo por RD-23. | RF-12; R-03 |
| RD-12 | Todo número se guarda, se calcula y se intercambia en decimal, nunca en punto flotante binario, con al menos 28 dígitos al calcular. | RNF-01; RNF-02 |
| RD-13 | Escalas: títulos enteros; precios con 7 decimales; valor nominal con 2; tasas con 5 decimales en por ciento anual (por confirmar en la API); plazos en días; al presentarse, importes y por cientos con 2 decimales. | RF-05; RF-26b; RNF-01; RNF-09 |
| RD-14 | Un valor con más decimales que su escala o una fecha inválida se rechaza sin redondear; todo dato aceptado, salvo la contraseña, se recupera sin alteración. | RF-05; RNF-01; RNF-04 |
| RD-15 | Fechas de operación, cierre, colocación y vencimiento sin hora; momentos de registro y carga con zona horaria; rige la hora de la Ciudad de México. | RF-05; RF-12; RF-26a; RF-31 |
| RD-16 | Solo se redondea al presentar una cifra y al obtener el precio de los CETES, a 7 decimales, con la mitad alejándose de cero. | RNF-01; RNF-02; RF-26b |
| RD-17 | Cada precio, tasa y tipo de cambio proviene de una sola carga. | RF-31; R-05 |
| RD-18 | Cada tasa lleva su plazo nominal y su plazo efectivo; sin plazo efectivo no se carga. | RF-26b; RF-30; RF-32 |
| RD-19 | A lo más un precio por instrumento, fecha y fuente (desde RF-33, también por autor), una tasa por plazo y fecha de colocación y un tipo de cambio por par y fecha. Desde RF-33, el precio capturado es privado de su autor y prevalece en sus portafolios. | RF-02; RF-07; RF-30; RF-31; RF-33; RNF-02 |
| RD-20 | Una observación sin dato se cuenta como omitida y no se guarda como valor (por confirmar cómo llega por la API); una tasa no se rechaza por tener fecha de colocación posterior a su carga. | RNF-09; R-14 |
| RD-21 | Si una carga posterior trae otro valor para la misma serie y fecha, lo sustituye y registra el anterior (abierto: o guardar versiones), salvo en el intervalo de la semilla, que solo cambia con una versión nueva del SRS 5.2. | RNF-09; RF-31; RNF-01 |
| RD-22 | No se depuran por antigüedad las transacciones de una cuenta activa. | RF-06; RF-09; RF-10 |
| RD-23 | Al revocar el consentimiento, la cuenta y su información se bloquean de inmediato y se suprimen al concluir el bloqueo, que dura hasta la prescripción de las responsabilidades del tratamiento (plazo por confirmar con la empresa). | RF-12; LFPDPPP |
| RD-24 | Los datos de mercado se conservan mientras su licencia lo permita y pueden suprimirse por fuente o por carga; las cifras que los usaban se presentan como no calculables (abierto). | RF-31; R-05; X-07 |

Estado en el MVP: el bloqueo inmediato al revocar está implementado; la supresión al concluir el bloqueo y el ejercicio de los derechos ARCO quedan fuera del MVP (MVP.md 8 y 9.6); para RD-24, la API responde con el código `cifra_no_calculable` (MVP.md 7.5).

### 8.4 Fuentes de datos de mercado

En el MVP el diseño es híbrido (detalle en MVP.md 5):

| Dato | Fuente | Licencia y atribución | Requisitos |
|---|---|---|---|
| Precios de cierre de acciones, ETF y FIBRA | Semilla sintética de demostración con fecha fija: 71 precios del 10/09 al 14/10/2026 de tres instrumentos ficticios | Licencia propia adoptada, por confirmar; se muestran como «Datos de demostración» | RF-07; R-04; R-05; R-13 |
| Tasas de CETES | Reales, del cuadro CF107 del SIE del Banco de México: 32 colocaciones de 28 a 728 días, con su plazo efectivo | Reproducción permitida citando «Fuente: Banco de México, https://www.banxico.org.mx» | RF-30; D-02; D-03 |
| Catálogo | Semilla: tres instrumentos ficticios con prefijo DEMO y cuatro emisiones reales de CETES | — | RF-04; S-09 |

La aceptación usa precios sintéticos marcados, tasas reales y la valuación de los CETES como estimación informativa; no evalúa la exactitud de los precios ni la cercanía de esa valuación al mercado secundario (SRS 3.9; por confirmar con el líder).

Evolución de los datos (SRS 2.6.1, 2.4.7, 4.2 y 4.3):

| Requisito | Qué agrega | Fecha objetivo |
|---|---|---|
| RF-32 | Tasas de CETES, series de plazo del CF107 y tipo de cambio FIX, a diario desde el SIE, en una sola consulta de hasta 20 series | Semana del 19 de octubre |
| RF-34 | Emisiones de CETES colocadas después de la semilla | Semana del 19 de octubre |
| RF-33 | Precios de cierre que captura o importa el usuario, privados de su autor | Semana del 26 de octubre |
| RF-23 | Tipo de cambio FIX histórico, cargado una sola vez desde el SIE | Semana del 2 de noviembre |
| RF-18 | Índice de referencia sintético o propio | Igual que RF-16 (propuesta) |
| X-07 | Fuentes comerciales de precios (Twelve Data, EODHD o Marketstack) | Nunca mientras PluriOne no contrate su licencia; la arquitectura las admite como un adaptador desactivado por configuración (RNF-10) |

### 8.5 Cambios previstos del modelo

| Requisito | Cambio previsto (SRS 4.3) |
|---|---|
| RF-32 y RF-23 | Tabla `tipo_cambio`: par, fecha, valor (escala por confirmar) y carga, con un solo valor por par y fecha. RF-23 sustituye las restricciones de divisa y reescribe RD-08. La tarea escribe con un rol propio (abierto). |
| RF-33 | El precio de cierre guarda a su autor, y la llave de RD-19 lo incluye. El rol de la API necesitaría escribir cargas y precios. |
| RF-34 | Sin cambio de estructura. |
| RF-39 | La base permite modificar y eliminar transacciones; RF-28 se revalida con el portafolio bloqueado. |
| RF-22 | Si sus composiciones se guardan (abierto), se agregan antes al SRS 3.4.1. |

### 8.6 Frecuencia de uso y acceso

El usuario escribe de forma esporádica. Cada consulta del tablero lee las transacciones hasta la fecha de corte y el último precio o tasa con fecha igual o anterior a cada valuación. Las semillas se cargan al instalar; desde RF-32, las tasas y los tipos de cambio, a diario. Solo las cargas escriben datos de mercado, y los cálculos nunca leen la fuente externa (SRS 3.4.8; R-15; RNF-08).

---

## 9. Experiencia de usuario

### 9.1 Principios

Según el SRS 2.3 y 4.5.1:

- El tablero debe entenderse «en frío», sin recordar sesiones anteriores; es el punto de entrada habitual (SRS 2.2).
- Cada indicador va con su unidad, su fecha de corte o periodo y su definición, sin salir de la pantalla (RNF-07).
- El cliente no redondea, suma, promedia ni convierte cifras: solo agrega separadores de miles, el símbolo de pesos y la unidad, y reordena las fechas. Toda cifra llega de la API como texto, ya calculada por el motor.
- Formato: coma de miles y punto decimal («-$218.56», «1.00 %»); fechas DD/MM/AAAA; sin notación abreviada. La única conversión de una cifra a número en el cliente sería la altura de cada punto de la gráfica (abierto, como excepción documentada de RD-12).
- Textos en español de México, trato de tú y lenguaje llano; un término por concepto («transacción», no «operación»); siglas desarrolladas en su primera aparición; nunca códigos internos.
- Ningún texto, color o icono califica una inversión o sugiere operar; no hay indicadores «en vivo», contadores animados ni recarga automática (R-01; R-02; R-13). El botón dice «Registrar transacción», nunca «Comprar» ni «Vender».
- Avisos permanentes, sin botón de cerrar, en el tablero, las posiciones y las transacciones. La propuesta los pone antes de las cifras, con la ubicación por decidir (SRS 4.5.1). Textos propuestos, por decidir: «La información de este sistema no constituye asesoría de inversión.» y «Las valuaciones son estimaciones informativas, no precios oficiales, y no sustituyen el estado de cuenta de tu intermediario.»
- Ningún dato se distingue solo por el color: ganancia y pérdida llevan signo, los enlaces van subrayados, los errores llevan icono y texto, y las series de las gráficas se distinguen por el trazo.

### 9.2 Guía de estilo

- Base: CDS (Coinbase Design System) con un tema propio, la «opción B» del SRS 4.5.1. Se adoptan la estructura y los nombres de los tokens de CDS, su escala de espacio de base 8 px, sus radios y puntos de corte, su escala tipográfica con la fuente Inter autoalojada y un subconjunto sobrio de componentes con todos sus textos en español.
- No se usan: los temas de CDS, cuyo primario es el azul de Coinbase; logotipos, ilustraciones ni glifos de marca; las gráficas de CDS (se usa Recharts 3.10.1); los componentes de venta, atracción o tiempo real, ni los que chocan con criterios de WCAG (Toast, Calendar y DatePicker). Coinbase solo se nombra en la página de avisos de licencias.
- Paleta propia para los modos claro y oscuro, según la preferencia del sistema operativo, con mínimos de contraste de 4.5:1 para texto y de 3:1 para bordes, iconos, foco y líneas de las gráficas. Los colores son una propuesta, medidos con la fórmula de WCAG pero aún no vistos en un navegador (por confirmar).
- Estado: CDS no está instalado. Para adoptar la opción B falta bajar React a la 19.1.10, que npm resuelva las dependencias sin forzarlas (por confirmar en una rama a más tardar el 23/10/2026), que compile con Vite 8 y retirar las reglas que dejó la plantilla de Vite. Mientras tanto, las vistas del MVP se escriben con componentes propios delgados, con HTML nativo y los mismos nombres de tokens.
- Abiertos: el identificador del tema o el uso de una identidad visual de PluriOne, si existe; el juego de iconos; los textos de varios componentes.

### 9.3 Accesibilidad

- Meta de diseño: nivel AA de WCAG 2.2. No es un requisito verificable, porque el SRS 3.3 no tiene un requisito de accesibilidad; agregarlo está abierto (SRS 4.5.1; sección 7.4).
- Reglas que ya fija la guía (SRS 4.5.1): cada pantalla funciona a 320 px CSS (criterio 1.4.10); objetivos de clic de al menos 24 × 24 px (criterio 2.5.8); un solo h1 por pantalla y el foco en el h1 tras cada navegación; enlace «Saltar al contenido»; foco siempre visible; gráfica con resumen textual visible, tabla alterna, recorrido con las flechas y sin animación.
- La sesión dura 480 minutos sin aviso ni renovación; cómo se atiende el criterio 2.2.1 está abierto (SRS 4.5.2).

### 9.4 Pantallas

Rutas, menú y transiciones del SRS 4.5.2 son una propuesta de diseño (abierto). Las operaciones de la API que usa cada pantalla salen del código del servidor.

| Id | Pantalla | Requisitos | Sesión |
|---|---|---|---|
| V-01 | Inicio de sesión | RF-01; RF-12 | No |
| V-02 | Registro, con la casilla de consentimiento sin marcar y el aviso en un diálogo | RF-01; RF-12 | No |
| V-03 | Aviso de privacidad | RF-12 | Con sesión y sin ella |
| V-04 | Tablero: selector de portafolio y periodo, cuatro indicadores con su definición, gráfica con su tabla, procedencia, marca de demostración y avisos | RF-11; RF-06; RF-08 a RF-10; RF-26a; RF-26b; RF-07; RF-12; RF-31; RNF-07 | Sí |
| V-05 | Posiciones al corte | RF-06; RF-08; RF-26a; RF-26b; RF-07; RF-12; RF-31 | Sí |
| V-06 | Transacciones | RF-05; RF-12 | Sí |
| V-07 | Registrar transacción (formulario guiado) | RF-05; RF-26a; RF-28; RF-04; RF-25; RF-02 | Sí |
| V-08 | Portafolios | RF-03; RF-02 | Sí |
| V-09 | Intermediarios | RF-25; RF-02 | Sí |
| V-10 | Catálogo | RF-04 | Sí (por confirmar) |
| V-11 | Cuenta, con la revocación del consentimiento | RF-12 | Sí |
| V-12 | No encontrado: lo ajeno se muestra igual que lo inexistente | RF-02; RNF-03 | Con sesión y sin ella |

Pantallas de la fase de refinamiento (SRS 4.5.2): «Modificar transacción» (RF-39), «Posiciones por intermediario» (RF-27), «Posiciones por clase de activo» (RF-13), «Escenarios Monte Carlo» (RF-21), «Composiciones alternativas» (RF-22) y «Precios de cierre» (RF-33). RF-15 es un botón «Exportar» en V-06; RF-14, una sección del tablero; RF-23 agrega la divisa a V-07 y V-08, y RF-24 sería otro cliente con el mismo mapa. El menú pasa de 8 a 10 elementos (abierto si se agrupan).

Menú principal propuesto, en este orden: Tablero, Posiciones, Transacciones, Portafolios, Intermediarios, Catálogo, Cuenta y Aviso de privacidad. No hay lista global de transacciones, porque los portafolios no se consolidan (X-06).

Resoluciones (SRS 3.6.1): escritorio desde 1280 × 720 px CSS; en móvil, 360 px de ancho, abierto (la recomendación del SRS es quitarla salvo que entre RF-24 y, si entra, usar 320 px CSS).

### 9.5 Verificación de la experiencia de usuario

| Qué se verifica | Cómo | Cuándo |
|---|---|---|
| Contraste de los colores | Análisis con el script de contraste, que aplica la fórmula de WCAG | 17/10/2026 y en la prueba de CDS, a más tardar el 23/10/2026 |
| Cifras idénticas en las vistas | Demostración (RNF-02) | 18/10/2026 |
| Unidad, fecha y definición de cada indicador | Demostración (RNF-07) | 23/10/2026 |
| Resoluciones | Demostración en Chromium y Firefox a 1280 × 720 y 320 px CSS, y a 360 px si se conserva (RNF-11) | 13/11/2026 |
| Teclado, lector de pantalla y revisión automática | Demostración con teclado y NVDA, y prueba con axe | Por decidir con el requisito de accesibilidad |
| Idioma y marca | Inspección: ningún texto en inglés ni color azul de Coinbase | En la prueba de CDS |
| Recorrido de los imprescindibles | Demostración a 1280 px con capturas fechadas (AC-04) | Con la entrega del MVP |

### 9.6 Estado al 18/10/2026

Ninguna de las 12 pantallas está construida; `frontend/src/` solo tiene la página de prueba de conexión con la API. Por eso RF-07, RF-11, RF-12 y RF-31 están pendientes en parte y AC-04 está pendiente (MVP.md 12). Si las pantallas no quedan antes de la revisión, rige S-02.

---

## 10. Arquitectura y tecnologías

### 10.1 Estructura

Sistema cliente-servidor con dos contenedores, el cliente web (React 19 y Vite 8) y el servidor (Python 3.13 con FastAPI), y un componente externo, PostgreSQL 18. Todo cálculo ocurre en el servidor, con el motor único, y el cliente solo presenta. Durante la estadía los tres corren en el equipo de desarrollo (SRS 4.2; MVP.md 7.1).

### 10.2 Decisiones que sostienen el diseño

Según el SRS 4.2:

1. Motor único: solo el motor deriva cifras; las rutas y las vistas las presentan sin recalcularlas ni guardarlas (RNF-01; RNF-02).
2. Adaptadores de datos: las cargas reciben las observaciones por una interfaz de fuente de datos, y el motor lee lo almacenado solo por una interfaz de datos de mercado. Así, una fuente que falla no detiene el cálculo (RNF-08), y cambiar de fuente no toca el motor (RNF-10; X-07).
3. Aritmética decimal: cada cálculo fija, en un contexto local, 28 dígitos y la mitad alejándose de cero; las cifras viajan como texto (RD-12; RD-16).
4. Autorización por propietario: se filtra por el usuario vigente lo que pertenece a una cuenta, y cada solicitud con sesión comprueba que la cuenta siga activa (RF-02; RNF-03; RD-23).
5. El *token* del SIE no llega al cliente: vive solo en la configuración del servidor y viaja en el encabezado Bmx-Token (RNF-05).

Los registros de decisión (ADR) de la interfaz de datos, la aritmética, las gráficas y CDS están pendientes: `docs/adr/` no existe (README, «Índice del paquete»).

### 10.3 Componentes

- MVP: los componentes del servidor (rutas de la API, cuentas y consentimiento, autorización, portafolios, transacciones, consultas, motor, acceso a datos y configuración) están implementados; el cliente web está pendiente. El componente «Cargas» y el adaptador de la semilla que describe el SRS 4.2 no existen en Python: la carga la hace un script SQL, una desviación por registrar en el SRS (MVP.md 7.1).
- Fase de refinamiento (SRS 4.2):

| Componente | Responsabilidad | Requisitos |
|---|---|---|
| Modificación y eliminación de transacciones | Reutiliza la regla de saldo de Transacciones | RF-39 |
| Captura de precios | Escribe por las cargas precios privados de su autor, que prevalecen en sus portafolios sin cambiar el motor (importación en CSV, abierta) | RF-33 |
| Exportación | Genera el archivo del portafolio y sus transacciones, con su atribución (formato abierto) | RF-15 |
| Explicación con plantillas | Describe los resultados del motor sin recalcularlos, sin servicio externo y sin juicios sobre la conveniencia de invertir | RF-14 |
| Tarea diaria del SIE | Cada día, con el equipo encendido (disparador abierto), invoca las cargas con el adaptador del SIE y da de alta las emisiones nuevas | RF-32; RF-34 |
| Adaptador del SIE | Consulta diaria de hasta 20 series y carga única del FIX histórico; el *token* va solo en el encabezado (cliente HTTP abierto) | RF-23; RF-32; RF-34; RNF-05; RNF-08; RNF-09 |
| Adaptador de otra fuente de precios | Desactivado por configuración; en la estadía es el adaptador ficticio de RNF-10 | RNF-10; X-07 |

RF-13, RF-16 a RF-22 y RF-27 ampliarán el motor y las vistas, con la misma biblioteca de gráficas del tablero. RF-24 sería otro cliente de la API (SRS 4.2).

### 10.4 API

API REST con 19 operaciones (E02 a E20 del SRS 4.5.2) más una de diagnóstico, documentada en `http://localhost:8000/docs` con la API en marcha. La lista, las respuestas y las convenciones (cifras como texto, fechas AAAA-MM-DD, una sola forma de error y orden de validación) están en MVP.md 7.4 y 7.5. Esas convenciones son valores adoptados en el código, por confirmar en el SRS, y la documentación OpenAPI todavía no describe la forma única de error ni declara los estados 401, 403, 404, 409 y 503 (MVP.md 12.4). En el SRS 4.2, el mecanismo de sesión sigue abierto.

### 10.5 Tecnologías

Versiones exactas en MVP.md 7.2. En breve:

| Capa | Tecnología |
|---|---|
| Servidor | Python 3.13, FastAPI, SQLAlchemy 2, psycopg 3, pydantic, pwdlib con Argon2id; entorno y dependencias con uv; pruebas con pytest |
| Base de datos | PostgreSQL 18 |
| Cliente web | React 19.3.0, Vite 8 y Recharts 3.10.1 (instalado y aún sin usar); se construye con Node.js 24 |
| Guía de estilo | CDS 9.29.0 como base, no instalado (sección 9.2) |
| Cálculo | `decimal` de Python con 28 dígitos; nunca punto flotante binario (RD-12) |

### 10.6 Requisitos de software y hardware

Software (SRS 3.5):

| Elemento | Requisito |
|---|---|
| Navegador | Versiones vigentes de navegadores basados en Chromium o Firefox: «las dos versiones más estables hasta la fecha de la prueba» (por confirmar si significa las dos versiones estables más recientes). Safari y WebKit no se admiten salvo que el SRS 3.5 lo declare (S-11). |
| Servidor de aplicación | Python 3.13, con su última corrección |
| Gestor de base de datos | PostgreSQL 18, con su última corrección |
| Construcción del cliente | Node.js 24, con su última corrección |
| Sistema operativo del servidor | Windows Server o Ubuntu Server, en las versiones del SRS 3.6.2; durante la estadía, el equipo de desarrollo |

Soporte de las plataformas (D-05): Python 3.13 recibe correcciones de seguridad hasta octubre de 2029; PostgreSQL 18, hasta el 14/11/2030, y Node.js 24, hasta el 30/04/2028, el primero en perderlo.

Hardware (SRS 3.6):

- Equipo del usuario: sin requisitos de cómputo; resoluciones de la sección 9.4.
- Servidor futuro: x86-64 con Windows Server 2025 o Ubuntu Server 24.04 LTS (otras versiones, abierto); procesador, memoria y almacenamiento del sistema operativo más el consumo del servidor y la base, por medir con RNF-06 (30/10/2026); salida HTTPS al SIE, la única interfaz externa, y entrada HTTPS desde la red de los usuarios.
- Equipo de desarrollo: el equipo personal del estudiante, que hace de servidor durante la estadía (R-07): Windows 11 Home, 16 GB de RAM y 23.9 GB libres de disco al 13/10/2026. El SRS 3.6.3 pide actualizar Python, Node.js y Firefox antes del 18/10/2026; no se ha hecho (MVP.md 7.2).

### 10.7 Licencias del software

- Ninguna dependencia es GPL ni AGPL; una dependencia AGPL contradiría la justificación técnica de la Definición (D-06).
- Las dependencias son permisivas, salvo psycopg 3 (LGPL-3.0) y certifi (MPL-2.0), que solo imponen obligaciones si se entrega una copia del servidor. Si la empresa lo entrega para instalarse (por confirmar), deberá incluir los avisos, ofrecer el código fuente de esas bibliotecas y permitir sustituir psycopg.
- El código del navegador sí se entrega a cada usuario, y las licencias MIT, ISC y BSD-3-Clause de sus dependencias piden conservar sus avisos. Cómo se incluyen está abierto, igual que los avisos de CDS (Apache-2.0, que no concede el uso de las marcas de Coinbase) y de Inter (SIL Open Font License 1.1).

---

## 11. Restricciones, marco legal, supuestos y dependencias

### 11.1 Restricciones

Elementos externos que limitan el diseño (SRS 2.4):

| ID | Restricción | Quién o qué la impone | La atienden |
|---|---|---|---|
| R-01 | No emitir recomendaciones de inversión individualizadas ni generar o sugerir composiciones de portafolio | LMV, art. 225: quien da asesoría de inversión individualizada debe registrarse ante la CNBV | RF-12; RF-14; RF-21; RF-22; S-15 |
| R-02 | No recibir, transmitir ni ejecutar órdenes; solo registrar operaciones ya realizadas | LMV, arts. 2, 9 y 113: la intermediación solo la prestan entidades autorizadas | RF-05 |
| R-03 | Consentimiento expreso y revocable, y aviso de privacidad que explique cómo revocarlo | LFPDPPP, arts. 7, 15 y 16 | RF-12 |
| R-04 | Sin datos reales de clientes ni información interna de la empresa durante el desarrollo | Convenio de confidencialidad con PluriOne | RF-07; RF-30; SRS 5.2 |
| R-05 | Solo datos de mercado cuya licencia permita usarlos en una aplicación para una empresa; cada dato con su fuente, fecha de carga, licencia y atribución | Términos de la BMV, de las API comerciales y del Banco de México | RF-07; RF-30; RF-31 |
| R-06 | El histórico del S&P/BMV IPC requiere una licencia de S&P Dow Jones Indices | Políticas de datos de la BMV | RF-18 |
| R-07 | Desarrollo, pruebas y demostración en el equipo personal del estudiante, sin servidor de producción | Sin presupuesto para equipo ni servicios en la nube | SRS 3.5 y 3.6.3; RNF-06; RNF-12 |
| R-08 | La única interfaz externa es la API del SIE del Banco de México; en el MVP solo sirvió para construir la semilla | Única fuente oficial sin costo, con API y uso reutilizable | RF-23; RF-30; RF-32; RNF-05; RNF-09 |
| R-09 | Retirada: RF-14 usa plantillas y no envía datos a terceros | — | — |
| R-10 | Un error de cálculo puede inducir decisiones equivocadas, y las fuentes no garantizan sus datos | Criticidad de la aplicación | RNF-01; RNF-02; SRS 5.2 |
| R-11 | Las valuaciones son estimaciones informativas, no precios oficiales | LMV, arts. 322 y 323: proveedores de precios autorizados | RF-12; RF-26b |
| R-12 | Proteger los datos personales y la información de la empresa | LFPDPPP, art. 18; convenio de confidencialidad | RF-01; RF-02; RNF-03 a RNF-05 |
| R-13 | Sin datos de mercado en tiempo real | La BMV licencia esos datos con contrato y pago | RF-07; RF-08; RF-31 |
| R-14 | Las tasas de CETES solo se generan en cada subasta y se fechan en la colocación; el calendario cambia cada trimestre | Programa de subastas de la SHCP; cuadro CF107 del SIE | RF-26b; RF-30; RF-32; RF-34 |
| R-15 | El SIE admite 10,000 consultas diarias por *token* y, si se rebasa, lo bloquea hasta el fin del día | Límites del SIE | RF-23; RF-30; RF-32; RNF-08 |

### 11.2 Marco legal

- Mercado de valores (LMV): art. 225, asesoría de inversión (R-01); arts. 2, 9 y 113, intermediación (R-02); arts. 322 y 323, proveedores de precios (R-11). Sin dictamen jurídico, se asume que respetar R-01, R-02 y R-11 basta para que quien opere la plataforma no necesite registro ni autorización de la CNBV (S-15, por confirmar con la empresa). Si la empresa tiene una opinión jurídica, RF-14, RF-21 y RF-22 se ajustan a ella; si concluye lo contrario, se eliminan o se rediseñan.
- Protección de datos personales (LFPDPPP de 2025): consentimiento y aviso (arts. 7, 15 y 16; R-03); medidas de seguridad (art. 18; R-12); datos mínimos de la cuenta (art. 12); derechos ARCO (art. 21); bloqueo y supresión tras la revocación (RD-23). Si se registran datos reales, el aviso debe identificar al responsable del tratamiento, que está por confirmar con la empresa (S-04). El aviso de demostración vigente deja pendientes el responsable, el plazo del bloqueo y el medio para los derechos ARCO (MVP.md 5.7).
- Revisión del DOF (D-04): se supone que durante la estadía no se expide un reglamento de la LFPDPPP ni se reforman los artículos de R-03 y R-12. El estudiante revisa el DOF antes del 18 de octubre y antes del 20 de noviembre de 2026 (AC-08 y AC-13). Al 18/10/2026 la revisión de AC-08 no consta en el SRS 3.1.
- Fiscal: RF-26a liquida los CETES antes de la retención de ISR, cuya tasa anual en 2026 es de 0.90 % (S-14). No hay cálculo fiscal de lotes ni del costo promedio fiscal (X-03).
- Licencias de datos: R-05, R-06 y R-13; el Banco de México permite reproducir su información citando la fuente (D-03).
- Licencias de software: sección 10.7.
- Confidencialidad: R-04 y R-12 vienen del convenio con la empresa. El repositorio es privado y no contiene documentación confidencial del cliente (README, «Avisos»). El documento de consideraciones legales (`docs/legal.md`) está pendiente (README).

### 11.3 Suposiciones

Las suposiciones se dan por ciertas sin poder garantizarlas; si alguna deja de cumplirse, cambian los requisitos y el cambio se registra en el SRS 3.1 (SRS 2.5). Las del usuario están en la sección 4.2.

| ID | Se asume | Si no se cumple | Estado |
|---|---|---|---|
| S-01 | El alcance es la delimitación MoSCoW de la Definición, que el estudiante definió con la libertad que dio el líder; el líder fijó la fecha del MVP y los dos archivos de `docs/`. La empresa no espera servicios en la nube ni otras tecnologías. | Se rehacen el SRS 3.2, 2.6, 2.4.7 y 5.3; otras tecnologías chocarían con R-07 | Por confirmar cuándo y por qué medio |
| S-02 | Una sola persona completa los 18 imprescindibles el 18/10/2026 y los requisitos del SRS 2.6 en sus fechas | Se acuerda con el líder qué imprescindibles pasan a la fase; los de 2.6 pasan a la fase posterior en orden MoSCoW estricto | — |
| S-03 | Sin servidor de producción durante la estadía | Se agrega un hito de despliegue, cifrado en tránsito y respaldo, y RF-32 deja de depender del equipo encendido | Decidido |
| S-05 | Quienes revisan aceptan validar con precios sintéticos marcados y tasas reales | Exigir precios reales choca con R-05 y X-07 sin licencia | Por confirmar con quienes revisan |
| S-06 | RF-24 se entrega solo para Android o como aplicación web progresiva | Con iOS, RF-24 no cabe en la estadía | Por confirmar con la empresa |
| S-12 | Las posiciones en CETES tienen a lo más 728 días por vencer | RF-26b aplica la tasa del plazo más largo | — |
| S-13 | La tasa de la subasta primaria interpolada aproxima lo suficiente el valor de los CETES para fines informativos | Cambian el método de RF-26b y el SRS 5.2 | Por confirmar con la empresa |
| S-14 | Basta liquidar los CETES a valor nominal antes de ISR, y la reinversión se registra como compra | Cambian RF-26a, el TWR y el SRS 5.2 | Decidido |
| S-15 | Sin dictamen, respetar R-01, R-02 y R-11 basta para no requerir registro ante la CNBV | Se ajustan, eliminan o rediseñan RF-14, RF-21 y RF-22 | Por confirmar con la empresa |

### 11.4 Dependencias

| ID | Se asume | Si falla o cambia | Estado |
|---|---|---|---|
| D-01 | La API del SIE sigue disponible en su versión 1, sin costo, y el *token* del estudiante sigue habilitado | Las tasas nuevas se cargan a mano; los cálculos no se interrumpen. Con un servidor de la empresa, el *token* lo genera quien lo opere | Por confirmar con la empresa |
| D-02 | El Banco de México mantiene las series de tasas, plazos y FIX con la misma clave, unidad y convención de fechas | Cambian la carga, la valuación, el vencimiento de las emisiones nuevas y el SRS 5.2 | — |
| D-03 | Se mantiene la autorización general del Banco de México para reproducir su información citando la fuente | Se revisan RF-30, RF-32, RF-34 y RF-23; si las tasas reales dejan de poder usarse, RF-30 se construye con otra fuente o con tasas sintéticas (abierto) | — |
| D-04 | No hay reglamento ni reforma de la LFPDPPP durante la estadía | Se revisan RF-12, R-03, R-12 y RNF-03 a RNF-05 | Se comprueba con AC-08 y AC-13 |
| D-05 | Python 3.13, PostgreSQL 18 y Node.js 24 reciben correcciones durante la estadía y el mantenimiento | El SRS 3.5 pasa a versiones con soporte y se repiten las pruebas | Periodo de mantenimiento por definir con la empresa |
| D-06 | Las licencias de las bibliotecas permiten un producto de código cerrado | Sección 10.7 | Forma de entrega por confirmar con la empresa; avisos del cliente, abierto |
| D-07 | El líder revisa el MVP después del 18 de octubre, y una segunda vez si hace falta; la asesora académica revisa la memoria y quizá el proyecto el 20/11/2026 | La aceptación del MVP se recorre y se reduce el margen de la fase de refinamiento | Fechas y forma por confirmar |

---

## 12. Fuera del alcance

### 12.1 Exclusiones: nunca entran

Decisiones de delimitación con la técnica MoSCoW, categoría «No se incluirá» (SRS 2.4.7; Definición):

| ID | Exclusión | Consecuencia |
|---|---|---|
| X-01 | Conexión automática con los intermediarios e importación de sus estados de cuenta | Toda transacción se captura a mano (RF-05) |
| X-02 | Operación para varias organizaciones cliente (*multitenant*) | Un solo perfil y aislamiento horizontal (RF-02) |
| X-03 | Cálculo fiscal de lotes y del costo promedio fiscal | El costo promedio de RF-08 no tiene efectos fiscales |
| X-04 | Ventas en corto y préstamo de valores | El saldo con cada intermediario no puede quedar negativo (RF-28) |
| X-05 | Rendimiento y riesgo por intermediario | Se miden solo para el portafolio en su conjunto |
| X-06 | Consolidación de varios portafolios de un mismo usuario | Cada portafolio se mide por separado |
| X-07 | Fuentes comerciales de precios (Twelve Data, EODHD o Marketstack) mientras PluriOne no contrate su licencia | La arquitectura las admite como un adaptador desactivado (RNF-10); los precios vienen de la semilla (RF-07) y, desde la fase de refinamiento, de la captura del usuario (RF-33) |

También quedan fuera, por restricción: la asesoría o las recomendaciones de inversión personalizadas (R-01), la ejecución de órdenes (R-02) y los datos de mercado en tiempo real (R-13).

### 12.2 Sin requisito en el SRS

Las capacidades de la sección 6.12 no forman parte del alcance vigente. Para operar fuera del entorno de la estadía, el SRS prevé estas condiciones:

- Servidor: cifrado en tránsito y respaldo en el SRS 3.3, mínimos del SRS 3.6.2 y un hito de despliegue en el SRS 3.8 (S-03).
- Datos reales: responsable del tratamiento, aviso definitivo, medidas de R-12 dimensionadas para la operación y probable recuperación de contraseña por correo (S-04).
- *Token* del SIE a cargo de quien opere el sistema (D-01).
- Obligaciones de licencia si se entrega el servidor (D-06) y periodo de mantenimiento con la empresa (D-05).
- Precios reales solo con una licencia que contrate PluriOne (X-07; S-05), y el IPC solo con la licencia de S&P Dow Jones Indices (R-06).

---

## 13. Hoja de ruta y entregas

### 13.1 Hitos

| Fecha | Hito | Fuente |
|---|---|---|
| Lunes 21 de septiembre de 2026 | Revisión de planeación, con la asesora académica | SRS 3.8; README |
| Lunes 28 de septiembre de 2026 | Revisión de avance | SRS 3.8; README |
| Domingo 18 de octubre de 2026, inclusive | Entrega del MVP; verificación de RNF-01 a RNF-05; revisión del DOF anterior a esa fecha (AC-08; por precisar si admite el mismo día) | SRS 3.8, 3.3 y 3.9.2 |
| Después del 18 de octubre | Revisión del MVP por el líder y, si hace falta, segunda revisión (fechas por confirmar) | SRS 3.9.1 |
| Lunes 19 de octubre de 2026 | Empieza la fase de refinamiento | SRS 2.6; Definición |
| Domingo 15 de noviembre de 2026 | Termina el desarrollo de la fase de refinamiento | SRS 2.6 |
| Semana del 16 de noviembre | Capacitación, entrega y cierre | SRS 2.6 y 3.9.4 |
| Viernes 20 de noviembre de 2026 | Cierre de la fase de refinamiento y fin de la estadía; aceptación al cierre (AC-09 a AC-13); revisión del DOF anterior a esa fecha (AC-13) | SRS 3.8 y 3.9.4 |

### 13.2 Prioridad al empezar la fase de refinamiento

Antes que los requisitos del SRS 2.6 van, en este orden (SRS 2.6.3 y 3.9.3):

1. Los imprescindibles que S-02 pase a la fase de refinamiento.
2. La revisión del MVP (D-07).
3. Si el líder encuentra inconsistencias o carencias, su corrección antes de la segunda revisión.

Lo que falta del MVP al 18/10/2026 está en MVP.md 12.6: pantallas del cliente web, registro de resultados, recorrido de AC-04, sección del README para instalar en local, revisión del DOF, el commit y el envío de este documento y de MVP.md, el criterio 1 de RF-11 y la confirmación de la tasa a 28 días del 10/09.

### 13.3 Semana a semana

| Semana | Requisitos con fecha | Verificaciones y otras fechas |
|---|---|---|
| Del 19 al 25 de octubre | Diferidos: RF-19, RF-20, RF-32 y RF-34. Deberían incluirse, como propuesta: RF-27 y RF-13. | 23/10: RNF-07. Antes del 23/10: fijar el volumen de referencia de RNF-06, completar el glosario del SRS 1.3 y probar CDS (opción B). |
| Del 26 de octubre al 1 de noviembre | Diferidos: RF-17, RF-21 y RF-33. Debería incluirse, como propuesta: RF-15. | 30/10: RNF-05 de nuevo (con RF-32), RNF-08 y RNF-09; línea base de RNF-06 para fijar T; mediciones del SRS 3.6. Al 1 de noviembre quedan fijos los indicadores que tendrá RF-24: los entregados a esa fecha. |
| Del 2 al 8 de noviembre | Diferidos: RF-22, RF-23 y RF-24 (primera de dos semanas). Debería incluirse, con fecha decidida: RF-14. | 06/11: RNF-06 y RNF-10. Semanas del 2 y del 9: documentación técnica, manual de usuario y plan de mantenimiento. El lunes 2 de noviembre es día sin operaciones bursátiles (MVP.md 5.4); si la empresa labora ese día está por confirmar. |
| Del 9 al 15 de noviembre | Diferido: RF-24 (segunda semana). Opcionales, como propuesta: RF-16 y RF-18, si hay margen; si no, posteriores a la estadía. | 13/11: RNF-11 y RNF-12, y límite de AC-09; el responsable de pruebas ejecuta las pruebas hasta esa fecha. 15/11: termina el desarrollo. |
| Del 16 al 20 de noviembre | Capacitación, entrega y cierre | AC-09 a AC-13; revisión del DOF antes del 20/11 (AC-13). |
| Por fijar | RF-39 | — |

### 13.4 Reglas de ajuste del plan

- Si una semana no se cumple, se aplica S-02: lo que ya no quepa pasa a la fase posterior a la estadía, en el orden de la sección 5.3 y con sus dependientes; cada cambio se registra en el SRS 3.1 (SRS 2.6).
- No hay una estimación de esfuerzo por requisito (registro de decisiones).
- Según el registro de decisiones, si la semana del 19 no alcanza, la recomendación es mover primero RF-27 y RF-13 a otra semana de la fase y después RF-19, y no mover RF-32, porque RF-23 y RF-34 dependen de él. No hay decisión.

### 13.5 Entregables

| Entregable | Cuándo | Criterio |
|---|---|---|
| Código del MVP en el repositorio que indique el líder | 18/10/2026 (hora de corte por confirmar) | AC-01 a AC-05 |
| `docs/MVP.md` y `docs/PRD.md` | 18/10/2026 | AC-06 |
| Base de demostración con solo semillas y cuentas de prueba | 18/10/2026 | AC-07 |
| Registro de resultados de las pruebas | 18/10/2026 y hasta el 13/11/2026 | AC-01 a AC-03, AC-07 (inspección de las semillas) y AC-09; al cierre, AC-10 |
| Código, base de demostración restaurable, manual técnico, manual de usuario, plan de mantenimiento y reporte de pruebas | Al cierre (fecha y medio por confirmar) | AC-12 (por confirmar si el líder los espera) |

### 13.6 Después de la estadía

- La fase posterior no tiene fecha; su responsable y su calendario dependen de la empresa (por confirmar; SRS 2.6.3).
- Entra en ella lo que se recorte por S-02, en el orden de la sección 5.3 y con sus dependientes, incluidos RF-16 y RF-18 si no hay margen (SRS 2.6.2 y 2.6.3), y RF-24 si la empresa exige iOS (S-06).
- AC-10 exige que lo no entregado conste en el SRS 3.1 y 2.6.3 como posterior a la estadía.
- El lugar de las capacidades sin requisito de la sección 6.12 no está decidido; la recomendación del registro de decisiones está en esa sección. Las condiciones de la sección 12.2 aplican si el sistema opera fuera del entorno de la estadía.

---

## 14. Criterios de aceptación

### 14.1 Bases comunes

Según el SRS 3.9:

- La aceptación se apoya en la verificación, que confirma con evidencia objetiva que se cumplen los requisitos.
- El cálculo se acepta con datos de demostración: precios sintéticos marcados (RF-07), tasas reales de CETES (RF-30) y la valuación de los CETES como estimación informativa (RF-26b; R-11).
- Por decisión del estudiante, por confirmar con el líder, la aceptación no evalúa la exactitud de los precios (S-05) ni la cercanía de la valuación al mercado secundario (S-13).
- No hay pruebas con usuarios reales (S-04).

### 14.2 Responsables

| Rol | Qué revisa | Cuándo | Resultado |
|---|---|---|---|
| Líder de proyecto | El MVP, incluidos los dos archivos de `docs/` (por confirmar si su revisión los cubre), en el repositorio que indique (por confirmar cuál, qué rama y cómo accede) | Después del 18 de octubre (fecha por confirmar), y una segunda vez si encuentra inconsistencias o carencias | Observaciones o conformidad (por confirmar si deja constancia escrita y si equivale a aceptar) |
| Responsable de pruebas (el estudiante) | Ejecuta los CPF y los CPNF y documenta el recorrido de AC-04 en un registro fechado de resultados (ruta abierta) | Hasta el 18 de octubre (MVP) y el 13 de noviembre (RNF-06 a RNF-12) | Evidencia, no la decisión de aceptar |
| Asesora académica | La memoria de estadías y, quizá, el desarrollo o la terminación del proyecto (por confirmar qué y con qué evidencia) | Quizá el 20 de noviembre (por confirmar) | Evaluación académica; si interviene en la conformidad del cierre, por confirmar |
| Asesor empresarial | No revisa el sistema ni la especificación | — | No interviene en la aceptación |

### 14.3 Aceptación del MVP

El MVP se entrega a más tardar el domingo 18 de octubre de 2026, inclusive, en el repositorio que indique el líder (hora de corte y si rige el commit o su envío, por confirmar). Solo se ejecuta en el equipo de desarrollo, donde el recorrido de AC-04 documenta su funcionamiento; no consta una demostración en sesión (por confirmar). Se considera aceptado cuando una revisión del líder, primera o segunda, concluye sin observaciones pendientes, condición por confirmar con él (SRS 3.9.2).

| AC | Criterio (SRS 3.9.2) | Evidencia | Estado al 18/10/2026 (MVP.md 12.2) |
|---|---|---|---|
| AC-01 | Cada imprescindible vigente en el SRS 3.2 cumple su criterio y aprueba su CPF | Resultado y fecha de cada CPF en el registro de resultados | Pendiente: faltan el registro de resultados, los criterios de interfaz de RF-07, RF-11, RF-12 y RF-31, y resolver el criterio 1 de RF-11 |
| AC-02 | RNF-02 a RNF-05 alcanzan su valor objetivo al 18 de octubre | Resultado y fecha de CPNF-02 a CPNF-05 | Pendiente en parte: falta el registro, ejecutar CPNF-05 y la demostración de RNF-02 con capturas |
| AC-03 | RNF-01 sobre el SRS 5.2, y el commit que lo congela es anterior al primero del motor | Tabla de diferencias de CPNF-01 y hash del commit `11097f8` | Hecho en código y git; falta guardar la evidencia |
| AC-04 | Recorrido de los imprescindibles, en el equipo de desarrollo y con los datos del SRS 5.2, con al menos una captura fechada por requisito | Registro del recorrido con sus capturas | Pendiente: no hay pantallas |
| AC-05 | El repositorio explica cómo instalar el MVP en local, crear la base, cargar las semillas y ejecutar las pruebas, sin valores reales en las variables de ejemplo | Sección «Cómo ejecutarlo localmente» del README | Pendiente; los pasos completos están en MVP.md 11 |
| AC-06 | `docs/` contiene los dos archivos Markdown que pidió el líder; el 18/10/2026 fijó sus nombres, `MVP.md` y `PRD.md` (por confirmar si deben ser exactamente esos dos) | Los archivos en la versión entregada | En curso: `docs/MVP.md` y este archivo; falta su envío |
| AC-07 | La base de demostración solo contiene semillas y cuentas de prueba con datos ficticios | Inspección del script de semillas | Hecho; falta guardar la evidencia |
| AC-08 | Consta en el SRS 3.1 una revisión del DOF conforme a D-04, anterior al 18 de octubre | Fecha y resultado en el SRS 3.1 | Pendiente |

Si un imprescindible no cumple AC-01 a tiempo, su paso a la fase de refinamiento se acuerda con el líder y se registra en el SRS 3.1 antes de la revisión (S-02).

### 14.4 Observaciones del líder

Según el SRS 3.9.3:

1. Cada observación se registra con su fecha y el requisito o documento afectado (medio por confirmar).
2. Se corrige, se repiten los CPF y CPNF afectados y se anotan su resultado y su fecha; si cambia el SRS, se abre una versión en su apartado 3.1.
3. Las correcciones preceden a los requisitos del SRS 2.6 y consumen el margen de la fase de refinamiento.
4. El líder revisa por segunda vez (fecha y aviso por confirmar). Si quedan observaciones, el MVP se considera revisado con observaciones, y estas se tratan conforme a AC-11 (por confirmar con el líder).

### 14.5 Aceptación al cierre de la estadía

La estadía termina el viernes 20 de noviembre de 2026. Quién da la conformidad del cierre (el líder o la asesora académica) y si el líder espera una capacitación están por confirmar. RF-24, si entra, se verifica por la red local. Al cierre, lo entregado debe cumplir (SRS 3.9.4):

| AC | Criterio | Evidencia |
|---|---|---|
| AC-09 | RNF-06 a RNF-12, y RNF-05 de nuevo si se entrega RF-32, alcanzan su valor objetivo a más tardar el 13 de noviembre | Resultado y fecha de CPNF-05 a CPNF-12; para RNF-12, el registro de GitHub Actions si alcanzan los minutos gratuitos (si no, abierto) |
| AC-10 | Cada imprescindible trasladado por S-02 y cada requisito del SRS 2.6 incorporado al SRS 3.2 cumple su criterio y aprueba su CPF; los no entregados constan en el SRS 3.1 y 2.6.3 como posteriores a la estadía | Registro de resultados y filas del SRS 3.1 |
| AC-11 | Cada observación de la revisión del MVP está resuelta o registrada en el SRS 3.1 como trasladada | Registro de observaciones y filas del SRS 3.1 |
| AC-12 | Lo entregado incluye el código, la base de demostración restaurable conforme a RNF-12, el manual técnico, el manual de usuario, el plan de mantenimiento y el reporte de pruebas (por confirmar si el líder los espera) | Los archivos entregados al cierre |
| AC-13 | Consta en el SRS 3.1 una revisión del DOF conforme a D-04, anterior al 20 de noviembre | Fecha y resultado en el SRS 3.1 |

### 14.6 Versión 1.0 del SRS

- Como nadie aprueba la especificación por separado, su versión 1.0 será la del documento al concluir la última revisión del MVP (abierto; por confirmar que esa revisión cubre `docs/`). Su fila registrará quién revisó, cuándo, por qué medio, con qué evidencia y qué observaciones siguen pendientes, y la llamará «revisada», no «aprobada», salvo confirmación escrita del líder (SRS 3.9.5).
- La versión del 18 de octubre sigue siendo 0.x, y los cambios posteriores a la 1.0 abren versiones 1.x. Hoy el SRS es la versión 0.3, en elaboración, con fecha de portada del 7 de octubre.

---

## 15. Riesgos y preguntas abiertas

### 15.1 Riesgos

| Riesgo | Efecto | Mitigación o regla | Fuente |
|---|---|---|---|
| Capacidad: una sola persona en cuatro roles, sin estimación de esfuerzo por requisito | Requisitos del SRS 2.6 que no caben | Recorte MoSCoW estricto con sus dependientes | SRS 3.7; S-02; 2.6.3 |
| Interfaz del MVP sin construir al 18/10/2026 | Imprescindibles trasladados por S-02 que consumen el margen de la fase de refinamiento | S-02, acordado con el líder y registrado en el SRS 3.1 | MVP.md 1.4 y 12.1; SRS 3.9.3 |
| Error de cálculo | Decisiones equivocadas del usuario | Motor único; conjunto de referencia resuelto por dos caminos y congelado; RNF-01 y RNF-02 | R-10; SRS 5.2 |
| Tasa a 28 días del 10/09/2026 confirmada con una sola fuente | Si cambia, se regeneran el SRS 5.2 y las semillas | Confirmarla con una segunda fuente | SRS 5.2; MVP.md 12.5 |
| Dependencia de una sola fuente externa (SIE) y de su límite diario | Sin tasas nuevas o con el *token* bloqueado | Los cálculos leen de la base (RNF-08); carga manual mientras tanto | D-01; D-02; R-15 |
| Sin servidor | RF-32 solo corre con el equipo encendido; RF-24 necesita HTTPS en la red local | — | SRS 2.6.1; S-03 |
| Equipo con poco disco (23.9 GB libres, 5.3 %, al 13/10/2026) | Limita Playwright, los respaldos y el registro de escritura de PostgreSQL | Medir al generarlos (30/10/2026) | R-07; SRS 3.6.3 |
| Intervalo de las semillas terminado el 14/10/2026 | No se pueden registrar transacciones posteriores hasta RF-32 | RF-32 en la semana del 19 de octubre | MVP.md 12.4 |
| Riesgo regulatorio sin dictamen (art. 225 de la LMV) | Rediseñar o eliminar RF-14, RF-21 y RF-22 | Criterios sin juicios de conveniencia; ajuste a una opinión jurídica si existe | S-15 |
| Datos reales durante la estadía | Aviso con responsable, medidas de R-12 y recuperación de contraseña | Supuesto de solo datos ficticios (por confirmar) | S-04 |
| El registro revela si un correo ya tiene cuenta | Cualquiera puede saber si un correo tiene cuenta; está por decidir si se acepta mientras solo haya datos ficticios (S-04) | Revisarlo antes de admitir datos reales (abierto) | MVP.md 12.4 |
| Sin matriz de riesgos | Riesgos del proyecto sin registro formal | La matriz `docs/riesgos.md` está pendiente | README |

### 15.2 Preguntas abiertas

Sin decisión registrada al 18/10/2026. Las fechas límite que no da el SRS vienen del registro de decisiones.

| Tema | Qué falta decidir o confirmar | Quién | Fecha límite | Afecta a |
|---|---|---|---|---|
| Plan de la fase de refinamiento | Fechas propuestas de RF-27, RF-13, RF-15, RF-16 y RF-18; fecha de RF-39; lugar y orden de los diferidos en el recorte; quién hace la fase posterior; si se labora el lunes 2 de noviembre | Estudiante; la fase posterior y el 2 de noviembre, con la empresa | RF-27 y RF-13, antes del 19/10; lo demás, al cierre de la semana del 19 | SRS 2.6.1 a 2.6.3 |
| Diseño de RF-32 | Rol con el que escribe la tarea del SIE, valores de origen de las cargas, disparador diario y cliente HTTP; componente «Cargas» frente al script SQL | Estudiante | Rol y origen, antes del 19/10; lo demás, en la semana del 19 | RF-32; RF-34; RF-23 |
| Reglas de datos para las cargas diarias | Sustituir o versionar las correcciones (RD-21) y la fecha de obtención de cada carga | Estudiante | Antes del 19/10 | RF-32 |
| Pantallas del MVP | Cuáles se construyen antes de la revisión y cuáles pasan por S-02, con aviso al líder | Estudiante, con el líder | 18/10 | RF-07; RF-11; RF-12; RF-31; AC-01; AC-04 |
| Criterio 1 de RF-11 | Aplicar la tolerancia a las cifras del motor o presentar 3 decimales | Estudiante | 18/10, antes de entregar el MVP, porque AC-01 juzga RF-11 con el texto vigente | RF-11; AC-01 |
| Revisión y aceptación | Si la revisión cubre `docs/`, fecha y constancia, segunda revisión, demostración, aceptación con datos de demostración y sin servidor, conformidad del cierre, entregables de AC-12 y capacitación | Líder de proyecto y asesora académica | Antes de la revisión del líder | SRS 3.9 |
| Entrega del MVP | Repositorio, rama y hora de corte; si `docs/` debe tener exactamente los dos archivos que pidió (hoy tiene cuatro) | Líder de proyecto | 18/10 | AC-06; SRS 3.9.2 |
| Datos personales | Datos reales, responsable del tratamiento y plazo del bloqueo tras la revocación | Empresa | Antes de la revisión del líder | S-04; RD-23; RF-12 |
| Opinión jurídica sobre el art. 225 de la LMV | Si la empresa la tiene | Empresa | Antes del 26/10 (RF-21) | RF-14; RF-21; RF-22 |
| Aplicación móvil | Android o aplicación web progresiva frente a iOS; si el SRS 3.6.1 conserva los 360 px | Estudiante y empresa | Antes del 2/11 | RF-24; S-06 |
| Forma de entrega y mantenimiento | Solo servicio web o instalación por los clientes; periodo del plan de mantenimiento; forma de los avisos de licencia del cliente | Empresa; los avisos, el estudiante | 2/11; los avisos, 23/10 | D-05; D-06; AC-12 |
| Accesibilidad | Agregar un requisito de WCAG 2.2 AA; si RNF-11 exceptúa tablas y gráficas; duración de la sesión frente al criterio 2.2.1 | Estudiante | 23/10 | SRS 3.3; RNF-11; 4.5.1 |
| Prueba de CDS | Bajar React a la 19.1.10, resolver sin forzar, compilar con Vite 8 e incorporar Inter | Estudiante | 23/10 | SRS 4.5.1; 3.5; D-06 |
| RNF-06 y RNF-12 | Volumen, percentil, número de cargas y caché; plan alterno si no alcanzan los minutos de GitHub Actions | Estudiante | 23/10; 13/11 | AC-09 |
| Glosario | Completar la tabla de términos del SRS 1.3, que usa RNF-07 | Estudiante | Antes del 23/10 | RNF-07 |
| Importación en CSV | Contradicción de RF-33 con «nunca por carga de archivo» del SRS 2.3 | Estudiante | Antes de la semana del 26/10 | RF-33 |
| Licencias de datos | Plantear a la empresa la licencia de precios reales o la del IPC | El estudiante decide si lo plantea; la empresa decide | Antes del 9/11 | RF-18; X-07; S-05 |
| Capacidades sin requisito | Saldo inicial, traspasos, eventos corporativos, recuperación de contraseña y Microsoft Entra ID: posteriores a la estadía, exclusiones o con fecha | Estudiante; Entra ID, con la empresa | Antes de cerrar la versión 0.3 del SRS | S-07; SRS 2.4.7, 2.6.3 y 3.4.1 |
| Reglas del cálculo del MVP | Confirmar las que adoptó el conjunto de referencia y llenar las fichas de RF-06, RF-08, RF-09 y RF-10 | Estudiante | Las reglas, antes del 19/10; las fichas, antes del 23/10 | RF-06; RF-08 a RF-10 |
| Valores adoptados en el código | Política de contraseña, mensajes, duración de la sesión, límite de RD-05 (728 o 730 días), decimales de presentación y forma de la API | Estudiante | A más tardar el 23/10; RD-05, antes de RF-34 (semana del 19/10) | MVP.md 12.5 |
| Licencia de la semilla sintética | Confirmar la versión «1» y el nombre de su fuente | Estudiante | Antes del 23/10 | RF-31 |
| Versiones del entorno | Actualizar Python, Node.js y Firefox o registrar una nueva fecha | Estudiante | 18/10 | SRS 3.6.3; AC-05 |
| Revisión del DOF | Hacerla y registrarla; si «anterior al 18» admite el mismo día | Estudiante | 18/10 | AC-08 |

### 15.3 Marcas abiertas del SRS

Al 18/10/2026, el SRS del commit `268a2c2` tiene 297 marcas de decisión o confirmación abiertas, 90 de ellas en el apartado 4.5. Las de mayor peso para el producto son las de esta sección: alcance y aceptación (S-01 y SRS 3.9), datos personales (S-04, RD-23, RF-12 y SRS 3.4.7), validación con datos de demostración (S-05, S-13 y SRS 3.9), riesgo regulatorio (S-15), plan de la fase de refinamiento (SRS 2.6.1 a 2.6.3), móvil (S-06 y SRS 3.6.1), operación y mantenimiento (D-01, D-05, D-06 y D-07), modelo de transacciones (S-07 y SRS 3.4.1) y verificación no funcional (RNF-06, RNF-12 y SRS 3.5).

---

## 16. Documentos relacionados y registro de cambios

### 16.1 Documentos relacionados

| Documento | Ubicación | Qué contiene |
|---|---|---|
| Descripción del MVP | [`docs/MVP.md`](MVP.md) | El MVP del 18 de octubre: capacidades, criterios, fórmulas, datos, API, instalación y estado |
| Especificación de requisitos (SRS) | [`docs/2 (SRS) Especificación de Requisitos de Software.md`](2%20%28SRS%29%20Especificaci%C3%B3n%20de%20Requisitos%20de%20Software.md) | Requisitos, reglas de datos, diseño, conjunto de referencia y criterios de aceptación |
| Definición del proyecto | [`docs/1 Definición del proyecto.md`](1%20Definici%C3%B3n%20del%20proyecto.md) | Problema, objetivos OE-1 a OE-5, justificación y clasificación MoSCoW |
| README del repositorio | [`README.md`](../README.md) | Índice del paquete, fechas clave, stack, base de datos local y avisos |
| Conjunto de referencia | [`backend/tests/oraculo/README.md`](../backend/tests/oraculo/README.md) | Escenario, entradas, cifras esperadas, fuentes y tolerancias |
| Aviso de privacidad de demostración | [`backend/semillas/aviso_privacidad_demo.md`](../backend/semillas/aviso_privacidad_demo.md) | Texto vigente del aviso (RF-12) |
| Glosario del dominio financiero | Documento aparte, enlazado en el SRS 1.3 | Términos financieros |
| Registros de decisión (ADR), matriz de riesgos, cronograma y consideraciones legales | `docs/adr/`, `docs/riesgos.md`, `docs/cronograma.md` y `docs/legal.md` | Pendientes (README, «Índice del paquete») |

### 16.2 Historia del alcance

El SRS 3.1 registra las versiones de la especificación: las 0.x son borradores, la 1.0 es la que fija el SRS 3.9.5 y las 1.x son los cambios posteriores. Cada cambio de alcance, fechas, suposiciones o dependencias abre una versión nueva (SRS 3.1).

| Fecha | Cambio | Fuente |
|---|---|---|
| 19/09/2026 | Repositorio inicial con la Definición del proyecto. SRS 0.1, con el MVP previsto para el 5 de octubre. | Commit `bb48cbd`; SRS 3.1 |
| 26/09/2026 | La Definición incorpora intermediarios y CETES: intermediario en cada transacción, saldo no negativo, posición como suma de saldos, emisiones de CETES, máxima caída sobre el rendimiento acumulado y costo promedio por intermediario. El MVP pasa al domingo 18 de octubre, inclusive. La documentación deja de ser objetivo y queda como actividad del cronograma. | Commit `01ac970`; SRS 3.1, fila 0.2 |
| 12/10/2026 | Se registra en el repositorio el diseño híbrido de datos (precios sintéticos y tasas reales del SIE), decidido el 6 de octubre según el registro de decisiones. RF-22 deja de ser la optimización de la composición del portafolio y pasa a simular composiciones que define el usuario, sin que el sistema las genere ni sugiera; RF-12 agrega el aviso de privacidad y la revocación del consentimiento. RF-31 pasa a imprescindible, con lo que el MVP suma 18; RF-32 y RF-33 quedan diferidos, RF-18 usa un índice sintético o propio y se excluyen las fuentes comerciales (X-07). El SRS pasa a la versión 0.3, fechada el 7 de octubre. | Commit `47c5b59`; SRS 3.1, fila 0.3 |
| 13/10/2026 | Cambian RF-05 (precio por título e importe de comisiones con IVA), RF-12 (aviso de valuación estimada), RF-28 (solo al registrar y dentro del portafolio) y RF-30 (CETES a 728 días y plazo efectivo). Se agregan los criterios de aceptación del SRS 3.2 y el apartado 3.9. Entra RF-39 como diferido. | Commits `eed561b` y `78b73b1`; SRS 3.1, fila 0.3 |
| 14/10/2026 | Entra RF-34 y el orden de recorte MoSCoW estricto. RF-32 deja la UDI y carga las series de plazo; el FIX histórico se carga una sola vez con RF-23. Se fijan los métodos de RF-17, RF-19, RF-20 y RF-21 y los indicadores de RF-24. Los precios de RF-33 son privados de su autor. RF-14 se hará en la semana del 2 de noviembre con plantillas y sin juicios de conveniencia; se retira R-09. | Commit `b80c439`; SRS 3.1, fila 0.3 |
| 15/10/2026 | Se congela el SRS 5.2, evidencia de AC-03. No cambia el alcance. | Commit `11097f8`; SRS 5.2 |
| 16 y 18/10/2026 | Decisiones de diseño, sin cambio de alcance: Recharts 3.10.1 para las gráficas; guía de estilo basada en CDS con tema propio (SRS 4.5.1) y mapa de navegación (SRS 4.5.2). | Commits `6cd253c` y `268a2c2`; SRS 3.1, fila 0.3 |

Pendientes de registro al 18/10/2026: ningún traslado de imprescindibles por S-02 consta en el SRS 3.1, la revisión del DOF de AC-08 tampoco, y la versión 0.3 sigue abierta y reúne todos los cambios del 7 al 18 de octubre (MVP.md 12; SRS 3.1).

### 16.3 Registro de cambios de este documento

| Versión | Fecha | Autor | Cambios |
|---|---|---|---|
| 1.0 | 18/10/2026 | Ramon Ernesto Nieblas Mendivil | Primera versión, entregada con el MVP (AC-06). Refleja el SRS 0.3 del commit `268a2c2` y el estado de MVP.md al 18/10/2026. |
