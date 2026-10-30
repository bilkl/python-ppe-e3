# Projet 5 — Mini-application testée avec pytest

**Rendu PPE — Cours *Python — Principes de base* (classe E3).**
Réalisé le **30 octobre 2026**. Niveau : avancé.

Une **mini-banque** en Python (comptes courants et épargne, virements, intérêts, relevés)
livrée avec sa **suite de tests pytest** : 165 tests, couverture de **100 % des lignes et des
branches**, et un test de mutation qui prouve que ces tests détectent vraiment les bugs.

## Sommaire

- [Avancement](#avancement)
- [Démarrage rapide](#démarrage-rapide)
- [Structure du dépôt](#structure-du-dépôt)
- [Le cas métier](#le-cas-métier)
- [Stratégie de test](#stratégie-de-test)
- [Captures d'écran](#captures-décran)
- [Rapport d'exécution et couverture](#rapport-dexécution-et-couverture)
- [Difficultés et décisions](#difficultés-et-décisions)
- [Limites](#limites)
- [Correspondance avec la fiche du projet](#correspondance-avec-la-fiche-du-projet)
- [Sources](#sources)

## Avancement

| Étape de la fiche | État |
| --- | --- |
| 1. Définir le cas métier | Terminé : mini-banque, voir [`CAS-METIER.md`](./CAS-METIER.md) (15 règles) |
| 2. Concevoir le module en isolant la logique des entrées/sorties | Terminé : seul `__main__.py` affiche ; l'heure est injectée |
| 3. Tests pytest des cas nominaux | Terminé |
| 4. Tests pytest des cas limites et des erreurs attendues | Terminé |
| 5. Exécuter la suite et documenter le taux de réussite et la couverture | Terminé : 165/165, 100 % lignes et branches, [`rapport/`](./rapport/) |
| Livrable : code source du module | [`banque/`](./banque/) |
| Livrable : suite de tests pytest | [`tests/`](./tests/) |
| Livrable : rapport d'exécution (capture ou export) | [`rapport/`](./rapport/) (4 exports) et captures 2 à 5 |

## Démarrage rapide

Prérequis : Python 3.8 ou plus récent (testé avec Python 3.12.3 sous Linux). Le module
`banque` n'a aucune dépendance ; `pytest` et `pytest-cov` ne servent qu'aux tests.

```bash
git clone https://github.com/bilkl/python-ppe-e3.git
cd python-ppe-e3/projet-5-mini-application-tests-pytest
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python3 -m banque                                   # démonstration
pytest                                              # les 165 tests
pytest --cov --cov-report=term-missing              # avec la couverture
python3 tools/mutation.py                           # test de mutation
tools/rapport.sh                                    # régénère rapport/
```

## Structure du dépôt

```text
.
├── banque/
│   ├── montants.py    # validation des montants (Decimal, 2 décimales, pas de float)
│   ├── compte.py      # CompteBancaire, CompteEpargne, Operation
│   ├── banque.py      # Banque : ouverture, recherche, virements tout-ou-rien
│   ├── erreurs.py     # exceptions métier
│   ├── releve.py      # relevé en texte (renvoie une chaîne)
│   └── __main__.py    # démonstration (seul module qui affiche)
├── tests/
│   ├── conftest.py        # fixtures partagées, horloge fixe
│   ├── test_montants.py   # 49 cas
│   ├── test_compte.py     # 49 cas
│   ├── test_epargne.py    # 28 cas
│   ├── test_banque.py     # 29 cas
│   └── test_releve.py     # 10 cas
├── rapport/               # rapport d'exécution (pytest, JUnit, couverture, mutation)
├── tools/
│   ├── mutation.py        # test de mutation artisanal (23 bugs)
│   ├── rapport.sh         # génère rapport/
│   └── capture.sh         # génère les captures d'écran
├── screenshots/
├── CAS-METIER.md          # cas métier et règles R1 à R15
├── pytest.ini  .coveragerc  requirements.txt
└── README.md
```

## Le cas métier

Une `Banque` ouvre des comptes et exécute des virements ; un compte courant a un découvert
autorisé ; un compte épargne verse des intérêts mensuels. Les règles (R1 à R15) sont
listées dans [`CAS-METIER.md`](./CAS-METIER.md), avec pour chacune le fichier de tests qui
la vérifie. Une démonstration (`python3 -m banque`) est en [capture 1](#1-démonstration-de-lapplication).

Un point de conception structure tout le reste : **l'argent est un `Decimal`**, jamais un
`float`. `0.1 + 0.2` donne `0.30000000000000004` en binaire ; un montant `float` est donc
refusé à l'entrée.

## Stratégie de test

77 fonctions de test, 165 cas une fois les paramétrages développés (`@pytest.mark.parametrize`).
Chaque fichier est organisé en deux parties : d'abord les **cas nominaux**, ensuite les
**cas limites et erreurs**.

| Famille | Exemples |
| --- | --- |
| **Nominaux** | dépôt, retrait, virement, intérêts exacts, historique chronologique, relevé complet |
| **Limites** (valeur exacte de la frontière, puis un centime au-delà) | retrait de `solde + découvert` accepté, `+ 0.01` refusé ; montant maximum accepté, `+ 0.01` refusé ; titulaire de 60 caractères accepté, 61 refusé ; taux de 10 % accepté, 10.1 % refusé ; plus petit montant : 0.01 |
| **Arrondis** | intérêts de 12.875 → 12.88 (demi vers le haut) ; 12.87475 → 12.87 ; intérêts sous le demi-centime → rien n'est crédité |
| **Erreurs attendues** | `FondsInsuffisants`, `MontantInvalide`, `CompteFerme`, `CompteInconnu`, `OperationInvalide`, toujours avec le message et le **solde inchangé** |
| **Entrées hostiles** | `float`, `True`, `None`, `nan`, `inf`, `"1 000"`, `"12.5.3"`, `"€10"`, notation `1e2`, 3 décimales |
| **Propriétés** | le total des dépôts est conservé par un virement ; le dernier solde de l'historique égale le solde ; une opération refusée ne laisse aucune trace |
| **Atomicité** | un virement refusé ne modifie **aucun** des deux comptes ni leurs historiques |

Techniques pytest utilisées : fixtures (`conftest.py`), `@pytest.mark.parametrize` (y compris
combiné, avec identifiants lisibles), `pytest.raises(..., match=...)`, horloge injectée pour
des tests déterministes, `capsys` et `runpy` pour tester la démonstration.

### Les tests testent-ils vraiment quelque chose ?

Une couverture de 100 % dit que chaque ligne **s'exécute** pendant les tests, pas que les
tests **vérifient** le résultat. D'où [`tools/mutation.py`](./tools/mutation.py) : le script
copie le code, y introduit un bug à la fois (un `>` devient `>=`, un signe est inversé, un
contrôle est supprimé...), relance la suite, et exige qu'un test **échoue**. Un bug qui
passe inaperçu (« survivant ») révèle un test manquant.

Résultat : **23 bugs introduits, 23 détectés.** La liste complète est dans
[`rapport/mutation.txt`](./rapport/mutation.txt).

## Captures d'écran

Commandes réellement tapées dans un terminal (écran virtuel Xvfb, `xterm`, `xdotool`,
`scrot`) ; [`tools/capture.sh`](./tools/capture.sh) les régénère.

### 1. Démonstration de l'application

![Démonstration](./screenshots/01-demonstration.png)

Deux comptes d'Alice : virement de 300 du courant vers l'épargne, intérêts du mois
(12.88 CHF), puis un retrait de 5 000 refusé.

### 2. Les tests, un par ligne

![pytest -v](./screenshots/02-pytest-verbose.png)

Fin de la sortie de `pytest -v` : chaque cas paramétré est un test à part, 165 réussis.

### 3. Couverture des lignes et des branches

![Couverture](./screenshots/03-couverture.png)

### 4. Un bug volontaire est détecté

![Bug volontaire détecté](./screenshots/04-bug-volontaire-detecte.png)

Dans une **copie temporaire** du code, `if montant > self.disponible` devient `>=` (retrait
de la totalité du disponible refusé à tort). La suite passe de 165 réussis à **9 échecs**,
dont le test du découvert, de l'épargne et de la clôture.

### 5. Test de mutation

![Test de mutation](./screenshots/05-test-de-mutation.png)

## Rapport d'exécution et couverture

Détail dans [`rapport/`](./rapport/) : sortie `pytest -v`, `junit.xml`, couverture, mutation.

| Mesure | Résultat |
| --- | --- |
| Tests réussis | **165 / 165** (0 échec, 0 ignoré) |
| Durée | environ 0,2 s |
| Couverture des lignes | **100 %** (217 instructions) |
| Couverture des branches | **100 %** (46 branches) |
| Mutations détectées | **23 / 23** |

Le fichier `__main__.py` est inclus dans la couverture : la démonstration est elle-même
testée.

## Difficultés et décisions

- **Imports sous pytest.** Premier lancement : `ModuleNotFoundError: No module named 'banque'`.
  Corrigé par `pythonpath = .` dans `pytest.ini` et un `tests/__init__.py`.
- **Configuration de la couverture ignorée.** J'avais d'abord placé les réglages de
  `coverage` dans `pytest.ini`, où il ne les lit pas : le premier rapport comptait les
  fichiers de test eux-mêmes (« 100 % » trompeur). Déplacés dans `.coveragerc`
  (`source = banque`, `branch = True`), le rapport ne porte plus que sur le code de
  l'application.
- **Un test de mutation a trouvé du code redondant, pas un test manquant.** La première
  exécution a laissé survivre 1 mutation sur 22 : le contrôle `isinstance(valeur, float)`
  était **doublé** par le contrôle de type suivant, qui refusait déjà les `float` avec le
  même message. Le bug introduit n'avait donc aucun effet observable. J'ai simplifié le code
  (un seul contrôle de type) et réécrit la mutation pour viser ce contrôle, plus une mutation
  sur les booléens.
- **Code mort supprimé.** Ma première version du virement contenait un retour en arrière
  (`try/except` qui annulait le débit si le crédit échouait). Après les contrôles préalables,
  le crédit ne peut plus échouer : ce code ne pouvait jamais s'exécuter, donc jamais
  être couvert ni testé. Supprimé, et l'ordre « tout vérifier puis agir » documenté.
- **`float` refusés plutôt que convertis.** Convertir `0.1` en `Decimal(str(0.1))` aurait
  masqué le problème. Les refuser force l'appelant à passer `"0.10"`.
- **Heure injectée.** Sans cela, les horodatages changeraient à chaque test.

## Limites

- **100 % de couverture ne prouve pas l'absence de bug.** Le test de mutation en réduit le
  risque mais ses 23 mutations sont choisies à la main : elles ne sont pas exhaustives.
  Une bibliothèque dédiée (par exemple `mutmut`) en génèrerait bien davantage.
- **Tests et code écrits par la même personne** : les cas imaginés partagent les mêmes
  angles morts. Une relecture croisée par un tiers serait utile.
- **Pas de persistance** : la banque vit en mémoire. Les comptes ne survivent pas à la
  fin du programme.
- **Pas de concurrence** : l'application n'est pas conçue pour des accès simultanés.
- **Une seule devise** (CHF), pas de frais, de plafond journalier ni de taux variable.
- Le cas métier est un choix personnel, à valider avec le formateur comme le demande la fiche.

## Correspondance avec la fiche du projet

| Critère d'évaluation | Pondération | Où le trouver |
| --- | --- | --- |
| Conception du module | 25 % | [`banque/`](./banque/), [`CAS-METIER.md`](./CAS-METIER.md) |
| Couverture des cas nominaux | 20 % | sections « cas nominaux » de chaque fichier de [`tests/`](./tests/), [stratégie](#stratégie-de-test) |
| Couverture des cas limites et erreurs | 25 % | sections « cas limites et erreurs », test de mutation, captures 4 et 5 |
| Qualité et clarté des tests | 15 % | noms explicites, fixtures, paramétrage, `match=` sur les messages, test de mutation |
| Documentation | 15 % | ce README, [`CAS-METIER.md`](./CAS-METIER.md), [`rapport/`](./rapport/) |

## Sources

- Fiche du projet : [Satom-IT-Learning-Solutions/E3 — Projet 5](https://github.com/Satom-IT-Learning-Solutions/E3/blob/main/02-python-principes-de-base/projet-5-mini-application-tests-pytest.md)
- [pytest — documentation officielle](https://docs.pytest.org/en/stable/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python — Module decimal](https://docs.python.org/3/library/decimal.html)
