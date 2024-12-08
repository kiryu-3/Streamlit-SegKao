import io
from io import BytesIO
import itertools
import hashlib

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
if 'questions_df' not in st.session_state:
    st.session_state['questions_df'] = pd.DataFrame()  # 空のデータフレーム
if 'answers_df' not in st.session_state:
    st.session_state['answers_df'] = pd.DataFrame()  # 空のデータフレーム

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

def analyze_selected_category(selected_category, grades, df, question_df):
    question_df = question_df[question_df["category"] == selected_category]

    # "B"から始まるものだけを残す
    grades = [grade for grade in grades if grade.startswith("B")]
    df = df[df['grade'].isin(grades)]

    for index, row in question_df.iterrows():
        st.write(f'Q{row['qnumber']}. {row["qsentence"]}')

        with st.expander("選択肢"):
            st.radio(
                label="rubric",
                options=[
                    f"(1) {row['level1'].split('.')[1].strip()}", 
                    f"(2) {row['level2'].split('.')[1].strip()}", 
                    f"(3) {row['level3'].split('.')[1].strip()}", 
                    f"(4) {row['level4'].split('.')[1].strip()}", 
                    f"(5) {row['level5'].split('.')[1].strip()}"
                ],
                index=None,
                key=f"radio_{row['qnumber']}",
                label_visibility="collapsed",
                disabled=True,
                horizontal=False,
            )
      
        # skill_{qnumber}列をndarrayに変換
        qnumber = row['qnumber'] 
        skill_array = df[f"Q{qnumber}"].values

        # 5件法の割合を計算
        skill_point_total = len(skill_array)
        skill_point_counts = np.array([
            np.sum(skill_array == 1),
            np.sum(skill_array == 2),
            np.sum(skill_array == 3),
            np.sum(skill_array == 4),
            np.sum(skill_array == 5)
        ])
        skill_point_percentages = (skill_point_counts / skill_point_total) * 100

        # 全学年の平均スコアと標準偏差を計算
        overall_average_score = np.mean(skill_array)
        overall_std_score = np.std(skill_array)

        # 各学年の平均スコアと標準偏差を計算して表示
        grade_results = []
        for grade in grades:
            grade_df = df[df["grade"] == grade]
            grade_average_score = np.mean(grade_df[f"Q{qnumber}"].values)
            grade_std_score = np.std(grade_df[f"Q{qnumber}"].values)
            grade_results.append({"学年": grade, "平均スコア": grade_average_score, "標準偏差": grade_std_score})

        # "全学年"の結果を追加
        grade_results.append({"学年": "全学年", "平均スコア": overall_average_score, "標準偏差": overall_std_score})

        # データフレームに変換
        results_df = pd.DataFrame(grade_results)

        # 指定された色
        colors = ['#2B4C7E', '#AED6F1', '#95A5A6', '#E6B0AA', '#943126']
        
        # 積み上げ棒グラフの作成
        fig = go.Figure()

        # 積み上げ棒グラフ
        for i in range(5):
            fig.add_trace(go.Bar(
                x=[skill_point_percentages[i]],
                name=f"{i+1}：{skill_point_percentages[i]:.1f}%",  # 凡例に割合を表示
                marker_color=colors[i],  # 色を指定
                orientation='h',
                hovertemplate=f"%{{x:.1f}}%<br>N= {skill_point_counts[i]}<extra></extra>",
            ))
            
        # グラフのレイアウト
        fig.update_layout(
            barmode='stack',
            xaxis_title='割合 (%)',
            yaxis=dict(showticklabels=False),  # y軸の座標（数字）を非表示にする
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, traceorder="normal")  # 凡例をグラフの上に配置
        )

        st.plotly_chart(fig, key=f"plot_{qnumber}")

        with st.expander("学年ごとの分布"):
            # 積み上げ棒グラフの作成
            fig = go.Figure()
            
            for grade in grades:
                grade_df = df[df["grade"]==grade]
                skill_array = grade_df[f"Q{qnumber}"].values

                # 5件法の割合を計算
                skill_point_total = len(skill_array)
                skill_point_counts = np.array([
                    np.sum(skill_array == 1), 
                    np.sum(skill_array == 2),
                    np.sum(skill_array == 3),
                    np.sum(skill_array == 4),
                    np.sum(skill_array == 5)
                ])
                skill_point_percentages = (skill_point_counts / skill_point_total) * 100
    
                # 指定された色
                colors = ['#2B4C7E', '#AED6F1', '#95A5A6', '#E6B0AA', '#943126']
                
    
                # 積み上げ棒グラフ
                for i in range(5):
                    show_legend = True if grade == grades[0] else False  # 最初のグレードのみ凡例を表示
                    fig.add_trace(go.Bar(
                        y=[f"{grade}"],
                        x=[skill_point_percentages[i]],
                        name=f"{i+1}：{skill_point_percentages[i]:.1f}%",  # 凡例に割合を表示
                        marker_color=colors[i],  # 色を指定
                        orientation='h',
                        hovertemplate=f"%{{x:.1f}}%<br>N= {skill_point_counts[i]}<extra></extra>",
                        showlegend=False  # 凡例を完全に非表示にする
                    ))
                
            # グラフのレイアウト
            fig.update_layout(
                barmode='stack',
                xaxis_title='割合 (%)',
                yaxis=dict(categoryorder='array', categoryarray=["B4", "B3", "B2"]),  # グレードの順序を指定
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, traceorder="normal")  # 凡例をグラフの上に配置
            )

            st.plotly_chart(fig, key=f"plots_{qnumber}")

            # 統計量を表示
            st.write("各学年の平均スコア")
            st.write(results_df)

            # 各グループのスコアをリストに分ける
            groups = [df[df['grade'] == grade][f"skill{qnumber}"] for grade in df['grade'].unique()]
            
            # Kruskal-Wallis検定
            stat, p = kruskal(*groups)
            
            # 有意差がある場合、事後検定 (Dunn検定)
            if p < 0.05:
                st.write("学年間のスコアの有意（以下のp値が0.05以下の学年間は有意差あり）")
                
                # Dunn検定の実施
                posthoc_results = sp.posthoc_dunn(df, val_col=f"skill{qnumber}", group_col='grade', p_adjust='bonferroni')
                st.write(posthoc_results)
    
            else:
                st.write("学年間のスコアの有意差はありません")
    
# 初回ロード時またはキャッシュクリア時にデータを取得
if 'answers_hash' not in st.session_state:
    fetch_and_process_data()

st.header("情報活用力チェック 設問別分析")    

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
tab_list = categories
# tab_list = categories + ["各分野のスコア分布", "各分野の学年別のスコア分布"]

tabs = st.tabs(tab_list)
# タブとカテゴリのループ
for i, tab in enumerate(tabs):
   with tab:
      analyze_selected_category(tab_list[i], grades, st.session_state['answers_df'], st.session_state['questions_df'])
