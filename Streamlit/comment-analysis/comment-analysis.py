import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import MeCab
import nlplot  # nlplotをインポート
import io
import chardet

# Streamlit ページの設定
st.set_page_config(
    page_title="EDAML-hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

def upload_csv():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile'] is not None:
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile'].read()
        # エンコーディングを検出
        raw_data = io.BytesIO(file_data).read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        st.session_state['encoding'] = result['encoding']
        
        df = pd.read_csv(io.BytesIO(file_data), encoding=encoding, on_bad_lines="skip", engine="python")
      
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

def display_unigram(df, column):
    npt = nlplot.NLPlot(df, target_col=column)
    stopwords = npt.get_stopword(top_n=0, min_freq=0)
    
    fig_unigram = npt.bar_ngram(
        title='uni-gram',
        xaxis_label='word_count',
        yaxis_label='word',
        ngram=1,
        top_n=50,
        stopwords=stopwords,
    )
    
    with st.expander(column):
        st.plotly_chart(fig_unigram)
    

def display_wordcloud(df, column):
    npt = nlplot.NLPlot(df, target_col=column)
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
    
    plt.figure(figsize=(10, 15))
    plt.imshow(fig_wc, interpolation="bilinear")
    plt.axis("off")

    with st.expander(column):
        st.pyplot(plt)
    

def display_treemap(df, column):
    npt = nlplot.NLPlot(df, target_col=column)
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
    
    with st.expander(column):
        st.plotly_chart(fig_treemap)
    

def display_co_network(df, column):
    npt = nlplot.NLPlot(df, target_col=column)
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
    
    with st.expander(column):
        st.plotly_chart(fig_co_network)
    

def display_sunburst(df, column):

    npt = nlplot.NLPlot(df, target_col=column)
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

    with st.expander(column):
        st.plotly_chart(fig_sunburst)
    

st.header("アンケートコメントの分析")
# ファイルアップロード
st.file_uploader("csvをアップロード（複数不可）",
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
    st.write(df)

    # 文字列データ型の列のみを抽出
    string_columns = [col for col in df.columns if df[col].dtype == 'object']

    selected_columns = st.multiselect(label='表示/ダウンロードしたい列を選択してください',
                                          options=string_columns,
                                          placeholder="列を選択してください")
    

    if len(selected_columns) != 0:
          
        # タブを作成
        tab_list = ["頻出単語ランキング", "ワードクラウド", "ツリーマップ", "共起ネットワーク", "サンバーストチャート"]
        tabs = st.tabs(tab_list)
    
        tabs[0].subheader("頻出単語ランキング")
        tabs[0].code("""
        def display_unigram(df, column):
            npt = nlplot.NLPlot(df, target_col=column)
            stopwords = npt.get_stopword(top_n=0, min_freq=0)
            
            fig_unigram = npt.bar_ngram(
                title='uni-gram',
                xaxis_label='word_count',
                yaxis_label='word',
                ngram=1,
                top_n=50,
                stopwords=stopwords,
            )
            
            with st.expander(column):
                st.plotly_chart(fig_unigram)
                """)
        tabs[1].subheader("ワードクラウド")
        tabs[1].code("""
        def display_wordcloud(df, column):
            npt = nlplot.NLPlot(df, target_col=column)
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
            
            plt.figure(figsize=(10, 15))
            plt.imshow(fig_wc, interpolation="bilinear")
            plt.axis("off")
        
            with st.expander(column):
                st.pyplot(plt)
        """)
        tabs[2].subheader("ツリーマップ")
        tabs[2].code("""
        def display_treemap(df, column):
            npt = nlplot.NLPlot(df, target_col=column)
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
            
            with st.expander(column):
                st.plotly_chart(fig_treemap)
        """)
        tabs[3].subheader("共起ネットワーク")
        tabs[3].code("""
        def display_co_network(df, column):
            npt = nlplot.NLPlot(df, target_col=column)
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
            
            with st.expander(column):
                st.plotly_chart(fig_co_network)
        """)
        tabs[4].subheader("サンバーストチャート")
        tabs[4].code("""
        def display_sunburst(df, column):

            npt = nlplot.NLPlot(df, target_col=column)
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
        
            with st.expander(column):
                st.plotly_chart(fig_sunburst)
        """)
        
        # 各カラムに対してタブを表示
        for column in selected_columns:
            with tabs[0]:
                # 欠損値がある行を取り除く
                temp_df = df.dropna(subset=[column])
                
                # 形態素結果をリスト化し、データフレームに結果を列追加する
                temp_df[column] = temp_df[column].apply(mecab_text)
                
                display_unigram(temp_df, column)
            with tabs[1]:
                # 欠損値がある行を取り除く
                temp_df = df.dropna(subset=[column])
                
                # 形態素結果をリスト化し、データフレームに結果を列追加する
                temp_df[column] = temp_df[column].apply(mecab_text)
                
                display_wordcloud(temp_df, column)
            with tabs[2]:
                # 欠損値がある行を取り除く
                temp_df = df.dropna(subset=[column])
                
                # 形態素結果をリスト化し、データフレームに結果を列追加する
                temp_df[column] = temp_df[column].apply(mecab_text)
                
                display_treemap(temp_df, column)
            with tabs[3]:
                # 欠損値がある行を取り除く
                temp_df = df.dropna(subset=[column])
                
                # 形態素結果をリスト化し、データフレームに結果を列追加する
                temp_df[column] = temp_df[column].apply(mecab_text)
                
                display_co_network(temp_df, column)
            with tabs[4]:
                # 欠損値がある行を取り除く
                temp_df = df.dropna(subset=[column])
                
                # 形態素結果をリスト化し、データフレームに結果を列追加する
                temp_df[column] = temp_df[column].apply(mecab_text)
                
                display_sunburst(temp_df, column)

except Exception as e:
    st.write(e)
    pass
