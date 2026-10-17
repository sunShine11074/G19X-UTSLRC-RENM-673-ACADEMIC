"""Criterios de aceptación de 3.2 que cubre el motor, con `MercadoEnMemoria` inyectado (§8.2 del diseño).

Cubren CPF-08, CPF-09, CPF-10 crit. 1 y 2 y CPF-26b crit. 1 y 2, que solo verifica el motor
(§8.3), y la parte de cálculo de RF-05, RF-06, RF-26a y RF-28.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import count

import pytest

from app import motor
from app.motor import Cierre, Colocacion, Historial, Instrumento, Intervalo, MercadoEnMemoria, Transaccion

pytestmark = pytest.mark.motor

D = Decimal
INICIO = date(2026, 3, 1)


def dia(n: int) -> date:
    """«Día n» de los criterios: el día 1 es INICIO."""
    return INICIO + timedelta(days=n - 1)


ACCION = Instrumento(id=1, clave="DEMOX", clase_activo="accion")
EMISION = Instrumento(id=3, clave="BI260331", clase_activo="cetes", vencimiento=dia(31), valor_nominal=D("10.00"))
CATALOGO = {i.id: i for i in (ACCION, EMISION)}

_ids = count(1)


def tx(
    tipo: str,
    n: int,
    cantidad: int,
    precio: str,
    importe: str = "0.00",
    *,
    intermediario: int = 1,
    instrumento: Instrumento = ACCION,
    portafolio: int = 1,
    candidata: bool = False,
) -> Transaccion:
    return Transaccion(
        id=None if candidata else next(_ids),
        portafolio_id=portafolio,
        intermediario_id=intermediario,
        instrumento_id=instrumento.id,
        tipo=tipo,  # type: ignore[arg-type]
        fecha_concertacion=dia(n),
        cantidad=cantidad,
        precio=D(precio),
        importe_comisiones=D(importe),
    )


def historial(*transacciones: Transaccion, portafolio: int = 1) -> Historial:
    return Historial(portafolio, transacciones, {t.instrumento_id: CATALOGO[t.instrumento_id] for t in transacciones})


def mercado(cierres: dict[int, str] | None = None, colocaciones: list[Colocacion] | None = None) -> MercadoEnMemoria:
    """Cierres de ACCION por número de día y colocaciones dadas."""
    return MercadoEnMemoria(
        [Cierre(ACCION.id, dia(n), D(p), 7) for n, p in (cierres or {}).items()],
        colocaciones or [],
    )


def colocacion(plazo: int, fecha: date, tasa: str, efectivo: int | None = None) -> Colocacion:
    return Colocacion(plazo, fecha, D(tasa), efectivo if efectivo is not None else plazo, 9)


# Tasas ilustrativas de RF-26b crit. 1, colocadas antes del día 1.
CURVA = [colocacion(28, dia(-5), "7.00000"), colocacion(91, dia(-5), "7.20000")]


def instrumento_en(corte: motor.Corte, instrumento: Instrumento) -> motor.PosicionInstrumento:
    return next(p for p in corte.instrumentos if p.instrumento_id == instrumento.id)


# --- RF-05 --------------------------------------------------------------------------


def test_rf05_costo_e_ingreso_por_titulo() -> None:
    compra = motor.importes(tx("compra", 1, 100, "50.00", "14.50"))
    assert compra.monto == D("5000.00")
    assert compra.costo_por_titulo == D("50.145")
    assert compra.ingreso_por_titulo is None
    assert compra.aportacion == D("5014.50")
    assert compra.retiro == 0
    assert motor.presentar_por_titulo(compra.costo_por_titulo) == "50.145"
    assert motor.presentar_importe(compra.aportacion) == "5014.50"

    venta = motor.importes(tx("venta", 2, 100, "55.00", "15.95"))
    assert venta.ingreso_por_titulo == D("54.8405")
    assert venta.costo_por_titulo is None
    assert venta.retiro == D("5484.05")
    assert venta.aportacion == 0
    assert motor.presentar_por_titulo(venta.ingreso_por_titulo) == "54.8405"
    assert motor.presentar_importe(venta.retiro) == "5484.05"


# --- RF-06 --------------------------------------------------------------------------


def test_rf06_posicion_suma_los_saldos_por_intermediario() -> None:
    m = mercado({1: "50.00"})
    compras = (tx("compra", 1, 100, "50.00", intermediario=1), tx("compra", 1, 50, "50.00", intermediario=2))
    assert instrumento_en(motor.posiciones(historial(*compras), m, dia(1)), ACCION).titulos == 150
    corte = motor.posiciones(historial(*compras, tx("venta", 2, 30, "50.00", intermediario=1)), m, dia(2))
    assert instrumento_en(corte, ACCION).titulos == 120
    assert {p.intermediario_id: p.titulos for p in corte.pares} == {1: 70, 2: 50}


def test_rf06_cuenta_lo_fechado_el_dia_de_corte() -> None:
    h = historial(tx("compra", 5, 100, "50.00"))
    m = mercado({1: "50.00"})
    assert instrumento_en(motor.posiciones(h, m, dia(5)), ACCION).titulos == 100
    al_4 = motor.posiciones(h, m, dia(4))
    assert instrumento_en(al_4, ACCION).titulos == 0
    assert al_4.pares[0].tiene_transacciones is False
    assert al_4.sin_transacciones is True
    assert al_4.valor == 0


def test_rf06_otro_portafolio_no_cuenta() -> None:
    m = mercado({1: "50.00"})
    propio = historial(tx("compra", 1, 100, "50.00", portafolio=1), portafolio=1)
    ajeno = tx("compra", 1, 500, "50.00", portafolio=2)
    assert instrumento_en(motor.posiciones(propio, m, dia(1)), ACCION).titulos == 100
    with pytest.raises(motor.HistorialInvalido):
        Historial(1, (*propio.transacciones, ajeno), propio.instrumentos)


# --- RF-08 --------------------------------------------------------------------------


def test_rf08_crit1_costo_promedio_y_venta_parcial() -> None:
    m = mercado({1: "58.00"})
    compras = (tx("compra", 1, 100, "50.00", "14.50"), tx("compra", 2, 100, "60.00", "18.56"))
    corte = motor.posiciones(historial(*compras), m, dia(3))
    assert corte.resultado_no_realizado == D("566.94")
    assert corte.pares[0].costo_unitario == D("55.1653")
    # Tras vender 50, a cualquier precio, el costo unitario no cambia (P-10).
    corte = motor.posiciones(historial(*compras, tx("venta", 3, 50, "71.30", "3.10")), m, dia(3))
    assert corte.resultado_no_realizado == D("425.205")
    assert motor.presentar_importe(corte.resultado_no_realizado) == "425.21"
    assert corte.pares[0].costo_unitario == D("55.1653")


def test_rf08_crit2_costo_por_intermediario() -> None:
    m = mercado({1: "58.00"})
    h = historial(
        tx("compra", 1, 100, "50.00", "14.50", intermediario=1),
        tx("compra", 2, 100, "60.00", "18.56", intermediario=2),
        tx("venta", 3, 50, "58.00", intermediario=1),
    )
    corte = motor.posiciones(h, m, dia(3))
    assert corte.resultado_no_realizado == D("174.19")
    assert motor.presentar_importe(corte.resultado_no_realizado) == "174.19"


def test_rf08_crit3_compras_antes_que_ventas() -> None:
    m = mercado({1: "58.00"})
    # La venta va primero en el historial: el orden de captura no importa.
    h = historial(
        tx("compra", 1, 100, "50.00", "14.50"),
        tx("venta", 2, 100, "58.00"),
        tx("compra", 2, 100, "60.00", "18.56"),
    )
    corte = motor.posiciones(h, m, dia(2))
    assert corte.resultado_no_realizado == D("283.47")
    assert corte.resultado_no_realizado != D("-218.56")


def test_rf08_crit4_sin_cierre_rige_el_ultimo_anterior() -> None:
    m = mercado({1: "58.00", 3: "59.00"})
    h = historial(tx("compra", 1, 10, "58.00"))
    usado = motor.cierre_vigente(m, ACCION, dia(5))
    assert usado == motor.PrecioUsado(ACCION.id, dia(5), dia(3), D("59.00"), 7, True)
    assert motor.cierre_vigente(m, ACCION, dia(3)).sin_cierre_ese_dia is False
    assert motor.cierre_vigente(m, ACCION, dia(0)) is None
    par = motor.posiciones(h, m, dia(5)).pares[0]
    assert (par.precio, par.fecha_precio, par.fuente_id, par.valor) == (D("59.00"), dia(3), 7, D("590.00"))


def test_rf08_posicion_en_cero_conserva_el_cierre_y_vale_cero() -> None:
    m = mercado({1: "58.00"})
    h = historial(tx("compra", 1, 10, "58.00"), tx("venta", 2, 10, "60.00"))
    par = motor.posiciones(h, m, dia(2)).pares[0]
    assert (par.titulos, par.costo_unitario, par.valor, par.precio) == (0, 0, 0, D("58.00"))
    assert motor.posiciones(h, m, dia(2)).fuentes_usadas == frozenset()


def test_rd24_sin_cierre_con_titulos_no_se_puede_valuar() -> None:
    h = historial(tx("compra", 5, 10, "58.00"))
    with pytest.raises(motor.CifraNoCalculable) as error:
        motor.posiciones(h, mercado({}), dia(5))
    assert (error.value.instrumento_id, error.value.fecha, error.value.clave) == (ACCION.id, dia(5), "DEMOX")


# --- RF-09 --------------------------------------------------------------------------


def test_rf09_crit1_twr_sin_flujos() -> None:
    m = mercado({1: "100.00", 31: "101.00"})
    h = historial(tx("compra", 1, 100, "100.00"))
    ind = motor.indicadores(h, m, dia(2), dia(31))
    assert (ind.valor_base, ind.valor_fin, ind.dias, ind.fecha_base) == (D("10000.00"), D("10100.00"), 30, dia(1))
    assert ind.twr == D("0.01")
    assert motor.presentar_por_ciento(ind.twr) == "1.00"
    assert len(ind.serie) == 31  # un punto por día natural, con la base


def test_rf09_crit2_aportaciones_y_retiros() -> None:
    m = mercado({1: "50.00", 2: "50.00", 3: "55.00"})
    h = historial(tx("compra", 2, 100, "50.00", "14.50"), tx("venta", 3, 100, "55.00", "15.95"))
    serie = {d.fecha: d for d in motor.indicadores(h, m, dia(2), dia(3)).serie}
    assert serie[dia(2)].aportaciones == D("5014.50")
    assert serie[dia(3)].retiros_ventas == D("5484.05")
    assert serie[dia(3)].retiros == D("5484.05")
    # r(3) = (V + R) / (V(t−1) + A) − 1 = 5484.05 / 5000 − 1
    assert serie[dia(3)].r == D("5484.05") / D("5000.00") - 1


def test_rf09_crit2_la_baja_de_valor_por_un_retiro_no_reduce_el_twr() -> None:
    m = mercado({1: "100.00"})
    h = historial(tx("compra", 1, 100, "100.00"), tx("venta", 3, 50, "100.00"))
    ind = motor.indicadores(h, m, dia(2), dia(5))
    assert ind.serie[2].valor == D("5000.00")  # el valor baja a la mitad
    assert ind.twr == 0
    assert ind.maxima_caida == 0  # los flujos no crean caídas (RF-10 crit. 2)


def test_rf09_crit2_un_vencimiento_es_un_retiro() -> None:
    m = mercado(colocaciones=CURVA)
    h = historial(tx("compra", 1, 1000, "9.9400000", instrumento=EMISION))
    ind = motor.indicadores(h, m, dia(2), dia(31))
    ultimo = ind.serie[-1]
    assert (ultimo.fecha, ultimo.valor, ultimo.retiros_vencimientos) == (dia(31), 0, D("10000.00"))
    assert ultimo.r > 0
    assert ind.twr > 0


def test_rf09_denominador_cero_es_factor_uno() -> None:
    assert motor.rendimiento_diario(D(0), D(0), D(0), D(0)) == 0
    m = mercado({1: "100.00", 5: "101.00"})
    h = historial(tx("compra", 5, 10, "100.00"))
    ind = motor.indicadores(h, m, dia(2), dia(5))
    assert [d.r for d in ind.serie] == [None, 0, 0, 0, D("0.01")]
    assert [d.indice for d in ind.serie[:4]] == [1, 1, 1, 1]
    assert ind.twr == D("0.01")


def test_d22_sin_transacciones_devuelve_ceros() -> None:
    ind = motor.indicadores(Historial(1, (), {}), mercado(), dia(2), dia(4))
    assert (ind.twr, ind.maxima_caida, ind.valor_fin, ind.fecha_pico) == (0, 0, 0, None)
    assert ind.corte_fin.sin_transacciones is True
    assert [d.valor for d in ind.serie] == [0, 0, 0, 0]


# --- RF-10 --------------------------------------------------------------------------


def _indices(*valores: str) -> list[tuple[date, Decimal]]:
    return [(dia(n + 2), D(v)) for n, v in enumerate(valores)]


def test_rf10_crit1_maxima_caida_con_recuperacion() -> None:
    resultado = motor.caida_maxima(dia(1), _indices("1.10", "0.99", "1.05", "1.12", "1.064"))
    assert resultado == motor.CaidaMaxima(D("-0.1"), dia(2), dia(3))
    assert motor.presentar_por_ciento(resultado.maxima_caida) == "-10.00"


def test_rf10_crit2_serie_que_no_baja() -> None:
    resultado = motor.caida_maxima(dia(1), _indices("1.00", "1.01", "1.01", "1.02"))
    assert resultado == motor.CaidaMaxima(D(0), None, None)
    assert motor.presentar_por_ciento(resultado.maxima_caida) == "0.00"


def test_rf10_empate_conserva_el_pico_mas_antiguo() -> None:
    resultado = motor.caida_maxima(dia(1), _indices("1.10", "1.10", "1.00"))
    assert (resultado.fecha_pico, resultado.fecha_valle) == (dia(2), dia(4))


def test_rf10_el_indice_inicial_es_el_primer_maximo() -> None:
    resultado = motor.caida_maxima(dia(1), _indices("0.98", "0.97", "0.99"))
    assert (resultado.fecha_pico, resultado.fecha_valle) == (dia(1), dia(3))
    assert resultado.maxima_caida == D("-0.03")


def test_rf10_se_mide_sobre_el_indice_del_twr() -> None:
    m = mercado({1: "100.00", 2: "110.00", 3: "99.00", 4: "105.00", 5: "112.00", 6: "106.40"})
    # Índice 1 → 1.10 → 0.99 → 1.05 → 1.12 → 1.064; el día 3 se vende la mitad al cierre y el
    # valor cae más que el índice, pero la caída se mide sobre el índice.
    h = historial(tx("compra", 1, 10, "100.00"), tx("venta", 3, 5, "99.00"))
    ind = motor.indicadores(h, m, dia(2), dia(6))
    assert [motor.presentar(d.indice, 6) for d in ind.serie] == ["1.000000", "1.100000", "0.990000", "1.050000", "1.120000", "1.064000"]
    assert ind.serie[2].valor / ind.serie[1].valor - 1 < D("-0.5")
    assert motor.presentar_por_ciento(ind.maxima_caida) == "-10.00"
    assert (ind.fecha_pico, ind.fecha_valle) == (dia(2), dia(3))


# --- RF-26a -------------------------------------------------------------------------


def test_rf26a_crit1_liquidacion_al_vencimiento() -> None:
    m = mercado(colocaciones=CURVA)
    h = historial(
        tx("compra", 1, 1000, "9.9400000", instrumento=EMISION, intermediario=1),
        tx("compra", 1, 500, "9.9400000", instrumento=EMISION, intermediario=2),
    )
    assert instrumento_en(motor.posiciones(h, m, dia(30)), EMISION).titulos == 1500
    al_vencimiento = motor.posiciones(h, m, dia(31))
    posicion = instrumento_en(al_vencimiento, EMISION)
    assert (posicion.titulos, posicion.vencida, posicion.valor, posicion.costo_total, posicion.precio) == (0, True, 0, 0, None)
    assert all(p.titulos == 0 and p.precio is None for p in al_vencimiento.pares)
    serie = {d.fecha: d for d in motor.indicadores(h, m, dia(2), dia(35)).serie}
    assert serie[dia(31)].retiros_vencimientos == D("15000.00")
    assert motor.presentar_importe(serie[dia(31)].retiros) == "15000.00"
    assert all(serie[dia(n)].retiros == 0 for n in range(32, 36))
    assert instrumento_en(motor.posiciones(h, m, dia(40)), EMISION).titulos == 0


def test_rf26a_crit1_tras_una_venta_parcial_solo_se_liquida_el_resto() -> None:
    m = mercado(colocaciones=CURVA)
    h = historial(
        tx("compra", 1, 1000, "9.9400000", instrumento=EMISION, intermediario=1),
        tx("compra", 1, 500, "9.9400000", instrumento=EMISION, intermediario=2),
        tx("venta", 10, 300, "9.9600000", instrumento=EMISION, intermediario=1),
    )
    serie = {d.fecha: d for d in motor.indicadores(h, m, dia(2), dia(31)).serie}
    assert serie[dia(31)].retiros_vencimientos == D("12000.00")


@pytest.mark.parametrize("n", [31, 32])
def test_rf26a_crit2_transaccion_en_el_vencimiento_o_despues(n: int) -> None:
    with pytest.raises(motor.HistorialInvalido):
        historial(tx("compra", n, 10, "10.0000000", instrumento=EMISION))


def test_rf26a_crit3_el_motor_no_crea_transacciones() -> None:
    m = mercado(colocaciones=CURVA)
    h = historial(tx("compra", 1, 1000, "9.9400000", instrumento=EMISION))
    antes = h.transacciones
    motor.indicadores(h, m, dia(2), dia(35))
    motor.posiciones(h, m, dia(35))
    assert h.transacciones == antes and len(h.transacciones) == 1


# --- RF-26b -------------------------------------------------------------------------

VENCIMIENTO = date(2026, 6, 30)
EMISION_B = Instrumento(id=4, clave="BI260630", clase_activo="cetes", vencimiento=VENCIMIENTO, valor_nominal=D("10.00"))


def _valuar(d: int, colocaciones: list[Colocacion] = CURVA) -> motor.ValuacionCetes:
    return motor.valuar_cetes(mercado(colocaciones=colocaciones), EMISION_B, VENCIMIENTO - timedelta(days=d))


def test_rf26b_crit1_interpolacion_por_plazo_efectivo() -> None:
    v = _valuar(50)
    assert v.caso == motor.CasoTasa.INTERPOLACION
    assert (v.inf.plazo_efectivo, v.sup.plazo_efectivo, v.d) == (28, 91, 50)
    assert format(v.r, "f").startswith("7.0698412698")
    assert v.r == D("7.069841269841269841269841270")
    assert v.p == D("9.9027626")
    assert motor.presentar(v.p, 7) == "9.9027626"
    assert motor.presentar(v.r, 5) == "7.06984"  # D-40


def test_rf26b_crit2_tasa_del_extremo() -> None:
    corto = _valuar(10)
    assert (corto.caso, corto.r, corto.p) == (motor.CasoTasa.EXTREMO_INFERIOR, D("7.00000"), D("9.9805933"))
    assert corto.inf == corto.sup
    largo = _valuar(100)
    assert (largo.caso, largo.r, largo.p) == (motor.CasoTasa.EXTREMO_SUPERIOR, D("7.20000"), D("9.8039216"))


def test_rf26b_nodo_exacto() -> None:
    v = _valuar(28)
    assert (v.caso, v.r, v.inf, v.sup) == (motor.CasoTasa.NODO, D("7.00000"), v.inf, v.inf)


def test_rf26b_crit3_una_colocacion_posterior_no_rige() -> None:
    fecha = VENCIMIENTO - timedelta(days=50)
    posterior = colocacion(28, fecha + timedelta(days=1), "8.00000")
    m = mercado(colocaciones=[*CURVA, posterior])
    assert motor.valuar_cetes(m, EMISION_B, fecha) == _valuar(50)
    al_dia_siguiente = motor.valuar_cetes(m, EMISION_B, fecha + timedelta(days=1))
    assert al_dia_siguiente.inf.fecha_colocacion == posterior.fecha_colocacion
    assert al_dia_siguiente.inf.tasa == D("8.00000")


def test_rf26b_valor_es_titulos_por_p() -> None:
    m = mercado(colocaciones=CURVA)
    h = historial(tx("compra", 1, 1000, "9.9000000", instrumento=EMISION))
    corte = motor.posiciones(h, m, dia(2))
    v = motor.valuar_cetes(m, EMISION, dia(2))
    assert corte.valor == 1000 * v.p
    assert corte.pares[0].cetes == v
    assert (corte.pares[0].precio, corte.pares[0].fecha_precio, corte.pares[0].fuente_id) == (v.p, dia(2), 9)


def test_d38_empate_de_plazos_efectivos() -> None:
    fecha = VENCIMIENTO - timedelta(days=175)
    reciente = [
        colocacion(182, fecha - timedelta(days=14), "7.50000", 175),
        colocacion(364, fecha - timedelta(days=7), "7.80000", 175),
    ]
    v = _valuar(175, reciente)
    assert (v.caso, v.inf.plazo_nominal, v.r) == (motor.CasoTasa.NODO, 364, D("7.80000"))
    misma_fecha = [
        colocacion(364, fecha - timedelta(days=7), "7.80000", 175),
        colocacion(182, fecha - timedelta(days=7), "7.50000", 175),
    ]
    assert _valuar(175, misma_fecha).inf.plazo_nominal == 182


def test_rf26b_sin_colocaciones_no_se_puede_valuar() -> None:
    with pytest.raises(motor.CifraNoCalculable):
        _valuar(50, [])


@pytest.mark.parametrize("d", [0, -1])
def test_rf26b_emision_liquidada_no_se_valua(d: int) -> None:
    with pytest.raises(ValueError):
        _valuar(d)


# --- RF-28 --------------------------------------------------------------------------


def test_rf28_crit1_saldo_por_intermediario() -> None:
    h = historial(tx("compra", 1, 100, "50.00", intermediario=1), tx("compra", 1, 50, "50.00", intermediario=2))
    rechazo = motor.primer_saldo_negativo(h, tx("venta", 2, 120, "50.00", intermediario=1, candidata=True))
    assert rechazo == motor.SaldoNegativo(dia(2), -20)
    assert motor.primer_saldo_negativo(h, tx("venta", 2, 100, "50.00", intermediario=1, candidata=True)) is None


def test_rf28_crit2_en_cualquier_fecha() -> None:
    h = historial(tx("compra", 1, 100, "50.00"), tx("venta", 10, 80, "50.00"))
    rechazo = motor.primer_saldo_negativo(h, tx("venta", 5, 50, "50.00", candidata=True))
    assert rechazo == motor.SaldoNegativo(dia(10), -30)


def test_rf28_crit3_otro_portafolio_no_cubre_y_no_se_registra_nada() -> None:
    propio = historial(tx("compra", 1, 100, "50.00", portafolio=1), portafolio=1)
    historial(tx("compra", 1, 500, "50.00", portafolio=2), portafolio=2)  # el otro portafolio existe
    antes = propio.transacciones
    rechazo = motor.primer_saldo_negativo(propio, tx("venta", 2, 120, "50.00", portafolio=1, candidata=True))
    assert rechazo == motor.SaldoNegativo(dia(2), -20)
    assert propio.transacciones == antes
    with pytest.raises(ValueError):
        motor.primer_saldo_negativo(propio, tx("venta", 2, 10, "50.00", portafolio=2, candidata=True))


def test_rf28_el_historial_rechaza_un_saldo_negativo() -> None:
    with pytest.raises(motor.HistorialInvalido):
        historial(tx("compra", 1, 100, "50.00"), tx("venta", 2, 120, "50.00"))


# --- RF-09 crit. 3 y RD-07: periodos y cortes -----------------------------------------

INTERVALO = Intervalo(date(2026, 9, 10), date(2026, 10, 14))


def test_validar_periodo() -> None:
    motor.validar_periodo(date(2026, 9, 11), date(2026, 10, 14), INTERVALO)
    motor.validar_periodo(date(2026, 9, 11), date(2026, 9, 11), INTERVALO)  # un solo día es válido
    casos = [
        (date(2026, 10, 14), date(2026, 9, 11), "periodo_invertido"),
        (date(2026, 9, 10), date(2026, 10, 14), "periodo_fuera_de_intervalo"),  # la base quedaría fuera
        (date(2026, 9, 11), date(2026, 10, 15), "periodo_fuera_de_intervalo"),
        (date(2026, 10, 20), date(2026, 9, 1), "periodo_invertido"),  # invertido se informa primero
    ]
    for inicio, fin, codigo in casos:
        with pytest.raises(motor.PeriodoInvalido) as error:
            motor.validar_periodo(inicio, fin, INTERVALO)
        assert (error.value.codigo, error.value.regla) == (codigo, "RF-09")


def test_validar_corte() -> None:
    motor.validar_corte(date(2026, 9, 10), INTERVALO)
    motor.validar_corte(date(2026, 10, 14), INTERVALO)
    for fecha in (date(2026, 9, 9), date(2026, 10, 15)):
        with pytest.raises(motor.PeriodoInvalido) as error:
            motor.validar_corte(fecha, INTERVALO)
        assert (error.value.codigo, error.value.regla, error.value.intervalo) == ("fecha_fuera_de_intervalo", "RD-07", INTERVALO)


# --- Defensas del motor (RD-12; RD-04; RD-19) ----------------------------------------


@pytest.mark.parametrize(
    ("campo", "valor", "error"),
    [
        ("precio", 50.0, TypeError),
        ("precio", 50, TypeError),
        ("importe_comisiones", 0.0, TypeError),
        ("cantidad", 1.5, TypeError),
        ("cantidad", True, TypeError),
        ("cantidad", 0, ValueError),
        ("precio", D("NaN"), ValueError),
        ("precio", D("0"), ValueError),
        ("importe_comisiones", D("-0.01"), ValueError),
        ("tipo", "dividendo", ValueError),
        ("fecha_concertacion", datetime(2026, 3, 1, 12, 0), TypeError),
    ],
)
def test_entradas_rechazan_float_y_valores_invalidos(campo: str, valor: object, error: type[Exception]) -> None:
    datos = dict(
        id=1, portafolio_id=1, intermediario_id=1, instrumento_id=1, tipo="compra",
        fecha_concertacion=dia(1), cantidad=10, precio=D("1.00"), importe_comisiones=D("0.00"),
    )
    datos[campo] = valor
    with pytest.raises(error):
        Transaccion(**datos)  # type: ignore[arg-type]


def test_otras_entradas_rechazan_float() -> None:
    with pytest.raises(TypeError):
        Cierre(1, dia(1), 58.0, 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Colocacion(28, dia(1), 7.0, 28, 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Instrumento(5, "BI260101", "cetes", dia(1), 10.0)  # type: ignore[arg-type]
    sin_vencimiento = Instrumento(5, "BIX", "cetes")
    with pytest.raises(motor.HistorialInvalido):
        Historial(1, (tx("compra", 1, 10, "1.00", instrumento=sin_vencimiento),), {5: sin_vencimiento})
    con_vencimiento = Instrumento(6, "DEMOZ", "accion", vencimiento=dia(30))
    with pytest.raises(motor.HistorialInvalido):
        Historial(1, (tx("compra", 1, 10, "1.00", instrumento=con_vencimiento),), {6: con_vencimiento})


def test_mercado_rechaza_cierres_duplicados_y_cierres_de_cetes() -> None:
    with pytest.raises(ValueError):
        MercadoEnMemoria([Cierre(1, dia(1), D("1.00"), 1), Cierre(1, dia(1), D("2.00"), 2)], [])
    con_cierre = MercadoEnMemoria([Cierre(EMISION.id, dia(1), D("9.90"), 1)], CURVA)
    with pytest.raises(ValueError):
        motor.cierre_vigente(con_cierre, EMISION, dia(2))
    with pytest.raises(ValueError):
        motor.posiciones(historial(tx("compra", 1, 10, "9.9000000", instrumento=EMISION)), con_cierre, dia(2))
