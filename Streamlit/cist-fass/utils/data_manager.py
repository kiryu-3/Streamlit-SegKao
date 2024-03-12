import pandas as pd
import io

class DataManager:
    def __init__(self):
        self.df = None
        self.df_new = None
        self.sorted_df = None
        self.kiseki_data = {}

    def load_data(self, uploaded_file):
        file_data = uploaded_file.read()
        self.df = pd.read_csv(io.BytesIO(file_data))
        self.preprocess_data()
        self.initialize_kiseki_data()

    def preprocess_data(self):
        self.df.columns = ['userid', 'datetime', 'latitude', 'longitude']
        self.df['datetime'] = pd.to_datetime(self.df['datetime'])
        self.df.sort_values(by=[self.df.columns[1]], inplace=True)
        unique_values = self.df.iloc[:, 0].unique()
        self.df_new = pd.DataFrame(unique_values, columns=["newid"])
        self.df_new.index = range(1, len(self.df_new) + 1)
        self.sorted_df = self.df.copy()

    def initialize_kiseki_data(self):
        if self.df is not None:
            unique_values = self.df.iloc[:, 0].unique()
            self.kiseki_data = {str(itr): [] for itr in unique_values}

    def filter_data(self, selected_ids):
        self.sorted_df = self.df[self.df.iloc[:, 0].isin(selected_ids)]
        self.sorted_df = self.sorted_df.reset_index(drop=True)
        self.sorted_df.sort_values(by=[self.sorted_df.columns[1]], inplace=True)
