# Script PowerShell pour déployer le smoke test (Windows)

$VPS_IP = "192.3.81.106"
$VPS_USER = "root"

Write-Host "📦 Transfert de verify_vps.py vers le VPS..." -ForegroundColor Cyan
scp backend\verify_vps.py ${VPS_USER}@${VPS_IP}:/root/verify_vps.py

Write-Host "🔧 Configuration de l'environnement et lancement du test..." -ForegroundColor Cyan

# Utiliser un here-string avec LF uniquement (Unix line endings)
$commands = "apt update && apt install -y python3-venv python3-full
cd /root
python3 -m venv test_env
source test_env/bin/activate
pip install dnspython
python3 verify_vps.py
deactivate"

# Envoyer les commandes via SSH
ssh ${VPS_USER}@${VPS_IP} $commands

Write-Host "`n✅ Test terminé !" -ForegroundColor Green
