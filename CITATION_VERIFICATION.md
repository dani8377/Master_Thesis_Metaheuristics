# Citation verification log

Running record of thesis citations checked against the source PDF itself, not
against memory or abstracts. One section per bib key. Each entry records the
claim as it appears in the report, the passage in the source that supports it,
the verdict, and any edit made.

---

## `mavrovouniotis2020benchmark` (ref. 64)

**Source:** M. Mavrovouniotis, C. Menelaou, S. Timotheou, G. Ellinas, C. Panayiotou,
M. Polycarpou, "A Benchmark Test Suite for the Electric Capacitated Vehicle
Routing Problem", 2020 IEEE Congress on Evolutionary Computation (CEC).
DOI 10.1109/CEC48606.2020.9185753.

**Checked:** 2026-08-13, against the full paper PDF.

**Bib entry:** correct. Author list and order match the PDF byline exactly
(Mavrovouniotis, Menelaou, Timotheou, Ellinas, Panayiotou, Polycarpou). Title and
venue match. No change needed.

### Statement 1 of 3 — Related Work, Exact Methods (`chapters/Related work.tex:38`)

> The EVRP is usually formulated as a mixed-integer linear programme (MILP) and
> solved either with commercial solvers~\cite{mavrovouniotis2020benchmark} or with
> specialised exact techniques [...]

**Verdict: CONFIRMED. No edit.**

The paper does exactly this. Section II-B ("MILP Problem Formulation") gives the
E-CVRP model in Eqs. (2a)-(2m). Section III-A ("Using the MILP Formulation")
linearises the `u_i * x_ij` product with big-M inequalities, Eqs. (3a)-(3d),
specifically so a standard solver can take it: "it cannot be handled by standard
mathematical optimization solvers, such as the Gurobi solver". Section V-A then
states: "The MILP approach was solved using the Gurobi solver". Gurobi is a
commercial solver, so the citation supports the "commercial solvers" branch of the
sentence.

Minor note for the defence, not an error: the paper treats the E-CVRP, not the
general EVRP. The sentence is a general framing with this paper as one exemplar,
and the following sentences already name the variant explicitly, so the scope is
clear in context.

### Statement 2 of 3 — Related Work, Exact Methods (`chapters/Related work.tex:38`)

> Mavrovouniotis et al.~\cite{mavrovouniotis2020benchmark} support this scaling
> limit on the related Electric Capacitated Vehicle Routing Problem (E-CVRP),
> reporting that their MILP formulation could not find solutions for large-scale
> instances within a time limit of approximately three weeks.

**Verdict: CONFIRMED, with a one-word precision fix applied.**

Two passages carry the claim:

- Section V-A: "The MILP approach was solved using the Gurobi solver [14] and a
  time limit of approximately 3 weeks was imposed."
- Section V-B: "Note that the MILP approach was not able to provide a solution for
  the large-scale problem instances within the pre-determined time limit, and,
  thus, only the results of the MMAS approach are reported in Table VI."

Table VI corroborates this: it lists MMAS results only, with no MILP column, for
all 18 large-scale instances.

**Edit made:** "within a three-week time limit" became "within a time limit of
approximately three weeks". The paper hedges with "approximately 3 weeks"; the
report was stating it as an exact figure. The claim itself was already sound.

### Statement 3 of 3 — Related Work, Heuristics and Metaheuristics on EVRP (`chapters/Related work.tex:45`)

> The instances introduced by Schneider et al. for the E-VRPTW~\cite{schneider2014}
> and the benchmark suite proposed by Mavrovouniotis et al. for the
> E-CVRP~\cite{mavrovouniotis2020benchmark} are widely used testbeds for their
> respective EVRP variants. On EVRP benchmark sets more generally, later work has
> reported incremental improvements on the best-known solutions~\cite{froger2022exact}.

**Verdict: Mavrovouniotis attribution CONFIRMED. A neighbouring citation in the
same sentence was mis-attributed and has been fixed.**

The part attributed to this reference is exact. Proposing an E-CVRP benchmark suite
is the paper's stated contribution: it is the title, it is Section IV ("E-CVRP
Benchmark Test Suite"), the instances are tabulated in Tables I-IV, and footnote 6
gives the public download location
(`github.com/KIOS-Research/e-cvrp_benchmark_instances`).

Two things to be aware of at the defence:

1. "widely used" is the thesis's own survey-level characterisation, not a claim
   this paper makes. A 2020 paper cannot attest to the later uptake of its own
   suite. Left as written because it is ordinary related-work framing, but if an
   examiner presses on "widely used", the honest answer is that it is a
   characterisation of the literature rather than a sourced figure.
2. Do not conflate this suite with the separate IEEE WCCI-2020 EVRP competition
   benchmark set from the same group, cited in the paper as its ref. [8]. They are
   different instance sets; this paper only borrows the competition's `25000n`
   evaluation budget as its termination condition (Section V-A, footnote 9).

**Edit made, and the reason:** the sentence previously ended "...and subsequent work
has reported incremental improvements of a few percent on the best-known
solutions~\cite{froger2022exact}", which reads as though Froger et al. improved on
the Schneider or Mavrovouniotis best-known solutions. They did not. Froger, Jabali,
Mendoza and Laporte (Transportation Science 56(2), 2022) study the E-VRP with
nonlinear charging and capacitated stations, and their abstract reports "new
best-known solutions for 80 of 120 instances" on the 120-instance E-VRP-NL testbed
of Montoya et al., a third benchmark set entirely. The "few percent" magnitude was
also unsourced. The clause was therefore split off into its own sentence and
generalised to "On EVRP benchmark sets more generally", which is true of Froger et
al. and no longer claims anything about the two named suites.

**Follow-up left open:** `froger2022exact` is cited in three other places
(`Related work.tex` lines 38, 40, 42) for claims about nonlinear charging,
matheuristics and approximation error. Those were not checked here and are worth a
pass of their own. The Froger instance-set finding above rests on the publisher
abstract plus the Montoya testbed description, not on a full read of the paper's
experimental section.

---

## `nie2022aco-evrpcc` (ref. 71)

**Source:** Z.-H. Nie, Q. Yang, E. Zhang, D. Liu, J. Zhang, "Ant Colony Optimization
for Electric Vehicle Routing Problem with Capacity and Charging Time Constraints",
2022 IEEE International Conference on Systems, Man, and Cybernetics (SMC),
pp. 480-485. DOI 10.1109/SMC53654.2022.9945248.

**Checked:** 2026-08-14, against the full paper PDF.

