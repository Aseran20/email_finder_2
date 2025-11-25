1) Les paramètres techniques du proxy

À transmettre au dev (copier-coller):

Hostname

geo.iproyal.com

Port

12321

Username

jY3laCsXluKQB2Gp

Password

sr1t3rutpV6UvcXZ

Protocole

http (par défaut) ou https

Pour un client bas niveau, on pourra aussi le considérer comme un proxy HTTP classique

Sous forme de “proxy URL” exploitable directement dans le code ou dans un .env:

http://jY3laCsXluKQB2Gp:sr1t3rutpV6UvcXZ@geo.iproyal.com:12321


Tu peux lui dire que c’est un résidentiel rotating, donc IPRoyal change d’IP automatiquement à chaque requête (pas besoin de gérer la rotation côté app pour l’instant).

2) Ce qu’il n’a PAS besoin de toucher

Residential Orders / logs / stats dans l’interface IPRoyal

Auto top-up (à laisser désactivé au début)

Sub-users

Changement de pays / ville pour le moment (Random suffit largement pour un POC)

Tout ça, tu peux le gérer toi-même si un jour tu veux affiner (par ex. bloquer sur Europe, etc.), mais ce n’est pas nécessaire pour coder le MVP.

3) Comment l’intégrer côté backend (ce que tu peux lui écrire)

Tu peux lui donner une section “config” concrète comme ça:

Dans .env:

IPROYAL_PROXY_URL=http://jY3laCsXluKQB2Gp:sr1t3rutpV6UvcXZ@geo.iproyal.com:12321


Et dans le code, l’idée sera:

Lire IPROYAL_PROXY_URL

Lorsqu’il ouvre une connexion SMTP vers mx.host:25, il doit passer par ce proxy HTTP

en pratique: soit via une lib qui gère les proxies, soit via un tunnel TCP au-dessus du proxy HTTP

Pour le MVP, un seul proxy suffit, pas besoin de liste/rotation côté app (IPRoyal le fait déjà avec “Randomize IP”)

Tu peux lui préciser aussi:

Ne jamais hardcoder le user/pass dans le code

Tout passe par les variables d’environnement / fichier de config non versionné