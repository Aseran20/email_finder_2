# Guide de maintenance - Email Finder

> Procédures de maintenance courantes et résolution de problèmes.

---

## 📋 Checklist maintenance mensuelle

### À faire chaque mois

- [ ] Vérifier l'espace disque VPS
- [ ] Backup de la base de données
- [ ] Vérifier les logs d'erreurs
- [ ] Contrôler le hit rate du cache
- [ ] Tester une recherche complète

---

## 💾 Backup

### Backup manuel de la base de données

```bash
# Connexion VPS
ssh root@192.3.81.106

# Créer backup avec date
cp /root/data/email_finder.db /root/backups/email_finder_$(date +%Y%m%d).db

# Télécharger en local (depuis Windows)
scp root@192.3.81.106:/root/backups/email_finder_$(date +%Y%m%d).db ./backups/
```

### Restauration depuis backup

```bash
# Sur le VPS
systemctl stop email-finder
cp /root/backups/email_finder_YYYYMMDD.db /root/data/email_finder.db
systemctl start email-finder
```

### Backup automatique (recommandé)

```bash
# Créer un cron job
ssh root@192.3.81.106
crontab -e

# Ajouter cette ligne (backup à 2h du matin)
0 2 * * * cp /root/data/email_finder.db /root/backups/email_finder_$(date +\%Y\%m\%d).db

# Cleanup des backups > 30 jours
0 3 * * * find /root/backups -name "email_finder_*.db" -mtime +30 -delete
```

---

## 🔄 Mises à jour

### Update du code backend

```powershell
# Méthode 1 : Script de déploiement
cd C:\Users\AdrianTurion\devprojects\2-auraia\vps-email-finder
.\scripts\deploy.ps1

# Méthode 2 : Manuel
scp backend/main.py root@192.3.81.106:/root/vps-email-finder/backend/
ssh root@192.3.81.106 "systemctl restart email-finder"
```

### Update des dépendances Python

```bash
ssh root@192.3.81.106
cd /root/vps-email-finder/backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
systemctl restart email-finder
```

### Update du système VPS

```bash
ssh root@192.3.81.106

# Update packages
apt update && apt upgrade -y

# Redémarrer si kernel update
reboot  # ⚠️ Downtime 2-3 minutes
```

---

## 🔍 Monitoring quotidien

### Commandes rapides

```bash
# Status service
ssh root@192.3.81.106 "systemctl status email-finder --no-pager"

# Cache stats
curl -s http://192.3.81.106:8000/api/cache/stats | python -m json.tool

# Dernières erreurs (24h)
ssh root@192.3.81.106 "tail -1000 /root/logs/email_finder.log | grep -i error | tail -10"

# Espace disque
ssh root@192.3.81.106 "df -h | grep -E 'Filesystem|/$'"

# Mémoire utilisée
ssh root@192.3.81.106 "free -h"
```

### Dashboard monitoring (script)

```powershell
# Créer scripts/monitor.ps1
$VPS = "192.3.81.106"

Write-Host "=== Email Finder Status ===" -ForegroundColor Cyan

# Service status
$status = ssh root@$VPS "systemctl is-active email-finder"
Write-Host "Service: $status" -ForegroundColor $(if($status -eq 'active'){'Green'}else{'Red'})

# Cache stats
$cache = Invoke-RestMethod "http://${VPS}:8000/api/cache/stats"
Write-Host "Cache hit rate: $($cache.hit_rate)" -ForegroundColor Yellow

# Disk space
ssh root@$VPS "df -h / | tail -1"
```

---

## 🔧 Problèmes courants

### Service ne démarre pas

**Symptômes** : `systemctl status email-finder` → failed

**Diagnostic** :
```bash
# Voir les logs détaillés
journalctl -u email-finder -n 50

# Vérifier la syntaxe Python
ssh root@192.3.81.106
cd /root/vps-email-finder/backend
source venv/bin/activate
python -m py_compile main.py
```

**Solutions** :
```bash
# 1. Vérifier les dépendances
pip install -r requirements.txt

# 2. Vérifier le .env
cat /root/vps-email-finder/backend/.env

# 3. Tester le lancement manuel
python -m uvicorn main:app --host 0.0.0.0 --port 8000
# Si ça marche → Problème systemd
# Si erreur → Problème code
```

### API retourne 500

