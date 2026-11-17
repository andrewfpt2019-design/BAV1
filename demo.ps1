#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$toolsDir = Join-Path $PSScriptRoot 'video-tools'
$bridge = Join-Path $toolsDir 'concat-desk.cmd'
$ffmpeg = Join-Path $toolsDir '.runtime\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe'
$node = Join-Path $toolsDir '.runtime\node\node.exe'
$capcut = Join-Path $toolsDir 'capcut-cli\dist\index.js'
if (!(Test-Path -LiteralPath $ffmpeg)) { throw 'Run setup.ps1 before the demo.' }
$env:PATH = "$(Split-Path -Parent $ffmpeg);$env:PATH"

function Invoke-Checked {
    param([string]$File, [string[]]$Arguments)
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$File exited with code $LASTEXITCODE." }
}

$parent = Join-Path $PSScriptRoot ('outputs\demo-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $parent -Force | Out-Null
$project = Join-Path $parent 'Demo Concat'
$clip1 = Join-Path $parent 'clip-1.mp4'
$clip2 = Join-Path $parent 'clip-2.mp4'

function New-TestClip {
    param([string]$Color, [int]$Frequency, [string]$OutputFile)
    Invoke-Checked $ffmpeg @(
        '-hide_banner', '-loglevel', 'error',
        '-f', 'lavfi', '-i', "color=c=${Color}:s=360x640:r=30:d=2",
        '-f', 'lavfi', '-i', "sine=frequency=${Frequency}:sample_rate=48000:duration=2",
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', $OutputFile
    )
}

New-TestClip 'teal' 440 $clip1
New-TestClip 'orange' 660 $clip2
Invoke-Checked $bridge @('new', $project, '--width', '360', '--height', '640')
Invoke-Checked $bridge @('add', $project, $clip1)
Invoke-Checked $bridge @('stitch', $project, $clip1, $clip2)
Invoke-Checked $bridge @('effect', $project, 'moody', $clip2, '--width', '360')

$silent = Join-Path $parent 'silent.mp4'
$audio = Join-Path $parent 'audio.wav'
Invoke-Checked $ffmpeg @('-v', 'error', '-i', $clip1, '-an', '-c:v', 'copy', $silent)
Invoke-Checked $ffmpeg @('-v', 'error', '-i', $clip1, '-vn', $audio)
$drafts = Join-Path $parent 'drafts'
New-Item -ItemType Directory -Path $drafts | Out-Null
$draftName = 'CapCut Demo'
$draft = Join-Path $drafts $draftName
Invoke-Checked $node @($capcut, 'init', $draftName, '--drafts', $drafts, '--template', 'bundled', '--width', '360', '--height', '640')
Invoke-Checked $node @($capcut, 'add-video', $draft, $silent, '0', '2')
Invoke-Checked $node @($capcut, 'add-audio', $draft, $audio, '0', '2')
Invoke-Checked $bridge @('capcut', $project, $draft)

$saved = Invoke-Checked $bridge @('inspect', $project) | ConvertFrom-Json
if ($saved.timeline.clips.Count -ne 4 -or
    @($saved.media | Where-Object { $_.hasAudio }).Count -ne 4 -or
    [math]::Abs($saved.timeline.duration - 10) -gt 0.12) {
    throw 'Expected four clips with audio and a timeline of about ten seconds.'
}
Write-Host ('Verified {0} clips with audio. Timeline duration: {1:F2} seconds.' -f $saved.timeline.clips.Count, $saved.timeline.duration)
Write-Host "Open this project folder in Concat: $project"
