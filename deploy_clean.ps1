# Clean VPS Deployment Script - PowerShell
# Excludes venv, __pycache__, and other unnecessary files

$VPS_IP = "192.3.81.106"
$VPS_USER = "root"

Write-Host "Step 1: Creating clean deployment package..." -ForegroundColor Yellow

# Create temporary directory for clean files
$tempDir = "backend_clean"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy only necessary files
Write-Host "Copying essential files..." -ForegroundColor Cyan
Copy-Item -Path "backend\core" -Destination "$tempDir\core" -Recurse
Copy-Item -Path "backend\main.py" -Destination "$tempDir\"
Copy-Item -Path "backend\models.py" -Destination "$tempDir\"
Copy-Item -Path "backend\database.py" -Destination "$tempDir\"
Copy-Item -Path "backend\requirements.txt" -Destination "$tempDir\"
Copy-Item -Path "backend\.env" -Destination "$tempDir\"

# Create ZIP
Write-Host "Creating deployment package..." -ForegroundColor Cyan
$zipPath = "deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath

# Cleanup temp directory
Remove-Item -Recurse -Force $tempDir

Write-Host ""
Write-Host "Step 2: Uploading to VPS..." -ForegroundColor Yellow
scp $zipPath ${VPS_USER}@${VPS_IP}:/root/

Write-Host ""
Write-Host "Step 3: Installing on VPS..." -ForegroundColor Yellow
$installCommands = @"
# Clean up previous deployment
rm -rf /root/backend

# Install unzip if needed
apt install -y unzip

# Prepare directory
mkdir -p /root/backend
mv /root/deploy.zip /root/backend/
cd /root/backend
unzip -q deploy.zip
rm deploy.zip

# Create clean Linux venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Start server
echo "Starting server..."
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/email_finder.log 2>&1 &
sleep 2
echo "Server PID: `$!"
ps aux | grep uvicorn | grep -v grep
"@

ssh ${VPS_USER}@${VPS_IP} $installCommands

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "API: http://${VPS_IP}:8000" -ForegroundColor Cyan
Write-Host "Logs: ssh ${VPS_USER}@${VPS_IP} 'tail -f /var/log/email_finder.log'" -ForegroundColor Cyan

# Cleanup local ZIP
Remove-Item -Force $zipPath
