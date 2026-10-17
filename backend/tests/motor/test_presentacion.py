"""Presentación de cifras: la única función de redondeo (RD-13; RD-16; D-14; D-39; §5.8 del diseño)."""

from datetime import date
from decimal import ROUND_DOWN, Decimal, Inexact, getcontext, localcontext

import pytest

from app import motor
from app.motor import Cierre, Historial, Instrumento, MercadoEnMemoria, Transaccion

pytestmark = pytest.mark.motor

D = Decimal


def test_mitad_alejandose_de_cero() -> None:
    assert motor.presentar(D("-0.125"), 2) == "-0.13"
    assert motor.presentar(D("0.125"), 2) == "0.13"
    assert motor.presentar(D("2.5"), 0) == "3"
    assert motor.presentar(D("-2.5"), 0) == "-3"
    assert motor.presentar_importe(D("425.205")) == "425.21"
    assert motor.presentar(D("9.95162404975812024879060124"), 7) == "9.9516240"


@pytest.mark.parametrize("valor", ["-0.001", "-0", "0", "-0.004999", "0E-28", "-0E+3"])
def test_cero_sin_signo(valor: str) -> None:
    assert motor.presentar_importe(D(valor)) == "0.00"
    assert motor.presentar_por_ciento(D(valor).scaleb(-2)) == "0.00"


def test_por_titulo_sin_ceros_finales_y_al_menos_dos_decimales() -> None:
    assert motor.presentar_por_titulo(D("50.145")) == "50.145"
    assert motor.presentar_por_titulo(D("54.8405")) == "54.8405"
    assert motor.presentar_por_titulo(D("2882.33") / 60) == "48.0388333"
    assert motor.presentar_por_titulo(D("103.9004666666666666666666667")) == "103.9004667"
    assert motor.presentar_por_titulo(D("50")) == "50.00"
    assert motor.presentar_por_titulo(D("50.10000000")) == "50.10"
    assert motor.presentar_por_titulo(D("9.95162400")) == "9.951624"
    assert motor.presentar_por_titulo(D("0E-7")) == "0.00"


def test_sin_notacion_exponencial_ni_separadores() -> None:
    assert motor.presentar_importe(D("0E-7")) == "0.00"
    assert motor.presentar_importe(D("1E+3")) == "1000.00"
    assert motor.presentar_importe(D("1234567.891")) == "1234567.89"
    assert motor.presentar(D("1E-9"), 7) == "0.0000000"
    assert motor.presentar(D("7.069841269841269841269841270"), 5) == "7.06984"


def test_por_ciento() -> None:
    assert motor.presentar_por_ciento(D("-0.0668047723072569401849512391")) == "-6.68"
    assert motor.presentar_por_ciento(D("0.043928084061150292021526333")) == "4.39"
    assert motor.presentar_por_ciento(D("0.01")) == "1.00"
    assert motor.presentar_por_ciento(D("-0.1")) == "-10.00"
    assert motor.presentar_por_ciento(D("0.000049999")) == "0.00"
    assert motor.presentar_por_ciento(D("0.00005")) == "0.01"


def test_solo_presenta_decimal_finito() -> None:
    with pytest.raises(TypeError):
        motor.presentar(1.5, 2)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        motor.presentar_importe(10)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        motor.presentar_importe(D("Infinity"))
    with pytest.raises(ValueError):
        motor.presentar(D("1"), -1)


# --- El contexto del hilo no altera ningún resultado (RD-12; 4.2 «Aritmética decimal») ---

ACCION = Instrumento(1, "DEMOX", "accion")
EMISION = Instrumento(2, "BI261008", "cetes", date(2026, 10, 8), D("10.00"))


def _calcular() -> tuple[object, ...]:
    h = Historial(
        1,
        (
            Transaccion(1, 1, 1, 1, "compra", date(2026, 9, 10), 150, D("103.60"), D("45.07")),
            Transaccion(2, 1, 1, 2, "compra", date(2026, 9, 10), 1500, D("9.9516240"), D("0.00")),
            Transaccion(3, 1, 1, 1, "venta", date(2026, 9, 14), 7, D("99.97"), D("2.03")),
        ),
        {1: ACCION, 2: EMISION},
    )
    m = MercadoEnMemoria(
        [Cierre(1, date(2026, 9, d), D(p), 1) for d, p in ((10, "100.20"), (11, "101.85"), (14, "97.33"))],
        [motor.Colocacion(28, date(2026, 9, 10), D("6.25000"), 28, 2), motor.Colocacion(91, date(2026, 9, 10), D("6.56000"), 91, 2)],
    )
    ind = motor.indicadores(h, m, date(2026, 9, 11), date(2026, 9, 20))
    return (
        motor.importes(h.transacciones[0]),
        ind,
        motor.posiciones(h, m, date(2026, 9, 13)),
        motor.valuar_cetes(m, EMISION, date(2026, 9, 17)),
        motor.presentar_por_titulo(motor.importes(h.transacciones[0]).costo_por_titulo),
        motor.presentar_por_ciento(ind.twr),
        motor.presentar_importe(D("425.205")),
        motor.presentar(D("-0.125"), 2),
    )


def test_un_contexto_global_cambiado_no_altera_ningun_resultado() -> None:
    referencia = _calcular()
    with localcontext() as contexto:
        contexto.prec = 5
        contexto.rounding = ROUND_DOWN
        contexto.traps[Inexact] = True  # si el motor usara este contexto, fallaría
        cambiado = _calcular()
        # El motor no modifica el contexto de quien lo llama.
        assert getcontext().prec == 5
        assert getcontext().rounding == ROUND_DOWN
    assert cambiado == referencia


def test_el_contexto_del_motor_es_de_28_digitos_y_mitad_alejandose_de_cero() -> None:
    assert motor.CONTEXTO.prec == 28
    assert motor.CONTEXTO.rounding == "ROUND_HALF_UP"
    importes = motor.importes(Transaccion(None, 1, 1, 1, "compra", date(2026, 9, 14), 150, D("103.60"), D("45.07")))
    # 15585.07 / 150 con 28 dígitos, sin redondear a 7 decimales.
    assert importes.costo_por_titulo == D("103.9004666666666666666666667")
