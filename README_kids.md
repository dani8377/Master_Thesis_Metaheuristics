# A Guide to This Project — Written for Everyone

> This is a friendly explanation of the code in this folder. You do not need to know
> anything about computers or mathematics to follow along. We will build up the ideas
> step by step, like a story.

---

## What Is This Project About?

Imagine you have two really hard puzzles to solve.

**Puzzle 1 — The Cloud Computer Scheduling Problem:**
A company has 10 computers (called "servers") and 50 jobs that need to be done.
The computers are all different — some are fast, some are slow, some use a lot of
electricity, some use very little. The goal is to decide which job goes on which
computer so that all the jobs get done quickly while using as little electricity as possible.

**Puzzle 2 — The Electric Car Delivery Problem:**
A single electric car needs to drive around the city of San Francisco and drop off
packages at 75 different houses. The car has a battery that can run out, so it also
needs to stop at charging stations along the way. The goal is to plan the best possible
route — one that uses as little time, energy, and money as possible.

Both puzzles are hard because there are millions and millions of possible answers to try.
You cannot check every single one — it would take forever. So instead, we use clever
tricks called **metaheuristics** to find a very good answer in a reasonable amount of time.

---

## Puzzle 1: The Cloud Computer Scheduling Problem

**Where is the code?** [Cloud_scheduling/](Cloud_scheduling/)

### The Setup

A company has **10 servers** (computers). They are all different — like a collection of
old and new laptops:

| Server type | CPU power | Memory | Idle electricity | Efficiency |
|---|---|---|---|---|
| Small old server | Low | 32 GB | 60 Watts | Uses 20% more energy than it should |
| Medium server | Medium | 65 GB | 95–110 Watts | Average |
| Large modern server | High | 131 GB | 180–190 Watts | Uses less energy |
| Huge powerful server | Very high | 262 GB | 250 Watts | Very efficient |

There are **50 jobs** (tasks) that need to be done. Each job has:
- How much **CPU** it needs.
- How much **memory** it needs.
- How much **electricity** it draws while running.
- How long it takes to respond (its **latency**).
- A **priority** — Low, Medium, or High. High-priority jobs matter three times more
  than medium-priority jobs, and four times more than low-priority jobs.

### What the Code is Trying to Minimise

The code scores each possible assignment using a formula that adds up four things:

| What | Symbol | Weight |
|---|---|---|
| Total electricity used (idle + workload) | Energy E(X) | 1× (balanced mode) |
| Total slowness, especially for high-priority jobs | Latency L(X) | 1× (balanced mode) |
| CPU overload penalty | Max(0, load − capacity) | 10× per normalised unit |
| Memory overload penalty | Max(0, load − capacity) | 10× per normalised unit |

**The key tension:** packing all jobs onto fewer servers saves idle electricity (fewer
machines switched on), but makes those servers slow and congested. Spreading jobs across
many servers is fast but wastes electricity on idle machines. The algorithm has to find
the right balance.

### The Three "Focus Modes"

You can tell the code which objective matters most by choosing a focus mode:

| Mode | What it prioritises |
|---|---|
| `balanced` (default) | Energy and latency equally |
| `performance` | Speed above all — energy is a minor concern |
| `eco` | Power saving above all — latency is a minor concern |

### How it Builds the Starting Assignment

The code uses a strategy called **First-Fit Decreasing (FFD)**:

1. Sort all 50 jobs from biggest (most CPU-hungry) to smallest.
2. For each job, find the server that is already the most loaded but still has enough room.
3. Put the job there. This packs jobs tightly, like fitting big boxes into a truck before small ones.

### How it Tweaks the Assignment (the 5 Moves)

The code knows 5 ways to make a small change to an assignment (used by Simulated Annealing):

1. **Reassign a random job** — move any job to a different randomly chosen server.
2. **Swap two jobs** — swap which servers two jobs are on.
3. **Rescue from an overloaded server** — find the most overloaded server and move one of its jobs elsewhere.
4. **Consolidate** — move a job from the least-loaded server to the most-loaded one (saves idle power).
5. **Spread** — move a job from the most-loaded server to the least-loaded one (reduces congestion).

---

## The Three Algorithms for Cloud Scheduling

We use **three different algorithms** to solve the cloud scheduling puzzle, and then
compare their results. Think of it like three different people solving the same puzzle
in their own way, and then seeing who does better.

### Algorithm 1: Simulated Annealing

Inspired by how metals cool and harden. When you heat metal very hot and then let it
cool down slowly, the atoms have time to settle into a strong arrangement. The algorithm
does the same thing with solutions.

