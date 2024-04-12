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

BASELINE = [
    "NS",
    "NF",
    "LA",
    "LD",
    "LT",
    "AGE",
    "NUC",
    "EXP",
    "SEXP",
]

HCC = [
    "V",
    "DD_V",
    "MDNL",
    "NB",
    "REC",
    "NP",
    "RG",
    "NTM",
    "TS",
    "RII",
]

BASELINE_HCC = HCC + BASELINE

FEATURE_SET = {
    "baseline": BASELINE,
    "hcc": HCC,
    "baseline+hcc": BASELINE_HCC,
}

PERFORMANCE_METRICS = ["f1_macro", "mcc", "brier"]

ACTIONABLE_FEATURES = HCC + ["NS", "NF", "LA", "LD", "LT"]