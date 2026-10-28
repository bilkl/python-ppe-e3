"""Persistance des tâches dans un fichier JSON.

Format (version 1) :  {"version": 1, "taches": [ {tâche}, ... ]}
Voir FORMAT-FICHIER.md pour la description complète.
"""

import json
import os
import tempfile

from .modele import valider_tache

VERSION = 1
FICHIER_PAR_DEFAUT = "taches.json"


class ErreurStockage(Exception):
    """Fichier illisible ou au format invalide."""


def chemin_fichier(option=None):
    """Ordre de priorité : option --fichier, variable TACHES_FICHIER, taches.json."""
    return option or os.environ.get("TACHES_FICHIER") or FICHIER_PAR_DEFAUT


def charger(chemin):
    """Charge la liste des tâches. Un fichier absent ou vide donne une liste vide.

    Lève ErreurStockage si le contenu est du JSON invalide ou mal formé.
    Le fichier n'est jamais modifié ni écrasé par cette fonction.
    """
    if not os.path.exists(chemin) or os.path.getsize(chemin) == 0:
        return []
    try:
        with open(chemin, encoding="utf-8") as fichier:
            donnees = json.load(fichier)
    except json.JSONDecodeError as erreur:
        raise ErreurStockage(f"{chemin} n'est pas du JSON valide ({erreur})") from None
    except OSError as erreur:
        raise ErreurStockage(f"lecture impossible de {chemin} ({erreur.strerror})") from None

    if not isinstance(donnees, dict) or not isinstance(donnees.get("taches"), list):
        raise ErreurStockage(f"{chemin} : clé 'taches' (liste) manquante")
    ids = set()
    for position, tache in enumerate(donnees["taches"], start=1):
        try:
            valider_tache(tache)
        except ValueError as erreur:
            raise ErreurStockage(f"{chemin} : tâche n°{position} : {erreur}") from None
        if tache["id"] in ids:
            raise ErreurStockage(f"{chemin} : identifiant en double : {tache['id']}")
        ids.add(tache["id"])
    return donnees["taches"]


def sauvegarder(chemin, taches):
    """Écrit la liste dans le fichier de façon atomique.

    On écrit d'abord dans un fichier temporaire du même dossier, puis on le
    renomme : une coupure en cours d'écriture ne peut pas laisser un fichier
    à moitié écrit.
    """
    dossier = os.path.dirname(os.path.abspath(chemin))
    os.makedirs(dossier, exist_ok=True)
    descripteur, temporaire = tempfile.mkstemp(dir=dossier, prefix=".taches-", suffix=".tmp")
    try:
        with os.fdopen(descripteur, "w", encoding="utf-8") as fichier:
            json.dump({"version": VERSION, "taches": taches}, fichier, ensure_ascii=False, indent=2)
            fichier.write("\n")
        os.replace(temporaire, chemin)
    except BaseException:
        if os.path.exists(temporaire):
            os.remove(temporaire)
        raise
