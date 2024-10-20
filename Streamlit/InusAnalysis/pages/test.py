import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import MeCab
import nlplot  # nlplotをインポート
from plotly.offline import iplot
import io
from io import BytesIO
import itertools

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

# 文章を分解し、名詞のみを取り込む
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
    df = st.session_state['df']
    # 欠損値がある行を取り除く
    df = df.dropna(subset=['comment'])
    st.write(df['comment'])
    
    # 形態素結果をリスト化し、データフレームに結果を列追加する
    df['words'] = df['comment'].apply(mecab_text)
    
    # Streamlitのタイトル
    st.title("コメント分析アプリ")
    
    # NLPlotを使用して分析する
    npt = nlplot.NLPlot(df, target_col='words')
    
    # ストップワードを設定
    stopwords = npt.get_stopword(top_n=0, min_freq=0)
    
    # 単語頻出ランキングを作成
    fig_unigram = npt.bar_ngram(
        title='uni-gram',
        xaxis_label='word_count',
        yaxis_label='word',
        ngram=1,
        top_n=50,
        stopwords=stopwords,
    )
    
    # 単語頻出ランキングを表示
    st.subheader("頻出単語ランキング")
    st.plotly_chart(fig_unigram)
    
    # 共起ネットワーク図作成
    npt.build_graph(stopwords=stopwords, min_edge_frequency=2)
    
    # 共起ネットワークを表示
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
    
    # ワードクラウドを作成
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
    
    # ワードクラウドを表示
    st.subheader("ワードクラウド")
    plt.figure(figsize=(10, 15))
    plt.imshow(fig_wc, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)
except Exception as e:
    st.write(e)
