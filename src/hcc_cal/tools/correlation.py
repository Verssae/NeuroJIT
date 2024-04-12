import numpy as np
import pandas as pd

import statsmodels.api as sm
from cliffs_delta import cliffs_delta
from scipy.stats import pointbiserialr, ranksums
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier


SEED = 42
np.random.seed(SEED)


def correlation(X, y, metrics, method):
    results = {}
    try:
        match method:
            case "logistic_regression":
                X_selected = X[metrics]
                scaler = StandardScaler()
                scaled_X = scaler.fit_transform(X_selected)
                scaled_X_df = pd.DataFrame(
                    scaled_X, columns=X_selected.columns, index=X_selected.index
                )

                X_const = sm.add_constant(scaled_X_df)

                model = sm.Logit(y, X_const)
                result = model.fit(disp=False, maxiter=1000)

                for metric in scaled_X_df.columns:
                    odds_ratio = np.exp(result.params[metric])

                    conf = result.conf_int().loc[metric]
                    conf_lower = np.exp(conf[0])
                    conf_upper = np.exp(conf[1])

                    error_lower = odds_ratio - conf_lower
                    error_upper = conf_upper - odds_ratio
                    error = max(error_lower, error_upper)

                    results[metric] = {
                        "p_value": result.pvalues[metric],
                        "odds_ratio": odds_ratio,
                        "error": error,
                        "conf_lower": conf_lower,
                        "conf_upper": conf_upper,
                    }

            case "point_biserial":
                for metric in metrics:
                    p_value = pointbiserialr(X[metric], y).pvalue
                    correlation = pointbiserialr(X[metric], y).correlation
                    # Storing p-value and correlation coefficient
                    results[metric] = {"p_value": p_value, "correlation": correlation}

            case "random_forest":
                X_selected = X[metrics]
                scaler = StandardScaler()
                scaled_X = scaler.fit_transform(X_selected)
                scaled_X_df = pd.DataFrame(
                    scaled_X, columns=X_selected.columns, index=X_selected.index
                )

                rf = RandomForestClassifier(n_estimators=100, random_state=SEED)
                rf.fit(scaled_X_df, y)

                importances = rf.feature_importances_
                for idx, metric in enumerate(scaled_X_df.columns):
                    results[metric] = {"feature_importance": importances[idx]}
            case _:
                raise NotImplementedError(
                    "Method not implemented. Choose 'logistic_regression', 'point_biserial', or 'random_forest'."
                )
        return results
    except Exception as e:
        print(type(e))
        print(metrics)


def group_difference(x1, x2, fmt="str"):
    p = ranksums(x1, x2).pvalue
    d, size = cliffs_delta(x1, x2)
    if fmt == "pair":
        p_str = "<" if p < 0.05 else ">"
        d_str = (
            "*"
            if size == "negligible"
            else "S"
            if size == "small"
            else "M"
            if size == "medium"
            else "L"
        )
        return f"({p_str}, {d_str})"

    if fmt == "one":
        p_str = (
            ""
            if p > 0.05
            else "(*)"
            if size == "negligible"
            else "(S)"
            if size == "small"
            else "(M)"
            if size == "medium"
            else "(L)"
        )
        return p_str

    if fmt == "str":
        d_str = (
            "[*]"
            if size == "negligible"
            else "[s]"
            if size == "small"
            else "[m]"
            if size == "medium"
            else "[l]"
        )
        return f"{p:.3f} {d_str}"


def significances(X, y, metrics):
    lr_results = correlation(X, y, metrics=metrics, method="logistic_regression")
    rf_results = correlation(X, y, metrics=metrics, method="random_forest")

    lr_p_values = []
    lr_odds_ratios = []
    lr_errors = []
    lr_conf_lower = []
    lr_conf_upper = []
    rf_feature_importances = []

    for metric in metrics:
        if metric in lr_results:
            lr_p_values.append(lr_results[metric]["p_value"])
            lr_odds_ratios.append(lr_results[metric]["odds_ratio"])
            lr_errors.append(lr_results[metric]["error"])
            lr_conf_lower.append(lr_results[metric]["conf_lower"])
            lr_conf_upper.append(lr_results[metric]["conf_upper"])

        if metric in rf_results:
            rf_feature_importances.append(rf_results[metric]["feature_importance"])

    results = pd.DataFrame(
        {
            "metric": metrics,
            "lr_p_value": lr_p_values,
            "lr_odds_ratio": lr_odds_ratios,
            "lr_errors": lr_errors,
            "lr_conf_lower": lr_conf_lower,
            "lr_conf_upper": lr_conf_upper,
            "rf_feature_importance": rf_feature_importances,
        }
    )

    return results
