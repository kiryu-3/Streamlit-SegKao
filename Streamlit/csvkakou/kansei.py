import numpy as np
import pandas as pd
import streamlit as st
import streamlit_pandas_kaoru as spk
from datetime import datetime, timedelta
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
            df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
            st.session_state["ja_honyaku"] = True

        st.session_state["uploaded_df"] = df.copy()
        st.session_state["edited_df"] = df.copy()

st.title("CSV Kakou")

# タブ
st.file_uploader("CSVファイルをアップロード",
                   type=["csv"],
                   key="upload_csvfile",
                   on_change=upload_csv
                   )

if st.session_state["upload_csvfile"] is not None:
  
  st.dataframe(st.session_state["uploaded_df"])

  # 評価を置き換える辞書
  replacement_dict = {
      '非常に（左）': 1,
      'かなり（左）': 2,
      'やや（左）': 3,
      'どちらでもない': 4,
      'やや（右）': 5,
      'かなり（右）': 6,
      '非常に（右）': 7,
  }
  
  # 各評価カラムを辞書に基づいて置き換える
  for column in st.session_state["uploaded_df"].columns[2:]:
      st.session_state["edited_df"][column] = st.session_state["uploaded_df"][column].replace(replacement_dict)

  pload_name = st.session_state['upload_csvfile'].name
  download_name = upload_name.split(".")[0]
  st.write("ファイル名を入力してください")
  st.text_input(
      label="Press Enter to Apply",
      value=f"{download_name}_filtered",
      key="download_name"
  )
  
  if st.session_state["ja_honyaku"]:
      csv_file = st.session_state["edited_df"].to_csv(index=False, encoding="shift-jis")
  else:
      csv_file = st.session_state["edited_df"].to_csv(index=False, encoding="utf-8")
  st.download_button(
      label="Download CSV",
      data=csv_file,
      file_name=f'{st.session_state["download_name"]}.csv'
  )
    
