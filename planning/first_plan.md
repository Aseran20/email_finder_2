# Spécification fonctionnelle et technique – Mini AnyMailFinder interne (IPRoyal)

Ce document est destiné au développeur qui va réaliser le MVP. L’objectif est que tu puisses démarrer et livrer quelque chose de fonctionnel sans avoir à re-poser 50 questions.

L’UI de référence est inspirée d’AnyMailFinder (screenshot "UI_example.png" fourni par Adrian).

---

## 1. Objectif du projet

Mettre en place un outil interne de type "AnyMailFinder" qui permet de trouver ou de deviner des emails professionnels à partir de:

* Un domaine ou un nom de société
* Un prénom + nom

Contexte d’usage:

* M&A / prospection B2B
* Volume faible à modéré (quelques dizaines / centaines de recherches par jour)
* Pas de base de données d’emails à long terme
* Pas de crawling massif de sites web

L’outil se compose de:

* Un frontend web simple (UI type AnyMailFinder)
* Un backend API qui:

  * génère des patterns d’emails
  * interroge les serveurs MX
  * effectue des checks SMTP via des proxies IPRoyal (Residential, 1 GB déjà acheté)
  * renvoie un statut et éventuellement un email

---

## 2. Portée (scope)

### 2.1 Fonctionnalités MVP

> Important: le MVP est limité à la fonctionnalité d’« Email Tools Search » uniquement.
> Il n’y a pas de Bulk Search, Verify, Lead Tools, GeoLead Finder, Browser Extension,
> Automation, API publiques, intégrations tierces, ni système de login.

1. Formulaire de recherche (colonne gauche)

* Modes de recherche (radios):

  * `Person search` (par défaut)

* Champs:

  * `domain` (string)

    * Domaine
    * Obligatoire pour lancer une recherche
  * `fullName` (string)

    * Prénom + nom
    * Obligatoire si `mode` = `person` ou `decisionMaker`
    * Désactivé si `mode` = `company` ou `linkedin`

* Bouton "Search"

  * Inactif si `domain` est vide
  * Affiche "Searching..." lorsque la requête vers l’API est en cours

2. Historique des recherches (colonne droite)

* Liste d’entrées de recherche, du plus récent au plus ancien

* Chaque entrée affiche:

  * Domaine / nom de société
  * Nom complet (si fourni)
  * Date / heure locale
  * Statut:

    * `Valid`
    * `Not found`
    * `Unknown` (pour domaines catch-all ou résultats incertains)
    * `Error`
    * `Searching...` (pendant la requête)
  * Email trouvé (si présent)
  * Bloc de debug repliable (texte brut)

* Filtre rapide sur l’historique:

  * Champ texte "History search..." filtrant client-side sur domaine, nom ou email

3. Historique uniquement à l’écran

* Le MVP ne comporte pas d’export CSV ni de fonctionnalité de téléchargement.

* L’historique est uniquement visible dans l’UI, en mémoire côté frontend.

* Bouton "Export"

* Génération côté frontend d’un CSV sur l’historique local, avec colonnes:

  * `Date`
  * `Mode`
  * `Domain/Company`
  * `Full name`
  * `Status`
  * `Email`

4. Endpoint backend principal

* `POST /api/find-email`
* Entrée JSON minimale:

  * `mode`: `person` | `company` | `decisionMaker` | `linkedin`
  * `domainOrCompany`: string
  * `fullName`: string optionnel
* Sortie JSON:

  * `status`: `valid` | `not_found` | `unknown` | `error`
  * `email`: string optionnel
  * `patternsTested`: tableau de strings (patterns générés)
  * `smtpLogs`: tableau de strings (logs courts par essai SMTP)
  * `catchAll`: booléen
  * `mxRecords`: tableau de strings
  * `debugInfo`: string synthétique pour l’UI
  * `errorMessage`: string optionnelle

5. Intégration IPRoyal

* Utilisation de proxies Residential IPRoyal (pay as you go, 1 GB déjà acheté)
* Connexions SMTP vers les MX doivent passer par ces proxies
* Rotation simple des proxies (round-robin ou aléatoire) pour répartir les requêtes

### 2.2 Hors scope MVP

