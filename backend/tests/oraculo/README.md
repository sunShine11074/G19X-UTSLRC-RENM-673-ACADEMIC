# Oráculo del conjunto de referencia (5.2) del Proyecto 077

Construido el jueves 15 de octubre de 2026, antes de programar el motor. Lo congela un commit en el repositorio (pendiente: ver al final).

## Qué es

Es el conjunto de referencia de la sección 5.2 del SRS. Lo forman un escenario con entradas cargables en la base y las cifras que el motor único debe reproducir dentro de las tolerancias de RNF-01. El escenario incluye:

- un usuario de prueba (`oraculo@example.com`, datos ficticios, S-04);
- dos portafolios en MXN, «Principal» y «Secundario»;
- dos intermediarios, «Casa A» y «Casa B», que comparten los dos portafolios;
- tres instrumentos de demostración (DEMOACC, DEMOETF y DEMOFIB) con precios sintéticos;
- cuatro emisiones reales de CETES (BI261008, BI261105, BI261217 y BI270318), valuadas con las tasas reales del CF107;
- 16 transacciones (T01 a T16), del 10/09 al 08/10/2026;
- ocho candidatos que deben rechazarse (N1 a N8) y un caso positivo (C1).

Las cifras son estas:

- por transacción: monto, costo o ingreso por título, aportación y retiro;
- por día natural: el cierre usado y la valuación de cada emisión de CETES (d, nodos, r y P);
- en cuatro cortes: títulos, costo unitario, costo total, precio o P, valor y resultado no realizado, por intermediario, por instrumento y por portafolio;
- la serie diaria V, A, R y r de cada portafolio;
- el índice, la caída, el TWR y la máxima caída de seis periodos;
- la regla de rechazo de cada candidato, con la fecha del primer saldo negativo y el saldo que dejaría.

OE-5 queda cubierto así:

- un instrumento en dos intermediarios: DEMOACC con Casa A y Casa B, y también BI261008;
- una emisión de CETES que vence en el periodo: BI261008, el 08/10.

Además, el escenario tiene días sin cierre, una caída con recuperación y ventas parciales.

## Contenido de la carpeta

| Ruta | Qué es |
|---|---|
| `oraculo_5_2.xlsx` | Camino 1: la hoja de cálculo. Tiene 16,488 fórmulas visibles; las entradas van en azul y los rótulos de estructura en gris. Ya está recalculada por Excel, con 0 errores y 44 comprobaciones en VERDADERO. |
| `genera_libro.py` | Arma el libro. Solo escribe entradas, rótulos y fórmulas; no calcula ninguna cifra. |
| `calcula_oraculo.py` | Camino 2, independiente: Python con `decimal` a 28 dígitos. Escribe `esperados/`, `rechazos_rf28.csv` y `casos_positivos.csv`. |
| `compara_vias.py` | Compara los dos caminos cifra por cifra y escribe `comparacion_vias.csv`. |
| `entradas/*.csv` | Entradas congelables (ver la tabla siguiente). |
| `esperados/*.csv` | Cifras esperadas sin redondear (28 dígitos significativos): `posiciones`, `serie_diaria`, `indicadores`, `valuacion_cetes`, `indice_por_periodo`, `transacciones` y `precios_usados`. Las lee pytest. |
| `rechazos_rf28.csv` | Los candidatos N1 a N8, con la regla, la fecha del primer saldo negativo y el saldo que dejarían. Todos sus renglones deben rechazarse. |
| `casos_positivos.csv` | El caso positivo C1: T11 y T12, ya cargadas, se aceptan porque las compras van antes que las ventas. No es una transacción por registrar. |
| `comparacion_vias.csv` | Diferencia máxima entre los dos caminos, por tipo de cifra. |
| `scripts/arma_entradas.py` | Arma `entradas/` a partir de `diseno/` y `datos/`. |
| `scripts/arma_calendario.py` | Arma `datos/dias_sin_operaciones_2026.csv`, el calendario completo de 2026. |
| `scripts/parse_cf107.py`, `scripts/arma_tasas.py` | Obtienen las tasas del CF107 (`datos/tasas_cf107.csv`) de las copias de `fuentes/`. |
| `scripts/recalc_excel.ps1` | Recalcula el libro con Excel y lista las fórmulas con error. |
| `datos/`, `fuentes/`, `diseno/` | Las tasas y el calendario con sus fuentes, las copias de las páginas consultadas y el diseño del escenario. |

### Entradas y su carga en la base (4.3 y 4.4)

Cada CSV trae las columnas de su tabla de 4.4, sin las llaves sustitutas (`id`), que asigna la base. Las filas se ligan por llave natural: correo, nombre de portafolio, nombre de intermediario, clave de instrumento, nombre de fuente, versión de licencia y carga. Una celda vacía en una columna que admite nulos (`direccion`, `obligacion_suprimir`) es NULL.

