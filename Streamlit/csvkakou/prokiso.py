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

    # 要求数でソート
    df_sorted = df.sort_values(by='要求数', ascending=False).reset_index(drop=True)

    # グループ数
    num_groups = 11
    groups = [[] for _ in range(num_groups)]
    group_sums = [0] * num_groups  # 各グループの合計要求数を保持

    # 貪欲法でグループ分け
    for index, row in df_sorted.iterrows():
        # 現在のグループの合計が最も少ないグループに追加
        min_group_index = group_sums.index(min(group_sums))
        groups[min_group_index].append(row)
        group_sums[min_group_index] += row['要求数']

    # グループ番号を追加
    for group_number, group in enumerate(groups, start=1):
        for member in group:
            df.loc[member.name, 'グループ番号'] = group_number

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
