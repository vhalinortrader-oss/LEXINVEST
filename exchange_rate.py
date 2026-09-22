import yfinance as yf


def get_usd_brl():

    ticker = yf.Ticker("BRL=X")

    data = ticker.history(
        period="5d",
        interval="1d"
    )

    if data.empty:
        return None

    return float(data["Close"].iloc[-1])


def convert_brl_to_usd(
    value_brl: float,
    exchange_rate: float
) -> float:

    if exchange_rate == 0:
        return 0.0

    return value_brl / exchange_rate


def convert_usd_to_brl(
    value_usd: float,
    exchange_rate: float
) -> float:

    return value_usd * exchange_rate
