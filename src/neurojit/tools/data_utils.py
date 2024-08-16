import pandas as pd


def commits_per_day(data: pd.DataFrame) -> float:
    assert isinstance(data.index, pd.DatetimeIndex)
    return len(data) / (data.index.max() - data.index.min()).days


def commits_per_month(data: pd.DataFrame) -> float:
    return commits_per_day(data) * 30


class KFoldDateSplit:
    def __init__(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.8,
        by: str = "median",
        k: int = 10,
        sliding_months: int = 3,
        start_gap: int = 3,
        end_gap: int = 3,
        is_mid_gap: bool = True,
    ) -> None:
        self.data = data.sort_index()
        self.by = by
        self.k = k
        self.train_ratio = train_ratio

        self.gap_size = self.gap() if is_mid_gap else 0
        self.commits_day = commits_per_day(self.data)
        self.commits_gap = round(self.commits_day * self.gap_size)
        self.sliding_months = sliding_months
        self.start_gap = start_gap
        self.end_gap = end_gap
        self.is_mid_gap = is_mid_gap

    def gap(self) -> float:
        gaps = self.data.loc[self.data["buggy"] == 1, "gap"]
        gaps = gaps.dropna()
        gaps = gaps.sort_values()
        # remove outliers
        q1 = gaps.quantile(0.2)
        q3 = gaps.quantile(0.8)
        gaps = gaps.loc[(gaps > q1) & (gaps < q3)]

        return gaps.agg("mean")

    def truncate(self):
        # drop the first and last 3 months
        start_date = self.data.index.min()
        end_date = self.data.index.max()

        start_gap = pd.Timedelta(days=30 * self.start_gap)
        end_gap = pd.Timedelta(days=30 * self.end_gap)

        return self.data.loc[start_date + start_gap : end_date - end_gap]

    def split(self):
        data = self.truncate()
        window_start = data.index.min()
        end_date = data.index.max()
        window_end = end_date - pd.Timedelta(days=30 * self.sliding_months * self.k)
        for i in range(self.k):
            if i == self.k - 1:
                window_end = end_date
            window = data.loc[window_start:window_end]
            commits_window = len(window)

            train_samples = round(
                (commits_window - self.commits_gap) * self.train_ratio
            )
            test_samples = commits_window - train_samples - self.commits_gap

            train = window.iloc[:train_samples]
            test = window.iloc[-test_samples:]

            yield train, test

            window_start += pd.Timedelta(days=30 * self.sliding_months)
            window_end += pd.Timedelta(days=30 * self.sliding_months)


