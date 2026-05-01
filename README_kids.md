# A Guide to This Project — Written for Everyone

> This is a friendly explanation of the code in this folder. You do not need to know anything about computers or maths to follow along. We will build up the ideas step by step, like a story.

---

## What Is This Project About?

Imagine you have two really hard puzzles to solve.

**Puzzle 1 — The Electric Car Delivery Problem:**
A single electric car needs to drive around the city of San Francisco and drop off packages at 75 different houses. The car has a battery that can run out, so it also needs to stop at charging stations along the way. The goal is to plan the best possible route — one that uses as little time, energy, and money as possible.

**Puzzle 2 — The Cloud Computer Scheduling Problem:**
A company has 10 computers (called "servers") and 50 jobs that need to be done. The computers are all different — some are fast, some are slow, some use a lot of electricity, some use very little. The goal is to decide which job goes on which computer so that all the jobs get done quickly while using as little electricity as possible.

Both puzzles are hard because there are millions and millions of possible answers to try. You cannot check every single one — it would take forever. So instead, we use clever tricks called **metaheuristics** to find a very good answer in a reasonable amount of time.

---

## The Three Algorithms We Use for Cloud Scheduling

The project now uses **three different algorithms** to solve the cloud scheduling puzzle, and then compares their results. Think of it like three different people trying to solve the same jigsaw puzzle in their own way, and then seeing who does better.

### Algorithm 1: Simulated Annealing

This is inspired by how metals cool and harden. When you heat metal very hot and then let it cool down slowly, the atoms have time to settle into a strong arrangement. The algorithm does the same thing with solutions.

**How it works:**
- Start with one fairly good answer (built using a simple rule).
- Make a small random change to it.
- If the new answer is better, keep it. If it's worse, *maybe* keep it anyway — more likely to do so early on, less likely later.
- Slowly become more picky over time (the "cooling" part).
- If stuck for too long, briefly warm up again to escape being trapped (the "reheating" part).

Think of it like a hiker searching for the tallest mountain. At first they wander freely. Gradually they settle down and fine-tune their position.

---

### Algorithm 2: Genetic Algorithm (GA)

This is inspired by evolution and natural selection. Instead of moving one solution around, it works with a whole **population** of solutions — like a group of 50 people, each with their own answer to the puzzle. The best ones "breed" to create a new generation.

**How it works:**
1. **Start** with 50 different answers (one built cleverly, the rest random).
2. **Judge** all 50 answers: score each one using the same formula as always (less electricity + faster jobs = better score).
3. **Select parents** using a tournament: randomly pick 3 answers from the group and keep the best one. Do this twice to get two "parents."
4. **Crossover** (like having children): for each job, randomly pick which parent's assignment the child inherits. This mixes the good parts of both parents.
5. **Mutate** (like random DNA changes): for each job, with a small probability (about 2%), randomly move it to a different server. This prevents the population from all looking the same.
6. **Elitism**: always keep the 2 best answers from the previous generation unchanged. You never want to accidentally lose a great solution.
7. **Repeat** for 3,000 generations.

The key insight: if one parent has jobs 1–25 well-assigned and another parent has jobs 26–50 well-assigned, their child might inherit both good parts and do even better than either parent.

---

### Algorithm 3: UMDA — Univariate Marginal Distribution Algorithm

This is the most mathematically sophisticated algorithm. Instead of moving solutions around or mixing them, it **learns a probability model** of what good solutions look like and then **samples** (randomly generates) new solutions from that model.

Think of it like this: after studying 50 really good chefs, you notice that Chef #3 always uses olive oil, Chef #7 always uses garlic, and so on. You build up a "recipe" that captures the patterns of good chefs. Then you generate a new chef who follows those patterns.

**How it works:**
1. **Start** with 100 different answers (one built cleverly, the rest random).
2. **Judge** all 100 answers.
3. **Select the best 50** (the top 50%).
4. **Learn the pattern**: for each job, count which server the best solutions tend to put it on. Build a probability table — for example, "job 7 goes to server 4 about 70% of the time" and "job 7 goes to server 2 about 20% of the time."
5. **Generate 100 new answers** by sampling from this probability table — each new answer follows the learned patterns but with some randomness.
6. **Always keep** the single best solution ever found and include it in the next generation, so you never "forget" a great answer.
7. **Repeat** for 1,500 generations.

The clever part: the model automatically figures out which server is best for each job based on which combinations worked well in the past.

---

### Why Three Algorithms?

Using three different algorithms lets us answer important research questions:
- Which algorithm finds the best solution?
- Which algorithm is most consistent (low spread between best and worst runs)?
- Which algorithm converges fastest?
- Is there a meaningful improvement over the simple greedy heuristic?

---

## Three Baselines for Comparison

