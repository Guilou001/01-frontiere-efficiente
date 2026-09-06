#set document(title: "Choisir un portefeuille : la frontière efficiente et ses limites", author: "Guillaume Vaudescal")
#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1 / 1",
  footer: context [
    #set text(size: 8pt, fill: luma(90))
    #grid(columns: (1fr, auto), align: (left, right),
      [efficient-frontier-mpt], [#counter(page).display("1 / 1", both: true)])
  ],
)
#set text(font: ("Helvetica", "Arial", "DejaVu Sans"), size: 10pt, lang: "fr")
#set par(justify: true, leading: 0.68em, spacing: 1.1em)
#set heading(numbering: none)
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.6em, text(size: 11pt, it))
#show raw.where(block: true): it => block(
  fill: luma(246), inset: 8pt, radius: 3pt, width: 100%, text(size: 8.5pt, it))
#show raw.where(block: false): it => text(size: 9pt, fill: rgb("#1a3f66"), it)
#show quote.where(block: true): it => block(
  inset: (left: 10pt), stroke: (left: 1.5pt + luma(180)),
  text(style: "italic", fill: luma(45), it.body))
// la table NE DOIT PAS être enfermée dans un par() : Typst 0.15 la supprime alors
// entièrement, sans erreur. Le réglage se pose donc dans la portée du bloc.
#show table: it => block(above: 1.1em, below: 1.1em,
  [#set par(justify: false); #text(size: 8.8pt, it)])
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[Choisir un portefeuille : la frontière efficiente et ses limites]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-06 · #link("https://github.com/Guilou001/01-frontiere-efficiente")[Guilou001/01-frontiere-efficiente]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Comment répartir son argent entre plusieurs fonds pour obtenir un rendement donné avec le moins de risque possible ? Ce projet calcule ce compromis, puis vérifie s'il reste avantageux sur des mois nouveaux.

*L'avantage observé de l'optimisation reste statistiquement incertain.* Après coûts, son ratio de Sharpe atteint *0,77 contre 0,51* pour une répartition égale aux États-Unis, et *0,62 contre 0,73* au Canada. Le rééchantillonnage par blocs ne permet de départager les règles dans aucun des deux pays au niveau nominal de 95 %.

Le *ratio de Sharpe* mesure le rendement au-delà du placement sans risque, rapporté à la variabilité de ce rendement. Plus il est élevé, meilleur est ce compromis sur la période étudiée.

#link("rapport/rapport.pdf")[Rapport PDF] · #link("docs/METHODES.md")[Méthodes détaillées] · #link("results/tables/us/")[Résultats américains] · #link("results/tables/canada/")[Résultats canadiens]

#figure(image("../results/figures/us/cloud_dirichlet_sample.png", width: 100%), caption: [Frontière efficiente américaine sur fond blanc, contrôlée avec FinQuant])

Chaque point représente une répartition possible entre onze fonds. Aller vers la gauche réduit la *volatilité*, c'est-à-dire l'ampleur des variations des rendements. Aller vers le haut augmente le rendement estimé.

Le trait foncé forme la *frontière efficiente* : pour chaque rendement cible, il donne le portefeuille le moins volatil sans vente à découvert. Les cercles verts sont des recalculs réalisés avec FinQuant.

Le carré minimise le risque. L'étoile maximise le ratio de Sharpe. Le cercle violet répartit l'argent également entre les fonds, soit environ 9,1 % chacun. Les valeurs viennent du passé et ne prédisent pas les rendements futurs.

== Deux univers de onze fonds

Un *fonds négocié en bourse (FNB)* est un panier de placements qui s'achète comme une action. Les univers mélangent actions, obligations, immobilier et actifs réels.

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [**],
    [*États-Unis*],
    [*Canada*],
    [Devise de mesure],
    [Dollar américain],
    [Dollar canadien],
    [Période de la frontière],
    [Janvier 2008 à juillet 2026],
    [Janvier 2011 à juillet 2026],
    [Nombre de rendements mensuels],
    [223],
    [187],
    [Fonds],
    [SPY, IWM, EFA, EEM, TLT, IEF, LQD, HYG, GLD, DBC, VNQ],
    [XIU, XSP, XIN, XEM, XBB, XCB, XRB, XHY, ZRE, CGL, XEG (suffixe .TO)],
    [Taux sans risque],
    [Bons du Trésor à 3 mois, FRED TB3MS],
    [Bons du Trésor à 3 mois, Banque du Canada TB.CDN.90D.MID],
)

