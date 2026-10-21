param(
    [Parameter(Mandatory=$true)][string]$PiIp,
    [string]$PiUser = 'pi'
)
$ErrorActionPreference='Stop'
$parsed = $null
if (-not [System.Net.IPAddress]::TryParse($PiIp, [ref]$parsed) -or $parsed.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw 'Ange Raspberry Pi:ns IPv4-adress, till exempel 192.168.1.50.'
}
if ($PiUser -notmatch '^[a-z_][a-z0-9_-]*$') { throw 'Otillåtet SSH-användarnamn.' }
$source = Join-Path $PSScriptRoot 'Pi'
if (!(Test-Path (Join-Path $source 'install-v3.sh'))) { throw 'Pi/install-v3.sh saknas i det uppackade paketet.' }
$target = "${PiUser}@${PiIp}"
Write-Host "Skapar uppladdningsmappen hos $target ..."
& ssh $target 'mkdir -p ~/pitv-v3-upload'
if ($LASTEXITCODE -ne 0) { throw 'SSH misslyckades. Kontrollera adress, SSH och användare.' }
Write-Host 'Kopierar PiTV V3 ...'
& scp -r $source "${target}:~/pitv-v3-upload/"
if ($LASTEXITCODE -ne 0) { throw 'SCP misslyckades.' }
Write-Host 'Klart! Anslut med:' -ForegroundColor Green
Write-Host "ssh $target"
Write-Host 'Kör därefter: bash ~/pitv-v3-upload/Pi/install-v3.sh'
