"""LEXINVEST — dashboard de análise quantitativa de investimentos.

Este arquivo integra módulos já existentes no projeto para montar uma
aplicação funcional em Streamlit com dados de mercado, indicadores técnicos,
projeções, risco e instituições.
"""

from __future__ import annotations

import base64
import io
import math
import struct
import wave
from datetime import datetime, timedelta, timezone
from typing import Iterable

import pandas as pd
import streamlit as st

from ai_investment import analyze_asset_ai, build_ai_recommendation, build_projection_plan
from config import DEFAULT_ASSETS
from exchange_rate import get_usd_brl
from institutions import brazil_institutions, safe_institutions, us_institutions
from market_data import get_history
from portfolio import portfolio_return, portfolio_value, portfolio_weights
from projections import scenario_projection
from risk import risk_report
from scoring import asset_score, classify_score
from technical import calculate_macd, calculate_rsi, moving_average

APP_TITLE = "LEXINVEST"
APP_ICON = "📈"
APP_SUBTITLE = "Análise inteligente de investimentos — Brasil 🇧🇷 e Estados Unidos 🇺🇸"

DISCLAIMER = (
    "⚠️ **Aviso legal:** todo o conteúdo apresentado é de caráter "
    "informativo e educacional. Não constitui recomendação individual "
    "de investimento, oferta ou solicitação de compra/venda de ativos. "
    "Consulte um profissional certificado antes de tomar decisões."
)

FEATURES: list[tuple[str, str]] = [
    ("📊", "Ativos financeiros"),
    ("💵", "Câmbio BRL/USD"),
    ("📈", "Indicadores técnicos"),
    ("📈", "Indicadores ações"),
    ("📈", "Indicadores fundos imobiliários"),
    ("📈", "Indicadores ETFs"),
    ("📈", "Indicadores índices"),
    ("📈", "Indicadores commodities"),
    ("📈", "Indicadores criptomoedas"),
    ("🧮", "Juros compostos"),
    ("📈", "Indicadores de juros compostos"),
    ("📈", "Indicadores de rentabilidade"),
    ("📈", "Indicadores de volatilidade"),
    ("📈", "Indicadores de drawdown"),
    ("📈", "Indicadores de Sharpe"),
    ("📈", "Indicadores de tendência"),
    ("📈", "Indicadores de confiança"),
    ("📈", "Indicadores de recomendação"),
    ("📈", "Indicadores de segurança"),
    ("📈", "Indicadores de probabilidade de alta"),
    ("💰", "Projeções de patrimônio"),
    ("🛡️", "Risco e volatilidade"),
    ("🏦", "Instituições financeiras"),
    ("📂", "Carteiras de investimentos"),
    ("📉", "Cenários de rentabilidade"),
    ("🔍", "Comparação entre mercados"),
    ("📅", "Rentabilidade histórica"),
    ("🌎", "Macroeconomia BR/EUA"),
]

