import itertools

import io
from io import BytesIO
import hashlib

import gspread
import matplotlib.pyplot as plt
import matplotlib_fontja
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import scikit_posthocs as sp
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from scipy.stats import kruskal, shapiro
import streamlit as st


# Streamlit ページの設定
st.set_page_config(
    page_title="情報活用力チェック-集計結果",
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
if 'questions_df' not in st.session_state:
    st.session_state['questions_df'] = pd.DataFrame()  # 空のデータフレーム
if 'answers_df' not in st.session_state:
    st.session_state['answers_df'] = pd.DataFrame()  # 空のデータフレーム

# # スプレッドシートのデータを取得
# def get_spreadsheet_data(spreadsheet_id, sheet_name, name):
#     url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
#     df = pd.read_csv(url, header=0)  # header=0 で1行目を列名として扱う

#     # Q数字の列名を持つ列をフィルタリング
#     q_columns = [col for col in df.columns if col.startswith('Q') and col[1:].isdigit()]
#     # 対象の列にのみ処理を適用
#     df[q_columns] = df[q_columns].applymap(lambda x: int(x.split('.')[0]) if isinstance(x, str) and '.' in x else x)

#     if name=="answers_df":
#         # 各カテゴリごとに平均を算出
#         df['オンライン・コラボレーション力'] = df.loc[:, 'Q1':'Q15'].mean(axis=1)
#         df['データ利活用力'] = df.loc[:, 'Q16':'Q30'].mean(axis=1)
#         df['情報システム開発力'] = df.loc[:, 'Q31':'Q44'].mean(axis=1)
#         df['情報倫理力'] = df.loc[:, 'Q45':'Q66'].mean(axis=1)
    
#     st.session_state[name] = df

# スプレッドシートのデータを取得
@st.cache_data(show_spinner=False, ttl=60)
def get_spreadsheet_data(spreadsheet_id, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url, header=0)  # header=0 で1行目を列名として扱う
    return df

# ハッシュを計算してデータの変更を検知
def get_sheet_hash(spreadsheet_id, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    response = pd.read_csv(url, header=0)
    # データフレームの内容をハッシュ化
    sheet_hash = hashlib.md5(response.to_csv(index=False).encode()).hexdigest()
    return sheet_hash

# スプレッドシートデータを効率的に取得
def fetch_and_process_data():
    spreadsheet_id = st.secrets["SHEET_ID"]

    # スプレッドシートのハッシュを取得
    questions_hash = get_sheet_hash(spreadsheet_id, "questions")
    answers_hash = get_sheet_hash(spreadsheet_id, "answers")

    # データ取得と処理
    questions_df = get_spreadsheet_data(spreadsheet_id, "questions")
    answers_df = get_spreadsheet_data(spreadsheet_id, "answers")

    # 必要に応じて前処理
    q_columns = [col for col in answers_df.columns if col.startswith('Q') and col[1:].isdigit()]
    answers_df[q_columns] = answers_df[q_columns].applymap(lambda x: int(x.split('.')[0]) if isinstance(x, str) and '.' in x else x)

    # 各カテゴリごとの平均を計算
    answers_df['オンライン・コラボレーション力'] = answers_df.loc[:, 'Q1':'Q15'].mean(axis=1)
    answers_df['データ利活用力'] = answers_df.loc[:, 'Q16':'Q30'].mean(axis=1)
    answers_df['情報システム開発力'] = answers_df.loc[:, 'Q31':'Q44'].mean(axis=1)
    answers_df['情報倫理力'] = answers_df.loc[:, 'Q45':'Q66'].mean(axis=1)

    # セッション状態に保存
    st.session_state['questions_hash'] = questions_hash
    st.session_state['answers_hash'] = answers_hash
    st.session_state['questions_df'] = questions_df
    st.session_state['answers_df'] = answers_df

def display_summary(df, categories, grades):
    
    # 各学年の人数を辞書に格納
    grade_counts = {grade: len(df[df['grade'] == grade]) for grade in grades}
    
    # 各分野の質問数を辞書に格納
    question_counts = {
        'オンライン・コラボレーション力': len(df.columns[6:21]),
        'データ利活用力': len(df.columns[21:36]),
        '情報システム開発力': len(df.columns[36:50]),
        '情報倫理力': len(df.columns[50:72])
    }
    
    # データフレームを作成
    summary_df = pd.DataFrame({
        'Grade': grade_counts.keys(),
        'Count': grade_counts.values()
    })
    
    question_df = pd.DataFrame({
        'Category': question_counts.keys(),
        'Question Count': question_counts.values()
    })

    return summary_df, question_df
  
# 正規性の検定
def normality_test(df, categories):

    # start_timeとend_timeをdatetime型に変換
    df['start_time'] = pd.to_datetime(df['start_time'], format='%Y/%m/%d %H:%M:%S')
    df['end_time'] = pd.to_datetime(df['end_time'], format='%Y/%m/%d %H:%M:%S')
    
    # 所要時間を計算して新しい列に追加 (秒単位)
    df['required_time_seconds'] = (df['end_time'] - df['start_time']).dt.total_seconds()

    # 正規性の検証
    results = {}
    stat, p = stats.shapiro(df["required_time_seconds"])
    results["required-seconds"] = {
        'W統計量': stat,
        'p値': p,
        '正規性検定結果': '正規分布に従っている可能性がある' if p > 0.05 else '正規分布に従っていない'
    }
  
    # 結果の表示
    st.write("####  正規性検定の結果")
    result_df = pd.DataFrame(results).T  # 結果をデータフレームに変換
    # st.dataframe(result_df)

    # for column, result in results.items():
    #     if result['p値'] > 0.05:
    #         st.write(f"{column}列は正規分布に従っている可能性があります。")
    #     else:
    #         st.write(f"{column}列は正規分布に従っているとはいえません。")

    # ヒストグラムとQ-Qプロットを描画
    fig_hist, ax_hist = plt.subplots(2, 2, figsize=(12, 10))

    # ヒストグラムを描画
    sns.histplot(df["required_time_seconds"], kde=True, ax=ax_hist[0, 0], stat="density", linewidth=0)
    ax_hist[0, 0].set_title('required-seconds_distribution')
    ax_hist[0, 0].set_xlabel('required-seconds')
    ax_hist[0, 0].set_ylabel('密度')

    # 他のサブプロットを非表示にする
    for i in range(2):
        for j in range(2):
            if (i, j) != (0, 0):
                ax_hist[i, j].set_axis_off()

    plt.tight_layout()

    # Q-Qプロットを描画
    fig_qq, ax_qq = plt.subplots(2, 2, figsize=(12, 10))
    stats.probplot(df["required_time_seconds"], dist="norm", plot=ax_qq[0, 0])
    ax_qq[0, 0].set_title("Q-QPlot: required-seconds列")

    # 他のサブプロットを非表示にする
    for i in range(2):
        for j in range(2):
            if (i, j) != (0, 0):
                ax_qq[i, j].set_axis_off()
    
    plt.tight_layout()

    return result_df, fig_hist, fig_qq

# 分野間の差の検定をする関数
def categories_test(df, categories):
    # start_timeとend_timeをdatetime型に変換
    df['start_time'] = pd.to_datetime(df['start_time'], format='%Y/%m/%d %H:%M:%S')
    df['end_time'] = pd.to_datetime(df['end_time'], format='%Y/%m/%d %H:%M:%S')
    
    # 所要時間を計算して新しい列に追加 (秒単位)
    df['required_time_seconds'] = (df['end_time'] - df['start_time']).dt.total_seconds()
    
    # データフレームの整形
    summary_stats = df.agg(
        mean=('required_time_seconds', 'mean'),
        std=('required_time_seconds', 'std')
    ).reset_index()
    
    # 学年を追加
    summary_stats['grade'] = 'ALL'

    # ボックスプロットの描画
    fig = px.box(df, y='required_time_seconds', title='所要時間分布') 

    return summary_stats, fig

# 分野-学年間の差の検定をする関数
def grade_test(df, categories, grades):
    # start_timeとend_timeをdatetime型に変換
    df['start_time'] = pd.to_datetime(df['start_time'], format='%Y/%m/%d %H:%M:%S')
    df['end_time'] = pd.to_datetime(df['end_time'], format='%Y/%m/%d %H:%M:%S')
    
    # 所要時間を計算して新しい列に追加 (秒単位)
    df['required_time_seconds'] = (df['end_time'] - df['start_time']).dt.total_seconds()
    
    # "B"から始まるものだけを残す
    grades = [grade for grade in grades if grade.startswith("B")]

    # データフレームの整形
    df = df[df['grade'].isin(grades)]
    
    # 学年ごとの平均と標準偏差を取得
    summary_stats = df.groupby(['grade']).agg(
        mean=('required_time_seconds', 'mean'),
        std=('required_time_seconds', 'std')
    ).reset_index()

    # 'grade'列をgradesの順番に並べ替え
    df['grade'] = pd.Categorical(df['grade'], categories=grades, ordered=True)

    df = df.sort_values('grade')

    # ボックスプロットの描画
    fig = px.box(df, y='required_time_seconds', color='grade', title='学年ごとの所要時間分布') 

    # 結果を格納するためのリスト
    result_pairs = []
    flag = 0

    # 学年ごとのデータを取得
    values = [df[df['grade'] == grade]['required_time_seconds'].values for grade in grades]
    
    # クラスカル・ウォリス検定を実行
    stat, p = kruskal(*values)
    
    # 有意差が見られる場合、ポストホックテストを実行
    if p < 0.05:
        # ポストホックテストの実行
        posthoc = sp.posthoc_dunn(values, p_adjust='bonferroni')
    
        # 結果のDataFrameのカラム名とインデックスを設定
        posthoc.columns = grades
        posthoc.index = grades
        
        # 有意差が見られる学年間の組み合わせをリスト内包表記で取得
        significant_pairs = [
            (idx, col)
            for col in posthoc.columns
            for idx in posthoc.index
            if posthoc.loc[idx, col] < 0.05
        ]
    
        # 重複を取り除くために、タプルをソートして集合に変換
        filtered_pairs = {tuple(sorted(pair)) for pair in significant_pairs}
    
        result_pairs.append(filtered_pairs)
        
    return summary_stats, fig, result_pairs
  
# 初回ロード時またはキャッシュクリア時にデータを取得
if 'answers_hash' not in st.session_state:
    fetch_and_process_data()
    

st.header("情報活用力チェック 集計結果 所要時間")   

# get_spreadsheet_data(st.secrets["SHEET_ID"], "questions", "questions_df")
# get_spreadsheet_data(st.secrets["SHEET_ID"], "answers", "answers_df")

categories = ["オンライン・コラボレーション力", "データ利活用力", "情報システム開発力", "情報倫理力"]
grades = sorted(list(st.session_state['answers_df']['grade'].unique()))

summary_df, question_df = display_summary(st.session_state['answers_df'], categories, grades)
# 表形式で表示
cols = st.columns([3, 7])
cols[0].write("#### 各学年の人数")
cols[0].dataframe(summary_df)
cols[1].write("#### 各分野の質問数")
cols[1].dataframe(question_df)

# st.write(st.session_state['questions_df'])
# st.write(st.session_state['answers_df'])
# tab_list = categories + ["各分野のスコア分布", "各分野の学年別のスコア分布"]
tab_list = ["正規性の検定", "所要時間分布", "学年間の所要時間分布"]

tabs = st.tabs(tab_list)
# タブとカテゴリのループ
for i, tab in enumerate(tabs):

    if tab_list[i] == "正規性の検定":
        with tab:
          normality_df, fig_hist, fig_qq = normality_test(st.session_state['answers_df'], categories)
          st.dataframe(normality_df)
          with st.expander("所要時間分布"):
              st.pyplot(fig_hist)
          with st.expander("Q-Qプロット"):
              st.pyplot(fig_qq)
  
    elif tab_list[i] == "所要時間分布":
        with tab:
            categories_df, fig = categories_test(st.session_state['answers_df'], categories)
            with st.expander("所要時間分布"):
                st.plotly_chart(fig)
              
    elif tab_list[i] == "学年間の所要時間分布":
        with tab:
            grade_df, fig, result_pairs = grade_test(st.session_state['answers_df'], categories, grades)
            st.dataframe(grade_df)
            with st.expander("学年間の所要時間分布"):
                st.plotly_chart(fig)
                st.write("有意差が見られる学年間の組み合わせ：")
                for result_set in result_pairs:
                    for category, grade1, grade2 in result_set:
                        st.write(f"【{category}】：【{grade1}】-【{grade2}】")
