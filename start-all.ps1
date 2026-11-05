# Levanta CMS (8080), métricas (8000), generador estático (8001) y blog (5500).
# Uso:  .\start-all.ps1
# Requiere que los entornos .venv de cada servicio ya existan.
# Si los servicios ya están corriendo, ciérralos antes (Ctrl+C en cada ventana).

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$services = @(
    @{
        Name = "CMS DevBlog (8080)"
        Dir  = Join-Path $root "API\devblog-cms-api-1.2\devblog-cms-api"
        Command = "uvicorn app.main:app --host 127.0.0.1 --port 8080"
    },
    @{
        Name = "Métricas (8000)"
        Dir  = Join-Path $root "pendiente\metrics-navigation-main\metrics-navigation-main"
        Command = "uvicorn app.main:app --host 127.0.0.1 --port 8000"
    },
    @{
        Name = "Generador estático (8001)"
        Dir  = Join-Path $root "pendiente\static-sites-generator-main\static-sites-generator-main"
        Command = "uvicorn src.main:app --host 127.0.0.1 --port 8001"
    },
    @{
        Name = "Blog (5500)"
        Dir  = Join-Path $root "dev-blog"
        Command = "python -m http.server 5500"
    }
)

foreach ($service in $services) {
    if (-not (Test-Path $service.Dir)) {
        Write-Warning "No existe la carpeta: $($service.Dir)"
        continue
    }

    $python = Join-Path $service.Dir ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        $python = "python"
    }

    $command = "Set-Location '$($service.Dir)'; & '$python' -m $($service.Command)"
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $command)
    Write-Host "Iniciado: $($service.Name)"
}

Write-Host ""
Write-Host "CMS:       http://127.0.0.1:8080/docs"
Write-Host "Métricas:  http://127.0.0.1:8000/v1/query"
Write-Host "Generador: http://127.0.0.1:8001/docs"
Write-Host "Blog:      http://127.0.0.1:5500/"
Write-Host "Consola:   http://127.0.0.1:5500/admin.html"
