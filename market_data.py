import yfinance as yf
import pandas as pd


def get_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
) -> pd.DataFrame:

    asset = yf.Ticker(ticker)

    data = asset.history(
        period=period,
        interval=interval,
        auto_adjust=True
    )

    return data


def get_info(ticker: str) -> dict:

    asset = yf.Ticker(ticker)

    try:
        return asset.info
    except Exception:
        return {}


def get_price(ticker: str):

    data = get_history(
        ticker,
        period="5d",
        interval="1d"
    )

    if data.empty:
        return None

    return float(data["Close"].iloc[-1])
