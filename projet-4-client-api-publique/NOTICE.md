# Notice d'utilisation

## Prérequis

Python 3.8 ou plus récent et la bibliothèque `requests` :

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Un accès Internet est nécessaire (aucune clé d'API : le service est gratuit et public).

## Commandes

```bash
python3 -m client_taux [options] <commande> ...
```

| Commande | Rôle | Exemple |
| --- | --- | --- |
| `convertir MONTANT BASE VERS` | convertit un montant | `convertir 250 CHF EUR` |
| `taux BASE [VERS ...]` | taux depuis une devise (toutes si aucune cible) | `taux CHF EUR USD GBP` |
| `historique BASE VERS --du D --au D` | évolution d'un taux, avec minimum, maximum, moyenne, variation | `historique CHF EUR --du 2026-10-01 --au 2026-10-28` |
| `devises [--filtre TEXTE]` | liste les devises disponibles | `devises --filtre dollar` |

`convertir` et `taux` acceptent `--date AAAA-MM-JJ` pour le cours d'un jour passé. Les
codes de devise s'écrivent en majuscules ou minuscules (`chf`), le montant avec point ou
virgule (`1500,50`).

Options générales, avant la commande :

| Option | Rôle | Défaut |
| --- | --- | --- |
| `--url URL` | adresse de l'API (aussi variable `FRANKFURTER_URL`) | `https://api.frankfurter.dev` |
| `--delai S` | délai maximal par requête, en secondes | 10 |
| `--tentatives N` | nombre d'essais en cas d'échec réseau ou HTTP 5xx / 429 | 3 |

## À savoir

- Les cours sont ceux de la Banque centrale européenne, publiés les **jours ouvrés**.
  Pour un week-end ou un jour férié, le dernier cours disponible est utilisé et une
  remarque l'indique.
- Les erreurs s'affichent en une ligne, code de sortie 1 (2 pour une option invalide).
  Détail dans [`GESTION-ERREURS.md`](./GESTION-ERREURS.md).
- Exemples de sorties réelles : [`exemples/sortie-exemples.txt`](./exemples/sortie-exemples.txt).
