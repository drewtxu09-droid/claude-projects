# RTSPP Extract - Scheduled Task Setup
# Run this once to register the monthly Windows Scheduled Task.
# Must be run as Administrator.

$taskName   = "RTSPP Monthly Extract"
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$batFile    = Join-Path $scriptDir "run_rtspp_extract_v2.bat"

# Verify the batch file exists
if (-not (Test-Path $batFile)) {
    Write-Error "Could not find: $batFile"
    Write-Error "Make sure setup_scheduled_task.ps1 is in the same folder as run_rtspp_extract_v2.bat"
    exit 1
}

Write-Host "Creating scheduled task: $taskName"
Write-Host "Batch file: $batFile"
Write-Host ""

# Action: run the batch file
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batFile`""

# Trigger: 2nd of every month at 8:00 AM
$trigger = New-ScheduledTaskTrigger `
    -Monthly `
    -DaysOfMonth 2 `
    -At "08:00AM"

# Settings:
#   -StartWhenAvailable  = run as soon as possible if the scheduled time was missed
#                          (covers the case where the PC was off on the 2nd)
#   -ExecutionTimeLimit  = allow up to 2 hours to complete
#   -RestartCount        = retry once if it fails (e.g. SAP timeout)
#   -RestartInterval     = wait 10 minutes before retrying
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 1 `
    -RestartInterval (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

# Register (or overwrite if already exists)
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "Scheduled task created successfully."
Write-Host ""
Write-Host "  Name    : $taskName"
Write-Host "  Runs on : 2nd of every month at 8:00 AM"
Write-Host "  If missed: runs on next login/wake"
Write-Host "  Retry   : once after 10 minutes if it fails"
Write-Host ""
Write-Host "To view or edit: open Task Scheduler -> Task Scheduler Library -> $taskName"
