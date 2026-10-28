"""Mise en forme du rapport et export de la synthèse (texte et CSV)."""

import csv
import os

from . import stats

TITRES_GROUPE = {"mois": "MOIS", "region": "RÉGION", "categorie": "CATÉGORIE", "produit": "PRODUIT"}


def chf(montant):
    """12345.6 -> « CHF 12'345.60 » (apostrophe pour les milliers, usage suisse)."""
    return "CHF " + f"{montant:,.2f}".replace(",", "'")


def unites(n):
    return f"{n} unité" + ("s" if n > 1 else "")


def tableau(entetes, lignes, alignements):
    """Tableau texte aligné. alignements : 'l' (gauche) ou 'r' (droite) par colonne."""
    largeurs = [max(len(str(x)) for x in col) for col in zip(entetes, *lignes)]

    def mise_en_forme(cellules):
        return "  ".join(
            str(c).ljust(w) if a == "l" else str(c).rjust(w) for c, w, a in zip(cellules, largeurs, alignements)
        ).rstrip()

    trait = "  ".join("-" * w for w in largeurs)
    return "\n".join([mise_en_forme(entetes), trait, *(mise_en_forme(l) for l in lignes)])


def tableau_groupes(groupes, cle, total_ca):
    lignes = [
        [g["cle"], g["ventes"], g["quantite"], chf(g["ca"]), f"{g['ca'] / total_ca * 100:5.1f} %"]
        for g in groupes
    ]
    return tableau([TITRES_GROUPE[cle], "VENTES", "QUANTITÉ", "CA", "PART"], lignes, "lrrrr")


def rapport(nom_fichier, ventes, rejets, nb_lignes, filtres, tri="ca", top=None):
    """Construit le rapport texte complet. `ventes` est déjà filtré."""
    sortie = [f"ANALYSE DES VENTES : {nom_fichier}"]
    actifs = {k: v for k, v in filtres.items() if v}
    sortie.append("Filtres : " + (", ".join(f"{k} = {v}" for k, v in actifs.items()) or "aucun"))
    sortie.append(
        f"Lignes de données : {nb_lignes}   valides : {nb_lignes - len(rejets)}   rejetées : {len(rejets)}"
    )
    for r in rejets[:10]:
        sortie.append(f"  ligne {r.ligne} rejetée : {r.raison}")
    if len(rejets) > 10:
        sortie.append(f"  ... et {len(rejets) - 10} autre(s)")
    sortie.append("")

    if not ventes:
        sortie.append("Aucune vente ne correspond aux filtres : pas de statistiques.")
        return "\n".join(sortie) + "\n"

    total = stats.chiffre_affaires(ventes)
    plus_vendu = stats.produit_le_plus_vendu(ventes)
    plus_gros = stats.produit_plus_gros_ca(ventes)
    premiere, derniere = min(v.jour for v in ventes), max(v.jour for v in ventes)

    sortie += [
        "INDICATEURS",
        f"  Période couverte        : {premiere} au {derniere}",
        f"  Nombre de ventes        : {len(ventes)}",
        f"  Quantité totale vendue  : {stats.quantite_totale(ventes)}",
        f"  Chiffre d'affaires      : {chf(total)}",
        f"  Moyenne par vente       : {chf(stats.moyenne_par_vente(ventes))}",
        f"  Produit le plus vendu   : {plus_vendu['cle']} ({unites(plus_vendu['quantite'])}, {chf(plus_vendu['ca'])})",
        f"  Produit au plus gros CA : {plus_gros['cle']} ({chf(plus_gros['ca'])}, {unites(plus_gros['quantite'])})",
        "",
    ]
    for cle, titre, ordre in (("mois", "PAR MOIS", "nom"), ("region", "PAR RÉGION", "ca"), ("categorie", "PAR CATÉGORIE", "ca")):
        sortie += [titre, tableau_groupes(stats.trier(stats.grouper(ventes, cle), ordre), cle, total), ""]

    produits = stats.trier(stats.grouper(ventes, "produit"), tri)
    libelle_tri = {"ca": "chiffre d'affaires décroissant", "quantite": "quantité décroissante", "nom": "nom croissant"}[tri]
    if top:
        produits = produits[:top]
        libelle_tri += f", {top} premiers"
    sortie += [f"PAR PRODUIT (tri : {libelle_tri})", tableau_groupes(produits, "produit", total), ""]
    return "\n".join(sortie)


def ecrire_synthese(dossier, texte, ventes):
    """Écrit synthese.txt (le rapport) et synthese-produits.csv (un produit par ligne).

    Renvoie la liste des chemins écrits.
    """
    os.makedirs(dossier, exist_ok=True)
    chemin_txt = os.path.join(dossier, "synthese.txt")
    with open(chemin_txt, "w", encoding="utf-8") as f:
        f.write(texte)

    chemin_csv = os.path.join(dossier, "synthese-produits.csv")
    with open(chemin_csv, "w", encoding="utf-8", newline="") as f:
        ecrivain = csv.writer(f, delimiter=";")
        ecrivain.writerow(["produit", "nb_ventes", "quantite", "chiffre_affaires_chf"])
        for g in stats.trier(stats.grouper(ventes, "produit"), "ca"):
            ecrivain.writerow([g["cle"], g["ventes"], g["quantite"], f"{g['ca']:.2f}"])
    return [chemin_txt, chemin_csv]
