# Human-centric Code Complexity (HCC) Metrics Calculator

This replication package contains the source code and data used in the paper *"The Impact of Understandability on Defect-inducing Risks of Software Changes"* and the implementation of the human-centric code complexity (HCC) metrics calculator, `hcc_cal`.

## Table of Contents

- [Human-centric Code Complexity (HCC) Metrics Calculator](#human-centric-code-complexity-hcc-metrics-calculator)
  - [Table of Contents](#table-of-contents)
- [`hcc_cal`](#hcc_cal)
  - [Structure](#structure)
  - [Pre-requisites](#pre-requisites)
  - [Installation](#installation)
  - [Building from Source](#building-from-source)
- [The Replication Package](#the-replication-package)
  - [0. Setup](#0-setup)
  - [1. Building Dataset](#1-building-dataset)
    - [1) Collecting the Changes and Contexts](#1-collecting-the-changes-and-contexts)
      - [(Option 1) From Scratch](#option-1-from-scratch)
      - [(Option 2) From Pre-filtered Commits](#option-2-from-pre-filtered-commits)
    - [2) Computing HCC Metrics](#2-computing-hcc-metrics)
  - [2. Reproducing the Results](#2-reproducing-the-results)
    - [Pre-analysis](#pre-analysis)
    - [RQ1: Do HCC metrics correlate with defect-inducing risk?](#rq1-do-hcc-metrics-correlate-with-defect-inducing-risk)
    - [RQ2: How do HCC metrics differ from existing JIT-SDP metrics?](#rq2-how-do-hcc-metrics-differ-from-existing-jit-sdp-metrics)
    - [RQ3: Can HCC metrics improve the performance of JIT-SDP models?](#rq3-can-hcc-metrics-improve-the-performance-of-jit-sdp-models)
    - [Discussion: More Actionable JIT-SDP with HCC metrics](#discussion-more-actionable-jit-sdp-with-hcc-metrics)

# `hcc_cal`

`hcc_cal` is a python package that calculates the human-centric code complexity (HCC) of a commit.

We provide `hcc_cal` as a standalone package for collecting commits with modified methods and calculating the HCC metrics.

## Structure

```bash
 src/hcc_cal
 ├── commit.py # The core module that contains the classes for the commit and its changes.
 ├── hcc
 │  ├── __init__.py
 │  ├── cfg.py
 │  ├── halstead.py
 │  ├── metrics.py # The module that calculates the HCC metrics.
 │  └── rii.py
 └── tools
    ├── __init__.py
    ├── correlation.py # The module that calculates the correlation
    └── data_utils.py # The module that processes the data for JIT-SDP.
```

## Pre-requisites

- python 3.10+
- pip
- wheel

## Installation

Currently, you can install `hcc_cal` via a .whl file. Download [hcc_cal-0.1.0-py3-none-any.whl](dist/hcc_cal-0.1.0-py3-none-any.whl) to your project and install it using pip wheel.

```bash
$ pip install hcc_cal-0.1.0-py3-none-any.whl
```

We will provide the package via PyPI in the future.

## Building from Source

Also, you can build the package from the source code via `rye`.

```bash
$ rye build --clean --wheel
```

# The Replication Package

This repository includes all the scripts, data and trained models to reproduce the results of the paper. The replication package is structured as follows:

```bash
├── data
│  ├── dataset # see `Building Dataset`
│  ├── output # generated output from `jit_sdp.py`
│  ├── plots # generated plots
│  └── archives # zipped trained models (pickles) in our experiment
├── dist # hcc_cal wheel file
├── hcc_cal # hcc_cal source code, see `hcc_cal`
└── scripts # scripts for reproducing the results
```


## 0. Setup

- [rye](https://rye-up.com): We recommend to use `rye`, a hassle-free python package manager. After installing rye, run the following command to install all dependencies for the replication and `hcc_cal`.

    ```bash
    $ rye pin 3.12 # pin the python version you want to use
    $ rye sync # install all dependencies
    ```

    See [pyproject.toml](./pyproject.toml) for the list of dependencies.
- [Checkstyle](https://github.com/checkstyle/checkstyle/releases/): Save to root directory as checkstyle.jar for easy replication. For example,

    ```bash
    $ wget https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.15.0/checkstyle-10.15.0-all.jar -O checkstyle.jar
    ```
- trained models: unzip the pickles.zip in the `data/archives` directory

    ```bash
    $ zip -s 0 data/archives/pickles.zip --out data/pickles.zip
    $ unzip data/pickles.zip -d data/pickles
    ```

## 1. Building Dataset

To calculate the verification latency gap (i.e., average fixing time, gap), we slightly modified the code of the [ApacheJIT](https://github.com/hosseinkshvrz/apachejit) repository to create an apachejit dataset that includes a fixed_date, and constructed `data/dataset/apachejit_gap.csv`, which is composed of a total of 8 projects that include the gap.

Then, we calculated the HCC of the ApacheJIT commits using the `hcc_cal` package. Additionally, we calculated the `LT` for the ApacheJIT commits because the `LT` is a widely used metric in the literature.

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
└── hcc   # HCC dataset
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

`hcc_cal.commit.MethodChangesCommit` instances are saved to `data/cache/<project>/<commit_hash>.pkl`.

### 2) Computing HCC Metrics

```bash
$ python scripts/compute.py hcc --help

 Usage: compute.py [OPTIONS] COMMAND [ARGS]...

╭─ Commands ──────────────────────────────────────────────────────╮
│ hcc                 Compute specific HCC metrics for a project  │
│ hcc-all             Compute all HCC metrics for a project       │
│ lt                  Compute LT for apachejit_metrics            │
╰─────────────────────────────────────────────────────────────────╯
```

To compute the HCC metrics from the saved changes and its contexts (i.e., `MethodChangesCommit` instances),

```bash
 Usage: compute.py hcc-all [OPTIONS] PROJECT

 Compute all HCC metrics for a project

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    project      TEXT  Project name [default: None] [required]                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --save-dir                              PATH  [default: data/dataset/hcc]                                      │
│ --quiet                   --no-quiet          Disable progress bar [default: no-quiet]                         │
│ --checkstyle-path                       TEXT  Path to checkstyle jar [default: checkstyle.jar]                 │
│ --xml-path                              TEXT  Path to checkstyle xml config [default: indentation_config.xml]  │
│ --checkstyle-cache-dir                  TEXT  Path to checkstyle cache [default: data/cache/checkstyle]        │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
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

Or just use the pre-computed HCC metrics and baseline dataset in `data/dataset/hcc` and `data/dataset/baseline`, respectively.

## 2. Reproducing the Results

### Pre-analysis

To reproduce the pre-analysis results, i.e., the distribution of the dataset and the correlation between HCC features and defect-inducing risks, run the `table-distribution` and `plot-hmap`. `plot-hmap` also generates the collinearity between features for RQ2.

```bash
$ python scripts/pre_analysis.py --help

 Usage: pre_analysis.py [OPTIONS] COMMAND [ARGS]...

╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ plot-corr                    [RQ1] Generate plots for Correlations between HCC Features and Defect-inducing Risks  │
│ plot-hmap                    [RQ2] Generate plots for Collinearity between Features                                │
│ table-distribution           Tabulate the distribution of the dataset                                              │
│ table-group-diff             [RQ1] Tabulate the group differences between buggy and clean commits for HCC          │
│ table-group-diff-projects    Tabulate the group differences between buggy and clean commits for HCC (each project) │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### RQ1: Do HCC metrics correlate with defect-inducing risk?

```bash
$ python scripts/pre_analysis.py plot-corr

$ python scripts/pre_analysis.py table-group-diff
```

### RQ2: How do HCC metrics differ from existing JIT-SDP metrics?

To reproduce the results of RQ2, run just-in-time software defect prediction (JIT-SDP) on the our dataset with the HCC metrics and the baseline metrics model.

```bash
$ python scripts/jit_sdp.py train-test --help

 Usage: jit_sdp.py train-test [OPTIONS] MODEL FEATURES

 Train and test the baseline/HCC/baseline+HCC model with 20 folds Just-In-Time Software Defect Prediction
 (JIT-SDP)

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    model         TEXT  Model to use: random_forest|xgboost [default: None] [required]                  │
│ *    features      TEXT  Feature set to use: baseline|HCC|baseline+HCC [default: None] [required]        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --smote           --no-smote               Use SMOTE for oversampling [default: smote]                   │
│ --display         --no-display             Display progress bar [default: no-display]                    │
│ --baseline-dir                       PATH  Baseline data directory [default: data/dataset/baseline]      │
│ --hcc-dir                            PATH  HCC data directory [default: data/dataset/hcc]                │
│ --output-dir                         PATH  Output directory [default: data/output]                       │
│ --save-model      --no-save-model          Save models [default: no-save-model]                          │
│ --load-model      --no-load-model          Load models [default: no-load-model]                          │
│ --save-dir                           PATH  Save directory [default: data/pickles]                        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

In RQ2, we used the `random_forest` model with the `baseline`, `HCC` features, and applied the `SMOTE` technique for oversampling.

```bash
$ python scripts/jit_sdp.py train-test random_forest baseline   # --load-model for loading the trained models from `data/pickles`
$ python scripts/jit_sdp.py train-test random_forest hcc    # --save-model for saving the trained models to `data/pickles`
```

Then, to generate the set relationships between the HCC model and the baseline model,

```bash
$ python scripts/analysis.py plot-set-relationships --help

 Usage: analysis.py plot-set-relationships [OPTIONS] [BASELINE_JSON] [HCC_JSON]

 Generate plots for TPs predicted by baseline model only vs HCC model only

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────╮
│   baseline_json      [BASELINE_JSON]  [default: data/output/random_forest_baseline.json]    │
│   hcc_json           [HCC_JSON]       [default: data/output/random_forest_hcc.json]         │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────╮
│ --save-path        PATH  [default: data/plots/analysis/diff_plot.svg]                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────╯
```

### RQ3: Can HCC metrics improve the performance of JIT-SDP models?

To reproduce the results of RQ3, run the RF and XGBoost models with the baseline and baseline+HCC features

```bash
$ python scripts/jit_sdp.py train-test random_forest baseline+hcc 
$ python scripts/jit_sdp.py train-test xgboost baseline 
$ python scripts/jit_sdp.py train-test xgboost baseline+hcc
```

Then, to generate the performance comparison radar charts between the baseline model and the baseline+HCC model,

```bash
$ python scripts/analysis.py plot-radars --help

 Usage: analysis.py plot-radars [OPTIONS] [RF_BASELINE] [RF_BASELINE_HCC]
                                [XGB_BASELINE] [XGB_BASELINE_HCC]

 Generate radar charts for performance comparison between models

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────╮
│   rf_baseline           [RF_BASELINE]       [default: data/output/random_forest_baseline.json]      │
│   rf_baseline_hcc       [RF_BASELINE_HCC]   [default: data/output/random_forest_baseline+hcc.json]  │
│   xgb_baseline          [XGB_BASELINE]      [default: data/output/xgboost_baseline.json]            │
│   xgb_baseline_hcc      [XGB_BASELINE_HCC]  [default: data/output/xgboost_baseline+hcc.json]        │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────╮
│ --save-dir        PATH  [default: data/plots/analysis]                                              │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

You can also generate the table version:

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
$ python scripts/analysis.py table-performances data/output/random_forest_baseline.json data/output/random_forest_baseline+hcc.json

$ python scripts/analysis.py table-performances data/output/xgboost_baseline.json data/output/xgboost_baseline+hcc.json
```


### Discussion: More Actionable JIT-SDP with HCC metrics

To generate the actionable JIT-SDP results,

```bash
 Usage: jit_sdp.py actionable [OPTIONS] MODEL

 Compute the ratios of actionable features for the baseline and baseline+HCC models for the true
 positive samples in the 20 folds JIT-SDP

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────╮
│ *    model      TEXT  Model to use: random_forest|xgboost [default: None] [required]                │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────╮
│ --smote           --no-smote               Use SMOTE for oversampling [default: smote]               │
│ --display         --no-display             Display progress bar [default: no-display]                │
│ --baseline-dir                       PATH  Baseline data directory [default: data/dataset/baseline]  │
│ --hcc-dir                            PATH  HCC data directory [default: data/dataset/hcc]            │
│ --output-dir                         PATH  Output directory [default: data/output]                   │
│ --load-model      --no-load-model          Load models [default: no-load-model]                      │
│ --pickles-dir                        PATH  Pickles directory [default: data/pickles]                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

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
