#!/usr/bin/env python3
"""
generate_index.py — Génère un index.html listant tous les fichiers HTML du dossier.
Les fichiers sont listés par leur nom (ordre alphabétique), pas par leur contenu.
Usage : python generate_index.py
        python generate_index.py --dir site/ --css style.css
"""

import argparse
from pathlib import Path


def generate_index(search_dir: str, css_file: str, lang: str = "fr"):
    directory = Path(search_dir)

    # Collecte tous les .html sauf index.html, triés alphabétiquement par nom
    html_files = sorted([
        f for f in directory.glob("*.html")
        if f.name.lower() != "index.html"
    ])

    if not html_files:
        print(f"[index] Aucun fichier HTML trouvé dans '{directory}'.")
        return

    # Construction de la liste : nom affiché = stem du fichier, tirets/underscores → espaces
    items = []
    for f in html_files:
        display_name = f.stem.replace("-", " ").replace("_", " ")
        items.append(f'    <li><a href="{f.name}">{display_name}</a></li>')

    items_html = "\n".join(items)

    page = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Index</title>
  <link rel="stylesheet" href="{css_file}">
</head>
<body>

  <div class="topbar">
    <div class="topbar-title">Index des documents</div>
  </div>
  <div class="topbar-spacer"></div>

  <div class="page-content">
    <ul class="index-liste">
{items_html}
    </ul>
  </div>

</body>
</html>
"""

    output = directory / "index.html"
    output.write_text(page, encoding="utf-8")
    print(f"[index] → {output} ({len(html_files)} document(s) listé(s))")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Génère un index.html listant tous les fichiers HTML du dossier."
    )
    parser.add_argument(
        "--dir", default=".",
        help="Dossier contenant les fichiers HTML (défaut : dossier courant)"
    )
    parser.add_argument(
        "--css", default="style.css",
        help="Chemin vers le CSS (défaut : style.css)"
    )
    parser.add_argument(
        "--lang", default="fr",
        help="Langue de la page (défaut : fr)"
    )
    args = parser.parse_args()
    generate_index(args.dir, args.css, args.lang)
