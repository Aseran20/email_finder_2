# Quick Start Guide - Email Finder

> Guide ultra-rapide pour un Claude qui arrive sans contexte.

---

## 🚀 En 30 secondes

**C'est quoi ?** Outil de vérification d'emails professionnels via SMTP.

**Où ?**
- Frontend : https://email.auraia.ch (Basic Auth)
- API : http://192.3.81.106:8000
- VPS : `ssh root@192.3.81.106` (clé SSH configurée)

**Comment utiliser ?**
```bash
curl -X POST "http://192.3.81.106:8000/api/find-email" \
  -H "Content-Type: application/json" \
  -d '{"domain":"company.com","fullName":"John Doe"}'
```

---

## 📚 Documents à lire (dans l'ordre)

1. **README.md** ← Commence ici (vue d'ensemble complète)
2. **docs/API_USAGE.md** - Comment utiliser l'API
3. **docs/ARCHITECTURE.md** - Détails techniques
4. **docs/MAINTENANCE.md** - Opérations quotidiennes
5. **docs/SESSION_NOTES.md** - État actuel du projet

---

## 🛠️ Commandes essentielles

### SSH VPS
```bash
ssh root@192.3.81.106
```

### Vérifier que tout marche
```bash
# Status service
ssh root@192.3.81.106 "systemctl status email-finder"

# Test API
curl http://192.3.81.106:8000/api/cache/stats

# Test recherche
curl -X POST "http://192.3.81.106:8000/api/find-email" \
  -H "Content-Type: application/json" \
  -d '{"domain":"auraia.ch","fullName":"Adrian Turion"}'
```

### Redémarrer le service
```bash
ssh root@192.3.81.106 "systemctl restart email-finder"
```

### Voir les logs
```bash
ssh root@192.3.81.106 "tail -f /root/logs/email_finder.log"
```

### Déployer une modification
```powershell
.\scripts\deploy.ps1
```

---

## 📁 Structure projet (clean)

```
vps-email-finder/
├── README.md              ← Commence ici
├── QUICKSTART.md          ← Ce fichier
├── .gitignore
│
├── backend/               ← API Python
│   ├── core/
│   │   ├── email_finder.py
│   │   ├── mx_cache.py
│   │   └── logger.py
│   ├── tests/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── frontend/              ← Interface React
│   └── src/
│
├── docs/                  ← Documentation
│   ├── API_USAGE.md
│   ├── ARCHITECTURE.md
│   ├── MAINTENANCE.md
│   └── SESSION_NOTES.md
│
├── scripts/               ← Scripts utiles
│   └── deploy.ps1
│
└── archives/              ← Fichiers obsolètes (gitignored)
```

---

## ⚡ Actions rapides

### Problème fréquent #1 : Service down
```bash
ssh root@192.3.81.106 "systemctl restart email-finder"
```

### Problème fréquent #2 : API retourne 500
```bash
# Voir les logs
ssh root@192.3.81.106 "tail -50 /root/logs/email_finder.log | grep ERROR"
```

### Problème fréquent #3 : Cache ne fonctionne pas
```bash
# Vérifier le fichier
ssh root@192.3.81.106 "ls -la /root/vps-email-finder/backend/core/mx_cache.py"

# Redéployer si manquant
scp backend/core/mx_cache.py root@192.3.81.106:/root/vps-email-finder/backend/core/
ssh root@192.3.81.106 "systemctl restart email-finder"
```

---

## 🧪 Test complet (1 minute)

```bash
# 1. Service up ?
ssh root@192.3.81.106 "systemctl is-active email-finder"
# Doit retourner : active

# 2. API répond ?
curl http://192.3.81.106:8000/docs
# Doit retourner : HTML

# 3. Cache fonctionne ?
curl http://192.3.81.106:8000/api/cache/stats
# Doit retourner : JSON avec hits/misses

# 4. Recherche marche ?
curl -X POST "http://192.3.81.106:8000/api/find-email" \
  -H "Content-Type: application/json" \
  -d '{"domain":"auraia.ch","fullName":"Adrian Turion"}'
# Doit retourner : status: "valid", email: "adrian.turion@auraia.ch"
```

Si tout marche ✅ → Système opérationnel

---

## 📊 Métriques importantes

```bash
# Cache hit rate (> 50% = bon)
curl -s http://192.3.81.106:8000/api/cache/stats | grep hit_rate

# Historique recherches
curl -s http://192.3.81.106:8000/api/history?limit=1 | grep -o '"id":[0-9]*'
# Nombre = total recherches

# Espace disque (> 2 GB libre = bon)
ssh root@192.3.81.106 "df -h /"
```

---

## 🎯 Modifications courantes

### Modifier la logique de recherche
```
Fichier : backend/core/email_finder.py
Fonction : find_email() ou generate_patterns()
Après : .\scripts\deploy.ps1
```

### Ajouter un endpoint API
```
Fichier : backend/main.py
Après : .\scripts\deploy.ps1
```

### Changer les patterns d'email
```
Fichier : backend/core/email_finder.py
Fonction : generate_patterns()
Après : .\scripts\deploy.ps1
```

### Modifier le cache TTL
```
Fichier : backend/core/email_finder.py
Ligne : EmailFinder(mx_cache_ttl=3600)  # Changer 3600 (secondes)
Après : .\scripts\deploy.ps1
```

---

## 🔑 Credentials

### SSH VPS
- **Host** : 192.3.81.106
- **User** : root
- **Auth** : Clé SSH (~/.ssh/id_ed25519)
- **Pas de mot de passe** ✅

### Basic Auth Frontend
- **URL** : https://email.auraia.ch
- **User** : admin
- **Password** : Demander à Adrian

### API Backend
- **Pas d'authentification** (usage interne)

---

## 🆘 En cas de panique

**Service complètement cassé ?**
```bash
# 1. Redémarrer
ssh root@192.3.81.106 "systemctl restart email-finder"

# 2. Vérifier les logs
ssh root@192.3.81.106 "journalctl -u email-finder -n 100"

# 3. Si toujours cassé, contacter Adrian
```

**VPS inaccessible ?**
1. Panel RackNerd : https://my.racknerd.com
2. Console VNC
3. Reboot

**Database corrompue ?**
```bash
# Restaurer le dernier backup
ssh root@192.3.81.106 "ls -lht /root/backup_*.tar.gz | head -1"
# Extraire et restaurer (voir MAINTENANCE.md)
```

---

## 📞 Contacts

**Projet maintenu par** : Adrian Turion
**Email** : adrian.turion@auraia.ch
**VPS Hébergeur** : RackNerd (panel: https://my.racknerd.com)

---

**Tu as lu ce fichier ? Maintenant lis README.md pour la vue complète ! 📖**
