# EV citation claims — verification checklist

Every claim the thesis attributes to a source, restricted to the EV half. One
entry per citation instance, quoted as the sentence stands in the `.tex` file so
it can be checked against the paper without opening the report.

**How to use it.** Open the paper, read the quoted sentence, and decide whether
the paper actually says that. Tick the box when it does. When it does not, the
fix is usually one of three things: the claim is right but the source is wrong
(swap the key), the source is right but the claim overreaches (narrow the
sentence), or the sentence attributes to the source something that is really our
own choice (split the attribution, as was just done for `deb2000`). Log whatever
you find in `CITATION_VERIFICATION.md`, which already holds
6 checked sources in that format.

**Scope.** Part 1 is EV-only. Part 2 is shared material the EV chapters depend
on. Part 3 is the mirror image: EV passages that assert something citable and
cite nothing. Cloud-only sources (36 references, 70 instances) are Christian's
and are left out.

**Two caveats on the extraction.** Sentences are pulled mechanically, so a few
run into an adjacent equation, which appears as `[equation]`. And a citation
sitting at the end of a sentence sometimes backs only that sentence's final
clause rather than the whole thing — read it in context before calling it wrong.

| | References | Claim instances |
|---|---|---|
| Part 1 — EV-specific | 37 | 66 |
| Part 2 — shared | 45 | 72 |
| **To check** | **72** | **138** |
| Already verified | 5 | — |

Already verified and re-listed here for completeness: `mavrovouniotis2020benchmark`, `nie2022aco-evrpcc`, `tahami2020exact`, `talbi2009`, `vanlaarhoven1987`.

---

## Part 1 — EV-specific references

37 references, 66 claim instances. Cited only where the thesis is talking about the routing problem, the EV energy model, ACO, or MA.

### `attri2025evstations` — Attri (2025)
*Global EV Charging Stations Dataset* · Kaggle

- [ ] **1.** `Problem Specification.tex:305` — Problem Specification › Electric Vehicle Routing Problem › Dataset Overview

  > The charging infrastructure used in this formulation is derived from the Global EV Charging Stations dataset [attri2025evstations], a publicly available collection of $5{,}000$ synthetic charging-station records distributed globally and released under the Apache License 2.0.

---

### `basso2019` — Basso et al. (2019)
*Energy consumption estimation integrated into the Electric Vehicle Routing Problem* · Transportation Research Part D: Transport and Environment

- [ ] **1.** `Problem Model Details.tex:192` — App. Problem Model Details › EV Energy Model: Derivation and Caveats

  > More advanced models such as that of [basso2019] work with link-by-link speed profiles that include acceleration and braking.

- [ ] **2.** `Problem Model Details.tex:200` — App. Problem Model Details › EV Energy Model: Derivation and Caveats

  > The exponent is fixed at 2, reflecting the quadratic growth of aerodynamic drag with speed [basso2019].

- [ ] **3.** `Problem Specification.tex:520` — Problem Specification › Electric Vehicle Routing Problem › Energy Consumption Model

  > The speed multiplier reflects aerodynamic drag, the dominant source of energy loss at higher speeds, growing with the square of vehicle velocity [basso2019].

- [ ] **4.** `Related work.tex:35` — Related Work › Electric Vehicle Routing › Energy Consumption Models

  > Basso et al. [basso2019] integrate such a consumption model, accounting for topography and speed, directly into the EVRP and validate it against real-world measurements from an electric bus.

---

### `clarke1964` — Clarke and Wright (1964)
*Scheduling of Vehicles from a Central Depot to a Number of Delivery Points* · Operations Research

- [ ] **1.** `Related work.tex:49` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Before the metaheuristics literature took over, classical constructive heuristics such as the Clarke and Wright savings algorithm [clarke1964] and the sweep heuristic of Gillett and Miller [gillett1974] dominated the routing literature, and they remain in use today as fast initial-solution generators or as baselines against which more sophisticated methods are compared.

---

### `davis1985` — Davis (1985)
*Applying Adaptive Algorithms to Epistatic Domains* · Proceedings of the 9th International Joint Conference on Artificial Intelligence (IJCAI)

- [ ] **1.** `Implementation.tex:162` — Implementation › Algorithm Implementations for Electric Vehicle Routing › Genetic Algorithm

  > Order crossover (OX) [davis1985] is applied to the customer sub-sequences only, with charging stations stripped out beforehand.

---

### `deb2000` — Deb (2000)
*An efficient constraint handling method for genetic algorithms* · Computer Methods in Applied Mechanics and Engineering

- [ ] **1.** `Implementation.tex:64` — Implementation › Objective Function › Electric Vehicle Routing

  > Anchoring a penalty to the feasible cost scale, so that violating solutions rank below satisfying ones, is the principle of [deb2000]; the factor of one hundred is a calibration choice of this thesis, realised as a static penalty [michalewicz1996] rather than as Deb's comparison operator.

---

### `desaulniers2016` — Desaulniers et al. (2016)
*Exact Algorithms for Electric Vehicle-Routing Problems with Time Windows* · Operations Research

- [ ] **1.** `Related work.tex:38` — Related Work › Electric Vehicle Routing › Exact Methods

  > The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with commercial solvers [mavrovouniotis2020benchmark] or with specialised exact techniques originally developed for the classical VRP and later adapted to the EVRP, including branch-and-cut [tahami2020exact] and branch-price-and-cut [desaulniers2016, toth2014vrp].

---

### `dorigo1997` — Dorigo and Gambardella (1997)
*Ant colony system: a cooperative learning approach to the traveling salesman problem* · IEEE Transactions on Evolutionary Computation

- [ ] **1.** `Implementation.tex:172` — Implementation › Algorithm Implementations for Electric Vehicle Routing › Ant Colony Optimisation

  > The implementation is a Max--Min Ant System [stutzle2000], which clamps every pheromone trail between a lower and an upper bound to prevent stagnation, combined with the pseudo-random proportional construction rule of [dorigo1997].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:386` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > Variants differ in how reinforcement is applied: the original Ant System [dorigo1996] lets all ants deposit, while Ant Colony System [dorigo1997] restricts deposit to the best ant.

---

### `dorigo2004` — Dorigo and Stutzle (2004)
*Ant Colony Optimization* · MIT Press

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:317` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation

  > Ant Colony Optimisation (ACO) [dorigo1996,dorigo2004] is a population-based method in which artificial ants cooperate to build solutions by following and reinforcing promising paths, mimicking the foraging behaviour of real colonies: ants deposit pheromone as they walk, others preferentially follow stronger trails, and shorter paths accumulate pheromone faster, so the colony converges on good routes without any individual having a global view.

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:329` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation

  > First demonstrated on the Travelling Salesman Problem [dorigo1996], ACO has become one of the most widely applied metaheuristics for routing and sequencing problems [dorigo2004].

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:350` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › Solution Construction

  > Pheromone is initialised to a small positive constant $_0$, commonly scaled from a greedy nearest-neighbour tour [dorigo2004], and the colony size $m$ trades per-iteration diversity against computational effort.

- [ ] **4.** `Metaheuristic Optimisation Methods.tex:390` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > The implementation in this thesis combines the pheromone clamping of MAX--MIN Ant System [stutzle2000], which bounds pheromone within $[_{}, _{}]$ so that no edge is ever completely abandoned and premature stagnation is resisted [dorigo2004], with the pseudo-random-proportional rule of Ant Colony System: with probability $q_0$ an ant moves greedily to the most attractive allowed node, and otherwise samples from the transition distribution above.

