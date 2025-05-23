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
        df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")  

        # 各カテゴリごとに平均を算出
        df['オンライン・コラボレーション力'] = df[df.columns[6:21]].mean(axis=1)  # オンライン・コラボレーション力
        df['データ利活用力'] = df[df.columns[21:36]].mean(axis=1)  # データ利活用力
        df['情報システム開発力'] = df[df.columns[36:50]].mean(axis=1)  # 情報システム開発力
        df['情報倫理力'] = df[df.columns[50:72]].mean(axis=1)  # 情報倫理力

        st.session_state['df'] = df
    else:
        # upload_csvfileがNoneの場合、空のデータフレームを作成
        st.session_state['df'] = pd.DataFrame()  # 空のデータフレーム
    
# 正規性の検定
def normality_test(df, categories):

    # 正規性の検証
    results = {}
    stat, p = stats.shapiro(df["required_time_seconds"])
    results["required-seconds"] = {
        'W統計量': stat,
        'p値': p,
        '正規性検定結果': '正規分布に従っている可能性がある' if p > 0.05 else '正規分布に従っていない'
    }

    # 結果の表示
    st.write("#### 正規性検定の結果")
    result_df = pd.DataFrame(results).T  # 結果をデータフレームに変換
    # st.dataframe(df)

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

st.header("所要時間の分析")
# ファイルアップロード
st.file_uploader("集計結果（5件法）のcsvをアップロード",
                       type=["csv"],
                       key="upload_csvfile",
                       on_change=upload_csv
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
    categories = ["オンライン・コラボレーション力", "データ利活用力", "情報システム開発力", "情報倫理力"]
    grades = sorted(list(st.session_state['df']['grade'].unique()))

    # user_idが22のものを除去する
    st.session_state['df'] = st.session_state['df'][st.session_state['df']["user_id"] != 22]

    selected_columns = st.session_state['df'].iloc[:, :6]
    categories_columns = st.session_state['df'][categories]
    final_df = pd.concat([selected_columns, categories_columns], axis=1)
    st.dataframe(final_df, width=None, height=500)

    summary_df, question_df = display_summary(st.session_state['df'], categories, grades)

    # 表形式で表示
    cols = st.columns([3, 7])
    cols[0].write("####  各学年の人数")
    cols[0].dataframe(summary_df)
    cols[1].write("#### 各分野の質問数")
    cols[1].dataframe(question_df)

    quantile1 = st.session_state['df']["required_time_seconds"].quantile(0.01)

    # 外れ値を除去する
    st.session_state['cleaned_df'] = st.session_state['df'][st.session_state['df']["required_time_seconds"] > quantile1]

    # タブを作成
    tabs = st.tabs(["正規性の検定", "所要時間分布", "学年間の所要時間分布"])

    with tabs[0]:  # "正規性の検定"タブ
        normality_df, fig_hist, fig_qq = normality_test(st.session_state['cleaned_df'], categories)
        st.dataframe(normality_df)
        with st.expander("分野ごとのスコア分布"):
            st.pyplot(fig_hist)
        with st.expander("Q-Qプロット"):
            st.pyplot(fig_qq)

    with tabs[1]:  # "所要時間分布"タブ
        categories_df, fig = categories_test(st.session_state['cleaned_df'], categories)
        st.dataframe(categories_df)
        with st.expander("所要時間分布"):
            st.plotly_chart(fig)

    with tabs[2]:  # "学年間の所要時間分布"タブ
        grade_df, fig, result_pairs = grade_test(st.session_state['cleaned_df'], categories, grades)
        st.dataframe(grade_df)
        with st.expander("学年間の所要時間分布"):
            st.plotly_chart(fig)
            st.write("有意差が見られる学年間の組み合わせ：")
            for result_set in result_pairs:
                for category, grade1, grade2 in result_set:
                    st.write(f"【{category}】：【{grade1}】-【{grade2}】")

except Exception as e:
    pass
