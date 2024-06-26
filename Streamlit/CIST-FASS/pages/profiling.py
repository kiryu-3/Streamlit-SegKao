# 標準ライブラリ
import io
import os
import re
from io import BytesIO

# サードパーティのライブラリ
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
import streamlit as st
from PIL import Image
from ydata_profiling import ProfileReport

# streamlit関連のライブラリ 
from mitosheet.streamlit.v1 import spreadsheet
from streamlit_ydata_profiling import st_profile_report


# 画像ファイルのパス
image_path = os.path.join(os.path.dirname(__file__), '..', 'icon_image.png')

# 画像をPILのImageオブジェクトとして読み込む
image = Image.open(image_path)

# Streamlit ページの設定
st.set_page_config(
    page_title="EDAML-hub",
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

# 初期モード設定
if 'select_mode' not in st.session_state:  # 初期化
    st.session_state.select_mode = "***CSVファイル***"

def reduce_mem_usage(df, verbose=True):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    start_mem = df.memory_usage().sum() / 1024**2
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
    end_mem = df.memory_usage().sum() / 1024**2
    return df

def upload_csv():
    # csvがアップロードされたとき
    # st.session_state['df'] = list()
    st.session_state["ja_honyaku"] = list()
    
    if st.session_state['upload_csvfile'] is not None:
        st.session_state["ja_honyaku"] += [False] * len(st.session_state['upload_csvfile'])
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile'][0].read()
        # バイナリデータからPandas DataFrameを作成
        try:
            df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8", engine="python")
            st.session_state["ja_honyaku"] = False
        except UnicodeDecodeError:
            # UTF-8で読み取れない場合はShift-JISエンコーディングで再試行
            df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
            st.session_state["ja_honyaku"] = True
            

        # カラムの型を自動で適切に変換
        st.session_state['df'] = reduce_mem_usage(df)

    else:
        st.session_state['df'] = pd.DataFrame()

st.title('Profiling')
st.sidebar.file_uploader(label="CSVファイルをアップロード（複数可）",
                       type=["csv"],
                       key="upload_csvfile",
                       accept_multiple_files=True,
                       on_change=upload_csv
                       )

try: 
    if len(st.session_state['df']) != 0:
        st.dataframe(st.session_state['df'])
        pr = ProfileReport(st.session_state['df'], title="Report")

        st_profile_report(pr)
                
        st.divider()
        
        with st.expander("Code"):
            st.code(code)
except:
    pass
