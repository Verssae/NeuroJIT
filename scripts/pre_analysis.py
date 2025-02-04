# Copyright (c) 2024 Hansae Ju
# Licensed under the Apache License, Version 2.0
# See the LICENSE file in the project root for license terms.

import warnings
from pathlib import Path
from matplotlib import pyplot as plt
from typing_extensions import Annotated

import typer
import pandas as pd
from tabulate import tabulate
from scipy.stats import ranksums
from cliffs_delta import cliffs_delta

from neurojit.commit import Mining
from data_utils import load_project_data
from visualization import corr_plot, visualize_hmap
from correlation import group_difference, significances
from environment import BASE_ALL, CUF_ALL, PROJECTS, COMBINED, CUF, BASELINE

warnings.filterwarnings("ignore")

app = typer.Typer(
    add_completion=False, help="Statistical pre-analysis for CUF, Baseline and Dataset"
)


@app.command()
def plot_corr():
    """
    (RQ1) Generate plots for Correlations between cuf Features and Defect-inducing Risks
    """
    data = load_project_data()

    y = data["buggy"]
    X = data[CUF]

    results_cuf = significances(X, y, metrics=CUF)

    X = data[COMBINED]
    results_combined = significances(X, y, metrics=COMBINED)

    save_dir = Path("data/output/plots/pre_analysis/significance")
    save_dir.mkdir(exist_ok=True, parents=True)

    corr_plot(results_cuf, results_combined, save_dir=save_dir, top_k=9)

    from rich import console

    df_cuf = pd.DataFrame(results_cuf)
    df_cuf = df_cuf.drop(["adjusted_odds", "abs_odds"], axis=1)
    df_combined = pd.DataFrame(results_combined)
    df_combined = df_combined.drop(["adjusted_odds", "abs_odds", "jit-sdp"], axis=1)
    console = console.Console()

    console.print("Saved plots to data/output/plots/pre_analysis/significance")

@app.command()
def plot_hmap():
    """
    Generate plots for Collinearity between Features
    """
    data = load_project_data()

    X = data[BASELINE + CUF]
    save_path = "data/output/plots/pre_analysis/hmap/ALL.png"
    visualize_hmap(X.corr(method="spearman"), size=7, save_path=save_path)

    X = data[CUF_ALL]
    save_path = "data/output/plots/pre_analysis/hmap/ALL_CUF.png"
    visualize_hmap(X.corr(method="spearman"), size=5, save_path=save_path)

    X = data[BASE_ALL]
    save_path = "data/output/plots/pre_analysis/hmap/ALL_Baseline.png"
    visualize_hmap(X.corr(method="spearman"), size=5, save_path=save_path)


@app.command()
def table_group_diff(
    fmt: Annotated[str, typer.Option()] = "github",
):
    """
    (RQ1) Tabulate the group differences between buggy and clean commits for cuf
    """
    data = load_project_data()
    no_defects = data.loc[data["buggy"] == 0]
    defects = data.loc[data["buggy"] == 1]
    table = []
    for metric in CUF:
        gd = ranksums(no_defects[metric], defects[metric]).pvalue
        d, res = cliffs_delta(no_defects[metric], defects[metric])
        table.append([metric, gd, abs(d), res])

    # sort by delta
    table = sorted(table, key=lambda x: x[2], reverse=True)

    output = tabulate(
        table,
        headers=["Metric", "Wilcoxon P-value", "Cliff's Delta", "Res"],
        tablefmt=fmt,
        floatfmt=".3f",
    )

    print(output)
    return output


@app.command()
def table_group_diff_projects(
    fmt: Annotated[str, typer.Option()] = "github",
):
    """
    Tabulate the group differences between buggy and clean commits for cuf (each project)
    """
    data = load_project_data()
    data["date"] = pd.to_datetime(data["date"])
    data = data.set_index(["date"])

    no_defects = data.loc[data["buggy"] == 0]
    defects = data.loc[data["buggy"] == 1]
    table = []
    for project in PROJECTS:
        no_defects = data.loc[(data["buggy"] == 0) & (data["project"] == project)]
        defects = data.loc[(data["buggy"] == 1) & (data["project"] == project)]
        row = [PROJECTS[project]]
        for metric in CUF:
            gd = group_difference(no_defects[metric], defects[metric], fmt="pair")
            row.append(gd)
        table.append(row)
    output = tabulate(
        table,
        headers=["Project"] + CUF,
        tablefmt=fmt,
        floatfmt=".3f",
    )

    print(output)
    return output