| Archivo | Tabla de 4.4 | Columnas auxiliares (no se cargan) |
|---|---|---|
| `usuarios.csv` | usuario (`correo`) | — |
| `portafolios.csv` | portafolio | `usuario_correo` (llave natural) |
| `intermediarios.csv` | intermediario | `usuario_correo` |
| `instrumentos.csv` | instrumento y emision_cetes (`vencimiento`, `valor_nominal`) | — |
| `fuentes_datos.csv` | fuente_datos (`nombre`, `direccion`, `de_demostracion`) | — |
| `versiones_licencia.csv` | version_licencia (`version`, `usos_permitidos`, `obligacion_suprimir`, `atribucion`) | `fuente_nombre` |
| `cargas_datos.csv` | carga_datos (`origen`, `fecha_inicial`, `fecha_final`, `resultado`, `observaciones_incorporadas`, `observaciones_omitidas`, `valores_sustituidos`) | `carga` (llave natural), `fuente_nombre`, `version` |
| `precios.csv` | precio_cierre (`fecha`, `precio`) | `instrumento_clave`, `fuente_nombre`, `carga` |
| `tasas.csv` | tasa_referencia (`plazo_nominal`, `fecha_colocacion`, `valor`, `unidad`, `plazo_efectivo`) | `fuente_nombre`, `carga`, `serie_valor`, `serie_plazo`, `fuentes_coincidentes` |
| `transacciones.csv` | transaccion (`tipo`, `fecha_concertacion`, `cantidad`, `precio`, `importe_comisiones`) | `ref`, `usuario_correo`, `portafolio_nombre`, `intermediario_nombre`, `instrumento_clave`, `proposito`, `regla_del_precio` |

Lo que la base o la Instalación de semillas fijan, y por eso no está en los CSV:

- `usuario.contrasena_hash`, `usuario.estado` («activa») y el otorgamiento de consentimiento del usuario de prueba con la versión vigente del aviso. Los genera la Instalación de semillas (RD-11; 4.3, «Restricciones e índices»).
- `carga_datos.incorporada_en` (now()) y `transaccion.registrada_en` (now()). `carga_datos.obtenida_en` solo existe si P-34 la adopta.

Las cargas son dos, ambas con origen «semilla», `resultado` «completa» (la lista de resultados sigue ⟦decidir⟧ en 4.3) y `valores_sustituidos` = {}:

- C-PRECIOS: semilla sintética, del 10/09 al 14/10/2026, 71 observaciones incorporadas y 0 omitidas.
- C-TASAS: Banco de México, del 27/08 al 15/10/2026, 32 incorporadas y 0 omitidas. El CSV solo trae observaciones publicadas. El JSON del SIE no lista las semanas sin subasta de 364 y 728 días; en ese intervalo son 8 (364 días el 27/08, 10/09, 24/09 y 08/10, y 728 días el 03/09, 17/09, 01/10 y 15/10). La página del CF107 las muestra como N/E; en las copias guardadas se ven cinco: 364 días el 24/09 y el 08/10, y 728 días el 17/09, el 01/10 y el 15/10. Si el Adaptador de la semilla lee el cuadro con sus N/E, debe contarlas como omitidas (4.4, ⟦confirmar cómo llegan⟧).

Las versiones de licencia son la «1» de cada fuente. La del Banco de México sigue R-05 y D-03. La de la semilla sintética es una propuesta del oráculo, porque RF-31, criterio 1, deja esa licencia en ⟦decidir⟧.

Los demás archivos de `entradas/` no se cargan en la base:

- `candidatos_rechazo.csv`: N1 a N8. pytest los intenta registrar después de T01 a T16.
- `parametros.csv`, `cortes.csv`, `periodos.csv` y `dias_sin_operaciones_2026.csv`: el intervalo, la serie, los cortes, los periodos y el calendario completo de 2026 (114 fechas: los 104 sábados y domingos y los festivos del art. 1 del DOF; el 12/12 cae en sábado).

## Cómo se construyó: dos caminos

1. **Hoja de cálculo** (`genera_libro.py` y Excel). Cada cifra es una fórmula de Excel 2019, 2021, 2024 o Microsoft 365: SUMIFS, COUNTIFS, INDEX, MATCH, MAXIFS y MINIFS (con `_xlfn.`), ROUND, PRODUCT y SUMPRODUCT, sin matrices dinámicas. MAXIFS y MINIFS no existen en Excel 2016 sin suscripción.
   - El costo promedio se lleva en un kardex por par portafolio-instrumento-intermediario (hoja Transacciones, columnas T a Z).
   - La valuación diaria es una cuadrícula de días naturales × pares, con 350 filas.
   - Los CETES se valúan en la hoja «CETES»: la colocación vigente por plazo nominal sale de MAXIFS, los nodos de MAXIFS y MINIFS sobre los plazos efectivos, y P de `ROUND(…;7)`.
   - La hoja «Rechazos» aplica a cada candidato las reglas en orden (intervalo, vencimiento y saldo negativo en cualquier fecha) con el saldo del par al cierre de cada fecha posterior.
   - Hojas: Léeme, Entradas, Transacciones, Precios, Tasas, CETES, Valuación diaria, Posiciones, Serie, Periodos, Rechazos, Comprobaciones y Esperados.
   - Colores: azul, entrada (su valor se puede cambiar dentro de la estructura); gris, rótulo de estructura (qué filas existen; se cambia en `entradas/*.csv` y se regenera el libro); negro, fórmula. Los bloques diarios de Periodos tienen un largo fijo: para cambiar el inicio o el fin de un periodo hay que editar `entradas/periodos.csv` y regenerar. Las comprobaciones 37 a 39 detectan un bloque que ya no termina en el fin del periodo, un TWR que no coincide con el de la Serie y un par o una fecha de Transacciones sin filas en la cuadrícula.
