# Format du fichier de sauvegarde

Les tâches sont enregistrées dans un fichier **JSON**, encodé en **UTF-8**, lisible
à la main. Exemple réel : [`exemple/taches-demo.json`](./exemple/taches-demo.json).

## Emplacement

Le fichier utilisé est, par ordre de priorité :

1. l'option `-f` / `--fichier` ;
2. la variable d'environnement `TACHES_FICHIER` ;
3. `taches.json` dans le dossier courant.

Un fichier **absent ou vide** est traité comme une liste vide ; il est créé à la
première sauvegarde (les dossiers manquants aussi).

## Structure

```json
{
  "version": 1,
  "taches": [
    {
      "id": 1,
      "titre": "Réviser le chapitre 3",
      "statut": "terminee",
      "priorite": "haute",
      "cree_le": "2026-10-28T08:24:33",
      "terminee_le": "2026-10-28T08:24:45"
    }
  ]
}
```

| Champ | Type | Règle |
| --- | --- | --- |
| `version` | entier | numéro de version du format, actuellement `1` |
| `taches` | liste | zéro, une ou plusieurs tâches |
| `id` | entier | unique dans le fichier ; attribué automatiquement (plus grand id existant + 1) |
| `titre` | texte | non vide, 100 caractères au plus, espaces superflus supprimés |
| `statut` | texte | `a_faire` ou `terminee` |
| `priorite` | texte | `basse`, `normale` ou `haute` |
| `cree_le` | texte | date et heure ISO 8601 locales, à la seconde |
| `terminee_le` | texte ou `null` | date de complétion, `null` tant que la tâche est à faire |

## Validation au chargement

Au démarrage, le programme vérifie le fichier. Il **refuse** de continuer, avec un
message d'erreur et le code de sortie 1, dans les cas suivants : JSON invalide,
racine qui n'est pas un objet, clé `taches` absente ou qui n'est pas une liste,
tâche sans `id` entier, sans titre, avec un statut ou une priorité inconnus,
identifiants en double.

**Un fichier refusé n'est jamais modifié ni écrasé** : on peut le corriger à la
main sans rien perdre (voir la capture
[fichier corrompu](./README.md#5-fichier-corrompu-refusé-et-jamais-écrasé)).

## Écriture

La sauvegarde est faite à **chaque modification** (ajout, fin, suppression), de
façon **atomique** : le contenu est d'abord écrit dans un fichier temporaire du même
dossier, puis renommé par-dessus l'ancien. Une coupure en cours d'écriture ne peut
donc pas laisser un fichier tronqué. La lecture (`lister`) n'écrit rien.

## Limites connues

- Pas de verrou : deux exécutions simultanées sur le même fichier peuvent s'écraser
  mutuellement (la dernière sauvegarde l'emporte).
- Un identifiant libéré par la suppression de la dernière tâche peut être
  réattribué à la tâche suivante (l'id est calculé comme « maximum + 1 »).
- Le renommage atomique remplace le fichier même s'il est en lecture seule, dès
  lors que le dossier est modifiable.
