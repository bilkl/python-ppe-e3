"""Accès à l'API REST Frankfurter (https://frankfurter.dev) avec la bibliothèque requests.

L'API est gratuite et publique : aucune clé n'est nécessaire. Les taux sont ceux de la
Banque centrale européenne, publiés les jours ouvrés.

Trois familles d'erreurs, toutes dérivées de ErreurClient :
  ErreurReseau   : API injoignable, délai dépassé, connexion refusée
  ErreurApi      : l'API répond mais refuse (HTTP 4xx / 5xx, clé absente ou refusée)
  ErreurReponse  : réponse reçue mais inutilisable (pas du JSON, champ absent, valeur invalide)
Les erreurs de saisie (code de devise, date, montant) sont des ValueError.
"""

import math
import re
import time
from datetime import date

import requests

URL_PAR_DEFAUT = "https://api.frankfurter.dev"
DELAI_PAR_DEFAUT = 10  # secondes
TENTATIVES_PAR_DEFAUT = 3
CODES_RETENTABLES = {429, 500, 502, 503, 504}


class ErreurClient(Exception):
    """Racine des erreurs de communication avec l'API."""


class ErreurReseau(ErreurClient):
    pass


class ErreurApi(ErreurClient):
    def __init__(self, message, statut=None):
        super().__init__(message)
        self.statut = statut


class ErreurReponse(ErreurClient):
    pass


def valider_devise(code):
    """Renvoie le code en majuscules. Lève ValueError s'il n'a pas 3 lettres."""
    texte = str(code).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", texte):
        raise ValueError(f"code de devise invalide : {code!r} (3 lettres attendues, ex. CHF)")
    return texte


def valider_date(texte):
    """Renvoie la date (objet date). Lève ValueError si le format n'est pas AAAA-MM-JJ."""
    try:
        return date.fromisoformat(str(texte).strip())
    except ValueError:
        raise ValueError(f"date invalide : {texte!r} (format AAAA-MM-JJ)") from None


def valider_montant(valeur):
    """Renvoie le montant (float). Lève ValueError s'il n'est pas un nombre fini > 0."""
    try:
        montant = float(str(valeur).replace(",", "."))
    except ValueError:
        raise ValueError(f"montant invalide : {valeur!r}") from None
    if not math.isfinite(montant) or montant <= 0:
        raise ValueError(f"le montant doit être un nombre positif : {valeur!r}")
    return montant


def _nombre(valeur, nom):
    """Vérifie qu'une valeur de la réponse est bien un nombre fini (et pas un booléen)."""
    if isinstance(valeur, bool) or not isinstance(valeur, (int, float)) or not math.isfinite(valeur):
        raise ErreurReponse(f"valeur non numérique pour {nom} : {valeur!r}")
    return float(valeur)


