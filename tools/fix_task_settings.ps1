# Repair the Parlevu-PublishNext schedule settings. Must run elevated.
#
# StartWhenAvailable=False means any morning the machine is asleep at 09:07 is
# skipped permanently rather than caught up, which has cost several posts.
# Set-ScheduledTask -Settings replaces the whole settings block, so this
# re-asserts the battery and timeout settings too, then verifies the action and
# trigger survived.

$ErrorActionPreference = 'Stop'
$TaskName = 'Parlevu-PublishNext'

$admin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
         ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {
    Write-Host "This must run as Administrator. Right-click PowerShell and choose Run as administrator." -ForegroundColor Red
    exit 1
}

Write-Host "Before:" -ForegroundColor Cyan
$before = (Get-ScheduledTask -TaskName $TaskName).Settings
Write-Host ("  StartWhenAvailable : " + $before.StartWhenAvailable)
Write-Host ("  ExecutionTimeLimit : " + $before.ExecutionTimeLimit)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew
Set-ScheduledTask -TaskName $TaskName -Settings $settings | Out-Null

$t = Get-ScheduledTask -TaskName $TaskName
$i = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "`nAfter:" -ForegroundColor Cyan
Write-Host ("  StartWhenAvailable   : " + $t.Settings.StartWhenAvailable)
Write-Host ("  StopIfGoingOnBatt    : " + $t.Settings.StopIfGoingOnBatteries)
Write-Host ("  ExecutionTimeLimit   : " + $t.Settings.ExecutionTimeLimit)
Write-Host ("  MultipleInstances    : " + $t.Settings.MultipleInstances)

Write-Host "`nUnchanged pieces (settings replacement can clobber these):" -ForegroundColor Cyan
Write-Host ("  Execute   : " + $t.Actions[0].Execute)
Write-Host ("  Exists    : " + (Test-Path $t.Actions[0].Execute))
Write-Host ("  Arguments : " + $t.Actions[0].Arguments)
Write-Host ("  WorkingDir: " + $t.Actions[0].WorkingDirectory)
foreach ($trg in $t.Triggers) {
    Write-Host ("  Trigger   : start=" + $trg.StartBoundary + " enabled=" + $trg.Enabled)
}
Write-Host ("  State     : " + $t.State)
Write-Host ("  NextRun   : " + $i.NextRunTime)

if ($t.Settings.StartWhenAvailable) {
    Write-Host "`nDone. A missed 09:07 will now run when the machine is next available." -ForegroundColor Green
} else {
    Write-Host "`nSetting did not take." -ForegroundColor Red
    exit 1
}
