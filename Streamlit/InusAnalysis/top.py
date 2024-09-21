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
    page_title="データ解析",
    layout="wide",
    initial_sidebar_state="expanded"
)

# サイドバーにメッセージを表示
st.header("情報開発力チェック結果分析ツール")
st.write("情報開発力チェックの結果を分析するためのツールです。")
st.write("https://inuscheck2.pythonanywhere.com/")
st.write("左に表示されているサイドバーから行いたい分析項目を選択してください。")
