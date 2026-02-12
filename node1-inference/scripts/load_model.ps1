param (
    [string]$model
)
if (-not $model) {
    Write-Error "No model specified."
    exit 1
}
Write-Host "🚢 Loading model: $model"
"" | ollama run $model
Write-Host "✅ Model signaled."
