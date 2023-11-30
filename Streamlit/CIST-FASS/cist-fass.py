import streamlit as st
from rembg import remove
from PIL import Image
import os
import requests
import io
from io import BytesIO
import time

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
  """)
  # st.write("The input text can be converted to speech")
  # st.write("Audio can be downloaded in mp3 format")

  response1 = requests.get("https://imgur.com/svBwwAT.png")
  image_example1 = Image.open(BytesIO(response1.content))
  st.image(image_example1)

with st.expander("CSV-Filter"):
  st.markdown("""
    - CSVs can be filtered and then downloaded
  """)
  # st.write("Can translate input text into a specified language")
  # st.write("The translated text can be downloaded in mp3 format after being converted to audio")

  response2 = requests.get("https://imgur.com/kOBBXOb.png")
  image_example2 = Image.open(BytesIO(response2.content))
  st.image(image_example2)