- [ ] **5.** `Metaheuristic Optimisation Methods.tex:409` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › Handling Constraints

  > During construction, infeasible moves can be excluded from ${A}^k$ (an ant can be prevented from travelling to a node that would exhaust the battery), which guarantees feasible tours but can limit exploration when the feasible region is small [dorigo2004].

---

### `dorigo1996` — Dorigo et al. (1996)
*Ant system: optimization by a colony of cooperating agents* · IEEE Transactions on Systems, Man, and Cybernetics, Part B

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:317` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation

  > Ant Colony Optimisation (ACO) [dorigo1996,dorigo2004] is a population-based method in which artificial ants cooperate to build solutions by following and reinforcing promising paths, mimicking the foraging behaviour of real colonies: ants deposit pheromone as they walk, others preferentially follow stronger trails, and shorter paths accumulate pheromone faster, so the colony converges on good routes without any individual having a global view.

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:327` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation

  > First demonstrated on the Travelling Salesman Problem [dorigo1996], ACO has become one of the most widely applied metaheuristics for routing and sequencing problems [dorigo2004].

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:343` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › Solution Construction

  > [equation] where ${A}^k$ is the set of nodes still allowed for ant $k$, $_{ij}$ is the pheromone level on edge $(i,j)$, and $_{ij}$ is a heuristic desirability, typically inverse distance $_{ij} = 1 / d_{ij}$ [dorigo1996].

- [ ] **4.** `Metaheuristic Optimisation Methods.tex:365` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > Once all ants have completed their tours, evaporation and deposit are combined into a single update [dorigo1996]: [equation] where $(0, 1)$ is the evaporation rate.

- [ ] **5.** `Metaheuristic Optimisation Methods.tex:380` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > The deposit term is [equation] where $L_k$ is the total cost of ant $k$'s tour, so better solutions exert a stronger influence on future iterations [dorigo1996], and $Q$ is a constant scaling every deposit equally, leaving the learning signal in the $1/L_k$ ratio alone (fixed at $Q = 1$ here).

- [ ] **6.** `Metaheuristic Optimisation Methods.tex:385` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > Variants differ in how reinforcement is applied: the original Ant System [dorigo1996] lets all ants deposit, while Ant Colony System [dorigo1997] restricts deposit to the best ant.

---

### `droste2006upper` — Droste et al. (2006)
*Upper and Lower Bounds for Randomized Search Heuristics in Black-Box Optimization* · Theory of Computing Systems

- [ ] **1.** `Related work.tex:58` — Related Work › Electric Vehicle Routing › Ant Colony Optimisation on EVRP

  > ACO is also the only method in this comparison that uses problem-specific information beyond the objective value, since its construction is guided by an inverse-distance heuristic over the graph edges, which makes it a grey-box method in the sense of Whitley et al. [whitley2016graybox], whereas SA, GA, and UMDA operate as black-box optimisers [droste2006upper].

---

### `farr2007srtm` — Farr et al. (2007)
*The Shuttle Radar Topography Mission* · Reviews of Geophysics

- [ ] **1.** `Problem Specification.tex:357` — Problem Specification › Electric Vehicle Routing Problem › Dataset Overview

  > The road distances $d_{ij}$ and travel times $t_{ij}$ are obtained from the Open Source Routing Machine (OSRM) [luxen2011osrm] on the OpenStreetMap San Francisco road network, and the per-node elevations $elev_i$ from the Shuttle Radar Topography Mission (SRTM) digital elevation model [farr2007srtm].

---

### `felipe2014` — Felipe et al. (2014)
*A Heuristic Approach for the Green Vehicle Routing Problem with Multiple Technologies and Partial Recharges* · Transportation Research Part E: Logistics and Transportation Review

- [ ] **1.** `Related work.tex:47` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Some allow only full recharges, others allow partial recharging [keskin2016, felipe2014].

---

### `froger2022exact` — Froger et al. (2022)
*The Electric Vehicle Routing Problem with Capacitated Charging Stations* · Transportation Science

- [ ] **1.** `Related work.tex:38` — Related Work › Electric Vehicle Routing › Exact Methods

  > Realistic features such as nonlinear charging functions or speed-dependent energy use make the formulations even larger, and often require approximations that introduce errors of their own [froger2022exact].

- [ ] **2.** `Related work.tex:40` — Related Work › Electric Vehicle Routing › Exact Methods

  > Examples include LP-based rounding, Lagrangian relaxation, column-generation heuristics, and matheuristics that combine MILP solvers with neighbourhood search [toth2014vrp], [froger2022exact].

- [ ] **3.** `Related work.tex:42` — Related Work › Electric Vehicle Routing › Exact Methods

  > The gradient- and speed-dependent arc energies and freely revisitable stations used here (Chapter (ch:problem_specification)) would require the kind of enlarged or approximated formulations discussed by Froger et al. [froger2022exact].

- [ ] **4.** `Related work.tex:45` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > On EVRP benchmark sets more generally, later work has reported incremental improvements on the best-known solutions [froger2022exact].

---

### `gillett1974` — Gillett and Miller (1974)
*A Heuristic Algorithm for the Vehicle-Dispatch Problem* · Operations Research

- [ ] **1.** `Related work.tex:49` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Before the metaheuristics literature took over, classical constructive heuristics such as the Clarke and Wright savings algorithm [clarke1964] and the sweep heuristic of Gillett and Miller [gillett1974] dominated the routing literature, and they remain in use today as fast initial-solution generators or as baselines against which more sophisticated methods are compared.

---

### `gutjahr2000` — Gutjahr (2000)
*A Graph-based Ant System and its Convergence* · Future Generation Computer Systems

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:400` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > For pheromone-bounded variants, convergence in value to the global optimum has been proven [gutjahr2000,stutzle2002convergence], though, as with SA's logarithmic-cooling guarantee, only in an idealised limit that does not bind under a finite budget.

---

### `hiermann2016` — Hiermann et al. (2016)
*The Electric Fleet Size and Mix Vehicle Routing Problem with Time Windows and Recharging Stations* · European Journal of Operational Research

- [ ] **1.** `Related work.tex:51` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Among the metaheuristics used on the EVRP, Adaptive Large Neighbourhood Search (ALNS) is one of the most widely used [keskin2016, hiermann2016, kucukoglu2021].

---

### `karakatic2021` — Karakatic (2021)
*Optimizing Nonlinear Charging Times of Electric Vehicle Routing with Genetic Algorithm* · Expert Systems with Applications

- [ ] **1.** `Related work.tex:53` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Karakatič [karakatic2021] solves a multi-depot EVRP variant with nonlinear charging using a GA in which the genotype is split into two layers, one for the customer visit order and one for charging decisions, with a different crossover operator applied to each.

---

### `keskin2016` — Keskin and Catay (2016)
*Partial Recharge Strategies for the Electric Vehicle Routing Problem with Time Windows* · Transportation Research Part C: Emerging Technologies

- [ ] **1.** `Related work.tex:47` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Some allow only full recharges, others allow partial recharging [keskin2016, felipe2014].

- [ ] **2.** `Related work.tex:51` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Among the metaheuristics used on the EVRP, Adaptive Large Neighbourhood Search (ALNS) is one of the most widely used [keskin2016, hiermann2016, kucukoglu2021].

---

