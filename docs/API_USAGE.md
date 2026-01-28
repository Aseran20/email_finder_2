# Email Finder API

API interne pour vérifier l'existence d'adresses email via SMTP.

## Endpoints

### Base URL
```
http://192.3.81.106:8000
```

### 1. Vérifier un email

**POST** `/api/find-email`

```bash
curl -X POST "http://192.3.81.106:8000/api/find-email" \
  -H "Content-Type: application/json" \
  -d '{"domain": "company.com", "fullName": "John Doe"}'
```

**Paramètres :**
| Champ | Type | Description |
|-------|------|-------------|
| `domain` | string | Domaine de l'entreprise (ex: `auraia.ch`) |
| `fullName` | string | Nom complet de la personne (ex: `Adrian Turion`) |

**Réponse :**
```json
{
  "status": "valid",
  "email": "adrian.turion@auraia.ch",
  "catchAll": false,
  "mxRecords": ["auraia-ch.mail.protection.outlook.com"],
  "patternsTested": ["adrian.turion@auraia.ch", "adrianturion@auraia.ch", ...],
  "smtpLogs": ["Pattern adrian.turion@auraia.ch: ... 250 2.1.5 Recipient OK"],
  "debugInfo": "MX: auraia-ch.mail.protection.outlook.com | Match: adrian.turion@auraia.ch (high confidence)",
  "errorMessage": null
}
```

**Status possibles :**
| Status | Signification | Confiance |
|--------|---------------|-----------|
| `valid` | Email trouvé et vérifié | Haute |
| `catch_all` | Serveur accepte tout, email deviné | Basse |
| `not_found` | Aucun pattern n'a matché | - |
| `error` | Erreur technique (pas de MX, timeout...) | - |

---

### 2. Bulk search (fichier CSV/Excel)

**POST** `/api/bulk-search`

```bash
curl -X POST "http://192.3.81.106:8000/api/bulk-search" \
  -F "file=@contacts.csv"
```

**Format CSV attendu :**
```csv
domain,fullName
auraia.ch,Adrian Turion
google.com,Sundar Pichai
```

Ou avec colonnes séparées :
```csv
domain,first_name,last_name
auraia.ch,Adrian,Turion
```

---

### 3. Historique des recherches

**GET** `/api/history?limit=50`

```bash
curl "http://192.3.81.106:8000/api/history?limit=10"
```

---

## Exemples d'intégration

### Python
```python
import requests

def find_email(domain: str, full_name: str) -> dict:
    response = requests.post(
        "http://192.3.81.106:8000/api/find-email",
        json={"domain": domain, "fullName": full_name}
    )
    return response.json()

# Usage
result = find_email("auraia.ch", "Adrian Turion")
if result["status"] == "valid":
    print(f"Email trouvé: {result['email']}")
elif result["status"] == "catch_all":
    print(f"Email probable (catch-all): {result['email']}")
else:
    print(f"Non trouvé: {result['debugInfo']}")
```

### JavaScript/Node
```javascript
async function findEmail(domain, fullName) {
  const response = await fetch("http://192.3.81.106:8000/api/find-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain, fullName })
  });
  return response.json();
}

// Usage
const result = await findEmail("auraia.ch", "Adrian Turion");
console.log(result.email); // adrian.turion@auraia.ch
```

### Claude Code (session interactive)
```bash
curl -s -X POST "http://192.3.81.106:8000/api/find-email" \
  -H "Content-Type: application/json" \
  -d '{"domain":"TARGET_DOMAIN","fullName":"PERSON_NAME"}'
```

---

## Notes techniques

- **Rate limiting** : 1 seconde entre chaque pattern testé (anti-ban)
- **Timeout** : 10 secondes par connexion SMTP
- **Pas d'auth** : API ouverte (usage interne uniquement)
- **Frontend** : https://email.auraia.ch (Basic Auth)

## Liens

- **Frontend web** : https://email.auraia.ch
- **API directe** : http://192.3.81.106:8000
- **Docs OpenAPI** : http://192.3.81.106:8000/docs
