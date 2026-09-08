#set document(title: "Mieux répartir son argent entre plusieurs fonds", author: "Guillaume Vaudescal")
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
    #text(size: 18pt, weight: "bold")[Mieux répartir son argent entre plusieurs fonds]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-09-08 · #link("https://github.com/Guilou001/01-frontiere-efficiente")[Guilou001/01-frontiere-efficiente]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Comment répartir son argent pour viser un rendement avec moins de variations ? Une frontière efficiente montre les meilleurs compromis calculés sur le passé.

Ce projet la vérifie avec #link("https://github.com/fmilthaler/FinQuant")[FinQuant], puis teste les répartitions sur des mois nouveaux.

*L'optimisation fait mieux aux États-Unis et moins bien au Canada sur les périodes étudiées. L'incertitude reste trop grande pour établir la supériorité d'une règle.*

== Lire la frontière

#figure(image("../results/figures/us/cloud_dirichlet_sample.png", width: 100%), caption: [Répartitions entre onze fonds américains et frontière efficiente vérifiée avec FinQuant])

Chaque point répartit l'argent entre onze fonds négociés en bourse, des paniers achetés comme des actions. À gauche, les rendements varient moins. En haut, leur moyenne est plus élevée.

Le trait foncé donne le portefeuille le moins volatil pour chaque rendement visé. Les cercles verts sont les recalculs de FinQuant. Le cercle violet répartit l'argent également entre les fonds.

La figure décrit janvier 2008 à juillet 2026, sans prévoir l'avenir. La #link("results/figures/canada/cloud_dirichlet_sample.png")[version canadienne] se lit de la même façon.

== Essayer les répartitions sur des mois nouveaux

Chaque mois, le programme choisit les poids avec les 60 mois précédents, puis les applique au mois suivant. Il déduit 0,10 % du montant de chaque achat ou vente, premier achat compris.

Le ratio de Sharpe rapporte le rendement au-delà du placement sans risque à sa variabilité. Plus il est élevé, meilleur est ce compromis sur la période.

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers et période du test*],
    [*Répartition optimisée*],
    [*Répartition égale*],
    [*Écart et intervalle approximatif à 95 %*],
    [États-Unis, janvier 2013 à juillet 2026],
    [0,77],
    [0,51],
    [+0,26 \[−0,15 ; +0,70\]],
    [Canada, janvier 2016 à juillet 2026],
    [0,62],
    [0,73],
    [−0,11 \[−0,54 ; +0,21\]],
)

Les Sharpe sont après coûts et en devise locale. Les périodes diffèrent, donc on compare les règles au sein de chaque univers. #link("results/tables/us/oos_metrics.csv")[Résultats américains] et #link("results/tables/canada/oos_metrics.csv")[canadiens].

== Mesurer ce qui pourrait venir du hasard

Nous reconstruisons 20 000 histoires en tirant des suites de six mois consécutifs. Les deux règles reçoivent toujours les mêmes mois, ce qui préserve leur comparaison.

#figure(image("../results/figures/oos_sharpe_uncertainty.png", width: 100%), caption: [Incertitude de l'écart de Sharpe pour des blocs de trois, six et douze mois])

Les points donnent l'écart observé et les traits son incertitude. Tous traversent zéro. Les données ne départagent donc pas les règles, sans prouver leur équivalence.

Cette analyse réutilise les rendements déjà obtenus. Elle ne recalcule pas les allocations dans chaque histoire et ne corrige pas le choix préalable des fonds. Les hypothèses sont dans la #link("docs/INFERENCE.md")[méthode d'inférence].

FinQuant contrôle le calcul, pas les prévisions.

== Refaire les calculs

#raw("make setup\nmake test\nmake demo\nmake inference", block: true, lang: "bash")

Les tests, la démonstration et l'inférence fonctionnent sans réseau. #raw("make data") puis #raw("make run") reconstruisent les frontières réelles. Une nouvelle collecte peut réviser l'historique.

== Pour aller plus loin

#link("docs/ETUDE_DETAILLEE.md")[Méthodes, résultats complets et références] · #link("rapport/rapport.pdf")[Présentation en PDF] · #link("CITATION.cff")[Citer le projet] · #link("LICENSE")[Licence].

== English summary

Efficient frontiers are checked with FinQuant and tested on subsequent months. Optimization's net Sharpe advantage is positive in the US sample and negative in Canada, but paired block bootstrap intervals include zero in both. This is not evidence that the rules are equivalent.
