#!/usr/bin/env python3
"""Génère un export CSV de ventes fictif mais réaliste (3e trimestre 2026).

Reproductible : la graine est fixée, le même fichier est produit à chaque
exécution.

Usage :  python3 tools/generer_donnees.py
Produit : data/ventes_t3_2026.csv        (320 ventes valides)
          data/ventes_avec_erreurs.csv   (petit fichier avec lignes invalides)
"""

import csv
import os
import random
from datetime import date, timedelta

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(RACINE, "data")

# (produit, catégorie, prix unitaire CHF, poids de popularité)
PRODUITS = [
    ("Ordinateur portable 15\"", "Informatique", "1290.00", 3),
    ("Écran 27\"", "Informatique", "389.00", 5),
    ("Dock USB-C", "Informatique", "149.90", 6),
    ("Imprimante laser", "Informatique", "219.00", 2),
    ("Clavier sans fil", "Accessoires", "59.90", 12),
    ("Souris ergonomique", "Accessoires", "44.50", 14),
    ("Casque audio", "Accessoires", "129.00", 7),
    ("Webcam HD", "Accessoires", "79.00", 8),
    ("Câble HDMI 2 m", "Accessoires", "14.90", 20),
    ("Chaise de bureau", "Mobilier", "249.00", 4),
    ("Bureau réglable", "Mobilier", "599.00", 2),
    ("Lampe LED", "Mobilier", "39.90", 9),
]
REGIONS = [("Genève", 30), ("Vaud", 28), ("Valais", 10), ("Fribourg", 8), ("Neuchâtel", 6), ("Jura", 4)]
DEBUT, FIN = date(2026, 7, 1), date(2026, 9, 30)
NB_VENTES = 320
COLONNES = ["date", "id_vente", "produit", "categorie", "region", "quantite", "prix_unitaire"]


def tirage_quantite(rng, prix):
    """Les articles chers se vendent à l'unité, les petits par lots."""
    if float(prix) > 500:
        return rng.choice([1, 1, 1, 2])
    if float(prix) > 100:
        return rng.choice([1, 1, 2, 3])
    return rng.choice([1, 2, 2, 3, 5, 10])


def generer(rng):
    jours = (FIN - DEBUT).days + 1
    lignes = []
    for _ in range(NB_VENTES):
        # un peu moins d'activité les week-ends
        while True:
            jour = DEBUT + timedelta(days=rng.randrange(jours))
            if jour.weekday() < 5 or rng.random() < 0.25:
                break
        produit, categorie, prix, _ = rng.choices(PRODUITS, weights=[p[3] for p in PRODUITS])[0]
        region = rng.choices([r[0] for r in REGIONS], weights=[r[1] for r in REGIONS])[0]
        lignes.append([jour.isoformat(), produit, categorie, region, tirage_quantite(rng, prix), prix])
    lignes.sort(key=lambda ligne: ligne[0])
    return [[l[0], f"V-{i:04d}", *l[1:]] for i, l in enumerate(lignes, start=1)]


def ecrire(chemin, lignes):
    with open(chemin, "w", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.writer(fichier, delimiter=";")
        ecrivain.writerow(COLONNES)
        ecrivain.writerows(lignes)


def main():
    os.makedirs(DATA, exist_ok=True)
    rng = random.Random(2026)
    ventes = generer(rng)
    ecrire(os.path.join(DATA, "ventes_t3_2026.csv"), ventes)

    # Petit fichier avec des erreurs typiques d'un export réel.
    sale = [
        ["2026-07-01", "E-001", "Souris ergonomique", "Accessoires", "Vaud", "2", "44.50"],  # valide
        ["2026-07-02", "E-002", "Écran 27\"", "Informatique", "Genève", "1", "389.00"],  # valide
        ["2026-07-03", "E-003", "Casque audio", "Accessoires", "Valais", "abc", "129.00"],  # quantité non numérique
        ["07/04/2026", "E-004", "Webcam HD", "Accessoires", "Jura", "1", "79.00"],  # date invalide
        ["2026-07-05", "E-005", "Lampe LED", "Mobilier", "Vaud", "-2", "39.90"],  # quantité négative
        ["2026-07-06", "E-006", "", "Mobilier", "Vaud", "1", "39.90"],  # produit manquant
        ["2026-07-07", "E-002", "Écran 27\"", "Informatique", "Genève", "1", "389.00"],  # id en double
        ["2026-07-08", "E-008", "Clavier sans fil", "Accessoires", "Fribourg", "3", "59,90"],  # virgule décimale
        ["2026-07-09", "E-009", "Dock USB-C", "Informatique", "Vaud", "1", "nan"],  # prix non fini
        ["2026-07-10", "E-010", "Bureau réglable", "Mobilier", "Neuchâtel", "1"],  # colonne manquante
    ]
    ecrire(os.path.join(DATA, "ventes_avec_erreurs.csv"), sale)
    print(f"{len(ventes)} ventes écrites dans data/ventes_t3_2026.csv")


if __name__ == "__main__":
    main()
