# Especificación de Requisitos de Software

## Software Requirements Specification — S.R.S.

**Proyecto:** 077 — Plataforma Inteligente de Gestión de Activos Financieros
**Autor:** Ramón Ernesto Nieblas Mendívil
**Empresa:** PluriOne S.A. de C.V. (Develop Talent & Technology)
**Institución:** Universidad Tecnológica — Ingeniería en Tecnologías de la Información e Innovación Digital
**Versión:** 0.1 (borrador) · **Fecha:** septiembre de 2026

<!--
GUÍA DE USO DE ESTE ESQUELETO
- Los comentarios como éste no se ven al exportar ni en GitHub. Bórralos conforme llenes.
- Regla de un solo domicilio: cada requisito se ENUNCIA una vez. En las demás secciones
  se cita por identificador ("satisface RF-02"), nunca se repite el texto.
- Léxico fijo: "deberá" para lo obligatorio, en TODO el documento.
- Nunca recicles un identificador. Si partes RF-01, son RF-01a y RF-01b.
- Series separadas de pruebas: CPF-nn para funcionales, CPNF-nn para no funcionales.
- Secciones 1 a 3: QUÉ debe hacer el sistema. Sin tablas, sin tipos de dato, sin endpoints.
  Sección 4: CÓMO. El diseño se deriva de la sección 3, nunca al revés.
-->

---

## Contenido