### `kucukoglu2021` — Kucukoglu et al. (2021)
*The Electric Vehicle Routing Problem and Its Variations: A Literature Review* · Computers \& Industrial Engineering

- [ ] **1.** `Related work.tex:47` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > A full treatment of these variants is out of scope here, but the survey by Küçükoğlu et al. [kucukoglu2021] covers them in detail.

- [ ] **2.** `Related work.tex:51` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Among the metaheuristics used on the EVRP, Adaptive Large Neighbourhood Search (ALNS) is one of the most widely used [keskin2016, hiermann2016, kucukoglu2021].

---

### `liu2022hybridga` — Liu et al. (2022)
*A Hybrid Genetic Algorithm for the Electric Vehicle Routing Problem with Time Windows* · Control Theory and Technology

- [ ] **1.** `Related work.tex:53` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Liu et al. [liu2022hybridga] are a representative example: they combine 2-opt local search with a GA on an E-VRPTW variant that incorporates road terrain grades into energy consumption, and report improvements over both a GA without local search and a Simulated Annealing baseline on the same instances.

---

### `luxen2011osrm` — Luxen and Vetter (2011)
*Real-time routing with OpenStreetMap data* · Proceedings of the 19th ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems

- [ ] **1.** `Problem Specification.tex:355` — Problem Specification › Electric Vehicle Routing Problem › Dataset Overview

  > The road distances $d_{ij}$ and travel times $t_{ij}$ are obtained from the Open Source Routing Machine (OSRM) [luxen2011osrm] on the OpenStreetMap San Francisco road network, and the per-node elevations $elev_i$ from the Shuttle Radar Topography Mission (SRTM) digital elevation model [farr2007srtm].

---

### `mavrovouniotis2020benchmark` — Mavrovouniotis et al. (2020) ✅ *already verified in `CITATION_VERIFICATION.md`*
*A Benchmark Test Suite for the Electric Capacitated Vehicle Routing Problem* · 2020 IEEE Congress on Evolutionary Computation (CEC)

- [ ] **1.** `Related work.tex:38` — Related Work › Electric Vehicle Routing › Exact Methods

  > The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with commercial solvers [mavrovouniotis2020benchmark] or with specialised exact techniques originally developed for the classical VRP and later adapted to the EVRP, including branch-and-cut [tahami2020exact] and branch-price-and-cut [desaulniers2016, toth2014vrp].

- [ ] **2.** `Related work.tex:38` — Related Work › Electric Vehicle Routing › Exact Methods

  > Mavrovouniotis et al. [mavrovouniotis2020benchmark] support this scaling limit on the related Electric Capacitated Vehicle Routing Problem (E-CVRP), reporting that their MILP formulation could not find solutions for large-scale instances within a time limit of approximately three weeks.

- [ ] **3.** `Related work.tex:45` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > The instances introduced by Schneider et al. for the E-VRPTW [schneider2014] and the benchmark suite proposed by Mavrovouniotis et al. for the E-CVRP [mavrovouniotis2020benchmark] are widely used testbeds for their respective EVRP variants.

---

### `mavrovouniotis2018` — Mavrovouniotis et al. (2018)
*Ant Colony Optimization for the Electric Vehicle Routing Problem* · 2018 IEEE Symposium Series on Computational Intelligence (SSCI)

- [ ] **1.** `Related work.tex:56` — Related Work › Electric Vehicle Routing › Ant Colony Optimisation on EVRP

  > Ant Colony Optimisation was applied to the EVRP by Mavrovouniotis et al. [mavrovouniotis2018], using the MAX--MIN Ant System (MMAS) variant together with a look-ahead strategy that ensures EVs always retain enough energy to reach a charging station.

---

### `michalewicz1996` — Michalewicz (1996)
*Genetic Algorithms + Data Structures = Evolution Programs* · Springer

- [ ] **1.** `Implementation.tex:64` — Implementation › Objective Function › Electric Vehicle Routing

  > Anchoring a penalty to the feasible cost scale, so that violating solutions rank below satisfying ones, is the principle of [deb2000]; the factor of one hundred is a calibration choice of this thesis, realised as a static penalty [michalewicz1996] rather than as Deb's comparison operator.

---

### `moscato1989` — Moscato (1989) ✅ *verified in `CITATION_VERIFICATION.md`*
*On Evolution, Search, Optimization, Genetic Algorithms and Martial Arts: Towards Memetic Algorithms*

- [x] **1.** `Implementation.tex:168` — Implementation › Algorithm Implementations for Electric Vehicle Routing › Memetic Algorithm

  > The memetic algorithm [moscato1989] reuses the GA but refines each offspring with up to thirty first-improvement local-search steps (drawn from the same eight operators) before it enters the population.

- [x] **2.** `Metaheuristic Optimisation Methods.tex:190` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Memetic Algorithms

  > A Memetic Algorithm (MA) hybridises a population-based method with local search, so that the population evolves over locally optimised solutions rather than raw offspring [moscato1989].{The name is Moscato's, after Dawkins's meme, a unit of cultural rather than genetic transmission.

- [x] **3.** `Metaheuristic Optimisation Methods.tex:190` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Memetic Algorithms *(edited: gene clause narrowed)*

  > Unlike a gene, a meme is usually improved by its carrier before being passed on, which is what local search does to each offspring [moscato1989].} In this thesis the MA extends the Genetic Algorithm of the previous section.

- [x] **4.** `Related work.tex:53` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Combining a genetic algorithm with local refinement yields a memetic algorithm [moscato1989], a template that is particularly effective on routing problems because the local-search step repairs the route disruption that recombination causes.

---

### `nie2022aco-evrpcc` — Nie et al. (2022) ✅ *already verified in `CITATION_VERIFICATION.md`*
*Ant Colony Optimization for Electric Vehicle Routing Problem with Capacity and Charging Time Constraints* · 2022 IEEE International Conference on Systems, Man, and Cybernetics (SMC)

- [ ] **1.** `Related work.tex:56` — Related Work › Electric Vehicle Routing › Ant Colony Optimisation on EVRP

  > A later study by Nie et al. [nie2022aco-evrpcc] compared five classical ACO variants, Ant System (AS), Rank-Based Ant System (Rank-AS), Elitist Ant System (EAS), MMAS, and Ant Colony System (ACS), on an EVRP variant with capacity and charging-time constraints, and found Rank-AS to be the strongest performer overall.

---

### `rodriguezesparza2024hyperheuristic` — Rodriguez-Esparza et al. (2024)
*A New Hyper-heuristic Based on Adaptive Simulated Annealing and Reinforcement Learning for the Capacitated Electric Vehicle Routing Problem* · Expert Systems with Applications

- [ ] **1.** `Related work.tex:53` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Stamadianos et al. [kyriakakis2023] combine SA with Variable Neighbourhood Search on a variant called the Close-Open EVRP, and Rodríguez-Esparza et al. [rodriguezesparza2024hyperheuristic] embed an adaptive version of SA inside a hyper-heuristic for the Capacitated EVRP.

---

### `rosenkrantz1977` — Rosenkrantz et al. (1977)
*An Analysis of Several Heuristics for the Traveling Salesman Problem* · SIAM Journal on Computing

- [ ] **1.** `Implementation.tex:138` — Implementation › Algorithm Implementations for Electric Vehicle Routing › Greedy Nearest-Neighbour

  > Customers are first placed in nearest-neighbour order [rosenkrantz1977].

---

