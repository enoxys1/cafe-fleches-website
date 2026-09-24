#!/usr/bin/env python3
"""Rendu PNG d'une grille Café Fléchés (Pillow + polices du jeu).

Reproduit le plateau de l'application (thème « Classique ») :
cases lettres crème, cases définition beiges avec texte en capitales
Barlow Condensed, triangle plein collé au bord pour le sens, cases doubles
coupées en deux (→ en haut, ↓ en bas), trame chocolat, lettres en Lora.
La mise en page des définitions suit `definition_text_layout.dart` :
jamais de coupure au milieu d'un mot (césure seulement après un trait
d'union), le corps descend pas à pas jusqu'à ce que le texte tienne.

Formats de sortie :
  (défaut)  carré 1080×1080 : bandeau « Café Fléchés · Défi du … »,
            grille centrée, mention « Réponse dans l'app » ;
  --og      1200×630 pour le partage social (grille à gauche, texte à droite) ;
  --card    1200×630, carte de présentation (chiffres clés + mini-grille).

Options : --solved (lettres), --blur F (avec --solved : floute la fraction F
des lettres, en diagonale vers le bas à droite), --date AAAA-MM-JJ (grille du
défi de ce jour-là, même règle que l'app), --no-date (bandeau sans date).

Exemples :
  tools/render_grid.py --date 2026-09-24 -o /tmp/defi.png
  tools/render_grid.py classique_042 --solved -o /tmp/solution.png
  tools/render_grid.py --date 2026-09-24 --og -o /tmp/og.png
  tools/render_grid.py --card -o /tmp/card.png

Emplacements (surchargeables par variables d'environnement) :
  CAFE_APP_DIR   dépôt de l'app (défaut /Applications/CafeFleches/cafe_fleches),
                 d'où sont lues assets/grids/ et assets/fonts/ (lecture seule).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

APP_DIR = Path(os.environ.get("CAFE_APP_DIR", "/Applications/CafeFleches/cafe_fleches"))
GRIDS_DIR = APP_DIR / "assets" / "grids"
FONTS_DIR = APP_DIR / "assets" / "fonts"
SITE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = SITE_DIR / "assets" / "logo.png"

# Charte (site + thème de grille « Classique » de l'app, grid_themes.dart).
PAPER = (0xFA, 0xED, 0xD9)       # crème
AMBER = (0xF4, 0xA4, 0x1C)
AMBER_WASH = (0xFB, 0xE3, 0xA6)
INK = (0x28, 0x14, 0x02)         # chocolat
INK_SOFT = (0x7B, 0x46, 0x0B)
LETTER_BG = (0xFD, 0xF6, 0xE7)
DEF_BG = (0xF3, 0xE2, 0xBE)
BLACK_BG = INK

SS = 2  # suréchantillonnage : dessin à 2×, réduction Lanczos à la fin

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# ---------------------------------------------------------------------------
# Polices
# ---------------------------------------------------------------------------

_font_cache: dict = {}


def font(name: str, size: float, weight: int | None = None) -> ImageFont.FreeTypeFont:
    size = max(1, int(round(size)))
    key = (name, size, weight)
    f = _font_cache.get(key)
    if f is None:
        files = {
            "fredoka": "Fredoka-Variable.ttf",
            "lora": "Lora-Variable.ttf",
            "lora-italic": "Lora-Italic-Variable.ttf",
            "barlow": "BarlowCondensed-Medium.ttf",
            "barlow-semibold": "BarlowCondensed-SemiBold.ttf",
        }
        f = ImageFont.truetype(str(FONTS_DIR / files[name]), size)
        if weight is not None:
            axes = f.get_variation_axes()
            values = []
            for ax in axes:
                n = ax["name"]
                n = n.decode() if isinstance(n, bytes) else n
                values.append(weight if n.lower() == "weight" else ax["default"])
            f.set_variation_by_axes(values)
        _font_cache[key] = f
    return f


def text_w(f: ImageFont.FreeTypeFont, s: str) -> float:
    return f.getlength(s)


def fit_font(name: str, text: str, max_w: float, start: float, weight=None, min_size=8):
    size = start
    while size > min_size and text_w(font(name, size, weight), text) > max_w:
        size -= 1
    return font(name, size, weight)


# ---------------------------------------------------------------------------
# Grilles et règle du défi du jour
# ---------------------------------------------------------------------------

def day_of_year(d: dt.date) -> int:
    """`_dayOfYear()` de home_state.dart : 1 le 1er janvier."""
    return (d - dt.date(d.year, 1, 1)).days + 1


def daily_grid_id(d: dt.date) -> str:
    """`classique_{(jour_de_l_année % 100) + 1}` (100 grilles Classique)."""
    return f"classique_{(day_of_year(d) % 100) + 1:03d}"


def load_grid(ref: str) -> dict:
    p = Path(ref)
    if not p.suffix:
        p = GRIDS_DIR / f"{ref}.json"
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def date_fr(d: dt.date, weekday=True) -> str:
    jour = "1er" if d.day == 1 else str(d.day)
    s = f"{jour} {MOIS[d.month - 1]}"
    return f"{JOURS[d.weekday()]} {s}" if weekday else s


# ---------------------------------------------------------------------------
# Mise en page des définitions (portage de definition_text_layout.dart)
# ---------------------------------------------------------------------------

NO_BREAK_BEFORE = {"!", "?", ":", ";", "»", "…"}


def _tokenize(text: str):
    out = []
    for word in text.split():
        if word in NO_BREAK_BEFORE and out:
            # « À LA VÔTRE ! » : la ponctuation haute ne part jamais seule
            # à la ligne (espace insécable, comme en typographie française).
            prev, glued = out[-1]
            out[-1] = (f"{prev} {word}", glued)
            continue
        parts = word.split("-")
        for i, part in enumerate(parts):
            piece = part if i == len(parts) - 1 else part + "-"
            if piece:
                out.append((piece, i > 0))
    return out


def _wrap(tokens, f, max_w):
    space = text_w(f, "n n") - text_w(f, "nn")
    lines, cur, cur_w = [], "", 0.0
    for tok, glued in tokens:
        w = text_w(f, tok)
        if w > max_w:
            return None
        if not cur:
            cur, cur_w = tok, w
            continue
        extra = w if glued else w + space
        if cur_w + extra <= max_w:
            cur = cur + tok if glued else f"{cur} {tok}"
            cur_w += extra
        else:
            lines.append(cur)
            cur, cur_w = tok, w
    if cur:
        lines.append(cur)
    return lines


def _ellipsize(s, f, max_w):
    if text_w(f, s) <= max_w:
        return s
    for end in range(len(s) - 1, 0, -1):
        c = s[:end].rstrip() + "…"
        if text_w(f, c) <= max_w:
            return c
    return "…"


def layout_definition(raw, max_w, max_h, max_lines, base, floor, step):
    """Retourne (lignes, police, taille) — jamais de mot coupé."""
    text = raw.strip().upper()
    tokens = _tokenize(text)
    if not tokens:
        return [], None, 0
    hard_floor = floor * 0.7
    size = base
    while size >= floor:
        f = font("barlow", size)
        lines = _wrap(tokens, f, max_w)
        if lines is not None and len(lines) <= max_lines and len(lines) * size <= max_h:
            return lines, f, size
        size -= step
        if size < floor and floor > hard_floor:
            # Mot très long (« CARACTÉRISTIQUE » dans une demi-case) : on
            # s'autorise un plancher plus bas plutôt que de tronquer.
            floor = hard_floor
    # Plancher atteint : on garde un maximum de mots entiers, puis « … ».
    f = font("barlow", floor)
    fit = max(1, int(max_h // floor))
    limit = min(max_lines, fit)
    space = text_w(f, "n n") - text_w(f, "nn")
    lines, cur, cur_w, dropped = [], "", 0.0, False
    for tok, glued in tokens:
        piece = _ellipsize(tok, f, max_w)
        w = text_w(f, piece)
        if not cur:
            cur, cur_w = piece, w
            continue
        extra = w if glued else w + space
        if cur_w + extra <= max_w:
            cur = cur + piece if glued else f"{cur} {piece}"
            cur_w += extra
        elif len(lines) + 1 < limit:
            lines.append(cur)
            cur, cur_w = piece, w
        else:
            dropped = True
            break
    if cur:
        lines.append(cur)
    if dropped and lines and not lines[-1].endswith("…"):
        lines[-1] = _ellipsize(lines[-1] + "…", f, max_w)
    print(f"  ! définition tronquée : {raw!r}", file=sys.stderr)
    return lines, f, floor


# ---------------------------------------------------------------------------
# Plateau
# ---------------------------------------------------------------------------

def _arrow(draw, rect, direction, length):
    l, t, r, b = rect
    half_base = length * 0.62
    edge = 1.5 * SS
    if direction == "down":
        cx, tip = (l + r) / 2, b - edge
        pts = [(cx, tip), (cx - half_base, tip - length), (cx + half_base, tip - length)]
    else:
        cy, tip = (t + b) / 2, r - edge
        pts = [(tip, cy), (tip - length, cy - half_base), (tip - length, cy + half_base)]
    draw.polygon(pts, fill=INK)


def _definition_part(draw, rect, text, direction, cell, half, stats):
    arrow_len = cell * (0.19 if half else 0.22)
    gap = cell * 0.04
    inset = cell * (0.04 if half else 0.06)
    l, t, r, b = rect
    al, at, ar, ab = l + inset, t + inset, r - inset, b - inset
    if direction == "down":
        ab -= arrow_len + gap
    else:
        ar -= arrow_len + gap
    _arrow(draw, rect, direction, arrow_len)
    if not text.strip():
        return
    max_w, max_h = ar - al, ab - at
    base = cell * 0.242
    floor = cell * 0.10  # ≈ plancher de 5 pt de l'app pour une case de 50 pt
    lines, f, size = layout_definition(text, max_w, max_h, 2 if half else 3,
                                       base, floor, step=max(0.5, cell / 200))
    if not lines:
        return
    stats["min_size"] = min(stats.get("min_size", 1e9), size / cell)
    step = size * 1.0
    y = at + (max_h - step * len(lines)) / 2
    for line in lines:
        w = text_w(f, line)
        if w > max_w + 0.5:
            stats["overflow"] = stats.get("overflow", 0) + 1
        draw.text((al + (max_w - w) / 2, y + step / 2), line, font=f, fill=INK, anchor="lm")
        y += step


def render_board(grid: dict, cell: int, solved=False, blur=0.0) -> Image.Image:
    """Plateau seul, fond transparent autour, taille cols*cell × rows*cell (1×)."""
    cols, rows = grid["cols"], grid["rows"]
    c = cell * SS
    rule = max(1.0, cell * 0.022) * SS
    img = Image.new("RGB", (cols * c, rows * c), LETTER_BG)
    draw = ImageDraw.Draw(img)
    stats: dict = {}

    def rect_of(x, y):
        return (x * c, y * c, (x + 1) * c, (y + 1) * c)

    for cl in grid["cells"]:
        fill = {"black": BLACK_BG, "definition": DEF_BG}.get(cl["type"], LETTER_BG)
        draw.rectangle(rect_of(cl["x"], cl["y"]), fill=fill)

    # Contenus (avant la trame pour que les traits restent nets).
    for cl in grid["cells"]:
        rect = rect_of(cl["x"], cl["y"])
        if cl["type"] == "definition":
            arrow = cl.get("arrow", "right")
            if arrow == "rightdown":
                l, t, r, b = rect
                mid = (t + b) / 2
                sep = tuple(int(round(v * 0.35 + p * 0.65)) for v, p in zip(INK, DEF_BG))
                draw.line([(l + 2 * SS, mid), (r - 2 * SS, mid)], fill=sep, width=max(1, int(SS)))
                _definition_part(draw, (l, t, r, mid), cl.get("text", ""), "right", c, True, stats)
                _definition_part(draw, (l, mid, r, b), cl.get("textDown", ""), "down", c, True, stats)
            else:
                _definition_part(draw, rect, cl.get("text", ""), arrow, c, False, stats)
        elif cl["type"] == "letter" and solved:
            f = font("lora", c * 0.55, 600)
            l, t, r, b = rect
            draw.text(((l + r) / 2, (t + b) / 2 + c * 0.02), cl["solution"], font=f,
                      fill=INK, anchor="mm")

    if solved and blur > 0:
        # Floute les lettres de la partie basse-droite (diagonale).
        # Chaque case est floutée seule : pas de bavure des cases voisines.
        threshold = (cols + rows - 2) * (1 - blur)
        for cl in grid["cells"]:
            if cl["type"] == "letter" and cl["x"] + cl["y"] >= threshold:
                box = rect_of(cl["x"], cl["y"])
                img.paste(img.crop(box).filter(ImageFilter.GaussianBlur(c * 0.11)), box[:2])

    # Trame continue + cadre plus gras (grid_board.dart).
    w = max(1, int(round(rule)))
    for i in range(1, cols):
        draw.line([(i * c, 0), (i * c, rows * c)], fill=INK, width=w)
    for j in range(1, rows):
        draw.line([(0, j * c), (cols * c, j * c)], fill=INK, width=w)
    draw.rectangle((0, 0, cols * c - 1, rows * c - 1), outline=INK, width=w * 2)

    if stats.get("overflow"):
        print(f"  ! {stats['overflow']} ligne(s) de définition trop large(s)", file=sys.stderr)
    render_board.last_stats = stats
    return img.resize((cols * cell, rows * cell), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Éléments de décor
# ---------------------------------------------------------------------------

def draw_cup(draw, x, y, h, color=INK):
    """Petite tasse fumante (remplace l'émoji ☕, absent des polices du jeu)."""
    w = h * 0.78
    lw = max(2, int(h * 0.085))
    top = y + h * 0.36
    body = (x, top, x + w, y + h)
    draw.rounded_rectangle(body, radius=h * 0.2, fill=color)
    draw.rectangle((x, top, x + w, top + h * 0.2), fill=color)
    # anse
    hx = x + w - lw * 0.5
    draw.arc((hx - h * 0.1, top + h * 0.1, hx + h * 0.32, top + h * 0.48), 270, 90, fill=color, width=lw)
    # vapeur
    for k in range(2):
        sx = x + w * (0.3 + 0.36 * k)
        draw.arc((sx - h * 0.09, y, sx + h * 0.09, y + h * 0.16), 90, 270, fill=color, width=lw)
        draw.arc((sx - h * 0.09, y + h * 0.14, sx + h * 0.09, y + h * 0.30), 270, 90, fill=color, width=lw)


def paste_logo(img, x, y, size):
    if not LOGO_PATH.exists():
        return
    logo = Image.open(LOGO_PATH).convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), radius=size * 0.9, fill=255)
    img.paste(logo, (x, y), mask.resize((size, size), Image.LANCZOS))


