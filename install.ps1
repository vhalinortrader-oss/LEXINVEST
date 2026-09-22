param(
    [switch]$Start
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $pythonCommand) {
    $pythonExecutable = $pythonCommand.Source
    $pythonArguments = @("-3")
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw "Python 3 nao foi encontrado. Instale Python 3.11 ou superior e tente novamente."
    }
    $pythonExecutable = $pythonCommand.Source
    $pythonArguments = @()
}

$venvPath = Join-Path $PSScriptRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Criando ambiente virtual em .venv..." -ForegroundColor Cyan
    & $pythonExecutable @pythonArguments -m venv $venvPath
}

Write-Host "Atualizando pip..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip

Write-Host "Instalando dependencias..." -ForegroundColor Cyan
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")

$envExample = Join-Path $PSScriptRoot ".env.example.txt"
$envFile = Join-Path $PSScriptRoot ".env"
if ((Test-Path $envExample) -and (-not (Test-Path $envFile))) {
    Copy-Item $envExample $envFile
    Write-Host "Arquivo .env criado a partir do modelo." -ForegroundColor Green
}

Write-Host "Instalacao concluida." -ForegroundColor Green
Write-Host "Para iniciar: .\.venv\Scripts\python.exe -m streamlit run app.py"

if ($Start) {
    & $venvPython -m streamlit run (Join-Path $PSScriptRoot "app.py")
}
