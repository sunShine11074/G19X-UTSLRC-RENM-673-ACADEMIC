# MVP del Proyecto 077

Plataforma Inteligente de Gestión de Activos Financieros: producto mínimo viable (MVP) entregado el 18 de octubre de 2026.

| Dato | Valor |
|---|---|
| Proyecto | 077 — Plataforma Inteligente de Gestión de Activos Financieros |
| Documento | `docs/MVP.md`: descripción del MVP y de cómo comprobar cada una de sus capacidades |
| Versión del documento | 1.0 |
| Fecha | Domingo 18 de octubre de 2026 |
| Autor | Ramon Ernesto Nieblas Mendivil, estudiante en estadía del TSU en Desarrollo de Software Multiplataforma (Universidad Tecnológica de San Luis Río Colorado). Analista, desarrollador y responsable de pruebas del proyecto (SRS 3.7). |
| Empresa | PluriOne S.A. de C.V. (Develop Talent & Technology) |
| Líder de proyecto | Edgar Loeffelmann Ibarra: revisión del MVP y aprobación del entregable (SRS 1.2) |
| Entrega del MVP | A más tardar el domingo 18 de octubre de 2026, inclusive (SRS 3.8 y 3.9.2) |
| Especificación de referencia | SRS versión 0.3 (en elaboración), tal como está en el commit `268a2c2` |
| Estado del MVP | Servidor completo (API, motor de cálculo, base de datos y datos semilla) y verificado con 271 pruebas automatizadas. La interfaz web está pendiente: hoy solo existe una página de prueba de conexión. El detalle está en la sección 12. |

## Propósito y uso de este documento

Este archivo describe el MVP del Proyecto 077: qué hace, para quién, con qué datos, cómo calcula, cómo se instala y cómo se comprueba cada capacidad. El líder de proyecto pidió que la carpeta `docs/` contenga dos archivos Markdown, uno del MVP y otro del PRD (SRS 2.5.1, S-01, y 3.9.2, AC-06), y el 18 de octubre de 2026 fijó sus nombres: `MVP.md` (este archivo) y `PRD.md`. Solo queda por confirmar con él si `docs/` debe tener exactamente esos dos (sección 12.5). Su plataforma los usará, entre otras cosas, como criterios para evaluar la aplicación.

Relación con los demás documentos:

- `docs/PRD.md` es el documento de requisitos del producto que pide AC-06 y trata el producto en su conjunto. Este archivo se limita al MVP, la entrega del 18 de octubre de 2026.
- `docs/2 (SRS) Especificación de Requisitos de Software.md` (en adelante, el SRS) es la especificación completa. Este documento la resume sin cambiarla y remite a ella por apartado e identificador; por ejemplo, «SRS 3.2, RF-08» es el requisito RF-08 del apartado 3.2. Si algo de aquí difiere del SRS, prevalece el SRS.
- `docs/1 Definición del proyecto.md` fija el objetivo general, los objetivos específicos (OE-1 a OE-5) y la clasificación MoSCoW de la que sale el alcance del MVP.

Cómo usarlo para evaluar la aplicación:

1. La sección 3 presenta cada capacidad del MVP con lo que hace, sus reglas, sus criterios de aceptación numerados (los mismos del SRS 3.2) y la prueba que la verifica.
2. Las secciones 4 y 5 dan las fórmulas y los datos, con resultados esperados que se pueden comprobar. La sección 6 da los requisitos no funcionales que se verifican con el MVP (RNF-01 a RNF-05), con su métrica, su prueba y su estado, y la sección 9, lo que queda fuera del MVP.
3. La sección 10 lista los criterios de aceptación de la entrega (AC-01 a AC-08) y la evidencia que pide cada uno.
4. La sección 11 da los comandos para instalar, ejecutar y probar el sistema en un equipo local.
5. La sección 12 dice, sin adornos, qué está hecho y verificado, qué está hecho sin interfaz y qué está pendiente, en todo o en parte, al 18 de octubre de 2026.

### Convenciones

| Identificador | Qué es | Dónde se define |
|---|---|---|
| RF-nn | Requisito funcional: algo que el sistema hace | SRS 3.2 (MVP) y 2.6 (fases posteriores) |
| RNF-nn | Requisito no funcional: una cualidad medible (corrección, seguridad, etc.) | SRS 3.3 |
| RD-nn | Regla de los datos: integridad, precisión, procedencia o conservación | SRS 3.4 |
| CPF-nn y CPNF-nn | Caso de prueba funcional y no funcional; lleva el número de su requisito | SRS 3.2 y 3.3 |
| AC-nn | Criterio de aceptación de una entrega | SRS 3.9 |
| CU-nn | Caso de uso | SRS 4.1 |
| V-nn | Pantalla del cliente web | SRS 4.5.2 |
| Enn | Operación de la API | SRS 4.5.2 y `backend/app/api/` |
| R-nn, X-nn, S-nn y D-nn | Restricción, exclusión de alcance, suposición y dependencia | SRS 2.4, 2.4.7 y 2.5 |
| OE-n | Objetivo específico | Definición del proyecto |
| SRS 5.2 | Conjunto de datos de referencia (el «oráculo»); este documento lo resume en la sección 5.8, no en su sección 5.2, que trata los precios sintéticos | SRS 5.2 y `backend/tests/oraculo/` |
| ⟦decidir⟧ y ⟦confirmar⟧ | Marcas con que el SRS señala una decisión o una confirmación abierta. Este documento no las usa: lo que el código aplica en su lugar se rotula «Adoptado, por confirmar», y lo que sigue abierto se lista en la sección 12.5 | SRS |

En este documento, el estado de cada cosa se nombra así:

- Especificado: lo exige el SRS.
- Implementado: existe en el código del repositorio.
- Verificado: lo comprueba una prueba automatizada que pasó el 18 de octubre de 2026.
- Adoptado, por confirmar: valor que el código aplica donde el SRS deja una decisión abierta. Funciona hoy, pero puede cambiar cuando se confirme y se lleve al SRS.
- Pendiente: lo exige un criterio y hoy no existe.

## Contenido

