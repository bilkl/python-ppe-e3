"""Conversion et validation des montants.

Les montants sont des Decimal avec au plus 2 décimales (centimes). Les `float` sont
REFUSÉS : 0.1 + 0.2 != 0.3 en binaire, ce qui est inacceptable pour de l'argent.
Types acceptés : int, str (« 12.50 » ou « 12,50 »), Decimal.
"""

from decimal import Decimal, InvalidOperation

from .erreurs import MontantInvalide

CENTIME = Decimal("0.01")
MONTANT_MAX = Decimal("1000000000.00")  # un milliard : garde-fou contre les erreurs de saisie


def en_montant(valeur, nom="montant", zero_autorise=False):
    """Renvoie `valeur` converti en Decimal valide, ou lève MontantInvalide.

    Règles : type accepté, nombre fini, au plus 2 décimales, strictement positif (ou >= 0
    si zero_autorise), au plus MONTANT_MAX.
    """
    if isinstance(valeur, str):
        valeur = valeur.strip().replace(",", ".")
    elif isinstance(valeur, bool) or not isinstance(valeur, (int, Decimal)):  # bool est un int : à exclure
        # (les float sont refusés ici aussi : ni int, ni Decimal)
        raise MontantInvalide(f"{nom} : type {type(valeur).__name__} refusé (utiliser int, str ou Decimal)")
    try:
        montant = Decimal(valeur)
    except InvalidOperation:
        raise MontantInvalide(f"{nom} : {valeur!r} n'est pas un nombre") from None
    if not montant.is_finite():
        raise MontantInvalide(f"{nom} : valeur non finie refusée")
    if montant != montant.quantize(CENTIME):
        raise MontantInvalide(f"{nom} : au plus 2 décimales (centimes) : {montant}")
    montant = montant.quantize(CENTIME)
    if montant < 0 or (montant == 0 and not zero_autorise):
        exigence = "positif ou nul" if zero_autorise else "strictement positif"
        raise MontantInvalide(f"{nom} : doit être {exigence} : {montant}")
    if montant > MONTANT_MAX:
        raise MontantInvalide(f"{nom} : dépasse le maximum de {MONTANT_MAX}")
    return montant
