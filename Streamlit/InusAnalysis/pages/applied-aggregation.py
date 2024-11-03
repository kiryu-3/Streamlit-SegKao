import io
from io import BytesIO
import re
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

# 初期化
if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame()  # 空のデータフレーム

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

def find_significantly_high_skill(df, selected_grade, selected_mode):
    # 選択された学年にデータをフィルタリング
    if selected_grade != "全学年":
        selected_df = df[df['grade']==selected_grade]
    else:
        selected_df = df
    
    # 'skill' と数字の列を選択
    df = df[[col for col in df.columns if re.match(r'skill\d+', col)]]
    selected_df = selected_df[[col for col in selected_df.columns if re.match(r'skill\d+', col)]]

    # データの総要素数
    total_elements = df.size

    if selected_mode == 'スコアが高い設問':
        # 各列の '4, 5' の数をカウント
        column_counts = ((selected_df == 4) | (selected_df == 5)).sum(axis=0)
        
        # 全体の '4, 5' の数をカウント
        total_count = ((df == 4) | (df == 5)).sum().sum()
        
    elif selected_mode == 'スコアが低い設問':
        # 各列の '1, 2' の数をカウント
        column_counts = ((selected_df == 1) | (selected_df == 2)).sum(axis=0)
        
        # 全体の '1, 2' の数をカウント
        total_count = ((df == 1) | (df == 2)).sum().sum()
    elif selected_mode == '"どちらともいえない"が多く選択された設問':
        # 各列の '3' の数をカウント
        column_counts = (selected_df == 3).sum(axis=0)
        
        # 全体の '3' の数をカウント
        total_count = (df == 3).sum().sum()
    
    # 各列と全体の count_score の割合を計算
    column_proportions = column_counts / selected_df.shape[0]
    overall_proportion = total_count / total_elements
    
    # p値が0.05以下かつ割合が全体より優位に高いスキル番号を格納するリスト
    significant_skills = []

    # st.write(total_elements)
    # st.write(selected_df.shape[0])
    # st.write(df.shape[0])
    # st.write(overall_proportion)
    # st.write(column_counts)
    # st.write(column_proportions)
    
    # 各列に対して二項検定を実施
    for col_name, count, proportion in zip(df.columns, column_counts, column_proportions):
        binom_test = stats.binomtest(count, selected_df.shape[0], overall_proportion)
        p_value = binom_test.pvalue
        
        # p値が0.05以下かつ割合が全体より高い場合
        if p_value < 0.01 and proportion > overall_proportion:
            # 'skill' の後ろの番号を抽出してリストに追加
            skill_number = col_name.replace('skill', '')
            significant_skills.append(skill_number)
    
    return significant_skills

def analyze_selected_grade(selected_mode, grades, selected_grade, df, question_df):
    significant_skills_number = find_significantly_high_skill(df, selected_grade, selected_mode)
    significant_skills_number = list(map(int, significant_skills_number))
    st.write(significant_skills_number)
    question_df = question_df[question_df["通し番号"].isin(significant_skills_number)]

    # "B"から始まるものだけを残す
    # grades = [grade for grade in grades if grade.startswith("B")]
    # df = df[df['grade'].isin(grades)]

    for index, row in question_df.iterrows():
        # skill_{qnumber}列をndarrayに変換
        qnumber = row['通し番号'] 
        skill_array = df[f"skill{qnumber}"].values

        # 5件法の割合を計算
        skill_point_total = len(skill_array)
        skill_point_counts = np.array([
            np.sum(skill_array == 1),  # 1：まったくあてはまらない
            np.sum(skill_array == 2),  # 2：あまりあてはまらない
            np.sum(skill_array == 3),  # 3：どちらともいえない
            np.sum(skill_array == 4),  # 4：ややあてはまる
            np.sum(skill_array == 5)   # 5：とてもあてはまる
        ])
        skill_point_percentages = (skill_point_counts / skill_point_total) * 100

        # 5件法の情報
        skill_point_labels = [
            "まったくあてはまらない (1)", 
            "あまりあてはまらない (2)", 
            "どちらともいえない (3)", 
            "ややあてはまる (4)", 
            "とてもあてはまる (5)"
        ]

        # 指定された色
        colors = ['#2B4C7E', '#AED6F1', '#95A5A6', '#E6B0AA', '#943126']
        
        # 積み上げ棒グラフの作成
        fig = go.Figure()

        # 積み上げ棒グラフ
        for i, label in enumerate(skill_point_labels):
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
            title=f'Q{row['通し番号']}：{row["質問文"]}',
            xaxis_title='割合 (%)',
            yaxis=dict(showticklabels=False),  # y軸の座標（数字）を非表示にする
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, traceorder="normal")  # 凡例をグラフの上に配置
        )

        if selected_mode == 'スコアが高い設問':
            st.plotly_chart(fig, key=f"sub_plot_high_{qnumber}")
        elif selected_mode == 'スコアが低い設問':
            st.plotly_chart(fig, key=f"sub_plot_low_{qnumber}")
        elif selected_mode == '"どちらともいえない"が多く選択された設問':
            st.plotly_chart(fig, key=f"sub_plot_draw_{qnumber}")
        else:
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
                    np.sum(skill_array == 1),  # 1：まったくあてはまらない
                    np.sum(skill_array == 2),  # 2：あまりあてはまらない
                    np.sum(skill_array == 3),  # 3：どちらともいえない
                    np.sum(skill_array == 4),  # 4：ややあてはまる
                    np.sum(skill_array == 5)   # 5：とてもあてはまる
                ])
                skill_point_percentages = (skill_point_counts / skill_point_total) * 100
    
                # 5件法の情報
                skill_point_labels = [
                    "まったくあてはまらない (1)", 
                    "あまりあてはまらない (2)", 
                    "どちらともいえない (3)", 
                    "ややあてはまる (4)", 
                    "とてもあてはまる (5)"
                ]
    
                # 指定された色
                colors = ['#2B4C7E', '#AED6F1', '#95A5A6', '#E6B0AA', '#943126']
                
    
                # 積み上げ棒グラフ
                for i, label in enumerate(skill_point_labels):
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

            if selected_mode == 'スコアが高い設問':
                st.plotly_chart(fig, key=f"sub_plots_high_{qnumber}")
            elif selected_mode == 'スコアが低い設問':
                st.plotly_chart(fig, key=f"sub_plots_low_{qnumber}")
            elif selected_mode == '"どちらともいえない"が多く選択された設問':
                st.plotly_chart(fig, key=f"sub_plots_draw_{qnumber}")
            else:
                st.plotly_chart(fig)

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
    