def pill(draw, x, y, text, f, fill, fg, pad_x=22, pad_y=12, outline=None):
    w = text_w(f, text)
    asc, desc = f.getmetrics()
    h = asc + desc
    box = (x, y, x + w + 2 * pad_x, y + h + 2 * pad_y)
    draw.rounded_rectangle(box, radius=(h + 2 * pad_y) / 2, fill=fill, outline=outline,
                           width=3 if outline else 0)
    draw.text((x + pad_x, y + pad_y + h / 2), text, font=f, fill=fg, anchor="lm")
    return box


# ---------------------------------------------------------------------------
# Compositions
# ---------------------------------------------------------------------------

def compose_square(grid, date: dt.date | None, solved=False, blur=0.0) -> Image.Image:
    W = H = 1080
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    band_h = 124
    draw.rectangle((0, 0, W, band_h), fill=AMBER)
    draw.line([(0, band_h), (W, band_h)], fill=INK, width=4)
    title = "Café Fléchés"
    if date:
        title += f" · Défi du {date_fr(date)}"
    cup_h = 50
    f = fit_font("fredoka", title, W - 2 * 56 - cup_h - 18, 50, weight=600)
    total = cup_h * 0.95 + 18 + text_w(f, title)
    x0 = (W - total) / 2
    draw_cup(draw, x0, band_h / 2 - cup_h / 2 - 2, cup_h)
    draw.text((x0 + cup_h * 0.95 + 18, band_h / 2), title, font=f, fill=INK, anchor="lm")

    foot_h = 84
    avail = H - band_h - foot_h - 2 * 28
    cell = min(avail // grid["rows"], (W - 2 * 60) // grid["cols"])
    board = render_board(grid, cell, solved, blur)
    bx = (W - board.width) // 2
    by = band_h + 28 + (avail - board.height) // 2
    # ombre « tampon » ambre, comme les cartes du site
    draw.rectangle((bx + 6, by + 6, bx + board.width + 6, by + board.height + 6), fill=(0xEA, 0xC0, 0x7A))
    img.paste(board, (bx, by))

    fy = H - foot_h / 2 - 6
    note = "Solution" if solved else "Réponse dans l'app"
    f1 = font("fredoka", 30, 500)
    f2 = font("fredoka", 30, 400)
    sep = "   ·   "
    t2 = "enoxys.fr/cafe-fleches"
    tw = text_w(f1, note) + text_w(f2, sep + t2)
    x = (W - tw) / 2
    draw.text((x, fy), note, font=f1, fill=INK, anchor="lm")
    draw.text((x + text_w(f1, note), fy), sep + t2, font=f2, fill=INK_SOFT, anchor="lm")
    return img


def compose_og(grid, date: dt.date | None, solved=False, blur=0.0, headline=None) -> Image.Image:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    margin = 34
    cell = (H - 2 * margin) // grid["rows"]
    board = render_board(grid, cell, solved, blur)
    bx, by = margin, (H - board.height) // 2
    draw.rectangle((bx + 6, by + 6, bx + board.width + 6, by + board.height + 6), fill=(0xEA, 0xC0, 0x7A))
    img.paste(board, (bx, by))

    x = bx + board.width + 56
    right = W - 48
    maxw = right - x
    paste_logo(img, x, 40, 92)
    ft = fit_font("fredoka", "Café Fléchés", maxw, 66, weight=600)
    draw.text((x, 206), "Café Fléchés", font=ft, fill=INK, anchor="ls")
    if headline is None:
        headline = f"Défi du {date_fr(date)}" if date else "La grille du jour"
    fh = fit_font("fredoka", headline, maxw, 40, weight=500)
    draw.text((x, 260), headline, font=fh, fill=INK_SOFT, anchor="ls")
    draw.line([(x, 292), (x + 90, 292)], fill=AMBER, width=6)

    fl = font("lora-italic", 34, 500)
    draw.text((x, 354), "Une grille, un café.", font=fl, fill=INK, anchor="ls")
    fs = font("fredoka", 28, 400)
    sub = "Le défi change chaque jour." if not solved else "La suite est dans l'app."
    draw.text((x, 400), sub, font=fs, fill=INK_SOFT, anchor="ls")

    fb = font("fredoka", 28, 600)
    pill(draw, x, 446, "Réponse dans l'app" if not solved else "Gratuit · iOS et Android",
         fb, AMBER, INK, outline=INK)
    fu = font("fredoka", 26, 400)
    draw.text((x, 580), "enoxys.fr/cafe-fleches", font=fu, fill=INK_SOFT, anchor="ls")
    return img


def compose_card(grid_count: int) -> Image.Image:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, H - 18, W, H), fill=AMBER)

    # Mini-grille résolue à droite, en décor.
    mini = load_grid("mini_f2_007") if (GRIDS_DIR / "mini_f2_007.json").exists() else load_grid("rapide_001")
    cell = 58
    board = render_board(mini, cell, solved=True)
    bx, by = W - board.width - 52, (H - 18 - board.height) // 2
    draw.rectangle((bx + 7, by + 7, bx + board.width + 7, by + board.height + 7), fill=(0xEA, 0xC0, 0x7A))
    img.paste(board, (bx, by))

    x, maxw = 64, bx - 64 - 40
    paste_logo(img, x, 56, 96)
    draw.text((x + 118, 104), "Café Fléchés", font=fit_font("fredoka", "Café Fléchés", maxw - 118, 60, 600),
              fill=INK, anchor="lm")
    draw.text((x, 200), "Mots fléchés façon kiosque", font=font("lora-italic", 34, 500),
              fill=INK_SOFT, anchor="ls")

    rows = [
        (f"{grid_count}", "grilles installées"),
        ("3", "formats : Mini, Classique, Grande"),
        ("3", "forces de définitions"),
    ]
    fv = font("fredoka", 54, 600)
    fl = font("fredoka", 30, 400)
    y = 250
    for value, label in rows:
        vw = text_w(fv, value)
        draw.text((x, y + 36), value, font=fv, fill=INK, anchor="lm")
        draw.text((x + max(vw, 96) + 18, y + 38), label, font=fl, fill=INK, anchor="lm")
        y += 74
    fp = fit_font("fredoka", "Sans compte, hors connexion", maxw - 44, 30, weight=600)
    pill(draw, x, y + 18, "Sans compte, hors connexion", fp, AMBER, INK, outline=INK)
    return img


