# Registro de resultados del 18 de octubre de 2026 (entrega del MVP)

Este índice reúne la evidencia de los criterios de aceptación del MVP (SRS 3.9.2) que se guarda en esta carpeta. Lo llenó el agente de evidencia la noche del 18/10/2026 con los datos de los propios archivos: los conteos de pruebas salen de leer `junit.xml` caso por caso, y los del recorrido, de `ac04/recorrido.csv`. Lo que todavía no tiene resultado dice «pendiente» y se reúne en la sección «Pendientes».

Las claves R3, R4, R5, R7, E3, E5, T4 y H-12 son tareas y decisiones del plan de trabajo del 18/10/2026, que no está en el repositorio; no son las restricciones R-03 ni R-04 del SRS 2.4.

- **Fecha y hora de la corrida:** 2026-10-18, de las 21:10 a las 21:11 de Sonora (UTC−7). `junit.xml` empieza a las 21:10:58 y dura 53.41 s; `ac03_junit.xml` empieza a las 21:11:53.
- **Último commit de código:** e636b78, «Construye el cliente web del MVP (pantallas V-01 a V-12)», del 18/10/2026 a las 21:06 (P-70: la corrida y el recorrido completo se hicieron después de ese commit). El backend (`backend/app`) no cambió desde faf6b32, del 17/10/2026. `cpnf01_versiones.csv` guarda el hash completo de e636b78 (HEAD) y el de 11097f8.
- **Equipo:** el equipo de desarrollo (R-07), Windows 11, con PostgreSQL 18, Python 3.13 (uv) y Node 24.
- **Base del recorrido:** la base de desarrollo de Ramon, `proyecto077` (puerto 5432, scripts 01 a 04 y rol `app_077`), con 5.2 cargado por `tests/referencia/cargador.py` en la cuenta ficticia `oraculo@example.com`; el cliente web en `http://localhost:5173` y, detrás de su proxy, la API en `127.0.0.1:8000`. El ensayo previo del guion (20:59, 54 de 54) se hizo en el entorno temporal y su salida no está en el repositorio.
- Ninguna ruta de usuario, contraseña, cookie ni token aparece en este índice ni en los archivos de esta carpeta (revisión E5, al final).

## Resumen por criterio de aceptación

| AC | Resultado | Evidencia en esta carpeta | Otra evidencia |
|---|---|---|---|
| AC-01 | Cumple: los 18 imprescindibles aprueban su CPF (101 casos de `junit.xml`, ninguno fallido, con error ni omitido) y cada uno tiene al menos una captura de AC-04 | `junit.xml` (sección «AC-01») y capturas de `ac04/` | Pantallas del cliente web (e636b78) |
| AC-02 | Cumple: CPNF-02 a CPNF-04 aprueban en `junit.xml` (20 de 20) y `cpnf05.txt` dice «CPNF-05: cumple»; según informó Ramon, terminó con código de salida 0, que el archivo no registra | `junit.xml`, `cpnf05.txt` y `ac04/RNF-02_*.png` (sección «AC-02») | — |
| AC-03 | Cumple: las 3,678 cifras de CPNF-01 quedan dentro de tolerancia, y 11097f8 es anterior a b3391fd (3 de 3 en `ac03_junit.xml`). La comprobación a mano de R4 está pendiente | `cpnf01_diferencias.csv`, `cpnf01_resumen.csv`, `cpnf01_versiones.csv` y `ac03_junit.xml` (sección «AC-03») | — |
| AC-04 | Cumple: el recorrido completo de las 21:08 deja 54 filas sin falla y 33 capturas, al menos una por cada imprescindible, por RNF-02 y por RNF-03 | `ac04/*.png`, `ac04/recorrido.csv` y `recorrido_ac04.mjs` (sección «AC-04») | — |
| AC-05 | No se registra aquí | — | Sección «Cómo ejecutarlo localmente» del `README.md` |
| AC-06 | No se registra aquí | — | `docs/MVP.md` y `docs/PRD.md`, versión 1.1 del 18/10/2026 (la 1.0 entró en 358fdae) |
| AC-07 | Cumple en lo inspeccionado (sección «AC-07») | Este índice | `backend/04_cargar_semillas.sql` |
| AC-08 | Pendiente (R3): la revisión del Diario Oficial de la Federación conforme a D-04 todavía no tiene resultado | — | SRS 3.1 |

## AC-01. Requisitos imprescindibles y sus CPF

Corrida con registro, desde `backend/`:

```
uv run --frozen pytest --registro-resultados --junitxml=tests/resultados/2026-10-18/junit.xml
```

