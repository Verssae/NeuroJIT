import json
from pathlib import Path
from typing import List
from typing_extensions import Annotated

import typer
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from tabulate import tabulate
import matplotlib.font_manager as fm

from neurojit.tools.correlation import group_difference
from visualization import radar_factory
from environment import PROJECTS, PERFORMANCE_METRICS


app = typer.Typer()


def load_data(
    jsons: List[Path],
) -> pd.DataFrame:
    data = []
    for json_file in jsons:
        with open(json_file) as f:
            data.extend(json.load(f))

    return pd.DataFrame(data)


@app.command()
def plot_radars(
    rf_baseline: Annotated[
        Path, typer.Argument(exists=True, file_okay=True, readable=True)
    ] = Path("data/output/random_forest_baseline.json"),
    rf_baseline_cuf: Annotated[
        Path, typer.Argument(exists=True, file_okay=True, readable=True)
    ] = Path("data/output/random_forest_combined.json"),
    xgb_baseline: Annotated[
        Path, typer.Argument(exists=True, file_okay=True, readable=True)
    ] = Path("data/output/xgboost_baseline.json"),
    xgb_baseline_cuf: Annotated[
        Path, typer.Argument(exists=True, file_okay=True, readable=True)
    ] = Path("data/output/xgboost_combined.json"),
    save_dir: Annotated[Path, typer.Option()] = Path("data/plots/analysis"),
):
    """
    Generate radar charts for performance comparison between models
    """
    rf_df = load_data([rf_baseline_cuf, rf_baseline])
    xgb_df = load_data([xgb_baseline_cuf, xgb_baseline])

    ours = rf_baseline_cuf.stem.split("_")[-1]
    baseline = rf_baseline.stem.split("_")[-1]

    rf = (
        rf_df.drop(columns=["tp_samples"])
        .groupby(["project", "features"])
        .agg("median")
    )

    xgb = (
        xgb_df.drop(columns=["tp_samples"])
        .groupby(["project", "features"])
        .agg("median")
    )

    sns.plotting_context("paper")
    plt.rc("font", family="Times New Roman")
    palette_rf = ["#8DE5A1", "#FF9F9B"]
    palette_xgb = ["#A1C9F4", "#FFB482"]
    grey = sns.color_palette("Greys", n_colors=9)

    for i in range(len(PERFORMANCE_METRICS)):
        fig = plt.figure(figsize=(8, 8))

        performance_df = rf[PERFORMANCE_METRICS[i]].unstack()

        performance_df = performance_df.reindex(index=PROJECTS.keys())

        theta = radar_factory(len(performance_df), frame="polygon")
        case_data = performance_df.loc[:, [ours, baseline]].values.T

        ax = fig.add_subplot(1, 1, 1, projection="radar")

        if i == len(PERFORMANCE_METRICS) - 1:
            # reverse case_data order
            case_data = case_data[::-1]
            palette_rf = palette_rf[::-1]

        ax.plot(
            theta,
            case_data[0],
            label=performance_df.index[0],
            color=palette_rf[0],
            linewidth=3,
        )
        ax.fill(theta, case_data[0], alpha=0.3, color=palette_rf[0])

        ax.fill(theta, case_data[1], alpha=1, color="white")

        ax.plot(
            theta,
            case_data[1],
            label=performance_df.index[1],
            color=palette_rf[1],
            linewidth=3,
        )
        ax.fill(theta, case_data[1], alpha=0.3, color=palette_rf[1])

        lines, texts = ax.set_varlabels([])
        ax.tick_params(labelsize=16, pad=20, colors=grey[4])

        save_path = save_dir / f"radar_chart_rf_{PERFORMANCE_METRICS[i]}.svg"
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, format="svg", bbox_inches="tight")

    for i in range(len(PERFORMANCE_METRICS)):
        fig = plt.figure(figsize=(8, 8))

        performance_df = xgb[PERFORMANCE_METRICS[i]].unstack()

        performance_df = performance_df.reindex(index=PROJECTS.keys())

        theta = radar_factory(len(performance_df), frame="polygon")
        case_data = performance_df.loc[:, [ours, baseline]].values.T

        ax = fig.add_subplot(1, 1, 1, projection="radar")

        if i == len(PERFORMANCE_METRICS) - 1:
            # reverse case_data order
            case_data = case_data[::-1]
            palette_xgb = palette_xgb[::-1]

        ax.plot(
            theta,
            case_data[0],
            label=performance_df.index[0],
            color=palette_xgb[0],
            linewidth=3,
        )
        ax.fill(theta, case_data[0], alpha=0.3, color=palette_xgb[0])

        ax.fill(theta, case_data[1], alpha=1, color="white")

        ax.plot(
            theta,
            case_data[1],
            label=performance_df.index[1],
            color=palette_xgb[1],
            linewidth=3,
        )
        ax.fill(theta, case_data[1], alpha=0.3, color=palette_xgb[1])

        lines, texts = ax.set_varlabels([])
        ax.tick_params(labelsize=16, pad=20, colors=grey[4])

        save_path = save_dir / f"radar_chart_xgb_{PERFORMANCE_METRICS[i]}.svg"
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, format="svg", bbox_inches="tight")

    plt.close()


