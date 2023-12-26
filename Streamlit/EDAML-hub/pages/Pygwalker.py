# モジュールの読み込み
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import pygwalker as pyg
from pygwalker.api.streamlit import init_streamlit_comm, get_streamlit_html

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


init_streamlit_comm()

# 今回のデータ生成に使う関数
def distance(x, y):
  # 東京タワーの座標を基準に値を生成する
  _x = 139.745433
  _y = 35.658581
  return ((x - _x)**2 + (y - _y)**2)**0.5

# ランダムなデータをnum_rows行を生成する
num_rows = 3000
df = pd.DataFrame(index=range(num_rows), columns=['名称', '緯度', '経度'])
df['名称'] = [''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=7)) for i in range(num_rows)]
df['緯度'] = [random.uniform(34, 38) for i in range(num_rows)]
df['経度'] = [random.uniform(135, 141) for i in range(num_rows)]
df['距離'] = [distance(df['経度'][i], df['緯度'][i]) for i in range(num_rows)]
df['カテゴリ'] = [random.randint(1, 10) for i in range(num_rows)]
df['バリュー'] = [random.random() * 100 for i in range(num_rows)]

# Graphic Walker 操作（メインパネル）
if df is not None:
    pyg_html = get_streamlit_html(df, spec="./gw0.json", use_kernel_calc=True, debug=False)


    # HTMLをStreamlitアプリケーションに埋め込む
    components.html(pyg_html, width=1300, height=1000, scrolling=True)