### `schneider2014` — Schneider et al. (2014)
*The Electric Vehicle-Routing Problem with Time Windows and Recharging Stations* · Transportation Science

- [ ] **1.** `Implementation.tex:174` — Implementation › Algorithm Implementations for Electric Vehicle Routing › Ant Colony Optimisation

  > Visiting a station while nearly full wastes distance and charging time, yet a station must be reachable before the charge becomes critical, so insertion is triggered dynamically by the battery state, the standard reserve-threshold treatment of proactive charging in energy-constrained routing [schneider2014].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:357` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › Solution Construction

  > Unlike the standard TSP setting, the allowed set ${A}^k$ must account for the vehicle's battery state, since energy consumption depends on the entire sequence of decisions made so far [schneider2014].

- [ ] **3.** `Related work.tex:45` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > The variant of EVRP with time windows and recharging stations (E-VRPTW) was introduced by Schneider et al. [schneider2014], who solved it using a hybrid of Variable Neighbourhood Search (VNS) and Tabu Search.

- [ ] **4.** `Related work.tex:45` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > The instances introduced by Schneider et al. for the E-VRPTW [schneider2014] and the benchmark suite proposed by Mavrovouniotis et al. for the E-CVRP [mavrovouniotis2020benchmark] are widely used testbeds for their respective EVRP variants.

---

### `kyriakakis2023` — Stamadianos et al. (2025)
*A Hybrid Simulated Annealing and Variable Neighborhood Search Algorithm for the Close-Open Electric Vehicle Routing Problem* · Annals of Mathematics and Artificial Intelligence

- [ ] **1.** `Related work.tex:53` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > Stamadianos et al. [kyriakakis2023] combine SA with Variable Neighbourhood Search on a variant called the Close-Open EVRP, and Rodríguez-Esparza et al. [rodriguezesparza2024hyperheuristic] embed an adaptive version of SA inside a hyper-heuristic for the Capacitated EVRP.

---

### `stutzle2002convergence` — Stutzle and Dorigo (2002)
*A Short Convergence Proof for a Class of Ant Colony Optimization Algorithms* · IEEE Transactions on Evolutionary Computation

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:400` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > For pheromone-bounded variants, convergence in value to the global optimum has been proven [gutjahr2000,stutzle2002convergence], though, as with SA's logarithmic-cooling guarantee, only in an idealised limit that does not bind under a finite budget.

---

### `stutzle2000` — Stutzle and Hoos (2000)
*MAX--MIN Ant System* · Future Generation Computer Systems

- [ ] **1.** `Implementation.tex:172` — Implementation › Algorithm Implementations for Electric Vehicle Routing › Ant Colony Optimisation

  > The implementation is a Max--Min Ant System [stutzle2000], which clamps every pheromone trail between a lower and an upper bound to prevent stagnation, combined with the pseudo-random proportional construction rule of [dorigo1997].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:388` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Ant Colony Optimisation › The Pheromone Update

  > The implementation in this thesis combines the pheromone clamping of MAX--MIN Ant System [stutzle2000], which bounds pheromone within $[_{}, _{}]$ so that no edge is ever completely abandoned and premature stagnation is resisted [dorigo2004], with the pseudo-random-proportional rule of Ant Colony System: with probability $q_0$ an ant moves greedily to the most attractive allowed node, and otherwise samples from the transition distribution above.

---

### `tahami2020exact` — Tahami et al. (2020) ✅ *already verified in `CITATION_VERIFICATION.md`*
*Exact Approaches for Routing Capacitated Electric Vehicles* · Transportation Research Part E: Logistics and Transportation Review

- [ ] **1.** `Related work.tex:38` — Related Work › Electric Vehicle Routing › Exact Methods

  > The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with commercial solvers [mavrovouniotis2020benchmark] or with specialised exact techniques originally developed for the classical VRP and later adapted to the EVRP, including branch-and-cut [tahami2020exact] and branch-price-and-cut [desaulniers2016, toth2014vrp].

- [ ] **2.** `Related work.tex:38` — Related Work › Electric Vehicle Routing › Exact Methods

  > Tahami et al. [tahami2020exact] report that their compact formulation reliably solves instances with up to 30 customers in moderate CPU time, and that their hybrid approach reaches 100 customers on some instances, but fails on the tightly constrained large-scale ones.

---

### `talbi2009` — Talbi (2009) ✅ *already verified in `CITATION_VERIFICATION.md`*
*Metaheuristics: From Design to Implementation* · John Wiley \& Sons

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:198` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Memetic Algorithms

  > On the routing problem the order-based crossover that the GA relies on frequently breaks up good sub-tours, and interleaving a local-search step repairs this disruption, a pairing long established for routing problems [talbi2009].

---

### `thymianis2022` — Thymianis et al. (2022)
*Electric Vehicle Routing Problem: Literature Review, Instances and Results with a Novel Ant Colony Optimization Method* · 2022 IEEE Congress on Evolutionary Computation (CEC)

- [ ] **1.** `Related work.tex:51` — Related Work › Electric Vehicle Routing › Heuristics and Metaheuristics on EVRP

  > For a broader review of metaheuristic approaches applied to the EVRP, see Thymianis et al. [thymianis2022].

---

### `toth2014vrp` — Toth and Vigo (2014)
*Vehicle Routing: Problems, Methods, and Applications* · Society for Industrial and Applied Mathematics

- [ ] **1.** `Related work.tex:38` — Related Work › Electric Vehicle Routing › Exact Methods

  > The EVRP is usually formulated as a mixed-integer linear programme (MILP) and solved either with commercial solvers [mavrovouniotis2020benchmark] or with specialised exact techniques originally developed for the classical VRP and later adapted to the EVRP, including branch-and-cut [tahami2020exact] and branch-price-and-cut [desaulniers2016, toth2014vrp].

- [ ] **2.** `Related work.tex:40` — Related Work › Electric Vehicle Routing › Exact Methods

  > Examples include LP-based rounding, Lagrangian relaxation, column-generation heuristics, and matheuristics that combine MILP solvers with neighbourhood search [toth2014vrp], [froger2022exact].

---

### `whitley2016graybox` — Whitley et al. (2016)
*Gray Box Optimization for Mk Landscapes (NK Landscapes and MAX-kSAT)* · Evolutionary Computation

- [ ] **1.** `Related work.tex:58` — Related Work › Electric Vehicle Routing › Ant Colony Optimisation on EVRP

  > ACO is also the only method in this comparison that uses problem-specific information beyond the objective value, since its construction is guided by an inverse-distance heuristic over the graph edges, which makes it a grey-box method in the sense of Whitley et al. [whitley2016graybox], whereas SA, GA, and UMDA operate as black-box optimisers [droste2006upper].

---
## Part 2 — Shared references the EV chapters lean on

45 references, 72 claim instances. Cited in material that covers both problems: the introduction, the shared SA and GA theory, the statistics, and the tooling. Christian's cloud chapters rest on the same sentences, so a correction here changes both halves of the thesis.