In addition to the three "smart" algorithms, the code also runs three simple **baselines** — ways of assigning jobs that use no intelligence at all. These give us a reference point.

| Baseline | What it does |
|---|---|
| **Greedy FFD** | Sorts jobs from biggest to smallest, then places each one on the most-loaded server that still has room. Smart but no searching. |
| **Round-Robin** | Assigns jobs in a cycle: job 1 → server 1, job 2 → server 2, ..., job 11 → server 1 again. No intelligence. |
| **Random** | Assigns each job to a completely random server. The worst possible approach. |

If the smart algorithms barely beat the greedy baseline, that tells us the greedy approach is already quite good. If they beat it by a lot, the search was worth it.

---

## The Two Puzzles in Detail

### Puzzle 1: The Electric Car Delivery Problem (EV Routing)

**Where is the code?** [EV_routing/](EV_routing/)

#### The Setup

We are in San Francisco. There is one electric car starting at a central garage (called the "depot"). It needs to visit **75 customer locations** and come back to the depot at the end. Along the way, it can stop at **30 charging stations** when its battery is getting low.

The car has:
- A battery that holds **20 kWh** of electricity.
- A consumption rate of **0.50 kWh per kilometre**.
- A constant speed of **50 km/h**.
- Charging stations each have their own price and charging speed.

#### What the code is trying to minimise

The code scores each possible route using a formula that adds up several things:

| What | How much it matters |
|---|---|
| Total distance driven | 1× |
| Total time spent (driving + charging) | 10× (time is very important!) |
| Total electricity used | 2× |
| Total money spent charging | 20× |
| Running out of battery (a big penalty!) | 10,000× |
| Visiting a place that does not exist | 5,000× |

A lower score is better.

#### How it builds the starting route

The code in [EV_routing/tools/initial_solution.py](EV_routing/tools/initial_solution.py) uses a simple "nearest neighbour" strategy:

1. Start at the depot.
2. Always drive to the nearest customer you haven't visited yet.
3. If the battery is getting low (below 50%), find the nearest charging station and stop there first.
4. Keep going until all customers are visited, then return to the depot.

#### How it tweaks the route (the 8 moves)

The code in [EV_routing/tools/neighborhoods.py](EV_routing/tools/neighborhoods.py) knows 8 different ways to make a small change to the route:

1. **Swap customers** — switch the positions of two customer stops.
2. **Relocate a customer** — remove a stop and put it somewhere else.
3. **Two-opt** — reverse a section of the route (untangles crossed paths).
4. **Insert a charging station** — add a charging stop.
5. **Remove a charging station** — delete a charging stop.
6. **Replace a charging station** — swap one charging station for another.
7. **Move a charging station** — put a charging stop in a different position.
8. **Repair a battery problem** — if the car would run out of battery between two stops, insert a charging station in between.

---

### Puzzle 2: The Cloud Computer Scheduling Problem

**Where is the code?** [Cloud scheduling/](Cloud%20scheduling/)

#### The Setup

A company has **10 servers** (computers). They are all different — like a collection of old and new laptops:

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
- A **priority** — Low, Medium, or High. High-priority jobs are weighted most heavily in the score.

#### What the code is trying to minimise

| What | How much it matters |
|---|---|
| Total electricity used (idle + workload) | 1× |
| Total slowness (especially for high-priority jobs) | 1× |
| CPU overload penalty | 1,000× |
| Memory overload penalty | 5× |

**Interesting tension:** Packing all jobs onto fewer servers saves idle electricity (fewer machines switched on), but makes those servers slow and congested. Spreading jobs across many servers is fast but wastes electricity on idle machines. The algorithm has to find the right balance.

#### How it builds the starting assignment

The code in [Cloud scheduling/tools/initial_solution.py](Cloud%20scheduling/tools/initial_solution.py) uses a strategy called **First-Fit Decreasing (FFD)**:

1. Sort all 50 jobs from biggest (most CPU-hungry) to smallest.
2. For each job, find the server that is already the most loaded but still has enough room. Put the job there.
3. This packs jobs tightly, like fitting big boxes into a truck before small ones.

#### How it tweaks the assignment (the 5 moves)

The code in [Cloud scheduling/tools/neighborhoods.py](Cloud%20scheduling/tools/neighborhoods.py) knows 5 ways to make a small change. These are used by Simulated Annealing and (implicitly) inform the search direction:

1. **Reassign a random job** — move any job to a different randomly chosen server.
2. **Swap two jobs** — swap which servers two jobs are on.
3. **Rescue from an overloaded server** — find the most overloaded server and move one of its jobs somewhere else.
4. **Consolidate** — move a job from the least-loaded server to the most-loaded one (packs tightly → saves idle power).
5. **Spread** — move a job from the most-loaded server to the least-loaded one (reduces congestion → makes jobs faster).

---

