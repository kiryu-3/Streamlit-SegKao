import pandas as pd
import streamlit as st
import io

def upload_csv():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile'] is not None:
        # アップロードされたファイルデータを読み込む
        file_data = st.session_state['upload_csvfile'].read()
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

    # "回答内容"列の「~したい」で要求数を数え、新しい"要求数"カラムを作成
    df['要求数'] = df['回答内容'].str.count('したい')

    # 要求数を元にグループ分け
    # 要求数でソート
    df_sorted = df.sort_values(by='要求数')

    # グループ分け
    group_size = 4  # 4人組のグループ
    groups = []

    # 要求数のバランスを取るために、交互にグループに追加
    for i in range(0, len(df_sorted), group_size):
        group = []
        # 奇数番目の要素を追加
        for j in range(group_size):
            if i + j < len(df_sorted):
                group.append(df_sorted.iloc[i + j])
        
        # 偶数番目の要素を追加
        for j in range(group_size):
            if i + group_size + j < len(df_sorted):
                group.append(df_sorted.iloc[i + group_size + j])

        # グループを追加
        groups.append(group)

    # グループ番号を付与
    group_number = 1
    for group in groups:
        for member in group:
            df.loc[member.name, 'グループ番号'] = group_number
        group_number += 1

    return df

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
if not st.session_state['before_df'].empty:
    df = process_csv(st.session_state['before_df'])
    st.dataframe(df)

    upload_name = st.session_state['upload_csvfile'].name
    download_name = upload_name.split(".")[0]
    
    # CSVをバイナリデータに変換
    csv_file = df.to_csv(index=False, encoding="shift-jis").encode('shift-jis')
    
    st.download_button(
        label="Download CSV",
        data=csv_file,
        file_name=f'{download_name}_edited.csv'
    )