class ClientTaux:
    def __init__(self, url=URL_PAR_DEFAUT, delai=DELAI_PAR_DEFAUT, tentatives=TENTATIVES_PAR_DEFAUT,
                 pause=time.sleep, session=None):
        self.url = url.rstrip("/")
        self.delai = delai
        self.tentatives = max(1, tentatives)
        self._pause = pause
        self._session = session or requests.Session()
        self._session.headers["User-Agent"] = "client-taux-ppe-e3/1.0"

    # -- requête de bas niveau ------------------------------------------------

    def _get(self, chemin, params=None):
        """GET avec délai maximal et nouvelles tentatives (réseau, 429 et 5xx).

        Attente entre tentatives : 0.5 s, 1 s, 2 s... Une erreur 4xx (hors 429) n'est
        jamais rejouée : la même requête échouerait de la même façon.
        """
        adresse = f"{self.url}{chemin}"
        derniere = None
        for essai in range(1, self.tentatives + 1):
            try:
                reponse = self._session.get(adresse, params=params, timeout=self.delai)
            except requests.exceptions.Timeout:
                derniere = ErreurReseau(f"délai dépassé ({self.delai} s) en contactant {self.url}")
            except requests.exceptions.ConnectionError:
                derniere = ErreurReseau(f"impossible de joindre {self.url} (réseau ou serveur indisponible)")
            except requests.exceptions.RequestException as erreur:
                raise ErreurReseau(f"requête impossible : {erreur}") from None
            else:
                if reponse.status_code in CODES_RETENTABLES:
                    derniere = ErreurApi(self._message(reponse), reponse.status_code)
                elif reponse.status_code >= 400:
                    raise ErreurApi(self._message(reponse), reponse.status_code)
                else:
                    return self._json(reponse)
            if essai < self.tentatives:
                self._pause(0.5 * 2 ** (essai - 1))
        raise derniere

    @staticmethod
    def _message(reponse):
        """Message d'erreur lisible pour une réponse HTTP en échec."""
        statut = reponse.status_code
        try:
            detail = reponse.json().get("message")
        except (ValueError, AttributeError):
            detail = None
        if statut in (401, 403):
            return f"accès refusé (HTTP {statut}) : clé d'API absente, invalide ou sans droit"
        if statut == 404:
            return "ressource introuvable (HTTP 404) : devise ou date inconnue, ou hors période disponible"
        if statut == 429:
            return "trop de requêtes (HTTP 429) : réessayez plus tard"
        if statut >= 500:
            return f"erreur du serveur (HTTP {statut})" + (f" : {detail}" if detail else "")
        return f"requête refusée (HTTP {statut})" + (f" : {detail}" if detail else "")

    @staticmethod
    def _json(reponse):
        try:
            donnees = reponse.json()
        except ValueError:
            raise ErreurReponse("la réponse n'est pas du JSON valide") from None
        if not isinstance(donnees, dict):
            raise ErreurReponse("la réponse JSON n'est pas un objet")
        return donnees

    # -- opérations ------------------------------------------------------------

    def devises(self):
        """Renvoie {code: nom} des devises disponibles."""
        donnees = self._get("/v1/currencies")
        if not donnees or not all(isinstance(k, str) and isinstance(v, str) for k, v in donnees.items()):
            raise ErreurReponse("liste de devises absente ou mal formée")
        return donnees

    def taux(self, base, vers=None, jour=None, montant=None):
        """Taux de change depuis `base`, vers une ou plusieurs devises.

        vers    : liste de codes (toutes les devises si None)
        jour    : date AAAA-MM-JJ (dernier cours publié si None)
        montant : si donné, les valeurs renvoyées sont celles de ce montant converti

        Renvoie {"base", "date", "montant", "valeurs": {code: nombre}}. `date` est la date
        du cours réellement utilisé : un week-end, l'API renvoie le dernier jour ouvré.
        """
        base = valider_devise(base)
        params = {"base": base}
        if vers:
            codes = [valider_devise(c) for c in vers]
            if base in codes:
                raise ValueError(f"la devise d'arrivée est la même que celle de départ ({base})")
            params["symbols"] = ",".join(codes)
        if montant is not None:
            params["amount"] = valider_montant(montant)
        chemin = "/v1/latest" if jour is None else f"/v1/{valider_date(jour).isoformat()}"
        donnees = self._get(chemin, params)
        try:
            valeurs = {c: _nombre(v, f"le taux {c}") for c, v in donnees["rates"].items()}
            resultat = {
                "base": str(donnees["base"]),
                "date": str(donnees["date"]),
                "montant": _nombre(donnees["amount"], "amount"),
                "valeurs": valeurs,
            }
        except (KeyError, AttributeError, TypeError):
            raise ErreurReponse("réponse incomplète : champs base, date, amount ou rates absents") from None
        if not valeurs:
            raise ErreurReponse("aucun taux dans la réponse")
        return resultat

    def historique(self, base, vers, debut, fin):
        """Évolution du taux base -> vers entre deux dates (jours ouvrés uniquement).

        Renvoie une liste triée de (date_iso, taux).
        """
        base, vers = valider_devise(base), valider_devise(vers)
        if base == vers:
            raise ValueError(f"la devise d'arrivée est la même que celle de départ ({base})")
        d, f = valider_date(debut), valider_date(fin)
        if d > f:
            raise ValueError(f"la date de début ({d}) est après la date de fin ({f})")
        donnees = self._get(f"/v1/{d.isoformat()}..{f.isoformat()}", {"base": base, "symbols": vers})
        try:
            serie = [(jour, _nombre(valeurs[vers], f"le taux du {jour}")) for jour, valeurs in donnees["rates"].items()]
        except (KeyError, AttributeError, TypeError):
            raise ErreurReponse("réponse incomplète : série de taux absente ou mal formée") from None
        if not serie:
            raise ErreurReponse("aucun taux publié sur cette période")
        return sorted(serie)