# ---------------------------------------------------------------------------
# Sortie
# ---------------------------------------------------------------------------

def save_png(img: Image.Image, path: Path, colors=96):
    """PNG palettisé (quantification sans tramage) et optimisé."""
    path.parent.mkdir(parents=True, exist_ok=True)
    q = img.convert("RGB").quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                                    dither=Image.Dither.NONE)
    q.save(path, optimize=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("grid", nargs="?", help="id de grille (classique_042) ou chemin d'un JSON")
    ap.add_argument("-o", "--out", required=True, type=Path)
    ap.add_argument("--date", help="AAAA-MM-JJ : date du bandeau ; sans grille, prend le défi de ce jour")
    ap.add_argument("--no-date", action="store_true", help="bandeau sans date")
    ap.add_argument("--solved", action="store_true", help="affiche les lettres")
    ap.add_argument("--blur", type=float, default=0.0, help="avec --solved : fraction des lettres floutées")
    ap.add_argument("--og", action="store_true", help="format 1200×630 (partage social)")
    ap.add_argument("--card", action="store_true", help="carte de présentation 1200×630")
    ap.add_argument("--headline", help="--og : remplace la ligne « Défi du … »")
    ap.add_argument("--colors", type=int, default=96, help="taille de la palette PNG")
    a = ap.parse_args(argv)

    if a.card:
        manifest = json.load(open(GRIDS_DIR / "manifest.json", encoding="utf-8"))
        save_png(compose_card(len(manifest["grids"])), a.out, a.colors)
        print(a.out)
        return

    date = dt.date.fromisoformat(a.date) if a.date else None
    if a.grid:
        grid = load_grid(a.grid)
    elif date:
        grid = load_grid(daily_grid_id(date))
    else:
        ap.error("donner une grille ou --date")
    if a.no_date:
        date = None
    if a.og:
        img = compose_og(grid, date, a.solved, a.blur, a.headline)
    else:
        img = compose_square(grid, date, a.solved, a.blur)
    save_png(img, a.out, a.colors)
    print(f"{a.out}  ({grid['id']})")


if __name__ == "__main__":
    main()
