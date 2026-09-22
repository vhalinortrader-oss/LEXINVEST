from __future__ import annotations

from importlib import import_module
from typing import Any

import numpy as np
import pandas as pd

from exchange_rate import get_usd_brl
from market_data import get_history
from risk import risk_report
from scoring import asset_score, classify_score
from technical import calculate_macd, calculate_rsi, moving_average

ML_FEATURES = [
    "return_1d",
    "return_5d",
    "return_10d",
    "return_20d",
    "volatility_20d",
    "rsi",
    "ma_gap",
    "ma50_gap",
    "macd_hist",
    "drawdown_20d",
]

ML_HORIZON = 5

# Horizontes de predição: pregões à frente + janelas usadas no score
INVESTMENT_HORIZONS = {
    "curto": {
        "label": "Curto prazo",
        "description": "Até ~1 mês (próximos 5–21 pregões)",
        "ml_days": 5,
        "lookback": 21,
        "momentum_key": "return_1m",
        "min_history": 60,
    },
    "medio": {
        "label": "Médio prazo",
        "description": "~3 meses (próximos 21–63 pregões)",
        "ml_days": 21,
        "lookback": 63,
        "momentum_key": "return_3m",
        "min_history": 120,
    },
    "longo": {
        "label": "Longo prazo",
        "description": "~1 ano (próximos 63–252 pregões)",
        "ml_days": 63,
        "lookback": 252,
        "momentum_key": "retorno_1y",
        "min_history": 180,
    },
}

PROFILE_RATES = {
    "Conservador": 0.06,
    "Moderado": 0.10,
    "Agressivo": 0.15,
}

PROFILE_THRESHOLDS = {
    "Conservador": {"score_min": 60, "volatilidade_max": 0.35},
    "Moderado": {"score_min": 50, "volatilidade_max": 0.55},
    "Agressivo": {"score_min": 40, "volatilidade_max": 0.75},
}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def estimate_daily_yield(prices: pd.Series) -> float:
    if prices.empty or len(prices) < 2:
        return 0.0

    start_price = safe_float(prices.iloc[0])
    end_price = safe_float(prices.iloc[-1])
    if start_price == 0:
        return 0.0

    total_return = (end_price / start_price) - 1
    days = max(len(prices) - 1, 1)
    return float((1 + total_return) ** (1 / days) - 1)


def period_return(prices: pd.Series, lookback: int) -> float:
    """Retorno percentual no lookback (em pregões). Retorna fração, não %."""
    if prices.empty or len(prices) < 2:
        return 0.0

    window = min(lookback, len(prices) - 1)
    start = safe_float(prices.iloc[-(window + 1)])
    end = safe_float(prices.iloc[-1])
    if start == 0:
        return 0.0
    return (end / start) - 1.0


def _macd_bias(prices: pd.Series) -> str:
    macd = calculate_macd(prices).dropna()
    if macd.empty:
        return "Neutro"

    last_macd = safe_float(macd["MACD"].iloc[-1])
    last_signal = safe_float(macd["Signal"].iloc[-1])
    hist = last_macd - last_signal

    if hist > 0 and last_macd > 0:
        return "Alta"
    if hist < 0 and last_macd < 0:
        return "Baixa"
    return "Neutro"


def determine_trend(prices: pd.Series) -> str:
    if prices.empty:
        return "Neutra"

    rsi_series = calculate_rsi(prices).dropna()
    ma20 = moving_average(prices, 20).dropna()
    ma50 = moving_average(prices, 50).dropna()

    last_rsi = safe_float(rsi_series.iloc[-1], 50.0) if not rsi_series.empty else 50.0
    last_price = safe_float(prices.iloc[-1])
    last_ma20 = safe_float(ma20.iloc[-1], last_price) if not ma20.empty else last_price
    last_ma50 = safe_float(ma50.iloc[-1], last_price) if not ma50.empty else last_price
    macd_bias = _macd_bias(prices)

    bullish_votes = 0
    bearish_votes = 0

    if last_ma20 > last_ma50:
        bullish_votes += 1
    elif last_ma20 < last_ma50:
        bearish_votes += 1

    if last_price > last_ma20:
        bullish_votes += 1
    elif last_price < last_ma20:
        bearish_votes += 1

    if last_rsi > 55:
        bullish_votes += 1
    elif last_rsi < 45:
        bearish_votes += 1

    if macd_bias == "Alta":
        bullish_votes += 1
    elif macd_bias == "Baixa":
        bearish_votes += 1

    if bullish_votes >= 3 and bullish_votes > bearish_votes:
        return "Alta"
    if bearish_votes >= 3 and bearish_votes > bullish_votes:
        return "Baixa"
    return "Neutra"


