# Architecture technique - Email Finder

> Documentation technique complète pour comprendre le fonctionnement interne du système.

---

## 🏗️ Vue d'ensemble

### Stack technique

```
Frontend (React + Vite)
    ↓ HTTPS
nginx (Basic Auth + Reverse Proxy)
    ↓ HTTP
FastAPI Backend (Python 3.12)
    ↓
├─ SQLite (historique)
├─ DNS Resolver (cache MX)
└─ SMTP Direct (verification)
```

### Composants

| Composant | Tech | Port | Rôle |
|-----------|------|------|------|
| Frontend | React + Vite | 443 | Interface utilisateur |
| nginx | nginx 1.18 | 443 | Reverse proxy + Basic Auth |
| Backend API | FastAPI + Uvicorn | 8000 | Logique métier |
| Database | SQLite | - | Historique (233 KB) |
| Cache | In-memory dict | - | MX records (1h TTL) |

---

## 🔍 Flow de vérification email

### Étape par étape

```python
# 1. Normalisation du domaine
"https://Company.COM" → "company.com"

# 2. Normalisation du nom
"André Müller-Schmidt" →
  first: ["andre", "andre-muller"]
  last: ["schmidt"]

# 3. Génération des patterns
9 patterns générés :
  andre.schmidt@company.com       # #1 Most common
  andreschmidt@company.com
  a.schmidt@company.com
  andre.s@company.com
  andre@company.com
  schmidt@company.com
  aschmidt@company.com            # Extended patterns
  schmidta@company.com
  andres@company.com

# 4. Résolution DNS MX (avec cache)
company.com → mx.company.com (cache hit: 66.7%)

# 5. Connexion SMTP
CONNECT mx.company.com:25
EHLO vps.auraia.ch
MAIL FROM:<verify@vps.auraia.ch>

# 6. Test catch-all
RCPT TO:<chk_random123@company.com>
  → 550 Rejected → Serveur honnête ✅
  → 250 OK → Catch-all détecté ⚠️

# 7. Test patterns (si pas catch-all)
Pour chaque pattern (avec 1s délai):
  RCPT TO:<pattern@company.com>
  → 250 OK → EMAIL TROUVÉ ! ✅
  → 550 Rejected → Pattern suivant

# 8. Retour résultat
{
  "status": "valid",
  "email": "andre.schmidt@company.com",
  "catchAll": false,
  "debugInfo": "Match: andre.schmidt@company.com (high confidence)"
}
```

---

## 📊 Détails techniques

### 1. Normalisation des noms

**Problème** : Noms avec accents, tirets, espaces multiples

**Solution** : `unidecode` + regex cleanup

```python
# Entrée : "Jean-François Müller"
# Sortie :
first_variants = ["jean-francois", "jeanfrancois"]
last_variants = ["muller"]
```

**Code** : `backend/core/email_finder.py` → `normalize_name()`

**Cas gérés** :
- ✅ Accents : André → andre
- ✅ Tirets : Jean-Paul → ["jean-paul", "jeanpaul"]
- ✅ Caractères spéciaux : D'Angelo → dangelo
- ✅ Espaces multiples : "John  Doe" → ["john"], ["doe"]

### 2. Génération de patterns

**9 patterns standards** :
1. `first.last@` (80% des cas)
2. `firstlast@`
3. `f.last@`
4. `first.l@`
5. `first@`
6. `last@`
7. `flast@` ← Pattern étendu
8. `lastf@` ← Pattern étendu
9. `firstl@` ← Pattern étendu

**Ordre important** : Les plus communs d'abord = résultat plus rapide.

**Code** : `backend/core/email_finder.py` → `generate_patterns()`

**Optimisation** : Dédoublonnage automatique (ex: si first=last, pas de doublon)

### 3. Cache MX Records

**Problème initial** :
- 200 recherches/jour = 200 requêtes DNS
- DNS lookup = 50-100ms
- Charge inutile sur les serveurs DNS

**Solution** : Cache en mémoire avec TTL

```python
class MXCache:
    def __init__(self, ttl=3600):  # 1 heure
        self._cache = {}  # {domain: ([mx_list], timestamp)}

    def get(self, domain):
        if domain in cache and not expired:
            return cached_mx_list  # Cache HIT ⚡
        return None  # Cache MISS
```