Totales de `junit.xml`: 271 pruebas; 271 aprobadas, 0 fallidas, 0 con error y 0 omitidas; 53.41 s. La salida de consola (`_e3_salida.txt`) dice «271 passed, 3 deselected in 53.41s» y termina con código 0: las 3 deseleccionadas son las de inspección de AC-03 (marca `inspeccion`, que no corre por omisión) y se corrieron aparte (sección «AC-03»). No hubo reintentos.

El conteo se hizo leyendo cada `<testcase>` de `junit.xml`; su `classname` da el archivo. En los archivos que comparten requisitos, cada caso se asigna por su nombre: en `motor/test_criterios_3_2.py`, por el prefijo `test_rfNN_`; en `api/test_cpf26_valuacion.py`, `test_vencimiento_deja_la_posicion_en_cero` es de RF-26a (crit. 1) y `test_rige_la_ultima_colocacion_igual_o_anterior`, de RF-26b (crit. 3); en `api/test_cpf07_30_31_semillas.py`, `test_marcas_de_demostracion_y_procedencia_por_la_api` cuenta para RF-07 (crit. 3) y para RF-31. Por ese caso compartido, la columna «Pruebas» suma 102 con 101 casos distintos.

| Requisito | CPF | Casos de `junit.xml` por archivo | Pruebas | Aprobadas | Fallidas, con error u omitidas | Filas y capturas de AC-04 |
|---|---|---|---|---|---|---|
| RF-01 | CPF-01 | `cuentas/test_cpf01_registro_sesion.py`: 12 | 12 | 12 | 0 | 3 filas, 3 capturas |
| RF-02 | CPF-02 | `api/test_cpf02_propiedad.py`: 3 | 3 | 3 | 0 | 2 filas, 2 capturas |
| RF-03 | CPF-03 | `api/test_cpf03_portafolios.py`: 5 | 5 | 5 | 0 | 5 filas, 5 capturas |
| RF-04 | CPF-04 | `api/test_cpf04_catalogo.py`: 3 | 3 | 3 | 0 | 1 fila, 1 captura |
| RF-05 | CPF-05 | `api/test_cpf05_transacciones.py`: 8; `motor/test_criterios_3_2.py` (`test_rf05_*`): 1 | 9 | 9 | 0 | 3 filas, 3 capturas |
| RF-06 | CPF-06 | `api/test_cpf06_posiciones.py`: 4; `motor/test_criterios_3_2.py` (`test_rf06_*`): 3 | 7 | 7 | 0 | 1 fila, 1 captura |
| RF-07 | CPF-07 | `api/test_cpf07_30_31_semillas.py`: 3 (los dos `test_cpf07_*` y `test_marcas_…`) | 3 | 3 | 0 | 2 filas, 2 capturas |
| RF-08 | CPF-08 | `motor/test_criterios_3_2.py` (`test_rf08_*`): 6 | 6 | 6 | 0 | 2 filas, 2 capturas |
| RF-09 | CPF-09 | `motor/test_criterios_3_2.py` (`test_rf09_*`): 5 | 5 | 5 | 0 | 1 fila, 1 captura |
| RF-10 | CPF-10 | `motor/test_criterios_3_2.py` (`test_rf10_*`): 7 | 7 | 7 | 0 | 1 fila, 1 captura |
| RF-11 | CPF-11 | `api/test_cpf11_tablero.py`: 6 | 6 | 6 | 0 | 3 filas, 3 capturas |
| RF-12 | CPF-12 | `cuentas/test_cpf12_consentimiento.py`: 3 | 3 | 3 | 0 | 11 filas, 11 capturas |
| RF-25 | CPF-25 | `api/test_cpf25_intermediarios.py`: 3 | 3 | 3 | 0 | 2 filas, 2 capturas |
| RF-26a | CPF-26a | `api/test_cpf26a_registro.py`: 3; `api/test_cpf26_valuacion.py`: 1; `motor/test_criterios_3_2.py` (`test_rf26a_*`): 5 | 9 | 9 | 0 | 1 fila, 1 captura |
| RF-26b | CPF-26b | `api/test_cpf26_valuacion.py`: 1; `motor/test_criterios_3_2.py` (`test_rf26b_*`): 8 | 9 | 9 | 0 | 2 filas, 2 capturas |
| RF-28 | CPF-28 | `api/test_cpf28_saldo.py`: 5; `motor/test_criterios_3_2.py` (`test_rf28_*`): 4 | 9 | 9 | 0 | 2 filas, 1 captura |
| RF-30 | CPF-30 | `api/test_cpf07_30_31_semillas.py` (`test_cpf30_*`): 1 | 1 | 1 | 0 | 2 filas, 2 capturas |
| RF-31 | CPF-31 | `api/test_cpf07_30_31_semillas.py`: 2 (`test_cpf31_*` y `test_marcas_…`) | 2 | 2 | 0 | 2 filas, 2 capturas |

