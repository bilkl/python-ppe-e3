"""Tests automatisés (unittest). Lancer depuis la racine :  python3 -m unittest -v

Le petit jeu de données ci-dessous est calculé à la main :
  V1  2026-07-10  Souris   Accessoires  Vaud    2 x 10.00 = 20.00
  V2  2026-07-20  Écran    Informatique Genève  1 x 100.50 = 100.50
  V3  2026-08-05  Souris   Accessoires  Genève  3 x 10.00 = 30.00
  V4  2026-08-06  Câble    Accessoires  Vaud    10 x 1.05 = 10.50
  CA total = 161.00 ; 4 ventes ; moyenne = 40.25 ; quantité = 16
  produit le plus vendu = Câble (10) ; plus gros CA = Écran (100.50)
"""

import contextlib
import io
import os
import tempfile
import unittest
from datetime import date
from decimal import Decimal

from analyse_ventes import cli, export, lecture, stats

D = Decimal
EN_TETE = "date;id_vente;produit;categorie;region;quantite;prix_unitaire\n"
CSV_PETIT = EN_TETE + (
    "2026-07-10;V1;Souris;Accessoires;Vaud;2;10.00\n"
    "2026-07-20;V2;Écran;Informatique;Genève;1;100.50\n"
    "2026-08-05;V3;Souris;Accessoires;Genève;3;10.00\n"
    "2026-08-06;V4;Câble;Accessoires;Vaud;10;1.05\n"
)


def vente(jour="2026-07-01", id_vente="X", produit="P", categorie="C", region="R", quantite=1, prix="1.00"):
    return lecture.Vente(date.fromisoformat(jour), id_vente, produit, categorie, region, quantite, D(prix))


class AvecFichier(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier.cleanup)

    def ecrire(self, contenu, nom="v.csv", encodage="utf-8"):
        chemin = os.path.join(self.dossier.name, nom)
        with open(chemin, "w", encoding=encodage, newline="") as f:
            f.write(contenu)
        return chemin