**How it works:**
- Start with one fairly good answer (built using the FFD rule above).
- Make a small random change to it (one of the 5 moves).
- If the new answer is better, keep it. If it's worse, *maybe* keep it anyway —
  more likely to do so early on, less likely later.
- Slowly become more picky over time (the "cooling" part).
- If stuck for too long, briefly warm up again to escape being trapped (the "reheating" part).

Think of it like a hiker searching for the tallest mountain. At first they wander freely.
Gradually they settle down and fine-tune their position.

**The starting temperature** is set automatically by sampling 400 random moves from the
starting solution and finding a temperature at which about 80% of worse moves would be
accepted. This clever trick means the algorithm self-calibrates to the problem.

### Algorithm 2: Genetic Algorithm (GA)

Inspired by evolution and natural selection. Instead of moving one solution around, it
works with a whole **population** of 50 solutions — like a group of 50 people each with
their own answer to the puzzle. The best ones "breed" to create a new generation.

**How it works:**
1. **Start** with 50 different answers (one built cleverly using FFD, the rest random).
2. **Judge** all 50 answers using the same formula.
3. **Select parents** using a tournament: randomly pick 3 answers from the group and
   keep the best one. Do this twice to get two "parents."
4. **Crossover** (mixing): for each job, randomly pick which parent's assignment the
   child inherits. This mixes the good parts of both parents.
5. **Mutate**: for each job, with a small probability (~2%), randomly move it to a
   different server. This prevents the population from all looking the same.
6. **Elitism**: always keep the 2 best answers from the previous generation unchanged.
   You never want to accidentally lose a great solution.
7. **Repeat** for 3,000 generations.

The key insight: if one parent has jobs 1–25 well-assigned and another parent has
jobs 26–50 well-assigned, their child might inherit both good parts and do even better.

### Algorithm 3: UMDA — Univariate Marginal Distribution Algorithm

The most mathematically sophisticated algorithm. Instead of moving solutions around or
mixing them, it **learns a probability model** of what good solutions look like and then
**samples** (randomly generates) new solutions from that model.

Think of it like this: after studying 50 really good chefs, you notice that Chef #3
always uses olive oil, Chef #7 always uses garlic, and so on. You build up a "recipe"
that captures the patterns of good chefs. Then you generate a new chef who follows those patterns.

**How it works:**
1. **Start** with 100 different answers (one built cleverly, the rest random).
2. **Judge** all 100 answers.
3. **Select the best 50** (the top 50%).
4. **Learn the pattern**: for each job, count which server the best solutions tend to
   put it on. Build a probability table — for example, "job 7 goes to server 4 about
   70% of the time."
5. **Generate 100 new answers** by sampling from this probability table.
6. **Always keep** the single best solution ever found, so you never forget a great answer.
7. **Repeat** for 1,500 generations.

The algorithm also tracks how "uncertain" the model is using something called **entropy**
(a measure of randomness). High entropy = the model is still exploring broadly. Low
entropy = the model has learned strong preferences and is fine-tuning.

### Algorithm 4: Branch and Bound (B&B) — The Perfect Solver

This algorithm is not a metaheuristic — it is an **exact solver**. It systematically
explores every possible assignment of jobs to servers (like a very smart tree search),
pruning paths that cannot possibly lead to a better answer. Given enough time, it would
find the perfect solution.

The catch: the perfect solution for 50 jobs takes impossibly long to compute. So we
give it a **60-second time limit** and stop it early, reporting how far its best-found
answer is from the true optimum. This "optimality gap" lets us know how good the
metaheuristics are.

We use B&B primarily on a small 20-job, 4-server instance (small enough that it can
actually finish), and use the result to validate that the three metaheuristics find
near-optimal solutions on easy problems before trusting them on harder ones.

### Why Four Algorithms?

Using four fundamentally different algorithms lets us answer important research questions:
- Which algorithm finds the best solution?
- Which algorithm is most consistent (low spread between best and worst runs)?
- Which algorithm converges fastest?
- Is a metaheuristic significantly better than the simple greedy starting point?
- How close to optimal are the metaheuristics on small, exactly-solvable problems?

---

## Three Baselines for Comparison

In addition to the three "smart" algorithms, the code also runs three simple **baselines** —
reference strategies that use no search at all:

