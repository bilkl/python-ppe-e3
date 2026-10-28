"""Interface en ligne de commande (argparse)."""

import argparse
import sys

from . import modele, stockage

SYMBOLES = {"a_faire": "[ ]", "terminee": "[x]"}


def formater_tache(tache):
    """Une ligne lisible par tâche."""
    ligne = f"{tache['id']:>3}  {SYMBOLES[tache['statut']]}  {tache['priorite']:<8}  {tache['titre']}"
    return ligne


def afficher_liste(taches):
    if not taches:
        print("Aucune tâche.")
        return
    print(f"{'ID':>3}  {'ST.':<3}  {'PRIORITÉ':<8}  TITRE")
    for tache in taches:
        print(formater_tache(tache))
    restantes = sum(1 for t in taches if t["statut"] == "a_faire")
    print(f"-- {len(taches)} tâche(s), {restantes} à faire")


def construire_parseur():
    parseur = argparse.ArgumentParser(
        prog="python3 -m gestionnaire",
        description="Gestionnaire de tâches en ligne de commande, sauvegardé en JSON.",
    )
    parseur.add_argument(
        "-f", "--fichier", help="fichier de sauvegarde (défaut : $TACHES_FICHIER ou taches.json)"
    )
    sous = parseur.add_subparsers(dest="commande", required=True, metavar="commande")

    p = sous.add_parser("ajouter", help="ajouter une tâche")
    p.add_argument("titre", help="titre de la tâche (entre guillemets)")
    p.add_argument("-p", "--priorite", choices=modele.PRIORITES, default="normale")

    p = sous.add_parser("lister", help="lister les tâches (haute priorité d'abord)")
    p.add_argument("--statut", choices=modele.STATUTS)
    p.add_argument("-p", "--priorite", choices=modele.PRIORITES)

    p = sous.add_parser("terminer", help="marquer une tâche comme terminée")
    p.add_argument("id", type=int)

    p = sous.add_parser("supprimer", help="supprimer une tâche")
    p.add_argument("id", type=int)
    return parseur


def main(argv=None):
    """Point d'entrée. Renvoie le code de sortie : 0 succès, 1 erreur d'usage ou de données."""
    args = construire_parseur().parse_args(argv)
    chemin = stockage.chemin_fichier(args.fichier)
    try:
        taches = stockage.charger(chemin)
        if args.commande == "lister":
            afficher_liste(modele.lister(taches, args.statut, args.priorite))
            return 0
        if args.commande == "ajouter":
            tache = modele.ajouter(taches, args.titre, args.priorite)
            message = f"Tâche {tache['id']} ajoutée : {tache['titre']} (priorité {tache['priorite']})"
        elif args.commande == "terminer":
            tache = modele.terminer(taches, args.id)
            message = f"Tâche {tache['id']} terminée : {tache['titre']}"
        else:
            tache = modele.supprimer(taches, args.id)
            message = f"Tâche {tache['id']} supprimée : {tache['titre']}"
        stockage.sauvegarder(chemin, taches)
        print(message)
        return 0
    except (ValueError, stockage.ErreurStockage) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    except OSError as erreur:
        print(f"Erreur : écriture impossible dans {chemin} ({erreur.strerror})", file=sys.stderr)
        return 1
