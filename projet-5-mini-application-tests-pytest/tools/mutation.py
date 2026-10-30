#!/usr/bin/env python3
"""Test de mutation « artisanal » : la couverture dit quelles lignes sont EXÉCUTÉES, pas si les
tests VÉRIFIENT quelque chose. Ici on introduit volontairement un bug dans une copie du code
(un `>` devient `>=`, un signe change...) et on vérifie que la suite de tests ÉCHOUE.
Un bug qui ne fait échouer aucun test est dit « survivant » : il révèle un test manquant.

Usage (depuis la racine du projet, avec pytest installé) :
    python3 tools/mutation.py
Code de sortie : 0 si tous les bugs sont détectés, 1 sinon.
"""

import os
import shutil
import subprocess
import sys
import tempfile

RACINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# (fichier, texte d'origine, texte modifié, n° de l'occurrence modifiée, description du bug)
MUTATIONS = [
    ("compte.py", "if montant > self.disponible:", "if montant >= self.disponible:", 1, "retrait : limite exclusive au lieu d'inclusive"),
    ("compte.py", "if montant > self.disponible:", "if montant >= self.disponible:", 2, "virement : limite exclusive au lieu d'inclusive"),
    ("compte.py", "return self._solde + self._decouvert", "return self._solde", 1, "le découvert n'est plus compté dans le disponible"),
    ("compte.py", 'self._enregistrer("depot", montant, montant,', 'self._enregistrer("depot", montant, -montant,', 1, "un dépôt retire de l'argent"),
    ("compte.py", 'self._enregistrer("retrait", montant, -montant,', 'self._enregistrer("retrait", montant, montant,', 1, "un retrait ajoute de l'argent"),
    ("compte.py", "if self._solde != 0:", "if self._solde < 0:", 1, "clôture autorisée avec un solde positif"),
    ("compte.py", "if self._ferme:", "if False:", 1, "un compte clôturé accepte des opérations"),
    ("compte.py", "len(titulaire) > TITULAIRE_MAX", "len(titulaire) >= TITULAIRE_MAX", 1, "titulaire : limite de longueur décalée"),
    ("compte.py", "from decimal import ROUND_HALF_UP, Decimal", "from decimal import ROUND_DOWN as ROUND_HALF_UP, Decimal", 1, "intérêts arrondis vers le bas"),
    ("compte.py", "self._taux / 12", "self._taux / 10", 1, "intérêts calculés sur 10 mois au lieu de 12"),
    ("compte.py", "if interets <= 0:", "if interets < 0:", 1, "une opération d'intérêts à zéro est créée"),
    ("compte.py", "0 <= taux <= self.TAUX_MAX", "0 <= taux < self.TAUX_MAX", 1, "taux maximum exclu"),
    ("compte.py", "return tuple(self._historique)", "return self._historique", 1, "l'historique peut être modifié de l'extérieur"),
    ("montants.py", "not isinstance(valeur, (int, Decimal)):", "not isinstance(valeur, (int, Decimal, float)):", 1, "les flottants sont acceptés"),
    ("montants.py", "elif isinstance(valeur, bool) or", "elif", 1, "les booléens sont acceptés (True = 1 centime)"),
    ("montants.py", "if montant > MONTANT_MAX:", "if montant >= MONTANT_MAX:", 1, "montant maximum exclu"),
    ("montants.py", "if montant != montant.quantize(CENTIME):", "if False:", 1, "plus de 2 décimales acceptées"),
    ("montants.py", "(montant == 0 and not zero_autorise)", "(montant == 0 and zero_autorise)", 1, "règle du zéro inversée"),
    ("montants.py", "if not montant.is_finite():", "if False:", 1, "NaN et infini acceptés"),
    ("banque.py", "if numero_source == numero_destination:", "if False:", 1, "virement d'un compte vers lui-même autorisé"),
    ("banque.py", "compte._verifier_ouvert()", "pass", 1, "virement vers/depuis un compte clôturé non contrôlé"),
    ("banque.py", "self._compteur += 1", "self._compteur += 0", 1, "numéros de compte en double"),
    ("releve.py", '{"retrait": "-", "virement_emis": "-"}', '{"retrait": "-"}', 1, "virement émis affiché comme un gain"),
]


def remplacer_occurrence(texte, ancien, nouveau, n):
    position = -1
    for _ in range(n):
        position = texte.find(ancien, position + 1)
        if position < 0:
            return None
    return texte[:position] + nouveau + texte[position + len(ancien):]


def suite_echoue(dossier):
    resultat = subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", "-p", "no:cov"],
        cwd=dossier, capture_output=True, text=True,
    )
    return resultat.returncode != 0


def main():
    with tempfile.TemporaryDirectory() as tmp:
        copie = os.path.join(tmp, "projet")
        shutil.copytree(RACINE, copie, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".git", ".pytest_cache", "htmlcov", ".coverage"))
        if suite_echoue(copie):
            print("La suite de tests échoue déjà sans modification : mutation impossible.")
            return 1
        survivants = []
        for numero, (fichier, ancien, nouveau, occurrence, bug) in enumerate(MUTATIONS, start=1):
            chemin = os.path.join(copie, "banque", fichier)
            with open(chemin, encoding="utf-8") as f:
                original = f.read()
            modifie = remplacer_occurrence(original, ancien, nouveau, occurrence)
            if modifie is None:
                print(f"{numero:>2}. ERREUR  texte introuvable : {ancien!r} (occurrence {occurrence})")
                return 1
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(modifie)
            detecte = suite_echoue(copie)
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(original)
            print(f"{numero:>2}. {'DÉTECTÉ ' if detecte else 'SURVIVANT'}  {fichier:<11} {bug}")
            if not detecte:
                survivants.append(bug)
    print(f"\n{len(MUTATIONS) - len(survivants)}/{len(MUTATIONS)} bugs introduits ont été détectés par les tests.")
    return 1 if survivants else 0


if __name__ == "__main__":
    sys.exit(main())
