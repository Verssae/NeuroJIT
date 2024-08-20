import json
import os
from pathlib import Path
from datetime import datetime
from typing import List
from typing_extensions import Annotated

import pandas as pd
from rich.progress import track
from rich.console import Console
from typer import Typer, Argument, Option

from neurojit.commit import Mining

from environment import PROJECTS

app = Typer()


@app.command()
def prepare_data(
    dataset_dir: Annotated[
        Path, Option(..., help="Path to the dataset directory")
    ] = Path("data/dataset"),
):
    """
    ApacheJIT(+bug_date column) dataset
    """
    apachejit = pd.read_csv(dataset_dir / "apachejit_date.csv")
    apachejit["fix_date"] = pd.to_datetime(apachejit["fix_date"])
    apachejit["fix_date"] = apachejit["fix_date"].apply(lambda x: x.tz_localize(None))

    apachejit["date"] = apachejit["date"].apply(lambda x: datetime.fromtimestamp(x))
    apachejit = apachejit.drop(columns=["bug_date", "year"])

    apachejit["gap"] = apachejit["fix_date"] - apachejit["date"]
    apachejit["gap"] = apachejit["gap"].apply(lambda x: x.days)

    apachejit["project"] = apachejit["project"].apply(
        lambda x: x.replace("apache/", "")
    )
    apachejit = apachejit.loc[apachejit["project"].isin(PROJECTS)]
    apachejit = apachejit.sort_index()
    apachejit = apachejit.sort_values(by="date")
    apachejit.to_csv(dataset_dir / "apachejit_gap.csv", index=False)

    metrics = pd.read_csv(dataset_dir / "apache_metrics_kamei.csv")
    apachejit_metrics = pd.merge(apachejit, metrics).drop(
        columns=["fix_date", "author_date"]
    )

    meta_features = ["commit_id", "project", "repo", "gap", "buggy", "date"]

    apachejit_metrics.columns = apachejit_metrics.columns.map(
        lambda x: x.upper() if x not in meta_features else x
    )
    apachejit_metrics = apachejit_metrics.rename(
        columns={"AEXP": "EXP", "AREXP": "REXP", "ASEXP": "SEXP", "ENT": "Entropy"}
    )

    apachejit_metrics.to_csv(dataset_dir / "baseline.csv", index=False)


@app.command()
def filter_commits(
    project: Annotated[
        str,
        Argument(..., help="activemq|camel|cassandra|flink|groovy|hbase|hive|ignite"),
    ],
    apachejit: Annotated[
        str, Option(help="Path to ApacheJIT dataset")
    ] = "data/dataset/apachejit_gap.csv",
    commits_dir: Annotated[Path, Option(help="Path to the commits directory")] = Path(
        "data/dataset/commits"
    ),
):
    """
    Filter method changes for each commit in the dataset and save methods to cache
    """
    console = Console()
    commit_csv = commits_dir / f"{project}.csv"
    if not Path(commit_csv).exists():
        split_commits(apachejit, commits_dir)
    df = pd.read_csv(commit_csv, index_col="commit_id")

    mining = Mining()
    try:
        for commit_id, row in track(
            df.iterrows(), f"Mining {project}...", total=df.shape[0], console=console
        ):
            if row["target"] != "not_yet":
                continue
            method_changes_commit = mining.only_method_changes(
                row["project"], commit_id
            )
            if method_changes_commit is None:
                df.loc[commit_id, "target"] = "no"
                df.to_csv(commit_csv)
                continue

            mining.save(method_changes_commit, "data/cache")
            df.loc[commit_id, "target"] = "yes"
            df.to_csv(commit_csv)

    except Exception as e:
        console.print(e)
        df.to_csv(commit_csv)
        console.log(f"Saved progress to {commit_csv}")


@app.command()
def save_methods(
    project: Annotated[
        str,
        Argument(..., help="activemq|camel|cassandra|flink|groovy|hbase|hive|ignite"),
    ],
    commits_dir: Annotated[Path, Option(help="Path to the commits directory")] = Path(
        "data/dataset/commits"
    ),
):
    """
    Save the change contexts for commits that modified existing methods
    """
    console = Console()

    df = pd.read_csv(commits_dir / f"{project}.csv", index_col="commit_id")

    mining = Mining()

    for commit_id, row in track(
        df.iterrows(), f"Mining {project}...", total=df.shape[0], console=console
    ):
        if row["target"] != "yes":
            continue

        if mining.check("data/cache", row["project"], commit_id):
            continue

        method_changes_commit = mining.only_method_changes(row["project"], commit_id)

        if method_changes_commit is None:
            continue

        mining.save(method_changes_commit, "data/cache")


@app.command()
def combine_dataset(
    baseline_dir: Annotated[Path, Option(help="Path to the baseline directory")] = Path(
        "data/dataset/baseline"
    ),
    cuf_dir: Annotated[Path, Option(help="Path to the CUF directory")] = Path(
        "data/dataset/cuf"
    ),
    combined_dir: Annotated[Path, Option(help="Path to the combined directory")] = Path(
        "data/dataset/combined"
    ),
):
    console = Console()
    if not combined_dir.exists():
        combined_dir.mkdir(parents=True)

    for project in track(PROJECTS, f"Combining datasets...", console=console):
        baseline_data = pd.read_csv(baseline_dir / f"{project}.csv", index_col=0)
        cuf_data = pd.read_csv(cuf_dir / f"{project}.csv", index_col=0)
        cuf_data = cuf_data.drop(
            labels=[
                "buggy",
                "target",
                "project",
                "date",
                "gap"
            ],
            axis=1,
        )

        # Concatenate the two dataframes based cuf_data's index
        data = pd.concat([baseline_data, cuf_data], axis=1, join="inner")
        assert data.shape[0] == cuf_data.shape[0]

        data.to_csv(combined_dir / f"{project}.csv")
        console.print(f"combined {project}")


def split_commits(
    apachejit: str = "data/dataset/apachejit_gap.csv",
    commits_dir: Path = Path("data/dataset/commits"),
):
    df = pd.read_csv(apachejit, index_col="commit_id")
    for project in df["project"].unique():
        project_df = df[df["project"] == project].copy()
        project_df["target"] = "not_yet"
        commits_dir.mkdir(exist_ok=True)
        project_df.to_csv(commits_dir / f"{project}.csv")


def load_project_data(base_dir: str = "data/dataset/combined") -> pd.DataFrame:
    total = []
    for project in PROJECTS:
        data = pd.read_csv(f"{base_dir}/{project}.csv")
        total.append(data)
    data = pd.concat(total)

    return data


def load_jsons(
    jsons: List[Path],
) -> pd.DataFrame:
    data = []
    for json_file in jsons:
        with open(json_file) as f:
            data.extend(json.load(f))

    return pd.DataFrame(data)


if __name__ == "__main__":
    app()