def build_ml_features(prices: pd.Series) -> pd.DataFrame:
    returns = prices.pct_change()
    features = pd.DataFrame(index=prices.index)
    features["return_1d"] = returns
    features["return_5d"] = prices.pct_change(5)
    features["return_10d"] = prices.pct_change(10)
    features["return_20d"] = prices.pct_change(20)
    features["volatility_20d"] = returns.rolling(20).std() * (252 ** 0.5)
    features["rsi"] = calculate_rsi(prices)

    ma20 = moving_average(prices, 20)
    ma50 = moving_average(prices, 50)
    features["ma_gap"] = prices / ma20 - 1
    features["ma50_gap"] = prices / ma50 - 1

    macd = calculate_macd(prices)
    features["macd_hist"] = macd["MACD"] - macd["Signal"]

    rolling_max = prices.rolling(20).max()
    features["drawdown_20d"] = prices / rolling_max - 1
    return features


def build_ml_dataset(prices: pd.Series, horizon: int = ML_HORIZON) -> tuple[pd.DataFrame, pd.Series]:
    features = build_ml_features(prices)

    future_return = (prices.shift(-horizon) / prices - 1).dropna()
    target = pd.Series(
        np.where(future_return.to_numpy() > 0, 1, 0),
        index=future_return.index,
        dtype="int64",
    )
    dataset = pd.concat([features, target.rename("target")], axis=1).dropna()
    return dataset[ML_FEATURES], dataset["target"]


def machine_learning_signal(prices: pd.Series, horizon: int = ML_HORIZON) -> dict:
    """Treina um modelo temporal para estimar alta nos próximos `horizon` pregões."""
    empty = {
        "probability_up": 0.5,
        "signal": "Indefinido",
        "training_rows": 0,
        "ml_accuracy": 0.0,
        "ml_horizon": horizon,
        "expected_return": 0.0,
    }
    try:
        RandomForestClassifier = import_module("sklearn.ensemble").RandomForestClassifier
        RandomForestRegressor = import_module("sklearn.ensemble").RandomForestRegressor
        Pipeline = import_module("sklearn.pipeline").Pipeline
        StandardScaler = import_module("sklearn.preprocessing").StandardScaler
    except ImportError:
        return empty

    features = build_ml_features(prices)
    future_return = (prices.shift(-horizon) / prices - 1).dropna()
    if future_return.empty:
        return empty

    target_cls = pd.Series(
        np.where(future_return.to_numpy() > 0, 1, 0),
        index=future_return.index,
        dtype="int64",
    )
    target_reg = future_return.rename("future_return")
    dataset = pd.concat(
        [features, target_cls.rename("target"), target_reg],
        axis=1,
    ).dropna()

    if len(dataset) < 60 or dataset["target"].nunique() < 2:
        return empty

    feature_frame = dataset[ML_FEATURES]
    class_target = dataset["target"]
    reg_target = dataset["future_return"]

    split = int(len(feature_frame) * 0.8)
    train_features = feature_frame.iloc[:split]
    train_target = class_target.iloc[:split]
    test_features = feature_frame.iloc[split:]
    test_target = class_target.iloc[split:]
    train_reg = reg_target.iloc[:split]

    if train_target.nunique() < 2:
        return empty

    classifier = Pipeline([
        ("scale", StandardScaler()),
        ("classifier", RandomForestClassifier(
            n_estimators=120,
            max_depth=5,
            min_samples_leaf=4,
            random_state=42,
            class_weight="balanced",
        )),
    ])
    classifier.fit(train_features, train_target)

    regressor = Pipeline([
        ("scale", StandardScaler()),
        ("regressor", RandomForestRegressor(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=4,
            random_state=42,
        )),
    ])
    regressor.fit(train_features, train_reg)

    ml_accuracy = 0.0
    if len(test_features) >= 5 and test_target.nunique() >= 1:
        predictions = classifier.predict(test_features)
        ml_accuracy = float((predictions == test_target.to_numpy()).mean())

    latest_features = build_ml_features(prices).dropna()[ML_FEATURES].iloc[[-1]]
    latest_probability = float(classifier.predict_proba(latest_features)[0, 1])
    expected_return = float(regressor.predict(latest_features)[0])

    if latest_probability >= 0.60:
        signal = "Probabilidade de alta"
    elif latest_probability <= 0.40:
        signal = "Probabilidade de baixa"
    else:
        signal = "Sinal neutro"

    return {
        "probability_up": round(latest_probability, 4),
        "signal": signal,
        "training_rows": len(train_features),
        "ml_accuracy": round(ml_accuracy, 4),
        "ml_horizon": horizon,
        "expected_return": round(expected_return, 6),
    }