Las otras 170 pruebas de `junit.xml` se cuentan aparte, por CPNF y por grupo; todas aprueban (101 + 170 = 271):

| Grupo | Archivo | Pruebas | Fallidas, con error u omitidas |
|---|---|---|---|
| CPNF-01, nivel 1 (el motor contra 5.2; incluye las cifras idénticas entre vistas de RNF-02) | `motor/test_oraculo_5_2.py` | 27 | 0 |
| CPNF-01, nivel 2 (la base y el servicio contra 5.2; genera los `cpnf01_*.csv`) | `referencia/test_cpnf01.py` | 3 | 0 |
| CPNF-02 | `referencia/test_cpnf02.py` | 17 | 0 |
| CPNF-03 | `no_funcionales/test_cpnf03.py` | 2 | 0 |
| CPNF-04 | `no_funcionales/test_cpnf04.py` | 1 | 0 |
| Infraestructura | `infra/test_infraestructura.py` | 28 | 0 |
| Cookie y origen | `cuentas/test_cookie_origen.py` | 10 | 0 |
| Dependencias | `cuentas/test_dependencias.py` | 5 | 0 |
| Aislamiento del motor | `motor/test_aislamiento.py` | 46 | 0 |
| Presentación del motor | `motor/test_presentacion.py` | 13 | 0 |
| Resto de los criterios del motor: decisiones D-22, D-38 y RD-24 (3), validación del periodo y del corte (2) y de las entradas y el mercado (13) | `motor/test_criterios_3_2.py` | 18 | 0 |
| **Total** | | **170** | **0** |

Lo que solo cumple la interfaz (tabla «Criterios que solo cumple la interfaz» del plan) queda en las capturas de AC-04.

## AC-02. Requisitos no funcionales del 18 de octubre

| RNF | CPNF | Evidencia | Resultado |
|---|---|---|---|
| RNF-02 | CPNF-02 | `referencia/test_cpnf02.py` en `junit.xml`; además, las capturas `ac04/RNF-02_*.png` y la consulta repetida (paso 3 del recorrido) | Cumple: 17 de 17, y en el recorrido la tarjeta, la etiqueta del corte, la última fila y el total de V-05 dicen «$58,940.88» en las dos consultas |
| RNF-03 | CPNF-03 | `no_funcionales/test_cpnf03.py` en `junit.xml`; además, el paso 10.7 del recorrido (lo ajeno y lo inexistente con el mismo texto) | Cumple: 2 de 2, y V-12 muestra «No existe el portafolio.» tanto para el portafolio ajeno como para el inexistente |
| RNF-04 | CPNF-04 | `no_funcionales/test_cpnf04.py` en `junit.xml`, en la misma corrida y sin reintento | Cumple: 1 de 1 |
| RNF-05 | CPNF-05 | `cpnf05.txt`, que generó Ramon a las 21:28 con `tests/inspeccion/cpnf05_credenciales.py` | Cumple: «CPNF-05: cumple» en `cpnf05.txt`; código de salida 0, según informó Ramon |

`cpnf05.txt` solo tiene conteos: 3 credenciales buscadas; 0 coincidencias en el historial de git (26 commits), en el índice, en el árbol de trabajo (sin los ignorados), en `frontend/dist` (36 archivos) y en los registros (45 archivos); `backend/.env` está ignorado por git y ningún commit lo incluye. Su última línea dice «CPNF-05: cumple».

## AC-03. Exactitud del motor contra 5.2

- Tabla de diferencias de CPNF-01: `cpnf01_diferencias.csv`, con 3,678 cifras de los 7 archivos de `esperados/`, todas con «cumple = sí». Su resumen (`cpnf01_resumen.csv`) tiene 19 grupos por archivo y tolerancia, con 0 cifras fuera de tolerancia; la mayor diferencia es de 1 × 10⁻²⁶ (`valuacion_cetes.csv`). Las versiones comparadas (`cpnf01_versiones.csv`) son HEAD, en e636b78, y 11097f8. Resultado: cumple. En `junit.xml`, CPNF-01 aprueba en sus dos niveles: `motor/test_oraculo_5_2.py` (27 de 27) y `referencia/test_cpnf01.py` (3 de 3).
- El commit que congela 5.2, 11097f8 (15/10/2026 19:47), es anterior al primero del motor, b3391fd (17/10/2026 11:00), que es el que agrega `backend/app/motor`. Inspección con `pytest -m inspeccion tests/inspeccion/test_ac03.py`, desde `backend/` y con salida en `ac03_junit.xml`: 3 de 3 aprobadas (11097f8 es ancestro de HEAD, en él todavía no existía `backend/app/motor` y `backend/tests/oraculo` no cambió desde entonces).
- Comprobación a mano de las tres cifras de la nota a.1 del borrador de 5.2 (costo por título de T01, BI261217 al 14/10 y el TWR de P2-C): **pendiente (R4)**; Ramon todavía no la registra. Mientras tanto, las tres cifras están entre las que compara CPNF-01 y quedan dentro de tolerancia (en `cpnf01_diferencias.csv`, las filas de `T01` y `costo_por_titulo`, las de `2026-10-14` y `BI261217`, y las de `P2-C` y `twr`); R4 es la comprobación independiente, con calculadora.

