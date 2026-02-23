#!/bin/bash
# deploy.sh — Conversion et publication vers GitHub Pages
# La sortie complète est enregistrée dans deploy_log.txt (écrasé à chaque lancement)

SOURCE=~/Nextcloud/Obsidian_sur_Nextcloud/Phinances
DEST=~/github/Phinances
LOG="$DEST/deploy_log.txt"

# Redirige stdout ET stderr vers le fichier log, en écrasant
exec > "$LOG" 2>&1

echo "=== Déploiement $(date '+%Y-%m-%d %H:%M:%S') ==="
echo ""

# Copie uniquement les .md qui commencent par un chiffre
echo "-- Copie des fichiers source --"
cp "$SOURCE"/[0-9]*.md "$DEST"/

cd "$DEST"

echo "-- Conversion Markdown → HTML --"
python3 convert.py *.md

echo ""
echo "-- Génération de l'index --"
python3 generate_index.py

echo ""
echo "-- Publication git --"
git add .
git commit -m "mise à jour $(date '+%Y-%m-%d %H:%M')"
git push

echo ""
echo "✓ Publié sur https://nuagerouge00.github.io/Phinances/"
