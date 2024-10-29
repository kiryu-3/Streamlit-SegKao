import streamlit as st
import numpy as np
import pandas as pd
import re
import os
import requests
from PIL import Image
import io
from io import BytesIO


# Streamlit ページの設定
st.set_page_config(
    page_title="EDAML-hub",
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


st.title('Mito-CSV')
st.sidebar.file_uploader(label="CSVファイルをアップロード（複数可）",
                       type=["csv"],
                       key="upload_csvfile",
                       accept_multiple_files=True,
                       on_change=upload_csv
                       )

try: 
    if len(st.session_state['df']) != 0:
        for df in st.session_state['df']:
            st.write(df)

            # Q1の問題文を探す
            q1_index = df[df[0] == 'Q 1'].index[0]  # Q1のインデックスを取得
            q1_question = df.iloc[q1_index + 1, 0]  # Q1の問題文を取得
            
            # 結果を表示
            st.write("Q1の問題文:", q1_question)
            
        download_name = f"df_{idx+1}"
        st.write("ファイル名を入力してください")
        st.text_input(
          label="Press Enter to Apply",
          value=f"{download_name}_filtered",
          key=f"download_name_{idx}"
        )

        download_df = pd.DataFrame(value)
        if st.session_state['select_mode'] == "***CSVファイル***":
            if st.session_state["ja_honyaku"][idx]:
              csv_file = download_df.to_csv(index=False, encoding="shift-jis")
            else:
              csv_file = download_df.to_csv(index=False, encoding="utf-8")    
        else:
            csv_file = download_df.to_csv(index=False)
        st.download_button(
              label="Download CSV",
              data=csv_file,
              file_name=f'{st.session_state[f"download_name_{idx}"]}.csv'
            )
            
    st.divider()
    
    with st.expander("Code"):
        st.code(code)
except Exception as e:
    st.write(e)
