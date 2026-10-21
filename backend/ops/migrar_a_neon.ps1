<#
Migra un volcado de pg_dump (formato custom) a Neon y verifica recuentos (spec 003, T037).

1. Restaura el volcado en un PostgreSQL efímero local y cuenta filas por tabla.
2. Lo restaura en Neon por la conexión DIRECTA (pg_restore no funciona por el pooler).
3. Cuenta en Neon y compara. Sale con código 1 si algún recuento difiere.

La URL sale de DATABASE_URL_UNPOOLED (entorno o .env.local de la raíz del repo).
Uso: backend/ops/migrar_a_neon.ps1 -Dump C:\ruta\housescore.dump
#>
param(
    [Parameter(Mandatory = $true)][string]$Dump,
    [string]$EnvFile = "",
    [string]$Imagen = "postgres:18-alpine"
)
$ErrorActionPreference = "Stop"
# En PowerShell 5 $PSScriptRoot esta vacio dentro de param(): se resuelve aqui
if (-not $EnvFile) { $EnvFile = Join-Path $PSScriptRoot "..\..\.env.local" }
function Leer-Url {
    if ($env:DATABASE_URL_UNPOOLED) { return $env:DATABASE_URL_UNPOOLED }
    if (Test-Path $EnvFile) {
        foreach ($linea in Get-Content $EnvFile) {
            if ($linea -match '^\s*DATABASE_URL_UNPOOLED\s*=\s*"?([^"]+)"?\s*$') { return $Matches[1] }
        }
    }
    throw "Falta DATABASE_URL_UNPOOLED (entorno o $EnvFile)"
}

$Tablas = @("listing", "historial_precio", "pasada_diaria", "precio_referencia", "alembic_version")
$Consulta = ($Tablas | ForEach-Object { "select '$_', count(*) from $_" }) -join " union all "

function Recuentos([string[]]$Salida) {
    $r = @{}
    foreach ($l in $Salida) { if ($l -match '^(\w+)\|(\d+)$') { $r[$Matches[1]] = [int]$Matches[2] } }
    return $r
}

$Dump = (Resolve-Path $Dump).Path
$Dir = Split-Path $Dump -Parent
$Fichero = Split-Path $Dump -Leaf
$Url = Leer-Url
if ($Url -match '-pooler\.') { throw "La URL es la del pooler; pg_restore necesita la conexion directa" }

# 1. Recuentos de referencia en un PostgreSQL efimero
$Nombre = "hs-migracion-$PID"
docker run -d --rm --name $Nombre -e POSTGRES_PASSWORD=x -e POSTGRES_DB=origen -v "${Dir}:/d:ro" $Imagen | Out-Null
try {
    for ($i = 0; $i -lt 30; $i++) {
        docker exec $Nombre pg_isready -U postgres -d origen 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Seconds 1
    }
    docker exec $Nombre pg_restore -U postgres -d origen --no-owner --no-privileges "/d/$Fichero"
    if ($LASTEXITCODE -ne 0) { throw "pg_restore fallo en la base efimera" }
    $Origen = Recuentos (docker exec $Nombre psql -U postgres -d origen -Atc $Consulta)
} finally {
    docker stop $Nombre | Out-Null
}

# 2. Restauracion en Neon (sustituye las tablas existentes)
docker run --rm -v "${Dir}:/d:ro" $Imagen pg_restore --no-owner --no-privileges --clean --if-exists -d $Url "/d/$Fichero"
if ($LASTEXITCODE -ne 0) { throw "pg_restore fallo contra Neon" }

# 3. Comparacion
$Neon = Recuentos (docker run --rm $Imagen psql $Url -Atc $Consulta)
$Diferencias = 0
"{0,-20} {1,10} {2,10}" -f "tabla", "volcado", "neon"
foreach ($t in $Tablas) {
    $marca = if ($Origen[$t] -eq $Neon[$t]) { "" } else { $Diferencias++; "  <-- DIFIERE" }
    "{0,-20} {1,10} {2,10}{3}" -f $t, $Origen[$t], $Neon[$t], $marca
}
if ($Diferencias -gt 0) { Write-Error "$Diferencias tabla(s) con recuentos distintos"; exit 1 }
"OK: recuentos identicos"
