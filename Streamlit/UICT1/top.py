import itertools

import io
from io import BytesIO

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

# スプレッドシートのデータを取得
def get_spreadsheet_data(spreadsheet_id, sheet_name, name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url, header=0)  # header=0 で1行目を列名として扱う

    # Q数字の列名を持つ列をフィルタリング
    q_columns = [col for col in df.columns if col.startswith('Q') and col[1:].isdigit()]
    # 対象の列にのみ処理を適用
    df[q_columns] = df[q_columns].applymap(lambda x: int(x.split('.')[0]) if isinstance(x, str) and '.' in x else x)
    st.session_state[name] = df

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
                options=[row['level1'], row['level2'], row['level3'], row['level4'], row['level5']],
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

            # # 各グループのスコアをリストに分ける
            # groups = [df[df['grade'] == grade][f"skill{qnumber}"] for grade in df['grade'].unique()]
            
            # # Kruskal-Wallis検定
            # stat, p = kruskal(*groups)

            # # 統計量を表示
            # st.write("各学年の平均スコア")
            # st.write(results_df)
            
            # # 有意差がある場合、事後検定 (Dunn検定)
            # if p < 0.05:
            #     st.write("学年間のスコアの有意（以下のp値が0.05以下の学年間は有意差あり）")
                
            #     # Dunn検定の実施
            #     posthoc_results = sp.posthoc_dunn(df, val_col=f"skill{qnumber}", group_col='grade', p_adjust='bonferroni')
            #     st.write(posthoc_results)
    
            # else:
            #     st.write("学年間のスコアの有意差はありません")
    
st.header("設問別スコアの分析-基本集計")    

get_spreadsheet_data(st.secrets["SHEET_ID"], "questions", "questions_df")
get_spreadsheet_data(st.secrets["SHEET_ID"], "answers", "answers_df")

categories = ["オンライン・コラボレーション力", "データ利活用力", "情報システム開発力", "情報倫理力"]
grades = sorted(list(st.session_state['answers_df']['grade'].unique()))

summary_df, question_df = display_summary(st.session_state['answers_df'], categories, grades)
# 表形式で表示
cols = st.columns([3, 7])
cols[0].write("#### 各学年の人数")
cols[0].dataframe(summary_df)
cols[1].write("#### 各分野の質問数")
cols[1].dataframe(question_df)

st.write(st.session_state['answers_df'])

tabs = st.tabs(categories)
# タブとカテゴリのループ
for i, tab in enumerate(tabs):
    with tab:
        analyze_selected_category(categories[i], grades, st.session_state['answers_df'], st.session_state['questions_df'])