2. **Python con decimal** (`calcula_oraculo.py`). No lee la hoja ni comparte código con ella, y usa algoritmos distintos:
   - lleva el **costo total** del saldo de cada par en un ciclo día por día, en vez del costo unitario del kardex;
   - selecciona los nodos de tasa ordenando la curva vigente;
   - acumula el índice en un ciclo;
   - evalúa los rechazos recorriendo cada día natural del intervalo con el candidato agregado.

   Usa un contexto explícito `Context(prec=28, rounding=ROUND_HALF_EVEN)`, cuyo modo de redondeo solo actúa en el límite de 28 dígitos. Aplica `ROUND_HALF_UP` (mitad alejándose de cero) **únicamente** a P, a 7 decimales. Antes de calcular valida las entradas contra 4.3 y 4.4 (incluidas fuentes, licencias, cargas y el calendario completo) y comprueba por dos caminos las cifras del escenario (7 f).

### Diferencia entre los dos caminos

Se compararon todas las cifras de los siete CSV de esperados, de `rechazos_rf28.csv` y de `casos_positivos.csv` contra la hoja «Esperados». Los renglones se emparejan por llave. La hoja usa doble precisión, así que se esperaban diferencias del orden de 1e-9 o menores.

| Tipo de cifra | Cifras | Diferencia máxima |
|---|---:|---|
| Importes (pesos) | 662 | 1.6E-11 |
| Precio o costo por título (pesos) | 297 | 7.2E-15 |
| P de CETES a 7 decimales | 91 | 91 de 91 iguales dígito a dígito |
| P de CETES sin redondear | 91 | 1.9E-15 |
| Tasa r de RF-26b (% anual) | 353 | 7.6E-16 |
| r(t) | 190 | 3.7E-16 (3.7E-14 pp) |
| Índice I(t) y máximo | 380 | 6.7E-16 |
| Caída | 190 | 4.3E-16 |
| TWR | 6 | 4.2E-16 (4.2E-14 pp) |
| Máxima caída | 6 | 1.5E-16 (1.6E-14 pp en la columna en por ciento) |
| Títulos, días, plazos y saldos | 634 | coincidencia exacta |
| Fechas | 1,122 | coincidencia exacta |
| Textos (llaves, caso, regla, resultado, sí o no) | 1,052 | coincidencia exacta |

Ninguna cifra supera 1e-6, así que no hubo que corregir nada.

Ningún P está cerca de un empate en el octavo decimal. El más cercano es el de BI261008 del 10/09: su P sin redondear dista 2.4E-10 del empate, cinco órdenes de magnitud más que el error de la doble precisión.

## Cómo regenerarlo y recalcularlo

Ejecuta los comandos desde la carpeta del oráculo, la que contiene este README (en el repositorio, `backend/tests/oraculo/`, la ubicación que propone 5.2), con `PYTHONIOENCODING=utf-8`. La carpeta no tiene archivos `.py` que tapen la biblioteca estándar.

```
python -I -B scripts/arma_tasas.py        # solo si cambian las fuentes; lee fuentes/ y escribe datos/tasas_cf107*.csv
python -I -B scripts/arma_calendario.py   # solo si cambia el calendario; escribe datos/dias_sin_operaciones_2026.csv
python -I -B scripts/arma_entradas.py     # solo si cambia el diseño; las entradas ya están congeladas
python -I -B calcula_oraculo.py           # camino 2: esperados/*.csv, rechazos_rf28.csv y casos_positivos.csv
python -B genera_libro.py                 # camino 1: libro con fórmulas, todavía sin valores
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/recalc_excel.ps1 oraculo_5_2.xlsx
python -B compara_vias.py                 # comparación cifra por cifra: comparacion_vias.csv
```

