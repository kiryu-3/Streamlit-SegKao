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

# def process_csv(df):
#     # # "クラス"カラムの値が"2C"ではないものの"出席番号"を90にする
#     # df.loc[df['クラス'] != '2C', '出席番号'] = 90

#     # # "回答内容"列の「たい」で要求数を数え、新しい"要求数"カラムを作成
#     # df['要求数'] = df['回答内容'].str.count('たい').astype(int)  # 整数型に変換

#     # "要求数"カラムが無い場合の条件
#     if "要求数" not in df.columns:
#         return None, None  # 列がない場合はNoneを返す
    
#     # 要求数でソート
#     df_sorted = df.sort_values(by='要求数', ascending=False).reset_index(drop=True)

#     # バランスを取ったグループ作成
#     group_size = 4  # 基本4人組
#     total_members = len(df_sorted)
#     num_full_groups = total_members // group_size  # 完全な4人組の数
#     st.write(total_members)

#     # グループを準備
#     groups = [[] for _ in range(num_full_groups)]
#     group_sums = [0] * len(groups)  # 各グループの合計要求数を保持

#     # 貪欲法でグループ分け
#     for index, row in df_sorted.iterrows():
#         # 4人組を作成
#         min_index = group_sums.index(min(group_sums))
#         if len(groups[min_index]) < group_size:
#             groups[min_index].append(row)
#             group_sums[min_index] += row['要求数']
#         else:
#             for i in range(num_full_groups):
#                 if len(groups[i]) < group_size:
#                     groups[i].append(row)
#                     group_sums[i] += row['要求数']
#                     break
#             else:
#                 # 全てのグループが4人の場合、最後のグループに追加
#                 groups[-1].append(row)
#                 group_sums[-1] += row['要求数']
            
#     # グループ番号を追加
#     for group_number, group in enumerate(groups, start=1):
#         for member in group:
#             df.loc[member.name, 'グループ番号'] = group_number

#     # dfをグループ番号でソート
#     df.sort_values(by='グループ番号', ascending=True, inplace=True)
    
#     # グループ番号ごとの要求数の合計を計算
#     group_totals = df.groupby('グループ番号')['要求数'].sum().reset_index()
#     group_totals.rename(columns={'要求数': '要求数の合計'}, inplace=True)  # カラム名を変更
    
#     return df, group_totals
def process_csv(df):
    if "要求数" not in df.columns:
        return None, None  # 列がない場合はNoneを返す
    
    # 要求数でソート
    df_sorted = df.sort_values(by='要求数', ascending=False).reset_index(drop=True)

    # バランスを取ったグループ作成
    group_size = 4  # 基本4人組
    total_members = len(df_sorted)
    num_full_groups = total_members // group_size  # 完全な4人組の数

    # グループを準備
    groups = [[] for _ in range(num_full_groups)]
    group_sums = [0] * len(groups)  # 各グループの合計要求数を保持
    group_ids = [set() for _ in range(num_full_groups)]  # 各グループの全グループIDを保持
    st.write(group_ids)

    # 貪欲法でグループ分け
    for index, row in df_sorted.iterrows():
        min_index = group_sums.index(min(group_sums))
        
        # 同じ「前グループ」IDの人がすでにいるか確認
        if row['前グループ'] not in group_ids[min_index]:
            groups[min_index].append(row)
            group_sums[min_index] += row['要求数']
            group_ids[min_index].add(row['前グループ'])
        else:
            # 他のグループを探す
            for i in range(num_full_groups):
                if row['前グループ'] not in group_ids[i] and len(groups[i]) < group_size:
                    groups[i].append(row)
                    group_sums[i] += row['要求数']
                    group_ids[i].add(row['前グループ'])
                    break
            else:
                # 全てのグループに同じ「前グループ」IDの人がいる場合、最後のグループに追加
                groups[-1].append(row)
                group_sums[-1] += row['要求数']
                group_ids[-1].add(row['前グループ'])
            
    # グループ番号を追加
    for group_number, group in enumerate(groups, start=1):
        for member in group:
            df.loc[member.name, 'グループ番号'] = group_number

    # dfをグループ番号でソート
    df.sort_values(by='グループ番号', ascending=True, inplace=True)
    
    # グループ番号ごとの要求数の合計を計算
    group_totals = df.groupby('グループ番号')['要求数'].sum().reset_index()
    group_totals.rename(columns={'要求数': '要求数の合計'}, inplace=True)  # カラム名を変更
    
    return df, group_totals


st.title("要求数に基づくグルーピング")

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
        st.session_state['before_df'] = pd.DataFrame()  # 空のデータフレームを設定
        st.switch_page("prokiso.py")
        st.rerun()  # アプリを再実行して状態を更新
        st.success("CSVファイルが消去されました。")

try:
    # csvがアップロードされたとき
    if not st.session_state['before_df'].empty:
        df, group_totals = process_csv(st.session_state['before_df'])

        if df is None or group_totals is None:
            st.error('「要求数」カラムがないデータをアップロードしています。')
        else:
            # タブを作成
            tabs = st.tabs(["グルーピング後のデータ", "グループごとの要求数の合計"])
            
            tabs[0].subheader("グルーピング後のデータ")
            tabs[0].dataframe(df)
            tabs[1].subheader("グループごとの要求数の合計")
            tabs[1].dataframe(group_totals, height=450)
        
            download_name = st.session_state['upload_name'].split(".")[0]
            
            # CSVをバイナリデータに変換
            csv_file = df.to_csv(index=False, encoding="shift-jis").encode('shift-jis')
        
            st.subheader("グルーピング後のデータダウンロード")
            st.download_button(
                label="Download CSV",
                data=csv_file,
                file_name=f'{download_name}_grouped.csv'
            )
except Exception as e:
    st.write(e)
    pass