## AC-04. Recorrido de los imprescindibles

- **Guion:** `recorrido_ac04.mjs`, en esta carpeta. Node 24 sin dependencias y Microsoft Edge sin interfaz, controlado por el protocolo de DevTools. Localiza cada pantalla y cada control por su atributo `data-recorrido`, espera a `[data-listo]` antes de capturar y toma las capturas con una ventana de 1280 × 720, en modo claro; las de pantalla completa conservan el ancho de 1280 y llevan el alto de la página.
- **Cómo se ejecutó** (desde la raíz del repositorio; el guion pide la contraseña sin mostrarla):

  ```
  node backend/tests/resultados/2026-10-18/recorrido_ac04.mjs --base http://localhost:5173 --correo oraculo@example.com --salida backend/tests/resultados/2026-10-18/ac04
  ```

- **Hora de inicio y de fin:** el recorrido completo empezó a las 21:08 (primera fila, 21:08:27) y terminó a las 21:09:10 (última fila, 21:09:09), con 54 filas sin falla (53 «correcto» y 1 «coincide») y 0 fallas. **Pasos fallidos y respaldo a mano:** ninguno; las 33 capturas son del guion y cada una tiene su fila en `ac04/recorrido.csv`. Un paso fallido se puede repetir solo, con `--pasos N` (por ejemplo, `--pasos 8,10`); sus filas se agregan a `ac04/recorrido.csv`. Las capturas `fallo-paso-NN_*.png` y `fallo-inicio_*.png` son de diagnóstico, no evidencia.
- **Intentos previos:** antes del recorrido completo quedaron en el mismo `ac04/recorrido.csv` dos intentos que no pasaron del inicio de sesión de la cuenta del oráculo, a las 20:14:21 y a las 21:07:44. Cada uno tiene su fila «inicio» con «falló» y su captura de diagnóstico (`fallo-inicio_V-01_2026-10-18_2014.png` y `fallo-inicio_V-01_2026-10-18_2107.png`, idénticas: V-01 con el mensaje único de RF-01 crit. 3, el correo `oraculo@example.com` y la contraseña vacía). Si el inicio de sesión falla, el guion guarda esa fila y termina sin ejecutar ningún paso, así que esos intentos no dejaron capturas de evidencia. El registro no dice la causa, porque el mensaje es el mismo para cualquier causa (RF-01 crit. 3) y el guion no guarda la contraseña; consta, eso sí, que el consentimiento de la cuenta del oráculo en esa base se otorgó el 18/10/2026 a las 20:57 (captura `RF-12_V-11_2026-10-18_2108.png`), después del primer intento. El recorrido completo de las 21:08 los supera.
- **Registro:** `ac04/recorrido.csv`, con una fila por requisito y captura (requisito, pantalla, archivo, hora, resultado y detalle). Los nombres de las capturas siguen la forma `RF-11_V-04_2026-10-18_HHMM.png`, con un sufijo cuando una misma pantalla tiene varias.
- **Orden** (T4: nada que cambie las cifras de 5.2 se hace antes de capturarlas): 1) V-04 de «Principal»; 2) V-05 al 14/10; 3) consulta repetida de V-04 y V-05 (RNF-02); 4) V-06; 5) V-07 con el rechazo N1; 6) V-10; 7) V-09; 8) en V-08, alta, cambio de nombre y eliminación del portafolio desechable «Recorrido AC-04 (desechable)», con una compra válida en él; 9) V-11 de la cuenta del oráculo, sin revocar; 10) en un contexto aislado, la cuenta B (`recorrido-b-HHMM@example.com`, con una clave aleatoria que no se guarda; en esta corrida, `recorrido-b-2108@example.com`): aviso sin sesión, registro sin y con consentimiento, inicio de sesión fallido y correcto, «Casa A», portafolio ajeno e inexistente, y revocación.

