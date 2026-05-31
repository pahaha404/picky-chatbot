param(
    [string]$BaseUrl = "https://picky-chatbot-production.up.railway.app"
)

$ErrorActionPreference = "Stop"

function Get-Json($Url) {
    $raw = & curl.exe -sS --retry 3 --retry-delay 2 --retry-all-errors $Url
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to fetch $Url"
    }

    return $raw | ConvertFrom-Json
}

function Format-Percent($Value) {
    if ($null -eq $Value) {
        return "0%"
    }

    return "$Value%"
}

function Metric($Value) {
    if ($null -eq $Value) {
        return 0
    }

    return $Value
}

$base = $BaseUrl.TrimEnd("/")
$kakao = Get-Json "$base/api/kakao/growth"
$toss = Get-Json "$base/api/toss/metrics"

Write-Host "Picky growth metrics"
Write-Host "Base URL: $base"
Write-Host ""

Write-Host "Kakao"
Write-Host "  Unique users: $(Metric $kakao.uniqueUsers) / $(Metric $kakao.targetUsers)"
Write-Host "  Remaining: $(Metric $kakao.remainingUsers)"
Write-Host "  Progress: $(Format-Percent $kakao.progressPercent)"
Write-Host "  Completion rate: $(Format-Percent $kakao.completionRate)"
Write-Host "  Feedback rate: $(Format-Percent $kakao.feedbackRate)"
Write-Host "  Starts: $(Metric $kakao.events.kakao_start)"
Write-Host "  Completions: $(Metric $kakao.events.kakao_recommendation_completed)"
Write-Host "  Feedback clicks: $(Metric $kakao.events.kakao_feedback_clicked)"
Write-Host "  Share prompts: $(Metric $kakao.events.kakao_share_prompt)"
Write-Host ""

Write-Host "Kakao campaign starts"
$campaignProperties = @()
if ($null -ne $kakao.campaignStarts) {
    $campaignProperties = @($kakao.campaignStarts.PSObject.Properties)
}

if ($campaignProperties.Count -eq 0) {
    Write-Host "  None yet"
} else {
    $campaignProperties |
        Sort-Object Value -Descending |
        ForEach-Object { Write-Host "  $($_.Name): $($_.Value)" }
}
Write-Host ""

Write-Host "Toss"
Write-Host "  Unique users: $(Metric $toss.uniqueUsers)"
Write-Host "  Total events: $(Metric $toss.eventsTotal)"
Write-Host "  App opens: $(Metric $toss.events.app_open)"
Write-Host "  Completions: $(Metric $toss.events.recommendation_completed)"
Write-Host "  Shares: $(Metric $toss.events.share_clicked)"
Write-Host ""

if ($kakao.uniqueUsers -lt 50) {
    Write-Host "Next action: push Day 1 direct tester loop until Kakao reaches 50 users."
} elseif ($kakao.completionRate -lt 55) {
    Write-Host "Next action: improve Kakao question flow because completion is below 55%."
} elseif ($kakao.feedbackRate -lt 10) {
    Write-Host "Next action: ask users to click feedback and improve result card CTA."
} else {
    Write-Host "Next action: repeat the best campaign keyword and scale posting."
}