def _technical_snapshot(prices: pd.Series) -> dict:
    last_price = safe_float(prices.iloc[-1])
    rsi_series = calculate_rsi(prices).dropna()
    ma20 = moving_average(prices, 20).dropna()
    ma50 = moving_average(prices, 50).dropna()

    last_rsi = safe_float(rsi_series.iloc[-1], 50.0) if not rsi_series.empty else 50.0
    last_ma20 = safe_float(ma20.iloc[-1], last_price) if not ma20.empty else last_price
    last_ma50 = safe_float(ma50.iloc[-1], last_price) if not ma50.empty else last_price

    ma20_distance = ((last_price / last_ma20) - 1) * 100 if last_ma20 else 0.0
    ma50_distance = ((last_price / last_ma50) - 1) * 100 if last_ma50 else 0.0

    return {
        "rsi": round(last_rsi, 2),
        "macd_bias": _macd_bias(prices),
        "ma20_distance_pct": round(ma20_distance, 2),
        "ma50_distance_pct": round(ma50_distance, 2),
    }


def _compute_confidence(
    data_points: int,
    ml_signal: dict,
    trend: str,
    macd_bias: str,
) -> float:
    data_score = min(data_points / 252.0, 1.0) * 40.0

    accuracy = safe_float(ml_signal.get("ml_accuracy", 0.0))
    training_rows = int(ml_signal.get("training_rows", 0))
    ml_score = 0.0
    if training_rows > 0:
        ml_score = (0.5 + accuracy * 0.5) * 35.0
    else:
        ml_score = 10.0

    alignment = 15.0
    if trend == "Alta" and macd_bias == "Alta":
        alignment = 25.0
    elif trend == "Baixa" and macd_bias == "Baixa":
        alignment = 25.0
    elif trend == "Neutra" or macd_bias == "Neutro":
        alignment = 18.0

    return round(min(100.0, data_score + ml_score + alignment), 1)


def _build_rationale(
    ticker: str,
    score: float,
    trend: str,
    volatilidade: float,
    drawdown: float,
    recommendation: str,
    ml_signal: dict,
) -> str:
    ml_part = (
        f"sinal ML {ml_signal.get('signal', 'Indefinido')} "
        f"(prob. alta {safe_float(ml_signal.get('probability_up', 0.5)):.0%})"
    )
    return (
        f"{ticker}: score {score:.1f} com tendência {trend.lower()}, "
        f"volatilidade anual {volatilidade:.1%} e drawdown máximo {drawdown:.1%}. "
        f"Indicação {recommendation} com base em {ml_part}."
    )


def _empty_horizon_prediction(horizon_key: str) -> dict:
    meta = INVESTMENT_HORIZONS[horizon_key]
    return {
        "horizon": horizon_key,
        "label": meta["label"],
        "description": meta["description"],
        "score": 0.0,
        "expected_return_pct": 0.0,
        "probability_up": 0.5,
        "signal": "Indefinido",
        "indication": "Sem dados",
        "ml_accuracy": 0.0,
        "ml_horizon": meta["ml_days"],
        "momentum_pct": 0.0,
        "rationale": "Dados insuficientes para predição neste horizonte.",
    }


