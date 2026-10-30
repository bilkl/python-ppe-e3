"""La banque : ouvre les comptes, les retrouve, exécute les virements entre comptes."""

from .compte import CompteBancaire, CompteEpargne, maintenant
from .erreurs import CompteInconnu, OperationInvalide
from .montants import en_montant


class Banque:
    def __init__(self, horloge=maintenant):
        self._comptes = {}
        self._horloge = horloge
        self._compteur = 0

    def ouvrir_compte(self, titulaire, solde_initial=0, decouvert_autorise=0, taux_epargne=None):
        """Ouvre un compte courant, ou un compte épargne si `taux_epargne` est donné.

        Le numéro est attribué automatiquement (CH-0001, CH-0002...). En cas d'erreur de
        validation, aucun numéro n'est consommé et aucun compte n'est créé.
        """
        numero = f"CH-{self._compteur + 1:04d}"
        if taux_epargne is None:
            compte = CompteBancaire(numero, titulaire, solde_initial, decouvert_autorise, self._horloge)
        else:
            if decouvert_autorise:
                raise OperationInvalide("un compte épargne n'a pas de découvert autorisé")
            compte = CompteEpargne(numero, titulaire, taux_epargne, solde_initial, self._horloge)
        self._compteur += 1
        self._comptes[numero] = compte
        return compte

    def compte(self, numero):
        try:
            return self._comptes[numero]
        except KeyError:
            raise CompteInconnu(f"aucun compte {numero!r}") from None

    def comptes(self):
        """Liste des comptes, dans l'ordre d'ouverture."""
        return list(self._comptes.values())

    def virement(self, numero_source, numero_destination, montant):
        """Transfère `montant` d'un compte à l'autre. Tout ou rien.

        Toutes les vérifications ont lieu AVANT le premier mouvement : si une règle est
        violée, aucun des deux comptes n'est modifié. Renvoie (operation_emise, operation_recue).
        """
        if numero_source == numero_destination:
            raise OperationInvalide("virement impossible d'un compte vers lui-même")
        source, destination = self.compte(numero_source), self.compte(numero_destination)
        montant = en_montant(montant)
        for compte in (source, destination):
            compte._verifier_ouvert()
        emise = source.emettre_virement(montant, destination.numero)  # seule étape qui peut échouer
        recue = destination.recevoir_virement(montant, source.numero)
        return emise, recue

    def total_depots(self):
        """Somme des soldes de tous les comptes."""
        return sum((c.solde for c in self._comptes.values()), start=en_montant(0, zero_autorise=True))

    def fermer_compte(self, numero):
        self.compte(numero).fermer()
