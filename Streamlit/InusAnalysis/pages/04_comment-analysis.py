import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import MeCab
import nlplot  # nlplotをインポート
import io

def upload_csv():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile'] is not None:
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile'].read()
        df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")  

        # 各カテゴリごとに平均を算出
        df['オンライン・コラボレーション力'] = df[df.columns[6:21]].mean(axis=1)
        df['データ利活用力'] = df[df.columns[21:36]].mean(axis=1)
        df['情報システム開発力'] = df[df.columns[36:50]].mean(axis=1)
        df['情報倫理力'] = df[df.columns[50:72]].mean(axis=1)

        st.session_state['df'] = df
    else:
        st.session_state['df'] = pd.DataFrame()  # 空のデータフレーム

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

st.header("アンケートコメントの分析")
# ファイルアップロード
st.file_uploader("CSVファイルをアップロード",
                  type=["csv"],
                  key="upload_csvfile",
                  on_change=upload_csv
                  )

# データフレームを空にするボタン
if len(st.session_state.get('df', [])) != 0:
    if st.button("アップロードしたCSVファイルを消去"):
        st.session_state['df'] = pd.DataFrame()  # 空のデータフレームを設定
        st.success("CSVファイルが消去されました。")
        st.rerun()  # アプリを再実行して状態を更新

try:
    df = st.session_state['df']
    # 欠損値がある行を取り除く
    df = df.dropna(subset=['comment'])
    
    # 形態素結果をリスト化し、データフレームに結果を列追加する
    df['words'] = df['comment'].apply(mecab_text)

    # アンケート内容と名詞のリスト（words列）のみを取り出して、新たにデータフレーム作成
    df = df[['comment','words']]

    st.dataframe(df['comment'], width=1000)

    # タブを作成
    tab_list = ["頻出単語ランキング", "ワードクラウド", "ツリーマップ", "共起ネットワーク", "サンバーストチャート"]
    tabs = st.tabs(tab_list)
    
    # 各表示関数を呼び出す
    with tabs[0]:
        display_unigram(df)
    with tabs[1]:
        display_wordcloud(df)
    with tabs[2]:
        display_treemap(df)
    with tabs[3]:
        display_co_network(df)
    with tabs[4]:
        display_sunburst(df)

except Exception as e:
    pass