### `back1997` — Back et al. (1997)
*Handbook of Evolutionary Computation* · IOP Publishing and Oxford University Press

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:107` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms

  > New candidates are produced by recombining existing solutions (crossover) and perturbing them (mutation), which together balance exploration of new regions against exploitation of known good solutions [eiben2015,back1997].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:159` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Encoding and Parameters

  > Four parameters govern the exploration--exploitation balance [goldberg1989,eiben2015,back1997]: the population size $N$ (diversity versus cost per generation), the crossover probability $p_c$ (typically $0.6$--$0.9$), the mutation probability $p_m$ (a common heuristic is $p_m 1/L$ for representation length $L$ [back1997]), and the selection pressure via the tournament size $k$ (typically $2$--$5$).

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:163` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Encoding and Parameters

  > Four parameters govern the exploration--exploitation balance [goldberg1989,eiben2015,back1997]: the population size $N$ (diversity versus cost per generation), the crossover probability $p_c$ (typically $0.6$--$0.9$), the mutation probability $p_m$ (a common heuristic is $p_m 1/L$ for representation length $L$ [back1997]), and the selection pressure via the tournament size $k$ (typically $2$--$5$).

---

### `cerny1985` — Cerny (1985)
*Thermodynamical approach to the traveling salesman problem: An efficient simulation algorithm* · Journal of Optimization Theory and Applications

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:213` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing

  > Simulated Annealing (SA) [kirkpatrick1983,cerny1985] is a single-solution search method that improves one candidate step by step.

---

### `coffman1997` — Coffman et al. (1997)
*Approximation Algorithms for Bin Packing: A Survey* · Approximation Algorithms for NP-Hard Problems

- [ ] **1.** `Related work.tex:3` — Related Work

  > Although framed in specific application settings, both problems are instances of well-studied combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment problem with bin-packing structure [coffman1997,garey1979], while electric vehicle routing extends the Vehicle Routing Problem (VRP) [dantzig1959,toth2014vrp], itself a generalisation of the Travelling Salesman Problem [lawler1985].

---

### `dantzig1959` — Dantzig and Ramser (1959)
*The Truck Dispatching Problem* · Management Science

- [ ] **1.** `Related work.tex:3` — Related Work

  > Although framed in specific application settings, both problems are instances of well-studied combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment problem with bin-packing structure [coffman1997,garey1979], while electric vehicle routing extends the Vehicle Routing Problem (VRP) [dantzig1959,toth2014vrp], itself a generalisation of the Travelling Salesman Problem [lawler1985].

---

### `devries2023growing` — de Vries (2023)
*The growing energy footprint of artificial intelligence* · Joule

- [ ] **1.** `Introduction.tex:8` — Introduction › Background and Motivation

  > This is a major concern due to the size of modern data centres [masanet2020recalibrating] and the growing demands of AI workloads [iea2025energyai,devries2023growing].

---

### `demsar2006statistical` — Demsar (2006)
*Statistical Comparisons of Classifiers over Multiple Data Sets* · Journal of Machine Learning Research

- [ ] **1.** `Experimental Setup.tex:422` — Experimental Setup › Evaluation Metrics and Statistical Tests

  > The test is paired (because every algorithm is run on the same seed list, the two algorithms in a pair are compared seed by seed) and non-parametric, so it makes no normality assumption about the cost distribution, which is the safe choice for the small number of seeds used here and follows the standard recommendations for comparing stochastic optimisers [demsar2006statistical, derrac2011practical].

---

### `derrac2011practical` — Derrac et al. (2011)
*A Practical Tutorial on the Use of Nonparametric Statistical Tests as a Methodology for Comparing Evolutionary and Swarm Intelligence Algorithms* · Swarm and Evolutionary Computation

- [ ] **1.** `Experimental Setup.tex:422` — Experimental Setup › Evaluation Metrics and Statistical Tests

  > The test is paired (because every algorithm is run on the same seed list, the two algorithms in a pair are compared seed by seed) and non-parametric, so it makes no normality assumption about the cost distribution, which is the safe choice for the small number of seeds used here and follows the standard recommendations for comparing stochastic optimisers [demsar2006statistical, derrac2011practical].

- [ ] **2.** `Related work.tex:65` — Related Work › Cross-Paradigm Benchmarking and Research Gap

  > Within-paradigm benchmarks are relatively common, for example the five-variant ACO comparison of Nie et al. [nie2022aco-evrpcc] on the EVRP, or the Derrac-style comparison protocols [derrac2011practical] increasingly adopted in the metaheuristics literature.

---

### `dorigo1996` — Dorigo et al. (1996)
*Ant system: optimization by a colony of cooperating agents* · IEEE Transactions on Systems, Man, and Cybernetics, Part B

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:572` — Metaheuristics › Matching Algorithms to Problems

  > Its pheromone model is indexed by edges (the same unit in which route cost accrues), and routing has been ACO's classic application domain since its first demonstration on the TSP [dorigo1996].

---

### `droste2006upper` — Droste et al. (2006)
*Upper and Lower Bounds for Randomized Search Heuristics in Black-Box Optimization* · Theory of Computing Systems

- [ ] **1.** `Introduction.tex:21` — Introduction › Problem Statement

  > Of these, SA, GA, and UMDA are black-box optimisers that use only objective-function evaluations, whereas ACO is a grey-box method that additionally exploits the distance structure of the routing graph [whitley2016graybox,droste2006upper].

---

### `eiben2015` — Eiben and Smith (2015)
*Introduction to Evolutionary Computing* · Springer

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:6` — Metaheuristics › Metaheuristics for Combinatorial Optimisation

  > To solve them, the thesis uses metaheuristics: general-purpose search methods that combine randomness with problem-specific logic to find good, if not perfect, solutions within a reasonable runtime [talbi2009,eiben2015].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:107` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms

  > New candidates are produced by recombining existing solutions (crossover) and perturbing them (mutation), which together balance exploration of new regions against exploitation of known good solutions [eiben2015,back1997].

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:136` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Working Principle

  > It is scale-invariant, so it handles a minimised objective without any fitness transformation, and the tournament size $k$ gives direct control over selection pressure [goldberg1989,eiben2015].

- [ ] **4.** `Metaheuristic Optimisation Methods.tex:143` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Working Principle

  > The dominant failure mode is premature convergence: once the population homogenises on a suboptimal region, crossover cannot recover the lost diversity and mutation alone is slow to do so [eiben2015].

- [ ] **5.** `Metaheuristic Optimisation Methods.tex:159` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Encoding and Parameters

  > Four parameters govern the exploration--exploitation balance [goldberg1989,eiben2015,back1997]: the population size $N$ (diversity versus cost per generation), the crossover probability $p_c$ (typically $0.6$--$0.9$), the mutation probability $p_m$ (a common heuristic is $p_m 1/L$ for representation length $L$ [back1997]), and the selection pressure via the tournament size $k$ (typically $2$--$5$).

---

