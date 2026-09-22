"""Exposição pública dos modelos do projeto LEXINVEST.

Este módulo centraliza funções reutilizáveis de risco, projeções e
pontuação qualitativa dos ativos para uso nos dashboards e scripts do
projeto.
"""

try:
    from .risk import *
    from .projections import *
    from .scoring import *
except ImportError:  # pragma: no cover - suporte para execução direta
    from risk import *
    from projections import *
    from scoring import *

__all__ = [
    "daily_returns",
    "annualized_volatility",
    "maximum_drawdown",
    "sharpe_ratio",
    "beta",
    "risk_report",
    "compound_interest",
    "projection_table",
    "monthly_income",
    "scenario_projection",
    "normalize",
    "asset_score",
    "classify_score",
]


def model_summary(prices):
    """Agrupa as métricas principais de risco e projeção em um único dicionário."""
    risk = risk_report(prices)
    return {
        "volatilidade_anual": risk.get("volatilidade_anual", 0.0),
        "drawdown_maximo": risk.get("drawdown_maximo", 0.0),
        "sharpe": risk.get("sharpe", 0.0),
        "retorno_anualizado_estimado": risk.get("retorno_anualizado_estimado", 0.0),
    }
