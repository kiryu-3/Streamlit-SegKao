import itertools
import numpy as np
import pandas as pd
import streamlit as st
import io

# Streamlit ページの設定
st.set_page_config(
    page_title="prokiso-edit",
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
        st.session_state['upload_name'] = st.session_state['upload_csvfile'].name
        # バイナリデータからPandas DataFrameを作成
        try:
            df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
            st.session_state["ja_honyaku"] = False
        except UnicodeDecodeError:
            # Shift-JISで読み取れない場合はutf-8エンコーディングで再試行
            df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8", engine="python")
            st.session_state["ja_honyaku"] = True

        st.session_state['before_df'] = df
    else:
        # upload_csvfileがNoneの場合、空のデータフレームを作成
        st.session_state['before_df'] = pd.DataFrame()  # 空のデータフレーム

def process_csv(df):
    # "クラス"カラムの値が"2C"ではないものの"出席番号"を90にする
    df.loc[df['クラス'] != '2C', '出席番号'] = 90

    # "回答内容"列の「たい」で要求数を数え、新しい"要求数"カラムを作成
    df['要求数'] = df['回答内容'].str.count('たい').astype(int)  # 整数型に変換

    # 要求数でソート
    df_sorted = df.sort_values(by='要求数', ascending=False).reset_index(drop=True)

    return df_sorted

st.title("プロジェクト基礎演習-グルーピングアプリ")

# 初期化
if 'before_df' not in st.session_state:
    st.session_state['before_df'] = pd.DataFrame()  # 空のデータフレーム

# ファイルアップロード
st.file_uploader("CSVファイルをアップロード",
                  type=["csv"],
                  key="upload_csvfile",
                  on_change=upload_csv
                  )

# csvがアップロードされたとき
if len(st.session_state['before_df']) != 0:
    if st.button("アップロードしたCSVファイルを消去"):
        st.session_state['df'] = pd.DataFrame()  # 空のデータフレームを設定
        st.switch_page("prokiso.py")
        st.rerun()  # アプリを再実行して状態を更新
        st.success("CSVファイルが消去されました。")

try:
    # csvがアップロードされたとき
    if not st.session_state['before_df'].empty:
        df = process_csv(st.session_state['before_df'])
        
        st.subheader("要求数カウント後のデータ")
        st.dataframe(df)
    
        download_name = st.session_state['upload_name'].split(".")[0]
        
        # CSVをバイナリデータに変換
        csv_file = df.to_csv(index=False, encoding="shift-jis").encode('shift-jis')
    
        st.subheader("グルーピング後のデータダウンロード")
        st.download_button(
            label="Download CSV",
            data=csv_file,
            file_name=f'{download_name}_edited.csv'
        )
except Exception as e:
    st.write(e)
