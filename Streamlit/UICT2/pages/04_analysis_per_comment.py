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
import MeCab
import nlplot  # nlplotをインポート
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from scipy.stats import kruskal, shapiro, mannwhitneyu
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

def analyze_selected_category(selected_category, grades, df, qsentence):
    if selected_category == "回答形式":
        selected_options = [
            "5件法", 
            "どちらともいえない", 
            "ルーブリック" 
        ]
    else:
        selected_options = [
            "全くそう思わない", 
            "あまりそう思わない", 
            "どちらともいえない", 
            "ややそう思う", 
            "とてもそう思う"
        ]

    # "B"から始まるものだけを残す
    grades = [grade for grade in grades if grade.startswith("B")]
    df = df[df['grade'].isin(grades)]

    st.write(qsentence)

    with st.expander("選択肢"):
        st.radio(
            label="rubric",
            options=selected_options,
            index=None,
            key=f"radio_{qsentence}",
            label_visibility="collapsed",
            disabled=True,
            horizontal=False,
        )
  
    skill_array = df.iloc[:, 1].values

    # 5件法の割合を計算
    skill_point_total = len(skill_array)
    if selected_category == "回答形式":
        skill_point_counts = np.array([
            np.sum(skill_array == -1),
            np.sum(skill_array == 0),
            np.sum(skill_array == 1),
        ])
    else:
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
        grade_average_score = np.mean(grade_df.iloc[:, 1].values)
        grade_std_score = np.std(grade_df.iloc[:, 1].values)
        grade_results.append({"学年": grade, "平均スコア": grade_average_score, "標準偏差": grade_std_score})

    # "全学年"の結果を追加
    grade_results.append({"学年": "全学年", "平均スコア": overall_average_score, "標準偏差": overall_std_score})

    # データフレームに変換
    results_df = pd.DataFrame(grade_results)

    # 指定された色
    if selected_category == "回答形式":
        colors = ['#2B4C7E', '#95A5A6', '#943126']
    else:
        colors = ['#2B4C7E', '#AED6F1', '#95A5A6', '#E6B0AA', '#943126']
  
    # 積み上げ棒グラフの作成
    fig = go.Figure()

    # 積み上げ棒グラフ
    for i in range(len(colors)):
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

    st.plotly_chart(fig, key=f"plot_{qsentence}")

    with st.expander("学年ごとの分布"):
        # 積み上げ棒グラフの作成
        fig = go.Figure()
        
        for grade in grades:
            grade_df = df[df["grade"]==grade]
            skill_array = grade_df.iloc[:, 1].values

            # 5件法の割合を計算
            skill_point_total = len(skill_array)
            if selected_category == "回答形式":
                skill_point_counts = np.array([
                    np.sum(skill_array == -1),
                    np.sum(skill_array == 0),
                    np.sum(skill_array == 1),
                ])
            else:
                skill_point_counts = np.array([
                    np.sum(skill_array == 1),
                    np.sum(skill_array == 2),
                    np.sum(skill_array == 3),
                    np.sum(skill_array == 4),
                    np.sum(skill_array == 5)
                ])
            skill_point_percentages = (skill_point_counts / skill_point_total) * 100

            # 指定された色
            if selected_category == "回答形式":
                colors = ['#2B4C7E', '#95A5A6', '#943126']
            else:
                colors = ['#2B4C7E', '#AED6F1', '#95A5A6', '#E6B0AA', '#943126']
            

            # 積み上げ棒グラフ
            for i in range(len(colors)):
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

        st.plotly_chart(fig, key=f"plots_{qsentence}")

        # 統計量を表示
        st.write("各学年の平均スコア")
        st.write(results_df)

        # 各グループのスコアをリストに分ける
        groups = [df[df['grade'] == grade].iloc[:, 1] for grade in df['grade'].unique()]
        
        # Kruskal-Wallis検定
        stat, p = kruskal(*groups)
        
        # 有意差がある場合、事後検定 (Dunn検定)
        if p < 0.05:
            st.write("学年間のスコアの有意（以下のp値が0.05以下の学年間は有意差あり）")
            
            # Dunn検定の実施
            posthoc_results = sp.posthoc_dunn(df, val_col=f"skill{qsentence}", group_col='grade', p_adjust='bonferroni')
            st.write(posthoc_results)

        else:
            st.write("学年間のスコアの有意差はありません")
        