Las capturas se nombran `REQ_PANTALLA_2026-10-18_HHMM[_sufijo].png`; en la tabla, `…` sustituye a `_2026-10-18_HHMM` (2108 o 2109). Una misma captura completa de V-04 o V-05 sirve a varios requisitos (`ac04/recorrido.csv` tiene una fila por cada uno).

| Requisito | Criterios que se ven | Capturas (`ac04/`) | Resultado |
|---|---|---|---|
| RF-01 | crit. 1 a 3 en lo visible: rechazo sin efecto, alta, mensaje único ante la contraseña errónea y la contraseña vaciada | `RF-12_V-02…_rechazo`, `RF-01_V-01…_cuenta-creada` y `RF-01_V-01…_rechazo` | Correcto (3 filas) |
| RF-02 | crit. 2: el portafolio ajeno muestra lo mismo que el inexistente | `RF-02_V-12…_ajeno` y `RNF-03_V-12…_inexistente` | Correcto (2 filas) |
| RF-03 | crit. 1 y 3: alta, cambio de nombre, diálogo de eliminar, Cancelar sin cambios y eliminación confirmada | `RF-03_V-04…_alta`, `RF-03_V-08…_cambio-nombre`, `…_dialogo-eliminar`, `…_cancelado` y `…_eliminado` | Correcto (5 filas) |
| RF-04 | crit. 1 a 3 | `RF-04_V-10…` | Correcto (1 fila) |
| RF-05 | consulta (V-06) y registro de una compra válida en el portafolio desechable | `RF-05_V-06…`, `RF-05_V-07…_compra` y `RF-05_V-06…_registrada` | Correcto (3 filas): 15 transacciones en «Principal»; compra de 10 DEMOACC con «Transacción registrada» |
| RF-06 | posiciones al 14/10 | `RF-06_V-05…` | Correcto (1 fila) |
| RF-07 | crit. 3: etiqueta «Datos de demostración» | `RF-11_V-04…` y `RF-06_V-05…` | Correcto (2 filas) |
| RF-08 | valor de mercado y resultado no realizado | `RF-11_V-04…` y `RF-06_V-05…` | Correcto (2 filas): $58,940.88 y $2,632.99 |
| RF-09 | TWR del periodo | `RF-11_V-04…` | Correcto (1 fila): 4.39 %, sin anualizar |
| RF-10 | máxima caída con el pico y el valle | `RF-11_V-04…` | Correcto (1 fila): -6.68 %, del pico del 16/09/2026 al valle del 23/09/2026 |
| RF-11 | crit. 1 (indicadores con unidad y fecha), crit. 2 (gráfica con la etiqueta del corte) y crit. 3 (tablero sin datos del portafolio desechable) | `RF-11_V-04…`, `RF-11_V-04…_grafica` y `RF-03_V-04…_alta` | Correcto (3 filas) |
| RF-12 | crit. 1 (V-11, casilla sin marcar y rechazo sin consentimiento), crit. 2 (aviso sin sesión y en el diálogo), crit. 3 (revocación de la cuenta B) y crit. 4 (avisos en V-04 a V-06) | `RF-12_V-11…`, `RF-12_V-02…_casilla`, `…_rechazo`, `RF-12_V-03…_sin-sesion`, `RF-12_V-02…_dialogo-aviso`, `RF-12_V-11…_dialogo-revocar`, `RF-12_V-01…_revocado` y `…_bloqueada`; crit. 4: `RF-11_V-04…`, `RF-06_V-05…` y `RF-05_V-06…` | Correcto (11 filas) |
| RF-25 | consulta y crit. 1: «Casa A» en otra cuenta | `RF-25_V-09…` y `RF-25_V-09…_casa-a-cuenta-b` | Correcto (2 filas) |
| RF-26a | CETES vencida y liquidada a su valor nominal | `RF-06_V-05…` | Correcto (1 fila) |
| RF-26b | CETES vigentes con «estimado» y el caso de la tasa | `RF-06_V-05…` y `RF-11_V-04…` | Correcto (2 filas) |
| RF-28 | crit. 1 y 3: motivo del rechazo de N1, nada registrado (E17 igual antes y después) y lo capturado se conserva | `RF-28_V-07…` | Correcto (2 filas): «No se registró la transacción…»; E17 con 15 transacciones antes y después |
| RF-30 | tasas con su fecha de colocación | `RF-06_V-05…` y `RF-11_V-04…` | Correcto (2 filas) |
| RF-31 | crit. 2 y 3: línea de fuente del Banco de México y procedencia de cada valuación | `RF-11_V-04…` y `RF-06_V-05…` | Correcto (2 filas) |
| RNF-02 | la misma cadena en la tarjeta, la etiqueta del corte, la última fila y el total, también en la consulta repetida | `RNF-02_V-04…_tarjeta`, `…_etiqueta-corte`, `…_ultima-fila`, `RNF-02_V-05…_total` y los dos `…_repetida` | Correcto (6 filas) y «coincide» en la comparación de las dos consultas |
| RNF-03 | el mismo texto para lo ajeno y lo inexistente | `RNF-03_V-12…_inexistente` (con `RF-02_V-12…_ajeno`) | Correcto (1 fila) |

