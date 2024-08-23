# NeuroJIT Replication Package

Here is a guide on how to use the replication package of NeuroJIT. If you have any questions regarding the use of the package, feel free to contact us anytime via email at {fantasyopy, sparky}@hanyang.ac.kr.

## Structure of the Replication Package

The replication package consists of `data/dataset`, the core module `src/neurojit` and `scripts/` used to reproduce the results of the paper. The structure of the replication package is as follows:

```Shell
├── archive # zipped trained models (pickles) in our experiment
├── data
│  ├── dataset # see Dataset
│  ├── output # output of the experiments
│  └── plots  # plots generated in the experiments
├── dist # neurojit package distribution
├── Dockerfile
├── docker-compose.yml
├── src/neurojit # neurojit source code, see `neurojit`
└── scripts 
# main scripts
   ├── data_utils.py # data preprocessing and caching
   ├── calculate.py # calculate CUF and LT
   ├── pre_analysis.py # pre-analysis for CUF, Baseline and Dataset
   ├── jit_sdp.py # JIT-SDP training and evaluation
   ├── analysis.py # analysis after JIT-SDP training and evaluation
# utility
   ├── correlation.py # correlation analysis utility
   ├── environment.py # environment variables for the scripts
   ├── visualization.py # visualization utility
# for replication
   ├── commit_distribution.ipynb # commit distribution analysis for the dataset (external validity)
   ├── neurojit_cli.py # simple example of NeuroJIT usage 
   └── reproduce.sh # script to reproduce the key experimental results from the paper
```

### Dataset

We provide the dataset in the `data/dataset` directory. The dataset is structured as follows:

```Shell
data/dataset
├── apachejit_total.csv # original ApacheJIT dataset
├── apachejit_date.csv # ApacheJIT dataset with bug_fix_date
├── apachejit_gap.csv # gap between commit date and bug_fix_date in ApacheJIT dataset
├── apache_metrics_kamei.csv # JIT metrics in ApacheJIT dataset
├── baseline.csv # LT added and filtered ApacheJIT dataset
├── baseline/  
│  ├── activemq.csv
│  ├── ...
├── combined/   # Combined of CUF and baseline dataset 
├── commits/   # Filtered commits (only method changes commits)
└── cuf/      # CUF calculated and filtered ApacheJIT dataset
```

If you want to build the dataset from scratch, you can use the following scripts:

```Shell
 (1) Usage: python scripts/data_utils.py COMMAND [ARGS]...

 Data preprocessing and caching

╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ combine-dataset   Combine the baseline and CUF datasets                                                                       │
│ filter-commits    Filter method changes for each commit in the dataset and save methods to cache                              │
│ prepare-data      ApacheJIT(+bug_date column) dataset                                                                         │
│ save-methods      Save the change contexts for commits that modified existing methods                                         │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

 (2) Usage: python scripts/calculate.py COMMAND [ARGS]...

 Calculate metrics for CUF and Baseline

╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ cuf-all       Calculate all CUF for a project                                                                                 │
│ cuf-metrics   Calculate specific CUF metrics for a project                                                                    │
│ lt            Calculate LT for apachejit_metrics(baseline)                                                                    │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

It takes very long time to build the dataset from scratch because it requires to compare the all methods in each commit when `filter-commits` and CUF calculation requires to envoke the checkstyle for each file in the commit. Therefore, we provide the pre-built dataset in the `data/dataset` directory.

### `neurojit` 

The structure of the core module `neurojit` is as follows:​

```Shell
src/neurojit
├── commit.py # commit filtering and saving
├── cuf
│  ├── cfg.py # control flow graph
│  ├── halstead.py # halstead metrics
│  ├── metrics.py  # cuf calculation (method and commit level)
│  └── rii.py # II feature calculation using checkstyle
└── tools
    └── data_utils.py # jit-sdp data split utility (chronological order, verification latency, concept drifts)
