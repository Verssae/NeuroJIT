# NeuroJIT: Improving Just-In-Time Defect Prediction Using Neurophysiological and Empirical Perceptions of Modern Developers

This replication package contains the source code and data used in the paper *"NeuroJIT: Improving Just-In-Time Defect Prediction Using Neurophysiological and Empirical Perceptions of Modern Developers"* and the implementation of the commit understandability features calculator called `neurojit`.

## Table of Contents

- [`neurojit`](#neurojit)
  - [Dependencies](#dependencies)
  - [Installation](#installation)
  - [Usage](#usage)
- [Dataset](#dataset)
- [Reproducing the Results](#reproducing-the-results)
  - [(Option 1) Install via Docker (recommended)](#option-1-install-via-docker-recommended)
  - [(Option 2) Install locally](#option-2-install-locally)
- [License](#license)

## `neurojit` 

`neurojit` is a python package that calculates the commit understandability features (CUF). The package is structured as follows:

```bash
 src/neurojit
 ├── commit.py 
 ├── cuf
 │  ├── cfg.py
 │  ├── halstead.py
 │  ├── metrics.py 
 │  └── rii.py
 └── tools
    └── data_utils.py 
```
### Dependencies

- python 3.11+
- PyDriller
- javalang
- pandas
- numpy

### Installation

To install the `neurojit` package, run the following command:
```bash
$ pip install --no-cache-dir ./dist/neurojit-1.0.0-py3-none-any.whl
```
Or to install the package with the optional dependencies for the replication, see [Install locally](#install-locally).

### Usage
(1) Filter commits that only modified existing methods and save the modified methods as `MethodChangesCommit` instances.

```python
from neurojit.commit import MethodChangesCommit, Mining, Method

mining = Mining()
target_commit = mining.only_method_changes(repo="activemq", commit_hash="8f40a7")
if target_commit is not None:
    mining.save(target_commit)
```
(2) Compute the commit understandability features (CUF) from the saved `MethodChangesCommit` instances.

```python
from neurojit.cuf.metrics import CommitUnderstandabilityFeatures

cuf_calculator = CommitUnderstandabilityFeatures(target_commit)
features = ["HV","DD", "MDNL", "NB", "EC", "NOP", "NOGV", "NOMT", "II", "TE", "DD_HV"]
for feature in features:
    value = getattr(cuf_calculator, feature)
    print(f"{feature}: {value}")
```
(3) `KFoldDateSplit` is a utility class that splits the dataset into training and testing sets considering chronological order, verification latency and concept drifts. See e section 2.4 Just-in-Time Defect Prediction and Fig. 3 in the paper for more details.

```python
from neurojit.tools.data_utils import KFoldDateSplit

data = pd.read_csv("...your jit-sdp dataset...")
data["date"] = pd.to_datetime(data["date"])
data = data.set_index(["date"])

splitter = KFoldDateSplit(
    data, k=20, start_gap=3, end_gap=3, is_mid_gap=True, sliding_months=1
)

for i, (train, test) in enumerate(splitter.split()):
    X_train, y_train = train[features], train["buggy"]
    X_test, y_test = test[features], test["buggy"]
```
For more usage examples, see the [scripts](./scripts).

## Dataset

To calculate the verification latency gap (i.e., average fixing time, gap), we slightly modified the code of the [ApacheJIT](https://github.com/hosseinkshvrz/apachejit) repository to create an apachejit dataset that includes a fixed_date, and constructed `data/dataset/apachejit_gap.csv`, which is composed of a total of 8 projects that include the gap.

Then, we calculated the CUF of the ApacheJIT commits using the `neurojit` package. Additionally, we calculated the `LT` for the ApacheJIT commits because the `LT` is a widely used metric in the literature.

We provide the dataset in the `data/dataset` directory. The dataset is structured as follows:

```bash
data/dataset
├── apache_metrics_kamei.csv
├── apachejit_date.csv
├── apachejit_gap.csv
├── baseline.csv
├── baseline/  # LT added apachejit dataset (baseline)
│  ├── activemq.csv
│  ├── ...
├── commits/   # Filtered commits
├── combined/   # Combined dataset
└── cuf/      # CUF added apachejit dataset 
```

If you want to build the dataset from scratch, you can use the following scripts:

```bash
$ python scripts/data_utils.py prepare-data
$ python scripts/data_utils.py filter-commits
$ python scripts/calculate.py cuf-all
$ python scripts/calculate.py lt
$ python scripts/data_utils.py combine
```

## Reproducing the Results

This repository includes all the scripts, data and trained models to reproduce the results of the paper. The replication package is structured as follows:

```bash
├── archive # zipped trained models (pickles) in our experiment
├── data
│  ├── dataset # see `Building Dataset`
│  ├── output
│  └── plots 
├── dist # neurojit package distribution
├── Dockerfile
├── docker-compose.yml
├── src/neurojit # neurojit source code, see `neurojit`
└── scripts # scripts for the experiments
```

### (Option 1) Install via Docker (recommended)

```bash
$ docker-compose up --build -d
```

Then, you can run the replication scripts in the container.

```bash
$ docker exec -it neurojit-ase ./scripts/rq1.sh
$ docker exec -it neurojit-ase ./scripts/rq2.sh
$ docker exec -it neurojit-ase ./scripts/rq3.sh
$ docker exec -it neurojit-ase ./scripts/actionable.sh
```

### (Option 2) Install locally

To install the package with the optional dependencies for the replication, run the following command:

```bash
$ pip install --no-cache-dir ./dist/neurojit-1.0.0-py3-none-any.whl[replication]
```

Or install the dependencies manually with [pyproject.toml](./pyproject.toml) based dependency management tools (e.g., [poetry](https://python-poetry.org)). We used  [rye](https://rye-up.com) for the dependency management.


```bash
$ rye pin 3.12 # pin the python version you want to use
$ rye sync --features=replication # install all dependencies
```

[Checkstyle](https://github.com/checkstyle/checkstyle/releases/): Save to root directory as checkstyle.jar for easy replication. For example,

```bash
$ wget https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.15.0/checkstyle-10.15.0-all.jar -O checkstyle.jar
```

To unzip the trained models (pickles) in our experiment, run the following command:

```bash
cat archive/pickles_part_* > pickles.tar.gz && tar -xzf pickles.tar.gz -C .
```
It will extract the pickles to the `data/pickles` directory.

Then, you can run the replication scripts in the virtual environment.

```bash
$ python scripts/rq1.py
$ python scripts/rq2.py
$ python scripts/rq3.py
$ python scripts/actionable.py
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.