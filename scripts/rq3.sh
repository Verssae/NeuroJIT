#!/bin/sh

echo "Evaluating combined models for random forest and xgboost"
python scripts/jit_sdp.py train-test random_forest combined --load-model --display
python scripts/jit_sdp.py train-test xgboost combined --load-model --display

echo "[RQ3] Performance Comparison between Baseline Models and Baseline+Understandability Models"
python scripts/analysis.py table-performances data/output/random_forest_baseline.json data/output/random_forest_combined.json
python scripts/analysis.py table-performances data/output/xgboost_baseline.json data/output/xgboost_combined.json