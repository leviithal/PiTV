# PiTV V3 native Android build. Run in PowerShell on Windows (not Raspberry Pi).
$ErrorActionPreference = 'Stop'
$project = Join-Path $PSScriptRoot 'PiTVRemote'
$androidSdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
if (!(Test-Path (Join-Path $androidSdk 'platforms\android-35\android.jar'))) {
  Write-Host 'Android SDK API 35 saknas. Installera Android Studio och SDK Platform 35 via SDK Manager.' -ForegroundColor Red
  exit 1
}
$gradleVersion = '8.11.1'
$cache = Join-Path $env:LOCALAPPDATA 'PiTVBuild'
$zip = Join-Path $cache "gradle-$gradleVersion-bin.zip"
$gradleExe = Join-Path $cache "gradle-$gradleVersion\bin\gradle.bat"
New-Item -ItemType Directory -Force -Path $cache | Out-Null
if (!(Test-Path $gradleExe)) {
  Write-Host 'Laddar ner Gradle 8.11.1 (engangskrav pa internetanslutning)...'
  Invoke-WebRequest "https://services.gradle.org/distributions/gradle-$gradleVersion-bin.zip" -OutFile $zip
  Expand-Archive -Path $zip -DestinationPath $cache -Force
}
$sdkProp = ($androidSdk -replace '\\','/')
Set-Content -Path (Join-Path $project 'local.properties') -Value "sdk.dir=$sdkProp" -Encoding ascii
Push-Location $project
try {
  & $gradleExe --no-daemon :app:assembleDebug
  if ($LASTEXITCODE -ne 0) { throw 'Gradle-bygget misslyckades.' }
  $apk = Join-Path $project 'app\build\outputs\apk\debug\app-debug.apk'
  if (!(Test-Path $apk)) { throw 'APK-filen saknas trots avslutat bygge.' }
  $destination = Join-Path $PSScriptRoot 'PiTV-Remote-installera-pa-Android.apk'
  Copy-Item $apk $destination -Force
  Write-Host "APK skapad: $destination" -ForegroundColor Green
} finally { Pop-Location }
