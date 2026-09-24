#!/usr/bin/env bash
# Régénère les images « Grille du jour » du site (à relancer tous les 3 mois).
#
#   tools/gen_daily.sh            # 120 jours à partir d'aujourd'hui (Europe/Paris)
#   tools/gen_daily.sh 2026-12-20 # à partir d'une autre date
#   DAYS=90 tools/gen_daily.sh    # autre durée
#
# Produit, dans assets/daily/ :
#   AAAA-MM-JJ.png   1080×1080, grille vide du défi de ce jour-là
#                    (règle de l'app : classique_{(jour_de_l_année % 100) + 1})
#   og-latest.png    1200×630, image de partage (og:image) de la page
#   manifest.json    liste des dates disponibles (lue par js/daily.js)
# Supprime les images datées d'avant-hier et plus anciennes, puis met à jour
# l'image de repli (sans JavaScript) de grille-du-jour.html et en/daily.html.
#
# Prérequis : Python 3 + Pillow ; le dépôt de l'app en lecture seule dans
# $CAFE_APP_DIR (défaut /Applications/CafeFleches/cafe_fleches) pour les
# grilles et les polices.
set -euo pipefail

SITE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
START="${1:-$(TZ=Europe/Paris date +%F)}"
DAYS="${DAYS:-120}"

cd "$SITE_DIR"
python3 - "$START" "$DAYS" <<'PY'
import datetime as dt, json, sys
from pathlib import Path
sys.path.insert(0, "tools")
import render_grid as rg

start = dt.date.fromisoformat(sys.argv[1])
days = int(sys.argv[2])
out = Path("assets/daily")
out.mkdir(parents=True, exist_ok=True)

keep_from = start - dt.timedelta(days=2)
for p in out.glob("????-??-??.png"):
    if dt.date.fromisoformat(p.stem) < keep_from:
        p.unlink()
        print("supprimé", p)

for i in range(days):
    d = start + dt.timedelta(days=i)
    gid = rg.daily_grid_id(d)
    rg.save_png(rg.compose_square(rg.load_grid(gid), d), out / f"{d}.png")

# og:image : les robots des réseaux sociaux n'exécutent pas le JavaScript,
# l'image est donc fixe jusqu'à la prochaine régénération — d'où un titre
# sans date.
rg.save_png(rg.compose_og(rg.load_grid(rg.daily_grid_id(start)), None,
                          headline="La grille du jour"), out / "og-latest.png")

dates = sorted(p.stem for p in out.glob("????-??-??.png"))
manifest = {
    "generated": start.isoformat(),
    "rule": "classique_{(jour_de_l_annee % 100) + 1}",
    "dates": dates,
    "grids": {d: rg.daily_grid_id(dt.date.fromisoformat(d)) for d in dates},
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
print(f"{days} images de {start} à {start + dt.timedelta(days=days - 1)} ; {len(dates)} en tout")
PY

# Image de repli (visiteurs sans JavaScript) : l'image du jour de génération.
for page in grille-du-jour.html en/daily.html; do
  [ -f "$page" ] || continue
  sed -i.bak -E "s#(/cafe-fleches/assets/daily/)[0-9]{4}-[0-9]{2}-[0-9]{2}\.png#\1${START}.png#g" "$page"
  rm -f "$page.bak"
done

du -sh assets/daily
