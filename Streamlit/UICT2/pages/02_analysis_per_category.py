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

    # 正規性の検証
    results = {}
    for column in categories:
        stat, p = stats.shapiro(df[column])
        results[column] = {
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
    fig_hist, axes_hist = plt.subplots(2, 2, figsize=(12, 10))
    for ax, column in zip(axes_hist.flatten(), categories):
        sns.histplot(df[column], kde=True, ax=ax, stat="density", linewidth=0)
        ax.set_title(f'{column}_distribution')
        ax.set_xlabel(column)
        ax.set_ylabel('密度')

    plt.tight_layout()

    fig_qq, axes_qq = plt.subplots(2, 2, figsize=(12, 10))
    for ax, column in zip(axes_qq.flatten(), categories):
        stats.probplot(df[column], dist="norm", plot=ax)
        ax.set_title(f"Q-QPlot: {column}列")

    plt.tight_layout()

    return result_df, fig_hist, fig_qq

# 分野間の差の検定をする関数
def categories_test(df, categories):

    # データフレームの整形
    melted_df = df.melt(id_vars='grade', value_vars=categories,
                        var_name='category', value_name='value')


    # 全学年の平均と標準偏差を追加
    summary_stats = melted_df.groupby('category').agg(
        mean=('value', 'mean'),
        std=('value', 'std')
    ).reset_index()
    summary_stats['grade'] = 'ALL'

    # categoriesの順序を設定
    summary_stats['category'] = pd.Categorical(summary_stats['category'], categories=categories, ordered=True)
    # categoriesの順にソート
    summary_stats = summary_stats.sort_values("category", ascending=True)

    # ボックスプロットの描画
    fig = px.box(melted_df, x='category', y='value', title='各分野のスコア分布') 

    # カテゴリごとのデータを取得
    values = [melted_df[melted_df['category'] == category]['value'].values for category in categories]

    # クラスカル・ウォリス検定を実行
    stat, p = kruskal(*values) 

    # 有意差が見られる場合、ポストホックテストを実行
    if p < 0.05:
        # ポストホックテストの実行
        posthoc = sp.posthoc_dunn(values,  p_adjust='bonferroni')

        # 結果のDataFrameのカラム名とインデックスを設定
        posthoc.columns = categories
        posthoc.index = categories

        # st.write(posthoc)
        
        # 有意差が見られるカテゴリ間の組み合わせをリスト内包表記で取得
        significant_pairs = [
            (idx, col)
            for col in posthoc.columns
            for idx in posthoc.index
            if posthoc.loc[idx, col] < 0.05
        ]

        # 重複を取り除くために、タプルをソートして集合に変換
        filtered_pairs = {tuple(sorted(pair)) for pair in significant_pairs}

    else :
        filtered_pairs = set()

    return summary_stats, fig, filtered_pairs

# 分野-学年間の差の検定をする関数
def grade_test(df, categories, grades):

    # "B"から始まるものだけを残す
    grades = [grade for grade in grades if grade.startswith("B")]

    # データフレームの整形
    melted_df = df.melt(id_vars='grade', value_vars=categories,
                        var_name='category', value_name='value')
    melted_df = melted_df[melted_df['grade'].isin(grades)]

    # 学年ごとの平均と標準偏差を取得
    summary_stats = melted_df.groupby(['category', 'grade']).agg(
        mean=('value', 'mean'),
        std=('value', 'std')
    ).reset_index()

    # categoriesの順序を設定
    summary_stats['category'] = pd.Categorical(summary_stats['category'], categories=categories, ordered=True)
    # categoriesの順にソート
    summary_stats = summary_stats.sort_values("category", ascending=True)

    # 'grade'列をgradesの順番に並べ替え
    melted_df['grade'] = pd.Categorical(melted_df['grade'], categories=grades, ordered=True)
    # 'category'列をcategoriesの順番に並べ替え
    melted_df['category'] = pd.Categorical(melted_df['category'], categories=categories, ordered=True)

    melted_df = melted_df.sort_values(['grade', 'category'])

    # ボックスプロットの描画
    fig = px.box(melted_df, x='category', y='value', color='grade', title='各分野の学年ごとのスコア分布') 

    # 結果を格納するためのリスト
    result_pairs = []
    y_offset = 0.5  # 最初のブラケットの高さオフセット
    y_increment = 0.3  # 複数のブラケットが重なった場合の追加オフセット
    flag = 0

    for category in categories:
        # 学年ごとのデータを取得
        values = [melted_df[melted_df['category']==category][melted_df['grade'] == grade]['value'].values for grade in grades]
        
        # クラスカル・ウォリス検定を実行
        stat, p = kruskal(*values) 

        # 有意差が見られる場合、ポストホックテストを実行
        if p < 0.05:
            # ポストホックテストの実行
            posthoc = sp.posthoc_dunn(values,  p_adjust='bonferroni')

            # 結果のDataFrameのカラム名とインデックスを設定
            posthoc.columns = grades
            posthoc.index = grades

            # st.write(posthoc)
            
            # 有意差が見られるカテゴリ間の組み合わせをリスト内包表記で取得
            significant_pairs = [
                (category, idx, col)
                for col in posthoc.columns
                for idx in posthoc.index
                if posthoc.loc[idx, col] < 0.05
            ]

            # 重複を取り除くために、タプルをソートして集合に変換
            filtered_pairs = {tuple(sorted(pair)) for pair in significant_pairs}

            result_pairs.append(filtered_pairs)
        else:
            # ポストホックテストの実行
            posthoc = sp.posthoc_dunn(values,  p_adjust='bonferroni')

            # 結果のDataFrameのカラム名とインデックスを設定
            posthoc.columns = grades
            posthoc.index = grades

    return summary_stats, fig, result_pairs



# 初回ロード時またはキャッシュクリア時にデータを取得
if 'answers_hash' not in st.session_state:
    fetch_and_process_data()

st.header("情報活用力チェック 集計結果 分野・学年別")  

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
tab_list = ["正規性の検定", "各分野のスコア分布", "各分野の学年別のスコア分布"]

tabs = st.tabs(tab_list)
# タブとカテゴリのループ
for i, tab in enumerate(tabs):

    if tab_list[i] == "正規性の検定":
        with tab:
          normality_df, fig_hist, fig_qq = normality_test(st.session_state['answers_df'], categories)
          st.dataframe(normality_df)
          with st.expander("各分野のスコア分布"):
              st.pyplot(fig_hist)
          with st.expander("Q-Qプロット"):
              st.pyplot(fig_qq)
  
    elif tab_list[i] == "各分野のスコア分布":
        with tab:
            categories_df, fig, filtered_pairs = categories_test(st.session_state['answers_df'], categories)
            st.dataframe(categories_df)
            with st.expander("各分野のスコア分布"):
                st.plotly_chart(fig)
                st.write("有意差が見られる分野間の組み合わせ：")
                for category1, category2 in filtered_pairs:
                    st.write(f"【{category1}】-【{category2}】")
                    
    elif tab_list[i] == "各分野の学年別のスコア分布":
        with tab:
            grade_df, fig, result_pairs = grade_test(st.session_state['answers_df'], categories, grades)
            st.dataframe(grade_df)
            with st.expander("各分野の学年別のスコア分布"):
                st.plotly_chart(fig)
                st.write("有意差が見られる各分野の学年間の組み合わせ：")
                for result_set in result_pairs:
                    for category, grade1, grade2 in result_set:
                        st.write(f"【{category}】：【{grade1}】-【{grade2}】")
