"""Compte courant : dépôt, retrait, découvert, clôture, historique."""

from decimal import Decimal

import pytest

from banque import CompteBancaire, CompteFerme, FondsInsuffisants, MontantInvalide, OperationInvalide
from tests.conftest import d

# ---- création ------------------------------------------------------------------------


def test_creation_avec_solde_et_decouvert(compte):
    assert compte.numero == "CH-0001"
    assert compte.titulaire == "Alice Martin"
    assert compte.solde == d("1000.00")
    assert compte.decouvert_autorise == d("500.00")
    assert compte.disponible == d("1500.00")
    assert not compte.ferme


def test_creation_par_defaut_solde_nul_et_aucune_operation():
    c = CompteBancaire("X", "Zoé")
    assert c.solde == 0 and c.decouvert_autorise == 0
    assert c.historique == ()


def test_ouverture_avec_solde_cree_une_operation_d_ouverture(compte):
    (ouverture,) = compte.historique
    assert (ouverture.type, ouverture.montant, ouverture.solde_apres) == ("ouverture", d("1000.00"), d("1000.00"))


def test_titulaire_normalise():
    assert CompteBancaire("X", "  Jean   Dupont ").titulaire == "Jean Dupont"


@pytest.mark.parametrize("titulaire", ["", "   ", "x" * 61])
def test_titulaire_invalide(titulaire):
    with pytest.raises(OperationInvalide):
        CompteBancaire("X", titulaire)


def test_titulaire_de_60_caracteres_accepte():
    assert len(CompteBancaire("X", "x" * 60).titulaire) == 60


@pytest.mark.parametrize("solde, decouvert", [(-1, 0), (0, -1), ("abc", 0), (0, "abc"), (0.5, 0), (0, 1.5)])
def test_creation_avec_montants_invalides(solde, decouvert):
    with pytest.raises(MontantInvalide):
        CompteBancaire("X", "Zoé", solde, decouvert)


# ---- dépôt -----------------------------------------------------------------------------


def test_depot(compte):
    operation = compte.deposer("250.50")
    assert compte.solde == d("1250.50")
    assert (operation.type, operation.montant, operation.solde_apres) == ("depot", d("250.50"), d("1250.50"))


def test_depots_successifs_additionnent_exactement(compte):
    for _ in range(10):
        compte.deposer("0.10")
    assert compte.solde == d("1001.00")  # avec des float : 1000.9999999999999


def test_depot_avec_libelle(compte):
    assert compte.deposer(5, libelle="Cadeau").libelle == "Cadeau"


@pytest.mark.parametrize("montant", [0, -10, "abc", 1.5, "10.999", None])
def test_depot_invalide_ne_modifie_rien(compte, montant):
    avant = (compte.solde, compte.historique)
    with pytest.raises(MontantInvalide):
        compte.deposer(montant)
    assert (compte.solde, compte.historique) == avant


# ---- retrait ---------------------------------------------------------------------------


def test_retrait(compte):
    operation = compte.retirer(300)
    assert compte.solde == d("700.00")
    assert (operation.type, operation.montant) == ("retrait", d("300.00"))


def test_retrait_du_solde_exact_laisse_zero(compte_sans_decouvert):
    compte_sans_decouvert.retirer("100.00")
    assert compte_sans_decouvert.solde == 0


def test_retrait_utilise_le_decouvert(compte):
    compte.retirer(1500)  # 1000 de solde + 500 de découvert = limite exacte
    assert compte.solde == d("-500.00")
    assert compte.disponible == 0


def test_retrait_d_un_centime_au_dela_de_la_limite_refuse(compte):
    with pytest.raises(FondsInsuffisants) as info:
        compte.retirer("1500.01")
    assert info.value.montant == d("1500.01")
    assert info.value.disponible == d("1500.00")
    assert compte.solde == d("1000.00")  # inchangé


def test_retrait_sans_decouvert_refuse_au_dela_du_solde(compte_sans_decouvert):
    with pytest.raises(FondsInsuffisants, match="fonds insuffisants"):
        compte_sans_decouvert.retirer("100.01")


def test_retrait_refuse_puis_retrait_valide_ensuite(compte_sans_decouvert):
    with pytest.raises(FondsInsuffisants):
        compte_sans_decouvert.retirer(500)
    compte_sans_decouvert.retirer(40)
    assert compte_sans_decouvert.solde == d("60.00")


@pytest.mark.parametrize("montant", [0, -5, "x", 2.5, True])
def test_retrait_invalide(compte, montant):
    with pytest.raises(MontantInvalide):
        compte.retirer(montant)
    assert compte.solde == d("1000.00")


def test_depot_apres_decouvert_remonte_le_solde(compte):
    compte.retirer(1200)
    compte.deposer(300)
    assert compte.solde == d("100.00")


# ---- clôture ----------------------------------------------------------------------------


def test_cloture_avec_solde_nul(compte_sans_decouvert):
    compte_sans_decouvert.retirer(100)
    compte_sans_decouvert.fermer()
    assert compte_sans_decouvert.ferme


@pytest.mark.parametrize("operation_sur_solde", ["positif", "negatif"])
def test_cloture_refusee_si_solde_non_nul(compte, operation_sur_solde):
    if operation_sur_solde == "negatif":
        compte.retirer(1200)
    with pytest.raises(OperationInvalide, match="solde non nul"):
        compte.fermer()
    assert not compte.ferme


@pytest.mark.parametrize(
    "action",
    [
        lambda c: c.deposer(10),
        lambda c: c.retirer(10),
        lambda c: c.recevoir_virement(10, "X"),
        lambda c: c.emettre_virement(10, "X"),
        lambda c: c.fermer(),
    ],
    ids=["deposer", "retirer", "recevoir", "emettre", "refermer"],
)
def test_un_compte_cloture_refuse_toute_operation(compte_sans_decouvert, action):
    compte_sans_decouvert.retirer(100)
    compte_sans_decouvert.fermer()
    with pytest.raises(CompteFerme, match="clôturé"):
        action(compte_sans_decouvert)


# ---- historique ------------------------------------------------------------------------


def test_historique_chronologique_et_soldes_successifs(compte):
    compte.deposer(100)
    compte.retirer(50)
    assert [(o.type, o.solde_apres) for o in compte.historique] == [
        ("ouverture", d("1000.00")), ("depot", d("1100.00")), ("retrait", d("1050.00")),
    ]
    assert [o.horodatage for o in compte.historique] == [
        "2026-10-30T09:00:01", "2026-10-30T09:00:02", "2026-10-30T09:00:03",
    ]


def test_historique_est_une_copie_non_modifiable(compte):
    historique = compte.historique
    assert isinstance(historique, tuple)
    compte.deposer(1)
    assert len(historique) == 1 and len(compte.historique) == 2


def test_operation_est_immuable(compte):
    operation = compte.historique[0]
    with pytest.raises(AttributeError):
        operation.montant = Decimal("999")


def test_le_dernier_solde_de_l_historique_est_le_solde_du_compte(compte):
    compte.deposer("12.34")
    compte.retirer("56.78")
    assert compte.historique[-1].solde_apres == compte.solde


def test_les_operations_refusees_ne_sont_pas_dans_l_historique(compte):
    with pytest.raises(FondsInsuffisants):
        compte.retirer(99999)
    assert len(compte.historique) == 1  # seulement l'ouverture


def test_repr_lisible(compte):
    assert "CH-0001" in repr(compte) and "solde 1000.00" in repr(compte)
    c = CompteBancaire("Z", "Zoé")
    c.fermer()
    assert "clôturé" in repr(c)
