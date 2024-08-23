# NeuroJIT Replication Package

이 문서에서는 논문 *NeuroJIT: Improving Just-In-Time Defect Prediction Using Neurophysiological and Empirical Perceptions of Modern Developers*(NeuroJIT)의 복제 패키지를 소개합니다. 복제 패키지는 NeuroJIT의 핵심 모듈과 논문의 결과를 재현하는 데 사용된 스크립트를 포함하고 있습니다. 복제 패키지를 사용하여 논문의 결과를 재현하거나 포함된 핵심 모듈을 바탕으로 사용자 정의 실험을 수행할 수 있습니다.
 
패키지 사용에 관한 질문이 있으시면 언제든지 [fantasyopy@hanyang.ac.kr](mailto:fantasyopy@hanyang.ac.kr) 또는 [sparky@hanyang.ac.kr](mailto:sparky@hanyang.ac.kr)로 이메일을 통해 연락해 주세요.

## Structure of the Replication Package

복제 패키지는 크게 데이터셋인 `data/dataset`, 핵심 모듈인 `src/neurojit`, 그리고 논문의 결과를 재현하는 데 사용된 `scripts`의 3가지로 구성되어 있습니다. 복제 패키지의 구조는 다음과 같습니다:

```Shell
├── archive # zipped trained models (pickles) in our experiment
├── data
│  ├── dataset # dataset used in the experiments
│  ├── output # output of the experiments
│  └── plots  # plots generated in the experiments
├── dist # neurojit package distribution
├── Dockerfile
├── docker-compose.yml
├── src/neurojit # core module
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

데이터셋은 ApacheJIT 데이터셋을 기반으로 구축되었습니다. 우리의 데이터셋은 총 8개의 Apache 프로젝트에 대해 Kamei et. al이 제안한 JIT 피처와 NeuroJIT에서 제안하는 Commit Understandability Features(CUF)를 모두 포함하고 있습니다. 데이터셋은 다음과 같은 구조로 구성되어 있습니다:

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
├── combined/   # Combined of CUF and baseline dataset (our main dataset)
├── commits/   # Filtered commits (only method changes commits)
└── cuf/      # CUF calculated and filtered ApacheJIT dataset
```

데이터셋을 처음부터 구축하려면 다음 스크립트들을 사용할 수 있습니다:

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

데이터를 처음부터 구축하는 데는 시간이 상당히 오래 걸리는데, 그 이유는 `filter-commits`를 위해 각 커밋의 모든 메서드를 비교해야 하며, CUF 계산 시 커밋의 각 파일에 대해 Checkstyle을 호출해야 하기 때문입니다. 따라서 우리는 [data/dataset](data/dataset/) 디렉터리에 미리 구축된 데이터셋을 제공합니다.

### `neurojit` 

`neurojit` 모듈은 NeuroJIT의 핵심 기능인 CUF 계산, JIT-SDP 데이터 분할 방법 구현을 제공합니다. 모듈은 다음과 같은 구조로 구성되어 있습니다:

```Shell
src/neurojit
├── commit.py # commit filtering and saving
├── cuf
│  ├── cfg.py # control flow graph
│  ├── halstead.py # halstead metrics
│  ├── metrics.py  # CUF calculation (method and commit level)
│  └── rii.py # II feature calculation using Checkstyle
└── tools
    └── data_utils.py # JIT-SDP data split utility (chronological order, verification latency, concept drifts)
```

## Setup

1. Hardware/Software Requirements

    우리는 다음 사양의 장치들에서 복제 패키지를 테스트했습니다:

    - Windows 11
      - CPU: AMD Ryzen 5 5600X
      - RAM: 32GB
    - Ubuntu 20.04.6
      - Device: NVIDIA DGX Station V100, 2019
      - CPU: Intel Xeon(R) E5-2698 v4 @ 2.20GHz
      - RAM: 256GB
    - MacOS 14.6.1
      - Device: MacBook Air M2, 2022
      - CPU: Apple M2
      - RAM: 24GB
    - Docker version 4.33.1
