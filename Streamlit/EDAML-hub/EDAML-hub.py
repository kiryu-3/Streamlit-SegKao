import streamlit as st
from PIL import Image
import os
import requests
import io
from io import BytesIO
import time
import pandas as pd
import numpy as np

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


st.write('# EDAML-hub')
st.caption("半自動で機械学習とデータ解析が行えます")
st.caption("サイドバーから行う作業を選択してください")

st.write('## Explanation')

with st.expander("データ解析"):
  st.markdown("""
    - 解析したいcsvファイルをアップロードすると自動で解析が始まる
    - Uユーザーが軸を選択して簡易的に相関を見れるようになっている
    - 読み込んだデータのカラム名からターゲットを選択する
    - 「EDAの実行」ボタンを押すと解析が始まる
  """)

with st.expander("回帰モデル"):
  st.markdown("""
    - 学習させたいcsvファイルをアップロードすると、データの確認ができる
    - ターゲットを選択しボタンを押すと、内部で[PyCaret](https://pycaret.org/)が動作し、複数のモデルを評価してくれる
    - 良さそうなモデルを選んでサイドバーに出現した「モデルをチューニング」ボタンを押す
  　- その後モデルの可視化と検証用のデータの予測が行える（元のモデルorチューニング後）
    - 
    - 残差プロットと予測誤差プロットが表示される
    - 自動で分割された検証用データで予測が行える
  """)

with st.expander("分類モデル"):
  st.markdown("""
    - 学習させたいcsvファイルをアップロードすると、データの確認ができる
    - ターゲットを選択しボタンを押すと、内部で[PyCaret](https://pycaret.org/)が動作し、複数のモデルを評価してくれる
    - 良さそうなモデルを選んでサイドバーに出現した「モデルをチューニング」ボタンを押す
  　- その後モデルの可視化と検証用のデータの予測が行える（元のモデルorチューニング後）
    - 
    - ROC曲線と混同行列が表示される
    - 自動で分割された検証用データで予測が行える
  """)

with st.expander("CSV-Filter"):
  st.markdown("""
    - CSVs can be filtered and then downloaded.
    - Basic CSV files of all types are supported.
  """)
  # st.write("Can translate input text into a specified language")
  # st.write("The translated text can be downloaded in mp3 format after being converted to audio")

  response2 = requests.get("https://imgur.com/kOBBXOb.png")
  image_example2 = Image.open(BytesIO(response2.content))
  st.image(image_example2)

with st.expander("Pygwalker"):
  st.markdown("""
    - データをTableau風のGUIで探索・可視化できる
    - 手元操作で試行錯誤しながらデータが探索できる
    - 2変数の単純なグラフ化だけではなく、多角的なデータの見方を支援してくれるツールになっている
  """)


