# PPE Python — Principes de base (classe E3)

Rendus de la semaine PPE du cours *Python — Principes de base*. Chaque projet est
réalisé selon sa fiche ([dépôt du cours](https://github.com/Satom-IT-Learning-Solutions/E3/tree/main/02-python-principes-de-base))
et documenté de la même façon : code, tests automatisés, tests manuels documentés,
notice, et captures d'écran du vrai programme.

Tous les projets utilisent **uniquement la bibliothèque standard de Python 3**
(testé avec Python 3.12.3 sous Linux) : rien à installer.

## Projets

| # | Projet | Niveau | Tests auto. | Cas manuels | État |
| --- | --- | --- | --- | --- | --- |
| 1 | [Calculatrice et convertisseur d'unités](./projet-1-calculatrice-convertisseur/) | Débutant | 20 | 28 | Terminé |
| 2 | [Gestionnaire de tâches en CLI](./projet-2-gestionnaire-taches-cli/) | Débutant / Intermédiaire | 21 | 25 | Terminé |
| 3 | [Analyse d'un fichier CSV de ventes](./projet-3-analyse-csv-ventes/) | Intermédiaire | 29 | 21 | Terminé |
| 4 | Client d'une API publique | Intermédiaire / Avancé | | | À faire |
| 5 | Mini-application testée avec pytest | Avancé | | | À faire |

## Lancer les tests d'un projet

```bash
cd projet-1-calculatrice-convertisseur   # ou projet-2-..., projet-3-...
python3 -m unittest -v
```

## Contenu de chaque projet

| Élément | Rôle |
| --- | --- |
| `README.md` | avancement, conception, captures commentées, difficultés rencontrées, correspondance avec les critères d'évaluation |
| `tests/` | tests automatisés (`unittest`) |
| `TESTS-MANUELS.md` | cas manuels : entrées, résultat attendu, résultat observé |
| `NOTICE.md` | notice d'utilisation |
| `screenshots/` + `tools/capture.sh` | captures du programme réel et script qui les régénère |

## Les captures d'écran

Elles sont produites par un script (`tools/capture.sh` dans chaque projet) : le
programme tourne réellement dans un terminal d'un écran virtuel isolé (Xvfb), les
commandes sont tapées par `xdotool` et capturées par `scrot`. Aucune capture ne montre
le bureau de la machine.