def mecab_text(text):
    tagger = MeCab.Tagger("")
    tagger.parse('')
    node = tagger.parseToNode(text)

    word_list = []
    while node:
        word_type = node.feature.split(',')[0]
        if word_type == '名詞':
            if (node.surface != "こと") and (node.surface != "ところ"):
                word_list.append(node.surface)
        node = node.next
        
    return word_list

def display_unigram(df):
    npt = nlplot.NLPlot(df, target_col='words')
    stopwords = npt.get_stopword(top_n=0, min_freq=0)
    
    fig_unigram = npt.bar_ngram(
        title='uni-gram',
        xaxis_label='word_count',
        yaxis_label='word',
        ngram=1,
        top_n=50,
        stopwords=stopwords,
    )
    
    st.subheader("頻出単語ランキング")
    st.plotly_chart(fig_unigram)

def display_wordcloud(df):
    npt = nlplot.NLPlot(df, target_col='words')
    stopwords = npt.get_stopword(top_n=0, min_freq=0)
    
    fig_wc = npt.wordcloud(
        width=1000,
        height=600,
        max_words=100,
        max_font_size=100,
        colormap='tab20_r',
        stopwords=stopwords,
        mask_file=None,
        save=False
    )
    
    st.subheader("ワードクラウド")
    plt.figure(figsize=(10, 15))
    plt.imshow(fig_wc, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)

def display_treemap(df):
    npt = nlplot.NLPlot(df, target_col='words')
    stopwords = npt.get_stopword(top_n=0, min_freq=0)
    
    fig_treemap = npt.treemap(
        title='Tree map',
        ngram=1,
        top_n=50,
        width=1300,
        height=600,
        stopwords=stopwords,
        verbose=False,
        save=False
    )
    st.subheader("ツリーマップ")
    st.plotly_chart(fig_treemap)

def display_co_network(df):
    npt = nlplot.NLPlot(df, target_col='words')
    stopwords = npt.get_stopword(top_n=0, min_freq=0)
    
    npt.build_graph(stopwords=stopwords, min_edge_frequency=3)
    
    fig_co_network = npt.co_network(
        title='Co-occurrence network',
        sizing=100,
        node_size='adjacency_frequency',
        color_palette='hls',
        width=1100,
        height=700,
        save=False
    )
    st.subheader("共起ネットワーク")
    st.plotly_chart(fig_co_network)

def display_sunburst(df):

    npt = nlplot.NLPlot(df, target_col='words')
    stopwords = npt.get_stopword(top_n=0, min_freq=0)

    # ビルド（データ件数によっては処理に時間を要します）
    npt.build_graph(stopwords=stopwords, min_edge_frequency=3)

    
    fig_sunburst = npt.sunburst(
        title='Sunburst chart',
        colorscale=True,
        color_continuous_scale='Oryel',
        width=1000,
        height=800,
        save=False
    )
    st.subheader("サンバーストチャート")
    st.plotly_chart(fig_sunburst)

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

st.session_state['questionnaires_df'] = get_spreadsheet_data(st.secrets["SHEET_ID"], "questionnaires")

# st.write(st.session_state['questions_df'])
# st.write(st.session_state['answers_df'])
select_list = ["回答のしやすさ", "評価の妥当性", "回答の負担", "ルーブリックの分かりやすさ", "回答形式", "ルーブリックの全体評価", "全体コメント"]
# tab_list = categories + ["各分野のスコア分布", "各分野の学年別のスコア分布"]

# タブを作成
tab_list = ["頻出単語ランキング", "ワードクラウド", "ツリーマップ", "共起ネットワーク", "サンバーストチャート"]
display_functions = [display_unigram, display_wordcloud, display_treemap, display_co_network, display_sunburst]

option = st.selectbox(
    "表示したい内容を選択してください",
    select_list,
    index=4
)