* Authentification utilisateur / multi-comptes
* Gestion de crédits / billing
* Base de données centralisée d’emails
* Crawling massif
* Analyse avancée par pays / secteur

---

## 3. Architecture générale

### 3.1 Vue d’ensemble

* **Frontend**

  * SPA React (TypeScript recommandé)
  * Style proche du screenshot fourni (UI_example.png)

* **Backend**

  * API REST (Python FastAPI recommandé pour aller vite)
  * Un endpoint principal `/api/find-email`
  * Logique métier email-finder encapsulée dans un module distinct

* **Services externes**

  * DNS / MX lookup (via bibliothèque)
  * Proxies IPRoyal (Residential) pour les connexions SMTP

### 3.2 Technologies recommandées

* Frontend:

  * React + TypeScript
  * Vite ou Create React App
  * TailwindCSS (ou framework CSS léger) pour reproduire un look similaire à AnyMailFinder

* Backend:

  * Python 3.10+
  * FastAPI + Uvicorn
  * `dnspython` pour MX lookup
  * `smtplib` ou client SMTP bas niveau pour engager la session
  * Eventuellement `asyncio` si tu veux paralléliser, mais ce n’est pas indispensable pour le MVP

---

## 4. Frontend – Détails

### 4.1 Layout

* Conteneur central (max-width ~1200 px)
* Deux colonnes:

  * Gauche: ~33 % de la largeur, bordure droite
  * Droite: ~67 %

Colonne gauche – "Start your Search"

* Radios pour le `mode`
* Input `domainOrCompany`
* Input `fullName` (désactivé lorsque mode = `company` ou `linkedin`)
* Bouton "Search"
* Texte d’information en bas (ex: "Internal tool – no external credits used")

Colonne droite – "Search history"

* Header:

  * Titre
  * Champ filtre (aucun bouton Export dans le MVP)
* Liste scrollable de cartes
* Carte:

  * Zone gauche: domaine, nom, date, `debugInfo` (dans un `<details>` / `<summary>`)
  * Zone droite: badge statut + email

### 4.2 Cycle de vie d’une recherche

1. L’utilisateur remplit le formulaire et clique sur "Search".
2. Le frontend:

   * crée un item d’historique avec un id unique (par ex. `Date.now().toString()`), statut `pending` / `Searching...`;
   * envoie un `POST /api/find-email` avec `{ mode, domainOrCompany, fullName }`.
3. À la réponse:

   * trouve l’item par `id`;
   * met à jour `status`, `email`, `debugInfo`.
4. En cas d’erreur HTTP / réseau:

   * `status = error`;
   * `debugInfo = "Backend error / network issue"`.

### 4.3 Stockage de l’historique

* Pour le MVP, stockage en mémoire côté frontend (state React).
* Pas besoin de persistance backend.
* Option: ajouter plus tard un stockage local (localStorage) si besoin.

---

## 5. Backend – Détails

### 5.1 Endpoint `/api/find-email`

**Méthode:** `POST`

**Entrée JSON:**

```json
{
  "mode": "person",
  "domainOrCompany": "genoud-freres.ch",
  "fullName": "Martial Genoud"
}
```

**Sortie JSON (exemple succès):**

```json
{
  "status": "valid",
  "email": "martial@genoud-freres.ch",
  "patternsTested": [
    "firstname.lastname@genoud-freres.ch",
    "firstname@genoud-freres.ch",
    "f.lastname@genoud-freres.ch"
  ],
  "smtpLogs": [
    "mx1.genoud-freres.ch: 250 OK RCPT TO:<martial@genoud-freres.ch>",
    "mx1.genoud-freres.ch: 550 user unknown pour m.genoud@genoud-freres.ch"
  ],
  "catchAll": false,
  "mxRecords": [
    "mx1.genoud-freres.ch"
  ],
  "debugInfo": "MX: mx1.genoud-freres.ch | 3 patterns testés | Match: firstname.lastname@",
  "errorMessage": null
}
```

**Sortie JSON (exemple not found):**