## The Files and What They Do

### Top-level files

| File | What it does |
|---|---|
| [run.py](run.py) | The main launcher. Type a command here to run either puzzle or both. |
| [Makefile](Makefile) | A shortcut so you can type `make ev` or `make cloud` instead of the full command. |
| [README.md](README.md) | The short, technical README for people who already know the subject. |
| [README_kids.md](README_kids.md) | This file! The friendly guide for everyone. |

### EV Routing files

| File | What it does |
|---|---|
| [EV_routing/main.py](EV_routing/main.py) | Entry point for EV routing. Runs the algorithm and saves results. |
| [EV_routing/algorithms/simmulated_annealing.py](EV_routing/algorithms/simmulated_annealing.py) | The Simulated Annealing loop for routing. |
| [EV_routing/tools/data_loader.py](EV_routing/tools/data_loader.py) | Reads the data files. |
| [EV_routing/tools/objective.py](EV_routing/tools/objective.py) | Calculates the route score. |
| [EV_routing/tools/feasibility.py](EV_routing/tools/feasibility.py) | Checks a route is structurally valid. |
| [EV_routing/tools/initial_solution.py](EV_routing/tools/initial_solution.py) | Builds the first route using nearest-neighbour. |
| [EV_routing/tools/neighborhoods.py](EV_routing/tools/neighborhoods.py) | The 8 ways to tweak a route. |
| [EV_routing/tools/experiment.py](EV_routing/tools/experiment.py) | Runs the algorithm 10 times and collects results. |
| [EV_routing/tools/plot.py](EV_routing/tools/plot.py) | Creates convergence graphs. |

### Cloud Scheduling files

| File | What it does |
|---|---|
| [Cloud scheduling/main.py](Cloud%20scheduling/main.py) | Entry point. Runs all algorithms, prints tables, saves plots and CSVs. |
| [Cloud scheduling/algorithms/simulated_annealing.py](Cloud%20scheduling/algorithms/simulated_annealing.py) | Simulated Annealing loop for scheduling. |
| [Cloud scheduling/algorithms/genetic_algorithm.py](Cloud%20scheduling/algorithms/genetic_algorithm.py) | **NEW** — Genetic Algorithm with tournament selection, uniform crossover, and per-gene mutation. |
| [Cloud scheduling/algorithms/umda.py](Cloud%20scheduling/algorithms/umda.py) | **NEW** — UMDA (EDA): learns a probability model of good solutions and samples from it. |
| [Cloud scheduling/algorithms/baselines.py](Cloud%20scheduling/algorithms/baselines.py) | **NEW** — Greedy FFD, Round-Robin, and Random one-shot baselines. |
| [Cloud scheduling/tools/data_loader.py](Cloud%20scheduling/tools/data_loader.py) | Reads the task spreadsheet and creates the 10 servers. |
| [Cloud scheduling/tools/objective.py](Cloud%20scheduling/tools/objective.py) | Calculates electricity + slowness + overload penalties. |
| [Cloud scheduling/tools/feasibility.py](Cloud%20scheduling/tools/feasibility.py) | Checks every job is assigned to a real server. |
| [Cloud scheduling/tools/initial_solution.py](Cloud%20scheduling/tools/initial_solution.py) | Greedy FFD, round-robin, and random constructors. |
| [Cloud scheduling/tools/neighborhoods.py](Cloud%20scheduling/tools/neighborhoods.py) | The 5 ways to tweak a job assignment (used by SA). |
| [Cloud scheduling/tools/experiment.py](Cloud%20scheduling/tools/experiment.py) | Generic harness: runs any algorithm 10 times and collects results. |
| [Cloud scheduling/tools/plot.py](Cloud%20scheduling/tools/plot.py) | Convergence graph, bar comparison chart, comparison table, CSV export. |

---

## How to Run the Code

Open your terminal in the project root folder and type one of these commands:

```bash
# Run both puzzles one after the other
uv run run.py

# Run only the electric car puzzle
uv run run.py ev

# Run only the cloud scheduling puzzle
uv run run.py cloud
```

Or if you have `make` installed:

```bash
make all    # both puzzles
make ev     # electric car only
make cloud  # scheduling only
```

---

## What Happens When You Run the Cloud Scheduling Code

Running `main.py` (or `uv run run.py cloud`) does all of this:

### Step 1 — Problem summary
It prints how many tasks and servers there are, and whether the total demand fits within the total capacity.

### Step 2 — One quick diagnostic run
It runs Simulated Annealing once and shows you:
- The final score
- How much electricity the assignment uses
- How slow the jobs are
- Whether any servers are overloaded
- A little bar chart showing how many jobs each server got

### Step 3 — Full experiments (10 runs × 6 algorithms = 60 runs)
It runs each of the six algorithms 10 times, each time with a different random seed (like shuffling a deck of cards differently). For SA, GA, and UMDA it prints a line for each run showing the cost and whether it was feasible.

