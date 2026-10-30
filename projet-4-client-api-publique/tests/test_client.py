"""Tests automatisés (unittest). Lancer depuis la racine :  python3 -m unittest -v

Le code réseau réel (requests) est exercé contre un serveur local factice :
aucun accès Internet nécessaire, résultats indépendants des taux du jour.
"""

import contextlib
import io
import socket
import unittest

from client_taux import api, cli
from tests.serveur_factice import ServeurFactice

LATEST = {"amount": 1.0, "base": "CHF", "date": "2026-10-29", "rates": {"EUR": 1.0844, "USD": 1.2069}}
HISTO = {
    "amount": 1.0, "base": "CHF", "start_date": "2026-10-01", "end_date": "2026-10-05",
    "rates": {"2026-10-05": {"EUR": 1.074}, "2026-10-01": {"EUR": 1.0597}, "2026-10-02": {"EUR": 1.0777}},
}


def client(serveur, **options):
    options.setdefault("pause", lambda secondes: None)  # pas d'attente réelle entre essais
    return api.ClientTaux(serveur.url, delai=2, **options)


class TestValidation(unittest.TestCase):
    def test_devise(self):
        self.assertEqual(api.valider_devise(" chf "), "CHF")
        for mauvais in ("", "CH", "CHFF", "C1F", "€€€", None):
            with self.subTest(mauvais=mauvais):
                with self.assertRaises(ValueError):
                    api.valider_devise(mauvais)

    def test_date(self):
        self.assertEqual(api.valider_date("2026-10-29").isoformat(), "2026-10-29")
        for mauvaise in ("29/10/2026", "2026-13-01", "2026-02-30", "", "hier"):
            with self.subTest(mauvaise=mauvaise):
                with self.assertRaises(ValueError):
                    api.valider_date(mauvaise)

    def test_montant(self):
        self.assertEqual(api.valider_montant("12,5"), 12.5)
        for mauvais in ("0", "-3", "abc", "nan", "inf", ""):
            with self.subTest(mauvais=mauvais):
                with self.assertRaises(ValueError):
                    api.valider_montant(mauvais)


class TestRequetes(unittest.TestCase):
    def test_devises(self):
        with ServeurFactice({"/v1/currencies": (200, {"CHF": "Swiss Franc", "EUR": "Euro"})}) as s:
            self.assertEqual(client(s).devises(), {"CHF": "Swiss Franc", "EUR": "Euro"})

    def test_taux_envoie_les_bons_parametres(self):
        with ServeurFactice({"/v1/latest": (200, LATEST)}) as s:
            resultat = client(s).taux("chf", ["eur", "usd"])
            self.assertEqual(s.requetes, [("/v1/latest", {"base": "CHF", "symbols": "EUR,USD"})])
        self.assertEqual(resultat, {"base": "CHF", "date": "2026-10-29", "montant": 1.0,
                                    "valeurs": {"EUR": 1.0844, "USD": 1.2069}})

    def test_taux_a_une_date_et_avec_montant(self):
        with ServeurFactice({"/v1/2026-10-03": (200, {**LATEST, "date": "2026-10-02", "amount": 100.0})}) as s:
            resultat = client(s).taux("CHF", ["EUR"], jour="2026-10-03", montant=100)
            self.assertEqual(s.requetes[0][1]["amount"], "100.0")
        self.assertEqual(resultat["date"], "2026-10-02")  # le cours réel, pas la date demandée

    def test_historique_trie_par_date(self):
        with ServeurFactice({"/v1/2026-10-01..2026-10-05": (200, HISTO)}) as s:
            serie = client(s).historique("CHF", "EUR", "2026-10-01", "2026-10-05")
            self.assertEqual(s.requetes[0][1], {"base": "CHF", "symbols": "EUR"})
        self.assertEqual(serie, [("2026-10-01", 1.0597), ("2026-10-02", 1.0777), ("2026-10-05", 1.074)])

    def test_saisie_invalide_ne_fait_aucune_requete(self):
        with ServeurFactice({}) as s:
            c = client(s)
            for appel in (lambda: c.taux("EURO"), lambda: c.taux("CHF", jour="demain"),
                          lambda: c.taux("CHF", montant="-1"), lambda: c.taux("CHF", ["eur", "chf"]),
                          lambda: c.historique("CHF", "chf", "2026-10-01", "2026-10-05"), lambda: c.historique("CHF", "EUR", "2026-10-05", "2026-10-01")):
                with self.assertRaises(ValueError):
                    appel()
            self.assertEqual(s.requetes, [])


