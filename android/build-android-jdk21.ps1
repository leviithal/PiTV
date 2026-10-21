# PiTV V3 - Windows build fix for a user profile containing '&' and spaces.
# Selects Java 21/17 (not Android Studio Java 25) and uses temporary SUBST drive.
$ErrorActionPreference = 'Stop'
$drive = $null
$substCreated = $false
$originalJavaHome = $env:JAVA_HOME
$originalPath = $env:Path
$originalAndroidHome = $env:ANDROID_HOME
$originalGradleHome = $env:GRADLE_USER_HOME
$originalLocalAppData = $env:LOCALAPPDATA
$pushed = $false

try {
    # IMPORTANT: Gradle 8.11.1 does not support running on Java 25.
    # Select a real JDK 21 or 17. Never blindly prefer Android Studio JBR.
    $jdkCandidates = New-Object System.Collections.Generic.List[string]
    if ($env:JAVA_HOME) { $jdkCandidates.Add($env:JAVA_HOME) }

    $searchRoots = @(
        (Join-Path $env:ProgramFiles 'Eclipse Adoptium'),
        (Join-Path $env:ProgramFiles 'Microsoft'),
        (Join-Path $env:ProgramFiles 'Java'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Eclipse Adoptium'),
        (Join-Path $env:ProgramFiles 'Android\Android Studio')
    )
    foreach ($root in $searchRoots) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        if ($root -like '*Android Studio') {
            $jdkCandidates.Add((Join-Path $root 'jbr'))
        } else {
            foreach ($dir in Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue) {
                $jdkCandidates.Add($dir.FullName)
            }
        }
    }

    $eligible = @()
    foreach ($candidate in ($jdkCandidates | Select-Object -Unique)) {
        $javaExe = Join-Path $candidate 'bin\java.exe'
        $javacExe = Join-Path $candidate 'bin\javac.exe'
        if (-not ((Test-Path -LiteralPath $javaExe) -and (Test-Path -LiteralPath $javacExe))) { continue }
        # Java --version writes to stdout (unlike java -version), safe with Stop.
        $ver = (& $javaExe --version | Out-String)
        if ($LASTEXITCODE -ne 0) { continue }
        if ($ver -match '(?m)^(?:openjdk|java)\s+(\d+)') {
            $major = [int]$Matches[1]
            if ($major -eq 21 -or $major -eq 17) {
                $eligible += [PSCustomObject]@{ Path = $candidate; Major = $major }
            }
        }
    }
    if (-not $eligible) {
        throw 'Java 17 eller 21 saknas. Installera med: winget install --id EclipseAdoptium.Temurin.21.JDK --exact --source winget'
    }
    # Prefer Java 21; Java 17 is a fully supported fallback.
    $selected = $eligible | Sort-Object -Property Major -Descending | Select-Object -First 1
    $env:JAVA_HOME = $selected.Path
    $env:Path = "$(Join-Path $env:JAVA_HOME 'bin');$originalPath"
    Write-Host "Vald Java $($selected.Major): $env:JAVA_HOME" -ForegroundColor Cyan
    & (Join-Path $env:JAVA_HOME 'bin\java.exe') -version
    if ($LASTEXITCODE -ne 0) { throw 'Java kunde inte startas.' }

    # Pick a free drive letter for a temporary alias to the actual user folder.
    foreach ($letter in @('P','Q','R','S','T','V','W','X','Y','Z')) {
        if (-not (Get-PSDrive -Name $letter -ErrorAction SilentlyContinue)) {
            $drive = "${letter}:"
            break
        }
    }
    if (-not $drive) { throw 'Ingen ledig enhetsbokstav for SUBST. Frigör t.ex. P:.' }
    if (-not $PSScriptRoot.StartsWith($env:USERPROFILE, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Placera skriptet i Android-mappen under din Windows-användarprofil.'
    }
    & (Join-Path $env:SystemRoot 'System32\subst.exe') $drive $env:USERPROFILE
    if ($LASTEXITCODE -ne 0) { throw "Kunde inte skapa en tillfällig enhet $drive" }
    $substCreated = $true
    Write-Host "Tillfallig enhet $drive anvands for att undvika & i sokvagen." -ForegroundColor Cyan

    $aliasFolder = $drive + $PSScriptRoot.Substring($env:USERPROFILE.Length)
    $project = Join-Path $aliasFolder 'PiTVRemote'
    if (-not (Test-Path (Join-Path $project 'settings.gradle.kts'))) {
        throw "Hittar inte Android-projektet under $project"
    }

    # Gradle script, project path and caches all use the temporary drive letter.
    $env:LOCALAPPDATA = $drive + '\AppData\Local'
    $env:GRADLE_USER_HOME = $drive + '\.gradle-pitv'
    $androidSdk = if ($originalAndroidHome) { $originalAndroidHome } else { Join-Path $originalLocalAppData 'Android\Sdk' }
    if ($androidSdk.StartsWith($env:USERPROFILE, [System.StringComparison]::OrdinalIgnoreCase)) {
        $androidSdk = $drive + $androidSdk.Substring($env:USERPROFILE.Length)
    }
    $env:ANDROID_HOME = $androidSdk
    if (-not (Test-Path (Join-Path $androidSdk 'platforms\android-35\android.jar'))) {
        throw "Android SDK Platform 35 saknas: $androidSdk"
    }

    $gradleVersion = '8.11.1'
    $cache = Join-Path $env:LOCALAPPDATA 'PiTVBuild'
    $zip = Join-Path $cache "gradle-$gradleVersion-bin.zip"
    $gradleExe = Join-Path $cache "gradle-$gradleVersion\bin\gradle.bat"
    New-Item -ItemType Directory -Force -Path $cache | Out-Null
    if (-not (Test-Path $gradleExe)) {
        Write-Host 'Laddar ner och packar upp Gradle 8.11.1 ...' -ForegroundColor Cyan
        Invoke-WebRequest -Uri "https://services.gradle.org/distributions/gradle-$gradleVersion-bin.zip" -OutFile $zip
        Expand-Archive -Path $zip -DestinationPath $cache -Force
    }

    # local.properties is restored to the normal Windows SDK path after this build.
    $propsPath = Join-Path $project 'local.properties'
    $originalProps = if (Test-Path $propsPath) { [System.IO.File]::ReadAllText($propsPath) } else { $null }
    $propsExisted = Test-Path $propsPath
    try {
        $sdkInProps = $androidSdk.Replace('\','/')
        Set-Content -Path $propsPath -Value "sdk.dir=$sdkInProps" -Encoding Ascii
        Push-Location $project
        $pushed = $true
        Write-Host 'Bygger APK med Gradle ...' -ForegroundColor Cyan
        & $gradleExe --no-daemon :app:assembleDebug
        if ($LASTEXITCODE -ne 0) { throw 'Gradle-bygget misslyckades. Se det forsta ERROR-meddelandet ovan.' }
        $apk = Join-Path $project 'app\build\outputs\apk\debug\app-debug.apk'
        if (-not (Test-Path $apk)) { throw 'Gradle rapporterade framgang men APK-filen saknas.' }
        $dest = Join-Path $PSScriptRoot 'PiTV-Remote-installera-pa-Android.apk'
        Copy-Item -LiteralPath $apk -Destination $dest -Force
        Write-Host "APK skapad: $dest" -ForegroundColor Green
    }
    finally {
        if ($pushed) { Pop-Location; $pushed = $false }
        if ($propsExisted) { [System.IO.File]::WriteAllText($propsPath, $originalProps) }
        elseif (Test-Path $propsPath) { Remove-Item -LiteralPath $propsPath -Force }
    }
}
finally {
    $env:JAVA_HOME = $originalJavaHome
    $env:Path = $originalPath
    $env:ANDROID_HOME = $originalAndroidHome
    $env:GRADLE_USER_HOME = $originalGradleHome
    $env:LOCALAPPDATA = $originalLocalAppData
    if ($substCreated) {
        & (Join-Path $env:SystemRoot 'System32\subst.exe') $drive /D 2>$null | Out-Null
    }
}
