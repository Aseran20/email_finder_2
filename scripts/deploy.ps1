# Déploiement simplifié VPS
# Usage: .\scripts\deploy.ps1

$VPS_IP = "192.3.81.106"
$VPS_USER = "root"
$VPS_PATH = "/root/vps-email-finder/backend"

Write-Host "=== Déploiement Email Finder ===" -ForegroundColor Cyan
Write-Host ""

# Vérifier la connexion SSH
Write-Host "1. Test connexion SSH..." -ForegroundColor Yellow
ssh $VPS_USER@$VPS_IP "echo 'Connected'" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Connexion SSH échouée. Vérifier la clé SSH." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Connexion OK" -ForegroundColor Green
Write-Host ""

# Copier les fichiers modifiés
Write-Host "2. Copie des fichiers..." -ForegroundColor Yellow
scp backend/core/email_finder.py $VPS_USER@${VPS_IP}:$VPS_PATH/core/
scp backend/core/mx_cache.py $VPS_USER@${VPS_IP}:$VPS_PATH/core/
scp backend/core/logger.py $VPS_USER@${VPS_IP}:$VPS_PATH/core/
scp backend/main.py $VPS_USER@${VPS_IP}:$VPS_PATH/
scp backend/models.py $VPS_USER@${VPS_IP}:$VPS_PATH/
scp backend/database.py $VPS_USER@${VPS_IP}:$VPS_PATH/
scp backend/requirements.txt $VPS_USER@${VPS_IP}:$VPS_PATH/

Write-Host "✅ Fichiers copiés" -ForegroundColor Green
Write-Host ""

# Installer les dépendances si requirements.txt a changé
Write-Host "3. Installation des dépendances..." -ForegroundColor Yellow
ssh $VPS_USER@$VPS_IP "cd $VPS_PATH && source venv/bin/activate && pip install -r requirements.txt -q"
Write-Host "✅ Dépendances OK" -ForegroundColor Green
Write-Host ""

# Redémarrer le service
Write-Host "4. Redémarrage du service..." -ForegroundColor Yellow
ssh $VPS_USER@$VPS_IP "systemctl restart email-finder"
Start-Sleep -Seconds 2
Write-Host "✅ Service redémarré" -ForegroundColor Green
Write-Host ""

# Vérifier que le service fonctionne
Write-Host "5. Vérification..." -ForegroundColor Yellow
$status = ssh $VPS_USER@$VPS_IP "systemctl is-active email-finder"
if ($status -eq "active") {
    Write-Host "✅ Service actif" -ForegroundColor Green
} else {
    Write-Host "❌ Service non actif : $status" -ForegroundColor Red
    Write-Host "Logs :" -ForegroundColor Yellow
    ssh $VPS_USER@$VPS_IP "journalctl -u email-finder -n 20 --no-pager"
    exit 1
}

# Test API
Write-Host ""
Write-Host "6. Test API..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "http://${VPS_IP}:8000/api/cache/stats" -UseBasicParsing -ErrorAction SilentlyContinue
if ($response.StatusCode -eq 200) {
    Write-Host "✅ API répond" -ForegroundColor Green
    Write-Host "Cache stats: $($response.Content)" -ForegroundColor Gray
} else {
    Write-Host "⚠️ API ne répond pas correctement" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Déploiement terminé !" -ForegroundColor Green
Write-Host ""
Write-Host "Commandes utiles :" -ForegroundColor Cyan
Write-Host "  Logs: ssh $VPS_USER@$VPS_IP 'tail -f /root/logs/email_finder.log'" -ForegroundColor White
Write-Host "  Stats: curl http://${VPS_IP}:8000/api/cache/stats" -ForegroundColor White
Write-Host "  Status: ssh $VPS_USER@$VPS_IP 'systemctl status email-finder'" -ForegroundColor White
