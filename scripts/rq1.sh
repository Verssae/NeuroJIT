#!/bin/sh

echo "[RQ1] Predictive Power of Understandability Features"
echo "(a) understandability features' odds ratio & (b) combined features' odds ratio"
python scripts/pre_analysis.py plot-corr

echo "(c) group difference between defective and clean commits"
python scripts/pre_analysis.py table-group-diff