1. [Introducción](#1-introducción)
2. [Descripción general](#2-descripción-general)
3. [Requisitos específicos](#3-requisitos-específicos)
4. [Diseño del producto](#4-diseño-del-producto)
5. [Verificación y trazabilidad](#5-verificación-y-trazabilidad)
6. [Referencias](#6-referencias)

---

# 1. Introducción

## 1.1 Propósito del documento

<!-- En Pomo-Go esta sección quedó vacía. Es la primera que lee el evaluador.
     Dos o tres frases: qué es este documento, para quién, y qué decide.
     No describas el producto aquí; eso va en 2.1. -->

## 1.2 Personal involucrado

| Nombre | Rol | Responsabilidad | Contacto |
|---|---|---|---|
| Ramón Ernesto Nieblas Mendívil | Desarrollador / Analista | Análisis, diseño, desarrollo y documentación del sistema | renm1172004@gmail.com |
| Juan Méndez Herrera | Asesor empresarial | Validación del alcance y seguimiento del proyecto | jmendez@develop.com.mx |
| Edgar Loeffelmann Ibarra | Líder de proyecto | Evaluación técnica y aprobación del entregable | eloeffelmann@develop.com.mx |
| Yohani _(apellidos)_ | Asesora académica | Seguimiento académico y evaluación del reporte | _(correo)_ |

## 1.3 Definiciones, acrónimos y abreviaturas

<!-- Aquí entra tu glosario financiero. Dos bloques:
     (a) Términos del dominio: activo, instrumento, posición, transacción, valuación,
         TWR, máxima caída, resultado no realizado...
     (b) Acrónimos: SRS, MVP, RF, RNF, CPF, CPNF, OE, AMIB, KPI, API.
     Un término canónico por concepto; los sinónimos que decidiste NO usar, decláralos. -->

### Términos del dominio

| Término | Definición |
|---|---|
| | |

### Acrónimos

| Sigla | Significado |
|---|---|
| SRS | Software Requirements Specification — Especificación de Requisitos de Software |
| MVP | Producto mínimo viable |
| RF / RNF | Requisito funcional / Requisito no funcional |
| CPF / CPNF | Caso de prueba funcional / no funcional |
| OE | Objetivo específico |
| TWR | Rendimiento ponderado por tiempo (*time-weighted return*) |

---

# 2. Descripción general

## 2.1 Objetivo del producto

<!-- Ya está escrito en "DSM 6-3. Ernesto. Definición del proyecto 077.md".
     DECISIÓN QUE TIENES QUE TOMAR: o lo copias aquí (documento autocontenido, mejor para
     el evaluador) o lo referencias (una sola fuente, mejor para mantenerlo).
     Si lo copias, la definición deja de ser la fuente y este documento manda. -->

## 2.2 Funciones del producto

<!-- Lista numerada, en prosa, de lo que hace el sistema visto desde afuera.
     NO son los requisitos: son 5 a 7 capacidades agrupadas.
     Ej.: consolidación del portafolio · cálculo de indicadores · presentación en tablero. -->

## 2.3 Características del usuario

<!-- El inversionista individual que administra su propio portafolio.
     Qué se asume que sabe (conceptos básicos de inversión) y qué no (nada técnico).
     Si hay más de un perfil, sepáralos. -->

## 2.4 Restricciones generales

<!-- Lo que el sistema NO hará por DECISIÓN, no por falta de tiempo.
     Viene de "No se incluirá — fuera de alcance" del documento de definición:
     no ejecuta órdenes, no emite asesoría, una sola divisa, precios al cierre,
     no multi-tenant, sin cálculo fiscal.
     Diferencia con 2.6: esto nunca entra; 2.6 entra después. -->

## 2.5 Suposiciones y dependencias

<!-- Cada supuesto numerado S-01, S-02... y CON SU CONSECUENCIA si resulta falso.
     Ése es el formato que te protege: "Se asume X. Si X no se cumple, RF-0n deja de ser válido."
     Los que ya identificaste: usuario objetivo, datos sintéticos, precios al cierre,
     una divisa, un solo tenant, sin ejecución de órdenes, fuente única de cálculo,
     sin requisitos de cumplimiento regulatorio en el MVP. -->

| ID | Supuesto | Consecuencia si no se cumple |
|---|---|---|
| S-01 | | |

## 2.6 Requisitos futuros

<!-- Los SHOULD, COULD y los diferidos con fecha. Viene de la tabla MoSCoW.
     El valor está en la FECHA: "no en el MVP" suena a recorte, "entra la semana del 13 de
     octubre" suena a plan. Aquí debe aparecer la autenticación con Microsoft Entra ID,
     que se había perdido. -->

---

# 3. Requisitos específicos

## 3.1 Revisión histórica

| Versión | Fecha | Autor | Cambios |
|---|---|---|---|
| 0.1 | | Ramón Nieblas | Versión inicial |

## 3.2 Requisitos funcionales

<!-- Los 17 MUST. Formato: tabla enriquecida como representación principal.
     SOLO RF-06, RF-09 y RF-10 llevan ficha larga aparte, porque cargan fórmula.
     No escribas doce fichas de ocho campos: son 15 páginas redundantes y 10 horas.
     Enunciado: "El sistema deberá <verbo> <objeto> <condición>". Sin tecnología. -->

| ID | Requisito | Criterio de aceptación | OE | Prueba |
|---|---|---|---|---|
| RF-01 | | | OE-3 | CPF-01 |

### Fichas detalladas

<!-- Sólo para los tres con fórmula. Campos: Función · Descripción · Entrada · Fuente ·
     Salida · Fuente · Proceso (3 a 6 pasos, NO cinco páginas) · Restricciones ·
     RNF asociado · Elaboró · Autorizó. -->

#### RF-06 — Determinación de la posición vigente

#### RF-09 — Rendimiento ponderado por tiempo (TWR)

#### RF-10 — Máxima caída

## 3.3 Requisitos no funcionales

<!-- Lo que a Pomo-Go le faltó, y lo que alimenta Estándares y Métricas en noviembre.
     ISO/IEC 25010:2023 tiene NUEVE características: la revisión añadió Safety,
     renombró Usabilidad a "Capacidad de interacción" y Portabilidad a "Flexibilidad".
     Al 077 le aplican siete. Declara Safety y Compatibilidad como NO APLICABLES con
     justificación escrita: esa declaración sola demuestra que leíste el modelo vigente.

     REGLA CRÍTICA: el enunciado lleva condición + propiedad observable + métrica + valor.
     NADA de rutas, códigos HTTP, nombres de algoritmo ni de tablas. Eso va en la columna
     de método de verificación o en restricciones de diseño.

     Escribe unos 10. Verifica 4 o 5 para el 18 de octubre (los de precisión y aislamiento);
     el resto lleva fecha 20 de noviembre. Los umbrales de desempeño que todavía no puedes
     medir se escriben como "por determinar tras medición de línea base; responsable Ramón;
     fecha 20 de noviembre". Un pendiente fechado es legítimo; un número inventado no. -->

| ID | Característica (ISO/IEC 25010:2023) | Enunciado | Métrica y valor objetivo | Método de verificación | Prueba | Fecha de verificación |
|---|---|---|---|---|---|---|
| RNF-01 | Adecuación funcional — corrección | | | | CPNF-01 | 18 oct |

### Características declaradas no aplicables

<!-- Safety y Compatibilidad, con una o dos frases de justificación cada una. -->

## 3.4 Requisitos lógicos de datos

<!-- ESTA SECCIÓN SOSTIENE EL ORDEN QUE DEFENDISTE: aquí describes las entidades y sus
     reglas EN PROSA, y el modelo E-R de la sección 4.3 se deriva de aquí.
     NO va DDL, ni nombres de tabla de PostgreSQL, ni tipos nativos.
     Sí van: qué información se guarda, qué relaciones existen, reglas de integridad,
     precisión de los importes, retención, y la regla de que la posición se DERIVA del
     historial de transacciones en lugar de almacenarse. -->

## 3.5 Requisitos de software

| Elemento | Requisito |
|---|---|
| Navegador | Versiones vigentes de navegadores basados en Chromium o Firefox |
| Servidor de aplicación | Python 3.13 |
| Gestor de base de datos | PostgreSQL 18 |
| Sistema operativo del servidor | Independiente (Windows, Linux) |

## 3.6 Requisitos de hardware

| Elemento | Mínimo |
|---|---|
| Procesador | |
| Memoria RAM | |
| Almacenamiento | |

## 3.7 Requisitos de recurso humano

| Rol | Responsable |
|---|---|
| Analista / Arquitecto | Ramón Ernesto Nieblas Mendívil |
| Desarrollador backend | Ramón Ernesto Nieblas Mendívil |
| Desarrollador frontend | Ramón Ernesto Nieblas Mendívil |
| Responsable de pruebas | Ramón Ernesto Nieblas Mendívil |

<!-- No es redundante: documenta que el proyecto lo ejecuta una sola persona en
     cuatro roles, y eso justifica el alcance ante el evaluador. -->

## 3.8 Requisitos de entrega

| Hito | Fecha |
|---|---|
| Revisión de planeación | Lunes 21 de septiembre de 2026 |
| Revisión de avance | Lunes 28 de septiembre de 2026 |
| **Entrega del MVP** | **Domingo 18 de octubre de 2026, inclusive** |
| Cierre de la fase de refinamiento | Viernes 20 de noviembre de 2026 |

## 3.9 Requisitos de aprobación y aceptación

<!-- Cómo se da por aceptado el sistema: demostración ante los asesores, criterios de
     aceptación cumplidos por requisito, y el conjunto de referencia coincidiendo con
     lo que calcula la plataforma. Ese último es tu criterio más fuerte. -->

---

# 4. Diseño del producto

<!-- Todo lo de esta sección se DERIVA de la sección 3. Escríbela después. -->

## 4.1 Diagrama de casos de uso

<!-- Un diagrama, tres actores, ocho elipses. Y sólo TRES fichas de caso de uso:
     CU-01 Registrar cuenta (con el paso de consentimiento), CU-05 Registrar transacción,
     CU-07 Consultar indicadores. No ocho fichas: son horas y dicen lo mismo que 3.2. -->

## 4.2 Diagrama de componentes

## 4.3 Modelo entidad-relación

<!-- Se deriva de 3.4. Verificación: el modelo no debe contener ninguna entidad que no
     esté nombrada en 3.4. Si aparece una, o falta un requisito o sobra una tabla. -->

## 4.4 Diccionario de datos

## 4.5 Elementos visuales

### 4.5.1 Guía de estilo

<!-- Paleta con valores hexadecimales, escala tipográfica, espaciado, iconografía y
     estilo de navegación. Se deriva de tu sistema de diseño existente: no la rehagas. -->

### 4.5.2 Mapa de navegación

### 4.5.3 Wireframes

### 4.5.4 Mockups

---

# 5. Verificación y trazabilidad

<!-- DOMICILIO ÚNICO del mapa requisito → prueba. No repitas esta información en 3.2
     ni en las fichas. Aquí se explican los métodos de verificación (inspección, análisis,
     demostración, prueba) y vive la matriz completa. -->

## 5.1 Métodos de verificación

| Método | Cuándo se usa |
|---|---|
| Inspección | Revisión visual del código o de la configuración |
| Análisis | Razonamiento sobre el diseño o sobre datos existentes |
| Demostración | Ejecución observada del sistema |
| Prueba | Ejecución automatizada con resultado esperado |

## 5.2 Conjunto de datos de referencia

<!-- El oráculo. Portafolio de juguete: 3 instrumentos, ~10 transacciones, con valor de
     mercado, resultado, TWR y máxima caída calculados A MANO en hoja de cálculo, y
     CONGELADO antes de programar el motor. Documenta aquí su ubicación y cómo se construyó.
     Es el argumento más difícil de refutar de toda la estadía. -->

## 5.3 Matriz de trazabilidad

| Requisito | Objetivo | Entidades | Prueba | Método |
|---|---|---|---|---|
| RF-01 | OE-3 | | CPF-01 | |

---

# 6. Referencias

Asociación Mexicana de Instituciones Bursátiles. (2026). *Valores por la fortaleza de México*, (62). https://www.amib.com.mx/

<!-- Añade aquí: la norma en la que te apoyas (por TÍTULO de cláusula, no por número,
     porque el cuerpo es de pago), ISO/IEC 25010:2023, y las licencias que cites. -->
