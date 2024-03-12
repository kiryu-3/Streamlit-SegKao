import plotly.graph_objs as go
import json
from collections import defaultdict
from datetime import datetime

class AnalysisManager:
    def __init__(self):
        self.graph_data = dict()

    def select_graph(self, selected_ids, tuuka_list):
        self.graph_data = dict()
        if len(selected_ids) != 0:
            for idx in selected_ids:
                data = tuuka_list[int(idx) - 1]
                dates = data.values()
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

                trace = go.Scatter(x=[f"{start_date.strftime('%m/%d')} {hour:02d}:00" for hour in range(24)],
                                   y=[counts for hour, counts in sorted_data],
                                   mode='lines', name='通過人数[人]')

                layout = go.Layout(
                    title='通過人数',
                    xaxis=dict(title='日時'),
                    yaxis=dict(
                        title='通過人数[人]',
                        tickvals=list(range(max([counts for hour, counts in sorted_data]) + 1)),
                        tickformat='d',
                    )
                )

                fig = go.Figure(data=[trace], layout=layout)

                graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

                self.graph_data[idx] = graph_json

    def display_graph(self, selected_graph_ids):
        if len(selected_graph_ids) != 0:
            fig = go.Figure()
            diff = len(tuuka_list) - len(selected_graph_ids)
            y_values = []
            for idx in selected_graph_ids:
                graph_json = self.graph_data[idx]
                fig_dict = json.loads(graph_json)
                y_values.extend(trace['y'] for trace in fig_dict['data'])
                for trace in fig_dict['data']:
                    name = f"図形{idx}"
                    fig.add_trace(go.Scatter(x=trace['x'], y=trace['y'], mode=trace['mode'], name=name))

            max_y_value = max(max(y) for y in y_values)

            if max_y_value > 5:
                dtick_value = 5
            else:
                dtick_value = 1

            layout = go.Layout(
                title='通過人数',
                xaxis=dict(title='日時', dtick=6),
                yaxis=dict(
                    title='通過人数[人]',
                    tickvals=list(range(0, max_y_value + 1, dtick_value)) + [max_y_value],
                    tickformat='d',
                )
            )

            fig.update_layout(layout)

            st.plotly_chart(fig)
