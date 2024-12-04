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
import gspread

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
def get_spreadsheet_data(spreadsheet_id, sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    data = pd.read_csv(url, header=0)  # header=0 で1行目を列名として扱う

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

def upload_csv():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile'] is not None:
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile'].read()
        try:
            # Shift-JISで読み込みを試みる
            df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
        except UnicodeDecodeError:
            # Shift-JISで失敗したらUTF-8で再試行
            df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8", engine="python") 
                

        # 各カテゴリごとに平均を算出
        df['オンライン・コラボレーション力'] = df[df.columns[6:21]].mean(axis=1)  # オンライン・コラボレーション力
        df['データ利活用力'] = df[df.columns[21:36]].mean(axis=1)  # データ利活用力
        df['情報システム開発力'] = df[df.columns[36:50]].mean(axis=1)  # 情報システム開発力
        df['情報倫理力'] = df[df.columns[50:72]].mean(axis=1)  # 情報倫理力

        st.session_state['df'] = df
    else:
        # upload_csvfileがNoneの場合、空のデータフレームを作成
        st.session_state['df'] = pd.DataFrame()  # 空のデータフレーム

def upload_csv2():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile2'] is not None:
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile2'].read()
        try:
            # Shift-JISで読み込みを試みる
            df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
        except UnicodeDecodeError:
            # Shift-JISで失敗したらUTF-8で再試行
            df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8", engine="python") 

        st.session_state['question_df'] = df
    else:
        # upload_csvfileがNoneの場合、空のデータフレームを作成
        st.session_state['question_df'] = pd.DataFrame()  # 空のデータフレーム

def find_significantly_high_skill3s(df):
    # 'skill' を含む列を選択
    df = df[[col for col in df.columns if 'skill' in col]]
    
    # データの総要素数
    total_elements = df.size
    
    # 各列の '3' の数をカウント
    column_3_counts = (df == 3).sum(axis=0)
    
    # 全体の '3' の数をカウント
    total_3_count = (df == 3).sum().sum()
    
    # 各列と全体の '3' の割合を計算
    column_3_proportions = column_3_counts / df.shape[0]
    overall_3_proportion = total_3_count / total_elements
    
    # p値が0.05以下かつ割合が全体より優位に高いスキル番号を格納するリスト
    significant_skills = []
    
    # 各列に対して二項検定を実施
    for col_name, count, proportion in zip(df.columns, column_3_counts, column_3_proportions):
        binom_test = stats.binomtest(count, df.shape[0], overall_3_proportion)
        p_value = binom_test.pvalue
        
        # p値が0.05以下かつ割合が全体より高い場合
        if p_value < 0.05 and proportion > overall_3_proportion:
            # 'skill' の後ろの番号を抽出してリストに追加
            skill_number = col_name.replace('skill', '')
            significant_skills.append(skill_number)
    
    return significant_skills

def analyze_selected_category(selected_category, grades, df, question_df):
    question_df = question_df[question_df["category"] == selected_category]

    # "B"から始まるものだけを残す
    grades = [grade for grade in grades if grade.startswith("B")]
    df = df[df['grade'].isin(grades)]

    for index, row in question_df.iterrows():
        st.write(f'Q{row['qnumber']}. {row["qsentence"]}')

        with st.expander("選択肢"):
            st.radio(
                options=[row['lebel1'], row['lebel2'], row['lebel3'], row['lebel4'], row['lebel5']],
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
            grade_average_score = np.mean(grade_df[f"skill{qnumber}"].values)
            grade_std_score = np.std(grade_df[f"skill{qnumber}"].values)
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

        st.plotly_chart(fig)

        with st.expander("学年ごとの分布"):
            # 積み上げ棒グラフの作成
            fig = go.Figure()
            
            for grade in grades:
                grade_df = df[df["grade"]==grade]
                skill_array = grade_df[f"skill{qnumber}"].values

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

            st.plotly_chart(fig)

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

tabs = st.tabs(categories)
# タブとカテゴリのループ
for i, tab in enumerate(tabs):
    with tab:
        analyze_selected_category(categories[i], grades, st.session_state['answers_df'], st.session_state['questions_df'])
