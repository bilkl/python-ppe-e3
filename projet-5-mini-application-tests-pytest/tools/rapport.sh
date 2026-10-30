#!/usr/bin/env bash
# Produit le rapport d'exécution des tests (export) dans rapport/ :
#   resultats-pytest.txt  sortie détaillée de pytest (un test par ligne)
#   junit.xml             résultats au format JUnit (lisible par la plupart des outils d'intégration continue)
#   couverture.txt        couverture des lignes et des branches
#   mutation.txt          résultat du test de mutation
# Usage : tools/rapport.sh   (pytest et pytest-cov installés : pip install -r requirements.txt)
set -uo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
mkdir -p rapport
{ echo "Rapport généré le $(date '+%Y-%m-%d à %H:%M') — $($PY --version) — $($PY -m pytest --version | head -1)"; echo; } > rapport/resultats-pytest.txt
$PY -m pytest -v -p no:cacheprovider --junitxml=rapport/junit.xml >> rapport/resultats-pytest.txt 2>&1
$PY -m pytest -q -p no:cacheprovider --cov --cov-report=term-missing > rapport/couverture.txt 2>&1
$PY tools/mutation.py > rapport/mutation.txt 2>&1
rm -f .coverage
sed -i "s|$PWD/||g; s|$PWD|.|g" rapport/*.txt
tail -n 3 rapport/resultats-pytest.txt