**Bib entry: correct, no change needed.** Author list and order match the PDF byline
exactly (Nie Zi-Hao, Yang Qiang, Zhang En, Liu Dong, Zhang Jun). Title, venue and
year match. Page range 480-485 matches the printed page numbers. DOI matches the
one printed in the IEEE Xplore sidebar on p. 1. Note the fifth author is **Zhang**,
Jun (Hanyang University), not "Zhan" as the tracking sheet has it; the .bib is the
one that is right.

### Statement 1 of 2 — Related Work, ACO on EVRP (`chapters/Related work.tex:56`)

> A later study by Nie et al.~\cite{nie2022aco-evrpcc} compared five classical ACO
> variants, Ant System (AS), Rank-Based Ant System (Rank-AS), Elitist Ant System
> (EAS), MMAS, and Ant Colony System (ACS), on an EVRP variant with capacity and
> charging-time constraints, and found Rank-AS to be the strongest performer overall.

**Verdict: CONFIRMED on every checkable detail. One framing word edited.**

Each component checks out against the paper:

1. *Five classical ACO variants, and exactly those five.* Contribution 3 in
   Section I: "This paper embeds the devised solution construction method into five
   classical ACO algorithms, namely Ant System (AS) [16], Elite Ant System (EAS)
   [17], Rank-based Ant System (Rank-AS) [18], Max-Min Ant System (MMAS) [19] and
   Ant Colony System (ACS) [20]". Section III treats them one per subsection
   (III-A to III-E). The naming difference, the paper writes "Elite Ant System"
   where the thesis writes "Elitist Ant System", is not an error: "elitist ant
   system" is the standard name in the ACO literature and the acronym EAS is
   identical.
2. *An EVRP variant with capacity and charging-time constraints.* This is the
   paper's own contribution, EVRP-CC, defined in Section II. The capacity
   constraint is Eqs. (2)-(3), the electricity constraint Eqs. (4)-(6), and the new
   charging-time constraint is Eq. (7), sum_ij x_ij <= CT, which caps each EV at CT
   full charges.
3. *Rank-AS strongest overall.* Stated by the authors twice in their own words.
   Abstract: "Rank-AS with the proposed solution construction method achieves the
   best overall performance in solving EVRP-CC". Section V, closing paragraph:
   "Rank-AS obtains the best overall performance among the five ACO variants in
   solving the seven EVRP-CC instances". Conclusion repeats it.

Table 2 (p. 484) supports the claim on the numbers as well, over 30 independent
runs on seven instances (n22-n101, CT = 1):

| | best mean | best single run |
|---|---|---|
| Rank-AS | 3 instances (n33, n76, n101) | 4 instances (n22, n33, n76, n101) |
| AS | 2 instances (n22, n23) | 3 instances (n23, n30, n51) |
| EAS | 2 instances (n30, n51) | 0 |
| MMAS | 0 | 0 |
| ACS | 0 (worst throughout) | 0 |

**Edit made, and the reason:** "A follow-up study by Nie et al." became "A later
study by Nie et al." The preceding sentence is about Mavrovouniotis et al. (2018),
so "follow-up" asserted a lineage that does not exist. Nie et al. are a different
group (Henan Normal / NUIST / Hanyang, versus KIOS in Cyprus) and their reference
list does not contain the 2018 MMAS look-ahead paper at all; their ACO-on-EVRP
citations are Jia, Mei and Zhang's bilevel ACO [6] and Shi et al.'s memory-based
ACS [14]. The only genuine link is that their instances are "generated from the
widely used EVRP benchmark set", i.e. the WCCI-2020 competition set of
Mavrovouniotis et al. [21], which is the same group but a different artefact.
"Later" is true, costs one word, and leaves the sentence otherwise untouched.

Two points to have ready for the defence, neither of which is an error in the text:

1. The five variants are not compared as off-the-shelf algorithms. All five are run
   with the paper's own two-stage solution construction method bolted on (Section
   IV), so what actually differs between them is the pheromone-update rule, with
   the constraint-handling held constant. The thesis sentence does not claim
   otherwise, but "compared five classical ACO variants" is worth being able to
   qualify if asked.
2. "Strongest performer overall" rests on a plurality, not a majority, and on no
   statistical test. Rank-AS wins 3 of 7 mean comparisons; AS and EAS take 2 each,
   and the standard deviations in Table 2 (50-120) are large next to several of the
   gaps between means. The claim is the authors' own summary and is reported as
   such, but it is weaker evidence than a Wilcoxon-backed result would be. Useful
   contrast for our own protocol, which does run the tests.

### Statement 2 of 2 — Related Work, Cross-Paradigm Benchmarking (`chapters/Related work.tex:65`)

> Within-paradigm benchmarks are relatively common, for example the five-variant ACO
> comparison of Nie et al.~\cite{nie2022aco-evrpcc} on the EVRP [...]

**Verdict: CONFIRMED. No edit.**

The paper is used here only as an example of a benchmark that stays inside one
paradigm, and it is a clean one. All five algorithms compared are ACO variants, no
non-ACO method appears anywhere in the experiments, and Section V compares them
against each other rather than against any external baseline. That is precisely the
within-paradigm design the sentence contrasts with the thesis's cross-paradigm one.

"On the EVRP" is family-level shorthand: the experiments are on EVRP-CC, the
capacity-and-charging-time variant the same paper introduces. That is accurate at
the level of precision the sentence operates at, the exact variant is already
spelled out at line 56, and the surrounding sentence names EVRP for two other
studies as well.

---

## `tahami2020exact` (ref. 87)

**Source:** H. Tahami, G. Rabadi, M. Haouari, "Exact approaches for routing
capacitated electric vehicles", Transportation Research Part E: Logistics and
Transportation Review, vol. 144, art. 102126, 2020.
DOI 10.1016/j.tre.2020.102126.

**Checked:** 2026-08-14, against the full paper PDF.

**Bib entry:** correct. Author list and order match the byline (Tahami, Rabadi,
Haouari), the journal, volume 144, article number 102126 and year all match the
running head on every page. The published title is lower-case after the first word
("Exact approaches for routing capacitated electric vehicles"); the bib entry uses
title case, which the bibliography style normalises anyway. No change needed.

### Statement 1 of 2 - Related Work, Exact Methods (`chapters/Related work.tex:38`)

> The EVRP is usually formulated as a mixed-integer linear programme (MILP) and
> solved either with commercial solvers~\cite{mavrovouniotis2020benchmark} or with
> specialised exact techniques originally developed for the classical VRP and later
> adapted to the EVRP, including branch-and-cut~\cite{tahami2020exact} [...]

**Verdict: CONFIRMED. No edit.**

Every element of what the citation is asked to carry is in the paper.

