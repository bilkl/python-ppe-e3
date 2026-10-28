"""Statistiques descriptives sur une liste de Vente. Aucune entrée/sortie ici.

Les montants sont des Decimal : les sommes sont exactes, sans erreur d'arrondi
des flottants. Seule la moyenne est arrondie (à 2 décimales, demi vers le haut).
"""

import unicodedata
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

CENTIMES = Decimal("0.01")
CLES_GROUPE = ("mois", "region", "categorie", "produit")


def cle_alpha(texte):
    """Clé de tri alphabétique français : sans casse et sans accents (Écran se range avec les E)."""
    decompose = unicodedata.normalize("NFD", texte.casefold())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def arrondir(montant):
    return montant.quantize(CENTIMES, rounding=ROUND_HALF_UP)


def filtrer(ventes, mois=None, region=None, categorie=None):
    """Garde les ventes qui respectent tous les filtres donnés (comparaison sans casse)."""
    def egal(valeur, voulu):
        return voulu is None or valeur.casefold() == voulu.casefold()

    return [v for v in ventes if egal(v.mois, mois) and egal(v.region, region) and egal(v.categorie, categorie)]


def chiffre_affaires(ventes):
    return sum((v.montant for v in ventes), Decimal(0))


def quantite_totale(ventes):
    return sum(v.quantite for v in ventes)


def moyenne_par_vente(ventes):
    """CA total divisé par le nombre de ventes (lignes). Lève ValueError si aucune vente."""
    if not ventes:
        raise ValueError("aucune vente")
    return arrondir(chiffre_affaires(ventes) / len(ventes))


def grouper(ventes, cle):
    """Regroupe par mois, région, catégorie ou produit.

    Renvoie une liste de dictionnaires {cle, ventes, quantite, ca}, non triée.
    """
    if cle not in CLES_GROUPE:
        raise ValueError(f"clé de regroupement inconnue : {cle!r}")
    groupes = defaultdict(lambda: {"ventes": 0, "quantite": 0, "ca": Decimal(0)})
    for v in ventes:
        g = groupes[getattr(v, cle)]
        g["ventes"] += 1
        g["quantite"] += v.quantite
        g["ca"] += v.montant
    return [{"cle": k, **g} for k, g in groupes.items()]


def trier(groupes, par="ca"):
    """Trie les groupes : 'ca' et 'quantite' décroissants, 'nom' croissant.

    En cas d'égalité, l'ordre alphabétique de la clé départage (résultat stable
    et reproductible).
    """
    if par == "nom":
        return sorted(groupes, key=lambda g: cle_alpha(g["cle"]))
    if par not in ("ca", "quantite"):
        raise ValueError(f"critère de tri inconnu : {par!r}")
    return sorted(groupes, key=lambda g: (-g[par], cle_alpha(g["cle"])))


def produit_le_plus_vendu(ventes):
    """Produit dont la quantité totale vendue est la plus élevée (égalité : plus fort CA)."""
    if not ventes:
        raise ValueError("aucune vente")
    produits = grouper(ventes, "produit")
    return min(produits, key=lambda g: (-g["quantite"], -g["ca"], cle_alpha(g["cle"])))


def produit_plus_gros_ca(ventes):
    """Produit au chiffre d'affaires le plus élevé."""
    if not ventes:
        raise ValueError("aucune vente")
    return trier(grouper(ventes, "produit"), "ca")[0]
