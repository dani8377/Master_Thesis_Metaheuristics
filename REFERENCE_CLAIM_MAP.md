# Reference-to-Claim Map

Every reference cited in the thesis, and under each, every claim it is used to support. Generated from `bibliography/Bibliography.bib` and the chapter sources on 2026-08-13.

**97 references cited** across **201 citation instances**. 13 entries sit in the `.bib` file without being cited (listed at the end).

Claims are quoted from the surrounding sentence with LaTeX markup, maths, and nested citations stripped, so wording is close to but not always identical to the typeset text. Each is tagged with the chapter and section it appears in, and the source file and line for verification.

---

## Attri (2025)

*Global EV Charging Stations Dataset* — Kaggle

`attri2025evstations` · misc · Attri, Vivek

Used **1×**:

- **Problem Specification › Dataset Overview** — `chapters/Problem Specification.tex:305`

  The charging infrastructure used in this formulation is derived from the Global EV Charging
  Stations dataset , a publicly available collection of synthetic charging-station records
  distributed globally and released under the Apache License 2.0

---

## Baluja (1994)

*Population-Based Incremental Learning: A Method for Integrating Genetic Search Based Function Optimization and Competitive Learning*

`baluja1994` · techreport · Baluja, Shumeet

Used **4×**:

- **Related Work › Estimation of Distribution Algorithms on Cloud Allocation** — `chapters/Related work.tex:21`

  A closely related variant, Population-Based Incremental Learning (PBIL) , instead updates a single
  probability vector incrementally toward the best individuals

- **Metaheuristic Optimisation Methods › Estimation of Distribution Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:429`

  They emerged in response to the difficulty standard GAs have with strongly interacting variables,
  where crossover can disrupt useful structure : instead of propagating structural information
  implicitly through recombination, an EDA fits a statistical model to the currently selected
  individuals each generation and samples new candidates from it

- **Metaheuristic Optimisation Methods › Working Principle of UMDA** — `chapters/Metaheuristic Optimisation Methods.tex:495`

  UMDA is chosen over PBIL and the compact GA because it re-estimates its marginals from scratch
  each generation, mirroring the population structure of GA

- **Design and Implementation › Model estimation** — `chapters/Implementation.tex:116`

  The algorithm is UMDA in its pure form: the probability matrix is re-estimated from scratch each
  generation, with no incremental learning rate (in the PBIL view, a learning rate of )

---

## Basso et al. (2019)

*Energy consumption estimation integrated into the Electric Vehicle Routing Problem* — Transportation Research Part D: Transport and Environment

`basso2019` · article · Basso, Rafael and Kulcsár, Balázs and Egardt, Bo and Lindroth, Peter and Sanchez-Diaz, Ivan

Used **4×**:

- **Related Work › Energy Consumption Models** — `chapters/Related work.tex:35`

  Basso et al. integrate such a consumption model, accounting for topography and speed, directly
  into the EVRP and validate it against real-world measurements from an electric bus

- **Problem Specification › Energy Consumption Model** — `chapters/Problem Specification.tex:520`

  The speed multiplier reflects aerodynamic drag, the dominant source of energy loss at higher
  speeds, growing with the square of vehicle velocity

- **Problem Model Details › Speed multiplier** — `appendices/Problem Model Details.tex:189`

  More advanced models such as that of work with link-by-link speed profiles that include
  acceleration and braking

- **Problem Model Details › Speed multiplier** — `appendices/Problem Model Details.tex:197`

  The exponent is fixed at 2, reflecting the quadratic growth of aerodynamic drag with speed

---

## Beloglazov et al. (2012)

*Energy-Aware Resource Allocation Heuristics for Efficient Management of Data Centers for Cloud Computing* — Future Generation Computer Systems

`beloglazov2012energy` · article · Beloglazov, Anton and Abawajy, Jemal and Buyya, Rajkumar

Used **3×**:

- **Related Work › Heuristics and Metaheuristics on Cloud Allocation** — `chapters/Related work.tex:14`

  The simplest of these are the classical bin-packing heuristics, namely First Fit, Best Fit, and
  their decreasing variants (FFD, BFD), which remain the dominant baseline because they produce
  competitive solutions at time-scales compatible with online decision making

- **Related Work › Heuristics and Metaheuristics on Cloud Allocation** — `chapters/Related work.tex:16`

  The standard reference for energy-aware VMP is Beloglazov, Abawajy, and Buyya , who propose a
  family of placement and migration policies designed to minimise the number of active physical
  hosts and report substantial energy savings relative to non-power-aware allocation, with modest
  impact on SLA compliance

- **Problem Specification › Sets and Parameters** — `chapters/Problem Specification.tex:92`

  CPU usage is assumed to be linearly additive across tasks and perfectly divisible across cores, a
  standard abstraction in the cloud scheduling literature that ignores non-linear effects such as
  cache contention but preserves the essential property that aggregate demand must not exceed
  aggregate capacity

---

## Birattari (2009)

*Tuning Metaheuristics: A Machine Learning Perspective* — Springer

`birattari2009` · book · Birattari, Mauro

Used **1×**:

- **Experimental Setup › Hyperparameter Tuning** — `chapters/Experimental Setup.tex:98`

  The relative ranking of combinations is preserved at the reduced budget

---

## Chen et al. (2010)

*Analysis of Computational Time of Simple Estimation of Distribution Algorithms* — IEEE Transactions on Evolutionary Computation

`chen2010analysis` · article · Chen, Tianshi and Tang, Ke and Chen, Guoliang and Yao, Xin

Used **1×**:

- **Metaheuristic Optimisation Methods › Working Principle of UMDA** — `chapters/Metaheuristic Optimisation Methods.tex:509`

  Three parameters govern the exploration--exploitation balance : the population size (estimate
  accuracy and drift resistance), the selection ratio (selection pressure, with a common default),
  and a margin that keeps marginals away from the exact extremes so a value absent from one
  generation's selection is not lost forever , realised in this thesis by Laplace smoothing of the
  frequency counts (Section )

---

## Clarke and Wright (1964)

*Scheduling of Vehicles from a Central Depot to a Number of Delivery Points* — Operations Research

`clarke1964` · article · Clarke, G. and Wright, J. W.

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:49`

  Before the metaheuristics literature took over, classical constructive heuristics such as the
  Clarke and Wright savings algorithm and the sweep heuristic of Gillett and Miller dominated the
  routing literature, and they remain in use today as fast initial-solution generators or as
  baselines against which more sophisticated methods are compared

---

## Coffman et al. (1997)

*Approximation Algorithms for Bin Packing: A Survey* — Approximation Algorithms for NP-Hard Problems

`coffman1997` · incollection · Coffman, Jr., E. G. and Garey, M. R. and Johnson, D. S.

Used **2×**:

- **Related Work** — `chapters/Related work.tex:3`

  Although framed in specific application settings, both problems are instances of well-studied
  combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment
  problem with bin-packing structure , while electric vehicle routing extends the Vehicle Routing
  Problem (VRP) , itself a generalisation of the Travelling Salesman Problem

- **Design and Implementation › Greedy Best-Fit Decreasing** — `chapters/Implementation.tex:91`

  sec:impl_greedy Tasks are sorted by CPU demand in decreasing order and each is placed, in turn, on
  the feasible server carrying the highest current CPU load, the classic Best-Fit-Decreasing bin-
  packing choice , which consolidates the workload onto as few active servers as possible and so
  directly lowers the idle-power term

---

## Dantzig and Ramser (1959)

*The Truck Dispatching Problem* — Management Science

`dantzig1959` · article · Dantzig, George B. and Ramser, John H.

Used **1×**:

- **Related Work** — `chapters/Related work.tex:3`

  Although framed in specific application settings, both problems are instances of well-studied
  combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment
  problem with bin-packing structure , while electric vehicle routing extends the Vehicle Routing
  Problem (VRP) , itself a generalisation of the Travelling Salesman Problem

---

## Davis (1985)

*Applying Adaptive Algorithms to Epistatic Domains* — Proceedings of the 9th International Joint Conference on Artificial Intelligence (IJCAI)

`davis1985` · inproceedings · Davis, Lawrence

Used **1×**:

- **Design and Implementation › Crossover and station repair** — `chapters/Implementation.tex:163`

  Order crossover (OX) is applied to the customer sub-sequences only, with charging stations
  stripped out beforehand

---

## De Bonet et al. (1997)

*MIMIC: Finding Optima by Estimating Probability Densities* — Advances in Neural Information Processing Systems 9 (NIPS)

`debonet1997` · inproceedings · De Bonet, Jeremy S. and Isbell, Charles L. and Viola, Paul

Used **1×**:

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:447`

  sec:eda-model-classes EDAs are classified by the complexity of the fitted model . Univariate
  models factorise the joint distribution into independent per-variable marginals and ignore
  interactions. Bivariate models capture pairwise dependencies (MIMIC , BMDA )

---

## De Jong (1975)

*An Analysis of the Behavior of a Class of Genetic Adaptive Systems* — University of Michigan

`dejong1975` · phdthesis · De Jong, Kenneth A.

Used **1×**:

- **Experimental Setup › Hyperparameter Tuning** — `chapters/Experimental Setup.tex:98`

  Two parameters are tuned per algorithm, a common compromise for keeping grid search tractable : SA
  sweeps cooling rate and iterations per temperature ( ), GA sweeps population size and crossover
  probability ( ) , and UMDA sweeps population size and selection ratio ( )

---

## de Vries (2023)

*The growing energy footprint of artificial intelligence* — Joule

`devries2023growing` · article · de Vries, Alex

Used **1×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:8`

  This is a major concern due to the size of modern data centres and the growing demands of AI
  workloads

---

## Deb (2000)

*An efficient constraint handling method for genetic algorithms* — Computer Methods in Applied Mechanics and Engineering

`deb2000` · article · Deb, Kalyanmoy

Used **5×**:

- **Problem Specification › Objective Function** — `chapters/Problem Specification.tex:163`

  The sampling estimator follows and the penalty calibration follows the parameter-less rule of