**Consulta repetida (RNF-02):** la tarjeta del valor, la etiqueta del corte, la última fila de la tabla de la serie y el total de V-05 dicen «$58,940.88» en la primera consulta y «$58,940.88» en la repetida; coinciden entre sí y con 5.2 (fila «RNF-02 (consulta repetida)» de `ac04/recorrido.csv`, con resultado «coincide»). Las capturas completas de V-04 de las dos consultas (`RF-11_V-04…` y `RNF-02_V-04…_repetida`) son idénticas byte a byte, igual que las del total de V-05 (`RNF-02_V-05…_total` y `…_repetida`). En esas capturas también coinciden el resultado no realizado ($2,632.99 en la tarjeta de V-04 y en el total de V-05), el TWR (4.39 %) y la máxima caída (-6.68 %, del 16/09/2026 al 23/09/2026); el TWR y la máxima caída son los de P1-A que comprueba `motor/test_oraculo_5_2.py` (`test_indicadores_presentados[P1-A-4.39--6.68-…]`).

Otros pares idénticos byte a byte, porque muestran lo mismo: `RF-11_V-04…_grafica` y `RNF-02_V-04…_etiqueta-corte` (la misma vista de la gráfica); `RF-01_V-01…_rechazo` y `RF-12_V-01…_bloqueada` (la cuenta bloqueada recibe el mismo mensaje que la contraseña errónea); y las dos `fallo-inicio_*`.

## AC-07. Base de demostración con datos ficticios

Inspección hecha el 18/10/2026 por el agente de evidencia, sin conectarse a ninguna base: a las 19:30, sobre el árbol de trabajo en c39dc25, y repetida después del commit del cliente web (e636b78) para `frontend/src` y para los conteos de correos.

**1. El script de semillas, `backend/04_cargar_semillas.sql`** (SHA-256 `ec2ff6b778c89c60d8d4e3c1dd8f438cdf49a22d14652b024ead293a680ca4d0`, el mismo en e636b78; último cambio en e1b34f1, 16/10/2026, sin cambios locales). Lo genera `backend/semillas/genera_semillas.py` desde las entradas congeladas de 5.2. Tiene 8 sentencias `INSERT`, una por tabla, y ninguna en las tablas de cuenta:

| Tabla | Qué carga | ¿Dato personal? |
|---|---|---|
| `version_aviso` | El aviso de privacidad de demostración (RF-12; P-20), que pide registrarse con un correo ficticio | No |
| `fuente_datos` y `version_licencia` | Banco de México y la semilla sintética, con su licencia y su atribución (RF-31) | No |
| `instrumento` y `emision_cetes` | 7 instrumentos: 3 de demostración (DEMOACC, DEMOETF y DEMOFIB) y 4 emisiones de CETES | No |
| `carga_datos` | 2 cargas, una por fuente | No |
| `precio_cierre` | 71 precios sintéticos del 10/09 al 14/10/2026, marcados como de demostración (RF-07) | No |
| `tasa_referencia` | 32 tasas públicas del CF107 del Banco de México (RF-30) | No |

No hay `INSERT` en `usuario`, `consentimiento`, `portafolio`, `intermediario` ni `transaccion`; el encabezado del script lo dice: «No carga usuarios: las cuentas de prueba se crean con la aplicación». El único correo que aparece en él es `nombre@example.com`, como ejemplo dentro del texto del aviso. La comprobación final del script (sección 8) compara una huella md5 de los precios, las tasas y el aviso con la de las entradas y deshace todo si difieren.

**2. Los correos de prueba.** Búsqueda en `backend/` y `frontend/src`, versionados y sin versionar, con

```
git grep --untracked -nIoE "[A-Za-z0-9._%+<>{}-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" -- backend frontend/src
```