```

## Setup

1. Hardware/Software Requirements

    We've tested the replication package on machines with the following specifications:
    - Windows 11
      - CPU: 
      - RAM:
    - Ubuntu 20.04.6
      - Device: NVIDIA DGX Station V100, 2019
      - CPU: Intel Xeon(R) E5-2698 v4 @ 2.20GHz
      - RAM: 256GB
    - MacOS 14.6.1
      - Device: MacBook Air M2, 2022
      - CPU: Apple M2
      - RAM: 24GB
    - Docker version 4.33.0 
2. Docker Installation

    To install Docker, please refer to the official Docker installation guide at https://docs.docker.com/get-docker/.
    
    Download and unzip the replication package from the following link: [NeuroJIT Replication Package](zenodo_link).

## Usage

### Docker Container Setup

After navigating to the project folder, execute the following commands in the terminal to build and run the Docker container.

```Shell
 $ docker-compose up --build -d
 ...
  ✔ Container neurojit-ase  Started
```
 
 To access the container, execute the following command:

```Shell
 $ docker exec -it neurojit-ase bash

 root@31d:/app# scripts/reproduce.sh
```

 Or execute scripts in the container directly such as:

```Shell
 $ docker exec -it neurojit-ase scripts/reproduce.sh
```

### Reproducing the Results

After the container is up and running, you can execute the replication script in the container.

```Shell
 $ docker exec -it neurojit-ase scripts/reproduce.sh
```
If the script runs successfully, you will obtain results similar to the following: [out.txt](./out.txt).

[`reproduce.sh`](scripts/reproduce.sh) contains the following python scripts with the specified commands:

```Shell
(1) Usage: python scripts/pre_analysis.py COMMAND [ARGS]...

Statistical pre-analysis for CUF, Baseline and Dataset

╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ plot-corr                   (RQ1) Generate plots for Correlations between cuf Features and Defect-inducing Risks              │
│ plot-hmap                   Generate plots for Collinearity between Features                                                  │
│ table-distribution          Tabulate the distribution of the dataset                                                          │
│ table-group-diff            (RQ1) Tabulate the group differences between buggy and clean commits for cuf                      │
│ table-group-diff-projects   Tabulate the group differences between buggy and clean commits for cuf (each project)             │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

(2) Usage: python scripts/jit_sdp.py COMMAND [ARGS]...

Experiments for Just-In-Time Software Defect Prediction (JIT-SDP)

╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ actionable   Compute the ratios of actionable features for the baseline and combined models for the true positive samples in  │
│              the 20 folds JIT-SDP                                                                                             │
│ train-test   Train and test the baseline/cuf/combined model with 20 folds JIT-SDP                                             │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

(3) Usage: python scripts/analysis.py COMMAND [ARGS]...

Table and plot generation for analysis

╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ plot-radars               (RQ3) Generate radar charts for performance comparison between models                               │
│ plot-set-relationships    (RQ2) Generate plots for TPs predicted by baseline model only vs cuf model only                     │
│ table-actionable          (Toward More Actionable Guidance) Tabulate the results of the actionable features                   │
│ table-performances        (RQ3) Generate table for performance comparison between models                                      │
│ table-set-relationships   (RQ2) Generate table for TPs predicted by baseline model only vs cuf model only                     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

for more details, `--help` option can be used with each command.

### Example Usage of NeuroJIT
To calculate the commit understandability features of a commit in a repository, you can use the following command:
```Shell
$ python scripts/neurojit_cli.py calculate --project REPONAME --commit-hash COMMIT_HASH
```
Here is an example of how to obtain features from a commit in the repository used in our research:

```Shell
$ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project activemq --commit-hash 8f40a7

{'NOGV': 1.0, 'MDNL': 0.0, 'TE': 3.5122864969277017, 'II': 0.03225806451612903, 'NOP': 0.0, 'NB': 0.0, 'EC': 0.5, 'DD_HV': 0.04324106779539902, 'NOMT': 9.0}
```

