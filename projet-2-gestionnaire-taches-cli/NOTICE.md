# Notice d'utilisation

## Prérequis

Python 3.8 ou plus récent. Aucune installation supplémentaire.

## Commandes

Toutes les commandes se lancent depuis la racine du projet :

```bash
python3 -m gestionnaire <commande> [options]
```

| Commande | Rôle | Exemple |
| --- | --- | --- |
| `ajouter TITRE [-p PRIORITE]` | ajoute une tâche (priorité : `basse`, `normale` par défaut, `haute`) | `python3 -m gestionnaire ajouter "Envoyer le rapport" -p haute` |
| `lister [--statut S] [-p P]` | liste les tâches, haute priorité d'abord ; filtres facultatifs (`a_faire`, `terminee`) | `python3 -m gestionnaire lister --statut a_faire` |
| `terminer ID` | marque la tâche comme terminée | `python3 -m gestionnaire terminer 2` |
| `supprimer ID` | supprime la tâche | `python3 -m gestionnaire supprimer 2` |
| `--help` | affiche l'aide (aussi `COMMANDE --help`) | `python3 -m gestionnaire ajouter --help` |

L'identifiant (`ID`) est celui affiché dans la première colonne de `lister`.

## Où sont mes tâches ?

Dans un fichier JSON, `taches.json` par défaut, créé dans le dossier où vous lancez
la commande. Pour en choisir un autre :

```bash
python3 -m gestionnaire -f ~/mes-taches.json lister        # une seule fois
export TACHES_FICHIER=~/mes-taches.json                    # pour toute la session
```

Le format est décrit dans [`FORMAT-FICHIER.md`](./FORMAT-FICHIER.md).

## Lecture de la liste

```text
 ID  ST.  PRIORITÉ  TITRE
  1  [x]  haute     Réviser le chapitre 3
  4  [ ]  haute     Envoyer le rapport
  2  [ ]  normale   Acheter du café
-- 3 tâche(s), 2 à faire
```

`[ ]` = à faire, `[x]` = terminée.

## Erreurs

Un message `Erreur : ...` est affiché sur la sortie d'erreur et le code de sortie
est **1** (usage incorrect des options : code **2**, message de `argparse`). Le fichier
n'est alors pas modifié. Cas courants : titre vide ou trop long, tâche introuvable
ou déjà terminée, fichier JSON corrompu.