**Impact mesuré** :
- Hit rate : 50-70%
- Économie DNS : 100-150 requêtes/jour
- Réduction latence : 50-100ms par hit

**Code** : `backend/core/mx_cache.py`

**Cleanup** : TTL expiré = auto-suppression au prochain get()

### 4. Détection catch-all

**Problème** : Certains serveurs acceptent TOUT pendant SMTP, puis rejettent après.

**Exemples réels** :
- Microsoft 365 : Souvent catch-all
- Google Workspace : Parfois catch-all
- Serveurs classiques : Rarement catch-all

**Méthode de détection** :

```python
# 1. Générer email random
catch_all_email = f"chk_{random_9_chars}@domain.com"

# 2. Tester
RCPT TO:<chk_xyz123@domain.com>

# 3. Interpréter
if code == 250:
    # Serveur accepte un random → CATCH-ALL
    return {
        "status": "catch_all",
        "email": best_guess,  # Pattern #1
        "catchAll": true,
        "confidence": "low"
    }
else:
    # Serveur rejette → Honnête, continuer les tests
    test_real_patterns()
```

**Code** : `backend/core/email_finder.py` → `find_email()` (ligne 160)

**Impact UX** : L'utilisateur sait que le résultat est incertain (catch-all).

### 5. Rate limiting SMTP

**Règle CRITIQUE** : 1 seconde entre chaque pattern testé

```python
for i, pattern in enumerate(patterns):
    if i > 0:
        time.sleep(1)  # ANTI-BAN

    is_valid, log, code = self.verify_email(pattern, mx_host)
```

**Pourquoi ?**
- Serveurs mail détectent les scans automatiques
- Trop rapide = IP bannie temporairement (1h-24h)
- 1s = perçu comme "humain"

**Volume actuel** : 200 recherches/jour = safe
**Seuil risque** : > 1000 recherches/jour sans délai

### 6. Logs structurés

**Avant** :
```python
print(f"DNS Error: {e}")  # Difficile à parser
```

**Après** :
```python
logger.error("DNS query failed", domain="example.com", error=str(e))
# Format : JSON ou plain text selon config
```

**Output JSON** :
```json
{
  "timestamp": "2026-01-28T09:30:45.123Z",
  "level": "ERROR",
  "logger": "email_finder",
  "message": "DNS query failed",
  "domain": "example.com",
  "error": "Timeout"
}
```

**Code** : `backend/core/logger.py`

**Usage** : `from core.logger import StructuredLogger`

---

## 🗄️ Base de données

### Schéma SQLite

```sql
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    domain TEXT NOT NULL,
    full_name TEXT NOT NULL,
    status TEXT NOT NULL,  -- valid/catch_all/not_found/error
    email TEXT,
    catch_all BOOLEAN DEFAULT 0,
    patterns_tested TEXT,  -- JSON array
    mx_records TEXT,       -- JSON array
    smtp_logs TEXT,        -- JSON array
    debug_info TEXT,
    error_message TEXT
);
```

**Taille actuelle** : 233 KB (114 entrées)

**Croissance** : ~2 KB par recherche → 1 GB = ~500 000 recherches

**Indexation** : Aucune pour l'instant (pas nécessaire avec ce volume)

**Backup** : Manuel via `cp /root/data/email_finder.db`

**Code** : `backend/database.py`

---

## 🔐 Sécurité

### 1. Basic Auth (Frontend)

```nginx
location / {
    auth_basic "Email Finder";
    auth_basic_user_file /etc/nginx/.htpasswd;

    proxy_pass http://localhost:3000;
}
```

**Credentials** : Stockés dans `/etc/nginx/.htpasswd` (bcrypt)

**Changement** :
```bash
htpasswd -c /etc/nginx/.htpasswd admin
systemctl reload nginx
```

### 2. API non authentifiée

⚠️ **L'API backend n'a PAS d'auth** : `http://192.3.81.106:8000`

**Acceptable car** :
- Usage interne uniquement
- Pas d'opérations destructives
- Pas de données sensibles
- Volume faible

