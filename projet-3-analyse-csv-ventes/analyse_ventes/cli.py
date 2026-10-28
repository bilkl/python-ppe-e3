"""Interface en ligne de commande."""

import argparse
import os
import re
import sys

from . import export, lecture, stats


def mois_valide(texte):
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", texte):
        raise argparse.ArgumentTypeError(f"{texte!r} n'est pas un mois AAAA-MM")
    return texte


def entier_positif(texte):
    try:
        n = int(texte)
    except ValueError:
        n = 0
    if n <= 0:
        raise argparse.ArgumentTypeError(f"{texte!r} n'est pas un entier positif")
    return n


def construire_parseur():
    p = argparse.ArgumentParser(
        prog="python3 -m analyse_ventes",
        description="Statistiques simples sur un export CSV de ventes (sans Excel).",
    )
    p.add_argument("fichier", help="export CSV (colonnes : " + ", ".join(lecture.COLONNES) + ")")
    p.add_argument("--mois", type=mois_valide, metavar="AAAA-MM", help="ne garder que ce mois")
    p.add_argument("--region", help="ne garder que cette région")
    p.add_argument("--categorie", help="ne garder que cette catégorie")
    p.add_argument("--tri", choices=("ca", "quantite", "nom"), default="ca", help="tri du tableau des produits (défaut : ca)")
    p.add_argument("--top", type=entier_positif, metavar="N", help="n'afficher que les N premiers produits")
    p.add_argument("--sortie", metavar="DOSSIER", help="écrire synthese.txt et synthese-produits.csv dans ce dossier")
    return p


def main(argv=None):
    """Renvoie 0 si l'analyse a été produite, 1 si le fichier est inutilisable."""
    args = construire_parseur().parse_args(argv)
    try:
        ventes, rejets, nb_lignes = lecture.lire_ventes(args.fichier)
    except lecture.ErreurLecture as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1

    retenues = stats.filtrer(ventes, args.mois, args.region, args.categorie)
    filtres = {"mois": args.mois, "région": args.region, "catégorie": args.categorie}
    texte = export.rapport(os.path.basename(args.fichier), retenues, rejets, nb_lignes, filtres, args.tri, args.top)
    print(texte, end="")

    if args.sortie:
        try:
            chemins = export.ecrire_synthese(args.sortie, texte, retenues)
        except OSError as erreur:
            print(f"Erreur : écriture impossible dans {args.sortie} ({erreur.strerror})", file=sys.stderr)
            return 1
        print("Fichiers écrits : " + ", ".join(chemins))
    return 0
