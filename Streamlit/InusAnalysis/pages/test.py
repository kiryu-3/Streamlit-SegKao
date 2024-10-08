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

from factor_analyzer import FactorAnalyzer


# Streamlit ページの設定
st.set_page_config(
    page_title="情報活用力チェック-結果分析",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    st.write("### 正規性検定の結果")
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

# ファイルアップロード
st.file_uploader("CSVファイルをアップロード",
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

    tete_df = st.session_state['df'].iloc[:, 6:72]
    st.write(tete_df)

    # データの標準化
    inga_df = tete_df
    df_std = inga_df.apply(lambda x: (x-x.mean())/x.std(), axis=0)

    #相関行列を求める
    df_std_corr = df_std.corr()
    
    #固有値を求める
    ev = np.linalg.eigvals(df_std_corr)
    ev_sorted = sorted(ev,reverse=True)

    plt.plot(ev_sorted, 's-') 
    
    # スクリープロットの描画
    # 固有値をプロット
    plt.figure(figsize=(10, 6))  # グラフのサイズを指定
    plt.plot(ev_sorted, 's-') 
    
    # 軸名を指定
    plt.xlabel("因子の数")
    plt.ylabel("固有値")

    # Streamlitでグラフを表示
    st.write(df_std)
    st.pyplot(plt)

    # 因子分析の実行
    fa = FactorAnalyzer(n_factors=5, rotation="promax")
    fa.fit(df_std)

    # 因子負荷量，共通性の表示
    loadings_df = pd.DataFrame(fa.loadings_, columns=["第１因子", "第２因子","第3因子", "第4因子","第5因子"]) #fa.loadingsで因子負荷量を算出
    loadings_df.index = df_std.columns
    loadings_df["共通性"] = fa.get_communalities() #共通性の算出
    st.write(loadings_df)
    
    # タブを作成
    tabs = st.tabs(["正規性の検定", "各分野のスコア分布", "各分野の学年別のスコア分布"])

    # with tabs[0]:  # "正規性の検定"タブ
    #     normality_df, fig_hist, fig_qq = normality_test(st.session_state['df'], categories)
    #     st.dataframe(normality_df)
    #     with st.expander("各分野のスコア分布"):
    #         st.pyplot(fig_hist)
    #     with st.expander("Q-Qプロット"):
    #         st.pyplot(fig_qq)

    # with tabs[1]:  # "各分野のスコア分布"タブ
    #     categories_df, fig, filtered_pairs = categories_test(st.session_state['df'], categories)
    #     st.dataframe(categories_df)
    #     with st.expander("各分野のスコア分布"):
    #         st.plotly_chart(fig)
    #         st.write("有意差が見られる分野間の組み合わせ：")
    #         for category1, category2 in filtered_pairs:
    #             st.write(f"【{category1}】-【{category2}】")

    # with tabs[2]:  # "各分野の学年別のスコア分布"タブ
    #     grade_df, fig, result_pairs = grade_test(st.session_state['df'], categories, grades)
    #     st.dataframe(grade_df)
    #     with st.expander("各分野の学年別のスコア分布"):
    #         st.plotly_chart(fig)
    #         st.write("有意差が見られる各分野の学年間の組み合わせ：")
    #         for result_set in result_pairs:
    #             for category, grade1, grade2 in result_set:
    #                 st.write(f"【{category}】：【{grade1}】-【{grade2}】")

except Exception as e:
    st.write(e)
