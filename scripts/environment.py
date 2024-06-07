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


BASE_FEATURES = ['NUC', 'SEXP', 'LT', 'Entropy', 'EXP', 'LA', 'LD', 'NS', 'AGE']
HCC_FEATURES = ['NP', 'REC', 'ENT_V', 'RII', 'MDNL', 'NB', 'NTM', 'TS', 'DD_V', 'RG']
FEATURES = BASE_FEATURES + HCC_FEATURES
HCC_ALL = [
    "V",
    "DD",
    "MDNL",
    "NB",
    "REC",
    "NP",
    "RG",
    "NTM",
    "TS",
    "RII",
    "ENT",
    "ENT_V",
    "DD_V",
]

BASE_ALL = [
    "NUC", "SEXP", "LT", "Entropy", "EXP", "LA", "LD", "NS", "AGE", "LA/LT", "LD/LT", "LT/NF", "NUC/NF", "REXP", "ND", "NF"
]

BASELINE =['NUC', 'SEXP', 'LT', 'Entropy', 'EXP', 'LA', 'LD', 'NS', 'AGE']

HCC = ['NP', 'REC', 'ENT', 'RII', 'MDNL', 'NB', 'NTM', 'DD_V', 'RG']

BASELINE_HCC = HCC + BASELINE

FEATURE_SET = {
    "baseline": BASELINE,
    "hcc": HCC,
    "baseline+hcc": BASELINE + HCC,
}

PERFORMANCE_METRICS = ["f1_macro", "mcc", "brier"]

INACTIONABLE_FEATURES = [ "NUC", "AGE", "EXP", "SEXP"]