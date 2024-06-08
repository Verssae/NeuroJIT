import warnings
from pathlib import Path
from typing_extensions import Annotated

import typer
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tabulate import tabulate
from scipy.stats import ranksums
from cliffs_delta import cliffs_delta
from matplotlib import font_manager as fm

from hcc_cal.commit import Mining
from visualization import visualize_hmap
from hcc_cal.tools.correlation import group_difference, significances
from environment import BASE_ALL, CUF_ALL, PROJECTS, COMBINED, CUF, BASELINE

warnings.filterwarnings("ignore")

app = typer.Typer()


def corr_plot(results_cuf, results_combined, save_dir, top_k=10):
    """
    2 x 2 plot
    """
    font_files = fm.findSystemFonts(fontpaths=fm.OSXFontDirectories[-1], fontext="ttf")
    font_files = [ f for f in font_files if "LinLibertine" in f]
    for font_file in font_files:
        fm.fontManager.addfont(font_file)
    # sns.set_context("paper")
    plt.rcParams["font.family"] = "Linux Libertine"

    palette = sns.color_palette("pastel", n_colors=4)
    base_color = palette[3]
    hcc_color = palette[2]
    greys = sns.color_palette("Greys", n_colors=9)

    results_combined["jit-sdp"] = results_combined["metric"].apply(
        lambda x: "baseline" if x in BASELINE else "understandability"
    )

    results_cuf["metric"] = results_cuf["metric"].apply(
        lambda x: x.replace("DD_HV", "DD/HV")
    )

    results_combined["metric"] = results_combined["metric"].apply(
        lambda x: x.replace("DD_HV", "DD/HV")
    )

    results_cuf["adjusted_odds"] = results_cuf["lr_odds_ratio"].apply(lambda x: x - 1)
    results_cuf["abs_odds"] = results_cuf["adjusted_odds"].abs()

    results_combined["adjusted_odds"] = results_combined["lr_odds_ratio"].apply(lambda x: x - 1)
    results_combined["abs_odds"] = results_combined["adjusted_odds"].abs()

    results_cuf = results_cuf.sort_values(by="abs_odds", ascending=False)
    results_combined = results_combined.sort_values(by="abs_odds", ascending=False)

    plt.figure(figsize=(3, 3.5))

    for i, row in results_cuf.iterrows():
        plt.errorbar(
            x=row["lr_odds_ratio"],
            y=row["metric"],
            xerr=[
                [row["lr_odds_ratio"] - row["lr_conf_lower"]],
                [row["lr_conf_upper"] - row["lr_odds_ratio"]],
            ],
            fmt="none",
            ecolor=greys[-2],
        )

    ax = sns.pointplot(
        x="lr_odds_ratio",
        y="metric",
        data=results_cuf,
        join=False,
        color=hcc_color,
        ci=None,
        markers="o",
        capsize=0.1,
    )

    plt.yticks(range(len(results_cuf)), results_cuf["metric"])
    plt.axvline(1, color=greys[8], linestyle="--")
    plt.xlabel("")
    # plt.title("HCC features", fontweight="bold", fontsize=16, pad=10)

    plt.ylabel("")

    for text in ax.get_yticklabels():
        # if significant, bold
        if (
            results_cuf.loc[
                results_cuf["metric"] == text.get_text(), "lr_p_value"
            ].values[0]
            < 0.05
        ):
            text.set_fontweight("bold")
        text.set_fontsize(16)

    for text in ax.get_xticklabels():
        text.set_fontsize(16)

    plt.tight_layout()
    sns.despine(top=True, right=True)
    plt.savefig(
        save_dir / "corr_hcc_lr.svg",
        bbox_inches="tight",
        dpi=300,
        format="svg",
    )
    plt.close()

    plt.figure(figsize=(3, 3.5))
    
    for i, row in results_combined[:top_k].iterrows():
        plt.errorbar(
            x=row["lr_odds_ratio"],
            y=row["metric"],
            xerr=[
                [row["lr_odds_ratio"] - row["lr_conf_lower"]],
                [row["lr_conf_upper"] - row["lr_odds_ratio"]],
            ],
            fmt="none",
            ecolor=greys[-2],
        )

    ax = sns.pointplot(
        x="lr_odds_ratio",
        y="metric",
        data=results_combined[:top_k],
        join=False,
        hue="jit-sdp",
        hue_order=["baseline", "understandability"],
        palette=(base_color, hcc_color),
        ci=None,
        markers="o",
        capsize=0.1,
    )

    plt.yticks(range(len(results_combined[:top_k])), results_combined[:top_k]["metric"])
    plt.axvline(1, color=greys[8], linestyle="--")
    plt.xlabel("")
    # plt.title("Top 9 baseline+HCC features", fontweight="bold", fontsize=16, pad=10)

    plt.ylabel("")

    for text in ax.get_yticklabels():
        # if significant, bold
        if (
            results_combined[:top_k]
            .loc[results_combined[:top_k]["metric"] == text.get_text(), "lr_p_value"]
            .values[0]
            < 0.05
        ):
            text.set_fontweight("bold")
        text.set_fontsize(16)

    for text in ax.get_xticklabels():
        text.set_fontsize(16)
    plt.legend().remove()
    plt.tight_layout()
    sns.despine(top=True, right=True)
    plt.savefig(
        save_dir / "corr_baseline+hcc_lr.svg",
        bbox_inches="tight",
        dpi=300,
        format="svg",
    )
    plt.close()



