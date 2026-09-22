def compound_interest(
    principal: float,
    annual_rate: float,
    years: float,
    contributions: float = 0.0,
    contribution_frequency: int = 12
) -> float:

    periods = int(years * contribution_frequency)

    periodic_rate = (
        (1 + annual_rate) ** (1 / contribution_frequency)
    ) - 1

    value = principal

    for _ in range(periods):
        value = value * (1 + periodic_rate)
        value += contributions

    return value


def projection_table(
    principal: float,
    annual_rate: float,
    monthly_contribution: float,
    years: int
):

    result = []

    for year in range(1, years + 1):

        value = compound_interest(
            principal=principal,
            annual_rate=annual_rate,
            years=year,
            contributions=monthly_contribution,
        )

        invested = (
            principal
            + monthly_contribution * 12 * year
        )

        result.append({
            "Ano": year,
            "Patrimônio": value,
            "Capital investido": invested,
            "Rendimento": value - invested,
        })

    return result


def monthly_income(
    capital: float,
    annual_rate: float
) -> float:

    monthly_rate = (
        (1 + annual_rate) ** (1 / 12)
    ) - 1

    return capital * monthly_rate


def scenario_projection(
    principal: float,
    monthly_contribution: float,
    years: int
):

    scenarios = {
        "Conservador": 0.06,
        "Base": 0.10,
        "Agressivo": 0.15,
    }

    output = {}

    for name, rate in scenarios.items():

        output[name] = compound_interest(
            principal,
            rate,
            years,
            monthly_contribution
        )

    return output