1. *MILP.* Section 2.1 gives a nonlinear compact formulation, Sections 2.2 and 2.3
   linearise the capacity and energy constraints with the Reformulation-Linearization
   Technique of Sherali and Adams, and Section 2.4 states the result outright: "we
   formulated the ECVRP as a mixed-integer linear program having O(|C|^2|R|) binary
   variables".
2. *Branch-and-cut.* Section 3.1 is titled "Solving (F2) by branch-and-cut" and
   describes the algorithm; Section 6.2 reports it running under CPLEX 12.8 with the
   USERCUT callback generating rounded capacity inequalities at each node. The
   abstract calls it "a branch-and-cut algorithm" in the list of contributions.
3. *Originally developed for the classical VRP, later adapted.* This is the paper's
   own framing. The cuts it separates are the rounded capacity constraints, and
   Section 3 says they "were first introduced by Laporte and Nobert (1983) in the
   context of the Capacitated Vehicle Routing Problem, and that they play a central
   role in branch-and-cut algorithms for solving this latter problem". The whole
   paper is an adaptation of the CVRP to the electric case, which it names the
   ECVRP.

Point for the defence, not an error: the paper's exact object is the ECVRP, the
capacitated EVRP with no time windows, which the authors present as the electric
variant of the classical CVRP. The sentence says "the EVRP" at family level, which
is the same level of precision it uses for the other two citations in the list.

### Statement 2 of 2 - Related Work, Exact Methods (`chapters/Related work.tex:38`)

> Tahami et al.~\cite{tahami2020exact} report that their compact formulation reliably
> solves instances with up to 30 customers in moderate CPU time, and that their
> hybrid approach reaches 100 customers on some instances, but fails on the tightly
> constrained large-scale ones.

**Verdict: CONFIRMED after one edit.** Both scale numbers are right; one clause
about the failure mode was not.

*The 30-customer figure is exact.* Abstract: the polynomial-sized formulation "can
consistently solve instances having up to 30 customer nodes and 21 charging
stations". Section 6.1: "All instances having up to 30 nodes were optimally
solved". Table 1 gives 12/12 optimal at |C| = 10, 20 and 30, with average total
times of 0.40 s, 14.61 s and 72.28 s. "Moderate CPU time" is the paper's own words:
"(F1) made it feasible to solve medium-sized instances in a moderate CPU time".

*Customers, not nodes.* Worth noting that the thesis is the more precise of the two
here. The paper's body text says "30 nodes" in places, but its tables label the
column |C| and pair |C| = 30 with |R| = 21 charging stations plus a depot, so the
30 counts customers only. The thesis says "30 customers", which matches the
abstract and the tables.

*The 100-customer figure is exact.* Abstract: "the hybrid algorithm solves some
instances having up to 100 customer nodes and 21 charging stations". Table 3 shows
6/12 solved at |C| = 100, and Table D.9 lists those six by name (c202, c208, r202,
r209, rc202, rc204). "On some instances" is the correct hedge: the rate falls off
from 12/12 at 60 customers to 8/12, 8/12, 7/12 and 6/12 at 70, 80, 90 and 100.

**Edit made, and the reason:** "but struggles on larger or tightly constrained ones"
became "but fails on the tightly constrained large-scale ones". Two problems with
the old clause. First, "larger" claims something the paper never tested: its testbed
stops at 100 customers, so there is no evidence in it about anything above that
size. Second, "struggles" understates what happened. Section 6.3 reports that on
large instances derived from c103, r102 and rc103 the hybrid approach "failed to
solve these instances (or even provide feasible solutions) after spending 3 h CPU
time", and the abstract records the same limitation as a limitation, not a
slowdown.

The replacement is also the sharper claim, because the two failure modes are not
independent in this paper: the instances that go unsolved at 70 to 100 customers
are exactly the tightly constrained ones. At |C| = 70 the four missing from Table
D.6 are r102, r105, rc103 and rc108, all with Q = 200 and Emax of 62.14 or 79.69,
while all eight solved instances have either Q = 700 or Q = 1000. Section 6.2 makes
the same association at the level of integrality gaps: the instances with gaps
above 2 per cent "correspond to very tightly constrained instances having both
reduced capacity (Q = 200) and very reduced battery range (Emax = 79.69 or 62.14)".
Tightness, not raw size, is what defeats the method, and the edited sentence now
says so.

---

## `adak2026` (ref. 1)

**Source:** S. Adak, C. Witt, "Mathematical runtime analysis of a multi-Valued
estimation of distribution algorithm", Artificial Intelligence 353 (2026) 104501.
DOI 10.1016/j.artint.2026.104501. Open access, CC BY.

**Checked:** 2026-08-14, against the full paper PDF.

**Bib entry: correct, no change needed.** Every field matches the PDF. Byline is
"Sumit Adak, Carsten Witt", both DTU Compute, Technical University of Denmark.
Title, journal, publisher (Elsevier) and year all match. The running footer reads
"Artificial Intelligence 353 (2026) 104501", so volume 353 and article number
104501 are confirmed, and the DOI line in the PDF header matches the bib DOI
character for character. This closes out the volume correction (327 to 353) made
in the 2026-07-15 metadata pass, which was right.

### Statement 1 of 1 - Metaheuristic Optimisation Methods, EDAs (`chapters/Metaheuristic Optimisation Methods.tex:495`)

> UMDA is chosen over PBIL~\cite{baluja1994} and the compact
> GA~\cite{harik1999cga}, including its multi-valued variant
> \cite{adak2026}, because it re-estimates its marginals from
> scratch each generation, mirroring the population structure of GA.

**Verdict: CONFIRMED. No edit.**

This is the only place in the thesis that cites `adak2026`, so one statement is
the whole exposure.

*The multi-valued variant exists and is analysed here.* This is the paper's entire
subject. The abstract: "recent developments have introduced multi-valued EDAs to
tackle problems with variables taking more than two values [...] we provide
theoretical analyses of the multi-valued compact genetic algorithm (r-cGA)".
Section 2.1 states the relationship the thesis clause asserts, that the multi-valued
algorithm is a variant of the compact GA and not a separate lineage: "An extended
version of the cGA is the r-valued compact genetic algorithm (r-cGA) [...] it
enhances the original cGA by supporting multi-valued variables rather than the
binary representation used in the classic version." Algorithm 1 is headed
"r-valued Compact Genetic Algorithm (r-cGA) for the maximization of
f : {0,...,r-1}^n -> R".

