"""Tests automatisés (unittest, bibliothèque standard).

Lancer depuis la racine du projet :  python3 -m unittest -v
"""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import calculatrice as c  # noqa: E402


class TestOperations(unittest.TestCase):
    def test_basiques(self):
        self.assertEqual(c.addition(2, 3), 5)
        self.assertEqual(c.soustraction(2, 5), -3)
        self.assertEqual(c.multiplication(4, 2.5), 10)
        self.assertEqual(c.division(9, 3), 3)
        self.assertEqual(c.puissance(2, 10), 1024)
        self.assertEqual(c.modulo(10, 3), 1)

    def test_division_par_zero(self):
        with self.assertRaises(ValueError):
            c.division(1, 0)

    def test_modulo_par_zero(self):
        with self.assertRaises(ValueError):
            c.modulo(1, 0)

    def test_puissance_cas_invalides(self):
        with self.assertRaises(ValueError):
            c.puissance(0, -1)
        with self.assertRaises(ValueError):
            c.puissance(-8, 0.5)
        with self.assertRaises(ValueError):
            c.puissance(10.0, 10000)


class TestConversions(unittest.TestCase):
    def test_temperature(self):
        self.assertAlmostEqual(c.convertir_temperature(100, "C", "F"), 212)
        self.assertAlmostEqual(c.convertir_temperature(32, "F", "C"), 0)
        self.assertAlmostEqual(c.convertir_temperature(0, "C", "K"), 273.15)
        self.assertAlmostEqual(c.convertir_temperature(-40, "C", "F"), -40)
        self.assertAlmostEqual(c.convertir_temperature(20, "c", "c"), 20)

    def test_temperature_zero_absolu(self):
        with self.assertRaises(ValueError):
            c.convertir_temperature(-300, "C", "K")
        with self.assertRaises(ValueError):
            c.convertir_temperature(-1, "K", "C")
        self.assertAlmostEqual(c.convertir_temperature(0, "K", "C"), -273.15)

    def test_temperature_unite_inconnue(self):
        with self.assertRaises(ValueError):
            c.convertir_temperature(1, "X", "C")

    def test_longueur(self):
        self.assertAlmostEqual(c.convertir_longueur(1, "km", "m"), 1000)
        self.assertAlmostEqual(c.convertir_longueur(1, "mi", "km"), 1.609344)
        self.assertAlmostEqual(c.convertir_longueur(12, "in", "ft"), 1)
        self.assertAlmostEqual(c.convertir_longueur(0, "m", "cm"), 0)

    def test_longueur_invalide(self):
        with self.assertRaises(ValueError):
            c.convertir_longueur(-1, "m", "km")
        with self.assertRaises(ValueError):
            c.convertir_longueur(1, "m", "parsec")

    def test_poids(self):
        self.assertAlmostEqual(c.convertir_poids(1, "kg", "g"), 1000)
        self.assertAlmostEqual(c.convertir_poids(1, "lb", "kg"), 0.45359237)
        self.assertAlmostEqual(c.convertir_poids(16, "oz", "lb"), 1, places=6)

    def test_poids_invalide(self):
        with self.assertRaises(ValueError):
            c.convertir_poids(-5, "kg", "g")
        with self.assertRaises(ValueError):
            c.convertir_poids(1, "kg", "stone")


class TestSaisie(unittest.TestCase):
    def test_parse_nombre_valide(self):
        self.assertEqual(c.parse_nombre("12"), 12.0)
        self.assertEqual(c.parse_nombre(" 3,5 "), 3.5)
        self.assertEqual(c.parse_nombre("-0.25"), -0.25)

    def test_parse_nombre_invalide(self):
        for texte in ("", "   ", "abc", "1,2,3", "nan", "inf", "-inf", "1e999"):
            with self.subTest(texte=texte):
                with self.assertRaises(ValueError):
                    c.parse_nombre(texte)

    def test_lire_nombre_redemande(self):
        reponses = iter(["abc", "", "4,5"])
        with redirect_stdout(io.StringIO()) as sortie:
            valeur = c.lire_nombre("? ", lambda _: next(reponses))
        self.assertEqual(valeur, 4.5)
        self.assertEqual(sortie.getvalue().count("Saisie invalide"), 2)

    def test_lire_unite_redemande(self):
        reponses = iter(["xx", "KM"])
        with redirect_stdout(io.StringIO()):
            unite = c.lire_unite("? ", ("m", "km"), lambda _: next(reponses))
        self.assertEqual(unite, "km")

    def test_formater(self):
        self.assertEqual(c.formater(5.0), "5")
        self.assertEqual(c.formater(1 / 3), "0.333333")
        self.assertEqual(c.formater(-0.0), "0")
        self.assertEqual(c.formater(0.0000001), "0")


class TestMenu(unittest.TestCase):
    def lancer(self, *reponses):
        it = iter(reponses)
        with redirect_stdout(io.StringIO()) as sortie:
            c.main(lambda _: next(it))
        return sortie.getvalue()

    def test_addition_puis_quitter(self):
        sortie = self.lancer("1", "2", "3", "0")
        self.assertIn("2 + 3 = 5", sortie)
        self.assertIn("Au revoir", sortie)

    def test_division_par_zero_ne_plante_pas(self):
        sortie = self.lancer("4", "5", "0", "0")
        self.assertIn("division par zéro impossible", sortie)

    def test_choix_invalide(self):
        sortie = self.lancer("zzz", "0")
        self.assertIn("Choix invalide", sortie)

    def test_conversion_temperature(self):
        sortie = self.lancer("7", "100", "C", "F", "0")
        self.assertIn("100 C = 212 F", sortie)


if __name__ == "__main__":
    unittest.main()
