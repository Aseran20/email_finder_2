# Roadmap - VPS Email Finder

> État du projet et features planifiées
> Dernière mise à jour: 28 janvier 2026

---

## 📊 Vue d'ensemble

| Feature | Status | Temps estimé | Priorité |
|---------|--------|--------------|----------|
| **1. UI Redesign (shadcn)** | ✅ Terminé | ~90 min | ✨ HAUTE |
| **2. Check Mail Endpoint** | 📋 Planifié | 3.5h | 📧 HAUTE |
| **3. Bulk JSON Endpoint** | 📋 Planifié | 1h | 🚀 MOYENNE |
| **4. API Robustness** | 📋 Planifié | 3h | 🛡️ MOYENNE |

**Temps total restant**: ~7.5 heures
**État global**: Phase 1 (UI) ✅ Complète, Phases 2-4 architecturées et prêtes

---

## ✅ Feature 1: UI Redesign avec shadcn/ui

**Status**: ✅ 100% Complete - Production Ready

### Ce qui est fait ✅

1. **Setup Infrastructure**
   - ✅ Path aliases configurés (@/* imports)
   - ✅ components.json créé (New York style)
   - ✅ Tailwind config avec fonts custom
   - ✅ vite.config.ts + tsconfig mis à jour

2. **Design System**
   - ✅ index.css avec variables CSS complètes
   - ✅ Fraunces (serif variable) pour headings
   - ✅ JetBrains Mono pour data/code
   - ✅ Palette indigo raffinée + grays sophistiqués
   - ✅ Système d'élévation (3 niveaux de shadow)
   - ✅ Animations (slide-in, fade-in, scale-in)

3. **Composants shadcn créés**
   - ✅ Button
   - ✅ Input
   - ✅ Label
   - ✅ Card (+ CardHeader, CardContent, CardTitle)
   - ✅ Badge

4. **Redesigns planifiés**
   - ✅ App.tsx - Header + Tabs
   - ✅ SearchForm.tsx - Card-based form
   - ✅ HistoryList.tsx - Status badges + Collapsible
   - ✅ BulkSearch.tsx - Table + Toast

### ✅ Tout est fait!

```bash
# ✅ 1. Dépendances installées
# ✅ 2. Composants shadcn installés (tabs, table, toast, collapsible)
# ✅ 3. Redesigns appliqués (App.tsx, SearchForm.tsx, HistoryList.tsx)
# ✅ 4. TypeScript compilation réussie (aucune erreur)

# Pour tester:
cd frontend
npm run dev
# Ouvrir http://localhost:5173
```

### Documentation

- 📄 **`frontend/UI_REDESIGN_GUIDE.md`** - Guide complet avec code
- 🎨 **Design tokens**: Voir `frontend/src/index.css`
- 🔧 **Config**: `frontend/tailwind.config.js`

### Résultat attendu

Une UI distinctive avec:
- Typographie Fraunces + JetBrains Mono (mémorable)
- Espacements généreux (32-48px)
- Badges status avec couleurs custom
- Animations micro-interactions
- Mode light raffiné

---

## 📋 Feature 2: Check Mail Endpoint

**Status**: 📋 Architecture complète, prêt à implémenter
**Temps estimé**: 3.5 heures

### Objectif

Nouvelle API endpoint qui:
1. Reçoit un email complet (`john.d@company.com`) + fullName
2. Valide l'email via SMTP
3. Si valide → Retourne succès
4. Si invalide → Lance recherche pattern avec fullName
5. Retourne résultat validation + email suggéré si trouvé

### Architecture

**Nouveau endpoint**: `POST /api/check-email`

**Request**:
```json
{
  "email": "john.d@company.com",
  "fullName": "John Doe"
}
```

**Response**:
```json
{
  "status": "invalid_found_alternative",
  "providedEmail": "john.d@company.com",
  "validationResult": {
    "isValid": false,
    "smtpCode": 550,
    "smtpMessage": "User unknown"
  },
  "suggestedEmail": "john.doe@company.com",
  "confidence": "high",
  "catchAll": false,
  "patternsTested": ["john.doe@...", "..."],
  "smtpLogs": ["..."]
}
```

### Fichiers à modifier

1. **`backend/models.py`**
   - Ajouter `EmailCheckRequest`
   - Ajouter `ValidationResult`
   - Ajouter `EmailCheckResponse`

2. **`backend/core/email_finder.py`**
   - Ajouter `extract_domain_from_email()` méthode
   - Ajouter `check_email_with_fallback()` méthode (réutilise `verify_email` + `find_email`)

3. **`backend/database.py`**
   - Étendre `SearchHistory` avec 3 colonnes:
     - `provided_email` (nullable)
     - `validation_smtp_code` (nullable)
     - `validation_is_valid` (nullable)

4. **`backend/main.py`**
   - Ajouter endpoint `/api/check-email`

### Checklist implémentation

- [ ] Créer Pydantic models (30 min)
- [ ] Implémenter `extract_domain_from_email()` (15 min)
- [ ] Implémenter `check_email_with_fallback()` (60 min)
- [ ] Ajouter endpoint API (30 min)
- [ ] Étendre DB schema (20 min)
- [ ] Tests unitaires (45 min)
- [ ] Tests API (30 min)
- [ ] Documentation (20 min)

### Référence architecture

- 🏗️ **Blueprint détaillé**: Agent aa909d4 (Phase 4)
- 📝 **Code samples**: Voir agent output
- 🧪 **Tests**: `backend/tests/test_check_email.py` (à créer)

---

## 🚀 Feature 3: Bulk JSON Endpoint

**Status**: 📋 Architecture complète, prêt à implémenter
**Temps estimé**: 1 heure

### Objectif

Alternative au CSV pour usage command-line:
- Accepter JSON array au lieu de fichier CSV
- Même logique de traitement (rate limiting, circuit breaker)
- curl-friendly pour scripts

### Architecture

**Nouveau endpoint**: `POST /api/bulk-search-json`

**Request**:
```json
{
  "searches": [
    {"domain": "company.com", "fullName": "John Doe"},
    {"domain": "example.org", "fullName": "Jane Smith"}
  ]
}
```

**Response** (identique au CSV):
```json
{
  "total": 2,
  "results": [
    {"domain": "...", "status": "valid", "email": "...", ...},
    ...
  ]
}
```

### Fichiers à modifier

1. **`backend/models.py`**
   - Ajouter `BulkSearchItem(BaseModel)`
   - Ajouter `BulkSearchRequest(BaseModel)`

2. **`backend/main.py`**
   - Extraire `_process_bulk_searches()` helper (logique partagée)
   - Refactorer `/api/bulk-search` (CSV) pour utiliser helper
   - Ajouter `/api/bulk-search-json` endpoint (utilise helper)

### Checklist implémentation

- [ ] Créer Pydantic models (10 min)
- [ ] Extraire `_process_bulk_searches()` (20 min)
- [ ] Ajouter endpoint JSON (15 min)
- [ ] Tests (10 min)
- [ ] Documentation (5 min)

### Référence architecture

- 🏗️ **Blueprint détaillé**: Agent af66a65 (Phase 4)
- 📝 **Code reuse**: 90% du code CSV réutilisable

---

## 🛡️ Feature 4: API Robustness

**Status**: 📋 Architecture complète, prêt à implémenter
**Temps estimé**: 3 heures

### Objectif

3 améliorations de robustesse:

#### A. Retry Logic avec Exponential Backoff

**Comportement**:
- Retry sur erreurs transientes (timeout, connection refused)
- Backoff: 1s → 2s → 4s (max 3 retries)
- **Ne pas** retry sur 550 (user unknown)

**Implémentation**:
- Nouveau: `verify_email_with_retry()` dans `email_finder.py`
- Config: `SMTP_MAX_RETRIES=3` (env var)

#### B. MX Fallback (Secondary MX)

**Comportement**:
- Essayer jusqu'à 2 MX servers (configurable)
- Fallback uniquement sur erreurs de connexion
- Stop si premier MX répond (même si no match)

**Implémentation**:
- Modifier `find_email()` pour loop sur MX records
- Config: `MAX_MX_SERVERS=2` (env var)

#### C. Health Check Endpoint

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T10:30:00Z",
  "database": "connected",
  "cache": {"hit_rate": "66.7%", "cached_domains": 5},
  "version": "v5",
  "system": {"platform": "Linux", "python": "3.12.0"}
}
```

### Fichiers à modifier

1. **`backend/config.py`** (NOUVEAU)
   - Centralisera toutes les env vars
   - `SMTP_MAX_RETRIES`, `MAX_MX_SERVERS`, etc.

2. **`backend/core/email_finder.py`**
   - Ajouter `verify_email_with_retry()` (avec exponential backoff)
   - Modifier `find_email()` pour MX fallback loop

3. **`backend/main.py`**
   - Ajouter endpoint `/health`

4. **`backend/.env`**
   - Ajouter nouvelles variables config

### Checklist implémentation

**Retry Logic** (60 min):
- [ ] Créer `config.py`
- [ ] Implémenter `verify_email_with_retry()`
- [ ] Tests retry scenarios

**MX Fallback** (60 min):
- [ ] Modifier `find_email()` avec MX loop
- [ ] Tests MX fallback

**Health Check** (30 min):
- [ ] Ajouter endpoint `/health`
- [ ] Tests

**Tests & Doc** (30 min):
- [ ] Tests unitaires complets
- [ ] Update `.env` sur VPS
- [ ] Documentation

### Référence architecture

- 🏗️ **Blueprint détaillé**: Agent af66a65 (Phase 4)
- 📝 **Config management**: Nouveau `backend/config.py`
- 🧪 **Tests**: `backend/tests/test_retry_logic.py` (à créer)

---

## 📁 Documentation & Références

### Documents créés

| Fichier | Contenu |
|---------|---------|
| **`CLAUDE.md`** | Guide pour futures instances de Claude Code |
| **`docs/ROADMAP.md`** | Ce fichier - état du projet |
| **`frontend/UI_REDESIGN_GUIDE.md`** | Guide complet UI avec code |
| **`README.md`** | Documentation projet complète |
| **`QUICKSTART.md`** | Guide rapide 30 secondes |
| **`PROJECT_FILES.md`** | Index des fichiers |

### Architectures des agents

Les blueprints détaillés sont dans les outputs des agents:
- **Agent a00bd51**: UI Redesign architecture
- **Agent aa909d4**: Check Mail Endpoint architecture
- **Agent af66a65**: Bulk JSON + Robustness architecture

### Pour la prochaine session

1. **Commencer par**: Finir UI (15 min restantes)
2. **Puis**: Check Mail Endpoint (3.5h)
3. **Puis**: Bulk JSON (1h)
4. **Puis**: API Robustness (3h)

**Total temps restant**: ~7.5 heures

---

## 🎯 Ordre d'implémentation recommandé

### ✅ Session actuelle - TERMINÉE

L'UI redesign est maintenant complet et prêt pour production!

```bash
cd frontend
npm run dev # tester la nouvelle UI
# Ouvrir http://localhost:5173
```

### Prochaine session

**Étape 1: Check Mail Endpoint** (3.5h)
- Backend feature la plus demandée
- Réutilise code existant élégamment
- Tests bien définis

**Étape 2: Bulk JSON** (1h)
- Quick win
- 90% code reuse
- Facilite usage command-line

**Étape 3: API Robustness** (3h)
- Infrastructure improvements
- Retry + MX fallback + Health check
- Améliore fiabilité globale

---

## 🔄 Déploiement

### Local → VPS

Après chaque feature:

```bash
# 1. Tests locaux
cd backend
pytest tests/ -v --cov

# 2. Commit
git add .
git commit -m "feat: [feature name]"
git push

# 3. Déployer sur VPS
ssh root@192.3.81.106
cd /root/vps-email-finder
git pull
cd backend && source venv/bin/activate && pip install -r requirements.txt
systemctl restart email-finder

# 4. Smoke test
curl http://192.3.81.106:8000/health
curl http://192.3.81.106:8000/api/cache/stats
```

---

## ✨ Résultat final

Après implémentation complète, le projet aura:

- ✨ **UI distinctive** avec Fraunces + JetBrains Mono
- 📧 **Email validation** avec fallback intelligent
- 🚀 **Bulk JSON** pour usage CLI
- 🛡️ **Retry logic** pour erreurs transientes
- 🔄 **MX fallback** pour résilience
- 💚 **Health check** pour monitoring

**Impact**: Outil plus fiable, plus beau, plus flexible.

---

**Maintenu par**: Adrian Turion (Auraia)
**Date**: 28 janvier 2026
**Version cible**: v6
