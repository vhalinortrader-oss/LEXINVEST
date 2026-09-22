"""
Módulo de utilitários para cálculo de variação percentual e métricas relacionadas.

Inclui suporte a números float, int e Decimal, além de validações de entrada
e funções auxiliares (variação absoluta, razão e formatação).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional, Union

Number = Union[int, float, Decimal]


def percentage_change(
    initial: Number,
    final: Number,
    *,
    as_fraction: bool = False,
    raise_on_zero: bool = True,
) -> Optional[Decimal]:
    """
    Calcula a variação percentual entre dois valores.

    Fórmula:
        ((final - initial) / |initial|) * 100

    O uso de `|initial|` garante que o **sinal** da variação reflita apenas
    a direção (aumento/diminuição), independentemente do sinal do valor base.

    Parameters
    ----------
    initial : Number
        Valor de referência (base). Pode ser int, float ou Decimal.
    final : Number
        Valor final (novo valor).
    as_fraction : bool, optional
        Se True, retorna a variação como fração (ex.: 0.25 em vez de 25.0).
        Padrão: False.
    raise_on_zero : bool, optional
        Se True, levanta ZeroDivisionError quando `initial == 0`.
        Se False, retorna None nesse caso. Padrão: True.

    Returns
    -------
    Decimal | None
        A variação percentual (ou fração, se `as_fraction=True`).
        Retorna None apenas se `initial == 0` e `raise_on_zero=False`.

    Raises
    ------
    TypeError
        Se `initial` ou `final` não forem numéricos.
    ZeroDivisionError
        Se `initial == 0` e `raise_on_zero=True`.

    Examples
    --------
    >>> percentage_change(100, 150)
    Decimal('50')
    >>> percentage_change(100, 50)
    Decimal('-50')
    >>> percentage_change(0, 100, raise_on_zero=False) is None
    True
    >>> percentage_change(200, 250, as_fraction=True)
    Decimal('0.25')
    """
    # --- Validação de tipos ---
    for name, value in (("initial", initial), ("final", final)):
        if not isinstance(value, (int, float, Decimal)):
            raise TypeError(
                f"'{name}' deve ser int, float ou Decimal, "
                f"recebido {type(value).__name__}"
            )
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise ValueError(f"'{name}' não pode ser NaN ou infinito")

    # --- Conversão para Decimal (evita erros de ponto flutuante) ---
    try:
        initial_d = Decimal(str(initial))
        final_d = Decimal(str(final))
    except InvalidOperation as exc:
        raise ValueError(f"Não foi possível converter valores para Decimal: {exc}") from exc

    # --- Caso especial: divisão por zero ---
    if initial_d == 0:
        if raise_on_zero:
            raise ZeroDivisionError(
                "Não é possível calcular variação percentual com 'initial' igual a zero."
            )
        return None

    # --- Cálculo ---
    change = (final_d - initial_d) / abs(initial_d)
    return change if as_fraction else change * Decimal("100")


def absolute_change(initial: Number, final: Number) -> Decimal:
    """Retorna a variação absoluta (final - initial)."""
    return Decimal(str(final)) - Decimal(str(initial))


def ratio(initial: Number, final: Number) -> Decimal:
    """
    Retorna a razão final / initial (ex.: 1.5 significa 150% do valor base).

    Raises
    ------
    ZeroDivisionError
        Se `initial == 0`.
    """
    initial_d = Decimal(str(initial))
    if initial_d == 0:
        raise ZeroDivisionError("'initial' não pode ser zero.")
    return Decimal(str(final)) / initial_d


def format_percentage(
    value: Number,
    *,
    decimals: int = 2,
    with_sign: bool = True,
) -> str:
    """
    Formata um número como percentual legível (ex.: '+12.34%').

    Parameters
    ----------
    value : Number
        Valor percentual (ex.: 12.34 para 12.34%).
    decimals : int, optional
        Casas decimais. Padrão: 2.
    with_sign : bool, optional
        Se True, prefixa '+' em valores positivos. Padrão: True.

    Returns
    -------
    str
    """
    d = Decimal(str(value))
    sinal = "+" if with_sign and d > 0 else ""
    quant = Decimal(1).scaleb(-decimals)
    return f"{sinal}{d.quantize(quant)}%"