- `genera_libro.py` y `compara_vias.py` van sin `-I`: necesitan openpyxl, que está en el site-packages del usuario, y `-I` lo excluye.
- `recalc_excel.ps1` abre una instancia invisible de Excel, recalcula, guarda y devuelve un JSON con las fórmulas en error. Debe decir `"errores":0`.
- El recálculo tarda unos 12 minutos, porque el script revisa cada celda por COM.
- `calcula_oraculo.py` termina con código 1 si una entrada es inválida y con código 2 si falla una comprobación.
- `compara_vias.py` termina con código 1 si una cifra difiere más de 1e-6 o si una fecha, un texto, un entero o un P no coinciden.
- En la hoja Comprobaciones, la última fila debe decir VERDADERO.

## Escenario

### Intervalos, cortes y periodos

- **Intervalo de las semillas** (S-09 y P-14; se fija al congelar): del 10/09 al 14/10/2026. Contiene 24 días con operaciones. No hay precios el 16/09 (festivo según el DOF del 10/12/2025) ni en los fines de semana.
- **Semilla de tasas:** las 32 colocaciones del CF107 del 27/08 al 15/10/2026. Cada plazo tiene una colocación anterior al intervalo (criterio 1 de RF-30). La del 15/10 se incluye a propósito: ya está publicada, pero no rige ninguna valuación (R-14).
- **Serie:** días naturales del 10/09 (cierre base, I = 1) al 14/10.
- **Cortes:**
  - 13/09: domingo; se valúa con los cierres del 11/09.
  - 16/09: festivo; se valúa con los del 15/09.
  - 08/10: vencimiento de BI261008 y reinversión T16; DEMOFIB no tiene cierre ese día.
  - 14/10: corte final.
- **Periodos:**
  - P1-A, del 11/09 al 14/10;
  - P1-B, del 11/09 al 30/09;
  - P1-C, del 01/10 al 14/10;
  - P1-D, del 09/10 al 12/10;
  - P2-A, del 11/09 al 14/10;
  - P2-C, del 01/10 al 14/10.

### Transacciones

| ref | Portafolio | Intermediario | Instrumento | Tipo | Fecha | Títulos | Precio | Importe |
|---|---|---|---|---|---|---:|---:|---:|
| T01 | Principal | Casa A | DEMOACC | compra | 10/09 | 200 | 99.95 | 57.97 |
| T02 | Principal | Casa B | DEMOETF | compra | 10/09 | 100 | 50.05 | 14.51 |
| T03 | Principal | Casa A | BI261008 | compra | 10/09 | 1,500 | 9.9516240 | 0.00 |
| T04 | Principal | Casa B | BI261008 | compra | 10/09 | 1,000 | 9.9516240 | 0.00 |
| T05 | Principal | Casa A | DEMOFIB | compra | 11/09 | 400 | 24.9825 | 28.98 |
| T06 | Principal | Casa B | DEMOACC | compra | 14/09 | 100 | 103.10 | 29.90 |
| T07 | Secundario | Casa A | DEMOACC | compra | 14/09 | 150 | 103.60 | 45.07 |
| T08 | Principal | Casa A | BI261217 | compra | 17/09 | 1,000 | 9.8344372 | 0.00 |
| T09 | Principal | Casa B | BI270318 | compra | 17/09 | 500 | 9.6629250 | 0.00 |
| T10 | Principal | Casa A | DEMOFIB | venta | 22/09 | 400 | 23.2075 | 26.92 |
| T11 | Principal | Casa B | DEMOETF | compra | 25/09 | 60 | 47.90 | 8.33 |
| T12 | Principal | Casa B | DEMOETF | venta | 25/09 | 120 | 48.10 | 16.74 |
| T13 | Principal | Casa A | BI261008 | venta | 01/10 | 500 | 9.9883275 | 0.00 |
| T14 | Principal | Casa A | DEMOACC | venta | 02/10 | 80 | 104.20 | 24.17 |
| T15 | Principal | Casa A | DEMOFIB | compra | 05/10 | 300 | 24.4125 | 21.24 |
| T16 | Principal | Casa B | BI261105 | compra | 08/10 | 1,000 | 9.9528566 | 0.00 |

Las compras de CETES (T03, T04, T08, T09 y T16) son compras en mercado secundario, concertadas ese día al P de RF-26b del día. Ese día d es un nodo exacto (28, 91, 182 y 28 días), así que P coincide con el precio de la colocación de esa semana. T13 es una venta en mercado secundario al P del día.

El vencimiento de BI261008 no es una transacción. El 08/10 se liquidan a 10.00 los 2,000 títulos que siguen en posición (1,000 con Casa A y 1,000 con Casa B): R = 20,000.00, sin ISR.

## Cifras clave

Las cifras completas, sin redondear, están en `esperados/`. Aquí se muestran con 4 decimales y en por ciento con 6.

