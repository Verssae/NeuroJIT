from flask import Flask, render_template
import json
from pathlib import Path

app = Flask(__name__)


@app.route("/")
def index():
    # redirect to the first repo
    return repo("hcc", "activemq")


@app.route("/repo/<metric>/<repo>")
def repo(metric, repo):
    repos = [
        "activemq",
        "camel",
        "cassandra",
        "flink",
        "groovy",
        "hbase",
        "hive",
        "ignite",
    ]
    json_path = Path("data/tp_samples") / f"{repo}_{metric}.json"
    with open(json_path) as f:
        commit_code_pairs = json.load(f)

    metric_path = Path("data/tp_samples") / f"{repo}_metrics.json"
    with open(metric_path) as f:
        metrics = json.load(f)

    return render_template("index.html", commit_code_pairs=commit_code_pairs, repo=repo, repos=repos, metrics=metrics, num_tp=len(commit_code_pairs), metric=metric)


if __name__ == "__main__":
    app.run(debug=True)
