#!/bin/sh

echo "[Section 3.5] Toward More Actionable Guidance"
# python scripts/jit_sdp.py actionable random_forest --display
# python scripts/jit_sdp.py actionable xgboost --display
echo "Random Forest"
python scripts/analysis.py table-actionable data/output/actionable_random_forest.csv
echo "XGBoost"
python scripts/analysis.py table-actionable data/output/actionable_xgboost.csv
