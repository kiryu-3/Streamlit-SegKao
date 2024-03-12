import folium
from turfpy.measurement import boolean_point_in_polygon
from geojson import Point, Polygon, Feature

class ShapeManager:
    def __init__(self):
        self.draw_data = []
        self.gate_data = []
        self.tuuka_list = []
        self.selected_shape = []
        self.selected_shape_type = "ゲート情報"

    def handle_new_shape(self, map_data, sorted_df):
        if map_data["all_drawings"] is not None and isinstance(map_data["all_drawings"], list) and len(map_data["all_drawings"]) > 0:
            new_shape = self.process_new_shape(map_data)
            if new_shape not in self.draw_data:
                self.draw_data.append(new_shape)
                self.gate_data.append(self.convert_to_gate_data(new_shape))
                self.update_tuuka_list(sorted_df)
                self.draw_shapes(sorted_df)

    def process_new_shape(self, map_data):
        if map_data["last_circle_polygon"] is not None:
            new_shape = map_data["all_drawings"][0]
            new_shape["geometry"]["type"] = "Polygon"
            new_shape["geometry"]["coordinates"] = map_data["last_circle_polygon"]["coordinates"]
            center_list = map_data["last_active_drawing"]["geometry"]["coordinates"]
            center_dict = {"lat": center_list[0], "lng": center_list[1]}
            new_shape["properties"]["center"] = center_dict
            return new_shape
        return map_data["all_drawings"][0]

    def convert_to_gate_data(self, shape_data):
        if shape_data["geometry"]["coordinates"][0][0] == shape_data["geometry"]["coordinates"][0][-1]:
            return shape_data["geometry"]["coordinates"][0]
        else:
            return shape_data["geometry"]["coordinates"]

    def update_tuuka_list(self, sorted_df):
        self.tuuka_list = [dict() for _ in range(len(self.draw_data))]
        for idx, gates in enumerate(self.gate_data):
            for user_id, values in sorted_df.groupby("userid"):
                if gates[0] == gates[-1]:
                    if self.ingate(values.iloc[0][['longitude', 'latitude']].tolist(), gates):
                        self.tuuka_list[idx][user_id] = values.iloc[0]['datetime'].strftime('%Y/%m/%d %H:%M')
                        continue
                kekka = self.cross_judge(gates, values)
                if kekka[0]:
                    self.tuuka_list[idx][user_id] = kekka[1]
                    continue

    def draw_shapes(self, sorted_df):
        for idx, shape_data in enumerate(self.draw_data):
            tooltip_html = f'<div style="font-size: 16px;">gateid：{idx + 1}</div>'
            if sorted_df is not None:
                popup_html = f'<div style="font-size: 16px; font-weight: bold; width: 110px; height: 20px;  color: #27b9cc;">通過人数：{len(self.tuuka_list[idx])}人</div>'
                folium.GeoJson(shape_data, tooltip=tooltip_html, popup=folium.Popup(popup_html)).add_to(st.session_state['map'])
            else:
                folium.GeoJson(shape_data, tooltip=tooltip_html).add_to(st.session_state['map'])

    def select_shape(self, shape_id):
        selected_shape = self.gate_data[shape_id - 1]
        if selected_shape[0] != selected_shape[-1]:
            self.selected_shape_type = f"ゲート{shape_id}(ライン)"
            self.selected_shape = [{"経度": row[0], "緯度": row[1]} for row in selected_shape]
        else:
            self.selected_shape_type = f"ゲート{shape_id}(ポリゴン)"
            self.selected_shape = [{"経度": row[0], "緯度": row[1]} for row in selected_shape]

    def delete_shape(self, shape_id):
        delete_shape = self.draw_data[shape_id - 1]
        keys_to_remove = []
        for key, value in st.session_state['map']._children.items():
            if isinstance(value, folium.features.GeoJson) and value.data == delete_shape:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del st.session_state['map']._children[key]
        self.draw_data.remove(delete_shape)
        self.gate_data.pop(shape_id - 1)
        if len(self.tuuka_list) != 0:
            self.tuuka_list.pop(shape_id - 1)
        if len(self.selected_shape) != 0:
            self.selected_shape.pop(shape_id - 1)

    def ingate(self, plot_point, gate_polygon):
        point = Feature(geometry=Point(plot_point))
        polygon = Polygon(gate_polygon)
        return boolean_point_in_polygon(point, polygon)

    def cross_judge(self, gates, values):
        flag = False
        idx = -1
        for idx1 in range(len(gates) - 1):
            line1 = [(gates[idx1][0], gates[idx1][1]), (gates[idx1 + 1][0], gates[idx1 + 1][1])]
            for idx2 in range(len(values)):
                line2 = [(values.iloc[idx2]['longitude'], values.iloc[idx2]['latitude']),
                         (values.iloc[idx2 + 1]['longitude'], values.iloc[idx2 + 1]['latitude'])]
                (a, b, c, d) = (line1[0], line1[1], line2[0], line2[1])

                if not self.max_min_cross(a[0], b[0], c[0], d[0]):
                    continue
                if not self.max_min_cross(a[1], b[1], c[1], d[1]):
                    continue

                tc1 = (a[0] - b[0]) * (c[1] - a[1]) + (a[1] - b[1]) * (a[0] - c[0])
                tc2 = (a[0] - b[0]) * (d[1] - a[1]) + (a[1] - b[1]) * (a[0] - d[0])
                td1 = (c[0] - d[0]) * (a[1] - c[1]) + (c[1] - d[1]) * (c[0] - a[0])
                td2 = (c[0] - d[0]) * (b[1] - c[1]) + (c[1] - d[1]) * (c[0] - b[0])
                if tc1 * tc2 <= 0 and td1 * td2 <= 0:
                    flag = True
                    idx = idx2
                    break
            if flag:
                break
        return (flag, values.iloc[idx]['datetime'].strftime('%Y/%m/%d %H:%M'))

    def max_min_cross(self, p1, p2, p3, p4):
        min_ab, max_ab = min(p1, p2), max(p1, p2)
        min_cd, max_cd = min(p3, p4), max(p3, p4)

        if min_ab > max_cd or max_ab < min_cd:
            return False

        return True
