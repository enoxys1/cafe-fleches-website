# Café Fléchés : kit presse

## En quelques lignes

**Café Fléchés** est une application de mots fléchés français pour iPhone,
iPad et Android, éditée par ENOXYS. Elle reprend la grille du journal telle
qu'on la fait au comptoir : définitions dans les cases, flèches en bord de
case, lettres qui se croisent. Le joueur choisit la taille de la grille (Mini
8×8, Classique 10×10, Grande 13×13) et, séparément, la force des définitions,
des plus directes aux plus allusives. 604 grilles sont installées avec
l'application, un défi Classique change chaque jour, et tout fonctionne sans
compte et hors connexion. L'application est gratuite ; un achat unique de
2,99 € (sans abonnement) débloque les indices illimités et retire la
publicité.

## Présentation (à reprendre telle quelle)

> Une grille, un café, dix minutes pour soi. Café Fléchés propose des mots
> fléchés français dessinés comme ceux de la presse, sur téléphone et
> tablette. Trois formats, du 8×8 le temps d'un expresso au 13×13 du
> week-end, et trois forces de définitions qui se choisissent à part : des
> définitions directes pour commencer, un vocabulaire plus soutenu, puis les
> définitions allusives et à double sens des magazines de jeux. Chaque jour,
> une nouvelle grille attend le joueur sur la page d'accueil, et
> l'application tient son carnet : grilles terminées, jours d'affilée, temps
> moyen par format. La saisie a été pensée pour ne pas freiner (le curseur
> saute les cases remplies, un mot terminé enchaîne sur le suivant), et la
> lecture pour ne pas fatiguer : taille des définitions réglable, contraste
> renforcé, thème sombre, VoiceOver et TalkBack. Pas de compte, pas de
> connexion nécessaire : la progression reste sur l'appareil.

## Fiche technique

| | |
|---|---|
| Nom | Café Fléchés |
| Genre | Jeu de lettres, mots fléchés |
| Éditeur | ENOXYS (France) |
| Plateformes | iPhone et iPad (iOS 15 ou plus récent), Android (téléphones et tablettes) |
| Langue | Français (grilles et interface) |
| Sortie | Septembre 2026 (App Store et Google Play) |
| Prix | Gratuit ; Premium 2,99 €, achat unique, sans abonnement, restaurable |
| Contenu | 604 grilles installées : 3 formats (Mini 8×8, Classique 10×10, Grande 13×13) × 3 forces de définitions, plus un défi quotidien |
| Publicité | Jamais imposée. Un indice offert par grille ; pour un indice de plus, une courte publicité, seulement si le joueur le demande. Aucune avec Premium |
| Premium | Indices illimités, sans publicité, 3 styles de grille en plus (Papier journal, Nuit, Nature), solution complète |
| Compte | Aucun ; progression, statistiques et réglages stockés sur l'appareil |
| Connexion | Non nécessaire, tout fonctionne hors ligne |
| Accessibilité | Taille des définitions jusqu'à ×1,6, contraste renforcé, thème sombre, VoiceOver (iOS) et TalkBack (Android) sur chaque case |
| Classification | 4+ (App Store), PEGI 3 (Google Play) |

## Liens

- Site : https://enoxys.fr/cafe-fleches
- Grille du jour (image du défi, mise à jour chaque jour) : https://enoxys.fr/cafe-fleches/grille-du-jour
- App Store : https://apps.apple.com/fr/app/id6811005313
- Google Play : https://play.google.com/store/apps/details?id=com.cafefleches.app
- Confidentialité : https://enoxys.fr/cafe-fleches/privacy
- Autres jeux ENOXYS : https://enoxys.fr

## Contact

ENOXYS : **contact@enoxys.fr**

Demandes d'interview, de visuels en haute définition ou de précisions :
écrire à l'adresse ci-dessus.

## Visuels disponibles

### Dans ce dépôt (site)

| Fichier | Format |
|---|---|
| `assets/logo.png` | icône de l'application, 512×512 |
| `promo/carte-604-grilles-1200x630.png` | carte de présentation, chiffres clés |
| `promo/grille-du-jour-1200x630.png` | une grille vide, format paysage |
| `promo/grille-resolue-floutee-1200x630.png` | une grille à moitié résolue, le reste flouté |
| `assets/daily/AAAA-MM-JJ.png` | la grille vide de chaque jour, 1080×1080 (120 jours d'avance) |

N'importe quelle grille (vide ou résolue, carrée ou 1200×630) se génère avec
`tools/render_grid.py` (voir `--help`).

### Dans le dépôt de l'application (`cafe_fleches/store_assets/`)

Captures d'écran officielles des fiches App Store et Google Play, en
français. Écrans : `01_accueil` (accueil et défi du jour), `02_grille`
(grille en cours), `03_forces` (choix du format et de la force),
`04_victoire` (fin de grille), `05_sombre` (thème sombre), `06_premium`
(Premium).

| Dossier | Appareil | Taille | Écrans |
|---|---|---|---|
| `ios-6.9/` | iPhone 6,9″ | 1320×2868 | 01 à 06 |
| `ios-6.5/` | iPhone 6,5″ | 1284×2778 | 01 à 06 |
| `ios-13/` | iPad 13″ | 2064×2752 | 01 à 05 |
| `play/phone/` | téléphone Android | 1080×1920 | 01 à 06 |
| `play/tablet-7/` | tablette 7″ | 1080×1920 | 01 à 03 |
| `play/tablet-10/` | tablette 10″ | 1440×2560 | 01 à 03 |
| `play/feature_graphic_1024x500.png` | bannière Google Play | 1024×500 | |
| `play/icon_512.png` | icône | 512×512 | |
| `iap-review/` | écran Premium (revue de l'achat intégré) | 750×1334, 1170×2532, 1242×2208 | |

`play/phone/raw/` et `play/tablet-10/raw/` contiennent les captures brutes
(plein écran, avant la mise en page de la fiche Google Play).

Trois captures allégées (600 px de large) sont aussi en ligne sur le site :
`assets/shot_accueil.png`, `assets/shot_jeu.png`, `assets/shot_victoire.png`.

## Droits

Les visuels et captures ci-dessus peuvent être reproduits librement pour
parler de Café Fléchés. Le nom, le logo et les grilles restent la propriété
d'ENOXYS.
