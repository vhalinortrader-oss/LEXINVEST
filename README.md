# LEXINVEST

Dashboard de analise quantitativa de investimentos para Brasil e Estados Unidos, desenvolvido em Python e Streamlit.

## Funcionalidades

- Analise de ativos brasileiros e norte-americanos
- Cotacao e conversao BRL/USD
- Indicadores tecnicos: medias moveis, RSI e MACD
- Analise de risco: volatilidade, drawdown e Sharpe
- Aprendizado de maquina para estimar probabilidade de alta
- Ranking por perfil: conservador, moderado e agressivo
- Mensagens e alertas sonoros de oportunidades promissoras
- Comparacao de ativos e graficos historicos
- Carteira de investimentos e pesos
- Juros compostos, aportes e projecoes financeiras
- Instituicoes e mecanismos de protecao no Brasil e nos EUA

## Requisitos

- Windows 10 ou superior
- Python 3.11 ou superior
- Acesso a internet para consultar dados do Yahoo Finance

## Instalacao automatica no Windows

Abra o PowerShell na pasta do projeto e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

Para instalar e iniciar o dashboard em seguida:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1 -Start
```

O instalador cria o ambiente `.venv`, atualiza o `pip`, instala o conteúdo de `requirements.txt` e cria o arquivo `.env` a partir do modelo.

## Instalacao manual

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example.txt .env
```

## Execucao

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Depois, abra `http://localhost:8501` no navegador.

## Configuracao

Edite o arquivo `.env` para alterar capital inicial, taxa livre de risco, período e intervalo dos dados:

```text
INITIAL_CAPITAL=10000
RISK_FREE_RATE_BR=0.10
RISK_FREE_RATE_US=0.04
YAHOO_PERIOD=1y
YAHOO_INTERVAL=1d
```

## Observacao

As analises sao educacionais e nao constituem recomendacao individual de investimento. Retornos passados e previsoes estatisticas nao garantem resultados futuros.
