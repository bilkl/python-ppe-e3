# Jeu de tests manuels

Programme testé : `python3 -m client_taux`, Python 3.12.3, `requests` 2.31.0, Linux.
Exécution le 30 octobre 2026 **contre la vraie API** Frankfurter (dernier cours disponible :
29 octobre 2026). Les erreurs serveur (5xx, 429, HTML, JSON incomplet...) ne peuvent pas
être provoquées sur la vraie API : elles sont rejouées par les tests automatisés contre
un serveur local factice (voir [`GESTION-ERREURS.md`](./GESTION-ERREURS.md)).

Les cas 1 à 5, 8, 10, 14, 15, 16, 17 et 18 ont aussi été tapés au clavier dans le terminal
des [captures d'écran](./README.md#captures-décran). Code de sortie entre parenthèses.

## A. Requêtes valides

| # | Commande (après `python3 -m client_taux`) | Attendu | Observé |
| --- | --- | --- | --- |
| 1 | `convertir 250 CHF EUR` | montant converti et taux | `250.00 CHF = 271.09 EUR`, `taux : 1 CHF = 1.0844 EUR (cours du 2026-10-29)` (0) |
| 2 | `convertir 1500,50 CHF USD` | virgule décimale acceptée, milliers en apostrophe | `1'500.50 CHF = 1'810.95 USD` (0) |
| 3 | `taux CHF EUR USD GBP JPY` | quatre taux, devises triées | EUR 1.0844, GBP 0.9063, JPY 190.7600, USD 1.2069 (0) |
| 4 | `taux CHF EUR USD --date 2026-10-03` (un samedi) | dernier cours ouvré, remarque affichée | `cours du 2026-10-02`, ligne `Remarque : aucun cours publié le 2026-10-03`, EUR 1.0777, USD 1.2097 (0) |
| 5 | `historique CHF EUR --du 2026-10-01 --au 2026-10-28` | série, extrêmes, moyenne, variation | 20 cours, minimum 1.0597, maximum 1.0857, moyenne 1.0766, variation +2.05 % ; 10 lignes affichées dont `...` (0) |
| 6 | `historique CHF EUR --du 2026-10-05 --au 2026-10-05` | un seul cours | 1 cours : 1.0740, variation +0.00 % (0) |
| 7 | `historique CHF EUR --du 2026-10-03 --au 2026-10-04` (samedi-dimanche) | période sans cours | l'API renvoie le vendredi précédent : `2026-10-02 au 2026-10-02 (1 cours)`, 1.0777 (0) |
| 8 | `devises --filtre dollar` | devises dont le nom contient « dollar » | 6 devises : AUD, CAD, HKD, NZD, SGD, USD (0) |
| 9 | `taux CHF` | toutes les devises | 29 lignes de taux (0) |

## B. Saisies invalides (refusées avant toute requête)

| # | Commande | Observé |
| --- | --- | --- |
| 10 | `convertir abc CHF EUR` | `Erreur de saisie : montant invalide : 'abc'` (1) |
| 11 | `convertir 0 CHF EUR`, puis `-5` | `le montant doit être un nombre positif` (1) |
| 12 | `convertir 100 CH EUR` | `code de devise invalide : 'CH' (3 lettres attendues, ex. CHF)` (1) |
| 13 | `convertir 100 CHF CHF` | `la devise d'arrivée est la même que celle de départ (CHF)` (1) |
| 14 | `taux CHF --date 29/10/2026`, puis `2026-02-30` | `date invalide ... (format AAAA-MM-JJ)` (1) |
| 15 | `historique CHF EUR --du 2026-10-28 --au 2026-10-01` | `la date de début (2026-10-28) est après la date de fin (2026-10-01)` (1) |

## C. Erreurs de l'API et du réseau

| # | Commande | Observé |
| --- | --- | --- |
| 16 | `convertir 100 CHF ZZZ` | `Erreur : ressource introuvable (HTTP 404) : devise ou date inconnue, ou hors période disponible` (1), une seule requête |
| 17 | `taux CHF --date 1990-01-01` | même message 404 (1) : avant la première publication de l'API |
| 18 | `--url http://127.0.0.1:9 --tentatives 3 taux CHF` | `Erreur : impossible de joindre http://127.0.0.1:9 (réseau ou serveur indisponible)` (1) en **1,646 s** : 3 essais, attentes de 0.5 s et 1 s |
| 19 | `--delai 0.001 --tentatives 2 taux CHF` | `Erreur : délai dépassé (0.001 s) en contactant https://api.frankfurter.dev` (1) |
| 20 | `FRANKFURTER_URL=http://127.0.0.1:9`, `--tentatives 1 taux CHF` | la variable d'environnement est bien prise en compte : même message que le cas 18 (1) |

## D. Usage incorrect (messages d'`argparse`, en anglais)

| # | Commande | Observé |
| --- | --- | --- |
| 21 | *(aucune commande)* | `the following arguments are required: commande` (2) |
| 22 | `historique CHF EUR --du 2026-10-01` | `the following arguments are required: --au` (2) |

## Bilan

22 cas exécutés, 22 conformes. Aucune trace Python. Deux comportements à connaître :

- **Cas 1.** Le montant converti vient de l'API, qui arrondit à 2 décimales ; le taux
  affiché est donc recalculé (`271.09 ÷ 250`) et arrondi à 4 décimales.
- **Cas 7.** Pour une période sans aucun jour ouvré, l'API renvoie le dernier cours
  précédent, hors de la période demandée. Le rapport affiche la période **réelle** des
  cours reçus (2026-10-02) et non celle demandée.

**Défaut trouvé pendant ces essais, corrigé.** `convertir 100 CHF CHF` partait vers l'API,
qui répondait `HTTP 422 : bad currency pair`, un message peu parlant. La devise identique
est maintenant refusée localement (cas 13) et couverte par un test automatisé.
