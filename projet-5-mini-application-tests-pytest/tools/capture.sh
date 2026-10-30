#!/usr/bin/env bash
# Génère les captures d'écran dans un écran virtuel isolé (Xvfb) : les commandes sont
# réellement tapées (xdotool) dans un xterm, puis capturées (scrot).
# Usage : tools/capture.sh   (pytest et pytest-cov installés dans .venv)
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$RACINE/screenshots"
D=":95"
mkdir -p "$OUT"

Xvfb "$D" -screen 0 1010x1100x24 >/dev/null 2>&1 &
XVFB_PID=$!
COPIE="$(mktemp -d)"
trap 'kill $XVFB_PID 2>/dev/null || true; rm -rf "$COPIE"' EXIT
sleep 1
export DISPLAY="$D"

XTERM_OPTS=(-geometry 100x53+0+0 -fa "DejaVu Sans Mono" -fs 12
            -bg "#1e1e2e" -fg "#cdd6f4" -b 12 +sb)

lancer() {
  xterm "${XTERM_OPTS[@]}" -e bash -c \
    "cd '${1:-$RACINE}'; export PS1='\$ ' PATH='$RACINE/.venv/bin':\$PATH; exec bash --norc --noprofile" &
  XT_PID=$!
  sleep 1.2
  xdotool mousemove 400 300
  WID=$(xdotool search --pid "$XT_PID" | tail -1)
  xdotool windowfocus "$WID" 2>/dev/null || true
  cmd "clear" 0.5
}

cmd() {
  xdotool type --delay 40 -- "$1"
  xdotool key Return
  sleep "${2:-2.5}"
}

fin() {
  kill "$XT_PID" 2>/dev/null || true
  wait "$XT_PID" 2>/dev/null || true
}

# 1. Démonstration de l'application
lancer
cmd "python3 -m banque" 1.5
scrot -o "$OUT/01-demonstration.png"
fin

# 2. Tous les tests, un par ligne (fin de la liste)
lancer
cmd "pytest -v 2>&1 | tail -n 49" 4
scrot -o "$OUT/02-pytest-verbose.png"
fin

# 3. Couverture des lignes et des branches
lancer
cmd "pytest -q --cov --cov-report=term-missing" 4
scrot -o "$OUT/03-couverture.png"
fin

# 4. Un bug introduit volontairement dans une COPIE du code : un test doit échouer
cp -r "$RACINE/banque" "$RACINE/tests" "$RACINE/pytest.ini" "$COPIE/"
lancer "$COPIE"
cmd "sed -i '0,/if montant > self.disponible:/s//if montant >= self.disponible:/' banque/compte.py" 0.5
cmd "grep -n 'montant >= self.disponible' banque/compte.py" 0.5
cmd "pytest -q -p no:cacheprovider 2>&1 | tail -n 40" 4
scrot -o "$OUT/04-bug-volontaire-detecte.png"
fin

# 5. Test de mutation : 23 bugs, tous doivent être détectés
lancer
cmd "python3 tools/mutation.py" 45
scrot -o "$OUT/05-test-de-mutation.png"
fin

echo "Captures générées dans $OUT"