2. Docker Container Setup

   본 문서에서는 Docker 컨테이너를 사용하여 복제 패키지를 실행하는 방법에 대해 설명합니다. 로컬 환경에서 설치 및 실행하는 방법은 문서 하단의 [Local Setup](#local-setup)을 참조하세요.

   Docker를 설치하려면 https://docs.docker.com/get-docker/ 에서 공식 설치 가이드를 참조하세요.

   본 복제 패키지를 다운로드하고 해당 디렉토리로 이동하세요. 복제 환경은 Docker 컨테이너로 실행 데이터셋 및 결과 파일을 호스트와 컨테이너 간에 공유	하기 위해 볼륨을 사용합니다. 간편한 볼륨 마운트를 위해 Docker Compose를 사용합니다. Docker Compose를 사용하여 컨테이너를 빌드하고 백그라운드에서 실행하려면 다음 명령을 실행하세요:

   ```Shell
   $ docker-compose up --build -d
   ...
   ✔ Container neurojit-ase  Started
   ```
   `docker ps`를 통해 `neurojit-ase` 컨테이너가 실행 중인지 확인하세요.

## Usage

### Accessing the Container

본 패키지에 포함된 모든 실행가능한 파일은 `neurojit-ase` 컨테이너 내에서 실행됩니다. `docker exec -it neurojit-ase COMMAND` 명령을 사용하여 컨테이너에 액세스할 수 있습니다. 예를 들어, 다음 명령을 사용하여 컨테이너 내 셸에 액세스할 수 있습니다:

```Shell
 $ docker exec -it neurojit-ase bash

 root@31d:/app#
```
스크립트를 바로 실행할 수도 있습니다:

```Shell
 $ docker exec -it neurojit-ase scripts/reproduce.sh
```

컨테이너 및 볼륨 정리를 하고자 할 때는 다음 명령을 사용하세요:

```Shell
 $ docker-compose down -v
```

### Reproducing the Results

논문의 핵심 결과를 재현하려면 다음 명령을 실행하세요:

```Shell
 $ docker exec -it neurojit-ase scripts/reproduce.sh
``` 

스크립트가 성공적으로 실행되면 다음과 같은 결과를 얻을 수 있습니다: [out.txt](./out.txt).

### About the Reproduction Script

[`reproduce.sh`](scripts/reproduce.sh) 스크립트는 논문의 핵심 결과를 재현하는 데 사용됩니다. 다음과 같이 크게 3가지 파이썬 스크립트를 실행합니다:

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

각 스크립트 내 서브 커맨드에 대한 자세한 내용은 `--help` 옵션을 사용하면 확인할 수 있습니다.

### Example Usage of NeuroJIT

NeuroJIT은 어느 프로젝트의 커밋에 대해서도 CUF를 계산하는 데 사용할 수 있도록 설계되었습니다. 간단하게 `neurojit` 컴포넌트들을 활용하여 만든 `neurojit_cli.py` 스크립트를 사용하여 다음과 같이 CUF를 계산할 수 있습니다:

```Shell
$ python scripts/neurojit_cli.py calculate --project REPONAME --commit-hash COMMIT_HASH
```

예를 들어, `activemq` 프로젝트의 `8f40a7` 커밋에 대한 CUF를 계산하려면 다음과 같이 실행하세요:

```Shell
$ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project activemq --commit-hash 8f40a7

{'NOGV': 1.0, 'MDNL': 0.0, 'TE': 3.5122864969277017, 'II': 0.03225806451612903, 'NOP': 0.0, 'NB': 0.0, 'EC': 0.5, 'DD_HV': 0.04324106779539902, 'NOMT': 9.0}
```

메소드만 변경하는 커밋이 아닌 경우 다음과 같은 메시지가 출력됩니다:

```Shell
$ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project groovy --commit-hash 7b84807

Target commit is not a method changes commit
```

논문의 실험에 포함된 apache 프로젝트가 아니어도 사용자가 원하는 프로젝트의 CUF를 계산할 수 있습니다. 예를 들어, `spring-projects/spring-framework` 프로젝트의 `0101945` 커밋에 대한 CUF를 계산하려면 다음과 같이 실행하세요:

```Shell
$ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project spring-projects/spring-framework --commit-hash 0101945

{'NOGV': 0.6, 'MDNL': 0.0, 'TE': 4.623781958476344, 'II': 0.9166666666666666, 'NOP': 1.0, 'NB': 0.0, 'EC': 0.3333333333333333, 'DD_HV': 0.04484876484351509, 'NOMT': 17.0}
```

### Additional Experiments

1. CUF가 기존 JIT 피처와는 다른 정보를 제공함을 보여주는 논문의 7페이지의 그림 5는 True positives 뿐 아니라 모든 positives 샘플에 대해서도 결론이 동일하게 나타납니다. `--no-only-tp` 옵션을 사용하여 모든 positives 샘플에 대한 결과를 확인할 수 있습니다. 

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
2. 논문 10페이지의 External Validity 섹션에서 언급된 연구와 우리 데이터셋이 다른 분포를 보인다는 결과는 [scripts/commit_distribution.ipynb](./scripts/commit_distribution.ipynb)에서 확인할 수 있습니다.

### Customizing NeuroJIT

NeuroJIT을 변형하여 사용자 정의 실험을 수행하려면 위에서 언급된 스크립트들을 참조하여 `neurojit` 모듈을 확장하거나 수정할 수 있습니다. 핵심적인 파일들은 다음과 같습니다:

- `neurojit.commit.py`: `Mining.only_method_changes(repo, commit_hash)`은 메소드만 수정하는 커밋을 필터링하고, 메소드 바디를 캐시에 저장합니다. 이 함수를 수정하여 다른 필터링 방법을 사용할 수 있습니다.
- `neurojit.cuf.metrics.py`: `MethodUnderstandabilityFeatures` 클래스는 메소드 수준에서 CUF를 계산하고, `CommitUnderstandabilityFeatures` 클래스는 메소드 수준의 피처를 커밋 수준으로 집계합니다. 각 클래스 내의 피쳐 계산 메소드를 추가하거나 수정하여 사용자 정의 피처를 계산할 수 있습니다. 
- `scripts/environment.py`: 스크립트에서 사용되는 환경 변수를 포함합니다. 환경 변수를 수정하여 실험을 사용자 정의할 수 있습니다.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.