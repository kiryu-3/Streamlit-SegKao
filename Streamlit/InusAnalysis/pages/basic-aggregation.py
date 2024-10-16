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

# 初期化
if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame()  # 空のデータフレーム

def display_summary(df, categories, grades):
    
    # 各学年の人数を辞書に格納
    grade_counts = {grade: len(df[df['grade'] == grade]) for grade in grades}
    
    # 各分野の質問数を辞書に格納
    question_counts = {
        'online_collab': len(df.columns[6:21]),
        'data_utilization': len(df.columns[21:36]),
        'info_sys_dev': len(df.columns[36:50]),
        'info_ethics': len(df.columns[50:72])
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
        df['online_collab'] = df[df.columns[6:21]].mean(axis=1)  # オンライン・コラボレーション力
        df['data_utilization'] = df[df.columns[21:36]].mean(axis=1)  # データ利活用力
        df['info_sys_dev'] = df[df.columns[36:50]].mean(axis=1)  # 情報システム開発力
        df['info_ethics'] = df[df.columns[50:72]].mean(axis=1)  # 情報倫理力

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

def analyze_selected_category(selected_category, df, question_df):
    if selected_category != '"どちらでもない"が多く選択された設問':
        question_df = question_df[question_df["カテゴリ"] == selected_category]

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
                    name=label,
                    marker_color=colors[i],  # 色を指定
                    orientation='h',
                    hovertemplate=f"%{{x:.1f}}%<br>N= {skill_point_counts[i]}<extra></extra>"
                ))
            
            # グラフのレイアウト
            fig.update_layout(
                barmode='stack',
                title=f'Q{row['通し番号']}：{row["質問文"]}',
                xaxis_title='割合 (%)',
                yaxis_title='尺度',
                legend_title='選択肢',
                height=400
            )

            st.plotly_chart(fig)
            
    

def find_significant_skills(df):

    df = df[[col for col in df.columns if 'skill' in col]]
    
    # Total number of elements in the data
    total_elements = df.size
    
    # Count the number of '3's in each column
    column_3_counts = (df == 3).sum(axis=0)
    
    # Count the number of '3's in the entire data
    total_3_count = (df == 3).sum().sum()
    
    # Calculate proportions of '3's in each column and overall
    column_3_proportions = column_3_counts / df.shape[0]
    overall_3_proportion = total_3_count / total_elements
    
    # Perform a binomial test for each column using binomtest
    p_values = []
    significance_results = []
    for count, proportion in zip(column_3_counts, column_3_proportions):
        binom_test = stats.binomtest(count, df.shape[0], overall_3_proportion)
        p_value = binom_test.pvalue
        p_values.append(p_value)
        
        # Check if the proportion in the column is significantly higher than the overall proportion
        if proportion > overall_3_proportion and p_value < 0.05:
            significance_results.append(True)
        else:
            significance_results.append(False)
    
    # Create a DataFrame for the results
    result_df = pd.DataFrame({
        'Column': df.columns,
        'Proportion_of_3': column_3_proportions,
        'P_value': p_values,
        'Significant': significance_results
    })

    return result_df
    
# ファイルアップロード
st.file_uploader("集計結果（5件法）のcsvをアップロード",
                       type=["csv"],
                       key="upload_csvfile",
                       on_change=upload_csv
                       )

# 設問文のファイルアップロード
st.file_uploader("設問分のcsvをアップロード",
                       type=["csv"],
                       key="upload_csvfile2",
                       on_change=upload_csv2
                       )

# データフレームを空にするボタン
# csvがアップロードされたとき
if len(st.session_state['df']) != 0:
    if st.button("アップロードしたCSVファイルを消去"):
        st.session_state['df'] = pd.DataFrame()  # 空のデータフレームを設定
        st.switch_page("top.py")
        st.rerun()  # アプリを再実行して状態を更新
        st.success("CSVファイルが消去されました。")

try:
    categories = ['online_collab', 'data_utilization', 'info_sys_dev', 'info_ethics']
    categories_ja = ["オンライン・コラボレーション力", "データ利活用力", "情報システム開発力", "情報倫理力"]
    grades = sorted(list(st.session_state['df']['grade'].unique()))

    selected_columns = st.session_state['df'].iloc[:, :5]
    categories_columns = st.session_state['df'][categories]
    final_df = pd.concat([selected_columns, categories_columns], axis=1)
    st.dataframe(final_df, width=None, height=500)

    summary_df, question_df = display_summary(st.session_state['df'], categories, grades)

    # 表形式で表示
    cols = st.columns(2)
    cols[0].write("### 各学年の人数")
    cols[0].dataframe(summary_df)
    cols[1].write("### 各分野の質問数")
    cols[1].dataframe(question_df)

    dfdf = find_significant_skills(st.session_state['df'])
    st.write("3割合:", dfdf)

    # タブを作成
    # tab_list = categories_ja + ['"どちらでもない"が多く選択された設問']
    tab_list = categories_ja
    tabs = st.tabs(tab_list)

    with tabs[0]:  # "オンライン・コラボレーション力"タブ
        analyze_selected_category(tab_list[0], st.session_state['df'], st.session_state['question_df'])

    with tabs[1]:  # "オンライン・コラボレーション力"タブ
        analyze_selected_category(tab_list[1], st.session_state['df'], st.session_state['question_df'])

    with tabs[2]:  # "オンライン・コラボレーション力"タブ
        analyze_selected_category(tab_list[2], st.session_state['df'], st.session_state['question_df'])

    with tabs[3]:  # "オンライン・コラボレーション力"タブ
        analyze_selected_category(tab_list[3], st.session_state['df'], st.session_state['question_df'])

except Exception as e:
    st.write(e)
