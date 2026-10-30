# Cas métier : mini-banque

Cas retenu parmi les exemples de la fiche (« compte bancaire simplifié »), **à valider avec
le formateur**. Il est assez riche pour avoir de vraies règles à tester (limites, états,
arrondis) tout en restant petit : 353 lignes de code.

## Ce que fait l'application

Une `Banque` ouvre des comptes, les retrouve par numéro et exécute des virements entre
eux. Un compte courant accepte dépôts, retraits et virements, avec un découvert autorisé
éventuel. Un compte épargne ne peut pas être à découvert et verse des intérêts mensuels.
Chaque compte tient un historique immuable de ses opérations.

## Séparation de la logique et des entrées/sorties

| Module | Contenu | Entrées/sorties |
| --- | --- | --- |
| `montants.py` | validation et conversion des montants | aucune |
| `compte.py` | `CompteBancaire`, `CompteEpargne`, `Operation` | aucune |
| `banque.py` | `Banque` : ouverture, recherche, virements | aucune |
| `erreurs.py` | exceptions métier | aucune |
| `releve.py` | mise en forme d'un relevé en texte | aucune (renvoie une chaîne) |
| `__main__.py` | démonstration `python3 -m banque` | **seul module qui affiche** |

Toute la logique se teste donc en appelant des fonctions, sans clavier ni écran à simuler.
L'heure est **injectée** (paramètre `horloge`) : les tests utilisent une horloge fixe, leurs
résultats ne dépendent jamais de l'heure réelle.

## Règles métier

| # | Règle | Vérifiée dans |
| --- | --- | --- |
| R1 | Un montant est un `Decimal` à 2 décimales au plus ; les `float` et les booléens sont **refusés** | `test_montants.py` |
| R2 | Un montant d'opération est strictement positif et ne dépasse pas 1 000 000 000 | `test_montants.py` |
| R3 | Le solde initial et le découvert autorisé sont positifs ou nuls | `test_compte.py` |
| R4 | Un dépôt crédite exactement le montant ; les sommes sont exactes (dix dépôts de 0.10 donnent 1.00) | `test_compte.py` |
| R5 | Un retrait est autorisé jusqu'à `solde + découvert` **inclus** ; un centime de plus est refusé | `test_compte.py` |
| R6 | Une opération refusée ne modifie ni le solde ni l'historique | `test_compte.py`, `test_banque.py` |
| R7 | Un compte ne peut être clôturé qu'avec un solde **exactement nul** ; un compte clôturé refuse toute opération | `test_compte.py` |
| R8 | L'historique est chronologique, immuable, et son dernier solde égale le solde du compte | `test_compte.py` |
| R9 | Un virement est **tout ou rien** : si l'un des deux comptes ne peut pas l'exécuter, aucun n'est modifié | `test_banque.py` |
| R10 | Un virement vers soi-même, vers ou depuis un compte inconnu ou clôturé est refusé | `test_banque.py` |
| R11 | Un virement conserve le total des dépôts de la banque | `test_banque.py` |
| R12 | Un compte épargne n'a jamais de découvert ; taux annuel entre 0 et 10 % | `test_epargne.py` |
| R13 | Intérêts mensuels = `solde × taux ÷ 12`, arrondis au centime, **demi vers le haut** ; rien n'est crédité s'ils arrondissent à 0 | `test_epargne.py` |
| R14 | Un numéro de compte n'est jamais réutilisé, même après un échec d'ouverture | `test_banque.py` |
| R15 | Le titulaire est non vide, 60 caractères au plus, espaces normalisés | `test_compte.py` |

## Erreurs

| Exception | Cas |
| --- | --- |
| `MontantInvalide` (aussi une `ValueError`) | type, format, signe, décimales, maximum, taux |
| `FondsInsuffisants` | retrait ou virement au-delà du disponible ; porte `montant` et `disponible` |
| `CompteFerme` | opération sur un compte clôturé |
| `CompteInconnu` | numéro absent |
| `OperationInvalide` | virement vers soi-même, clôture avec solde, titulaire invalide, découvert sur un épargne |

Toutes dérivent de `ErreurBancaire`.
