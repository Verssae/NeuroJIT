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

CUF_ALL = [
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
    "DD_HV"
]

BASE_ALL = [
    "NUC", "SEXP", "LT", "Entropy", "EXP", "LA", "LD", "NS", "AGE","REXP", "ND", "NF"
]

BASELINE =['LA', 'NUC', 'LT', 'LD', 'Entropy', 'SEXP', 'EXP', 'AGE', 'NS']

CUF = ['NOGV', 'MDNL', 'TE', 'II', 'NOP', 'NB', 'EC', 'DD_HV', 'NOMT']

COMBINED = BASELINE + CUF

FEATURE_SET = {
    "baseline": BASELINE,
    "cuf": CUF,
    "combined": BASELINE + CUF,
}

PERFORMANCE_METRICS = ["f1_macro","auc","mcc",  "brier", "fpr"]

ACTIONABLE_FEATURES = CUF + ["LA", "LD", "LT", "NS"]