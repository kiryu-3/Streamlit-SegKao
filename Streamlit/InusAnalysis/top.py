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

# サイドバーにメッセージを表示
st.header("情報活用力チェック結果分析ツール")
st.write("情報活用力チェックの結果を分析するためのツールです。")
st.write("https://inuscheck2.pythonanywhere.com/")
st.write("左に表示されているサイドバーから行いたい分析項目を選択してください。")

st.subheader('各項目説明')

with st.expander("設問別スコアの分析（basic-aggregation）"):
  st.markdown("""
    - チェック結果と設問のcsv2つをアップロードすると、設問ごとのスコア分布を確認できる  
    - 各設問ごとに、対象全体のスコア分布と、学年別のスコア分布を確認できる  
    - "どちらともいえない"が有位に多く選択された設問とその分布を確認できる  
  """)

with st.expander("分野別スコアの分析（category-scores）"):
  st.markdown("""
    - チェック結果のcsvをアップロードすると、分野ごとのスコア分布を確認できる      
    - 分野ごとのスコア分布が正規分布かどうか、シャピロウィルク検定によって判定できる      
    - 分野間でスコアの有意差があるかどうか、ある場合はどの分野間かを判定できる      
    - 分野別において、学年間にスコアの有意差があるかどうか、ある場合はどの学年間かを判定できる      
    - 分野別において、資格の有無でスコアの有意差があるかどうかを判定できる      
  """)

with st.expander("所要時間の分析（required-seconds）"):
  st.markdown("""
    - チェック結果のcsvをアップロードすると、所要時間の分布を確認できる      
    - 所要時間の分布が正規分布かどうか、シャピロウィルク検定によって判定できる      
    - 学年間で所要時間の有意差があるかどうか、ある場合はどの学年間かを判定できる      
  """)

with st.expander("アンケートコメントの分析（comment-analysis）"):
  st.markdown("""
    - チェック結果のcsvをアップロードすると、アンケートに記入された自由記述コメントを確認できる  
    - 頻出単語ランキング、ワードクラウド、ツリーマップ、共起ネットワーク、サンバーストチャートを表示できる  
  """)

