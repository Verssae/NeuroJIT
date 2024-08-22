from typing import Optional
from typer import Typer, Argument, Option
from neurojit.commit import MethodChangesCommit, Mining, Method
from neurojit.cuf.metrics import CommitUnderstandabilityFeatures
from environment import CUF

app = Typer(add_completion=False, help="NeuroJIT CLI")

@app.command()
def fetch_commit(
    project: str = "activemq",
    commit_hash: str = "8f40a7",
    verbose: bool = True,
)-> Optional[MethodChangesCommit]:
    """
    Fetch the target commit if it is a method changes commit and save it to the cache
    """
    mining = Mining()
    target_commit = mining.only_method_changes(repo=project, commit_hash=commit_hash)
    if target_commit is not None:
        mining.save(target_commit)
        if verbose:

            print("Saved target commit")
    else:
        if verbose:
            print("Target commit is not a method changes commit")

    return target_commit

@app.command()
def calculate(
    project: str = "activemq",
    commit_hash: str = "8f40a7",
)-> Optional[dict]:
    """
    Calculate metrics if the target commit is a method changes commit
    """
    target_commit = fetch_commit(project, commit_hash, verbose=False)
    if target_commit is None:
        print("Target commit is not a method changes commit")
        return None
    cuf_calculator = CommitUnderstandabilityFeatures(target_commit)
    metrics = { metric: float(getattr(cuf_calculator, metric)) for metric in CUF }
    print(metrics)
    return metrics

if __name__ == "__main__":
    app()