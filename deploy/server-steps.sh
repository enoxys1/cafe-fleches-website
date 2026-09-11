#!/usr/bin/env bash
#
# Mise en ligne de https://enoxys.fr/cafe-fleches
# ------------------------------------------------------------------
# À lancer SUR LE SERVEUR OVH, depuis le Mac :  ssh ovh
#
# Ce fichier n'est PAS conçu pour être exécuté d'un bloc les yeux fermés.
# Chaque étape est idempotente et commentée ; lisez, puis copiez-collez
# étape par étape, en vérifiant la sortie avant de passer à la suivante.
#
# Prérequis : le dépôt https://github.com/enoxys1/cafe-fleches-website
# existe (privé) et la branche `cafe-fleches` du hub a été fusionnée dans
# `master` — voir l'étape 5.
#
set -euo pipefail

APPS=/home/ubuntu/apps
SITE_DIR="$APPS/cafe-fleches-website"
COMPOSE="$APPS/docker-compose.yml"
NGINX_CONF="$APPS/nginx.conf"
NGINX_CTR=enoxys-nginx           # container_name du service nginx
STAMP=$(date +%Y%m%d-%H%M%S)

# ==================================================================
# 0. Sauvegardes préalables (on modifie deux fichiers de production)
# ==================================================================
cp -a "$COMPOSE"    "$COMPOSE.bak-$STAMP"
cp -a "$NGINX_CONF" "$NGINX_CONF.bak-$STAMP"
echo "Sauvegardes : $COMPOSE.bak-$STAMP et $NGINX_CONF.bak-$STAMP"

# ==================================================================
# (a) Cloner le dépôt du site
# ==================================================================
# Le clone se fait à côté des autres sites (fracture-website,
# stellar-dominion-website). Si le dossier existe déjà, on se contente
# de le mettre à jour : l'étape est rejouable sans dégât.
if [ -d "$SITE_DIR/.git" ]; then
  echo "== dépôt déjà présent, mise à jour"
  git -C "$SITE_DIR" pull --ff-only
else
  echo "== clonage du site"
  git clone https://github.com/enoxys1/cafe-fleches-website.git "$SITE_DIR"
fi

# Contrôle : les 8 pages doivent être là.
ls "$SITE_DIR"/index.html "$SITE_DIR"/privacy.html "$SITE_DIR"/terms.html \
   "$SITE_DIR"/contact.html "$SITE_DIR"/en/index.html "$SITE_DIR"/en/privacy.html \
   "$SITE_DIR"/en/terms.html "$SITE_DIR"/en/contact.html

# ==================================================================
# (b) Monter le site dans le conteneur nginx
# ==================================================================
# Le service nginx de docker-compose.yml monte déjà, dans cet ordre :
#   - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
#   - ./geodb/dist:/var/www/geodb/dist:ro
#   - ./stellar-dominion-website:/var/www/stellar-dominion:ro
#   - ./fracture-website:/var/www/fracture-website:ro
#   - /etc/letsencrypt:/etc/letsencrypt:ro
# On insère la ligne Café Fléchés juste après celle de Fracture, en
# conservant son indentation (6 espaces).
VOLUME_LINE='      - ./cafe-fleches-website:/var/www/cafe-fleches-website:ro'

if grep -qF 'cafe-fleches-website:/var/www/cafe-fleches-website' "$COMPOSE"; then
  echo "== volume déjà présent, rien à faire"
else
  echo "== ajout du volume au service nginx"
  # awk plutôt que sed : l'indentation YAML (6 espaces) est écrite telle
  # quelle, sans dépendre des règles d'échappement de `sed a\`.
  awk -v line="$VOLUME_LINE" '
    { print }
    /- \.\/fracture-website:\/var\/www\/fracture-website:ro/ { print line }
  ' "$COMPOSE" > "$COMPOSE.new"
  mv "$COMPOSE.new" "$COMPOSE"
fi

# Contrôle : la ligne doit apparaître UNE seule fois, dans le service nginx.
grep -n 'cafe-fleches-website' "$COMPOSE"
grep -c 'cafe-fleches-website:/var/www/cafe-fleches-website' "$COMPOSE"   # doit afficher 1
# Et la syntaxe YAML doit rester valide :
sudo docker compose -f "$COMPOSE" config >/dev/null && echo "docker-compose.yml : OK"

# ==================================================================
# (c) Ajouter le bloc location dans nginx.conf
# ==================================================================
# Forme calquée sur le bloc « Fracture website (public) » déjà en place :
#     location /fracture {
#         alias /var/www/fracture-website;
#         index index.html;
#         try_files $uri $uri.html $uri/ /fracture/index.html;
#     }
# Le `$uri.html` est ce qui permet d'écrire les liens sans extension
# (/cafe-fleches/privacy → privacy.html). Aucun en-tête particulier n'est
# nécessaire : le site est public, statique, sans authentification —
# contrairement à /fracture/admin et /fracture/viewer qui, eux, portent
# un `auth_request`.
#
# Le bloc est inséré JUSTE AVANT `location /ops` : nginx choisit le
# préfixe le plus long, l'ordre n'est donc pas fonctionnellement critique,
# mais on respecte l'ordre de lecture du fichier (les sites, puis /ops,
# puis le catch-all `location /` du hub).