Les prix ajustés viennent de Yahoo Finance. Les rendements utilisent le dernier prix de chaque mois, distributions réinvesties selon les ajustements du fournisseur. Le cache et son manifeste conservent les dates et empreintes des fichiers.

Les données brutes restent locales. La mise à jour visuelle et le contrôle FinQuant utilisent le même échantillon, arrêté à juillet 2026.

== FinQuant vérifie le calcul de la frontière

#link("https://github.com/fmilthaler/FinQuant")[FinQuant] est intégré au pipeline en version *0.7.0*, avec ses dépendances verrouillées. Il recalcule les portefeuilles avec SLSQP, un autre algorithme que le solveur quadratique Clarabel du dépôt.

Les deux moteurs reçoivent les mêmes rendements moyens, covariances, taux sans risque et contraintes. Le contrôle porte sur 60 rendements cibles par univers et par estimateur.

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers*],
    [*Estimation de la covariance*],
    [*Cibles*],
    [*Écart maximal de volatilité (pb)*],
    [États-Unis],
    [Échantillon],
    [60],
    [0,069],
    [États-Unis],
    [Ledoit-Wolf],
    [60],
    [0,054],
    [Canada],
    [Échantillon],
    [60],
    [0,861],
    [Canada],
    [Ledoit-Wolf],
    [60],
    [0,615],
)

Un point de base (pb) vaut 0,01 point de pourcentage. L'écart reste donc inférieur à 0,01 point de volatilité dans les quatre cas. Cela vérifie le calcul, pas la capacité de prévoir les marchés.

Les sorties détaillées sont dans #raw("results/tables/<univers>/finquant_check_<estimateur>.csv") : poids, rendements obtenus, écarts aux cibles et écarts au solveur du dépôt.

Deux adaptations sont explicites dans #link("src/efficient_frontier/finquant_bridge.py")[finquant\_bridge.py]. La première harmonise l'annualisation interne de FinQuant avec nos moments mensuels déjà annualisés. La seconde adapte temporairement son contrôle des types à NumPy 2. Les fonctions d'optimisation de la bibliothèque restent inchangées.

== Le test décisif utilise des mois nouveaux

Pour chaque mois, le programme estime les paramètres sur les *60 mois précédents*, choisit les poids, puis applique ces poids au mois suivant. Il répète cette opération jusqu'à juillet 2026.

Il déduit *10 points de base par montant négocié*, achat ou vente, en tenant compte des poids qui dérivent entre deux rééquilibrages. Le premier achat est également facturé.

#table(
  columns: 6,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers*],
    [*Règle*],
    [*Croissance annuelle composée*],
    [*Volatilité annuelle*],
    [*Sharpe*],
    [*Perte maximale*],
    [États-Unis],
    [Sharpe maximal],
    [8,06 %],
    [8,39 %],
    [0,77],
    [-20,4 %],
    [États-Unis],
    [Répartition égale],
    [6,12 %],
    [9,18 %],
    [0,51],
    [-19,5 %],
    [États-Unis],
    [Risque minimal],
    [2,90 %],
    [5,20 %],
    [0,24],
    [-15,7 %],
    [États-Unis],
    [Inverse de la volatilité],
    [5,24 %],
    [7,90 %],
    [0,47],
    [-19,2 %],
    [Canada],
    [Sharpe maximal],
    [8,27 %],
    [10,94 %],
    [0,62],
    [-18,0 %],
    [Canada],
    [Répartition égale],
    [8,56 %],
    [9,33 %],
    [0,73],
    [-17,6 %],
    [Canada],
    [Risque minimal],
    [2,33 %],
    [5,81 %],
    [0,11],
    [-14,8 %],
    [Canada],
    [Inverse de la volatilité],
    [6,36 %],
    [7,58 %],
    [0,61],
    [-14,1 %],
)

