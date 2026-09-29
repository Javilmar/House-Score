<#
.SYNOPSIS
  Copia de seguridad de PostgreSQL (FR-016, T051) con rotacion.

.DESCRIPTION
  Ejecuta pg_dump (formato custom) dentro del contenedor `db` y guarda el volcado en
  -Destino, que debe estar FUERA del disco que aloja el volumen de Docker (otro disco o
  una carpeta sincronizada con la nube). Conserva los -Conservar volcados mas recientes.

  Restaurar (verificado): copiar el volcado al contenedor y restaurarlo en una base vacia
    docker compose cp volcado.dump db:/tmp/r.dump
    docker compose exec -T db pg_restore -U housescore -d <base> --no-owner /tmp/r.dump
  (desde Git Bash, con MSYS_NO_PATHCONV=1 para que /tmp no se convierta en ruta de Windows).

.EXAMPLE
  .\ops\backup.ps1 -Destino "D:\backups\housescore"
#>
param(
    [Parameter(Mandatory = $true)][string]$Destino,
    [int]$Conservar = 14
)

$ErrorActionPreference = "Stop"
$backend = Split-Path -Parent $PSScriptRoot
Set-Location $backend

New-Item -ItemType Directory -Force -Path $Destino | Out-Null
$nombre = "housescore-{0}.dump" -f (Get-Date -Format "yyyy-MM-dd_HHmm")
$destinoFinal = Join-Path $Destino $nombre

docker compose exec -T db sh -c "pg_dump -U housescore -Fc housescore > /tmp/backup.dump"
if ($LASTEXITCODE -ne 0) { throw "pg_dump fallo (codigo $LASTEXITCODE)" }

docker compose cp db:/tmp/backup.dump $destinoFinal
if ($LASTEXITCODE -ne 0) { throw "no se pudo copiar el volcado (codigo $LASTEXITCODE)" }
docker compose exec -T db rm -f /tmp/backup.dump | Out-Null

if (-not (Test-Path $destinoFinal) -or (Get-Item $destinoFinal).Length -eq 0) {
    throw "el volcado esta vacio o no existe: $destinoFinal"
}

Get-ChildItem $Destino -Filter "housescore-*.dump" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Conservar |
    Remove-Item -Force

Write-Host "Copia guardada en $destinoFinal"