if grep -q 'location /cafe-fleches' "$NGINX_CONF"; then
  echo "== bloc nginx déjà présent, rien à faire"
else
  echo "== insertion du bloc location /cafe-fleches"
  # On écrit le bloc dans un fichier temporaire (heredoc entre quotes :
  # ni $uri ni les accolades ne sont interprétés par le shell), puis awk
  # l'insère AVANT la ligne `location /ops`.
  cat > /tmp/cafe-fleches.location <<'NGINX'
    # Café Fléchés website (public)
    location /cafe-fleches {
        alias /var/www/cafe-fleches-website;
        index index.html;
        try_files $uri $uri.html $uri/ /cafe-fleches/index.html;
    }

NGINX
  # Sécurité : il ne doit y avoir qu'un seul `location /ops`.
  test "$(grep -c '^[[:space:]]*location /ops' "$NGINX_CONF")" -eq 1

  awk '
    /^[[:space:]]*location \/ops/ && !done {
      while ((getline l < "/tmp/cafe-fleches.location") > 0) print l
      done = 1
    }
    { print }
  ' "$NGINX_CONF" > "$NGINX_CONF.new"
  mv "$NGINX_CONF.new" "$NGINX_CONF"
  rm -f /tmp/cafe-fleches.location
fi

# Contrôle visuel : le bloc doit précéder /ops et suivre /stellar.
grep -n 'location /\(fracture\|stellar\|cafe-fleches\|ops\)' "$NGINX_CONF"

# ==================================================================
# (d) Recréer le conteneur nginx (obligatoire : nouveau volume)
# ==================================================================
# Un `nginx -s reload` ne suffit PAS ici : un montage de volume ne
# s'ajoute qu'à la création du conteneur. D'où le `up -d` qui le recrée.
cd "$APPS"
sudo docker compose up -d nginx

# Le volume doit être visible dans le conteneur :
sudo docker exec "$NGINX_CTR" ls /var/www/cafe-fleches-website/index.html

# Test de configuration AVANT tout reload. Ne jamais recharger une
# configuration qui ne passe pas `nginx -t` : cela tue le service.
sudo docker exec "$NGINX_CTR" nginx -t
sudo docker exec "$NGINX_CTR" nginx -s reload

# ==================================================================
# (e) Mettre à jour le hub (carte « Café Fléchés » + bannière)
# ==================================================================
# Prérequis : la branche `cafe-fleches` a été fusionnée dans `master`
# sur GitHub (voir la commande de merge dans le rapport). Le hub est une
# image construite localement : il faut donc un --build, pas un simple
# restart, pour embarquer apps.json, app.js et assets/banner_cafe-fleches.png.
cd "$APPS/EnoxysHUB"
git pull --ff-only
cd "$APPS"
sudo docker compose up -d --build enoxys-hub

# ⚠️ Après un rebuild, le conteneur reçoit une NOUVELLE IP Docker. Les
# `proxy_pass` de nginx qui pointent vers `enoxys-hub` sont résolus au
# démarrage : sans reload, nginx continue d'envoyer vers l'ancienne IP et
# le hub répond 502. C'est l'incident déjà documenté côté serveur.
sudo docker exec "$NGINX_CTR" nginx -t
sudo docker exec "$NGINX_CTR" nginx -s reload

# ==================================================================
# (f) Vérifications
# ==================================================================
# Toutes les lignes doivent afficher 200.
# `-L` suit la redirection : comme pour /fracture, nginx renvoie un 301 de
# /cafe-fleches vers /cafe-fleches/ (alias + index sur un répertoire).
for u in \
  https://enoxys.fr/ \
  https://enoxys.fr/cafe-fleches \
  https://enoxys.fr/cafe-fleches/privacy \
  https://enoxys.fr/cafe-fleches/terms \
  https://enoxys.fr/cafe-fleches/contact \
  https://enoxys.fr/cafe-fleches/en/ \
  https://enoxys.fr/cafe-fleches/en/privacy \
  https://enoxys.fr/cafe-fleches/en/terms \
  https://enoxys.fr/cafe-fleches/en/contact \
  https://enoxys.fr/cafe-fleches/css/style.css \
  https://enoxys.fr/cafe-fleches/assets/logo.png \
  https://enoxys.fr/assets/banner_cafe-fleches.png
do
  printf '%-58s %s\n' "$u" "$(curl -sL -o /dev/null -w '%{http_code}' "$u")"
done

# La carte doit être servie par l'API du hub :
curl -s https://enoxys.fr/api/apps | grep -o 'cafe-fleches' | head -1

# Le titre de la page d'accueil du site :
curl -s https://enoxys.fr/cafe-fleches | grep -o '<title>[^<]*</title>'

echo
echo "Terminé. En cas de problème, restaurer :"
echo "  cp -a $COMPOSE.bak-$STAMP $COMPOSE"
echo "  cp -a $NGINX_CONF.bak-$STAMP $NGINX_CONF"
echo "  cd $APPS && sudo docker compose up -d nginx"
