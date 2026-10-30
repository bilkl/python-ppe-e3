#!/usr/bin/env bash
# Génère les captures d'écran dans un écran virtuel isolé (Xvfb) : les commandes sont
# réellement tapées (xdotool) dans un xterm, contre la VRAIE API (accès Internet requis),
# puis capturées (scrot). Les taux affichés sont ceux du jour de l'exécution.
# Usage : tools/capture.sh
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$RACINE/screenshots"
D=":96"
mkdir -p "$OUT"

Xvfb "$D" -screen 0 1010x900x24 >/dev/null 2>&1 &
XVFB_PID=$!
trap 'kill $XVFB_PID 2>/dev/null || true' EXIT
sleep 1
export DISPLAY="$D"

XTERM_OPTS=(-geometry 100x42+0+0 -fa "DejaVu Sans Mono" -fs 12
            -bg "#1e1e2e" -fg "#cdd6f4" -b 12 +sb)

lancer() {
  xterm "${XTERM_OPTS[@]}" -e bash -c "cd '$RACINE'; export PS1='\$ '; exec bash --norc --noprofile" &
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
  sleep "${2:-3.5}"   # laisse le temps à la requête réseau
}

fin() {
  kill "$XT_PID" 2>/dev/null || true
  wait "$XT_PID" 2>/dev/null || true
}

# 1. Aide, puis conversion (requête n°1)
lancer
cmd "python3 -m client_taux --help" 1
cmd "python3 -m client_taux convertir 250 CHF EUR"
cmd "python3 -m client_taux convertir 1500,50 CHF USD"
scrot -o "$OUT/01-aide-et-conversions.png"
fin

# 2. Taux vers plusieurs devises, au cours d'un week-end (requête n°2)
lancer
cmd "python3 -m client_taux taux CHF EUR USD GBP JPY"
cmd "python3 -m client_taux taux CHF EUR USD --date 2026-10-03"
scrot -o "$OUT/02-taux-et-week-end.png"
fin

# 3. Historique sur un mois (requête n°3) et liste filtrée des devises
lancer
cmd "python3 -m client_taux historique CHF EUR --du 2026-10-01 --au 2026-10-28" 3
cmd "python3 -m client_taux devises --filtre dollar"
scrot -o "$OUT/03-historique-et-devises.png"
fin

# 4. Gestion des erreurs
lancer
cmd "python3 -m client_taux convertir 100 CHF ZZZ"
cmd "python3 -m client_taux convertir abc CHF EUR"
cmd "python3 -m client_taux taux CHF --date 29/10/2026"
cmd "python3 -m client_taux historique CHF EUR --du 2026-10-28 --au 2026-10-01"
cmd "python3 -m client_taux taux CHF --date 1990-01-01"
cmd "time python3 -m client_taux --url http://127.0.0.1:9 --tentatives 3 taux CHF" 6
scrot -o "$OUT/04-gestion-des-erreurs.png"
fin

# 5. Tests automatisés
xterm "${XTERM_OPTS[@]}" -e bash -c "cd '$RACINE'; python3 -m unittest -v 2>&1 | tail -n 34; sleep 30" &
XT_PID=$!
sleep 5
scrot -o "$OUT/05-tests-automatises.png"
fin

echo "Captures générées dans $OUT"