@app.command()
def table_performances(
    json1: Annotated[Path, typer.Argument(exists=True, file_okay=True)],
    json2: Annotated[Path, typer.Argument(exists=True, file_okay=True)],
    fmt: Annotated[str, typer.Option()] = "github",
    quiet: Annotated[bool, typer.Option()] = False,
):
    """
    Generate table for performance comparison between models
    """
    result_df = load_data([json1, json2])
    table = []
    features_1 = json1.stem.split("_")[-1]
    features_2 = json2.stem.split("_")[-1]

    for project in PROJECTS:
        row1 = [PROJECTS[project], f"{features_1}"]
        row2 = ["", f"{features_2.split('_')[0]}"]

        for performance in PERFORMANCE_METRICS:
            score_1 = result_df.loc[
                (result_df["project"] == project)
                & (result_df["features"] == features_1),
                performance,
            ]
            score_2 = result_df.loc[
                (result_df["project"] == project)
                & (result_df["features"] == features_2),
                performance,
            ]
            significance = group_difference(score_1, score_2, fmt="str")
            row1.extend([f"{score_1.agg('mean'):.3f}"])
            row2.extend([f"{score_2.agg('mean'):.3f} {significance}"])

        table.append(row1)
        table.append(row2)

    output = tabulate(
        table,
        headers=["Project", "Features", *PERFORMANCE_METRICS],
        tablefmt=fmt,
    )

    if not quiet:
        print(f"#### {features_1.capitalize()} vs {features_2.capitalize()}")
        print(output)

    return output


@app.command()
def table_set_relationships(
    baseline_json: Annotated[Path, typer.Argument(exists=True, file_okay=True)],
    cuf_json: Annotated[Path, typer.Argument(exists=True, file_okay=True)],
    fmt: Annotated[str, typer.Option()] = "github",
    quiet: Annotated[bool, typer.Option()] = False,
    only_tp: Annotated[bool, typer.Option()] = True
):
    """
    Generate table for TPs predicted by baseline model only vs cuf model only
    """
    result_df = load_data([baseline_json, cuf_json])
    features_1 = baseline_json.stem
    features_2 = cuf_json.stem
    table = []

    for project in PROJECTS:
        only_1_ratio = []
        only_2_ratio = []
        intersection_ratio = []

        for i in range(10):
            project_df = result_df.loc[
                (result_df["project"] == project)
                & (result_df["features"] == features_1)
                & (result_df["fold"] == i)
            ]
            project_df_2 = result_df.loc[
                (result_df["project"] == project)
                & (result_df["features"] == features_2)
                & (result_df["fold"] == i)
            ]

            if only_tp:
                tp_samples_1 = set(project_df["tp_samples"].explode())
                tp_samples_2 = set(project_df_2["tp_samples"].explode())

                if len(tp_samples_1 | tp_samples_2) == 0:
                    continue

                only_1_ratio.append(
                    len(tp_samples_1 - tp_samples_2) / len(tp_samples_1 | tp_samples_2)
                )
                only_2_ratio.append(
                    len(tp_samples_2 - tp_samples_1) / len(tp_samples_1 | tp_samples_2)
                )
                intersection_ratio.append(
                    len(tp_samples_1 & tp_samples_2) / len(tp_samples_1 | tp_samples_2)
                )
            else:
                pos_samples_1 = set(project_df["pos_samples"].explode())
                pos_samples_2 = set(project_df_2["pos_samples"].explode())

                if len(pos_samples_1 | pos_samples_2) == 0:
                    continue

                only_1_ratio.append(
                    len(pos_samples_1 - pos_samples_2) / len(pos_samples_1 | pos_samples_2)
                )
                only_2_ratio.append(
                    len(pos_samples_2 - pos_samples_1) / len(pos_samples_1 | pos_samples_2)
                )
                intersection_ratio.append(
                    len(pos_samples_1 & pos_samples_2) / len(pos_samples_1 | pos_samples_2)
                )

        table.append(
            [
                PROJECTS[project],
                f"{pd.Series(only_1_ratio).agg('mean') * 100:2.1f}%",
                f"{pd.Series(intersection_ratio).agg('mean') * 100:2.1f}%",
                f"{pd.Series(only_2_ratio).agg('mean') * 100:2.1f}%",
            ]
        )

    table = sorted(table, key=lambda x: float(x[1].replace("%", "")), reverse=True)

    output = tabulate(
        table,
        headers=[
            "Project",
            f"{features_1} only",
            "Intersection",
            f"{features_2.split('_')[0]} only",
        ],
        floatfmt=".2f",
        tablefmt=fmt,
    )

    if not quiet:
        print(f"{features_1} vs {features_2}")
        print(output)

    return output


