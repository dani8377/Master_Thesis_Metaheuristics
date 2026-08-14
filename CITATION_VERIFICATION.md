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

*Partly superseded, 2026-08-14.* The last clause of the first paragraph above, "so the
co-citation to `kirkpatrick1983` is correctly placed too", no longer holds. The
`kirkpatrick1983` pass checked the 1983 *Science* article itself and the 0.8 rule is not
in it. The book's key for the number is [KIR82], not [KIR83]. `kirkpatrick1983` has been
removed from that one citation; see Statement 5 under `kirkpatrick1983` below. The
book's own support for the sentence is unaffected and still stands.

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

---

## `muhlenbein1996` (ref. 70)

**Source:** H. Muhlenbein and G. Paass, "From Recombination of Genes to the Estimation of
Distributions I. Binary Parameters", in *Parallel Problem Solving from Nature - PPSN IV*,
Lecture Notes in Computer Science 1141, Springer, Berlin, 1996, pp. 178-187.
DOI 10.1007/3-540-61723-X_982.

**Checked:** 2026-08-14, against the full paper PDF (10 pages, Sections 1-6 plus 18
references).

**Bib entry: correct, no change.** The byline reads "H. Muhlenbein and G. Paass, GMD -
Forschungszentrum Informationstechnik, 53754 Sankt Augustin, Germany", matching the author
fields. The title matches exactly, including the "I. Binary Parameters" part. The Crossref
record for the DOI returns the same title, the same two authors, container title "Parallel
Problem Solving from Nature - PPSN IV", and pages 178-187, so venue, page range and year
are all confirmed. Volume 1141 is the LNCS number for PPSN IV. The DOI resolves.

**Summary of the pass:** eight statements checked across three chapters, all eight
confirmed as written. No bibliographic field changed and no wording changed anywhere in
the thesis. This key is unusually well supported: three of the eight statements are near
verbatim restatements of the paper's own algorithm box or theorems.

**Standing caveat for all eight.** The paper is binary, x_i in {0,1}, as its title says.
The thesis uses a categorical marginal over m servers. Nowhere does the thesis attribute
the multi-valued generalisation to this paper, and it cites `adak2026` separately for a
multi-valued variant of the compact GA
(`chapters/Metaheuristic Optimisation Methods.tex:498`), so the distinction is already
drawn. If an examiner raises it, the answer is that going from Bernoulli to categorical
marginals changes the per-variable distribution family only and leaves the
select-estimate-sample loop untouched.

### Statement 1 of 8 - Implementation, UMDA, Model estimation (`chapters/Implementation.tex:119`)

> The algorithm is UMDA in its pure form: the probability matrix is re-estimated from
> scratch each generation, with no incremental learning rate (in the PBIL view, a learning
> rate of $1$ \citep{baluja1994,muhlenbein1996})

**Verdict: CONFIRMED. No edit.**

This is the strongest of the eight, because the paper draws the UMDA-versus-PBIL contrast
itself and each citation is the correct half of it. UMDA, Section 3, samples directly from
the selected set's frequencies with no carry-over: "STEP1: Select M <= N points according
to a selection schedule. Compute the marginal frequencies r_{t;i}(x_i) of the selected set.
STEP2: Generate N new points according to the distribution
q_{t+1}(x) = prod_{i=1}^n r_{t;i}(x_i)." That is re-estimation from scratch, and it is what
the implementation does.

Section 4 then introduces the incremental variant and attributes it to Baluja and Caruana
by name: "Independently of the theory presented in this paper a simple algorithm has been
already proposed in [2]. In this algorithm the univariate marginal frequencies are updated
according to p_{t+1;i}(x_i) = p_{t;i}(x_i) + lambda(r_{t;i}(x_i) - p_{t;i}(x_i))" (eq. 14),
"where lambda is a control parameter. The resulting algorithm we call the simple univariate
marginal distribution algorithm (SUMDA)". Reference [2] is "S. Baluja and R. Caruana.
Removing the genetics from the standard genetic algorithm", which is the thesis's
`baluja1994`. Setting lambda = 1 in eq. 14 collapses it to p_{t+1;i} = r_{t;i}, which is
exactly UMDA's STEP2. The parenthetical is therefore not an analogy imported from
elsewhere, it is arithmetic on the paper's own equation, with `baluja1994` carrying the
PBIL update rule and `muhlenbein1996` carrying the lambda = 1 endpoint.

### Statement 2 of 8 - Metaheuristic Optimisation Methods, EDAs (`chapters/Metaheuristic Optimisation Methods.tex:427`)

> Estimation of Distribution Algorithms (EDAs)
> \cite{muhlenbein1996,larranaga2001,hauschild2011} are model-based alternatives to
> traditional GAs.

**Verdict: CONFIRMED. No edit.**

This is an origin citation and the paper is the origin. Its title supplies the phrase and
the abstract states the programme: "In the last part of the paper we discuss more
sophisticated methods, based on estimating the distribution of promising points."
Section 3 delivers the first such algorithm, UMDA. The framing as an alternative to GA
recombination is the paper's own: "But in evolutionary computation we have more freedom. We
can design new recombination operators which have no counterpart in nature", and, on gene
pool recombination, "The biologically inspired idea of restricting the recombination to the
alleles of two parents for each offspring is abandoned."

Worth knowing rather than fixing: the paper never uses the acronym "EDA", which was
consolidated later. The two co-cites are what carry the acronym and the modern definition,
so the triple is correctly ordered as origin plus definition.

### Statement 3 of 8 - Metaheuristic Optimisation Methods, EDAs (`chapters/Metaheuristic Optimisation Methods.tex:429`)

> They emerged in response to the difficulty standard GAs have with strongly interacting
> variables, where crossover can disrupt useful structure
> \cite{baluja1994,muhlenbein1996}

**Verdict: CONFIRMED. No edit.** This one genuinely earns its co-citation, so the division
of labour is worth having ready.

`muhlenbein1996` carries the interacting-variables half, in three places. Section 6:
"Deceptive problems have been introduced by Goldberg [9] as a challenge to genetic
algorithm. For these functions genetic algorithms will converge to sub-optimal points."
Section 5: "The suitability of these algorithms for solving optimization problems with
strongly interacting genes at different loci seems limited", which is what motivates the
move to conditional distributions in the same section. And on the messy GA, Section 6: "we
believe that it is impossible to detect all important gene interactions by simply
manipulating substrings".

`baluja1994` carries the crossover clause. This paper does discuss crossover, but its
complaint is analytic rather than about disruption of building blocks. Section 2: "Uniform
crossover in genetic algorithms, which models Mendelian recombination, leads to very
difficult systems of difference equations. The genetic population moves away from linkage
equilibrium. This makes an analysis of the algorithm almost impossible." The sentence is
supported as written by the pair, and if pressed on which reference supports which clause,
the answer is the split above rather than both for both.

The sharpest form of the objection, worth pre-empting, is about "emerged in response to".
The paper's *own* stated motivation is neither of the two clauses but a third thing,
namely analytical tractability of the breeder-GA theory. The abstract: "The Breeder Genetic
Algorithm (BGA) is based on the equation for the response to selection. In order to use
this equation for prediction, the variance of the fitness of the population has to be
estimated. For the usual sexual recombination the computation can be difficult." So the
thesis sentence states the standard retrospective account of why the EDA line of work
arose, which `larranaga2001` and `hauschild2011` give in exactly those terms one paragraph
earlier, rather than paraphrasing this paper's introduction. That is a normal use of an
origin paper and not an over-claim, because the thesis does not write "Muhlenbein and Paass
argue that". The interacting-variables thread genuinely is in the paper, in Sections 5 and
6, as quoted above; it is simply not what its abstract leads with.

### Statement 4 of 8 - Metaheuristic Optimisation Methods, Model Classes (`chapters/Metaheuristic Optimisation Methods.tex:457`)

> This work therefore evaluates a single representative, the Univariate Marginal
> Distribution Algorithm (UMDA) \cite{muhlenbein1996}.

**Verdict: CONFIRMED. No edit.**

A naming citation, and the name is coined here. Section 3, immediately after eq. 7: "The
conceptual Univariate Marginal Distribution Algorithm (UMDA) is defined as follows",
followed by the four-step box. Nothing beyond the name and the algorithm is claimed by the
sentence.

### Statement 5 of 8 - Metaheuristic Optimisation Methods, Working Principle of UMDA (`chapters/Metaheuristic Optimisation Methods.tex:471`)

> UMDA maintains a population $P_t$ of $N$ candidates and, each generation, performs
> \emph{evaluation}, \emph{selection}, \emph{estimation}, and \emph{sampling}
> \cite{muhlenbein1996,larranaga2001}: $S_t = select(P_t)$, $p_t = estimate(S_t)$,
> $P_{t+1} = sample(p_t, N)$.

**Verdict: CONFIRMED. No edit.** A near verbatim restatement of the algorithm box.

