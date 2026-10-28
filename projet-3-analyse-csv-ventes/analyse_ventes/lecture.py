"""Lecture et validation du fichier CSV (module csv de la bibliothèque standard).

Une ligne invalide n'arrête pas l'analyse : elle est écartée et signalée avec
son numéro de ligne et la raison. Seules les erreurs qui rendent tout le fichier
inutilisable (absent, vide, colonnes manquantes) lèvent ErreurLecture.
"""

import csv
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import NamedTuple

COLONNES = ("date", "id_vente", "produit", "categorie", "region", "quantite", "prix_unitaire")


class ErreurLecture(Exception):
    """Le fichier entier est inutilisable."""


class Vente(NamedTuple):
    jour: date
    id_vente: str
    produit: str
    categorie: str
    region: str
    quantite: int
    prix_unitaire: Decimal

    @property
    def mois(self):
        return self.jour.strftime("%Y-%m")

    @property
    def montant(self):
        """Montant de la ligne : quantité × prix unitaire (exact, en Decimal)."""
        return self.quantite * self.prix_unitaire


class Rejet(NamedTuple):
    ligne: int
    raison: str


def detecter_delimiteur(premiere_ligne):
    """';' (export Excel suisse/français) ou ',' : le plus fréquent dans l'en-tête."""
    return ";" if premiere_ligne.count(";") > premiere_ligne.count(",") else ","


def convertir_ligne(champs):
    """Transforme un dictionnaire de champs texte en Vente. Lève ValueError si invalide."""
    texte = {}
    for nom in COLONNES:
        valeur = champs.get(nom)
        if valeur is None:
            raise ValueError("colonne manquante sur la ligne")
        texte[nom] = valeur.strip()

    for nom in ("id_vente", "produit", "categorie", "region"):
        if not texte[nom]:
            raise ValueError(f"champ {nom} vide")
    try:
        jour = date.fromisoformat(texte["date"])
    except ValueError:
        raise ValueError(f"date invalide : {texte['date']!r} (attendu AAAA-MM-JJ)") from None
    try:
        quantite = int(texte["quantite"])
    except ValueError:
        raise ValueError(f"quantité invalide : {texte['quantite']!r}") from None
    if quantite <= 0:
        raise ValueError(f"quantité non positive : {quantite}")
    try:
        prix = Decimal(texte["prix_unitaire"].replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"prix invalide : {texte['prix_unitaire']!r}") from None
    if not prix.is_finite():
        raise ValueError(f"prix invalide : {texte['prix_unitaire']!r}")
    if prix <= 0:
        raise ValueError(f"prix non positif : {prix}")
    return Vente(jour, texte["id_vente"], texte["produit"], texte["categorie"], texte["region"], quantite, prix)


def lire_ventes(chemin):
    """Lit le fichier. Renvoie (ventes, rejets, nombre_de_lignes_de_données)."""
    if not os.path.isfile(chemin):
        raise ErreurLecture(f"fichier introuvable : {chemin}")
    try:
        with open(chemin, encoding="utf-8-sig", newline="") as fichier:
            entete = fichier.readline()
            if not entete.strip():
                raise ErreurLecture(f"{chemin} est vide")
            fichier.seek(0)
            lecteur = csv.reader(fichier, delimiter=detecter_delimiteur(entete))
            noms = [n.strip() for n in next(lecteur)]
            manquantes = [c for c in COLONNES if c not in noms]
            if manquantes:
                raise ErreurLecture(f"colonnes manquantes : {', '.join(manquantes)}")
            ventes, rejets, vus, total = [], [], set(), 0
            for ligne in lecteur:
                if not any(c.strip() for c in ligne):
                    continue  # ligne vide, ignorée sans compter
                total += 1
                numero = lecteur.line_num
                if len(ligne) != len(noms):
                    rejets.append(Rejet(numero, f"{len(ligne)} colonnes au lieu de {len(noms)}"))
                    continue
                try:
                    vente = convertir_ligne(dict(zip(noms, ligne)))
                except ValueError as erreur:
                    rejets.append(Rejet(numero, str(erreur)))
                    continue
                if vente.id_vente in vus:
                    rejets.append(Rejet(numero, f"identifiant en double : {vente.id_vente}"))
                    continue
                vus.add(vente.id_vente)
                ventes.append(vente)
    except UnicodeDecodeError:
        raise ErreurLecture(f"{chemin} n'est pas encodé en UTF-8") from None
    except OSError as erreur:
        raise ErreurLecture(f"lecture impossible de {chemin} ({erreur.strerror})") from None
    return ventes, rejets, total
