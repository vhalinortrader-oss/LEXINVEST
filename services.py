try:
    from .market_data import *
    from .exchange_rate import *
    from .investment_data import *
except ImportError:  # pragma: no cover - suporte para execução direta
    from market_data import *
    from exchange_rate import *
    from investment_data import *
