"""CPNF-01, nivel 1: el motor puro contra el conjunto de referencia de 5.2 (RNF-01; §8.2 del diseño).

Arma los historiales y el mercado desde `entradas/` (conftest) y compara cada renglón de los
siete archivos de `esperados/` con las tolerancias de §5.10. Además comprueba los rechazos
N1 a N4, N7 y N8, el caso positivo C1 y que cada cifra sea idéntica en todas las vistas (RNF-02).
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app import motor
from tests.comparacion_5_2 import (
    ARCHIVOS_ESPERADOS,
    Comparador,
    comparar_5_2,
    fecha_iso,
    leer_csv,
)

pytestmark = pytest.mark.motor

# Correspondencia de la columna `regla` de rechazos_rf28.csv con el código del motor (§4.4).
CODIGO_POR_REGLA = {
    "criterio 3 de RF-09: fecha final anterior a la inicial": "periodo_invertido",
    "criterio 3 de RF-09: fechas fuera de las semillas": "periodo_fuera_de_intervalo",
}


def _rechazos() -> dict[str, dict[str, str]]:
    return {fila["id"]: fila for fila in leer_csv("rechazos_rf28", "")}


def _candidata(datos, fila: dict[str, str]) -> motor.Transaccion:
    return motor.Transaccion(
        id=None,
        portafolio_id=datos.portafolios[fila["portafolio_nombre"]],
        intermediario_id=datos.ids_intermediario[fila["intermediario_nombre"]],
        instrumento_id=datos.instrumentos[fila["instrumento_clave"]].id,
        tipo=fila["tipo"],
        fecha_concertacion=fecha_iso(fila["fecha_concertacion"]),
        cantidad=int(fila["cantidad"]),
        precio=Decimal(fila["precio"]),
        importe_comisiones=Decimal(fila["importe_comisiones"]),
    )


def test_cpnf01_nivel_1_siete_archivos_dentro_de_tolerancia(datos_5_2, tmp_path: Path) -> None:
    comparador = comparar_5_2(
        datos_5_2.historiales, datos_5_2.mercado, datos_5_2.claves, datos_5_2.intermediarios, datos_5_2.refs
    )
    comparador.escribir(tmp_path)
    assert (tmp_path / "cpnf01_diferencias.csv").is_file()
    assert (tmp_path / "cpnf01_resumen.csv").is_file()

    # Cada renglón de cada archivo de esperados/ se comparó.
    por_archivo: dict[str, set[str]] = {}
    for d in comparador.diferencias:
        por_archivo.setdefault(d.archivo, set()).add(d.llave)
    for archivo in ARCHIVOS_ESPERADOS:
        assert len(por_archivo.get(archivo, set())) == len(leer_csv(archivo)), archivo

    comparador.verificar()


def test_igualdad_exacta_en_fechas_caso_titulos_y_p(datos_5_2) -> None:
    """Las columnas exactas (§5.10) no admiten ninguna diferencia, ni siquiera de representación."""
    comparador = comparar_5_2(
        datos_5_2.historiales, datos_5_2.mercado, datos_5_2.claves, datos_5_2.intermediarios, datos_5_2.refs
    )
    exactas = [d for d in comparador.diferencias if d.tolerancia.startswith("exacto")]
    assert len(exactas) > 1500
    assert all(d.cumple for d in exactas)
    # P de CETES: además del valor, los 7 decimales del texto (RD-16).
    for d in exactas:
        if d.archivo == "valuacion_cetes.csv" and d.columna == "p":
            assert d.esperado == d.obtenido


@pytest.mark.parametrize("id_rechazo", ["N1", "N2", "N3"])
def test_rechazos_por_saldo_negativo(datos_5_2, id_rechazo: str) -> None:
    """RF-28 crit. 1 a 3: primera fecha con saldo negativo y ese saldo, como en rechazos_rf28.csv."""
    fila = _rechazos()[id_rechazo]
    h = datos_5_2.historiales[fila["portafolio_nombre"]]
    resultado = motor.primer_saldo_negativo(h, _candidata(datos_5_2, fila))
    assert resultado == motor.SaldoNegativo(fecha_iso(fila["fecha_saldo_negativo"]), int(fila["saldo_resultante"]))
    assert fila["regla"].startswith("RF-28")


def test_c1_compras_antes_que_ventas(datos_5_2) -> None:
    """C1: T12 se acepta con T11 ya cargada (100 + 60 − 120 = 40); sin T11 quedaría en −20."""
    caso = leer_csv("casos_positivos", "")[0]
    t12 = datos_5_2.transacciones["T12"]
    sin_t12 = datos_5_2.historial_sin("Principal", "T12")
    assert motor.primer_saldo_negativo(sin_t12, t12) is None
    sin_t11_ni_t12 = datos_5_2.historial_sin("Principal", "T11", "T12")
    resultado = motor.primer_saldo_negativo(sin_t11_ni_t12, t12)
    assert resultado == motor.SaldoNegativo(t12.fecha_concertacion, int(caso["saldo_si_ventas_antes_que_compras"]))
    # El historial completo ya incluye T11 y T12 y es válido.
    assert len(datos_5_2.historiales["Principal"].transacciones) == 15


def test_n4_fecha_en_el_vencimiento_es_historial_invalido(datos_5_2) -> None:
    """RF-26a crit. 2: una transacción de la emisión fechada en su vencimiento no entra al motor."""
    fila = _rechazos()["N4"]
    candidata = _candidata(datos_5_2, fila)
    h = datos_5_2.historiales["Principal"]
    assert candidata.fecha_concertacion == datos_5_2.instrumentos["BI261008"].vencimiento
    with pytest.raises(motor.HistorialInvalido):
        motor.Historial(h.portafolio_id, (*h.transacciones, candidata), h.instrumentos)


@pytest.mark.parametrize("id_rechazo", ["N7", "N8"])
def test_periodos_invalidos(datos_5_2, id_rechazo: str) -> None:
    """RF-09 crit. 3: el código de `validar_periodo` corresponde a la columna `regla`."""
    fila = _rechazos()[id_rechazo]
    with pytest.raises(motor.PeriodoInvalido) as error:
        motor.validar_periodo(fecha_iso(fila["periodo_inicio"]), fecha_iso(fila["periodo_fin"]), datos_5_2.intervalo)
    assert error.value.codigo == CODIGO_POR_REGLA[fila["regla"]]
    assert error.value.regla == "RF-09"
    assert error.value.intervalo == datos_5_2.intervalo


def test_periodos_de_5_2_son_validos(datos_5_2) -> None:
    for fila in leer_csv("periodos", "entradas"):
        motor.validar_periodo(fecha_iso(fila["inicio"]), fecha_iso(fila["fin"]), datos_5_2.intervalo)
    for fila in leer_csv("cortes", "entradas"):
        motor.validar_corte(fecha_iso(fila["fecha_corte"]), datos_5_2.intervalo)


def test_rechazos_no_cambian_ninguna_cifra(datos_5_2) -> None:
    """Después de evaluar N1 a N8, todas las cifras siguen iguales (el motor no guarda nada)."""
    argumentos = (datos_5_2.historiales, datos_5_2.mercado, datos_5_2.claves, datos_5_2.intermediarios, datos_5_2.refs)
    antes = [(d.llave, d.columna, d.obtenido) for d in comparar_5_2(*argumentos).diferencias]
    for id_rechazo in ("N1", "N2", "N3"):
        fila = _rechazos()[id_rechazo]
        motor.primer_saldo_negativo(datos_5_2.historiales[fila["portafolio_nombre"]], _candidata(datos_5_2, fila))
    despues = [(d.llave, d.columna, d.obtenido) for d in comparar_5_2(*argumentos).diferencias]
    assert antes == despues


@pytest.mark.parametrize("periodo", [fila["periodo"] for fila in leer_csv("periodos", "entradas")])
def test_cifras_identicas_en_todas_las_vistas(datos_5_2, periodo: str) -> None:
    """RNF-02: el valor al corte es el mismo `Decimal` en la serie, el tablero y las posiciones."""
    fila = next(f for f in leer_csv("periodos", "entradas") if f["periodo"] == periodo)
    h = datos_5_2.historiales[fila["portafolio_nombre"]]
    inicio, fin = fecha_iso(fila["inicio"]), fecha_iso(fila["fin"])
    ind = motor.indicadores(h, datos_5_2.mercado, inicio, fin)
    corte = motor.posiciones(h, datos_5_2.mercado, fin)
    assert ind.corte_fin == corte
    assert ind.serie[-1].valor == ind.valor_fin == corte.valor
    assert sum((p.valor for p in corte.pares), Decimal(0)) == corte.valor
    assert sum((p.valor for p in corte.instrumentos), Decimal(0)) == corte.valor
    textos = {
        motor.presentar_importe(ind.serie[-1].valor),
        motor.presentar_importe(ind.valor_fin),
        motor.presentar_importe(corte.valor),
    }
    assert len(textos) == 1
    # Una consulta repetida da el mismo resultado.
    assert motor.indicadores(h, datos_5_2.mercado, inicio, fin) == ind
    # La serie de un periodo es un tramo de la serie completa, salvo el índice (que reinicia en la base).
    completa = {d.fecha: d for d in motor.indicadores(h, datos_5_2.mercado, date(2026, 9, 11), date(2026, 10, 14)).serie}
    for dia in ind.serie:
        assert dia.valor == completa[dia.fecha].valor


# Valores presentados que esperan las pruebas de la API (§4.3, «Valores esperados con las semillas»).
TABLERO = [
    ("P1-A", "4.39", "-6.68", date(2026, 9, 16), date(2026, 9, 23)),
    ("P1-B", "2.50", "-6.68", date(2026, 9, 16), date(2026, 9, 23)),
    ("P1-C", "1.84", "-2.18", date(2026, 9, 30), date(2026, 10, 5)),
    ("P1-D", "1.50", "0.00", None, None),
    ("P2-A", "6.88", "-13.68", date(2026, 9, 15), date(2026, 9, 23)),
    ("P2-C", "3.69", "-5.09", date(2026, 9, 30), date(2026, 10, 5)),
]


@pytest.mark.parametrize(("periodo", "twr", "caida", "pico", "valle"), TABLERO)
def test_indicadores_presentados(datos_5_2, periodo: str, twr: str, caida: str, pico, valle) -> None:
    fila = next(f for f in leer_csv("periodos", "entradas") if f["periodo"] == periodo)
    h = datos_5_2.historiales[fila["portafolio_nombre"]]
    ind = motor.indicadores(h, datos_5_2.mercado, fecha_iso(fila["inicio"]), fecha_iso(fila["fin"]))
    assert motor.presentar_por_ciento(ind.twr) == twr
    assert motor.presentar_por_ciento(ind.maxima_caida) == caida
    assert (ind.fecha_pico, ind.fecha_valle) == (pico, valle)


def test_cortes_presentados_de_principal(datos_5_2) -> None:
    h = datos_5_2.historiales["Principal"]
    al_16 = motor.posiciones(h, datos_5_2.mercado, date(2026, 9, 16))
    assert motor.presentar_importe(al_16.valor) == "71641.88"
    assert motor.presentar_importe(al_16.resultado_no_realizado) == "1333.46"
    al_14 = motor.posiciones(h, datos_5_2.mercado, date(2026, 10, 14))
    assert motor.presentar_importe(al_14.valor) == "58940.88"
    assert motor.presentar_importe(al_14.costo_total) == "56307.89"
    assert motor.presentar_importe(al_14.resultado_no_realizado) == "2632.99"
    ind = motor.indicadores(h, datos_5_2.mercado, date(2026, 9, 11), date(2026, 10, 14))
    assert len(ind.serie) == 35
    assert motor.presentar_importe(ind.serie[0].valor) == "49929.06"


def test_costo_e_ingreso_por_titulo_presentados(datos_5_2) -> None:
    """E17 (§4.3): T01 «100.23985», T11 «48.0388333» y T10 «23.1402» (D-14)."""
    t = datos_5_2.transacciones
    assert motor.presentar_por_titulo(motor.importes(t["T01"]).costo_por_titulo) == "100.23985"
    assert motor.presentar_por_titulo(motor.importes(t["T11"]).costo_por_titulo) == "48.0388333"
    assert motor.presentar_por_titulo(motor.importes(t["T10"]).ingreso_por_titulo) == "23.1402"


def test_procedencia_de_los_datos_usados(datos_5_2) -> None:
    """RF-31 crit. 2 y 3: fecha del cierre usado, no la de valuación, y fuentes de cada cifra."""
    h = datos_5_2.historiales["Principal"]
    corte = motor.posiciones(h, datos_5_2.mercado, date(2026, 10, 8))
    demofib = next(p for p in corte.instrumentos if p.instrumento_id == datos_5_2.instrumentos["DEMOFIB"].id)
    assert demofib.fecha_precio == date(2026, 10, 7)
    al_13 = motor.posiciones(h, datos_5_2.mercado, date(2026, 9, 13))
    demoacc = next(p for p in al_13.instrumentos if p.instrumento_id == datos_5_2.instrumentos["DEMOACC"].id)
    assert demoacc.fecha_precio == date(2026, 9, 11)
    # Banco de México (tasas, id 1) y la semilla sintética (cierres, id 2).
    assert corte.fuentes_usadas == frozenset({1, 2})
    secundario = motor.posiciones(datos_5_2.historiales["Secundario"], datos_5_2.mercado, date(2026, 10, 8))
    assert secundario.fuentes_usadas == frozenset({2})
    # Al 07/10 rige la colocación del 01/10; la del 08/10 todavía no (RF-26b crit. 3).
    al_7 = motor.valuar_cetes(datos_5_2.mercado, datos_5_2.instrumentos["BI261008"], date(2026, 10, 7))
    assert (al_7.d, al_7.inf.fecha_colocacion, al_7.r) == (1, date(2026, 10, 1), Decimal("6.01000"))


def test_comparador_detecta_cifras_fuera_de_tolerancia() -> None:
    """El comparador no es vacuo: distingue lo que está dentro y fuera de cada tolerancia."""
    comparador = Comparador()
    comparador.comparar("x.csv", "a", "valor", "100.0000", Decimal("100.01"), "importe")
    comparador.comparar("x.csv", "b", "valor", "100.0000", Decimal("100.0101"), "importe")
    comparador.comparar("x.csv", "c", "twr_por_ciento", "4.3928", Decimal("4.3938"), "pp")
    comparador.comparar("x.csv", "d", "twr_por_ciento", "4.3928", Decimal("4.39381"), "pp")
    comparador.comparar("x.csv", "e", "p", "9.9516240", Decimal("9.9516241"), "exacto")
    comparador.comparar("x.csv", "f", "fecha_pico", "", None, "exacto")
    comparador.comparar("x.csv", "g", "fecha_pico", "2026-09-15", date(2026, 9, 16), "exacto")
    comparador.comparar("x.csv", "h", "tiene_transacciones", "sí", True, "exacto")
    comparador.comparar("x.csv", "i", "r", "", Decimal(0), "fraccion")
    assert [d.cumple for d in comparador.diferencias] == [True, False, True, False, False, True, False, True, False]
    with pytest.raises(AssertionError, match="5 de 9"):
        comparador.verificar()
    with pytest.raises(TypeError):
        comparador.comparar("x.csv", "j", "valor", "1", 1.0, "importe")
