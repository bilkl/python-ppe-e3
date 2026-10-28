# Jeu de tests manuels

Programme testé : `python3 -m analyse_ventes`, Python 3.12.3, Linux. Exécution le 28 octobre 2026.

**Méthode.** Chaque cas lance la vraie commande et relève la sortie et le code de
sortie. Là où c'est possible, le résultat est **recoupé avec `awk`**, qui recalcule sans
le code Python (colonne « Contrôle »). Les cas 1, 2, 7, 10 et 21 ont aussi été tapés au
clavier dans le terminal des [captures d'écran](./README.md#captures-décran). Jeux de
données : `data/ventes_t3_2026.csv` (320 ventes valides) et `data/ventes_avec_erreurs.csv`
(10 lignes dont 7 invalides), générés par [`tools/generer_donnees.py`](./tools/generer_donnees.py).

## A. Analyses normales

| # | Commande (après `python3 -m analyse_ventes`) | Attendu | Observé (code 0) | Contrôle | OK |
| --- | --- | --- | --- | --- | --- |
| 1 | `data/ventes_t3_2026.csv` | indicateurs globaux | 320 ventes, quantité 968, CA CHF 89'754.00, moyenne 280.48, plus vendu : Câble HDMI 2 m (197 unités) | `awk` : 320, 968, 89754.00, 280.48, 197 | oui |
| 2 | `... --mois 2026-08 --region Vaud --tri quantite --top 5` | filtres cumulés | 39 ventes, quantité 112, CA CHF 8'802.70, moyenne 225.71 ; tableau produits trié par quantité, 5 lignes | `awk` : 39, 112, 8802.70, 225.71 | oui |
| 3 | `... --categorie mobilier` (minuscules) | filtre sans casse | 60 ventes, CA CHF 20'620.80, filtre affiché `catégorie = mobilier` | `awk` : 60, 20620.80 | oui |
| 4 | `... --mois 2026-09 --top 2 --tri nom` | tri alphabétique, 2 produits | `PAR PRODUIT (tri : nom croissant, 2 premiers)` ; 108 ventes, CA CHF 24'561.10 | CA recoupé avec `awk` (capture 05, 3 mois) | oui |
| 5 | `... --region Genève --mois 2026-07 --categorie Informatique` | trois filtres | 8 ventes, CA CHF 5'840.30, moyenne 730.04, plus vendu : Écran 27" (9 unités) | aucun | oui |
| 6 | `... --mois 2027-01` | aucune vente : message, pas de plantage | `Aucune vente ne correspond aux filtres : pas de statistiques.` | | oui |
| 7 | `... --sortie resultats` | deux fichiers écrits | `Fichiers écrits : resultats/synthese.txt, resultats/synthese-produits.csv` ; 421 et 2446 octets | contenu du CSV = tableau produits | oui |
| 8 | même fichier converti en virgules + BOM UTF-8 | résultats identiques à ceux du cas 1 | 320 ventes, CHF 89'754.00, moyenne 280.48, Câble HDMI 2 m | | oui |
| 9 | fichier avec en-tête seul | pas de ventes, pas d'erreur | `Lignes de données : 0   valides : 0   rejetées : 0` puis le message du cas 6 | | oui |

## B. Données invalides

| # | Fichier | Attendu | Observé (code 0) | OK |
| --- | --- | --- | --- | --- |
| 10 | `data/ventes_avec_erreurs.csv` (capture 03) | 7 rejets avec numéro de ligne et raison ; les 3 lignes valides analysées | `valides : 3   rejetées : 7` ; rejets : ligne 4 quantité `abc`, 5 date `07/04/2026`, 6 quantité -2, 7 produit vide, 8 id `E-002` en double, 10 prix `nan`, 11 `6 colonnes au lieu de 7`. La ligne 9 (prix `59,90` à virgule décimale) est acceptée. CA CHF 657.70 | oui |

## C. Fichier ou options incorrects

| # | Commande | Attendu | Observé | Code | OK |
| --- | --- | --- | --- | --- | --- |
| 11 | `data/absent.csv` | erreur claire | `Erreur : fichier introuvable : data/absent.csv` | 1 | oui |
| 12 | fichier vide | erreur | `Erreur : /tmp/vide.csv est vide` | 1 | oui |
| 13 | CSV sans les 7 colonnes | erreur listant les manquantes | `Erreur : colonnes manquantes : id_vente, categorie, region, quantite, prix_unitaire` | 1 | oui |
| 14 | CSV non UTF-8 (Latin-1) | erreur d'encodage, pas de trace Python | `Erreur : /tmp/latin.csv n'est pas encodé en UTF-8` | 1 | oui |
| 15 | `... --mois 2026-13` | refus | `argument --mois: '2026-13' n'est pas un mois AAAA-MM` | 2 | oui |
| 16 | `... --mois juillet` | refus | `argument --mois: 'juillet' n'est pas un mois AAAA-MM` | 2 | oui |
| 17 | `... --top 0` | refus | `argument --top: '0' n'est pas un entier positif` | 2 | oui |
| 18 | `... --tri prix` | refus | `invalid choice: 'prix' (choose from 'ca', 'quantite', 'nom')` | 2 | oui |
| 19 | *(sans fichier)* | refus | `the following arguments are required: fichier` | 2 | oui |
| 20 | `... --sortie /proc/x/y` | erreur d'écriture claire | rapport affiché, puis `Erreur : écriture impossible dans /proc/x/y (No such file or directory)` | 1 | oui |

## D. Vérification croisée

| # | Vérification | Résultat | OK |
| --- | --- | --- | --- |
| 21 | [`tools/verification_croisee.sh`](./tools/verification_croisee.sh) (capture 05) | `awk` et le programme donnent les mêmes valeurs : CA 89754.00, 320 ventes, quantité 968, moyenne 280.48, produit le plus vendu (197 unités), CA de juillet 31399.50, août 33793.40, septembre 24561.10 | oui |

## Bilan

21 cas exécutés, 21 conformes à l'attendu. Aucune trace d'erreur Python
(`Traceback`). Tous les chiffres recoupables avec `awk` concordent exactement, au
centime.

À noter, comportements constatés et assumés :

- le cas 20 affiche d'abord le rapport puis signale l'échec de l'écriture (code 1) : le
  calcul n'est pas perdu ;
- les messages d'`argparse` des cas 18 et 19 sont en anglais.

**Défaut trouvé pendant le développement, corrigé avant ces relevés.** Le tri
`--tri nom` plaçait « Écran » après « Souris » (l'ordre par défaut de Python classe les
lettres accentuées après `z`). Détecté par un test automatisé écrit à la main
(`test_trier`), corrigé par une clé de tri sans accents ni casse (`cle_alpha`).
