# Definición del proyecto 077

*Descripción, objetivos, justificación y delimitaciones iniciales del proyecto 077*

---

## Contenido

- [Descripción](#descripción)
- [Objetivos del proyecto 077](#objetivos-del-proyecto-077)
  - [Objetivo general](#objetivo-general)
  - [Objetivos específicos](#objetivos-específicos)
- [Justificación del proyecto](#justificación-del-proyecto)
  - [Impacto](#impacto)
  - [Valor para PluriOne](#valor-para-plurione)
  - [Justificación técnica](#justificación-técnica)
  - [Desarrollo del alumno](#desarrollo-del-alumno)
- [Delimitación del proyecto (MoSCoW)](#delimitación-del-proyecto-moscow)
  - [Imprescindible — obligatorio para el 18 de octubre](#imprescindible--obligatorio-para-el-18-de-octubre)
  - [Debería incluirse & Opcional](#debería-incluirse--opcional)
  - [Diferidos a la fase de refinamiento](#diferidos-a-la-fase-de-refinamiento)
  - [No se incluirá — fuera de alcance](#no-se-incluirá--fuera-de-alcance)
- [Referencias](#referencias)

---

## Descripción

Administrar un portafolio de inversión plantea un problema que parece simple y no lo es: saber cuánto se está ganando realmente. Un inversionista individual suele tener su información dispersa entre estados de cuenta, hojas de cálculo y notas propias, lo que lo obliga a trasladar cifras de un documento a otro cada vez que quiere una visión completa. A esa dispersión se suma una dificultad de método: el rendimiento observado mezcla dos efectos distintos –lo que rindió el mercado y lo que el propio inversionista aportó o retiró– y separarlos exige cálculos diferentes. Cuando además no se cuenta con una medida consistente y actualizada de riesgo, las decisiones terminan apoyándose en la intuición y los reportes se rehacen a mano cada vez.

El Proyecto 077 es una plataforma dirigida a inversionistas individuales que consolida en un solo lugar los instrumentos, las posiciones y las transacciones de su portafolio, y calcula sobre ellos un conjunto de métricas de rendimiento y riesgo mediante un motor único de cálculo, de modo que todas las vistas del sistema presenten cifras consistentes entre sí. La plataforma presenta esa información en un tablero operativo y explica los resultados en lenguaje natural, sin emitir recomendaciones de inversión.

## Objetivos del proyecto 077

### Objetivo general

Desarrollar una plataforma web que consolide las posiciones y transacciones de un inversionista individual con distintos intermediarios en México, incluidas las de CETES, para medir el rendimiento ponderado por tiempo y el riesgo del portafolio en su conjunto.

### Objetivos específicos

**OE-1** **Especificar** los requisitos funcionales, no funcionales y lógicos de datos de la plataforma, junto con el glosario del dominio, para delimitar qué se consolida y qué se mide.

**OE-2** **Diseñar** la arquitectura web, el modelo de datos y la interfaz de la plataforma, y registrar sus decisiones técnicas, para que todas las vistas obtengan sus cifras de un motor único de cálculo.

**OE-3** **Implementar** el registro de portafolios, intermediarios y transacciones sobre un catálogo de instrumentos que incluya las emisiones de CETES, con validación de saldos por intermediario y aislamiento por usuario, para consolidar las posiciones y las transacciones del portafolio en su conjunto.

**OE-4** **Implementar** el motor de cálculo del valor de mercado, del rendimiento ponderado por tiempo y de la máxima caída –incluidos el vencimiento y la valuación de los CETES– y su presentación en un tablero, para medir el rendimiento y el riesgo del portafolio en su conjunto.

**OE-5** **Comparar** los resultados del motor con un conjunto de referencia resuelto de forma independiente, que incluya un instrumento en dos intermediarios y una emisión de CETES que venza en el periodo, para demostrar que difieren a lo más un centavo en importes y 0.001 puntos porcentuales en rendimiento y máxima caída.

Los objetivos se enumeran en orden lógico. La documentación técnica, el manual de usuario y el plan de mantenimiento no son necesarios para cumplir el objetivo general, por lo que no forman un objetivo específico; se conservan como actividades del cronograma y entregables del proyecto.

## Justificación del proyecto

### Impacto

En la última década, México experimentó una masificación del acceso a instrumentos de inversión. De acuerdo con la Asociación Mexicana de Instituciones Bursátiles (AMIB), el número de clientes de fondos de inversión pasó de 2,119,566 en 2015 a 16,352,095 al primer trimestre de 2026, mientras que el número de fondos disponibles creció únicamente de 567 a 636 en el mismo periodo (AMIB, 2026, p. 55). Es decir, el mercado no se amplió en variedad de productos sino en número de clientes. Esa cifra no equivale a personas, porque suma los clientes de fondos de deuda y los de renta variable; medida en personas, la proporción de la población de 18 a 70 años con un fondo de inversión o un depósito a plazo pasó de 2.1 % en 2021 a 3.4 % en 2024 (Instituto Nacional de Estadística y Geografía [INEGI], 2025, p. 8). La escala de esas cuentas queda descrita por otro indicador: la cuenta promedio en casa de bolsa al primer trimestre de 2026 fue de 0.4 millones de pesos (AMIB, 2026, p. 35), monto que refleja el predominio de cuentas de escala individual y no institucional.

Quien invierte con más de un intermediario recibe de cada uno un estado de cuenta separado, con su propia posición y su propio rendimiento, y ni la Ley del Mercado de Valores ni la Ley de Fondos de Inversión prevén un estado de cuenta que integre distintos intermediarios (Ley del Mercado de Valores, 2005, arts. 191 y 203; Ley de Fondos de Inversión, 2001, art. 61 Bis). Las alternativas disponibles atienden el problema sólo en parte. La consolidación manual en hojas de cálculo está expuesta a errores: las auditorías de hojas de cálculo en organizaciones reunidas por Panko (2008) los encontraron en 88 % de 113 hojas. Entre las herramientas de código abierto, Wealthfolio da seguimiento a emisoras de la Bolsa Mexicana de Valores y calcula el rendimiento ponderado por tiempo, pero ni esta ni Ghostfolio documentan una fuente de precios para valores gubernamentales mexicanos como los CETES (Ghostfolio, s.f.; Wealthfolio, 2026a, 2026b). El proyecto 077 atiende esa brecha: consolida las posiciones que el inversionista mantiene con distintos intermediarios, incluidas las de CETES, y mide su rendimiento y su riesgo con un motor único de cálculo cuyas cifras se validan contra un conjunto de datos de referencia.

### Valor para PluriOne

PluriOne es una empresa que cuenta con experiencia en el desarrollo de sistemas financieros. Esta plataforma amplía su portafolio de soluciones FinTech con un producto propio, construido sobre una arquitectura documentada y extensible, cuyo motor de cálculo puede reutilizarse en desarrollos posteriores y cuya capa de analítica avanzada queda preparada para una fase siguiente.

### Justificación técnica

Se evaluaron las plataformas de código abierto para el seguimiento de inversiones y de finanzas personales: Ghostfolio, Wealthfolio, Firefly III, Maybe y OpenBB. Todas se distribuyen bajo la licencia AGPL-3.0, que obliga a ofrecer el código fuente de cualquier versión modificada a los usuarios que interactúan con ella a través de una red (Free Software Foundation, 2007, secc. 13). Derivar el producto de alguna de ellas obligaría a ofrecer su código fuente a quienes lo usen, lo que es incompatible con mantener cerrado el código de un producto propio de la empresa. Además, las dos que gestionan portafolios, Ghostfolio y Wealthfolio, no documentan una fuente de precios para valores gubernamentales mexicanos como los CETES (Ghostfolio, s.f.; Wealthfolio, 2026a); Firefly III no gestiona inversiones (Firefly III, s.f.), el repositorio de Maybe está archivado desde 2025 y OpenBB es una plataforma de datos para análisis, no de seguimiento de portafolios. Se optó por un desarrollo propio, tomando esas implementaciones como referencia de diseño.

### Desarrollo del alumno

El proyecto consolida competencias de requisitos conforme a estándares, diseño de arquitectura con decisiones documentadas, modelado de datos para un dominio financiero, desarrollo de servicios web y validación de cálculos contra conjuntos de referencia. Son competencias con demanda directa en el sector de desarrollo de software financiero.

## Delimitación del proyecto (MoSCoW)

| # | Prioridad | Categoría MoSCoW |
|---|-----------|------------------|
| 1 | **Imprescindible** | **M**ust-have |
| 2 | **Debería incluirse** | **S**hould-have |
| 3 | **Opcional** | **C**ould-have |
| — | **Diferidos a la fase de refinamiento** | — |
| 4 | **No se incluirá** | **W**on't have |

### Imprescindible — obligatorio para el 18 de octubre

El MVP se da por terminado a más tardar el domingo 18 de octubre de 2026, inclusive.

| ID | Requisito | OE | Prueba |
|----|-----------|----|--------|
| RF-01 | El sistema deberá permitir a una persona registrarse con correo y contraseña, e iniciar sesión con esas credenciales. | OE-3 | CPF-01 |
| RF-02 | El sistema deberá restringir el acceso de cada usuario autenticado exclusivamente a los portafolios, intermediarios, transacciones y posiciones de su propiedad. | OE-3 | CPF-02 |
| RF-03 | El sistema deberá permitir crear, consultar, modificar y eliminar portafolios identificados por nombre y divisa base. | OE-3 | CPF-03 |
| RF-04 | El sistema deberá permitir consultar el catálogo de instrumentos disponibles con su clave, nombre y clase de activo; cada emisión de CETES será un instrumento propio, identificado por su clave de emisión (BI seguida de su fecha de vencimiento en formato AAMMDD), con su valor nominal y su fecha de vencimiento. | OE-3 | CPF-04 |
| RF-05 | El sistema deberá permitir registrar y consultar las transacciones de compra y venta del portafolio, con su intermediario, instrumento, fecha, cantidad de títulos y precio unitario, este último con las comisiones e impuestos de la operación incluidos. | OE-3 | CPF-05 |
| RF-06 | El sistema deberá determinar, a una fecha de corte, la posición de cada instrumento del portafolio como la suma de sus saldos con cada intermediario, derivados del historial de transacciones registradas. | OE-3 | CPF-06 |
| RF-07 | El sistema deberá incorporar los precios históricos de los instrumentos a partir del conjunto de datos semilla. | OE-4 | CPF-07 |
| RF-08 | El sistema deberá calcular el valor de mercado y el resultado no realizado de cada posición y del portafolio a una fecha dada, con el costo asignado por costo promedio ponderado dentro de cada intermediario. | OE-4 | CPF-08 |
| RF-09 | El sistema deberá calcular el rendimiento ponderado por tiempo (TWR) del portafolio para un periodo determinado. | OE-4 | CPF-09 |
| RF-10 | El sistema deberá calcular la máxima caída del rendimiento acumulado ponderado por tiempo del portafolio dentro de un periodo determinado. | OE-4 | CPF-10 |
| RF-11 | El sistema deberá presentar un tablero con los indicadores calculados y la evolución del valor del portafolio en el tiempo. | OE-4 | CPF-11 |
| RF-12 | El sistema deberá recabar el consentimiento expreso para el tratamiento de datos y mostrar de forma visible que la información no constituye asesoría de inversión. | OE-3 | CPF-12 |
| RF-25 | El sistema deberá permitir a cada usuario registrar y consultar los intermediarios con los que mantiene sus inversiones, identificados por un nombre único dentro de su cuenta. | OE-3 | CPF-25 |
| RF-26a | El sistema deberá liquidar a su valor nominal, en su fecha de vencimiento, los títulos de cada emisión de CETES que sigan en posición, tratar ese importe como un retiro del portafolio y rechazar transacciones de la emisión con fecha igual o posterior a su vencimiento. | OE-4 | CPF-26a |
| RF-26b | El sistema deberá estimar el valor de las posiciones en CETES antes de su vencimiento con P = VN / (1 + r·d/360), donde d son los días naturales por vencer y r la tasa de referencia más reciente, interpolada linealmente a d días. | OE-4 | CPF-26b |
| RF-28 | El sistema deberá rechazar el registro, la modificación o la eliminación de una transacción que deje negativo, en cualquier fecha, el saldo de un instrumento con un intermediario, aunque la posición consolidada sea suficiente. | OE-3 | CPF-28 |
| RF-30 | El sistema deberá incorporar, desde el conjunto de datos semilla, las tasas de rendimiento de las subastas primarias de CETES a 28, 91, 182 y 364 días. | OE-4 | CPF-30 |

### Debería incluirse & Opcional

| ID | Requisito | Prio | OE | Prueba |
|----|-----------|------|----|--------|
| RF-13 | Presentar la distribución del portafolio por clase de activo. | S | OE-4 | CPF-13 |
| RF-14 | Generar una explicación en lenguaje natural de los indicadores calculados. | S | OE-4 | CPF-14 |
| RF-15 | Exportar el portafolio y sus transacciones a un archivo. | S | OE-3 | CPF-15 |
| RF-27 | Presentar, a una fecha de corte, la cantidad de títulos y el valor de mercado de cada instrumento desglosados por intermediario, de modo que su suma coincida con la posición y el valor consolidados. | S | OE-3 | CPF-27 |
| RF-16 | Calcular el valor en riesgo histórico del portafolio. | C | OE-4 | CPF-16 |
| RF-18 | Comparar el rendimiento del portafolio contra un índice de referencia. | C | OE-4 | CPF-18 |

### Diferidos a la fase de refinamiento

Del lunes 19 de octubre al viernes 20 de noviembre de 2026. La semana del 16 de noviembre se reserva para la capacitación, la entrega y el cierre.

| ID | Requisito | Fecha objetivo |
|----|-----------|----------------|
| RF-19 | Rendimiento ponderado por dinero (XIRR). | Semana del 19 oct |
| RF-20 | Volatilidad anualizada. | Semana del 19 oct |
| RF-17 | Índice de Sharpe con la tasa de CETES a 28 días como tasa libre de riesgo; depende de RF-20 y RF-30. | Semana del 26 oct |
| RF-21 | Simulación de escenarios por método Monte Carlo. | Semana del 26 oct |
| RF-22 | Optimización de la composición del portafolio. | Semana del 2 nov |
| RF-23 | Registro de transacciones en más de una divisa. | Semana del 2 nov |
| RF-24 | Aplicación móvil con paridad de indicadores. | Semanas del 2 y del 9 nov |

### No se incluirá — fuera de alcance

- Ejecución de órdenes, conexión automática con intermediarios o importación de sus estados de cuenta; toda transacción se captura manualmente.
- Asesoría o recomendaciones de inversión personalizadas.
- Operación multi-tenant para varias organizaciones cliente.
- Datos de mercado en tiempo real; precios y tasas provienen del conjunto de datos semilla.
- Cálculo fiscal de lotes y del costo promedio fiscal; el costo promedio de RF-08 no tiene efectos fiscales.
- Ventas en corto y préstamo de valores.
- Rendimiento y riesgo por intermediario; se miden sólo para el portafolio en su conjunto.
- Consolidación de varios portafolios de un mismo usuario. El portafolio en su conjunto es un solo portafolio sumado entre sus intermediarios; cada portafolio se mide por separado.

## Referencias

Asociación Mexicana de Instituciones Bursátiles. (2026). *Valores* (Boletín informativo núm. 62). https://www.amib.com.mx/

Firefly III. (s.f.). *What Firefly III isn't*. Recuperado el 25 de septiembre de 2026, de https://docs.firefly-iii.org/explanation/more-information/what-its-not/

Free Software Foundation. (2007). *GNU Affero General Public License* (Versión 3). https://www.gnu.org/licenses/agpl-3.0.html

Ghostfolio. (s.f.). *Frequently asked questions (FAQ): Self-hosting*. Recuperado el 25 de septiembre de 2026, de https://ghostfol.io/en/faq/self-hosting

Instituto Nacional de Estadística y Geografía. (2025). *Encuesta Nacional de Inclusión Financiera (ENIF) 2024: Reporte de resultados* (Reporte de resultados 7/25). https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2025/enif/ENIF2024_RR.pdf

Ley de Fondos de Inversión. (2001, 4 de junio). Congreso General de los Estados Unidos Mexicanos. Diario Oficial de la Federación (última reforma publicada el 14 de noviembre de 2025). Artículo 61 Bis. https://www.diputados.gob.mx/LeyesBiblio/pdf/LFI.pdf

Ley del Mercado de Valores. (2005, 30 de diciembre). Congreso General de los Estados Unidos Mexicanos. Diario Oficial de la Federación (última reforma publicada el 14 de noviembre de 2025). Artículos 191 y 203. https://www.diputados.gob.mx/LeyesBiblio/pdf/LMV.pdf

Panko, R. R. (2008). *What we know about spreadsheet errors* [Versión revisada del artículo publicado en *Journal of End User Computing, 10*(2), 15-21, 1998]. University of Hawaii. http://web.archive.org/web/20191229170034/http://panko.shidler.hawaii.edu:80/SSR/Mypapers/whatknow.htm

Wealthfolio. (2026a, 23 de septiembre). *Market data & FX*. Wealthfolio Docs. https://wealthfolio.app/docs/concepts/market-data-and-fx/

Wealthfolio. (2026b, 23 de septiembre). *Performance metrics*. Wealthfolio Docs. https://wealthfolio.app/docs/concepts/performance-metrics/
