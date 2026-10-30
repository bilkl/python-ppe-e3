"""Exceptions métier. Toutes dérivent de ErreurBancaire : un appelant peut les attraper d'un coup."""


class ErreurBancaire(Exception):
    """Racine de toutes les erreurs du module."""


class MontantInvalide(ErreurBancaire, ValueError):
    """Montant mal formé, hors limites ou de mauvais type."""


class FondsInsuffisants(ErreurBancaire):
    """Le retrait dépasserait le solde augmenté du découvert autorisé."""

    def __init__(self, montant, disponible):
        super().__init__(f"fonds insuffisants : retrait de {montant} demandé, {disponible} disponible")
        self.montant = montant
        self.disponible = disponible


class CompteFerme(ErreurBancaire):
    """Opération demandée sur un compte clôturé."""


class CompteInconnu(ErreurBancaire):
    """Numéro de compte absent de la banque."""


class OperationInvalide(ErreurBancaire):
    """Opération interdite par une règle métier (virement vers soi-même, clôture avec solde...)."""
