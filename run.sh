#!/bin/bash

function run_model() {
    model=$1
    for feature in "baseline" "combined"; do
        echo "Running $model with $feature"
        rye run python scripts/jit_sdp.py early-train-test $model $feature --display
    done
}

function show_result() {
    model=$1
    echo "### $(echo $model | tr '[:lower:]' '[:upper:]')"
    # rye run python scripts/analysis.py table-performances "rebuttal/output/${model}_baseline.json" "rebuttal/output/${model}_cuf.json"
    rye run python scripts/analysis.py table-performances "rebuttal/output/${model}_baseline.json" "rebuttal/output/${model}_combined.json"
    # rye run python scripts/analysis.py table-performances "rebuttal/output/${model}_cuf.json" "rebuttal/output/${model}_combined.json"
}

function run_models() {
    for model in "random_forest xgboost" "naive_bayes" "logistic_regression" "svm" "knn" "decision_tree"; do
        run_model $model
    done
}

function show_results() {
    for model in "random_forest xgboost" "naive_bayes" "logistic_regression" "svm" "knn" "decision_tree"; do
        show_result $model
    done
}

# Get command line arguments and run the corresponding function
if [ "$1" == "run" ]; then
    run_models
elif [ "$1" == "run_model" ]; then
    run_model $2
elif [ "$1" == "show" ]; then
    show_result $2
elif [ "$1" == "show_results" ]; then
    show_results
else
    echo "Usage: $0 run|show <model>"
fi
