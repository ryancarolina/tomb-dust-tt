$log = Join-Path $PSScriptRoot "..\app\logs\session-2026-05-22.jsonl" | Resolve-Path
$watchTypes = @(
    'player_input', 'creation_step', 'creation_advanced', 'tool_call',
    'api_error', 'creation_drift', 'narration_verify_fail', 'narration_verify_exhausted',
    'creation_finalize', 'gm_narration'
)
$pos = (Get-Item $log).Length
Write-Output "SESSION_MONITOR_START offset=$pos"
while ($true) {
    Start-Sleep -Seconds 3
    $item = Get-Item $log -ErrorAction SilentlyContinue
    if (-not $item -or $item.Length -le $pos) { continue }

    $stream = [System.IO.File]::Open(
        $log,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::ReadWrite
    )
    $null = $stream.Seek($pos, [System.IO.SeekOrigin]::Begin)
    $reader = New-Object System.IO.StreamReader($stream)
    $newLines = [System.Collections.Generic.List[string]]::new()
    while ($null -ne ($line = $reader.ReadLine())) {
        if ($line.Trim()) { $newLines.Add($line) }
    }
    $reader.Close()
    $stream.Close()
    $pos = $item.Length

    if ($newLines.Count -eq 0) { continue }

    $blob = $newLines -join "`n"
    $isPytestBatch = $blob -match 'Test narration\.|pytest-of-PC\\pytest'
    $hasLiveMarker = $blob -match 'play\\workspace|"type":\s*"(api_error|creation_drift|narration_verify_fail|narration_verify_exhausted)"'
    $hasWatchEvent = $false
    foreach ($line in $newLines) {
        foreach ($t in $watchTypes) {
            if ($line -match ('"type":\s*"' + [regex]::Escape($t) + '"')) {
                $hasWatchEvent = $true
                break
            }
        }
        if ($hasWatchEvent) { break }
    }

    if ($hasWatchEvent -and (-not $isPytestBatch -or $hasLiveMarker)) {
        $payload = '{"prompt":"Session log monitor: read app/logs/session-2026-05-22.jsonl new events and post a brief turn report (input, step, tools, errors). Flag anything unhealthy."}'
        Write-Output "AGENT_LOOP_WAKE_SESSION_LOG $payload"
    }
}