NAV_PAGES: list[tuple[str, str, str]] = [
    ("📊", "Mercados", "Visão geral de índices e ativos"),
    ("💼", "Carteira", "Composição e alocação"),
    ("🧮", "Projeções", "Juros compostos e metas"),
    ("🏦", "Instituições", "Bancos, corretoras e fundos"),
    ("⚙️", "Configurações", "Preferências e parâmetros"),
]


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**LEXINVEST** — plataforma educacional de análise de "
            "investimentos para os mercados do Brasil e dos EUA."
        ),
        "Get Help": None,
        "Report a bug": None,
    },
)


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
            .main-title {
                font-size: 2.6rem;
                font-weight: 800;
                background: linear-gradient(90deg, #1f77b4, #2ca02c);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.2rem;
            }
            .main-subtitle {
                font-size: 1.05rem;
                color: #555;
                margin-bottom: 1.5rem;
            }
            .feature-card {
                background: rgba(31, 119, 180, 0.06);
                border: 1px solid rgba(31, 119, 180, 0.20);
                border-radius: 12px;
                padding: 14px 16px;
                margin-bottom: 10px;
            }
            .feature-title {
                font-weight: 600;
                font-size: 1rem;
                margin: 0;
            }
            .footer {
                text-align: center;
                color: #888;
                font-size: 0.85rem;
                margin-top: 3rem;
                padding-top: 1rem;
                border-top: 1px solid #eee;
            }
            .status-badge {
                display: inline-block;
                padding: 2px 10px;
                border-radius: 10px;
                font-size: 0.75rem;
                font-weight: 600;
                background: #d4f4dd;
                color: #1b6e3c;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon: str, label: str) -> None:
    st.markdown(
        f"""
        <div class="feature-card">
            <p class="feature-title">{icon} {label}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_features(features: Iterable[tuple[str, str]], cols: int = 3) -> None:
    columns = st.columns(cols)
    for idx, (icon, label) in enumerate(list(features)):
        with columns[idx % cols]:
            feature_card(icon, label)


def render_kpi_row(items: list[tuple[str, str, str | None]]) -> None:
    columns = st.columns(len(items))
    for col, (label, value, delta) in zip(columns, items):
        with col:
            st.metric(label=label, value=value, delta=delta)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## {APP_ICON} {APP_TITLE}")
        st.caption("Análise quantitativa para BR 🇧🇷 e EUA 🇺🇸")

        st.markdown("### 🧭 Navegação")
        for icon, name, desc in NAV_PAGES:
            st.markdown(f"**{icon} {name}**  \n<small>{desc}</small>", unsafe_allow_html=True)

        st.divider()
        st.markdown("### 📌 Status")
        st.markdown('<span class="status-badge">● Online</span>', unsafe_allow_html=True)
        tz = timezone(timedelta(hours=-3))
        st.caption(f"Última atualização: {datetime.now(tz):%d/%m/%Y %H:%M} (BRT)")

        st.divider()
        st.markdown("### ⚠️ Aviso")
        st.caption("As análises são informativas e **não constituem recomendação individual de investimento**.")


def render_header() -> None:
    st.markdown(f'<div class="main-title">{APP_ICON} {APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="main-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)


def render_overview() -> None:
    st.markdown("#### 📌 Visão geral")
    render_kpi_row([
        ("Mercados", "🇧🇷 BR + 🇺🇸 EUA", None),
        ("Moedas", "BRL / USD", None),
        ("Abordagem", "Quantitativa", None),
        ("Motor de projeção", "Juros compostos", None),
    ])


def render_features_section() -> None:
    st.markdown("### 🚀 O que a plataforma oferece")
    render_features(FEATURES, cols=3)


def build_alert_sound() -> str:
    """Cria um beep curto em memória para alertas do navegador."""
    sample_rate = 22050
    duration = 0.18
    frequency = 880
    samples = int(sample_rate * duration)
    frames = b"".join(
        struct.pack("<h", int(12000 * math.sin(2 * math.pi * frequency * i / sample_rate)))
        for i in range(samples)
    )

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(sample_rate)
        sound.writeframes(frames)

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{encoded}"


def render_promising_alerts(strategy: dict, sound_enabled: bool) -> None:
    promising = [
        item for item in strategy["ranked"]
        if item["score"] >= 65
        and item["trend"] != "Baixa"
        and item["recommendation"] in {"Comprar", "Acompanhar"}
        and (
            item["ml_signal"] == "Indefinido"
            or item["ml_probability_up"] >= 0.55
        )
    ][:3]

    if not promising:
        st.info("Nenhum alerta de oportunidade foi ativado pelos critérios atuais.")
        return

    best = promising[0]
    alert_key = f"{best['ticker']}:{best['score']}:{best['ml_probability_up']}"
    st.success(
        f"🔔 Oportunidade promissora detectada: **{best['ticker']}**. "
        f"Score {best['score']}, tendência {best['trend']} e indicação **{best['recommendation']}**. "
        "A análise não garante rentabilidade e deve ser confirmada pelo investidor."
    )

    with st.expander("Ver mensagens de oportunidades", expanded=True):
        for item in promising:
            ml_message = (
                f"probabilidade de alta da IA: {item['ml_probability_up']:.1%}"
                if item["ml_signal"] != "Indefinido"
                else "modelo de IA indisponível; decisão baseada nos indicadores quantitativos"
            )
            st.write(
                f"**{item['ticker']}**: {item['recommendation']} | score {item['score']} | "
                f"retorno de 1 ano {item['retorno_1y']:.2f}% | {ml_message}."
            )

    if sound_enabled and st.session_state.get("last_investment_alert") != alert_key:
        st.markdown(
            f'<audio autoplay src="{build_alert_sound()}"></audio>',
            unsafe_allow_html=True,
        )
        st.session_state["last_investment_alert"] = alert_key


def render_ai_advisor_section() -> None:
    st.markdown("### 🤖 IA de investimento e recomendação inteligente")

    perfil = st.selectbox(
        "Perfil do investidor",
        ["Conservador", "Moderado", "Agressivo"],
        index=1,
        key="ai_advisor_profile",
    )
    capital = st.number_input(
        "Capital inicial para simulação",
        min_value=1000.0,
        value=20000.0,
        step=1000.0,
        key="ai_advisor_capital",
    )
    sound_enabled = st.checkbox(
        "Ativar alertas sonoros de oportunidades",
        value=True,
        key="ai_advisor_sound",
    )
    selected = st.multiselect(
        "Ativos para análise",
        DEFAULT_ASSETS,
        default=["BOVA11.SA", "PETR4.SA", "VALE3.SA", "AAPL", "MSFT", "SPY"],
        key="ai_advisor_assets",
    )

    if not selected:
        st.info("Selecione pelo menos um ativo para receber a recomendação da IA.")
        return

    strategy = build_ai_recommendation(perfil, selected, capital)
    if not strategy["top"]:
        st.warning("Não foi possível gerar recomendações com os dados atuais.")
        return

    st.success(strategy["summary"])
    render_promising_alerts(strategy, sound_enabled)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Melhor ativo", strategy["best"]["ticker"], f"Score {strategy['best']['score']}")
    with col2:
        st.metric("Rentabilidade diária", f"{strategy['best']['daily_yield']:.4f}%")
    with col3:
        st.metric("Câmbio atual", f"R$ {strategy['fx_rate']:.2f}")
    with col4:
        st.metric("Renda mensal est.", f"R$ {strategy['monthly_br']:,.2f}")

    allocation = strategy.get("allocation") or []
    if allocation:
        st.markdown("#### Alocação sugerida")
        alloc_df = pd.DataFrame(allocation)[["ticker", "weight_pct", "score", "recommendation"]].rename(columns={
            "ticker": "Ativo",
            "weight_pct": "Peso %",
            "score": "Score",
            "recommendation": "Indicação",
        })
        st.dataframe(alloc_df, use_container_width=True, hide_index=True)
        note = strategy.get("diversification_note") or ""
        if note:
            st.warning(note)

    ranked_df = pd.DataFrame(strategy["ranked"])
    display_cols = [
        "ticker",
        "score",
        "profile_score",
        "retorno_1y",
        "return_3m",
        "return_6m",
        "daily_yield",
        "volatilidade",
        "drawdown_maximo",
        "sharpe",
        "trend",
        "confidence",
        "recommendation",
        "safety",
        "ml_probability_up",
        "ml_accuracy",
        "ml_signal",
    ]
    available = [col for col in display_cols if col in ranked_df.columns]
    ranked_df = ranked_df[available].rename(columns={
        "ticker": "Ativo",
        "score": "Score",
        "profile_score": "Score perfil",
        "retorno_1y": "Retorno 1Y %",
        "return_3m": "Retorno 3M %",
        "return_6m": "Retorno 6M %",
        "daily_yield": "Rendimento diário %",
        "volatilidade": "Volatilidade",
        "drawdown_maximo": "Drawdown",
        "sharpe": "Sharpe",
        "trend": "Tendência",
        "confidence": "Confiança",
        "recommendation": "Indicação",
        "safety": "Segurança",
        "ml_probability_up": "IA: prob. alta",
        "ml_accuracy": "IA: acurácia",
        "ml_signal": "IA: sinal",
    })
    st.dataframe(ranked_df, use_container_width=True, hide_index=True)

    with st.expander("Racionais por ativo"):
        for item in strategy["ranked"][:5]:
            st.write(f"**{item['ticker']}**: {item.get('rationale', 'Sem racional disponível.')}")


def fetch_asset_history(ticker: str) -> pd.DataFrame:
    data = get_history(ticker, period="1y", interval="1d")
    if data is None or data.empty:
        return pd.DataFrame()
    return data.reset_index(drop=False)


def render_market_section() -> None:
    st.markdown("### 📊 Mercado e comparação")
    selected = st.multiselect(
        "Selecione ativos para analisar",
        DEFAULT_ASSETS,
        default=["PETR4.SA", "AAPL", "SPY"],
        key="market_compare_assets",
    )

    if not selected:
        st.info("Escolha pelo menos um ativo para comparar.")
        return

    results = []
    for ticker in selected:
        history = fetch_asset_history(ticker)
        if history.empty:
            continue
        close = pd.to_numeric(history["Close"], errors="coerce").dropna()
        if close.empty:
            continue
        current = float(close.iloc[-1])
        prior = float(close.iloc[-2]) if len(close) > 1 else current
        change = ((current - prior) / prior) * 100 if prior else 0.0
        results.append({"Ticker": ticker, "Preço": current, "Retorno%": round(change, 2)})

    if results:
        st.dataframe(pd.DataFrame(results).sort_values("Retorno%", ascending=False), use_container_width=True)

    for ticker in selected[:3]:
        history = fetch_asset_history(ticker)
        if history.empty:
            st.warning(f"Não foi possível carregar {ticker}.")
            continue

        st.subheader(ticker)
        prices = pd.to_numeric(history["Close"], errors="coerce").dropna()
        chart = pd.DataFrame({
            "Preço": prices,
            "Média 20": moving_average(prices, 20),
            "Média 50": moving_average(prices, 50),
        })
        st.line_chart(chart)


def analyze_asset_quality(ticker: str) -> dict:
    """Avalia um ativo com retorno, risco, tendência e score de qualidade."""
    history = fetch_asset_history(ticker)
    if history.empty:
        return {
            "ticker": ticker,
            "score": 0.0,
            "recommendation": "Sem dados",
            "trend": "Neutra",
            "volatilidade": 0.0,
            "retorno_1y": 0.0,
            "sharpe": 0.0,
        }

    prices = pd.to_numeric(history["Close"], errors="coerce").dropna()
    if prices.empty or len(prices) < 10:
        return {
            "ticker": ticker,
            "score": 0.0,
            "recommendation": "Dados insuficientes",
            "trend": "Neutra",
            "volatilidade": 0.0,
            "retorno_1y": 0.0,
            "sharpe": 0.0,
        }

    retorno = float((prices.iloc[-1] / prices.iloc[0]) - 1)
    risk = risk_report(prices)
    volatilidade = float(risk.get("volatilidade_anual", 0.0))
    sharpe = float(risk.get("sharpe", 0.0))

    score = asset_score(retorno, min(volatilidade, 1.0), sharpe)
    classification = classify_score(score)

    rsi_series = calculate_rsi(prices).dropna()
    last_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0
    ma20 = moving_average(prices, 20).dropna()
    ma50 = moving_average(prices, 50).dropna()
    last_ma20 = float(ma20.iloc[-1]) if not ma20.empty else prices.iloc[-1]
    last_ma50 = float(ma50.iloc[-1]) if not ma50.empty else prices.iloc[-1]

    if last_ma20 > last_ma50 and last_rsi > 55:
        trend = "Alta"
    elif last_ma20 < last_ma50 and last_rsi < 45:
        trend = "Baixa"
    else:
        trend = "Neutra"

    if score >= 75 and trend != "Baixa" and sharpe > 0:
        recommendation = "Comprar"
    elif score >= 55 and trend != "Baixa":
        recommendation = "Acompanhar"
    elif score >= 40 and sharpe > -1:
        recommendation = "Aguardar"
    else:
        recommendation = "Evitar"

    return {
        "ticker": ticker,
        "score": round(score, 2),
        "recommendation": recommendation,
        "trend": trend,
        "volatilidade": round(volatilidade, 4),
        "retorno_1y": round(retorno * 100, 2),
        "sharpe": round(sharpe, 2),
        "classification": classification,
    }


def render_investor_recommendations() -> None:
    """Mostra uma classificação dos melhores investimentos por perfil do investidor."""
    st.markdown("### 🎯 Melhor escolha para o investidor")

    perfil = st.selectbox(
        "Perfil do investidor",
        ["Conservador", "Moderado", "Agressivo"],
        index=1,
        key="investor_reco_profile",
    )

    selected = st.multiselect(
        "Ativos para avaliar",
        DEFAULT_ASSETS,
        default=["PETR4.SA", "VALE3.SA", "AAPL", "MSFT", "SPY", "BOVA11.SA"],
        key="investor_reco_assets",
    )

    if not selected:
        st.info("Selecione pelo menos um ativo para gerar a indicação.")
        return

    analyses = [analyze_asset_quality(ticker) for ticker in selected]
    analyses = [item for item in analyses if item["score"] > 0]
    if not analyses:
        st.warning("Não foi possível calcular a avaliação dos ativos selecionados.")
        return

    risk_thresholds = {
        "Conservador": {"volatilidade_max": 0.35, "score_min": 60},
        "Moderado": {"volatilidade_max": 0.55, "score_min": 50},
        "Agressivo": {"volatilidade_max": 0.80, "score_min": 40},
    }

    thresholds = risk_thresholds[perfil]
    filtered = [
        item for item in analyses
        if item["score"] >= thresholds["score_min"]
        and item["volatilidade"] <= thresholds["volatilidade_max"]
    ]

    if not filtered:
        filtered = analyses

    ranked = sorted(filtered, key=lambda item: item["score"], reverse=True)
    best = ranked[0]

    st.success(
        f"Melhor indicação para perfil {perfil}: {best['ticker']} com score {best['score']} — "
        f"Classificação: {best['classification']}"
    )

    for item in ranked[:3]:
        if item["recommendation"] == "Comprar":
            tone = "success"
        elif item["recommendation"] == "Acompanhar":
            tone = "info"
        elif item["recommendation"] == "Aguardar":
            tone = "warning"
        else:
            tone = "error"

        with st.container():
            getattr(st, tone)(
                f"{item['ticker']} | Score: {item['score']} | Retorno 1Y: {item['retorno_1y']}% | "
                f"Volatilidade: {item['volatilidade']} | Sharpe: {item['sharpe']} | Tendência: {item['trend']} | "
                f"Indicador: {item['recommendation']}"
            )

    ranking_df = pd.DataFrame(ranked)
    ranking_df = ranking_df[["ticker", "score", "retorno_1y", "volatilidade", "sharpe", "trend", "recommendation"]]
    ranking_df = ranking_df.rename(columns={
        "ticker": "Ativo",
        "score": "Score",
        "retorno_1y": "Retorno 1Y (%)",
        "volatilidade": "Volatilidade",
        "sharpe": "Sharpe",
        "trend": "Tendência",
        "recommendation": "Indicação",
    })
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)


def render_safe_institutions_section() -> None:
    st.markdown("### 🏦 Instituições seguras e mais rentáveis")
    region = st.radio(
        "Região",
        ["Brasil", "Estados Unidos"],
        horizontal=True,
        key="safe_institutions_region",
    )
    institutions = safe_institutions(region)
    st.dataframe(pd.DataFrame(institutions), use_container_width=True, hide_index=True)


def render_technical_section() -> None:
    st.markdown("### 📈 Indicadores técnicos")
    ticker = st.selectbox("Ativo", DEFAULT_ASSETS, index=0, key="technical_ticker")
    history = fetch_asset_history(ticker)
    if history.empty:
        st.warning(f"Dados indisponíveis para {ticker}.")
        return

    prices = pd.to_numeric(history["Close"], errors="coerce").dropna()
    rsi = calculate_rsi(prices)
    macd = calculate_macd(prices)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("RSI")
        st.line_chart(rsi.rename("RSI"))
    with col2:
        st.subheader("MACD")
        st.line_chart(macd)

    st.caption(f"Último preço: R$ {prices.iloc[-1]:,.2f}" if ticker.endswith(".SA") else f"Último preço: US$ {prices.iloc[-1]:,.2f}")


def render_portfolio_section() -> None:
    st.markdown("### 💼 Carteira")
    positions = pd.DataFrame(
        {
            "Ativo": ["PETR4.SA", "AAPL", "SPY"],
            "Quantidade": [10, 15, 8],
            "Preço": [33.80, 210.20, 550.40],
            "Preço Médio": [30.50, 195.00, 520.00],
            "Preço Atual": [33.80, 210.20, 550.40],
        }
    )

    positions["Valor"] = positions["Quantidade"] * positions["Preço"]
    weights = portfolio_weights(positions)
    st.dataframe(
        weights[["Ativo", "Quantidade", "Preço", "Valor", "Peso"]],
        use_container_width=True,
    )

    st.metric("Valor total da carteira", f"R$ {portfolio_value(positions):,.2f}")
    st.metric("Retorno da carteira", f"{portfolio_return(positions) * 100:.2f}%")


def render_projection_section() -> None:
    st.markdown("### 🧮 Projeções")
    principal = st.number_input(
        "Capital inicial",
        min_value=0.0,
        value=10000.0,
        step=1000.0,
        key="projection_principal",
    )
    aporte = st.number_input(
        "Aporte mensal",
        min_value=0.0,
        value=1000.0,
        step=100.0,
        key="projection_aporte",
    )
    years = st.slider("Horizonte", 1, 20, 10, key="projection_years")
    profile = st.selectbox(
        "Perfil para taxa de projeção",
        ["Conservador", "Moderado", "Agressivo"],
        index=1,
        key="projection_profile",
    )

    scenarios = scenario_projection(principal, aporte, years)
    table = pd.DataFrame({
        "Cenário": list(scenarios.keys()),
        "Valor final": list(scenarios.values()),
    })
    st.dataframe(table, use_container_width=True)

    future_value = build_projection_plan(principal, aporte, years, profile=profile)
    chart = pd.DataFrame(future_value)[["Ano", "Patrimônio", "Rendimento"]].set_index("Ano")
    st.line_chart(chart)

    rate_label = {"Conservador": "6%", "Moderado": "10%", "Agressivo": "15%"}[profile]
    st.caption(
        f"A projeção do perfil {profile} usa juros compostos, aportes mensais "
        f"e crescimento anual estimado de {rate_label}."
    )

    last = future_value[-1]
    st.markdown(
        f"**Projeção final ({profile}):** R$ {last['Patrimônio']:.2f} | "
        f"Rendimento acumulado: R$ {last['Rendimento']:.2f} | "
        f"Capital investido: R$ {last['Capital investido']:.2f}"
    )


def render_institutions_section() -> None:
    st.markdown("### 🏦 Instituições")
    tab1, tab2 = st.tabs(["Brasil", "Estados Unidos"])
    with tab1:
        st.dataframe(pd.DataFrame(brazil_institutions()), use_container_width=True)
    with tab2:
        st.dataframe(pd.DataFrame(us_institutions()), use_container_width=True)


def render_currency_section() -> None:
    st.markdown("### 💵 Câmbio")
    usd_brl = get_usd_brl()
    if usd_brl is None:
        st.warning("Não foi possível buscar a cotação do dólar.")
        return

    st.metric("BRL / USD", f"R$ {usd_brl:,.2f}")
    amount = st.number_input("Valor em BRL", value=1000.0, step=100.0)
    converted = amount / usd_brl if usd_brl else 0.0
    st.write(f"{amount:,.2f} BRL = {converted:,.2f} USD")


def render_quick_start() -> None:
    st.markdown("### 🏁 Como começar")
    with st.expander("Ver passos recomendados", expanded=True):
        st.markdown(
            """
            1. **Explore os mercados** — índices, ações, FIIs, ETFs e câmbio.
            2. **Monte sua carteira** — adicione ativos e defina pesos.
            3. **Simule projeções** — juros compostos, aportes e metas.
            4. **Analise risco** — volatilidade, drawdown e Sharpe.
            5. **Compare instituições** — taxas, produtos e serviços.
            """
        )


def render_disclaimer() -> None:
    st.warning(DISCLAIMER, icon="⚖️")


def render_footer() -> None:
    st.markdown(
        """
        <div class="footer">
            LEXINVEST © 2024 · Feito com ❤️ e Streamlit ·
            Dados meramente ilustrativos
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_custom_css()
    render_sidebar()
    render_header()
    render_overview()

    st.divider()
    render_features_section()

    st.divider()
    render_ai_advisor_section()

    st.divider()
    render_market_section()

    st.divider()
    render_technical_section()

    st.divider()
    render_currency_section()

    st.divider()
    render_portfolio_section()

    st.divider()
    render_projection_section()

    st.divider()
    render_investor_recommendations()

    st.divider()
    render_safe_institutions_section()

    st.divider()
    render_institutions_section()

    st.divider()
    render_quick_start()
    render_disclaimer()
    render_footer()


if __name__ == "__main__":
    main()
