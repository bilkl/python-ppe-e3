"""Comptes bancaires. Logique métier seule : aucune lecture clavier, aucun affichage."""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from .erreurs import CompteFerme, FondsInsuffisants, MontantInvalide, OperationInvalide
from .montants import CENTIME, en_montant

TITULAIRE_MAX = 60


def maintenant():
    return datetime.now().isoformat(timespec="seconds")


@dataclass(frozen=True)
class Operation:
    """Une ligne de l'historique. Immuable : l'historique ne se réécrit pas."""

    type: str  # ouverture, depot, retrait, virement_emis, virement_recu, interets
    montant: Decimal
    solde_apres: Decimal
    libelle: str
    horodatage: str


class CompteBancaire:
    def __init__(self, numero, titulaire, solde_initial=0, decouvert_autorise=0, horloge=maintenant):
        titulaire = " ".join(str(titulaire).split())
        if not titulaire:
            raise OperationInvalide("le titulaire ne peut pas être vide")
        if len(titulaire) > TITULAIRE_MAX:
            raise OperationInvalide(f"le titulaire dépasse {TITULAIRE_MAX} caractères")
        self._numero = numero
        self._titulaire = titulaire
        self._decouvert = en_montant(decouvert_autorise, "découvert autorisé", zero_autorise=True)
        self._solde = Decimal("0.00")
        self._ferme = False
        self._historique = []
        self._horloge = horloge
        initial = en_montant(solde_initial, "solde initial", zero_autorise=True)
        if initial > 0:
            self._enregistrer("ouverture", initial, initial, "Ouverture du compte")

    # -- lecture -----------------------------------------------------------------

    @property
    def numero(self):
        return self._numero

    @property
    def titulaire(self):
        return self._titulaire

    @property
    def solde(self):
        return self._solde

    @property
    def decouvert_autorise(self):
        return self._decouvert

    @property
    def disponible(self):
        """Montant retirable : solde plus découvert autorisé."""
        return self._solde + self._decouvert

    @property
    def ferme(self):
        return self._ferme

    @property
    def historique(self):
        """Copie de l'historique (tuple) : l'appelant ne peut pas le modifier."""
        return tuple(self._historique)

    # -- opérations --------------------------------------------------------------

    def _verifier_ouvert(self):
        if self._ferme:
            raise CompteFerme(f"le compte {self._numero} est clôturé")

    def _enregistrer(self, type_operation, montant, variation, libelle):
        self._solde += variation
        operation = Operation(type_operation, montant, self._solde, libelle, self._horloge())
        self._historique.append(operation)
        return operation

    def deposer(self, montant, libelle="Dépôt"):
        """Crédite le compte. Renvoie l'Operation créée."""
        self._verifier_ouvert()
        montant = en_montant(montant)
        return self._enregistrer("depot", montant, montant, libelle)

    def retirer(self, montant, libelle="Retrait"):
        """Débite le compte, dans la limite du solde plus le découvert autorisé."""
        self._verifier_ouvert()
        montant = en_montant(montant)
        if montant > self.disponible:
            raise FondsInsuffisants(montant, self.disponible)
        return self._enregistrer("retrait", montant, -montant, libelle)

    def emettre_virement(self, montant, destinataire):
        """Débit d'un virement (même règle que retirer). Utilisé par Banque.virement."""
        self._verifier_ouvert()
        montant = en_montant(montant)
        if montant > self.disponible:
            raise FondsInsuffisants(montant, self.disponible)
        return self._enregistrer("virement_emis", montant, -montant, f"Virement vers {destinataire}")

    def recevoir_virement(self, montant, expediteur):
        """Crédit d'un virement. Utilisé par Banque.virement."""
        self._verifier_ouvert()
        montant = en_montant(montant)
        return self._enregistrer("virement_recu", montant, montant, f"Virement de {expediteur}")

    def fermer(self):
        """Clôture le compte. Interdit tant que le solde n'est pas exactement nul."""
        self._verifier_ouvert()
        if self._solde != 0:
            raise OperationInvalide(f"clôture impossible : solde non nul ({self._solde})")
        self._ferme = True

    def __repr__(self):
        etat = "clôturé" if self._ferme else f"solde {self._solde}"
        return f"<{type(self).__name__} {self._numero} {self._titulaire!r} {etat}>"


class CompteEpargne(CompteBancaire):
    """Compte rémunéré : jamais à découvert, intérêts mensuels au taux annuel donné."""

    TAUX_MAX = Decimal("0.10")  # 10 % par an : au-delà, c'est une erreur de saisie

    def __init__(self, numero, titulaire, taux_annuel, solde_initial=0, horloge=maintenant):
        try:
            taux = Decimal(str(taux_annuel)) if not isinstance(taux_annuel, (bool, float)) else None
        except ArithmeticError:
            taux = None
        if taux is None or not taux.is_finite():
            raise MontantInvalide(f"taux annuel invalide : {taux_annuel!r} (utiliser str ou Decimal, ex. '0.015')")
        if not (0 <= taux <= self.TAUX_MAX):
            raise MontantInvalide(f"taux annuel hors limites : {taux} (entre 0 et {self.TAUX_MAX})")
        super().__init__(numero, titulaire, solde_initial, decouvert_autorise=0, horloge=horloge)
        self._taux = taux

    @property
    def taux_annuel(self):
        return self._taux

    def appliquer_interets(self):
        """Crédite les intérêts d'un mois : solde × taux ÷ 12, arrondi au centime supérieur dès .5.

        Renvoie l'Operation créée, ou None s'il n'y a rien à créditer (solde nul ou
        intérêts inférieurs à 0.005).
        """
        self._verifier_ouvert()
        interets = (self._solde * self._taux / 12).quantize(CENTIME, rounding=ROUND_HALF_UP)
        if interets <= 0:
            return None
        return self._enregistrer("interets", interets, interets, "Intérêts mensuels")