@app.command()
def plot_set_relationships(
    baseline_json: Annotated[Path, typer.Argument(exists=True, file_okay=True)] = Path("data/output/random_forest_baseline.json"),
    cuf_json: Annotated[Path, typer.Argument(exists=True, file_okay=True)] = Path("data/output/random_forest_cuf.json"),
    save_path: Annotated[Path, typer.Option()] = Path(
        "data/plots/analysis/diff_plot.svg"
    ),
    only_tp: Annotated[bool, typer.Option()] = True
):
    """
    Generate plots for TPs predicted by baseline model only vs cuf model only
    """
    result_df = load_data([baseline_json, cuf_json])
    features_1 = baseline_json.stem.split("_")[-1]
    features_2 = cuf_json.stem.split("_")[-1]
    table = []

    for project in PROJECTS:
        only_1_ratio = []
        only_2_ratio = []
        intersection_ratio = []

        for i in range(20):
            project_df = result_df.loc[
                (result_df["project"] == project)
                & (result_df["features"] == features_1)
                & (result_df["fold"] == i)
            ]
            project_df_2 = result_df.loc[
                (result_df["project"] == project)
                & (result_df["features"] == features_2)
                & (result_df["fold"] == i)
            ]

            if only_tp:
                tp_samples_1 = set(project_df["tp_samples"].explode())
                tp_samples_2 = set(project_df_2["tp_samples"].explode())

                if len(tp_samples_1 | tp_samples_2) == 0:
                    continue

                only_1_ratio.append(
                    len(tp_samples_1 - tp_samples_2) / len(tp_samples_1 | tp_samples_2)
                )
                only_2_ratio.append(
                    len(tp_samples_2 - tp_samples_1) / len(tp_samples_1 | tp_samples_2)
                )
                intersection_ratio.append(
                    len(tp_samples_1 & tp_samples_2) / len(tp_samples_1 | tp_samples_2)
                )
            else:
                pos_samples_1 = set(project_df["pos_samples"].explode())
                pos_samples_2 = set(project_df_2["pos_samples"].explode())

                if len(pos_samples_1 | pos_samples_2) == 0:
                    continue

                only_1_ratio.append(
                    len(pos_samples_1 - pos_samples_2) / len(pos_samples_1 | pos_samples_2)
                )
                only_2_ratio.append(
                    len(pos_samples_2 - pos_samples_1) / len(pos_samples_1 | pos_samples_2)
                )
                intersection_ratio.append(
                    len(pos_samples_1 & pos_samples_2) / len(pos_samples_1 | pos_samples_2)
                )


        table.append(
            [
                PROJECTS[project],
                pd.Series(only_1_ratio).agg("mean"),
                pd.Series(intersection_ratio).agg("mean"),
                pd.Series(only_2_ratio).agg("mean"),
            ]
        )
    df = pd.DataFrame(table, columns=["Project", "Baseline", "Intersection", "cuf"])

    # plot stacked barh plot using seaborn
    palette = sns.color_palette("pastel", n_colors=5)
    df = df.set_index("Project")
    plt.figure(figsize=(4.5, 6))
    # sns.plotting_context("paper")
    font_files = fm.findSystemFonts(fontpaths=fm.OSXFontDirectories[-1], fontext="ttf")
    font_files = [ f for f in font_files if "LinLibertine" in f]
    for font_file in font_files:
        fm.fontManager.addfont(font_file)
    
    plt.rcParams["font.family"] = "Linux Libertine"

    df = df.sort_values(by="cuf", ascending=False)
    df["bar2"] = df["cuf"] + df["Intersection"]
    df["bar3"] = df["bar2"] + df["Baseline"]
    sns.barplot(data=df, y=df.index, x="bar3", color=palette[3], orient="h")
    sns.barplot(data=df, y=df.index, x="bar2", color=palette[4], orient="h")
    ax = sns.barplot(data=df, y=df.index, x="cuf", color=palette[2], orient="h")

    labels = []
    labels.extend(df["Baseline"].values)
    labels.extend(df["Intersection"].values)
    labels.extend(df["cuf"].values)

    for i, p in enumerate(ax.patches):
        width = labels[i] * 100
        if 0 <= i < len(PROJECTS):
            ax.text(
                labels[i + len(PROJECTS) * 2]
                + labels[i + len(PROJECTS)]
                + (labels[i] / 2),
                p.get_y() + p.get_height() / 2,
                f"{round(width, 1)}",
                va="center",
                ha="center",
                fontsize=20,
                # fontweight="bold",
                color="black",
            )
        elif len(PROJECTS) <= i < len(PROJECTS) * 2:
            ax.text(
                labels[i + len(PROJECTS)] + (labels[i] / 2),
                p.get_y() + p.get_height() / 2,
                f"{round(width, 1)}",
                va="center",
                ha="center",
                fontsize=20,
                # fontweight="bold",
                color="black",
            )
        else:
            ax.text(
                labels[i] / 2,
                p.get_y() + p.get_height() / 2,
                f"{round(width, 1)}",
                va="center",
                ha="center",
                fontsize=20,
                # fontweight="bold",
                color="black",
            )

    top_bar = mpatches.Patch(color=palette[3], label="understand", linewidth=0.5)
    middle_bar = mpatches.Patch(color=palette[4], label="intersection", linewidth=0.5)
    bottom_bar = mpatches.Patch(color=palette[2], label="baseline", linewidth=0.5)
    plt.legend(
        handles=[top_bar, middle_bar, bottom_bar],
        labels=["baseline", "intersection", "understand"],
        loc="lower center",
        ncol=3,
        fontsize=16,
        frameon=False,
        bbox_to_anchor=(0.5, -0.12),
    )

    plt.xticks([])
    plt.xlabel(None)
    plt.yticks(fontsize=20)
    plt.ylabel(None)

    sns.despine(bottom=True, right=True, top=True, left=True)

    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, bbox_inches="tight", dpi=300, format="svg")
    plt.close()
    print(save_path)


@app.command()
def table_actionable(
    path: Annotated[Path, typer.Argument(exists=True, file_okay=True)] = Path("data/output/actionable.csv"),
    fmt: Annotated[str, typer.Option()] = "github",
):
    """
    Tabulate the results of the actionable features
    """
    scores_df = pd.read_csv(path)
    table = []
    for project in scores_df.project.unique():
        project_df = scores_df[scores_df.project == project]
        gd = group_difference(
            project_df.our_actionable_ratio,
            project_df.baseline_actionable_ratio,
            fmt="str",
        )
        our_mean = project_df.our_actionable_ratio.mean() * 100
        baseline_mean = project_df.baseline_actionable_ratio.mean() * 100
        table.append([project, our_mean, baseline_mean, gd])

    table.append(
        [
            "Average",
            sum([t[1] for t in table]) / len(table),
            sum([t[2] for t in table]) / len(table),
            "",
        ]
    )
    print(
        tabulate(
            table,
            headers=["Project", "combined", "baseline", "Wilcoxon, Cliff's Delta"],
            tablefmt=fmt,
            floatfmt=".1f",
        )
    )


if __name__ == "__main__":
    app()
