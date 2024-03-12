import pandas as pd
import io

class DataManager:
    def __init__(self):
        self.df = pd.DataFrame()
        self.df_new = pd.DataFrame()
        self.sorted_df = pd.DataFrame()
        self.kiseki_data = dict()

    def load_data(self, file_data):
        self.df = pd.read_csv(io.BytesIO(file_data))
        self.df.columns = ['userid', 'datetime', 'latitude', 'longitude']
        self.df['datetime'] = pd.to_datetime(self.df['datetime'])
        self.df.sort_values(by=[self.df.columns[1]], inplace=True)

        unique_values = self.df.iloc[:, 0].unique()
        self.df_new = pd.DataFrame(unique_values, columns=["newid"])
        self.df_new.index = range(1, len(self.df_new) + 1)

        self.sorted_df = self.df.copy()
        self.kiseki_data = {str(itr): [] for itr in unique_values}

    def select_data(self, selected_values):
        if len(selected_values) == 0:
            self.sorted_df = self.df
        else:
            self.sorted_df = self.df[self.df.iloc[:, 0].isin(selected_values)]
            self.sorted_df = self.sorted_df.reset_index(drop=True)
            self.sorted_df.sort_values(by=[self.sorted_df.columns[1]], inplace=True)

    def make_line_features(self, kiseki):
        for itr, group in self.sorted_df.groupby(self.sorted_df.columns[0]):
            rows = list(group.iterrows())
            for i, (index, zahyou) in enumerate(rows):
                if i < len(rows) - 1:
                    next_index, next_zahyou = rows[i + 1]
                    if kiseki:
                        self.kiseki_data[str(itr)].append(
                            {'座標': [[zahyou["longitude"], zahyou["latitude"]], [next_zahyou["longitude"], next_zahyou["latitude"]]], '日時': datetime.strptime(str(zahyou["datetime"]), '%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M')})
                    else:
                        pass