```json
{
  "status": "not_found",
  "email": null,
  "patternsTested": ["..."],
  "smtpLogs": ["..."],
  "catchAll": false,
  "mxRecords": ["mx.mailhost.ch"],
  "debugInfo": "MX: mx.mailhost.ch | 10 patterns testés | aucun RCPT TO accepté",
  "errorMessage": null
}
```

**Sortie JSON (exemple catch-all / inconnu):**

```json
{
  "status": "unknown",
  "email": "martial.genoud@genoud-freres.ch", // best guess optionnel
  "patternsTested": ["..."],
  "smtpLogs": ["..."],
  "catchAll": true,
  "mxRecords": ["mx1.genoud-freres.ch"],
  "debugInfo": "MX catch-all détecté | best guess: firstname.lastname@",
  "errorMessage": null
}
```

### 5.2 Étapes de traitement

1. **Normalisation des inputs**

* `domainOrCompany`:

  * si c’est une URL complète (avec `http`, `https`), extraire le host et garder le domaine
  * convertir en lowercase
  * trim espaces

* `fullName` (mode person/decision):

  * trim
  * séparer en `firstName`, `lastName` (split sur espace, prendre le premier et le dernier)
  * retirer accents (é → e, ü → u, etc.)
  * passer en lowercase
  * supprimer caractères spéciaux inutiles

2. **Génération de patterns**

À partir de `firstName`, `lastName`, `domain`:

* `firstname.lastname@domain`
* `firstname@domain`
* `lastname@domain`
* `f.lastname@domain`
* `firstname.l@domain`
* `flastname@domain`
* `firstname_lastname@domain`
* `firstname-lastname@domain`
* `lastname.firstname@domain`

Objectif MVP: une quinzaine de patterns max. Ordre des patterns: du plus fréquent au plus rare (firstname.lastname en premier).

3. **MX lookup**

* Utiliser `dnspython` (ou équivalent) pour récupérer les enregistrements MX du domaine.
* Si aucun MX trouvé:

  * `status = error`
  * `errorMessage = "No MX records found for domain"`

4. **Connexion SMTP via proxies IPRoyal**

#### 5.2.4.1 Configuration IPRoyal

Les proxies IPRoyal Residential seront fournis sous forme d’URLs, par exemple:

* `http://user:pass@proxy.iproyal.com:12345`
* `socks5://user:pass@proxy.iproyal.com:12345`

À mettre dans un fichier `.env` ou config:

* `IPROYAL_PROXIES=http://user:pass@host1:port1, http://user:pass@host2:port2, ...`

Le backend:

* parse cette variable en liste
* pour chaque tentative SMTP, choisit un proxy dans cette liste (round-robin ou aléatoire)

#### 5.2.4.2 Logique SMTP

Pour chaque pattern candidat (dans la limite d’un nombre max de tests, par exemple 10):

* Choisir un MX (le premier de la liste, ou tenter le suivant en cas d’erreur réseau)
* Choisir un proxy IPRoyal
* Établir une connexion TCP vers `mx_host:25` via ce proxy
* Envoyer la séquence:

  * `EHLO your-host`
  * `MAIL FROM:<test@your-domain>` (adresse fictive mais syntaxiquement valide)
  * `RCPT TO:<candidate@domain>`
* Lire la réponse du serveur sur `RCPT TO`:

  * `250` / `251`: considérer le pattern comme **valide** (sauf si le domaine est catch-all, voir plus bas)
  * `550` / `551`: utilisateur inexistant
  * `450`, `451`, `421`: erreurs temporaires (greylisting / rate limit)

Paramètres recommandés:

* Timeout connexion: 3–5 s
* Timeout lecture: 3–5 s
* Max patterns testés par requête: 10 (pour limiter le volume)
* Max tentatives par domaine si erreurs temporaires: 2–3

5. **Détection catch-all**

* Tester 1 ou 2 adresses volontairement absurdes (ex: `zzq123invalid@domain`)
* Si le serveur renvoie `250` sur ces adresses:

  * marquer `catchAll = true`
  * considérer que la validation SMTP ne permet pas de distinguer les bons patterns

6. **Décision**

* Si au moins un pattern renvoie `250` et `catchAll = false`:

  * `status = valid`
  * `email = pattern correspondant`