*Same model class as the thesis UMDA.* Section 2.1: "The probabilistic model of the
r-cGA is defined by a (n x r)-matrix (the frequency matrix), where each row
i in {1,...,n} forms a vector p_i := (p^(t)_{i,j})_{j in {0,...,r-1}}", each
frequency initialised to 1/r and each row summing to 1. That is one categorical
distribution per decision variable over r values, which is the model the thesis
builds over m servers for each of n tasks (lines 484 to 494). The comparison the
sentence sets up is therefore between two algorithms with the same model class and
different update rules, which is the honest form of the comparison.

*The stated reason for preferring UMDA is accurate.* The cGA is incremental where
the thesis UMDA re-estimates. Section 2.1: "During each iteration of the cGA, two
solutions are generated independently. Then, based on the fitness comparison
between the two solutions, each frequency is updated by 1/K, either increasing or
decreasing." Algorithm 1, line 9, gives the rule
p^(t+1)_{i,j} <- p^(t)_{i,j} + (1/K)(1{x_i = j} - 1{y_i = j}). The model persists
across iterations and is nudged by one step, never rebuilt, which is the exact
complement of the maximum-likelihood re-estimate over the mu selected individuals
in Equation (line 485).

*"Mirroring the population structure of GA" is also supported, and more sharply
than the sentence claims.* The cGA has no population at all. Section 2.1 calls K
"the hypothetical population size", a simulated quantity, and the algorithm samples
exactly two individuals per iteration. So the contrast is not that the cGA has a
differently managed population, it is that UMDA has one and the cGA does not. The
thesis phrasing is the weaker and therefore safe claim.

**Note for the defence, not an error: the paper is not the origin of the r-cGA.**
Section 2.1 attributes it elsewhere, "the r-valued compact genetic algorithm
(r-cGA), first introduced in [19]", where [19] is Ben Jedidia, Doerr and Krejca,
Theor. Comput. Sci. 1003 (2024) 114622. The paper's own introduction is looser,
listing "the multi-valued compact genetic algorithm (r-cGA) [20]" against its
authors' earlier PPSN 2024 paper and crediting [20] and Hamano et al. [21] with the
first runtime analysis of it. The thesis clause claims neither invention nor
priority, only that the variant exists and is studied, so `adak2026` supports it as
written and no edit follows. Flagging it because the sentence would need a different
citation if it were ever rewritten as "introduced by", in which case the correct
key would be Ben Jedidia et al. (2024), which is not currently in the bibliography.

**Incidental check of the two neighbouring keys in the same sentence.** This paper's
reference list gives independent records for both, and both match the thesis bib.
Ref. [29] is "G.R. Harik, F.G. Lobo, D.E. Goldberg, The compact genetic algorithm,
IEEE Trans. Evol. Comput. 3 (4) (1999) 287-297", matching `harik1999cga` on authors,
title, venue, volume, number, pages and year. Ref. [28] is "S. Baluja,
Population-based incremental learning: A method for integrating genetic search based
function optimization and competitive learning, School of Computer Science, Carnegie
Mellon University Pittsburgh, PA, 1994", matching `baluja1994` on author, title,
institution, address and year. The report number CMU-CS-94-163 in the thesis entry
is not carried by this paper's reference list and was not re-checked here, having
been confirmed in the 2026-07-15 metadata pass.

---

## `talbi2009` (ref. 88)

**Source:** E.-G. Talbi, *Metaheuristics: From Design to Implementation*, John Wiley
& Sons, Hoboken, NJ, 2009. DOI 10.1002/9780470496916.

**Checked:** 2026-08-14, against the full book PDF (Wiley Online Library copy).

**Bib entry:** correct. Title page reads "METAHEURISTICS: FROM DESIGN TO
IMPLEMENTATION / El-Ghazali Talbi, University of Lille - CNRS - INRIA"; copyright
page reads "Copyright 2009 by John Wiley & Sons, Inc." and "Published by John Wiley
& Sons, Inc., Hoboken, New Jersey". Author, title, publisher, address and year all
match. No change needed.

**Summary of the pass:** ten statements checked. Six confirmed as written. Four
edited: one factual miscount (Statement 3), one superlative the book does not make
(Statement 7), one where the citation covered thesis-specific mechanism the book does
not describe (Statement 8), and one where the book says close to the opposite of the
claim as scoped (Statement 9). All four edits are wording-only; no algorithm, result
or number is affected.

### Statement 1 of 10 - Metaheuristics for Combinatorial Optimisation (`chapters/Metaheuristic Optimisation Methods.tex:6`)

> the thesis uses \emph{metaheuristics}: general-purpose search methods that combine
> randomness with problem-specific logic to find good, if not perfect, solutions
> within a reasonable runtime~\cite{talbi2009,eiben2015}

**Verdict: CONFIRMED. No edit.**

Every element of the definition is in the book, and mostly on its opening page.
Chapter 1, p. 1: "Metaheuristics represent a family of approximate optimization
techniques [...] Metaheuristics provide 'acceptable' solutions in a reasonable time
for solving hard and complex problems in science and engineering. Unlike exact
optimization algorithms, metaheuristics do not guarantee the optimality of the
obtained solutions." That covers "good, if not perfect" and "within a reasonable
runtime" almost word for word.

*General-purpose plus problem-specific logic.* Section 1.3.2, p. 21: "Metaheuristics
are general-purpose algorithms that can be applied to solve almost any optimization
problem. They may be viewed as upper level general methodologies that can be used as
a guiding strategy in designing underlying heuristics to solve specific optimization
problems." The two halves of the thesis phrase, general-purpose and problem-specific,
are the two halves of that sentence.

*Randomness.* Section 1.4.1, p. 25: "Deterministic versus stochastic [...] In
stochastic metaheuristics, some random rules are applied during the search", with the
consequence that "different final solutions may be obtained" from the same starting
point. The thesis relies on exactly that property when it runs multiple seeds per
configuration.

### Statement 2 of 10 - Genetic Algorithms (`chapters/Metaheuristic Optimisation Methods.tex:112`)

> Because a GA requires only the ability to evaluate the objective function, it
> applies as a \emph{black-box} optimiser to both problems in this thesis: on the
> Cloud Resource Allocation problem, recombination can exploit partial structure
> across many candidate task-to-server assignments in parallel~\cite{talbi2009}

**Verdict: CONFIRMED. No edit.**

*Black box.* Section 1.4.1, pp. 31-32, gives the formal definition the sentence uses:
"A function f : X -> R is called a black box function iff the domain X is known, it
is possible to know f for each point of X according to a simulation, and no other
information is available for the function f." Figure 1.14 is captioned "Black box
scenario for the objective function" and draws precisely the thesis arrangement, a
box labelled "Metaheuristic" feeding x into a black box that returns f(x). The same
page states why this matters: "Unlike mathematical programming, the main advantage of
using metaheuristics is a restrictive assumption in formulating the model", that is,
only the ability to evaluate is required.

