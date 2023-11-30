import streamlit as st
from PIL import Image
import os
import requests
import io
from io import BytesIO
import time
import pandas as pd

# 画像URLを指定
image_url = "https://imgur.com/C32lMvR.jpg"

# 画像をダウンロードしPILのImageオブジェクトとして読み込む
response = requests.get(image_url)
image = Image.open(BytesIO(response.content))

# Streamlit ページの設定
st.set_page_config(
    page_title="CSV Filters",
    page_icon=image,
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)


st.write('# Image Hub')
st.write('## Explanation')

with st.expander("Human-Flow-Analytics"):
  st.markdown("""
    - CIST's original human flow data visualization tool
    - Uploading data (csv) with latitude and longitude and their time information will allow visualization of the flow of human flow.
    - When the user draws a shape on the map, the number of people who have passed through that shape can be counted.
    - The CSV file to be uploaded must contain data for ID, time, latitude and longitude that identifies the individual.
  """)
  # st.write("The input text can be converted to speech")
  # st.write("Audio can be downloaded in mp3 format")

  response1 = requests.get("https://imgur.com/svBwwAT.png")
  image_example1 = Image.open(BytesIO(response1.content))
  st.image(image_example1)

with st.expander("CSV-Filter"):
  st.markdown("""
    - CSVs can be filtered and then downloaded.
    - Basic CSV files of all types are supported.
  """)
  # st.write("Can translate input text into a specified language")
  # st.write("The translated text can be downloaded in mp3 format after being converted to audio")

  response2 = requests.get("https://imgur.com/kOBBXOb.png")
  image_example2 = Image.open(BytesIO(response2.content))
  st.image(image_example2)

with st.expander("Sample-Data"):
  st.markdown("""
    - Sample data with ID, time, latitude and longitude information to identify individuals.
    - Can be used for "Human-Flow-Analytics" and "CSV-Filter.
  """)

  # 現在のスクリプトのディレクトリを取得
  script_directory = os.path.dirname(os.path.abspath(__file__))
  # CSVファイルを読み込み
  example_data = pd.read_csv(os.path.join(script_directory, 'example_data.csv'))   
  csv_file = example_data.to_csv(index=False)
  st.download_button(
    label="Download CSV",
    data=csv_file,
    file_name='sample_data.csv'
  )
  st.dataframe(example_data)


