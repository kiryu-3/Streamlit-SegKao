import streamlit as st
from streamlit_folium import st_folium
import os
from PIL import Image
from utils.data_manager import DataManager
from utils.map_manager import MapManager
from utils.shape_manager import ShapeManager
from utils.analysis_manager import AnalysisManager

# 画像ファイルのパス
image_path = os.path.join(os.path.dirname(__file__), 'icon_image.png')

# 画像をPILのImageオブジェクトとして読み込む
image = Image.open(image_path)

# Streamlit ページの設定
st.set_page_config(
    page_title="CIST-FASS",
    page_icon=image,
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

data_manager = DataManager()
map_manager = MapManager()
shape_manager = ShapeManager(map_manager)
analysis_manager = AnalysisManager()

# csvのuploaderの状態が変化したときに呼ばれるcallback関数
def upload_csv():
    if st.session_state["upload_csvfile"] is not None:
        file_data = st.session_state["upload_csvfile"].read()
        data_manager.load_data(file_data)
        map_manager.add_timestamped_geojson(data_manager)
        data_manager.make_line_features(True)
    else:
        data_manager.df = pd.DataFrame()
        data_manager.df_new = pd.DataFrame()
        data_manager.sorted_df = pd.DataFrame()
        data_manager.kiseki_data = dict()
        analysis_manager.graph_data = dict()

        layers_to_remove = []
        for key, value in map_manager.map._children.items():
            if isinstance(value, TimestampedGeoJson):
                layers_to_remove.append(key)
        for key in layers_to_remove:
            del map_manager.map._children[key]

        line_layers_to_remove = []
        for key, value in map_manager.map._children.items():
            if isinstance(value, folium.features.GeoJson):
                line_layers_to_remove.append(key)
        for key in line_layers_to_remove:
            del map_manager.map._children[key]

        if len(map_manager.draw_data) != 0:
            for idx, sdata in enumerate(map_manager.draw_data):
                if len(data_manager.df_new) != 0:
                    append_list = [dict() for _ in range(len(map_manager.draw_data))]
                    map_manager.tuuka_list = append_list

                    for idx1, gates in enumerate(map_manager.gate_data):
                        for key, values in data_manager.kiseki_data.items():
                            if gates[0] == gates[-1]:
                                if map_manager.ingate(values[0]["座標"][0], gates):
                                    map_manager.tuuka_list[idx1][key] = values[0]["日時"]
                                    continue
                            kekka = map_manager.cross_judge(gates, values)
                            if kekka[0]:
                                map_manager.tuuka_list[idx1][key] = values[kekka[1]]["日時"]
                                continue

                    tooltip_html = f'<div style="font-size: 16px;">gateid：{idx + 1}</div>'
                    popup_html = f'<div style="font-size: 16px; font-weight: bold; width: 110px; height: 20px;  color: #27b9cc;">通過人数：{len(map_manager.tuuka_list[idx])}人</div>'
                    folium.GeoJson(sdata, tooltip=tooltip_html, popup=folium.Popup(popup_html)).add_to(map_manager.map)

                else:
                    tooltip_html = f'<div style="font-size: 16px;">gateid：{idx + 1}</div>'
                    folium.GeoJson(sdata, tooltip=tooltip_html).add_to(map_manager.map)

        line_layers_to_remove = []
        for key, value in map_manager.map._children.items():
            if isinstance(value, folium.vector_layers.PolyLine):
                line_layers_to_remove.append(key)
        for key in line_layers_to_remove:
            del map_manager.map._children[key]

def select_data():
    selected_values = st.session_state["select_data_id"]
    data_manager.select_data(selected_values)
    map_manager.add_timestamped_geojson(data_manager)
    map_manager.polylines_maker(data_manager)
    data_manager.make_line_features(False)

    if map_manager.kiseki_flag:
        map_manager.polylines_maker(data_manager)

    for idx, sdata in enumerate(map_manager.draw_data):
        if len(data_manager.df_new) != 0:
            append_list = [dict() for _ in range(len(map_manager.draw_data))]
            map_manager.tuuka_list = append_list

            for idx1, gates in enumerate(map_manager.gate_data):
                for key, values in data_manager.kiseki_data.items():
                    if gates[0] == gates[-1]:
                        if map_manager.ingate(values[0]["座標"][0], gates):
                            map_manager.tuuka_list[idx1][key] = values[0]["日時"]
                            continue
                    kekka = map_manager.cross_judge(gates, values)
                    if kekka[0]:
                        map_manager.tuuka_list[idx1][key] = values[kekka[1]]["日時"]
                        continue

            tooltip_html = f'<div style="font-size: 16px;">gateid：{idx + 1}</div>'
            popup_html = f'<div style="font-size: 16px; font-weight: bold; width: 110px; height: 20px;  color: #27b9cc;">通過人数：{len(map_manager.tuuka_list[idx])}人</div>'
            folium.GeoJson(sdata, tooltip=tooltip_html, popup=folium.Popup(popup_html)).add_to(map_manager.map)

        else:
            tooltip_html = f'<div style="font-size: 16px;">gateid：{idx + 1}</div>'
            folium.GeoJson(sdata, tooltip=tooltip_html).add_to(map_manager.map)

def select_graph():
    analysis_manager.select_graph(st.session_state["select_graph_ids"], map_manager.tuuka_list)

def kiseki_draw():
    map_manager.toggle_kiseki()

def select_shape():
    shape_manager.select_shape(st.session_state["select_shape_id"])

def delete_shape():
    shape_manager.delete_shape(st.session_state["delete_shape_id"])

# 表示する地図
st_data = st_folium(map_manager.map, width=800, height=800, zoom=map_manager.zoom_level, center=map_manager.center)

# 地図のデータをコピー
st.session_state["data"] = st_data

shape_manager.handle_draw_data(data_manager, st.session_state["data"]["all_drawings"])
st.write(map_manager.gate_append_list)

# try:
#     shape_manager.handle_draw_data(st.session_state["data"]["all_drawings"])
# except Exception as e:
#     st.write(st.session_state["data"]["all_drawings"])
#     st.error(e)

try:
    if len(data_manager.df) != 0 and len(map_manager.gate_data):
        available_ids = [str(value) for value in range(1, len(map_manager.gate_data) + 1) if
                         len(map_manager.tuuka_list[value - 1]) > 0]

        st.multiselect(
            "グラフを表示したい図形のIDを選択してください",
            available_ids,
            key="select_graph_ids",
            on_change=select_graph
        )

        analysis_manager.display_graph(st.session_state["select_graph_ids"])
except:
    pass

with st.sidebar:
    tab1, tab2, tab3, tab4 = st.tabs(["Uploader", "Data_info", "Gate_info", "Kiseki_info"])

    with tab1:
        st.file_uploader("CSVファイルをアップロード", type=["csv"], key="upload_csvfile", on_change=upload_csv)
        st.write(st.session_state["upload_csvfile"])

    with tab2:
        if len(data_manager.df) != 0:
            st.write(data_manager.df_new)

            if len(data_manager.df) != 0:
                st.multiselect("選択してください", data_manager.df.iloc[:, 0].unique(), key="select_data_id",
                               on_change=select_data)
                data_manager.sorted_df = data_manager.sorted_df.sort_values(by=data_manager.sorted_df.columns[1])
                csv_file = data_manager.sorted_df.to_csv(index=False)

                if len(st.session_state["select_data_id"]) != 0:
                    st.download_button(label="Download CSV", data=csv_file, file_name='sorted.csv')

    with tab3:
        if len(map_manager.draw_data) != 0:
            st.selectbox("表示したい図形のIDを選択してください",
                         [""] + [str(value) for value in range(1, len(map_manager.gate_data) + 1)],
                         key="select_shape_id",
                         on_change=select_shape)

            st.selectbox("削除したい図形のIDを選択してください",
                         [""] + [str(value) for value in range(1, len(map_manager.draw_data) + 1)],
                         key="delete_shape_id",
                         on_change=delete_shape)

            st.write("ゲートと通過時刻")
            st.write(map_manager.tuuka_list)
            st.write(map_manager.selected_shape_type)
            st.write(map_manager.selected_shape)

    with tab4:
        if len(data_manager.df) != 0:
            st.checkbox(label='軌跡の表示', key='kiseki_flag', on_change=kiseki_draw)
