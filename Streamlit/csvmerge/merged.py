import streamlit as st
import csv
import numpy as np
import pandas as pd
import re
import os
import requests
from PIL import Image
import io
from io import BytesIO, StringIO
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
        
        try:
            df = pd.read_csv(io.BytesIO(file_data), header=None, encoding=encoding, on_bad_lines="skip", engine="python")
        except Exception as e:
            st.write(f"データの読み込み中にエラーが発生しました: {e}")

        st.session_state['anketo_name'] = df.iloc[0, 1]  # Qの問題文を取得
        
        q_number = 1  # 初期値を設定
        st.session_state['question_dict'] = dict()
        
        while True:  # 無限ループ
            try:
                # Qの問題文を探す
                q_index = df[df[0] == f'Q {q_number}'].index[0]  # Qのインデックスを取得
                q_question = df.iloc[q_index + 1, 0]  # Qの問題文を取得
                # st.write(df.iloc[q_index + 1, 0])
                # st.write(df.iloc[q_index + 2, 0])
                
                # 結果を表示
                # st.write(f"Q{q_number}の問題文:", q_question)
                st.session_state['question_dict'][f'Q{q_number}'] = q_index
                
                q_number += 1  # 次の番号に進む
            except IndexError:
                # インデックスエラーが発生した場合にループを抜ける
                # st.write("ループを終了します。")
                break
            except Exception as e:
                # 他のエラーをキャッチする場合
                # st.write(f"予期しないエラーが発生しました: {e}")
                break

        st.session_state['df'] = df
        
    else:
        st.session_state['df'] = pd.DataFrame()
        st.session_state['question_df'] = dict()

def upload_csv2():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile2'] is not None:

        st.session_state['question_df'] = dict()
        
        for idx, upload_data in enumerate(st.session_state['upload_csvfile2']):

            # アップロードされたファイルデータを読み込む
            file_data = upload_data.read()

            # ファイルをStringIOに変換
            file = StringIO(upload_data.getvalue().decode("shift-jis"))
            
            reader = csv.reader(file)
        
            # 最初の3行をスキップ
            for _ in range(3):
                next(reader)
        
            # ヘッダーを取得し、余分な空白や引用符を削除
            header = next(reader)
            header = [cell for cell in header if cell.strip() != '']
        
            rows = []
            for row in reader:
                # 余分な空白や引用符を削除
                row = [cell for cell in row if cell.strip() != '']
        
                # 列数が異なる場合、必要な列数に調整
                if len(row) > len(header):
                    row[5] = '、'.join(row[5:])  # 5列目以降を結合し、1つの列として扱う
                    row = row[:len(header)]
                rows.append(row)

            try:
                temp_df = pd.read_csv(io.BytesIO(file_data), header=None, encoding=st.session_state['encoding'], on_bad_lines="skip", engine="python")
                # 設問番号を取得（1行目の1列目の値）
                q_number = temp_df.iloc[0, 1]  # 設問番号を取得

                df = pd.DataFrame(rows, columns=header)
                
                st.session_state['question_df'][f'Q{q_number}'] = df
            except Exception as e:
                (f"データの読み込み中にエラーが発生しました: {e}")

    else:
        st.session_state['question_df'] = dict()

# 初期化
if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame()  # 空のデータフレーム

st.title('Portal-CSV-merged')
# ラベルの改行に対応
st.sidebar.markdown("設問文のCSVファイルをアップロード（複数不可）<br>(例): summary.csv, outline.csv", unsafe_allow_html=True)
st.sidebar.file_uploader(label="", type=["csv"],
                         key="upload_csvfile",
                         accept_multiple_files=False,
                         on_change=upload_csv
                         )

try:
    if len(st.session_state['df']) != 0:
        st.sidebar.write(st.session_state['question_dict'])

        st.markdown("設問回答のCSVファイルをアップロード（複数可、順不同）<br>(例): Q[1].csv, Q[2].csv, Q[3].csv", unsafe_allow_html=True)
        st.file_uploader(label="", type=["csv"],
                         key="upload_csvfile2",
                         accept_multiple_files=True,
                         on_change=upload_csv2
                         )
        
        # 最初のデータフレームを基準にして結合
        merged_df = None
        for q_number, df in st.session_state['question_df'].items():
            if merged_df is None:
                merged_df = df
                
                q_context = st.session_state['question_dict'][q_number]

                # 回答内容をカンマで結合する
                merged_df = merged_df.groupby(['[学籍番号', ' 氏名', ' フリガナ', ' クラス', ' 出席番号'], as_index=False).agg({' 回答内容]': lambda x: ','.join(x.astype(str))})

                merged_df.rename(columns={' 回答内容]': f'{q_number}：{q_context}'}, inplace=True)
                # merged_df.rename(columns={' 回答内容]': f'{q_number}：{q_context}'}, inplace=True)
            else:
                q_context = st.session_state['question_dict'][q_number]

                # 回答内容をカンマで結合する
                df = df.groupby(['[学籍番号', ' 氏名', ' フリガナ', ' クラス', ' 出席番号'], as_index=False).agg({' 回答内容]': lambda x: ','.join(x.astype(str))})

                df.rename(columns={' 回答内容]': f'{q_number}'}, inplace=True)
                # df.rename(columns={' 回答内容]': f'{q_number}：{q_context}'}, inplace=True)
                
                merged_df = pd.merge(merged_df, df, on="[学籍番号", how="outer", suffixes=('', '_y'))
                # 不要な重複列を削除
                merged_df = merged_df.loc[:, ~merged_df.columns.str.endswith('_y')]
             
        merged_df.rename(columns={'[学籍番号': '学籍番号'}, inplace=True)

        for column in merged_df.columns[5:]:
            q_index = st.session_state['question_dict'][column]
            q_sentence = list()
            
            q_candidates = list(st.session_state['df'].iloc[q_index:q_index+10, 0])
            for q_candidate in q_candidates:
                if q_candidate in merged_df[column].unique()[0]:
                    break
                q_sentence.append(q_candidate)
                
            # 半角スペースを区切り文字として結合
            q_sentence_str = " ".join(q_sentence)
            merged_df.rename(columns={f'{column}': f'{column}：{q_sentence_str}'}, inplace=True)
        
        columns_to_sort = merged_df.columns[5:]  # 6列目以降の列を取得
        sorted_columns = sorted(columns_to_sort, key=lambda x: int(x.split('：')[0][1:]))  # 数字を基準にソート
        new_order = list(merged_df.columns[:5]) + sorted_columns  # 新しい列の順番を作成（最初の5列 + ソートされた列）
        merged_df = merged_df[new_order]  # 新しい順番でデータフレームを再構築

        st.subheader("結合後のデータ")
        st.write(merged_df)
        # st.write(merged_df.columns)
        
        merged_df.to_csv(buf := BytesIO(), index=False, encoding=st.session_state['encoding'])

        st.download_button(
                  label="Download CSV",
                  data=buf.getvalue(),
                  file_name=f'{st.session_state['anketo_name']}.csv'
                )
        st.divider()
except Exception as e:
    st.write(e)
    pass
    