Source : #raw("oos_metrics.csv") de chaque univers. Les règles optimisées utilisent ici la covariance échantillon. La règle inverse de la volatilité attribue davantage de poids aux fonds les moins volatils.

Le test américain couvre janvier 2013 à juillet 2026, et le canadien janvier 2016 à juillet 2026. Les périodes diffèrent : le tableau compare les règles au sein de chaque univers.

Au Canada, maximiser le Sharpe estimé fait moins bien que répartir également l'argent. Stabiliser les covariances avec la méthode de Ledoit-Wolf ne renverse pas ce résultat : le Sharpe de la règle optimisée descend à 0,57.

#figure(image("../results/figures/canada/cloud_dirichlet_sample.png", width: 100%), caption: [Frontière efficiente canadienne sur fond blanc, contrôlée avec FinQuant])

Même lecture que pour les États-Unis. Le portefeuille optimisé sur toute la période semble avantageux sur cette figure, mais le tableau précédent montre que cet avantage ne se maintient pas sur des mois nouveaux.

== Les écarts observés restent incertains

Le *bootstrap par blocs* rééchantillonne des suites de mois consécutifs pour mesurer l'incertitude de l'écart de Sharpe. Il garde les deux stratégies sur les mêmes mois.

Nous tirons 20 000 histoires de même longueur, avec des blocs de 6 mois. Les quantiles à 2,5 % et 97,5 % donnent les intervalles approximatifs à 95 %. Les hypothèses sont détaillées dans la #link("docs/INFERENCE.md")[méthode d'inférence].

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers*],
    [*Covariance de la règle optimisée*],
    [*Écart de Sharpe contre répartition égale*],
    [*Intervalle à 95 %*],
    [États-Unis],
    [Échantillon],
    [+0,26],
    [\[−0,15 ; +0,70\]],
    [États-Unis],
    [Ledoit-Wolf],
    [+0,18],
    [\[−0,24 ; +0,61\]],
    [Canada],
    [Échantillon],
    [−0,11],
    [\[−0,54 ; +0,21\]],
    [Canada],
    [Ledoit-Wolf],
    [−0,16],
    [\[−0,55 ; +0,15\]],
)

Source : #raw("oos_sharpe_uncertainty.csv") de chaque univers, blocs de 6 mois. Un écart positif favorise l'optimisation. Chaque intervalle contient zéro : ces données ne permettent pas d'établir la supériorité d'une règle. Cela ne prouve pas leur équivalence.

#figure(image("../results/figures/oos_sharpe_uncertainty.png", width: 100%), caption: [Incertitude de l'écart de Sharpe, intervalles à 95 % pour des blocs de 3, 6 et 12 mois])

Les points donnent les écarts observés et les traits leur incertitude. Les *douze intervalles* traversent zéro, y compris avec des blocs de 3 et 12 mois. Les tailles de blocs ont été fixées avant ce calcul ; aucune n'a été choisie pour favoriser un résultat.

Cette analyse reste conditionnelle aux rendements déjà produits. Elle ne réestime pas les allocations dans chaque histoire et ne corrige pas le choix préalable des fonds ou des stratégies.

== Ce que le dépôt permet aussi d'explorer

- *Les limites du tirage au hasard.* Même 50 000 portefeuilles simulés manquent les meilleures allocations, surtout lorsqu'elles se concentrent sur quelques fonds.
- *L'incertitude des estimations.* Deux estimateurs de covariance et 200 rééchantillonnages des mois montrent comment les poids et la frontière changent.
- *La composition des portefeuilles.* Les cartes de poids montrent quels fonds sont retenus le long de la frontière et au fil du test mensuel.