**Symptômes** : Toutes les requêtes retournent 500

**Diagnostic** :
```bash
# Logs détaillés
ssh root@192.3.81.106 "tail -100 /root/logs/email_finder.log | grep ERROR"

# Test manuel
curl -X POST http://192.3.81.106:8000/api/find-email \
  -H "Content-Type: application/json" \
  -d '{"domain":"test.com","fullName":"Test"}'
```

**Solutions** :
```bash
# Database corrompue
sqlite3 /root/data/email_finder.db "PRAGMA integrity_check;"

# Permissions fichiers
chmod 644 /root/data/email_finder.db
chown root:root /root/data/email_finder.db

# Redémarrer
systemctl restart email-finder
```

### Cache ne fonctionne pas

**Symptômes** : hit_rate toujours à 0%

**Diagnostic** :
```bash
# Vérifier que mx_cache.py existe
ssh root@192.3.81.106 "ls -la /root/vps-email-finder/backend/core/mx_cache.py"

# Vérifier l'import dans email_finder.py
ssh root@192.3.81.106 "grep 'from core.mx_cache' /root/vps-email-finder/backend/core/email_finder.py"

# Test multiple sur même domaine
for i in {1..3}; do
  curl -s -X POST http://192.3.81.106:8000/api/find-email \
    -H "Content-Type: application/json" \
    -d '{"domain":"google.com","fullName":"Test Person'$i'"}'
  sleep 1
done

curl -s http://192.3.81.106:8000/api/cache/stats
# hits devrait être > 0
```

**Solutions** :
```bash
# Redéployer mx_cache.py
scp backend/core/mx_cache.py root@192.3.81.106:/root/vps-email-finder/backend/core/
systemctl restart email-finder
```

### Port 25 bloqué

**Symptômes** : Toutes les recherches retournent timeout

**Diagnostic** :
```bash
# Test telnet
ssh root@192.3.81.106 "timeout 5 telnet gmail-smtp-in.l.google.com 25"

# Test avec Python
ssh root@192.3.81.106 "cd /root/vps-email-finder/backend && python3 verify_vps.py"
```

**Solutions** :
1. Contacter l'hébergeur (RackNerd) pour débloquer port 25
2. Utiliser un proxy SMTP externe
3. Changer de VPS

### IP bannie temporairement

**Symptômes** : Recherches fonctionnaient, maintenant timeout ou erreur

**Diagnostic** :
```bash
# Tester plusieurs domaines
curl -s -X POST http://192.3.81.106:8000/api/find-email \
  -H "Content-Type: application/json" \
  -d '{"domain":"gmail.com","fullName":"Test"}'

# Si tous échouent → Probablement ban
```

**Solutions** :
1. Attendre 1-24h (ban temporaire)
2. Réduire le volume de recherches
3. Augmenter le délai entre patterns (2s au lieu de 1s)
4. Utiliser plusieurs IPs (rotation)

### Database trop grosse

**Symptômes** : email_finder.db > 1 GB

**Diagnostic** :
```bash
ssh root@192.3.81.106 "ls -lh /root/data/email_finder.db"
```

**Solutions** :
```bash
# 1. Archiver les vieilles entrées (> 6 mois)
ssh root@192.3.81.106
cd /root/vps-email-finder/backend

sqlite3 /root/data/email_finder.db << EOF
-- Export old data
.output /root/archives/old_searches.sql
.dump search_history
-- Delete old entries
DELETE FROM search_history WHERE created_at < datetime('now', '-6 months');
-- Vacuum to reclaim space
VACUUM;
EOF

# 2. Vérifier la taille
ls -lh /root/data/email_finder.db
```

---

## 🗑️ Cleanup

### Cleanup logs

```bash
# Logs > 100 MB
ssh root@192.3.81.106 "truncate -s 0 /root/logs/email_finder.log"

# Ou avec rotation
ssh root@192.3.81.106 << EOF
mv /root/logs/email_finder.log /root/logs/email_finder.log.$(date +%Y%m%d)
touch /root/logs/email_finder.log
systemctl restart email-finder
# Cleanup logs > 30 jours
find /root/logs -name "email_finder.log.*" -mtime +30 -delete
EOF
```

### Cleanup cache Docker/Build

```bash
# Pas de Docker actuellement, mais si jamais :
ssh root@192.3.81.106 "docker system prune -a"
```

