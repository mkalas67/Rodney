# Run this once (as admin) to create a nightly Windows Task Scheduler job.
# The task runs kpi_refresh.py at 2:00 AM every day.
#
# Usage (in an admin PowerShell):
#   .\schedule_task.ps1

$taskName   = "KPI Dashboard Nightly Refresh"
$python     = "D:\tools\kpi-venv\Scripts\python.exe"
$script     = "D:\Rodney\kpi-dashboard\kpi_refresh.py"
$logFile    = "D:\tools\kpi-dashboard\kpi_refresh.log"
$triggerTime = "02:00"

$action  = New-ScheduledTaskAction -Execute $python -Argument "$script >> $logFile 2>&1"
$trigger = New-ScheduledTaskTrigger -Daily -At $triggerTime
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force

Write-Host "Task '$taskName' registered. Runs nightly at $triggerTime."
Write-Host "Log output: $logFile"
Write-Host ""
Write-Host "To run immediately for testing:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