class TestLecture(AvecFichier):
    def test_lecture_valide(self):
        ventes, rejets, total = lecture.lire_ventes(self.ecrire(CSV_PETIT))
        self.assertEqual((len(ventes), rejets, total), (4, [], 4))
        self.assertEqual(ventes[1].produit, "Écran")
        self.assertEqual(ventes[1].montant, D("100.50"))
        self.assertEqual(ventes[3].mois, "2026-08")

    def test_delimiteur_virgule_et_bom(self):
        contenu = "﻿" + CSV_PETIT.replace(";", ",")
        ventes, rejets, _ = lecture.lire_ventes(self.ecrire(contenu))
        self.assertEqual((len(ventes), rejets), (4, []))

    def test_champ_entre_guillemets_avec_delimiteur(self):
        contenu = EN_TETE + '2026-07-01;V1;"Écran 27"" ; noir";Info;Vaud;1;389.00\n'
        ventes, _, _ = lecture.lire_ventes(self.ecrire(contenu))
        self.assertEqual(ventes[0].produit, 'Écran 27" ; noir')

    def test_lignes_vides_ignorees(self):
        ventes, rejets, total = lecture.lire_ventes(self.ecrire(CSV_PETIT + "\n;;;;;;\n"))
        self.assertEqual((len(ventes), rejets, total), (4, [], 4))

    def test_virgule_decimale_acceptee(self):
        contenu = EN_TETE + "2026-07-01;V1;P;C;R;1;12,50\n"
        self.assertEqual(lecture.lire_ventes(self.ecrire(contenu))[0][0].prix_unitaire, D("12.50"))

    def test_rejets_avec_numero_de_ligne(self):
        contenu = EN_TETE + (
            "2026-07-01;A;P;C;R;1;1.00\n"        # ligne 2 : valide
            "2026-07-01;B;P;C;R;abc;1.00\n"      # ligne 3
            "01/07/2026;C;P;C;R;1;1.00\n"        # ligne 4
            "2026-07-01;D;P;C;R;0;1.00\n"        # ligne 5
            "2026-07-01;E;;C;R;1;1.00\n"         # ligne 6
            "2026-07-01;A;P;C;R;1;1.00\n"        # ligne 7 : doublon
            "2026-07-01;G;P;C;R;1;nan\n"         # ligne 8
            "2026-07-01;H;P;C;R;1;-5\n"          # ligne 9
            "2026-07-01;I;P;C;R;1\n"             # ligne 10
            "2026-13-01;J;P;C;R;1;1.00\n"        # ligne 11 : mois 13
        )
        ventes, rejets, total = lecture.lire_ventes(self.ecrire(contenu))
        self.assertEqual((len(ventes), total), (1, 10))
        self.assertEqual([r.ligne for r in rejets], [3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.assertIn("quantité invalide", rejets[0].raison)
        self.assertIn("date invalide", rejets[1].raison)
        self.assertIn("non positive", rejets[2].raison)
        self.assertIn("produit vide", rejets[3].raison)
        self.assertIn("en double", rejets[4].raison)
        self.assertIn("prix invalide", rejets[5].raison)
        self.assertIn("non positif", rejets[6].raison)
        self.assertIn("6 colonnes au lieu de 7", rejets[7].raison)

    def test_erreurs_fatales(self):
        with self.assertRaises(lecture.ErreurLecture):
            lecture.lire_ventes(os.path.join(self.dossier.name, "absent.csv"))
        with self.assertRaises(lecture.ErreurLecture):
            lecture.lire_ventes(self.ecrire(""))
        with self.assertRaises(lecture.ErreurLecture) as ctx:
            lecture.lire_ventes(self.ecrire("date;produit\n2026-07-01;x\n"))
        self.assertIn("colonnes manquantes", str(ctx.exception))
        with self.assertRaises(lecture.ErreurLecture) as ctx:
            lecture.lire_ventes(self.ecrire(CSV_PETIT, encodage="latin-1"))
        self.assertIn("UTF-8", str(ctx.exception))

    def test_entete_seul(self):
        self.assertEqual(lecture.lire_ventes(self.ecrire(EN_TETE)), ([], [], 0))


class TestStats(AvecFichier):
    def setUp(self):
        super().setUp()
        self.ventes = lecture.lire_ventes(self.ecrire(CSV_PETIT))[0]

    def test_indicateurs(self):
        self.assertEqual(stats.chiffre_affaires(self.ventes), D("161.00"))
        self.assertEqual(stats.moyenne_par_vente(self.ventes), D("40.25"))
        self.assertEqual(stats.quantite_totale(self.ventes), 16)

    def test_precision_decimale(self):
        # 0.1 + 0.2 en flottant vaut 0.30000000000000004 ; en Decimal : exactement 0.30
        ventes = [vente(quantite=1, prix="0.10"), vente(id_vente="Y", quantite=1, prix="0.20")]
        self.assertEqual(stats.chiffre_affaires(ventes), D("0.30"))

    def test_moyenne_arrondie_demi_vers_le_haut(self):
        ventes = [vente(prix="0.01"), vente(id_vente="Y", prix="0.02")]  # 0.03 / 2 = 0.015
        self.assertEqual(stats.moyenne_par_vente(ventes), D("0.02"))

    def test_produits_le_plus_vendu_et_plus_gros_ca(self):
        self.assertEqual(stats.produit_le_plus_vendu(self.ventes)["cle"], "Câble")
        self.assertEqual(stats.produit_plus_gros_ca(self.ventes)["cle"], "Écran")

    def test_egalite_departagee_par_ca_puis_nom(self):
        ventes = [vente(produit="B", quantite=2, prix="1"), vente(id_vente="Y", produit="A", quantite=2, prix="5")]
        self.assertEqual(stats.produit_le_plus_vendu(ventes)["cle"], "A")  # même quantité, plus fort CA
        ventes = [vente(produit="B", quantite=2), vente(id_vente="Y", produit="A", quantite=2)]
        self.assertEqual(stats.produit_le_plus_vendu(ventes)["cle"], "A")  # tout égal : ordre alphabétique

    def test_grouper(self):
        par_mois = {g["cle"]: g for g in stats.grouper(self.ventes, "mois")}
        self.assertEqual(par_mois["2026-07"]["ca"], D("120.50"))
        self.assertEqual(par_mois["2026-08"]["ca"], D("40.50"))
        self.assertEqual(par_mois["2026-08"]["ventes"], 2)
        par_region = {g["cle"]: g["ca"] for g in stats.grouper(self.ventes, "region")}
        self.assertEqual(par_region, {"Vaud": D("30.50"), "Genève": D("130.50")})
        with self.assertRaises(ValueError):
            stats.grouper(self.ventes, "couleur")

    def test_trier(self):
        groupes = stats.grouper(self.ventes, "produit")
        self.assertEqual([g["cle"] for g in stats.trier(groupes, "ca")], ["Écran", "Souris", "Câble"])
        self.assertEqual([g["cle"] for g in stats.trier(groupes, "quantite")], ["Câble", "Souris", "Écran"])
        self.assertEqual([g["cle"] for g in stats.trier(groupes, "nom")], ["Câble", "Écran", "Souris"])  # Écran se range avec les E
        with self.assertRaises(ValueError):
            stats.trier(groupes, "prix")

    def test_filtrer(self):
        self.assertEqual(len(stats.filtrer(self.ventes)), 4)
        self.assertEqual(len(stats.filtrer(self.ventes, mois="2026-08")), 2)
        self.assertEqual(len(stats.filtrer(self.ventes, region="genève")), 2)  # sans casse
        self.assertEqual(len(stats.filtrer(self.ventes, mois="2026-08", region="Vaud", categorie="Accessoires")), 1)
        self.assertEqual(stats.filtrer(self.ventes, mois="2025-01"), [])

    def test_aucune_vente(self):
        with self.assertRaises(ValueError):
            stats.moyenne_par_vente([])
        with self.assertRaises(ValueError):
            stats.produit_le_plus_vendu([])
        self.assertEqual(stats.chiffre_affaires([]), D(0))


class TestExport(AvecFichier):
    def test_chf(self):
        self.assertEqual(export.chf(D("12345.6")), "CHF 12'345.60")
        self.assertEqual(export.chf(D("0")), "CHF 0.00")
        self.assertEqual(export.chf(D("1234567.891")), "CHF 1'234'567.89")

    def test_rapport_contient_les_chiffres_attendus(self):
        ventes, rejets, total = lecture.lire_ventes(self.ecrire(CSV_PETIT))
        texte = export.rapport("v.csv", ventes, rejets, total, {})
        for attendu in ("CHF 161.00", "CHF 40.25", "Câble (10 unités", "Écran (CHF 100.50", "valides : 4   rejetées : 0"):
            self.assertIn(attendu, texte)

    def test_rapport_sans_vente(self):
        texte = export.rapport("v.csv", [], [], 0, {"mois": "2025-01"})
        self.assertIn("Aucune vente ne correspond", texte)
        self.assertIn("mois = 2025-01", texte)

    def test_unite_au_singulier(self):
        self.assertEqual(export.unites(1), "1 unité")
        self.assertEqual(export.unites(2), "2 unités")

    def test_ecrire_synthese(self):
        ventes = lecture.lire_ventes(self.ecrire(CSV_PETIT))[0]
        dossier = os.path.join(self.dossier.name, "sortie", "sous")
        chemins = export.ecrire_synthese(dossier, "texte\n", ventes)
        self.assertEqual([os.path.basename(c) for c in chemins], ["synthese.txt", "synthese-produits.csv"])
        with open(chemins[1], encoding="utf-8") as f:
            lignes = f.read().splitlines()
        self.assertEqual(lignes[0], "produit;nb_ventes;quantite;chiffre_affaires_chf")
        self.assertEqual(lignes[1], "Écran;1;1;100.50")
        self.assertEqual(len(lignes), 4)


class TestCli(AvecFichier):
    def lancer(self, *args):
        sortie, erreur = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreur):
            try:
                code = cli.main(list(args))
            except SystemExit as e:
                code = e.code
        return code, sortie.getvalue(), erreur.getvalue()

    def test_analyse_complete(self):
        chemin = self.ecrire(CSV_PETIT)
        code, sortie, _ = self.lancer(chemin)
        self.assertEqual(code, 0)
        self.assertIn("CHF 161.00", sortie)

    def test_filtre_et_top(self):
        chemin = self.ecrire(CSV_PETIT)
        _, sortie, _ = self.lancer(chemin, "--mois", "2026-08", "--tri", "quantite", "--top", "1")
        self.assertIn("CHF 40.50", sortie)
        self.assertIn("mois = 2026-08", sortie)
        self.assertIn("1 premiers", sortie)

    def test_filtre_sans_resultat_code_0(self):
        code, sortie, _ = self.lancer(self.ecrire(CSV_PETIT), "--region", "Mars")
        self.assertEqual(code, 0)
        self.assertIn("Aucune vente ne correspond", sortie)

    def test_sortie_ecrit_les_fichiers(self):
        dossier = os.path.join(self.dossier.name, "res")
        code, sortie, _ = self.lancer(self.ecrire(CSV_PETIT), "--sortie", dossier)
        self.assertEqual(code, 0)
        self.assertEqual(sorted(os.listdir(dossier)), ["synthese-produits.csv", "synthese.txt"])
        with open(os.path.join(dossier, "synthese.txt"), encoding="utf-8") as f:
            self.assertIn("CHF 161.00", f.read())

    def test_erreurs(self):
        code, _, erreur = self.lancer(os.path.join(self.dossier.name, "absent.csv"))
        self.assertEqual((code, "introuvable" in erreur), (1, True))
        self.assertEqual(self.lancer(self.ecrire(CSV_PETIT), "--mois", "2026-13")[0], 2)
        self.assertEqual(self.lancer(self.ecrire(CSV_PETIT), "--mois", "juillet")[0], 2)
        self.assertEqual(self.lancer(self.ecrire(CSV_PETIT), "--top", "0")[0], 2)
        self.assertEqual(self.lancer(self.ecrire(CSV_PETIT), "--tri", "prix")[0], 2)
        self.assertEqual(self.lancer()[0], 2)

    def test_sortie_impossible(self):
        fichier = self.ecrire("x", "occupe")
        code, _, erreur = self.lancer(self.ecrire(CSV_PETIT), "--sortie", os.path.join(fichier, "sous"))
        self.assertEqual(code, 1)
        self.assertIn("écriture impossible", erreur)

    def test_jeu_de_donnees_du_depot(self):
        racine = os.path.join(os.path.dirname(__file__), "..", "data")
        code, sortie, _ = self.lancer(os.path.join(racine, "ventes_t3_2026.csv"))
        self.assertEqual(code, 0)
        self.assertIn("rejetées : 0", sortie)
        code, sortie, _ = self.lancer(os.path.join(racine, "ventes_avec_erreurs.csv"))
        self.assertEqual(code, 0)
        self.assertIn("valides : 3   rejetées : 7", sortie)


if __name__ == "__main__":
    unittest.main()
