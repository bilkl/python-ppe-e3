# Rapport d'exécution des tests

Export généré par [`tools/rapport.sh`](../tools/rapport.sh) (livrable : rapport d'exécution
des tests). Python 3.12.3, pytest 9.2.0, pytest-cov 7.1.0.

| Fichier | Contenu |
| --- | --- |
| [`resultats-pytest.txt`](./resultats-pytest.txt) | sortie `pytest -v` : un test par ligne, avec son résultat |
| [`junit.xml`](./junit.xml) | mêmes résultats au format JUnit XML (lisible par les outils d'intégration continue) |
| [`couverture.txt`](./couverture.txt) | couverture des lignes **et des branches**, module par module |
| [`mutation.txt`](./mutation.txt) | résultat du test de mutation (bugs introduits volontairement) |

Synthèse : **165 tests réussis, 0 échec**, couverture **100 %** des lignes et des branches,
**23 bugs sur 23** détectés par le test de mutation.
