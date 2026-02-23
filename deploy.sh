#!/bin/bash
# deploy.sh

SOURCE=~/Nextcloud/Obsidian_sur_nextcloud/Phinances
DEST=~/github/Phinances

# Copie uniquement les .md qui commencent par un chiffre
# Cela permet de ne pas copier les brouillons et les notes
cp "$SOURCE"/[0-9]*.md "$DEST"/

cd "$DEST"
python3 convert.py *.md
python3 generate_index.py
git add .
git commit -m "mise à jour $(date '+%Y-%m-%d %H:%M')"
git push

echo "✓ Publié sur https://nuagerouge00.github.io/Phinances/"