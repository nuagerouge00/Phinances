#!/usr/bin/env python3
"""
convert.py — Convertisseur Obsidian Markdown → HTML statique
Usage : python convert.py mon-document.md
        python convert.py *.md
        python convert.py *.md --config config.json --output site/

Dépendances :
  pip install markdown --break-system-packages
"""

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

# ─── Dépendance : python-markdown ───────────────────────────────────────────
try:
    import markdown
except ImportError:
    print("Erreur : la bibliothèque 'markdown' n'est pas installée.")
    print("Installez-la avec : pip install markdown --break-system-packages")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    # Niveaux de titres convertis en <details> dépliables
    # Exemple : [2, 4] convertit H2 et H4, laisse H1 H3 H5 H6 normaux
    "collapsible_levels": [2, 3],

    # Chemin vers la feuille de style CSS (relatif au fichier HTML produit)
    "css_file": "style.css",

    # Niveaux dont les <details> sont ouverts par défaut
    # Exemple : [2] ouvre tous les H2 au chargement
    "open_by_default": [],

    # Attribut lang du <html>
    "lang": "fr"
}


def load_config(config_path: str) -> dict:
    """Charge config.json et fusionne avec les valeurs par défaut."""
    config = DEFAULT_CONFIG.copy()
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        config.update(user_config)
        print(f"[config] Chargé depuis : {config_path}")
    else:
        print(f"[config] '{config_path}' introuvable — valeurs par défaut utilisées.")
    return config


# ════════════════════════════════════════════════════════════════════════════
# FRONTMATTER YAML — strip silencieux, contenu ignoré
# ════════════════════════════════════════════════════════════════════════════

def strip_frontmatter(content: str) -> str:
    """
    Supprime le bloc frontmatter YAML s'il est présent (entre --- au début).
    Le contenu du frontmatter est ignoré : le nom du fichier fait office de titre.
    """
    if not content.startswith("---"):
        return content
    end = content.find("\n---", 3)
    if end == -1:
        return content
    return content[end + 4:].lstrip("\n")


# ════════════════════════════════════════════════════════════════════════════
# PARSING DU DOCUMENT EN NŒUDS
# ════════════════════════════════════════════════════════════════════════════

def parse_sections(content: str) -> list:
    """
    Découpe le document en nœuds alternant titres et blocs de contenu :
      {"type": "heading", "level": int, "text": str}
      {"type": "content", "text": str}
    """
    nodes = []
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    last_pos = 0
    for match in heading_pattern.finditer(content):
        before = content[last_pos:match.start()]
        if before.strip():
            nodes.append({"type": "content", "text": before})
        level = len(match.group(1))
        text = match.group(2).strip()
        nodes.append({"type": "heading", "level": level, "text": text})
        last_pos = match.end()

    remainder = content[last_pos:]
    if remainder.strip():
        nodes.append({"type": "content", "text": remainder})

    return nodes


# ════════════════════════════════════════════════════════════════════════════
# CONVERSION MARKDOWN → HTML
# ════════════════════════════════════════════════════════════════════════════

def md_to_html(text: str) -> str:
    """Convertit un bloc Markdown en HTML via python-markdown."""
    if not text.strip():
        return ""
    extensions = ["fenced_code", "tables", "nl2br"]
    try:
        md = markdown.Markdown(extensions=extensions + ["attr_list"], output_format="html")
    except Exception:
        md = markdown.Markdown(extensions=extensions, output_format="html")
    return md.convert(text)


# ════════════════════════════════════════════════════════════════════════════
# CONSTRUCTION HTML AVEC DETAILS IMBRIQUÉS
# ════════════════════════════════════════════════════════════════════════════

class HtmlBuilder:
    """
    Construit le corps HTML du document.
    Gère l'imbrication des <details> via une pile (stack).
    """

    def __init__(self, collapsible_levels: list, open_by_default: list):
        self.collapsible_levels = collapsible_levels
        self.open_by_default = open_by_default
        self.lines = []
        self.stack = []

    def _close_until(self, level: int):
        while self.stack and self.stack[-1] >= level:
            self.lines.append("</details>")
            self.stack.pop()

    def _pad(self, extra: int = 0) -> str:
        return "  " * (len(self.stack) + extra)

    def add_heading(self, level: int, text: str):
        self._close_until(level)
        pad = self._pad()
        if level in self.collapsible_levels:
            open_attr = " open" if level in self.open_by_default else ""
            self.lines.append(f'{pad}<details class="niveau{level}"{open_attr}>')
            self.lines.append(f'{pad}  <summary class="summary-h{level}">{text}</summary>')
            self.stack.append(level)
        else:
            self.lines.append(f'{pad}<h{level}>{text}</h{level}>')

    def add_content(self, text: str):
        html = md_to_html(text)
        if not html:
            return
        pad = self._pad(extra=1)
        for line in html.splitlines():
            self.lines.append(pad + line if line.strip() else "")

    def close_all(self):
        while self.stack:
            self.lines.append("</details>")
            self.stack.pop()

    def get_html(self) -> str:
        return "\n".join(self.lines)