### `felipe2014` — Felipe et al. (2014)
*A Heuristic Approach for the Green Vehicle Routing Problem with Multiple Technologies and Partial Recharges* · Transportation Research Part E: Logistics and Transportation Review

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:295` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Defining the Neighbourhood

  > Because the battery level evolves along the route, dedicated operators insert, remove, or relocate charging stations [schneider2014], and a repair operator inserts a station at the cheapest position within an interval where battery constraints would otherwise be violated [felipe2014].

---

### `gao2013multi` — Gao et al. (2013)
*A Multi-Objective Ant Colony System Algorithm for Virtual Machine Placement in Cloud Computing* · Journal of Computer and System Sciences

- [ ] **1.** `Related work.tex:69` — Related Work › Cross-Paradigm Benchmarking and Research Gap

  > The opposite mismatch is just as clear: ACO has been applied to virtual machine placement [gao2013multi], but ACO stores its learning on the edges between nodes, and an assignment problem has no meaningful edges to learn from, only the choice of which server receives each task.

---

### `garey1979` — Garey and Johnson (1979)
*Computers and Intractability: A Guide to the Theory of NP-Completeness* · W. H. Freeman and Company

- [ ] **1.** `Introduction.tex:8` — Introduction › Background and Motivation

  > They require complex decisions under tight resource limits, and both are NP-hard [garey1979,lenstra1981complexity], so no exact algorithm is known whose running time scales polynomially with instance size.

- [ ] **2.** `Related work.tex:3` — Related Work

  > Although framed in specific application settings, both problems are instances of well-studied combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment problem with bin-packing structure [coffman1997,garey1979], while electric vehicle routing extends the Vehicle Routing Problem (VRP) [dantzig1959,toth2014vrp], itself a generalisation of the Travelling Salesman Problem [lawler1985].

---

### `goldberg1989` — Goldberg (1989)
*Genetic Algorithms in Search, Optimization, and Machine Learning* · Addison-Wesley Professional

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:99` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms

  > Genetic Algorithms (GAs) [holland1975,goldberg1989] are a population-based metaheuristic inspired by Darwinian natural selection: a population of encoded candidate solutions undergoes repeated cycles of selection and variation, higher-fitness individuals are more likely to reproduce, and favourable traits propagate over generations.

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:124` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Working Principle

  > Variation produces offspring by applying crossover with probability $p_c$ and mutation independently at each position with probability $p_m$ [syswerda1989,goldberg1989].

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:136` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Working Principle

  > It is scale-invariant, so it handles a minimised objective without any fitness transformation, and the tournament size $k$ gives direct control over selection pressure [goldberg1989,eiben2015].

- [ ] **4.** `Metaheuristic Optimisation Methods.tex:159` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Encoding and Parameters

  > Four parameters govern the exploration--exploitation balance [goldberg1989,eiben2015,back1997]: the population size $N$ (diversity versus cost per generation), the crossover probability $p_c$ (typically $0.6$--$0.9$), the mutation probability $p_m$ (a common heuristic is $p_m 1/L$ for representation length $L$ [back1997]), and the selection pressure via the tournament size $k$ (typically $2$--$5$).

---

### `hajek1988` — Hajek (1988)
*Cooling schedules for optimal annealing* · Mathematics of Operations Research

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:262` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > A logarithmically slow schedule guarantees the global optimum in theory [hajek1988] but is far too slow to be useful in practice, so performance within a fixed budget depends heavily on the tuned schedule [vanlaarhoven1987].

---

### `harris2020array` — Harris et al. (2020)
*Array Programming with NumPy* · Nature

- [ ] **1.** `Implementation.tex:7` — Implementation › Tools and Environment

  > NumPy [harris2020array] supplies the vectorised operations behind the objective functions, neighbourhood operators, and UMDA's marginal-model sampling.

---

### `holland1975` — Holland (1975)
*Adaptation in Natural and Artificial Systems* · University of Michigan Press

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:99` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms

  > Genetic Algorithms (GAs) [holland1975,goldberg1989] are a population-based metaheuristic inspired by Darwinian natural selection: a population of encoded candidate solutions undergoes repeated cycles of selection and variation, higher-fitness individuals are more likely to reproduce, and favourable traits propagate over generations.

---

### `holland1992` — Holland (1992)
*Adaptation in Natural and Artificial Systems: An Introductory Analysis with Applications to Biology, Control, and Artificial Intelligence* · MIT Press

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:140` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Working Principle

  > Crossover is the primary mechanism by which a GA exploits existing structure, mixing high-quality components already present in the population, while mutation re-injects diversity and prevents the population from collapsing onto near-identical copies [holland1992].

---

### `holm1979` — Holm (1979)
*A Simple Sequentially Rejective Multiple Test Procedure* · Scandinavian Journal of Statistics

- [ ] **1.** `Experimental Setup.tex:424` — Experimental Setup › Evaluation Metrics and Statistical Tests

  > Because several pairs are tested per experiment ($3$ per cloud mode, $6$ per EV mode), the raw $p$-values are additionally adjusted by the Holm step-down procedure [holm1979] within each mode's family of pairwise tests, which controls the family-wise error rate without the full conservativeness of a Bonferroni correction.

---

### `hunter2007matplotlib` — Hunter (2007)
*Matplotlib: A 2D Graphics Environment* · Computing in Science \& Engineering

- [ ] **1.** `Implementation.tex:7` — Implementation › Tools and Environment

  > All figures are rendered to disk with matplotlib [hunter2007matplotlib].

---

### `iea2021netzero` — International Energy Agency (2021)
*Net Zero by 2050: A Roadmap for the Global Energy Sector* · International Energy Agency

- [ ] **1.** `Introduction.tex:6` — Introduction › Background and Motivation

  > The reasons for this shift are both economic and environmental. Electricity prices have risen sharply, international agreements like the Paris Agreement [unfccc2015paris] have led to strict emissions targets, and companies face increasing pressure to meet corporate sustainability pledges [iea2021netzero].

---

### `iea2025energyai` — International Energy Agency (2025)
*Energy and AI* · International Energy Agency

- [ ] **1.** `Introduction.tex:8` — Introduction › Background and Motivation

  > This is a major concern due to the size of modern data centres [masanet2020recalibrating] and the growing demands of AI workloads [iea2025energyai,devries2023growing].

---

### `kirkpatrick1983` — Kirkpatrick et al. (1983)
*Optimization by simulated annealing* · Science

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:213` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing

  > Simulated Annealing (SA) [kirkpatrick1983,cerny1985] is a single-solution search method that improves one candidate step by step.

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:228` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Working Principle

  > At each step, SA takes the current solution $s$ and generates a slightly modified ``neighbour'' $s'$, then computes the difference in objective value [kirkpatrick1983]:

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:249` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > The temperature schedule controls how fast SA transitions from broad exploration to focused local search, and SA's performance is highly sensitive to it [kirkpatrick1983,talbi2009,vanlaarhoven1987].

- [ ] **4.** `Metaheuristic Optimisation Methods.tex:257` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > The starting temperature $T_{}$ is commonly calibrated so that typical worsening moves are initially accepted around $80\,\%$ of the time [kirkpatrick1983,vanlaarhoven1987].

---

### `lawler1985` — Lawler et al. (1985)
*The Traveling Salesman Problem: A Guided Tour of Combinatorial Optimization* · John Wiley \& Sons

- [ ] **1.** `Related work.tex:3` — Related Work

  > Although framed in specific application settings, both problems are instances of well-studied combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment problem with bin-packing structure [coffman1997,garey1979], while electric vehicle routing extends the Vehicle Routing Problem (VRP) [dantzig1959,toth2014vrp], itself a generalisation of the Travelling Salesman Problem [lawler1985].

---

### `lenstra1981complexity` — Lenstra and Rinnooy Kan (1981)
*Complexity of vehicle routing and scheduling problems* · Networks

- [ ] **1.** `Introduction.tex:8` — Introduction › Background and Motivation

  > They require complex decisions under tight resource limits, and both are NP-hard [garey1979,lenstra1981complexity], so no exact algorithm is known whose running time scales polynomially with instance size.

---