| Corte | Portafolio | Costo total | Valor de mercado | Resultado no realizado |
|---|---|---:|---:|---:|
| 13/09 | Principal | 59,968.5200 | 60,329.9620 | 361.4420 |
| 13/09 | Secundario | 0.0000 | 0.0000 | 0.0000 |
| 16/09 | Principal | 70,308.4200 | 71,641.8773 (71,641.87725) | 1,333.4573 (1,333.45725) |
| 16/09 | Secundario | 15,585.0700 | 15,712.5000 | 127.4300 |
| 08/10 | Principal | 56,307.8883 | 57,842.7197 | 1,534.8314 |
| 08/10 | Secundario | 15,585.0700 | 16,110.0000 | 524.9300 |
| 14/10 | Principal | 56,307.8883 | 58,940.8782 | 2,632.9899 |
| 14/10 | Secundario | 15,585.0700 | 16,657.5000 | 1,072.4300 |

| Periodo | TWR | Máxima caída | Pico | Valle |
|---|---:|---:|---|---|
| P1-A | 4.392808 % | −6.680477 % | 16/09 (festivo) | 23/09 |
| P1-B | 2.504499 % | −6.680477 % | 16/09 | 23/09 |
| P1-C | 1.842172 % | −2.181030 % | 30/09 (base, I = 1) | 05/10 |
| P1-D | 1.497119 % | 0.000000 % | — | — |
| P2-A | 6.881137 % | −13.675418 % | 15/09 (el 16/09 empata; ver la regla del pico) | 23/09 |
| P2-C | 3.688142 % | −5.088702 % | 30/09 (base, I = 1) | 05/10 |

## Fuentes

- **Tasas:** Banco de México, Sistema de Información Económica (SIE), cuadro CF107, resultados de las subastas primarias de valores gubernamentales.
  - Series de tasa: SF43936, SF43939, SF43942, SF43945 y SF349785. Series de plazo efectivo: SF43935, SF43938, SF43941, SF43944 y SF349778.
  - Página del cuadro: https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=22&accion=consultarCuadro&idCuadro=CF107&locale=es
  - Serie completa en JSON público, sin token: `https://www.banxico.org.mx/SieInternet/consultaSerieGrafica.do?s=<SERIE>,CF107,<posición>&versionSerie=LA-MAS-RECIENTE&l=es`. La posición es la de la serie en el cuadro, tal como la enlaza la página: SF43935, 3; SF43936, 5; SF43938, 7; SF43939, 9; SF43941, 11; SF43942, 13; SF43944, 15; SF43945, 17; SF349778, 19; SF349785, 21.
  - Fechas de consulta: la página del cuadro, el 5, el 6 y el 15/10/2026, y el JSON, el 15/10/2026. Las copias están en `fuentes/` (`cf107_5oct.html`, `cf107_6oct.html`, `cf107_15oct.html` y `sie_json/`). La página del cuadro solo muestra las tres últimas colocaciones de cada serie.
  - Atribución (RF-31): «Fuente: Banco de México, https://www.banxico.org.mx». La coincidencia entre fuentes de cada tasa está en `entradas/tasas.csv`.
