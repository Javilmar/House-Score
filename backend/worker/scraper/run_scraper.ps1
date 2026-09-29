<#
.SYNOPSIS
  Ejecuta el scraper en el host y, si se indica, envia una pasada a la API (T040).

.DESCRIPTION
  1. Ejecuta -Comando (el scorer) y guarda su salida en logs\scraper-YYYY-MM-DD.log.
  2. Si se pasa -Archivo, envia ese JSON a POST /ingest con el cliente (worker.scraper.client).
  Cualquier fallo queda en el log (FR-014) y el script termina con codigo distinto de 0.

  Variables de entorno (backend\.env se carga si existe): INGEST_SECRET, HOUSESCORE_API_URL.

.EXAMPLE
  .\worker\scraper\run_scraper.ps1 -Comando "python C:\ruta\scorer.py" -Archivo C:\ruta\pasada.json
#>
param(
    [Parameter(Mandatory = $true)][string]$Comando,
    [string]$Archivo
)

$ErrorActionPreference = "Stop"
$backend = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $backend

$logs = Join-Path $backend "logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$log = Join-Path $logs ("scraper-{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))

function Escribir($linea) {
    Write-Host $linea
    Add-Content -Path $log -Value $linea -Encoding UTF8
}

function Log($msg) {
    Escribir ("{0} {1}" -f (Get-Date -Format "s"), $msg)
}

# Carga backend\.env (KEY=VALUE) sin sobrescribir variables ya definidas
$envFile = Join-Path $backend ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -match "^\s*[^#\s][^=]*=" } | ForEach-Object {
        $k, $v = $_ -split "=", 2
        if (-not (Test-Path "Env:$($k.Trim())")) { Set-Item "Env:$($k.Trim())" $v.Trim() }
    }
}

$codigo = 0
try {
    Log "Inicio: $Comando"
    Invoke-Expression $Comando 2>&1 | ForEach-Object { Escribir "$_" }
    if ($LASTEXITCODE -ne 0) { throw "el scraper termino con codigo $LASTEXITCODE" }

    if ($Archivo) {
        Log "Enviando $Archivo a la API"
        $python = Join-Path $backend ".venv\Scripts\python.exe"
        if (-not (Test-Path $python)) { $python = "python" }
        & $python -m worker.scraper.client $Archivo 2>&1 | ForEach-Object { Escribir "$_" }
        if ($LASTEXITCODE -ne 0) { throw "el envio a la API fallo (codigo $LASTEXITCODE)" }
    }
    Log "Fin correcto"
} catch {
    Log "ERROR: $($_.Exception.Message)"
    $codigo = 1
}
exit $codigo
