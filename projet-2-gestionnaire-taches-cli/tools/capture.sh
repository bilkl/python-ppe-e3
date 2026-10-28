#!/usr/bin/env bash
# Génère les captures d'écran du projet dans un écran virtuel isolé (Xvfb).
# Les commandes sont réellement tapées (xdotool) dans un terminal xterm, puis
# capturées (scrot). La preuve de persistance utilise DEUX terminaux distincts :
# le premier est fermé, le second est ouvert ensuite.
# Usage : tools/capture.sh
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$RACINE/screenshots"
DEMO="exemple/taches-demo.json"
D=":98"
mkdir -p "$OUT" "$RACINE/exemple"
rm -f "$RACINE/$DEMO" "$RACINE/exemple/corrompu-demo.json"

Xvfb "$D" -screen 0 1010x900x24 >/dev/null 2>&1 &
XVFB_PID=$!
trap 'kill $XVFB_PID 2>/dev/null || true; rm -f "$RACINE/exemple/corrompu-demo.json"' EXIT
sleep 1
export DISPLAY="$D"

XTERM_OPTS=(-geometry 100x43+0+0 -fa "DejaVu Sans Mono" -fs 12
            -bg "#1e1e2e" -fg "#cdd6f4" -b 12 +sb)

# Terminal avec une invite courte ; TACHES_FICHIER pointe sur le fichier de démonstration.
lancer() {
  xterm "${XTERM_OPTS[@]}" -e bash -c \
    "cd '$RACINE'; export TACHES_FICHIER='$DEMO' PS1='\$ '; exec bash --norc --noprofile" &
  XT_PID=$!
  sleep 1.2
  xdotool mousemove 400 300
  WID=$(xdotool search --pid "$XT_PID" | tail -1)
  xdotool windowfocus "$WID" 2>/dev/null || true
}

# cmd <texte> : tape la commande, valide, attend l'exécution.
cmd() {
  xdotool type --delay 45 -- "$1"
  xdotool key Return
  sleep 0.9
}

fin() {
  kill "$XT_PID" 2>/dev/null || true
  wait "$XT_PID" 2>/dev/null || true
}

# 1. Aide et ajout de tâches
lancer
cmd "clear"
cmd "python3 -m gestionnaire --help"
cmd "python3 -m gestionnaire ajouter 'Réviser le chapitre 3' -p haute"
cmd "python3 -m gestionnaire ajouter 'Acheter du café'"
cmd "python3 -m gestionnaire ajouter 'Ranger le bureau' -p basse"
cmd "python3 -m gestionnaire ajouter 'Envoyer le rapport' -p haute"
cmd "python3 -m gestionnaire lister"
scrot -o "$OUT/01-ajout-et-liste.png"
fin

# 2. Terminer, supprimer, filtrer, erreurs
lancer
cmd "clear"
cmd "python3 -m gestionnaire terminer 1"
cmd "python3 -m gestionnaire supprimer 3"
cmd "python3 -m gestionnaire lister --statut a_faire"
cmd "python3 -m gestionnaire terminer 1"
cmd "python3 -m gestionnaire terminer 99"
cmd "python3 -m gestionnaire ajouter '   '"
cmd "python3 -m gestionnaire ajouter 'x' -p urgente"
scrot -o "$OUT/02-terminer-supprimer-erreurs.png"
fin

# 3. Persistance, AVANT : état de la liste et contenu du fichier
lancer
cmd "clear"
cmd "python3 -m gestionnaire lister"
cmd "ls -l $DEMO"
cmd "cat $DEMO"
scrot -o "$OUT/03-persistance-avant.png"
fin   # le terminal (donc le programme et sa mémoire) est fermé

# 3bis. Persistance, APRÈS : nouveau terminal, nouvelle exécution
lancer
cmd "clear"
cmd "python3 -m gestionnaire lister"
cmd "python3 -m gestionnaire ajouter 'Tâche ajoutée après redémarrage'"
cmd "python3 -m gestionnaire lister"
scrot -o "$OUT/04-persistance-apres-redemarrage.png"
fin

# 4. Fichier corrompu : refusé, jamais écrasé
lancer
cmd "clear"
cmd "echo '{casse' > exemple/corrompu-demo.json"
cmd "python3 -m gestionnaire -f exemple/corrompu-demo.json ajouter 'test'; echo \"code de sortie : \$?\""
cmd "cat exemple/corrompu-demo.json"
scrot -o "$OUT/05-fichier-corrompu.png"
fin

# 5. Tests automatisés
xterm "${XTERM_OPTS[@]}" -e bash -c "cd '$RACINE'; python3 -m unittest -v 2>&1 | tail -n 30; sleep 30" &
XT_PID=$!
sleep 3
scrot -o "$OUT/06-tests-automatises.png"
fin

echo "Captures générées dans $OUT"