@app.command()
def table_distribution(
    fmt: Annotated[str, typer.Option()] = "github",
):
    """
    Tabulate the distribution of the dataset
    """
    table = []

    for project in PROJECTS:

        data = pd.read_csv(f"data/dataset/combined/{project}.csv")

        data["date"] = pd.to_datetime(data["date"])
        data = data.set_index(["date"])
        data = data.sort_index()

        data = data.drop_duplicates()

        data = data.loc[data["project"] == project]

        buggy = data.loc[data["project"] == project].buggy.sum()

        start_date = data.index.min()
        end_date = data.index.max()

        commits_day = len(data) / (end_date - start_date).days
        avg_gap = data.loc[data["buggy"] == 1, "gap"].mean()
        commits_gap = round(avg_gap * commits_day, 1)

        changed_methods = []
        changed_lines = []
        method_lts = []

        data = data.set_index("commit_id")
        for commit_id, row in data.iterrows():
            commit = Mining.load("data/cache", row["project"], commit_id)
            if commit is None:
                continue
            la = 0
            ld = 0
            lt = 0
            changed_methods.append(len(commit.methods_before))
            for method in commit.methods_after:
                la += len(method.added_lines)
            for method in commit.methods_before:
                ld += len(method.deleted_lines)
                lt += method.loc
            changed_lines.append(la + ld)
            method_lts.append(lt)

        table.append(
            [
                PROJECTS[project],
                f"{buggy} ({buggy / len(data) * 100:.2f}%)",
                f"{len(data) - buggy} ({(len(data) - buggy) / len(data) * 100:.2f}%)",
                sum(changed_methods) / len(data),
                sum(changed_lines) / len(data),
                sum(method_lts) / len(data),
                commits_gap,
                f"{start_date.date()} ~ {end_date.date()}",
            ]
        )

    defective_sum = sum([int(row[1].split("(")[0].strip()) for row in table])
    clean_sum = sum([int(row[2].split("(")[0].strip()) for row in table])
    table.append(
        [
            "Total",
            f"{defective_sum} ({defective_sum / (defective_sum + clean_sum) * 100:.2f}%)",
            f"{clean_sum} ({clean_sum / (defective_sum + clean_sum) * 100:.2f}%)",
            sum([row[3] for row in table]) / len(PROJECTS),
            sum([row[4] for row in table]) / len(PROJECTS),
            sum([row[5] for row in table]) / len(PROJECTS),
            sum([row[6] for row in table]) / len(PROJECTS),
            "",
        ]
    )

    output = tabulate(
        table,
        headers=[
            "Project",
            "Defective Commits",
            "Clean Commits",
            "Changed Methods",
            "Changed Lines (avg.)",
            "Context Sizes (avg.)",
            "Fixing Time (avg.)",
            "Duration",
        ],
        tablefmt=fmt,
        floatfmt=".1f",
    )
    print(output)
    return output

@app.command()
def plot_commit_distribution(
    ours: bool = typer.Option(False, help="Plot for our dataset"),
):
    """
    Generate plots for Commit Distribution
    """
    all_projects_data = []

    for project in PROJECTS:
        if ours:
            data = pd.read_csv(f"data/dataset/combined/{project}.csv")
            data = data.loc[data["project"] == project]
            data["date"] = pd.to_datetime(data["date"])
        else:
            data = pd.read_csv("data/dataset/apachejit_total.csv")
            data = data.loc[data["project"] == f"apache/{project}"]
            data = data.rename(columns={"author_date": "date"})
            data["date"] = pd.to_datetime(data["date"], unit="s")
        data = data.set_index(["date"])
        data = data.sort_index()

        monthly_bug_counts = data.resample("M")["buggy"].value_counts().unstack(fill_value=0)
        monthly_bug_counts["total"] = monthly_bug_counts[False] + monthly_bug_counts[True]
        monthly_bug_counts["project"] = project

        monthly_bug_counts["month_number"] = range(1, len(monthly_bug_counts) + 1)

        all_projects_data.append(monthly_bug_counts)

    num_projects = len(PROJECTS)
    cols = 2
    rows = (num_projects + 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(10, 9))

    for i, (project, ax) in enumerate(zip(PROJECTS, axes.flatten())):
        project_data = all_projects_data[i]
        
        ax.plot(project_data['month_number'], project_data[True], color='red')
        ax.fill_between(project_data['month_number'], project_data[True], color='red', alpha=0.3)
        ax.plot(project_data['month_number'], project_data['total'], color='black')
        ax.axvline(x=4, color='green', linestyle='--')
        ax.set_title(project.capitalize())

    if num_projects % cols != 0:
        for j in range(num_projects, rows * cols):
            fig.delaxes(axes.flatten()[j])

    save_path = f"data/output/plots/commit_distribution_{'ours' if ours else 'apachejit'}.png"
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"Saved plot to {save_path}")


if __name__ == "__main__":
    app()