- **Calendario:**
  - DOF del 10/12/2025, CNBV, disposiciones que señalan los días de 2026 en que las entidades financieras suspenden operaciones, art. 1, fracciones I a IX (https://dof.gob.mx/nota_detalle.php?codigo=5775684&fecha=10/12/2025).
  - Festivos confirmados con Grupo BMV, Calendario de días festivos (https://www.bmv.com.mx/es/grupo-bmv/calendario-de-dias-festivos), consultado el 15/10/2026.
- **Precios de DEMOACC, DEMOETF y DEMOFIB:** sintéticos de demostración, no son precios reales (R-04, R-05 y RF-07). Fuente: «Semilla sintetica de demostracion 077».

## Reglas aplicadas

| Regla | Origen |
|---|---|
| Portafolio sin efectivo. Una compra es una aportación A = títulos × precio + importe; una venta, un retiro R = títulos × precio − importe; un vencimiento de CETES, un retiro R = títulos × 10.00, sin ISR. | RF-09 crit. 2; RF-26a crit. 1; P-09; P-16; S-14 |
| Fecha de concertación, corte inclusivo y compras antes que ventas el mismo día. | RF-06 crit. 2; RF-08 crit. 3; P-09 |
| Posición = suma de los saldos por intermediario dentro del portafolio; las emisiones vencidas no cuentan. Títulos enteros. | RF-06; RF-26a; 3.4.3; X-06; P-07 |
| Costo promedio ponderado por intermediario en cada portafolio. Costo por título de una compra = (títulos × precio + importe) / títulos. Una venta no cambia el costo unitario y, con saldo 0, el costo se reinicia. Resultado no realizado = valor − títulos × costo unitario. | RF-05; RF-08; P-10; X-03 |
| Valor = títulos × último cierre igual o anterior a la fecha. | RF-08 crit. 4; P-09 |
| CETES: d = días naturales al vencimiento (≥ 1). En cada plazo rige la última colocación con fecha igual o anterior, con su plazo efectivo. La tasa se interpola linealmente por plazo efectivo; fuera del rango, se usa la del extremo. r va sin redondear. P = 10.00 / (1 + r/100 × d/360), a 7 decimales con la mitad alejándose de cero. | RF-26b; P-11; R-14; RD-16 |
| r(t) = [V(t) + R(t)] / [V(t−1) + A(t)] − 1. TWR = Π[1 + r(t)] − 1, sin anualizar. | RF-09; P-09 |
| I(t) = Π[1 + r(s)]. Máxima caída = mín{I(t) / máx[I(u), u ≤ t]} − 1, negativa o cero, medida sobre el índice. | RF-10; P-09 |
| No se redondea nada salvo P. Los importes se guardan con 4 decimales o más y los por cientos con 6 o más. | RD-12; RD-16; P-13 |
| Ningún saldo por intermediario queda negativo en ninguna fecha. Ninguna transacción de una emisión puede tener fecha igual o posterior a su vencimiento. | RF-28; RF-26a crit. 2 |

### Recomendaciones de 3.2 aplicadas

Son los ⟦decidir: recomendado⟧ de 3.2, y se registran como recomendaciones:

- RF-09: serie diaria en días naturales, y factor 1 si el denominador es 0.
- RF-04, criterio 3: prefijo DEMO.
- RF-05, criterio 2: importe con 2 decimales que admite 0, y rechazo de una venta cuyo importe sea igual o mayor que títulos × precio.
- RF-09, criterio 3: rechazo de periodos invertidos o fuera de las semillas.

### Decisiones abiertas de 3.2 que el oráculo fija

En 3.2 son ⟦decidir⟧ sin recomendación. El oráculo las fija así para poder calcular, y Ramon debe confirmarlas:

- RF-09: la serie parte del cierre del día previo al inicio del periodo (bases V(10/09), V(30/09) y V(08/10)).
- RF-10: I = 1 al inicio es el primer máximo (en P1-C y P2-C, el pico es la fecha base).

### Decisiones y convenciones

- **P-16**, delegada en Claude:
  - el precio por título y el importe de las comisiones con IVA se capturan por separado;
  - la liquidación es al valor nominal, antes del ISR;
  - la reinversión se registra como compra.
- **Compras de CETES:** T03, T04, T08, T09 y T16 son compras en mercado secundario, concertadas ese día al P de RF-26b del día (P-09; 4.4, «fecha en que se pactó la operación, no la de su liquidación»). No se modelan como compras en subasta: una compra en subasta se concierta el martes de la subasta, y T03 y T04 caerían el 08/09, antes del intervalo de las semillas (RD-07; criterio 3 de RF-05). Si Ramon prefiere modelarlas así, hay que adelantar `intervalo_semillas_inicio` y regenerar precios, serie, periodos y esperados.
- **Datos sintéticos:**
  - comisión de 0.29 % (0.25 % más IVA de 16 %), redondeada al centavo; solo sirve para generar los importes y el motor no la usa;
  - T13 se vende al P del día, sin comisión;
  - DEMOFIB no tiene cierre el 08/10.
- **Convenciones de presentación:**
  - el costo unitario es 0 cuando el saldo es 0;
  - **pico:** la primera fecha (la más antigua, contando la fecha base con I = 1) en que I alcanza el máximo vigente en el valle; si ese máximo es el I = 1 inicial, el pico es la fecha base;
  - **valle:** la primera fecha con la caída mínima;
  - en P2-A, I(16/09) = I(15/09), porque el 16/09 es festivo y Secundario no tiene CETES; por esta regla, el pico es el 15/09;
  - si la máxima caída es 0, pico y valle quedan vacíos;
  - el periodo más temprano empieza el 11/09, con base en el cierre del 10/09.

## Matriz de cobertura

| Caso | Requisito | Dónde | Qué se comprueba |
|---|---|---|---|
| Instrumento en dos intermediarios | OE-5; RF-06 crit. 1 | `posiciones`, 16/09, 08/10 y 14/10 | DEMOACC: 200 + 100 = 300; 120 + 100 = 220. BI261008: 1,500 + 1,000. |
| CETES que vence en el periodo | OE-5; RF-26a crit. 1 | `serie_diaria` 08/10; `posiciones` 08/10 y 14/10 | R(08/10) = 20,000.00; posición 0 desde el vencimiento |
| Día sin cierre | 5.2; RF-08 crit. 4 | `precios_usados`; cortes 13/09 y 16/09; DEMOFIB el 08/10 | Usa el cierre del 11/09, del 15/09 y del 07/10 |
| Caída con recuperación | 5.2; RF-10 crit. 1 | `indicadores` P1-A | Pico el 16/09, valle el 23/09 y nuevo máximo el 30/09; la segunda caída no cambia la máxima |
| Venta parcial | 5.2; RF-08 crit. 1 | T14, T13 y T12 | El costo unitario no cambia (100.23985 con Casa A) |
| Corte inclusivo | RF-06 crit. 2 | `posiciones` 13/09 y 08/10 | T06 y T07 no cuentan el 13/09; T16 sí cuenta el 08/10 |
| Otro portafolio no cuenta | RF-06 crit. 3; X-06 | `posiciones` 16/09; N3 | DEMOACC en Principal = 300, no 450 |
| Costo por intermediario | RF-08 crit. 2 | `posiciones` 08/10 y 14/10 | 100.23985 (Casa A) y 103.399 (Casa B) |
| Compras antes que ventas | RF-08 crit. 3; RF-28 | T11, T12; `casos_positivos.csv` (C1) | Costo de 40 títulos = 49.3865; T12 se acepta (saldo 40; con la venta primero, −20) |
| Costo que se reinicia | RF-08 | DEMOFIB, cortes 08/10 y 14/10 | El costo unitario es el de T15 (24.4833) |
| TWR sin flujos | RF-09 crit. 1 | P2-C | 111.05 / 107.10 − 1 |
| Flujos con importe y vencimiento | RF-09 crit. 2 | `serie_diaria` | A incluye el importe; R lo descuenta; R(08/10) = 20,000.00 |
| Días naturales, base y denominador 0 | RF-09 (recomendado y decisión abierta) | `serie_diaria`; P2-A | r > 0 en fines de semana; P2 tiene r = 0 del 11/09 al 13/09 |
| Encadenamiento | RF-09 | P1-A, P1-B, P1-C | (1 + TWR B)(1 + TWR C) = 1 + TWR A |
| Serie que no baja | RF-10 crit. 2 | P1-D | Máxima caída 0 |
| I = 1 como primer máximo | RF-10 (decisión abierta) | P1-C, P2-C | El pico es la fecha base (30/09) |
| Pico con empate | RF-10 (convención) | P2-A | I(16/09) = I(15/09); el pico es el 15/09 |
| Interpolación por plazo efectivo | RF-26b crit. 1 | `valuacion_cetes` BI261217 y BI270318 | Entre 28 y 91, entre 91 y 182 y entre 91 y 175 efectivos |
| Tasa del extremo | RF-26b crit. 2 (solo extremo inferior) | BI261008 y BI261105 con d < 28 | Usan la tasa a 28 días |
| Extremo superior y nodos de 364 y 728 días | RF-26b crit. 2; RF-30 | No se ejercitan en 5.2: el d máximo es 182 y el plazo efectivo del nodo más largo nunca baja de 679 | Solo los cubren la prueba del motor CPF-26b (d = 100 con nodos de 28 y 91: P = 9.8039216) y CPF-30 (carga de los cinco plazos) |
| Última colocación igual o anterior | RF-26b crit. 3; R-14 | 07/10 (d = 1) y 14/10 | El 07/10 usa la del 01/10 (6.01), no la del 08/10; la del 15/10 no rige |
| Nodos exactos y P a 7 decimales | RF-26b | Días de compra; T13 | P = precio de compra; 91 de 91 P iguales en los dos caminos |
| Reinversión como compra | RF-26a crit. 3; S-14 | T16 | El sistema no crea transacciones |
| Rechazos | RF-28 crit. 1 a 3; RF-26a crit. 2 | `rechazos_rf28.csv` N1 a N4; hoja Rechazos | Saldo −50 (18/09), −100 (el 22/09, no el 15/09) y −30 (09/10); fecha igual al vencimiento |
| Rechazos opcionales | RF-05 crit. 3; RF-09 crit. 3 | N5 a N8 | Fechas fuera del intervalo; periodo invertido o fuera de las semillas |
| Datos de entrada válidos | RF-04, RF-05, RF-07, RF-30, RF-31; 4.3 y 4.4 | `entradas/`; hoja Comprobaciones | Escalas, claves, días con operaciones (calendario completo), plazos efectivos, semilla de tasas, fuentes, licencias y cargas |
| Fuente y fecha del dato | RF-31 crit. 1 a 3 | `cargas_datos.csv`, `versiones_licencia.csv`; `posiciones` (fecha_precio y colocaciones) | Cada precio y tasa ligado a una carga con fuente y licencia; el cierre usado y las colocaciones de cada valuación |
| Una cifra en todas las vistas | RF-11 crit. 1 y 2; RNF-02 | Hoja Posiciones; `serie_diaria` | Total del corte = suma por intermediario = V(t) |

## Tolerancias de RNF-01 y cómo debe compararlo pytest

### Comparación

1. Carga `entradas/` en la base (semilla), en este orden: usuario (con lo que genera la Instalación de semillas), portafolios, intermediarios, instrumentos, fuentes, versiones de licencia, cargas, precios y tasas. Después inserta T01 a T16 **en el orden de `ref`**. Cada una debe aceptarse.
2. Para cada renglón de `esperados/*.csv`, pide al motor la cifra con la misma llave.
3. Compara **sin redondear**. Lee los CSV con `decimal.Decimal`, nunca con `float`, y no redondees la salida del motor antes de comparar (P-13).
4. Guarda la tabla de diferencias como evidencia de 3.9.

### Tolerancias

| Cifras | Columnas | Tolerancia |
|---|---|---|
| Importes (RNF-01) | `valor`, `costo_total`, `resultado_no_realizado`, `aportaciones`, `retiros*`, `monto`, `aportacion`, `retiro`, `valor_base`, `valor_fin`, `costo_total_fin`, `resultado_no_realizado_fin` | \|motor − esperado\| ≤ 0.01 |
| TWR y máxima caída (RNF-01) | `twr_por_ciento`, `maxima_caida_por_ciento` | ≤ 0.001 puntos porcentuales; en fracción (`twr`, `maxima_caida`), ≤ 0.00001 |
| Exactas | `titulos`, `d`, plazos, fechas (`fecha_precio`, `fecha_pico`, `fecha_valle`, colocaciones), `caso` y P de CETES (`p`, 7 decimales) | Igualdad exacta (recomendado; RNF-01 no fija tolerancia) |
| Otras sin tolerancia en RNF-01 | `r` y `r_por_ciento` diarios, `indice`, `caida`, costos y precios por título, `r_por_ciento_anual` | Se sugieren 0.001 pp para las fracciones y 1e-7 para los precios por título |

`fecha_pico` y `fecha_valle` se comparan con igualdad exacta porque siguen la regla de «Convenciones de presentación»: con empates, la fecha más antigua. Un motor que actualice el máximo con «≥», o que tome la última fecha del máximo, reportaría el 16/09 como pico de P2-A y debe ajustarse a esa regla.

### Rechazos

Después de cargar T01 a T16, intenta cada renglón de `rechazos_rf28.csv` (todos son N). Cada uno debe:

- rechazarse sin registrar nada;
- informar el motivo de la columna `regla`;
- dejar todas las cifras de `esperados/` sin cambio.

`fecha_saldo_negativo` y `saldo_resultante` solo tienen valor en los rechazos por RF-28: son la primera fecha en que el saldo del par quedaría negativo y ese saldo. Las columnas de transacción (`intermediario_nombre` a `importe_comisiones`) están vacías en los candidatos de periodo (N7 y N8), y las de periodo, en los de transacción.

`casos_positivos.csv` documenta C1, que no se registra: T11 y T12, ya cargadas, se aceptan porque el saldo de DEMOETF con Casa B queda en 100 + 60 − 120 = 40. Un validador que aplicara la venta antes que la compra vería 100 − 120 = −20 y rechazaría T12.

### Ejemplo

```python
from decimal import Decimal
import csv

TOL_IMPORTE, TOL_PP = Decimal("0.01"), Decimal("0.001")

with open(RUTA / "esperados" / "indicadores.csv", encoding="utf-8") as fh:
    for fila in csv.DictReader(fh):
        r = motor.indicadores(fila["portafolio"], fila["inicio"], fila["fin"])   # Decimal, sin redondear
        assert abs(r.twr * 100 - Decimal(fila["twr_por_ciento"])) <= TOL_PP
        assert abs(r.maxima_caida * 100 - Decimal(fila["maxima_caida_por_ciento"])) <= TOL_PP
        assert abs(r.valor_fin - Decimal(fila["valor_fin"])) <= TOL_IMPORTE
```

## Pendientes antes de congelar

1. **Confirmar la tasa a 28 días del 10/09/2026** (6.25000 %, plazo efectivo de 28) con una segunda fuente: el CF107 con rango de fechas o la API con token. La página pública del cuadro no sirve, porque solo muestra las tres últimas colocaciones. Es la única tasa de una sola fuente que mueve cifras: T03, T04 y las valuaciones de BI261008 del 10/09 al 16/09. Las del 27/08 y del 03/09 también tienen una sola fuente, pero no mueven ninguna cifra.
2. **Confirmar las dos decisiones abiertas de 3.2** que el oráculo fija (serie desde el cierre previo e I = 1 como primer máximo) y la licencia de la semilla sintética (RF-31 crit. 1). Al redactar la ficha de RF-10, agregar la regla del pico y del valle con empates.
3. **Opcional, antes de congelar:** ejercitar el nodo de 364 días con una compra de la emisión de 364 días colocada el 17/09 (vence el 15/09/2027, efectivo 363). Cambiaría todas las cifras de Principal, así que habría que regenerar los esperados.
4. **Revisar las fórmulas del libro y congelar con un commit** antes de programar el motor. Este trabajo no tocó el repositorio.
   - Ubicación: `backend/tests/oraculo/`, la que propone el borrador de 5.2, para que pytest lea `esperados/` desde ahí. El README del repositorio todavía dice `backend/tests/fixtures/`: ajústalo al congelar.
   - No subas `fuentes/bmv_calendario_dias_festivos.html`: la BMV prohíbe reproducir el contenido de su sitio (R-05). Basta con citar su dirección. Las copias del CF107 sí pueden subirse, porque el Banco de México permite reutilizar su información citando la fuente (D-03).
   - Tampoco subas `prueba_recalc.xlsx`, que no es parte del oráculo.
