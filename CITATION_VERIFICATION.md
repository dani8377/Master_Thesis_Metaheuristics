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