### Cleanup archives

```bash
# Supprimer les vieux backups VPS
ssh root@192.3.81.106 "rm -rf /root/backend_old_prod /root/archives"
```

---

## 🔐 Sécurité

### Changer le mot de passe Basic Auth

```bash
ssh root@192.3.81.106
htpasswd -c /etc/nginx/.htpasswd admin
# Entrer le nouveau mot de passe
systemctl reload nginx
```

### Vérifier les connexions suspectes

```bash
# Voir les connexions SSH récentes
ssh root@192.3.81.106 "last -n 20"

# Voir les tentatives échouées
ssh root@192.3.81.106 "grep 'Failed password' /var/log/auth.log | tail -20"

# Bloquer une IP (si abuse)
ssh root@192.3.81.106 "ufw deny from 1.2.3.4"
```

### Rotation clé SSH

```bash
# Générer nouvelle clé locale
ssh-keygen -t ed25519 -f ~/.ssh/vps_email_finder_new

# Ajouter sur VPS
ssh-copy-id -i ~/.ssh/vps_email_finder_new.pub root@192.3.81.106

# Tester la nouvelle clé
ssh -i ~/.ssh/vps_email_finder_new root@192.3.81.106 "hostname"

# Supprimer l'ancienne clé du VPS
ssh root@192.3.81.106 "nano ~/.ssh/authorized_keys"
```

---

## 📊 Statistiques

### Requêtes SQL utiles

```sql
-- Recherches par jour (30 derniers jours)
SELECT
    DATE(created_at) as date,
    COUNT(*) as searches
FROM search_history
WHERE created_at > datetime('now', '-30 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Taux de succès par status
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM search_history), 2) as percentage
FROM search_history
GROUP BY status;

-- Domaines les plus recherchés
SELECT
    domain,
    COUNT(*) as count
FROM search_history
GROUP BY domain
ORDER BY count DESC
LIMIT 10;

-- Taille DB
SELECT
    COUNT(*) as total_searches,
    ROUND(SUM(LENGTH(patterns_tested) + LENGTH(smtp_logs))/1024.0/1024.0, 2) as size_mb
FROM search_history;
```

### Export stats

```bash
ssh root@192.3.81.106 << 'EOF'
cd /root/vps-email-finder/backend
sqlite3 /root/data/email_finder.db << SQL
.mode csv
.output /tmp/stats.csv
SELECT DATE(created_at) as date, status, COUNT(*) as count
FROM search_history
WHERE created_at > datetime('now', '-30 days')
GROUP BY DATE(created_at), status;
SQL
EOF

scp root@192.3.81.106:/tmp/stats.csv ./stats_$(date +%Y%m%d).csv
```

---

## 🚨 Urgences

### Service down - Redémarrage rapide

```bash
# Quick fix
ssh root@192.3.81.106 "systemctl restart email-finder"

# Si ça ne marche pas
ssh root@192.3.81.106 "systemctl stop email-finder && pkill -f uvicorn && systemctl start email-finder"
```

### Database corrompue

```bash
# Backup immédiat
ssh root@192.3.81.106 "cp /root/data/email_finder.db /root/email_finder.db.corrupt"

# Tenter réparation
ssh root@192.3.81.106 << 'EOF'
sqlite3 /root/data/email_finder.db << SQL
PRAGMA integrity_check;
REINDEX;
VACUUM;
SQL
EOF

# Si échec → Restaurer backup
ssh root@192.3.81.106 "cp /root/backups/email_finder_DERNIERBACKUP.db /root/data/email_finder.db"
ssh root@192.3.81.106 "systemctl restart email-finder"
```

### VPS inaccessible

**Si SSH ne répond pas** :
1. Vérifier depuis le panel RackNerd
2. Console VNC via le panel
3. Reboot via le panel

**Si VPS up mais service down** :
1. `systemctl restart email-finder`
2. Check logs : `journalctl -u email-finder -n 100`

---

## 📞 Contacts

**Hébergeur VPS** : RackNerd
- Panel : https://my.racknerd.com
- IP : 192.3.81.106
- Support : ticket via panel

**DNS** : (À compléter selon provider)

**Monitoring** : (Pas configuré actuellement)

---

**Document maintenu par** : Adrian Turion
**Dernière mise à jour** : 28 janvier 2026