| Baseline | What it does | Notes |
|---|---|---|
| **Greedy FFD** | Sorts jobs from biggest to smallest, places each on the most-loaded server with room. Smart but no searching. | Deterministic — always finds the same answer. The starting point for SA and GA. |
| **Round-Robin** | Assigns jobs in a cycle: job 1 → server 1, job 2 → server 2, ..., job 11 → server 1 again. No intelligence. | Deterministic — because the answer is always identical, the code only runs it once instead of 10 times (running it more would just waste time). |
| **Random** | Assigns each job to a completely random server. The worst-case reference. | Different every run, almost always overloads servers. |

If the smart algorithms barely beat the greedy baseline, that tells us the greedy
approach is already very good. If they beat it by a lot, the search was worth it.

---

## Puzzle 2: The Electric Car Delivery Problem (EV Routing)

**Where is the code?** [EV_routing/](EV_routing/)

### The Setup

We are in San Francisco. There is one electric car starting at a central garage (called
the "depot"). It needs to visit **75 customer locations** and come back to the depot at
the end. Along the way, it can stop at **30 charging stations** when its battery is low.

The car has:
- A battery that holds **20 kWh** of electricity.
- A consumption rate of **0.50 kWh per kilometre**.
- A constant speed of **50 km/h**.
- Charging stations each have their own price and charging speed.

### What the Code is Trying to Minimise

| What | How much it matters |
|---|---|
| Total distance driven | 1× |
| Total time spent (driving + charging) | 10× |
| Total electricity used | 2× |
| Total money spent charging | 20× |
| Running out of battery (big penalty!) | 10,000× |
| Visiting a place that does not exist | 5,000× |

### How it Builds the Starting Route

The code uses a **nearest neighbour** strategy:

1. Start at the depot.
2. Always drive to the nearest customer you haven't visited yet.
3. If the battery is getting low (below 50%), find the nearest charging station first.
4. Keep going until all customers are visited, then return to the depot.

### How it Tweaks the Route (the 8 Moves)

1. **Swap customers** — switch the positions of two customer stops.
2. **Relocate a customer** — remove a stop and put it somewhere else.
3. **Two-opt** — reverse a section of the route (untangles crossed paths).
4. **Insert a charging station** — add a charging stop.
5. **Remove a charging station** — delete a charging stop.
6. **Replace a charging station** — swap one charging station for another.
7. **Move a charging station** — put a charging stop in a different position.
8. **Repair a battery problem** — if the car would run out between two stops, insert a charging station.

This problem uses Simulated Annealing only (one algorithm, not three).

---

## The Files and What They Do

### Top-Level Files

| File | What it does |
|---|---|
| [run.py](run.py) | The main launcher. Type a command here to run either puzzle or both. |
| [Makefile](Makefile) | A shortcut so you can type `make cloud` or `make ev` instead of the full command. |
| [README.md](README.md) | The technical README for people who know the subject. |
| [README_kids.md](README_kids.md) | This file! The friendly guide for everyone. |

### Cloud Scheduling Files

| File | What it does |
|---|---|
| [Cloud_scheduling/main.py](Cloud_scheduling/main.py) | Entry point. Runs all algorithms, prints tables, saves plots and CSVs. |
| [Cloud_scheduling/config.yaml](Cloud_scheduling/config.yaml) | **The one file you edit to change algorithm settings.** Population sizes, cooling rates, number of seeds — all here. |
| [Cloud_scheduling/BEGINNERS_GUIDE.md](Cloud_scheduling/BEGINNERS_GUIDE.md) | A step-by-step guide explaining which files to read first and in what order, to understand the code. |
| [Cloud_scheduling/algorithms/simulated_annealing.py](Cloud_scheduling/algorithms/simulated_annealing.py) | Simulated Annealing loop for scheduling. |
| [Cloud_scheduling/algorithms/genetic_algorithm.py](Cloud_scheduling/algorithms/genetic_algorithm.py) | Genetic Algorithm with tournament selection, uniform crossover, and per-gene mutation. |
| [Cloud_scheduling/algorithms/umda.py](Cloud_scheduling/algorithms/umda.py) | UMDA (EDA): learns a probability model of good solutions and samples from it. |
| [Cloud_scheduling/algorithms/baselines.py](Cloud_scheduling/algorithms/baselines.py) | Greedy FFD, Round-Robin, and Random one-shot baselines. |
| [Cloud_scheduling/algorithms/branch_and_bound.py](Cloud_scheduling/algorithms/branch_and_bound.py) | The exact solver (B&B). Used on small instances to measure optimality gaps. |
| [Cloud_scheduling/algorithms/branch_and_bound.py](Cloud_scheduling/algorithms/branch_and_bound.py) | Exact B&B solver (time-limited; gives optimality gap when stopped early). |
| [Cloud_scheduling/tools/config_loader.py](Cloud_scheduling/tools/config_loader.py) | Reads config.yaml into typed Python dataclasses. |
| [Cloud_scheduling/tools/data_loader.py](Cloud_scheduling/tools/data_loader.py) | Reads the task spreadsheet and creates the 10 servers. |
| [Cloud_scheduling/tools/objective.py](Cloud_scheduling/tools/objective.py) | Calculates electricity + slowness + overload penalties. The core formula. |
| [Cloud_scheduling/tools/feasibility.py](Cloud_scheduling/tools/feasibility.py) | Checks every job is assigned to a real server. |
| [Cloud_scheduling/tools/initial_solution.py](Cloud_scheduling/tools/initial_solution.py) | Greedy FFD, round-robin, and random constructors for initial assignments. |
| [Cloud_scheduling/tools/neighborhoods.py](Cloud_scheduling/tools/neighborhoods.py) | The 5 ways to tweak a job assignment (used by SA). |
| [Cloud_scheduling/tools/experiment.py](Cloud_scheduling/tools/experiment.py) | Generic harness: runs any algorithm N times and collects results. |
| [Cloud_scheduling/tools/plot.py](Cloud_scheduling/tools/plot.py) | Convergence graph, bar comparison chart, box plots, comparison table, CSV export. |