### `lin1973` — Lin and Kernighan (1973)
*An Effective Heuristic Algorithm for the Traveling-Salesman Problem* · Operations Research

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:285` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Defining the Neighbourhood

  > The first concerns customer ordering: 2-opt segment reversal (a special case of the k-opt framework of [lin1973]), swapping two customers, and relocating a customer (removing it from position $i$ and reinserting it at position $j$, shifting the customers in between by one place), all standard moves for permutation-based representations [talbi2009].

---

### `masanet2020recalibrating` — Masanet et al. (2020)
*Recalibrating global data center energy-use estimates* · Science

- [ ] **1.** `Introduction.tex:8` — Introduction › Background and Motivation

  > This is a major concern due to the size of modern data centres [masanet2020recalibrating] and the growing demands of AI workloads [iea2025energyai,devries2023growing].

---

### `mckinney2010pandas` — McKinney (2010)
*Data Structures for Statistical Computing in Python* · Proceedings of the 9th Python in Science Conference (SciPy 2010)

- [ ] **1.** `Implementation.tex:7` — Implementation › Tools and Environment

  > The pandas library [mckinney2010pandas] ingests the CSV datasets and samples tasks for the synthetic scalability instances.

---

### `metropolis1953` — Metropolis et al. (1953)
*Equation of state calculations by fast computing machines* · Journal of Chemical Physics

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:234` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Working Principle

  > Worsening moves are accepted with the probability originally proposed by Metropolis et al. [metropolis1953], giving the full acceptance rule:

---

### `michalewicz1996` — Michalewicz (1996)
*Genetic Algorithms + Data Structures = Evolution Programs* · Springer

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:170` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Handling Constraints

  > Of the standard strategies (penalty functions, repair, and feasibility-preserving operators, among others [michalewicz1996,talbi2009]), the penalty approach is applied, consistent with the objective formulation used by SA and UMDA on the same problem: infeasible individuals are retained but their selection fitness is worsened in proportion to the CPU and memory violations, weighted by the coefficients $_{cpu}$ and $_{mem}$ introduced in Section (sec:cloud-penalties).

---

### `nie2022aco-evrpcc` — Nie et al. (2022) ✅ *already verified in `CITATION_VERIFICATION.md`*
*Ant Colony Optimization for Electric Vehicle Routing Problem with Capacity and Charging Time Constraints* · 2022 IEEE International Conference on Systems, Man, and Cybernetics (SMC)

- [ ] **1.** `Related work.tex:65` — Related Work › Cross-Paradigm Benchmarking and Research Gap

  > Within-paradigm benchmarks are relatively common, for example the five-variant ACO comparison of Nie et al. [nie2022aco-evrpcc] on the EVRP, or the Derrac-style comparison protocols [derrac2011practical] increasingly adopted in the metaheuristics literature.

---

### `perez2019eda` — Perez-Rodriguez and Hernandez-Aguirre (2019)
*A Hybrid Estimation of Distribution Algorithm for the Vehicle Routing Problem with Time Windows* · Computers \& Industrial Engineering

- [ ] **1.** `Related work.tex:69` — Related Work › Cross-Paradigm Benchmarking and Research Gap

  > EDAs have been used on routing problems, but only after being rebuilt around orderings: Pérez-Rodríguez and Hernández-Aguirre [perez2019eda], for example, replace the simple per-variable model used in this thesis with a Mallows model defined directly over sequences.

---

### `rudolph1994` — Rudolph (1994)
*Convergence Analysis of Canonical Genetic Algorithms* · IEEE Transactions on Neural Networks

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:128` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Working Principle

  > The most basic GA omits it, but it is used throughout this thesis because it guarantees that the best solution found never deteriorates [rudolph1994].

---

### `schneider2014` — Schneider et al. (2014)
*The Electric Vehicle-Routing Problem with Time Windows and Recharging Stations* · Transportation Science

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:293` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Defining the Neighbourhood

  > Because the battery level evolves along the route, dedicated operators insert, remove, or relocate charging stations [schneider2014], and a repair operator inserts a station at the cheapest position within an interval where battery constraints would otherwise be violated [felipe2014].

---

### `syswerda1989` — Syswerda (1989)
*Uniform Crossover in Genetic Algorithms* · Proceedings of the Third International Conference on Genetic Algorithms (ICGA)

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:124` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Working Principle

  > Variation produces offspring by applying crossover with probability $p_c$ and mutation independently at each position with probability $p_m$ [syswerda1989,goldberg1989].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:150` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Encoding and Parameters

  > Standard one-point, two-point, and uniform crossover [syswerda1989] apply directly, because every combination of server indices is a well-formed assignment.

---

### `talbi2009` — Talbi (2009) ✅ *already verified in `CITATION_VERIFICATION.md`*
*Metaheuristics: From Design to Implementation* · John Wiley \& Sons

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:6` — Metaheuristics › Metaheuristics for Combinatorial Optimisation

  > To solve them, the thesis uses metaheuristics: general-purpose search methods that combine randomness with problem-specific logic to find good, if not perfect, solutions within a reasonable runtime [talbi2009,eiben2015].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:112` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms

  > Because a GA requires only the ability to evaluate the objective function, it applies as a black-box optimiser to both problems in this thesis: on the Cloud Resource Allocation problem, recombination can exploit partial structure across many candidate task-to-server assignments in parallel [talbi2009].

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:170` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Genetic Algorithms › Handling Constraints

  > Of the standard strategies (penalty functions, repair, and feasibility-preserving operators, among others [michalewicz1996,talbi2009]), the penalty approach is applied, consistent with the objective formulation used by SA and UMDA on the same problem: infeasible individuals are retained but their selection fitness is worsened in proportion to the CPU and memory violations, weighted by the coefficients $_{cpu}$ and $_{mem}$ introduced in Section (sec:cloud-penalties).

- [ ] **4.** `Metaheuristic Optimisation Methods.tex:221` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing

  > The analogy to optimisation is that occasional uphill moves early in the search prevent the algorithm from getting permanently stuck in a poor solution, while a gradually decreasing temperature parameter makes the search increasingly selective [talbi2009].

- [ ] **5.** `Metaheuristic Optimisation Methods.tex:243` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Working Principle

  > In practice SA is structured with an inner loop: a fixed number of moves $L$ (the epoch length) is attempted at each temperature level before cooling, so that the neighbourhood is adequately sampled before the search commits to a colder regime [vanlaarhoven1987,talbi2009].

- [ ] **6.** `Metaheuristic Optimisation Methods.tex:249` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > The temperature schedule controls how fast SA transitions from broad exploration to focused local search, and SA's performance is highly sensitive to it [kirkpatrick1983,talbi2009,vanlaarhoven1987].

- [ ] **7.** `Metaheuristic Optimisation Methods.tex:267` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > A common extension, used in this thesis, is reheating, a non-monotonic schedule in which the temperature is raised again [talbi2009].

- [ ] **8.** `Metaheuristic Optimisation Methods.tex:289` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Defining the Neighbourhood

  > The first concerns customer ordering: 2-opt segment reversal (a special case of the k-opt framework of [lin1973]), swapping two customers, and relocating a customer (removing it from position $i$ and reinserting it at position $j$, shifting the customers in between by one place), all standard moves for permutation-based representations [talbi2009].

- [ ] **9.** `Metaheuristic Optimisation Methods.tex:301` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Handling Constraints

  > SA accommodates constraints through the same penalty formulation as the other methods [talbi2009]: capacity violations are penalised via the coefficients $_{cpu}$ and $_{mem}$ of Section (sec:cloud-penalties) on the cloud problem, and battery or visit violations via $_{bat}$ and $_{vis}$ on the routing problem.

---

