import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "LEXINVEST"

DEFAULT_CURRENCY = "BRL"

INITIAL_CAPITAL = float(
    os.getenv("INITIAL_CAPITAL", "100")
)

DATA_DIR = "data"

RISK_FREE_RATE_BR = float(
    os.getenv("RISK_FREE_RATE_BR", "0.10")
)

RISK_FREE_RATE_US = float(
    os.getenv("RISK_FREE_RATE_US", "0.04")
)

YAHOO_PERIOD = os.getenv(
    "YAHOO_PERIOD",
    "1y"
)

YAHOO_INTERVAL = os.getenv(
    "YAHOO_INTERVAL",
    "1d"
)

# Ativos de exemplo
BRAZIL_ASSETS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BOVA11.SA",
    "IVVB11.SA",
]

US_ASSETS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "SPY",
    "QQQ",
]

DEFAULT_ASSETS = BRAZIL_ASSETS + US_ASSETS
