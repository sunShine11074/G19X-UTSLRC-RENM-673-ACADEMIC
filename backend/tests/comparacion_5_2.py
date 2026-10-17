"""Lector de `esperados/` del conjunto de referencia (5.2) y comparador con las tolerancias de RNF-01.

Lo usan CPNF-01 nivel 1 (motor puro, `tests/motor/test_oraculo_5_2.py`) y nivel 2 (base y
servicio de cálculo, WP5). Compara sin redondear: los CSV se leen como `Decimal` y la salida
del motor no se redondea (P-13). Las diferencias se acumulan para tener la tabla completa
(§5.10 del diseño; README del oráculo, «Tolerancias de RNF-01»).
"""

import csv
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Context, Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import TypeVar

from app import motor
from app.motor import DatosMercado, Historial, Instrumento

RUTA_ORACULO = Path(__file__).resolve().parent / "oraculo"

TOLERANCIAS: dict[str, Decimal | None] = {
    "importe": Decimal("0.01"),  # pesos (RNF-01)
    "fraccion": Decimal("0.00001"),  # twr, maxima_caida, r, indice, maximo y caida
    "pp": Decimal("0.001"),  # puntos porcentuales (RNF-01)
    "unitario": Decimal("0.0000001"),  # costo o ingreso por título, costo unitario y P sin redondear
    "exacto": None,  # títulos, d, plazos, fechas, caso, sí/no, P, tasas y cierres
}

ARCHIVOS_ESPERADOS: tuple[str, ...] = (
    "transacciones.csv",
    "precios_usados.csv",
    "valuacion_cetes.csv",
    "posiciones.csv",
    "serie_diaria.csv",
    "indice_por_periodo.csv",
    "indicadores.csv",
)

_PRECISION_DIFERENCIA = Context(prec=80)
_T = TypeVar("_T")


def leer_csv(nombre: str, carpeta: str = "esperados") -> list[dict[str, str]]:
    """Filas de un CSV del oráculo como diccionarios de texto (sin convertir).

    `carpeta` es relativa a `tests/oraculo`; con "" se lee un archivo de la raíz del
    oráculo, como `rechazos_rf28.csv`.
    """
    archivo = nombre if nombre.endswith(".csv") else f"{nombre}.csv"
    ruta = RUTA_ORACULO / carpeta / archivo if carpeta else RUTA_ORACULO / archivo
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def fecha_iso(texto: str) -> date:
    """Fecha AAAA-MM-DD de un CSV."""
    return date.fromisoformat(texto)


@dataclass
class Diferencia:
    """Una cifra comparada: su llave, ambos valores y si cumple la tolerancia."""

    archivo: str
    llave: str
    columna: str
    esperado: str
    obtenido: str
    diferencia_abs: Decimal | None
    tolerancia: str
    cumple: bool


