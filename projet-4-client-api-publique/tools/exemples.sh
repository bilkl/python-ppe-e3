#!/usr/bin/env bash
# Enregistre dans exemples/sortie-exemples.txt la sortie de plusieurs requêtes réelles
# (livrable : exemple de sortie pour au moins 3 requêtes différentes).
# Usage : tools/exemples.sh   (accès Internet requis ; les taux sont ceux du jour)
set -euo pipefail
cd "$(dirname "$0")/.."
SORTIE="exemples/sortie-exemples.txt"
mkdir -p exemples
{
  echo "Sorties réelles de l'API Frankfurter, enregistrées le $(date '+%Y-%m-%d à %H:%M')."
  for commande in \
    "convertir 250 CHF EUR" \
    "taux CHF EUR USD GBP JPY" \
    "historique CHF EUR --du 2026-10-01 --au 2026-10-28" \
    "devises --filtre franc"; do
    echo
    echo "\$ python3 -m client_taux $commande"
    # shellcheck disable=SC2086
    python3 -m client_taux $commande
  done
} > "$SORTIE"
echo "Écrit : $SORTIE"
