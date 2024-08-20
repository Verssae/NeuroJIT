#!/bin/sh

echo "Evaluating baseline/cuf models for random forest and xgboost"
python scripts/jit_sdp.py train-test random_forest baseline --load-model --display
python scripts/jit_sdp.py train-test random_forest cuf --load-model --display
python scripts/jit_sdp.py train-test xgboost baseline --load-model --display
python scripts/jit_sdp.py train-test xgboost cuf --load-model --display

echo "[RQ2] Set Relationships between True Positives Predicted by Understandability Models and Baseline Models"
echo "(a) Random Forest"
python scripts/analysis.py table-set-relationships data/output/random_forest_cuf.json data/output/random_forest_baseline.json
echo "(b) XGBoost"
python scripts/analysis.py table-set-relationships data/output/xgboost_cuf.json data/output/xgboost_baseline.json