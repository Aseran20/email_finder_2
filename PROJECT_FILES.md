# Index des fichiers du projet

> Liste complète et organisée de tous les fichiers importants.

---

## 📖 Documentation (lire dans cet ordre)

| Fichier | Description | Quand lire ? |
|---------|-------------|--------------|
| `QUICKSTART.md` | Guide rapide 30 secondes | Premier contact |
| `README.md` | Vue d'ensemble complète | Après QUICKSTART |
| `docs/API_USAGE.md` | Guide utilisation API | Pour utiliser l'API |
| `docs/SESSION_NOTES.md` | État actuel du projet | Pour comprendre l'historique |
| `docs/ARCHITECTURE.md` | Détails techniques | Pour modifier le code |
| `docs/MAINTENANCE.md` | Opérations & troubleshooting | Problèmes quotidiens |
| `PROJECT_FILES.md` | Ce fichier - Index | Navigation |

---

## 🐍 Backend (Python)

### Core Logic
| Fichier | Lignes | Rôle |
|---------|--------|------|
| `backend/core/email_finder.py` | ~200 | Logique principale (patterns, SMTP) |
| `backend/core/mx_cache.py` | ~95 | Cache DNS MX (1h TTL) |
| `backend/core/logger.py` | ~130 | Logs structurés (JSON/plain text) |

### API
| Fichier | Lignes | Rôle |
|---------|--------|------|
| `backend/main.py` | ~225 | Endpoints FastAPI |
| `backend/models.py` | ~17 | Pydantic schemas |
| `backend/database.py` | ~40 | SQLite ORM |

### Configuration
| Fichier | Description |
|---------|-------------|
| `backend/requirements.txt` | Dépendances production (11 packages) |
| `backend/requirements-dev.txt` | Dépendances tests (pytest, etc.) |
| `backend/.env` | Config SMTP (gitignored) |
| `backend/pytest.ini` | Config pytest |

### Tests
| Fichier | Tests | Coverage |
|---------|-------|----------|
| `backend/tests/test_email_finder.py` | 24 | 94% email_finder.py |
| `backend/tests/test_api.py` | 13 | 83% main.py |
| `backend/tests/conftest.py` | - | Fixtures partagées |

**Total** : 37 tests, 86% coverage

---

## ⚛️ Frontend (React)

| Fichier | Rôle |
|---------|------|
| `frontend/src/App.tsx` | Application principale |
| `frontend/src/components/SearchForm.tsx` | Formulaire recherche |
| `frontend/src/components/BulkSearch.tsx` | Import CSV |
| `frontend/src/components/HistoryList.tsx` | Historique |
| `frontend/src/types.ts` | Types TypeScript |
| `frontend/package.json` | Dépendances npm |
| `frontend/vite.config.ts` | Config Vite |
| `frontend/tailwind.config.js` | Config Tailwind CSS |

---

## 🛠️ Scripts & Outils

| Fichier | Usage |
|---------|-------|
| `scripts/deploy.ps1` | Déploiement VPS (PowerShell) |
| `scripts/deploy_clean.ps1` | Ancien script (gardé pour ref) |

---

## 🗂️ Fichiers système

| Fichier | Rôle |
|---------|------|
| `.gitignore` | Fichiers à ignorer dans Git |
| `.git/` | Historique Git |

---

## 🗄️ Structure VPS

```
/root/vps-email-finder/        ← Repo Git (production)
    ├── backend/
    │   ├── core/
    │   │   ├── email_finder.py
    │   │   ├── mx_cache.py
    │   │   └── logger.py
    │   ├── venv/              (Python virtualenv)
    │   ├── .env               (Config SMTP)
    │   └── main.py
    └── frontend/

/root/data/
    └── email_finder.db        (SQLite, 233 KB)

/root/logs/
    └── email_finder.log       (Logs applicatifs)

/etc/systemd/system/
    └── email-finder.service   (Service systemd)

/etc/nginx/
    └── .htpasswd              (Basic Auth)
```

---

## 📦 Archives (gitignored)

```
archives/
├── README.md                  ← Lire pour comprendre le contenu
├── session-notes/             ← Notes session 28 jan 2026
├── ssh-setup/                 ← Scripts setup SSH (obsolètes)
├── old-deploy-scripts/        ← Anciens scripts déploiement
└── planning/                  ← Notes planification initiale
```

**Ces fichiers ne sont PAS versionnés** (dans .gitignore).

---

## 🔍 Rechercher un fichier

### Par fonctionnalité

**Modifier la détection catch-all** :
- `backend/core/email_finder.py` → `find_email()` ligne ~160

**Changer les patterns d'email** :
- `backend/core/email_finder.py` → `generate_patterns()` ligne ~60

