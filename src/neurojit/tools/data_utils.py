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



class EarlySplit:
    def __init__(self, data: pd.DataFrame, k: int = 10) -> None:
        self.data = data.sort_index()
        self.k = k
        self.train_data = self.get_initial_samples()
        self.test_data = self.data.loc[self.train_data.index.max():]
    
    # def get_initial_samples(self) -> pd.DataFrame:
    #     # Get the first 50 buggy samples
    #     total_bugs = len(self.data[self.data['buggy'] == 1])
    #     print(f"Total bugs: {total_bugs}")
    #     ratio = 0.03
    #     buggy_samples = self.data[self.data['buggy'] == 1].head( int(total_bugs * ratio) )
    #     non_buggy_samples = self.data[self.data['buggy'] == 0].head(int(total_bugs * ratio) )

    #     if buggy_samples.index.max() < non_buggy_samples.index.max():
    #         last_date = non_buggy_samples.index.max()
    #     else:
    #         last_date = buggy_samples.index.max()

    #     few_month = (last_date - self.data.index.min()) / pd.Timedelta(days=30)
    #     date_ratio = (last_date - self.data.index.min()) / (self.data.index.max() - self.data.index.min())
    #     print(f"First {few_month:.2f} month ({date_ratio*100:.2f})%")
        
    #     return self.data[self.data.index <= last_date]
           
    # def get_initial_samples(self) -> pd.DataFrame:
    #     # Get the first 50 buggy samples
    #     total_bugs = len(self.data[self.data['buggy'] == 1])

    #     few_month = 30
    #     last_date = self.data.index.min() + pd.Timedelta(days=30 * few_month)

    #     train = self.data[self.data.index <= last_date]

    #     while train['buggy'].sum() < 50:
    #         few_month += 1
    #         last_date = self.data.index.min() + pd.Timedelta(days=30 * few_month)
    #         train = self.data[self.data.index <= last_date]

    #     print(f"First {few_month:.2f} month")

    #     return train
    
    # def get_initial_samples(self) -> pd.DataFrame:
    #     first_bug_date = self.data.index.min()
    #     few_month = 4
    #     last_date = first_bug_date + pd.Timedelta(days=30 * few_month)
    #     train = self.data[self.data.index >= first_bug_date]
    #     train = train[train.index <= last_date]

    #     return train
    
    def get_initial_samples(self) -> pd.DataFrame:
        num_samples = 25
        buggy = self.data[self.data['buggy'] == 1].head(num_samples)
        non_buggy = self.data[self.data['buggy'] == 0].head(num_samples)

        last_date = buggy.index.max() if buggy.index.max() > non_buggy.index.max() else non_buggy.index.max()

        print((last_date - self.data.index.min()))

        train = self.data[self.data.index <= last_date]

        # print(len(train) / len(self.data) * 100, len(train), len(self.data))
        # print(25 / len(self.data[self.data['buggy'] == 1]) * 100)

        buggy = train[train['buggy'] == 1].sample(num_samples)
        non_buggy = train[train['buggy'] == 0].sample(num_samples)

        train = pd.concat([buggy, non_buggy]).sort_index()

        return train

        
    # def split(self):
    #     fold_size = len(self.test_data) // self.k

    #     start = 0
    #     for i in range(self.k):
            
    #         end = (i + 1) * fold_size
    #         test = self.test_data.iloc[start:end]

    #         if test["buggy"].sum() < 1:
    #             continue

    #         yield self.train_data, test

    #         start = end
        

    def split(self):
        test_duration = pd.Timedelta(days=30 * 3)

        start = self.train_data.index.max() + pd.Timedelta(days=1)
        end = start + test_duration
        
        while end + test_duration < self.data.index.max():
            end = end + test_duration
            test = self.data.loc[start:end]

            if test["buggy"].sum() < 5:
                continue

            yield self.train_data, test

            start += pd.Timedelta(days=1) + test_duration
            



        




