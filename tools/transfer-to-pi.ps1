# Run from Windows PowerShell. Copies this repository to a NEW Raspberry Pi over SCP.
param(
    [Parameter(Mandatory=$true)][string]$PiIp,
    [string]$PiUser = "pi"
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$target = "${PiUser}@${PiIp}"
Write-Host "Uploading PiTV repository from $repo to $target"
& scp.exe -r $repo "${target}:~/"
if ($LASTEXITCODE -ne 0) { throw "SCP failed with exit code $LASTEXITCODE" }
Write-Host "Ready. SSH: ssh $target"
Write-Host 'Then: cd ~/PiTV-GitHub && bash installer/install-fresh-pi.sh --preflight'
