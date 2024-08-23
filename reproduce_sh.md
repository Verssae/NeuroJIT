`reproduce.sh` 스크립트는 논문의 핵심 결과를 재현하는 데 사용됩니다. 다음과 같이 크게 3가지 파이썬 스크립트를 실행합니다:

```Shell
(1) Usage: python scripts/pre_analysis.py COMMAND [ARGS]...

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
