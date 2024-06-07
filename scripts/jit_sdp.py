import json
import pickle
import warnings
from pathlib import Path
from typing_extensions import Annotated

import pandas as pd
from rich.console import Console
from rich.progress import track
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score,
    matthews_corrcoef,
    brier_score_loss,
)
from sklearn.preprocessing import StandardScaler, RobustScaler
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from lime.lime_tabular import LimeTabularExplainer
from tabulate import tabulate
from typer import Typer, Argument, Option

from hcc_cal.commit import Mining
from hcc_cal.tools.data_utils import KFoldDateSplit
from hcc_cal.tools.correlation import group_difference
from environment import (
    HCC,
    BASELINE,
    BASELINE_HCC,
    FEATURE_SET,
    INACTIONABLE_FEATURES,
    PROJECTS,
    SEED,
    PERFORMANCE_METRICS,
)
from pre_analysis import load_data

warnings.filterwarnings("ignore")
app = Typer()


def evaluate(y_test, y_pred):
    score = {
        "f1_macro": f1_score(y_test, y_pred, average="macro"),
        "mcc": matthews_corrcoef(y_test, y_pred),
        "brier": brier_score_loss(y_test, y_pred),
    }
    return {k: v for k, v in score.items() if k in PERFORMANCE_METRICS}


def get_model(model: str):
    if model == "random_forest":
        return RandomForestClassifier(random_state=SEED, n_jobs=1)
    elif model == "xgboost":
        return XGBClassifier(random_state=SEED, n_jobs=1)
    else:
        raise ValueError(f"Not supported model: {model}")


def simple_pipeline(base_model, smote=True):
    steps = []
    steps.append(("scaler", StandardScaler()))
    if smote:
        steps.append(("smote", SMOTE(random_state=SEED)))
        steps.append(("model", base_model))
        return ImbPipeline(steps)
    else:
        steps.append(("model", base_model))
        return Pipeline(steps)


@app.command()
def train_test(
    model: Annotated[str, Argument(help="Model to use: random_forest|xgboost")],
    features: Annotated[
        str, Argument(help="Feature set to use: baseline|HCC|baseline+HCC")
    ],
    smote: Annotated[bool, Option(help="Use SMOTE for oversampling")] = True,
    display: Annotated[bool, Option(help="Display progress bar")] = False,
    baseline_dir: Annotated[Path, Option(help="Baseline data directory")] = Path(
        "data/dataset/baseline"
    ),
    hcc_dir: Annotated[Path, Option(help="HCC data directory")] = Path(
        "data/dataset/hcc"
    ),
    output_dir: Annotated[Path, Option(help="Output directory")] = Path("data/output"),
    save_model: Annotated[bool, Option(help="Save models")] = True,
    load_model: Annotated[bool, Option(help="Load models")] = False,
    save_dir: Annotated[Path, Option(help="Save directory")] = Path("data/pickles"),
):
    """
    Train and test the baseline/HCC/baseline+HCC model with 20 folds Just-In-Time Software Defect Prediction (JIT-SDP)
    """
    console = Console(quiet=not display)
    scores = []
    total_data = load_data()
    for project in track(
        PROJECTS,
        description="Projects...",
        console=console,
        total=len(PROJECTS),
    ):
        data = total_data.loc[total_data["project"] == project].copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.set_index(["date"])
        

        splitter = KFoldDateSplit(
            data, k=20, start_gap=3, end_gap=3, is_mid_gap=True, sliding_months=1
        )

        for i, (train, test) in enumerate(splitter.split()):
            X_train, y_train = train[FEATURE_SET[features]], train["buggy"]
            X_test, y_test = test[FEATURE_SET[features]], test["buggy"]

            if load_model:
                pickes_dir = save_dir / model / features / project
                load_path = pickes_dir / f"{i}.pkl"
                with open(load_path, "rb") as f:
                    pipeline = pickle.load(f)
            else:
                pipeline = simple_pipeline(get_model(model), smote=smote)
                pipeline.fit(X_train, y_train)

            y_pred = pipeline.predict(X_test)
            score = evaluate(y_test, y_pred)
            # True positive samples
            tp_index = (y_test == 1) & (y_pred == 1)
            score["tp_samples"] = test.loc[tp_index, "commit_id"].tolist()
            score["test"] = len(y_test)
            score["buggy"] = sum(y_test)
            score["project"] = project
            score["fold"] = i
            score["features"] = features

            scores.append(score)

            if save_model:
                pickes_dir = save_dir / model / features / project
                pickes_dir.mkdir(exist_ok=True, parents=True)
                save_path = pickes_dir / f"{i}.pkl"
                with open(save_path, "wb") as f:
                    pickle.dump(pipeline, f)

    output_dir.mkdir(exist_ok=True, parents=True)
    save_path = output_dir / f"{model}_{features}.json"
    with open(save_path, "w") as f:
        json.dump(scores, f, indent=4)
    console.print(f"Results saved at {save_path}")



