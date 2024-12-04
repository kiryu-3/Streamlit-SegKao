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

    if name=="answers_df":
        # 各カテゴリごとに平均を算出
        df['オンライン・コラボレーション力'] = df.loc[:, 'Q1':'Q15'].mean(axis=1)
        df['データ利活用力'] = df.loc[:, 'Q16':'Q30'].mean(axis=1)
        df['情報システム開発力'] = df.loc[:, 'Q31':'Q44'].mean(axis=1)
        df['情報倫理力'] = df.loc[:, 'Q45':'Q66'].mean(axis=1)
    
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

    # # カテゴリごとのデータを取得
    # values = [melted_df[melted_df['category'] == category]['value'].values for category in categories]

    # # クラスカル・ウォリス検定を実行
    # stat, p = kruskal(*values) 

    # # 有意差が見られる場合、ポストホックテストを実行
    # if p < 0.05:
    #     # ポストホックテストの実行
    #     posthoc = sp.posthoc_dunn(values,  p_adjust='bonferroni')

    #     # 結果のDataFrameのカラム名とインデックスを設定
    #     posthoc.columns = categories
    #     posthoc.index = categories

    #     # st.write(posthoc)
        
    #     # 有意差が見られるカテゴリ間の組み合わせをリスト内包表記で取得
    #     significant_pairs = [
    #         (idx, col)
    #         for col in posthoc.columns
    #         for idx in posthoc.index
    #         if posthoc.loc[idx, col] < 0.05
    #     ]

    #     # 重複を取り除くために、タプルをソートして集合に変換
    #     filtered_pairs = {tuple(sorted(pair)) for pair in significant_pairs}

    # else :
    #     filtered_pairs = set()

    return summary_stats, fig
    # return summary_stats, fig, filtered_pairs

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

    # # 結果を格納するためのリスト
    # result_pairs = []
    # y_offset = 0.5  # 最初のブラケットの高さオフセット
    # y_increment = 0.3  # 複数のブラケットが重なった場合の追加オフセット
    # flag = 0

    # for category in categories:
    #     # 学年ごとのデータを取得
    #     values = [melted_df[melted_df['category']==category][melted_df['grade'] == grade]['value'].values for grade in grades]
        
    #     # クラスカル・ウォリス検定を実行
    #     stat, p = kruskal(*values) 

    #     # 有意差が見られる場合、ポストホックテストを実行
    #     if p < 0.05:
    #         # ポストホックテストの実行
    #         posthoc = sp.posthoc_dunn(values,  p_adjust='bonferroni')

    #         # 結果のDataFrameのカラム名とインデックスを設定
    #         posthoc.columns = grades
    #         posthoc.index = grades

    #         # st.write(posthoc)
            
    #         # 有意差が見られるカテゴリ間の組み合わせをリスト内包表記で取得
    #         significant_pairs = [
    #             (category, idx, col)
    #             for col in posthoc.columns
    #             for idx in posthoc.index
    #             if posthoc.loc[idx, col] < 0.05
    #         ]

    #         # 重複を取り除くために、タプルをソートして集合に変換
    #         filtered_pairs = {tuple(sorted(pair)) for pair in significant_pairs}

    #         result_pairs.append(filtered_pairs)
    #     else:
    #         # ポストホックテストの実行
    #         posthoc = sp.posthoc_dunn(values,  p_adjust='bonferroni')

    #         # 結果のDataFrameのカラム名とインデックスを設定
    #         posthoc.columns = grades
    #         posthoc.index = grades

    return summary_stats, fig
    # return summary_stats, fig, result_pairs

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

# st.write(st.session_state['questions_df'])
st.write(st.session_state['answers_df'])
tab_list = categories + ["各分野のスコア分布", "各分野の学年別のスコア分布"]

tabs = st.tabs(tab_list)
# タブとカテゴリのループ
for i, tab in enumerate(tabs):
    if tab_list[i] == "各分野のスコア分布":
        with tab:
            categories_df, fig = categories_test(st.session_state['answers_df'], categories)
            with st.expander("各分野の平均・標準偏差"):
                st.dataframe(categories_df)
            with st.expander("各分野のスコア分布"):
                st.plotly_chart(fig)
    elif tab_list[i] == "各分野の学年別のスコア分布":
        with tab:
            grade_df, fig = grade_test(st.session_state['answers_df'], categories, grades)
            with st.expander("各分野の学年別の平均・標準偏差"):
                st.dataframe(grade_df)
            with st.expander("各分野の学年別のスコア分布"):
                st.plotly_chart(fig)
    else:
        with tab:
            analyze_selected_category(tab_list[i], grades, st.session_state['answers_df'], st.session_state['questions_df'])