st.header("設問別スコアの分析")    
# ファイルアップロード
st.file_uploader("集計結果（5件法）のcsvをアップロード",
                       type=["csv"],
                       key="upload_csvfile",
                       on_change=upload_csv
                       )

# 設問文のファイルアップロード
st.file_uploader("設問文のcsvをアップロード",
                       type=["csv"],
                       key="upload_csvfile2",
                       on_change=upload_csv2
                       )

# データフレームを空にするボタン
# csvがアップロードされたとき
if len(st.session_state['df']) != 0:
    if st.button("アップロードしたCSVファイルを消去"):
        st.session_state['df'] = pd.DataFrame()  # 空のデータフレームを設定
        st.session_state['question_df'] = pd.DataFrame()  # 空のデータフレームを設定
        st.switch_page("top.py")
        st.rerun()  # アプリを再実行して状態を更新
        st.success("CSVファイルが消去されました。")

try:
    categories = ["オンライン・コラボレーション力", "データ利活用力", "情報システム開発力", "情報倫理力"]
    grades = sorted(list(st.session_state['df']['grade'].unique()))

    # user_idが22のものを除去する
    st.session_state['df'] = st.session_state['df'][st.session_state['df']["user_id"] != 22]

    selected_columns = st.session_state['df'].iloc[:, :5]
    categories_columns = st.session_state['df'][categories]
    final_df = pd.concat([selected_columns, categories_columns], axis=1)
    st.dataframe(final_df, width=None, height=500)

    summary_df, question_df = display_summary(st.session_state['df'], categories, grades)

    # 表形式で表示
    cols = st.columns([3, 7])
    cols[0].write("#### 各学年の人数")
    cols[0].dataframe(summary_df)
    cols[1].write("#### 各分野の質問数")
    cols[1].dataframe(question_df)

    if len(st.session_state['question_df']) != 0:
        st.markdown(
            """
            #### 1：まったくあてはまらない　2：あまりあてはまらない<br>3：どちらともいえない<br>4：ややあてはまる　5：とてもあてはまる
            """,
            unsafe_allow_html=True
        )
    
    # タブを作成
    # "B"から始まるものだけを残す
    grades = [grade for grade in grades if grade.startswith("B")]
    grades_list = grades + ['全学年']
    # '全学年'のインデックスを取得
    initial_index = grades_list.index('全学年')
  
    selected_grade = st.selectbox(
                      label='学年を選択してください',
                      options=grades_list,
                      index=initial_index,
                      placeholder="都市を選択してください")
  
    tab_list = ['スコアが高い設問', 'スコアが低い設問', '"どちらともいえない"が多く選択された設問']
    tabs = st.tabs(tab_list)

    # question_dfが未定義または空の場合のチェック
    if 'question_df' not in st.session_state or len(st.session_state['question_df']) == 0:
        # 各タブに同じエラーメッセージを表示
        for tab in tabs:
            with tab:
                st.error("設問文のcsvをアップロードしてください")
        
    else:
        # タブとカテゴリのループ
        for i, tab in enumerate(tabs):
            with tab:
                analyze_selected_grade(tab_list[i], grades, selected_grade, st.session_state['df'], st.session_state['question_df'])
    
except Exception as e:
    # st.write(e)
    pass
