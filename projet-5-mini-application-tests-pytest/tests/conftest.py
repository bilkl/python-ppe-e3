"""Fixtures partagées par tous les tests."""

from decimal import Decimal

import pytest

from banque import Banque, CompteBancaire, CompteEpargne


class HorlogeFixe:
    """Horloge déterministe : chaque appel avance d'une seconde. Les tests ne dépendent jamais de l'heure réelle."""

    def __init__(self):
        self.secondes = 0

    def __call__(self):
        self.secondes += 1
        return f"2026-10-30T09:00:{self.secondes:02d}"


@pytest.fixture
def horloge():
    return HorlogeFixe()


@pytest.fixture
def compte(horloge):
    """Compte courant : 1000.00 de solde, 500.00 de découvert autorisé."""
    return CompteBancaire("CH-0001", "Alice Martin", "1000", "500", horloge=horloge)


@pytest.fixture
def compte_sans_decouvert(horloge):
    return CompteBancaire("CH-0002", "Bob Dupont", "100", horloge=horloge)


@pytest.fixture
def epargne(horloge):
    """Compte épargne : 12000.00 à 1.5 % par an (intérêt mensuel exact : 15.00)."""
    return CompteEpargne("CH-0003", "Alice Martin", "0.015", "12000", horloge=horloge)


@pytest.fixture
def banque(horloge):
    return Banque(horloge=horloge)


@pytest.fixture
def banque_avec_deux_comptes(banque):
    a = banque.ouvrir_compte("Alice Martin", "1000", decouvert_autorise="200")
    b = banque.ouvrir_compte("Bob Dupont", "50")
    return banque, a, b


def d(texte):
    """Raccourci : d("12.50") -> Decimal('12.50')."""
    return Decimal(texte)
