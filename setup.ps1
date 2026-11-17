#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw 'Run this script in 64-bit Windows PowerShell on Windows x64.'
}

$toolsDir = Join-Path $PSScriptRoot 'video-tools'
$runtime = Join-Path $toolsDir '.runtime'
$downloads = Join-Path $runtime 'downloads'
New-Item -ItemType Directory -Path $downloads -Force | Out-Null

function Invoke-Native {
    param([string]$File, [string[]]$Arguments)
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$File exited with code $LASTEXITCODE." }
}

function Get-Download {
    param([string]$Url, [string]$Name, [string]$Sha256)
    $file = Join-Path $downloads $Name
    if ((Test-Path -LiteralPath $file) -and
        (!$Sha256 -or (Get-FileHash -LiteralPath $file).Hash -eq $Sha256)) { return $file }

    $temporary = "$file.partial"
    Write-Host "Downloading $Name"
    Invoke-WebRequest -Uri $Url -OutFile $temporary -UseBasicParsing
    if ($Sha256 -and (Get-FileHash -LiteralPath $temporary).Hash -ne $Sha256) {
        throw "SHA-256 verification failed for $Name."
    }
    Move-Item -LiteralPath $temporary -Destination $file -Force
    return $file
}

function Install-Archive {
    param([string]$Url, [string]$Destination, [string]$Name, [string]$Sha256, [string]$TopFolder)
    if (Test-Path -LiteralPath $Destination) { return }
    $file = Get-Download $Url $Name $Sha256
    $stage = Join-Path $runtime ([guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stage | Out-Null
    try {
        # bsdtar handles large archives and Unicode paths on Windows.
        Invoke-Native 'tar.exe' @('-xf', $file, '-C', $stage)
        $content = if ($TopFolder) { Join-Path $stage $TopFolder } else { $stage }
        Move-Item -LiteralPath $content -Destination $Destination
    } finally {
        if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Force -Recurse }
    }
}

function Install-Source {
    param([string]$Repository, [string]$Folder, [string]$Commit)
    $destination = Join-Path $toolsDir $Folder
    $marker = Join-Path $destination '.workflow-commit'
    if ((Test-Path -LiteralPath $destination) -and
        (!(Test-Path -LiteralPath $marker) -or (Get-Content -LiteralPath $marker -Raw).Trim() -ne $Commit)) {
        throw "Move the existing $Folder directory elsewhere before setup. Setup preserves existing source trees."
    }
    Install-Archive "https://github.com/$Repository/archive/$Commit.zip" $destination "${Folder}-$Commit.zip" '' "${Folder}-$Commit"
    Set-Content -LiteralPath $marker -Value $Commit -Encoding Ascii
}

$uv = Join-Path $runtime 'uv'
$node = Join-Path $runtime 'node'
Install-Archive 'https://github.com/astral-sh/uv/releases/download/0.9.11/uv-x86_64-pc-windows-msvc.zip' $uv 'uv-0.9.11.zip' '45a3ff2a68c246ed9fd2d9df032496c1beebe480357f356ac25d2cb144884c30' ''
Install-Archive 'https://nodejs.org/dist/v24.22.1/node-v24.22.1-win-x64.zip' $node 'node-v24.22.1.zip' 'd2046d28c2c3dcd211ac5145c0bf30e2047ef9dfb306693c8c6e2eccd8b95fa5' 'node-v24.22.1-win-x64'
$ffmpeg = 'ffmpeg-8.0.1-essentials_build'
Install-Archive "https://github.com/GyanD/codexffmpeg/releases/download/8.0.1/$ffmpeg.zip" (Join-Path $runtime $ffmpeg) "$ffmpeg.zip" 'e2aaeaa0fdbc397d4794828086424d4aaa2102cef1fb6874f6ffd29c0b88b673' $ffmpeg

Install-Source 'renezander030/capcut-cli' 'capcut-cli' '0c93e8fd981db9d88a4013c675720ea5313c93e7'
Install-Source 'OpenMontageInc/OpenMontage' 'OpenMontage' '2e003e65fa99a0f329478a2c1cdcf26bc481933a'
Install-Source 'Vibha-Ramprakash/claude-video-effects' 'claude-video-effects' '60840acc7e126a5e34068276a23e912ec4c8c34c'

$env:UV_PYTHON_INSTALL_DIR = Join-Path $runtime 'python'
$env:UV_CACHE_DIR = Join-Path $runtime 'uv-cache'
$uvExe = Join-Path $uv 'uv.exe'
$venv = Join-Path $runtime 'venv'
$python = Join-Path $venv 'Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) {
    Invoke-Native $uvExe @('venv', '--managed-python', '--python', '3.12.12', $venv)
}
Invoke-Native $uvExe @('pip', 'install', '--python', $python, '-r', (Join-Path $toolsDir 'requirements.txt'))

$env:PATH = "$node;$env:PATH"
$env:HUSKY = '0'
Push-Location (Join-Path $toolsDir 'capcut-cli')
try {
    Invoke-Native (Join-Path $node 'npm.cmd') @('ci', '--no-audit', '--no-fund')
    Invoke-Native (Join-Path $node 'npm.cmd') @('run', 'build')
} finally {
    Pop-Location
}

$concat = Join-Path $env:LOCALAPPDATA 'Programs\Concat\concat.exe'
if (!(Test-Path -LiteralPath $concat)) {
    $asset = 'Concat-0.2.9-windows-x86_64-setup.exe'
    $installer = Get-Download "https://github.com/jub0t/Concat/releases/download/v0.2.9/$asset" $asset 'bc3e994a592d46c9dce037bf0b41e329de7b3821c25bc27717a8e0d5d34d1a0a'
    Write-Host 'Installing Concat for the current Windows user.'
    $process = Start-Process -FilePath $installer -ArgumentList '/S' -Wait -PassThru -WindowStyle Hidden
    if ($process.ExitCode -ne 0) { throw "Concat installer exited with code $($process.ExitCode)." }
}
Invoke-Native (Join-Path $toolsDir 'concat-desk.cmd') @('doctor')
