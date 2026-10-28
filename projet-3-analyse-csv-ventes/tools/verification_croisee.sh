#!/usr/bin/env bash
# Recalcule les indicateurs avec awk, sans passer par le code Python, pour
# comparer avec la sortie du programme.
# Usage : tools/verification_croisee.sh data/ventes_t3_2026.csv
set -euo pipefail
FICHIER="${1:-data/ventes_t3_2026.csv}"
echo "== awk (calcul indépendant) =="
awk -F';' 'NR>1 { ca+=$6*$7; q+=$6; n++; qp[$3]+=$6; cm[substr($1,1,7)]+=$6*$7 }
END {
  printf "Chiffre d affaires : %.2f\nNombre de ventes   : %d\nQuantité totale    : %d\nMoyenne par vente  : %.2f\n", ca, n, q, ca/n
  for (p in qp) printf "%d\t%s\n", qp[p], p | "sort -rn | head -1"
  close("sort -rn | head -1")
  for (m in cm) printf "CA %s : %.2f\n", m, cm[m] | "sort"
}' "$FICHIER"
echo
echo "== programme Python =="
python3 -m analyse_ventes "$FICHIER" | grep -E "Chiffre|Nombre de ventes|Quantité totale|Moyenne|plus vendu|^2026-0"
