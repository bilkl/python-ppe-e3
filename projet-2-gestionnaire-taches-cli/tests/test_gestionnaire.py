"""Tests automatisés (unittest). Lancer depuis la racine :  python3 -m unittest -v"""

import contextlib
import io
import json
import os
import tempfile
import unittest

from gestionnaire import cli, modele, stockage

H = "2026-10-28T09:00:00"


class TestModele(unittest.TestCase):
    def test_ajouter_attribue_des_ids_croissants(self):
        taches = []
        a = modele.ajouter(taches, "Un", horodatage=H)
        b = modele.ajouter(taches, "Deux", "haute", horodatage=H)
        self.assertEqual((a["id"], b["id"]), (1, 2))
        self.assertEqual(b["priorite"], "haute")
        self.assertEqual(a["statut"], "a_faire")
        self.assertIsNone(a["terminee_le"])

    def test_id_suivant_apres_suppression_du_premier(self):
        taches = []
        modele.ajouter(taches, "Un")
        modele.ajouter(taches, "Deux")
        modele.supprimer(taches, 1)
        self.assertEqual(modele.ajouter(taches, "Trois")["id"], 3)

    def test_titre_nettoye(self):
        self.assertEqual(modele.ajouter([], "  deux   mots ")["titre"], "deux mots")

    def test_titre_invalide(self):
        for titre in ("", "   ", "x" * (modele.TITRE_MAX + 1)):
            with self.subTest(titre=titre[:10]):
                with self.assertRaises(ValueError):
                    modele.ajouter([], titre)

    def test_priorite_inconnue(self):
        with self.assertRaises(ValueError):
            modele.ajouter([], "x", "urgente")

    def test_terminer(self):
        taches = []
        modele.ajouter(taches, "x")
        t = modele.terminer(taches, 1, horodatage=H)
        self.assertEqual((t["statut"], t["terminee_le"]), ("terminee", H))

    def test_terminer_deux_fois_ou_inconnue(self):
        taches = []
        modele.ajouter(taches, "x")
        modele.terminer(taches, 1)
        with self.assertRaises(ValueError):
            modele.terminer(taches, 1)
        with self.assertRaises(ValueError):
            modele.terminer(taches, 99)

    def test_supprimer(self):
        taches = []
        modele.ajouter(taches, "x")
        modele.supprimer(taches, 1)
        self.assertEqual(taches, [])
        with self.assertRaises(ValueError):
            modele.supprimer(taches, 1)

    def test_lister_tri_et_filtres(self):
        taches = []
        modele.ajouter(taches, "basse", "basse")
        modele.ajouter(taches, "haute", "haute")
        modele.ajouter(taches, "normale")
        modele.terminer(taches, 2)
        self.assertEqual([t["titre"] for t in modele.lister(taches)], ["haute", "normale", "basse"])
        self.assertEqual([t["id"] for t in modele.lister(taches, statut="a_faire")], [3, 1])
        self.assertEqual([t["id"] for t in modele.lister(taches, priorite="haute")], [2])
        with self.assertRaises(ValueError):
            modele.lister(taches, statut="nimporte")

    def test_valider_tache(self):
        valide = {"id": 1, "titre": "x", "statut": "a_faire", "priorite": "basse"}
        self.assertIs(modele.valider_tache(valide), valide)
        for mauvais in (
            "texte", {}, {**valide, "id": "1"}, {**valide, "id": True}, {**valide, "titre": " "},
            {**valide, "statut": "?"}, {**valide, "priorite": "?"},
        ):
            with self.subTest(mauvais=mauvais):
                with self.assertRaises(ValueError):
                    modele.valider_tache(mauvais)