class TestErreurs(unittest.TestCase):
    def test_404_pas_de_nouvelle_tentative(self):
        with ServeurFactice({"/v1/latest": (404, {"message": "not found"})}) as s:
            with self.assertRaises(api.ErreurApi) as ctx:
                client(s).taux("CHF")
            self.assertEqual(len(s.requetes), 1)
        self.assertEqual(ctx.exception.statut, 404)
        self.assertIn("introuvable", str(ctx.exception))

    def test_401_et_403_parlent_de_cle(self):
        for statut in (401, 403):
            with self.subTest(statut=statut):
                with ServeurFactice({"/v1/latest": (statut, {"message": "nope"})}) as s:
                    with self.assertRaises(api.ErreurApi) as ctx:
                        client(s).taux("CHF")
                self.assertIn("clé d'API", str(ctx.exception))
                self.assertEqual(ctx.exception.statut, statut)

    def test_5xx_puis_succes(self):
        pauses = []
        with ServeurFactice({"/v1/latest": [(503, {"message": "x"}), (500, "boum"), (200, LATEST)]}) as s:
            resultat = client(s, pause=pauses.append).taux("CHF")
            self.assertEqual(len(s.requetes), 3)
        self.assertEqual(resultat["date"], "2026-10-29")
        self.assertEqual(pauses, [0.5, 1.0])  # attente croissante

    def test_5xx_persistant_abandonne_apres_les_tentatives(self):
        with ServeurFactice({"/v1/latest": (500, {"message": "panne"})}) as s:
            with self.assertRaises(api.ErreurApi) as ctx:
                client(s, tentatives=3).taux("CHF")
            self.assertEqual(len(s.requetes), 3)
        self.assertEqual(ctx.exception.statut, 500)
        self.assertIn("panne", str(ctx.exception))

    def test_429_est_rejoue(self):
        with ServeurFactice({"/v1/latest": [(429, {}), (200, LATEST)]}) as s:
            client(s).taux("CHF")
            self.assertEqual(len(s.requetes), 2)

    def test_delai_depasse(self):
        with ServeurFactice({"/v1/latest": (200, LATEST, 1.0)}) as s:
            c = api.ClientTaux(s.url, delai=0.2, tentatives=2, pause=lambda _: None)
            with self.assertRaises(api.ErreurReseau) as ctx:
                c.taux("CHF")
        self.assertIn("délai dépassé", str(ctx.exception))

    def test_serveur_injoignable(self):
        with socket.socket() as sock:  # port libre, puis fermé : personne n'écoute
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        c = api.ClientTaux(f"http://127.0.0.1:{port}", delai=1, tentatives=2, pause=lambda _: None)
        with self.assertRaises(api.ErreurReseau) as ctx:
            c.devises()
        self.assertIn("impossible de joindre", str(ctx.exception))

    def test_reponses_inutilisables(self):
        cas = {
            "pas du json": (200, "<html>maintenance</html>"),
            "liste au lieu d'objet": (200, [1, 2]),
            "sans rates": (200, {"amount": 1.0, "base": "CHF", "date": "2026-10-29"}),
            "rates vide": (200, {**LATEST, "rates": {}}),
            "taux texte": (200, {**LATEST, "rates": {"EUR": "beaucoup"}}),
            "taux booléen": (200, {**LATEST, "rates": {"EUR": True}}),
            "rates pas un objet": (200, {**LATEST, "rates": [1]}),
            "sans date": (200, {k: v for k, v in LATEST.items() if k != "date"}),
        }
        for nom, reponse in cas.items():
            with self.subTest(nom):
                with ServeurFactice({"/v1/latest": reponse}) as s:
                    with self.assertRaises(api.ErreurReponse):
                        client(s).taux("CHF")

    def test_devises_et_historique_mal_formes(self):
        with ServeurFactice({"/v1/currencies": (200, {"CHF": 3}),
                             "/v1/2026-10-01..2026-10-05": (200, {**HISTO, "rates": {}})}) as s:
            with self.assertRaises(api.ErreurReponse):
                client(s).devises()
            with self.assertRaises(api.ErreurReponse):
                client(s).historique("CHF", "EUR", "2026-10-01", "2026-10-05")


