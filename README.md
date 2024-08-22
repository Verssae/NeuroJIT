# NeuroJIT Replication Package

Hello. Here is a guide on how to use the replication package of NeuroJIT. If you have any questions regarding the use of the package, feel free to contact us anytime via email at {fantasyopy, sparky}@hanyang.ac.kr.

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

1. Docker: After navigating to the project folder, execute the following commands in the terminal to build and run the Docker container.
   ```Shell
    $ docker-compose up --build -d
    ...
     ✔ Container neurojit-ase  Started
    ```
2. How to run the scripts to reproduce the key experimental results from the paper: After the container is up and running, you can execute the replication script in the container.
   ```Shell
    $ docker exec -it neurojit-ase scripts/reproduce.sh
    ```
    If the script runs successfully, you will obtain results similar to the following: [out.txt](./out.txt).
3. Using NeuroJIT to obtain commit understandability features for just-in-time defect prediction
   1. NeuroJIT takes a repository name and a commit hash value to identify the commits that modify methods. From those commits, it calculates the nine commit understandability features proposed in our research, as follows.
   
        ```Shell
        $ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project activemq --commit-hash 8f40a7

        {'NOGV': 1.0, 'MDNL': 0.0, 'TE': 3.5122864969277017, 'II': 0.03225806451612903, 'NOP': 0.0, 'NB': 0.0, 'EC': 0.5, 'DD_HV': 0.04324106779539902, 'NOMT': 9.0}
        
        $ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project groovy --commit-hash 7b84807
        
        Target commit is not a method changes commit
        ```

    2. Here is how to obtain features from a commit in a new repository that was not used in our research:
        ```Shell
        $ docker exec -it neurojit-ase python scripts/neurojit_cli.py calculate --project spring-projects/spring-framework --commit-hash 0101945

        {'NOGV': 0.6, 'MDNL': 0.0, 'TE': 4.623781958476344, 'II': 0.9166666666666666, 'NOP': 1.0, 'NB': 0.0, 'EC': 0.3333333333333333, 'DD_HV': 0.04484876484351509, 'NOMT': 17.0}
        ```
    3. Additional experiments conducted to ensure the methodological rigor of NeuroJIT include the following:
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

    4. Customizing NeuroJIT

        The structure of the core module `neurojit` is as follows:​

        ```Shell
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

        If you want to customize NeuroJIT, consider the following:
        - `commit.py`: Contains the `Mining` class, which filters commits that only modify existing methods and saves the modified methods as `MethodChangesCommit` instances. 
        - `cuf.metrics`: Contains the `MethodUnderstandabilityFeatures` class, which calculates the CUF at the method level and `CommitUnderstandabilityFeatures` which aggregate the method level features to the commit level. 
        - other files: Refer to the source code and comments for more details.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