def score_horizon_opportunity(
    analysis: dict,
    ml_signal: dict,
    horizon_key: str,
    profile: str = "Moderado",
) -> dict:
    """Pontua atratividade e rentabilidade esperada em um horizonte."""
    meta = INVESTMENT_HORIZONS[horizon_key]
    momentum_key = meta["momentum_key"]
    momentum_pct = safe_float(analysis.get(momentum_key, 0.0))
    volatility = safe_float(analysis.get("volatilidade", 0.0))
    drawdown = abs(safe_float(analysis.get("drawdown_maximo", 0.0)))
    sharpe = safe_float(analysis.get("sharpe", 0.0))
    trend = analysis.get("trend", "Neutra")
    confidence = safe_float(analysis.get("confidence", 50.0)) / 100.0

    probability_up = safe_float(ml_signal.get("probability_up", 0.5))
    expected_return = safe_float(ml_signal.get("expected_return", 0.0))
    ml_accuracy = safe_float(ml_signal.get("ml_accuracy", 0.0))

    # Combina retorno histórico do lookback com retorno esperado pelo regressor
    hist_fraction = momentum_pct / 100.0
    blended_return = 0.45 * expected_return + 0.55 * hist_fraction

    base = (
        probability_up * 35.0
        + max(blended_return, -0.5) * 100.0 * 0.25
        + max(sharpe, -1.0) * 8.0
        + confidence * 15.0
        + ml_accuracy * 10.0
    )

    if trend == "Alta":
        base += 8.0
    elif trend == "Baixa":
        base -= 12.0

    if profile == "Conservador":
        base -= volatility * 35.0 + drawdown * 25.0
    elif profile == "Agressivo":
        base += max(blended_return, 0.0) * 40.0 - drawdown * 8.0
    else:
        base -= volatility * 18.0 + drawdown * 12.0

    score = round(max(0.0, min(100.0, base)), 2)

    if score >= 70 and probability_up >= 0.55 and blended_return > 0:
        indication = "Priorizar"
    elif score >= 55 and blended_return >= 0:
        indication = "Favorável"
    elif score >= 40:
        indication = "Neutro"
    else:
        indication = "Desfavorável"

    rationale = (
        f"{meta['label']}: score {score:.1f}, retorno esperado {blended_return * 100:.2f}%, "
        f"prob. de alta {probability_up:.0%}, momentum {momentum_pct:.2f}%. "
        f"Indicação: {indication}."
    )

    return {
        "horizon": horizon_key,
        "label": meta["label"],
        "description": meta["description"],
        "score": score,
        "expected_return_pct": round(blended_return * 100, 2),
        "probability_up": round(probability_up, 4),
        "signal": ml_signal.get("signal", "Indefinido"),
        "indication": indication,
        "ml_accuracy": round(ml_accuracy, 4),
        "ml_horizon": ml_signal.get("ml_horizon", meta["ml_days"]),
        "momentum_pct": round(momentum_pct, 2),
        "rationale": rationale,
    }


def predict_asset_horizons(
    ticker: str,
    prices: pd.Series | None = None,
    analysis: dict | None = None,
    profile: str = "Moderado",
) -> dict:
    """Predição de IA para curto, médio e longo prazo em um ativo."""
    if analysis is not None and analysis.get("horizon_predictions"):
        return analysis["horizon_predictions"]

    if analysis is None:
        return analyze_asset_ai(ticker, profile=profile).get(
            "horizon_predictions",
            {key: _empty_horizon_prediction(key) for key in INVESTMENT_HORIZONS},
        )

    if prices is None:
        history = get_history(ticker, period="2y", interval="1d")
        if history is None or history.empty:
            return {key: _empty_horizon_prediction(key) for key in INVESTMENT_HORIZONS}
        prices = pd.to_numeric(history["Close"], errors="coerce").dropna()

    if prices.empty or len(prices) < 30 or safe_float(analysis.get("score", 0)) <= 0:
        return {key: _empty_horizon_prediction(key) for key in INVESTMENT_HORIZONS}

    predictions: dict[str, dict] = {}
    for key, meta in INVESTMENT_HORIZONS.items():
        if len(prices) < meta["min_history"]:
            predictions[key] = _empty_horizon_prediction(key)
            continue
        ml_signal = machine_learning_signal(prices, horizon=meta["ml_days"])
        predictions[key] = score_horizon_opportunity(analysis, ml_signal, key, profile)

    return predictions


