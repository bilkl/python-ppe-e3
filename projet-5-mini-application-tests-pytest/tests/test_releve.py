"""Relevé de compte : mise en forme, et démonstration `python3 -m banque`."""

import runpy

import pytest

from banque import CompteBancaire, formater_releve
from banque.releve import chf


@pytest.mark.parametrize(
    "valeur, attendu",
    [("0", "0.00"), ("12.5", "12.50"), ("1234.5", "1'234.50"), ("1234567.89", "1'234'567.89"), ("-500", "-500.00")],
)
def test_format_des_montants(valeur, attendu):
    from decimal import Decimal
    assert chf(Decimal(valeur)) == attendu


def test_releve_complet(compte):
    compte.deposer("250.50")
    compte.retirer(80)
    lignes = formater_releve(compte).splitlines()
    assert lignes[0] == "Compte CH-0001 : Alice Martin"
    assert "ouverture" in lignes[2] and "+1'000.00" in lignes[2]
    assert "depot" in lignes[3] and "+250.50" in lignes[3] and "1'250.50" in lignes[3]
    assert "retrait" in lignes[4] and "-80.00" in lignes[4] and lignes[4].rstrip().endswith("1'170.50")
    assert lignes[-1] == "Solde : CHF 1'170.50   Disponible : CHF 1'670.50"


def test_releve_d_un_compte_sans_operation():
    texte = formater_releve(CompteBancaire("X", "Zoé"))
    assert "(aucune opération)" in texte
    assert texte.endswith("Solde : CHF 0.00   Disponible : CHF 0.00")


def test_releve_signale_un_compte_cloture():
    compte = CompteBancaire("X", "Zoé")
    compte.fermer()
    assert formater_releve(compte).splitlines()[0].endswith("(CLÔTURÉ)")


def test_virements_affiches_avec_le_bon_signe(banque_avec_deux_comptes):
    banque, a, b = banque_avec_deux_comptes
    banque.virement(a.numero, b.numero, 100)
    assert "-100.00" in formater_releve(a)
    assert "+100.00" in formater_releve(b)


def test_demonstration_s_execute_sans_erreur(capsys):
    runpy.run_module("banque", run_name="__main__")
    sortie = capsys.readouterr().out
    assert "Compte CH-0001" in sortie and "interets" in sortie
    assert "refusé -> fonds insuffisants" in sortie
