# Notice d'utilisation

## Lancer le programme

```bash
python3 calculatrice.py
```

Python 3.8 ou plus récent suffit, aucune installation supplémentaire.

## Utiliser le menu

Le menu s'affiche après chaque opération. Tapez le **numéro** de l'action puis
`Entrée`.

| Numéro | Action |
| --- | --- |
| 1 à 6 | Calcul : addition, soustraction, multiplication, division, puissance, modulo |
| 7 | Conversion de température |
| 8 | Conversion de longueur |
| 9 | Conversion de poids |
| 0 | Quitter |

### Faire un calcul

Choisissez 1 à 6, puis entrez le premier et le second nombre. Le résultat
s'affiche sous la forme `12.5 + 7.5 = 20`.

### Faire une conversion

Choisissez 7, 8 ou 9, puis entrez la valeur, l'unité de départ et l'unité
d'arrivée. Les unités possibles sont rappelées entre parenthèses.

| Grandeur | Unités |
| --- | --- |
| Température | `C`, `F`, `K` |
| Longueur | `mm`, `cm`, `m`, `km`, `in`, `ft`, `yd`, `mi` |
| Poids | `mg`, `g`, `kg`, `t`, `oz`, `lb` |

## Bon à savoir

- La virgule (`2,5`) et le point (`2.5`) sont tous deux acceptés.
- Les unités peuvent s'écrire en majuscules ou minuscules.
- Une saisie invalide (texte, vide, unité inconnue) est refusée et
  **redemandée** : le programme ne s'arrête pas.
- Une opération impossible (division par zéro, température sous le zéro absolu,
  longueur ou poids négatif) affiche un message `! Erreur : ...` et ramène au
  menu.
- `Ctrl+C` ou `Ctrl+D` quitte proprement à tout moment.

## Exemples

```text
Votre choix : 7
  Valeur à convertir : 100
  Unité de départ (C/F/K) : C
  Unité d'arrivée (C/F/K) : F
  Résultat : 100 C = 212 F
```

```text
Votre choix : 4
  Premier nombre : 10
  Second nombre  : 0
  ! Erreur : division par zéro impossible.
```
