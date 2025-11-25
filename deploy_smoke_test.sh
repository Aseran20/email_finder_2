#!/bin/bash
# Script de déploiement du smoke test sur le VPS

VPS_IP="192.3.81.106"
VPS_USER="root"

echo "📦 Transfert de verify_vps.py vers le VPS..."
scp backend/verify_vps.py ${VPS_USER}@${VPS_IP}:/root/

echo "🔧 Installation de dnspython et lancement du test..."
ssh ${VPS_USER}@${VPS_IP} << 'ENDSSH'
pip3 install dnspython
cd /root
python3 verify_vps.py
ENDSSH

echo "✅ Test terminé ! Vérifiez les résultats ci-dessus."
