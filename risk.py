import numpy as np
import pandas as pd


def daily_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def annualized_volatility(prices: pd.Series) -> float:
    returns = daily_returns(prices)

    if returns.empty:
        return 0.0

    return float(returns.std() * np.sqrt(252))


def maximum_drawdown(prices: pd.Series) -> float:
    if prices.empty:
        return 0.0

    cumulative_max = prices.cummax()
    drawdown = prices / cumulative_max - 1

    return float(drawdown.min())


def sharpe_ratio(
    prices: pd.Series,
    risk_free_rate: float = 0.0
) -> float:

    returns = daily_returns(prices)

    if returns.empty or returns.std() == 0:
        return 0.0

    daily_rf = risk_free_rate / 252

    excess_returns = returns - daily_rf

    return float(
        np.sqrt(252)
        * excess_returns.mean()
        / returns.std()
    )


def beta(
    asset_prices: pd.Series,
    benchmark_prices: pd.Series
) -> float:

    data = pd.concat(
        [
            daily_returns(asset_prices),
            daily_returns(benchmark_prices)
        ],
        axis=1
    ).dropna()

    if len(data) < 2:
        return 0.0

    covariance = data.iloc[:, 0].cov(data.iloc[:, 1])
    variance = data.iloc[:, 1].var()

    if variance == 0:
        return 0.0

    return float(covariance / variance)


def risk_report(prices: pd.Series) -> dict:

    returns = daily_returns(prices)

    annual_return = 0.0

    if not returns.empty:
        annual_return = float(
            (1 + returns.mean()) ** 252 - 1
        )

    return {
        "volatilidade_anual": annualized_volatility(prices),
        "drawdown_maximo": maximum_drawdown(prices),
        "sharpe": sharpe_ratio(prices),
        "retorno_anualizado_estimado": annual_return,
    }
