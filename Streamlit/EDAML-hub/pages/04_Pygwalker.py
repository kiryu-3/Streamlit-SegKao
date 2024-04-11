# モジュールの読み込み
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import pygwalker as pyg
from pygwalker.api.streamlit import init_streamlit_comm, get_streamlit_html
import duckdb
import polars as pl

import re
import os
import requests
from PIL import Image
import io
from io import BytesIO

# 画像ファイルのパス
image_path = os.path.join(os.path.dirname(__file__), '..', 'icon_image.jpg')

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


init_streamlit_comm()

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
    if st.session_state['upload_csvfile'] is not None:
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile'].read()
        # バイナリデータからPandas DataFrameを作成
        try:
            df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8", engine="python")
            st.session_state["ja_honyaku"] = False
        except UnicodeDecodeError:
            # UTF-8で読み取れない場合はShift-JISエンコーディングで再試行
            df = pl.read_csv(io.BytesIO(file_data), encoding="shift-jis")
            # df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
            st.session_state["ja_honyaku"] = True

        # カラムの型を自動で適切に変換
        st.session_state['df'] = reduce_mem_usage(df)

            
st.title('Pygwalker')
st.file_uploader("CSVファイルをアップロード",
                       type=["csv"],
                       key="upload_csvfile",
                       on_change=upload_csv
                       )

# Graphic Walker 操作（メインパネル）
if st.session_state['upload_csvfile'] is not None:
    pyg_html = get_streamlit_html(st.session_state['df'], spec="./gw0.json", use_kernel_calc=True, debug=False)


    # HTMLをStreamlitアプリケーションに埋め込む
    components.html(pyg_html, width=1300, height=1000, scrolling=True)
