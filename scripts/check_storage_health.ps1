param(
    [string]$BaseUrl = "https://picky-chatbot-production.up.railway.app"
)

$ErrorActionPreference = "Stop"
$base = $BaseUrl.TrimEnd("/")

function Get-Json($Url) {
    try {
        return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 20
    }
    catch {
        Write-Error "Failed to fetch $Url. $($_.Exception.Message)"
    }
}

$health = Get-Json "$base/api/ops/storage"

Write-Host "Picky storage health"
Write-Host "  Supabase configured: $($health.supabaseConfigured)"
Write-Host "  Metrics persistence: $($health.metricsPersistence)"

foreach ($property in @($health.tables.PSObject.Properties)) {
    $table = $property.Name
    $status = $property.Value
    Write-Host "  $table`: $($status.persistence)"

    if (-not $status.ok) {
        Write-Host "    Error: $($status.error)"
    }
}

if ($health.metricsPersistence -ne "supabase") {
    Write-Host ""
    Write-Host "Next action: run docs/kakao-supabase-events.sql and docs/toss-supabase-events.sql in the production Supabase SQL Editor."
}