* Si aucun pattern n’est accepté (`550` partout) et pas de catch-all:

  * `status = not_found`

* Si `catchAll = true` ou la majorité des réponses sont des `4xx` (greylisting) ou timeouts:

  * `status = unknown`
  * option: renvoyer un `email` best guess (ex: `firstname.lastname@domain`)

* En cas d’erreur technique (DNS, proxy, exception non récupérée):

  * `status = error`
  * `errorMessage` renseigné

7. **Construction de `debugInfo`**

* Exemple:

  * "MX: mx1.genoud-freres.ch | 6 patterns testés | Match: firstname.lastname@"
  * "MX: mx.mailhost.ch | 8 patterns testés | aucun RCPT TO accepté"
  * "MX: mx1.company.com | catch-all détecté | best guess: firstname.lastname@"

Ce champ est simplement un résumé humain lisible des principaux éléments pour l’UI.

### 5.3 Gestion de la rotation IPRoyal

* Charger la liste des proxies depuis la config
* Stratégie simple de round-robin:

  * garder un index global en mémoire
  * à chaque nouvelle tentative SMTP, utiliser `proxies[index]`, puis `index = (index + 1) % len(proxies)`
* En cas d’erreur réseau persistante sur un proxy:

  * option MVP: logguer l’erreur, passer au proxy suivant
  * option plus tard: marquer le proxy comme "down" pendant X minutes

### 5.4 Logging

* Logs applicatifs

  * requêtes entrantes (sans stocker les emails en base persistante)
  * MX retournés
  * statut global de la requête (valid / not_found / unknown / error)
* `smtpLogs` renvoyé dans la réponse contiendra des mini-lignes textuelles utiles au debug frontend

---

## 6. Sécurité et compliance

* Usage B2B uniquement (emails professionnels)
* Pas de stockage de masse des emails
* Pas d’envoi d’emails depuis cet outil (simple vérification, pas de campagne)
* Configurer convenablement les timeouts et limites pour ne pas surcharger les serveurs MX

---

## 7. Roadmap de développement

### Phase 1 – Backend core (CLI ou script simple)

* Implémenter un script Python qui prend en entrée:

  * domaine
  * prénom
  * nom
* Implémenter:

  * normalisation du nom
  * génération des patterns
  * MX lookup
  * check SMTP via **un** proxy IPRoyal (configuré en dur pour commencer)
* Tester sur quelques domaines réels fournis par Adrian

### Phase 2 – Gestion multi-proxies + détection catch-all

* Ajouter parsing de la variable `IPROYAL_PROXIES`
* Implémenter la rotation des proxies
* Ajouter la logique de test catch-all

### Phase 3 – Exposition FastAPI `/api/find-email`

* Emballer la logique dans un service/une fonction réutilisable
* Créer l’endpoint HTTP
* Structurer la réponse comme défini section 5.1

### Phase 4 – Frontend React

* Reproduire la UI d’AnyMailFinder à partir du screenshot
* Brancher le bouton "Search" sur l’endpoint `/api/find-email`
* Gérer les états `pending`, `valid`, `not_found`, `unknown`, `error`
* Afficher `debugInfo` dans le bloc dépliable
* Brancher le bouton "Search" sur l’endpoint `/api/find-email`
* Gérer les états `pending`, `valid`, `not_found`, `unknown`, `error`
* Afficher `debugInfo` dans le bloc dépliable

### Phase 5 – Nettoyage et documentation – Nettoyage et documentation

* Factoriser le code, gérer les constantes (timeouts, nb max de patterns)
* Ajouter un `.env.example` avec:

  * `IPROYAL_PROXIES`
  * `APP_PORT`
* Rédiger un mini README:

  * comment installer les dépendances backend/frontend
  * comment remplir `.env`
  * comment lancer le backend et le frontend en local

---

## 8. Critères de validation

Le MVP est considéré comme livré lorsque:

* L’UI permet de saisir un domaine + nom/prénom et d’afficher un résultat dans l’historique
* Le backend est capable de:

  * trouver les MX,
  * tester quelques patterns via SMTP avec les proxies IPRoyal,
  * renvoyer un email `status = valid` pour au moins certains domaines,"
