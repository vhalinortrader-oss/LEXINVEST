import numpy as np
from datetime import datetime, timedelta

# ========== 配置参数 ==========
taxa_anual_br = 0.14       # 巴西 Selic 假设 14% a.a.（来源[citation:15]）
taxa_anual_us = 0.0365     # 美国 3-month T-bill 约 3.65%[citation:6]
cambio_usd_brl = 5.40      # 假设汇率，需实时更新

valor_inicial_brl = 10000
valor_inicial_usd = valor_inicial_brl / cambio_usd_brl

dias = 365  # 投资期限

# ========== 巴西：每日复利 ==========
def calcular_br(valor_inicial, taxa_anual, dias):
    taxa_diaria = (1 + taxa_anual) ** (1/365) - 1
    valor_final = valor_inicial * (1 + taxa_diaria) ** dias
    # IR regressivo: 15% para > 720 dias (simplificado como 22.5% para curto prazo)
    ir = 0.225 if dias <= 180 else 0.15
    rendimento = valor_final - valor_inicial
    valor_liquido = valor_inicial + rendimento * (1 - ir)
    return valor_final, valor_liquido, rendimento

# ========== 美国：每日复利（以 USD 计） ==========
def calcular_us(valor_inicial, taxa_anual, dias):
    taxa_diaria = (1 + taxa_anual) ** (1/365) - 1
    valor_final = valor_inicial * (1 + taxa_diaria) ** dias
    # 美国 T-bill 利息联邦税（假设 22% 税率）
    imposto = 0.22
    rendimento = valor_final - valor_inicial
    valor_liquido = valor_inicial + rendimento * (1 - imposto)
    return valor_final, valor_liquido, rendimento


if __name__ == "__main__":
    # 执行
    br_bruto, br_liquido, br_rend = calcular_br(valor_inicial_brl, taxa_anual_br, dias)
    us_bruto, us_liquido, us_rend = calcular_us(valor_inicial_usd, taxa_anual_us, dias)

    # 换算回 BRL
    us_liquido_brl = us_liquido * cambio_usd_brl

    print(f"=== 巴西 Tesouro Reserva (100% Selic) ===")
    print(f"Bruto: R$ {br_bruto:,.2f} | Líquido: R$ {br_liquido:,.2f} | Rendimento líq: R$ {br_liquido - valor_inicial_brl:,.2f}")
    print(f"\n=== 美国 T-Bill (USD) ===")
    print(f"Bruto: $ {us_bruto:,.2f} | Líquido: $ {us_liquido:,.2f}")
    print(f"Líquido em BRL: R$ {us_liquido_brl:,.2f} | Rendimento líq: R$ {us_liquido_brl - valor_inicial_brl:,.2f}")

    # ========== 复利推进表（每月） ==========
    print("\n=== 复利推进（巴西，12 个月）===")
    saldo = valor_inicial_brl
    taxa_mensal_br = (1 + taxa_anual_br) ** (1/12) - 1
    for mes in range(1, 13):
        saldo *= (1 + taxa_mensal_br)
        print(f"Mês {mes:02d}: R$ {saldo:,.2f}")
