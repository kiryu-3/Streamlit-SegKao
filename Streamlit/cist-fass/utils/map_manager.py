import folium
from folium.plugins import Draw, TimestampedGeoJson

class MapManager:
    def __init__(self):
        self.map = folium.Map()
        self.center = {"lat": 42.79355312, "lng": 141.695872412}
        self.zoom_level = 16
        self.line_geojson = None

        # Leaflet.jsのDrawプラグインを追加
        draw_options = {'polyline': True, 'rectangle': True, 'circle': True, 'marker': False, 'circlemarker': False}
        self.draw = Draw(export=False, position='topleft', draw_options=draw_options)

    def initialize_map(self):
        self.map = folium.Map(location=[self.center["lat"], self.center["lng"]], zoom_start=self.zoom_level)
        self.draw.add_to(self.map)

    def draw_map(self, sorted_df):
        self.initialize_map()
        features = self.create_features(sorted_df)
        geojson = {"type": "FeatureCollection", "features": features}
        timestamped_geojson = TimestampedGeoJson(
            geojson,
            period="PT1M",
            duration='PT1M',
            auto_play=False,
            loop=False,
            transition_time=500
        )
        timestamped_geojson.add_to(self.map)

    def create_features(self, sorted_df):
        features = []
        max_id_length = max(len(str(user_id)) for user_id in sorted_df["userid"].unique())
        popup_width = max_id_length * 14
        for user_id, user_data in sorted_df.groupby("userid"):
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

    def draw_trajectories(self, sorted_df):
        self.line_geojson = self.create_line_geojson(sorted_df)
        folium.GeoJson(self.line_geojson, name='線の表示/非表示', style_function=lambda x: {"weight": 2, "opacity": 1}).add_to(self.map)

    def create_line_geojson(self, sorted_df):
        line_features = []
        for user_id, user_data in sorted_df.groupby("userid"):
            coords = user_data[['latitude', 'longitude']].values.tolist()
            for i in range(len(coords) - 1):
                line_feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [coords[i], coords[i + 1]]
                    },
                    'properties': {
                        'popup': f"{user_id}"
                    }
                }
                line_features.append(line_feature)
        return {'type': 'FeatureCollection', 'features': line_features}

    def remove_trajectories(self):
        line_layers_to_remove = []
        for key, value in self.map._children.items():
            if isinstance(value, folium.features.GeoJson):
                line_layers_to_remove.append(key)
        for key in line_layers_to_remove:
            del self.map._children[key]
        self.line_geojson = None

    def update_map_state(self, map_data):
        self.center = map_data["center"]
        self.zoom_level = map_data["zoom"]