def _best_horizon_pick(rows: list[dict], prefer_profit: bool) -> dict | None:
    if not rows:
        return None
    if prefer_profit:
        return max(rows, key=lambda item: (item["expected_return_pct"], item["score"]))
    return max(rows, key=lambda item: (item["score"], item["expected_return_pct"]))


def predict_best_investments(
    selected_assets: list[str],
    profile: str = "Moderado",
    top_n: int = 3,
) -> dict:
    """Indica os melhores e mais rentáveis investimentos por horizonte."""
    profile_name = profile if profile in PROFILE_THRESHOLDS else "Moderado"
    analyses = [
        analyze_asset_ai(ticker, profile=profile_name)
        for ticker in selected_assets
        if ticker
    ]
    analyses = [item for item in analyses if item.get("score", 0) > 0]

    empty = {
        "profile": profile_name,
        "horizons": {},
        "summary": "Não foi possível gerar predições: dados insuficientes.",
        "best_overall": None,
    }
    if not analyses:
        return empty

    horizon_boards: dict[str, dict] = {}
    all_scored: list[dict] = []

    for analysis in analyses:
        ticker = analysis["ticker"]
        predictions = analysis.get("horizon_predictions") or predict_asset_horizons(
            ticker, analysis=analysis, profile=profile_name
        )

        for key, pred in predictions.items():
            if pred.get("indication") == "Sem dados" or pred.get("score", 0) <= 0:
                continue
            row = {
                "ticker": ticker,
                "horizon": key,
                "label": pred["label"],
                "score": pred["score"],
                "expected_return_pct": pred["expected_return_pct"],
                "probability_up": pred["probability_up"],
                "indication": pred["indication"],
                "signal": pred["signal"],
                "ml_accuracy": pred["ml_accuracy"],
                "momentum_pct": pred["momentum_pct"],
                "rationale": pred["rationale"],
                "volatilidade": analysis.get("volatilidade", 0.0),
                "safety": analysis.get("safety", "Baixa"),
                "trend": analysis.get("trend", "Neutra"),
                "recommendation": analysis.get("recommendation", ""),
            }
            all_scored.append(row)

    for key, meta in INVESTMENT_HORIZONS.items():
        rows = [row for row in all_scored if row["horizon"] == key]
        ranked_best = sorted(rows, key=lambda item: item["score"], reverse=True)[:top_n]
        ranked_profit = sorted(
            rows,
            key=lambda item: item["expected_return_pct"],
            reverse=True,
        )[:top_n]
        best = _best_horizon_pick(rows, prefer_profit=False)
        most_profitable = _best_horizon_pick(rows, prefer_profit=True)

        horizon_boards[key] = {
            "label": meta["label"],
            "description": meta["description"],
            "best": best,
            "most_profitable": most_profitable,
            "top_by_score": ranked_best,
            "top_by_return": ranked_profit,
        }

    favorable = [
        row for row in all_scored
        if row["indication"] in {"Priorizar", "Favorável"}
    ]
    best_overall = _best_horizon_pick(favorable or all_scored, prefer_profit=False)

    parts = []
    for key in ("curto", "medio", "longo"):
        board = horizon_boards.get(key) or {}
        best = board.get("best")
        profit = board.get("most_profitable")
        if best and profit:
            parts.append(
                f"{board['label']}: melhor {best['ticker']} (score {best['score']:.1f}); "
                f"mais rentável {profit['ticker']} "
                f"(retorno esp. {profit['expected_return_pct']:.2f}%)"
            )

    summary = (
        "Predição da IA por horizonte — " + "; ".join(parts) + ". "
        "Conteúdo educacional; não garante rentabilidade futura."
        if parts
        else empty["summary"]
    )

    return {
        "profile": profile_name,
        "horizons": horizon_boards,
        "summary": summary,
        "best_overall": best_overall,
        "analyses": analyses,
    }