class TestCli(unittest.TestCase):
    def lancer(self, serveur, *args):
        sortie, erreur = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
            try:
                code = cli.main(["--url", serveur.url, "--tentatives", "1", *args])
            except SystemExit as e:
                code = e.code
        return code, sortie.getvalue(), erreur.getvalue()

    def test_convertir(self):
        reponse = {"amount": 100.0, "base": "CHF", "date": "2026-10-29", "rates": {"EUR": 108.44}}
        with ServeurFactice({"/v1/latest": (200, reponse)}) as s:
            code, sortie, _ = self.lancer(s, "convertir", "100", "chf", "eur")
        self.assertEqual(code, 0)
        self.assertIn("100.00 CHF = 108.44 EUR", sortie)
        self.assertIn("taux : 1 CHF = 1.0844 EUR", sortie)

    def test_taux_signale_le_jour_ferie(self):
        with ServeurFactice({"/v1/2026-10-03": (200, {**LATEST, "date": "2026-10-02"})}) as s:
            code, sortie, _ = self.lancer(s, "taux", "CHF", "EUR", "USD", "--date", "2026-10-03")
        self.assertEqual(code, 0)
        self.assertIn("aucun cours publié le 2026-10-03", sortie)
        self.assertIn("1.0844", sortie)

    def test_historique_resume(self):
        with ServeurFactice({"/v1/2026-10-01..2026-10-05": (200, HISTO)}) as s:
            code, sortie, _ = self.lancer(s, "historique", "CHF", "EUR", "--du", "2026-10-01", "--au", "2026-10-05")
        self.assertEqual(code, 0)
        self.assertIn("minimum  : 1.0597", sortie)
        self.assertIn("maximum : 1.0777", sortie)
        self.assertIn("variation : +1.35 %", sortie)  # (1.074 - 1.0597) / 1.0597

    def test_devises_filtre(self):
        with ServeurFactice({"/v1/currencies": (200, {"CHF": "Swiss Franc", "EUR": "Euro", "GBP": "British Pound"})}) as s:
            _, sortie, _ = self.lancer(s, "devises", "--filtre", "pound")
            self.assertIn("GBP", sortie)
            self.assertNotIn("EUR", sortie)
            _, sortie, _ = self.lancer(s, "devises", "--filtre", "zzz")
            self.assertIn("Aucune devise", sortie)

    def test_erreurs_donnent_code_1_et_message(self):
        with ServeurFactice({"/v1/latest": (503, {"message": "x"})}) as s:
            code, _, erreur = self.lancer(s, "taux", "CHF")
            self.assertEqual((code, "erreur du serveur" in erreur), (1, True))
            code, _, erreur = self.lancer(s, "convertir", "abc", "CHF", "EUR")
            self.assertEqual((code, "Erreur de saisie" in erreur), (1, True))
            code, _, erreur = self.lancer(s, "taux", "EURO")
            self.assertEqual((code, "Erreur de saisie" in erreur), (1, True))
            self.assertEqual(len(s.requetes), 1)  # seules les requêtes valides partent

    def test_usage_incorrect(self):
        with ServeurFactice({}) as s:
            self.assertEqual(self.lancer(s)[0], 2)
            self.assertEqual(self.lancer(s, "historique", "CHF", "EUR")[0], 2)
            self.assertEqual(self.lancer(s, "inconnue")[0], 2)

    def test_formatage(self):
        self.assertEqual(cli.formater_nombre(1234567.5), "1'234'567.50")
        self.assertEqual(cli.formater_nombre(1.08444, 4), "1.0844")


if __name__ == "__main__":
    unittest.main()