If the commit is not a method changes commit, you will see the following message:
```Shell
$ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project groovy --commit-hash 7b84807

Target commit is not a method changes commit
```

For the commits not used in our research, you can also obtain the features using the same command. For example, to obtain the features of the commit `0101945` in the `spring-projects/spring-framework` repository:

```Shell
$ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project spring-projects/spring-framework --commit-hash 0101945

{'NOGV': 0.6, 'MDNL': 0.0, 'TE': 4.623781958476344, 'II': 0.9166666666666666, 'NOP': 1.0, 'NB': 0.0, 'EC': 0.3333333333333333, 'DD_HV': 0.04484876484351509, 'NOMT': 17.0}
```

### Additional Experiments

1. Evidence that the conclusion regarding Figure 5 on page 7 does not change even for all positives.

    ```Shell
    $ docker exec -it neurojit-ase python scripts/analysis.py table-set-relationships data/output/random_forest_cuf.json data/output/random_forest_baseline.json --fmt fancy_outline --no-only-tp

    ╒═══════════╤════════════╤════════════════╤═════════════════╕
    │ Project   │   cuf only │   Intersection │   baseline only │
    ╞═══════════╪════════════╪════════════════╪═════════════════╡
    │ Groovy    │       58.2 │           15.7 │            26.1 │
    │ Camel     │       53.7 │           17.9 │            28.4 │
    │ Flink     │       47.1 │           13.4 │            39.5 │
    │ Ignite    │       41.9 │           10.2 │            47.9 │
    │ Cassandra │       33.8 │           17.2 │            48.9 │
    │ HBase     │       31.4 │           35.6 │            33.0 │
    │ ActiveMQ  │       30.3 │           14.7 │            54.9 │
    │ Hive      │       29.8 │           40.3 │            29.9 │
    ╘═══════════╧════════════╧════════════════╧═════════════════╛

    $ docker exec -it neurojit-ase python scripts/analysis.py table-set-relationships data/output/xgboost_cuf.json data/output/xgboost_baseline.json --fmt fancy_outline --no-only-tp

    ╒═══════════╤════════════╤════════════════╤═════════════════╕
    │ Project   │   cuf only │   Intersection │   baseline only │
    ╞═══════════╪════════════╪════════════════╪═════════════════╡
    │ Groovy    │       60.2 │           15.9 │            23.9 │
    │ Camel     │       57.2 │           17.0 │            25.8 │
    │ Flink     │       49.3 │           13.0 │            37.7 │
    │ Ignite    │       45.0 │           10.1 │            44.9 │
    │ Cassandra │       40.4 │           18.2 │            41.4 │
    │ HBase     │       39.8 │           31.6 │            28.6 │
    │ ActiveMQ  │       34.9 │           16.0 │            49.1 │
    │ Hive      │       29.2 │           37.9 │            32.9 │
    ╘═══════════╧════════════╧════════════════╧═════════════════╛
    ```
2. Evidence that our dataset shows a different defect distribution compared to the studies cited in the External Validity section on page 10: see [scripts/commit_distribution.ipynb](./scripts/commit_distribution.ipynb).

### Customizing NeuroJIT

If you want to customize NeuroJIT, consider the following:
- `commit.py`: `Mining.only_method_changes(repo, commit_hash)` filters commits that only modify existing methods and saves the modified methods as `MethodChangesCommit` instances. You can customize the method filtering logic in this function.
- `cuf.metrics.py`: Contains the `MethodUnderstandabilityFeatures` class, which calculates the CUF at the method level and `CommitUnderstandabilityFeatures` which aggregate the method level features to the commit level. You can extend or modify the features calculated in these classes by adding new methods or modifying existing ones.
- `scripts/environment.py`: Contains the environment variables used in the scripts. You can modify the environment variables to customize the experiments.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