Step for step, Section 3: "STEP0: Set t = 1. Generate N >> 0 points randomly" gives the
population of N; "STEP1: Select M <= N points according to a selection schedule. Compute
the marginal frequencies r_{t;i}(x_i) of the selected set" gives select then estimate;
"STEP2: Generate N new points according to the distribution
q_{t+1}(x) = prod_{i=1}^n r_{t;i}(x_i)" gives sample, and STEP3 returns to STEP1. The
thesis's factorisation p_t(x) = prod_i p_{t,i}(x_i) two lines further down is the paper's
eq. 6, and the frequency-count estimator is its eq. 7, p_i(x_i) = sum_{x|x_i} q(x).

Two incidental corroborations. The thesis writes "keeping the top mu <= N individuals", and
the paper's STEP1 is literally "Select M <= N points", the same relation under a different
letter. And the thesis's choice of truncation is a legitimate instantiation rather than a
departure, because STEP1 specifies only "according to a selection schedule". The paper's
theorems then specialise to proportionate selection for tractability, which the thesis does
not claim to follow.

### Statement 6 of 8 - Metaheuristic Optimisation Methods, Working Principle of UMDA (`chapters/Metaheuristic Optimisation Methods.tex:506`)

> Three parameters govern the exploration--exploitation balance
> \cite{muhlenbein1996,larranaga2001}: the population size $N$ [...] the selection ratio
> $\mu / N$ [...] and a margin that keeps marginals away from the exact extremes so a value
> absent from one generation's selection is not lost forever \cite{chen2010analysis}

**Verdict: CONFIRMED. No edit.** The weakest of the eight for this key taken alone, but the
citations are placed so that every clause has a source that carries it.

N and the selection ratio are the paper's only UMDA parameters, and they are exactly the
two free quantities in the algorithm box: N in STEP0 and M <= N in STEP1. The paper also
treats N as governing behaviour rather than as an implementation detail: "For difficult
multi modal fitness functions the success of SUMDA depends on the parameter lambda and N",
and "Because the size of the population, N, is very large, the speed of convergence is
almost independent of the size of the problem n."

Three things this paper does not supply, each already sourced elsewhere in the thesis, so
none is an over-attribution. The margin has its own citation, `chen2010analysis`, at the end
of that clause; this paper has no margin, and its own safeguard against collapse is SUMDA's
lambda instead. "mu = N/2 a common default" is hedged as convention and rests on
`larranaga2001`. The word "drift" in the gloss on N rests on `shapiro2005drift`,
`doerr2020sharp` and `witt2019upper`, cited two paragraphs earlier at line 465 where the
concept is introduced; this paper predates that analysis and does not use the term.

### Statement 7 of 8 - Metaheuristic Optimisation Methods, Encoding and Constraints (`chapters/Metaheuristic Optimisation Methods.tex:527`)

> Third, the objective function of Equation~\eqref{eq:cloud_obj} is approximately additive
> across tasks under the soft-penalty formulation, a structure favourable to univariate EDAs
> \cite{muhlenbein1996,muhlenbein1999fda}.

**Verdict: CONFIRMED. No edit.** The paper proves this rather than asserting it, which makes
the citation stronger than the sentence needs.

Theorem 4 gives the response to selection as R(t) = V_A(t)/f(t) plus a term that vanishes in
linkage equilibrium, where V_A is the additive genetic variance of eq. 11. The corollary on
the same page is the sharp form: "For proportionate selection the UMDA stays in equilibrium
iff V_A = 0", glossed as "The response to selection is zero if the additive variance is
zero. UMDA only exploits the additive genetic variance." Section 5 states the consequence
for problem structure directly: the marginal-distribution algorithms "exploit the additive
genetic variance mainly", and their "suitability for solving optimization problems with
strongly interacting genes at different loci seems limited". The empirical side matches,
with Table 1 showing SUMDA converging on the linear function ONEMAX while Sections 5 and 6
abandon univariate models for the deceptive functions.

So "favourable to univariate EDAs" is the contrapositive of a theorem in the source, not a
soft claim. The thesis's own hedge in the next sentence, that the argument weakens when
capacities bind tightly, is the right one, because the paper's limit case is "UMDA is not a
global optimization method for difficult fitness functions."

### Statement 8 of 8 - Related Work, EDAs on Cloud Allocation (`chapters/Related work.tex:21`)

> The most widely used univariate EDA is the Univariate Marginal Distribution Algorithm
> (UMDA)~\cite{muhlenbein1996}, which re-estimates each variable's marginal directly from
> the selected population at every generation

**Verdict: CONFIRMED. No edit.**

The mechanism clause is the algorithm box again, and "directly from the selected population"
is the precise wording, because STEP2 samples from r_{t;i}, the frequencies of the selected
set itself, with no intermediate vector. The contrast drawn in the next sentence of the same
paragraph is also the paper's own: PBIL "instead updates a single probability vector
incrementally", which is eq. 14 and its attribution to reference [2], Baluja and Caruana.
See Statement 1.

"Most widely used" is a claim about the literature, not about this paper, and the citation
sits on the algorithm's name rather than on the superlative, so it is correctly placed.

## `moscato1989` (ref. 68)

**Source:** P. Moscato, "On Evolution, Search, Optimization, Genetic Algorithms and Martial
Arts: Towards Memetic Algorithms", Caltech Concurrent Computation Program, California
Institute of Technology, Pasadena, CA, C3P Report 826, 1989.

**Checked:** 2026-08-14, against the full report PDF (67 pages, Sections 1-10 plus 194
references).

**Bib entry: correct, no change.** The cover page gives the author as Pablo Moscato and the
title on two lines, "On Evolution, Search, Optimization, Genetic Algorithms and Martial
Arts" over "Towards Memetic Algorithms", which the bib joins with a colon in the usual way.
The affiliation block reads "Caltech Concurrent Computation Program 158-79, California
Institute of Technology, Pasadena, CA 91125", matching the institution and address fields.
Two fields cannot be read off this scan and were checked for consistency instead. The report
number C3P 826 is not printed on the cover, but the report's own reference list cites three
neighbouring Moscato items as C3P-778, C3P-789 and C3P-790, all 1989, so 826 sits in the
right series and is the number by which the report is universally cited. The year is not
printed either, but the newest references in it are from July 1989 and the acknowledgements
thank friends "during this year at Caltech", so 1989 is consistent.

**Summary of the pass:** four statements checked across three chapters. Three confirmed as
written. One clause in the Chapter 4 footnote was narrowed, because it overstated the gene
side of the gene-versus-meme contrast in a way the source does not support and the thesis's
own GA contradicts. No bibliographic field changed.

**Note on what this source is.** It is the report that names memetic algorithms, so all four
instances are origin citations for the term and the template rather than claims about
experimental results. That is the right use of it. The report's own experiments are on the
TSP and the quadratic assignment problem, and the thesis never attributes an EV routing
result to it.

### Statement 1 of 4 - Implementation, Memetic Algorithm (`chapters/Implementation.tex:170`)

> The memetic algorithm \citep{moscato1989} reuses the GA but refines each offspring with up
> to thirty first-improvement local-search steps (drawn from the same eight operators)
> before it enters the population.

**Verdict: CONFIRMED. No edit.**

The citation carries the name and the template, and both are the report's. Section 5, "The
Memetic algorithm": "Memetic algorithms is a marriage between a population-based global
search and the heuristic local search made by each of the individuals." The ordering the
sentence describes, local search first and population membership second, is the report's own
procedure: "After that, each individual makes local search... After that, when the individual
has reached a certain development, it interacts with the other members of the population."

The bounded budget of thirty steps is within what the report allows rather than a departure
from it. It states that local search need not run to a local optimum: "The mechanism to do
local search can be to reach a local optima or to improve (regarding the objective cost
function) up to a predetermined level." A step cap is one such level.

The numbers, the eight operators and the first-improvement rule are this thesis's own design
choices, and the sentence does not attribute them to the source.

### Statement 2 of 4 - Metaheuristic Optimisation Methods, Memetic Algorithms (`chapters/Metaheuristic Optimisation Methods.tex:190`)

> A Memetic Algorithm (MA) hybridises a population-based method with local search, so that
> the population evolves over locally optimised solutions rather than raw offspring
> \cite{moscato1989}. [footnote] The name is Moscato's, after Dawkins's \emph{meme}, a unit
> of cultural rather than genetic transmission.

**Verdict: CONFIRMED. No edit.**

Three separate claims here, all of them the report's.

The definition is the sentence quoted under Statement 1, the marriage of population-based
global search with per-individual local search. The stronger half of the thesis sentence,
that the population evolves over locally optimised solutions rather than raw offspring, is
the report's too, in the passage where it quotes Brown et al. on SAGA and endorses the
wording: "each of the offspring generated by the GA in a given generation is improved using
SA. In other words, each offspring is required to 'mature' before being allowed to have
offspring". Moscato adds that he "found myself using the same words" for all three methods
he surveys.

