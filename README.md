# NeuroJIT: Improving Just-In-Time Defect Prediction Using Neurophysiological and Empirical Perceptions of Modern Developers

This replication package contains the source code and data used in the paper *"NeuroJIT: Improving Just-In-Time Defect Prediction Using Neurophysiological and Empirical Perceptions of Modern Developers"* and the implementation of the commit understandability metrics calculator.

## Table of Contents

# NeuroJIT

`neurojit` is a python package that calculates the commit understandability features.

We provide `neurojit` as a standalone package for collecting commits with modified methods and calculating the commit understandability features.

## Structure

```bash
 src/neurojit
 ├── commit.py # The core module that contains the classes for the commit and its changes.
 ├── neurojit
 │  ├── __init__.py
 │  ├── cfg.py
 │  ├── halstead.py
 │  ├── metrics.py # The module that calculates the commit understandability features.
 │  └── rii.py
 └── tools
    ├── __init__.py
    ├── correlation.py # The module that calculates the correlation
    └── data_utils.py # The module that processes the data for JIT-SDP.
```

## Pre-requisites

- python 3.12+
- pip
- wheel

# The Replication Package

This repository includes all the scripts, data and trained models to reproduce the results of the paper. The replication package is structured as follows:

```bash
├── data
│  ├── dataset # see `Building Dataset`
│  ├── output # generated output from `jit_sdp.py`
│  ├── plots # generated plots
│  └── archives # zipped trained models (pickles) in our experiment
├── dist # neurojit wheel file
├── neurojit # neurojit source code, see `neurojit`
└── scripts # scripts for reproducing the results
```


## 0. Setup

