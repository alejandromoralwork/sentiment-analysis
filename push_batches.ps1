param(
    [int]$BatchSize = 1,
    [string[]]$Paths = @(
        'app.py',
        'src',
        'templates',
        'latex',
        'README.md',
        'requirements.txt',
        'requirements.pinned.txt',
        'IA_Sentiment.spec',
        'build_exe.bat',
        'docs',
        '.gitignore',
        'push_batches.ps1'
    ),
    [switch]$PushOnly,
    [string]$CommitPrefix = 'Batch'
)

$ErrorActionPreference = 'Stop'

function Get-ChangedFiles {
    $status = git status --porcelain=v1 --untracked-files=all
    $files = @()

    foreach ($line in $status) {
        if ($line -match '^.{2}\s+(.*)$') {
            $path = $Matches[1].Trim()
            if ($path -match '^"(.+)"$') {
                $path = $Matches[1]
            }

            # Ignore rename source/target notation and keep the final path.
            if ($path -match '^(.*) -> (.*)$') {
                $path = $Matches[2].Trim()
            }

            $files += $path
        }
    }

    return $files
}

function Split-IntoBatches {
    param(
        [string[]]$Items,
        [int]$Size
    )

    if ($Items.Count -eq 0) {
        return @()
    }

    for ($i = 0; $i -lt $Items.Count; $i += $Size) {
        ,$Items[$i..([Math]::Min($i + $Size - 1, $Items.Count - 1))]
    }
}

# Ensure we are in a git repository.
git rev-parse --is-inside-work-tree | Out-Null

$changed = Get-ChangedFiles
if (-not $changed -or $changed.Count -eq 0) {
    Write-Host 'No changed files found.'
    exit 0
}

# Keep only the paths we actually want to process.
$selected = foreach ($file in $changed) {
    foreach ($path in $Paths) {
        $normalizedFile = $file -replace '\\', '/'
        $normalizedPath = $path -replace '\\', '/'

        if ($normalizedFile -eq $normalizedPath -or $normalizedFile.StartsWith("$normalizedPath/")) {
            $file
            break
        }
    }
}

$selected = $selected | Sort-Object -Unique
if (-not $selected -or $selected.Count -eq 0) {
    Write-Host 'No matching files found for the configured paths.'
    Write-Host 'Changed files detected:'
    $changed | Sort-Object -Unique | ForEach-Object { Write-Host "  $_" }
    exit 0
}

$batches = Split-IntoBatches -Items $selected -Size $BatchSize
if (-not $batches -or $batches.Count -eq 0) {
    Write-Host 'Nothing to process.'
    exit 0
}

$batchNumber = 1
foreach ($batch in $batches) {
    Write-Host "Processing batch $batchNumber of $($batches.Count)"
    $batch | ForEach-Object { Write-Host "  $_" }

    git add -- $batch

    if (-not $PushOnly) {
        $message = "$CommitPrefix $batchNumber"
        git commit -m $message
    }

    git push
    $batchNumber++
}

Write-Host 'Done.'