The name is his. Conclusions: "Due to some of these analogies and the fact that they clearly
diverge of some other approaches, I found that they can be labeled as memetic algorithms."

The etymology is stated in Section 5, "The concept of the meme": "R. Dawkins in the last
chapter of his book 'The Selfish Gene', has introduced the word meme to denote the idea of a
unit of imitation in cultural transmission which in some aspects is analogous to the gene."
The thesis compresses "unit of imitation in cultural transmission" to "a unit of cultural
rather than genetic transmission", and the contrast it adds is the report's framing
throughout that section, which is built on "the analogies between cultural and genetic
evolution".

### Statement 3 of 4 - Metaheuristic Optimisation Methods, Memetic Algorithms footnote (`chapters/Metaheuristic Optimisation Methods.tex:190`)

> Genes are passed on unchanged, whereas memes are typically improved by their carrier
> before being propagated, just as each offspring here is locally refined before it enters
> the population \cite{moscato1989}.

**Verdict: OVERREACHED ON THE GENE SIDE. Edited.**

The meme half is well supported and stays. Section 5 is explicit that a meme is improved
before it is passed on, and that this is what separates cultural from genetic evolution:
"Only the masters have the sufficient knowledge that permits them create a new movement and
to incorporate it to the form... So, there is much problem specific knowledge that is applied
to each modification. Almost all modifications give improvements rather than create a
disorder. This fast-feedback flow of information from high order phenotype knowledge to
genotype level, seems to have differences with the processes of biological evolution."
He names this as the source of the speed-up: "the analogy of cultural and genetic evolution
breaks down in the copying-fidelity aspects of them in addition with mutation. And that
these break-down points are the reasons of the tremendous speed-up observed in cultural
evolution."

"Genes are passed on unchanged" was the problem. The report does not say that. What it
quotes from Dawkins is about particulateness, not constancy: meme transmission looks "quite
unlike the particulate, all-or-none quality of gene transmission", the point being that a
gene arrives whole or not at all while a meme can arrive blended. Moscato says close to the
opposite of "unchanged" two pages earlier, listing how life searches: "performing point
mutational operations like the substitution, insertion or deletion of nucleotides in the DNA
or RNA. Other rearrangements of the structure are chromosomal mutations like the deletions,
inversions, duplications, transpositions, translocations, conversions". The sentence also sat
oddly next to the thesis's own GA, which mutates offspring at rate $0.15$ and at $0.25$ in
the MA, so an examiner reading the footnote against Chapter 6 would have a fair question.

**Edit made.** `chapters/Metaheuristic Optimisation Methods.tex:190`, the footnote's second
sentence:

- before: "Genes are passed on unchanged, whereas memes are typically improved by their
  carrier before being propagated, just as each offspring here is locally refined before it
  enters the population"
- after: "Unlike a gene, a meme is usually improved by its carrier before being passed on,
  which is what local search does to each offspring"

That is the contrast the report actually draws, the absence in biology of any feedback from
what the individual learns back into what it transmits, against the meme that its carrier
refines first. It is also the contrast the analogy needs, since local search is that
feedback. "Usually" carries the report's own hedge, "almost all modifications give
improvements rather than create a disorder".

The replacement is also shorter than the original, 24 words against 34. The first draft of
this fix kept the original three-clause shape and read "Genes are not improved by the
individual that carries them, whereas memes usually are, just as each offspring here is
locally refined before it enters the population". Two things were wrong with it against the
supervisor's style rules. "Whereas memes usually are" leaves the verb phrase elliptical,
where "unlike a gene" states the contrast directly. And the closing clause repeated what the
body sentence had just said two lines earlier, that the population evolves over locally
optimised solutions rather than raw offspring. Nothing else in the footnote or the paragraph
changed.

### Statement 4 of 4 - Related Work, Heuristics and Metaheuristics on EVRP (`chapters/Related work.tex:53`)

> Combining a genetic algorithm with local refinement yields a \emph{memetic
> algorithm}~\cite{moscato1989}, a template that is particularly effective on routing
> problems because the local-search step repairs the route disruption that recombination
> causes.

**Verdict: CONFIRMED. No edit.**

The first clause is the report's own way of positioning MA against GA: "The GA community
would like to say that MA are only a special kind of GA with local hill-climbing", and "my
impression is that the only clear separation is the local search, which was considered the
hybrid characteristic for the eyes of the GA community".

The causal clause is the stronger claim and it is supported almost verbatim, in the report's
own TSP implementation. Section 6, "The Optimisation Schedule", gives as the first reason for
interleaving the phases "that the results of cooperation do not compete until they have
undergone local optimisation to ameliorate the damage caused by the OX operator". Damage
caused by the OX operator is route disruption caused by recombination, and local optimisation
ameliorating it is the local-search step repairing it. The disruption itself is quantified in
the preceding subsection: "the excision of cities means that achieving the subtour often makes
significant changes to the tour into which it is inserted... the number of links in the second
tour which change during crossover may be any value, up to the number of links it contains."

"Particularly effective on routing problems" is carried by the report's results rather than by
an assertion in it, which is the weaker form of support but adequate here. Its own TSP runs
land at or near optimum, and the ASPARAGOS results it surveys reach the optimum on instances
below 100 cities and come under one percent above optimum on the 532-city Padberg and Rinaldi
instance. The same pairing is separately attributed to `talbi2009` in Chapter 4 and shown
empirically by `liu2022hybridga` in the sentence that follows this one, so the claim does not
rest on this source alone.

## `mann2015allocation` (ref. 61)

**Source:** Z. A. Mann, "Allocation of Virtual Machines in Cloud Data Centers - A Survey of
Problem Models and Optimization Algorithms", ACM Computing Surveys, volume 48, issue 1, 2015.
DOI 10.1145/2797211.

**Checked:** 2026-08-14, against the full survey PDF (28 pages, Sections 1-8 plus 124
references).

**Bib entry: correct, no change.** The byline reads "Zoltan Adam Mann, Budapest University of
Technology and Economics" and the first-page footnote reads "Published in ACM Computing
Surveys, volume 48, issue 1, 2015", which fixes author, journal, volume, number and year. The
title matches word for word; the dash before "A Survey" prints as an en dash in this preprint
and as an em dash in the ACM version, which is the form the bib uses. One field cannot be read
off this scan: the `pages` value `11:1--11:34` is the ACM article numbering, and the preprint
paginates 1-28 with no article number printed. It was left as is, since nothing in the PDF
contradicts it and it is consistent with the DOI.

**Summary of the pass:** four statements checked across two chapters, all confirmed as
written. No edit to the report, and no bibliographic field changed.

**Note on what this source is.** It is a survey of problem models and algorithms, so every
instance here is a "this is how the field frames it" citation rather than an experimental
result. That is the right use of it: the survey reports no experiments of its own, and the
thesis never attributes a measured number to it.

### Statement 1 of 4 - Problem Specification, Sets and Parameters (`chapters/Problem Specification.tex:92`)

> CPU usage is assumed to be linearly additive across tasks and perfectly divisible across
> cores, a standard abstraction in the cloud scheduling
> literature~\cite{beloglazov2012energy,mann2015allocation} that ignores non-linear effects
> such as cache contention but preserves the essential property that aggregate demand must
> not exceed aggregate capacity.

**Verdict: CONFIRMED. No edit.**

The citation is shared with `beloglazov2012energy`, which supplies an instance of the
abstraction. Mann is what carries the word "standard", and the survey supports all three parts
of the sentence separately.

Divisible across cores, Section 4.2: "Beloglazov and Buyya model a multi-core CPU by means of
a single-core CPU with capacity equal to the sum of the capacities of the cores of the
original multi-core CPU". That summing of core capacities into one pool is exactly the
assumption the sentence names. Section 4.1.3 records how common it is, "In this
often-investigated special case, only the computational demands and computational capacities
are considered, and no other resources. Moreover, the CPU is taken to be single-core, making
the problem truly one-dimensional", and Section 7.1 lists the gap among the field's open
problems: "The existing problem formulations in the literature either do not model multi-core
CPUs at all, or model them in a very simplistic way."

Additive, and the capacity property that survives, Section 7.1: "When deciding to place a set
of VMs on a PM, many works only check that the total size of the VMs does not exceed the PM's
capacity." Total size against capacity is the aggregate-demand test the sentence says the
abstraction preserves.

Cache contention as the named casualty, Section 3.3: "current virtualization technologies do
not ensure isolation of the cache usage of individual VMs accommodated by the same PM, leading
to contention between them". The same Section 7.1 paragraph puts this on the deficit list
under "co-location interference" and the "noisy neighbor" effect, so the survey agrees both
that the abstraction is standard and that this is what it costs.

### Statement 2 of 4 - Related Work, Cloud Resource Allocation (`chapters/Related work.tex:8`)

