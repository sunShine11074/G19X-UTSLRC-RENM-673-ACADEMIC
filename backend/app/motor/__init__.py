"""Motor único de cálculo (2.1; 4.2 «Motor único»; §5 del diseño).

Deriva toda cifra del sistema con `decimal` a 28 dígitos y solo con la biblioteca
estándar (RNF-10). No guarda cifras, no conoce usuarios ni lee la base: recibe un
`Historial` y lee precios y tasas por `DatosMercado`. Solo redondea el precio P de los
CETES; para presentar, ofrece las funciones `presentar*`.
"""

from .cetes import valuar_cetes
from .contexto import CONTEXTO, SIETE, calculo
from .errores import CifraNoCalculable, ErrorMotor, HistorialInvalido, PeriodoInvalido
from .importes import importes
from .kardex import primer_saldo_negativo
from .mercado import DatosMercado, MercadoEnMemoria
from .modelos import (
    CaidaMaxima,
    CasoTasa,
    ClaseActivo,
    Cierre,
    Colocacion,
    Corte,
    DiaSerie,
    Historial,
    ImportesTransaccion,
    Indicadores,
    Instrumento,
    Intervalo,
    NodoTasa,
    PosicionInstrumento,
    PosicionPar,
    PrecioUsado,
    SaldoNegativo,
    TipoTx,
    Transaccion,
    ValuacionCetes,
)
from .presentacion import presentar, presentar_importe, presentar_por_ciento, presentar_por_titulo
from .serie import (
    caida_maxima,
    indicadores,
    rendimiento_diario,
    serie_diaria,
    validar_corte,
    validar_periodo,
)
from .valuacion import cierre_vigente, posiciones

__all__ = [
    # Cálculo (§5.9)
    "importes",
    "primer_saldo_negativo",
    "cierre_vigente",
    "valuar_cetes",
    "posiciones",
    "serie_diaria",
    "indicadores",
    "rendimiento_diario",
    "caida_maxima",
    "validar_periodo",
    "validar_corte",
    # Presentación (§5.8)
    "presentar",
    "presentar_importe",
    "presentar_por_ciento",
    "presentar_por_titulo",
    # Datos de mercado (§5.4)
    "DatosMercado",
    "MercadoEnMemoria",
    # Entradas (§5.3)
    "ClaseActivo",
    "TipoTx",
    "Instrumento",
    "Transaccion",
    "Cierre",
    "Colocacion",
    "Historial",
    "Intervalo",
    # Salidas (§5.7)
    "ImportesTransaccion",
    "SaldoNegativo",
    "PrecioUsado",
    "CasoTasa",
    "NodoTasa",
    "ValuacionCetes",
    "PosicionPar",
    "PosicionInstrumento",
    "Corte",
    "DiaSerie",
    "CaidaMaxima",
    "Indicadores",
    # Errores
    "ErrorMotor",
    "CifraNoCalculable",
    "PeriodoInvalido",
    "HistorialInvalido",
    # Aritmética
    "CONTEXTO",
    "SIETE",
    "calculo",
]