**Si besoin de sécuriser** :

```python
# Option 1 : API Key
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(403, "Invalid API key")

@app.post("/api/find-email", dependencies=[Depends(verify_api_key)])
```

```python
# Option 2 : IP Whitelist
from fastapi import Request

@app.middleware("http")
async def ip_whitelist(request: Request, call_next):
    client_ip = request.client.host
    if client_ip not in ALLOWED_IPS:
        return JSONResponse({"error": "Forbidden"}, 403)
    return await call_next(request)
```

### 3. SMTP Security

**Pas d'authentification SMTP** : On ne se connecte pas à un compte mail, on utilise SMTP pour vérifier uniquement.

**Commandes envoyées** :
```
EHLO vps.auraia.ch
MAIL FROM:<verify@vps.auraia.ch>
RCPT TO:<test@target.com>
QUIT
```

**Pas de STARTTLS** : Non nécessaire (pas d'envoi réel de mail)

**Reverse DNS** : `192.3.81.106` → `vps.auraia.ch` (bon pour délivrabilité)

---

## 🚀 Performance

### Benchmarks

| Opération | Temps moyen | Notes |
|-----------|-------------|-------|
| DNS MX lookup | 50-100ms | Avec cache : 0ms |
| SMTP connection | 200-500ms | Dépend du serveur cible |
| Pattern test (1) | 300-800ms | Avec 1s sleep |
| Recherche complète | 3-10s | 9 patterns max |

### Goulots d'étranglement

1. **SMTP latency** (non optimisable)
   - Dépend du serveur mail cible
   - Microsoft 365 : ~300ms
   - Gmail : ~200ms
   - Petits serveurs : 500-1000ms

2. **Rate limiting 1s** (volontaire)
   - Nécessaire pour éviter les bans
   - Ne peut pas être réduit sans risque

3. **DNS lookup** (optimisé ✅)
   - Avant : 50-100ms par recherche
   - Après cache : 0ms (hit rate 66%)

### Scalabilité

**Volume actuel** : 200 recherches/jour ✅

**Limite théorique** :
- SQLite : 10 000 recherches/jour
- Cache mémoire : Illimité (TTL 1h)
- SMTP : Limité par les bans serveurs (max ~1000/jour par domaine cible)

**Si > 1000 recherches/jour** :
1. Migrer vers PostgreSQL
2. Distribuer sur plusieurs IPs
3. Augmenter le cache TTL (6h)
4. Implémenter un système de queue

---

## 🧪 Tests

### Structure des tests

```
backend/tests/
├── conftest.py           # Fixtures partagées
├── test_email_finder.py  # Tests unitaires (152 lignes)
└── test_api.py          # Tests API (134 lignes)
```

### Ce qui est testé

**Normalisation** :
```python
def test_normalize_name_with_accents():
    # André Müller → ["andre"], ["muller"]
    first, last = finder.normalize_name("André Müller")
    assert "andre" in first
    assert "muller" in last
```

**Patterns** :
```python
def test_generate_patterns_extended():
    patterns = finder.generate_patterns(["john"], ["doe"], "example.com")
    # Vérifier les 9 patterns
    assert "john.doe@example.com" in patterns
    assert "jdoe@example.com" in patterns  # Pattern étendu
```

**Catch-all** :
```python
@patch.object(EmailFinder, 'verify_email')
def test_detect_catch_all(mock_verify):
    mock_verify.return_value = (True, "250 OK", 250)  # Random accepted
    result = finder.find_email("example.com", "John Doe")
    assert result.status == "catch_all"
```

**API** :
```python
def test_find_email_success(client):
    response = client.post("/api/find-email", json={
        "domain": "example.com",
        "fullName": "John Doe"
    })
    assert response.status_code == 200
```

### Lancer les tests

```bash
cd backend

# Tous les tests
pytest tests/ -v

# Avec coverage
pytest tests/ -v --cov --cov-report=html

# Tests spécifiques
pytest tests/test_email_finder.py::TestNormalization -v

# Tests rapides uniquement (skip slow)
pytest tests/ -v -m "not slow"
```

### Coverage actuel

```
Module                   Stmts   Miss  Cover
-------------------------------------------
core/email_finder.py       124      8    94%
database.py                 30      1    97%
main.py                     88     15    83%
models.py                   14      0   100%
-------------------------------------------
TOTAL                      609     87    86%
```

**Tests qui échouent** : 6/37 (mocking database incomplet, non critique)

---

## 🐛 Debugging

### Logs utiles

```bash
# Logs du service
journalctl -u email-finder -f

# Logs applicatifs
tail -f /root/logs/email_finder.log

# Dernières erreurs
tail -100 /root/logs/email_finder.log | grep -i error

# Logs SMTP (si activé debug)
# Modifier email_finder.py : server.set_debuglevel(1)
```

### Mode debug

**Activer le debug SMTP** :
```python
# backend/core/email_finder.py
def verify_email(self, email, mx_host):
    server = smtplib.SMTP(timeout=10)
    server.set_debuglevel(1)  # ← Activer ici
    # ...
```

**Output** :
```
send: 'ehlo vps.auraia.ch\r\n'
reply: b'250-mx.example.com\r\n'
send: 'mail FROM:<verify@vps.auraia.ch>\r\n'
reply: b'250 2.1.0 Ok\r\n'
send: 'rcpt TO:<test@example.com>\r\n'
reply: b'550 5.1.1 User unknown\r\n'
```

### Problèmes fréquents

**1. Port 25 bloqué**
```bash
# Test manuel
telnet mx.example.com 25
# Si timeout → Port bloqué par l'hébergeur
```

**2. IP bannie**
```bash
# Test depuis le VPS
ssh root@192.3.81.106
python3 backend/verify_vps.py
# Si toutes les recherches échouent → Ban temporaire
```

**3. Cache ne fonctionne pas**
```python
# Vérifier l'import
from core.mx_cache import MXCache  # ← Doit être présent

# Vérifier l'initialisation
finder = EmailFinder(mx_cache_ttl=3600)  # ← Cache activé
```

**4. Database locked**
```bash
# Si "database is locked"
lsof /root/data/email_finder.db
# Killer le process si nécessaire
```

---

## 📈 Monitoring

### Métriques à surveiller

**1. Hit rate cache** (cible: > 50%)
```bash
curl -s http://192.3.81.106:8000/api/cache/stats | jq .hit_rate
```

**2. Taux de succès** (cible: > 70%)
```sql
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM search_history), 2) as percentage
FROM search_history
GROUP BY status;
```

**3. Performance** (cible: < 10s par recherche)
```bash
time curl -X POST http://192.3.81.106:8000/api/find-email \
  -H "Content-Type: application/json" \
  -d '{"domain":"example.com","fullName":"John Doe"}'
```

**4. Mémoire** (cible: < 500 MB)
```bash
ssh root@192.3.81.106 "ps aux | grep uvicorn"
# Check la colonne %MEM
```

### Alertes recommandées

- ⚠️ Service down : `systemctl is-active email-finder != active`
- ⚠️ Taux erreur > 20% : Check bans SMTP
- ⚠️ Cache hit rate < 30% : Vérifier TTL
- ⚠️ DB > 1 GB : Archiver vieilles recherches

---

## 🔮 Évolutions futures

### Court terme (priorité moyenne)

**1. Health check endpoint**
```python
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "uptime": get_uptime(),
        "cache_stats": finder.mx_cache.stats(),
        "db_size": get_db_size()
    }
```

**2. Backup automatique DB**
```bash
# Cron job quotidien
0 2 * * * cp /root/data/email_finder.db /root/backups/email_finder_$(date +\%Y\%m\%d).db
```

**3. Métriques Prometheus** (si monitoring avancé)

### Long terme (low priority)

**1. OSINT integration**
- LinkedIn scraping pour confirmer les emails
- Hunter.io API en fallback

**2. Machine Learning**
- Prédire le pattern le plus probable selon l'entreprise
- Réduire le nombre de tests SMTP

**3. Queue system**
- Bulk search asynchrone
- Priorité aux recherches répétées

**4. Multi-IP support**
- Round-robin sur plusieurs IPs
- Éviter les bans à haut volume

---

**Document maintenu par** : Adrian Turion
**Dernière mise à jour** : 28 janvier 2026
