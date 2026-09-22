def fundamental_report(info: dict) -> dict:

    fields = [
        "marketCap",
        "trailingPE",
        "forwardPE",
        "priceToBook",
        "dividendYield",
        "returnOnEquity",
        "profitMargins",
        "debtToEquity",
        "revenueGrowth",
        "earningsGrowth",
    ]

    return {
        field: info.get(field)
        for field in fields
    }


def fundamental_summary(info: dict) -> str:

    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    margin = info.get("profitMargins")

    return (
        f"P/L: {pe}\n"
        f"ROE: {roe}\n"
        f"Margem líquida: {margin}"
    )
