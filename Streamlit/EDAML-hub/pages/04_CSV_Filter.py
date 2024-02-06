import streamlit as st
import pandas as pd

# Streamlit Uploaderを使用してExcelファイルをアップロードする
uploaded_file = st.file_uploader("Excelファイルをアップロードしてください", type=["xlsx", "xls"])

if uploaded_file is not None:
    # Excelファイルを読み込む
    xls = pd.ExcelFile(uploaded_file)

    # Excelファイル内の各シートを処理する
    for sheet_name in xls.sheet_names:
        st.write(f"シート名: {sheet_name}")
        
        # シートごとにデータフレームに読み込む
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # データフレームを表示する
        st.dataframe(df)
