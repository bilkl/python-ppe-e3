"""Banque : ouverture, recherche, virements (tout ou rien)."""

import pytest

from banque import (CompteEpargne, CompteFerme, CompteInconnu, FondsInsuffisants, MontantInvalide,
                    OperationInvalide)
from tests.conftest import d

# ---- ouverture et recherche ---------------------------------------------------------------


def test_numeros_attribues_dans_l_ordre(banque):
    assert [banque.ouvrir_compte(f"Client {i}").numero for i in range(3)] == ["CH-0001", "CH-0002", "CH-0003"]


def test_ouvrir_un_compte_epargne(banque):
    compte = banque.ouvrir_compte("Alice", 500, taux_epargne="0.02")
    assert isinstance(compte, CompteEpargne) and compte.solde == d("500.00")


def test_epargne_avec_decouvert_refuse(banque):
    with pytest.raises(OperationInvalide, match="épargne"):
        banque.ouvrir_compte("Alice", taux_epargne="0.02", decouvert_autorise=100)
    assert banque.comptes() == []


def test_ouverture_refusee_ne_consomme_pas_de_numero(banque):
    with pytest.raises(MontantInvalide):
        banque.ouvrir_compte("Alice", solde_initial="abc")
    with pytest.raises(OperationInvalide):
        banque.ouvrir_compte("   ")
    assert banque.ouvrir_compte("Alice").numero == "CH-0001"


def test_retrouver_un_compte(banque):
    compte = banque.ouvrir_compte("Alice")
    assert banque.compte("CH-0001") is compte


@pytest.mark.parametrize("numero", ["CH-9999", "", "ch-0001", None])
def test_compte_inconnu(banque, numero):
    banque.ouvrir_compte("Alice")
    with pytest.raises(CompteInconnu):
        banque.compte(numero)


def test_comptes_dans_l_ordre_d_ouverture(banque):
    a, b = banque.ouvrir_compte("A"), banque.ouvrir_compte("B")
    assert banque.comptes() == [a, b]


def test_comptes_renvoie_une_copie(banque):
    banque.ouvrir_compte("A")
    banque.comptes().clear()
    assert len(banque.comptes()) == 1


# ---- virements ----------------------------------------------------------------------------


def test_virement(banque_avec_deux_comptes):
    banque, a, b = banque_avec_deux_comptes
    emise, recue = banque.virement(a.numero, b.numero, "300.50")
    assert (a.solde, b.solde) == (d("699.50"), d("350.50"))
    assert (emise.type, recue.type) == ("virement_emis", "virement_recu")
    assert "CH-0002" in emise.libelle and "CH-0001" in recue.libelle


def test_virement_conserve_le_total(banque_avec_deux_comptes):
    banque, a, b = banque_avec_deux_comptes
    avant = banque.total_depots()
    banque.virement(a.numero, b.numero, "123.45")
    banque.virement(b.numero, a.numero, "0.01")
    assert banque.total_depots() == avant == d("1050.00")


def test_virement_utilise_le_decouvert_de_l_emetteur(banque_avec_deux_comptes):
    banque, a, b = banque_avec_deux_comptes
    banque.virement(a.numero, b.numero, 1200)  # 1000 + 200 de découvert : limite exacte
    assert (a.solde, b.solde) == (d("-200.00"), d("1250.00"))


def test_virement_refuse_pour_fonds_insuffisants_ne_modifie_aucun_compte(banque_avec_deux_comptes):
    banque, a, b = banque_avec_deux_comptes
    with pytest.raises(FondsInsuffisants):
        banque.virement(b.numero, a.numero, "50.01")  # b n'a que 50 et pas de découvert
    assert (a.solde, b.solde) == (d("1000.00"), d("50.00"))
    assert len(a.historique) == 1 and len(b.historique) == 1


def test_virement_vers_soi_meme_refuse(banque_avec_deux_comptes):
    banque, a, _ = banque_avec_deux_comptes
    with pytest.raises(OperationInvalide, match="lui-même"):
        banque.virement(a.numero, a.numero, 10)


@pytest.mark.parametrize("source, destination", [("CH-0001", "CH-9999"), ("CH-9999", "CH-0001")])
def test_virement_avec_compte_inconnu(banque_avec_deux_comptes, source, destination):
    banque, a, b = banque_avec_deux_comptes
    with pytest.raises(CompteInconnu):
        banque.virement(source, destination, 10)
    assert (a.solde, b.solde) == (d("1000.00"), d("50.00"))


@pytest.mark.parametrize("montant", [0, -5, "abc", 1.5, "1.005"])
def test_virement_avec_montant_invalide(banque_avec_deux_comptes, montant):
    banque, a, b = banque_avec_deux_comptes
    with pytest.raises(MontantInvalide):
        banque.virement(a.numero, b.numero, montant)
    assert (a.solde, b.solde) == (d("1000.00"), d("50.00"))


def test_virement_depuis_ou_vers_un_compte_cloture_ne_modifie_rien(banque):
    actif = banque.ouvrir_compte("Actif", 100)
    ferme = banque.ouvrir_compte("Fermé")
    banque.fermer_compte(ferme.numero)
    with pytest.raises(CompteFerme):
        banque.virement(actif.numero, ferme.numero, 10)
    with pytest.raises(CompteFerme):
        banque.virement(ferme.numero, actif.numero, 10)
    assert actif.solde == d("100.00") and len(actif.historique) == 1


def test_virement_entre_courant_et_epargne(banque):
    courant = banque.ouvrir_compte("Alice", 1000)
    epargne = banque.ouvrir_compte("Alice", 0, taux_epargne="0.012")
    banque.virement(courant.numero, epargne.numero, 600)
    assert epargne.appliquer_interets().montant == d("0.60")  # 600 × 0.012 ÷ 12
    assert courant.solde == d("400.00")


# ---- total et clôture ---------------------------------------------------------------------


def test_total_des_depots_d_une_banque_vide(banque):
    assert banque.total_depots() == 0


def test_total_inclut_les_soldes_negatifs(banque):
    banque.ouvrir_compte("A", 100)
    b = banque.ouvrir_compte("B", 0, decouvert_autorise=100)
    b.retirer(30)
    assert banque.total_depots() == d("70.00")


def test_fermer_compte_par_numero(banque):
    compte = banque.ouvrir_compte("A")
    banque.fermer_compte(compte.numero)
    assert compte.ferme


def test_fermer_compte_inconnu(banque):
    with pytest.raises(CompteInconnu):
        banque.fermer_compte("CH-0042")