@app.command()
def actionable(
    model: Annotated[str, Argument(help="Model to use: random_forest|xgboost")],
    smote: Annotated[bool, Option(help="Use SMOTE for oversampling")] = True,
    display: Annotated[bool, Option(help="Display progress bar")] = False,
    baseline_dir: Annotated[Path, Option(help="Baseline data directory")] = Path(
        "data/dataset/baseline"
    ),
    hcc_dir: Annotated[Path, Option(help="HCC data directory")] = Path(
        "data/dataset/hcc"
    ),
    output_dir: Annotated[Path, Option(help="Output directory")] = Path("data/output"),
    load_model: Annotated[bool, Option(help="Load models")] = False,
    pickles_dir: Annotated[Path, Option(help="Pickles directory")] = Path("data/pickles"),
):
    """
    Compute the ratios of actionable features for the baseline and baseline+HCC models for the true positive samples in the 20 folds JIT-SDP
    """
    console = Console(quiet=not display)
    scores = []
    total_data = load_data()
    for project in track(
        PROJECTS,
        description="Projects...",
        console=console,
        total=len(PROJECTS),
    ):
        data = total_data.loc[total_data["project"] == project].copy()
        data["date"] = pd.to_datetime(data["date"])
        data = data.set_index(["date"])

        splitter = KFoldDateSplit(
            data, k=20, start_gap=3, end_gap=3, is_mid_gap=True, sliding_months=1
        )

        for i, (train, test) in enumerate(splitter.split()):

            our_X_train, baseline_X_train, y_train = (
                train[BASELINE_HCC],
                train[BASELINE],
                train["buggy"],
            )
            our_X_test, baseline_X_test, y_test = (
                test[BASELINE_HCC],
                test[BASELINE],
                test["buggy"],
            )

            if load_model:
                our_model = pickle.load(
                    open(pickles_dir / model / "baseline+hcc" / project / f"{i}.pkl", "rb")
                )
                baseline_model = pickle.load(
                    open(pickles_dir / model / "baseline" / project / f"{i}.pkl", "rb")
                )
            else:
                our_model = simple_pipeline(get_model(model), smote=smote)
                baseline_model = simple_pipeline(get_model(model), smote=smote)

                our_model.fit(our_X_train, y_train)
                baseline_model.fit(baseline_X_train, y_train)

            our_y_pred = our_model.predict(our_X_test)
            base_y_pred = baseline_model.predict(baseline_X_test)

            # LIME explanation
            our_explainer = LimeTabularExplainer(
                our_X_train.values,
                feature_names=our_X_train.columns,
                class_names=["not buggy", "buggy"],
                mode="classification",
                discretize_continuous=False,
            )

            baseline_explainer = LimeTabularExplainer(
                baseline_X_train.values,
                feature_names=baseline_X_train.columns,
                class_names=["not buggy", "buggy"],
                mode="classification",
                discretize_continuous=False,
            )

            # Get the explanation for the common tp samples
            tp_index = (y_test == 1) & (our_y_pred == 1) & (base_y_pred == 1)
            if sum(tp_index) == 0:
                continue

            for idx, row in test.loc[tp_index].iterrows():
                commit_id = row.commit_id
                our_explanation = our_explainer.explain_instance(
                    row[BASELINE_HCC],
                    our_model.predict_proba,
                    num_features=len(BASELINE_HCC),
                )

                baseline_explanation = baseline_explainer.explain_instance(
                    row[BASELINE],
                    baseline_model.predict_proba,
                    num_features=len(BASELINE),
                )

                our_top_features = our_explanation.as_map()[1]
                our_top_feature_index = [f[0] for f in our_top_features]
                our_top5_features = our_X_train.columns[our_top_feature_index].tolist()[
                    :5
                ]

                baseline_top_features = baseline_explanation.as_map()[1]
                baseline_top_feature_index = [f[0] for f in baseline_top_features]
                baseline_top5_features = baseline_X_train.columns[
                    baseline_top_feature_index
                ].tolist()[:5]

                our_inactionable_ratio = (
                    len(set(our_top5_features) & set(INACTIONABLE_FEATURES)) / 5
                )
                baseline_inactionable_ratio = (
                    len(set(baseline_top5_features) & set(INACTIONABLE_FEATURES)) / 5
                )

                our_actionable_ratio = 1 - our_inactionable_ratio
                baseline_actionable_ratio = 1 - baseline_inactionable_ratio

                scores.append(
                    {
                        "commit_id": commit_id,
                        "project": project,
                        "fold": i,
                        "our_actionable_ratio": our_actionable_ratio,
                        "baseline_actionable_ratio": baseline_actionable_ratio,
                    }
                )

    scores_df = pd.DataFrame(scores)
    output_dir.mkdir(exist_ok=True, parents=True)
    save_path = output_dir / "actionable.csv"
    scores_df.to_csv(save_path, index=False)
    console.print(f"Results saved at {save_path}")