- **Problem Specification › Capacity Penalties** — `chapters/Problem Specification.tex:284`

  The coefficients and are calibrated at runtime following the parameter-less penalty rule of , at a
  scale where any violation exceeding one per cent of the instance's total demand outweighs the
  largest feasible value of the two cost terms combined

- **Design and Implementation › Cloud Resource Allocation** — `chapters/Implementation.tex:43`

  The penalty coefficients and are set to over the feasible pool and applied to the violation
  expressed as a fraction of total demand (Equation ), following the parameter-less penalty rule of
  : any violation exceeding one per cent of total demand then scores worse than every feasible
  schedule, and the violations single moves actually produce (of the order of one task's demand)
  typically lie at or above that threshold

- **Design and Implementation › Electric Vehicle Routing** — `chapters/Implementation.tex:63`

  The two penalty coefficients and are then set to following the parameter-less penalty rule of , so
  a single infeasible arc dominates the entire feasible cost and the search is driven back toward
  feasibility even though the constraint is modelled as soft

- **Problem Model Details › Cloud Model Calibration Details** — `appendices/Problem Model Details.tex:127`

  The penalty coefficients and of Section are calibrated at runtime to one hundred times the largest
  feasible objective value observed in the calibration sample, following the parameter-less penalty
  rule of

---

## Deb (2001)

*Multi-Objective Optimization Using Evolutionary Algorithms* — John Wiley & Sons

`deb2001` · book · Deb, Kalyanmoy

Used **2×**:

- **Problem Specification › Objective Function** — `chapters/Problem Specification.tex:163`

  The sampling estimator follows and the penalty calibration follows the parameter-less rule of

- **Design and Implementation › Cloud Resource Allocation** — `chapters/Implementation.tex:36`

  Following the sample-based normalisation of , random assignments are drawn under the calibration
  seed and the feasible-draw means of energy and latency become the references, so each real-cost
  term contributes on the order of on a typical feasible schedule

---

## Demšar (2006)

*Statistical Comparisons of Classifiers over Multiple Data Sets* — Journal of Machine Learning Research

`demsar2006statistical` · article · Demšar, Janez

Used **1×**:

- **Experimental Setup › Evaluation Metrics and Statistical Tests** — `chapters/Experimental Setup.tex:422`

  The test is paired (because every algorithm is run on the same seed list, the two algorithms in a
  pair are compared seed by seed) and non-parametric, so it makes no normality assumption about the
  cost distribution, which is the safe choice for the small number of seeds used here and follows
  the standard recommendations for comparing stochastic optimisers

---

## Derrac et al. (2011)

*A Practical Tutorial on the Use of Nonparametric Statistical Tests as a Methodology for Comparing Evolutionary and Swarm Intelligence Algorithms* — Swarm and Evolutionary Computation

`derrac2011practical` · article · Derrac, Joaquín and García, Salvador and Molina, Daniel and Herrera, Francisco

Used **2×**:

- **Related Work › Cross-Paradigm Benchmarking and Research Gap** — `chapters/Related work.tex:65`

  Within-paradigm benchmarks are relatively common, for example the five-variant ACO comparison of
  Nie et al. on the EVRP, or the Derrac-style comparison protocols increasingly adopted in the
  metaheuristics literature

- **Experimental Setup › Evaluation Metrics and Statistical Tests** — `chapters/Experimental Setup.tex:422`

  The test is paired (because every algorithm is run on the same seed list, the two algorithms in a
  pair are compared seed by seed) and non-parametric, so it makes no normality assumption about the
  cost distribution, which is the safe choice for the small number of seeds used here and follows
  the standard recommendations for comparing stochastic optimisers

---

## Desaulniers et al. (2016)

*Exact Algorithms for Electric Vehicle-Routing Problems with Time Windows* — Operations Research

`desaulniers2016` · article · Desaulniers, Guy and Errico, Fausto and Irnich, Stefan and Schneider, Michael

Used **1×**:

- **Related Work › Exact Methods** — `chapters/Related work.tex:38`

  The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with
  commercial solvers or with specialised exact techniques originally developed for the classical VRP
  and later adapted to the EVRP, including branch-and-cut and branch-price-and-cut

---

## Developer (2025)

*Energy-Efficient Cloud Resource Allocation Dataset* — Kaggle, user programmer3

`programmer3_2025_cloud` · misc · Python Developer

Used **1×**:

- **Problem Specification › Dataset Overview** — `chapters/Problem Specification.tex:23`

  The task parameters used in this formulation are taken directly from the Energy-Efficient Cloud
  Resource Allocation dataset , a publicly available collection of synthetic task records released
  under a CC0 Public Domain dedication

---

## Doerr and Zheng (2020)

*Sharp Bounds for Genetic Drift in Estimation of Distribution Algorithms* — IEEE Transactions on Evolutionary Computation

`doerr2020sharp` · article · Doerr, Benjamin and Zheng, Weijie

Used **1×**:

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:463`

  Under the univariate factorisation the model holds parameters ( tasks, servers: one probability
  per task--server pair), re-estimated each generation from only the selected individuals.
  Theoretical analyses show the population must be sized generously relative to to prevent genetic
  drift, in which a marginal moves toward its extremes through finite-sample noise rather than
  genuine selection pressure

---

## Dorigo et al. (1996)

*Ant system: optimization by a colony of cooperating agents* — IEEE Transactions on Systems, Man, and Cybernetics, Part B

`dorigo1996` · article · Dorigo, Marco and Maniezzo, Vittorio and Colorni, Alberto

Used **7×**:

- **Metaheuristic Optimisation Methods › Ant Colony Optimisation** — `chapters/Metaheuristic Optimisation Methods.tex:315`

  Ant Colony Optimisation (ACO) is a population-based method in which artificial ants cooperate to
  build solutions by following and reinforcing promising paths, mimicking the foraging behaviour of
  real colonies: ants deposit pheromone as they walk, others preferentially follow stronger trails,
  and shorter paths accumulate pheromone faster, so the colony converges on good routes without any
  individual having a global view

- **Metaheuristic Optimisation Methods › Ant Colony Optimisation** — `chapters/Metaheuristic Optimisation Methods.tex:325`

  First demonstrated on the Travelling Salesman Problem , ACO has become one of the most widely
  applied metaheuristics for routing and sequencing problems

- **Metaheuristic Optimisation Methods › Solution Construction** — `chapters/Metaheuristic Optimisation Methods.tex:341`

  where is the set of nodes still allowed for ant , is the pheromone level on edge , and is a
  heuristic desirability, typically inverse distance

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:363`

  Once all ants have completed their tours, evaporation and deposit are combined into a single
  update : where is the evaporation rate

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:378`

  The deposit term is where is the total cost of ant 's tour, so better solutions exert a stronger
  influence on future iterations , and is a constant scaling every deposit equally, leaving the
  learning signal in the ratio alone (fixed at here)

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:383`

  Variants differ in how reinforcement is applied: the original Ant System lets all ants deposit,
  while Ant Colony System restricts deposit to the best ant

- **Metaheuristic Optimisation Methods › Matching Algorithms to Problems** — `chapters/Metaheuristic Optimisation Methods.tex:569`

  Its pheromone model is indexed by edges (the same unit in which route cost accrues), and routing
  has been ACO's classic application domain since its first demonstration on the TSP

---

## Dorigo and Gambardella (1997)

*Ant colony system: a cooperative learning approach to the traveling salesman problem* — IEEE Transactions on Evolutionary Computation

`dorigo1997` · article · Dorigo, Marco and Gambardella, Luca Maria

Used **2×**:

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:384`

  Variants differ in how reinforcement is applied: the original Ant System lets all ants deposit,
  while Ant Colony System restricts deposit to the best ant

- **Design and Implementation › Ant Colony Optimisation** — `chapters/Implementation.tex:173`

  The implementation is a Max--Min Ant System , which clamps every pheromone trail between a lower
  and an upper bound to prevent stagnation, combined with the pseudo-random proportional
  construction rule of

---

## Dorigo and Stützle (2004)

*Ant Colony Optimization* — MIT Press

`dorigo2004` · book · Dorigo, Marco and Stützle, Thomas

Used **5×**:

- **Metaheuristic Optimisation Methods › Ant Colony Optimisation** — `chapters/Metaheuristic Optimisation Methods.tex:315`

  Ant Colony Optimisation (ACO) is a population-based method in which artificial ants cooperate to
  build solutions by following and reinforcing promising paths, mimicking the foraging behaviour of
  real colonies: ants deposit pheromone as they walk, others preferentially follow stronger trails,
  and shorter paths accumulate pheromone faster, so the colony converges on good routes without any
  individual having a global view

- **Metaheuristic Optimisation Methods › Ant Colony Optimisation** — `chapters/Metaheuristic Optimisation Methods.tex:327`

  First demonstrated on the Travelling Salesman Problem , ACO has become one of the most widely
  applied metaheuristics for routing and sequencing problems

- **Metaheuristic Optimisation Methods › Solution Construction** — `chapters/Metaheuristic Optimisation Methods.tex:348`

  Pheromone is initialised to a small positive constant , commonly scaled from a greedy nearest-
  neighbour tour , and the colony size trades per-iteration diversity against computational effort

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:388`

  The implementation in this thesis combines the pheromone clamping of MAX--MIN Ant System , which
  bounds pheromone within so that no edge is ever completely abandoned and premature stagnation is
  resisted , with the pseudo-random-proportional rule of Ant Colony System: with probability an ant
  moves greedily to the most attractive allowed node, and otherwise samples from the transition
  distribution above

- **Metaheuristic Optimisation Methods › Handling Constraints** — `chapters/Metaheuristic Optimisation Methods.tex:407`

  During construction, infeasible moves can be excluded from (an ant can be prevented from
  travelling to a node that would exhaust the battery), which guarantees feasible tours but can
  limit exploration when the feasible region is small

---

## Droste et al. (2006)

*Upper and Lower Bounds for Randomized Search Heuristics in Black-Box Optimization* — Theory of Computing Systems

`droste2006upper` · article · Droste, Stefan and Jansen, Thomas and Wegener, Ingo

Used **2×**:

- **Introduction › Problem Statement** — `chapters/Introduction.tex:21`

  Of these, SA, GA, and UMDA are black-box optimisers that use only objective-function evaluations,
  whereas ACO is a grey-box method that additionally exploits the distance structure of the routing
  graph

- **Related Work › Ant Colony Optimisation on EVRP** — `chapters/Related work.tex:58`

  ACO is also the only method in this comparison that uses problem-specific information beyond the
  objective value, since its construction is guided by an inverse-distance heuristic over the graph
  edges, which makes it a grey-box method in the sense of Whitley et al. , whereas SA, GA, and UMDA
  operate as black-box optimisers

---

## Eiben and Smith (2015)

*Introduction to Evolutionary Computing* — Springer

`eiben2015` · book · Eiben, A. E. and Smith, J. E.

Used **6×**:

- **Metaheuristic Optimisation Methods › Metaheuristics for Combinatorial Optimisation** — `chapters/Metaheuristic Optimisation Methods.tex:6`

  To solve them, the thesis uses metaheuristics: general-purpose search methods that combine
  randomness with problem-specific logic to find good, if not perfect, solutions within a reasonable
  runtime

- **Metaheuristic Optimisation Methods › Genetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:107`

  New candidates are produced by recombining existing solutions (crossover) and perturbing them
  (mutation), which together balance exploration of new regions against exploitation of known good
  solutions

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:136`

  It is scale-invariant, so it handles a minimised objective without any fitness transformation, and
  the tournament size gives direct control over selection pressure

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:143`

  The dominant failure mode is premature convergence: once the population homogenises on a
  suboptimal region, crossover cannot recover the lost diversity and mutation alone is slow to do so

- **Metaheuristic Optimisation Methods › Encoding and Parameters** — `chapters/Metaheuristic Optimisation Methods.tex:159`

  Four parameters govern the exploration--exploitation balance : the population size (diversity
  versus cost per generation), the crossover probability (typically -- ), the mutation probability
  (a common heuristic is for representation length ), and the selection pressure via the tournament
  size (typically -- )

- **Experimental Setup › Hyperparameter Tuning** — `chapters/Experimental Setup.tex:98`

  Two parameters are tuned per algorithm, a common compromise for keeping grid search tractable : SA
  sweeps cooling rate and iterations per temperature ( ), GA sweeps population size and crossover
  probability ( ) , and UMDA sweeps population size and selection ratio ( )

---

## Farr et al. (2007)

*The Shuttle Radar Topography Mission* — Reviews of Geophysics

`farr2007srtm` · article · Farr, Tom G. and Rosen, Paul A. and Caro, Edward and Crippen, Robert and Duren, Riley and Hensley, Scott and Kobrick, Michael and Paller, Mimi and Rodriguez, Ernesto and Roth, Ladislav and Seal, David and Shaffer, Scott and Shimada, Joanne and Umland, Jeffrey and Werner, Marian and Oskin, Michael and Burbank, Douglas and Alsdorf, Douglas

Used **1×**:

- **Problem Specification › Dataset Overview** — `chapters/Problem Specification.tex:357`

  The road distances and travel times are obtained from the OSRM routing engine on the OpenStreetMap
  San Francisco road network, and the per-node elevations from the SRTM digital elevation model

---

## Farzai et al. (2020)

*Multi-Objective Communication-Aware Optimization for Virtual Machine Placement in Cloud Datacenters* — Sustainable Computing: Informatics and Systems

`farzai2020multiobjective` · article · Farzai, Sajedeh and Shirvani, Mirsaeid Hosseini and Rabbani, Masoud

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on Cloud Allocation** — `chapters/Related work.tex:16`

  Subsequent work has extended this formulation into multi-objective settings that jointly minimise
  energy, migration overhead, and SLA violations

---

## Felipe et al. (2014)

*A Heuristic Approach for the Green Vehicle Routing Problem with Multiple Technologies and Partial Recharges* — Transportation Research Part E: Logistics and Transportation Review

`felipe2014` · article · Felipe, Ángel and Ortuño, M. Teresa and Righini, Giovanni and Tirado, Gregorio

Used **2×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:47`

  Some allow only full recharges, others allow partial recharging

- **Metaheuristic Optimisation Methods › Defining the Neighbourhood** — `chapters/Metaheuristic Optimisation Methods.tex:293`

  Because the battery level evolves along the route, dedicated operators insert, remove, or relocate
  charging stations , and a repair operator inserts a station at the cheapest position within an
  interval where battery constraints would otherwise be violated

---

## Froger et al. (2022)

*The Electric Vehicle Routing Problem with Capacitated Charging Stations* — Transportation Science

`froger2022exact` · article · Froger, Aurélien and Jabali, Ola and Mendoza, Jorge E. and Laporte, Gilbert

Used **4×**:

- **Related Work › Exact Methods** — `chapters/Related work.tex:38`

  Realistic features such as nonlinear charging functions or speed-dependent energy use make the
  formulations even larger, and often require approximations that introduce errors of their own

- **Related Work › Exact Methods** — `chapters/Related work.tex:40`

  Examples include LP-based rounding, Lagrangian relaxation, column-generation heuristics, and
  matheuristics that combine MILP solvers with neighbourhood search

- **Related Work › Exact Methods** — `chapters/Related work.tex:42`

  The gradient- and speed-dependent arc energies and freely revisitable stations used here (Chapter
  ) would require the kind of enlarged or approximated formulations discussed by Froger et al

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:45`

  for the E-CVRP are widely used testbeds for their respective EVRP variants, and subsequent work
  has reported incremental improvements of a few percent on the best-known solutions

---

## Gao et al. (2013)

*A Multi-Objective Ant Colony System Algorithm for Virtual Machine Placement in Cloud Computing* — Journal of Computer and System Sciences

`gao2013multi` · article · Gao, Yongqiang and Guan, Haibing and Qi, Zhengwei and Hou, Yang and Liu, Liang

Used **1×**:

- **Related Work › Cross-Paradigm Benchmarking and Research Gap** — `chapters/Related work.tex:69`

  The opposite mismatch is just as clear: ACO has been applied to virtual machine placement , but
  ACO stores its learning on the edges between nodes, and an assignment problem has no meaningful
  edges to learn from, only the choice of which server receives each task

---

## Garey and Johnson (1979)

*Computers and Intractability: A Guide to the Theory of NP-Completeness* — W. H. Freeman and Company

`garey1979` · book · Garey, Michael R. and Johnson, David S.

Used **3×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:8`

  They require complex decisions under tight resource limits, and both are NP-hard , so no exact
  algorithm is known whose running time scales polynomially with instance size

- **Related Work** — `chapters/Related work.tex:3`

  Although framed in specific application settings, both problems are instances of well-studied
  combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment
  problem with bin-packing structure , while electric vehicle routing extends the Vehicle Routing
  Problem (VRP) , itself a generalisation of the Travelling Salesman Problem

- **Problem Specification › Solution Representation** — `chapters/Problem Specification.tex:115`

  The exponential size of the search space does not by itself establish NP-hardness, but the problem
  inherits hardness from its close relationship to the Generalised Assignment Problem, which is
  known to be NP-hard

---

## Gillett and Miller (1974)

*A Heuristic Algorithm for the Vehicle-Dispatch Problem* — Operations Research

`gillett1974` · article · Gillett, Billy E. and Miller, Leland R.

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:49`

  Before the metaheuristics literature took over, classical constructive heuristics such as the
  Clarke and Wright savings algorithm and the sweep heuristic of Gillett and Miller dominated the
  routing literature, and they remain in use today as fast initial-solution generators or as
  baselines against which more sophisticated methods are compared

---

## Goldberg (1989)

*Genetic Algorithms in Search, Optimization, and Machine Learning* — Addison-Wesley Professional

`goldberg1989` · book · Goldberg, David E.

Used **4×**:

- **Metaheuristic Optimisation Methods › Genetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:99`

  Genetic Algorithms (GAs) are a population-based metaheuristic inspired by Darwinian natural
  selection: a population of encoded candidate solutions undergoes repeated cycles of selection and
  variation, higher-fitness individuals are more likely to reproduce, and favourable traits
  propagate over generations

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:124`

  Selection draws parents with a bias toward higher fitness. Variation produces offspring by
  applying crossover with probability and mutation independently at each position with probability

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:136`

  It is scale-invariant, so it handles a minimised objective without any fitness transformation, and
  the tournament size gives direct control over selection pressure

- **Metaheuristic Optimisation Methods › Encoding and Parameters** — `chapters/Metaheuristic Optimisation Methods.tex:159`

  Four parameters govern the exploration--exploitation balance : the population size (diversity
  versus cost per generation), the crossover probability (typically -- ), the mutation probability
  (a common heuristic is for representation length ), and the selection pressure via the tournament
  size (typically -- )

---

## Gutjahr (2000)

*A Graph-based Ant System and its Convergence* — Future Generation Computer Systems

`gutjahr2000` · article · Gutjahr, Walter J.

Used **1×**:

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:398`

  The two mechanisms act on different objects, on a single move during construction and the MAX--MIN
  bounds on the pheromone values after the update. For pheromone-bounded variants, convergence in
  value to the global optimum has been proven , though, as with SA's logarithmic-cooling guarantee,
  only in an idealised limit that does not bind under a finite budget

---

## Hajek (1988)

*Cooling schedules for optimal annealing* — Mathematics of Operations Research

`hajek1988` · article · Hajek, Bruce

Used **1×**:

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:261`

  A logarithmically slow schedule guarantees the global optimum in theory but is far too slow to be
  useful in practice, so performance within a fixed budget depends heavily on the tuned schedule

---

## Harik (1999)

*Linkage Learning via Probabilistic Modeling in the ECGA*

`harik1999ecga` · techreport · Harik, Georges R.

Used **1×**:

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:449`

  Multivariate models partition variables into linkage groups (ECGA ) or learn a full Bayesian
  network (BOA )

---

## Harik et al. (1999)

*The Compact Genetic Algorithm* — IEEE Transactions on Evolutionary Computation

`harik1999cga` · article · Harik, Georges R. and Lobo, Fernando G. and Goldberg, David E.

Used **1×**:

- **Metaheuristic Optimisation Methods › Working Principle of UMDA** — `chapters/Metaheuristic Optimisation Methods.tex:496`

  UMDA is chosen over PBIL and the compact GA because it re-estimates its marginals from scratch
  each generation, mirroring the population structure of GA

---

## Harris et al. (2020)

*Array Programming with NumPy* — Nature

`harris2020array` · article · Harris, Charles R. and Millman, K. Jarrod and van der Walt, Stéfan J. and Gommers, Ralf and Virtanen, Pauli and Cournapeau, David and Wieser, Eric and Taylor, Julian and Berg, Sebastian and Smith, Nathaniel J. and Kern, Robert and Picus, Matti and Hoyer, Stephan and van Kerkwijk, Marten H. and Brett, Matthew and Haldane, Allan and Fernández del Río, Jaime and Wiebe, Mark and Peterson, Pearu and Gérard-Marchant, Pierre and Sheppard, Kevin and Reddy, Tyler and Weckesser, Warren and Abbasi, Hameer and Gohlke, Christoph and Oliphant, Travis E.

Used **1×**:

- **Design and Implementation › Tools and Environment** — `chapters/Implementation.tex:7`

  NumPy supplies the vectorised operations behind the objective functions, neighbourhood operators,
  and UMDA's marginal-model sampling

---

## Hauschild and Pelikan (2011)

*An Introduction and Survey of Estimation of Distribution Algorithms* — Swarm and Evolutionary Computation

`hauschild2011` · article · Hauschild, Mark and Pelikan, Martin

Used **4×**:

- **Related Work › Estimation of Distribution Algorithms on Cloud Allocation** — `chapters/Related work.tex:21`

  Estimation of Distribution Algorithms (EDAs) replace the crossover and mutation operators of
  evolutionary algorithms with a probabilistic model that is fitted to selected individuals from the
  current population and then sampled to generate new candidate solutions

- **Metaheuristic Optimisation Methods › Probabilistic Model-Based Metaheuristics** — `chapters/Metaheuristic Optimisation Methods.tex:420`

  replace the heuristic variation operators with an explicit probabilistic model fitted to the
  currently best solutions, and generate new candidates by sampling from that model

- **Metaheuristic Optimisation Methods › Estimation of Distribution Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:425`

  Estimation of Distribution Algorithms (EDAs) are model-based alternatives to traditional GAs

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:443`

  sec:eda-model-classes EDAs are classified by the complexity of the fitted model

---

## Hiermann et al. (2016)

*The Electric Fleet Size and Mix Vehicle Routing Problem with Time Windows and Recharging Stations* — European Journal of Operational Research

`hiermann2016` · article · Hiermann, Gerhard and Puchinger, Jakob and Ropke, Stefan and Hartl, Richard F.

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:51`

  Among the metaheuristics used on the EVRP, Adaptive Large Neighbourhood Search (ALNS) is one of
  the most widely used

---

## Holland (1975)

*Adaptation in Natural and Artificial Systems* — University of Michigan Press

`holland1975` · book · Holland, John H.

Used **1×**:

- **Metaheuristic Optimisation Methods › Genetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:99`

  Genetic Algorithms (GAs) are a population-based metaheuristic inspired by Darwinian natural
  selection: a population of encoded candidate solutions undergoes repeated cycles of selection and
  variation, higher-fitness individuals are more likely to reproduce, and favourable traits
  propagate over generations

---

## Holland (1992)

*Adaptation in Natural and Artificial Systems: An Introductory Analysis with Applications to Biology, Control, and Artificial Intelligence* — MIT Press

`holland1992` · book · Holland, John H.

Used **1×**:

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:140`

  Crossover is the primary mechanism by which a GA exploits existing structure, mixing high-quality
  components already present in the population, while mutation re-injects diversity and prevents the
  population from collapsing onto near-identical copies

---

## Hunter (2007)

*Matplotlib: A 2D Graphics Environment* — Computing in Science & Engineering

`hunter2007matplotlib` · article · Hunter, John D.

Used **1×**:

- **Design and Implementation › Tools and Environment** — `chapters/Implementation.tex:7`

  All figures are rendered to disk with matplotlib

---

## Hutter et al. (2009)

*ParamILS: An Automatic Algorithm Configuration Framework* — Journal of Artificial Intelligence Research

`hutter2009` · article · Hutter, Frank and Hoos, Holger H. and Leyton-Brown, Kevin and Stützle, Thomas

Used **1×**:

- **Experimental Setup › Hyperparameter Tuning** — `chapters/Experimental Setup.tex:98`

  Two parameters are tuned per algorithm, a common compromise for keeping grid search tractable : SA
  sweeps cooling rate and iterations per temperature ( ), GA sweeps population size and crossover
  probability ( ) , and UMDA sweeps population size and selection ratio ( )

---

## International Energy Agency (2021)

*Net Zero by 2050: A Roadmap for the Global Energy Sector*

`iea2021netzero` · techreport · International Energy Agency

Used **1×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:6`

  Electricity prices have risen sharply, international agreements like the Paris Agreement have led
  to strict emissions targets, and companies face increasing pressure to meet corporate
  sustainability pledges

---

## International Energy Agency (2025)

*Energy and AI*

`iea2025energyai` · techreport · International Energy Agency

Used **1×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:8`

  This is a major concern due to the size of modern data centres and the growing demands of AI
  workloads

---

## Karakatič (2021)

*Optimizing Nonlinear Charging Times of Electric Vehicle Routing with Genetic Algorithm* — Expert Systems with Applications

`karakatic2021` · article · Karakatič, Sašo

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:53`

  Karakatič solves a multi-depot EVRP variant with nonlinear charging using a GA in which the
  genotype is split into two layers, one for the customer visit order and one for charging
  decisions, with a different crossover operator applied to each

---

## Keskin and Çatay (2016)

*Partial Recharge Strategies for the Electric Vehicle Routing Problem with Time Windows* — Transportation Research Part C: Emerging Technologies

`keskin2016` · article · Keskin, Merve and Çatay, Bülent

Used **2×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:47`

  Some allow only full recharges, others allow partial recharging

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:51`

  Among the metaheuristics used on the EVRP, Adaptive Large Neighbourhood Search (ALNS) is one of
  the most widely used

---

## Kirkpatrick et al. (1983)

*Optimization by simulated annealing* — Science

`kirkpatrick1983` · article · Kirkpatrick, Scott and Gelatt, C. D. and Vecchi, M. P.

Used **5×**:

- **Metaheuristic Optimisation Methods › Simulated Annealing** — `chapters/Metaheuristic Optimisation Methods.tex:212`

  Simulated Annealing (SA) is a single-solution search method that improves one candidate step by
  step

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:227`

  At each step, SA takes the current solution and generates a slightly modified ``neighbour'' , then
  computes the difference in objective value : where is the fitness function to be minimised

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:248`

  The temperature schedule controls how fast SA transitions from broad exploration to focused local
  search, and it is the most important design decision when applying the algorithm

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:256`

  The starting temperature is commonly calibrated so that typical worsening moves are initially
  accepted around of the time

- **Design and Implementation › Simulated Annealing** — `chapters/Implementation.tex:94`

  sec:impl_sa The implementation applies the standard Metropolis acceptance rule and geometric
  cooling introduced in Chapter , cooling once per temperature step of candidate moves

---

## Kumaraswamy and Nair (2019)

*Bin Packing Algorithms for Virtual Machine Placement in Cloud Computing: A Review* — International Journal of Electrical and Computer Engineering (IJECE)

`kumaraswamy2019binpacking` · article · Kumaraswamy, S. and Nair, Mydhili K.

Used **3×**:

- **Related Work › Exact Methods** — `chapters/Related work.tex:11`

  They are typically formulated as Integer Linear Programmes (ILPs) or Mixed-Integer Linear
  Programmes (MILPs) and solved using branch-and-bound-based optimisation solvers

- **Related Work › Heuristics and Metaheuristics on Cloud Allocation** — `chapters/Related work.tex:14`

  Comprehensive surveys are given by Mann and, with a focus on bin-packing-style approaches, by
  Kumaraswamy and Nair

- **Related Work › Heuristics and Metaheuristics on Cloud Allocation** — `chapters/Related work.tex:14`

  The simplest of these are the classical bin-packing heuristics, namely First Fit, Best Fit, and
  their decreasing variants (FFD, BFD), which remain the dominant baseline because they produce
  competitive solutions at time-scales compatible with online decision making

---

## Küçükoğlu et al. (2021)

*The Electric Vehicle Routing Problem and Its Variations: A Literature Review* — Computers & Industrial Engineering

`kucukoglu2021` · article · Küçükoğlu, Ilker and Dewil, Reginald and Cattrysse, Dirk

Used **2×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:47`

  A full treatment of these variants is out of scope here, but the survey by Küçükoğlu et al. covers
  them in detail

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:51`

  Among the metaheuristics used on the EVRP, Adaptive Large Neighbourhood Search (ALNS) is one of
  the most widely used

---

## Lenstra and Rinnooy Kan (1981)

*Complexity of vehicle routing and scheduling problems* — Networks

`lenstra1981complexity` · article · Lenstra, Jan Karel and Rinnooy Kan, A. H. G.

Used **1×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:8`

  They require complex decisions under tight resource limits, and both are NP-hard , so no exact
  algorithm is known whose running time scales polynomially with instance size

---

## Lin and Kernighan (1973)

*An Effective Heuristic Algorithm for the Traveling-Salesman Problem* — Operations Research

`lin1973` · article · Lin, Shen and Kernighan, Brian W.

Used **1×**:

- **Metaheuristic Optimisation Methods › Defining the Neighbourhood** — `chapters/Metaheuristic Optimisation Methods.tex:283`

  The first concerns customer ordering: 2-opt segment reversal (a special case of the k-opt
  framework of ), swapping two customers, and relocating a customer (removing it from position and
  reinserting it at position , shifting the customers in between by one place), all standard moves
  for permutation-based routing

---

## Liu et al. (2022)

*A Hybrid Genetic Algorithm for the Electric Vehicle Routing Problem with Time Windows* — Control Theory and Technology

`liu2022hybridga` · article · Liu, Qixing and Xu, Peng and Wu, Yuhu and Shen, Tielong

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:53`

  Liu et al. are a representative example: they combine 2-opt local search with a GA on an E-VRPTW
  variant that incorporates road terrain grades into energy consumption, and report improvements
  over a Simulated Annealing baseline on the same instances

---

## Luxen and Vetter (2011)

*Real-time routing with OpenStreetMap data* — Proceedings of the 19th ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems

`luxen2011osrm` · inproceedings · Luxen, Dennis and Vetter, Christian

Used **1×**:

- **Problem Specification › Dataset Overview** — `chapters/Problem Specification.tex:355`

  The road distances and travel times are obtained from the OSRM routing engine on the OpenStreetMap
  San Francisco road network, and the per-node elevations from the SRTM digital elevation model

---

## Mann (2015)

*Allocation of Virtual Machines in Cloud Data Centers–-A Survey of Problem Models and Optimization Algorithms* — ACM Computing Surveys

`mann2015allocation` · article · Mann, Zoltán Ádám

Used **4×**:

- **Related Work › Cloud Resource Allocation** — `chapters/Related work.tex:8`

  The cloud resource allocation problem studied in this thesis is usually framed as Virtual Machine
  Placement (VMP)

- **Related Work › Cloud Resource Allocation** — `chapters/Related work.tex:8`

  The problem is NP-hard , and the scale of modern data centres rules out exhaustive search in
  practice

- **Related Work › Heuristics and Metaheuristics on Cloud Allocation** — `chapters/Related work.tex:14`

  Comprehensive surveys are given by Mann and, with a focus on bin-packing-style approaches, by
  Kumaraswamy and Nair

- **Problem Specification › Sets and Parameters** — `chapters/Problem Specification.tex:92`

  CPU usage is assumed to be linearly additive across tasks and perfectly divisible across cores, a
  standard abstraction in the cloud scheduling literature that ignores non-linear effects such as
  cache contention but preserves the essential property that aggregate demand must not exceed
  aggregate capacity

---

## Masanet et al. (2020)

*Recalibrating global data center energy-use estimates* — Science

`masanet2020recalibrating` · article · Masanet, Eric and Shehabi, Arman and Lei, Nuoa and Smith, Sarah and Koomey, Jonathan

Used **1×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:8`

  This is a major concern due to the size of modern data centres and the growing demands of AI
  workloads

---

## Mavrovouniotis et al. (2018)

*Ant Colony Optimization for the Electric Vehicle Routing Problem* — 2018 IEEE Symposium Series on Computational Intelligence (SSCI)

`mavrovouniotis2018` · inproceedings · Mavrovouniotis, Michalis and Ellinas, Georgios and Polycarpou, Marios

Used **1×**:

- **Related Work › Ant Colony Optimisation on EVRP** — `chapters/Related work.tex:56`

  Ant Colony Optimisation was applied to the EVRP by Mavrovouniotis et al. , using the MAX-MIN
  variant (MMAS) together with a look-ahead strategy that ensures EVs always retain enough energy to
  reach a charging station

---

## Mavrovouniotis et al. (2020)

*A Benchmark Test Suite for the Electric Capacitated Vehicle Routing Problem* — 2020 IEEE Congress on Evolutionary Computation (CEC)

`mavrovouniotis2020benchmark` · inproceedings · Mavrovouniotis, Michalis and Menelaou, Charalambos and Timotheou, Stelios and Ellinas, Georgios and Panayiotou, Christos and Polycarpou, Marios

Used **3×**:

- **Related Work › Exact Methods** — `chapters/Related work.tex:38`

  The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with
  commercial solvers or with specialised exact techniques originally developed for the classical VRP
  and later adapted to the EVRP, including branch-and-cut and branch-price-and-cut

- **Related Work › Exact Methods** — `chapters/Related work.tex:38`

  Mavrovouniotis et al. support this scaling limit on the related E-CVRP, reporting that their MILP
  formulation could not find solutions for large-scale instances within a three-week time limit

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:45`

  for the E-CVRP are widely used testbeds for their respective EVRP variants, and subsequent work
  has reported incremental improvements of a few percent on the best-known solutions

---

## McKinney (2010)

*Data Structures for Statistical Computing in Python* — Proceedings of the 9th Python in Science Conference (SciPy 2010)

`mckinney2010pandas` · inproceedings · McKinney, Wes

Used **1×**:

- **Design and Implementation › Tools and Environment** — `chapters/Implementation.tex:7`

  The pandas library ingests the CSV datasets and samples tasks for the synthetic scalability
  instances

---

## Metropolis et al. (1953)

*Equation of state calculations by fast computing machines* — Journal of Chemical Physics

`metropolis1953` · article · Metropolis, Nicholas and Rosenbluth, Arianna W. and Rosenbluth, Marshall N. and Teller, Augusta H. and Teller, Edward

Used **1×**:

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:233`

  Worsening moves are accepted with the probability originally proposed by Metropolis et al. ,
  giving the full acceptance rule: At high temperatures even large worsening moves have a reasonable
  chance of acceptance, so the algorithm explores freely

---

## Michalewicz (1996)

*Genetic Algorithms + Data Structures = Evolution Programs* — Springer

`michalewicz1996` · book · Michalewicz, Zbigniew

Used **2×**:

- **Metaheuristic Optimisation Methods › Handling Constraints** — `chapters/Metaheuristic Optimisation Methods.tex:169`

  Of the three standard strategies (penalty functions, repair, and feasibility-preserving operators
  ), the penalty approach is applied, consistent with the objective formulation used by SA and UMDA
  on the same problem: infeasible individuals are retained but their selection fitness is worsened
  in proportion to the CPU and memory violations, weighted by the coefficients and introduced in
  Section

- **Metaheuristic Optimisation Methods › Encoding and Handling Constraints** — `chapters/Metaheuristic Optimisation Methods.tex:536`

  Repair would bias the training data toward repaired rather than genuinely favoured assignments,
  and hard rejection would waste much of each sampled generation under tight constraints

---

## Moscato (1989)

*On Evolution, Search, Optimization, Genetic Algorithms and Martial Arts: Towards Memetic Algorithms*

`moscato1989` · techreport · Moscato, Pablo

Used **4×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:53`

  Combining a genetic algorithm with local refinement yields a memetic algorithm , a template that
  is particularly effective on routing problems because the local-search step repairs the route
  disruption that recombination causes

- **Metaheuristic Optimisation Methods › Memetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:189`

  A Memetic Algorithm (MA) hybridises a population-based method with local search, so that the
  population evolves over locally optimised solutions rather than raw offspring . The name is
  Moscato's, after Dawkins's meme, a unit of cultural rather than genetic transmission

- **Metaheuristic Optimisation Methods › Memetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:189`

  Genes are passed on unchanged, whereas memes are typically improved by their carrier before being
  propagated, just as each offspring here is locally refined before it enters the population . In
  this thesis the MA extends the Genetic Algorithm of the previous section

- **Design and Implementation › Memetic Algorithm** — `chapters/Implementation.tex:169`

  The memetic algorithm reuses the GA but refines each offspring with up to thirty first-improvement
  local-search steps (drawn from the same eight operators) before it enters the population

---

## Mühlenbein and Paaß (1996)

*From Recombination of Genes to the Estimation of Distributions I. Binary Parameters* — Parallel Problem Solving from Nature–-PPSN IV

`muhlenbein1996` · inproceedings · Mühlenbein, Heinz and Paaß, Gerhard

Used **8×**:

- **Related Work › Estimation of Distribution Algorithms on Cloud Allocation** — `chapters/Related work.tex:21`

  The most widely used univariate EDA is the Univariate Marginal Distribution Algorithm (UMDA) ,
  which re-estimates each variable's marginal directly from the selected population at every
  generation, and it is the univariate EDA studied in this thesis

- **Metaheuristic Optimisation Methods › Estimation of Distribution Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:425`

  Estimation of Distribution Algorithms (EDAs) are model-based alternatives to traditional GAs

- **Metaheuristic Optimisation Methods › Estimation of Distribution Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:429`

  They emerged in response to the difficulty standard GAs have with strongly interacting variables,
  where crossover can disrupt useful structure : instead of propagating structural information
  implicitly through recombination, an EDA fits a statistical model to the currently selected
  individuals each generation and samples new candidates from it

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:456`

  A systematic comparison across the hierarchy lies outside the scope of this thesis. This work
  therefore evaluates a single representative, the Univariate Marginal Distribution Algorithm (UMDA)

- **Metaheuristic Optimisation Methods › Working Principle of UMDA** — `chapters/Metaheuristic Optimisation Methods.tex:471`

  UMDA maintains a population of candidates and, each generation, performs evaluation, selection,
  estimation, and sampling : [ S_t = select (P_t), p_t = estimate (S_t), P_ t+1 = sample (p_t, N)

- **Metaheuristic Optimisation Methods › Working Principle of UMDA** — `chapters/Metaheuristic Optimisation Methods.tex:504`

  Three parameters govern the exploration--exploitation balance : the population size (estimate
  accuracy and drift resistance), the selection ratio (selection pressure, with a common default),
  and a margin that keeps marginals away from the exact extremes so a value absent from one
  generation's selection is not lost forever , realised in this thesis by Laplace smoothing of the
  frequency counts (Section )

- **Metaheuristic Optimisation Methods › Encoding and Handling Constraints** — `chapters/Metaheuristic Optimisation Methods.tex:527`

  Second, variable interactions are indirect, mediated by aggregate server load rather than the
  encoding. Third, the objective function of Equation is approximately additive across tasks under
  the soft-penalty formulation, a structure favourable to univariate EDAs

- **Design and Implementation › Model estimation** — `chapters/Implementation.tex:116`

  The algorithm is UMDA in its pure form: the probability matrix is re-estimated from scratch each
  generation, with no incremental learning rate (in the PBIL view, a learning rate of )

---

## Mühlenbein and Mahnig (1999)

*FDA–-A Scalable Evolutionary Algorithm for the Optimization of Additively Decomposed Functions* — Evolutionary Computation

`muhlenbein1999fda` · article · Mühlenbein, Heinz and Mahnig, Thilo

Used **1×**:

- **Metaheuristic Optimisation Methods › Encoding and Handling Constraints** — `chapters/Metaheuristic Optimisation Methods.tex:527`

  Second, variable interactions are indirect, mediated by aggregate server load rather than the
  encoding. Third, the objective function of Equation is approximately additive across tasks under
  the soft-penalty formulation, a structure favourable to univariate EDAs

---

## Nie et al. (2022)

*Ant Colony Optimization for Electric Vehicle Routing Problem with Capacity and Charging Time Constraints* — 2022 IEEE International Conference on Systems, Man, and Cybernetics (SMC)

`nie2022aco-evrpcc` · inproceedings · Nie, Zi-Hao and Yang, Qiang and Zhang, En and Liu, Dong and Zhang, Jun

Used **2×**:

- **Related Work › Ant Colony Optimisation on EVRP** — `chapters/Related work.tex:56`

  A follow-up study by Nie et al. compared five classical ACO variants (AS, Rank-AS, EAS, MMAS, ACS)
  on an EVRP variant with capacity and charging-time constraints, and found Rank-AS to be the
  strongest performer overall

- **Related Work › Cross-Paradigm Benchmarking and Research Gap** — `chapters/Related work.tex:65`

  Within-paradigm benchmarks are relatively common, for example the five-variant ACO comparison of
  Nie et al. on the EVRP, or the Derrac-style comparison protocols increasingly adopted in the
  metaheuristics literature

---

## Pan and Ruiz (2012)

*An Estimation of Distribution Algorithm for Lot-Streaming Flow Shop Problems with Setup Times* — Omega

`pan2012hybrid` · article · Pan, Quan-Ke and Ruiz, Rubén

Used **1×**:

- **Related Work › Estimation of Distribution Algorithms on Cloud Allocation** — `chapters/Related work.tex:23`

  Hybrid EDAs have been used effectively on the multidimensional knapsack problem , and EDA-based
  approaches have been applied competitively to permutation flow-shop scheduling

---

## Pelikan and Mühlenbein (1999)

*The Bivariate Marginal Distribution Algorithm* — Advances in Soft Computing –- Engineering Design and Manufacturing

`pelikan1999bmda` · incollection · Pelikan, Martin and Mühlenbein, Heinz

Used **1×**:

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:447`

  sec:eda-model-classes EDAs are classified by the complexity of the fitted model . Univariate
  models factorise the joint distribution into independent per-variable marginals and ignore
  interactions. Bivariate models capture pairwise dependencies (MIMIC , BMDA )

---

## Pelikan et al. (1999)

*BOA: The Bayesian Optimization Algorithm* — Proceedings of the Genetic and Evolutionary Computation Conference (GECCO-99)

`pelikan1999boa` · inproceedings · Pelikan, Martin and Goldberg, David E. and Cantú-Paz, Erick

Used **1×**:

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:450`

  Multivariate models partition variables into linkage groups (ECGA ) or learn a full Bayesian
  network (BOA )

---

## Pelikan et al. (2002)

*A Survey of Optimization by Building and Using Probabilistic Models* — Computational Optimization and Applications

`pelikan2002survey` · article · Pelikan, Martin and Goldberg, David E. and Lobo, Fernando G.

Used **3×**:

- **Metaheuristic Optimisation Methods › Probabilistic Model-Based Metaheuristics** — `chapters/Metaheuristic Optimisation Methods.tex:420`

  replace the heuristic variation operators with an explicit probabilistic model fitted to the
  currently best solutions, and generate new candidates by sampling from that model

- **Metaheuristic Optimisation Methods › Estimation of Distribution Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:433`

  They emerged in response to the difficulty standard GAs have with strongly interacting variables,
  where crossover can disrupt useful structure : instead of propagating structural information
  implicitly through recombination, an EDA fits a statistical model to the currently selected
  individuals each generation and samples new candidates from it

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:443`

  sec:eda-model-classes EDAs are classified by the complexity of the fitted model

---

## Pérez-Rodríguez and Hernández-Aguirre (2019)

*A Hybrid Estimation of Distribution Algorithm for the Vehicle Routing Problem with Time Windows* — Computers & Industrial Engineering

`perez2019eda` · article · Pérez-Rodríguez, Ricardo and Hernández-Aguirre, Arturo

Used **1×**:

- **Related Work › Cross-Paradigm Benchmarking and Research Gap** — `chapters/Related work.tex:69`

  EDAs have been used on routing problems, but only after being rebuilt around orderings: Pérez-
  Rodríguez and Hernández-Aguirre , for example, replace the simple per-variable model used in this
  thesis with a Mallows model defined directly over sequences

---

## Rodríguez-Esparza et al. (2024)

*A New Hyper-heuristic Based on Adaptive Simulated Annealing and Reinforcement Learning for the Capacitated Electric Vehicle Routing Problem* — Expert Systems with Applications

`rodriguezesparza2024hyperheuristic` · article · Rodríguez-Esparza, Erick and Masegosa, Antonio D. and Oliva, Diego and Onieva, Enrique

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:53`

  Stamadianos et al. combine SA with Variable Neighbourhood Search on a variant called the Close-
  Open EVRP, and Rodríguez-Esparza et al. embed an adaptive version of SA inside a hyper-heuristic
  for the Capacitated EVRP

---

## Rudolph (1994)

*Convergence Analysis of Canonical Genetic Algorithms* — IEEE Transactions on Neural Networks

`rudolph1994` · article · Rudolph, Günter

Used **1×**:

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:128`

  The most basic GA omits it, but it is used throughout this thesis because it guarantees that the
  best solution found never deteriorates

---

## Schneider et al. (2014)

*The Electric Vehicle-Routing Problem with Time Windows and Recharging Stations* — Transportation Science

`schneider2014` · article · Schneider, Michael and Stenger, Andreas and Goeke, Dominik

Used **5×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:45`

  The variant of EVRP with time windows and recharging stations (E-VRPTW) was introduced by
  Schneider et al. , who solved it using a hybrid of Variable Neighbourhood Search (VNS) and Tabu
  Search

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:45`

  for the E-VRPTW and the benchmark suite proposed by Mavrovouniotis et al

- **Metaheuristic Optimisation Methods › Defining the Neighbourhood** — `chapters/Metaheuristic Optimisation Methods.tex:291`

  Because the battery level evolves along the route, dedicated operators insert, remove, or relocate
  charging stations , and a repair operator inserts a station at the cheapest position within an
  interval where battery constraints would otherwise be violated

- **Metaheuristic Optimisation Methods › Solution Construction** — `chapters/Metaheuristic Optimisation Methods.tex:355`

  Unlike the standard TSP setting, the allowed set must account for the vehicle's battery state,
  since energy consumption depends on the entire sequence of decisions made so far

- **Design and Implementation › Dynamic charging-station insertion** — `chapters/Implementation.tex:175`

  Visiting a station while nearly full wastes distance and charging time, yet a station must be
  reachable before the charge becomes critical, so insertion is triggered dynamically by the battery
  state, the standard reserve-threshold treatment of proactive charging in energy-constrained
  routing

---

## Speitkamp and Bichler (2010)

*A Mathematical Programming Approach for Server Consolidation Problems in Virtualized Data Centers* — IEEE Transactions on Services Computing

`speitkamp2010mathematical` · article · Speitkamp, Benjamin and Bichler, Martin

Used **2×**:

- **Related Work › Exact Methods** — `chapters/Related work.tex:11`

  They are typically formulated as Integer Linear Programmes (ILPs) or Mixed-Integer Linear
  Programmes (MILPs) and solved using branch-and-bound-based optimisation solvers

- **Related Work › Exact Methods** — `chapters/Related work.tex:11`

  Speitkamp and Bichler present a mathematical-programming formulation of the server-consolidation
  problem and report that it remains tractable for instances of moderate size, but becomes
  prohibitive once the number of virtual machines and hosts grows into the hundreds

---

## Stamadianos et al. (2025)

*A Hybrid Simulated Annealing and Variable Neighborhood Search Algorithm for the Close-Open Electric Vehicle Routing Problem* — Annals of Mathematics and Artificial Intelligence

`kyriakakis2023` · article · Stamadianos, Themistoklis and Kyriakakis, Nikolaos A. and Marinaki, Magdalene and Marinakis, Yannis

Used **1×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:53`

  Stamadianos et al. combine SA with Variable Neighbourhood Search on a variant called the Close-
  Open EVRP, and Rodríguez-Esparza et al. embed an adaptive version of SA inside a hyper-heuristic
  for the Capacitated EVRP

---

## Stützle and Hoos (2000)

*MAX–MIN Ant System* — Future Generation Computer Systems

`stutzle2000` · article · Stützle, Thomas and Hoos, Holger H.

Used **2×**:

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:386`

  The implementation in this thesis combines the pheromone clamping of MAX--MIN Ant System , which
  bounds pheromone within so that no edge is ever completely abandoned and premature stagnation is
  resisted , with the pseudo-random-proportional rule of Ant Colony System: with probability an ant
  moves greedily to the most attractive allowed node, and otherwise samples from the transition
  distribution above

- **Design and Implementation › Ant Colony Optimisation** — `chapters/Implementation.tex:173`

  The implementation is a Max--Min Ant System , which clamps every pheromone trail between a lower
  and an upper bound to prevent stagnation, combined with the pseudo-random proportional
  construction rule of

---

## Stützle and Dorigo (2002)

*A Short Convergence Proof for a Class of Ant Colony Optimization Algorithms* — IEEE Transactions on Evolutionary Computation

`stutzle2002convergence` · article · Stützle, Thomas and Dorigo, Marco

Used **1×**:

- **Metaheuristic Optimisation Methods › The Pheromone Update** — `chapters/Metaheuristic Optimisation Methods.tex:398`

  The two mechanisms act on different objects, on a single move during construction and the MAX--MIN
  bounds on the pheromone values after the update. For pheromone-bounded variants, convergence in
  value to the global optimum has been proven , though, as with SA's logarithmic-cooling guarantee,
  only in an idealised limit that does not bind under a finite budget

---

## Syswerda (1989)

*Uniform Crossover in Genetic Algorithms* — Proceedings of the Third International Conference on Genetic Algorithms (ICGA)

`syswerda1989` · inproceedings · Syswerda, Gilbert

Used **2×**:

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:124`

  Selection draws parents with a bias toward higher fitness. Variation produces offspring by
  applying crossover with probability and mutation independently at each position with probability

- **Metaheuristic Optimisation Methods › Encoding and Parameters** — `chapters/Metaheuristic Optimisation Methods.tex:150`

  For the Cloud Resource Allocation problem a candidate is encoded as an integer vector with
  denoting the server assigned to task . Standard one-point, two-point, and uniform crossover apply
  directly, because every combination of server indices is a well-formed assignment

---

## Tahami et al. (2020)

*Exact Approaches for Routing Capacitated Electric Vehicles* — Transportation Research Part E: Logistics and Transportation Review

`tahami2020exact` · article · Tahami, Hesamoddin and Rabadi, Ghaith and Haouari, Mohamed

Used **2×**:

- **Related Work › Exact Methods** — `chapters/Related work.tex:38`

  The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with
  commercial solvers or with specialised exact techniques originally developed for the classical VRP
  and later adapted to the EVRP, including branch-and-cut and branch-price-and-cut

- **Related Work › Exact Methods** — `chapters/Related work.tex:38`

  Tahami et al. report that their compact formulation reliably solves instances with up to 30
  customers in moderate CPU time, and that their hybrid approach reaches 100 customers on some
  instances, but struggles on larger or tightly constrained ones

---

## Talbi (2009)

*Metaheuristics: From Design to Implementation* — John Wiley & Sons

`talbi2009` · book · Talbi, El-Ghazali

Used **10×**:

- **Metaheuristic Optimisation Methods › Metaheuristics for Combinatorial Optimisation** — `chapters/Metaheuristic Optimisation Methods.tex:6`

  To solve them, the thesis uses metaheuristics: general-purpose search methods that combine
  randomness with problem-specific logic to find good, if not perfect, solutions within a reasonable
  runtime

- **Metaheuristic Optimisation Methods › Genetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:112`

  Because a GA requires only the ability to evaluate the objective function, it applies as a black-
  box optimiser to both problems in this thesis: on the Cloud Resource Allocation problem,
  recombination can exploit partial structure across many candidate task-to-server assignments in
  parallel

- **Metaheuristic Optimisation Methods › Handling Constraints** — `chapters/Metaheuristic Optimisation Methods.tex:169`

  Of the three standard strategies (penalty functions, repair, and feasibility-preserving operators
  ), the penalty approach is applied, consistent with the objective formulation used by SA and UMDA
  on the same problem: infeasible individuals are retained but their selection fitness is worsened
  in proportion to the CPU and memory violations, weighted by the coefficients and introduced in
  Section

- **Metaheuristic Optimisation Methods › Memetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:197`

  On the routing problem the order-based crossover that the GA relies on frequently breaks up good
  sub-tours, and interleaving a local-search step repairs this disruption, a pairing long
  established for routing problems

- **Metaheuristic Optimisation Methods › Simulated Annealing** — `chapters/Metaheuristic Optimisation Methods.tex:220`

  The analogy to optimisation is that occasional uphill moves early in the search prevent the
  algorithm from getting permanently stuck in a poor solution, while a gradually decreasing
  temperature parameter makes the search increasingly selective

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:242`

  In practice SA is structured with an inner loop: a fixed number of moves (the epoch length) is
  attempted at each temperature level before cooling, so that the neighbourhood is adequately
  sampled before the search commits to a colder regime

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:248`

  The temperature schedule controls how fast SA transitions from broad exploration to focused local
  search, and it is the most important design decision when applying the algorithm

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:268`

  A common extension, used in this thesis, is reheating: if the search stagnates for a number of
  steps, the temperature is raised back to a fraction of its initial value, allowing escape from
  deep local optima while the best solution found so far is retained separately

- **Metaheuristic Optimisation Methods › Defining the Neighbourhood** — `chapters/Metaheuristic Optimisation Methods.tex:287`

  The first concerns customer ordering: 2-opt segment reversal (a special case of the k-opt
  framework of ), swapping two customers, and relocating a customer (removing it from position and
  reinserting it at position , shifting the customers in between by one place), all standard moves
  for permutation-based routing

- **Metaheuristic Optimisation Methods › Handling Constraints** — `chapters/Metaheuristic Optimisation Methods.tex:299`

  SA accommodates constraints through the same penalty formulation as the other methods : capacity
  violations are penalised via the coefficients and of Section on the cloud problem, and battery or
  visit violations via and on the routing problem

---

## Thymianis et al. (2022)

*Electric Vehicle Routing Problem: Literature Review, Instances and Results with a Novel Ant Colony Optimization Method* — 2022 IEEE Congress on Evolutionary Computation (CEC)

`thymianis2022` · inproceedings · Thymianis, Marios and Tzanetos, Alexandros and Osaba, Eneko and Dounias, Georgios and Del Ser, Javier

Used **2×**:

- **Related Work › Heuristics and Metaheuristics on EVRP** — `chapters/Related work.tex:51`

  For a broader review of metaheuristic approaches applied to the EVRP, see Thymianis et al

- **Related Work › Cross-Paradigm Benchmarking and Research Gap** — `chapters/Related work.tex:65`

  Cross-paradigm comparisons within a single problem also exist, such as the ACO-versus-VNS
  comparison of Thymianis et al. on the EVRP or the GA-versus-heuristic study of Wilcox et al. on
  VMP

---

## United Nations Framework Convention on Climate Change (2015)

*Paris Agreement* — United Nations

`unfccc2015paris` · misc · United Nations Framework Convention on Climate Change

Used **1×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:6`

  Electricity prices have risen sharply, international agreements like the Paris Agreement have led
  to strict emissions targets, and companies face increasing pressure to meet corporate
  sustainability pledges

---

## van Laarhoven and Aarts (1987)

*Simulated Annealing: Theory and Applications* — Kluwer Academic Publishers

`vanlaarhoven1987` · book · van Laarhoven, Peter J. M. and Aarts, Emile H. L.

Used **4×**:

- **Metaheuristic Optimisation Methods › Working Principle** — `chapters/Metaheuristic Optimisation Methods.tex:242`

  In practice SA is structured with an inner loop: a fixed number of moves (the epoch length) is
  attempted at each temperature level before cooling, so that the neighbourhood is adequately
  sampled before the search commits to a colder regime

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:248`

  The temperature schedule controls how fast SA transitions from broad exploration to focused local
  search, and it is the most important design decision when applying the algorithm

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:256`

  The starting temperature is commonly calibrated so that typical worsening moves are initially
  accepted around of the time

- **Metaheuristic Optimisation Methods › The Cooling Schedule** — `chapters/Metaheuristic Optimisation Methods.tex:264`

  A logarithmically slow schedule guarantees the global optimum in theory but is far too slow to be
  useful in practice, so performance within a fixed budget depends heavily on the tuned schedule

---

## Virtanen et al. (2020)

*SciPy 1.0: Fundamental Algorithms for Scientific Computing in Python* — Nature Methods

`virtanen2020scipy` · article · Virtanen, Pauli and Gommers, Ralf and Oliphant, Travis E. and Haberland, Matt and Reddy, Tyler and Cournapeau, David and Burovski, Evgeni and Peterson, Pearu and Weckesser, Warren and Bright, Jonathan and van der Walt, Stéfan J. and Brett, Matthew and Wilson, Joshua and Millman, K. Jarrod and Mayorov, Nikolay and Nelson, Andrew R. J. and Jones, Eric and Kern, Robert and Larson, Eric and Carey, C. J. and Polat, \.Ilhan and Feng, Yu and Moore, Eric W. and VanderPlas, Jake and Laxalde, Denis and Perktold, Josef and Cimrman, Robert and Henriksen, Ian and Quintero, E. A. and Harris, Charles R. and Archibald, Anne M. and Ribeiro, Antônio H. and Pedregosa, Fabian and van Mulbregt, Paul and SciPy 1.0 Contributors

Used **1×**:

- **Design and Implementation › Tools and Environment** — `chapters/Implementation.tex:7`

  SciPy provides only the two-sided Wilcoxon signed-rank test, with a manual fallback when
  unavailable

---

## Wang et al. (2012)

*An Effective Hybrid EDA-Based Algorithm for Solving Multidimensional Knapsack Problem* — Expert Systems with Applications

`wang2012hybrid` · article · Wang, Ling and Wang, Sheng-Yao and Xu, Ye

Used **1×**:

- **Related Work › Estimation of Distribution Algorithms on Cloud Allocation** — `chapters/Related work.tex:23`

  Hybrid EDAs have been used effectively on the multidimensional knapsack problem , and EDA-based
  approaches have been applied competitively to permutation flow-shop scheduling

---

## Whitley et al. (2016)

*Gray Box Optimization for Mk Landscapes (NK Landscapes and MAX-kSAT)* — Evolutionary Computation

`whitley2016graybox` · article · Whitley, Darrell and Chicano, Francisco and Goldman, Brian W.

Used **2×**:

- **Introduction › Problem Statement** — `chapters/Introduction.tex:21`

  Of these, SA, GA, and UMDA are black-box optimisers that use only objective-function evaluations,
  whereas ACO is a grey-box method that additionally exploits the distance structure of the routing
  graph

- **Related Work › Ant Colony Optimisation on EVRP** — `chapters/Related work.tex:58`

  ACO is also the only method in this comparison that uses problem-specific information beyond the
  objective value, since its construction is guided by an inverse-distance heuristic over the graph
  edges, which makes it a grey-box method in the sense of Whitley et al. , whereas SA, GA, and UMDA
  operate as black-box optimisers

---

## Wilcox et al. (2011)

*Solving Virtual Machine Packing with a Reordering Grouping Genetic Algorithm* — 2011 IEEE Congress of Evolutionary Computation (CEC)

`wilcox2011reliable` · inproceedings · Wilcox, David and McNabb, Andrew and Seppi, Kevin

Used **2×**:

- **Related Work › Heuristics and Metaheuristics on Cloud Allocation** — `chapters/Related work.tex:18`

  Wilcox et al. apply a reordering grouping GA to VM packing and report consistent improvements over
  greedy heuristics, at substantially higher computational cost

- **Related Work › Cross-Paradigm Benchmarking and Research Gap** — `chapters/Related work.tex:65`

  Cross-paradigm comparisons within a single problem also exist, such as the ACO-versus-VNS
  comparison of Thymianis et al. on the EVRP or the GA-versus-heuristic study of Wilcox et al. on
  VMP

---

## Wilcoxon (1945)

*Individual Comparisons by Ranking Methods* — Biometrics Bulletin

`wilcoxon1945` · article · Wilcoxon, Frank

Used **1×**:

- **Experimental Setup › Evaluation Metrics and Statistical Tests** — `chapters/Experimental Setup.tex:417`

  Significance is tested with the pairwise Wilcoxon signed-rank test (two-sided, )

---

## Witt (2019)

*Upper Bounds on the Running Time of the Univariate Marginal Distribution Algorithm on OneMax* — Algorithmica

`witt2019upper` · article · Witt, Carsten

Used **1×**:

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:463`

  Under the univariate factorisation the model holds parameters ( tasks, servers: one probability
  per task--server pair), re-estimated each generation from only the selected individuals.
  Theoretical analyses show the population must be sized generously relative to to prevent genetic
  drift, in which a marginal moves toward its extremes through finite-sample noise rather than
  genuine selection pressure

---

## Wolpert and Macready (1997)

*No Free Lunch Theorems for Optimization* — IEEE Transactions on Evolutionary Computation

`wolpert1997` · article · Wolpert, David H. and Macready, William G.

Used **2×**:

- **Introduction › Background and Motivation** — `chapters/Introduction.tex:10`

  Such an advantage can never be universal and the No Free Lunch theorems establish that no search
  strategy is best on every problem, so any gain must come from structure the problem actually
  possesses

- **Related Work › Cross-Paradigm Benchmarking and Research Gap** — `chapters/Related work.tex:67`

  This expectation is consistent with the No Free Lunch theorems , which establish that no single
  optimiser dominates across all problems, so any performance advantage must come from exploiting
  problem-specific structure

---

## Wolsey (1998)

*Integer Programming* — Wiley-Interscience

`wolsey1998` · book · Wolsey, Laurence A.

Used **1×**:

- **Problem Specification › Server Utilisation** — `chapters/Problem Specification.tex:203`

  This is unproblematic for the metaheuristics used in this thesis, which evaluate as a black box,
  but it would require a big- linearisation in a classical Mixed-Integer Linear Programming (MILP)
  formulation

---

## The Traveling Salesman Problem: A Guided

*The Traveling Salesman Problem: A Guided Tour of Combinatorial Optimization* — John Wiley & Sons

`lawler1985` · book

Used **1×**:

- **Related Work** — `chapters/Related work.tex:3`

  Although framed in specific application settings, both problems are instances of well-studied
  combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment
  problem with bin-packing structure , while electric vehicle routing extends the Vehicle Routing
  Problem (VRP) , itself a generalisation of the Travelling Salesman Problem

---

## Handbook of Evolutionary Computation

*Handbook of Evolutionary Computation* — IOP Publishing and Oxford University Press

`back1997` · book

Used **3×**:

- **Metaheuristic Optimisation Methods › Genetic Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:107`

  New candidates are produced by recombining existing solutions (crossover) and perturbing them
  (mutation), which together balance exploration of new regions against exploitation of known good
  solutions

- **Metaheuristic Optimisation Methods › Encoding and Parameters** — `chapters/Metaheuristic Optimisation Methods.tex:159`

  Four parameters govern the exploration--exploitation balance : the population size (diversity
  versus cost per generation), the crossover probability (typically -- ), the mutation probability
  (a common heuristic is for representation length ), and the selection pressure via the tournament
  size (typically -- )

- **Metaheuristic Optimisation Methods › Encoding and Parameters** — `chapters/Metaheuristic Optimisation Methods.tex:163` *(same passage)*

  Four parameters govern the exploration--exploitation balance : the population size (diversity
  versus cost per generation), the crossover probability (typically -- ), the mutation probability
  (a common heuristic is for representation length ), and the selection pressure via the tournament
  size (typically -- )

---

## Estimation of Distribution Algorithms: A

*Estimation of Distribution Algorithms: A New Tool for Evolutionary Computation* — Kluwer Academic Publishers

`larranaga2001` · book

Used **6×**:

- **Related Work › Estimation of Distribution Algorithms on Cloud Allocation** — `chapters/Related work.tex:21`

  Estimation of Distribution Algorithms (EDAs) replace the crossover and mutation operators of
  evolutionary algorithms with a probabilistic model that is fitted to selected individuals from the
  current population and then sampled to generate new candidate solutions

- **Metaheuristic Optimisation Methods › Probabilistic Model-Based Metaheuristics** — `chapters/Metaheuristic Optimisation Methods.tex:420`

  replace the heuristic variation operators with an explicit probabilistic model fitted to the
  currently best solutions, and generate new candidates by sampling from that model

- **Metaheuristic Optimisation Methods › Estimation of Distribution Algorithms** — `chapters/Metaheuristic Optimisation Methods.tex:425`

  Estimation of Distribution Algorithms (EDAs) are model-based alternatives to traditional GAs

- **Metaheuristic Optimisation Methods › Model Classes and Choice of Algorithm** — `chapters/Metaheuristic Optimisation Methods.tex:443`

  sec:eda-model-classes EDAs are classified by the complexity of the fitted model

- **Metaheuristic Optimisation Methods › Working Principle of UMDA** — `chapters/Metaheuristic Optimisation Methods.tex:471`

  UMDA maintains a population of candidates and, each generation, performs evaluation, selection,
  estimation, and sampling : [ S_t = select (P_t), p_t = estimate (S_t), P_ t+1 = sample (p_t, N)

- **Metaheuristic Optimisation Methods › Working Principle of UMDA** — `chapters/Metaheuristic Optimisation Methods.tex:504`

  Three parameters govern the exploration--exploitation balance : the population size (estimate
  accuracy and drift resistance), the selection ratio (selection pressure, with a common default),
  and a margin that keeps marginals away from the exact extremes so a value absent from one
  generation's selection is not lost forever , realised in this thesis by Laplace smoothing of the
  frequency counts (Section )

---

## Vehicle Routing: Problems, Methods, and 

*Vehicle Routing: Problems, Methods, and Applications* — Society for Industrial and Applied Mathematics

`toth2014vrp` · book

Used **3×**:

- **Related Work** — `chapters/Related work.tex:3`

  Although framed in specific application settings, both problems are instances of well-studied
  combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment
  problem with bin-packing structure , while electric vehicle routing extends the Vehicle Routing
  Problem (VRP) , itself a generalisation of the Travelling Salesman Problem

- **Related Work › Exact Methods** — `chapters/Related work.tex:38`

  The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with
  commercial solvers or with specialised exact techniques originally developed for the classical VRP
  and later adapted to the EVRP, including branch-and-cut and branch-price-and-cut

- **Related Work › Exact Methods** — `chapters/Related work.tex:40`

  Examples include LP-based rounding, Lagrangian relaxation, column-generation heuristics, and
  matheuristics that combine MILP solvers with neighbourhood search

---

## Černý (1985)

*Thermodynamical approach to the traveling salesman problem: An efficient simulation algorithm* — Journal of Optimization Theory and Applications

`cerny1985` · article · Černý, V.

Used **1×**:

- **Metaheuristic Optimisation Methods › Simulated Annealing** — `chapters/Metaheuristic Optimisation Methods.tex:212`

  Simulated Annealing (SA) is a single-solution search method that improves one candidate step by
  step

---

## Entries in the bibliography that are never cited

These sit in `Bibliography.bib` but no `\cite` refers to them, so they do not appear in the printed reference list. Harmless, but worth removing or citing before submission.

- `adak2026` — Adak and Witt (2026), *Mathematical Runtime Analysis of a Multi-Valued Estimation of Distribution Algorithm* (Artificial Intelligence)
- `baluja1997comit` — Baluja and Davies (1997), *Using Optimal Dependency-Trees for Combinatorial Optimization: Learning the Structure of the Search Space* (Proceedings of the 14th International Conference on Machine Learning (ICML))
- `chen2014pbil` — Chen et al. (2013), *User-Priority Guided Min-Min Scheduling Algorithm for Load Balancing in Cloud Computing* (2013 National Conference on Parallel Computing Technologies (PARCOMPTECH))
- `davis1991` — Davis (1991), *Handbook of Genetic Algorithms* (Van Nostrand Reinhold)
- `euchi2017` — Euchi (2017), *The Vehicle Routing Problem with Private Fleet and Multiple Common Carriers: Solution with Hybrid Metaheuristic Algorithm* (Vehicular Communications)
- `hoos2004` — Hoos and Stützle (2004), *Stochastic Local Search: Foundations and Applications* (Elsevier / Morgan Kaufmann)
- `laporte1983` — Laporte and Nobert (1983), *A Branch and Bound Algorithm for the Capacitated Vehicle Routing Problem* (OR Spektrum)
- `mavrovouniotis2017` — Mavrovouniotis et al. (2017), *A survey of swarm intelligence for dynamic optimization: algorithms and applications* (Swarm and Evolutionary Computation)
- `pelikan2005` — Pelikan (2005), *Hierarchical Bayesian Optimization Algorithm: Toward a New Generation of Evolutionary Algorithms* (Springer)
- `rosenkrantz1977` — Rosenkrantz et al. (1977), *An Analysis of Several Heuristics for the Traveling Salesman Problem* (SIAM Journal on Computing)
- `shapiro2005drift` — Shapiro (2005), *Drift and Scaling in Estimation of Distribution Algorithms* (Evolutionary Computation)
- `sinnott1984` — Sinnott (1984), *Virtues of the Haversine* (Sky and Telescope)
- `xu2010multiobjective` — Xu and Fortes (2010), *Multi-Objective Virtual Machine Placement in Virtualized Data Center Environments* (2010 IEEE/ACM Int'l Conference on Green Computing and Communications & Int'l Conference on Cyber, Physical and Social Computing)