*Recombination exploiting partial structure.* Section 3.3.2.2 ("Recombination or
Crossover"), pp. 213-214: "The role of crossover operators is to inherit some
characteristics of the two parents to generate the offsprings", and, under
Heritability, "A crossover operator Ox is respectful if the common decisions in both
parents are preserved". "Common decisions preserved" is what the thesis calls partial
structure; on the cloud encoding a decision is one task-to-server assignment, so the
mapping is direct.

*"In parallel".* Section 1.4.1, p. 25: "in population-based algorithms (e.g.,
particle swarm, evolutionary algorithms) a whole population of solutions is evolved
[...] Population-based metaheuristics are exploration oriented; they allow a better
diversification in the whole search space." The thesis's "in parallel" is a paraphrase
of a whole population being evolved at once, not a claim about parallel hardware, and
the surrounding text does not read it that way.

### Statement 3 of 10 - Genetic Algorithms, Handling Constraints (`chapters/Metaheuristic Optimisation Methods.tex:168`)

> Of the ~~three~~ standard strategies (penalty functions, repair, and
> feasibility-preserving operators~\cite{michalewicz1996,talbi2009}), the
> \emph{penalty} approach is applied [...]

**Verdict: NOT SUPPORTED AS WRITTEN. Edited.**

The list of three is right, the word "three" is not. Section 1.5, p. 48, enumerates
**five**: "In this section, constraint handling strategies, which mainly act on the
representation of solutions or the objective function, are presented. They can be
classified as reject strategies, penalizing strategies, repairing strategies,
decoding strategies, and preserving strategies." Section 1.5 then gives each its own
subsection (1.5.1 Reject through 1.5.5 Preserving), and the Chapter 1 summary, p. 77,
repeats the five: "Most of the constraint handling strategies act on the
representation of solutions or the objective function (e.g., reject, penalizing,
repairing, decoding, and preserving strategies)."

The second cited source does not rescue the count either: Michalewicz's taxonomy
likewise runs to more than three categories (preserving feasibility, penalty
functions, distinguishing feasible from infeasible solutions, decoders, hybrids). So
no cited source supports "the three standard strategies", and an examiner opening
either book at the constraint-handling chapter would see a list of five.

**Edit made:** deleted "three" and added ", among others", so the sentence now reads
"Of the standard strategies (penalty functions, repair, and feasibility-preserving
operators, among others [...])". The three named are still the three the paragraph
goes on to weigh, and the sentence no longer misreports the taxonomy. Nothing else in
the paragraph changes.

### Statement 4 of 10 - Memetic Algorithms (`chapters/Metaheuristic Optimisation Methods.tex:197`)

> the order-based crossover that the GA relies on frequently breaks up good sub-tours,
> and interleaving a local-search step repairs this disruption, a pairing long
> established for routing problems~\cite{talbi2009}

**Verdict: CONFIRMED. No edit.**

The citation sits on the final clause, "a pairing long established", which is what the
book supports. Section 5.1.1, under LTH (low-level teamwork hybrid), pp. 388-389:
"most efficient P-metaheuristics have been coupled with S-metaheuristics such as local
search, simulated annealing, and tabu search, which are powerful optimization methods
in terms of exploitation. The two classes of algorithms have complementary strengths
and weaknesses [...] This class of hybrid algorithms is very popular and has been
applied successfully to many optimization problems. Most of the state-of-the-art
P-metaheuristics integrate into S-metaheuristics." Footnote 1 on the same page ties it
to the thesis's term: "This class of hybrid metaheuristics includes memetic
algorithms." Example 5.2, p. 389, then describes the thesis's exact scheme: "When an
evolutionary algorithm is used as a global optimizer, its standard operators may be
augmented with the ability to perform local search [...] a heuristic operator that
considers an individual as the origin of its search applies itself, and finally
replaces the original individual by the enhanced one", which the book labels
Lamarckian, and which is what the thesis does when each offspring is refined before
entering the population.

*On "for routing problems".* The book's routing instances of the hybrid idea are
present but illustrative rather than central: p. 388 works the TSP case of embedding
2-opt local search, and p. 390 reports that heuristic crossover was "shown to improve
EAs results when applied to job-shop scheduling, set covering, and traveling salesman
problems". So "long established" is well supported and "for routing problems" is
supported by example. No overclaim, so the sentence stands.

*Scope note, not an error.* The first clause, that order-based crossover breaks up
good sub-tours, is the thesis's own reasoning and is not attributed to Talbi. That is
the correct placement: the book gives the general machinery for judging such a
mismatch (heritability and the "respectful" property, p. 214; locality, p. 92) but
does not make this claim about order-based crossover on the EVRP. The MA's origin is
separately and correctly credited to `moscato1989` two sentences earlier.

### Statement 5 of 10 - Simulated Annealing (`chapters/Metaheuristic Optimisation Methods.tex:216`)

> The analogy to optimisation is that occasional uphill moves early in the search
> prevent the algorithm from getting permanently stuck in a poor solution, while a
> gradually decreasing temperature parameter makes the search increasingly
> selective~\cite{talbi2009}

**Verdict: CONFIRMED. No edit.**

Section 2.4, pp. 126-127, states both halves. Uphill moves and their purpose: "SA is a
stochastic algorithm that enables under some conditions the degradation of a solution.
The objective is to escape from local optima and so to delay the convergence."
Increasing selectivity: "It uses a control parameter, called temperature, to determine
the probability of accepting nonimproving solutions [...] As the algorithm progresses,
the probability that such moves are accepted decreases", reinforced by Section 2.4.1,
p. 130: "At high temperatures, the probability of accepting worse moves is high. If T
= infinity, all moves are accepted, which corresponds to a random local walk in the
landscape [...] If T = 0, no worse moves are accepted and the search is equivalent to
local search (i.e., hill climbing)." Figure 2.25 is captioned "Simulated annealing
escaping from local optima. The higher the temperature, the more significant the
probability of accepting a worst move."

The physical analogy the sentence opens with is Table 2.4, p. 127, "Analogy Between
the Physical System and the Optimization Problem", which maps energy to objective
function, ground state to global optimum, and metastable state to local optimum.

### Statement 6 of 10 - Simulated Annealing, Working Principle (`chapters/Metaheuristic Optimisation Methods.tex:238`)

> In practice SA is structured with an inner loop: a fixed number of moves $L$ (the
> epoch length) is attempted at each temperature level before cooling, so that the
> neighbourhood is adequately sampled before the search commits to a colder
> regime~\cite{vanlaarhoven1987,talbi2009}

**Verdict: CONFIRMED. No edit.**

