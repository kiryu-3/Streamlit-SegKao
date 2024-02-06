import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet
import re
import requests
from PIL import Image
import io
from io import BytesIO

# 画像URLを指定
image_url = "https://imgur.com/C32lMvR.jpg"

# 画像をダウンロードしPILのImageオブジェクトとして読み込む
response = requests.get(image_url)
image = Image.open(BytesIO(response.content))

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
    st.session_state['df'] = list()
    st.session_state["ja_honyaku"] = list()
    
    if st.session_state['upload_csvfile'] is not None:
        st.session_state["ja_honyaku"] += [False] * len(st.session_state['upload_csvfile'])
        for idx, uploaddata in enumerate(st.session_state['upload_csvfile']):
            # アップロードされたファイルデータを読み込む
            file_data = uploaddata.read()
            # バイナリデータからPandas DataFrameを作成
            try:
                df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8", engine="python")
                st.session_state["ja_honyaku"][idx] = False
            except UnicodeDecodeError:
                # UTF-8で読み取れない場合はShift-JISエンコーディングで再試行
                df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
                st.session_state["ja_honyaku"][idx] = True

            # カラムの型を自動で適切に変換
            st.session_state[f'df_{idx+1}'] = reduce_mem_usage(df)
            st.session_state['df'].append(st.session_state[f'df_{idx+1}'])

st.title('Mito')
st.sidebar.file_uploader(label="CSVファイルをアップロード（複数可）",
                       type=["csv"],
                       key="upload_csvfile",
                       accept_multiple_files=True,
                       on_change=upload_csv
                       )

# Graphic Walker 操作（メインパネル）
if st.session_state['upload_csvfile'] is not None:
    final_dfs, code = spreadsheet(*st.session_state['df'])

    tabs_list = list()
    for idx, (key, value) in enumerate(final_dfs.items()):
        tabs_list.append(f"df_{idx+1}")
    # タブ
    tabs = st.tabs(tabs_list)

    for idx, (key, value) in enumerate(final_dfs.items()):
        with tabs[idx]:
            st.caption(f"df_{idx+1}")
            st.write(pd.DataFrame(value))

            upload_name = st.session_state['upload_csvfile'][idx].name

            download_name = upload_name.split(".")[0]
            st.write("ファイル名を入力してください")
            st.text_input(
              label="Press Enter to Apply",
              value=f"{download_name}_filtered",
              key=f"download_name_{idx}"
            )

            download_df = pd.DataFrame(value)
            if st.session_state["ja_honyaku"][idx]:
              csv_file = download_df.to_csv(index=False, encoding="shift-jis")
            else:
              csv_file = download_df.to_csv(index=False, encoding="utf-8")
            st.download_button(
              label="Download CSV",
              data=csv_file,
              file_name=f'{st.session_state[f"download_name_{idx}"]}.csv'
            )

    with st.expander("Code"):
        st.code(code)
