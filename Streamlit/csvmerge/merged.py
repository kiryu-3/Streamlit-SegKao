import streamlit as st
import numpy as np
import pandas as pd
import re
import os
import requests
from PIL import Image
import io
from io import BytesIO
import chardet

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
    if st.session_state['upload_csvfile'] is not None:
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile'].read()
        # エンコーディングを検出
        raw_data = io.BytesIO(file_data).read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        st.write(encoding)
        
        try:
            df = pd.read_csv(io.BytesIO(file_data), header=None, encoding=encoding, engine="python")
        except Exception as e:
            st.write(f"データの読み込み中にエラーが発生しました: {e}")

        q_number = 1  # 初期値を設定
        st.session_state['question_dict'] = dict()
        
        while True:  # 無限ループ
            try:
                # Qの問題文を探す
                q_index = df[df[0] == f'Q {q_number}'].index[0]  # Qのインデックスを取得
                q_question = df.iloc[q_index + 1, 0]  # Qの問題文を取得
                
                # 結果を表示
                st.write(f"Q{q_number}の問題文:", q_question)
                st.session_state['question_dict'][f'Q{q_number}'] = q_question
                
                q_number += 1  # 次の番号に進む
            except IndexError:
                # インデックスエラーが発生した場合にループを抜ける
                st.write("ループを終了します。")
                break
            except Exception as e:
                # 他のエラーをキャッチする場合
                st.write(f"予期しないエラーが発生しました: {e}")
                break

        
        st.session_state['question_df'] = df
    else:
        st.session_state['question_df'] = pd.DataFrame()

def upload_csv2():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile2'] is not None:
        for idx, uploaddata in enumerate(st.session_state['upload_csvfile2']):
            # アップロードされたファイルデータを読み込む
            file_data = uploaddata.read()
            # バイナリデータからPandas DataFrameを作成
            try:
                df = pd.read_csv(io.BytesIO(file_data), header=None, encoding="utf-8", engine="python")
            except UnicodeDecodeError:
                # UTF-8で読み取れない場合はShift-JISエンコーディングで再試行
                df = pd.read_csv(io.BytesIO(file_data), header=None, encoding="shift-jis", engine="python")

            

            st.session_state['question_df'] = df
    else:
        st.session_state['question_df'] = pd.DataFrame()

# 初期化
if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame()  # 空のデータフレーム

st.title('Mito-CSV')
st.sidebar.file_uploader(label="設問文のCSVファイルをアップロード",
                       type=["csv"],
                       key="upload_csvfile",
                       accept_multiple_files=False,
                       on_change=upload_csv
                       )

st.file_uploader(label="設問回答のCSVファイルをアップロード（複数可）",
                       type=["csv"],
                       key="upload_csvfile2",
                       accept_multiple_files=True,
                       on_change=upload_csv
                       )

try: 
    if len(st.session_state['df']) != 0:
        for df in st.session_state['df']:
            st.write(df)

            # ユーザーに数字を入力してもらう
            max_question_number = st.number_input("表示する質問番号の上限を入力してください", min_value=2, step=1)
        
            # 質問を格納するリスト
            questions = []
        
            for number in range(1, max_question_number):
                # Qの問題文を探す
                q_index = df[df[0] == f'Q {number}'].index[0]  # Qのインデックスを取得
                q_question = df.iloc[q_index + 1, 0]  # Qの問題文を取得
                
                # 結果を表示
                st.write(f"Q{number}の問題文:", q_question)

    # 結果の表示
    st.write("質問文:")
    for question in questions:
        st.write(f"{question[0]}: {question[1]}")  # 質問番号と問題文を表示
            
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
