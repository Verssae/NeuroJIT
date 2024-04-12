import pandas as pd
from pathlib import Path
from environment import *

for project in PROJECTS:
    hcc_csv = Path(f"data/dataset/baseline/{project}.csv")
    df = pd.read_csv(hcc_csv, index_col="commit_id")
    df = df.drop(columns=["ENT/NF","NS/NF","ND/NF","LA/LT","LD/LT","NUC/NF","NDEV/NF","FIX"])
    df.to_csv(hcc_csv, index=True)