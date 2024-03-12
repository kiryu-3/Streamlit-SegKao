import streamlit as st
from streamlit_folium import st_folium
from utils.data_manager import DataManager
from utils.map_manager import MapManager
from utils.shape_manager import ShapeManager
from utils.analysis_manager import AnalysisManager
from PIL import Image
import os

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

# インスタンス化
data_manager = DataManager()
map_manager = MapManager()
shape_manager = ShapeManager()
analysis_manager = AnalysisManager()

# サイドバー
with st.sidebar:
    # タブ
    tab1, tab2, tab3, tab4 = st.tabs(["Uploader", "Data_info", "Gate_info", "Kiseki_info"])

    # csvのuploader
    with tab1:
        # CSVファイルのアップロード
        uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"], key="upload_csvfile")
        if uploaded_file is not None:
            data_manager.load_data(uploaded_file)

    # csvから読み込んだIDの表示とプロットするマーカー・軌跡の選択
    with tab2:
        if data_manager.df is not None:
            st.write(data_manager.df_new)
            if data_manager.df is not None:
                selected_ids = st.multiselect("選択してください", data_manager.df.iloc[:, 0].unique(), key="select_data_id")
                if selected_ids:
                    data_manager.filter_data(selected_ids)
                    map_manager.draw_map(data_manager.sorted_df)
                    csv_file = data_manager.sorted_df.to_csv(index=False)
                    st.download_button(label="Download CSV", data=csv_file, file_name='sorted.csv')

    # 図形の情報の選択と削除
    with tab3:
        if shape_manager.draw_data:
            selected_shape_id = st.selectbox("表示したい図形のIDを選択してください",
                                             [""] + [str(value) for value in range(1, len(shape_manager.gate_data) + 1)],
                                             key="select_shape_id")
            if selected_shape_id:
                shape_manager.select_shape(int(selected_shape_id))

            deleted_shape_id = st.selectbox("削除したい図形のIDを選択してください",
                                            [""] + [str(value) for value in range(1, len(shape_manager.draw_data) + 1)],
                                            key="delete_shape_id")
            if deleted_shape_id:
                shape_manager.delete_shape(int(deleted_shape_id))
                map_manager.draw_map(data_manager.sorted_df)

            st.write("ゲートと通過時刻")
            st.write(shape_manager.tuuka_list)
            st.write(shape_manager.selected_shape_type)
            st.write(shape_manager.selected_shape)

    # 軌跡を描画するか選択
    with tab4:
        if data_manager.df is not None:
            kiseki_flag = st.checkbox(label='軌跡の表示', key='kiseki_flag')
            if kiseki_flag:
                map_manager.draw_trajectories(data_manager.sorted_df)
            else:
                map_manager.remove_trajectories()

# 表示する地図
map_data = st_folium(map_manager.map, width=800, height=800)

st.write(dict(map_data))

# 地図データをコピー
map_manager.update_map_state(dict(map_data))

# 新しい図形が描画されたら処理
shape_manager.handle_new_shape(map_data, data_manager.sorted_df)

# グラフの表示
if shape_manager.gate_data and data_manager.df is not None:
    available_ids = [str(value) for value in range(1, len(shape_manager.gate_data) + 1) if len(shape_manager.tuuka_list[value - 1]) > 0]
    selected_graph_ids = st.multiselect("グラフを表示したい図形のIDを選択してください", available_ids, key="select_graph_ids")
    if selected_graph_ids:
        analysis_manager.create_graph(selected_graph_ids, shape_manager.tuuka_list)