- [rye](https://rye-up.com): We recommend to use `rye`, a hassle-free python package manager. After installing rye, run the following command to install all dependencies for the replication and `neurojit`.

    ```bash
    $ rye pin 3.12 # pin the python version you want to use
    $ rye sync # install all dependencies
    ```

    See [pyproject.toml](./pyproject.toml) for the list of dependencies.
- [Checkstyle](https://github.com/checkstyle/checkstyle/releases/): Save to root directory as checkstyle.jar for easy replication. For example,

    ```bash
    $ wget https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.15.0/checkstyle-10.15.0-all.jar -O checkstyle.jar
    ```
## 1. Building Dataset

To calculate the verification latency gap (i.e., average fixing time, gap), we slightly modified the code of the [ApacheJIT](https://github.com/hosseinkshvrz/apachejit) repository to create an apachejit dataset that includes a fixed_date, and constructed `data/dataset/apachejit_gap.csv`, which is composed of a total of 8 projects that include the gap.

Then, we calculated the HCC of the ApacheJIT commits using the `neurojit` package. Additionally, we calculated the `LT` for the ApacheJIT commits because the `LT` is a widely used metric in the literature.

```bash
data/dataset
├── apache_metrics_kamei.csv
├── apachejit_date.csv
├── apachejit_gap.csv
├── baseline  # LT added apachejit dataset (baseline)
│  ├── activemq.csv
│  ├── camel.csv
│  ├── ...
├── baseline.csv
├── commits   # Filtered commits
│  ├── activemq.csv
│  ├── ...
└── neurojit  
   ├── ...
```

### 1) Collecting the Changes and Contexts

```bash
$ python scripts/collect.py --help

 Usage: collect.py [OPTIONS] COMMAND [ARGS]...
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────╮
│ change-contexts            Save the change contexts for commits that modified existing methods           │
│ changes-and-contexts       Filter and collect change contexts for commits that modified existing methods │
│ prepare-data               Generate the gap added column in the apachejit dataset                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### (Option 1) From Scratch

To build the dataset from scratch (i.e., from `data/dataset/apachejit_date.csv`, which is the `fixed_date` added version`apachejit_total.csv` of ApacheJIT),

```bash
 Usage: collect.py prepare-data [OPTIONS]

 Generate the gap added column in the apachejit dataset

╭─ Options ─────────────────────────────────────────────────────────────────────────╮
│ --dataset-dir        PATH  Path to the dataset directory [default: data/dataset]  │
╰───────────────────────────────────────────────────────────────────────────────────╯
```

Then, to filter the commits that modified only existing methods (i.e., our target software changes) and collect corresponding modified methods (i.e., change contexts),

```bash
 Usage: collect.py changes-and-contexts [OPTIONS] PROJECT

 Filter and collect change contexts for commits that modified existing methods

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    project      TEXT  activemq|camel|cassandra|flink|groovy|hbase|hive|ignite [default: None] [required] │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --apachejit        TEXT  Path to ApacheJIT dataset [default: data/dataset/apachejit_gap.csv]               │
│ --commits-dir        PATH  Path to the commits directory [default: data/dataset/commits]                   │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### (Option 2) From Pre-filtered Commits

Or to save the change contexts for all commits that modified existing methods with pre-filtered commits (i.e., `data/dataset/commits`)

```bash
 Usage: collect.py change-contexts [OPTIONS] PROJECT

 Save the change contexts for commits that modified existing methods

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────╮
│ *    project      TEXT  [default: None] [required]                                        │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────╮
│ --commits-dir        PATH  Path to the commits directory [default: data/dataset/commits]  │
│ --help                     Show this message and exit.                                    │
╰───────────────────────────────────────────────────────────────────────────────────────────╯
```

`neurojit.commit.MethodChangesCommit` instances are saved to `data/cache/<project>/<commit_hash>.pkl`.

### 2) Computing commit understandability features

To compute the commit understandability features from the saved changes and its contexts (i.e., `MethodChangesCommit` instances),
```bash
python scripts/compute.py --help

 Usage: compute.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                                             │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                      │
│ --help                        Show this message and exit.                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ cuf                        Compute specific CUF metrics for a project                                                                                               │
│ cuf-all                    Compute all CUF for a project                                                                                                            │
│ lt                         Compute LT for apachejit_metrics                                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```



Additionally, to compute the `LT` for the baseline dataset,

```bash
 Usage: compute.py lt [OPTIONS] PROJECT

 Compute LT for apachejit_metrics

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    project      TEXT  Project name [default: None] [required]              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --save-dir                  PATH  [default: data/dataset/baseline]           │
│ --quiet       --no-quiet          Disable progress bar [default: no-quiet]   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 3) Filtering the Dataset

To filter the dataset for the JIT-SDP, run `scripts/filtering.ipynb`.

Or just use the pre-computed commit understandability features and baseline dataset in `data/dataset/filtered`.

## 2. Reproducing the Results

### Pre-analysis

To reproduce the pre-analysis results, i.e., the distribution of the dataset and the correlation between CUF and defect-inducing risks, run the `table-distribution` and `plot-hmap`. `plot-hmap` also generates the collinearity between features for RQ2.

```bash
$ python scripts/pre_analysis.py --help

 Usage: pre_analysis.py [OPTIONS] COMMAND [ARGS]...

╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ plot-corr                    [RQ1] Generate plots for Correlations between CUF and Defect-inducing Risks  │
│ plot-hmap                    [RQ2] Generate plots for Collinearity between Features                                │
│ table-distribution           Tabulate the distribution of the dataset                                              │
│ table-group-diff             [RQ1] Tabulate the group differences between buggy and clean commits for HCC          │
│ table-group-diff-projects    Tabulate the group differences between buggy and clean commits for HCC (each project) │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### RQ1: Does the understandability of commits have predictive power for defect-inducing commits?

```bash
$ python scripts/pre_analysis.py plot-corr

$ python scripts/pre_analysis.py table-group-diff
```

### RQ2: Does the understandability of commits provide exclusive information to predict defect-inducing commits?

To reproduce the results of RQ2, run just-in-time software defect prediction (JIT-SDP) on the our dataset with the commit understandability features and the baseline metrics model.

```bash
$ python scripts/jit_sdp.py --help

 Usage: jit_sdp.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                                             │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                      │
│ --help                        Show this message and exit.                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ actionable    Compute the ratios of actionable features for the baseline and combined models for the true positive samples in the 20 folds JIT-SDP                  │
│ tp-samples    Save TP samples as json                                                                                                                               │
│ train-test    Train and test the baseline/cuf/combined model with 20 folds Just-In-Time Software Defect Prediction (JIT-SDP)                                        │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


Then, to generate the set relationships between the cuf model and the baseline model,

```bash
$ python scripts/analysis.py plot-set-relationships --help

 Usage: analysis.py plot-set-relationships [OPTIONS] [BASELINE_JSON] [CUF_JSON]

 Generate plots for TPs predicted by baseline model only vs cuf model only

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│   baseline_json      [BASELINE_JSON]  [default: data/output/random_forest_baseline.json]    │
│   cuf_json           [CUF_JSON]       [default: data/output/random_forest_cuf.json]         │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --save-path        PATH  [default: data/plots/analysis/diff_plot.svg]                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```

### RQ3: Can the understandability of commits improve the performance of just-in-time defect prediction models?

To reproduce the results of RQ3, run the RF and XGBoost models with the baseline and baseline+CUF(combined)

```bash
$ python scripts/jit_sdp.py train-test random_forest combined 
$ python scripts/jit_sdp.py train-test xgboost baseline 
$ python scripts/jit_sdp.py train-test xgboost combined
```

You can  generate the table for performance comparison between models,

```bash
$ python scripts/analysis.py table-performances --help

 Usage: analysis.py table-performances [OPTIONS] JSON1 JSON2

 Generate table for performance comparison between models

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────╮
│ *    json1      PATH  [default: None] [required]                                                    │
│ *    json2      PATH  [default: None] [required]                                                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────╮
│ --fmt                    TEXT  [default: github]                                                    │
│ --quiet    --no-quiet          [default: no-quiet]                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

```bash
$ python scripts/analysis.py table-performances data/output/random_forest_baseline.json data/output/random_forest_combined.json

$ python scripts/analysis.py table-performances data/output/xgboost_baseline.json data/output/xgboost_combined.json
```


### Discussion: Toward More Actionable Guidance

To generate the actionable JIT-SDP results, run the `actionable` command.


Then, to tabulate the results,

```bash
$ python scripts/analysis.py table-actionable --help

 Usage: analysis.py table-actionable [OPTIONS] [PATH]

 Tabulate the results of the actionable features

╭─ Arguments ──────────────────────────────────────────────────╮
│   path      [PATH]  [default: data/output/actionable.csv]    │
╰──────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────╮
│ --fmt         TEXT  [default: github]                        │
╰──────────────────────────────────────────────────────────────╯
```
