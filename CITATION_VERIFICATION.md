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
