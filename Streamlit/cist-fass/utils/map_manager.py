import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import TimestampedGeoJson
import json

class MapManager:
    def __init__(self):
        self.map = folium.Map()
        self.draw_options = {'polyline': True, 'rectangle': True, 'circle': True, 'marker': False, 'circlemarker': False}
        self.draw = folium.plugins.Draw(export=False, position='topleft', draw_options=self.draw_options)
        self.draw.add_to(self.map)
        self.center = {"lat": 42.79355312, "lng": 141.695872412}
        self.zoom_level = 16
        self.draw_data = []
        self.gate_data = []
        self.tuuka_list = []
        self.selected_shape = []
        self.selected_shape_type = "ゲート情報"
        self.kiseki_flag = False
        self.line_geojson = None

    def display_map(self, width=800, height=800):
        st_data = st_folium(self.map, width=width, height=height, zoom=self.zoom_level, center=self.center)
        return dict(st_data)

    def features_maker(self, data_manager):
        features = []
        max_id_length = max(len(str(user_id)) for user_id in data_manager.sorted_df["userid"].unique())
        popup_width = max_id_length * 14

        for user_id, user_data in data_manager.sorted_df.groupby("userid"):
            popup_html = f'<div style="font-size: 14px; font-weight: bold; width: {int(popup_width)}px; height: 15px; color: black;">UserID：{user_id}</div>'
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "MultiPoint",
                    "coordinates": user_data[['longitude', 'latitude']].values.tolist()
                },
                "properties": {
                    "times": user_data["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
                    "icon": "circle",
                    "iconstyle": {
                        "color": "#4169e1",
                        "fillColor": "#01bfff",
                        "weight": 10,
                        "radius": 3
                    },
                    "popup": popup_html
                }
            }
            features.append(feature)
        return features

    def add_timestamped_geojson(self, data_manager):
        features = self.features_maker(data_manager)
        geojson = {"type": "FeatureCollection", "features": features}
        timestamped_geojson = TimestampedGeoJson(
            geojson,
            period="PT1M",
            duration='PT1M',
            auto_play=False,
            loop=False,
            transition_time=500
        )

        layers_to_remove = []
        for key, value in self.map._children.items():
            if isinstance(value, TimestampedGeoJson):
                layers_to_remove.append(key)
        for key in layers_to_remove:
            del self.map._children[key]

        timestamped_geojson.add_to(self.map)

    def polylines_maker(self, data_manager):
        max_id_length = max(len(str(user_id)) for user_id in data_manager.sorted_df["userid"].unique())
        popup_width = max_id_length * 14

        for user_id, user_data in data_manager.sorted_df.groupby("userid"):
            popup_html = f'<div style="font-size: 14px; font-weight: bold; width: {int(popup_width)}px; height: 15px; color: black;">UserID：{user_id}</div>'
            folium.PolyLine(locations=user_data[['latitude', 'longitude']].values.tolist(), color='#01bfff', weight=3, opacity=0.9,
                            popup=folium.Popup(popup_html)).add_to(self.map)

    def add_shape_data(self, data_manager):
        line_layers_to_remove = []
        for key, value in self.map._children.items():
            if isinstance(value, folium.features.GeoJson):
                line_layers_to_remove.append(key)
        for key in line_layers_to_remove:
            del self.map._children[key]

        gate_append_list = []
        for idx, sdata in enumerate(self.draw_data):
            if sdata["geometry"]["coordinates"][0][0] == sdata["geometry"]["coordinates"][0][-1]:
                gate_append_list.append(sdata["geometry"]["coordinates"][0])
            else:
                gate_append_list.append(sdata["geometry"]["coordinates"])

        self.gate_data = gate_append_list

        self.tuuka_list = [dict() for _ in range(len(self.draw_data))]

        for idx, sdata in enumerate(self.draw_data):
            if len(data_manager.df_new) != 0:
                for idx1, gates in enumerate(self.gate_data):
                    for key, values in data_manager.kiseki_data.items():
                        if gates[0] == gates[-1]:
                            if self.ingate(values[0]["座標"][0], gates):
                                self.tuuka_list[idx1][key] = values[0]["日時"]
                                continue
                        kekka = self.cross_judge(gates, values)
                        if kekka[0]:
                            self.tuuka_list[idx1][key] = values[kekka[1]]["日時"]
                            continue

                tooltip_html = f'<div style="font-size: 16px;">gateid：{idx + 1}</div>'
                popup_html = f'<div style="font-size: 16px; font-weight: bold; width: 110px; height: 20px;  color: #27b9cc;">通過人数：{len(self.tuuka_list[idx])}人</div>'
                folium.GeoJson(sdata, tooltip=tooltip_html, popup=folium.Popup(popup_html)).add_to(self.map)

            else:
                tooltip_html = f'<div style="font-size: 16px;">gateid：{idx + 1}</div>'
                folium.GeoJson(sdata, tooltip=tooltip_html).add_to(self.map)

    def max_min_cross(self, p1, p2, p3, p4):
        min_ab, max_ab = min(p1, p2), max(p1, p2)
        min_cd, max_cd = min(p3, p4), max(p3, p4)

        if min_ab > max_cd or max_ab < min_cd:
            return False

        return True

    def cross_judge(self, gates, values):
        flag = False
        idx = -1
        for idx1 in range(len(gates) - 1):
            line1 = [(gates[idx1][0], gates[idx1][1]), (gates[idx1 + 1][0], gates[idx1 + 1][1])]
            for idx2 in range(len(values)):
                line2 = [(values[idx2]["座標"][0][0], values[idx2]["座標"][0][1]), (values[idx2]["座標"][1][0], values[idx2]["座標"][1][1])]
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
        return (flag, idx)

    def ingate(self, plot_point, gate_polygon):
        point = Feature(geometry=Point(plot_point))
        polygon = Polygon([gate_polygon])
        return boolean_point_in_polygon(point, polygon)

    def select_shape(self, shape_id):
        if shape_id != "":
            select_shape_id = int(shape_id)
            selected_shape = self.gate_data[select_shape_id - 1]

            if selected_shape[0] != selected_shape[-1]:
                self.selected_shape_type = f"ゲート{select_shape_id}(ライン)"
                self.selected_shape = [{"経度": row[0], "緯度": row[1]} for row in selected_shape]
            else:
                self.selected_shape_type = f"ゲート{select_shape_id}(ポリゴン)"
                self.selected_shape = [{"経度": row[0], "緯度": row[1]} for row in selected_shape]
        else:
            self.selected_shape_type = "ゲート情報"
            self.selected_shape = []

    def delete_shape(self, shape_id):
        if shape_id != "":
            delete_shape_id = int(shape_id)
            delete_shape = self.draw_data[delete_shape_id - 1]

            keys_to_remove = []
            for key, value in self.map._children.items():
                if isinstance(value, folium.features.GeoJson) and value.data == delete_shape:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.map._children[key]

            self.draw_data.remove(delete_shape)
            self.gate_data.pop(delete_shape_id - 1)
            if len(self.tuuka_list) != 0:
                self.tuuka_list.pop(delete_shape_id - 1)
            if len(self.selected_shape) != 0:
                self.selected_shape.pop(delete_shape_id - 1)

            self.add_shape_data(data_manager)

    def add_draw_data(self, data_manager):
        if self.draw_data is not None and isinstance(self.draw_data, list) and len(self.draw_data) > 0:
            if "last_circle_polygon" in st.session_state["data"] and st.session_state["data"]["last_circle_polygon"] is not None:
                self.draw_data[0]["geometry"]["type"] = "Polygon"
                self.draw_data[0]["geometry"]["coordinates"] = st.session_state["data"]["last_circle_polygon"]["coordinates"]
                center_list = st.session_state["data"]["last_active_drawing"]["geometry"]["coordinates"]
                center_dict = {"lat": center_list[0], "lng": center_list[1]}
                self.draw_data[0]["properties"]["center"] = center_dict

            if self.draw_data[0] not in self.draw_data or len(self.draw_data) == 0:
                self.draw_data.append(self.draw_data[0])
                self.add_shape_data(data_manager)

    def toggle_kiseki(self):
        if self.kiseki_flag:
            self.polylines_maker(data_manager)
        else:
            line_layers_to_remove = []
            for key, value in self.map._children.items():
                if isinstance(value, folium.vector_layers.PolyLine):
                    line_layers_to_remove.append(key)
            for key in line_layers_to_remove:
                del self.map._children[key]
