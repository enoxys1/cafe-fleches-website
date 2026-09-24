# cafe-fleches-website

Site public de **Café Fléchés** — jeu de mots fléchés français pour iOS et
Android, édité par Enoxys.

En ligne (une fois déployé) : <https://enoxys.fr/cafe-fleches>

## Contenu

| Chemin | URL publique |
|---|---|
| `index.html` | `/cafe-fleches` |
| `privacy.html` | `/cafe-fleches/privacy` |
| `terms.html` | `/cafe-fleches/terms` |
| `contact.html` | `/cafe-fleches/contact` |
| `en/index.html` | `/cafe-fleches/en/` |
| `en/privacy.html` | `/cafe-fleches/en/privacy` |
| `en/terms.html` | `/cafe-fleches/en/terms` |
| `en/contact.html` | `/cafe-fleches/en/contact` |
| `grille-du-jour.html` | `/cafe-fleches/grille-du-jour` |
| `defi.html` | `/cafe-fleches/defi` (redirection vers la grille du jour, lien de partage de l'app) |
| `en/daily.html` | `/cafe-fleches/en/daily` |

Les liens internes sont écrits **sans extension** : nginx résout `$uri.html`
(voir la directive `try_files` ci-dessous), comme pour les sites Fracture et
Stellar Dominion.

```
css/style.css     direction artistique (papier crème, ambre, chocolat)
js/main.js        menu mobile, apparition au défilement, lien de nav actif
assets/           logo 512 px, favicon 64 px, 3 captures 600 px de large
deploy/           script des commandes à lancer sur le serveur
js/daily.js       grille du jour : choix de l'image selon la date à Paris
assets/daily/     images de la grille du jour (120 jours), og-latest.png, manifest.json
tools/            render_grid.py (rendu PNG d'une grille), gen_daily.sh
promo/            kit de promotion (messages, kit presse, images 1200×630)
```

## Principes

- **Site statique pur.** Aucun script tiers, aucun traceur, aucune mesure
  d'audience, aucun cookie. La seule ressource externe est Google Fonts
  (Fredoka pour les titres, Inter pour le corps).
- **Aucun formulaire** posté vers un serveur : la page contact propose
  uniquement un lien `mailto:contact@enoxys.fr`.
- **Mode sombre** via `prefers-color-scheme`, fond `#1E120A`.
- **Règle de la charte** : jamais de texte clair sur l'ambre — le token
  `--on-amber` vaut le chocolat `#281402` dans les deux modes.

## Aperçu local

```sh
python3 -m http.server 8000
# puis http://localhost:8000/  (les liens absolus /cafe-fleches/… ne
# fonctionnent qu'une fois servis sous ce préfixe ; pour un aperçu fidèle :
mkdir -p /tmp/preview/cafe-fleches && cp -R . /tmp/preview/cafe-fleches/
cd /tmp/preview && python3 -m http.server 8000
# → http://localhost:8000/cafe-fleches/
```

## Grille du jour

Les images `assets/daily/AAAA-MM-JJ.png` couvrent 120 jours à partir de leur
génération (règle de l'app : `classique_{(jour_de_l_année % 100) + 1}`).
**À relancer tous les 3 mois**, puis commit + push + `git pull` sur le serveur :

```sh
tools/gen_daily.sh            # Python 3 + Pillow ; lit les grilles et les
                              # polices dans /Applications/CafeFleches/cafe_fleches
```

Au-delà de la dernière date générée, la page affiche la dernière image
disponible avec un avertissement. `tools/render_grid.py --help` pour le rendu
d'une grille isolée (vide, résolue, format réseaux sociaux).

## Déploiement

Le site est servi par le conteneur **nginx** du serveur OVH
(`/home/ubuntu/apps/docker-compose.yml`), comme les autres sites Enoxys :

1. le dépôt est cloné dans `/home/ubuntu/apps/cafe-fleches-website` ;
2. il est monté en lecture seule dans le conteneur nginx :
   `./cafe-fleches-website:/var/www/cafe-fleches-website:ro` ;
3. `/home/ubuntu/apps/nginx.conf` contient, avant le bloc `location /ops` :

```nginx
    # Café Fléchés website (public)
    location /cafe-fleches {
        alias /var/www/cafe-fleches-website;
        index index.html;
        try_files $uri $uri.html $uri/ /cafe-fleches/index.html;
    }
```

Les commandes exactes, étape par étape, sont dans
[`deploy/server-steps.sh`](deploy/server-steps.sh). **Ce script n'est pas fait
pour être exécuté à l'aveugle** : lisez-le, il commente chaque étape.

### Mise à jour du site une fois en place

```sh
ssh ovh
cd /home/ubuntu/apps/cafe-fleches-website && git pull
# Le volume est monté en direct : aucun rebuild, aucun reload nginx nécessaire
# pour un simple changement de contenu.
```

## Licence

© Enoxys. Tous droits réservés. Le logo, les textes et les captures sont la
propriété d'Enoxys.