Algorithm 2.3, p. 128, is the template, and its inner loop is annotated exactly as the
thesis describes it: "Repeat / At a fixed temperature / [...] Until Equilibrium
condition / e.g. a given number of iterations executed at each temperature T /".
Section 2.4.2.2 ("Equilibrium State"), p. 131, supplies the rationale about adequate
sampling: "To reach an equilibrium state at each temperature, a number of sufficient
transitions (moves) must be applied [...] The number of iterations must be set
according to the size of the problem instance and particularly proportional to the
neighborhood size |N(s)|", and under the static strategy, "a given proportion y of the
neighborhood N(s) is explored [...] The more significant the ratio y, the higher the
computational cost and the better the results."

Incidental confirmation of notation: the book also writes L for this quantity on
p. 131 ("The next number of transitions L is defined as follows"), so the thesis's L
is the book's L rather than a clashing symbol.

### Statement 7 of 10 - Simulated Annealing, The Cooling Schedule (`chapters/Metaheuristic Optimisation Methods.tex:245`)

> The temperature schedule controls how fast SA transitions from broad exploration to
> focused local search, and ~~it is the most important design decision when applying
> the algorithm~~ **SA's performance is highly sensitive to
> it**~\cite{kirkpatrick1983,talbi2009,vanlaarhoven1987}

**Verdict: OVERSTATED. Edited.**

The substance is supported, the superlative is not. Section 2.4.2, p. 130: "The
cooling schedule defines for each step of the algorithm i the temperature Ti. It has a
great impact on the success of the SA optimization algorithm. Indeed, the performance
of SA is very sensitive to the choice of the cooling schedule." The book says great
impact and very sensitive; it does not rank the schedule above SA's other design
decisions, and in fact Section 2.4 introduces the acceptance probability function and
the cooling schedule side by side as the two things needing practical guidance:
"The following sections present a practical guideline in the definition of the
acceptance probability function and the cooling schedule in SA." Ranking the schedule
first is the thesis's own judgement dressed as the source's.

The first half of the sentence is fine independently: Section 2.4.2.1, p. 130, "If the
starting temperature is very high, the search will be more or less a random local
search. Otherwise, if the initial temperature is very low, the search will be more or
less a first improving local search algorithm", which is the exploration-to-local-
search transition the thesis describes.

**Edit made:** replaced "it is the most important design decision when applying the
algorithm" with "SA's performance is highly sensitive to it", which is what the cited
sources actually support. This also removes a superlative of the kind flagged in the
earlier voice pass. The claim still does the work the section needs, since the whole
point of the following paragraphs is that the schedule must be tuned.

### Statement 8 of 10 - Simulated Annealing, The Cooling Schedule (`chapters/Metaheuristic Optimisation Methods.tex:264`)

> A common extension, used in this thesis, is \emph{reheating}: **a nonmonotonic
> schedule in which the temperature is raised again to renew
> diversification**~\cite{talbi2009}. **Here it is triggered by stagnation, raising**
> the temperature back to a fraction of its initial value to escape deep local optima,
> while the best solution found so far is retained separately.

**Verdict: PARTIALLY SUPPORTED. Edited.**

The book supports the idea, not the implementation. Section 2.4.2.3, pp. 132-133,
lists it among the cooling functions: "Nonmonotonic: Typical cooling schedules use
monotone temperatures. Some nonmonotone scheduling schemes where the temperature is
increased again may be suggested. This will encourage the diversification in the
search space. For some types of search landscapes, the optimal schedule is
nonmonotone." That is raising the temperature again, and its purpose, and nothing
more.

What the book does **not** say, but the old sentence attributed to it: the name
"reheating", the stagnation trigger ("if the search stagnates for a number of steps"),
and the amount ("a fraction of its initial value"). Those are the thesis's own design
choices. The one remaining clause is supported elsewhere, Section 2.4, p. 128: "In
addition to the current solution, the best solution found since the beginning of the
search is stored." Talbi does treat stagnation as a recognised signal, but as a
stopping criterion rather than a reheat trigger, Section 2.4.2.4, p. 133: "Achieving a
predetermined number of iterations without improvement of the best found solution."

**Edit made:** split into two sentences so the citation lands on the concept the book
gives (a nonmonotonic schedule that raises the temperature again to renew
diversification) and the specific trigger and amount are presented as this thesis's
instantiation. No parameter values or behaviour change, and the implementation
chapter's description of the reheat rule is unaffected.

### Statement 9 of 10 - Simulated Annealing, Defining the Neighbourhood (`chapters/Metaheuristic Optimisation Methods.tex:281`)

> 2-opt segment reversal (a special case of the k-opt framework of~\cite{lin1973}),
> swapping two customers, and relocating a customer [...] all standard moves for
> permutation-based ~~routing~~ **representations**~\cite{talbi2009}

**Verdict: CONTRADICTED AS SCOPED. Edited. This is the one to know about.**

