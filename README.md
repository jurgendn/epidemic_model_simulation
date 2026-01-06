# Epidemic Model Simulation (Graph-Based)

This repo implements (and partially prototypes) the graph-based epidemic modeling approach described in the report “Mô phỏng mô hình lan truyền dịch bệnh” (HUST – Applied Mathematics & Informatics, 2020).

[Report PDF](https://drive.google.com/file/d/1xAvo7zwlBNHZxxsiwgL30FlB6OCQ5aU1/view?usp=sharing)

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Neo4j](https://img.shields.io/badge/neo4j-graph%20database-008CC1.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-prototype-orange.svg)
![Contributions](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)

Instead of only using compartmental models (SI/SIR/SEIR), the report treats spread as a **time-varying influence process over a network** (patients + shared locations), and ranks “influential” patients per day using **PageRank**.

## Model summary (from the report)

### 1) Entities and graph construction

The report models the outbreak as a graph $G=(V,E)$.

- **Patient nodes**: each case is a node with attributes such as age group, symptom onset date, and announcement date.
- **Edges**: represent potential transmission influence (direct relationships).
- **Location nodes (optional but important)**: to connect otherwise fragmented patient-only graphs, location nodes (e.g., wards/communes) are added and connected to patients.
  - This encodes indirect links (shared environment) and “unknown source” links among co-located patients.

### 2) Handling missing symptom onset dates

The report highlights that onset dates are often missing. It defines

$$\Delta = (\text{onset date}) - (\text{last contact date})$$

and fits a distribution to observed $\Delta$ values (using Anderson–Darling for goodness-of-fit and MLE for parameters). Missing onset dates are then imputed by sampling $\Delta$.

### 3) Time-varying edge weights and PageRank

The report proposes a **daily weighted influence network**. Edge weights vary over time, peaking around symptom onset and decaying afterward. The weight combines:

- relationship-type strength,
- age-group mixing,
- intervention/media factors,
- (when using locations) a short surface-survival window (e.g., ~3 days) and an indirect transmission decay factor $\gamma$.

Each day $t$, PageRank is computed on the weighted network to identify the most “influential” cases at time $t$.

## What this repository currently implements

The code in [server/](server/) is a prototype pipeline to:

1) transform raw case CSV → relationship CSV,
2) load the graph into Neo4j,
3) export graph JSON for visualization (Sigma.js),
4) compute PageRank on the exported graph (in the notebook).

Important note: the full weighting scheme described in the report is **not fully implemented** in the checked-in scripts.

- [server/Generate data.ipynb](server/Generate%20data.ipynb) imputes missing onset dates with a simple heuristic (announcement date − 5 days) rather than the report’s fitted-$\Delta$ approach.
- [server/Graph.ipynb](server/Graph.ipynb) currently assigns **random edge weights** and computes PageRank from those weights.
- The “location node” extension and explicit intervention/media factors are not implemented in the scripts as-is.

## Repository layout

- [server/](server/): data prep + Neo4j import + analysis/export tooling
- [visualization/](visualization/): Sigma.js-based viewer reading `visualization/data.json`

Key files in [server/](server/):

- `data.csv`: raw case table (Vietnamese column names)
- `relation_new.csv`: processed edge list (also includes a `relationship` id column in this repo)
- `Generate data.ipynb`: builds an edge list from `data.csv`
- `Update DB.ipynb`: loads `relation_new.csv` into Neo4j (nodes + typed edges)
- `Graph.ipynb`: pulls Neo4j → igraph, computes PageRank, exports JSON
- `pass_igraph.py`: quick Neo4j → igraph → JSON export (clusters + colors)
- `test.py`: minimal Neo4j driver wrapper used by `pass_igraph.py`

## Quickstart

### Prerequisites

- Neo4j running locally (Bolt enabled) at `bolt://localhost:7687`
- Python 3 + packages:

```bash
pip install pandas numpy neo4j py2neo python-igraph
```

Security note: several scripts/notebooks use the default username/password `neo4j` / `123`. Update credentials before running against any non-local DB.

### End-to-end workflow

1) **(Optional) regenerate relationship CSV**

Open and run [server/Generate data.ipynb](server/Generate%20data.ipynb) to produce an edge list.

2) **Load into Neo4j**

Open and run [server/Update DB.ipynb](server/Update%20DB.ipynb). It creates:

- nodes labeled by age group (`G1`, `G2`, `G3`, `G4`)
- relationship types mapped from the `relationship` column:
  - `0` → `Unknown`
  - `1` → `Staff_Patience`
  - `2` → `Fellow`
  - `3` → `Relatives`
  - `4` → `Social`

3) **Export JSON for visualization**

Option A (notebook): run [server/Graph.ipynb](server/Graph.ipynb) and it writes `visualization/data.json`.

Option B (script):

```bash
cd server
python pass_igraph.py
```

4) **View**

Open [visualization/index.html](visualization/index.html). It reads `visualization/data.json`.

## JSON format written for Sigma.js

Both export paths create a Sigma.js-like JSON:

```json
{
  "nodes": [{
    "id": 0,
    "label": "BN416",
    "x": 0,
    "y": 0,
    "size": 2,
    "_color": "#34c0eb"
  }],
  "edges": [{
    "id": 0,
    "source": 0,
    "target": 1,
    "weight": 0.42,
    "type": "Relatives"
  }]
}
```

If you want the code to match the report more closely (time-dependent weights, location nodes, fitted onset imputation), the natural place to implement it is in [server/Graph.ipynb](server/Graph.ipynb) (edge weight function) plus the preprocessing stage that generates onset dates.