def load_data():
    total = []
    for project in PROJECTS:
        data = pd.read_csv(f"data/dataset/filtered/{project}.csv")
        total.append(data)
    data = pd.concat(total)
 
    # data = pd.read_csv("data/dataset/to_preprocess.csv", index_col="commit_id")



    return data


@app.command()
def plot_corr():
    """
    Generate plots for Correlations between HCC Features and Defect-inducing Risks
    """
    data = load_data()

    y = data["buggy"]


    X = data[CUF]

    results_ccc = significances(X, y, metrics=CUF)

    X = data[COMBINED]
    results_kc = significances(X, y, metrics=COMBINED)

    save_dir = Path("data/plots/pre_analysis/significance_ase")
    save_dir.mkdir(exist_ok=True, parents=True)

    corr_plot(results_ccc, results_kc, save_dir=save_dir, top_k=9)

    from rich import console
    
    console = console.Console()
    df = pd.DataFrame(results_ccc)
    console.print(df.T)


@app.command()
def plot_hmap():
    """
    Generate plots for Collinearity between Features
    """
    data = load_data()

    X = data[BASELINE + CUF]
    save_path = "data/plots/pre_analysis/hmap/ALL.svg"
    visualize_hmap(X.corr(method="spearman"), size=7, save_path=save_path)

    X = data[CUF_ALL]
    save_path = "data/plots/pre_analysis/hmap/ALL_H.svg"
    visualize_hmap(X.corr(method="spearman"), size=5, save_path=save_path)

    X = data[BASE_ALL]
    save_path = "data/plots/pre_analysis/hmap/ALL_B.svg"
    visualize_hmap(X.corr(method="spearman"), size=5, save_path=save_path)


@app.command()
def table_group_diff(
    fmt: Annotated[str, typer.Option()] = "github",
):
    """
    Tabulate the group differences between buggy and clean commits for HCC
    """
    data = load_data()
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
    Tabulate the group differences between buggy and clean commits for HCC (each project)
    """
    data = load_data()
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
        # hcc_data = pd.read_csv(f"data/dataset/hcc/{project}.csv")
        # hcc_data = hcc_data.drop(columns=["fix_date", "target"])

        # baseline_data = pd.read_csv("data/dataset/baseline.csv")

        # data = hcc_data.merge(
        #     baseline_data, on=["commit_id", "project", "gap", "buggy", "date"]
        # )
        data = pd.read_csv(f"data/dataset/filtered/{project}.csv")

        data["date"] = pd.to_datetime(data["date"])
        data = data.set_index(["date"])
        data = data.sort_index()

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

    table.append(
        [
            "Total",
            "",
            "",
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


if __name__ == "__main__":
    app()