### `thymianis2022` — Thymianis et al. (2022)
*Electric Vehicle Routing Problem: Literature Review, Instances and Results with a Novel Ant Colony Optimization Method* · 2022 IEEE Congress on Evolutionary Computation (CEC)

- [ ] **1.** `Related work.tex:65` — Related Work › Cross-Paradigm Benchmarking and Research Gap

  > Cross-paradigm comparisons within a single problem also exist, such as the ACO-versus-VNS comparison of Thymianis et al. [thymianis2022] on the EVRP or the GA-versus-heuristic study of Wilcox et al. [wilcox2011reliable] on VMP.

---

### `toth2014vrp` — Toth and Vigo (2014)
*Vehicle Routing: Problems, Methods, and Applications* · Society for Industrial and Applied Mathematics

- [ ] **1.** `Related work.tex:3` — Related Work

  > Although framed in specific application settings, both problems are instances of well-studied combinatorial problems: cloud resource allocation is a multi-dimensional generalised assignment problem with bin-packing structure [coffman1997,garey1979], while electric vehicle routing extends the Vehicle Routing Problem (VRP) [dantzig1959,toth2014vrp], itself a generalisation of the Travelling Salesman Problem [lawler1985].

---

### `unfccc2015paris` — United Nations Framework Convention on Climate Change (2015)
*Paris Agreement* · United Nations

- [ ] **1.** `Introduction.tex:6` — Introduction › Background and Motivation

  > The reasons for this shift are both economic and environmental. Electricity prices have risen sharply, international agreements like the Paris Agreement [unfccc2015paris] have led to strict emissions targets, and companies face increasing pressure to meet corporate sustainability pledges [iea2021netzero].

---

### `vanlaarhoven1987` — van Laarhoven and Aarts (1987) ✅ *already verified in `CITATION_VERIFICATION.md`*
*Simulated Annealing: Theory and Applications* · Kluwer Academic Publishers

- [ ] **1.** `Metaheuristic Optimisation Methods.tex:243` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › Working Principle

  > In practice SA is structured with an inner loop: a fixed number of moves $L$ (the epoch length) is attempted at each temperature level before cooling, so that the neighbourhood is adequately sampled before the search commits to a colder regime [vanlaarhoven1987,talbi2009].

- [ ] **2.** `Metaheuristic Optimisation Methods.tex:249` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > The temperature schedule controls how fast SA transitions from broad exploration to focused local search, and SA's performance is highly sensitive to it [kirkpatrick1983,talbi2009,vanlaarhoven1987].

- [ ] **3.** `Metaheuristic Optimisation Methods.tex:257` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > The starting temperature $T_{}$ is commonly calibrated so that typical worsening moves are initially accepted around $80\,\%$ of the time [kirkpatrick1983,vanlaarhoven1987].

- [ ] **4.** `Metaheuristic Optimisation Methods.tex:265` — Metaheuristics › Bio-inspired & Heuristic-Based Metaheuristics › Simulated Annealing › The Cooling Schedule

  > A logarithmically slow schedule guarantees the global optimum in theory [hajek1988] but is far too slow to be useful in practice, so performance within a fixed budget depends heavily on the tuned schedule [vanlaarhoven1987].

---

### `virtanen2020scipy` — Virtanen et al. (2020)
*SciPy 1.0: Fundamental Algorithms for Scientific Computing in Python* · Nature Methods

- [ ] **1.** `Implementation.tex:7` — Implementation › Tools and Environment

  > SciPy [virtanen2020scipy] provides only the two-sided Wilcoxon signed-rank test, with a manual fallback when unavailable.

---

### `whitley2016graybox` — Whitley et al. (2016)
*Gray Box Optimization for Mk Landscapes (NK Landscapes and MAX-kSAT)* · Evolutionary Computation

- [ ] **1.** `Introduction.tex:21` — Introduction › Problem Statement

  > Of these, SA, GA, and UMDA are black-box optimisers that use only objective-function evaluations, whereas ACO is a grey-box method that additionally exploits the distance structure of the routing graph [whitley2016graybox,droste2006upper].

---

### `wilcox2011reliable` — Wilcox et al. (2011)
*Solving Virtual Machine Packing with a Reordering Grouping Genetic Algorithm* · 2011 IEEE Congress of Evolutionary Computation (CEC)

- [ ] **1.** `Related work.tex:65` — Related Work › Cross-Paradigm Benchmarking and Research Gap

  > Cross-paradigm comparisons within a single problem also exist, such as the ACO-versus-VNS comparison of Thymianis et al. [thymianis2022] on the EVRP or the GA-versus-heuristic study of Wilcox et al. [wilcox2011reliable] on VMP.

---

### `wilcoxon1945` — Wilcoxon (1945)
*Individual Comparisons by Ranking Methods* · Biometrics Bulletin

- [ ] **1.** `Experimental Setup.tex:417` — Experimental Setup › Evaluation Metrics and Statistical Tests

  > Significance is tested with the pairwise Wilcoxon signed-rank test [wilcoxon1945] (two-sided, $= 0.05$).

---

### `wolpert1997` — Wolpert and Macready (1997)
*No Free Lunch Theorems for Optimization* · IEEE Transactions on Evolutionary Computation

- [ ] **1.** `Introduction.tex:10` — Introduction › Background and Motivation

  > Such an advantage can never be universal and the No Free Lunch theorems [wolpert1997] establish that no search strategy is best on every problem, so any gain must come from structure the problem actually possesses.

- [ ] **2.** `Related work.tex:67` — Related Work › Cross-Paradigm Benchmarking and Research Gap

  > This expectation is consistent with the No Free Lunch theorems [wolpert1997], which establish that no single optimiser dominates across all problems, so any performance advantage must come from exploiting problem-specific structure.

---
## Part 3 — EV passages that assert something citable and cite nothing

Not claims to verify, but the mirror image: places where the EV side states a
methodological choice as if it were standard practice without naming a source.
Each was confirmed by reading the passage, not inferred.

- [ ] **The entire EV experimental-setup section carries no citation.**
  `Experimental Setup.tex:183-406` covers instances, tuning, the main
  experiment, sensitivity, scalability, and the optimality-gap benchmark across
  223 lines with zero references. The cloud counterpart
  (`Experimental Setup.tex:79-182`) cites three sources over a third of the
  length. An examiner comparing the two halves will notice the asymmetry.

- [ ] **Random search for hyperparameter tuning is uncited.**
  `Experimental Setup.tex:231` — *"Tuning is by random search on `sf_75` [...]
  Random search is used instead of a full grid because the grids are large."*
  This is the standard argument from Bergstra and Bengio (2012), which is not in
  the bibliography. The cloud tuning subsection cites `eiben2015,hutter2009` for
  its own grid-size compromise, so the EV side is arguing the same kind of point
  unsupported.

- [ ] **The reduced-budget tuning assumption is uncited on the EV side.**
  `Experimental Setup.tex:232` tunes at 50,000 evaluations and runs the main
  experiment at 150,000. The cloud subsection states the same assumption and
  attaches `birattari2009` to it (`Experimental Setup.tex:98`). Reusing that key
  on the EV side would cost one citation and close the gap.

- [ ] **`Results`, `Comparative Discussion`, and `Conclusion` contain no
  citations at all** (both halves of the thesis). Defensible for chapters
  reporting own measurements, but the comparative discussion does interpret
  results against the representation-alignment hypothesis, which is a literature
  claim. Worth a deliberate decision rather than an accident.

---