> The cloud resource allocation problem studied in this thesis is usually framed as Virtual
> Machine Placement (VMP)~\cite{mann2015allocation}.

**Verdict: CONFIRMED. No edit.**

The survey is that framing. Its keyword list is "Cloud computing, data center, virtual
machine, live migration, VM placement, VM consolidation, green computing", and the abstract
states the object of study as "a careful allocation of VMs to hosts". Section 7.1 gives the
usual-case wording the thesis sentence needs: "In the Single-DC problem, the usual formulation
is about mapping VMs to PMs." Section 5.2 then uses "the VM placement problem" as the standing
name throughout. Mann treats "VM allocation" and "VM placement" as the same problem, so the
thesis naming it VMP is faithful rather than a narrowing.

### Statement 3 of 4 - Related Work, Cloud Resource Allocation (`chapters/Related work.tex:8`)

> The problem is NP-hard~\cite{mann2015allocation}, and the scale of modern data centres rules
> out exhaustive search in practice.

**Verdict: CONFIRMED. No edit.**

Section 7.2 states it and gives the argument: "Since the VM placement problem contains the
bin-packing problem as special case, which is NP-hard in the strong sense [77], there is no
hope for an exact algorithm with polynomial or even pseudo-polynomial runtime." The reduction
is by containment, with the bin-packing hardness itself credited to Martello and Toth, which
is the standard route and is also how Chapter 2 of the thesis reaches the same conclusion.
Section 6.3 carries an independent NP-hardness proof for one variant, Meng et al. "prove its
NP-hardness by reduction from Balanced Minimum k-Cut".

The second clause is supported by the same section: "the fact that those solvers took a long
time to solve even mid-sized problem instances", and Section 5.1, "its worst-case runtime is
exponential with respect to the size of the input, so that solving large-scale problem
instances takes much too long. Most researchers turned to heuristics for this reason."

### Statement 4 of 4 - Related Work, Heuristics and Metaheuristics on Cloud Allocation (`chapters/Related work.tex:14`)

> Comprehensive surveys are given by Mann~\cite{mann2015allocation} and, with a focus on
> bin-packing-style approaches, by Kumaraswamy and Nair~\cite{kumaraswamy2019binpacking}.

**Verdict: CONFIRMED. No edit.**

"Comprehensive" is fair and the survey says so itself, "we tried to show a representative
selection of the most important works", covering 124 references, two problem-model tables and
a full algorithm review split into exact methods (Section 5.1), Single-DC heuristics (5.2),
Multi-IaaS heuristics (5.3) and evaluation practice (5.5).

The sentence sits under a heading about heuristics and metaheuristics, and the survey covers
both, which is what the paragraph goes on to use it for: the bin-packing family in Section
5.2, "the usage of FF has been suggested [16], just like BF [10], WF [56, 71, 107], FFD [111,
113] and BFD [8, 7, 46]", and the metaheuristics in the next paragraph, "simulated annealing
[52], genetic algorithms [44], and ant colony optimization [41]". The lead-in sentence, that
the practical literature relies on heuristics, is the survey's own position: "Although the
majority of the proposed algorithms are heuristics, also some exact algorithms have been
proposed".

Scope note, not an error. Mann's coverage is wider than the subsection heading, since it
includes exact methods too. The sentence claims only that he gives a comprehensive survey, not
that the survey is confined to heuristics, so the placement is correct. The narrower framing
belongs to `kumaraswamy2019binpacking`, and the thesis already says so in the same sentence.

## `witt2019upper` (ref. 98)

**Source:** C. Witt, "Upper Bounds on the Running Time of the Univariate Marginal Distribution
Algorithm on OneMax", Algorithmica, volume 81, issue 2, pages 632-667, 2019.
DOI 10.1007/s00453-018-0463-0.

**Checked:** 2026-08-14, against the full paper PDF (36 pages, Sections 1-6 plus the appendix
proof of the drift theorem).

**Bib entry: correct, no change.** Author, title, journal, volume, pages and year match the
running head "Algorithmica (2019) 81:632-667" and the DOI printed on page 1. The issue number
is the one field the PDF never prints; Crossref gives issue 2, print date February 2019, which
is what the entry already has.

### Statement 1 of 1 - Metaheuristic Optimisation Methods, Model Classes (`chapters/Metaheuristic Optimisation Methods.tex:463`)

> Theoretical analyses show the population must be sized generously relative to $n$ to prevent
> \emph{genetic drift}, in which a marginal moves toward its extremes through finite-sample
> noise rather than genuine selection pressure
> \cite{shapiro2005drift,doerr2020sharp,witt2019upper}.

**Verdict: CONFIRMED. No edit.** Every clause is carried, and the paper uses the term itself
rather than leaving it to be inferred.

**The term.** Section 1 says Wu et al. "use concentration bounds such as Chernoff bounds to
bound the effect of so-called genetic drift, which is also considered in the present paper".
Section 3 fixes the meaning: "there are random fluctuations (referred to as genetic drift in
[26]) of frequencies that may lead to undesired decreases towards 0". Reference [26] is
Sudholt and Witt, GECCO 2016, where the name is coined.

**Noise rather than selection pressure.** Section 2.2 gives the mechanism exactly as the report
glosses it. Strip selection and "the frequency describes a random walk that is a martingale,
i.e., in expectation it does not change"; keep selection and "since only the accumulated number
of 1-bits per individual matters for selection, a single frequency may still decrease even if
the step leads to an increase of the best-so-far seen OneMax value".

**The extremes are absorbing.** Section 2: "If a frequency is either 0 or 1, it cannot change
anymore since then all values at this position will be either 0 or 1." Same passage supports
the later sentence at line 516 that a drifted marginal cannot recover without a mutation
operator.