class TestStockage(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier.cleanup)
        self.chemin = os.path.join(self.dossier.name, "taches.json")

    def ecrire(self, texte):
        with open(self.chemin, "w", encoding="utf-8") as f:
            f.write(texte)

    def test_fichier_absent_ou_vide(self):
        self.assertEqual(stockage.charger(self.chemin), [])
        self.ecrire("")
        self.assertEqual(stockage.charger(self.chemin), [])

    def test_aller_retour_avec_accents(self):
        taches = []
        modele.ajouter(taches, "Réviser l'étape « 3 » ✓", "haute", horodatage=H)
        stockage.sauvegarder(self.chemin, taches)
        self.assertEqual(stockage.charger(self.chemin), taches)
        with open(self.chemin, encoding="utf-8") as f:
            self.assertIn("Réviser", f.read())

    def test_sauvegarde_ne_laisse_pas_de_temporaire(self):
        stockage.sauvegarder(self.chemin, [])
        self.assertEqual(os.listdir(self.dossier.name), ["taches.json"])

    def test_sauvegarde_cree_le_dossier(self):
        chemin = os.path.join(self.dossier.name, "a", "b", "t.json")
        stockage.sauvegarder(chemin, [])
        self.assertTrue(os.path.exists(chemin))

    def test_fichiers_invalides_refuses_sans_etre_modifies(self):
        cas = {
            "json casse": "{pas du json",
            "racine liste": "[]",
            "sans cle taches": '{"version": 1}',
            "tache invalide": '{"taches": [{"id": 1}]}',
            "id en double": json.dumps({"taches": [
                {"id": 1, "titre": "a", "statut": "a_faire", "priorite": "basse"},
                {"id": 1, "titre": "b", "statut": "a_faire", "priorite": "basse"},
            ]}),
        }
        for nom, contenu in cas.items():
            with self.subTest(nom):
                self.ecrire(contenu)
                with self.assertRaises(stockage.ErreurStockage):
                    stockage.charger(self.chemin)
                with open(self.chemin, encoding="utf-8") as f:
                    self.assertEqual(f.read(), contenu)

    def test_chemin_fichier_priorites(self):
        ancien = os.environ.pop("TACHES_FICHIER", None)
        self.addCleanup(lambda: os.environ.__setitem__("TACHES_FICHIER", ancien) if ancien else None)
        self.assertEqual(stockage.chemin_fichier(), "taches.json")
        os.environ["TACHES_FICHIER"] = "env.json"
        self.addCleanup(os.environ.pop, "TACHES_FICHIER", None)
        self.assertEqual(stockage.chemin_fichier(), "env.json")
        self.assertEqual(stockage.chemin_fichier("opt.json"), "opt.json")


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return f.read()


class TestCli(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier.cleanup)
        self.chemin = os.path.join(self.dossier.name, "t.json")

    def lancer(self, *args):
        sortie, erreur = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
            try:
                code = cli.main(["-f", self.chemin, *args])
            except SystemExit as e:  # argparse
                code = e.code
        return code, sortie.getvalue(), erreur.getvalue()

    def test_persistance_entre_deux_executions(self):
        self.assertEqual(self.lancer("ajouter", "Acheter du pain", "-p", "haute")[0], 0)
        self.assertEqual(self.lancer("ajouter", "Appeler Paul")[0], 0)
        self.assertEqual(self.lancer("terminer", "2")[0], 0)
        code, sortie, _ = self.lancer("lister")  # nouvelle « exécution » : relit le fichier
        self.assertEqual(code, 0)
        self.assertIn("Acheter du pain", sortie)
        self.assertIn("[x]", sortie)
        self.assertIn("2 tâche(s), 1 à faire", sortie)

    def test_liste_vide(self):
        self.assertIn("Aucune tâche", self.lancer("lister")[1])

    def test_erreurs_renvoient_1_et_ne_modifient_pas_le_fichier(self):
        self.lancer("ajouter", "x")
        avant = lire(self.chemin)
        for args in (("terminer", "9"), ("supprimer", "9"), ("ajouter", "  ")):
            with self.subTest(args):
                code, _, erreur = self.lancer(*args)
                self.assertEqual(code, 1)
                self.assertIn("Erreur", erreur)
        self.assertEqual(lire(self.chemin), avant)

    def test_fichier_corrompu_non_ecrase(self):
        with open(self.chemin, "w", encoding="utf-8") as f:
            f.write("{casse")
        code, _, erreur = self.lancer("ajouter", "x")
        self.assertEqual(code, 1)
        self.assertIn("pas du JSON valide", erreur)
        self.assertEqual(lire(self.chemin), "{casse")

    def test_arguments_invalides_argparse(self):
        self.assertEqual(self.lancer("terminer", "abc")[0], 2)
        self.assertEqual(self.lancer("ajouter", "x", "-p", "urgente")[0], 2)
        self.assertEqual(self.lancer()[0], 2)


if __name__ == "__main__":
    unittest.main()
