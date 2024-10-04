import itertools
import numpy as np
import pandas as pd
import streamlit as st
import io

# Streamlit ページの設定
st.set_page_config(
    page_title="prokiso-edit",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)


# サイドバーにメッセージを表示
st.header("プロジェクト基礎演習-グルーピング")
st.write("プロジェクト基礎演習・要件定義チームの班分けのためのツールです")

st.write("左に表示されているサイドバーから行いたい項目を選択してください。")
st.write("「要求数」カウントは不確定な要素があるので、本ツールのカウント後の結果を必ず目でも確認してください")
st.write("現在は「たい」を区切り文字としてカウントしています")
st.write("「要求数」列があるcsvをグルーピングのページにてアップロードすると、要求数がグループ間で比較的同じになるようにグループ分けがなされます")
