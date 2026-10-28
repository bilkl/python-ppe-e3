#!/usr/bin/env bash
# Génère les captures d'écran du projet dans un écran virtuel isolé (Xvfb).
# Le programme tourne réellement dans un terminal xterm ; les touches sont
# envoyées par xdotool, la capture est faite par scrot.
# Usage : tools/capture.sh   (depuis n'importe où)
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$RACINE/screenshots"
D=":99"
mkdir -p "$OUT"

Xvfb "$D" -screen 0 1010x960x24 >/dev/null 2>&1 &
XVFB_PID=$!
trap 'kill $XVFB_PID 2>/dev/null || true' EXIT
sleep 1
export DISPLAY="$D"

XTERM_OPTS=(-geometry 100x46+0+0 -fa "DejaVu Sans Mono" -fs 12
            -bg "#1e1e2e" -fg "#cdd6f4" -b 12 +sb)

# lancer <commande> : ouvre xterm, renvoie son PID et donne le focus.
lancer() {
  xterm "${XTERM_OPTS[@]}" -e bash -c "cd '$RACINE'; $1" &
  XT_PID=$!
  sleep 1.2
  xdotool mousemove 400 300
  WID=$(xdotool search --pid "$XT_PID" | tail -1)
  xdotool windowfocus "$WID" 2>/dev/null || true
}

# frappe <texte> : tape le texte puis Entrée, avec une pause lisible.
frappe() {
  if [ -n "$1" ]; then xdotool type --delay 60 -- "$1"; fi
  xdotool key Return
  sleep 0.6
}

fin() {
  kill "$XT_PID" 2>/dev/null || true
  wait "$XT_PID" 2>/dev/null || true
}

# 1. Menu principal
lancer "python3 calculatrice.py"
sleep 0.5
scrot -o "$OUT/01-menu-principal.png"
frappe "0"; sleep 0.5; fin

# 2. Calculs : addition, puis division par zéro
lancer "python3 calculatrice.py"
frappe "1"; frappe "12,5"; frappe "7.5"
frappe "4"; frappe "10"; frappe "0"
sleep 0.4
scrot -o "$OUT/02-calculs-division-par-zero.png"
frappe "0"; sleep 0.5; fin

# 3. Conversions : température, longueur, poids
lancer "python3 calculatrice.py"
frappe "7"; frappe "100"; frappe "C"; frappe "F"
frappe "8"; frappe "5"; frappe "km"; frappe "mi"
frappe "9"; frappe "2,5"; frappe "kg"; frappe "lb"
sleep 0.4
scrot -o "$OUT/03-conversions.png"
frappe "0"; sleep 0.5; fin

# 4. Saisies invalides (menu, nombres) puis (unités, zéro absolu)
lancer "python3 calculatrice.py"
frappe "zzz"
frappe "3"; frappe "abc"; frappe ""; frappe "4"; frappe "6"
sleep 0.4
scrot -o "$OUT/04-saisies-invalides-nombres.png"
frappe "8"; frappe "3"; frappe "xx"; frappe "m"; frappe "cm"
frappe "7"; frappe "-300"; frappe "C"; frappe "K"
sleep 0.4
scrot -o "$OUT/05-saisies-invalides-unites.png"
frappe "0"; sleep 0.5; fin

# 6. Tests automatisés
lancer "python3 -m unittest discover -v -s tests -t . 2>&1 | tail -n 30; sleep 30"
sleep 2.5
scrot -o "$OUT/06-tests-automatises.png"
fin

echo "Captures générées dans $OUT"