Les démonstrations, références et figures secondaires sont dans #link("docs/METHODES.md")[Méthodes et résultats détaillés]. Les fichiers #raw("cloud_interactive_<estimateur>.html") permettent aussi de survoler les points pour lire leurs poids, après téléchargement et ouverture dans un navigateur.

== Reproduire les résultats

Prérequis : Python 3.12 et #link("https://docs.astral.sh/uv/")[uv].

#raw("make setup         # installe les versions verrouillées, FinQuant compris\nmake data          # télécharge les données si le cache est absent\nmake run           # deux univers, FinQuant, figures et inférence par blocs\nmake report        # régénère ce README en PDF", block: true, lang: "bash")

Sans accès aux données de marché :

#raw("make demo          # données synthétiques, résultats dans results/demo/\nmake inference     # rejoue les intervalles depuis les rendements dérivés publiés\nmake test          # tests sans téléchargement\nmake lint          # contrôle du code", block: true, lang: "bash")

Les graines sont fixées à 123. Les calculs de portefeuille utilisent NumPy, pandas, SciPy et cvxpy ; les figures utilisent Matplotlib et Plotly. Une nouvelle collecte Yahoo peut réviser l'historique : conserver le cache pour reproduire exactement les chiffres publiés.

== Limites et suites utiles

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Limite*],
    [*Traitement*],
    [Moyennes et covariances estimées sur le passé],
    [Rééchantillonnage et test sur des mois nouveaux ; les rendements restent incertains],
    [Fonds choisis parmi les survivants disponibles en 2026],
    [Biais reconnu ; aucun fonds fermé n'est réintroduit],
    [Coût de transaction fixe],
    [Rotation publiée ; fiscalité et impact de marché non modélisés],
    [Différences entre les périodes américaine et canadienne],
    [Comparaison des règles dans chaque univers, sans attribuer l'écart entre pays à une cause unique],
    [Dépendances entre les mois],
    [Blocs de 3, 6 et 12 mois pour l'inférence ; rééchantillonnage indépendant conservé pour la frontière de Michaud],
    [Intervalles de confiance],
    [Méthode percentile approximative, stationnarité supposée, comparaisons individuelles sans correction des choix multiples],
    [Solveur FinQuant],
    [Contraintes et valeurs finies vérifiées ; écarts aux solutions QP publiés, sans assimilation à une preuve générale d'optimalité],
)

Une analyse des coûts variables et un plafond de poids par fonds permettraient de tester la stabilité des conclusions. Une nouvelle période laissée intacte permettrait ensuite d'évaluer des règles fixées à l'avance.

== Références et crédits

Le projet applique Markowitz (1952), Sharpe (1964, 1966), Merton (1972), Ledoit-Wolf (2004) et Michaud (1998). La comparaison à une allocation égale suit la question de DeMiguel, Garlappi et Uppal (2009). Il applique leurs méthodes à ces FNB ; il ne réplique pas leurs tableaux d'origine.

#link("docs/METHODES.md#10-références")[Bibliographie complète]. #link("https://github.com/fmilthaler/FinQuant")[FinQuant, code source et licence MIT] : Frederik Milthaler et contributeurs. Données : Yahoo Finance, FRED et Banque du Canada.

Code MIT ; texte, tableaux et figures CC BY 4.0. Auteur : Guillaume Vaudescal, M. Sc. économique, UQAM (2024). #link("CITATION.cff")[Citation]. Code préparé avec assistance IA et vérifié par des tests et des recalculs indépendants.

*English summary.* FinQuant validates 240 efficient-frontier portfolios, with volatility discrepancies below one basis point. Observed net Sharpe favours optimisation in the US and equal weighting in Canada. All twelve paired block-bootstrap percentile intervals include zero at the nominal 95% level (20,000 draws; 3, 6 and 12-month blocks). This conditional analysis neither re-fits allocations nor adjusts for strategy selection. Both samples end in July 2026 but start on different dates.
