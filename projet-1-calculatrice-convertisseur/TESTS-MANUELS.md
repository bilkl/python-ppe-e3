# Jeu de tests manuels

Programme testé : [`calculatrice.py`](./calculatrice.py), Python 3.12.3, Linux.
Date d'exécution : 26 octobre 2026.

**Méthode.** Chaque cas lance le programme réel, saisit les entrées indiquées
dans l'ordre (menu, puis valeurs) et relève la ligne de résultat. Les saisies
sont envoyées à l'entrée standard du programme (`printf ... | python3
calculatrice.py`) ; les cas 1, 4, 11, 15, 18, 19, 20, 21 et 22 ont aussi été
tapés au clavier dans le terminal des [captures d'écran](./README.md#captures-décran).
La colonne « Observé » reprend la sortie réelle.

Légende des entrées : `→` sépare les saisies successives.

## A. Calculs

| # | Entrées | Attendu | Observé | OK |
| --- | --- | --- | --- | --- |
| 1 | `1` → `12,5` → `7.5` | `12.5 + 7.5 = 20` (virgule acceptée) | `12.5 + 7.5 = 20` | oui |
| 2 | `2` → `10` → `25` | `10 - 25 = -15` | `10 - 25 = -15` | oui |
| 3 | `3` → `-4` → `2.5` | `-4 * 2.5 = -10` | `-4 * 2.5 = -10` | oui |
| 4 | `4` → `10` → `0` | erreur, pas de plantage | `! Erreur : division par zéro impossible.` | oui |
| 5 | `5` → `2` → `10` | `2 ^ 10 = 1024` | `2 ^ 10 = 1024` | oui |
| 6 | `5` → `0` → `-1` | erreur | `! Erreur : 0 ne peut pas être élevé à une puissance négative.` | oui |
| 7 | `5` → `-8` → `0.5` | erreur (résultat complexe) | `! Erreur : résultat non réel (base négative et exposant décimal).` | oui |
| 8 | `6` → `10` → `3` | `10 % 3 = 1` | `10 % 3 = 1` | oui |
| 9 | `6` → `5` → `0` | erreur | `! Erreur : modulo par zéro impossible.` | oui |
| 10 | `1` → `0,1` → `0,2` | `0.3` (pas `0.30000000000000004`) | `0.1 + 0.2 = 0.3` | oui |

## B. Conversions

| # | Entrées | Attendu | Observé | OK |
| --- | --- | --- | --- | --- |
| 11 | `7` → `100` → `C` → `F` | `212 F` | `100 C = 212 F` | oui |
| 12 | `7` → `-40` → `C` → `F` | `-40 F` (point d'égalité) | `-40 C = -40 F` | oui |
| 13 | `7` → `0` → `K` → `C` | `-273.15 C` (zéro absolu accepté) | `0 K = -273.15 C` | oui |
| 14 | `8` → `1` → `mi` → `km` | `1.609344 km` | `1 mi = 1.609344 km` | oui |
| 15 | `8` → `5` → `km` → `mi` | `3.106856 mi` | `5 km = 3.106856 mi` | oui |
| 16 | `8` → `3` → `m` → `cm` | `300 cm` | `3 m = 300 cm` | oui |
| 17 | `9` → `16` → `oz` → `lb` | `1 lb` | `16 oz = 1 lb` | oui |
| 18 | `9` → `2,5` → `kg` → `lb` | `5.511557 lb` | `2.5 kg = 5.511557 lb` | oui |

## C. Cas invalides

| # | Entrées | Attendu | Observé | OK |
| --- | --- | --- | --- | --- |
| 19 | `zzz` (choix de menu) | message, retour au menu | `! Choix invalide, entrez un chiffre entre 0 et 9.` | oui |
| 20 | `3` → `abc` → *(vide)* → `4` → `6` | deux refus, puis `4 * 6 = 24` | `'abc' n'est pas un nombre`, `saisie vide`, `4 * 6 = 24` | oui |
| 21 | `8` → `3` → `xx` → `m` → `cm` | unité `xx` refusée, redemandée | `! Unité inconnue. Choix possibles : mm, cm, m, ...` puis `3 m = 300 cm` | oui |
| 22 | `7` → `-300` → `C` → `K` | refus (sous le zéro absolu) | `! Erreur : température inférieure au zéro absolu.` | oui |
| 23 | `8` → `-5` → `m` → `km` | refus (longueur négative) | `! Erreur : une longueur ne peut pas être négative.` | oui |
| 24 | `9` → `-5` → `kg` → `g` | refus (poids négatif) | `! Erreur : un poids ne peut pas être négatif.` | oui |
| 25 | `1` → `nan` → `2` → `3` | `nan` refusé, redemandé | `! Saisie invalide : valeur non finie refusée.` | oui |
| 26 | `1` → `1e999` → `2` → `3` | dépassement refusé | `! Saisie invalide : valeur non finie refusée.` | oui |
| 27 | fin de saisie (`Ctrl+D`) au menu | sortie propre, pas de trace d'erreur | `Interruption : au revoir !` | oui |
| 28 | `Ctrl+C` au menu | sortie propre, pas de trace d'erreur | `Interruption : au revoir !` | oui |

## Bilan

28 cas exécutés, 28 conformes à l'attendu. Aucun cas n'a produit de trace
d'erreur Python (`Traceback`).

Deux erreurs de **mon propre scénario** ont été rencontrées pendant les essais
(une saisie en trop qui décalait toutes les suivantes) : ce sont des erreurs de
script de test, pas du programme, et elles ont été corrigées avant les relevés
ci-dessus.
