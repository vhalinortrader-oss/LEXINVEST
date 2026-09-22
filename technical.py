import pandas as pd


def moving_average(
    prices: pd.Series,
    window: int
) -> pd.Series:

    return prices.rolling(window).mean()


def calculate_rsi(
    prices: pd.Series,
    period: int = 14
) -> pd.Series:

    delta = prices.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, pd.NA)

    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    prices: pd.Series
) -> pd.DataFrame:

    ema12 = prices.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = prices.ewm(
        span=26,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    return pd.DataFrame({
        "MACD": macd,
        "Signal": signal,
    })


def technical_report(prices: pd.Series) -> dict:

    ma20 = moving_average(prices, 20)
    ma50 = moving_average(prices, 50)

    rsi = calculate_rsi(prices)

    return {
        "MA20": ma20,
        "MA50": ma50,
        "RSI": rsi,
        "MACD": calculate_macd(prices),
    }
