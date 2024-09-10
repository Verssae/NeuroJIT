# neurojit

`neurojit` is a Python package designed to enhance Just-In-Time (JIT) defect prediction by combining neurophysiological and empirical developer insights. The package provides tools for calculating commit understandability features (CUF), which are critical in modern software development and defect prediction. For more information, see our research paper *"NeuroJIT: Improving Just-In-Time Defect Prediction Using Neurophysiological and Empirical Perceptions of Modern Developers"*.

## Installation

You can install the NeuroJIT package from PyPI using pip:

```Shell
$ pip install neurojit
```
To install with additional dependencies for replicating the research results:

```Shell
$ pip install neurojit[replication]
```

For more information about the replication package, see our [replication package](https://github.com/Verssae/NeuroJIT)

### Example Usage
1. Filtering Commits and Saving Method Changes

    ```python
    from neurojit.commit import MethodChangesCommit, Mining, Method

    mining = Mining()
    target_commit = mining.only_method_changes(repo="activemq", commit_hash="8f40a7")
    if target_commit is not None:
        mining.save(target_commit)
    ```
2. Calculating Commit Understandability Features (CUF)

    Compute commit understandability features (CUF) from the saved MethodChangesCommit instances.

    ```python
    from neurojit.cuf.metrics import CommitUnderstandabilityFeatures

    cuf_calculator = CommitUnderstandabilityFeatures(target_commit)
    features = ["HV","DD", "MDNL", "NB", "EC", "NOP", "NOGV", "NOMT", "II", "TE", "DD_HV"]
    for feature in features:
        value = getattr(cuf_calculator, feature)
        print(f"{feature}: {value}")
    ```

3. Splitting the Dataset Chronologically with KFoldDateSplit

    Use `KFoldDateSplit` to split the dataset into training and testing sets, considering chronological order, verification latency, and concept drifts.

    ```python
    from neurojit.tools.data_utils import KFoldDateSplit

    data = pd.read_csv("...your jit-sdp dataset...")
    data["date"] = pd.to_datetime(data["date"])
    data = data.set_index(["date"])

    splitter = KFoldDateSplit(
        data, k=20, start_gap=3, end_gap=3, is_mid_gap=True, sliding_months=1
    )

    for i, (train, test) in enumerate(splitter.split()):
        X_train, y_train = train[features], train["buggy"]
        X_test, y_test = test[features], test["buggy"]
    ```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](https://github.com/Verssae/NeuroJIT/blob/main/LICENSE) file for details.