| Dominio | Apariciones | Dónde y para qué |
|---|---|---|
| example.com (en minúsculas o con mayúsculas) | 150 sin contar este índice: 144 en 21 archivos versionados, igual que a las 19:30, y 6 en esta carpeta | Versionados: pruebas, entradas de 5.2 (`usuarios.csv` solo tiene `oraculo@example.com`), el cargador, el mensaje de la API «como nombre@example.com» y el aviso de demostración. En esta carpeta: `recorrido_ac04.mjs` (5: `oraculo@example.com` y la plantilla de la cuenta B) y `ac04/recorrido.csv` (1: `recorrido-b-2108@example.com`) |
| ejemplo.test | 1 | `tests/cuentas/test_cpf01_registro_sesion.py`: un correo que la prueba espera que la API **rechace** |
| banxico.org.mx y segob.gob.mx | 8 | Páginas públicas guardadas como fuente del oráculo (`tests/oraculo/fuentes/*.html`); son el contacto de esas instituciones, no cuentas |

En `frontend/src` (56 archivos, todos versionados en e636b78 y ninguno sin versionar) no aparece ningún correo, ni de example.com ni de otro dominio: la búsqueda anterior, limitada a `frontend/src`, no da coincidencias. `pantallas/_MuestraUi.jsx`, que a las 19:30 tenía `nombre@example.com`, ya no existe. El único ejemplo de correo que ve quien usa el cliente es `nombre@example.com`, dentro del aviso de demostración que viene de la base (captura `RF-12_V-03…_sin-sesion`).

Las cuentas que llegan a una base las crea la aplicación: `oraculo@example.com` (el cargador de 5.2) y, en el recorrido de las 21:08, `recorrido-b-2108@example.com`, que quedó revocada y bloqueada (paso 10.8) con su intermediario «Casa A»; el portafolio desechable de la cuenta del oráculo se eliminó con su compra (paso 8). Las pruebas automáticas crean sus cuentas (`ana@example.com`, `beto@example.com` y otras de example.com) en un clúster temporal que se borra al terminar. Todos los nombres de portafolio e intermediario de 5.2 son ficticios («Principal», «Secundario», «Casa A» y «Casa B»).

**Resultado:** cumple en lo inspeccionado: el script solo siembra datos de referencia y de demostración, todos los correos de prueba son de example.com y `frontend/src` no tiene ninguno; los otros dominios son el correo que una prueba espera rechazado (ejemplo.test) y el contacto de dos instituciones en páginas públicas guardadas.

**Límite:** no se inspeccionó el contenido de la base de desarrollo de Ramon (puerto 5432), que ningún agente abre. Si se quiere constancia de ella, Ramon puede listar, con una consulta de solo lectura, los correos que no sean de example.com: `SELECT count(*) FROM usuario WHERE correo NOT ILIKE '%@example.com';` (se espera 0).

## Fuera de esta entrega (S-02)

Ninguno, sin traslados: no hubo recorte de los niveles 2 y 3 ni de la gráfica. Las 12 pantallas V-01 a V-12 de SRS 4.5.2 están hechas y probadas, y ningún requisito ni criterio de 3.2 pasa por S-02 a la fase de refinamiento.

El nivel 1 de recorte del plan (aplicado desde el arranque, a las 18:35) no quita criterios de 3.2 ni RNF que se juzguen el 18/10, así que no se lista aquí; está en «Pendientes».

## Pendientes

| Pendiente | Qué falta | Estado |
|---|---|---|
| R3 | Revisión del Diario Oficial de la Federación conforme a D-04, para AC-08 | Pendiente; la hace Ramon y su fecha y resultado van en SRS 3.1 |
| R4 | Comprobación a mano de las tres cifras de la nota a.1 de 5.2: costo por título de T01, BI261217 al 14/10 y TWR de P2-C | Pendiente; la hace Ramon (sección «AC-03») |
| P-65 | Confirmar con una segunda fuente la tasa a 28 días del 10/09 | Pendiente; 5.2 no se modifica (H-12) |

**Recortes de nivel 1**, que quedan para la fase de refinamiento (ninguno quita criterios de 3.2 ni RNF que se juzguen el 18/10):

- las definiciones desplegables de RNF-07 (junto a cada indicador se conservan su unidad y su fecha o periodo);
- el menú desplegable por debajo de 1280 px (la lista queda visible);
- la revisión a 320 px y los detalles del modo oscuro (los tokens oscuros sí están);
- «Mapa del sitio»;
- la entrada al historial de N-17;
- el selector N-16 en V-05 y V-06;
- el manejo propio de Esc en la gráfica (← y → de Recharts y la tabla alternativa sí están);
- el sessionStorage del portafolio activo;
- el foco y `document.title` por pantalla;
- el diálogo de revisión de V-07 y «Registrar otra».

**Hallazgos menores del corte**, también para la fase de refinamiento:

