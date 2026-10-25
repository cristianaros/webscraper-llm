param([Parameter(Mandatory)][string]$ProjectRoot)
$ErrorActionPreference='Stop'; $root=(Resolve-Path -LiteralPath $ProjectRoot).Path; $wrapper=Join-Path $root 'scripts\windows\run-collector.ps1'
$arguments='-NoProfile -NonInteractive -WindowStyle Hidden -File "'+$wrapper+'" -ProjectRoot "'+$root+'"'
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $root
$repeat=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15)
$startup=New-ScheduledTaskTrigger -AtStartup
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 14) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$credential=Get-Credential -Message 'Cuenta de Windows que ejecutará UniNews sin iniciar sesión'
$existing=Get-ScheduledTask -TaskName 'UniNews Collector' -ErrorAction SilentlyContinue
if($existing){
    Set-ScheduledTask -TaskName 'UniNews Collector' -Action $action -Trigger @($repeat,$startup) -Settings $settings -User $credential.UserName -Password $credential.GetNetworkCredential().Password | Out-Null
} else {
    Register-ScheduledTask -TaskName 'UniNews Collector' -Action $action -Trigger @($repeat,$startup) -Settings $settings -User $credential.UserName -Password $credential.GetNetworkCredential().Password | Out-Null
}
