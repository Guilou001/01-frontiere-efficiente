# L'écart de Sharpe ne suffit pas à établir une supériorité

[Retour au README](../README.md). Calcul du 6 septembre 2026, rendements arrêtés à juillet 2026.

Les douze intervalles calculés contiennent zéro. Les classements historiques restent descriptifs : ils ne permettent pas de départager les règles au niveau nominal de 95 % avec cette méthode.

## La quantité estimée

Nous comparons la règle de Sharpe maximal à la répartition égale, après les coûts déjà déduits dans le backtest. La covariance est estimée soit sur l'échantillon, soit par Ledoit-Wolf.

Pour chaque mois, le rendement excédentaire est le rendement net moins le taux sans risque du même mois. Le Sharpe publié est la moyenne de ces excédents divisée par leur écart type empirique, puis multipliée par la racine de douze.

L'écart étudié est le Sharpe optimisé moins le Sharpe équipondéré. Il ne s'agit pas du Sharpe de la différence des rendements. L'écart type utilise le diviseur `n − 1`, comme le tableau historique.

L'annualisation conserve la convention du dépôt. Avec des rendements autocorrélés, elle ne représente pas nécessairement le Sharpe d'un rendement cumulé sur douze mois.

## Les mois sont tirés ensemble, par blocs

1. Les dates des deux stratégies et du taux sans risque doivent être identiques, uniques, ordonnées et mensuellement consécutives. Une valeur absente ou non finie provoque une erreur.
2. Pour chaque bloc, un mois de départ est tiré uniformément parmi tous les mois disponibles. Les mois suivants restent consécutifs.
3. Un bloc qui dépasse juillet 2026 continue au début de l'échantillon. Ce retour circulaire donne à chaque mois la même possibilité d'être tiré, mais crée une jonction artificielle explicitement assumée.
4. Les blocs sont concaténés jusqu'à retrouver le nombre initial de mois, soit 163 aux États-Unis et 127 au Canada. Le dernier bloc est tronqué si nécessaire.
5. Le même tirage s'applique aux deux stratégies et au taux sans risque. On conserve ainsi leur dépendance commune au marché et une partie de la dépendance temporelle.
6. L'écart de Sharpe est recalculé 20 000 fois. Les quantiles empiriques à 2,5 % et 97,5 %, avec interpolation linéaire, forment l'intervalle percentile.

Le bloc principal vaut 6 mois. Les blocs de 3 et 12 mois sont des sensibilités définies avant le calcul, sans sélection automatique. La graine est 123, avec un générateur distinct par longueur via `SeedSequence([123, longueur])`.

Les deux estimateurs utilisent les mêmes indices pour faciliter leur comparaison. Les pays sont analysés séparément ; aucun test d'écart entre pays n'est effectué.

Le [bootstrap circulaire documenté par arch](https://bashtage.github.io/arch/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html) décrit le tirage de blocs fixes avec retour au début. Le dépôt implémente ce tirage en NumPy, sans dépendance supplémentaire.

Les [intervalles percentiles documentés par arch](https://bashtage.github.io/arch/bootstrap/confidence-intervals.html) utilisent directement les quantiles des estimations rééchantillonnées. La documentation déconseille de traiter les rendements financiers comme indépendants lorsque leur volatilité persiste.

## Ce que la fourchette permet de dire

Un intervalle entièrement positif indiquerait un avantage de l'optimisation selon cette procédure. Un intervalle entièrement négatif indiquerait un avantage de la répartition égale. Ici, tous contiennent zéro, pour les deux estimateurs et les trois longueurs de blocs.

Cela signifie une absence de conclusion nette avec ces échantillons et ces hypothèses. Cela ne signifie ni que les stratégies sont équivalentes, ni que l'écart est nécessairement dû au hasard.

Le niveau de 95 % est nominal et approximatif. Il décrit la couverture visée lors de répétitions de l'expérience, sous les hypothèses de la méthode. Il n'est pas une probabilité de 95 % que la stratégie gagne.

## Les limites qui comptent

- **Stationnarité supposée.** La distribution des rendements doit rester suffisamment stable et la dépendance s'atténuer avec le temps. Le tirage par blocs ne corrige pas une rupture durable du marché.
- **Histoires de rendements fixées.** Les poids ont été estimés sans information future dans le backtest initial. Ils ne sont pas réestimés dans chaque rééchantillonnage. Les coûts déjà encaissés sont tirés avec les rendements, sans nouvelle facturation aux jonctions des blocs.
- **Sélection non corrigée.** Les fonds survivants, les stratégies et les périodes ont déjà été choisis. Les intervalles sont individuels, sans ajustement pour recherches multiples et sans preuve d'un avantage sur une future période intacte.
- **Méthode non studentisée.** Les intervalles utilisent les seuls quantiles des écarts. Ils ne normalisent pas chaque écart par son erreur type ; leur couverture finie peut différer de 95 %. Elle n'est pas calibrée sur le mécanisme inconnu des marchés étudiés.

[Ledoit et Wolf (2008)](https://www.econ.uzh.ch/dam/jcr%3Affffffff-935a-b0d6-0000-00007214c2bc/jef_2008pdf.pdf) proposent un bootstrap temporel studentisé pour comparer des Sharpe. Leur procédure estime une erreur type dans les tirages. Le présent contrôle est plus simple et ne prétend pas répliquer leur test.

## Rejouer et contrôler

```bash
make inference
make test
make report
```

`make inference` fonctionne sans Yahoo ni données brutes : il lit les rendements de stratégies dérivés déjà publiés. `make run` régénère ces entrées depuis le cache puis exécute aussi l'inférence.

| Fichier | Contenu |
|---|---|
| `results/tables/<univers>/oos_inference_inputs.csv` | Deux rendements nets optimisés, rendement équipondéré et taux sans risque, conservés avec 17 chiffres significatifs |
| `results/tables/<univers>/oos_sharpe_uncertainty.csv` | Écarts, bornes, erreurs types bootstrap et paramètres pour les trois longueurs de blocs |
| `results/tables/sharpe_uncertainty_manifest.json` | Paramètres et empreintes SHA-256 des fichiers d'entrée |
| `results/figures/oos_sharpe_uncertainty.png` | Intervalles et écarts observés, avec un volet par pays |

Les tests vérifient un Sharpe calculé à la main, un bloc circulaire imposé et des quantiles recomposés indépendamment avec pandas. Deux séries identiques doivent donner un intervalle exactement nul. Inverser leur ordre doit inverser les bornes et le signe.

Les tests vérifient aussi l'alignement du taux sans risque et rejettent les mois manquants ainsi que les variances nulles. Un tirage dégénéré n'est jamais supprimé silencieusement.