### EV Routing Files

| File | What it does |
|---|---|
| [EV_routing/main.py](EV_routing/main.py) | Entry point for EV routing. Runs the algorithm and saves results. |
| [EV_routing/algorithms/simmulated_annealing.py](EV_routing/algorithms/simmulated_annealing.py) | The Simulated Annealing loop for routing. |
| [EV_routing/tools/data_loader.py](EV_routing/tools/data_loader.py) | Reads the data files. |
| [EV_routing/tools/objective.py](EV_routing/tools/objective.py) | Calculates the route score. |
| [EV_routing/tools/feasibility.py](EV_routing/tools/feasibility.py) | Checks a route is structurally valid. |
| [EV_routing/tools/initial_solution.py](EV_routing/tools/initial_solution.py) | Builds the first route using nearest-neighbour. |
| [EV_routing/tools/neighborhoods.py](EV_routing/tools/neighborhoods.py) | The 8 ways to tweak a route. |
| [EV_routing/tools/experiment.py](EV_routing/tools/experiment.py) | Runs the algorithm N times and collects results. |
| [EV_routing/tools/plot.py](EV_routing/tools/plot.py) | Creates convergence graphs. |

---

## How to Run the Code

Open your terminal in the project root folder and type one of these commands:

```bash
# Run only the cloud scheduling puzzle (recommended first)
uv run run.py cloud

# Run only the electric car puzzle
uv run run.py ev

# Run both puzzles one after the other
uv run run.py
```

Or if you have `make` installed:

```bash
make cloud  # cloud scheduling only
make ev     # electric car only
make all    # both puzzles
```

---

## What Happens When You Run the Cloud Scheduling Code

Running `uv run run.py cloud` does all of this automatically:

### Step 1 — Problem Summary
Prints how many tasks and servers there are, and whether the total demand fits
within the total capacity.

### Step 2 — One Quick Diagnostic Run
Runs Simulated Annealing once and shows:
- The final score
- How much electricity the assignment uses
- How slow the jobs are
- Whether any servers are overloaded
- A little bar chart showing how many jobs each server got

### Step 3 — Full Experiments (10 runs × 6 algorithms = 60 runs)
Runs each of the six algorithms 10 times with different random seeds (like shuffling
a deck of cards differently). For SA, GA, and UMDA it prints a line for each run
showing the cost and whether it was feasible.

### Step 4 — Comparison Table
Prints one big table with all six algorithms side by side:

```
Algorithm                Best     Average     Worst   Std Dev   Feasible   Avg Time
Simulated Annealing   12345.67   12987.34   14023.11   456.78     10/10     4.52s
Genetic Algorithm     12501.23   13102.45   14501.67   612.34      9/10     5.13s
UMDA (EDA)            12789.01   13456.78   14678.90   512.34      9/10     4.87s
Greedy FFD (baseline) 15234.56   15234.56   15234.56     0.00     10/10     0.01s
Round-Robin (baseline)23456.78   23456.78   23456.78     0.00      0/10     0.00s
Random (baseline)     28901.23   31234.56   35678.90  2345.67      0/10     0.00s
```