try:
    if option == "回答形式": 
        # 取り出すカラムのインデックスを計算
        start_col_index = 74 + select_list.index(option) * 3
        
        # カラムを取り出す
        sorted_df = pd.concat([
            st.session_state['answers_df']['grade'],
            st.session_state['answers_df'].iloc[:, start_col_index:start_col_index + 2]
        ], axis=1)
    
        # 3列目に .apply(mecab_text) を適用して新しい列 words を作成
        sorted_df['words'] = sorted_df.iloc[:, 2].apply(mecab_text)
    
        # options の定義
        options = [
            "5件法", 
            "どちらともいえない", 
            "ルーブリック"
        ]
        
        # 置き換え用の辞書を作成
        replace_dict = {option: i - 1 for i, option in enumerate(options)}
        
        # 一列目に対して置き換えを適用
        sorted_df.iloc[:, 1] = sorted_df.iloc[:, 1].replace(replace_dict)
    
        # qcategory が option に等しい行を取り出す
        questionnaires_df = st.session_state['questionnaires_df'][st.session_state['questionnaires_df']['qcategory'] == option].reset_index(drop=True)
        analyze_selected_category(option, grades, sorted_df.iloc[:, [0, 1]], questionnaires_df.at[0, "qsentence"])
    
        st.write(questionnaires_df.at[1, "qsentence"])
        tabs = st.tabs(tab_list)
        
        # 各表示関数を呼び出す
        for tab, display_func in zip(tabs, display_functions):
            with tab:
                display_func(sorted_df)
    
    elif option in ["ルーブリックの全体評価", "全体コメント"]:
        if option == "ルーブリックの全体評価":
            # カラムを取り出す
            sorted_df = pd.concat([
                st.session_state['answers_df']['grade'],
                st.session_state['answers_df']['rubric']
            ], axis=1)
        elif option == "全体コメント":
            # カラムを取り出す
            sorted_df = pd.concat([
                st.session_state['answers_df']['grade'],
                st.session_state['answers_df']['all']
            ], axis=1)

        # 1行目に欠損がある行を除外
        sorted_df = sorted_df.dropna(subset=sorted_df.iloc[0].index)

        # 3列目に .apply(mecab_text) を適用して新しい列 words を作成
        sorted_df['words'] = sorted_df.iloc[:, 1].apply(mecab_text)
    
        # qcategory が option に等しい行を取り出す
        questionnaires_df = st.session_state['questionnaires_df'][st.session_state['questionnaires_df']['qcategory'] == option].reset_index(drop=True)
        
        tabs = st.tabs(tab_list)
        
        # 各表示関数を呼び出す
        for tab, display_func in zip(tabs, display_functions):
            with tab:
                display_func(sorted_df)
          
    else:
        # 取り出すカラムのインデックスを計算
        start_col_index = 74 + select_list.index(option) * 3
        
        # カラムを取り出す
        sorted_df = pd.concat([
            st.session_state['answers_df']['grade'],
            st.session_state['answers_df'].iloc[:, start_col_index:start_col_index + 3]
        ], axis=1)

        
        # 3列目に .apply(mecab_text) を適用して新しい列 words を作成
        sorted_df['words'] = sorted_df.iloc[:, 3].apply(mecab_text)
      
        # options の定義
        options = [
            "全くそう思わない", 
            "あまりそう思わない", 
            "どちらともいえない", 
            "ややそう思う", 
            "とてもそう思う"
        ]
        
        # 置き換え用の辞書を作成
        replace_dict = {option: i + 1 for i, option in enumerate(options)}
        
        # 一列目と二列目に対して置き換えを適用
        sorted_df.iloc[:, 1:3] = sorted_df.iloc[:, 1:3].replace(replace_dict)
    
        # qcategory が option に等しい行を取り出す
        questionnaires_df = st.session_state['questionnaires_df'][st.session_state['questionnaires_df']['qcategory'] == option].reset_index(drop=True)
        analyze_selected_category(option, grades, sorted_df.iloc[:, [0, 1]], questionnaires_df.at[0, "qsentence"])
        analyze_selected_category(option, grades, sorted_df.iloc[:, [0, 2]], questionnaires_df.at[1, "qsentence"])

        with st.expander("回答方式間の比較"):
            # 1列目と2列目のデータを取得
            data1 = sorted_df.iloc[:, 1]  # 1列目
            data2 = sorted_df.iloc[:, 2]  # 2列目
            
            # マンホイットニーのU検定
            stat, p = mannwhitneyu(data1, data2)
        
            if p < 0.05:
                st.write("回答方式間で有意差があります")
            else:
                st.write("回答方式間で有意差がありません")
    
        st.write(questionnaires_df.at[2, "qsentence"])
        tabs = st.tabs(tab_list)
    
        
        # 各表示関数を呼び出す
        for tab, display_func in zip(tabs, display_functions):
            with tab:
                display_func(sorted_df)
except Exception as e:
    st.error(e)
