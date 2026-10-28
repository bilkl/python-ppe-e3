#!/usr/bin/env python3
"""Calculatrice et convertisseur d'unités en ligne de commande.

Projet 1 — Python, principes de base (E3).

Le module sépare la logique (fonctions pures, testables) de l'interface
(menu interactif). Chaque opération et chaque conversion est une fonction
indépendante qui reçoit des paramètres et renvoie une valeur.
"""

import math

# ---------------------------------------------------------------------------
# Opérations de calcul
# ---------------------------------------------------------------------------


def addition(a, b):
    """Renvoie a + b."""
    return a + b


def soustraction(a, b):
    """Renvoie a - b."""
    return a - b


def multiplication(a, b):
    """Renvoie a * b."""
    return a * b


def division(a, b):
    """Renvoie a / b. Lève ValueError si b vaut 0."""
    if b == 0:
        raise ValueError("division par zéro impossible")
    return a / b


def puissance(a, b):
    """Renvoie a puissance b. Lève ValueError si le résultat n'est pas réel."""
    try:
        resultat = a**b
    except ZeroDivisionError:
        raise ValueError("0 ne peut pas être élevé à une puissance négative")
    except OverflowError:
        raise ValueError("résultat trop grand pour être représenté")
    if isinstance(resultat, complex):
        raise ValueError("résultat non réel (base négative et exposant décimal)")
    return resultat


def modulo(a, b):
    """Renvoie le reste de a / b. Lève ValueError si b vaut 0."""
    if b == 0:
        raise ValueError("modulo par zéro impossible")
    return a % b


# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------

# Température : on passe par le Celsius comme unité pivot.
_VERS_CELSIUS = {
    "C": lambda v: v,
    "F": lambda v: (v - 32) * 5 / 9,
    "K": lambda v: v - 273.15,
}
_DEPUIS_CELSIUS = {
    "C": lambda c: c,
    "F": lambda c: c * 9 / 5 + 32,
    "K": lambda c: c + 273.15,
}
_ZERO_ABSOLU_C = -273.15

# Longueur : facteurs vers le mètre.
LONGUEURS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.344,
}

# Poids : facteurs vers le kilogramme.
POIDS = {
    "mg": 0.000001,
    "g": 0.001,
    "kg": 1.0,
    "t": 1000.0,
    "oz": 0.028349523125,
    "lb": 0.45359237,
}

TEMPERATURES = tuple(_VERS_CELSIUS)


def convertir_temperature(valeur, source, cible):
    """Convertit une température entre C, F et K.

    Lève ValueError si une unité est inconnue ou si la valeur est sous le
    zéro absolu.
    """
    source, cible = source.upper(), cible.upper()
    for unite in (source, cible):
        if unite not in _VERS_CELSIUS:
            raise ValueError(f"unité de température inconnue : {unite!r}")
    celsius = _VERS_CELSIUS[source](valeur)
    if celsius < _ZERO_ABSOLU_C:
        raise ValueError("température inférieure au zéro absolu")
    return _DEPUIS_CELSIUS[cible](celsius)


def _convertir_par_facteur(valeur, source, cible, table, grandeur):
    """Conversion générique via une table de facteurs vers l'unité pivot."""
    source, cible = source.lower(), cible.lower()
    for unite in (source, cible):
        if unite not in table:
            raise ValueError(f"unité de {grandeur} inconnue : {unite!r}")
    return valeur * table[source] / table[cible]


def convertir_longueur(valeur, source, cible):
    """Convertit une longueur (mm, cm, m, km, in, ft, yd, mi)."""
    if valeur < 0:
        raise ValueError("une longueur ne peut pas être négative")
    return _convertir_par_facteur(valeur, source, cible, LONGUEURS, "longueur")


def convertir_poids(valeur, source, cible):
    """Convertit un poids (mg, g, kg, t, oz, lb)."""
    if valeur < 0:
        raise ValueError("un poids ne peut pas être négatif")
    return _convertir_par_facteur(valeur, source, cible, POIDS, "poids")


# ---------------------------------------------------------------------------
# Saisie utilisateur
# ---------------------------------------------------------------------------


