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
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    f1_score,
    matthews_corrcoef,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from lime.lime_tabular import LimeTabularExplainer
from typer import Typer, Argument, Option

from neurojit.commit import Mining
from neurojit.tools.data_utils import KFoldDateSplit
from environment import (
    CUF,
    BASELINE,
    COMBINED,
    FEATURE_SET,
    ACTIONABLE_FEATURES,
    PROJECTS,
    SEED,
    PERFORMANCE_METRICS,
)
from data_utils import load_project_data

warnings.filterwarnings("ignore")
app = Typer()


def evaluate(y_test, y_pred, y_pred_proba):
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    fpr = fp / (fp + tn)
    score = {
        "f1_macro": f1_score(y_test, y_pred, average="macro"),
        "mcc": matthews_corrcoef(y_test, y_pred),
        "brier": brier_score_loss(y_test, y_pred_proba),
        "fpr": fpr,
        "auc": roc_auc_score(y_test, y_pred),
    }
    return {k: v for k, v in score.items() if k in PERFORMANCE_METRICS}


def get_model(model: str):
    if model == "random_forest":
        return RandomForestClassifier(random_state=SEED, n_jobs=1)
    elif model == "xgboost":
        return XGBClassifier(random_state=SEED, n_jobs=1)
    elif model == "naive_bayes":
        return GaussianNB()
    elif model == "logistic_regression":
        return LogisticRegression(random_state=SEED)
    elif model == "svm":
        return SVC(random_state=SEED, probability=True)
    elif model == "knn":
        return KNeighborsClassifier()
    elif model == "decision_tree":
        return DecisionTreeClassifier(random_state=SEED)
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
        str, Argument(help="Feature set to use: baseline|cuf|combined")
    ],
    smote: Annotated[bool, Option(help="Use SMOTE for oversampling")] = True,
    display: Annotated[bool, Option(help="Display progress bar")] = False,
    output_dir: Annotated[Path, Option(help="Output directory")] = Path("data/output"),
    save_model: Annotated[bool, Option(help="Save models")] = True,
    load_model: Annotated[bool, Option(help="Load models")] = False,
    save_dir: Annotated[Path, Option(help="Save directory")] = Path("data/pickles"),
):
    """
    Train and test the baseline/cuf/combined model with 20 folds Just-In-Time Software Defect Prediction (JIT-SDP)
    """
    console = Console(quiet=not display)
    scores = []
    total_data = load_project_data()
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
            y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
            score = evaluate(y_test, y_pred, y_pred_proba)
            # True positive samples
            tp_index = (y_test == 1) & (y_pred == 1)
            score["tp_samples"] = test.loc[tp_index, "commit_id"].tolist()

            # Positive samples
            pos_index = y_pred == 1
            score["pos_samples"] = test.loc[pos_index, "commit_id"].tolist()

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
    output_dir: Annotated[Path, Option(help="Output directory")] = Path("data/output"),
    load_model: Annotated[bool, Option(help="Load models")] = True,
    pickles_dir: Annotated[Path, Option(help="Pickles directory")] = Path(
        "data/pickles"
    ),
):
    """
    Compute the ratios of actionable features for the baseline and combined models for the true positive samples in the 20 folds JIT-SDP
    """
    console = Console(quiet=not display)
    scores = []
    total_data = load_project_data()
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

            combined_X_train, baseline_X_train, y_train = (
                train[COMBINED],
                train[BASELINE],
                train["buggy"],
            )
            combined_X_test, baseline_X_test, y_test = (
                test[COMBINED],
                test[BASELINE],
                test["buggy"],
            )

            if load_model:
                combined_model = pickle.load(
                    open(pickles_dir / model / "combined" / project / f"{i}.pkl", "rb")
                )
                baseline_model = pickle.load(
                    open(pickles_dir / model / "baseline" / project / f"{i}.pkl", "rb")
                )
            else:
                combined_model = simple_pipeline(get_model(model), smote=smote)
                baseline_model = simple_pipeline(get_model(model), smote=smote)

                combined_model.fit(combined_X_train, y_train)
                baseline_model.fit(baseline_X_train, y_train)

            cuf_y_pred = combined_model.predict(combined_X_test)
            base_y_pred = baseline_model.predict(baseline_X_test)

            # LIME explanation
            our_explainer = LimeTabularExplainer(
                combined_X_train.values,
                feature_names=combined_X_train.columns,
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
            tp_index = (y_test == 1) & (cuf_y_pred == 1) & (base_y_pred == 1)
            if sum(tp_index) == 0:
                continue

            for idx, row in test.loc[tp_index].iterrows():
                commit_id = row.commit_id
                our_explanation = our_explainer.explain_instance(
                    row[COMBINED],
                    combined_model.predict_proba,
                    num_features=len(COMBINED),
                )

                baseline_explanation = baseline_explainer.explain_instance(
                    row[BASELINE],
                    baseline_model.predict_proba,
                    num_features=len(BASELINE),
                )

                our_top_features = our_explanation.as_map()[1]
                our_top_feature_index = [f[0] for f in our_top_features]
                our_top5_features = combined_X_train.columns[
                    our_top_feature_index
                ].tolist()[:5]

                baseline_top_features = baseline_explanation.as_map()[1]
                baseline_top_feature_index = [f[0] for f in baseline_top_features]
                baseline_top5_features = baseline_X_train.columns[
                    baseline_top_feature_index
                ].tolist()[:5]

                our_actionable_ratio = (
                    len(set(our_top5_features) & set(ACTIONABLE_FEATURES)) / 5
                )
                baseline_actionable_ratio = (
                    len(set(baseline_top5_features) & set(ACTIONABLE_FEATURES)) / 5
                )

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
    save_path = output_dir / f"actionable_{model}.csv"
    scores_df.to_csv(save_path, index=False)
    console.print(f"Results saved at {save_path}")


if __name__ == "__main__":
    app()
