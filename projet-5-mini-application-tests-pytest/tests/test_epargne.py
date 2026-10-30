"""Compte épargne : taux, intérêts, absence de découvert."""

from decimal import Decimal

import pytest

from banque import CompteBancaire, CompteEpargne, CompteFerme, FondsInsuffisants, MontantInvalide
from tests.conftest import d


def test_un_compte_epargne_est_un_compte_bancaire(epargne):
    assert isinstance(epargne, CompteBancaire)
    assert epargne.taux_annuel == Decimal("0.015")
    assert epargne.decouvert_autorise == 0


def test_interets_mensuels_exacts(epargne):
    operation = epargne.appliquer_interets()  # 12000 × 0.015 ÷ 12 = 15.00
    assert (operation.type, operation.montant) == ("interets", d("15.00"))
    assert epargne.solde == d("12015.00")


def test_interets_composes_d_un_mois_a_l_autre(epargne):
    epargne.appliquer_interets()
    epargne.appliquer_interets()  # 12015 × 0.00125 = 15.01875 -> 15.02
    assert epargne.solde == d("12030.02")


@pytest.mark.parametrize(
    "solde, taux, attendu",
    [
        ("10300", "0.015", "12.88"),   # 12.875 : arrondi vers le haut, au demi
        ("10299.80", "0.015", "12.87"),  # 12.87475 : arrondi vers le bas
        ("100", "0.01", "0.08"),       # 0.0833...
        ("1000", "0", None),           # taux nul : rien à créditer
        ("0.50", "0.001", None),       # 0.0000416 : sous le demi-centime
        ("0.01", "0.10", None),        # 0.0000833
        ("1000000", "0.10", "8333.33"),
    ],
)
def test_arrondi_des_interets(horloge, solde, taux, attendu):
    compte = CompteEpargne("E", "Zoé", taux, solde, horloge=horloge)
    operation = compte.appliquer_interets()
    if attendu is None:
        assert operation is None and compte.solde == d(solde)
    else:
        assert operation.montant == d(attendu)


def test_pas_d_interets_sur_solde_nul(horloge):
    compte = CompteEpargne("E", "Zoé", "0.05", horloge=horloge)
    assert compte.appliquer_interets() is None
    assert compte.historique == ()


def test_interets_refuses_sur_compte_cloture(horloge):
    compte = CompteEpargne("E", "Zoé", "0.05", horloge=horloge)
    compte.fermer()
    with pytest.raises(CompteFerme):
        compte.appliquer_interets()


def test_epargne_ne_peut_jamais_etre_a_decouvert(epargne):
    with pytest.raises(FondsInsuffisants):
        epargne.retirer("12000.01")
    epargne.retirer(12000)
    assert epargne.solde == 0


@pytest.mark.parametrize("taux", ["0", "0.10", "0.05", 0, Decimal("0.0001")])
def test_taux_valides(horloge, taux):
    assert CompteEpargne("E", "Zoé", taux, horloge=horloge).taux_annuel == Decimal(str(taux))


@pytest.mark.parametrize("taux", ["-0.01", "0.101", "1", "abc", "nan", "inf", 0.015, True, None, [1]])
def test_taux_invalides(taux):
    with pytest.raises(MontantInvalide, match="taux annuel"):
        CompteEpargne("E", "Zoé", taux)