@app.command()
def tp_samples(
    model: Annotated[str, Argument(help="Model to use: random_forest|xgboost")],
    smote: Annotated[bool, Option(help="Use SMOTE for oversampling")] = True,
    display: Annotated[bool, Option(help="Display progress bar")] = False,
    baseline_dir: Annotated[Path, Option(help="Baseline data directory")] = Path(
        "data/dataset/baseline"
    ),
    hcc_dir: Annotated[Path, Option(help="HCC data directory")] = Path(
        "data/dataset/hcc"
    ),
    output_dir: Annotated[Path, Option(help="Output directory")] = Path("data/output"),
    load_model: Annotated[bool, Option(help="Load models")] = False,
    pickles_dir: Annotated[Path, Option(help="Pickles directory")] = Path("data/pickles"),
):
    """
    Save TP samples as json
    """
    
    console = Console(quiet=not display)



    for project in track(
        PROJECTS,
        description="Projects...",
        console=console,
        total=len(PROJECTS),
    ):
        baseline_data = pd.read_csv(baseline_dir / f"{project}.csv")
        baseline_data = baseline_data.drop(columns=["target", "ENT"])
        hcc_data = pd.read_csv(hcc_dir / f"{project}.csv")
        hcc_data = hcc_data.drop(columns=["fix_date", "target", "Unnamed: 0"])
        data = hcc_data.merge(
            baseline_data, on=["commit_id", "project", "gap", "buggy", "date", "repo"]
        )

        data["date"] = pd.to_datetime(data["date"])
        data = data.set_index(["date"])

        data = data.dropna(subset=list(set(data.columns) - {"gap"}))
        data = data.drop_duplicates(subset=list(set(data.columns) - {"gap"}))

        splitter = KFoldDateSplit(
            data, k=20, start_gap=3, end_gap=3, is_mid_gap=True, sliding_months=1
        )

        hcc_pairs = {}
        baseline_pairs = {}
        common_pairs = {}
        
        metric_pairs = {}

        for i, (train, test) in enumerate(splitter.split()):

            hcc_X_train, baseline_X_train, y_train = (
                train[HCC],
                train[BASELINE],
                train["buggy"],
            )
            hcc_X_test, baseline_X_test, y_test = (
                test[HCC],
                test[BASELINE],
                test["buggy"],
            )

            if load_model:
                hcc_model = pickle.load(
                    open(pickles_dir / model / "hcc" / project / f"{i}.pkl", "rb")
                )
                baseline_model = pickle.load(
                    open(pickles_dir / model / "baseline" / project / f"{i}.pkl", "rb")
                )
            else:
                hcc_model = simple_pipeline(get_model(model), smote=smote)
                baseline_model = simple_pipeline(get_model(model), smote=smote)

                hcc_model.fit(hcc_X_train, y_train)
                baseline_model.fit(baseline_X_train, y_train)

            hcc_y_pred = hcc_model.predict(hcc_X_test)
            base_y_pred = baseline_model.predict(baseline_X_test)

            hcc_only_tp_index = (y_test == 1) & (hcc_y_pred == 1) & (base_y_pred == 0)
            baseline_only_tp_index = (y_test == 1) & (hcc_y_pred == 0) & (base_y_pred == 1)
            common_tp_index = (y_test == 1) & (hcc_y_pred == 1) & (base_y_pred == 1)


            for idx, row in test.loc[hcc_only_tp_index].iterrows():
                commit_id = row.commit_id
                commit = Mining.load("data/cache", row["repo"], commit_id)
                if commit is None:
                    console.log(f"Commit {commit_id} not found")
                    continue
                
                methods = {}
                for m in commit.methods_after:
                    methods[m.signature] = {
                        'after' : m.snippet,
                        'after_col': m.line_numbers_col(True)
                    }

                for m in commit.methods_before:
                    if m.signature in methods:
                        methods[m.signature]['before'] = m.snippet
                        methods[m.signature]['before_col'] = m.line_numbers_col(False)
                    else:
                        methods[m.signature] = {
                            'before' : m.snippet,
                            'before_col': m.line_numbers_col(False)
                        }

                hcc_pairs[commit_id] = []
                for signature, m in methods.items():
                    hcc_pairs[commit_id].append(
                        (
                            signature,
                            m.get('before_col', ''),
                            m.get('before', ''),
                            m.get('after_col', ''),
                            m.get('after', ''),
                        )
                    )
                
                hcc_row =  { f: round(row[HCC][f], 2) for f in HCC }
                baseline_row = { f: round(row[BASELINE][f], 2) for f in BASELINE }

                metric_pairs[commit_id] = {
                    'hcc': hcc_row,
                    'baseline': baseline_row
                }

            for idx, row in test.loc[baseline_only_tp_index].iterrows():
                commit_id = row.commit_id
                commit = Mining.load("data/cache", row["repo"], commit_id)
                if commit is None:
                    console.log(f"Commit {commit_id} not found")
                    continue

                methods = {}
                for m in commit.methods_after:
                    methods[m.signature] = {
                        'after' : m.snippet,
                        'after_col': m.line_numbers_col(True)
                    }

                for m in commit.methods_before:
                    if m.signature in methods:
                        methods[m.signature]['before'] = m.snippet
                        methods[m.signature]['before_col'] = m.line_numbers_col(False)
                    else:
                        methods[m.signature] = {
                            'before' : m.snippet,
                            'before_col': m.line_numbers_col(False)
                        }

                baseline_pairs[commit_id] = []
                for signature, m in methods.items():
                    baseline_pairs[commit_id].append(
                        (
                            signature,
                            m.get('before_col', ''),
                            m.get('before', ''),
                            m.get('after_col', ''),
                            m.get('after', ''),
                        )
                    )

                hcc_row =  { f: round(row[HCC][f], 2) for f in HCC }
                baseline_row = { f: round(row[BASELINE][f], 2) for f in BASELINE }

                metric_pairs[commit_id] = {
                    'hcc': hcc_row,
                    'baseline': baseline_row
                }

            for idx, row in test.loc[common_tp_index].iterrows():
                commit_id = row.commit_id
                commit = Mining.load("data/cache", row["repo"], commit_id)
                if commit is None:
                    console.log(f"Commit {commit_id} not found")
                    continue

                methods = {}
                for m in commit.methods_after:
                    methods[m.signature] = {
                        'after' : m.snippet,
                        'after_col': m.line_numbers_col(True)
                    }

                for m in commit.methods_before:
                    if m.signature in methods:
                        methods[m.signature]['before'] = m.snippet
                        methods[m.signature]['before_col'] = m.line_numbers_col(False)
                    else:
                        methods[m.signature] = {
                            'before' : m.snippet,
                            'before_col': m.line_numbers_col(False)
                        }

                common_pairs[commit_id] = []
                for signature, m in methods.items():
                    common_pairs[commit_id].append(
                        (
                            signature,
                            m.get('before_col', ''),
                            m.get('before', ''),
                            m.get('after_col', ''),
                            m.get('after', ''),
                        )
                    )

                hcc_row =  { f: round(row[HCC][f], 2) for f in HCC }
                baseline_row = { f: round(row[BASELINE][f], 2) for f in BASELINE }

                metric_pairs[commit_id] = {
                    'hcc': hcc_row,
                    'baseline': baseline_row
                }

        will_delete = set()
        for commit_id in hcc_pairs.keys():
            if commit_id in baseline_pairs or commit_id in common_pairs:
                will_delete.add(commit_id)

        for commit_id in baseline_pairs.keys():
            if commit_id in hcc_pairs or commit_id in common_pairs:
                will_delete.add(commit_id)

        for commit_id in will_delete:
            if commit_id in hcc_pairs:
                del hcc_pairs[commit_id]

            if commit_id in baseline_pairs:
                del baseline_pairs[commit_id]

            if commit_id in common_pairs:
                del common_pairs[commit_id]

        console.print(f"Project: {project}: {len(will_delete)} commits are contradictory.")

            

        output_dir.mkdir(exist_ok=True, parents=True)
        save_path = output_dir / f"{project}_hcc.json"
        with open(save_path, "w") as f:
            json.dump(hcc_pairs, f, indent=4)
        


        save_path = output_dir / f"{project}_baseline.json"
        with open(save_path, "w") as f:
            json.dump(baseline_pairs, f, indent=4)

        save_path = output_dir / f"{project}_common.json"
        with open(save_path, "w") as f:
            json.dump(common_pairs, f, indent=4)

        save_path = output_dir / f"{project}_metrics.json"
        with open(save_path, "w") as f:
            json.dump(metric_pairs, f, indent=4)
            
        console.print(f"Results saved at {save_path}")



            # for idx, row in test.loc[baseline_only_tp_index].iterrows():
            #     commit_id = row.commit_id
            #     console.print(f"Baseline only: {commit_id}")

            
            # for idx, row in test.loc[tp_index].iterrows():
            #     commit_id = row.commit_id
            #     our_explanation = our_explainer.explain_instance(
            #         row[BASELINE_HCC],
            #         our_model.predict_proba,
            #         num_features=len(BASELINE_HCC),
            #     )

            #     baseline_explanation = baseline_explainer.explain_instance(
            #         row[BASELINE],
            #         baseline_model.predict_proba,
            #         num_features=len(BASELINE),
            #     )

            #     our_top_features = our_explanation.as_map()[1]
            #     our_top_feature_index = [f[0] for f in our_top_features]
            #     our_top5_features = our_X_train.columns[our_top_feature_index].tolist()[
            #         :5
            #     ]

            #     baseline_top_features = baseline_explanation.as_map()[1]
            #     baseline_top_feature_index = [f[0] for f in baseline_top_features]
            #     baseline_top5_features = baseline_X_train.columns[
            #         baseline_top_feature_index
            #     ].tolist()[:5]

            #     our_actionable_ratio = (
            #         len(set(our_top5_features) & set(ACTIONABLE_FEATURES)) / 5
            #     )
            #     baseline_actionable_ratio = (
            #         len(set(baseline_top5_features) & set(ACTIONABLE_FEATURES)) / 5
            #     )

            #     scores.append(
            #         {
            #             "commit_id": commit_id,
            #             "project": project,
            #             "fold": i,
            #             "our_actionable_ratio": our_actionable_ratio,
            #             "baseline_actionable_ratio": baseline_actionable_ratio,
            #         }
            #     )

    # scores_df = pd.DataFrame(scores)
    # output_dir.mkdir(exist_ok=True, parents=True)
    # save_path = output_dir / "actionable.csv"
    # scores_df.to_csv(save_path, index=False)
    # console.print(f"Results saved at {save_path}")

if __name__ == "__main__":
    app()