def parse_nombre(texte):
    """Transforme un texte en float. Accepte la virgule décimale.

    Lève ValueError pour une saisie vide, non numérique, NaN ou infinie.
    """
    texte = texte.strip().replace(",", ".")
    if not texte:
        raise ValueError("saisie vide")
    try:
        nombre = float(texte)
    except ValueError:
        raise ValueError(f"{texte!r} n'est pas un nombre") from None
    if not math.isfinite(nombre):
        raise ValueError("valeur non finie refusée")
    return nombre


def lire_nombre(invite, saisie=input):
    """Redemande un nombre tant que la saisie est invalide."""
    while True:
        try:
            return parse_nombre(saisie(invite))
        except ValueError as erreur:
            print(f"  ! Saisie invalide : {erreur}. Réessayez.")


def lire_unite(invite, unites, saisie=input):
    """Redemande une unité tant qu'elle n'appartient pas à la liste."""
    valides = {u.lower(): u for u in unites}
    while True:
        texte = saisie(invite).strip().lower()
        if texte in valides:
            return valides[texte]
        print(f"  ! Unité inconnue. Choix possibles : {', '.join(unites)}")


def formater(valeur):
    """Affichage lisible : 6 décimales au plus, sans zéros inutiles."""
    texte = f"{valeur:.6f}".rstrip("0").rstrip(".")
    return "0" if texte in ("", "-0") else texte


# ---------------------------------------------------------------------------
# Menu interactif
# ---------------------------------------------------------------------------

OPERATIONS = {
    "1": ("Addition", "+", addition),
    "2": ("Soustraction", "-", soustraction),
    "3": ("Multiplication", "*", multiplication),
    "4": ("Division", "/", division),
    "5": ("Puissance", "^", puissance),
    "6": ("Modulo", "%", modulo),
}

CONVERSIONS = {
    "7": ("Température", TEMPERATURES, convertir_temperature),
    "8": ("Longueur", tuple(LONGUEURS), convertir_longueur),
    "9": ("Poids", tuple(POIDS), convertir_poids),
}

MENU = """
=========== CALCULATRICE & CONVERTISSEUR ===========
  Calculs                 Conversions
  1. Addition             7. Température (C, F, K)
  2. Soustraction         8. Longueur
  3. Multiplication       9. Poids
  4. Division
  5. Puissance            0. Quitter
  6. Modulo
====================================================="""


def executer_calcul(choix, saisie=input):
    nom, symbole, fonction = OPERATIONS[choix]
    print(f"\n-- {nom} --")
    a = lire_nombre("  Premier nombre : ", saisie)
    b = lire_nombre("  Second nombre  : ", saisie)
    try:
        resultat = fonction(a, b)
    except ValueError as erreur:
        print(f"  ! Erreur : {erreur}.")
        return
    print(f"  Résultat : {formater(a)} {symbole} {formater(b)} = {formater(resultat)}")


def executer_conversion(choix, saisie=input):
    nom, unites, fonction = CONVERSIONS[choix]
    print(f"\n-- Conversion de {nom.lower()} --")
    valeur = lire_nombre("  Valeur à convertir : ", saisie)
    source = lire_unite(f"  Unité de départ ({'/'.join(unites)}) : ", unites, saisie)
    cible = lire_unite(f"  Unité d'arrivée ({'/'.join(unites)}) : ", unites, saisie)
    try:
        resultat = fonction(valeur, source, cible)
    except ValueError as erreur:
        print(f"  ! Erreur : {erreur}.")
        return
    print(f"  Résultat : {formater(valeur)} {source} = {formater(resultat)} {cible}")


def main(saisie=input):
    """Boucle principale du menu."""
    while True:
        print(MENU)
        choix = saisie("Votre choix : ").strip()
        if choix == "0":
            print("Au revoir !")
            return
        if choix in OPERATIONS:
            executer_calcul(choix, saisie)
        elif choix in CONVERSIONS:
            executer_conversion(choix, saisie)
        else:
            print("  ! Choix invalide, entrez un chiffre entre 0 et 9.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nInterruption : au revoir !")