### Step 4 — Comparison table
It prints one big table with all six algorithms side by side:

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
- **Best** — the best score seen across 10 runs (lower is better)
- **Average** — the typical score
- **Worst** — the worst score
- **Std Dev** — how much the results vary (0 = always identical; large = unpredictable)
- **Feasible** — how many of the 10 runs produced a solution where no server was overloaded
- **Avg Time** — how long each run took in seconds

### Step 5 — Plots
Three image files are saved to the `figures/` folder:
- **convergence_all_algorithms.png**: A line graph showing how each algorithm's best score improved over time. SA, GA, and UMDA are drawn in different colours with a shaded band showing the spread across 10 seeds.
- **sa_convergence.png**: The same graph but for SA only.
- **algorithm_comparison_bar.png**: A horizontal bar chart comparing all six algorithms on their Best, Average, and Worst scores.

### Step 6 — CSV files
Two spreadsheet files are saved to the `results/` folder:
- **results_per_seed.csv**: Every single run (algorithm + seed number + all scores).
- **results_summary.csv**: One row per algorithm with the averages.

You can open these in Excel for further analysis.

---

## A Quick Glossary

| Word | What it means |
|---|---|
| **Metaheuristic** | A general-purpose method for solving hard puzzles. It does not guarantee the perfect answer, but finds a very good one quickly. |
| **Simulated Annealing (SA)** | Metaheuristic inspired by metal cooling: starts adventurous, gradually becomes careful. Works with one solution at a time. |
| **Genetic Algorithm (GA)** | Metaheuristic inspired by evolution: maintains a population of solutions that breed and mutate over generations. |
| **UMDA (EDA)** | Metaheuristic that learns a statistical model of good solutions and generates new ones by sampling from that model. |
| **Population** | In GA and UMDA: the group of candidate solutions maintained each generation (like a class of 50 or 100 students each with their own answer). |
| **Crossover** | In GA: mixing the server assignments of two parent solutions to create a child solution. Like combining two recipes. |
| **Mutation** | In GA: randomly changing one or more server assignments in a solution. Prevents all solutions from becoming identical. |
| **Elitism** | Automatically keeping the best solution(s) in the next generation, so you never accidentally discard a great answer. |
| **Probability model** | In UMDA: a table of numbers showing how likely each task is to go on each server. Built by learning from the best solutions seen so far. |
| **Objective function** | The formula that gives a score to a solution. Lower is better. |
| **Feasible** | A solution that follows all the rules (no server is overloaded). |
| **Infeasible** | A solution that breaks a rule. The code allows infeasible solutions temporarily but gives them a big penalty score. |
| **Neighbourhood / Move** | A small change to the current solution. |
| **Temperature** | In SA: a number that controls how willing the algorithm is to accept a worse solution. High = adventurous. Low = careful. |
| **Cooling rate** | In SA: how quickly the temperature drops each step. Here it drops to 99.5% of its previous value each round. |
| **Reheat** | In SA: temporarily raise the temperature again if the algorithm gets stuck. |
| **Tournament selection** | In GA: pick 3 random solutions from the population, keep the best one as a parent. |
| **Truncation selection** | In UMDA: simply keep the top 50% of solutions and discard the rest. |
| **Laplace smoothing** | In UMDA: add a tiny number to all probability counts so no option ever gets a probability of zero. |
| **Seed** | A starting number for the random number generator. Using the same seed gives exactly the same sequence of random choices — useful for repeating an experiment. |
| **Baseline** | A simple, non-searching reference algorithm. Used to measure how much the metaheuristic actually improves on. |
| **Greedy FFD** | First-Fit Decreasing: sort jobs by size, fill the most-loaded server that still fits each job. Fast but no searching. |
| **Convergence plot** | A graph showing the best score found so far, plotted over time. A healthy graph goes steeply down at first, then flattens. |
| **Server** | A computer in a data centre that runs jobs for other people. |
| **Depot** | In EV routing: the starting and ending point for the electric car. |
| **kWh** | Kilowatt-hour. A unit of energy — how you measure electricity use at home. |

---

## The Bigger Picture

This project is part of a Master's thesis. The research question is: **how do Simulated Annealing, Genetic Algorithm, and UMDA compare when applied to cloud resource allocation?**

By solving the same problem with three fundamentally different metaheuristics and three simple baselines, we can answer:
- How good are the solutions from each algorithm?
- How consistent is each algorithm across repeated runs?
- How quickly does each algorithm converge?
- Is a metaheuristic significantly better than the greedy starting point?

This kind of comparative study helps researchers and engineers decide which algorithms are worth using in real cloud computing environments.

---

*Made with curiosity and a lot of patience.*
