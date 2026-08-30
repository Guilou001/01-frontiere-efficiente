#set document(title: "La frontière efficiente de Markowitz, mesurée : Monte Carlo contre programme quadratique, frontière rééchantillonnée et test hors échantillon contre 1/N", author: "Guillaume Vaudescal")
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
#show table: it => block(above: 1.1em, below: 1.1em,
  par(justify: false, text(size: 8.8pt, it)))
#show figure: it => block(above: 1.4em, below: 1.4em, it)
#show figure.caption: it => text(size: 8.5pt, fill: luma(70), it)
#show link: it => text(fill: rgb("#0072B2"), it)

#align(center)[
  #block(width: 100%)[
    #text(size: 18pt, weight: "bold")[La frontière efficiente de Markowitz, mesurée : Monte Carlo contre programme quadratique, frontière rééchantillonnée et test hors échantillon contre 1/N]
    #v(0.6em)
    #text(size: 10pt, fill: luma(70))[Guillaume Vaudescal · 2026-08-29 · #link("https://github.com/Guilou001/01-frontiere-efficiente")[Guilou001/01-frontiere-efficiente]]
  ]
]
#v(1.2em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#v(0.8em)

Markowitz (1952) et Sharpe (1964, 1966) appliqués à 11 FNB américains multi-actifs (2008-01 à 2026-07) et à 11 FNB canadiens (2011-01 à 2026-07). S'y ajoutent le rétrécissement de la covariance de Ledoit et Wolf (2004), la frontière rééchantillonnée de Michaud (1998) et la comparaison hors échantillon à l'équipondéré de DeMiguel, Garlappi et Uppal (2009).

Le même contenu en PDF : #link("rapport/rapport.pdf")[rapport/rapport.pdf].

*Résultat en une phrase.* Sur 50 000 portefeuilles aléatoires, le meilleur ratio de Sharpe, le rendement excédant le taux sans risque par unité de volatilité, plafonne à 0,73 contre 0,80 pour le portefeuille de tangence, le portefeuille de la frontière où ce ratio est maximal, calculé par programme quadratique (FNB américains, 2008-2026) ; hors échantillon, net de 10 points de base par rotation, le portefeuille de Sharpe maximal bat l'équipondéré aux États-Unis (Sharpe 0,77 contre 0,51, 2013-2026) et perd au Canada (0,62 contre 0,73, 2016-2026).

_English summary._ Modern Portfolio Theory on two ETF universes: 11 US multi-asset ETFs (2008-01 to 2026-07, 223 months) and 11 Canadian ETFs in CAD (2011-01 to 2026-07, 187 months). Long-only efficient frontier by quadratic programming (cvxpy, Clarabel), closed-form unconstrained frontier (two-fund theorem), minimum-variance, tangency and capital market line; 50,000 random portfolios per draw (Dirichlet(1) versus uniform-normalised weights) and why the cloud never reaches the frontier's ends; Ledoit-Wolf constant-correlation shrinkage (intensity 0.085 US, 0.203 Canada); Michaud's resampled frontier (200 bootstraps); walk-forward backtest (60-month window, monthly rebalancing, 10 bp one-way costs) of max-Sharpe, min-variance, inverse-vol and 1/N. Measured: the best simulated Sharpe is 0.73 (US) and 0.82 (Canada) against 0.80 and 0.85 for the tangency portfolio; out of sample, max-Sharpe beats 1/N in the US (0.77 vs 0.51) and loses in Canada (0.62 vs 0.73); Ledoit-Wolf inputs do not rescue max-Sharpe (0.69 US, 0.57 Canada). All numbers come from #raw("results/tables/").

#figure(image("../results/figures/us/cloud_dirichlet_sample.png", width: 100%), caption: [Nuage Monte Carlo et frontière efficiente, FNB américains])