Scoped to routing, the book says close to the opposite for two of the three moves.
Example 2.2, p. 93, introduces the insertion operator (the thesis's relocate: "an
element at one position is removed and put at another position") and the exchange
operator (the thesis's swap: "arbitrarily selected two elements are swapped"), and
then closes: "**Those operators are largely used in scheduling problems and seldom for
routing problems such as the TSP for efficiency reasons.**" The same example opens by
ruling out the other family for scheduling: "For permutations representing sequencing
and scheduling problems, the k-opt family of operators is not well suited."

Only 2-opt survives the original wording. Page 92: "in scheduling problems,
permutations represent a priority queue. Then, the relative order in the sequence is
very important, whereas in the TSP it is the adjacency of the elements that is
important. For scheduling problems, the 2-opt operator will generate a very large
variation (weak locality), whereas for routing problems such as the TSP, it is a very
efficient operator because the variation is much smaller (strong locality)."

Scoped to permutations generally, all three are supported, twice over. Section 2.1.1,
p. 87: "For permutation-based representations, a usual neighborhood is based on the
swap operator." Section 3.3.2.1, p. 209: "Mutation in permutations: Mutation in
order-based representations are generally based on the swapping, inversion, or the
insertion operators." Figures 2.7 and 2.8 draw the insertion and exchange operators on
a permutation.

**Edit made:** one word, "routing" to "representations". The sentence now claims what
the book states and no longer claims what it denies. The move set itself is unchanged,
and the justification for using it here is already in the paragraph's closing sentence
("These operators change either the visiting order or the placement of charging
stations, which are the two decisions the EV routing problem contains").

**For the defence, if pressed on why we use moves Talbi calls inefficient for
routing.** His remark is about the *pure* TSP, where the objective depends only on
adjacency, so relocate and swap disturb many edges for little gain while 2-opt
disturbs two. The EVRP here is not that problem: capacity, battery state and station
placement all depend on a customer's *position along* the route, not only on its
neighbours, so relocating one customer changes the feasibility profile of the whole
remainder of the tour in a way 2-opt cannot reproduce. That is why the VRP literature
treats relocate and exchange as standard alongside 2-opt. The answer is a one-sentence
point about problem structure, not a retreat.

*Incidental check of the neighbouring key.* The k-opt attribution to `lin1973` is
corroborated here: p. 87, "Another widely used operator is the k-opt operator, where k
edges are removed", footnote 3 "Also called k-exchange operator", and "The
neighborhood for the 2-opt operator is represented by all the permutations obtained by
removing two edges", which is the "special case" relation the thesis asserts.

### Statement 10 of 10 - Simulated Annealing, Handling Constraints (`chapters/Metaheuristic Optimisation Methods.tex:298`)

> SA accommodates constraints through the same penalty formulation as the other
> methods~\cite{talbi2009}: capacity violations are penalised via the coefficients
> $\lambda_{\text{cpu}}$ and $\lambda_{\text{mem}}$ [...] and battery or visit
> violations via $\lambda_{\text{bat}}$ and $\lambda_{\text{vis}}$

**Verdict: CONFIRMED. No edit.**

Section 1.5.2 ("Penalizing Strategies"), p. 50, states the approach and its standing:
"The unconstrained objective function is extended by a penalty function that will
penalize infeasible solutions. **This is the most popular approach.**" The linear form
given there, f'(s) = f(s) + lambda * c(s) where "c(s) represents the cost of the
constraint violation and lambda the aggregation weights", is the thesis's formulation
with lambda renamed per constraint type.

The thesis penalises by violation magnitude rather than by counting violations, which
is the variant the book prefers. Same section, p. 50: a count of violated constraints
uses "no information [...] on how close the solution is to the feasible region", and
"For a problem with few and tight constraints, this strategy is useless"; whereas
under "Amount of infeasibility or repairing cost", "more efficient approaches consist
in including a distance to feasibility for each constraint", giving fp(x) = f(x) +
sum_i wi * di^k. The thesis's lambda-weighted CPU, memory, battery and visit
violations are exactly that di form.

Two further points in the same section back the surrounding sentences. That the same
formulation serves every method is why it appears in Chapter 1, "Common Concepts for
Metaheuristics", rather than in the SA chapter. And the paragraph's caution about
calibrating the coefficients is the book's, p. 50: "a good compromise for the
initialization of the coefficient factors wi must be found. Indeed, if wi is too
small, final solutions may be infeasible. If the coefficient factor wi is too high, we
may converge toward nonoptimal feasible solutions."

---

## `vanlaarhoven1987` (ref. 92)

**Source:** P. J. M. van Laarhoven and E. H. L. Aarts, *Simulated Annealing: Theory and
Applications*, D. Reidel, Dordrecht, 1987. DOI 10.1007/978-94-015-7744-1.

**Checked:** 2026-08-14, against the full book PDF. An earlier draft of this entry was
written against a journal book *review* of the book, which was supplied first by
mistake and could confirm nothing; it is superseded by what follows.

**Bib entry: corrected.** Authors, title, year and address match the title page ("by
P. J. M. van Laarhoven and E. H. L. Aarts, Philips Research Laboratories, Eindhoven,
The Netherlands") and the Library of Congress data on the copyright page. The publisher
did not. The copyright page reads "(c) 1987 by Springer Science+Business Media
Dordrecht / Originally published by D. Reidel Publishing Company, Dordrecht, Holland in
1987", and the series line names "Mathematics and its applications (D. Reidel
Publishing Company)". Kluwer appears nowhere in the book. **Edit made:** `publisher =
{Kluwer Academic Publishers}` to `publisher = {D. Reidel}`, one field, nothing else
touched. Kluwer absorbed Reidel after publication, which is where the common miscitation
comes from, but the 1987 imprint is Reidel and that is what the book itself says.

**Summary of the pass:** four statements checked, all four confirmed as written. One
bibliographic field corrected. No wording change anywhere in the thesis.

### Statement 1 of 4 - Simulated Annealing, Working Principle (`chapters/Metaheuristic Optimisation Methods.tex:239`)

> In practice SA is structured with an inner loop: a fixed number of moves $L$ (the
> epoch length) is attempted at each temperature level before cooling, so that the
> neighbourhood is adequately sampled before the search commits to a colder
> regime~\cite{vanlaarhoven1987,talbi2009}

**Verdict: CONFIRMED. No edit.**

The inner loop is the book's own pseudocode. Figure 2.1, p. 10, "Description of the
annealing algorithm in pseudo-PASCAL", is two nested `repeat` loops: the inner one does
PERTURB, the Metropolis test and UPDATE and runs "until equilibrium is approached
sufficiently closely", after which the outer loop cools, "c_{M+1} := f(c_M)", and
repeats "until stop criterion = true (system is 'frozen')". That is the structure the
sentence describes, in the order it describes it.

*The quantity and its symbol.* Section 5.1, p. 57, lists what an implementation must
fix: "1. initial value of the control parameter, c_0; 2. final value of the control
parameter, c_f (stop criterion); 3. length of Markov chains; 4. a rule for changing the
current value of the control parameter, c_k, into the next one, c_{k+1}", and calls the
four together "a cooling schedule". The same page introduces the symbol: "if L_k is the
length of the k-th Markov chain, then the annealing algorithm is said to be in
quasi-equilibrium at c_k". The thesis's L is the book's L_k.

*That it is fixed.* Section 5.2, p. 60: "The simplest choice for L_k, the length of the
k-th Markov chain, is a value depending (polynomially) on the size of the problem.
Thus, L_k is independent of k." The book then sorts every schedule into two families,
p. 71: "Class A: a variable Markov chain length and a fixed decrement of the control
parameter" and "Class B: a fixed Markov chain length and a variable decrement of the
control parameter". This thesis fixes L and decrements geometrically, so the sentence
describes a choice the book documents rather than claiming it is the only one.

*Adequate sampling of the neighbourhood.* This is the book's own sizing rule. Table
5.1, p. 72, gives the chain length for the Aarts and Van Laarhoven schedule as
"R = |R_i|", the size of the neighbourhood, and p. 61 reports the same convention in
others: Kirkpatrick et al. use "L = n, the number of variables of the problem to solve",
Johnson et al. "L = m . R, a multiple of the size of the neighbourhoods". Why it must
happen before cooling is the physical analogy the book opens with, p. 8: "if the cooling
is too rapid, i.e. if the solid is not allowed to reach thermal equilibrium for each
temperature value, defects can be 'frozen' into the solid", carried into the algorithm
on p. 9: "The control parameter is then lowered in steps, with the system being allowed
to approach equilibrium for each step".

*Terminology note, not an error.* The book does use the word "epoch", but for a
different construct: p. 61, "define an epoch as a number of transitions with a fixed
number of acceptances" (Skiscim and Golden's variable-length rule). The thesis defines
"epoch length" inline as the fixed move count L, which is standard current usage and is
what `talbi2009` supports at p. 131, so nothing needs changing. Worth knowing if anyone
reads the two side by side.

### Statement 2 of 4 - Simulated Annealing, The Cooling Schedule (`chapters/Metaheuristic Optimisation Methods.tex:246`)

> The temperature schedule controls how fast SA transitions from broad exploration to
> focused local search, and SA's performance is highly sensitive to
> it~\cite{kirkpatrick1983,talbi2009,vanlaarhoven1987}

**Verdict: CONFIRMED. No edit, and the earlier softening of this sentence is vindicated.**

The sensitivity claim is one of the book's headline conclusions, stated twice. Chapter
6, p. 98: "the performance of the simulated annealing algorithm depends strongly on the
chosen cooling schedule; this is especially true for the quality of the solution
obtained by the algorithm". Chapter 9, p. 154: "the performance of the algorithm is
strongly dependent on the chosen cooling schedule, especially as far as the quality of
solution is concerned. Indeed, it is shown that the performance of the algorithm
deteriorates severely if the cooling schedule employed belongs to the class of simple
schedules mentioned before." "Highly sensitive" is the right strength for that.

The exploration-to-local-search half is the book's two limits. High c, p. 58: "For
c_k -> infinity, the stationary distribution is given by the uniform distribution on the
set of configurations R [...] choosing the initial value of c, c_0, such that virtually
all transitions are accepted". Low c, p. 10: "the situation where the control parameter
in the simulated annealing algorithm is set to 0 corresponds to a version of iterative
improvement", and p. 65, in Huang et al.'s stop rule, "c is set to 0 and the
optimization is concluded with a local search (iterative improvement)".

*On the Statement 7 edit under `talbi2009`.* That pass replaced "it is the most
important design decision when applying the algorithm" with the present wording. This
book confirms the change was right in both directions: it says performance depends
strongly on the schedule, and it nowhere ranks the schedule above SA's other design
choices. p. 96 adds the empirical form of the same point: "The large difference between
these numbers and the average results shown in table 6.1 is another indication for the
importance of choosing a more elaborate cooling schedule."

### Statement 3 of 4 - Simulated Annealing, The Cooling Schedule (`chapters/Metaheuristic Optimisation Methods.tex:254`)

> The starting temperature $T_{\max}$ is commonly calibrated so that typical worsening
> moves are initially accepted around $80\,\%$ of the
> time~\cite{kirkpatrick1983,vanlaarhoven1987}

**Verdict: CONFIRMED. No edit.**

The number and its attribution are both on p. 59: "Kirkpatrick et al. propose the
following empirical rule: choose a large value for c_0 and perform a number of
transitions. If the acceptance ratio chi, defined as the number of accepted transitions
divided by the number of proposed transitions, is less than a given value chi_0 (in
[KIR82] chi_0 = 0.8), double the current value of c_0. Continue this procedure until the
observed acceptance ratio exceeds chi_0." That is the 80 % rule, and the book credits it
to Kirkpatrick et al., so the co-citation to `kirkpatrick1983` is correctly placed too.

*Precision point worth having ready.* "Worsening moves" matches the refinement on the
same page rather than Kirkpatrick's raw ratio. Kirkpatrick's chi counts all accepted
transitions over all proposed ones, which includes improving moves that are accepted
unconditionally. Johnson et al., quoted immediately after, "determine c_0 by calculating
the average increase in cost, dC(+), for a number of random transitions and solve c_0
from chi_0 = exp(-dC(+)/c_0)", giving eq. 5.7, c_0 = dC(+) / ln(chi_0^-1). There chi_0
is exactly the Metropolis acceptance probability of a move of average cost increase,
which is what the thesis sentence says. Both readings sit on p. 59 and both use 0.8, so
the sentence is supported as written; if pressed, the answer is that the thesis quotes
the calibration in its worsening-move form, which is the form an implementation uses.

### Statement 4 of 4 - Simulated Annealing, The Cooling Schedule (`chapters/Metaheuristic Optimisation Methods.tex:261`)

> A logarithmically slow schedule guarantees the global optimum in
> theory~\cite{hajek1988} but is far too slow to be useful in practice, so performance
> within a fixed budget depends heavily on the tuned schedule~\cite{vanlaarhoven1987}

**Verdict: CONFIRMED. No edit.**

The clause carrying `vanlaarhoven1987` is the impracticality, and the book makes it
directly. Section 5.1, p. 56, on why the convergence theory gives no usable schedule:
the equilibrium condition "implies that the length of the Markov chains should at least
be exponential in the problem size, which is, in the light of the discussion in chapter
1, highly undesirable", and the logarithmic decrement rule "requires knowledge about the
value of the constant Gamma. Usually, however, it is extremely difficult to determine
such a value [...] One resorts to conservative estimates, like Gamma = dC_max, which
leads, however, to unnecessarily slow convergence of the algorithm". Section 6.2, p. 81,
quantifies it: "This bound is rather poor, however, in the sense that if one works it
out for a particular problem one typically finds that the time required for good
accuracy is larger than the number of configurations (for the n-city travelling salesman
problem, for example, one finds that k is O(e^-n^(2n+1)) [...] whereas the number of
configurations is O(n!))." The closing clause about the tuned schedule is the same
conclusion quoted under Statement 2.

*Incidental check of the neighbouring key.* The `hajek1988` attribution is corroborated
here. Section 3.2.3, Theorem 6, p. 36, is stated as "(Hajek, [HAJ88])" and gives the
necessary and sufficient condition for convergence, with "If c_k is of the form
c_k = Gamma/log k [...] then Hajek's result clearly implies that eq. 3.96 holds if and
only if Gamma >= D." The book's [HAJ88] is "Hajek, B., Cooling Schedules for Optimal
Annealing, Mathematics of Operations Research, 13(1988)311-329", which is the thesis's
`hajek1988`. Note the strength: Hajek's condition is necessary *and* sufficient,
stronger than the sufficient-only bounds of Geman and Geman, Anily and Federgruen and
Mitra et al. on pp. 30-33. "Guarantees the global optimum in theory" is a fair reading
and, if anything, understates the result.
