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
        df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")  

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
        file_data = st.session_state['upload_csvfile'].read()
        df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")  

        st.session_state['question_df'] = df
    else:
        # upload_csvfileがNoneの場合、空のデータフレームを作成
        st.session_state['question_df'] = pd.DataFrame()  # 空のデータフレーム


def find_significant_skills(df):
    # skill1 から skill66 の列を選択
    skill_columns = [f'skill{i}' for i in range(1, 67)]

    # 各列の平均値を計算
    means = df[skill_columns].mean()
    

    # 全体平均を計算
    overall_mean = df[skill_columns].values.flatten().mean()

    # 各スキル列の平均値と全体平均を比較し、p値を計算
    p_values = {}
    for skill in skill_columns:
        meann = df[skill_columns].mean()
        t_stat, p_value = stats.ttest_1samp(df[skill], meann)
        p_values[skill] = p_value

    st.write(p_values)
    
    # 有意水準を設定（例: 0.05）
    significance_level = 0.05

    # 有意に大きいものと有意に小さいものを分類
    significantly_large = {skill: means[skill] for skill, p in p_values.items() if p < significance_level and means[skill] > overall_mean}
    significantly_small = {skill: means[skill] for skill, p in p_values.items() if p < significance_level and means[skill] < overall_mean}

    # 結果を返す
    return significantly_large, significantly_small

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

    large_skills, small_skills = find_significant_skills(st.session_state['df'])
    st.write("有意に大きい列とその平均値:", large_skills)
    st.write("有意に小さい列とその平均値:", small_skills)

    # タブを作成
    tabs = st.tabs(["正規性の検定", "各分野のスコア分布", "各分野の学年別のスコア分布"])

    with tabs[0]:  # "正規性の検定"タブ
        normality_df, fig_hist, fig_qq = normality_test(st.session_state['df'], categories)
        st.dataframe(normality_df)
        with st.expander("各分野のスコア分布"):
            st.pyplot(fig_hist)
        with st.expander("Q-Qプロット"):
            st.pyplot(fig_qq)

    with tabs[1]:  # "各分野のスコア分布"タブ
        categories_df, fig, filtered_pairs = categories_test(st.session_state['df'], categories)
        st.dataframe(categories_df)
        with st.expander("各分野のスコア分布"):
            st.plotly_chart(fig)
            st.write("有意差が見られる分野間の組み合わせ：")
            for category1, category2 in filtered_pairs:
                st.write(f"【{category1}】-【{category2}】")

    with tabs[2]:  # "各分野の学年別のスコア分布"タブ
        grade_df, fig, result_pairs = grade_test(st.session_state['df'], categories, grades)
        st.dataframe(grade_df)
        with st.expander("各分野の学年別のスコア分布"):
            st.plotly_chart(fig)
            st.write("有意差が見られる各分野の学年間の組み合わせ：")
            for result_set in result_pairs:
                for category, grade1, grade2 in result_set:
                    st.write(f"【{category}】：【{grade1}】-【{grade2}】")

except Exception as e:
    st.write(e)
