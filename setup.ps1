# Prepara los entornos de los tres servicios y carga los datos iniciales.
# Uso:  .\setup.ps1
# Funciona con `uv` si está instalado; si no, usa `python -m venv` + pip.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$hasUv = $null -ne (Get-Command uv -ErrorAction SilentlyContinue)

function Initialize-Service {
    param(
        [string]$Name,
        [string]$Directory
    )

    $full = Join-Path $root $Directory
    if (-not (Test-Path $full)) {
        throw "No existe la carpeta de $Name : $full"
    }

    $venv = Join-Path $full ".venv"
    $python = Join-Path $venv "Scripts\python.exe"

    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan

    Push-Location $full
    try {
        if (-not (Test-Path $python)) {
            if ($hasUv) {
                Write-Host "Creando .venv con uv..."
                uv venv --python 3.12 .venv | Out-Host
            } else {
                Write-Host "Creando .venv con python -m venv..."
                python -m venv .venv | Out-Host
            }
        } else {
            Write-Host ".venv ya existe."
        }

        if ($hasUv) {
            uv pip install --python $python -r requirements.txt | Out-Host
        } else {
            & $python -m pip install --upgrade pip | Out-Host
            & $python -m pip install -r requirements.txt | Out-Host
        }

        if (Test-Path ".env.example") {
            if (-not (Test-Path ".env")) {
                Copy-Item ".env.example" ".env"
                Write-Host "Creado .env desde .env.example"
            } else {
                Write-Host ".env ya existe; se conserva."
            }
        }
    }
    finally {
        Pop-Location
    }

    return $python
}

$cmsPython = Initialize-Service -Name "CMS DevBlog" -Directory "API\devblog-cms-api-1.2\devblog-cms-api"
Initialize-Service -Name "Métricas" -Directory "pendiente\metrics-navigation-main\metrics-navigation-main" | Out-Null
Initialize-Service -Name "Generador estático" -Directory "pendiente\static-sites-generator-main\static-sites-generator-main" | Out-Null

Write-Host ""
Write-Host "== Datos iniciales del CMS ==" -ForegroundColor Cyan
Push-Location (Join-Path $root "API\devblog-cms-api-1.2\devblog-cms-api")
try {
    & $cmsPython -m app.seed
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Listo. Ahora ejecuta:" -ForegroundColor Green
Write-Host "  .\start-all.ps1"
Write-Host ""
Write-Host "CMS:       http://127.0.0.1:8080/docs"
Write-Host "Métricas:  http://127.0.0.1:8000/v1/query"
Write-Host "Generador: http://127.0.0.1:8001/docs"
Write-Host "Blog:      http://127.0.0.1:5500/"
Write-Host "Consola:   http://127.0.0.1:5500/admin.html  (token: console-dev-token)"
