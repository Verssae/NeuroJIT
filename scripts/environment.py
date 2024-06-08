SEED = 42

PROJECTS = {
    "activemq": "ActiveMQ",
    "camel": "Camel",
    "flink": "Flink",
    "groovy": "Groovy",
    "cassandra": "Cassandra",
    "hbase": "HBase",
    "hive": "Hive",
    "ignite": "Ignite",
}

HCC_ALL = [
    "HV",
    "DD",
    "MDNL",
    "NB",
    "EC",
    "NOP",
    "NOGV",
    "NOMT",
    "II",
    "TE",
    "E_HV",
    "DD_HV",
    'TS'
]

BASE_ALL = [
    "NUC", "SEXP", "LT", "Entropy", "EXP", "LA", "LD", "NS", "AGE","REXP", "ND", "NF"
]

BASELINE =['LA', 'NUC', 'LT', 'LD', 'Entropy', 'SEXP', 'EXP', 'AGE', 'NS']

HCC = ['NOGV', 'MDNL', 'TE', 'II', 'NOP', 'NB', 'EC', 'DD_HV', 'NOMT']

BASELINE_HCC = BASELINE + HCC

FEATURE_SET = {
    "baseline": BASELINE,
    "hcc": HCC,
    "baseline+hcc": BASELINE + HCC,
}

PERFORMANCE_METRICS = ["f1_macro", "mcc", "brier"]

ACTIONABLE_FEATURES = HCC + ["LA", "LD", "LT", "NS"]