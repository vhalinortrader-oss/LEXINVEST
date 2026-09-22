try:
    from .market_data import get_history, get_info
except ImportError:  # pragma: no cover - suporte para execução direta
    from market_data import get_history, get_info


def asset_data(ticker: str):

    history = get_history(
        ticker,
        period="2y",
        interval="1d"
    )

    info = get_info(ticker)

    return {
        "history": history,
        "info": info,
    }


def multiple_assets(tickers):

    output = {}

    for ticker in tickers:
        output[ticker] = asset_data(ticker)

    return output
