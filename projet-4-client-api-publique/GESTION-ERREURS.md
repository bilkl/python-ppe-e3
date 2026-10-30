# Gestion des erreurs

Note sur les erreurs prévues et sur la façon dont le client y réagit (livrable de la
fiche). Principe : **aucune trace Python n'est jamais affichée** ; chaque problème donne
un message clair, un code de sortie non nul, et n'est rejoué que s'il a une chance de
réussir la deuxième fois.

## Quatre types d'erreurs

| Classe | Situation | Exemple de message |
| --- | --- | --- |
| `ValueError` (saisie) | l'utilisateur a mal saisi : détectée **avant** toute requête | `Erreur de saisie : date invalide : '29/10/2026' (format AAAA-MM-JJ)` |
| `ErreurReseau` | l'API est injoignable ou trop lente | `Erreur : impossible de joindre http://127.0.0.1:9 (réseau ou serveur indisponible)` |
| `ErreurApi` | l'API répond, mais refuse (HTTP 4xx / 5xx) | `Erreur : ressource introuvable (HTTP 404) : devise ou date inconnue...` |
| `ErreurReponse` | l'API répond 200 mais le contenu est inutilisable | `réponse incomplète : champs base, date, amount ou rates absents` |

## Cas traités

| Cas | Détection | Comportement |
| --- | --- | --- |
| Code de devise invalide (`CH`, `EURO`, `C1F`) | regex `[A-Z]{3}` | refusé localement, aucune requête |
| Devise de départ = devise d'arrivée | comparaison | refusé localement (l'API répondrait HTTP 422) |
| Montant non numérique, nul, négatif, `nan`, `inf` | `valider_montant` | refusé localement |
| Date mal formée ou inexistante (`29/10/2026`, `2026-02-30`) | `date.fromisoformat` | refusé localement |
| Début d'historique après la fin | comparaison | refusé localement |
| Devise ou date inconnue côté API | HTTP 404 | message explicite, **pas de nouvelle tentative** |
| Date sans cours (week-end, jour férié) | champ `date` de la réponse ≠ date demandée | le dernier cours disponible est utilisé **et la remarque est affichée** |
| Clé d'API absente, invalide ou sans droit | HTTP 401 / 403 | message « clé d'API absente, invalide ou sans droit » |
| Trop de requêtes | HTTP 429 | rejoué avec attente, puis message |
| Erreur serveur | HTTP 500, 502, 503, 504 | rejoué avec attente, puis message avec le détail fourni par l'API |
| API injoignable (pas de réseau, serveur arrêté) | `ConnectionError` | rejoué, puis message |
| Délai dépassé | `Timeout` (10 s par défaut, `--delai`) | rejoué, puis message |
| Réponse qui n'est pas du JSON (page de maintenance HTML) | `ValueError` à la lecture | `ErreurReponse` |
| JSON valide mais pas un objet, champ absent, taux texte ou booléen, `rates` vide | contrôles dans `taux()`, `historique()`, `devises()` | `ErreurReponse` |

**Clé d'API.** Frankfurter est gratuit et ne demande aucune clé : ce cas ne peut donc pas
se produire avec cette API. Il est tout de même traité (401 / 403) pour que le client
reste correct si on le pointe, via `--url` ou `FRANKFURTER_URL`, vers un service qui en
exige une. Il est vérifié par un test automatisé contre un serveur local factice.

## Politique de nouvelles tentatives

- **Rejouées** : erreurs réseau, délai dépassé, HTTP 429 et 5xx (problèmes souvent
  passagers). 3 essais au total par défaut (`--tentatives`), avec attente croissante :
  0.5 s puis 1 s entre les essais.
- **Jamais rejouées** : les autres erreurs 4xx (404, 401, 403, 422) : la même requête
  échouerait de la même façon. Un test automatisé vérifie qu'un 404 ne provoque qu'une
  seule requête.
- Le temps total est borné : `tentatives × délai` plus les attentes (10 s × 3 + 1.5 s au
  pire avec les valeurs par défaut).

La capture [gestion des erreurs](./README.md#4-gestion-des-erreurs) montre ce
comportement : avec 3 tentatives vers une adresse injoignable, la commande se termine en
1,6 s, soit les deux attentes de 0.5 s et 1 s.

## Comment c'est testé

Le vrai code réseau (`requests`) est testé contre un **serveur HTTP local factice**
([`tests/serveur_factice.py`](./tests/serveur_factice.py)) qui rejoue chaque situation :
statuts 401, 403, 404, 429, 500, 503, corps HTML, JSON incomplet, réponse lente, port
fermé. Ces tests ne dépendent ni d'Internet ni des taux du jour. Voir
[`TESTS-MANUELS.md`](./TESTS-MANUELS.md) pour les essais contre la vraie API.
