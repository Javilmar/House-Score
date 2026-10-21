<#
.SYNOPSIS
  Copia de seguridad de la base de datos de Neon (FR-016, T051/T035) con rotacion.

.DESCRIPTION
  Ejecuta pg_dump (formato custom) contra Neon desde un contenedor `postgres:18-alpine` (no hace
  falta tener cliente de PostgreSQL instalado) y guarda el volcado en -Destino, que debe estar
  FUERA del disco local (otro disco o una carpeta sincronizada con la nube, p. ej. OneDrive).
  Conserva los -Conservar volcados mas recientes.

  La URL sale de DATABASE_URL_UNPOOLED (conexion directa; el pooler de Neon no sirve para
  pg_dump) y, si no existe, de DATABASE_URL. Se lee del entorno o, si no esta, del fichero
  .env.local de la raiz del repo (formato dotenv; los valores pueden ir entre comillas).

  Restaurar (en una base vacia, con el mismo cliente por Docker):
    docker run --rm -v "<carpeta>:/b" postgres:18-alpine pg_restore -d "<url-destino>" --no-owner /b/<volcado>.dump

.EXAMPLE
  .\ops\backup.ps1 -Destino "D:\backups\housescore"
#>
param(
    [Parameter(Mandatory = $true)][string]$Destino,
    [int]$Conservar = 14
)

$ErrorActionPreference = "Stop"
$backend = Split-Path -Parent $PSScriptRoot
$raiz = Split-Path -Parent $backend

function Leer-DotEnv([string]$ruta) {
    $valores = @{}
    if (-not (Test-Path $ruta)) { return $valores }
    foreach ($linea in Get-Content $ruta -Encoding UTF8) {
        $linea = $linea.Trim()
        if (-not $linea -or $linea.StartsWith("#") -or -not $linea.Contains("=")) { continue }
        $clave, $valor = $linea -split "=", 2
        $clave = ($clave.Trim() -replace "^export\s+", "")
        $valor = $valor.Trim()
        if ($valor.Length -ge 2 -and (($valor.StartsWith('"') -and $valor.EndsWith('"')) -or
                ($valor.StartsWith("'") -and $valor.EndsWith("'")))) {
            $valor = $valor.Substring(1, $valor.Length - 2)
        }
        $valores[$clave] = $valor
    }
    return $valores
}

$dotenv = Leer-DotEnv (Join-Path $raiz ".env.local")
$url = $null
foreach ($nombreVar in "DATABASE_URL_UNPOOLED", "DATABASE_URL") {
    $candidata = [Environment]::GetEnvironmentVariable($nombreVar)
    if (-not $candidata) { $candidata = $dotenv[$nombreVar] }
    if ($candidata) { $url = $candidata; break }
}
if (-not $url) {
    throw "falta DATABASE_URL_UNPOOLED (o DATABASE_URL): definela en el entorno o en $raiz\.env.local"
}

New-Item -ItemType Directory -Force -Path $Destino | Out-Null
$nombre = "housescore-{0}.dump" -f (Get-Date -Format "yyyy-MM-dd_HHmm")
$destinoFinal = Join-Path $Destino $nombre

# pg_dump escribe el volcado por stdout; se redirige a fichero en bytes (sin pasar por el
# codificador de texto de PowerShell, que corromperia el formato binario).
$proceso = Start-Process -FilePath "docker" `
    -ArgumentList @("run", "--rm", "postgres:18-alpine", "pg_dump", "-Fc", $url) `
    -RedirectStandardOutput $destinoFinal -NoNewWindow -Wait -PassThru
if ($proceso.ExitCode -ne 0) {
    Remove-Item -Force -ErrorAction SilentlyContinue $destinoFinal
    throw "pg_dump fallo (codigo $($proceso.ExitCode))"
}

if (-not (Test-Path $destinoFinal) -or (Get-Item $destinoFinal).Length -eq 0) {
    throw "el volcado esta vacio o no existe: $destinoFinal"
}

Get-ChildItem $Destino -Filter "housescore-*.dump" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Conservar |
    Remove-Item -Force

Write-Host "Copia guardada en $destinoFinal"