**Sized relative to n.** This is the paper's phase transition. Section 1: "Around
mu = Theta(sqrt(n) log n), there is a phase transition in the behavior of the algorithm. With
smaller mu, the stochastic movement of the frequencies is more chaotic and many frequencies
will hit the lowest possible value during the optimization." Above the threshold, Lemma 11
proves that for mu >= c sqrt(n) log n a frequency does not fall to 1/4 within n^Theta(c)
generations, which subsumes any polynomial number of steps for c large enough, and Theorem 10
turns that into the O(lambda sqrt(n)) running-time bound. Section 5 matches empirically: for
n = 2000 the number of hits of the lower border decreases exponentially in lambda and the
transition sits "somewhere between 250 and 300", the same order as sqrt(n) ln n, about 340
(my arithmetic, not the paper's).

Three things worth having ready for the defence, none of them an error in the report.

**1. The paper proves sufficiency; necessity is quoted from elsewhere.** Lemma 11 shows a large
population prevents drift. The converse, that a small one causes it, is Krejca and Witt, FOGA
2017, restated in Section 4: "with high probability n^Omega(1) frequencies will walk to the
lower border before the optimum is found, resulting in a coupon collector effect". The report
says "theoretical analyses show", plural, across three sources, and this paper states the
two-sided threshold in its own introduction, so the "must" is carried. If pressed, quote the
phase-transition sentence, not Lemma 11.

**2. Drift is not failure, and that is the paper's headline.** With the borders [1/n, 1-1/n] in
place, Theorem 12 gives expected time O(lambda n) for mu >= c log n, far below the drift
threshold, and the conclusion extracts O(n log n) at mu = c' log n. Only the border-free
variant breaks: "For UMDA*, it is infinite with high probability if mu < c' sqrt(n) log n". The
report's sentence survives this because it claims a large population is needed to prevent
drift, not to make UMDA work at all. The margin paragraph at lines 510-518 is the counterpart
the UMDA/UMDA* split calls for, and it is also the answer if the examiner asks why this thesis
does not simply scale N with n: it uses Laplace smoothing, which is the border, so it sits on
the UMDA rather than the UMDA* side of that result.

**3. Scope.** All of this is binary UMDA on OneMax; this thesis runs a multi-valued UMDA over m
servers on a penalised objective. The mechanism transfers, since a marginal estimated from mu
samples carries sampling noise whatever its arity, but the threshold constant does not. That is
the reason not to sharpen "sized generously relative to $n$" into "of order sqrt(n) log n": the
figure belongs to this benchmark, and quoting it would claim more transfer than the sources
support. The wording stays qualitative on purpose.

**Not verified in this pass:** `shapiro2005drift` and `doerr2020sharp`, the other two citations
on the same sentence. Only the Witt PDF was supplied.

---

## `larranaga2001` (ref. 55)

**Source:** P. Larranaga and J. A. Lozano (editors), *Estimation of Distribution Algorithms:
A New Tool for Evolutionary Computation*, Genetic Algorithms and Evolutionary Computation
series, Kluwer Academic Publishers, Boston, MA, 2001. DOI 10.1007/978-1-4615-1539-5.

**Checked:** 2026-08-14.

**Read the caveat first: this pass is by proxy, not against the book.** The PDF supplied was
not the Kluwer book. It was E. Bengoetxea, P. Larranaga, I. Bloch and A. Perchant,
"Estimation of Distribution Algorithms: A New Evolutionary Computation Approach for Graph
Matching Problems", in *EMMCVPR 2001*, Lecture Notes in Computer Science 2134, Springer,
pages 454-469. That paper is a legitimate proxy and an unusually good one, for three reasons.
Larranaga is its second author. It is the same year as the book. And its Section 2, pages
455-460, is a self-contained tutorial exposition of the EDA framework which cites the book as
its own reference [16] on the opening line of Section 2.1, that is, the paper's summary of
EDAs is presented as a summary *of* the book, by one of the book's editors. Every one of the
six thesis statements below is matched against that Section 2. What this pass therefore
establishes is that the six claims are true of the EDA framework as the book's own editor set
it out in the same year, not that a specific page of the book says so. If an examiner asks for
page numbers in the book itself, that has not been done and the honest answer is to say so.

**Bib entry: correct, no change.** The one thing the supplied PDF verifies directly, and
verifies twice, is the bibliographic record. Reference [16] on page 467 reads
"P. Larranaga and J. A. Lozano. Estimation of Distribution Algorithms. A New Tool for
Evolutionary Computation. Kluwer Academic Publishers, 2001", confirming both names, the title
including the subtitle, the publisher and the year. Reference [35] on page 468 confirms
independently that the two are *editors* rather than sole authors, and so that `@book` with an
`editor` field is the right form: "In P. Larranaga and J. A. Lozano, editors, Estimation of
Distribution Algorithms. A new tool for Evolutionary Computation. Kluwer Academic Publishers,
2001". Reference [35] is itself a chapter in that book by the authors of the supplied paper,
which is also why the paper's Section 2 tracks the book so closely. The `series`, `address`
and `doi` fields are not printed in either reference and were not checked in this pass.

**Summary of the pass:** six statements checked across two chapters, all six confirmed as
written. No bibliographic field changed and no wording changed anywhere in the thesis. Four of
the six are near verbatim restatements of the source's own sentences or of its Figure 1
pseudocode.

### Statement 1 of 6 - Metaheuristic Optimisation Methods, model-based section (`chapters/Metaheuristic Optimisation Methods.tex:423`)

> Probabilistic Model-Based Metaheuristics replace the heuristic variation operators with an
> explicit probabilistic model fitted to the currently best solutions, and generate new
> candidates by sampling from that model \cite{larranaga2001,hauschild2011,pelikan2002survey}.

**Verdict: CONFIRMED. No edit.** The source states this as the defining property, and states
both halves of it, the fitting and the replacement, in consecutive sentences. Section 2.1,
page 455: "the characteristic that most differentiates EDAs from other evolutionary search
strategies such as GAs is that the evolution from a generation to the next one is done by
estimating the probability distribution of the fittest individuals, and afterwards by sampling
the induced model. This avoids the use of crossing or mutation operators." "The fittest
individuals" is the report's "the currently best solutions", and "avoids the use of crossing
or mutation operators" is the report's "replace the heuristic variation operators".

### Statement 2 of 6 - Metaheuristic Optimisation Methods, EDAs (`chapters/Metaheuristic Optimisation Methods.tex:427`)

> Estimation of Distribution Algorithms (EDAs)
> \cite{muhlenbein1996,larranaga2001,hauschild2011} are model-based alternatives to
> traditional GAs.

**Verdict: CONFIRMED. No edit.** This is a bare framing sentence and the source frames them
the same way. Section 2.1, page 455, places EDAs inside evolutionary computation, "EDAs
[16,17,18] are non-deterministic, stochastic heuristic search strategies that form part of the
evolutionary computation approaches", and then separates them from GAs by the model, in the
sentence quoted under Statement 1. The reference marker [16] on that first line is the book
itself, so the citation points at the work the source points at.

### Statement 3 of 6 - Metaheuristic Optimisation Methods, Model Classes (`chapters/Metaheuristic Optimisation Methods.tex:445`)

> EDAs are classified by the complexity of the fitted model
> \cite{pelikan2002survey,hauschild2011,larranaga2001}.

**Verdict: CONFIRMED. No edit.** The source not only states the classification principle but
organises its own Section 2.2 by it, and the three tiers it uses are the report's three tiers.
Page 457: "All the EDAs are classified depending on the maximum number of dependencies between
variables that they accept (maximum number of parents that a variable $X_i$ can have in the
probabilistic graphical model)." Maximum number of dependencies is the report's "complexity of
the fitted model". The subheadings that follow are "Without Interdependencies", with UMDA as
the example; "Pairwise Dependencies", with MIMIC as the example and reference [21] being
De Bonet, Isbell and Viola 1997, which is the thesis's `debonet1997`; and "Multiple
Interdependencies", with EBNA and a learned Bayesian network. That maps onto the report's
univariate, bivariate and multivariate tiers item for item, including the choice of MIMIC as
the bivariate representative.

### Statement 4 of 6 - Metaheuristic Optimisation Methods, Working Principle of UMDA (`chapters/Metaheuristic Optimisation Methods.tex:471`)

> UMDA maintains a population $P_t$ of $N$ candidates and, each generation, performs
> \emph{evaluation}, \emph{selection}, \emph{estimation}, and \emph{sampling}
> \cite{muhlenbein1996,larranaga2001}: [select, estimate, sample display]

**Verdict: CONFIRMED. No edit.** The strongest of the six. The report's three-operator display
is the source's Figure 1 pseudocode line for line, page 456: "$D_0$ <- Generate $N$ individuals
(the initial population) randomly. Repeat for $l = 1, 2, \ldots$ until a stopping criterion is
met: $D^{Se}_{l-1}$ <- Select $Se \leq N$ individuals from $D_{l-1}$ according to a selection
method; $\rho_l(x) = \rho(x|D^{Se}_{l-1})$ <- Estimate the probability distribution of an
individual being among the selected individuals; $D_l$ <- Sample $N$ individuals (the new
population) from $\rho_l(x)$." The population size is $N$ and the selected count satisfies
$Se \leq N$, which is the report's $\mu \leq N$ under a different letter.

Two details further down carry the rest of the paragraph. The univariate factorisation
$p_t(x) = \prod_i p_{t,i}(x_i)$ is equation (4) on page 458,
$p_l(x; \theta^l) = \prod_{i=1}^{n} p_l(x_i; \theta_i)$. The maximum-likelihood frequency
estimate is the sentence immediately after it: "$\theta^l$ is recalculated every generation by
its maximum likelihood estimation, i.e. $\hat\theta^l_{ijk} = N^{l-1}_{ijk} / N^{l-1}_{ij}$", a
count of cases divided by a total, which is the report's
$p_{t,i}(s) = \frac{1}{\mu}\sum_{x \in S_t}\mathds{1}[x_i = s]$ in the parent-free case.
"Recalculated every generation" is the report's re-estimation from scratch.

### Statement 5 of 6 - Metaheuristic Optimisation Methods, UMDA parameters (`chapters/Metaheuristic Optimisation Methods.tex:507`)

> Three parameters govern the exploration--exploitation balance
> \cite{muhlenbein1996,larranaga2001}: the population size $N$ (estimate accuracy and drift
> resistance), the selection ratio $\mu / N$ (selection pressure, with $\mu = N/2$ a common
> default), and a margin that keeps marginals away from the exact extremes so a value absent
> from one generation's selection is not lost forever \cite{chen2010analysis} [...]

**Verdict: CONFIRMED. No edit.** Read the citation brackets carefully before judging this one,
because the sentence does three things and only two of them are charged to this key. The margin
is cited to `chen2010analysis`, separately, at the clause where it appears. `larranaga2001`
carries $N$ and the selection ratio.

$N$ and $\mu/N$ are both parameters of the source's own experiment, Section 4.2, page 463: "a
population of 2000 individuals ($N = 2000$), from which a subset of the best 1000 are selected
($S_e = 1000$) to estimate the probability, and the elitist approach was chosen". That is
$\mu/N = 1/2$ exactly, which is the report's "$\mu = N/2$ a common default", corroborated by
use rather than by prescription, but corroborated in a paper by the book's own editor, which is
about as good as "common default" claims get. The same sentence supports "keeping the top $\mu$
individuals by fitness" as truncation ("the best 1000 are selected") and the report's elitism
sentence four lines later ("always the best individual is included for the next population and
1999 individuals are simulated").

Worth noting rather than fixing: the parenthetical "(estimate accuracy and drift resistance)"
is not supported by the supplied PDF, which never discusses drift. It does not need to be. The
drift claim is made and cited in full two paragraphs earlier at line 463, to
`shapiro2005drift`, `doerr2020sharp` and `witt2019upper`, and the parenthetical is a
back-reference to it, not a fresh claim. The one sentence in the supplied PDF that gestures at
the margin idea is on page 457, "We assume that every $\theta_{ijk}$ is greater than zero", the
positivity condition that Laplace smoothing enforces, but it is stated there as a modelling
assumption on Bayesian network parameters, not as a tunable parameter, so it is not strong
enough to carry the margin clause and the clause does not lean on it.

### Statement 6 of 6 - Related Work, EDAs on Cloud Allocation (`chapters/Related work.tex:21`)

> Estimation of Distribution Algorithms (EDAs) replace the crossover and mutation operators of
> evolutionary algorithms with a probabilistic model that is fitted to selected individuals
> from the current population and then sampled to generate new candidate
> solutions~\cite{hauschild2011, larranaga2001}.

**Verdict: CONFIRMED. No edit.** Same support as Statement 1, and here the match is closer
still because the report names the two operators the source names. Section 2.1, page 455:
"This avoids the use of crossing or mutation operators." Crossing is crossover. "Fitted to
selected individuals from the current population" is Figure 1's estimate step, whose object is
$D^{Se}_{l-1}$, the selected subset, and the source's own gloss for the estimated quantity is
"the probability distribution of an individual being among the selected individuals".

**Not verified in this pass:** the `series`, `address` and `doi` fields of the bib entry, which
neither reference in the supplied PDF prints; and `hauschild2011`, `pelikan2002survey` and
`chen2010analysis`, the co-cited keys on four of the six statements. Only the Bengoetxea et al.
PDF was supplied.

---

## `kirkpatrick1983` (ref. 52)

**Source:** S. Kirkpatrick, C. D. Gelatt, Jr., M. P. Vecchi, "Optimization by Simulated
Annealing", *Science* (New Series) 220(4598), 13 May 1983, pp. 671-680. DOI
10.1126/science.220.4598.671.

**Checked:** 2026-08-14, against the full article (JSTOR scan of the printed pages).

**Bib entry: correct, no edit.** Journal, volume, issue, pages and year all match the
article's own running head, "13 May 1983, Volume 220, Number 4598", and the page range
671-680. Title and author order match the byline. One cosmetic difference left alone: the
byline reads "C. D. Gelatt, Jr." and the bib omits the suffix, which is how most
bibliographies of this paper render it, and changing it risks a name-parse change in a
file I cannot compile locally.

**Summary of the pass:** five statements checked, four confirmed as written, one edited.
The edit removes `kirkpatrick1983` from the citation on the 80 % initial-acceptance rule,
because that rule is in the van Laarhoven and Aarts book and not in this article. No prose
was changed anywhere, and this also amends the earlier `vanlaarhoven1987` entry above.

### Statement 1 of 5 - Implementation, Simulated Annealing (`chapters/Implementation.tex:97`)

> The implementation applies the standard Metropolis acceptance rule and geometric cooling
> introduced in Chapter~\ref{ch:metaheuristics} \citep{kirkpatrick1983}, cooling once per
> \emph{temperature step} of $50$ candidate moves

**Verdict: CONFIRMED. No edit.**

Both named ingredients are the paper's own. The Metropolis rule, p. 672: "The case
Delta-E > 0 is treated probabilistically: the probability that the configuration is
accepted is P(Delta-E) = exp(-Delta-E/k_B T)", and the transfer out of physics on the same
page: "Using the cost function in place of the energy and defining configurations by a set
of parameters {x_i}, it is straightforward with the Metropolis procedure to generate a
population of configurations of a given optimization problem at some effective
temperature."

Geometric cooling, p. 675: "For the annealing schedule we chose to start at a high
'temperature,' T_0 = 10 [...] then cool exponentially, T_n = (T_1/T_0)^n T_0, with the
ratio T_1/T_0 = 0.9." That is exactly T_{k+1} = alpha . T_k with alpha = 0.9, the form
given in Chapter 4, so "introduced in Chapter 4" points at the right rule.

*The 50-move temperature step is not attributed to the paper and does not need to be.* It
is this thesis's own number. The paper's per-temperature budget is far larger but the same
in kind, p. 675: "At each temperature enough flips are attempted that either there are ten
accepted flips per circuit on the average (for this case, 50,000 accepted flips at each
temperature), or the number of attempts exceeds 100 times the number of circuits."

### Statement 2 of 5 - Simulated Annealing (`chapters/Metaheuristic Optimisation Methods.tex:213`)

> Simulated Annealing (SA) \cite{kirkpatrick1983,cerny1985} is a single-solution search
> method that improves one candidate step by step. It is inspired by the metallurgical
> process of annealing

**Verdict: CONFIRMED. No edit.**

This is the paper being cited for being the paper, and the annealing analogy is its central
device. p. 672: "Experiments that determine the low-temperature state of a material, for
example, by growing a single crystal from a melt, are done by careful annealing, first
melting the substance, then lowering the temperature slowly, and spending a long time at
temperatures in the vicinity of the freezing point", carried into the algorithm on the same
page: "The simulated annealing process consists of first 'melting' the system being
optimized at a high effective temperature, then lowering the temperature by slow stages
until the system 'freezes' and no further changes occur."

Single-solution and step-by-step, p. 680: "Like most iterative improvement schemes, the
Metropolis algorithm proceeds in small steps from one configuration to the next, but the
temperature keeps the algorithm from getting stuck by permitting uphill moves." The
following sentence in the thesis, that early uphill moves prevent getting permanently
stuck, is cited to `talbi2009` but is equally this paper's, p. 673: "the procedure need not
get stuck since transitions out of a local optimum are always possible at nonzero
temperature."

*The `cerny1985` co-citation is endorsed by this paper itself.* Note 29, p. 680: "V. Cerny
has described an approach to the traveling salesman problem similar to ours in a manuscript
received after this article was submitted for publication." Worth having ready if anyone
asks why two references sit on one sentence: the joint attribution is Kirkpatrick et al.'s
own.

### Statement 3 of 5 - Working Principle (`chapters/Metaheuristic Optimisation Methods.tex:226`)

> At each step, SA takes the current solution $s$ and generates a slightly modified
> ``neighbour'' $s'$, then computes the difference in objective value
> \cite{kirkpatrick1983}: \[\Delta E = F(s') - F(s)\]

**Verdict: CONFIRMED. No edit.**

p. 672: "In each step of this algorithm, an atom is given a small random displacement and
the resulting change, Delta-E, in the energy of the system is computed." The rename from
energy to objective value is the paper's own instruction two paragraphs later, "Using the
cost function in place of the energy", so both the quantity and the symbol Delta-E come
from the source.

*Notation point, not an error.* The paper writes exp(-Delta-E/k_B T) with Boltzmann's
constant and the thesis writes e^{-Delta E / T}. Dropping k_B is the standard optimisation
convention and the paper licenses it where it defines the effective temperature, p. 672:
"This temperature is simply a control parameter in the same units as the cost function."
The acceptance rule itself is cited to `metropolis1953` on the next line, which is where it
belongs.

### Statement 4 of 5 - The Cooling Schedule (`chapters/Metaheuristic Optimisation Methods.tex:246`)

> The temperature schedule controls how fast SA transitions from broad exploration to
> focused local search, and SA's performance is highly sensitive to
> it~\cite{kirkpatrick1983,talbi2009,vanlaarhoven1987}

**Verdict: CONFIRMED. No edit.**

The first half is stated twice. p. 673: "Gross features of the eventual state of the system
appear at higher temperatures; fine details develop at lower temperatures." Restated in the
conclusions, p. 680: "The temperature distinguishes classes of rearrangements, so that
rearrangements causing large changes in the objective function occur at high temperatures,
while the small changes are deferred until low temperatures."

The sensitivity half is the paper's headline experiment rather than an aside. Annealed, the
5000-gate partitioning problem gave two chips of 353 and 321 pins. Quenched, p. 675: "If,
instead of slowly cooling, one were to start from a random partition and accept only flips
that reduce the objective function (equivalent to setting T = 0 in the Metropolis rule),
the result is chips with approximately 700 pins (several such runs led to results with 677
to 730 pins). Rapid cooling results in a system frozen into a metastable state far from the
optimal configuration." That is about a factor of two on the objective from the schedule
alone. p. 673 adds the diagnostic form: a large specific heat "can be used in the
optimization context to indicate that freezing has begun and hence that very slow cooling
is required".

*Spreadsheet note.* The tracking sheet still carries this statement in its older wording,
"it is the most important design decision when applying the algorithm". That superlative was
already removed under `talbi2009` (Statement 7 there) and confirmed removed under
`vanlaarhoven1987` (Statement 2 there). The sentence in the tree is the corrected one and is
what I checked, so there is nothing outstanding here. This paper would not have supported
the superlative either: p. 680 lists the schedule as one of four needed ingredients and puts
the difficulty elsewhere, "Inventing the most effective sets of moves and deciding which
factors to incorporate into the objective function require insight into the problem being
solved and may not be obvious."

### Statement 5 of 5 - The Cooling Schedule (`chapters/Metaheuristic Optimisation Methods.tex:254`)

> The starting temperature $T_{\max}$ is commonly calibrated so that typical worsening moves
> are initially accepted around $80\,\%$ of the
> time~\cite{~~kirkpatrick1983,~~vanlaarhoven1987}

**Verdict: NOT IN THIS SOURCE. Edited, one bib key removed, prose unchanged.**

The article sets no target acceptance ratio, and where it does fix an initial temperature it
fixes a much hotter one. p. 675: "we chose to start at a high 'temperature,' T_0 = 10, where
essentially all proposed circuit flips are accepted." Essentially all is not 80 %. The
travelling-salesman section is qualitative in the same direction, p. 680: "The temperature
at which segments flow about freely will be of order N^{1/2}." The summary offers only trial
and error, p. 680: the schedule "may be developed by trial and error for a given problem, or
may consist of just warming the system until it is obviously melted, then cooling in slow
stages until diffusion of the components ceases." The one 0.9 on p. 675 is the cooling ratio
T_1/T_0 and not an acceptance rate, which is a trap for a quick reader.

*Why the earlier pass concluded the opposite, and why this supersedes it.* The
`vanlaarhoven1987` entry confirmed the co-citation from the book's p. 59: "Kirkpatrick et al.
propose the following empirical rule [...] If the acceptance ratio chi [...] is less than a
given value chi_0 (in [KIR82] chi_0 = 0.8), double the current value of c_0." The book's key
there is **[KIR82]**, a 1982 Kirkpatrick et al. item, not [KIR83], and neither the 0.8 nor
the doubling procedure appears anywhere in the 1983 *Science* article. Whatever [KIR82] is,
`kirkpatrick1983` resolves to the *Science* article and the bib entry carries its DOI, so an
examiner who follows the citation lands on a paper that says "essentially all". The number is
real and the credit to Kirkpatrick et al. is real, but the source that documents both is the
book, so the book now carries the sentence alone.

*What the edit costs:* nothing. `kirkpatrick1983` still carries four statements, two of them
in this same subsection, and the 80 % figure keeps a source that provably contains it. The
thesis's own calibration, e^{-Delta-bar/T_0} = 0.80 at `chapters/Implementation.tex:104`, is
presented there as this work's choice and cites nobody, so it is untouched and still
consistent with the chapter.

**Not verified in this pass:** `cerny1985`, `metropolis1953`, `talbi2009`, `hajek1988` and
`vanlaarhoven1987`, the co-cited keys on these sentences. `talbi2009` and `vanlaarhoven1987`
have their own entries above. Only the Kirkpatrick PDF was supplied here.

---

## `dorigo1996` (ref. 25)

**Source:** M. Dorigo, V. Maniezzo, A. Colorni, "Ant System: Optimization by a Colony of
Cooperating Agents", *IEEE Transactions on Systems, Man, and Cybernetics, Part B: Cybernetics*,
vol. 26, no. 1, pp. 29-41, February 1996. DOI 10.1109/3477.484436.

**Checked:** 2026-08-14, against the full paper PDF.

**Bib entry: correct, no change.** Author list and order match the byline (Dorigo, Maniezzo,
Colorni). Title, journal, volume 26, number 1, pages 29-41 and year 1996 all match the running
head and first page of the PDF.

**Summary of the pass:** seven statements checked, all seven confirmed on the substance. Two
citation-list edits made, both because a clause is carried by `dorigo2004` rather than by this
paper: the pheromone-update equation is written in the modern evaporation-rate convention
(line 367), and the "classic application domain" claim is a statement about eight subsequent
years of literature (line 576). No prose changed anywhere.

### Statement 1 of 7 - Metaheuristic Optimisation Methods, ACO opening (`chapters/Metaheuristic Optimisation Methods.tex:319`)

> Ant Colony Optimisation (ACO) \cite{dorigo1996,dorigo2004} is a population-based method in
> which artificial ants cooperate to build solutions by following and reinforcing promising
> paths, mimicking the foraging behaviour of real colonies: ants deposit pheromone as they
> walk, others preferentially follow stronger trails, and shorter paths accumulate pheromone
> faster, so the colony converges on good routes without any individual having a global view.

**Verdict: CONFIRMED. No edit.** Every clause is in Section I, most of them nearly verbatim.

- Population-based. Third bullet of the Introduction: "It is a *population based approach*."
- Deposit while walking. "A moving ant lays some pheromone (in varying quantities) on the
  ground, thus marking the path by a trail of this substance."
- Preferential following. "an ant encountering a previously laid trail can detect it and decide
  with high probability to follow it, thus reinforcing the trail with its own pheromone."
- Shorter paths accumulate faster. "This causes the quantity of pheromone on the shorter path
  to grow faster than on the longer one."
- Convergence without a global view. "how almost blind animals like ants could manage to
  establish shortest route paths from their colony to feeding sources and back", and the
  outcome, "The final result is that very quickly all ants will choose the shorter path."

One point worth having ready for the defence, not an error. In the algorithm the paper settles
on, *ant-cycle*, trail is laid after the tour is complete, not while walking: "when it completes
a tour, it lays a substance called trail on each edge (i,j) visited". The two variants that do
deposit step by step, *ant-density* and *ant-quantity*, are the ones Table I shows to be worse,
because they "use local information" and their "search is not directed by any measure of the
final result achieved". The report's sentence is safe from this because the colon scopes
"deposit pheromone as they walk" to "the foraging behaviour of real colonies", which is exactly
the paper's own framing of that clause, and the report's own update rule at line 366 states the
end-of-tour timing explicitly.

### Statement 2 of 7 - Metaheuristic Optimisation Methods, ACO opening (`chapters/Metaheuristic Optimisation Methods.tex:328`)

> First demonstrated on the Travelling Salesman Problem \cite{dorigo1996}, ACO has become one of
> the most widely applied metaheuristics for routing and sequencing problems \cite{dorigo2004}.

**Verdict: CONFIRMED. No edit.** Abstract: "We apply the proposed methodology to the classical
Traveling Salesman Problem (TSP), and report simulation results." Section II opens by saying so
in the paper's own words: "We decided to use the well-known traveling salesman problem [26] as
benchmark, in order to make the comparison with other heuristic approaches easier." The whole
of Sections II to VI is the TSP, and the other problems in Section VII (ATSP, QAP, JSP) are
presented as evidence of generality *after* it.

Note the citation split in this sentence, which is the pattern the fix at line 576 was made to
match: the TSP demonstration is charged to this paper, the "most widely applied" claim to
`dorigo2004`. Only the first half is this paper's to carry.

If an examiner presses on "first": the earliest AS-on-TSP results are not in this 1996 journal
paper but in the conference and thesis work it supersedes, which it lists itself as "Preliminary
results, obtained on small-scale problems, have been presented in [6], [7], and [12], [13]",
that is Colorni, Dorigo and Maniezzo at ECAL 1991 and Dorigo's 1992 PhD thesis. The report's
claim is that ACO was first demonstrated on the TSP, which is true, and it cites the paper of
record for that demonstration. The honest answer if asked is that the 1991-92 work came first
and this is its journal form.

### Statement 3 of 7 - Metaheuristic Optimisation Methods, Solution Construction (`chapters/Metaheuristic Optimisation Methods.tex:338`)

> \[ P_{ij}^{k} = \frac{\tau_{ij}^{\alpha} \cdot \eta_{ij}^{\beta}}{\sum_{l \in \mathcal{A}^{k}}
> \tau_{il}^{\alpha} \cdot \eta_{il}^{\beta}} \]
> where $\mathcal{A}^k$ is the set of nodes still allowed for ant $k$, $\tau_{ij}$ is the
> pheromone level on edge $(i,j)$, and $\eta_{ij}$ is a heuristic desirability, typically
> inverse distance $\eta_{ij} = 1 / d_{ij}$ \cite{dorigo1996}.

**Verdict: CONFIRMED. No edit.** This is the paper's **Equation (4)** term for term, page 31:
p_ij^k(t) = [tau_ij(t)]^alpha [eta_ij]^beta / sum_{k in allowed_k} [tau_ik(t)]^alpha
[eta_ik]^beta for j in allowed_k, and 0 otherwise.

- The allowed set. "where allowed_k = {N-tabu_k}", the towns not yet in the ant's tabu list.
  The report's $\mathcal{A}^k$ is the same object under a different letter, and the report's
  omission of the "0 otherwise" branch is not a loss, since it states that the denominator
  "normalises over the allowed nodes, so the $P^k_{ij}$ form a probability distribution on
  $\mathcal{A}^k$", which assigns zero mass outside it by construction.
- Inverse distance. "We call *visibility* eta_ij the quantity 1/d_ij." Verbatim.
- The exponents. "alpha and beta are parameters that control the relative importance of trail
  versus visibility", which is the report's "balance learned preference against heuristic
  knowledge". The report's gloss that high beta "prefers short edges regardless of pheromone"
  is the paper's own limiting case: "setting alpha = 0, the trail level is no longer considered,
  and a stochastic greedy algorithm with multiple starting points is obtained."

Correction to the working notes, not to the report: the transition rule is Equation (4), not
Equation (1). Equation (1) is the trail update quoted under Statement 4.

### Statement 4 of 7 - Metaheuristic Optimisation Methods, The Pheromone Update (`chapters/Metaheuristic Optimisation Methods.tex:366`)

> Once all ants have completed their tours, evaporation and deposit are combined into a single
> update \cite{dorigo1996,dorigo2004}:
> \[ \tau_{ij}(t+1) = (1 - \rho) \cdot \tau_{ij}(t) + \sum_{k=1}^{m} \Delta\tau_{ij}^{k} \]
> where $\rho \in (0, 1)$ is the evaporation rate.

**Verdict: CONFIRMED as mathematics, with `dorigo2004` added to the citation.** This is the one
statement of the seven that is not a literal restatement of the source, and the reason is a
notation convention that has flipped since 1996.

The paper's **Equation (1)**, page 31, is tau_ij(t+n) = rho * tau_ij(t) + Delta tau_ij, and its
rho is the *persistence*, not the evaporation: "where rho is a coefficient such that (1 - rho)
represents the evaporation of trail between time t and t+n". Section IV repeats it in the
parameter list: "rho: trail persistence, 0 <= rho < 1 (1 - rho can be interpreted as trail
evaporation)". The report multiplies by (1 - rho) and calls rho the evaporation rate, so the
report's rho is the paper's 1 - rho. The two equations are the same map under that substitution,
but a reader checking the report against the 1996 paper alone would find the symbol used the
other way round, and the report's tuned rho = 0.3 would read as heavy evaporation in one
convention and light in the other.

The form the report actually writes, with (1 - rho) and rho as the evaporation rate, is the
convention of Dorigo and Stutzle's 2004 book, which is already cited three times in the same
subsection and is already in the bibliography. Adding it to this citation makes the equation
attributable exactly as written, and costs one key. **Edit applied:** `\cite{dorigo1996}` ->
`\cite{dorigo1996,dorigo2004}` at line 367. No prose changed, and the equation is right as it
stands, so nothing downstream moves. The code agrees with the report and not with the 1996
symbol: `pheromone *= (1.0 - rho)` in `EV_routing/algorithms/ant_colony.py:445`, with the tuned
rho = 0.3 stated at `chapters/Implementation.tex:182`.

Two further details, both carried and neither needing an edit.

- The sum over ants is the paper's **Equation (2)**, Delta tau_ij = sum_{k=1}^{m} Delta
  tau_ij^k, with m the total number of ants.
- "Once all ants have completed their tours" is the ant-cycle timing exactly: "After n
  iterations all ants have completed a tour, and their tabu lists will be full; at this point
  for each ant k the value of L_k is computed and the values Delta tau_ij^k are updated". The
  report indexes the update by iteration, t+1, where the paper indexes by ant move, t+n, because
  in the paper a cycle is n moves. Same event, different clock.

Worth knowing for the defence: the m-ant sum in this display is the generic Ant System update,
not the update this thesis runs. The implementation deposits from a single ant per iteration,
alternating iteration-best and global-best, which `chapters/Implementation.tex:182` states
plainly and which the variants paragraph at line 386 sets up. The methods chapter is describing
the canonical rule before narrowing to the variant, which is the right order, but the question
"your equation sums over m ants and your code deposits from one" has an answer and it is in the
implementation chapter.

### Statement 5 of 7 - Metaheuristic Optimisation Methods, The Pheromone Update (`chapters/Metaheuristic Optimisation Methods.tex:374`)

> \[ \Delta\tau_{ij}^{k} = \begin{cases} \dfrac{Q}{L_k} & \text{if ant } k \text{ used edge }
> (i,j) \text{ in its tour} \\ 0 & \text{otherwise} \end{cases} \]
> where $L_k$ is the total cost of ant $k$'s tour, so better solutions exert a stronger influence
> on future iterations \cite{dorigo1996}, and $Q$ is a constant scaling every deposit equally,
> leaving the learning signal in the $1/L_k$ ratio alone (fixed at $Q = 1$ here).

**Verdict: CONFIRMED. No edit.** The strongest of the seven, and the report's own gloss is the
paper's explanation rather than an inference from the formula.

The display is **Equation (3)**, page 31: Delta tau_ij^k = Q/L_k "if kth ant uses edge (i,j) in
its tour (between time t and t+n)", 0 otherwise, "where Q is a constant and L_k is the tour
length of the kth ant". Both branches and both symbols match.

"Better solutions exert a stronger influence" is the paper's stated reason for preferring
ant-cycle over the two rejected variants, page 33: "Ant-cycle uses global information, that is,
its ants lay an amount of trail which is proportional to how good the solution produced was. In
fact, ants producing shorter paths contribute a higher amount of trail than ants whose tour was
poor."

The parenthetical about Q is supported twice over, which is more than it needs. The paper's own
parameter study dropped Q from Table I for exactly the report's reason: "Parameter Q is not
shown because its influence was found to be negligible." And the code matches the report's
"fixed at Q = 1 here": `delta = 1.0 / update_cost` in
`EV_routing/algorithms/ant_colony.py:447`, with no Q factor at all, which is Q = 1.

One scope note. The paper writes "tour length" where the report writes "total cost of ant k's
tour", because in this thesis L_k is the weighted objective value rather than a distance. That
is a deliberate generalisation to the EV objective and the surrounding text makes it explicit,
so it is not an overstatement of the source.

### Statement 6 of 7 - Metaheuristic Optimisation Methods, variants (`chapters/Metaheuristic Optimisation Methods.tex:386`)

> Variants differ in how reinforcement is applied: the original Ant System \cite{dorigo1996}
> lets all ants deposit, while Ant Colony System \cite{dorigo1997} restricts the offline deposit
> to the best ant.

**Verdict: CONFIRMED. No edit.** The half charged to this paper is Equation (2) again, the sum
running k = 1 to m over the whole colony, and step 4 of the formal algorithm on page 32 confirms
it procedurally: "For every edge (i,j), For k := 1 to m do", accumulating Delta tau_ij^k from
every ant. The word "original" is right as well, since this is the paper that names the method
Ant System.

Two things to have ready, neither of which contradicts the sentence.

- The paper also introduces an *elitist* variant, Section V-C, in which the best-so-far tour is
  reinforced by an extra e * Q/L*, and the parameter set it finally recommends includes e = 8:
  "given a good parameter setting (for instance alpha = 1, beta = 5, rho = 0.5, Q = 100, e = 8)".
  This does not weaken "lets all ants deposit", because the elitist term is added on top of the
  m-ant sum rather than replacing it, but "the original Ant System has no elitism" would be the
  wrong thing to say if asked, and the report does not say it.
- The word "offline" in the ACS half is doing real work and is correct. ACS also applies a local
  update on each edge as it is traversed, so "restricts *deposit*" without the qualifier would
  be too strong. That half belongs to `dorigo1997` and was not checked in this pass.

### Statement 7 of 7 - Matching Algorithms to Problems (`chapters/Metaheuristic Optimisation Methods.tex:573`)

> Its pheromone model is indexed by edges (the same unit in which route cost accrues), and
> routing has been ACO's classic application domain \cite{dorigo2004} since its first
> demonstration on the TSP \cite{dorigo1996}.

**Verdict: CONFIRMED for the clause this paper carries, with `dorigo2004` added for the clause
it does not.** The sentence makes two claims and the citation sat at the end of both.

- Edge-indexed pheromone. Carried outright, and it is the paper's central data structure:
  "Let tau_ij(t) be the *intensity of trail* on edge (i,j) at time t", deposited per edge in
  Equation (3) and read per edge in Equation (4).
- First demonstration on the TSP. Carried, same evidence as Statement 2.
- "Routing has been ACO's classic application domain." Not this paper's claim to make. It is a
  statement about what happened to the method after 1996, and if anything the 1996 paper pushes
  the other way: Section VII is an argument for generality *beyond* routing, applying AS to the
  quadratic assignment and job-shop scheduling problems, and the Introduction sells robustness
  as the headline property. Dorigo and Stutzle 2004 is the source that surveys the intervening
  literature and is already used for the identical claim at line 330.

**Edit applied:** the sentence now reads "routing has been ACO's classic application domain
\cite{dorigo2004} since its first demonstration on the TSP \cite{dorigo1996}", splitting the two
citations at the clause boundary in the same pattern already used at lines 328-331. No wording
changed, only the placement of one key.

**Not verified in this pass:** `dorigo2004`, `dorigo1997` and `stutzle2000`, the co-cited keys
in this subsection, and `schneider2014` on the EV-adaptation paragraph. Only the Dorigo,
Maniezzo and Colorni 1996 PDF was supplied.