def _empty_asset_result(ticker: str) -> dict:
    return {
        "ticker": ticker,
        "score": 0.0,
        "recommendation": "Dados insuficientes",
        "trend": "Neutra",
        "volatilidade": 0.0,
        "retorno_1y": 0.0,
        "return_1m": 0.0,
        "return_3m": 0.0,
        "return_6m": 0.0,
        "sharpe": 0.0,
        "daily_yield": 0.0,
        "drawdown_maximo": 0.0,
        "retorno_anualizado": 0.0,
        "rsi": 50.0,
        "macd_bias": "Neutro",
        "ma20_distance_pct": 0.0,
        "ma50_distance_pct": 0.0,
        "confidence": 0.0,
        "rationale": f"{ticker}: dados insuficientes para análise quantitativa.",
        "classification": "Sem dados",
        "safety": "Baixa",
        "ml_probability_up": 0.5,
        "ml_signal": "Indefinido",
        "ml_training_rows": 0,
        "ml_accuracy": 0.0,
        "ml_horizon": ML_HORIZON,
        "ml_expected_return": 0.0,
        "profile_score": 0.0,
        "horizon_predictions": {
            key: _empty_horizon_prediction(key) for key in INVESTMENT_HORIZONS
        },
        "best_horizon": None,
    }


def analyze_asset_ai(ticker: str, profile: str = "Moderado") -> dict:
    # Preferir 2y para alimentar ML de médio/longo prazo
    history = get_history(ticker, period="2y", interval="1d")
    empty_result = _empty_asset_result(ticker)

    if history is None or history.empty:
        return empty_result

    close = pd.to_numeric(history["Close"], errors="coerce").dropna()
    if close.empty or len(close) < 10:
        return empty_result

    # Janela de 1 ano para métricas anuais clássicas
    close_1y = close.iloc[-252:] if len(close) > 252 else close

    retorno = safe_float((close_1y.iloc[-1] / close_1y.iloc[0]) - 1)
    return_1m = period_return(close, 21)
    return_3m = period_return(close, 63)
    return_6m = period_return(close, 126)

    risk = risk_report(close_1y)
    volatilidade = safe_float(risk.get("volatilidade_anual", 0.0))
    sharpe = safe_float(risk.get("sharpe", 0.0))
    drawdown = safe_float(risk.get("drawdown_maximo", 0.0))
    retorno_anualizado = safe_float(risk.get("retorno_anualizado_estimado", 0.0))

    base_score = asset_score(retorno, min(volatilidade, 1.0), sharpe)
    classification = classify_score(base_score)
    trend = determine_trend(close_1y)
    tech = _technical_snapshot(close_1y)
    daily_yield = estimate_daily_yield(close_1y)
    ml_signal = machine_learning_signal(close, horizon=ML_HORIZON)
    ml_score = ml_signal["probability_up"] * 100
    score = round(base_score * 0.7 + ml_score * 0.3, 2)

    if score >= 75 and trend != "Baixa" and sharpe > 0 and ml_signal["probability_up"] >= 0.5:
        recommendation = "Comprar"
        safety = "Alta"
    elif score >= 55 and trend != "Baixa":
        recommendation = "Acompanhar"
        safety = "Média"
    elif score >= 40 and sharpe > -1:
        recommendation = "Aguardar"
        safety = "Moderada"
    else:
        recommendation = "Evitar"
        safety = "Baixa"

    confidence = _compute_confidence(len(close_1y), ml_signal, trend, tech["macd_bias"])
    rationale = _build_rationale(
        ticker, score, trend, volatilidade, drawdown, recommendation, ml_signal
    )

    partial = {
        "ticker": ticker,
        "score": round(score, 2),
        "recommendation": recommendation,
        "trend": trend,
        "volatilidade": round(volatilidade, 4),
        "retorno_1y": round(retorno * 100, 2),
        "return_1m": round(return_1m * 100, 2),
        "return_3m": round(return_3m * 100, 2),
        "return_6m": round(return_6m * 100, 2),
        "sharpe": round(sharpe, 2),
        "daily_yield": round(daily_yield * 100, 4),
        "drawdown_maximo": round(drawdown, 4),
        "retorno_anualizado": round(retorno_anualizado * 100, 2),
        "rsi": tech["rsi"],
        "macd_bias": tech["macd_bias"],
        "ma20_distance_pct": tech["ma20_distance_pct"],
        "ma50_distance_pct": tech["ma50_distance_pct"],
        "confidence": confidence,
        "rationale": rationale,
        "classification": classification,
        "safety": safety,
        "ml_probability_up": ml_signal["probability_up"],
        "ml_signal": ml_signal["signal"],
        "ml_training_rows": ml_signal["training_rows"],
        "ml_accuracy": ml_signal.get("ml_accuracy", 0.0),
        "ml_horizon": ml_signal.get("ml_horizon", ML_HORIZON),
        "ml_expected_return": round(safe_float(ml_signal.get("expected_return", 0.0)) * 100, 4),
        "profile_score": round(score, 2),
    }

    horizon_predictions: dict[str, dict] = {}
    for key, meta in INVESTMENT_HORIZONS.items():
        if len(close) < meta["min_history"]:
            horizon_predictions[key] = _empty_horizon_prediction(key)
            continue
        hz_signal = (
            ml_signal
            if meta["ml_days"] == ML_HORIZON
            else machine_learning_signal(close, horizon=meta["ml_days"])
        )
        horizon_predictions[key] = score_horizon_opportunity(
            partial, hz_signal, key, profile
        )

    best_horizon = max(
        horizon_predictions.values(),
        key=lambda item: (item["score"], item["expected_return_pct"]),
    )

    partial["horizon_predictions"] = horizon_predictions
    partial["best_horizon"] = best_horizon["horizon"] if best_horizon["score"] > 0 else None
    return partial


