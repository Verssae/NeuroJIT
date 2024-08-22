#!/bin/sh

echo "  _   _                          _ ___ _____ 
 | \ | | ___ _   _ _ __ ___     | |_ _|_   _|
 |  \| |/ _ \ | | | '__/ _ \ _  | || |  | |  
 | |\  |  __/ |_| | | | (_) | |_| || |  | |  
 |_| \_|\___|\__,_|_|  \___/ \___/|___| |_|  
                                             "
echo "[Figure 2] Correlations of Features in Each Group"
python scripts/pre_analysis.py plot-hmap

echo "=====================[RQ1]====================="
echo "[Figure 4] Predictive Power of Understandability Features"
echo "(a) understandability features' odds ratio & (b) combined features' odds ratio"
python scripts/pre_analysis.py plot-corr
echo "(c) group difference between defective and clean commits"
python scripts/pre_analysis.py table-group-diff

echo "=====================[RQ2]====================="
echo "** Evaluating baseline/cuf models for random forest and xgboost **"
python scripts/jit_sdp.py train-test random_forest baseline --load-model --display
python scripts/jit_sdp.py train-test random_forest cuf --load-model --display
python scripts/jit_sdp.py train-test xgboost baseline --load-model --display
python scripts/jit_sdp.py train-test xgboost cuf --load-model --display
echo "[Figure 5] Set Relationships between True Positives Predicted by Understandability Models and Baseline Models"
echo "(a) Random Forest"
python scripts/analysis.py table-set-relationships data/output/random_forest_cuf.json data/output/random_forest_baseline.json
echo "(b) XGBoost"
python scripts/analysis.py table-set-relationships data/output/xgboost_cuf.json data/output/xgboost_baseline.json
echo "** Generating Figure 5 **"
python scripts/analysis.py plot-set-relationships data/output/random_forest_cuf.json data/output/random_forest_baseline.json
python scripts/analysis.py plot-set-relationships data/output/xgboost_cuf.json data/output/xgboost_baseline.json

echo "=====================[RQ3]====================="
echo "** Evaluating combined models for random forest and xgboost **"
python scripts/jit_sdp.py train-test random_forest combined --load-model --display
python scripts/jit_sdp.py train-test xgboost combined --load-model --display

echo "[Figure 7] Performance Comparison between Baseline Models and Baseline+Understandability Models"
python scripts/analysis.py table-performances data/output/random_forest_baseline.json data/output/random_forest_combined.json
python scripts/analysis.py table-performances data/output/xgboost_baseline.json data/output/xgboost_combined.json
echo "** Generating Figure 7 components **"
python scripts/analysis.py plot-radars data/output/random_forest_baseline.json data/output/random_forest_combined.json
python scripts/analysis.py plot-radars data/output/xgboost_baseline.json data/output/xgboost_combined.json


echo "========[Toward More Actionable Guidance]======="
echo "[Table 3] Average Ratios of Actionable Features within Top 5 Contribution Rankings of LIME Explanations"
echo "** Generating LIME explanations for random forest and xgboost **"
python scripts/jit_sdp.py actionable random_forest --display
python scripts/jit_sdp.py actionable xgboost --display
echo "Random Forest"
python scripts/analysis.py table-actionable data/output/actionable_random_forest.csv
echo "XGBoost"
python scripts/analysis.py table-actionable data/output/actionable_xgboost.csv

echo "=====================[END]====================="