def _texto(valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    if isinstance(valor, Decimal):
        return format(valor, "f")
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def _decimal(texto: str) -> Decimal | None:
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def _iguales(esperado: str, obtenido: object) -> bool:
    """Igualdad exacta según el tipo de lo obtenido; una celda vacía equivale a None."""
    if obtenido is None or esperado == "":
        return obtenido is None and esperado == ""
    if isinstance(obtenido, bool):
        return esperado == ("sí" if obtenido else "no")
    if isinstance(obtenido, int):
        return esperado.strip() == str(obtenido)
    if isinstance(obtenido, Decimal):
        valor = _decimal(esperado)
        return valor is not None and valor == obtenido
    if isinstance(obtenido, date):
        try:
            return date.fromisoformat(esperado) == obtenido
        except ValueError:
            return False
    if isinstance(obtenido, str):
        return esperado == obtenido
    raise TypeError(f"No se sabe comparar {type(obtenido).__name__} con igualdad exacta.")


class Comparador:
    """Acumula cada cifra comparada y falla al final con las peores diferencias."""

    def __init__(self) -> None:
        self.diferencias: list[Diferencia] = []

    def comparar(self, archivo: str, llave: str, columna: str, esperado: str, obtenido: object, tipo: str) -> None:
        """Compara `obtenido` contra el texto `esperado` con la tolerancia de `tipo`.

        tipo ∈ {"importe", "fraccion", "pp", "unitario", "exacto"}. Para "pp", `obtenido`
        ya debe venir en puntos porcentuales.
        """
        if tipo not in TOLERANCIAS:
            raise ValueError(f"Tipo de comparación desconocido: {tipo}")
        if isinstance(obtenido, float):
            raise TypeError("El motor no puede entregar float (RD-12).")
        tolerancia = TOLERANCIAS[tipo]
        diferencia: Decimal | None = None
        if tolerancia is None:
            cumple = _iguales(esperado, obtenido)
            texto_tolerancia = "exacto: igualdad"
        else:
            texto_tolerancia = f"{tipo}: ≤ {tolerancia}"
            if esperado == "" or obtenido is None:
                cumple = esperado == "" and obtenido is None
            else:
                if not isinstance(obtenido, Decimal | int) or isinstance(obtenido, bool):
                    raise TypeError(f"{columna}: se esperaba Decimal, no {type(obtenido).__name__}.")
                valor = _decimal(esperado)
                if valor is None:
                    cumple = False
                else:
                    with localcontext(_PRECISION_DIFERENCIA):
                        diferencia = abs(valor - Decimal(obtenido))
                    cumple = diferencia <= tolerancia
        self.diferencias.append(
            Diferencia(
                archivo=archivo,
                llave=llave,
                columna=columna,
                esperado=esperado,
                obtenido=_texto(obtenido),
                diferencia_abs=diferencia,
                tolerancia=texto_tolerancia,
                cumple=cumple,
            )
        )

    def falla(self, archivo: str, llave: str, columna: str, esperado: str, obtenido: str) -> None:
        """Registra un renglón sin contraparte o un error del motor."""
        self.diferencias.append(
            Diferencia(archivo, llave, columna, esperado, obtenido, None, "renglón", False)
        )

    def fallas(self) -> list[Diferencia]:
        return [d for d in self.diferencias if not d.cumple]

    def maxima_diferencia(self, archivo: str, columna: str) -> Decimal | None:
        valores = [
            d.diferencia_abs
            for d in self.diferencias
            if d.archivo == archivo and d.columna == columna and d.diferencia_abs is not None
        ]
        return max(valores) if valores else None

    def verificar(self, peores: int = 20) -> None:
        """Falla con las `peores` diferencias si alguna cifra queda fuera de tolerancia."""
        fallas = self.fallas()
        if not fallas:
            return

        def gravedad(d: Diferencia) -> tuple[int, Decimal]:
            if d.diferencia_abs is None:
                return (1, Decimal(0))
            tipo = d.tolerancia.split(":", 1)[0]
            tolerancia = TOLERANCIAS.get(tipo) or Decimal(1)
            with localcontext(_PRECISION_DIFERENCIA):
                return (0, d.diferencia_abs / tolerancia)

        fallas.sort(key=gravedad, reverse=True)
        lineas = [
            f"{len(fallas)} de {len(self.diferencias)} cifras de 5.2 fuera de tolerancia; las {min(peores, len(fallas))} peores:",
        ]
        for d in fallas[:peores]:
            lineas.append(
                f"  {d.archivo} [{d.llave}] {d.columna}: esperado={d.esperado!r} obtenido={d.obtenido!r} "
                f"diferencia={_texto(d.diferencia_abs) or '—'} ({d.tolerancia})"
            )
        raise AssertionError("\n".join(lineas))

    def escribir(self, carpeta: Path) -> None:
        """Escribe `cpnf01_diferencias.csv` (cada cifra) y `cpnf01_resumen.csv` (por archivo y tolerancia)."""
        carpeta.mkdir(parents=True, exist_ok=True)
        with (carpeta / "cpnf01_diferencias.csv").open("w", encoding="utf-8", newline="") as fh:
            escritor = csv.writer(fh)
            escritor.writerow(
                ["archivo", "llave", "columna", "esperado", "obtenido", "diferencia_abs", "tolerancia", "cumple"]
            )
            for d in self.diferencias:
                escritor.writerow(
                    [
                        d.archivo,
                        d.llave,
                        d.columna,
                        d.esperado,
                        d.obtenido,
                        _texto(d.diferencia_abs),
                        d.tolerancia,
                        "sí" if d.cumple else "no",
                    ]
                )
        resumen: dict[tuple[str, str], list[Diferencia]] = {}
        for d in self.diferencias:
            resumen.setdefault((d.archivo, d.tolerancia), []).append(d)
        with (carpeta / "cpnf01_resumen.csv").open("w", encoding="utf-8", newline="") as fh:
            escritor = csv.writer(fh)
            escritor.writerow(["archivo", "tolerancia", "cifras", "fuera_de_tolerancia", "diferencia_maxima"])
            for (archivo, tolerancia), grupo in sorted(resumen.items()):
                maximas = [d.diferencia_abs for d in grupo if d.diferencia_abs is not None]
                escritor.writerow(
                    [
                        archivo,
                        tolerancia,
                        len(grupo),
                        sum(1 for d in grupo if not d.cumple),
                        _texto(max(maximas)) if maximas else "",
                    ]
                )


# --- Comparación de los siete archivos de esperados/ ---------------------------------


def _intentar(comparador: Comparador, archivo: str, llave: str, funcion: Callable[[], _T]) -> _T | None:
    """Llama al motor; si lanza un error, lo registra como falla del renglón."""
    try:
        return funcion()
    except Exception as exc:  # se registra y la prueba falla al final con la tabla completa
        comparador.falla(archivo, llave, "(error del motor)", "", f"{type(exc).__name__}: {exc}")
        return None


def _dias(inicio: date, fin: date) -> list[date]:
    return [inicio + timedelta(days=n) for n in range((fin - inicio).days + 1)]


def _por_ciento(valor: Decimal | None) -> Decimal | None:
    return None if valor is None else valor.scaleb(2)


def _parametros() -> dict[str, str]:
    return {fila["parametro"]: fila["valor"] for fila in leer_csv("parametros", "entradas")}


def _comparar_transacciones(
    comp: Comparador, transacciones: Mapping[int, motor.Transaccion], refs: Mapping[str, int]
) -> None:
    archivo = "transacciones.csv"
    vistas: set[str] = set()
    for fila in leer_csv(archivo):
        ref = fila["ref"]
        vistas.add(ref)
        t = transacciones.get(refs.get(ref, -1))
        if t is None:
            comp.falla(archivo, ref, "ref", ref, "sin transacción")
            continue
        imp = _intentar(comp, archivo, ref, lambda t=t: motor.importes(t))
        if imp is None:
            continue
        comp.comparar(archivo, ref, "tipo", fila["tipo"], t.tipo, "exacto")
        comp.comparar(archivo, ref, "monto", fila["monto"], imp.monto, "importe")
        comp.comparar(archivo, ref, "costo_por_titulo", fila["costo_por_titulo"], imp.costo_por_titulo, "unitario")
        comp.comparar(archivo, ref, "ingreso_por_titulo", fila["ingreso_por_titulo"], imp.ingreso_por_titulo, "unitario")
        comp.comparar(archivo, ref, "aportacion", fila["aportacion"], imp.aportacion, "importe")
        comp.comparar(archivo, ref, "retiro", fila["retiro"], imp.retiro, "importe")
    for ref in sorted(set(refs) - vistas):
        comp.falla(archivo, ref, "ref", "", "transacción de más")


def _comparar_precios_usados(
    comp: Comparador, mercado: DatosMercado, por_clave: Mapping[str, Instrumento], dias: list[date]
) -> None:
    archivo = "precios_usados.csv"
    vistas: set[tuple[date, str]] = set()
    for fila in leer_csv(archivo):
        fecha, clave = fecha_iso(fila["fecha"]), fila["instrumento_clave"]
        llave = f"{fila['fecha']}|{clave}"
        vistas.add((fecha, clave))
        instrumento = por_clave.get(clave)
        if instrumento is None:
            comp.falla(archivo, llave, "instrumento_clave", clave, "instrumento desconocido")
            continue
        usado = _intentar(comp, archivo, llave, lambda i=instrumento, f=fecha: motor.cierre_vigente(mercado, i, f))
        comp.comparar(archivo, llave, "fecha_cierre", fila["fecha_cierre"], usado and usado.fecha_cierre, "exacto")
        comp.comparar(archivo, llave, "precio", fila["precio"], usado and usado.precio, "exacto")
        comp.comparar(
            archivo, llave, "sin_cierre_ese_dia", fila["sin_cierre_ese_dia"], usado and usado.sin_cierre_ese_dia, "exacto"
        )
    # Un cierre que el motor usaría en un día de la serie y que no está en esperados es un fallo.
    for fecha in dias:
        for clave, instrumento in sorted(por_clave.items()):
            if instrumento.es_cetes or (fecha, clave) in vistas:
                continue
            usado = _intentar(comp, archivo, f"{fecha}|{clave}", lambda i=instrumento, f=fecha: motor.cierre_vigente(mercado, i, f))
            if usado is not None:
                comp.falla(archivo, f"{fecha}|{clave}", "fecha_cierre", "", f"renglón de más ({usado.fecha_cierre})")


def _comparar_cetes(comp: Comparador, archivo: str, llave: str, fila: Mapping[str, str], v: motor.ValuacionCetes | None) -> None:
    comp.comparar(archivo, llave, "vencimiento", fila["vencimiento"], v and v.vencimiento, "exacto")
    comp.comparar(archivo, llave, "d", fila["d"], v and v.d, "exacto")
    comp.comparar(archivo, llave, "caso", fila["caso"], v and str(v.caso), "exacto")
    for lado in ("inf", "sup"):
        nodo = v and (v.inf if lado == "inf" else v.sup)
        comp.comparar(archivo, llave, f"{lado}_plazo_nominal", fila[f"{lado}_plazo_nominal"], nodo and nodo.plazo_nominal, "exacto")
        comp.comparar(archivo, llave, f"{lado}_plazo_efectivo", fila[f"{lado}_plazo_efectivo"], nodo and nodo.plazo_efectivo, "exacto")
        comp.comparar(archivo, llave, f"{lado}_tasa", fila[f"{lado}_tasa"], nodo and nodo.tasa, "exacto")
        comp.comparar(archivo, llave, f"{lado}_fecha_colocacion", fila[f"{lado}_fecha_colocacion"], nodo and nodo.fecha_colocacion, "exacto")
    comp.comparar(archivo, llave, "r_por_ciento_anual", fila["r_por_ciento_anual"], v and v.r, "pp")
    comp.comparar(archivo, llave, "p_sin_redondear", fila["p_sin_redondear"], v and v.p_sin_redondear, "unitario")
    comp.comparar(archivo, llave, "p", fila["p"], v and v.p, "exacto")


def _comparar_valuacion_cetes(
    comp: Comparador,
    mercado: DatosMercado,
    por_clave: Mapping[str, Instrumento],
    cortes_diarios: Mapping[tuple[date, str], motor.Corte],
    claves: Mapping[int, str],
) -> None:
    archivo = "valuacion_cetes.csv"
    # Valuaciones que usan las posiciones de cada día (la misma función que E19 y E20).
    en_posiciones: dict[tuple[date, str], motor.ValuacionCetes] = {}
    for (fecha, _portafolio), corte in cortes_diarios.items():
        for posicion in corte.instrumentos:
            if posicion.cetes is not None:
                en_posiciones[(fecha, claves[posicion.instrumento_id])] = posicion.cetes
    vistas: set[tuple[date, str]] = set()
    for fila in leer_csv(archivo):
        fecha, clave = fecha_iso(fila["fecha"]), fila["instrumento_clave"]
        llave = f"{fila['fecha']}|{clave}"
        vistas.add((fecha, clave))
        emision = por_clave.get(clave)
        if emision is None:
            comp.falla(archivo, llave, "instrumento_clave", clave, "emisión desconocida")
            continue
        v = _intentar(comp, archivo, llave, lambda e=emision, f=fecha: motor.valuar_cetes(mercado, e, f))
        _comparar_cetes(comp, archivo, llave, fila, v)
        # La valuación de las posiciones es la misma (RNF-02).
        en_corte = en_posiciones.get((fecha, clave))
        comp.comparar(archivo, llave, "p (posiciones del día)", fila["p"], en_corte and en_corte.p, "exacto")
    for fecha, clave in sorted(set(en_posiciones) - vistas):
        comp.falla(archivo, f"{fecha}|{clave}", "p", "", f"renglón de más ({en_posiciones[(fecha, clave)].p})")


def _comparar_posiciones(
    comp: Comparador,
    cortes: Mapping[tuple[date, str], motor.Corte],
    claves: Mapping[int, str],
    intermediarios: Mapping[int, str],
) -> None:
    archivo = "posiciones.csv"
    # Renglones del motor por llave (nivel, fecha, portafolio, clave, intermediario).
    del_motor: dict[tuple[str, str, str, str, str], object] = {}
    for (fecha, portafolio), corte in cortes.items():
        f = fecha.isoformat()
        for par in corte.pares:
            del_motor[("intermediario", f, portafolio, claves[par.instrumento_id], intermediarios[par.intermediario_id])] = par
        for posicion in corte.instrumentos:
            del_motor[("instrumento", f, portafolio, claves[posicion.instrumento_id], "")] = posicion
        del_motor[("portafolio", f, portafolio, "", "")] = corte

    vistas: set[tuple[str, str, str, str, str]] = set()
    for fila in leer_csv(archivo):
        llave_t = (fila["nivel"], fila["fecha_corte"], fila["portafolio"], fila["instrumento_clave"], fila["intermediario"])
        llave = "|".join(llave_t)
        vistas.add(llave_t)
        obtenido = del_motor.get(llave_t)
        if obtenido is None:
            # Un renglón esperado con títulos 0 que el motor no emite cuenta como renglón en cero.
            if fila["nivel"] != "portafolio" and fila["titulos"] == "0":
                for columna in ("costo_total", "valor", "resultado_no_realizado"):
                    comp.comparar(archivo, llave, columna, fila[columna], Decimal(0), "importe")
            else:
                comp.falla(archivo, llave, "renglón", "presente", "el motor no lo emite")
            continue
        if isinstance(obtenido, motor.PosicionPar):
            cetes = obtenido.cetes
            comp.comparar(archivo, llave, "tiene_transacciones", fila["tiene_transacciones"], obtenido.tiene_transacciones, "exacto")
            comp.comparar(archivo, llave, "costo_unitario", fila["costo_unitario"], obtenido.costo_unitario, "unitario")
            comp.comparar(archivo, llave, "precio", fila["precio"], obtenido.precio, "exacto")
            comp.comparar(archivo, llave, "fecha_precio", fila["fecha_precio"], obtenido.fecha_precio, "exacto")
            comp.comparar(archivo, llave, "d", fila["d"], cetes and cetes.d, "exacto")
            comp.comparar(archivo, llave, "r_por_ciento_anual", fila["r_por_ciento_anual"], cetes and cetes.r, "pp")
            comp.comparar(archivo, llave, "fecha_colocacion_inf", fila["fecha_colocacion_inf"], cetes and cetes.inf.fecha_colocacion, "exacto")
            comp.comparar(archivo, llave, "fecha_colocacion_sup", fila["fecha_colocacion_sup"], cetes and cetes.sup.fecha_colocacion, "exacto")
        if isinstance(obtenido, motor.PosicionPar | motor.PosicionInstrumento):
            comp.comparar(archivo, llave, "titulos", fila["titulos"], obtenido.titulos, "exacto")
        assert isinstance(obtenido, motor.PosicionPar | motor.PosicionInstrumento | motor.Corte)
        comp.comparar(archivo, llave, "costo_total", fila["costo_total"], obtenido.costo_total, "importe")
        comp.comparar(archivo, llave, "valor", fila["valor"], obtenido.valor, "importe")
        comp.comparar(archivo, llave, "resultado_no_realizado", fila["resultado_no_realizado"], obtenido.resultado_no_realizado, "importe")

    # Un renglón de más en el motor con cifras distintas de 0 es un fallo.
    for llave_t in sorted(set(del_motor) - vistas):
        obtenido = del_motor[llave_t]
        assert isinstance(obtenido, motor.PosicionPar | motor.PosicionInstrumento | motor.Corte)
        titulos = getattr(obtenido, "titulos", 0)
        if titulos != 0 or obtenido.costo_total != 0 or obtenido.valor != 0 or obtenido.resultado_no_realizado != 0:
            comp.falla(archivo, "|".join(llave_t), "renglón", "", f"renglón de más con valor {obtenido.valor}")


def _comparar_dia(comp: Comparador, archivo: str, llave: str, fila: Mapping[str, str], dia: motor.DiaSerie) -> None:
    comp.comparar(archivo, llave, "r", fila["r"], dia.r, "fraccion")
    if "r_por_ciento" in fila:
        comp.comparar(archivo, llave, "r_por_ciento", fila["r_por_ciento"], _por_ciento(dia.r), "pp")
    comp.comparar(archivo, llave, "indice", fila["indice"], dia.indice, "fraccion")
    comp.comparar(archivo, llave, "maximo", fila["maximo"], dia.maximo, "fraccion")
    comp.comparar(archivo, llave, "caida", fila["caida"], dia.caida, "fraccion")


def _comparar_serie_diaria(comp: Comparador, series: Mapping[str, tuple[motor.DiaSerie, ...]]) -> None:
    archivo = "serie_diaria.csv"
    del_motor = {(dia.fecha, portafolio): dia for portafolio, serie in series.items() for dia in serie}
    vistas: set[tuple[date, str]] = set()
    for fila in leer_csv(archivo):
        llave_t = (fecha_iso(fila["fecha"]), fila["portafolio"])
        llave = f"{fila['fecha']}|{fila['portafolio']}"
        vistas.add(llave_t)
        dia = del_motor.get(llave_t)
        if dia is None:
            comp.falla(archivo, llave, "renglón", "presente", "el motor no lo emite")
            continue
        comp.comparar(archivo, llave, "valor", fila["valor"], dia.valor, "importe")
        comp.comparar(archivo, llave, "aportaciones", fila["aportaciones"], dia.aportaciones, "importe")
        comp.comparar(archivo, llave, "retiros_ventas", fila["retiros_ventas"], dia.retiros_ventas, "importe")
        comp.comparar(archivo, llave, "retiros_vencimientos", fila["retiros_vencimientos"], dia.retiros_vencimientos, "importe")
        comp.comparar(archivo, llave, "retiros", fila["retiros"], dia.retiros, "importe")
        _comparar_dia(comp, archivo, llave, fila, dia)
    for fecha, portafolio in sorted(set(del_motor) - vistas):
        comp.falla(archivo, f"{fecha}|{portafolio}", "renglón", "", "renglón de más")


def _comparar_periodos(comp: Comparador, resultados: Mapping[str, tuple[str, motor.Indicadores]]) -> None:
    archivo = "indice_por_periodo.csv"
    del_motor = {
        (periodo, dia.fecha): dia for periodo, (_p, ind) in resultados.items() for dia in ind.serie[1:]
    }
    vistas: set[tuple[str, date]] = set()
    for fila in leer_csv(archivo):
        llave_t = (fila["periodo"], fecha_iso(fila["fecha"]))
        llave = f"{fila['periodo']}|{fila['fecha']}"
        vistas.add(llave_t)
        dia = del_motor.get(llave_t)
        if dia is None:
            comp.falla(archivo, llave, "renglón", "presente", "el motor no lo emite")
            continue
        _comparar_dia(comp, archivo, llave, fila, dia)
    for periodo, fecha in sorted(set(del_motor) - vistas):
        comp.falla(archivo, f"{periodo}|{fecha}", "renglón", "", "renglón de más")

    archivo = "indicadores.csv"
    vistos: set[str] = set()
    for fila in leer_csv(archivo):
        periodo = fila["periodo"]
        vistos.add(periodo)
        if periodo not in resultados:
            comp.falla(archivo, periodo, "renglón", "presente", "periodo sin calcular")
            continue
        portafolio, ind = resultados[periodo]
        comp.comparar(archivo, periodo, "portafolio", fila["portafolio"], portafolio, "exacto")
        comp.comparar(archivo, periodo, "inicio", fila["inicio"], ind.inicio, "exacto")
        comp.comparar(archivo, periodo, "fin", fila["fin"], ind.fin, "exacto")
        comp.comparar(archivo, periodo, "fecha_base", fila["fecha_base"], ind.fecha_base, "exacto")
        comp.comparar(archivo, periodo, "dias", fila["dias"], ind.dias, "exacto")
        comp.comparar(archivo, periodo, "valor_base", fila["valor_base"], ind.valor_base, "importe")
        comp.comparar(archivo, periodo, "valor_fin", fila["valor_fin"], ind.valor_fin, "importe")
        comp.comparar(archivo, periodo, "costo_total_fin", fila["costo_total_fin"], ind.costo_total_fin, "importe")
        comp.comparar(archivo, periodo, "resultado_no_realizado_fin", fila["resultado_no_realizado_fin"], ind.resultado_no_realizado_fin, "importe")
        comp.comparar(archivo, periodo, "twr", fila["twr"], ind.twr, "fraccion")
        comp.comparar(archivo, periodo, "twr_por_ciento", fila["twr_por_ciento"], _por_ciento(ind.twr), "pp")
        comp.comparar(archivo, periodo, "maxima_caida", fila["maxima_caida"], ind.maxima_caida, "fraccion")
        comp.comparar(archivo, periodo, "maxima_caida_por_ciento", fila["maxima_caida_por_ciento"], _por_ciento(ind.maxima_caida), "pp")
        comp.comparar(archivo, periodo, "fecha_pico", fila["fecha_pico"], ind.fecha_pico, "exacto")
        comp.comparar(archivo, periodo, "fecha_valle", fila["fecha_valle"], ind.fecha_valle, "exacto")
    for periodo in sorted(set(resultados) - vistos):
        comp.falla(archivo, periodo, "renglón", "", "periodo de más")


def comparar_5_2(
    historiales: Mapping[str, Historial],
    mercado: DatosMercado,
    claves: Mapping[int, str],
    intermediarios: Mapping[int, str],
    refs: Mapping[str, int],
) -> Comparador:
    """Compara con `esperados/` todo lo que calcula el motor para 5.2.

    - `historiales`: un `Historial` por nombre de portafolio («Principal», «Secundario»).
    - `claves`: clave de cada instrumento por id; `intermediarios`: nombre por id.
    - `refs`: id de cada transacción por su `ref` (T01 a T16).
    Los cortes, periodos y la serie salen de `entradas/` (cortes, periodos y parametros).
    """
    comp = Comparador()
    por_clave: dict[str, Instrumento] = {}
    transacciones: dict[int, motor.Transaccion] = {}
    for h in historiales.values():
        for instrumento in h.instrumentos.values():
            por_clave[instrumento.clave] = instrumento
            if claves.get(instrumento.id) != instrumento.clave:
                comp.falla("(entradas)", instrumento.clave, "clave", instrumento.clave, str(claves.get(instrumento.id)))
        for t in h.transacciones:
            if t.id is not None:
                transacciones[t.id] = t

    parametros = _parametros()
    serie_base = fecha_iso(parametros["serie_inicio"])
    serie_fin = fecha_iso(parametros["serie_fin"])
    dias = _dias(serie_base, serie_fin)

    # 1. transacciones.csv
    _comparar_transacciones(comp, transacciones, refs)
    # 2. precios_usados.csv
    _comparar_precios_usados(comp, mercado, por_clave, dias)

    # Posiciones de cada día de la serie y de cada corte, por portafolio.
    fechas_corte = {fecha_iso(f["fecha_corte"]) for f in leer_csv("cortes", "entradas")}
    fechas_corte |= {fecha_iso(f["fecha_corte"]) for f in leer_csv("posiciones.csv")}
    cortes_diarios: dict[tuple[date, str], motor.Corte] = {}
    for nombre, h in historiales.items():
        for fecha in sorted(set(dias) | fechas_corte):
            corte = _intentar(comp, "posiciones.csv", f"{fecha}|{nombre}", lambda h=h, f=fecha: motor.posiciones(h, mercado, f))
            if corte is not None:
                cortes_diarios[(fecha, nombre)] = corte

    # 3. valuacion_cetes.csv
    _comparar_valuacion_cetes(comp, mercado, por_clave, {k: v for k, v in cortes_diarios.items() if k[0] in dias}, claves)
    # 4. posiciones.csv
    _comparar_posiciones(comp, {k: v for k, v in cortes_diarios.items() if k[0] in fechas_corte}, claves, intermediarios)

    # 5. serie_diaria.csv: indicadores del intervalo completo (base en serie_inicio).
    series: dict[str, tuple[motor.DiaSerie, ...]] = {}
    for nombre, h in historiales.items():
        ind = _intentar(comp, "serie_diaria.csv", nombre, lambda h=h: motor.indicadores(h, mercado, serie_base + timedelta(days=1), serie_fin))
        if ind is not None:
            series[nombre] = ind.serie
    _comparar_serie_diaria(comp, series)

    # 6 y 7. indice_por_periodo.csv e indicadores.csv
    resultados: dict[str, tuple[str, motor.Indicadores]] = {}
    for fila in leer_csv("periodos", "entradas"):
        nombre = fila["portafolio_nombre"]
        h = historiales.get(nombre)
        if h is None:
            comp.falla("indicadores.csv", fila["periodo"], "portafolio", nombre, "sin historial")
            continue
        inicio, fin = fecha_iso(fila["inicio"]), fecha_iso(fila["fin"])
        ind = _intentar(comp, "indicadores.csv", fila["periodo"], lambda h=h, i=inicio, f=fin: motor.indicadores(h, mercado, i, f))
        if ind is not None:
            resultados[fila["periodo"]] = (nombre, ind)
    _comparar_periodos(comp, resultados)
    return comp
