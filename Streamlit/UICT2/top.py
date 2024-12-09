import io
from io import BytesIO
import itertools

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib_fontja
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import statsmodels.api as sm
from scipy import stats
from scipy.stats import kruskal, shapiro
import scikit_posthocs as sp
import streamlit as st


# Streamlit ページの設定
st.set_page_config(
    page_title="情報活用力チェック-結果分析",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 初期化
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False  # False

if not st.session_state['submitted']:
    # 管理者用のユーザー名とパスワードをst.secretsから取得
    ADMIN_USERNAME = st.secrets["admin_username"]
    ADMIN_PASSWORD = st.secrets["admin_password"]
    
    # ユーザー名とパスワードの入力フォーム
    with st.form("login_form"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")
        if submitted and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state['submitted'] = True
else:
    # サイドバーにメッセージを表示
    st.header("情報活用力チェック結果分析ツール")
    st.write("情報活用力チェックの結果を分析するためのツールです。")
    st.write("https://inuscheck2.pythonanywhere.com/")
    st.write("左に表示されているサイドバーから行いたい分析項目を選択してください。")
    
    st.subheader('各項目説明')
    
    with st.expander("設問別スコアの分析（question）"):
      st.markdown("""
        - 設問ごとのスコア分布を確認できる  
        - 各設問ごとに、対象全体のスコア分布と、学年別のスコア分布を確認できる   
      """)
    
    with st.expander("分野別スコアの分析（category）"):
      st.markdown("""
        - 分野ごとのスコア分布を確認できる      
        - 分野ごとのスコア分布が正規分布かどうか、シャピロウィルク検定によって判定できる      
        - 分野間でスコアの有意差があるかどうか、ある場合はどの分野間かを判定できる      
        - 分野別において、学年間にスコアの有意差があるかどうか、ある場合はどの学年間かを判定できる           
      """)
    
    with st.expander("所要時間の分析（required-seconds）"):
      st.markdown("""
        - 所要時間の分布を確認できる      
        - 所要時間の分布が正規分布かどうか、シャピロウィルク検定によって判定できる      
        - 学年間で所要時間の有意差があるかどうか、ある場合はどの学年間かを判定できる      
      """)
    
    with st.expander("アンケートの分析（questionnaire）"):
      st.markdown("""
        - アンケートの選択回答・自由記述を確認できる
        - 選択回答は棒グラフで全体・学年別のスコア分布を確認できる
        - 頻出単語ランキング、ワードクラウド、ツリーマップ、共起ネットワーク、サンバーストチャートを表示できる  
      """)
