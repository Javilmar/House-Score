<#
.SYNOPSIS
  Registra las tareas programadas de Windows del backend (T048, T051).

.DESCRIPTION
  - HouseScore-Backup: lanza ops\backup.ps1 cada dia (siempre).
  - HouseScore-Scraper: lanza worker\scraper\run_scraper.ps1 cada dia. Es OPCIONAL (-Comando):
    el scraper ya lo programa el cron de hermes (job "Buscador Pisos", 09:00) a traves de
    ops\hermes_launcher.py; registrar ademas esta tarea lo ejecutaria dos veces.
  Ambas usan StartWhenAvailable: si el equipo estaba apagado a la hora programada, la tarea se
  ejecuta en cuanto vuelve a encenderse (FR-015).

.EXAMPLE
  .\ops\registrar_tareas.ps1 -DestinoBackup "D:\backups\housescore"
#>
param(
    [Parameter(Mandatory = $true)][string]$DestinoBackup,
    [string]$Comando,
    [string]$HoraBackup = "09:30",
    [string]$HoraScraper = "08:00"
)

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

if ($Comando) {
    Registrar "HouseScore-Scraper" $HoraScraper `
        ("-File `"{0}`" -Comando `"{1}`"" -f (Join-Path $backend "worker\scraper\run_scraper.ps1"), $Comando)
}
