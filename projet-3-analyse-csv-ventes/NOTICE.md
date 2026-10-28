# Notice d'utilisation

## Prérequis

Python 3.8 ou plus récent. Aucune installation supplémentaire (module `csv` de la
bibliothèque standard, pas de pandas).

## Lancer une analyse

Depuis la racine du projet :

```bash
python3 -m analyse_ventes data/ventes_t3_2026.csv
```

| Option | Rôle | Exemple |
| --- | --- | --- |
| `--mois AAAA-MM` | ne garder que ce mois | `--mois 2026-08` |
| `--region NOM` | ne garder que cette région | `--region Vaud` |
| `--categorie NOM` | ne garder que cette catégorie | `--categorie Mobilier` |
| `--tri ca\|quantite\|nom` | tri du tableau des produits (défaut : `ca`) | `--tri quantite` |
| `--top N` | n'afficher que les N premiers produits | `--top 5` |
| `--sortie DOSSIER` | écrire la synthèse dans des fichiers | `--sortie resultats` |
| `-h`, `--help` | aide | |

Les filtres se combinent, sans distinction de majuscules :

```bash
python3 -m analyse_ventes data/ventes_t3_2026.csv --mois 2026-08 --region Vaud --tri quantite --top 5
```

## Votre propre fichier

Le CSV doit avoir une ligne d'en-tête avec ces 7 colonnes (dans n'importe quel ordre) :

```text
date;id_vente;produit;categorie;region;quantite;prix_unitaire
2026-07-01;V-0001;Webcam HD;Accessoires;Genève;1;79.00
```

Dates `AAAA-MM-JJ`, prix en CHF, encodage UTF-8, séparateur `;` ou `,` (détecté
automatiquement). Les règles complètes sont dans [`METHODE.md`](./METHODE.md).

## Lire le rapport

1. **En-tête** : filtres actifs, lignes lues / valides / rejetées (avec le numéro et la
   raison de chaque ligne rejetée, jusqu'à 10).
2. **Indicateurs** : période, nombre de ventes, quantité, chiffre d'affaires, moyenne par
   vente, produit le plus vendu, produit au plus gros CA.
3. **Tableaux** par mois, région, catégorie et produit, avec la part du CA.

## Fichiers produits (`--sortie`)

| Fichier | Contenu |
| --- | --- |
| `synthese.txt` | le rapport complet, tel qu'affiché |
| `synthese-produits.csv` | un produit par ligne : `produit;nb_ventes;quantite;chiffre_affaires_chf`, trié par CA décroissant |

Exemple : [`resultats/`](./resultats/).

## Codes de sortie et erreurs

| Code | Signification |
| --- | --- |
| 0 | analyse produite (même si des lignes ont été rejetées, ou si les filtres ne laissent aucune vente) |
| 1 | fichier absent, vide, mal encodé, colonnes manquantes, ou écriture de `--sortie` impossible |
| 2 | option invalide (mois mal écrit, `--top 0`, tri inconnu...) |

## Régénérer les données d'exemple

```bash
python3 tools/generer_donnees.py
```

Produit toujours les mêmes fichiers (graine fixe) : `data/ventes_t3_2026.csv` (320
ventes) et `data/ventes_avec_erreurs.csv` (lignes invalides, pour tester la robustesse).