- en V-05, un portafolio inexistente muestra NoEncontrado dentro de V-05 en lugar de V-12, lo que no es coherente con N-08;
- quedan clases `.muestra-*` sin uso en `ui/datos.css`.

## Archivos de esta carpeta

| Archivo | Qué es | Quién lo genera |
|---|---|---|
| `INDICE.md` | Este índice | Agente de evidencia |
| `junit.xml` | Corrida completa con registro: 271 casos | pytest (E3) |
| `ac03_junit.xml` | Inspección de AC-03: 3 casos | pytest (E3) |
| `cpnf01_diferencias.csv`, `cpnf01_resumen.csv` y `cpnf01_versiones.csv` | CPNF-01 contra 5.2 | `referencia/test_cpnf01.py` (E3) |
| `_e3_salida.txt` | Salida de consola de E3: el avance, los totales («271 passed, 3 deselected in 53.41s» y «3 passed in 0.59s») y los dos códigos de salida, ambos 0 | E3 |
| `cpnf05.txt` | Salida de CPNF-05 (solo conteos) | Ramon (R7), con `tests/inspeccion/cpnf05_credenciales.py` |
| `recorrido_ac04.mjs` | Guion del recorrido de AC-04 | Agente de evidencia |
| `ac04/recorrido.csv` y las 33 capturas `ac04/R*.png` | Registro y capturas del recorrido | El guion, ejecutado por Ramon (R5) |
| `ac04/fallo-inicio_*.png` (2) | Capturas de diagnóstico de los dos intentos previos; no son evidencia | El guion, ejecutado por Ramon |

## Revisión de esta carpeta (E5)

Hecha el 18/10/2026, después de que Ramon generó `cpnf05.txt`, sobre los 44 archivos de la carpeta además de este índice: 8 en la raíz y 36 en `ac04/` (`recorrido.csv` y 35 PNG). No se borró ni se cambió ningún archivo de evidencia.

1. **Rutas de usuario.** La búsqueda

   ```
   git grep --untracked -nIiE "(^|[^a-z])[a-z]:[\\/]|users[\\/]|appdata" -- backend/tests/resultados/2026-10-18
   ```

   solo encuentra la línea 183 de `recorrido_ac04.mjs`, que arma la ruta de Edge con la variable de entorno `LOCALAPPDATA`, sin ninguna ruta escrita. `_e3_salida.txt`, `ac04/recorrido.csv`, `cpnf05.txt`, los dos XML y los tres CSV de CPNF-01 no tienen ninguna.
2. **Contraseñas, cookies y tokens.** La búsqueda

   ```
   git grep --untracked -cIiE "users[\\/]|contrase|cookie|token|sesion_077" -- backend/tests/resultados/2026-10-18
   ```

   da coincidencias en tres archivos, ninguna con un secreto: en `junit.xml`, nombres de pruebas como `test_cookie_origen` o `test_contrasena_se_normaliza_con_nfkc`; en `ac04/recorrido.csv`, 4 líneas con textos de la interfaz («Revisa tu correo y tu contraseña…» y «la contraseña se vació»); y en `recorrido_ac04.mjs`, 15 líneas de la petición oculta de la contraseña, la opción `--clave-archivo` y el campo `contrasena`. La clave de la cuenta B es aleatoria (`crypto.randomBytes`) y solo vive en memoria.
3. **Correos.** Los únicos son de example.com: `oraculo@example.com` y la plantilla `recorrido-b-HHMM@example.com` en `recorrido_ac04.mjs`, y `recorrido-b-2108@example.com` en `ac04/recorrido.csv`. Ningún correo real.
4. **Capturas.** Se revisaron con Read las 35 (las 33 de evidencia y las 2 de diagnóstico). Solo muestran `oraculo@example.com`, `recorrido-b-2108@example.com` y, en el aviso de demostración, `nombre@example.com`; los campos de contraseña están vacíos o enmascarados con puntos (en `RF-12_V-02…_rechazo`, la clave aleatoria de la cuenta B); no se ven la barra de direcciones ni rutas de archivos, y la única dirección web que aparece es la del Banco de México, como fuente. Los PNG no llevan metadatos de texto: solo tienen los bloques IHDR, IDAT e IEND.
5. **Otros datos.** `junit.xml` y `ac03_junit.xml` registran el nombre del equipo (`hostname="MSI"`) y la zona horaria (−07:00), como los genera pytest; no son rutas, contraseñas ni correos. `cpnf05.txt` está en UTF-8 con BOM y fin de línea CRLF.

**Resultado:** ningún archivo de esta carpeta tiene rutas de usuario, contraseñas ni correos reales; `_e3_salida.txt` y `ac04/recorrido.csv` tampoco.
