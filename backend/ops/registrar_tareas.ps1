<#
.SYNOPSIS
  Registra las tareas programadas de Windows del backend (T048, T051).

.DESCRIPTION
  - HouseScore-Backup: lanza ops\backup.ps1 cada dia.
  - HouseScore-Scraper: tarea de RECUPERACION. El cron de hermes (job "Buscador Pisos", 09:00)
    es el disparador principal, pero solo corre si el PC esta encendido a esa hora. Esta tarea
    lanza ops\hermes_launcher.py a las 10:00 con StartWhenAvailable: si se perdio la hora, se
    lanza al encender el equipo. El lanzador escribe ultima_pasada_ok.txt (fecha de la ultima
    pasada completa) y no repite la pasada si hermes ya la completo hoy.
  Ambas usan StartWhenAvailable (FR-015). Requiere HOUSESCORE_PYTHON (Python con Playwright)
  salvo que se pase -Comando.

.EXAMPLE
  .\ops\registrar_tareas.ps1 -DestinoBackup "D:\backups\housescore"
#>
param(
    [Parameter(Mandatory = $true)][string]$DestinoBackup,
    [string]$Comando = "& '$env:HOUSESCORE_PYTHON' '$PSScriptRoot\hermes_launcher.py'",
    [string]$HoraBackup = "09:30",
    [string]$HoraScraper = "10:00"
)

if (-not $env:HOUSESCORE_PYTHON -and $PSBoundParameters.ContainsKey("Comando") -eq $false) {
    throw "Define HOUSESCORE_PYTHON (Python con Playwright) antes de registrar la tarea"
}

$ErrorActionPreference = "Stop"
$backend = Split-Path -Parent $PSScriptRoot

$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

function Registrar($nombre, $hora, $argumentos) {
    $accion = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass $argumentos" -WorkingDirectory $backend
    $disparador = New-ScheduledTaskTrigger -Daily -At $hora
    Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparador `
        -Settings $ajustes -Force | Out-Null
    Write-Host "Tarea registrada: $nombre ($hora)"
}

Registrar "HouseScore-Backup" $HoraBackup `
    ("-File `"{0}`" -Destino `"{1}`"" -f (Join-Path $backend "ops\backup.ps1"), $DestinoBackup)

Registrar "HouseScore-Scraper" $HoraScraper `
    ("-File `"{0}`" -Comando `"{1}`"" -f (Join-Path $backend "worker\scraper\run_scraper.ps1"), $Comando)