1. [Resumen del MVP](#1-resumen-del-mvp)
2. [Usuario y escenario de uso](#2-usuario-y-escenario-de-uso)
3. [Alcance funcional](#3-alcance-funcional)
4. [Cómo calcula](#4-cómo-calcula)
5. [Datos del MVP](#5-datos-del-mvp)
6. [Requisitos no funcionales del MVP](#6-requisitos-no-funcionales-del-mvp)
7. [Arquitectura, tecnologías y API](#7-arquitectura-tecnologías-y-api)
8. [Seguridad y privacidad](#8-seguridad-y-privacidad)
9. [Fuera del alcance del MVP](#9-fuera-del-alcance-del-mvp)
10. [Criterios de aceptación del MVP](#10-criterios-de-aceptación-del-mvp)
11. [Cómo ejecutarlo y verificarlo en local](#11-cómo-ejecutarlo-y-verificarlo-en-local)
12. [Estado al 18 de octubre de 2026](#12-estado-al-18-de-octubre-de-2026)
13. [Documentos relacionados](#13-documentos-relacionados)

---

## 1. Resumen del MVP

### 1.1 El producto

El Proyecto 077 es una plataforma web de gestión de activos financieros para el inversionista individual (SRS 2.1). Reúne en un solo lugar los portafolios del usuario, los intermediarios con los que invierte en México y las transacciones de compra y venta que realiza, incluidas las de CETES. Con esa información calcula el valor de mercado, el resultado no realizado, el rendimiento ponderado por tiempo (TWR) y la máxima caída del portafolio en su conjunto (Definición del proyecto, objetivo general y OE-4; SRS 3.2, RF-08).

Su principio de diseño es el motor único de cálculo: todas las cifras se calculan en el servidor, en un solo componente, y ninguna vista recalcula por su cuenta. Por eso una cifra es idéntica en todas las vistas donde aparece y se puede reproducir contra un conjunto de datos de referencia resuelto de forma independiente (SRS 2.1 y 5.2; README, «Principio de arquitectura»).

El producto no emite recomendaciones de inversión ni ejecuta órdenes: solo registra las operaciones que el usuario ya hizo con su intermediario (SRS 2.4, R-01 y R-02).

### 1.2 El problema que atiende

- La información de un inversionista individual suele estar dispersa entre estados de cuenta, hojas de cálculo y notas propias, y cada visión completa obliga a pasar cifras de un documento a otro (Definición, «Descripción»).
- El rendimiento observado mezcla lo que rindió el mercado con lo que el inversionista aportó o retiró; separar esos dos efectos exige cálculos distintos. Sin una medida de riesgo consistente, las decisiones se apoyan en la intuición (Definición, «Descripción»).
- Quien invierte con más de un intermediario recibe un estado de cuenta separado de cada uno, y la ley no prevé uno que los integre (Definición, «Impacto»).
- Las herramientas de código abierto evaluadas usan la licencia AGPL-3.0, incompatible con un producto de código cerrado de la empresa, y las dos que gestionan portafolios, Ghostfolio y Wealthfolio, no documentan una fuente de precios para valores gubernamentales mexicanos como los CETES (Definición, «Impacto» y «Justificación técnica»).

### 1.3 Qué es el MVP

- Alcance: los 18 requisitos imprescindibles (categoría «Must-have» de MoSCoW) del SRS 3.2: RF-01 a RF-12, RF-25, RF-26a, RF-26b, RF-28, RF-30 y RF-31. Atienden los objetivos OE-3 (registro y consolidación del portafolio) y OE-4 (motor de cálculo y tablero). OE-5, la comparación con un conjunto de referencia, se demuestra con RNF-01 (sección 6).
- Fecha: a más tardar el domingo 18 de octubre de 2026, inclusive (SRS 3.8).
- Quién lo definió: el líder de proyecto fijó la fecha del MVP y los dos archivos de `docs/`; el alcance funcional y las tecnologías los definió el estudiante (SRS 2.5, S-01).
- Datos: precios de cierre sintéticos, marcados como datos de demostración (RF-07); tasas reales de CETES del Banco de México (RF-30), y la valuación de los CETES como estimación informativa (RF-26b). Según el SRS 3.9, la aceptación evalúa el cálculo contra el conjunto de referencia, no la exactitud de los precios ni la cercanía de la valuación al mercado. Es una decisión del estudiante que el SRS deja por confirmar con el líder de proyecto (S-05 y S-13).
- Dónde corre: no hay servidor de producción. El sistema se ejecuta, se prueba y se demuestra en el equipo de desarrollo (SRS 2.5, S-03; 3.9.2).
- Usuarios: solo cuentas de prueba con datos ficticios y un aviso de privacidad de demostración (SRS 2.5, S-04).
- Divisa: solo pesos mexicanos, MXN (SRS 3.4, RD-08; S-10).

### 1.4 Lo que se entrega el 18 de octubre, en breve

- El servidor está completo: una API con 19 operaciones más una de diagnóstico, el motor único de cálculo, el esquema de base de datos de 13 tablas y la carga de los datos semilla. Lo verifican 271 pruebas automatizadas que pasan (sección 11.5).
- El conjunto de referencia (SRS 5.2) se congeló en el commit `11097f8`, del 15 de octubre, antes del primer commit del motor (`b3391fd`, del 17 de octubre). El motor reproduce sus cifras dentro de la tolerancia (RNF-01).
- La interfaz web no está construida: `frontend/src/App.jsx` solo muestra una página que comprueba la conexión con la API. Por eso faltan las 12 pantallas del SRS 4.5.2 y las partes de los criterios que solo puede cumplir la interfaz (sección 12). Si no quedan a tiempo, rige S-02: su paso a la fase de refinamiento se acuerda con el líder y se registra en el SRS 3.1 antes de la revisión (SRS 3.9.2).

### 1.5 Términos

| Término | Significado en este documento |
|---|---|
| Portafolio | Conjunto de inversiones que el usuario agrupa con un nombre y una divisa base (MXN). Cada portafolio se mide por separado. |
| Intermediario | La entidad con la que el usuario mantiene sus inversiones; en el sistema se identifica solo por su nombre (por ejemplo, «Casa A»). |
| Instrumento | Lo que se compra o se vende. Pertenece a una de cuatro clases: acción, ETF, FIBRA o CETES. |
| CETES | Certificados de la Tesorería de la Federación: títulos de deuda del Gobierno Federal que pagan su valor nominal, 10.00 pesos por título, en su fecha de vencimiento. Cada emisión es un instrumento propio, con clave «BI» más su vencimiento en formato AAMMDD. |
| Colocación, plazo nominal y plazo efectivo | El Banco de México coloca CETES en subastas a plazos nominales de 28, 91, 182, 364 y 728 días. El plazo efectivo es el número real de días de cada colocación (por ejemplo, 175 en una colocación nominal de 182). |
| Fecha de concertación | La fecha en que se pactó la transacción. |
| Saldo | Títulos de un instrumento con un intermediario, dentro de un portafolio. |
| Posición | Suma de los saldos de un instrumento con todos los intermediarios del portafolio, a una fecha de corte. Se deriva de las transacciones; nunca se captura. |
| Fecha de corte | La fecha a la que se calcula, inclusive. |
| Costo promedio ponderado | Costo por título que resulta de promediar las compras, ponderadas por sus títulos, dentro de cada intermediario. No tiene efectos fiscales. |
| Valor de mercado | Títulos por el último precio de cierre igual o anterior a la fecha; en CETES, títulos por el precio estimado P. |
| Resultado no realizado | Valor de mercado menos el costo de los títulos que siguen en posición: la ganancia o pérdida que todavía no se concreta con una venta. |
| Aportación y retiro | Dinero que entra al portafolio con una compra y que sale con una venta o con el vencimiento de un CETES. |
| TWR | Rendimiento ponderado por tiempo: encadena los rendimientos diarios para medir cuánto rindió el portafolio sin el efecto de las aportaciones y los retiros. No se anualiza. |
| Máxima caída | La mayor baja, en por ciento, desde un máximo del rendimiento acumulado hasta un mínimo posterior dentro del periodo. Es negativa o cero. |
| Datos semilla | Datos fijos que se cargan al instalar: catálogo, precios sintéticos, tasas de CETES y aviso de privacidad. |
| Datos de demostración | Los precios sintéticos, que no son precios reales, y las cifras que dependen de ellos. |
| Conjunto de referencia (SRS 5.2) | Escenario con resultados calculados de forma independiente antes de programar el motor; sirve para comprobar sus cifras. |
| MoSCoW | Clasificación de prioridad: imprescindible (Must), debería incluirse (Should), opcional (Could) y no se incluirá (Won't). |
| API | La interfaz por la que el cliente web pide datos y cálculos al servidor. |
| ETF | Fondo cotizado en bolsa (*exchange-traded fund*); una de las cuatro clases de instrumento. |
| FIBRA | Fideicomiso de Infraestructura y Bienes Raíces; una de las cuatro clases de instrumento. |
| P y VN | P es el precio estimado de un título de CETES antes de su vencimiento (RF-26b; fórmula en la sección 4.3); VN es su valor nominal, 10.00 pesos. |
| IVA e ISR | Impuesto al valor agregado, incluido en el importe de las comisiones de cada transacción, e impuesto sobre la renta, que retiene el intermediario al vencer un CETES y que el MVP no descuenta (S-14). |
| SIE | Sistema de Información Económica del Banco de México, de donde salen las tasas de CETES. |
| FIX | Tipo de cambio peso-dólar que determina y publica el Banco de México; lo usan requisitos posteriores al MVP. |
| CNBV | Comisión Nacional Bancaria y de Valores. |
| ARCO | Derechos de acceso, rectificación, cancelación y oposición sobre los datos personales. |
| AGPL | Licencia Pública General Affero de GNU. |
| TSU | Técnico Superior Universitario. |

El glosario completo del dominio financiero es un documento aparte, enlazado en el SRS 1.3.

---

## 2. Usuario y escenario de uso

### 2.1 Usuario

El MVP tiene un único perfil: el inversionista (SRS 2.3). No hay administradores, operadores ni grupos.

| Dimensión | Qué se supone | Qué no se supone | Consecuencia para el sistema |
|---|---|---|---|
| Relación con el sistema | Persona física, mayor de edad, que administra su propio patrimonio repartido entre varios instrumentos e intermediarios. | Que represente a una persona moral, administre patrimonio de terceros o espere que el sistema decida por ella. | Aislamiento entre cuentas equivalentes, sin operación multiorganización (RF-02). La mayoría de edad sustenta el consentimiento de RF-12, y la ausencia de asesoría, su advertencia. |
| Conocimiento financiero | Sabe qué es comprar y vender, distingue una ganancia de una pérdida y sabe que el valor cambia con el tiempo. | Que conozca o calcule el TWR o la máxima caída. | Cada indicador lleva su unidad y una definición en la misma pantalla (RNF-07). |
| Competencia técnica | Usa aplicaciones web y banca en línea sin dificultad. | Que construya hojas de cálculo o manipule datos en lote. | Las transacciones se capturan en un formulario guiado (RF-05). |
| Frecuencia de uso | Consulta esporádica; registra las transacciones cuando ocurren. | Uso diario o supervisión en tiempo real. | El tablero debe entenderse sin recordar sesiones anteriores. |

### 2.2 Escenario de uso

El recorrido típico del MVP, con los casos de uso del SRS 4.1:

1. Antes de usarlo, quien instala carga los datos semilla: catálogo, precios sintéticos, tasas de CETES y aviso de privacidad (CU-11; RF-07, RF-30 y RF-31).
2. La persona lee el aviso de privacidad de demostración (CU-09) y se registra con correo, contraseña y su consentimiento expreso (CU-01; RF-01 y RF-12). El registro no abre la sesión.
3. Inicia sesión (CU-02; RF-01).
4. Crea un portafolio en MXN, por ejemplo «Principal» (CU-03; RF-03), y registra sus intermediarios, por ejemplo «Casa A» y «Casa B» (CU-04; RF-25).
5. Consulta el catálogo de instrumentos (CU-08; RF-04).
6. Registra las compras y ventas que ya hizo con sus intermediarios, incluidas las de CETES (CU-05; RF-05). El sistema rechaza, con su motivo, la venta que deje negativo el saldo con un intermediario (CU-12; RF-28), la transacción de un CETES en su vencimiento o después (RF-26a) y las fechas fuera del intervalo de los datos semilla (RD-07).
7. Consulta sus transacciones y sus posiciones a una fecha de corte, con su costo, su valor de mercado, su resultado no realizado, la fuente y la fecha de cada precio o tasa, la marca de datos de demostración y los avisos de uso (CU-06; RF-05, RF-06, RF-08, RF-26a, RF-26b, RF-07, RF-12 y RF-31).
8. Abre el tablero de un portafolio y un periodo: valor de mercado, resultado no realizado, TWR, máxima caída y la gráfica de la evolución del valor (CU-07; RF-09, RF-10 y RF-11).
9. Si ya no quiere que se traten sus datos, revoca su consentimiento y la cuenta queda bloqueada (CU-10; RF-12).

### 2.3 Escenario de demostración

La demostración y la aceptación usan el escenario del conjunto de referencia (SRS 5.2): un usuario ficticio con dos portafolios en MXN, «Principal» y «Secundario», y dos intermediarios, «Casa A» y «Casa B», que registra 16 transacciones del 10/09 al 08/10/2026 con tres instrumentos de demostración y cuatro emisiones de CETES. Una de esas emisiones vence dentro del periodo. El escenario completo, con sus resultados esperados, está en la sección 5.8.

### 2.4 Entorno de uso

- Cliente y servidor se ejecutan en el mismo equipo; no se requiere Internet (SRS 3.6.1).
- Navegadores: versiones vigentes basadas en Chromium o Firefox (SRS 3.5).
- Resolución mínima de escritorio: 1280 × 720 px CSS, con el navegador al 100 % de zoom (SRS 3.6.1).
- El cliente debe abrirse en `localhost`, no en `127.0.0.1`, para que la cookie de sesión viaje (sección 11.7).

---

## 3. Alcance funcional

### 3.1 Resumen de los 18 imprescindibles

La agrupación por área es de este documento; el SRS 3.2 los lista por identificador. La columna «Estado» usa las categorías de la sección 12.

| RF | Capacidad | Área | OE | Prueba | Casos de uso | Pantallas | API | Estado al 18/10/2026 |
|---|---|---|---|---|---|---|---|---|
| RF-01 | Registro e inicio de sesión | A | OE-3 | CPF-01 | CU-01, CU-02 | V-01, V-02 | E03 a E06 | Hecho sin interfaz |
| RF-02 | Aislamiento de la información de cada usuario | A | OE-3 | CPF-02 | CU-03 a CU-07 | V-12 | Todas las que exigen sesión | Hecho sin interfaz |
| RF-03 | Gestión de portafolios | B | OE-3 | CPF-03 | CU-03 | V-08 | E12 a E16 | Hecho sin interfaz |
| RF-04 | Catálogo de instrumentos | C | OE-3 | CPF-04 | CU-08 | V-10 | E08 | Hecho sin interfaz |
| RF-05 | Registro y consulta de transacciones | D | OE-3 | CPF-05 | CU-05, CU-06 | V-06, V-07 | E17, E18 | Hecho sin interfaz |
| RF-06 | Posición vigente | E | OE-3 | CPF-06 | CU-06, CU-07 | V-05, V-04 | E19, E20 | Hecho sin interfaz |
| RF-07 | Precios de cierre sintéticos | G | OE-4 | CPF-07 | CU-11, CU-06, CU-07 | V-04, V-05 | Semillas; E19, E20 | Pendiente en parte (criterio 3) |
| RF-08 | Valor de mercado y resultado no realizado | E | OE-4 | CPF-08 | CU-06, CU-07 | V-05, V-04 | E19, E20 | Hecho sin interfaz |
| RF-09 | Rendimiento ponderado por tiempo (TWR) | F | OE-4 | CPF-09 | CU-07 | V-04 | E20 | Hecho sin interfaz |
| RF-10 | Máxima caída | F | OE-4 | CPF-10 | CU-07 | V-04 | E20 | Hecho sin interfaz |
| RF-11 | Tablero | F | OE-4 | CPF-11 | CU-07 | V-04 | E20, E09, E12 | Pendiente en parte (criterios 1 y 2) |
| RF-12 | Consentimiento, aviso de privacidad y advertencias | A | OE-3 | CPF-12 | CU-01, CU-02, CU-09, CU-10 | V-02, V-03, V-11; avisos en V-04 a V-06 | E02, E03, E06, E07 | Pendiente en parte (criterios 1, 2 y 4) |
| RF-25 | Intermediarios | B | OE-3 | CPF-25 | CU-04 | V-09 | E10, E11 | Hecho sin interfaz |
| RF-26a | Vencimiento de los CETES | E | OE-4 | CPF-26a | CU-05, CU-06, CU-07 | V-05, V-07 | E18, E19, E20 | Hecho sin interfaz |
| RF-26b | Valor estimado de los CETES antes del vencimiento | E | OE-4 | CPF-26b | CU-06, CU-07 | V-05, V-04 | E19, E20 | Hecho sin interfaz |
| RF-28 | Saldo no negativo por intermediario | D | OE-3 | CPF-28 | CU-12 (dentro de CU-05) | V-07 | E18 | Hecho sin interfaz |
| RF-30 | Tasas reales de CETES | G | OE-4 | CPF-30 | CU-11 | Sin pantalla propia | Semillas | Hecho y verificado |
| RF-31 | Procedencia de cada dato | G | OE-4 | CPF-31 | CU-06, CU-07, CU-11 | V-04, V-05 | E19, E20 | Pendiente en parte (criterios 2 y 3) |

Áreas: A, cuenta, consentimiento y aislamiento; B, portafolios e intermediarios; C, catálogo; D, transacciones; E, posiciones y valuación; F, indicadores y tablero; G, datos de mercado y procedencia. Fuentes: SRS 3.2 (OE y prueba), 4.1 (casos de uso) y 4.5.2 (pantallas y operaciones de la API).

### 3.2 Reglas que valen para todas las capacidades

- Sesión: toda operación exige sesión iniciada, salvo el registro, el inicio y el cierre de sesión, la consulta del aviso de privacidad y el diagnóstico `/health`. Sin sesión, la API responde 401 (SRS 4.5.2).
- Lo ajeno es inexistente: la información de otra cuenta recibe la misma respuesta que un recurso que no existe (404) y nada cambia (RF-02; RNF-03).
- Un rechazo no deja rastro: ninguna solicitud rechazada registra, modifica ni elimina nada, y la respuesta informa el motivo, salvo cuando el dato es ajeno (SRS 4.1, CU-05).
- Sin redondeo de lo capturado: un valor con más decimales que los permitidos, o una fecha inválida, se rechaza; nunca se redondea. Todo dato aceptado, salvo la contraseña, se recupera tal como se capturó (RD-13 y RD-14).
- Nombres únicos: el correo de cada cuenta, y el nombre de cada portafolio e intermediario dentro de una cuenta, son únicos sin distinguir mayúsculas ni espacios al inicio o al final (RD-03).
- Fechas: las transacciones y las fechas de corte de las posiciones deben caer en el intervalo de los datos semilla, del 10/09/2026 al 14/10/2026, y ninguna transacción puede ser posterior a su registro (RD-07; sección 5.6). Un periodo del tablero debe empezar el 11/09/2026 o después, porque su serie parte del cierre del día anterior, y terminar a más tardar el 14/10/2026; un periodo que empieza el 10/09 se rechaza con 422 `periodo_fuera_de_intervalo` (adoptado, por confirmar). Rige la hora de la Ciudad de México (RD-15).

### 3.3 Área A. Cuenta, consentimiento y aislamiento

#### RF-01 — Registro e inicio de sesión

Qué hace: permite a una persona registrarse con correo y contraseña e iniciar sesión con esas credenciales (SRS 3.2).

Reglas:

- El correo es único en el sistema, sin distinguir mayúsculas ni espacios iniciales o finales (RD-03).
- Ninguna cuenta existe sin su consentimiento registrado (RD-11).
- La contraseña solo se guarda en forma no reversible, distinta por cuenta, con Argon2id (RNF-04). De la persona solo se guardan el correo, la contraseña en esa forma y el estado de la cuenta, activa o bloqueada (SRS 3.4.1).

Criterios de aceptación (SRS 3.2):

1. Con un correo no registrado, una contraseña que cumple la política y el consentimiento de RF-12, se crea la cuenta, y con esas credenciales se inicia sesión.
2. Si un correo ya está registrado, se rechaza registrarlo otra vez con otras mayúsculas o con espacios al inicio o al final; con esas mismas variantes y su contraseña sí se inicia sesión (RD-03). El SRS lo ejemplifica con un correo ficticio.
3. Se rechazan sin efecto un correo sin sintaxis válida, una contraseña fuera de la política, un registro sin consentimiento (RD-11) y un inicio de sesión con credenciales incorrectas.

Verificación: CPF-01, en `backend/tests/cuentas/test_cpf01_registro_sesion.py` (12 pruebas). La cookie de sesión y el control de origen tienen además `backend/tests/cuentas/test_cookie_origen.py` (10) y `test_dependencias.py` (5); la contraseña, CPNF-04 (sección 6).

Adoptado, por confirmar (el SRS deja abiertas estas decisiones):

- Política de contraseña: de 15 a 128 caracteres después de normalizarla (NFKC), sin reglas de composición y distinta del correo. El SRS recomienda 15 caracteres o más.
- Solo se valida la sintaxis del correo, con 254 caracteres o menos.
- El inicio de sesión responde el mismo error 401 ante cualquier fallo, incluida una cuenta bloqueada. El registro informa el motivo por campo y responde 409 si el correo ya existe.
- El registro responde 201 y no abre la sesión.
- La sesión dura 480 minutos sin renovarse (configurable de 5 a 1440).

No está por confirmar, porque lo decidió el estudiante: Argon2id con m = 19456 KiB, t = 2 y p = 1, el mínimo que exige RNF-04.

Estado: implementado y verificado en la API (E03 a E06). Pendientes: las pantallas V-01 (inicio de sesión) y V-02 (registro).

#### RF-02 — Aislamiento de la información de cada usuario

Qué hace: cada usuario autenticado solo accede a sus propios portafolios, intermediarios, transacciones y posiciones (SRS 3.2).

Reglas:

- Cada portafolio, intermediario y registro de consentimiento pertenece a un solo usuario, y cada transacción, al usuario de su portafolio (RD-01).
- El portafolio y el intermediario de una transacción deben ser del mismo usuario (RD-02).
- Sin sesión, o con la sesión de otra cuenta, la solicitud se rechaza sin consultar, registrar, modificar ni eliminar nada y sin revelar si la información existe (RNF-03).
- El aislamiento es horizontal, entre cuentas equivalentes, sin roles (SRS 2.3; X-02).

Criterios de aceptación (SRS 3.2):

1. Con dos usuarios, A y B, que tienen portafolios e intermediarios con el mismo nombre y transacciones del mismo instrumento, las listas, posiciones e indicadores de A solo contienen datos de A.
2. Toda operación de A sobre datos de B, incluida una transacción con un intermediario de B (RD-02), recibe la respuesta de un recurso inexistente y no cambia nada. Sin sesión, la operación se rechaza (RNF-03).

Verificación: CPF-02, en `backend/tests/api/test_cpf02_propiedad.py` (3 pruebas): la respuesta 404 a un dato de B es idéntica, byte por byte, a la de un identificador inexistente, y la base no cambia. CPNF-03 (`backend/tests/no_funcionales/test_cpnf03.py`) recorre todas las operaciones de la API sin sesión y con sesión ajena.

Estado: implementado y verificado en la API. Pendiente: la pantalla V-12 («No encontrado»).

#### RF-12 — Consentimiento, aviso de privacidad y advertencias de uso

Qué hace: recaba el consentimiento expreso del usuario para tratar sus datos personales, financieros y patrimoniales; pone a su disposición el aviso de privacidad; le permite revocar el consentimiento en cualquier momento, y muestra a la vista que la información no constituye asesoría de inversión y que las valuaciones son estimaciones informativas, no precios oficiales (SRS 3.2).

Reglas:

- Los registros de consentimiento y de revocación no se modifican ni se eliminan (RD-11).
- Los momentos se guardan con zona horaria; rige la hora de la Ciudad de México (RD-15).
- Al revocar, la cuenta se bloquea de inmediato; su supresión al concluir el bloqueo tiene un plazo por confirmar con la empresa (RD-23).
- Marco legal: Ley Federal de Protección de Datos Personales en Posesión de los Particulares (SRS 2.4, R-03). Las valuaciones son estimaciones informativas (R-11).

Criterios de aceptación (SRS 3.2):

1. El registro exige marcar el consentimiento, cuya casilla aparece sin marcar (RD-11). Se guardan su momento (RD-15), su medio y la versión del aviso, y se conserva el texto de esa versión.
2. El aviso de privacidad de demostración se puede leer antes de registrarse y con sesión, y explica cómo revocar el consentimiento.
3. Al revocar, la revocación queda registrada y la cuenta se bloquea: la sesión termina y no se puede abrir otra (RD-23).
4. El tablero y las vistas de posiciones y de transacciones muestran a la vista los dos avisos: que la información no constituye asesoría de inversión y que las valuaciones son estimaciones informativas, no precios oficiales (R-11).

Verificación: CPF-12, en `backend/tests/cuentas/test_cpf12_consentimiento.py` (3 pruebas): aviso con y sin sesión, registro del consentimiento con su medio, momento y versión, y revocación con bloqueo.

Adoptado, por confirmar:

- El MVP solo bloquea la cuenta; la supresión de los datos queda fuera del MVP.
- Revocar exige una confirmación expresa en la solicitud.
- El registro debe indicar la versión del aviso que leyó la persona; si ya no es la vigente, responde 409. Sin aviso vigente, responde 503.
- Los textos de los avisos viven en el cliente. El SRS 4.5.1 propone: «La información de este sistema no constituye asesoría de inversión.» y «Las valuaciones son estimaciones informativas, no precios oficiales, y no sustituyen el estado de cuenta de tu intermediario.» El texto de la casilla de consentimiento sigue abierto.

Estado: implementado y verificado en la API (E02, E03, E06 y E07), y el criterio 3 se cumple completo. Pendiente lo que depende del cliente: la casilla sin marcar en pantalla (criterio 1), la lectura del aviso en la interfaz (criterio 2), los avisos visibles (criterio 4) y las pantallas V-02, V-03 y V-11.

### 3.4 Área B. Portafolios e intermediarios

#### RF-03 — Gestión de portafolios

Qué hace: permite crear, consultar, modificar y eliminar portafolios identificados por nombre y divisa base (SRS 3.2).

Reglas:

- Nombre único en la cuenta, sin distinguir mayúsculas ni espacios iniciales o finales (RD-03).
- La divisa base solo puede ser MXN (RD-08).
- Al eliminar un portafolio, previa confirmación expresa, se eliminan sus transacciones y se conservan los intermediarios (RD-10).
- El portafolio no maneja efectivo, y sus posiciones e indicadores no se guardan: se calculan (SRS 3.4.1 y 3.4.3). Los portafolios no se consolidan entre sí (X-06).

Criterios de aceptación (SRS 3.2):

1. Se crea un portafolio con un nombre y la divisa MXN, la única que se ofrece (RD-08), y la consulta muestra ambos datos. Modificarlo solo cambia su nombre.
2. Si la cuenta ya tiene un portafolio «Retiro», se rechaza crear o renombrar otro como « retiro » o con nombre vacío (RD-03). Otro usuario sí puede usar «Retiro».
3. Eliminar pide confirmación expresa. Si se cancela, nada cambia; si se confirma, se eliminan el portafolio y sus transacciones y se conservan los intermediarios (RD-10).

Verificación: CPF-03, en `backend/tests/api/test_cpf03_portafolios.py` (5 pruebas).

Adoptado, por confirmar: la confirmación se da escribiendo el nombre del portafolio en la solicitud de eliminación; si no coincide, responde 422 y nada cambia. Los nombres tienen 120 caracteres o menos, sin caracteres de control.

Estado: implementado y verificado en la API (E12 a E16). Pendiente: la pantalla V-08, con el diálogo de confirmación y la opción de cancelar.

#### RF-25 — Intermediarios

Qué hace: permite a cada usuario registrar y consultar los intermediarios con los que mantiene sus inversiones, identificados por un nombre único dentro de su cuenta (SRS 3.2).

Reglas: nombre único en la cuenta (RD-03), guardado tal como se capturó (SRS 3.4.1); los intermediarios no se modifican ni se eliminan (RD-09) y se conservan al eliminar un portafolio (RD-10). No se mide rendimiento ni riesgo por intermediario (X-05).

Criterios de aceptación (SRS 3.2):

1. «Casa A» se registra y se consulta tal como se capturó, y la lista solo muestra los intermediarios del usuario.
2. En la misma cuenta se rechazan «casa a», « Casa A » y un nombre vacío (RD-03). Otra cuenta sí puede usar «Casa A».
3. No se puede modificar ni eliminar un intermediario (RD-09), y se conserva al eliminar un portafolio (RD-10).

Verificación: CPF-25, en `backend/tests/api/test_cpf25_intermediarios.py` (3 pruebas). La API no ofrece operaciones para modificar ni eliminar intermediarios.

Estado: implementado y verificado en la API (E10 y E11). Pendientes: la pantalla V-09 y el diálogo de alta dentro de V-07.

### 3.5 Área C. Catálogo

#### RF-04 — Catálogo de instrumentos

Qué hace: permite consultar el catálogo de instrumentos con su clave, nombre y clase de activo. Cada emisión de CETES es un instrumento propio, con clave «BI» seguida de su fecha de vencimiento en formato AAMMDD, su valor nominal y su fecha de vencimiento (SRS 3.2).

Reglas: cada clave es única y la de una emisión corresponde a su vencimiento; ninguna emisión tiene precios de cierre (RD-04). Nadie modifica el catálogo (RD-09) y el usuario no da de alta instrumentos (S-09). El valor nominal es mayor que cero, con 2 decimales (RD-06 y RD-13).

Criterios de aceptación (SRS 3.2):

1. Cada instrumento muestra su clave, su nombre y una sola de cuatro clases (acción, ETF, FIBRA o CETES), sin claves repetidas (RD-04).
2. Cada emisión de CETES muestra un valor nominal de 10.00 y su vencimiento, y su clave es «BI» más ese vencimiento en AAMMDD; por ejemplo, el vencimiento del 12/11/2026 da BI261112.
3. Los demás instrumentos llevan clave ficticia y marca de demostración, y nadie modifica el catálogo (RD-09).

Verificación: CPF-04, en `backend/tests/api/test_cpf04_catalogo.py` (3 pruebas): sin sesión responde 401, el catálogo coincide con las semillas y la API no ofrece operaciones de escritura sobre él.

Adoptado, por confirmar: las claves ficticias llevan el prefijo «DEMO», como recomienda el SRS. La consulta del catálogo exige sesión; el SRS deja abierto si CU-08 la exige.

Datos: los 7 instrumentos de la sección 5.1.

Estado: implementado y verificado en la API (E08). Pendiente: la pantalla V-10, con la marca de demostración visible.

### 3.6 Área D. Transacciones

#### RF-05 — Registro y consulta de transacciones

Qué hace: permite registrar y consultar las transacciones de compra y venta del portafolio, con su intermediario, instrumento, fecha de concertación, cantidad de títulos, precio por título e importe de las comisiones de la operación con su IVA. Con ellos calcula el costo por título de cada compra y el ingreso por título de cada venta (SRS 3.2):

- costo por título = (títulos × precio + importe) / títulos;
- ingreso por título = (títulos × precio − importe) / títulos.

Reglas:

- Portafolio e intermediario del mismo usuario (RD-02). Cantidades y precios mayores que cero; el sentido lo da el tipo, compra o venta (RD-06).
- La fecha no puede ser posterior al registro y debe caer en el intervalo de las semillas (RD-07).
- Títulos enteros y precios con hasta 7 decimales; lo que exceda se rechaza sin redondear (RD-13 y RD-14).
- Ninguna transacción se modifica ni se elimina, salvo al eliminar su portafolio (RD-09 y RD-10).
- Solo se registran operaciones ya realizadas, capturadas a mano en un formulario guiado (R-02; X-01; SRS 2.3). El costo o ingreso por título se calcula y no se guarda (SRS 3.4.3).

Criterios de aceptación (SRS 3.2):

1. Comprar 100 títulos a 50.00 con un importe de comisiones de 14.50 da un costo por título de 50.145. Vender 100 a 55.00 con 15.95 da un ingreso por título de 54.8405. Ambas transacciones se consultan sin alteración (RD-14).
2. Se rechazan sin redondear ni registrar (RD-06, RD-13 y RD-14): títulos no enteros o no positivos; un precio no positivo o con más de 7 decimales; un importe negativo; la fecha 31/11/2026, y una venta cuyo importe sea igual o mayor que títulos × precio.
3. Se rechazan las fechas posteriores al registro y las que caen fuera del intervalo de las semillas (RD-07 y RD-15). Ninguna transacción se modifica ni se elimina, salvo al eliminar su portafolio (RD-09 y RD-10).

Verificación: CPF-05, en `backend/tests/api/test_cpf05_transacciones.py` (8 pruebas). Incluye registrar por la API las 16 transacciones del conjunto de referencia, T01 a T16, con su costo o ingreso por título esperado, y rechazar los candidatos N1 a N6 (sección 5.8). El cálculo también se prueba en el motor (`backend/tests/motor/test_criterios_3_2.py`).

Adoptado, por confirmar:

- Solo hay dos tipos de transacción: compra y venta.
- Importe de comisiones con hasta 2 decimales; admite 0. En una venta debe ser menor que títulos × precio.
- Límites de entrada: títulos de 1 a 2,147,483,647; precio menor que 10¹¹; importe menor que 10¹⁶.
- El costo o ingreso por título se presenta con hasta 7 decimales, sin ceros finales y con al menos 2 (por ejemplo, «50.145» y «54.8405»).
- El SRS deja abierto si el formulario muestra una revisión antes de registrar.

Estado: implementado y verificado en la API (E17 y E18). Pendientes: las pantallas V-06 (lista de transacciones) y V-07 (registro).

#### RF-28 — Saldo no negativo por intermediario

Qué hace: rechaza el registro de una transacción que deje negativo, en cualquier fecha, el saldo de un instrumento con un intermediario dentro del portafolio, aunque la posición consolidada alcance (SRS 3.2).

Reglas: no hay ventas en corto (X-04). El saldo se calcula dentro de cada portafolio, aunque el intermediario se comparta entre portafolios (SRS 3.4.3; X-06). El mismo día, las compras se aplican antes que las ventas (regla de RF-08).

Criterios de aceptación (SRS 3.2):

1. Con 100 títulos con un intermediario y 50 con otro, vender 120 con el primero se rechaza aunque la posición sea 150, y vender 100 se acepta.
2. Con una compra de 100 el día 1 y una venta de 80 el día 10, una venta de 50 fechada el día 5 se rechaza, porque el día 10 el saldo sería −30.
3. Los títulos del mismo instrumento en otro portafolio no cubren la venta. El rechazo no registra nada e informa el motivo.

Verificación: CPF-28, en `backend/tests/api/test_cpf28_saldo.py` (5 pruebas), que incluye dos ventas simultáneas de las que solo una debe pasar; además, las pruebas `test_rf28_*` del motor. En el conjunto de referencia se rechazan N1, N2 y N3 y se acepta el caso C1 (sección 5.8).

Estado: implementado y verificado en la API. La API responde 409 con el código `saldo_negativo`, la fecha del primer saldo negativo y el saldo que resultaría. Pendiente: mostrar el motivo junto al campo en V-07.

### 3.7 Área E. Posiciones y valuación, con CETES

#### RF-06 — Posición vigente

Qué hace: determina, a una fecha de corte, la posición de cada instrumento del portafolio como la suma de sus saldos con cada intermediario, derivados del historial de transacciones (SRS 3.2).

Reglas: se cuenta por fecha de concertación, con corte inclusivo y sin efectivo; la posición suma los saldos por intermediario y no cuenta las emisiones vencidas (SRS 3.2, «Reglas de cálculo»). La posición no se captura ni se almacena (SRS 3.4.3).

Criterios de aceptación (SRS 3.2):

1. Con 100 títulos con un intermediario y 50 con otro, la posición es 150; tras vender 30 con el primero, es 120.
2. Cuenta lo fechado el mismo día de corte: con una sola compra de 100 del día 5, la posición al día 5 es 100, y al día 4 es 0.
3. En el conjunto de referencia, cada posición coincide con la esperada y es idéntica en cada vista que la presenta (RNF-02). Los títulos en otro portafolio no la cambian (X-06).

Verificación: CPF-06, en `backend/tests/api/test_cpf06_posiciones.py` (4 pruebas); las pruebas `test_rf06_*` del motor, y CPNF-01 y CPNF-02 en `backend/tests/referencia/`.

Estado: implementado y verificado en la API (E19 y E20). Pendiente: la pantalla V-05.

#### RF-08 — Valor de mercado y resultado no realizado

Qué hace: calcula el valor de mercado y el resultado no realizado de cada posición y del portafolio a una fecha, con el costo asignado por costo promedio ponderado dentro de cada intermediario (SRS 3.2). Las fórmulas están en la sección 4.3.

Criterios de aceptación (SRS 3.2):

1. Con un intermediario, compras de 100 títulos a 50.00 (importe 14.50) y de 100 a 60.00 (importe 18.56) y un cierre de 58.00, el resultado no realizado es 566.94. Tras vender 50, a cualquier precio, es 425.21 (425.205 sin redondear; RD-16).
2. Si esas compras se hacen con intermediarios distintos y la venta con el primero, el resultado es 174.19, no 425.21 (que sería el del promedio consolidado).
3. Tras la primera compra, se compran 100 a 60.00 (importe 18.56) y se venden 100 un mismo día posterior, con ese intermediario. Con el mismo cierre, el resultado es 283.47, no −218.56, porque las compras del día se aplican antes que las ventas.
4. Si no hay cierre en la fecha, rige el último anterior, y los CETES se valúan con RF-26b. En el conjunto de referencia, cada cifra queda a 0.01 o menos (RNF-01).

Verificación: CPF-08, con las pruebas `test_rf08_crit1` a `test_rf08_crit4` de `backend/tests/motor/test_criterios_3_2.py`, y CPNF-01 para el conjunto de referencia, en el motor (`backend/tests/motor/test_oraculo_5_2.py`) y por la API (`backend/tests/referencia/test_cpnf01.py`).

Estado: implementado y verificado en el motor y en la API (E19 y E20). Pendientes: las pantallas V-05 y V-04. La ficha detallada de RF-08 del SRS 3.2 sigue vacía.

#### RF-26a — Vencimiento de los CETES

Qué hace: en la fecha de vencimiento de cada emisión de CETES liquida a su valor nominal los títulos que siguen en posición, trata ese importe como un retiro del portafolio y rechaza transacciones de la emisión con fecha igual o posterior a su vencimiento (SRS 3.2).

Reglas: la liquidación es a valor nominal, antes de la retención de ISR; la reinversión se registra como una compra (S-14). La liquidación se calcula y no se guarda (SRS 3.4.3). Ninguna transacción de CETES puede estar a más de 728 días de su vencimiento (RD-05; el límite está abierto en el SRS).

Criterios de aceptación (SRS 3.2):

1. Con 1,000 títulos de una emisión con un intermediario y 500 con otro, la posición es 0 desde el vencimiento, y ese día RF-09 cuenta un retiro de 15,000.00, sin descontar ISR y sin guardarlo. Si antes hubo una venta parcial, solo se liquida el resto.
2. Se rechaza toda transacción de la emisión fechada en su vencimiento o después.
3. La reinversión es una compra que registra el usuario; el sistema no crea transacciones.

Verificación: CPF-26a, en `backend/tests/api/test_cpf26a_registro.py` (3 pruebas) y `backend/tests/api/test_cpf26_valuacion.py` (2), más las pruebas `test_rf26a_*` del motor. En el conjunto de referencia, BI261008 vence el 08/10/2026 con un retiro de 20,000.00, y la venta N4, fechada ese día, se rechaza.

Adoptado, por confirmar: una emisión vencida aparece en las posiciones marcada como vencida y sin valuación. El límite de RD-05 se aplica como 730 días, no 728.

Estado: implementado y verificado. Pendiente: su presentación en V-05 y el motivo de rechazo en V-07.

#### RF-26b — Valor estimado de los CETES antes del vencimiento

Qué hace: estima el valor de las posiciones en CETES antes de su vencimiento con P = VN / (1 + r·d/360), donde d son los días naturales por vencer y r es la tasa de referencia más reciente, interpolada linealmente a d días (SRS 3.2). El detalle está en la sección 4.3.

Criterios de aceptación (SRS 3.2):

1. En una prueba del motor, con tasas ilustrativas de 7.00000 % a 28 días y 7.20000 % a 91 días efectivos y d = 50, se obtienen r = 7.0698412698… % y P = 9.9027626 (RD-16).
2. Con d = 10 rige la tasa del plazo más corto (P = 9.9805933), y con d = 100, la del más largo (P = 9.8039216).
3. Rige la última colocación de cada plazo con fecha igual o anterior a la de valuación. En el conjunto de referencia, cada posición queda a 0.01 o menos (RNF-01).

Verificación: CPF-26b, con las pruebas `test_rf26b_*` del motor (criterios 1 y 2) y `backend/tests/api/test_cpf26_valuacion.py` (criterio 3): al 07/10 rige la colocación del 01/10, y al 14/10, la del 08/10; la del 15/10 ya está en la base, pero no rige. El conjunto de referencia incluye 91 valuaciones diarias de CETES.

Adoptado, por confirmar: si dos colocaciones tienen el mismo plazo efectivo, rige la más reciente y, si persiste el empate, la de menor plazo nominal. La tasa interpolada se presenta con 5 decimales. El SRS deja abierto si RF-26b tiene ficha propia.

Estado: implementado y verificado. Pendiente: presentarla en V-05 con el rótulo de estimación (SRS 4.5.1).

### 3.8 Área F. Indicadores y tablero

#### RF-09 — Rendimiento ponderado por tiempo (TWR)

Qué hace: calcula el TWR del portafolio para un periodo (SRS 3.2). Las fórmulas están en la sección 4.3.

Criterios de aceptación (SRS 3.2):

1. Sin compras, ventas ni vencimientos, el TWR es el valor final entre el inicial, menos 1, sin anualizar: de 10,000.00 a 10,100.00 en 30 días da 1.00 %.
2. Una compra es una aportación de títulos × precio más su importe, y una venta, un retiro de títulos × precio menos su importe (con los datos de RF-05, 5,014.50 y 5,484.05). Un vencimiento es un retiro de títulos × 10.00 (RF-26a). La baja de valor que causa un retiro no reduce el TWR.
3. Se rechazan un periodo cuya fecha final es anterior a la inicial y las fechas fuera de las semillas. En el conjunto de referencia, el TWR queda a 0.001 puntos porcentuales o menos (RNF-01).

Verificación: CPF-09, con las pruebas `test_rf09_*` del motor, los rechazos N7 y N8 en `backend/tests/api/test_cpf11_tablero.py` y CPNF-01. En el conjunto de referencia, el periodo P1-A (Principal, del 11/09 al 14/10/2026) da TWR = 4.392808406… %.

Adoptado, por confirmar: un periodo inválido responde 422. El corte del tablero es siempre el fin del periodo. Por omisión, el periodo va del día siguiente al inicio de las semillas hasta el menor entre su fin y la fecha de hoy; hoy, del 11/09 al 14/10/2026.

Estado: implementado y verificado. Pendiente: la presentación en V-04. La ficha detallada de RF-09 sigue vacía en el SRS.

#### RF-10 — Máxima caída

Qué hace: calcula la máxima caída del rendimiento acumulado ponderado por tiempo del portafolio dentro de un periodo (SRS 3.2). Se mide sobre el índice del TWR, no sobre el valor, para que las aportaciones y los retiros no creen caídas. Las fórmulas están en la sección 4.3.

Criterios de aceptación (SRS 3.2):

1. En una prueba del motor, con el índice 1 → 1.10 → 0.99 → 1.05 → 1.12 → 1.064, la máxima caída es −10.00 %. Ni la recuperación ni la segunda caída, de −5.00 %, la cambian.
2. Una serie que no baja da 0.00 %, y los flujos no crean caídas.
3. En el conjunto de referencia queda a 0.001 puntos porcentuales o menos (RNF-01).

Verificación: CPF-10, con las pruebas `test_rf10_*` del motor y CPNF-01. En el conjunto de referencia, P1-A da −6.680477… %, con pico el 16/09/2026 y valle el 23/09/2026, y P1-D (del 09/10 al 12/10) da 0.

Estado: implementado y verificado. Pendiente: la presentación en V-04. La ficha detallada de RF-10 sigue vacía en el SRS.

#### RF-11 — Tablero

Qué hace: presenta un tablero con los indicadores calculados y la evolución del valor del portafolio en el tiempo (SRS 3.2). Es el punto de entrada habitual al sistema (SRS 2.2, función F-5, «Presentación de resultados») y debe entenderse sin contexto de sesiones previas (SRS 2.3).

Reglas: cifras dentro de RNF-01 e idénticas entre vistas (RNF-02). Junto a cada indicador van su unidad, su fecha de corte o periodo y su definición (RNF-07, que se verifica el 23/10/2026).

Criterios de aceptación (SRS 3.2):

1. Para el conjunto de referencia, el tablero muestra el valor de mercado, el resultado no realizado, el TWR y la máxima caída a la fecha de corte y del periodo indicados, dentro de RNF-01 y RNF-02.
2. La gráfica tiene un punto por día de la serie de RF-09, y el punto del día de corte es igual al valor mostrado.
3. Sin transacciones, el tablero abre sin error.

Verificación: CPF-11, en `backend/tests/api/test_cpf11_tablero.py` (6 pruebas): los cuatro indicadores con su unidad y su fecha o periodo; un punto por día natural, con el último igual, como texto, al valor de mercado y al total de las posiciones; el estado «sin datos», y los rechazos N7 y N8. CPNF-02 (`backend/tests/referencia/test_cpnf02.py`) comprueba que las cifras coinciden entre las operaciones de la API.

Lo que devuelve hoy la API del tablero (E20) para P1-A: TWR 4.39 %; máxima caída −6.68 %, con pico el 16/09 y valle el 23/09; valor de mercado 58,940.88 al 14/10/2026, igual al último punto de una serie de 35 puntos cuyo primer punto es 49,929.06. Al mismo corte, las posiciones (E19) dan un costo de 56,307.89 y un resultado no realizado de 2,632.99.

Adoptado, por confirmar: sin transacciones hasta el fin del periodo, el tablero responde con el estado «sin datos», como recomienda el SRS.

Conflicto abierto en el criterio 1: pide la tolerancia de RNF-01 (0.001 puntos porcentuales), pero el tablero presenta los por cientos con 2 decimales, como manda RD-13. En P1-A muestra 4.39 y el valor esperado es 4.3928 %; 9 de las 12 cifras de por ciento del conjunto de referencia quedan a más de 0.001 puntos de lo que se muestra; solo quedan dentro las máximas caídas de P1-A y P1-B (−6.680477 %, que se muestra −6.68) y la de P1-D (0.00) (sección 5.8). La tolerancia sí se cumple en las cifras del motor (CPNF-01). Hay dos salidas, sin decidir: precisar el criterio para que la tolerancia aplique a las cifras del motor, o presentar los por cientos con 3 decimales.

Estado: implementado y verificado en la API. Pendiente la pantalla V-04: la gráfica (Recharts 3.10.1 está instalado, pero aún no se usa), las definiciones de RNF-07, los avisos, la marca de demostración y la procedencia.

### 3.9 Área G. Datos de mercado y procedencia

#### RF-07 — Precios de cierre sintéticos

Qué hace: incorpora los precios de cierre históricos desde un conjunto de datos semilla sintético, con fecha fija, y los señala en la interfaz como datos de demostración (SRS 3.2).

Reglas: ninguna emisión de CETES tiene precios de cierre (RD-04); precios con hasta 7 decimales (RD-13); cada precio proviene de una sola carga (RD-17); a lo más un precio por instrumento, fecha y fuente (RD-19); el intervalo de la semilla solo cambia con una versión nueva del conjunto de referencia (RD-21). No se usan precios reales porque su licencia no lo permite (R-04, R-05 y R-13; X-07; S-05).

Criterios de aceptación (SRS 3.2):

1. Al instalar, los precios son los de la semilla, ligados a su carga. Volver a cargarla no los duplica ni los altera (RD-19 y RD-21).
2. No hay precios de CETES (RD-04), ni precios no positivos, con más de 7 decimales, en días sin operaciones de 2026 o fuera del intervalo de las semillas.
3. El tablero y la vista de posiciones señalan esos precios como datos de demostración.

Verificación: CPF-07, en `backend/tests/api/test_cpf07_30_31_semillas.py` (5 pruebas, compartidas con CPF-30 y CPF-31): 71 precios sintéticos y volver a ejecutar la carga no cambia conteos ni huellas. La API marca cada precio y cada respuesta que contiene datos de demostración.

Datos: sección 5.2.

Estado: criterios 1 y 2 implementados y verificados. Pendiente el criterio 3: señalar los datos de demostración en V-04 y V-05. Desviación por registrar en el SRS: la carga la hace un script SQL (`backend/04_cargar_semillas.sql`), no un componente «Cargas» en Python como describe el SRS 4.2.

#### RF-30 — Tasas reales de CETES

Qué hace: incorpora, desde un conjunto de datos semilla construido con las series que publica el Banco de México en su Sistema de Información Económica (SIE), las tasas de las subastas primarias de CETES a 28, 91, 182, 364 y 728 días, con el plazo efectivo de cada colocación (SRS 3.2).

Reglas: cada tasa lleva su plazo nominal y su plazo efectivo, y sin plazo efectivo no se carga (RD-18); a lo más una tasa por plazo y fecha de colocación (RD-19); una observación sin dato (N/E) cuenta como omitida y no se guarda (RD-20); tasas en por ciento anual con 5 decimales (RD-13).

Criterios de aceptación (SRS 3.2):

1. Al instalar están las tasas de los cinco plazos de la semilla, con sus plazos nominal y efectivo (RD-18). Cada plazo empieza con una colocación anterior al intervalo.
2. Ninguna tasa guardada proviene de una observación N/E ni carece de plazo efectivo, y la carga registra cuántas omitió (RD-18 y RD-20).
3. No hay dos tasas del mismo plazo y fecha de colocación, y recargar no las duplica (RD-19).

Verificación: CPF-30, en `backend/tests/api/test_cpf07_30_31_semillas.py`: 32 tasas de cinco plazos, cada uno con una colocación anterior al 10/09/2026.

Datos: sección 5.3.

Estado: hecho y verificado. No tiene pantalla propia; sus tasas se ven en la procedencia de V-04 y V-05 (SRS 4.5.2). Pendiente de confirmar con una segunda fuente la tasa a 28 días del 10/09/2026 (sección 12.5).

#### RF-31 — Procedencia de cada dato

Qué hace: registra, para cada precio y cada tasa, su fuente, su fecha de carga y su licencia, y muestra junto a cada dato externo su fuente y la fecha del dato; en las tasas, «Fuente: Banco de México, https://www.banxico.org.mx» (SRS 3.2).

Reglas: cada precio y cada tasa provienen de una sola carga (RD-17). Cada dato externo conserva su fuente, su fecha de carga y su licencia, con la atribución que esta exija (R-05). El Banco de México permite reutilizar su información citando la fuente y su dirección (SRS 2.5, D-03).

Criterios de aceptación (SRS 3.2):

1. Todo precio y toda tasa están ligados a una carga con fuente, fecha de carga y versión de licencia (RD-17).
2. Junto a cada valuación de CETES aparecen «Fuente: Banco de México, https://www.banxico.org.mx» y la fecha de colocación de las tasas usadas.
3. Junto a cada precio aparecen su fuente, señalada como datos de demostración, y la fecha del cierre usado, no la de valuación. (Ejemplo del SRS 5.2, no del criterio: el corte del 13/09/2026, domingo, usa el cierre del 11/09.)

Verificación: CPF-31, en `backend/tests/api/test_cpf07_30_31_semillas.py`: atribución del Banco de México, fechas de colocación y cierre del 11/09 para el corte del 13/09, todo en las respuestas de la API.

Adoptado, por confirmar: la licencia de la semilla sintética es la versión «1», propuesta al construir el conjunto de referencia (el SRS deja abierta esa licencia). La fecha de carga que se muestra es la del momento en que se ejecutó la carga.

Estado: criterio 1 hecho y verificado; los datos de los criterios 2 y 3 ya los entrega la API. Pendiente: mostrar la línea de fuente junto a cada dato en V-04 y V-05 (SRS 4.5.1, «Línea de fuente»).

---

## 4. Cómo calcula

### 4.1 Motor único

- Todas las métricas salen de un solo motor de cálculo en el servidor (`backend/app/motor/`). Ninguna vista ni el cliente web recalculan (SRS 2.1; README).
- El sistema solo guarda hechos: lo que captura el usuario y lo que publican las fuentes. Posiciones, importes, costos, valores, indicadores, valuación y liquidación de los CETES se derivan en cada consulta y no se almacenan (SRS 3.4.3).
- Los cálculos nunca consultan una fuente externa; solo leen la base de datos (SRS 3.4.8).
- Una sola función valúa las posiciones, y la usan tanto la consulta de posiciones como cada día de la serie del tablero. Por eso el total de un corte es el mismo valor del día en la serie (RNF-02).
- El motor solo usa la biblioteca estándar de Python, sin punto flotante binario; lo comprueba `backend/tests/motor/test_aislamiento.py` (46 pruebas).

### 4.2 Aritmética, precisión y redondeo

| Regla | Qué dice | Fuente |
|---|---|---|
| Representación | Todo número se guarda, se calcula y se intercambia en decimal, nunca en punto flotante binario, con al menos 28 dígitos significativos al calcular. | RD-12 |
| Escalas | Títulos enteros; precios con 7 decimales; valor nominal con 2; tasas con 5 decimales en por ciento anual; plazos en días enteros. Al presentarse, importes y por cientos van con 2 decimales. | RD-13 |
| Entrada | Un valor con más decimales que su escala, o una fecha inválida, se rechaza sin redondear. | RD-14 |
| Fechas | Las fechas de operación, cierre, colocación y vencimiento no llevan hora; los momentos de registro y carga se guardan con zona horaria. Rige la hora de la Ciudad de México. | RD-15 |
| Redondeo | Solo se redondea al presentar una cifra y al obtener el precio P de los CETES, a 7 decimales, siempre con la mitad alejándose de cero. | RD-16 |

En el código: el motor calcula con `decimal` a 28 dígitos y redondeo con la mitad alejándose de cero, en un contexto propio que no modifica el global. Dentro del motor solo se redondea P. El índice del TWR y las caídas se comparan a 20 dígitos solo para elegir el pico y el valle, de modo que un empate exacto no dependa del último dígito; ese valor nunca se guarda ni se presenta (adoptado, por confirmar).

### 4.3 Fórmulas

Transacciones (RF-05):

| Tipo | Costo o ingreso por título | Aportación al portafolio | Retiro del portafolio |
|---|---|---|---|
| Compra | (títulos × precio + importe) / títulos | títulos × precio + importe | 0 |
| Venta | (títulos × precio − importe) / títulos | 0 | títulos × precio − importe |

Saldo, costo y posición (RF-06, RF-08, RF-26a y RF-28). El cálculo lleva un registro por cada par (instrumento, intermediario) dentro del portafolio y procesa cada día, en este orden:

1. Vencimientos: si una emisión de CETES vence ese día, su saldo se liquida como retiro de saldo × 10.00, sin ISR, y saldo y costo quedan en 0 (RF-26a).
2. Compras del día, sumadas por par: con Q títulos comprados y K = suma de (títulos × precio + importe), el costo unitario pasa a c = (S × c + K) / (S + Q) y el saldo a S + Q.
3. Ventas del día: el saldo baja y el costo unitario no cambia; si el saldo llega a 0, el costo se reinicia.

Con eso:

- Posición de un instrumento = suma de sus saldos con cada intermediario, al corte, inclusive (RF-06).
- Costo total de un par = saldo × costo unitario. El código lo lleva acumulado (suma K en las compras y lo reduce en proporción en las ventas) para no perder un centavo al presentar.
- Valor de mercado = saldo × último precio de cierre con fecha igual o anterior a la de valuación, sin límite de antigüedad; en CETES, saldo × P (RF-08 y RF-26b). Si hay títulos y ningún cierre, la cifra no es calculable y la API responde 422 (RD-24).
- Resultado no realizado = valor de mercado − costo total (RF-08).
- Saldo no negativo: se rechaza la transacción si, con ella, el saldo de su par queda negativo en cualquier fecha (RF-28).

Valuación de los CETES (RF-26b):

- d = días naturales desde la fecha de valuación hasta el vencimiento, con d ≥ 1.
- Curva de tasas: por cada plazo nominal (28, 91, 182, 364 y 728 días), la colocación más reciente con fecha igual o anterior a la de valuación; los nodos se ordenan por plazo efectivo (R-14).
- r = la tasa del nodo si d coincide con un plazo efectivo; si d cae entre dos nodos, r = r_inf + (r_sup − r_inf) × (d − e_inf) / (e_sup − e_inf), sin redondear; si d queda fuera del rango, la tasa del extremo más cercano.
- P = 10.00 / (1 + (r / 100) × d / 360), redondeado a 7 decimales; valor = títulos × P.

TWR (RF-09):

- V(t) es el valor del portafolio al cierre del día t; A(t), las aportaciones del día, y R(t), los retiros del día (ventas y vencimientos).
- r(t) = [V(t) + R(t)] / [V(t−1) + A(t)] − 1. Si el denominador es 0, el factor del día es 1.
- La serie es diaria, en días naturales, desde el día base (el cierre del día anterior al inicio) hasta el fin del periodo, inclusive.
- TWR = Π[1 + r(t)] − 1, sin anualizar.

Máxima caída (RF-10):

- Índice: I(base) = 1 e I(t) = I(t−1) × [1 + r(t)]; el TWR es I(fin) − 1.
- Máxima caída = mín{ I(t) / máx[I(u), u ≤ t] } − 1, negativa o cero; el día base cuenta como primer máximo.
- Valle: la primera fecha en que se alcanza la máxima caída, es decir, el valor más negativo de I(t) / máx[I(u), u ≤ t] − 1. Pico: la fecha en que el índice alcanzó el máximo vigente en el valle; si alcanzó ese nivel en varias fechas, cuenta la más antigua (en P2-A, el 15/09 y no el 16/09; sección 5.8). Si la caída es 0, no hay pico ni valle.

Siguen abiertas en el SRS, y el conjunto de referencia las adoptó (sección 12.5): la fórmula de r(t) con factor 1 si el denominador es 0 y la serie en días naturales, que el SRS 3.2 recomienda; la serie que parte del día base y el índice 1 como primer máximo (SRS 3.2), y la regla de pico y valle (SRS 5.2). La fórmula de la máxima caída no está abierta.

### 4.4 Cómo se presentan las cifras

| Cifra | Presentación | Ejemplo |
|---|---|---|
| Títulos, días y plazos | Entero | 1000 |
| Importes: valor, costo, resultado, aportación y retiro | 2 decimales | 425.205 se presenta 425.21 |
| TWR y máxima caída | Por ciento con 2 decimales | −0.0668047… se presenta −6.68 |
| Costo o ingreso por título | Hasta 7 decimales, sin ceros finales y con al menos 2 | 50.145; 54.8405; 48.0388333 |
| Precio P de los CETES | 7 decimales | 9.9027626 |
| Tasa interpolada r | 5 decimales, en por ciento anual (adoptado, por confirmar) | 6.48429 |
| Precio, tasa y valor nominal capturados o cargados | Tal como se guardaron (RD-14) | 9.9516240 |

Las cifras viajan por la API como texto, sin separador de miles ni exponente, y el cero nunca lleva signo («0.00»). En este documento los importes llevan coma de miles para leerse mejor.

### 4.5 Límites conocidos del cálculo

- Las fichas detalladas de RF-06, RF-08, RF-09 y RF-10 del SRS 3.2 tienen título y siguen vacías; las reglas vigentes son las de «Reglas de cálculo para las fichas» y los criterios de 3.2.
- Un TWR que cae exactamente en medio punto de la segunda cifra decimal se presenta redondeado hacia cero: en un caso sintético con TWR exacto de 0.01005 se presenta 1.00 en vez de 1.01, por el último dígito del índice encadenado. No ocurre en el conjunto de referencia y la corrección está sin decidir.

---

## 5. Datos del MVP

### 5.1 Catálogo de instrumentos

Lo carga `backend/04_cargar_semillas.sql` desde `backend/tests/oraculo/entradas/instrumentos.csv`. El usuario no da de alta instrumentos (S-09).

| Clave | Nombre | Clase | Divisa | De demostración | Vencimiento | Valor nominal |
|---|---|---|---|---|---|---|
| DEMOACC | Acción de demostración | Acción | MXN | Sí | — | — |
| DEMOETF | ETF de demostración | ETF | MXN | Sí | — | — |
| DEMOFIB | FIBRA de demostración | FIBRA | MXN | Sí | — | — |
| BI261008 | CETES con vencimiento el 08/10/2026 | CETES | MXN | No | 08/10/2026 | 10.00 |
| BI261105 | CETES con vencimiento el 05/11/2026 | CETES | MXN | No | 05/11/2026 | 10.00 |
| BI261217 | CETES con vencimiento el 17/12/2026 | CETES | MXN | No | 17/12/2026 | 10.00 |
| BI270318 | CETES con vencimiento el 18/03/2027 | CETES | MXN | No | 18/03/2027 | 10.00 |

Las cuatro emisiones de CETES son reales; los otros tres instrumentos son ficticios. El generador de semillas (`backend/semillas/genera_semillas.py`) valida antes de escribir el script que la clave de cada emisión sea «BI» más su vencimiento, que su valor nominal sea 10.00 y que ninguna clave ficticia tenga forma de emisión.

### 5.2 Precios de cierre sintéticos (RF-07)

- 71 precios de demostración, del 10/09/2026 al 14/10/2026, solo en días con operaciones de 2026 (SRS 5.2).
- No son precios reales. La Bolsa Mexicana de Valores licencia sus datos de cierre por contrato y con pago, y los planes gratuitos de las API comerciales consultadas son de uso personal o no comercial (SRS 2.4, R-05).
- Fuente registrada: «Semilla sintetica de demostracion 077» (así, sin acentos).

| Instrumento | Precios | Mínimo | Máximo | Nota |
|---|---|---|---|---|
| DEMOACC | 24 | 90.4250 | 111.05 | |
| DEMOETF | 24 | 46.15 | 52.95 | |
| DEMOFIB | 23 | 22.8500 | 25.6225 | Sin cierre el 08/10, a propósito, para probar el uso del último cierre anterior |

### 5.3 Tasas de CETES del Banco de México (RF-30)

- 32 colocaciones reales de las subastas primarias, con su plazo efectivo, fechadas del 27/08/2026 al 15/10/2026, del cuadro CF107 del SIE, consultado el 5, el 6 y el 15 de octubre de 2026 (SRS 5.2).
- Series de tasa: SF43936, SF43939, SF43942, SF43945 y SF349785; series de plazo efectivo: SF43935, SF43938, SF43941, SF43944 y SF349778 (SRS 2.5, D-02).
- Atribución obligatoria: «Fuente: Banco de México, https://www.banxico.org.mx» (RF-31; D-03).
- En el MVP no hay consulta automática al SIE: la API del SIE solo sirvió para construir la semilla. La actualización diaria es RF-32, de la fase de refinamiento (SRS 2.4, R-08).

| Plazo nominal (días) | Colocaciones | Fechas de colocación (2026) | Tasas (% anual) | Plazos efectivos (días) |
|---|---|---|---|---|
| 28 | 8 | 27/08, 03/09, 10/09, 17/09, 24/09, 01/10, 08/10 y 15/10 | 6.13, 6.49, 6.25, 6.25, 6.15, 6.01, 6.09 y 6.25 | 28 en todas |
| 91 | 8 | Las mismas | 6.60, 6.54, 6.56, 6.66, 6.59, 6.73, 6.78 y 6.55 | 91 en todas |
| 182 | 8 | Las mismas | 6.72, 6.69, 6.78, 6.90, 6.91, 7.01, 6.91 y 6.79 | 175, 182, 175, 182, 175, 182, 175 y 182 |
| 364 | 4 | 03/09, 17/09, 01/10 y 15/10 | 7.00, 7.24, 7.44 y 7.11 | 350, 363, 349 y 364 |
| 728 | 4 | 27/08, 10/09, 24/09 y 08/10 | 7.87, 7.94, 8.01 y 7.98 | 707, 693, 679 y 721 |

Notas:

- Cada plazo empieza con una colocación anterior al intervalo de precios, como pide el criterio 1 de RF-30.
- La colocación del 15/10 se incluye a propósito: ya estaba publicada, pero no rige ninguna valuación del intervalo (R-14).
- La carga incorporó 32 observaciones y omitió 0; las semanas sin subasta de 364 y 728 días no aparecen como observaciones.
- De las 12 tasas que tienen una sola fuente, solo la de 28 días del 10/09/2026 (6.25 %) afecta las cifras del conjunto de referencia; está pendiente confirmarla con una segunda fuente (SRS 5.2).

### 5.4 Calendario de 2026

El conjunto de referencia incluye los 114 días sin operaciones de 2026: los 104 sábados y domingos y los días inhábiles que publicó la CNBV en el Diario Oficial de la Federación del 10/12/2025 (01/01, 02/02, 16/03, 02/04, 03/04, 01/05, 16/09, 02/11, 16/11 y 25/12; el 12/12 cae en sábado). En el intervalo de las semillas hay 24 días con operaciones; no hay precios el 16/09 (día inhábil) ni en fines de semana (`backend/tests/oraculo/README.md`).

### 5.5 Fuentes, licencias y cargas (RF-31)

| Fuente | Dirección | De demostración | Licencia (versión «1») | Atribución que se muestra |
|---|---|---|---|---|
| Banco de México | https://www.banxico.org.mx | No | Reproducir y usar la información que publica el Banco de México, con la sola condición de mencionar la fuente y su dirección de Internet (R-05; D-03) | «Fuente: Banco de México, https://www.banxico.org.mx» |
| Semilla sintetica de demostracion 077 | — | Sí | Datos sintéticos creados para el Proyecto 077: uso libre dentro de la aplicación y sus pruebas, solo como datos de demostración (adoptado, por confirmar) | «Datos de demostración: precios sintéticos, no son precios reales» |

| Carga | Fuente | Intervalo | Observaciones incorporadas | Omitidas |
|---|---|---|---|---|
| C-PRECIOS | Semilla sintética | 10/09/2026 a 14/10/2026 | 71 | 0 |
| C-TASAS | Banco de México | 27/08/2026 a 15/10/2026 | 32 | 0 |

### 5.6 Intervalo de las semillas

- El intervalo va del 10/09/2026 al 14/10/2026 (SRS 5.2; S-09). El sistema lo deriva de las cargas semilla y no lo guarda.
- Fuera de él se rechazan las transacciones y las fechas de corte (RD-07) y los periodos (RF-09, criterio 3); además, un periodo debe empezar a partir del 11/09/2026 (sección 3.2).
- Como hoy es posterior al 14/10/2026, toda transacción nueva debe fecharse dentro del intervalo, y el periodo por omisión del tablero va del 11/09 al 14/10/2026. La operación `GET /api/intervalo-datos` (E09) informa el intervalo, la fecha de hoy y las fechas por omisión.

### 5.7 Aviso de privacidad de demostración y cuentas

- El texto vive en `backend/semillas/aviso_privacidad_demo.md`, vigente desde el 16/10/2026 a las 00:00 (hora de la Ciudad de México). Lo carga el mismo script de semillas.
- Pide no capturar datos reales; describe los datos que se tratan y su finalidad; aclara que la información no constituye asesoría de inversión y que las valuaciones son estimaciones informativas; dice que los datos no se transfieren a terceros; explica que el consentimiento es expreso y que su revocación bloquea la cuenta de inmediato y es definitiva. El responsable del tratamiento, el plazo del bloqueo y el medio para los derechos ARCO están pendientes de definir con la empresa.
- El script de semillas no carga usuarios. Las cuentas de prueba se crean por la API, con correos ficticios (SRS 3.4.7; S-04; AC-07).

### 5.8 Conjunto de referencia (SRS 5.2)

#### Qué es y cómo se construyó

Es un escenario cuyas entradas se cargan en la base y cuyas cifras esperadas el motor debe reproducir: el valor resuelto de forma independiente que exige OE-5. Vive en `backend/tests/oraculo/` (`entradas/`, `esperados/`, `rechazos_rf28.csv` y `casos_positivos.csv`).

Se resolvió antes de programar el motor, por dos caminos que no comparten código con él ni entre sí: un libro de Excel con fórmulas visibles y 44 comprobaciones internas, y un programa en Python con `decimal` a 28 dígitos y otros algoritmos. Los dos caminos difieren a lo más 1.6 × 10⁻¹¹ pesos en importes y 4.2 × 10⁻¹⁴ puntos porcentuales en TWR y máxima caída, y coinciden en fechas, títulos y precios de CETES. Según el SRS 5.2, se elaboró con apoyo de Claude Code, de Anthropic, y lo revisó el estudiante (marcado ahí como por confirmar).

#### Escenario

Un usuario ficticio tiene dos portafolios en MXN, Principal y Secundario, y dos intermediarios, Casa A y Casa B, compartidos por ambos portafolios. Registra 16 transacciones del 10/09 al 08/10/2026. La serie diaria va del 10/09 (día base, índice 1) al 14/10/2026.

#### Transacciones T01 a T16

Entradas en `entradas/transacciones.csv`; importes derivados, sin redondear, en `esperados/transacciones.csv`. Fechas de 2026.

| Ref. | Portafolio | Intermediario | Instrumento | Tipo | Fecha | Títulos | Precio | Importe | Costo o ingreso por título | Aportación | Retiro |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| T01 | Principal | Casa A | DEMOACC | Compra | 10/09 | 200 | 99.95 | 57.97 | 100.23985 | 20,047.97 | 0 |
| T02 | Principal | Casa B | DEMOETF | Compra | 10/09 | 100 | 50.05 | 14.51 | 50.1951 | 5,019.51 | 0 |
| T03 | Principal | Casa A | BI261008 | Compra | 10/09 | 1,500 | 9.9516240 | 0.00 | 9.9516240 | 14,927.436 | 0 |
| T04 | Principal | Casa B | BI261008 | Compra | 10/09 | 1,000 | 9.9516240 | 0.00 | 9.9516240 | 9,951.624 | 0 |
| T05 | Principal | Casa A | DEMOFIB | Compra | 11/09 | 400 | 24.9825 | 28.98 | 25.05495 | 10,021.98 | 0 |
| T06 | Principal | Casa B | DEMOACC | Compra | 14/09 | 100 | 103.10 | 29.90 | 103.399 | 10,339.90 | 0 |
| T07 | Secundario | Casa A | DEMOACC | Compra | 14/09 | 150 | 103.60 | 45.07 | 103.9004666… | 15,585.07 | 0 |
| T08 | Principal | Casa A | BI261217 | Compra | 17/09 | 1,000 | 9.8344372 | 0.00 | 9.8344372 | 9,834.4372 | 0 |
| T09 | Principal | Casa B | BI270318 | Compra | 17/09 | 500 | 9.6629250 | 0.00 | 9.6629250 | 4,831.4625 | 0 |
| T10 | Principal | Casa A | DEMOFIB | Venta | 22/09 | 400 | 23.2075 | 26.92 | 23.1402 | 0 | 9,256.08 |
| T11 | Principal | Casa B | DEMOETF | Compra | 25/09 | 60 | 47.90 | 8.33 | 48.0388333… | 2,882.33 | 0 |
| T12 | Principal | Casa B | DEMOETF | Venta | 25/09 | 120 | 48.10 | 16.74 | 47.9605 | 0 | 5,755.26 |
| T13 | Principal | Casa A | BI261008 | Venta | 01/10 | 500 | 9.9883275 | 0.00 | 9.9883275 | 0 | 4,994.16375 |
| T14 | Principal | Casa A | DEMOACC | Venta | 02/10 | 80 | 104.20 | 24.17 | 103.897875 | 0 | 8,311.83 |
| T15 | Principal | Casa A | DEMOFIB | Compra | 05/10 | 300 | 24.4125 | 21.24 | 24.4833 | 7,344.99 | 0 |
| T16 | Principal | Casa B | BI261105 | Compra | 08/10 | 1,000 | 9.9528566 | 0.00 | 9.9528566 | 9,952.8566 | 0 |

- Las compras de CETES (T03, T04, T08, T09 y T16) son compras en mercado secundario al precio P de RF-26b de ese día, y la venta T13 es al P del día, sin comisión. El SRS 5.2 marca esta convención como pendiente de confirmar.
- El vencimiento de BI261008 no es una transacción: el 08/10 se liquidan a 10.00 los 2,000 títulos que siguen en posición (1,000 con Casa A y 1,000 con Casa B), un retiro de 20,000.00 sin ISR.

#### Cortes y periodos

Cortes (fechas de valuación):

- 13/09/2026, domingo: se valúa con los cierres del 11/09.
- 16/09/2026, día inhábil: se valúa con los cierres del 15/09. DEMOACC está en dos intermediarios (OE-5).
- 08/10/2026: vence BI261008 y se registra T16. DEMOFIB no tiene cierre ese día y usa el del 07/10.
- 14/10/2026: corte final.

| Periodo | Portafolio | Del | Al | Día base | Propósito |
|---|---|---|---|---|---|
| P1-A | Principal | 11/09 | 14/10 | 10/09 | Periodo completo |
| P1-B | Principal | 11/09 | 30/09 | 10/09 | Primer tramo; se encadena con P1-C |
| P1-C | Principal | 01/10 | 14/10 | 30/09 | Segundo tramo; el máximo es el día base |
| P1-D | Principal | 09/10 | 12/10 | 08/10 | Serie que no baja: máxima caída 0 |
| P2-A | Secundario | 11/09 | 14/10 | 10/09 | Factor 1 con denominador 0 del 11/09 al 13/09 |
| P2-C | Secundario | 01/10 | 14/10 | 30/09 | Sin flujos (criterio 1 de RF-09) |

#### Casos que cubre

| Caso | Requisito | Datos |
|---|---|---|
| Instrumento en dos intermediarios | OE-5; RF-06 | DEMOACC: 200 + 100 = 300, y luego 120 + 100 = 220. BI261008: 1,500 + 1,000 |
| CETES que vence en el periodo | OE-5; RF-26a | BI261008, el 08/10: retiro de 20,000.00 y posición 0 desde el vencimiento |
| Día sin cierre | RF-08 | Usa el cierre del 11/09, del 15/09 y, para DEMOFIB, del 07/10 |
| Caída con recuperación y serie que no baja | RF-10 | Principal: pico el 16/09, valle el 23/09 y nuevo máximo el 30/09; sin caídas del 09/10 al 12/10 |
| Venta parcial y costo que se reinicia | RF-08; RF-26a | Tres ventas parciales (T12, T13 y T14); DEMOFIB vendida completa (T10) y recomprada (T15, costo 24.4833) |
| Costo por intermediario | RF-08, criterio 2 | DEMOACC: 100.23985 con Casa A y 103.399 con Casa B |
| Compras antes que ventas (C1) | RF-08; RF-28 | DEMOETF con Casa B el 25/09: 100 + 60 − 120 = 40; con la venta primero serían −20 |
| Tasa en un nodo, interpolada, del extremo inferior y vigente | RF-26b | 91 valuaciones diarias de CETES; el 07/10 (d = 1) rige la colocación del 01/10, no la del 08/10 |
| TWR con flujos, sin flujos y con denominador 0 | RF-09 | Principal; Secundario en octubre y del 11/09 al 13/09 |
| Encadenamiento | RF-09 | (1 + TWR de P1-B) × (1 + TWR de P1-C) = 1 + TWR de P1-A |
| Pico con empate | RF-10 | P2-A: el índice del 16/09 es igual al del 15/09, y el pico es el 15/09 |

El conjunto no ejercita el extremo superior de la curva ni los nodos de 364 y 728 días, porque el d máximo es 182; los cubren CPF-26b (con d = 100, P = 9.8039216) y CPF-30.

#### Rechazos esperados y caso positivo

Cada rechazo no registra nada, informa su motivo y deja sin cambio todas las cifras.

| ID | Regla | Candidato | Resultado esperado |
|---|---|---|---|
| N1 | RF-28, criterio 1 | Principal, Casa B, venta de 150 DEMOACC el 18/09 | Rechazo: el saldo con Casa B quedaría en −50 el 18/09, aunque la posición sea 300 |
| N2 | RF-28, criterio 2 | Principal, Casa A, venta de 100 DEMOFIB el 15/09 | Rechazo: con T10, el saldo quedaría en −100 el 22/09 |
| N3 | RF-28, criterio 3; X-06 | Principal, Casa A, venta de 150 DEMOACC el 09/10 | Rechazo: saldo de −30 el 09/10; los 150 del Secundario no cuentan |
| N4 | RF-26a, criterio 2 | Principal, Casa B, venta de 100 BI261008 el 08/10 | Rechazo: la fecha es igual al vencimiento |
| N5 | RF-05, criterio 3 | Compra de DEMOACC el 09/09 | Rechazo: antes del intervalo de las semillas |
| N6 | RF-05, criterio 3 | Compra de DEMOACC el 15/10 | Rechazo: después del intervalo |
| N7 | RF-09, criterio 3 | Periodo del 14/10 al 11/09 | Rechazo: fecha final anterior a la inicial |
| N8 | RF-09, criterio 3 | Periodo del 11/09 al 15/10 | Rechazo: termina después del intervalo |
| C1 | RF-08, criterio 3; RF-28 | T11 y T12 (ya cargadas) | Se aceptan: compras antes que ventas |

Los precios e importes completos de cada candidato están en `backend/tests/oraculo/rechazos_rf28.csv`. Así responde la API a cada uno:

- N1 a N3: 409 `saldo_negativo`, con la fecha y el saldo que resultaría (N1: 2026-09-18 y −50; N2: 2026-09-22 y −100; N3: 2026-10-09 y −30).
- N4: 422 `fecha_en_o_despues_del_vencimiento`.
- N5 y N6: 422 `fecha_fuera_de_intervalo`.
- N7 y N8, en el tablero (E20): 422 `periodo_invertido` y 422 `periodo_fuera_de_intervalo`.

Lo comprueban `backend/tests/api/test_cpf05_transacciones.py` y `backend/tests/api/test_cpf11_tablero.py`.

#### Resultados esperados representativos

Por corte y portafolio (`esperados/posiciones.csv`; pesos, sin redondear):

| Corte | Portafolio | Costo total | Valor de mercado | Resultado no realizado |
|---|---|---:|---:|---:|
| 13/09 | Principal | 59,968.5200 | 60,329.9620 | 361.4420 |
| 13/09 | Secundario | 0.0000 | 0.0000 | 0.0000 |
| 16/09 | Principal | 70,308.4200 | 71,641.87725 | 1,333.45725 |
| 16/09 | Secundario | 15,585.0700 | 15,712.5000 | 127.4300 |
| 08/10 | Principal | 56,307.8883 | 57,842.7197 | 1,534.8314 |
| 08/10 | Secundario | 15,585.0700 | 16,110.0000 | 524.9300 |
| 14/10 | Principal | 56,307.8883 | 58,940.8782 | 2,632.9899 |
| 14/10 | Secundario | 15,585.0700 | 16,657.5000 | 1,072.4300 |

Por periodo (`esperados/indicadores.csv`). Los por cientos van con 6 decimales; la última columna es lo que presenta el tablero con 2 decimales.

| Periodo | Valor base | Valor final | TWR | Máxima caída | Pico | Valle | Presentado (TWR / caída) |
|---|---:|---:|---:|---:|---|---|---|
| P1-A | 49,929.06 | 58,940.8782 | 4.392808 % | −6.680477 % | 16/09 | 23/09 | 4.39 / −6.68 |
| P1-B | 49,929.06 | 73,866.02555 | 2.504499 % | −6.680477 % | 16/09 | 23/09 | 2.50 / −6.68 |
| P1-C | 73,866.02555 | 58,940.8782 | 1.842172 % | −2.181030 % | 30/09 (día base) | 05/10 | 1.84 / −2.18 |
| P1-D | 57,842.7197 | 58,708.69395 | 1.497119 % | 0.000000 % | — | — | 1.50 / 0.00 |
| P2-A | 0.0000 | 16,657.5000 | 6.881137 % | −13.675418 % | 15/09 | 23/09 | 6.88 / −13.68 |
| P2-C | 16,065.0000 | 16,657.5000 | 3.688142 % | −5.088702 % | 30/09 (día base) | 05/10 | 3.69 / −5.09 |

Posiciones del Principal al 14/10/2026, por intermediario (`esperados/posiciones.csv`):

| Instrumento | Intermediario | Títulos | Costo unitario | Costo total | Precio o P | Valor | Resultado |
|---|---|---:|---:|---:|---|---:|---:|
| DEMOACC | Casa A | 120 | 100.23985 | 12,028.782 | 111.05 (cierre del 14/10) | 13,326.00 | 1,297.218 |
| DEMOACC | Casa B | 100 | 103.399 | 10,339.90 | 111.05 | 11,105.00 | 765.10 |
| DEMOETF | Casa B | 40 | 49.3865 | 1,975.46 | 52.95 | 2,118.00 | 142.54 |
| DEMOFIB | Casa A | 300 | 24.4833 | 7,344.99 | 25.6225 | 7,686.75 | 341.76 |
| BI261008 | Casa A y Casa B | 0 (vencida el 08/10) | — | 0 | — | 0 | 0 |
| BI261105 | Casa B | 1,000 | 9.9528566 | 9,952.8566 | P = 9.9629213 (d = 22, extremo inferior, r = 6.09 %) | 9,962.9213 | 10.0647 |
| BI261217 | Casa A | 1,000 | 9.8344372 | 9,834.4372 | P = 9.8860375 (d = 64, r = 6.4842857… %) | 9,886.0375 | 51.6003 |
| BI270318 | Casa B | 500 | 9.6629250 | 4,831.4625 | P = 9.7123388 (d = 155, r = 6.8790476… %) | 4,856.1694 | 24.7069 |

En el Secundario, al mismo corte, DEMOACC con Casa A tiene 150 títulos, costo unitario de 103.9004666…, costo de 15,585.07, cierre de 111.05, valor de 16,657.50 y resultado de 1,072.43.

Valuaciones de CETES de muestra (`esperados/valuacion_cetes.csv`):

| Fecha | Emisión | d | Caso | Tasas usadas (colocación) | r (% anual) | P |
|---|---|---:|---|---|---:|---:|
| 10/09 | BI261008 | 28 | Nodo | 28 días, 6.25 % (10/09) | 6.25 | 9.9516240 |
| 17/09 | BI261217 | 91 | Nodo | 91 días, 6.66 % (17/09) | 6.66 | 9.8344372 |
| 17/09 | BI270318 | 182 | Nodo | 182 días, 6.90 % (17/09) | 6.90 | 9.6629250 |
| 07/10 | BI261008 | 1 | Extremo inferior | 28 días, 6.01 % (01/10); la del 08/10 aún no rige | 6.01 | 9.9983308 |
| 07/10 | BI261217 | 71 | Interpolación | 28 días, 6.01 %, y 91 días, 6.73 % (01/10) | 6.5014285… | 9.8734007 |
| 14/10 | BI261217 | 64 | Interpolación | 28 días, 6.09 %, y 91 días, 6.78 % (08/10) | 6.4842857… | 9.8860375 |
| 14/10 | BI270318 | 155 | Interpolación | 91 días, 6.78 %, y 182 días con plazo efectivo de 175, 6.91 % (08/10) | 6.8790476… | 9.7123388 |

Serie diaria del Principal el 08/10/2026 (`esperados/serie_diaria.csv`): V = 57,842.7197; A = 9,952.8566 (T16); R = 20,000.00 por el vencimiento; r = 0.7477527… %.

#### Tolerancias

La comparación se hace sin redondear, leyendo los esperados como decimales (SRS 5.2; RNF-01):

| Cifras | Tolerancia |
|---|---|
| Importes: valor, costo, resultado no realizado, aportaciones, retiros | Diferencia de 0.01 o menos |
| TWR y máxima caída | 0.001 puntos porcentuales o menos |
| Títulos | Igualdad exacta (exigida por el SRS 5.2) |
| Fechas (incluidos pico y valle) y precio P de los CETES | Igualdad exacta (recomendada por el SRS) |
| Rechazos N1 a N8 | Cada uno se rechaza con su motivo y sin cambiar ninguna cifra |

#### Congelamiento

El conjunto se congeló con el commit `11097f8`, del 15/10/2026, anterior al primer commit del motor (`b3391fd`, del 17/10/2026): es la evidencia de AC-03. Solo cambiará con una versión nueva del SRS 5.2, registrada en el SRS 3.1 y regenerada por los dos caminos (RD-21). El 18/10/2026, `git diff 11097f8 HEAD -- backend/tests/oraculo` no muestra cambios.

---

## 6. Requisitos no funcionales del MVP

### 6.1 Los que se verifican con el MVP

Según el SRS 3.3, RNF-01 a RNF-05 se verifican a más tardar el 18 de octubre de 2026. AC-03 cubre RNF-01 y AC-02 cubre RNF-02 a RNF-05.

| RNF | Qué exige | Métrica y valor objetivo | Método y prueba | Estado al 18/10/2026 |
|---|---|---|---|---|
| RNF-01 Corrección | Cada importe, TWR y máxima caída del conjunto de referencia dentro de la tolerancia de OE-5 | Diferencia máxima ≤ 0.01 en importes y ≤ 0.001 puntos porcentuales en rendimiento y máxima caída | Prueba CPNF-01: pytest compara sin redondear y genera la tabla de diferencias | Pasa en el motor (`backend/tests/motor/test_oraculo_5_2.py`, 27 pruebas) y por la API desde la base, sin red (`backend/tests/referencia/test_cpnf01.py`, 3). Falta guardar la tabla de diferencias en el repositorio. |
| RNF-02 Cifras idénticas | Misma cifra, dígito por dígito, en todas las vistas y en consultas repetidas | 0 cifras distintas para el conjunto de referencia | Demostración CPNF-02: comparar como texto, con capturas, el tablero y las posiciones | La comparación automática por la API pasa (`backend/tests/referencia/test_cpnf02.py`, 17 pruebas). La demostración con capturas requiere las pantallas V-04 y V-05. |
| RNF-03 Confidencialidad entre cuentas | Sin sesión o con sesión ajena, nada se consulta ni se cambia, y no se revela si existe | 0 solicitudes aceptadas; 0 respuestas que distingan lo ajeno de lo inexistente | Prueba CPNF-03: recorre todas las operaciones de la API | Pasa (`backend/tests/no_funcionales/test_cpnf03.py`). |
| RNF-04 Contraseñas no reversibles | Ninguna contraseña legible en la base, respaldos, registros ni respuestas | 0 contraseñas legibles; 0 cuentas con igual valor almacenado; Argon2id con m ≥ 19 MiB, t ≥ 2 y p = 1 | Prueba CPNF-04, con un respaldo `pg_dump` | Pasa (`backend/tests/no_funcionales/test_cpnf04.py`). |
| RNF-05 Credenciales fuera del alcance | Ninguna credencial vigente en el historial del repositorio, los archivos del navegador, las direcciones ni los registros | 0 apariciones por lugar | Inspección CPNF-05 (`backend/tests/inspeccion/cpnf05_credenciales.py`), que solo ejecuta el autor porque lee `backend/.env` | No consta su ejecución. `backend/.env` está excluido del control de versiones y ningún commit lo incluye. Se verifica otra vez el 30/10/2026, con RF-32. |

### 6.2 Los que se verifican después del MVP

| RNF | Qué exige | Fecha de verificación (SRS 3.3) |
|---|---|---|
| RNF-07 | Unidad, fecha de corte o periodo y definición junto a cada indicador, en cada pantalla | 23/10/2026; su aceptación cae en AC-09, al cierre |
| RNF-08 y RNF-09 | Seguir calculando si falla la fuente de tasas; registrar las series tal como se publican | 30/10/2026 |
| RNF-06 y RNF-10 | Tiempo de carga del tablero; agregar o quitar una fuente sin tocar el motor | 06/11/2026 |
| RNF-11 y RNF-12 | Pantallas completas en cada navegador y resolución; instalación desde el manual técnico | 13/11/2026 |

El MVP adelanta dos de ellos: CPNF-01 corre sin red (base de RNF-08) y el motor vive aislado en su carpeta, sin dependencias externas (base de RNF-10).

---

## 7. Arquitectura, tecnologías y API

### 7.1 Arquitectura

Es un sistema cliente-servidor: todo cálculo ocurre en el servidor, con el motor único, y el cliente solo presenta resultados (SRS 3.6 y 4.2). Hay dos contenedores, el cliente web y el servidor, y un componente externo, PostgreSQL. Durante la estadía los tres corren en el equipo de desarrollo.

| Componente (SRS 4.2) | Dónde está | Estado |
|---|---|---|
| Rutas de la API (FastAPI) | `backend/app/main.py` y `backend/app/api/` | Implementado |
| Cuentas, sesión y consentimiento | `backend/app/cuentas/` | Implementado |
| Autorización por propietario | `backend/app/cuentas/dependencias.py` y `backend/app/api/dependencias.py` | Implementado |
| Portafolios, intermediarios y catálogo | `backend/app/servicios/portafolios.py` | Implementado |
| Transacciones | `backend/app/servicios/transacciones.py` | Implementado |
| Consultas: intervalo, posiciones y tablero | `backend/app/servicios/consultas.py` | Implementado |
| Motor único de cálculo | `backend/app/motor/` | Implementado |
| Acceso a datos (SQLAlchemy 2) | `backend/app/db.py` y `backend/app/datos/` | Implementado |
| Configuración | `backend/app/config.py` | Implementado |
| Instalación de semillas | `backend/04_cargar_semillas.sql`, generado por `backend/semillas/genera_semillas.py` | Implementado como script SQL |
| Cargas de datos de mercado y adaptador de la semilla | No existen en Python; la carga la hace el script SQL | Desviación de SRS 4.2, por registrar |
| Cliente web: vistas de cuenta y consentimiento, vistas de portafolio, tablero, avisos y procedencia, cliente de la API | `frontend/src/` solo tiene la página de prueba de conexión | Pendiente |

### 7.2 Tecnologías y versiones

| Pieza | Versión | Fuente |
|---|---|---|
| Python | 3.13 (instalada: 3.13.5) | `backend/pyproject.toml`; SRS 3.5 |
| uv (entorno y dependencias del servidor) | 0.12.13 | SRS 3.5 y 3.6.3 |
| FastAPI | 0.141.1 | `backend/uv.lock` |
| SQLAlchemy | 2.0.54 | `backend/uv.lock` |
| psycopg | 3.3.6 | `backend/uv.lock` |
| pwdlib con Argon2id (argon2-cffi) | 0.3.1 (25.1.0) | `backend/uv.lock` |
| pydantic y pydantic-settings | 2.13.5 y 2.15.0 | `backend/uv.lock` |
| pytest | 9.1.1 | `backend/uv.lock` |
| PostgreSQL | 18 (instalada: 18.6) | SRS 3.5 y 3.6.3 |
| Node.js y npm (construcción del cliente) | 24 (instaladas: 24.12.0 y 11.6.2) | SRS 3.5 y 3.6.3 |
| React, react-dom y react-is | 19.3.0, versión exacta | `frontend/package.json` |
| Recharts (gráficas) | 3.10.1, versión exacta; instalada, aún sin usar | `frontend/package.json`; SRS 4.2 |
| Vite | 8.3.0 | `frontend/package-lock.json` |

El SRS 3.5 pide Python, PostgreSQL y Node.js «con su última corrección», y el SRS 3.6.3 pide actualizar Python, Node.js y Firefox antes del 18/10/2026; esa actualización no se ha hecho (sección 12.5).

### 7.3 Base de datos

- 13 tablas (SRS 4.3 y 4.4): cuentas (`usuario`, `version_aviso`, `consentimiento`); datos del usuario (`portafolio`, `intermediario`, `transaccion`); catálogo (`instrumento`, `emision_cetes`); fuentes y cargas (`fuente_datos`, `version_licencia`, `carga_datos`), y datos de mercado (`precio_cierre`, `tasa_referencia`).
- Las cifras se guardan como `numeric`, con la escala controlada por restricciones, para que la base rechace sin redondear. La zona horaria de la base es America/Mexico_City.
- La API se conecta con el rol `app_077`, con privilegios mínimos: lee las 13 tablas; inserta solo en cuentas, consentimientos, portafolios, intermediarios y transacciones; actualiza solo el estado y la contraseña de la cuenta y el nombre del portafolio; elimina solo portafolios (sus transacciones se eliminan en cascada), y no puede escribir en el catálogo, el aviso ni los datos de mercado (`backend/02_crear_esquema.sql`).
- La API no arranca si su rol es superusuario o si la zona horaria de la sesión no es la de la Ciudad de México (`backend/app/db.py`).

### 7.4 Operaciones de la API

La numeración E02 a E20 es la del SRS 4.5.2 y de los comentarios del código (`backend/app/api/`); E01, el diagnóstico `/health` de `backend/app/main.py`, no figura en el SRS ni lleva número en el código, y aquí se numera solo para listarlo. Con la API en marcha, la documentación interactiva está en `http://localhost:8000/docs`.

| Id | Método y ruta | Sesión | Para qué | Respuestas propias | Requisitos |
|---|---|---|---|---|---|
| E01 | GET /health | No | Diagnóstico: la API responde, sin tocar la base | 200 | — |
| E02 | GET /api/aviso-privacidad | No | Texto y versión vigentes del aviso | 200; 503 sin aviso vigente | RF-12 (crit. 2); CU-09 |
| E03 | POST /api/cuentas | No | Alta de la cuenta con su consentimiento; no abre la sesión | 201; 409 si el correo existe o el aviso cambió; 422; 503 | RF-01; RF-12 (crit. 1); CU-01 |
| E04 | POST /api/sesion | No | Abre la sesión con una cookie | 200; el mismo 401 ante cualquier fallo | RF-01; CU-02 |
| E05 | DELETE /api/sesion | No | Cierra la sesión (borra la cookie) | 204 | Sin requisito propio |
| E06 | GET /api/cuenta | Sí | La cuenta y sus consentimientos | 200; 401 | RF-12 (crit. 1, evidencia) |
| E07 | POST /api/cuenta/revocacion | Sí | Con confirmación expresa, revoca el consentimiento, bloquea la cuenta y cierra la sesión | 204; 422 | RF-12 (crit. 3); CU-10 |
| E08 | GET /api/instrumentos | Sí | Catálogo, ordenado por clave | 200 | RF-04 |
| E09 | GET /api/intervalo-datos | Sí | Intervalo de las semillas, fecha de hoy y fechas por omisión | 200 | RD-07; RF-09 (crit. 3) |
| E10 | GET /api/intermediarios | Sí | Intermediarios del usuario | 200 | RF-25; RF-02 |
| E11 | POST /api/intermediarios | Sí | Alta de un intermediario | 201; 409 nombre duplicado | RF-25 |
| E12 | GET /api/portafolios | Sí | Portafolios del usuario | 200 | RF-03; RF-02 |
| E13 | POST /api/portafolios | Sí | Alta, con divisa MXN | 201; 409 nombre duplicado | RF-03 |
| E14 | GET /api/portafolios/{id} | Sí | Consulta | 200; 404 si no existe o es ajeno | RF-03; RF-02 |
| E15 | PATCH /api/portafolios/{id} | Sí | Cambio de nombre | 200; 409; 422 | RF-03 |
| E16 | DELETE /api/portafolios/{id} | Sí | Eliminación confirmada con el nombre del portafolio | 204; 422 sin cambios | RF-03 (crit. 3) |
| E17 | GET /api/portafolios/{id}/transacciones | Sí | Lista de transacciones, por fecha de concertación | 200 | RF-05 |
| E18 | POST /api/portafolios/{id}/transacciones | Sí | Registro de una compra o venta | 201; 404; 409 saldo negativo; 422 | RF-05; RF-26a; RF-28 |
| E19 | GET /api/portafolios/{id}/posiciones?fecha_corte=AAAA-MM-DD | Sí | Posiciones, costos, valores y procedencia al corte | 200; 422 | RF-06; RF-08; RF-26a; RF-26b; RF-31 |
| E20 | GET /api/portafolios/{id}/tablero?inicio=AAAA-MM-DD&fin=AAAA-MM-DD | Sí | Indicadores del periodo, serie diaria y procedencia; el corte es el fin | 200, con «sin datos» si no hay transacciones; 422 | RF-09 a RF-11; RF-26a; RF-26b; RF-31 |

No existen operaciones para modificar o eliminar intermediarios o transacciones, ni para escribir en el catálogo o los datos de mercado (RD-09).

### 7.5 Convenciones de la API

- Toda cifra viaja como texto, en ambos sentidos; un número JSON en un campo de cifra se rechaza con 422. Los identificadores son enteros.
- Fechas en formato AAAA-MM-DD estricto; momentos en ISO 8601 con el desfase de la Ciudad de México.
- Orden de validación: origen (403), sesión (401), propiedad del recurso (404), forma de la solicitud (422), referencias del cuerpo (404) y reglas de negocio (422 o 409).
- Errores con una sola forma: `{"codigo", "regla", "mensaje"}`, más la lista de errores por campo cuando aplica y datos adicionales como la fecha y el saldo de un `saldo_negativo`. Ninguna respuesta repite el valor recibido.

| Estado | Códigos |
|---|---|
| 401 | `sesion_requerida`, `credenciales_invalidas` |
| 403 | `origen_no_permitido` |
| 404 | `no_encontrado` |
| 405 | `metodo_no_permitido` |
| 409 | `correo_registrado`, `nombre_duplicado`, `aviso_cambio`, `saldo_negativo` |
| 422 | `datos_invalidos`, `fecha_posterior_al_registro`, `fecha_fuera_de_intervalo`, `fecha_en_o_despues_del_vencimiento`, `plazo_cetes_excedido`, `divisa_distinta`, `periodo_invertido`, `periodo_fuera_de_intervalo`, `confirmacion_invalida`, `cifra_no_calculable` |
| 503 | `sin_aviso_vigente`, `sin_datos_de_mercado` |
| 500 | `error_interno` |

Estas convenciones son valores adoptados en el código, pendientes de confirmar en el SRS. La documentación OpenAPI todavía no describe esta forma única de error ni declara los estados 401, 403, 404, 409 y 503 (sección 12.4).

---

## 8. Seguridad y privacidad

Lo que implementa el MVP:

- Contraseñas con Argon2id (m = 19456 KiB, t = 2, p = 1), con un valor almacenado distinto por cuenta; nunca aparecen en respuestas ni en registros (RNF-04).
- Sesión en una cookie firmada con HMAC-SHA256, `HttpOnly` (el navegador no la deja leer al código de la página), `SameSite=Strict` y limitada a `/api`. Dura 480 minutos sin renovarse. No hay tabla de sesiones: cada solicitud comprueba que la cuenta siga activa, así que una cuenta bloqueada pierde el acceso de inmediato.
- Toda escritura exige que la solicitud venga de un origen permitido (`CORS_ORIGINS`); si no, responde 403.
- Lo ajeno se responde como inexistente (404), sin revelar que existe (RNF-03).
- Las respuestas de la API no se guardan en caché (`Cache-Control: no-store`).
- La base usa un rol de privilegios mínimos (sección 7.3).
- Los secretos (contraseña de la base, clave de firma de las sesiones y token del SIE) solo viven en `backend/.env`, que está excluido del control de versiones; `backend/.env.example` solo tiene marcadores (RNF-05). El MVP no usa todavía el token del SIE.
- Consentimiento expreso con registro de su momento, medio y versión del aviso; revocación con bloqueo inmediato (RF-12).
- Solo datos ficticios: cuentas de prueba con correos ficticios y ningún dato real de clientes ni información interna de la empresa (SRS 2.4, R-04; S-04).
- Avisos: la información no constituye asesoría de inversión y las valuaciones son estimaciones informativas (R-01 y R-11). Hoy los entrega la API como datos; su presentación en pantalla está pendiente.

Lo que no cubre el MVP (sección 9.6): HTTPS y cifrado en tránsito, límite de intentos de inicio de sesión, recuperación o cambio de contraseña, supresión de datos al concluir el bloqueo y el ejercicio de los derechos ARCO. Las limitaciones conocidas de seguridad están en la sección 12.4.

---

## 9. Fuera del alcance del MVP

### 9.1 Límites propios del MVP

No son exclusiones definitivas; la mayoría llega después.

- No se modifican ni se eliminan transacciones; un error de captura solo se corrige eliminando el portafolio con todas sus transacciones (RD-09 y RD-10). La edición llega con RF-39, con fecha por fijar.
- Solo compras y ventas: sin saldo inicial ni traspasos entre intermediarios, porque cada posición se registra desde su primera compra (S-07), y sin eventos corporativos.
- Solo pesos mexicanos; la multidivisa es RF-23 (S-10).
- Datos de mercado fijos: sin actualización diaria desde el SIE (RF-32) y sin los CETES colocados después de la semilla (RF-34).
- Los CETES se liquidan antes de la retención de ISR (S-14).

### 9.2 Requisitos diferidos con fecha (SRS 2.6.1)

Fase de refinamiento: del lunes 19 de octubre al viernes 20 de noviembre de 2026; el desarrollo termina el domingo 15 de noviembre, y la semana del 16 se reserva para capacitación, entrega y cierre (SRS 2.6).

| RF | Requisito | Fecha objetivo |
|---|---|---|
| RF-19 | Rendimiento ponderado por dinero (XIRR) | Semana del 19 de octubre |
| RF-20 | Volatilidad anualizada | Semana del 19 de octubre |
| RF-32 | Actualización diaria y automática desde el SIE de las tasas de CETES, sus plazos y el tipo de cambio FIX | Semana del 19 de octubre |
| RF-34 | Emisiones de CETES colocadas después de la semilla | Semana del 19 de octubre |
| RF-17 | Índice de Sharpe, con la tasa de CETES a 28 días como tasa libre de riesgo | Semana del 26 de octubre |
| RF-21 | Escenarios por el método Monte Carlo (escenario hipotético, no recomendación) | Semana del 26 de octubre |
| RF-33 | Captura o importación desde CSV de precios de cierre propios del usuario | Semana del 26 de octubre |
| RF-22 | Composiciones alternativas definidas por el usuario, sin que el sistema las sugiera | Semana del 2 de noviembre |
| RF-23 | Transacciones en más de una divisa (con el FIX, solo dólar) | Semana del 2 de noviembre |
| RF-24 | Aplicación móvil con paridad de indicadores | Semanas del 2 y del 9 de noviembre |
| RF-39 | Modificar y eliminar transacciones, revalidando el saldo por intermediario | Por fijar |

### 9.3 Requisitos que deberían incluirse (S) y opcionales (C) (SRS 2.6.2)

| RF | Requisito | Prioridad | Fecha objetivo |
|---|---|---|---|
| RF-27 | Títulos y valor de cada instrumento desglosados por intermediario | S | Semana del 19 de octubre (propuesta) |
| RF-13 | Distribución del portafolio por clase de activo | S | Semana del 19 de octubre (propuesta) |
| RF-15 | Exportar el portafolio y sus transacciones a un archivo | S | Semana del 26 de octubre (propuesta) |
| RF-14 | Explicación en lenguaje natural de los indicadores, con plantillas y sin servicio externo | S | Semana del 2 de noviembre |
| RF-16 | Valor en riesgo histórico | C | Semana del 9 de noviembre si hay margen (propuesta) |
| RF-18 | Comparación contra un índice de referencia sintético o propio | C | Igual que RF-16 (propuesta) |

Si la capacidad no alcanza, se recortan primero los opcionales, en orden MoSCoW estricto (SRS 2.6.3).

### 9.4 Exclusiones: nunca entran (SRS 2.4.7)

| ID | Exclusión |
|---|---|
| X-01 | Conexión automática con los intermediarios e importación de sus estados de cuenta; toda transacción se captura a mano |
| X-02 | Operación para varias organizaciones cliente (multitenant) |
| X-03 | Cálculo fiscal de lotes y del costo promedio fiscal |
| X-04 | Ventas en corto y préstamo de valores |
| X-05 | Rendimiento y riesgo por intermediario |
| X-06 | Consolidación de varios portafolios de un mismo usuario |
| X-07 | Fuentes comerciales de precios mientras PluriOne no contrate su licencia |

### 9.5 Restricciones del producto (SRS 2.4)

- R-01: no emite recomendaciones de inversión individualizadas ni sugiere composiciones de portafolio.
- R-02: no recibe, transmite ni ejecuta órdenes de compra o venta.
- R-08: no se conecta con intermediarios ni con proveedores comerciales de datos; su única interfaz externa es la API del SIE del Banco de México.
- R-11: sus valuaciones son estimaciones informativas, no precios oficiales, y no sustituyen el estado de cuenta del intermediario.
- R-13: no hay datos de mercado en tiempo real.

### 9.6 Fuera del MVP sin requisito en el SRS

Recuperar o cambiar la contraseña, el límite de intentos de inicio de sesión, la rectificación de datos (derechos ARCO), el inicio de sesión con Microsoft Entra ID y HTTPS. Ninguno tiene hoy un requisito en el SRS; quedan como propuestas para después.

La supresión de los datos al concluir el bloqueo es distinta: también queda fuera del MVP, que solo bloquea la cuenta (sección 3.3, RF-12), pero la exige la regla RD-23 del SRS 3.4.7, con un plazo por confirmar con la empresa.

---

## 10. Criterios de aceptación del MVP

### 10.1 Quién acepta y cómo (SRS 3.9)

- Revisa y acepta el líder de proyecto, en el repositorio que él indique, después del 18 de octubre, y una segunda vez si encuentra inconsistencias o carencias (SRS 3.9.1). La hora de corte y si cuenta el commit o su envío están por confirmar (SRS 3.9.2).
- El SRS propone, por confirmar con el líder, que el MVP quede aceptado cuando una revisión suya, primera o segunda, concluya sin observaciones pendientes. Cada observación se registra con su fecha, se corrige antes que los requisitos de la fase de refinamiento y se repiten las pruebas afectadas. Si la segunda revisión deja observaciones, el MVP se considera revisado con observaciones, y cada una se resuelve antes del cierre o se registra en el SRS 3.1 como trasladada (SRS 3.9.2 y 3.9.3; AC-11); este tratamiento también está por confirmar con el líder. La fecha de la revisión y si su conformidad queda por escrito están por confirmar con él.
- El responsable de pruebas, el autor, aporta la evidencia en un registro fechado de resultados; no decide la aceptación (SRS 3.9.1).
- La aceptación del cálculo se hace con datos de demostración y contra el conjunto de referencia (SRS 3.9).
- Si un imprescindible no cumple AC-01 a tiempo, su paso a la fase de refinamiento se acuerda con el líder y se registra en el SRS 3.1 antes de la revisión (S-02).

### 10.2 Criterios AC-01 a AC-08 (SRS 3.9.2)

| AC | Criterio | Evidencia exigida | Dónde se comprueba |
|---|---|---|---|
| AC-01 | Cada imprescindible vigente en 3.2 al entregarse cumple su criterio de aceptación y aprueba su CPF. | Resultado y fecha de cada CPF en el registro de resultados | Sección 3 (criterios y pruebas), sección 11.5 (comandos) |
| AC-02 | RNF-02 a RNF-05 alcanzan su valor objetivo al 18 de octubre. | Resultado y fecha de CPNF-02 a CPNF-05 en el registro de resultados | Sección 6.1 |
| AC-03 | RNF-01 se cumple sobre el conjunto de referencia, y el commit que lo congela es anterior al primero del motor. | Tabla de diferencias de CPNF-01 y hash del commit que congela el conjunto de referencia (`11097f8`) | Sección 5.8; `backend/tests/inspeccion/test_ac03.py` |
| AC-04 | Un recorrido de los imprescindibles, en el equipo de desarrollo y con los datos del conjunto de referencia (SRS 5.2; sección 5.8), deja al menos una captura fechada por requisito. | Registro del recorrido con sus capturas | Requiere las pantallas del SRS 4.5.2 |
| AC-05 | El repositorio explica cómo instalar el MVP en local con las versiones de 3.5, crear la base, cargar las semillas y ejecutar las pruebas, sin valores reales en las variables de ejemplo. | La sección «Cómo ejecutarlo localmente» del README | `README.md`; sección 11 de este documento |
| AC-06 | La carpeta `docs/` contiene los dos archivos Markdown que pidió el líder: uno del MVP y otro del documento de requisitos del producto (PRD). El líder fijó sus nombres el 18/10/2026: `MVP.md` y `PRD.md`; falta confirmar si `docs/` debe tener exactamente esos dos. | Los archivos en la versión entregada | `docs/MVP.md` (este archivo) y `docs/PRD.md` |
| AC-07 | La base de demostración solo contiene semillas y cuentas de prueba con datos ficticios. | Inspección del script de semillas, en el registro de resultados | `backend/04_cargar_semillas.sql` |
| AC-08 | Consta en el SRS 3.1 una revisión del Diario Oficial de la Federación conforme a D-04, anterior al 18 de octubre. D-04 supone que durante la estadía no se expide un reglamento de la Ley Federal de Protección de Datos Personales en Posesión de los Particulares ni se reforman los artículos en que se basan R-03 y R-12 de modo que cambien el aviso de privacidad, la revocación del consentimiento o las medidas de seguridad; la revisión comprueba que así sea. | Fecha y resultado en el SRS 3.1 | SRS 3.1 |

El estado de cada criterio está en la sección 12.2. RNF-07 no forma parte de esta aceptación: se verifica el 23/10/2026 y entra en AC-09, al cierre de la estadía (SRS 3.9.4).

---

## 11. Cómo ejecutarlo y verificarlo en local

Los comandos salen del README, de los encabezados de los scripts y de la documentación del código. El 18/10/2026 se ejecutaron las pruebas automatizadas y la inspección de AC-03 (sección 11.5); los pasos de instalación y arranque no se repitieron ese día. Las rutas son relativas a la raíz del repositorio, y el equipo de desarrollo usa Windows con PowerShell.

### 11.1 Requisitos

- Python 3.13 y uv.
- PostgreSQL 18, con `psql`, `initdb` y `pg_ctl`.
- Node.js 24 con npm.
- Un navegador basado en Chromium o Firefox, en versión vigente.

### 11.2 Base de datos

Los scripts de `backend/` se ejecutan en orden con `psql`, como el superusuario `postgres`. Ninguno contiene contraseñas.

1. Crear la base `proyecto077` y el rol `app_077`, conectado a la base `postgres` (comando armado a partir del README y del encabezado del script):

   ```
   psql -U postgres -d postgres -f backend/01_crear_base.sql
   ```

   Después, dentro de `psql`, fijar la contraseña del rol con `\password app_077` y anotarla solo en `backend/.env`.

2. Crear el esquema, probarlo y cargar las semillas, conectado a `proyecto077`:

   ```
   psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/02_crear_esquema.sql
   psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/03_probar_esquema.sql
   psql -U postgres -d proyecto077 -v ON_ERROR_STOP=1 -f backend/04_cargar_semillas.sql
   ```

   - `02` crea las 13 tablas, fija la zona horaria y los privilegios; corre una sola vez y se detiene si la configuración regional de la base no convierte bien a minúsculas las letras acentuadas (RD-03).
   - `03` prueba cada restricción y cada privilegio dentro de una transacción que se deshace.
   - `04` carga el aviso, las fuentes y licencias, el catálogo, los 71 precios y las 32 tasas. Volver a ejecutarlo no duplica nada; al final comprueba conteos y huellas, y si algo no coincide, deshace todo.

### 11.3 Configuración del servidor

En `backend/`, copiar el ejemplo y completar los valores:

```
Copy-Item .env.example .env
```

| Variable | Valor por omisión | Regla |
|---|---|---|
| `DATABASE_URL` | Ninguno; obligatoria | `postgresql+psycopg://USUARIO:CONTRASENA@localhost:5432/proyecto077`, con el rol `app_077` |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes exactos, separados por coma |
| `SESION_CLAVE` | Ninguno; sin ella la API no arranca | 32 caracteres o más. Se genera con `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SESION_DURACION_MINUTOS` | 480 | De 5 a 1440 |
| `SESION_COOKIE_SEGURA` | `false` | `true` solo si la API se sirve con HTTPS |
| `BANXICO_TOKEN` | — | El MVP no la usa |

### 11.4 Ejecutar

Servidor, en `backend/` (por omisión escucha en `http://127.0.0.1:8000`; la documentación interactiva queda en `http://localhost:8000/docs`):

```
uv sync
uv run fastapi dev app/main.py
```

Cliente web, en `frontend/` (Vite sirve en `http://localhost:5173`; hoy solo muestra la prueba de conexión con la API):

```
npm ci
npm run dev
```

Cargar el escenario del conjunto de referencia en la API en marcha, para demostrar el recorrido de AC-04. Se ejecuta en `backend/`. El cargador registra la cuenta ficticia `oraculo@example.com` (otra, con `--correo`) y pide para ella una contraseña de 15 caracteres o más, sin mostrarla. Luego inicia sesión y registra por la API los dos portafolios, los dos intermediarios y las transacciones T01 a T16; al terminar solo imprime conteos, no identificadores. Si la cuenta ya existe, el registro responde 409 y la carga se detiene, así que se corre una sola vez por base o con otro correo:

```
uv run python -m tests.referencia.cargador --url http://localhost:8000 --origen http://localhost:5173
```

### 11.5 Pruebas automatizadas

Las pruebas no usan `backend/.env` ni la base de desarrollo: cada corrida levanta su propio clúster temporal de PostgreSQL 18 en `127.0.0.1`, con contraseñas aleatorias, ejecuta los scripts `02`, `03` y `04`, y al terminar lo detiene y lo borra. Necesitan los binarios de PostgreSQL 18 en el PATH, en la variable `P077_PG_BIN` o en `C:/Program Files/PostgreSQL/18/bin`.

| Qué | Comando (en `backend/`) | Resultado el 18/10/2026 |
|---|---|---|
| Suite completa | `uv run --frozen pytest -q` | 271 pasan, 3 deseleccionadas (las de inspección), 0 fallan; de 1 a 7 minutos según la carga del equipo (66 s en una corrida sin otra carga) |
| Solo el motor, sin base de datos | `uv run --frozen pytest -m motor` | 143 pasan, en unos 3 segundos según pytest |
| Un requisito por la API | `uv run --frozen pytest tests/api/test_cpf28_saldo.py` (con el archivo que da la sección 3) | — |
| Un requisito en el motor | `uv run --frozen pytest tests/motor/test_criterios_3_2.py -k rf08` (con `rf06`, `rf09`, `rf10`, `rf26a`, `rf26b` o `rf28` en lugar de `rf08`) | — |
| Inspección de AC-03 (desde la raíz) | `uv run --directory backend pytest -m inspeccion tests/inspeccion/test_ac03.py` | 3 pasan |
| Inspección de RNF-05 (solo el autor; lee `backend/.env`) | `uv run python tests/inspeccion/cpnf05_credenciales.py` | No consta su ejecución |
| Suite con evidencia guardada | `uv run --frozen pytest --registro-resultados` | Aún no se ejecuta; escribe en `backend/tests/resultados/AAAA-MM-DD/` |

Marcas disponibles: `motor` (sin base), `bd` (con el clúster temporal), `api`, `referencia` y `no_funcional`; `inspeccion` queda excluida por omisión.

Mapa de pruebas por carpeta:

| Carpeta | Pruebas | Qué cubre |
|---|---:|---|
| `tests/motor` | 143 | Criterios de cálculo de 3.2 (57), el motor contra el conjunto de referencia (27), la presentación de cifras (13) y el aislamiento del motor (46) |
| `tests/api` | 47 | CPF-02 a CPF-07, CPF-11, CPF-25, CPF-26a, CPF-26b, CPF-28, CPF-30 y CPF-31 por la API |
| `tests/cuentas` | 30 | CPF-01, CPF-12, cookie, origen y bloqueo de cuentas |
| `tests/infra` | 28 | Configuración, errores, clúster temporal, arranque y diagnóstico |
| `tests/referencia` | 20 | CPNF-01 por la API y CPNF-02 |
| `tests/no_funcionales` | 3 | CPNF-03 y CPNF-04 |
| Total | 271 | |

### 11.6 Comprobación manual rápida

Con la API en marcha y el escenario cargado (sección 11.4), primero se inicia sesión y se obtiene el identificador del portafolio:

- `POST /api/sesion`, con el cuerpo `{"correo": …, "contrasena": …}`, usando el correo ficticio de la cuenta que creó el cargador (`oraculo@example.com`, salvo que se haya usado `--correo`) y la contraseña que se le dio. Es una escritura, así que exige un origen permitido: desde `/docs`, tener `http://localhost:8000` en `CORS_ORIGINS` (sección 11.7); desde otro cliente, enviar el encabezado `Origin: http://localhost:5173` y conservar la cookie de sesión que devuelve.
- `GET /api/portafolios` da el `id` de «Principal», que sustituye a `{id}` en los pasos siguientes.

Después:

1. `GET /api/portafolios/{id}/tablero?inicio=2026-09-11&fin=2026-10-14` del portafolio Principal debe dar TWR «4.39», máxima caída «-6.68», pico 2026-09-16, valle 2026-09-23, valor de mercado «58940.88», resultado no realizado «2632.99» y 35 puntos en la serie, del 2026-09-10 (día base, «49929.06») al 2026-10-14 («58940.88»).
2. `GET /api/portafolios/{id}/posiciones?fecha_corte=2026-10-14` debe dar un costo total de «56307.89», un valor de «58940.88» y un resultado no realizado de «2632.99».
3. `GET /api/portafolios/{id}/posiciones?fecha_corte=2026-09-13` debe usar, para cada precio, el cierre del 11/09, con la fuente marcada como de demostración.
4. Registrar la venta N1 (Principal, Casa B, 150 DEMOACC el 2026-09-18, a 98.50 con un importe de comisiones de 42.85) debe responder 409 `saldo_negativo`, con la fecha 2026-09-18 y el saldo −50 que resultaría, y no registrar nada.

### 11.7 Advertencias

- Guardar `backend/.env` en UTF-8; si PowerShell 5.1 lo guarda en otra codificación, la API no arranca y lo dice con un mensaje.
- Abrir el cliente en `http://localhost:5173`, no en `127.0.0.1`, o la cookie de sesión no viaja.
- Para iniciar sesión o registrar datos desde `/docs`, agregar `http://localhost:8000` a `CORS_ORIGINS` y volver a arrancar la API; si no, toda escritura, el inicio de sesión incluido, responde 403.
- `frontend/vite.config.js` no fija el puerto: si el 5173 está ocupado, Vite usa otro y el cliente queda fuera de `CORS_ORIGINS`.
- Si `02` se detiene por la configuración regional, el mensaje de error del script indica cómo crear la base con otra.

---

## 12. Estado al 18 de octubre de 2026

Esta sección se actualiza con cada entrega. Fecha de corte: domingo 18 de octubre de 2026, sobre el commit `268a2c2`, el último antes de agregar este archivo. Desde `faf6b32` (correcciones de la revisión del servidor) solo cambió el SRS; el código no.

Categorías:

- Hecho y verificado: implementado, verificado por pruebas automatizadas y sin partes de interfaz pendientes.
- Hecho sin interfaz: el motor y la API cumplen los criterios y sus pruebas pasan; faltan las pantallas para usarlo desde el navegador y para el recorrido de AC-04.
- Pendiente en parte: una parte de lo exigido está hecha y verificada, y otra no. En un imprescindible, el motor y la API cumplen lo que les toca y sus pruebas pasan, pero al menos un criterio pide algo que solo puede dar la interfaz web (una casilla, la lectura del aviso, un aviso a la vista, la marca de demostración, la línea de fuente o la gráfica) o está en conflicto; cada fila nombra el criterio pendiente.
- Pendiente: algo que el criterio exige y hoy no existe.

### 12.1 Por imprescindible

| RF | Motor y API | Interfaz web | Estado |
|---|---|---|---|
| RF-01 | Implementado y verificado (CPF-01) | Faltan V-01 y V-02 | Hecho sin interfaz |
| RF-02 | Implementado y verificado (CPF-02, CPNF-03) | Falta V-12 | Hecho sin interfaz |
| RF-03 | Implementado y verificado (CPF-03) | Falta V-08, con el diálogo de confirmación | Hecho sin interfaz |
| RF-04 | Implementado y verificado (CPF-04) | Falta V-10 | Hecho sin interfaz |
| RF-05 | Implementado y verificado (CPF-05) | Faltan V-06 y V-07 | Hecho sin interfaz |
| RF-06 | Implementado y verificado (CPF-06, CPNF-01, CPNF-02) | Falta V-05 | Hecho sin interfaz |
| RF-07 | Criterios 1 y 2 verificados (CPF-07) | Criterio 3 pendiente: la marca de demostración en V-04 y V-05 | Pendiente en parte |
| RF-08 | Implementado y verificado (CPF-08, CPNF-01) | Faltan V-04 y V-05 | Hecho sin interfaz |
| RF-09 | Implementado y verificado (CPF-09, CPNF-01) | Falta V-04 | Hecho sin interfaz |
| RF-10 | Implementado y verificado (CPF-10, CPNF-01) | Falta V-04 | Hecho sin interfaz |
| RF-11 | Criterio 3 y datos de los criterios 1 y 2 verificados (CPF-11, CPNF-02) | Criterio 2 pendiente: la gráfica en V-04. Criterio 1 en conflicto con los 2 decimales de RD-13 | Pendiente en parte |
| RF-12 | Criterio 3 y la parte de API de los demás verificados (CPF-12) | Criterios 1, 2 y 4 pendientes: casilla, lectura del aviso y avisos visibles; faltan V-02, V-03 y V-11 | Pendiente en parte |
| RF-25 | Implementado y verificado (CPF-25) | Falta V-09 | Hecho sin interfaz |
| RF-26a | Implementado y verificado (CPF-26a) | Faltan V-05 y V-07 | Hecho sin interfaz |
| RF-26b | Implementado y verificado (CPF-26b) | Falta V-05 | Hecho sin interfaz |
| RF-28 | Implementado y verificado (CPF-28) | Falta mostrar el motivo en V-07 | Hecho sin interfaz |
| RF-30 | Implementado y verificado (CPF-30) | Sin pantalla propia | Hecho y verificado |
| RF-31 | Criterio 1 verificado; la API entrega los datos de los criterios 2 y 3 (CPF-31) | Criterios 2 y 3 pendientes: fuente y fecha junto a cada dato en V-04 y V-05 | Pendiente en parte |

Resumen: 1 imprescindible hecho y verificado, 13 hechos sin interfaz y 4 con criterios pendientes de la interfaz (RF-07, RF-11, RF-12 y RF-31). Ninguna de las 12 pantallas del SRS 4.5.2 está construida. Si no quedan antes de la revisión, rige S-02 (sección 10.1); al 18/10/2026 no consta ese acuerdo en el SRS 3.1.

### 12.2 Por criterio de aceptación

| AC | Lo que existe | Lo que falta | Estado |
|---|---|---|---|
| AC-01 | Pruebas automatizadas de los 18 CPF; 271 pruebas pasan | El registro de resultados con fecha; los criterios de interfaz de RF-07, RF-11, RF-12 y RF-31; resolver el conflicto del criterio 1 de RF-11 | Pendiente |
| AC-02 | CPNF-03 y CPNF-04 pasan; CPNF-02 pasa por la API; existe el script de CPNF-05 | El registro de resultados; ejecutar CPNF-05; la demostración de RNF-02 con capturas | Pendiente en parte |
| AC-03 | `11097f8` (15/10) es anterior a `b3391fd` (17/10) y el conjunto no cambió desde entonces; `test_ac03.py` pasa; CPNF-01 pasa | Guardar en el repositorio la tabla de diferencias de CPNF-01; confirmar la tasa a 28 días del 10/09 | Hecho en código y git; falta la evidencia guardada |
| AC-04 | El cargador del escenario y el mapa de pantallas del SRS 4.5.2 | Las pantallas, el recorrido y sus capturas | Pendiente |
| AC-05 | El README explica la base de datos local; `.env.example` no tiene valores reales; este documento da los pasos completos (sección 11) | La sección «Cómo ejecutarlo localmente» en el README | Pendiente |
| AC-06 | `docs/MVP.md` (este archivo) y `docs/PRD.md`, con los nombres que fijó el líder | El envío de los dos antes de la hora de corte; confirmar con el líder si `docs/` debe tener exactamente esos dos archivos (sección 12.5) | En curso |
| AC-07 | `04_cargar_semillas.sql` no carga usuarios; las cuentas de prueba se crean por la API con correos ficticios | Anotar la inspección en el registro de resultados | Hecho; falta la evidencia guardada |
| AC-08 | Nada | La revisión del Diario Oficial y su fila en el SRS 3.1 | Pendiente |

### 12.3 Verificación ejecutada el 18/10/2026

- Suite completa sobre `268a2c2`: 271 pruebas pasan, 3 deseleccionadas y 0 fallan, el mismo conteo que registró el commit `faf6b32`. Una corrida hecha mientras corrían otras dos suites en el mismo equipo dio un error de conexión por tiempo de espera en CPNF-04; repetida sola, esa prueba pasa.
- Inspección de AC-03: 3 pruebas pasan.
- Comprobaciones con git: `11097f8` es ancestro del commit actual, `backend/tests/oraculo` no cambió desde entonces y `backend/.env` no está en ningún commit.
- Estas corridas no dejan evidencia en el repositorio; no sustituyen el registro de resultados que piden AC-01 a AC-03.

### 12.4 Limitaciones conocidas

- Interfaz web: solo existe la página de prueba de conexión. Todo el MVP se usa hoy por la API.
- Presentación del TWR y de la máxima caída con 2 decimales frente a la tolerancia de 0.001 puntos porcentuales del criterio 1 de RF-11 (sección 3.8).
- Un TWR exactamente en medio punto se presenta redondeado hacia cero (sección 4.5); no ocurre en el conjunto de referencia.
- El intervalo de las semillas terminó el 14/10/2026: no se pueden registrar transacciones posteriores hasta que llegue RF-32.
- Solo corre en el equipo de desarrollo, sin HTTPS.
- La documentación OpenAPI no describe la forma única de error ni declara los estados 401, 403, 404, 409 y 503.
- No hay tope para el tamaño de las solicitudes.
- Al arrancar, la API solo comprueba que su rol no sea superusuario y la zona horaria de la sesión; un rol dueño de las tablas arrancaría con más privilegios de los previstos.
- Si alguien sube el registro de SQLAlchemy al nivel DEBUG, se registran el correo y el valor almacenado de la contraseña (no la contraseña).
- El registro revela si un correo ya tiene cuenta (409). Está por decidir si se acepta mientras solo haya datos ficticios (S-04) y se revisa antes de admitir datos reales.
- Cerrar la sesión no invalida una cookie copiada antes de su vencimiento.
- Si las pruebas se interrumpen a la fuerza, el clúster temporal puede quedar en ejecución.
- La duración de la suite depende de la carga del equipo (de 1 a 7 minutos el 18/10/2026; 66 s en una corrida sin otra carga).
- Documentación desactualizada: el índice del README todavía da por pendiente todo el apartado 4.5 del SRS, aunque ya tiene 4.5.1 y 4.5.2 (siguen vacíos 4.5.3 y 4.5.4, y 5.3 solo tiene la fila de RF-01); el README del conjunto de referencia todavía dice que el congelamiento está pendiente; la portada del SRS conserva la fecha del 7 de octubre.

### 12.5 Decisiones abiertas que afectan al MVP

| Tema | Qué falta decidir o confirmar | Afecta a |
|---|---|---|
| Pantallas del MVP | Cuáles se construyen antes de la revisión y cuáles pasan a la fase de refinamiento por S-02, con aviso al líder y registro en el SRS 3.1 | RF-07, RF-11, RF-12, RF-31; RNF-02; AC-01, AC-02 y AC-04 |
| Criterio 1 de RF-11 | Aplicar la tolerancia a las cifras del motor o presentar los por cientos con 3 decimales | AC-01 |
| Tasa a 28 días del 10/09/2026 | Confirmarla con una segunda fuente; si cambia, se regeneran el conjunto de referencia y las semillas | RNF-01; AC-03 |
| Reglas del cálculo | Confirmar las que fijó el conjunto de referencia (serie diaria en días naturales desde el día base, factor 1 con denominador 0, índice 1 como primer máximo, pico y valle) y llenar las fichas de RF-06, RF-08, RF-09 y RF-10 | RF-06, RF-08, RF-09 y RF-10 |
| Valores adoptados en el código | Política de contraseña, mensajes de error, duración de la sesión, si el registro abre la sesión, si el catálogo exige sesión, límite de 728 o 730 días de RD-05, decimales de presentación y forma de la API | RF-01, RF-03 a RF-05, RF-12, RF-26a, RF-26b |
| Licencia de la semilla sintética | Confirmar la versión «1» y el nombre de su fuente | RF-31 |
| Componente de cargas | Registrar en el SRS 4.2 que las semillas las carga un script SQL | RF-07, RF-30 |
| Registro de resultados | Ruta, formato y versionado de la evidencia | AC-01 a AC-04 y AC-07 |
| Entrega | Repositorio, rama y hora de corte que revisa el líder; si `docs/` debe tener exactamente los dos archivos que pidió (hoy tiene cuatro) | AC-06; SRS 3.9.2 |
| Aviso y consentimiento | Textos de los avisos y de la casilla; plazo de supresión tras la revocación y responsable del tratamiento, con la empresa | RF-12 |
| Versiones del entorno | Actualizar Python, Node.js y Firefox, como pide el SRS 3.6.3, o registrar una nueva fecha | AC-05 |
| Revisión del Diario Oficial | Hacerla y registrarla; precisar si «anterior al 18» admite el mismo día | AC-08 |

### 12.6 Lo que falta para cumplir el SRS 3.9.2

1. Las pantallas mínimas del cliente web, o el acuerdo de S-02 para las que no alcancen.
2. El registro de resultados: la suite con `--registro-resultados` después del último commit de código, CPNF-05 y AC-03, con su resultado y fecha.
3. El recorrido de AC-04 con capturas fechadas.
4. La sección «Cómo ejecutarlo localmente» del README.
5. La revisión del Diario Oficial registrada en el SRS 3.1.
6. El commit y el envío de `docs/MVP.md` y `docs/PRD.md` antes de la hora de corte.
7. La decisión sobre el criterio 1 de RF-11 y la confirmación de la tasa a 28 días del 10/09.

---

## 13. Documentos relacionados

| Documento | Ubicación | Qué contiene |
|---|---|---|
| Documento de requisitos del producto (PRD) | [`docs/PRD.md`](PRD.md) | El producto en su conjunto (AC-06) |
| Especificación de requisitos (SRS) | [`docs/2 (SRS) Especificación de Requisitos de Software.md`](2%20%28SRS%29%20Especificaci%C3%B3n%20de%20Requisitos%20de%20Software.md) | Requisitos, reglas de datos, diseño, conjunto de referencia y criterios de aceptación |
| Definición del proyecto | [`docs/1 Definición del proyecto.md`](1%20Definici%C3%B3n%20del%20proyecto.md) | Descripción, objetivos OE-1 a OE-5, justificación y clasificación MoSCoW |
| README del repositorio | [`README.md`](../README.md) | Stack, estructura del repositorio y base de datos local |
| Conjunto de referencia | [`backend/tests/oraculo/README.md`](../backend/tests/oraculo/README.md) | Escenario, entradas, cifras esperadas, fuentes y tolerancias |
| Aviso de privacidad de demostración | [`backend/semillas/aviso_privacidad_demo.md`](../backend/semillas/aviso_privacidad_demo.md) | Texto vigente del aviso (RF-12) |
| Scripts de la base | `backend/01_crear_base.sql` a `backend/04_cargar_semillas.sql` | Base, esquema, prueba del esquema y semillas |
| Variables de ejemplo | [`backend/.env.example`](../backend/.env.example) | Configuración del servidor, sin valores reales |
| Documentación interactiva de la API | `http://localhost:8000/docs`, con la API en marcha | Operaciones E01 a E20 |
| Glosario del dominio financiero | Documento aparte, enlazado en el SRS 1.3 | Términos financieros |
