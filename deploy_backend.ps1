# Complete VPS Backend Deployment Script (PowerShell)

$VPS_IP = "192.3.81.106"
$VPS_USER = "root"
$APP_DIR = "/opt/email_finder_2/backend"

Write-Host "Starting VPS Backend Deployment..." -ForegroundColor Cyan

Write-Host ""
Write-Host "Step 1: Creating application directory on VPS..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "mkdir -p $APP_DIR"

Write-Host ""
Write-Host "Step 2: Transferring backend files..." -ForegroundColor Yellow
scp -r backend\* ${VPS_USER}@${VPS_IP}:${APP_DIR}/

Write-Host ""
Write-Host "Step 3: Setting up Python environment..." -ForegroundColor Yellow
$setupCommands = @"
cd /opt/email_finder_2/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
"@
ssh ${VPS_USER}@${VPS_IP} $setupCommands

Write-Host ""
Write-Host "Step 4: Verifying .env configuration..." -ForegroundColor Yellow
ssh ${VPS_USER}@${VPS_IP} "cat $APP_DIR/.env"

Write-Host ""
Write-Host "Step 5: Starting the server..." -ForegroundColor Yellow
$startCommands = @"
cd /opt/email_finder_2/backend
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/email_finder.log 2>&1 &
echo "Server started. PID: `$!"
sleep 2
ps aux | grep uvicorn | grep -v grep
"@
ssh ${VPS_USER}@${VPS_IP} $startCommands

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "API URL: http://${VPS_IP}:8000" -ForegroundColor Cyan
Write-Host "Logs: ssh ${VPS_USER}@${VPS_IP} 'tail -f /var/log/email_finder.log'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test with:" -ForegroundColor Yellow
Write-Host "curl -X POST http://${VPS_IP}:8000/api/find-email ``" -ForegroundColor White
Write-Host "  -H 'Content-Type: application/json' ``" -ForegroundColor White
Write-Host "  -d '{`"domain`":`"outlook.com`",`"fullName`":`"Satya Nadella`"}'" -ForegroundColor White
