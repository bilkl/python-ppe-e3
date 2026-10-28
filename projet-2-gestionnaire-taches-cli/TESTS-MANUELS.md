# Jeu de tests manuels

Programme testé : `python3 -m gestionnaire`, Python 3.12.3, Linux. Exécution le 28 octobre 2026.

**Méthode.** Chaque cas lance la vraie commande sur un fichier de sauvegarde neuf
(`TACHES_FICHIER` pointant sur un fichier temporaire) et relève la sortie et le
code de sortie. Les cas sont exécutés **dans l'ordre**, car chacun part de l'état
laissé par le précédent (colonne « État »). Les cas 2, 3, 5, 7, 10 à 12, 14, 17, 24
et 25 ont aussi été tapés au clavier dans le terminal des
[captures d'écran](./README.md#captures-décran), avec des titres de tâche
propres au scénario.

## A. Fonctionnement normal

| # | Commande | Attendu | Observé (sortie, code) | État après | OK |
| --- | --- | --- | --- | --- | --- |
| 1 | `lister` (fichier absent) | message, pas d'erreur | `Aucune tâche.` (0) | pas de fichier créé | oui |
| 2 | `ajouter "Réviser le chapitre 3" -p haute` | tâche 1, priorité haute | `Tâche 1 ajoutée : Réviser le chapitre 3 (priorité haute)` (0) | 1 tâche | oui |
| 3 | `ajouter "Acheter du café"` | tâche 2, priorité par défaut | `Tâche 2 ajoutée : Acheter du café (priorité normale)` (0) | 2 tâches | oui |
| 4 | `ajouter "   Ranger    le  bureau " -p basse` | espaces superflus supprimés | `Tâche 3 ajoutée : Ranger le bureau (priorité basse)` (0) | 3 tâches | oui |
| 5 | `lister` | tri haute, normale, basse | lignes 1, 2, 3 dans cet ordre, `-- 3 tâche(s), 3 à faire` (0) | inchangé | oui |
| 6 | `lister --statut a_faire -p haute` | filtres combinés | seule la tâche 1, `-- 1 tâche(s), 1 à faire` (0) | inchangé | oui |
| 7 | `terminer 1` | tâche 1 terminée | `Tâche 1 terminée : Réviser le chapitre 3` (0) | 1 terminée | oui |
| 8 | `supprimer 3` | tâche 3 supprimée | `Tâche 3 supprimée : Ranger le bureau` (0) | 2 tâches | oui |
| 9 | `ajouter "Après suppression"` | nouvel id | `Tâche 3 ajoutée : ...` (0) : **l'id 3 est réattribué** (voir [limites](./FORMAT-FICHIER.md#limites-connues)) | 3 tâches | oui, comportement documenté |
| 10 | `lister --statut terminee` | uniquement les terminées | tâche 1 `[x]`, `-- 1 tâche(s), 0 à faire` (0) | inchangé | oui |

## B. Cas invalides (le fichier ne doit pas changer)

| # | Commande | Attendu | Observé (sortie, code) | OK |
| --- | --- | --- | --- | --- |
| 11 | `terminer 1` (déjà terminée) | erreur | `Erreur : la tâche 1 est déjà terminée` (1) | oui |
| 12 | `terminer 99` | erreur | `Erreur : aucune tâche avec l'identifiant 99` (1) | oui |
| 13 | `terminer abc` | refus d'usage | `error: argument id: invalid int value: 'abc'` (2) | oui |
| 14 | `supprimer 3` puis encore `supprimer 3` | 2e appel en erreur | `Erreur : aucune tâche avec l'identifiant 3` (1) | oui |
| 15 | `ajouter ""` | erreur | `Erreur : le titre ne peut pas être vide` (1) | oui |
| 16 | `ajouter` + 101 caractères | erreur | `Erreur : le titre dépasse 100 caractères` (1) | oui |
| 17 | `ajouter x -p urgente` | refus d'usage | `invalid choice: 'urgente' (choose from 'basse', 'normale', 'haute')` (2) | oui |
| 18 | *(aucune commande)* | aide d'usage | `error: the following arguments are required: commande` (2) | oui |
| 19 | `-f /proc/nope/x.json ajouter x` | erreur d'écriture claire, pas de trace Python | `Erreur : écriture impossible dans /proc/nope/x.json (No such file or directory)` (1) | oui |

Note : les messages 13, 17 et 18 viennent d'`argparse` et sont en anglais.

## C. Fichier de sauvegarde

| # | Contenu du fichier | Attendu | Observé (sortie, code) | OK |
| --- | --- | --- | --- | --- |
| 20 | `[]` (racine = liste) | refusé | `Erreur : ... : clé 'taches' (liste) manquante` (1) | oui |
| 21 | fichier vide | liste vide | `Aucune tâche.` (0) | oui |
| 22 | deux tâches d'`id` 1 | refusé | `Erreur : ... : identifiant en double : 1` (1) | oui |
| 23 | `{"taches":[{"id":1}]}` | refusé | `Erreur : ... : tâche n°1 : titre manquant ou invalide` (1) | oui |
| 24 | `{casse` (capture 05) | refusé, fichier intact | `Erreur : ... n'est pas du JSON valide (Expecting property name ...)`, `code de sortie : 1`, le `cat` montre `{casse` inchangé | oui |
| 25 | persistance, captures 03 et 04 | mêmes tâches après fermeture du terminal | liste identique dans un nouveau terminal, ajout suivant = id 5 | oui |

Aucun fichier temporaire (`.taches-*.tmp`) n'est resté dans le dossier après les
essais.

## Bilan

25 cas exécutés, 25 conformes à l'attendu. Aucune trace d'erreur Python
(`Traceback`) n'est apparue. Un comportement à connaître, documenté plutôt que
corrigé : la réattribution d'un identifiant libéré par la suppression de la
dernière tâche (cas 9).

Un essai complémentaire, non retenu comme cas de test : sur un fichier en lecture
seule situé dans un dossier modifiable, l'ajout **réussit** (le renommage atomique
remplace le fichier). C'est noté dans les limites du format.
