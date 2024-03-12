from datetime import datetime
from collections import defaultdict
import plotly.graph_objs as go
import streamlit as st


class AnalysisManager:
    def __init__(self):
        self.visitor_counts = []
        self.time_series = None
        self.shape_manager = ShapeManager()

    def count_visitors(self, data, shape_manager):
        self.visitor_counts = []
        for gate_data in shape_manager.get_gate_data():
            counts = shape_manager.check_intersection(data, shape_manager.get_gate_data().index(gate_data))
            self.visitor_counts.append(counts)

    def generate_time_series(self, data, gate_index):
        gate_data = self.visitor_counts[gate_index]
        dates = gate_data.values()
        first_date_str = next(iter(dates))
        start_date = datetime.strptime(first_date_str, '%Y/%m/%d %H:%M').date()
        hourly_counts = defaultdict(lambda: defaultdict(int))
        for date_str in dates:
            dt = datetime.strptime(date_str, '%Y/%m/%d %H:%M')
            date = dt.date()
            hour = dt.hour
            hourly_counts[date][hour] += 1
        counts_dict = dict()
        for date, counts in hourly_counts.items():
            for hour in range(24):
                counts_dict[f"{date.strftime('%m/%d')} {hour:02d}時"] = counts[hour]
        sorted_data = sorted(counts_dict.items())
        self.time_series = sorted_data

    def plot_time_series(self):
        if self.time_series:
            trace = go.Scatter(x=[f"{start_date.strftime('%m/%d')} {hour:02d}:00" for hour in range(24)],
                               y=[counts for hour, counts in self.time_series],
                               mode='lines', name='通過人数[人]')
            layout = go.Layout(
                title='通過人数',
                xaxis=dict(title='日時'),
                yaxis=dict(
                    title='通過人数[人]',
                    tickvals=list(range(max([counts for hour, counts in self.time_series]) + 1)),
                    tickformat='d',
                )
            )
            fig = go.Figure(data=[trace], layout=layout)
            st.plotly_chart(fig)
