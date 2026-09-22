__all__ = [
    "institution_profile",
    "brazil_institutions",
    "us_institutions",
    "safe_institutions",
]


def institution_profile(
    name: str,
    country: str,
    regulation: str,
    protection: str,
    product_focus: str,
    safety_rating: str,
    expected_return: str,
    notes: str = ""
) -> dict:

    return {
        "Instituição": name,
        "País": country,
        "Regulação": regulation,
        "Proteção": protection,
        "Foco": product_focus,
        "Segurança": safety_rating,
        "Rentabilidade esperada": expected_return,
        "Observações": notes,
    }


def brazil_institutions():

    return [
        institution_profile(
            "Itaú Unibanco",
            "Brasil",
            "Banco Central do Brasil / B3",
            "Alta. Forte supervisão regulatória e estrutura sólida",
            "Conta corrente, CDB, renda fixa, previdência e fundos",
            "Excelente",
            "CDB e renda fixa em torno de 6% a 12% a.a. conforme cenário",
            "Ótima opção para investidores conservadores e moderados com boa liquidez."
        ),
        institution_profile(
            "Banco do Brasil",
            "Brasil",
            "Banco Central do Brasil / B3",
            "Alta. Grande solidez e acesso ao mercado",
            "Tesouro Direto, CDB, previdência e educação financeira",
            "Excelente",
            "Tesouro Selic e títulos públicos com retornos conservadores e previsíveis",
            "Muito robusto para estratégia de segurança e longo prazo."
        ),
        institution_profile(
            "Bradesco",
            "Brasil",
            "Banco Central do Brasil / B3",
            "Alta. Rede ampla e produtos de baixa volatilidade",
            "CDB, fundos, previdência e investimentos em renda fixa",
            "Boa",
            "Rentabilidade moderada a sólida em carteira conservadora",
            "Bom equilíbrio entre segurança, liquidez e opções de planejamento."
        ),
        institution_profile(
            "XP Investimentos",
            "Brasil",
            "CVM / B3",
            "Alta. Plataforma diversificada e serviços de assessoria",
            "Fundos, ETFs, ações, renda fixa e gestão de carteira",
            "Boa",
            "Bom potencial para carteiras diversificadas e moderadas",
            "Ótima para quem busca acesso a ativos e planejamento estruturado."
        ),
        institution_profile(
            "Tesouro Direto",
            "Brasil",
            "Tesouro Nacional / B3",
            "Muito alta. Instrumento público e regulado",
            "Tesouro Selic, IPCA e Prefixado",
            "Muito Excelente",
            "Entre 5% e 12% a.a. conforme título e cenário",
            "Uma das opções mais seguras do Brasil para preservação de patrimônio."
        ),
    ]


def us_institutions():

    return [
        institution_profile(
            "Fidelity",
            "Estados Unidos",
            "SEC / FINRA",
            "Alta. Corretora consolidada e bem regulamentada",
            "ETFs, ações, fundos e renda fixa",
            "Excelente",
            "Diversificação com potencial de retorno de 7% a 12% a.a. em carteiras balanceadas",
            "Excelente para investidores com foco em longo prazo e diversidade."
        ),
        institution_profile(
            "Charles Schwab",
            "Estados Unidos",
            "SEC / FINRA",
            "Alta. Estrutura institucional forte",
            "Ações, ETFs, fundos e estratégias de investimento",
            "Excelente",
            "Retornos robustos em portfólios bem diversificados",
            "Muito adequada para exposição ao mercado norte-americano."
        ),
        institution_profile(
            "Vanguard",
            "Estados Unidos",
            "SEC / FINRA",
            "Alta. Forte reputação e foco em custos baixos",
            "ETFs, fundos de índice e renda fixa",
            "Excelente",
            "Boa combinação de segurança, diversificação e retorno de mercado",
            "Recomendada para apostas consistentes e de baixo custo."
        ),
        institution_profile(
            "Interactive Brokers",
            "Estados Unidos",
            "SEC / FINRA",
            "Alta. Plataforma internacional e acesso global",
            "Ações, ETFs, forex e mercados internacionais",
            "Excelente",
            "Permite diversificação entre BRL e USD com relação de risco e retorno eficiente",
            "Ideal para investidores que operam em múltiplos mercados."
        ),
        institution_profile(
            "SIPC",
            "Estados Unidos",
            "Regulador de proteção de contas",
            "Proteção de contas de corretoras elegíveis",
            "Proteção para contas de corretoras",
            "Muito boa",
            "Proteção em limites previstos pela legislação",
            "Importante, mas não substitui a análise do risco real do ativo."
        ),
    ]


def safe_institutions(region: str = "Brasil") -> list[dict]:

    normalized = region.strip().lower()
    if normalized in {
        "eua",
        "usa",
        "us",
        "estados unidos",
        "united states",
    }:
        return us_institutions()

    return brazil_institutions()
