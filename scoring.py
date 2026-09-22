def normalize(value, minimum, maximum):

    if maximum == minimum:
        return 0.0

    score = (value - minimum) / (maximum - minimum)

    return max(0.0, min(1.0, score))


def asset_score(
    return_rate: float,
    volatility: float,
    sharpe: float
) -> float:

    return_rate_score = normalize(
        return_rate,
        -0.50,
        0.50
    )

    volatility_score = 1 - normalize(
        volatility,
        0.0,
        1.0
    )

    sharpe_score = normalize(
        sharpe,
        -2.0,
        3.0
    )

    score = (
        return_rate_score * 0.40
        + volatility_score * 0.30
        + sharpe_score * 0.30
    )

    return round(score * 100, 2)


def classify_score(score: float) -> str:

    if score >= 75:
        return "Perfil quantitativo favorável"

    if score >= 50:
        return "Perfil quantitativo intermediário"

    return "Perfil quantitativo de maior risco"
