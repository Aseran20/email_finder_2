# Email Finder - Notes de session

> Dernière mise à jour : 27 janvier 2026

## État du projet

**Status** : Fonctionnel, en production sur VPS

| Composant | URL | Tech |
|-----------|-----|------|
| Frontend | https://email.auraia.ch | React + Vite + Tailwind (Basic Auth) |
| Backend API | http://192.3.81.106:8000 | FastAPI + Python |
| Docs Swagger | http://192.3.81.106:8000/docs | Auto-généré |

## Architecture

```
nginx (443) ─── Basic Auth ─── Frontend statique
     │
     └── Reverse proxy ─── Backend FastAPI (:8000) ─── SMTP direct vers MX
                                    │
                               SQLite (historique)
```

**VPS** : RackNerd (192.3.81.106)
- Hostname : `vps.auraia.ch`
- Email from : `verify@vps.auraia.ch`
- Pas de proxy, connexion SMTP directe

## Comment utiliser l'API

### Vérifier un email
```bash
curl -s -X POST "http://192.3.81.106:8000/api/find-email" \
  -H "Content-Type: application/json" \
  -d '{"domain":"company.com","fullName":"John Doe"}'
```

### Réponses possibles
| Status | Signification | Confiance |
|--------|---------------|-----------|
| `valid` | Email trouvé et vérifié | Haute |
| `catch_all` | Serveur accepte tout, email deviné | Basse |
| `not_found` | Aucun pattern n'a matché | - |
| `error` | Erreur technique | - |

Voir `API_USAGE.md` pour la doc complète.

## Déploiement

### Backend
```powershell
.\deploy_clean.ps1
```
- Zip les fichiers
- SCP vers VPS
- Relance uvicorn

### Frontend
Pas de script automatisé. Probablement :
```powershell
cd frontend
npm run build
scp -r dist/* root@192.3.81.106:/var/www/email.auraia.ch/
```
*(À vérifier le path exact sur le VPS)*

## Limites connues

### Serveurs catch-all
- Microsoft 365 et Google sont souvent catch-all
- Impossible de vérifier avec certitude via SMTP
- Solutions alternatives (non implémentées) :
  - Envoyer un vrai mail et attendre le bounce
  - Pixel tracking (mais nécessite que le destinataire ouvre)
  - OSINT (LinkedIn, site web)

### Risque de ban
- Volume actuel (200/jour) : risque faible
- Délai 1s entre chaque test : ok
- Pas de reverse DNS configuré (à améliorer)

## Améliorations possibles (non prioritaires)

- [ ] Ajouter API Key pour sécuriser l'accès
- [ ] Systemd au lieu de nohup (restart auto)
- [ ] Script de déploiement frontend
- [ ] Configurer reverse DNS pour l'IP du VPS
- [ ] Patterns supplémentaires (variantes de domaine avec/sans "sa")

## Décisions prises

1. **Pas de Docker** - Overkill pour l'usage (interne, 200 calls/jour)
2. **Pas de tracking pixel** - Trop intrusif, abîme la délivrabilité
3. **Pas d'API key pour l'instant** - Usage interne uniquement
4. **Garder l'archi simple** - Ça marche, pas besoin de complexifier

## Contacts testés (exemples)

| Nom | Domaine | Résultat |
|-----|---------|----------|
| Adrian Turion | auraia.ch | `valid` - adrian.turion@auraia.ch |
| Kevin Zambaz | sylvapro.ch | `catch_all` - kevin.zambaz@sylvapro.ch (probable) |
| Kevin Zambaz | sylvaprosa.ch | `not_found` - pas de mail sur ce domaine |
| Oleksii Kostiak | centuriongroup.ch | `valid` - oleksii.kostiak@centuriongroup.ch |

---

## Pour reprendre le projet

1. Lire ce fichier + `API_USAGE.md`
2. L'API est prête à l'emploi, juste curl
3. Frontend sur https://email.auraia.ch (demander le mdp Basic Auth)
4. Code source dans ce repo
