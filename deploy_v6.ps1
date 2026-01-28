# VPS Email Finder - Deployment Script v6
# Deploys backend changes to production VPS

Write-Host "=== VPS Email Finder v6 Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$VPS_HOST = "192.3.81.106"
$VPS_USER = "root"
$VPS_PATH = "/root/vps-email-finder"

Write-Host "Step 1: Running local tests..." -ForegroundColor Yellow
cd backend
$testResult = python -m pytest tests/ -v --tb=no -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Some tests failed. Continue anyway? (y/n)" -ForegroundColor Red
    $continue = Read-Host
    if ($continue -ne "y") {
        Write-Host "Deployment cancelled." -ForegroundColor Red
        exit 1
    }
}
Write-Host "✓ Tests completed" -ForegroundColor Green
cd ..

Write-Host ""
Write-Host "Step 2: Copying files to VPS..." -ForegroundColor Yellow

# Copy modified backend files
scp backend/config.py "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/backend/"
scp backend/models.py "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/backend/"
scp backend/main.py "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/backend/"
scp backend/core/email_finder.py "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/backend/core/"

Write-Host "✓ Files copied" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Restarting service on VPS..." -ForegroundColor Yellow

# Restart service
ssh "${VPS_USER}@${VPS_HOST}" "systemctl restart email-finder"
Start-Sleep -Seconds 2

Write-Host "✓ Service restarted" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Running smoke tests..." -ForegroundColor Yellow

# Test health endpoint
Write-Host "  - Testing /health endpoint..." -ForegroundColor Gray
$healthResponse = curl -s "http://${VPS_HOST}:8000/health" | ConvertFrom-Json
if ($healthResponse.status -eq "healthy") {
    Write-Host "    ✓ Health: $($healthResponse.status), Version: $($healthResponse.version)" -ForegroundColor Green
} else {
    Write-Host "    ✗ Health check failed!" -ForegroundColor Red
    exit 1
}

# Test find-email endpoint
Write-Host "  - Testing /api/find-email..." -ForegroundColor Gray
$findEmailResponse = curl -s -X POST "http://${VPS_HOST}:8000/api/find-email" `
    -H "Content-Type: application/json" `
    -d '{"domain":"auraia.ch","fullName":"Adrian Turion"}' | ConvertFrom-Json
if ($findEmailResponse.status -eq "valid" -or $findEmailResponse.status -eq "catch_all") {
    Write-Host "    ✓ Find email: $($findEmailResponse.status)" -ForegroundColor Green
} else {
    Write-Host "    ✗ Find email failed: $($findEmailResponse.status)" -ForegroundColor Red
}

# Test check-email endpoint
Write-Host "  - Testing /api/check-email..." -ForegroundColor Gray
$checkEmailResponse = curl -s -X POST "http://${VPS_HOST}:8000/api/check-email" `
    -H "Content-Type: application/json" `
    -d '{"email":"adrian.turion@auraia.ch"}' | ConvertFrom-Json
if ($checkEmailResponse.status -eq "valid") {
    Write-Host "    ✓ Check email: $($checkEmailResponse.status)" -ForegroundColor Green
} else {
    Write-Host "    ⚠️  Check email: $($checkEmailResponse.status)" -ForegroundColor Yellow
}

# Test bulk-search-json endpoint
Write-Host "  - Testing /api/bulk-search-json..." -ForegroundColor Gray
$bulkSearchResponse = curl -s -X POST "http://${VPS_HOST}:8000/api/bulk-search-json" `
    -H "Content-Type: application/json" `
    -d '{"searches":[{"domain":"google.com","fullName":"Test User"}]}' | ConvertFrom-Json
if ($bulkSearchResponse.total -eq 1) {
    Write-Host "    ✓ Bulk search: $($bulkSearchResponse.results[0].status)" -ForegroundColor Green
} else {
    Write-Host "    ✗ Bulk search failed" -ForegroundColor Red
}

# Test cache stats
Write-Host "  - Testing /api/cache/stats..." -ForegroundColor Gray
$cacheResponse = curl -s "http://${VPS_HOST}:8000/api/cache/stats" | ConvertFrom-Json
Write-Host "    ✓ Cache: $($cacheResponse.hit_rate) hit rate, $($cacheResponse.cached_domains) domains" -ForegroundColor Green

Write-Host ""
Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "New endpoints available:" -ForegroundColor Cyan
Write-Host "  - GET  http://${VPS_HOST}:8000/health" -ForegroundColor White
Write-Host "  - POST http://${VPS_HOST}:8000/api/check-email" -ForegroundColor White
Write-Host "  - POST http://${VPS_HOST}:8000/api/bulk-search-json" -ForegroundColor White
Write-Host ""
Write-Host "View logs: ssh ${VPS_USER}@${VPS_HOST} 'tail -f /root/logs/email_finder.log'" -ForegroundColor Gray