**Ajouter un endpoint API** :
- `backend/main.py` → Ajouter `@app.get()` ou `@app.post()`

**Modifier le cache TTL** :
- `backend/core/email_finder.py` → `EmailFinder(mx_cache_ttl=3600)`
- `backend/core/mx_cache.py` → `MXCache(ttl=3600)`

**Changer les logs** :
- `backend/core/logger.py` → `StructuredLogger`

**Tests unitaires** :
- `backend/tests/test_email_finder.py`

**Tests API** :
- `backend/tests/test_api.py`

### Par mot-clé

**Cache** :
- `backend/core/mx_cache.py`
- `backend/core/email_finder.py` (ligne ~18, 97)

**SMTP** :
- `backend/core/email_finder.py` (ligne ~106)

**Database** :
- `backend/database.py`
- `backend/main.py` (ligne ~42)

**Logs** :
- `backend/core/logger.py`
- `/root/logs/email_finder.log` (VPS)

**Déploiement** :
- `scripts/deploy.ps1`
- `docs/MAINTENANCE.md` → Section "Déploiement"

**Monitoring** :
- `docs/MAINTENANCE.md` → Section "Monitoring"
- Endpoint `/api/cache/stats`

---

## 📊 Statistiques du projet

### Code

| Langage | Fichiers | Lignes |
|---------|----------|--------|
| Python | 9 | ~900 |
| TypeScript/React | 7 | ~600 |
| Markdown | 8 | ~3000 |
| PowerShell | 2 | ~150 |

### Tests

- 37 tests au total
- 31 passent (84%)
- 86% code coverage
- Temps d'exécution : ~23s

### Documentation

- 8 fichiers Markdown
- ~3000 lignes de documentation
- 100% du projet documenté

---

## 🎯 Fichiers critiques (ne pas supprimer)

### En local
```
backend/core/email_finder.py    ← Logique principale
backend/core/mx_cache.py        ← Cache DNS
backend/core/logger.py          ← Logs structurés
backend/main.py                 ← API endpoints
backend/models.py               ← Data schemas
backend/database.py             ← Database ORM
backend/requirements.txt        ← Dépendances Python
```

### Sur VPS
```
/root/vps-email-finder/         ← Repo Git
/root/data/email_finder.db      ← Base de données
/etc/systemd/system/email-finder.service  ← Service
~/.ssh/authorized_keys          ← Clé SSH
```

---

## 🗑️ Fichiers pouvant être supprimés

### Sans risque
```
archives/                       ← Tout le dossier
backend/htmlcov/               ← Reports coverage HTML
backend/.pytest_cache/         ← Cache pytest
backend/__pycache__/           ← Cache Python
nul                            ← Fichier vide Windows (supprimé)
```

### Obsolètes sur VPS (si tout marche depuis 1 semaine)
```
/root/backend_old_prod/        ← Ancien backend
/root/archives/                ← Vieux projets
```

---

## 🔄 Workflow modifications

### Pour modifier le code

1. Modifier localement (ex: `backend/core/email_finder.py`)
2. Tester localement : `pytest tests/`
3. Déployer : `.\scripts\deploy.ps1`
4. Vérifier VPS : `curl http://192.3.81.106:8000/api/cache/stats`

### Pour ajouter une dépendance

1. Local : `pip install nouvelle-lib`
2. Mettre à jour : `pip freeze > backend/requirements.txt`
3. VPS : `ssh root@192.3.81.106 "cd /root/vps-email-finder/backend && source venv/bin/activate && pip install -r requirements.txt"`
4. Redémarrer : `ssh root@192.3.81.106 "systemctl restart email-finder"`

### Pour écrire un test

1. Créer/modifier : `backend/tests/test_*.py`
2. Lancer : `pytest tests/test_*.py -v`
3. Coverage : `pytest tests/ --cov --cov-report=html`
4. Voir rapport : `backend/htmlcov/index.html`

---

## 📞 Questions fréquentes

**"Où est le code qui génère les patterns d'email ?"**
→ `backend/core/email_finder.py` fonction `generate_patterns()`

**"Où sont les logs ?"**
→ VPS : `/root/logs/email_finder.log`

**"Comment je teste l'API ?"**
→ `curl http://192.3.81.106:8000/api/cache/stats`

**"Où est la database ?"**
→ VPS : `/root/data/email_finder.db`

**"Comment je déploie ?"**
→ `.\scripts\deploy.ps1`

**"Où sont les tests ?"**
→ `backend/tests/`

**"Comment je lance les tests ?"**
→ `pytest tests/ -v`

---

**Dernière mise à jour** : 28 janvier 2026
**Maintenu par** : Adrian Turion