def profile_adjusted_score(item: dict, profile: str) -> float:
    """Ajusta o score conforme o perfil do investidor."""
    base = safe_float(item.get("score", 0.0))
    volatility = safe_float(item.get("volatilidade", 0.0))
    drawdown = abs(safe_float(item.get("drawdown_maximo", 0.0)))
    sharpe = safe_float(item.get("sharpe", 0.0))
    momentum = safe_float(item.get("return_3m", 0.0)) / 100.0
    confidence = safe_float(item.get("confidence", 50.0)) / 100.0

    if profile == "Conservador":
        adjusted = (
            base
            - volatility * 40.0
            - drawdown * 30.0
            + max(sharpe, 0.0) * 5.0
            + confidence * 10.0
        )
    elif profile == "Agressivo":
        adjusted = (
            base
            + momentum * 25.0
            + max(sharpe, 0.0) * 8.0
            + safe_float(item.get("ml_probability_up", 0.5)) * 15.0
            - drawdown * 10.0
        )
    else:
        adjusted = (
            base
            + max(sharpe, 0.0) * 6.0
            + momentum * 10.0
            - volatility * 15.0
            - drawdown * 15.0
            + confidence * 8.0
        )

    return round(max(0.0, min(100.0, adjusted)), 2)


def build_allocation(top: list[dict], profile: str) -> list[dict]:
    """Gera pesos percentuais normalizados para os top ativos."""
    if not top:
        return []

    n = len(top)
    if profile == "Conservador":
        # Mais uniforme: evita concentração extrema
        raw = np.linspace(1.2, 1.0, n)
    elif profile == "Agressivo":
        raw = np.linspace(2.2, 0.6, n)
    else:
        raw = np.linspace(1.6, 0.8, n)

    scores = np.array([max(safe_float(item.get("profile_score", item.get("score", 1.0))), 0.1) for item in top])
    blended = raw * scores
    weights = blended / blended.sum()

    allocation = []
    for item, weight in zip(top, weights):
        allocation.append({
            "ticker": item["ticker"],
            "weight": round(float(weight), 4),
            "weight_pct": round(float(weight) * 100, 2),
            "score": item.get("score", 0.0),
            "recommendation": item.get("recommendation", ""),
        })
    return allocation


