"""Validation des montants : cas nominaux, puis cas limites et erreurs."""

from decimal import Decimal

import pytest

from banque.erreurs import MontantInvalide
from banque.montants import MONTANT_MAX, en_montant

# ---- cas nominaux --------------------------------------------------------------------


@pytest.mark.parametrize(
    "entree, attendu",
    [
        (10, "10.00"),
        ("12.5", "12.50"),
        ("12,50", "12.50"),          # virgule décimale acceptée
        ("  7.00  ", "7.00"),         # espaces autour ignorés
        (Decimal("3.1"), "3.10"),
        (Decimal("0.01"), "0.01"),    # plus petit montant possible : un centime
        ("1e2", "100.00"),            # notation scientifique équivalente à un entier
    ],
)
def test_montants_valides(entree, attendu):
    resultat = en_montant(entree)
    assert resultat == Decimal(attendu)
    assert str(resultat) == attendu  # toujours exactement 2 décimales


def test_zero_autorise_uniquement_si_demande():
    assert en_montant(0, zero_autorise=True) == Decimal("0.00")
    with pytest.raises(MontantInvalide, match="strictement positif"):
        en_montant(0)


def test_montant_maximum_accepte():
    assert en_montant(MONTANT_MAX) == MONTANT_MAX


# ---- cas limites et erreurs ---------------------------------------------------------------


@pytest.mark.parametrize("flottant", [0.1, 12.5, 1.0])
def test_les_flottants_sont_refuses(flottant):
    with pytest.raises(MontantInvalide, match="float refusé"):
        en_montant(flottant)


@pytest.mark.parametrize("mauvais_type", [True, False, None, [5], (5,), {"a": 1}, b"5"])
def test_types_refuses(mauvais_type):
    with pytest.raises(MontantInvalide, match="refusé"):
        en_montant(mauvais_type)


@pytest.mark.parametrize("texte", ["", "   ", "abc", "12.5.3", "1 000", "12,5,3", "--5", "€10"])
def test_textes_non_numeriques(texte):
    with pytest.raises(MontantInvalide, match="n'est pas un nombre"):
        en_montant(texte)


@pytest.mark.parametrize("texte", ["nan", "NaN", "inf", "-inf", "Infinity"])
def test_valeurs_non_finies(texte):
    with pytest.raises(MontantInvalide, match="non finie"):
        en_montant(texte)


@pytest.mark.parametrize("valeur", ["10.001", "0.005", "1.234", Decimal("5.555")])
def test_plus_de_deux_decimales(valeur):
    with pytest.raises(MontantInvalide, match="2 décimales"):
        en_montant(valeur)


@pytest.mark.parametrize("valeur", [0, "0", "0.00", "-0"])
def test_zero_refuse_par_defaut(valeur):
    with pytest.raises(MontantInvalide):
        en_montant(valeur)


@pytest.mark.parametrize("valeur", [-1, "-0.01", Decimal("-5")])
@pytest.mark.parametrize("zero_autorise", [False, True])
def test_negatifs_toujours_refuses(valeur, zero_autorise):
    with pytest.raises(MontantInvalide):
        en_montant(valeur, zero_autorise=zero_autorise)


def test_au_dessus_du_maximum_refuse():
    with pytest.raises(MontantInvalide, match="maximum"):
        en_montant(MONTANT_MAX + Decimal("0.01"))


def test_le_nom_du_champ_figure_dans_le_message():
    with pytest.raises(MontantInvalide, match="solde initial"):
        en_montant("abc", nom="solde initial")


def test_montant_invalide_est_aussi_une_value_error():
    with pytest.raises(ValueError):
        en_montant("abc")
