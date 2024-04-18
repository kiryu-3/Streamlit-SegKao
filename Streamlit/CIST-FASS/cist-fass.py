import streamlit as st
from PIL import Image
import os
import requests
import io
from io import BytesIO
import time
import pandas as pd
import os

# 画像ファイルのパス
image_path = os.path.join(os.path.dirname(__file__), 'icon_image.png')

# 画像をPILのImageオブジェクトとして読み込む
image = Image.open(image_path)

# Streamlit ページの設定
st.set_page_config(
    page_title="CSV Filters",
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


st.write('# CIST-FASS')
st.caption("CIST Human Flow Analytics System with Streamlit-Folium")

st.write('## Explanation')

with st.expander("Human-Flow-Analytics"):
      st.markdown("""
        - CISTのオリジナル人流データ可視化ツールです。
        - 緯度と経度およびその時間情報を含むデータ（csv）をアップロードすることで、人の流れの可視化が可能になります。
        - ユーザーが地図上に形を描くと、その形を通過した人数を数えることができます。
        - アップロードするCSVファイルには、個人を識別するID、時間、緯度、経度のデータが含まれている必要があります。
      """)
      # st.write("The input text can be converted to speech")
      # st.write("Audio can be downloaded in mp3 format")
    
      # 画像ファイルのパス
      image_path = os.path.join(os.path.dirname(__file__), 'map_image.png')
        
      # 画像をPILのImageオブジェクトとして読み込む
      image_example1 = Image.open(image_path)
      st.image(image_example1)

with st.expander("CSV&Excel-Processer"):
  st.markdown("""
    - CSV/Excelファイルをインポートできる
    - 現在地での列の名前変更、並び替え、削除を行うことができる
    - 多くのフィルタ条件を持つフィルタリングを行うことができる
    - データの加工をExcelファイルを操作している感覚で行うことができる
  """)
  # st.write("Can translate input text into a specified language")
  # st.write("The translated text can be downloaded in mp3 format after being converted to audio")

  # 画像ファイルのパス
  image_path = os.path.join(os.path.dirname(__file__), 'csv_image.png')
    
  # 画像をPILのImageオブジェクトとして読み込む
  image_example2 = Image.open(image_path)
  st.image(image_example2)

with st.expander("Sample-Data"):
  st.markdown("""
    - 個人を識別するためのID、時間、緯度、経度情報を含むサンプルデータ。
    - 「Human-Flow-Analytics」と「CSV-Filter」に利用できます。
  """)

  # 現在のスクリプトのディレクトリを取得
  script_directory = os.path.dirname(os.path.abspath(__file__))
  # CSVファイルを読み込み
  example_data = pd.read_csv(os.path.join(script_directory, 'example_data.csv'))   
  csv_file = example_data.to_csv(index=False)
  st.download_button(
    label="Download CSV",
    data=csv_file,
    file_name='sample_data.csv'
  )
  st.dataframe(example_data)

with st.expander("profiling"):
  st.markdown("""
    - データセットの統計的要約を自動生成できる
    - 各列の欠損値、一意の値の数、データタイプなどを簡単に確認できる
    - 相関関係、ヒストグラム、散布図などの視覚化を通じて、データの分布や関係性を把握できる
    - データセットの品質を評価し、データクレンジングや前処理が必要な領域を特定できる
  """)