def build_ai_recommendation(profile: str, selected_assets: list[str], capital: float = 20000.0) -> dict:
    profile_name = profile if profile in PROFILE_THRESHOLDS else "Moderado"
    config = PROFILE_THRESHOLDS[profile_name]

    analyses = [analyze_asset_ai(ticker) for ticker in selected_assets if ticker]
    analyses = [item for item in analyses if item.get("score", 0) > 0]

    empty_payload = {
        "profile": profile_name,
        "best": None,
        "top": [],
        "summary": "Nenhum ativo foi avaliado com dados suficientes para recomendar uma posição.",
        "capital": capital,
        "ranked": [],
        "allocation": [],
        "diversification_note": "",
        "avg_volatility": 0.0,
        "monthly_br": 0.0,
        "monthly_usd": 0.0,
        "fx_rate": round(get_usd_brl() or 5.4, 2),
    }

    if not analyses:
        return empty_payload

    for item in analyses:
        item["profile_score"] = profile_adjusted_score(item, profile_name)

    filtered = [
        item for item in analyses
        if item["score"] >= config["score_min"]
        and item["volatilidade"] <= config["volatilidade_max"]
    ]
    pool = filtered if filtered else analyses
    ranked = sorted(pool, key=lambda item: item["profile_score"], reverse=True)
    best = ranked[0]
    top = ranked[:5]

    safe_assets = [item for item in top if item["safety"] in {"Alta", "Média"}]
    suggested = safe_assets[0] if safe_assets else best

    allocation = build_allocation(top, profile_name)
    diversification_note = ""
    if allocation and allocation[0]["weight_pct"] > 50:
        diversification_note = (
            f"Atenção: {allocation[0]['ticker']} concentra {allocation[0]['weight_pct']:.1f}% "
            "da alocação sugerida. Considere diversificar para reduzir risco idiossincrático."
        )

    weight_map = {row["ticker"]: row["weight"] for row in allocation}
    weighted_daily = sum(
        safe_float(item.get("daily_yield", 0.0)) / 100.0 * weight_map.get(item["ticker"], 0.0)
        for item in top
    )
    monthly_factor = (1 + weighted_daily) ** 21 - 1
    usd_rate = get_usd_brl() or 5.4
    monthly_rent = capital * monthly_factor
    monthly_in_usd = (capital / usd_rate) * monthly_factor

    avg_volatility = float(np.mean([safe_float(item.get("volatilidade", 0.0)) for item in top])) if top else 0.0
    weights_text = ", ".join(f"{row['ticker']} {row['weight_pct']:.1f}%" for row in allocation[:3])

    summary = (
        f"Para o perfil {profile_name}, o destaque é {suggested['ticker']} "
        f"(score {suggested['score']}, indicação {suggested['recommendation']}). "
        f"Alocação sugerida: {weights_text}. "
        f"Volatilidade média da seleção: {avg_volatility:.1%}. "
        f"{suggested.get('rationale', '')} "
        "Conteúdo educacional — não constitui recomendação individual de investimento."
    )
    if diversification_note:
        summary = f"{summary} {diversification_note}"

    return {
        "profile": profile_name,
        "best": suggested,
        "top": top,
        "summary": summary,
        "capital": capital,
        "monthly_br": round(monthly_rent, 2),
        "monthly_usd": round(monthly_in_usd, 2),
        "fx_rate": round(usd_rate, 2),
        "ranked": ranked,
        "allocation": allocation,
        "diversification_note": diversification_note,
        "avg_volatility": round(avg_volatility, 4),
    }


def build_projection_plan(
    principal: float,
    monthly_contribution: float,
    years: int = 10,
    annual_rate: float | None = None,
    profile: str = "Moderado",
) -> list[dict]:
    from projections import projection_table

    profile_name = profile if profile in PROFILE_RATES else "Moderado"
    rate = PROFILE_RATES[profile_name] if annual_rate is None else float(annual_rate)
    return projection_table(principal, rate, monthly_contribution, years)
