#!/usr/bin/env bash
# Génère les captures d'écran dans un écran virtuel isolé (Xvfb) : les commandes
# sont réellement tapées (xdotool) dans un xterm puis capturées (scrot).
# Régénère aussi resultats/ (synthèse du jeu de données complet).
# Usage : tools/capture.sh
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$RACINE/screenshots"
D=":97"
mkdir -p "$OUT"
rm -rf "$RACINE/resultats"

Xvfb "$D" -screen 0 1010x1180x24 >/dev/null 2>&1 &
XVFB_PID=$!
trap 'kill $XVFB_PID 2>/dev/null || true' EXIT
sleep 1
export DISPLAY="$D"

XTERM_OPTS=(-geometry 100x57+0+0 -fa "DejaVu Sans Mono" -fs 12
            -bg "#1e1e2e" -fg "#cdd6f4" -b 12 +sb)

lancer() {
  xterm "${XTERM_OPTS[@]}" -e bash -c \
    "cd '$RACINE'; export PS1='\$ '; exec bash --norc --noprofile" &
  XT_PID=$!
  sleep 1.2
  xdotool mousemove 400 300
  WID=$(xdotool search --pid "$XT_PID" | tail -1)
  xdotool windowfocus "$WID" 2>/dev/null || true
  cmd "clear"
}

cmd() {
  xdotool type --delay 40 -- "$1"
  xdotool key Return
  sleep 1.0
}

fin() {
  kill "$XT_PID" 2>/dev/null || true
  wait "$XT_PID" 2>/dev/null || true
}

# 1. Aperçu du CSV puis analyse complète
lancer
cmd "head -4 data/ventes_t3_2026.csv; wc -l data/ventes_t3_2026.csv"
cmd "python3 -m analyse_ventes data/ventes_t3_2026.csv --top 5"
scrot -o "$OUT/01-analyse-complete.png"
fin

# 2. Filtres, tri et top
lancer
cmd "python3 -m analyse_ventes data/ventes_t3_2026.csv --mois 2026-08 --region Vaud --tri quantite --top 5"
scrot -o "$OUT/02-filtres-tri-top.png"
fin

# 3. Fichier avec lignes invalides
lancer
cmd "cat data/ventes_avec_erreurs.csv"
cmd "python3 -m analyse_ventes data/ventes_avec_erreurs.csv --top 3"
scrot -o "$OUT/03-lignes-rejetees.png"
fin

# 4. Export de la synthèse
lancer
cmd "python3 -m analyse_ventes data/ventes_t3_2026.csv --sortie resultats | tail -n 4"
cmd "ls -l resultats"
cmd "head -6 resultats/synthese-produits.csv"
scrot -o "$OUT/04-export-synthese.png"
fin

# 5. Vérification croisée avec awk
lancer
cmd "tools/verification_croisee.sh"
scrot -o "$OUT/05-verification-croisee-awk.png"
fin

# 6. Tests automatisés
xterm "${XTERM_OPTS[@]}" -e bash -c "cd '$RACINE'; python3 -m unittest -v 2>&1 | tail -n 36; sleep 30" &
XT_PID=$!
sleep 3
scrot -o "$OUT/06-tests-automatises.png"
fin

echo "Captures générées dans $OUT"