_Figure 1. FNB américains, 2008-01 à 2026-07, moments échantillon. 50 000 portefeuilles long-only, c'est-à-dire sans vente à découvert, tirés d'une loi de Dirichlet(1), la loi uniforme sur le simplexe des poids positifs de somme un, et colorés par ratio de Sharpe. Frontière long-only (trait noir), frontière sans contrainte de signe (pointillé gris), portefeuille de variance minimale (carré), portefeuille de tangence (étoile, Sharpe 0,80), droite de marché des capitaux (tirets), les 11 FNB (losanges). Version interactive, survol = poids : \`results/figures/us/cloud\_interactive\_sample.html\`._

Comment lire cette figure : chaque point est un portefeuille simulé, placé par sa volatilité (axe horizontal) et son rendement espéré (axe vertical), puis coloré par son ratio de Sharpe ; à volatilité égale, plus haut est mieux. Le trait noir est la limite atteignable sans vente à découvert : aucun point ne la franchit, et l'écart entre le nuage et ses deux extrémités est mesuré en section 5.2.

== 1. Ce que c'est, ce que ce n'est pas

C'est une mise en œuvre complète et testée de la théorie moderne du portefeuille sur des données publiques, avec des paquets Python courants (numpy, pandas, scipy, cvxpy, matplotlib, seaborn, plotly, yfinance) et des résultats mesurés plutôt que racontés. Les paramètres sont fixés avant l'exécution et ne sont pas ajustés après coup : fenêtre de 60 mois, 10 points de base, graine 123, 50 000 tirages, 200 bootstraps, le bootstrap étant un rééchantillonnage avec remise des mois observés. La partie dans l'échantillon (sections 5.1 à 5.4) et la partie hors échantillon (section 5.5) sont séparées une fois pour toutes.

Ce n'est pas un conseil d'investissement, ni une étude des rendements futurs. Les frontières sont calculées sur des moments estimés sur le passé ; la section 5.5 montre ce qu'ils valent une fois sortis de l'échantillon.

== 2. Papiers et éléments répliqués

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Élément*],
    [*Référence*],
    [*Fichier produit*],
    [*Code*],
    [Frontière moyenne-variance long-only, variance minimale],
    [Markowitz (1952)],
    [#raw("results/tables/<univers>/frontier_<est>.csv"), #raw("special_portfolios_<est>.csv")],
    [#raw("frontier.py") : #raw("FrontierSolver"), #raw("efficient_frontier")],
    [Frontière sans contrainte de signe, théorème des deux fonds],
    [Merton (1972)],
    [colonne #raw("vol_unconstrained") de #raw("frontier_<est>.csv")],
    [#raw("frontier.py") : #raw("closed_form_frontier")],
    [Portefeuille de tangence, droite de marché des capitaux, ratio de Sharpe],
    [Sharpe (1964, 1966)],
    [#raw("special_portfolios_<est>.csv")],
    [#raw("frontier.py") : #raw("FrontierSolver.tangency"), #raw("capital_market_line")],
    [Rétrécissement vers la corrélation constante],
    [Ledoit et Wolf (2004)],
    [#raw("moments_ledoit_wolf.csv"), #raw("summary_ledoit_wolf.json") (intensité)],
    [#raw("estimation.py") : #raw("ledoit_wolf_constant_correlation")],
    [Frontière rééchantillonnée],
    [Michaud (1998)],
    [#raw("resampled_frontier_<est>.csv")],
    [#raw("montecarlo.py") : #raw("resampled_frontier")],
    [Comparaison hors échantillon à 1/N],
    [DeMiguel, Garlappi et Uppal (2009)],
    [#raw("oos_metrics.csv"), #raw("oos_returns.csv")],
    [#raw("backtest.py") : #raw("walk_forward")],
    [Diversification maximale (portefeuille de référence supplémentaire)],
    [Choueifaty et Coignard (2008)],
    [#raw("special_portfolios_<est>.csv")],
    [#raw("frontier.py") : #raw("FrontierSolver.max_diversification")],
)

Ce qui n'est pas répliqué : les tableaux chiffrés de ces papiers (autres univers, autres périodes). Le dépôt applique leurs méthodes à deux univers de FNB et mesure ce qu'elles donnent.

== 3. Données

#table(
  columns: 3,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [**],
    [*FNB américains*],
    [*FNB canadiens*],
    [Tickers],
    [SPY, IWM, EFA, EEM, TLT, IEF, LQD, HYG, GLD, DBC, VNQ],
    [XIU.TO, XSP.TO, XIN.TO, XEM.TO, XBB.TO, XCB.TO, XRB.TO, XHY.TO, ZRE.TO, CGL.TO, XEG.TO],
    [Classes couvertes],
    [actions É.-U. grandes et petites capitalisations, EAEO, émergents ; Trésor long et intermédiaire, crédit IG et haut rendement ; or, matières premières, FPI],
    [actions canadiennes, É.-U. couvert, EAEO couvert, émergents ; obligations univers, corporatives, à rendement réel, haut rendement couvert ; FPI, or couvert, énergie],
    [Rendements mensuels],
    [2008-01 à 2026-07, 223 mois],
    [2011-01 à 2026-07, 187 mois],
    [Prix],
    [clôtures ajustées quotidiennes Yahoo Finance (yfinance, #raw("auto_adjust=True")), dernier prix du mois],
    [idem],
    [Taux sans risque],
    [bons du Trésor 3 mois, FRED #raw("TB3MS") (mensuel), moyenne 1,38 % par an sur la période],
    [bons du Trésor 3 mois, Banque du Canada #raw("TB.CDN.90D.MID") (quotidien, moyenne mensuelle), 1,54 % par an],
    [Devise],
    [USD],
    [CAD (XSP, XIN, XHY et CGL sont couverts contre le dollar américain)],
)

Choix et abandons, vérifiés sur Yahoo Finance le 2026-08-23 (#raw("data/raw/manifest.json")) : XEF.TO (MSCI EAEO IMI) commence le 2013-04-15, remplacé par XIN.TO (EAEO couvert, 2002) ; XBM.TO (matériaux) commence le 2012-01-24, écarté ; XEG.TO (énergie, 2001) retenu comme secteur canadien. CGL.TO commence le 2010-10-04 et fixe le début de l'univers canadien à 2011-01. L'univers américain démarre en 2008-01 parce que HYG (2007-04) est le dernier venu.

Les prix ne sont pas versionnés (conditions d'utilisation de Yahoo Finance) : #raw("make data") les télécharge dans #raw("data/raw/") (parquet) avec un manifeste (date, tickers, bornes, sha256). Les séries FRED et Banque du Canada sont publiques et téléchargées sans clé. Seules les sorties dérivées (tables CSV, figures) sont dans le dépôt.

== 4. Méthode

#raw("flowchart LR\n  A[prix ajustés quotidiens<br>yfinance] --> B[rendements mensuels simples]\n  R[taux sans risque<br>FRED / BdC] --> B\n  B --> C{estimateur}\n  C -->|sample| D[moyenne, covariance ddof 1, x12]\n  C -->|ledoit_wolf| E[covariance rétrécie<br>vers la corrélation constante]\n  D --> F[frontière long-only QP<br>variance min, tangence, CML]\n  E --> F\n  D --> G[50 000 portefeuilles<br>Dirichlet et uniforme]\n  B --> H[200 bootstraps<br>frontière rééchantillonnée]\n  B --> I[backtest glissant 60 mois<br>4 règles, 10 pb, 2 estimateurs]\n  F --> J[tables CSV, figures PNG/PDF, HTML]\n  G --> J\n  H --> J\n  I --> J", block: true, lang: "mermaid")

Choix qui comptent :

+ Moments annualisés par simple produit par 12 (moyenne arithmétique, covariance), sans correction d'autocorrélation. Le taux sans risque de la frontière est la moyenne des taux mensuels de la période, composée sur l'année.
+ Frontière long-only par programme quadratique (cvxpy, solveur Clarabel), compilé une fois avec des paramètres et résolu pour 60 cibles de rendement entre le minimum de variance et l'actif le plus rentable. La tangence long-only passe par la transformation de Charnes-Cooper (minimiser y'Σy sous (μ - r)'y = 1, y ≥ 0, puis normaliser), qui en fait un QP exact plutôt qu'une recherche non convexe.
+ Deux tirages de poids pour le Monte Carlo : Dirichlet(1, …, 1), définie sous la figure 1, et vecteur uniforme normalisé par sa somme, qui se concentre autour de 1/N. Les deux sont vectorisés (un produit matriciel et un #raw("einsum"), aucune boucle sur les portefeuilles).
+ Frontière rééchantillonnée : 200 bootstraps i.i.d. des mois, les tirages étant indépendants et identiquement distribués, ré-estimation, frontière à 30 rangs, moyenne des poids par rang, statistiques évaluées sous les moments d'origine.
+ Backtest glissant : à chaque fin de mois, moments estimés sur les 60 mois précédents, poids cibles tenus le mois suivant, dérive des poids entre deux rééquilibrages, coût de 10 points de base par unité de rotation aller simple. Quatre règles : Sharpe maximal, variance minimale, inverse de la volatilité, 1/N ; les deux premières sous moments échantillon et sous Ledoit-Wolf. TCAC, le taux de croissance annuel composé, en années civiles (jours / 365,25) ; Sharpe sur rendements excédentaires mensuels × √12 ; perte maximale sur la richesse cumulée ; rotation annuelle moyenne.

== 5. Résultats (mesurés, copiés de #raw("results/tables/"))

=== 5.1 Dans l'échantillon : trois FNB suffisent au portefeuille de tangence

#table(
  columns: 6,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers, estimateur*],
    [*Portefeuille*],
    [*Rendement*],
    [*Volatilité*],
    [*Sharpe*],
    [*Poids supérieurs à 0,5 %*],
    [É.-U., échantillon],
    [variance minimale],
    [3,30 %],
    [5,41 %],
    [0,36],
    [IEF 73,2 %, HYG 14,7 %, DBC 12,1 %],
    [É.-U., échantillon],
    [tangence],
    [9,00 %],
    [9,49 %],
    [0,80],
    [SPY 48,9 %, IEF 26,2 %, GLD 24,9 %],
    [É.-U., échantillon],
    [équipondéré],
    [6,54 %],
    [10,79 %],
    [0,48],
    [11 × 9,1 %],
    [É.-U., Ledoit-Wolf (δ = 0,085)],
    [variance minimale],
    [3,34 %],
    [5,56 %],
    [0,35],
    [IEF 73,1 %, HYG 16,1 %, DBC 10,8 %],
    [É.-U., Ledoit-Wolf (δ = 0,085)],
    [tangence],
    [9,22 %],
    [9,90 %],
    [0,79],
    [SPY 50,6 %, GLD 25,9 %, IEF 23,6 %],
    [Canada, échantillon],
    [variance minimale],
    [3,00 %],
    [4,78 %],
    [0,31],
    [XBB 95,0 %, XEG 3,8 %, XIN 1,2 %],
    [Canada, échantillon],
    [tangence],
    [11,30 %],
    [11,51 %],
    [0,85],
    [XSP 63,7 %, CGL 18,9 %, XIU 17,4 %],
    [Canada, échantillon],
    [équipondéré],
    [6,90 %],
    [8,72 %],
    [0,61],
    [11 × 9,1 %],
    [Canada, Ledoit-Wolf (δ = 0,203)],
    [variance minimale],
    [3,06 %],
    [4,78 %],
    [0,32],
    [XBB 62,5 %, XCB 35,3 %, XEG 1,1 %, XHY 0,7 %],
    [Canada, Ledoit-Wolf (δ = 0,203)],
    [tangence],
    [11,27 %],
    [11,50 %],
    [0,85],
    [XSP 57,1 %, XIU 29,7 %, CGL 13,2 %],
)

Sources : #raw("special_portfolios_<est>.csv") et #raw("summary_<est>.json") dans #raw("results/tables/us/") et #raw("results/tables/canada/"). Lecture : sur 11 actifs, l'optimiseur n'en garde que trois à la tangence et trois ou quatre au minimum de variance ; les huit autres ont un poids nul. La contrainte de positivité coûte cher en volatilité. Au rendement de la tangence américaine (8,98 %), la frontière sans contrainte de signe atteint 6,54 % de volatilité contre 9,46 % en long-only (#raw("frontier_sample.csv"), colonne #raw("vol_unconstrained")). Ce gain exige des ventes à découvert qu'un investisseur en FNB ne fait pas.

#figure(image("../results/figures/us/transition_map_sample.png", width: 100%), caption: [Carte de transition, FNB américains])

_Figure 2. Poids le long de la frontière long-only américaine en fonction de la volatilité cible : IEF domine le bas de la frontière, SPY et GLD le haut. La légende ne liste que les FNB dont le poids dépasse 0,5 % quelque part sur la frontière ; IWM, EFA, EEM, LQD et VNQ, jamais retenus par l'optimiseur, en sont exclus._

Comment lire cette figure : chaque bande verticale est un portefeuille de la frontière, les aires empilées sont ses poids et somment à 100 % ; on lit à volatilité fixée quelles classes composent le portefeuille.

=== 5.2 Le nuage Monte Carlo n'atteint jamais les extrémités de la frontière

#table(
  columns: 10,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers, tirage*],
    [*Meilleur Sharpe simulé*],
    [*Sharpe de tangence*],
    [*Vol. min. simulée*],
    [*Vol. du min. de variance*],
    [*Rend. max. simulé*],
    [*Rend. max. de la frontière*],
    [*Écart médian de vol. à la frontière*],
    [*Part à moins de 1 pt de la frontière*],
    [*Part avec un poids ≥ 50 %*],
    [É.-U., Dirichlet],
    [0,73],
    [0,80],
    [6,06 %],
    [5,41 %],
    [10,32 %],
    [11,89 %],
    [4,12 pt],
    [0,06 %],
    [1,08 %],
    [É.-U., uniforme normalisé],
    [0,68],
    [0,80],
    [7,22 %],
    [5,41 %],
    [9,58 %],
    [11,89 %],
    [4,00 pt],
    [0,00 %],
    [0,00 %],
    [Canada, Dirichlet],
    [0,82],
    [0,85],
    [5,34 %],
    [4,78 %],
    [10,73 %],
    [12,94 %],
    [1,87 pt],
    [7,89 %],
    [1,08 %],
    [Canada, uniforme normalisé],
    [0,77],
    [0,85],
    [6,17 %],
    [4,78 %],
    [9,42 %],
    [12,94 %],
    [1,82 pt],
    [3,58 %],
    [0,00 %],
)

Source : #raw("montecarlo_summary_sample.csv") (50 000 portefeuilles par ligne, graine 123). Lecture : la colonne « Meilleur Sharpe simulé » se compare à « Sharpe de tangence », « Vol. min. simulée » à « Vol. du min. de variance », « Rend. max. simulé » à « Rend. max. de la frontière » ; les trois dernières colonnes mesurent la distance du nuage à la frontière. Trois constats. 1) Aucun des quatre tirages n'atteint la frontière : le meilleur des 50 000 portefeuilles reste sous la tangence (0,73 contre 0,80 aux É.-U., 0,82 contre 0,85 au Canada) et aucune volatilité simulée ne descend au minimum de variance (6,06 % contre 5,41 % aux É.-U.). 2) Le tirage uniforme normalisé fait pire que Dirichlet aux deux bouts de la frontière : Sharpe 0,68 contre 0,73 et volatilité minimale 7,22 % contre 6,06 % aux É.-U., aucun portefeuille à moins de 1 point de la frontière ni avec un poids au-dessus de 50 % ; seul l'écart médian est comparable (4,00 contre 4,12 pt). 3) Le nuage canadien colle davantage à la frontière (écart médian 1,87 point contre 4,12 ; 7,89 % des tirages à moins de 1 point contre 0,06 %) : l'équipondéré canadien, autour duquel les tirages se concentrent, part moins loin de sa tangence (Sharpe 0,61 contre 0,85, tableau 5.1) que l'américain (0,48 contre 0,80).

Pourquoi le nuage ne touche pas la frontière. Les extrémités de la frontière sont des portefeuilles concentrés. Le rendement maximal est un seul FNB (SPY ou XSP.TO à 100 %) ; le minimum de variance met 73 % dans IEF ou 95 % dans XBB.TO. Or un tirage uniforme sur le simplexe à 11 actifs donne un poids maximal médian de 26,2 % et ne dépasse 50 % que dans 1,08 % des cas. Le tirage uniforme normalisé est pire : poids maximal médian de 16,7 %, 99e centile à 25,6 %, aucun portefeuille au-dessus de 50 %. Sous Dirichlet(1), la probabilité qu'un poids dépasse 95 % vaut 11 × 0,05^10, soit environ 10^-12 (calcul, non simulé) : il faudrait mille milliards de tirages pour voir un seul portefeuille proche d'un sommet. C'est pourquoi le nuage reste un ovale au centre du diagramme, d'autant plus compact que le tirage est normalisé. Aux États-Unis, aucun des 100 000 portefeuilles simulés n'atteint 0,75 de Sharpe ni ne descend sous 6 % de volatilité ; le QP trouve 0,80 et 5,41 % en 3 millisecondes (tangence et variance minimale, mesuré). Le Monte Carlo illustre la forme du problème ; il ne le résout pas.

#figure(image("../results/figures/canada/cloud_uniform_sample.png", width: 100%), caption: [Nuage Monte Carlo, tirage uniforme normalisé, FNB canadiens])

_Figure 3. FNB canadiens, tirage uniforme normalisé : le nuage est plus compact que sous Dirichlet (figure 1) et s'éloigne davantage de la frontière. XEM.TO, XRB.TO, XHY.TO et ZRE.TO ne reçoivent aucun poids sur la frontière ; XEG.TO (énergie, 29,2 % de volatilité) n'y entre qu'au minimum de variance (3,8 % au plus)._

Comment lire cette figure : mêmes conventions que la figure 1 ; seul le tirage change (vecteur uniforme normalisé par sa somme au lieu de Dirichlet), le nuage se resserre autour de l'équipondéré et le vide entre le nuage et la frontière s'élargit.

=== 5.3 La frontière rééchantillonnée diversifie davantage et plafonne plus bas

#table(
  columns: 4,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers (moments échantillon)*],
    [*Meilleur Sharpe sur la frontière*],
    [*Actifs au-dessus de 0,5 % à ce point*],
    [*Rendement maximal atteint*],
    [É.-U., analytique (QP)],
    [0,80],
    [3 (SPY, IEF, GLD)],
    [11,89 % (SPY seul)],
    [É.-U., rééchantillonnée (200 bootstraps)],
    [0,77],
    [9 (SPY 44,4 %, GLD 22,8 %, IEF 15,7 %, TLT 7,0 %, LQD 3,2 %, IWM 2,1 %, HYG 2,1 %, VNQ 1,8 %, DBC 0,8 %)],
    [10,67 % au rang 27 sur 30, puis 10,46 % au dernier rang],
    [Canada, analytique (QP)],
    [0,85],
    [3 (XSP, CGL, XIU)],
    [12,94 % (XSP seul)],
    [Canada, rééchantillonnée],
    [0,80],
    [9 (XSP 39,9 %, CGL 15,3 %, XIU 14,3 %, XIN 7,4 %, XBB 6,3 %, ZRE 5,6 %, XCB 4,2 %, XEG 3,9 %, XEM 2,6 %)],
    [11,15 %],
)

Sources : #raw("frontier_sample.csv"), #raw("resampled_frontier_sample.csv"). Lecture : moyenner les poids de 200 frontières bootstrap redonne un poids à neuf actifs sur onze, au prix de 0,03 à 0,05 de Sharpe évalué sous les moments d'origine. Le haut de la frontière rééchantillonnée américaine rebrousse chemin : le rendement baisse de 10,67 % à 10,46 % entre les rangs 27 et 30. Les bootstraps ne s'accordent pas sur l'actif le plus rentable, et leur moyenne mélange SPY, GLD, VNQ et IWM (figure 4, droite). Michaud présente ce repli comme une propriété de la méthode, pas comme un défaut ; il signifie que le portefeuille « rendement maximal » est celui dont l'estimation est la moins sûre.

#figure(image("../results/figures/us/resampled_vs_analytical_sample.png", width: 100%), caption: [Frontière rééchantillonnée contre analytique, FNB américains])

_Figure 4. Gauche : frontière analytique (noir) et rééchantillonnée (orange), toutes deux évaluées sous les moments d'origine. Droite : poids moyens rééchantillonnés le long de la frontière, à comparer à la figure 2._

Comment lire cette figure : à gauche, les deux frontières sont notées sous les mêmes moments, donc comparables point à point ; la rééchantillonnée reste sous l'analytique et rebrousse chemin en haut. À droite, même construction que la figure 2, mais avec les poids moyens des 200 bootstraps : neuf FNB au lieu de trois portent la frontière.

=== 5.4 Ledoit-Wolf déplace peu la frontière et n'aide pas hors échantillon

L'intensité de rétrécissement estimée est de 0,085 avec 223 mois (É.-U.) et de 0,203 avec 187 mois (Canada) : la covariance échantillon est déplacée de 8,5 % et de 20,3 % vers la cible à corrélation constante (corrélation moyenne 0,38 aux États-Unis, 0,45 au Canada). Dans l'échantillon, la tangence américaine passe de SPY 48,9 % / IEF 26,2 % / GLD 24,9 % à SPY 50,6 % / GLD 25,9 % / IEF 23,6 %. La canadienne passe de XSP 63,7 % / CGL 18,9 % / XIU 17,4 % à XSP 57,1 % / XIU 29,7 % / CGL 13,2 %. Hors échantillon (section 5.5), le Sharpe maximal sous Ledoit-Wolf fait moins bien que sous moments échantillon dans les deux univers : 0,69 contre 0,77 aux États-Unis, 0,57 contre 0,62 au Canada. La variance minimale aussi : 0,20 contre 0,24 et 0,07 contre 0,11. Le rétrécissement répare la covariance, or ce qui déstabilise le portefeuille de tangence est l'estimation des moyennes, que Ledoit-Wolf ne touche pas : c'est l'argument de DeMiguel, Garlappi et Uppal (2009).

=== 5.5 Hors échantillon : le Sharpe maximal gagne aux États-Unis et perd au Canada

Fenêtre de 60 mois, rééquilibrage mensuel, 10 points de base par unité de rotation aller simple.

#table(
  columns: 8,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Univers, période*],
    [*Règle*],
    [*Estimateur*],
    [*TCAC*],
    [*Volatilité*],
    [*Sharpe*],
    [*Perte max.*],
    [*Rotation annuelle*],
    [É.-U., 2013-01 à 2026-07 (163 mois)],
    [Sharpe maximal],
    [échantillon],
    [8,06 %],
    [8,39 %],
    [0,77],
    [−20,4 %],
    [1,90],
    [],
    [Sharpe maximal],
    [Ledoit-Wolf],
    [7,46 %],
    [8,59 %],
    [0,69],
    [−21,6 %],
    [2,06],
    [],
    [variance minimale],
    [échantillon],
    [2,90 %],
    [5,20 %],
    [0,24],
    [−15,7 %],
    [0,79],
    [],
    [variance minimale],
    [Ledoit-Wolf],
    [2,70 %],
    [5,21 %],
    [0,20],
    [−16,1 %],
    [0,75],
    [],
    [inverse de la volatilité],
    [aucun],
    [5,24 %],
    [7,90 %],
    [0,47],
    [−19,2 %],
    [0,36],
    [],
    [équipondéré (1/N)],
    [aucun],
    [6,12 %],
    [9,18 %],
    [0,51],
    [−19,5 %],
    [0,35],
    [Canada, 2016-01 à 2026-07 (127 mois)],
    [Sharpe maximal],
    [échantillon],
    [8,27 %],
    [10,94 %],
    [0,62],
    [−18,0 %],
    [3,20],
    [],
    [Sharpe maximal],
    [Ledoit-Wolf],
    [7,65 %],
    [10,82 %],
    [0,57],
    [−19,6 %],
    [2,80],
    [],
    [variance minimale],
    [échantillon],
    [2,33 %],
    [5,81 %],
    [0,11],
    [−14,8 %],
    [0,71],
    [],
    [variance minimale],
    [Ledoit-Wolf],
    [2,09 %],
    [5,74 %],
    [0,07],
    [−14,9 %],
    [0,63],
    [],
    [inverse de la volatilité],
    [aucun],
    [6,36 %],
    [7,58 %],
    [0,61],
    [−14,1 %],
    [0,33],
    [],
    [équipondéré (1/N)],
    [aucun],
    [8,56 %],
    [9,33 %],
    [0,73],
    [−17,7 %],
    [0,36],
)

Source : #raw("results/tables/<univers>/oos_metrics.csv") ; rendements mensuels dans #raw("oos_returns.csv"). Lecture : aux États-Unis, le portefeuille de Sharpe maximal bat 1/N de 0,26 de Sharpe net. Ses fenêtres glissantes ont surpondéré SPY, IEF puis GLD (figure 8), trois actifs qui ont continué à faire mieux que le reste de l'univers. Au Canada, il perd 0,11 de Sharpe contre 1/N et fait jeu égal avec l'inverse de la volatilité (0,62 contre 0,61). Sa rotation annuelle est de 3,2 contre 0,36 pour 1/N : le portefeuille est renouvelé plus de trois fois par an. Ce n'est donc pas une victoire générale de l'optimisation. DeMiguel, Garlappi et Uppal (2009) ont montré sur 14 règles et 7 jeux de données que 1/N n'est battu de façon fiable par aucune d'elles, et le résultat canadien va dans leur sens. La variance minimale, investie surtout en obligations (IEF aux États-Unis, figure 8), finit avec un TCAC inférieur à 3 % dans les deux univers.

#figure(image("../results/figures/oos_sharpe_bars.png", width: 100%), caption: [Sharpe hors échantillon net par règle, É.-U. et Canada])

_Figure 5. Ratio de Sharpe hors échantillon net par règle, É.-U. (2013-01 à 2026-07) et Canada (2016-01 à 2026-07), moments échantillon pour les règles optimisées. Chiffres copiés de \`oos\_metrics.csv\` des deux univers par \`scripts/plot\_oos\_sharpe.py\`._

Comment lire cette figure : chaque groupe de barres est une règle, la barre bleue l'univers américain, l'orange le canadien ; plus la barre est haute, meilleur est le ratio de Sharpe net. Le classement s'inverse d'un univers à l'autre : le Sharpe maximal domine aux États-Unis (0,77 contre 0,51 pour 1/N) et l'équipondéré domine au Canada (0,73 contre 0,62).

#figure(image("../results/figures/us/oos_growth.png", width: 100%), caption: [Croissance hors échantillon, FNB américains])

_Figure 6. Valeur de 1 dollar investi, net de coûts, FNB américains, 2013-01 à 2026-07 : couleur = règle, trait plein = moments échantillon, tirets = Ledoit-Wolf._

Comment lire cette figure : chaque courbe cumule les rendements mensuels nets d'une règle en partant de 1 ; l'étiquette au bord droit est la valeur finale, colonne #raw("final_wealth") de #raw("oos_metrics.csv"). Le Sharpe maximal (bleu, trait plein) finit premier à 2,86, sa variante Ledoit-Wolf (tirets) derrière à 2,66.

#figure(image("../results/figures/canada/oos_growth.png", width: 100%), caption: [Croissance hors échantillon, FNB canadiens])

_Figure 7. Valeur de 1 dollar investi, net de coûts, FNB canadiens, 2016-01 à 2026-07, mêmes conventions que la figure 6. L'équipondéré finit premier (2,38) devant le Sharpe maximal (2,32), avec une rotation annuelle près de neuf fois moindre (0,36 contre 3,20, \`oos\_metrics.csv\`)._

Comment lire cette figure : mêmes conventions que la figure 6 ; la courbe orange (1/N) reste au-dessus de la bleue (Sharpe maximal) pendant presque toute la période, l'inverse de la figure américaine.

#figure(image("../results/figures/us/oos_weights_sample.png", width: 100%), caption: [Poids glissants hors échantillon, FNB américains])

_Figure 8. Poids cibles mensuels des quatre règles (moments échantillon, FNB américains, 2013-01 à 2026-07). Le Sharpe maximal bascule entre trois ou quatre actifs, la variance minimale vit dans IEF et HYG, l'inverse de la volatilité et 1/N bougent à peine._

Comment lire cette figure : quatre sous-figures, une par règle ; dans chacune, les aires empilées sont les poids du portefeuille au début de chaque mois et somment à 100 %. Une règle stable dessine des bandes horizontales (1/N, en bas à droite) ; une règle instable dessine des à-coups verticaux (Sharpe maximal, en haut à gauche).

Les autres figures canadiennes et les variantes Ledoit-Wolf sont dans #raw("results/figures/canada/") et sous le suffixe #raw("_ledoit_wolf").

== 6. Limites et biais (statut)

#table(
  columns: 2,
  stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { none },
  align: left + top,
  inset: 5pt,
    [*Limite*],
    [*Statut*],
    [Erreur d'estimation des moyennes : les frontières dans l'échantillon reposent sur 187 à 223 mois et des poids concentrés sur trois actifs],
    [quantifié (sections 5.2, 5.3, 5.5) : rééchantillonnage et test hors échantillon ; non corrigé (pas de Black-Litterman ni de James-Stein sur les moyennes)],
    [Biais de sélection de l'univers : FNB choisis en 2026 parmi ceux qui ont survécu et qui ont un historique complet],
    [reconnu ; deux abandons documentés (section 3) ; aucun FNB fermé n'est inclus],
    [Rééquilibrage mensuel et coût fixe de 10 points de base, sans écart acheteur-vendeur variable ni impact de marché],
    [reconnu ; la rotation annuelle est publiée pour que le lecteur applique son propre coût],
    [Taxes, distributions, frais de gestion : les clôtures ajustées de Yahoo réinvestissent les distributions brutes et ignorent la fiscalité],
    [reconnu],
    [Long-only seulement : la frontière sans contrainte de signe est calculée (forme fermée) mais ni simulée ni testée hors échantillon],
    [reconnu, par choix (investisseur en FNB)],
    [Rendements mensuels supposés i.i.d. pour l'annualisation et le bootstrap ; pas de bloc-bootstrap],
    [reconnu],
    [Taux sans risque moyen sur la période pour la tangence dans l'échantillon],
    [reconnu ; le backtest utilise la moyenne de chaque fenêtre],
    [Prix ajustés Yahoo révisés dans le temps (dividendes, corrections) : une réexécution ultérieure peut différer à la marge],
    [reconnu ; manifeste avec sha256 et date],
    [Tangence long-only indéfinie si aucun actif ne bat le taux sans risque : le code renvoie la variance minimale],
    [vérifié : 0 déclenchement sur les 326 fenêtres américaines et les 254 fenêtres canadiennes du backtest (2 estimateurs)],
)

== 7. Reproduire

#raw("uv sync --locked --all-extras            # Python 3.12, versions épinglées (uv.lock)\nuv run python scripts/fetch_data.py      # prix Yahoo + taux FRED et Banque du Canada -> data/raw/ (avec manifeste)\nmake run                                 # 2 univers x 2 estimateurs -> results/tables/, results/figures/\nuv run python scripts/plot_oos_sharpe.py # figure 5 : barres du Sharpe hors échantillon, depuis oos_metrics.csv", block: true, lang: "bash")

Équivalents : #raw("make setup"), #raw("make data"), #raw("make run"). Durées mesurées (MacBook M2) : #raw("make run") entre 24 et 30 secondes pour les quatre exécutions, dont 200 bootstraps × 30 QP et (163 + 127) mois de backtest × 2 estimateurs. #raw("uv run pytest") passe 25 tests en moins de 10 secondes. #raw("uv run efficient-frontier demo") tourne en 3 secondes sur un univers synthétique sans réseau ; c'est ce que la CI exécute. Graines : 123 pour le Monte Carlo et le bootstrap ; les QP sont déterministes.

Ligne de commande :

#raw("uv run efficient-frontier run --universe us --n-sim 50000 --seed 123 --estimator sample\nuv run efficient-frontier run --universe canada --n-sim 50000 --seed 123 --estimator ledoit_wolf\nuv run efficient-frontier demo --n-sim 5000 --n-boot 20      # sorties dans results/demo/ (non versionné)", block: true, lang: "bash")

== 8. Arborescence

#raw("efficient-frontier-mpt/\n├── src/efficient_frontier/   config.py (univers, chemins), data.py (parquet -> rendements, taux), estimation.py,\n│                             frontier.py, montecarlo.py, backtest.py, plots.py, pipeline.py, cli.py\n├── scripts/                  fetch_data.py (téléchargement idempotent, manifeste sha256),\n│                             plot_oos_sharpe.py (figure 5 : barres du Sharpe hors échantillon)\n├── tests/                    25 tests pytest, données synthétiques, sans réseau\n├── assets/style.mplstyle     palette Okabe-Ito, polices DejaVu/STIX, PDF avec polices de type 42\n├── results/tables/<univers>/ frontier, special_portfolios, montecarlo_summary, resampled_frontier, moments,\n│                             correlation, oos_metrics, oos_returns, summary (JSON), par estimateur\n├── results/figures/<univers>/ cloud_{dirichlet,uniform}_<est>, transition_map, corr_heatmap,\n│                             resampled_vs_analytical, oos_growth, oos_weights (PNG + PDF), cloud_interactive (HTML)\n├── results/figures/          oos_sharpe_bars (PNG + PDF), les deux univers côte à côte\n├── data/raw/                 non versionné : prix parquet, CSV des taux, manifest.json\n├── .github/workflows/ci.yml  uv sync --locked, ruff, pytest, démo synthétique\n└── Makefile, pyproject.toml, uv.lock, LICENSE, CITATION.cff", block: true)

Il n'y a pas de rapport PDF séparé : ce README est le compte rendu, et les figures interactives complètent les PNG. Le code est dans #raw("src/"), rien dans des carnets.

== 9. Extensions possibles avec ce code

+ Canada : ajouter XEF.TO et XBM.TO à partir de 2013 (univers plus large, période plus courte) et comparer les deux frontières sur la période commune.
+ Black-Litterman : remplacer #raw("estimate_moments") par des moyennes d'équilibre inversées depuis les capitalisations des FNB, en gardant #raw("FrontierSolver") tel quel ; c'est la réponse naturelle à la section 5.4.
+ CVaR : #raw("FrontierSolver") accepte une autre fonction objectif convexe ; une frontière moyenne-CVaR (Rockafellar et Uryasev, 2000) s'écrit en une vingtaine de lignes cvxpy sur les mêmes rendements.
+ Bootstrap par blocs pour la frontière rééchantillonnée, afin de respecter l'autocorrélation des rendements.

== 10. Références

#raw("@article{markowitz1952,\n  author  = {Markowitz, Harry},\n  title   = {Portfolio Selection},\n  journal = {The Journal of Finance},\n  year    = {1952}, volume = {7}, number = {1}, pages = {77--91}, doi = {10.2307/2975974}\n}\n@article{sharpe1964,\n  author  = {Sharpe, William F.},\n  title   = {Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk},\n  journal = {The Journal of Finance},\n  year    = {1964}, volume = {19}, number = {3}, pages = {425--442}, doi = {10.2307/2977928}\n}\n@article{sharpe1966,\n  author  = {Sharpe, William F.},\n  title   = {Mutual Fund Performance},\n  journal = {The Journal of Business},\n  year    = {1966}, volume = {39}, number = {1}, pages = {119--138}\n}\n@article{merton1972,\n  author  = {Merton, Robert C.},\n  title   = {An Analytic Derivation of the Efficient Portfolio Frontier},\n  journal = {Journal of Financial and Quantitative Analysis},\n  year    = {1972}, volume = {7}, number = {4}, pages = {1851--1872}, doi = {10.2307/2329621}\n}\n@article{ledoitwolf2004,\n  author  = {Ledoit, Olivier and Wolf, Michael},\n  title   = {Honey, I Shrunk the Sample Covariance Matrix},\n  journal = {The Journal of Portfolio Management},\n  year    = {2004}, volume = {30}, number = {4}, pages = {110--119}, doi = {10.3905/jpm.2004.110}\n}\n@book{michaud1998,\n  author    = {Michaud, Richard O.},\n  title     = {Efficient Asset Management: A Practical Guide to Stock Portfolio Optimization and Asset Allocation},\n  publisher = {Harvard Business School Press},\n  year      = {1998}\n}\n@article{demiguel2009,\n  author  = {DeMiguel, Victor and Garlappi, Lorenzo and Uppal, Raman},\n  title   = {Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?},\n  journal = {The Review of Financial Studies},\n  year    = {2009}, volume = {22}, number = {5}, pages = {1915--1953}, doi = {10.1093/rfs/hhm075}\n}\n@article{choueifaty2008,\n  author  = {Choueifaty, Yves and Coignard, Yves},\n  title   = {Toward Maximum Diversification},\n  journal = {The Journal of Portfolio Management},\n  year    = {2008}, volume = {35}, number = {1}, pages = {40--51}, doi = {10.3905/JPM.2008.35.1.40}\n}", block: true, lang: "bibtex")

Données : Yahoo Finance (prix, usage personnel, non redistribués) ; FRED, Federal Reserve Bank of St. Louis, série TB3MS ; Banque du Canada, Valet, série TB.CDN.90D.MID. Bibliothèques : cvxpy et Clarabel (QP), numpy, pandas, scipy, matplotlib, seaborn, plotly, yfinance, pyarrow.

== 11. Licence, citation, auteur

Code sous licence MIT ; figures, tableaux et texte sous CC BY 4.0 (voir #raw("LICENSE")). Citation : #raw("CITATION.cff").

Guillaume Vaudescal, M. Sc. économique (UQAM, 2024), Montréal. Code écrit avec l'aide d'un assistant IA, relu, testé (25 tests, CI) et exécuté par l'auteur ; tous les nombres du README proviennent de #raw("results/tables/").
