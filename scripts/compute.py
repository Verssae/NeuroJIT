from pathlib import Path
from typing import List
from typing_extensions import Annotated

import pandas as pd
from typer import Typer, Argument, Option
from rich.progress import track

from neurojit.commit import Mining
from neurojit.cuf.metrics import CommitUnderstandabilityFeatures

app = Typer()


@app.command()
def CUF_ALL(
    project: Annotated[str, Argument(..., help="Pactivemq|camel|cassandra|flink|groovy|hbase|hive|ignite")],
    save_dir: Annotated[Path, Option()] = Path("data/dataset/cuf"),
    quiet: Annotated[bool, Option(help="Disable progress bar")] = False,
    checkstyle_path: Annotated[
        str, Option(help="Path to checkstyle jar")
    ] = "checkstyle.jar",
    xml_path: Annotated[
        str, Option(help="Path to checkstyle xml config")
    ] = "indentation_config.xml",
    checkstyle_cache_dir: Annotated[
        str, Option(help="Path to checkstyle cache")
    ] = "data/cache/checkstyle",
):
    """
    Compute all CUF for a project
    """
    save_path = save_dir / f"{project}.csv"
    Path(save_path).parent.mkdir(exist_ok=True, parents=True)
    if not Path(save_path).exists():
        df = pd.read_csv(f"data/dataset/commits/{project}.csv", index_col="commit_id")
        assert df[df["target"] == "not_yet"].shape[0] == 0
        df = df[df["target"] == "yes"]
    else:
        df = pd.read_csv(save_path, index_col="commit_id")

    for commit_id, row in track(
        df.iterrows(),
        f"Computing cuf for {project}...",
        total=df.shape[0],
        disable=quiet,
    ):
        if row["target"] == "done":
            continue
        commit = Mining.load("data/cache", row["repo"], commit_id)
        if commit is None:
            df.loc[commit_id, "target"] = "error"
            df.to_csv(save_path)
            continue
        cuf = CommitUnderstandabilityFeatures(commit, checkstyle_path, xml_path, checkstyle_cache_dir)
        cufs = cuf.all
        for metric, value in cufs.items():
            df.loc[commit_id, metric] = value

        df.loc[commit_id, "target"] = "done"
        df.to_csv(save_path)

    df.to_csv(save_path)


@app.command()
def CUF(
    project: Annotated[str, Argument(..., help="Project name")],
    metrics: Annotated[
        List[str], Argument(..., help="Metrics to compute (e.g. V DD_V ENT)")
    ],
    save_dir: Annotated[Path, Option()] = Path("data/dataset/cuf"),
    quiet: Annotated[bool, Option(help="Disable progress bar")] = False,
    checkstyle_path: Annotated[
        str, Option(help="Path to checkstyle jar")
    ] = "checkstyle.jar",
    xml_path: Annotated[
        str, Option(help="Path to checkstyle xml config")
    ] = "indentation_config.xml",
    checkstyle_cache_dir: Annotated[
        str, Option(help="Path to checkstyle cache")
    ] = "data/cache/checkstyle",
):
    """
    Compute specific CUF metrics for a project
    """
    save_path = save_dir / f"{project}.csv"
    Path(save_path).parent.mkdir(exist_ok=True, parents=True)
    if not Path(save_path).exists():
        df = pd.read_csv(f"data/dataset/commits/{project}.csv", index_col="commit_id")
        assert df[df["target"] == "not_yet"].shape[0] == 0
        df = df[df["target"] == "yes"]
    else:
        df = pd.read_csv(save_path, index_col="commit_id")

    for metric in metrics:
        if metric not in df.columns:
            df[metric] = None

    for commit_id, row in track(
        df.iterrows(),
        f"Computing CUF {', '.join(metrics)} for {project}...",
        total=df.shape[0],
        disable=quiet,
    ):
        commit = Mining.load("data/cache", row["repo"], commit_id)
        if commit is None:
            continue
        cuf = CommitUnderstandabilityFeatures(commit, checkstyle_path, xml_path, checkstyle_cache_dir)

        for metric in metrics:
            value = getattr(cuf, metric)
            df.loc[commit_id, metric] = value
        df.to_csv(save_path)
    df.to_csv(save_path)


@app.command()
def LT(
    project: Annotated[str, Argument(..., help="activemq|camel|cassandra|flink|groovy|hbase|hive|ignite")],
    save_dir: Annotated[Path, Option()] = Path("data/dataset/baseline"),
    quiet: Annotated[bool, Option(help="Disable progress bar")] = False,
):
    """
    Compute LT for apachejit_metrics
    """
    save_path = save_dir / f"{project}.csv"

    Path(save_path).parent.mkdir(exist_ok=True, parents=True)
    if not Path(save_path).exists():
        df = pd.read_csv("data/dataset/apachejit_metrics.csv", index_col="commit_id")
        df = df[df["project"] == project]
        df["target"] = "not_yet"
    else:
        df = pd.read_csv(save_path, index_col="commit_id")

    for commit_id, row in track(
        df.iterrows(),
        f"Computing KAMEI for {project}...",
        total=df.shape[0],
        disable=quiet,
    ):
        if row["target"] == "done":
            continue
        commit = Mining.load("data/cache", row["repo"], commit_id)
        if commit is None:
            df.loc[commit_id, "target"] = "error"
            df.to_csv(save_path)
            continue

        before_code_files = {method.code for method in commit.methods_before}
        lt = sum(len(code.splitlines()) for code in before_code_files)

        df.loc[commit_id, "LT"] = lt
        df.loc[commit_id, "target"] = "done"
        df.to_csv(save_path)

    df.to_csv(save_path)

    return str(save_path)


if __name__ == "__main__":
    app()
