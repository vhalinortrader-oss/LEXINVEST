import pandas as pd
import numpy as np


def _numeric_column(positions: pd.DataFrame, column: str) -> pd.Series:
    if column not in positions.columns:
        raise ValueError(f"A carteira precisa da coluna '{column}'.")

    values = pd.to_numeric(positions[column], errors="coerce")
    if values.isna().any():
        raise ValueError(f"A coluna '{column}' contém valores inválidos.")
    return values


def portfolio_value(
    positions: pd.DataFrame
) -> float:

    quantities = _numeric_column(positions, "Quantidade")
    prices = _numeric_column(positions, "Preço")
    return float((quantities * prices).sum())


def portfolio_weights(
    positions: pd.DataFrame
) -> pd.DataFrame:

    data = positions.copy()

    quantities = _numeric_column(data, "Quantidade")
    prices = _numeric_column(data, "Preço")
    data["Valor"] = quantities * prices

    total = data["Valor"].sum()

    if total == 0:
        data["Peso"] = 0.0
    else:
        data["Peso"] = data["Valor"] / total

    return data


def portfolio_return(
    positions: pd.DataFrame
) -> float:

    data = positions.copy()
    quantities = _numeric_column(data, "Quantidade")

    if {"Preço Atual", "Preço Médio"}.issubset(data.columns):
        current_prices = _numeric_column(data, "Preço Atual")
        average_prices = _numeric_column(data, "Preço Médio")
    elif "Preço" in data.columns:
        current_prices = _numeric_column(data, "Preço")
        average_prices = current_prices
    else:
        raise ValueError("A carteira precisa de 'Preço' ou de 'Preço Atual' e 'Preço Médio'.")

    data["Resultado"] = quantities * (current_prices - average_prices)
    invested = (quantities * average_prices).sum()

    if invested == 0:
        return 0.0

    return float(
        data["Resultado"].sum() / invested
    )


def portfolio_volatility(
    returns: pd.DataFrame,
    weights: np.ndarray
) -> float:

    numeric_returns = returns.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    if numeric_returns.empty:
        return 0.0

    weights_array = np.asarray(weights, dtype=float)
    if weights_array.ndim != 1 or len(weights_array) != numeric_returns.shape[1]:
        raise ValueError("O número de pesos deve corresponder ao número de ativos.")

    if not np.isfinite(weights_array).all():
        raise ValueError("Os pesos devem conter apenas números finitos.")

    covariance = numeric_returns.cov() * 252

    variance = (
        weights_array.T
        @ covariance.values
        @ weights_array
    )

    return float(np.sqrt(max(variance, 0.0)))