The columns mean:
- **Best** — the best score seen across 10 runs (lower is always better)
- **Average** — the typical score
- **Worst** — the worst score
- **Std Dev** — how much results vary (0 = always identical; large = unpredictable)
- **Feasible** — how many of the 10 runs had no server overloaded
- **Avg Time** — how long each run took in seconds

### Step 5 — Statistical Test
Prints a table of pairwise Wilcoxon significance tests — a way of checking whether
the difference between two algorithms is real or just due to random chance.

### Step 6 — Plots
Five image files are saved to the `figures/` folder:
- **convergence_all_algorithms.png**: SA, GA, and UMDA improvement over time, overlaid.
- **metaheuristics_comparison.png**: Bar chart comparing SA/GA/UMDA + energy/latency breakdown.
- **boxplot_comparison.png**: Box plots with individual seed dots for all algorithms.
- **algorithm_comparison_bar.png**: All six algorithms compared on Best/Avg/Worst.
- Individual convergence plots per algorithm.

### Step 7 — CSV Files and Summary

Three files are saved to the `results/` folder:
- **results_per_seed.csv**: Every single run (algorithm + seed + all scores).
- **results_summary.csv**: One row per algorithm with the averages.
- **summary.md**: A human-readable text summary — the winner, a clean results table,
  energy vs latency breakdown, and key findings. **Read this first after a run!**

---

## A Quick Glossary

| Word | What it means |
|---|---|
| **Metaheuristic** | A general-purpose method for solving hard puzzles. Finds a very good answer quickly without guaranteeing perfection. |
| **Simulated Annealing (SA)** | Inspired by metal cooling: starts adventurous, gradually becomes careful. Works with one solution at a time. |
| **Genetic Algorithm (GA)** | Inspired by evolution: maintains a population of solutions that breed and mutate over generations. |
| **UMDA (EDA)** | Learns a statistical model of good solutions and generates new ones by sampling from that model. |
| **Population** | In GA and UMDA: the group of candidate solutions maintained each generation. |
| **Crossover** | In GA: mixing server assignments of two parent solutions to create a child. |
| **Mutation** | In GA: randomly changing one or more server assignments in a solution. |
| **Elitism** | Automatically keeping the best solution(s) in the next generation. |
| **Probability model** | In UMDA: a table showing how likely each task is to go on each server. |
| **Entropy** | In UMDA: a measure of model uncertainty. High = exploring broadly. Low = exploiting a near-fixed assignment. |
| **Objective function** | The formula that gives a score to a solution. Lower is always better here. |
| **Feasible** | A solution where no server is overloaded. |
| **Infeasible** | A solution that breaks a capacity rule. The code allows these temporarily but penalises them. |
| **Neighbourhood / Move** | A small change to the current solution. |
| **Temperature** | In SA: controls willingness to accept a worse solution. High = adventurous. Low = careful. |
| **Cooling rate** | In SA: how quickly the temperature drops (here: 99.5% of previous value each step). |
| **Reheat** | In SA: temporarily raise the temperature again if the algorithm gets stuck. |
| **Tournament selection** | In GA: pick 3 random solutions, keep the best one as a parent. |
| **Truncation selection** | In UMDA: simply keep the top 50% and discard the rest. |
| **Laplace smoothing** | In UMDA: add a tiny number (0.1) to all counts so no server ever gets zero probability. |
| **Seed** | A starting number for the random number generator. Same seed = same random choices = reproducible result. |
| **Baseline** | A simple, non-searching reference algorithm used to measure how much the metaheuristic actually helps. |
| **Greedy FFD** | First-Fit Decreasing: sort jobs by size, fill the most-loaded server that still fits each job. |
| **Convergence plot** | A graph showing the best score found so far, plotted over time. A healthy graph drops steeply then flattens. |
| **Server** | A computer in a data centre that runs jobs. |
| **Depot** | In EV routing: the starting and ending point for the electric car. |
| **kWh** | Kilowatt-hour — a unit of energy, the same one on your electricity bill. |

---

## The Bigger Picture

This project is part of a Master's thesis at DTU. The research question is:
**how do Simulated Annealing, Genetic Algorithm, and UMDA compare when applied
to cloud resource allocation?**

By solving the same problem with three fundamentally different metaheuristics and three
simple baselines, we can answer:
- How good are the solutions from each algorithm?
- How consistent is each algorithm across repeated runs?
- How quickly does each algorithm converge?
- Is a metaheuristic significantly better than the greedy starting point?

This kind of comparative study helps researchers and engineers decide which algorithms
are worth using in real cloud computing environments.

---

*Made with curiosity and a lot of patience.*
