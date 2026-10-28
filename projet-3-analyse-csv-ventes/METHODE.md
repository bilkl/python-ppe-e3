# Méthode de calcul

Note explicative sur les calculs de l'outil (livrable de la fiche). Chaque
indicateur est défini, calculé de façon exacte, puis vérifié par un second calcul
indépendant (voir [Vérification](#vérification)).

## Données d'entrée

Une ligne du CSV = une **vente** (un article, ou un lot du même article, vendu à un
client ce jour-là).

| Colonne | Format | Règle de validation |
| --- | --- | --- |
| `date` | `AAAA-MM-JJ` | date réelle du calendrier |
| `id_vente` | texte | non vide, **unique** |
| `produit`, `categorie`, `region` | texte | non vides |
| `quantite` | entier | strictement positif |
| `prix_unitaire` | décimal, en CHF | fini et strictement positif ; la virgule décimale (`59,90`) est acceptée |

Le délimiteur (`;` ou `,`) est détecté sur la ligne d'en-tête ; un BOM UTF-8 est toléré.

Une ligne qui ne respecte pas ces règles est **écartée du calcul** et signalée avec son
numéro de ligne dans le fichier et la raison. Elle n'arrête pas l'analyse. Si
l'identifiant est en double, la **première** occurrence est gardée. Seuls un fichier
absent, vide, mal encodé ou sans les 7 colonnes arrêtent le programme.

## Définitions

| Indicateur | Définition |
| --- | --- |
| Montant d'une vente | `quantité × prix unitaire` |
| **Chiffre d'affaires (CA) total** | somme des montants de toutes les ventes retenues |
| Nombre de ventes | nombre de lignes valides retenues |
| **Moyenne par vente** | `CA total ÷ nombre de ventes`, arrondi à 0.01 CHF (demi vers le haut) |
| Quantité totale | somme des quantités |
| **Produit le plus vendu** | produit dont la **quantité totale** est la plus élevée ; en cas d'égalité, celui au plus fort CA, puis l'ordre alphabétique |
| Produit au plus gros CA | produit dont le CA total est le plus élevé (aide à lire l'écart avec le précédent) |
| Part (%) | `CA du groupe ÷ CA total retenu × 100`, affiché à 0.1 % |

« Plus vendu » est pris au sens des **unités vendues**, pas du chiffre d'affaires : un
câble à 14.90 CHF peut être le plus vendu sans être le plus rentable. Les deux sont
affichés.

## Regroupements, filtres et tri

- **Regroupements** : par mois (`AAAA-MM` de la date), région, catégorie, produit.
  Pour chaque groupe : nombre de ventes, quantité, CA, part du CA.
- **Filtres** (`--mois`, `--region`, `--categorie`) : cumulatifs (ET logique), sans
  distinction de majuscules. Les statistiques portent sur les ventes **retenues** ;
  le rapport indique aussi le nombre de lignes lues, valides et rejetées.
- **Tri** des produits : `ca` ou `quantite` (décroissants), `nom` (alphabétique
  français, sans tenir compte des accents ni de la casse : *Écran* se range avec les
  E). En cas d'égalité, l'ordre alphabétique départage : le résultat est reproductible.
  Les tableaux par mois, région et catégorie sont triés par mois croissant puis par CA
  décroissant.

## Exactitude des calculs

Les montants sont des `Decimal`, pas des `float`. Avec des flottants,
`0.1 + 0.2` donne `0.30000000000000004` ; sur des centaines de lignes, ces écarts
s'accumulent. Avec `Decimal`, les sommes de montants à deux décimales sont **exactes** ;
la seule approximation est l'arrondi final de la moyenne, indiqué ci-dessus. Un test
automatisé (`test_precision_decimale`) le vérifie.

## Vérification

1. **Calcul à la main** : les tests automatisés utilisent un jeu de 4 ventes dont tous
   les résultats (CA 161.00, moyenne 40.25, produit le plus vendu, etc.) sont calculés
   à la main dans le commentaire du fichier de test.
2. **Calcul indépendant** : [`tools/verification_croisee.sh`](./tools/verification_croisee.sh)
   recalcule CA, nombre de ventes, quantité, moyenne, produit le plus vendu et CA
   mensuel avec `awk`, sans le code Python. Les résultats sont identiques sur les 320
   ventes (capture 05). Des filtres ont aussi été recoupés avec `awk` (voir
   [`TESTS-MANUELS.md`](./TESTS-MANUELS.md)).

## Limites

- Les données sont **fictives** (générées par [`tools/generer_donnees.py`](./tools/generer_donnees.py),
  graine fixe, reproductibles) : les chiffres n'ont aucune valeur commerciale.
- Une seule devise (CHF), pas de remises, de TVA ni de retours.
- Le fichier est lu entièrement en mémoire. Testé uniquement sur 320 lignes : aucune
  mesure n'a été faite sur de gros fichiers.
- Encodage UTF-8 uniquement ; un export Excel en Windows-1252 doit être réenregistré en
  UTF-8 (le programme le signale clairement).
