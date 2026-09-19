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
  - [Imprescindible — obligatorio para el 5 de octubre](#imprescindible--obligatorio-para-el-5-de-octubre)
  - [Debería incluirse & Opcional](#debería-incluirse--opcional)
  - [Poco factibles para el 5 de octubre](#poco-factibles-para-el-5-de-octubre)
  - [No se incluirá — fuera de alcance](#no-se-incluirá--fuera-de-alcance)
- [Referencias](#referencias)

---

## Descripción

Administrar un portafolio de inversión plantea un problema que parece simple y no lo es: saber cuánto se está ganando realmente. Un inversionista individual suele tener su información dispersa entre estados de cuenta, hojas de cálculo y notas propias, lo que lo obliga a trasladar cifras de un documento a otro cada vez que quiere una visión completa. A esa dispersión se suma una dificultad de método: el rendimiento observado mezcla dos efectos distintos –lo que rindió el mercado y lo que el propio inversionista aportó o retiró– y separarlos exige cálculos diferentes. Cuando además no se cuenta con una medida consistente y actualizada de riesgo, las decisiones terminan apoyándose en la intuición y los reportes se rehacen a mano cada vez.

El Proyecto 077 es una plataforma dirigida a inversionistas individuales que consolida en un solo lugar los instrumentos, las posiciones y las transacciones de su portafolio, y calcula sobre ellos un conjuntos de métricas de rendimiento y riesgo mediante un motor único de cálculo, de modo que todas las vistas del sistema presenten cifras consistentes entre sí. La plataforma presenta esa información en un tablero operativo y explica los resultados en lenguaje natural, sin emitir recomendaciones de inversión.

## Objetivos del proyecto 077

### Objetivo general

Desarrollar una plataforma web que permita a un inversionista individual consolidar los instrumentos, posiciones y transacciones de su portafolio y conocer su rendimiento y riesgo, mediante un motor único de cálculo que garantice cifras consistentes en todas las vistas del sistema.

### Objetivos específicos

**OE-1** **Especificar** los requisitos funcionales y no funcionales de la plataforma, sustentados en un glosario del dominio financiero y un modelo entidad-relación normalizado.

**OE-2** **Diseñar** la arquitectura de la solución y documentar las decisiones técnicas en registros de decisión, de modo que cada componente sea trazable a un requisito.

**OE-3** **Implementar el registro y la consolidación** del portafolio –instrumentos, posiciones y transacciones– con aislamiento por usuario.

**OE-4** **Implementar el motor de cálculo** de métricas de rendimiento y riesgo como fuente única de verdad.

**OE-5** **Validar** la precisión de los cálculos contra un conjunto de datos de referencia resuelto de forma independiente, y el aislamiento de la información entre usuarios distintos.

**OE-6** **Elaborar** la documentación técnica, el manual de usuario y el plan de mantenimiento de la plataforma.

## Justificación del proyecto

### Impacto

En la última década, México experimentó una masificación del acceso a instrumentos de inversión. De acuerdo con la Asociación Mexicana de Instituciones Bursátiles, el número de clientes de fondos de inversión pasó de 2,119,566 en 2015 a 16,352,095 al primer trimestre de 2026, mientras que el número de fondos disponibles creció únicamente de 567 a 636 en el mismo periodo (AMIB, 2026, p. 55). Es decir, el mercado no se amplió en variedad de productos sino en número de participantes. La escala de esos participantes queda descrita por otro indicador: la cuenta promedio en casa de bolsa al primer trimestre de 2026 fue de 0.4 millones de pesos (AMIB, 2026, p. 35), monto que corresponde al inversionista individual y no al institucional.

Ese crecimiento incorporó a millones de personas que administran patrimonio distribuido entre fondos de inversión, posiciones directas en casa de bolsa y ahorro para el retiro, sin herramientas adecuadas para consolidarlo ni para medir su desempeño. Las alternativas disponibles son hojas de cálculo construidas a mano, propensas a error y sin medición de riesgo, o aplicaciones extranjeras que no modelan los instrumentos del mercado mexicano. El proyecto 077 atiende esa brecha al ofrecer una medición consistente y verificable del rendimiento y el riesgo de un portafolio.

### Valor para PluriOne

PluriOne es una empresa que cuenta con experiencia en el desarrollo de sistemas financieros. Esta plataforma amplía su portafolio de soluciones FinTech con un producto propio, construido sobre una arquitectura documentada y extensible, cuyo motor de cálculo puede reutilizarse en desarrollos posteriores y cuya capa de analítica avanzada queda preparada para una fase siguiente.

### Justificación técnica

Se evaluaron las plataformas de gestión de portafolios de código abierto disponibles. Las que cubren el dominio se distribuyen bajo licencia AGPL-3.0, que obligaría a liberar el código fuente de cualquier obra derivada ofrecida por red, lo que resulta incompatible con un producto comercial. Adicionalmente, ninguna modela de forma nativa los instrumentos del mercado mexicano. Se optó por un desarrollo propio, tomando esas implementaciones como referencia de diseño.

### Desarrollo del alumno

El proyecto consolida competencias de requisitos conforme a estándares, diseño de arquitectura con decisiones documentadas, modelado de datos para un dominio financiero, desarrollo de servicios web y validación de cálculos contra conjuntos de referencia. Son competencias con demanda directa en el sector de desarrollo de software financiero.

## Delimitación del proyecto (MoSCoW)

| # | Prioridad | Categoría MoSCoW |
|---|-----------|------------------|
| 1 | **Imprescindible** | **M**ust-have |
| 2 | **Debería incluirse** | **S**hould-have |
| 3 | **Opcional** | **C**ould-have |
| — | **Poco factibles para el 5 de octubre** | — |
| 4 | **No se incluirá** | **W**on't have |

### Imprescindible — obligatorio para el 5 de octubre

| ID | Requisito | OE | Prueba |
|----|-----------|----|--------|
| RF-01 | El sistema deberá permitir a una persona registrarse con correo y contraseña, e iniciar sesión con esas credenciales. | OE-3 | CP-01 |
| RF-02 | El sistema deberá restringir el acceso de cada usuario autenticado exclusivamente a los portafolios, transacciones y posiciones de su propiedad. | OE-3 | CP-02 |
| RF-03 | El sistema deberá permitir crear, consultar, modificar y eliminar portafolios identificados por nombre y divisa base. | OE-3 | CP-03 |
| RF-04 | El sistema deberá permitir consultar el catálogo de instrumentos disponibles con su clave, nombre y clase de activo. | OE-3 | CP-04 |
| RF-05 | El sistema deberá permitir registrar transacciones de compra y venta indicando instrumento, fecha, cantidad y precio unitario. | OE-3 | CP-05 |
| RF-06 | El sistema deberá determinar la posición vigente de cada instrumento a partir del historial de transacciones registradas. | OE-3 | CP-06 |
| RF-07 | El sistema deberá incorporar los precios históricos de los instrumentos a partir del conjunto de datos semilla. | OE-3 | CP-07 |
| RF-08 | El sistema deberá calcular el valor de mercado y el resultado no realizado de cada posición y del portafolio a una fecha dada. | OE-4 | CP-08 |
| RF-09 | El sistema deberá calcular el rendimiento ponderado por tiempo (TWR) del portafolio para un periodo determinado. | OE-4 | CP-09 |
| RF-10 | El sistema deberá calcular la máxima caída del valor del portafolio dentro de un periodo determinado. | OE-4 | CP-10 |
| RF-11 | El sistema deberá presentar un tablero con los indicadores calculados y la evolución del valor del portafolio en el tiempo. | OE-4 | CP-11 |
| RF-12 | El sistema deberá recabar el consentimiento expreso para el tratamiento de datos y mostrar de forma visible que la información no constituye asesoría de inversión. | OE-3 | CP-12 |

### Debería incluirse & Opcional

| ID | Requisito | Prio | OE | Prueba |
|----|-----------|------|----|--------|
| RF-13 | Presentar la distribución del portafolio por clase de activo. | S | OE-4 | CP-13 |
| RF-14 | Generar una explicación en lenguaje natural de los indicadores calculados. | S | OE-4 | CP-14 |
| RF-15 | Exportar el portafolio y sus transacciones a un archivo. | S | OE-3 | CP-15 |
| RF-16 | Calcular el valor en riesgo histórico del portafolio. | C | OE-4 | CP-16 |
| RF-17 | Calcular el índice de Sharpe usando CETES 28 como tasa libre de riesgo. | C | OE-4 | CP-17 |
| RF-18 | Comparar el rendimiento del portafolio contra un índice de referencia. | C | OE-4 | CP-18 |

### Poco factibles para el 5 de octubre

| ID | Requisito | Fecha objetivo |
|----|-----------|----------------|
| RF-19 | Rendimiento ponderado por dinero (XIRR). | Semana del 6 oct |
| RF-20 | Volatilidad anualizada. | Semana del 6 oct |
| RF-21 | Simulación de escenarios por método Monte Carlo. | Semana del 13 oct |
| RF-22 | Optimización de la composición del portafolio. | Semana del 20 oct |
| RF-23 | Registro de transacciones en más de una divisa. | Semana del 27 oct |
| RF-24 | Aplicación móvil con paridad de indicadores. | Semana del 3 nov al 17 nov |

### No se incluirá — fuera de alcance

- Ejecución de órdenes o conexión con casas de bolsa.
- Asesoría o recomendaciones de inversión personalizadas.
- Operación multi-tenant para varias organizaciones cliente.
- Datos de mercado en tiempo real.
- Cálculo fiscal de lotes y costo promedio.

## Referencias

Asociación Mexicana de Instituciones Bursátiles. (2026). *Valores por la fortaleza de México*, (62). https://www.amib.com.mx/