# ════════════════════════════════════════════════════════════════════════════
# TEMPLATE HTML COMPLET
# ════════════════════════════════════════════════════════════════════════════

def build_page(page_title: str, body_html: str, css_file: str, lang: str) -> str:
    """
    Assemble la page HTML complète.
    - Barre sticky en haut : boutons + titre de page
    - Le titre de page reste visible au scroll
    - Le H1 du document s'affiche dans le corps (sous la barre)
    - Fond de page et couleur du titre définis dans le CSS
    """
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <link rel="stylesheet" href="{css_file}">
</head>
<body>

  <!-- Barre fixe en haut : toujours visible au scroll -->
  <div class="topbar">
    <div class="topbar-buttons">
      <a href="index.html" class="btn-toggle">← Index</a>
      <button class="btn-toggle" id="btn-toggle-all">⊞ Replier / Déplier tout</button>
    </div>
    <div class="topbar-title">{page_title}</div>
  </div>

  <!-- Espace pour compenser la hauteur de la barre fixe -->
  <div class="topbar-spacer"></div>

  <!-- Corps du document -->
  <div class="page-content">
{body_html}
  </div>

  <script>
    (function () {{
      var btn = document.getElementById('btn-toggle-all');
      btn.addEventListener('click', function () {{
        var all = Array.from(document.querySelectorAll('details'));
        var anyOpen = all.some(function (d) {{ return d.open; }});
        all.forEach(function (d) {{ d.open = !anyOpen; }});
      }});
    }})();
  </script>

</body>
</html>
"""


# ════════════════════════════════════════════════════════════════════════════
# CONVERSION D'UN FICHIER
# ════════════════════════════════════════════════════════════════════════════

def convert(input_path: str, config: dict, output_dir: str = None) -> Path:
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[erreur] Fichier introuvable : '{input_path}'")
        return None

    # Lecture
    content = input_file.read_text(encoding="utf-8")
    print(f"[lecture] {input_file.name} ({len(content)} caractères)")

    # Suppression silencieuse du frontmatter
    body = strip_frontmatter(content)

    # Titre de la page = nom du fichier (sans extension), tirets/underscores → espaces
    page_title = input_file.stem.replace("-", " ").replace("_", " ")
    print(f"[titre]   {page_title}")

    # Parsing
    nodes = parse_sections(body)
    print(f"[parsing] {len(nodes)} nœuds — niveaux repliables : {config['collapsible_levels']}")

    # Construction HTML
    builder = HtmlBuilder(
        collapsible_levels=config["collapsible_levels"],
        open_by_default=config.get("open_by_default", [])
    )
    for node in nodes:
        if node["type"] == "heading":
            builder.add_heading(node["level"], node["text"])
        else:
            builder.add_content(node["text"])
    builder.close_all()

    # Assemblage
    page_html = build_page(
        page_title=page_title,
        body_html=builder.get_html(),
        css_file=config["css_file"],
        lang=config["lang"]
    )

    # Écriture
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = input_file.parent

    output_file = out_dir / (input_file.stem + ".html")
    output_file.write_text(page_html, encoding="utf-8")
    print(f"[sortie]  → {output_file}")
    return output_file


# ════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convertit un ou plusieurs fichiers Markdown Obsidian en HTML statique.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python convert.py cours-macro.md
  python convert.py *.md
  python convert.py *.md --output site/
        """
    )
    # nargs="+" accepte un ou plusieurs fichiers (gère *.md déjà expansé par le shell)
    parser.add_argument("inputs", nargs="+", help="Fichier(s) .md source(s)")
    parser.add_argument(
        "--config", default="config.json",
        help="Fichier de configuration JSON (défaut : config.json)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Dossier de sortie (défaut : même dossier que chaque fichier source)"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    converted = 0
    for pattern in args.inputs:
        # Expansion manuelle au cas où le shell ne l'aurait pas fait (Windows, quotes)
        matches = glob.glob(pattern)
        if not matches:
            matches = [pattern]  # on tente quand même, convert() gérera l'erreur
        for filepath in sorted(matches):
            if Path(filepath).suffix.lower() == ".md":
                result = convert(filepath, cfg, args.output)
                if result:
                    converted += 1
            else:
                print(f"[ignoré]  {filepath} (pas un fichier .md)")

    print(f"\n✓ {converted} fichier(s) converti(s).")
