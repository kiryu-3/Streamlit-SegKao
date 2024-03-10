import streamlit as st
from rembg import remove
from PIL import Image
import os
import requests
import io
from io import BytesIO
import time
import os

# 画像ファイルのパス
image_path = os.path.join(os.path.dirname(__file__), 'icon_image.png')

# 画像をPILのImageオブジェクトとして読み込む
image = Image.open(image_path)

# Streamlit ページの設定
st.set_page_config(
    page_title="Image-Hub",
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
st.file_uploader("File Upload", type=('jpg', 'png', 'jpeg'),
                  key="uploaded_image",
                  accept_multiple_files=False)

# 画像がアップロードされたとき
if st.session_state["uploaded_image"] is not None:

  st.session_state["first_image"] = Image.open(st.session_state["uploaded_image"])
  st.session_state["edit_image"] = Image.open(st.session_state["uploaded_image"])
  # if 'edit_image' not in st.session_state:  # 初期化
    # st.session_state["edit_image"] = Image.open(st.session_state["uploaded_image"])
  if 'count' not in st.session_state:  # 初期化
    st.session_state["count"] = 0

  col1 = st.columns(3)

  resize_title = col1[0].empty()
  resize_expander = col1[0].empty()
  radio_area = col1[0].empty()
  width_area = col1[0].empty()
  height_area = col1[0].empty()

  resize_title.write('## Image Resize')
  with resize_expander.expander("See explanation"):
    st.markdown("""
      - You can specify the width and height of the image in pixels
      - After checking the reflected image, you can download it

      Reference <<<Recommended size>>
      - Discord custom pictograms: 128px x 128px
      - Custom server icon for Discord: 512px x 512px or larger
      - Notion custom icon: 280px x 280px
    """)




  # col1[0].write(f'幅：{st.session_state["edit_image"].width}px　高さ：{st.session_state["edit_image"].height}px')

  col1[1].write('## Transparent')
  with col1[1].expander("See explanation"):
    st.markdown("""
      - You can specify the width and height of the image in pixels
      - After checking the reflected image, you can download it
    """)

  def checkbox_callback():
    checkbox_value = st.session_state.checkbox_key  # ここで処理を行う
    if checkbox_value:
      st.session_state["edit_image"] = remove(st.session_state["edit_image"])
    else:
      st.session_state["edit_image"] = Image.open(st.session_state["uploaded_image"])

  # col1[1].checkbox('Transparent', key="checkbox_key", on_change=checkbox_callback)

  col1[1].checkbox('Transparent', key="checkbox_key")
  if st.session_state["checkbox_key"]:
    st.session_state["edit_image"] = remove(st.session_state["edit_image"])
  else:
    st.session_state["edit_image"] = Image.open(st.session_state["uploaded_image"])


  col1[2].write('## Rotation Angle')
  with col1[2].expander("See explanation"):
    st.markdown("""
      - Rotation angle can be set
      - After checking the reflected image, you can download it
    """)

  def rotate_renew():
    st.session_state["count"] += 90

  col1[2].button("Turn", on_click=rotate_renew)


  col2 = st.columns(2)

  col2[0].write("### Image before Reflection")
  col2[0].image(st.session_state["first_image"],
                    caption = f'幅：{st.session_state["first_image"].width}px　高さ：{st.session_state["first_image"].height}px',
                    use_column_width="auto",)

  st.session_state["edit_image"] = st.session_state["edit_image"].rotate(st.session_state["count"], expand=True)
  edit_width = st.session_state["edit_image"].width
  edit_height = st.session_state["edit_image"].height

  # ラジオボタンで選択肢を切り替え
  selected_option = radio_area.radio("Select input type:", ["Number Input", "Slider"], horizontal=True)
  if selected_option == "Number Input":
    # Number Inputの場合
    width_area.number_input("Select the width to resize (px)", min_value=1, max_value=edit_width*10, value=edit_width, step=1, key="resize_width")
    height_area.number_input("Select the height to resize (px)", min_value=1, max_value=edit_height*10, value=edit_height, step=1, key="resize_height")
  else:
    width_area.slider("Select the width to resize (px)", 1, edit_width*10, edit_width, step=1, key="resize_width",)
    height_area.slider("Select the height to resize (px)", 1, edit_height*10, edit_height, step=1, key="resize_height")
  st.session_state["edit_image"] = st.session_state["edit_image"].resize((st.session_state["resize_width"], st.session_state["resize_height"]))

  image_area_title = col2[1].empty()
  image_area_title.write("### Image after Reflection")

  status_area = col2[1].empty()
  bar_area = col2[1].empty()
  bar = bar_area.progress(0)
  for i in range(100):
      status_area.text(f'Iteration {i+1}')
      bar.progress(i+1)
      time.sleep(0.1)
  status_area.empty()
  bar_area.empty()

  col2[1].image(st.session_state["edit_image"],
                  caption = f'幅：{st.session_state["edit_image"].width}px　高さ：{st.session_state["edit_image"].height}px',
                  use_column_width="auto",)


  image_name = st.session_state["uploaded_image"].name.split(".")[0]
  image_type = st.session_state["uploaded_image"].name.split(".")[1]

  # 画像のバイナリエンコード
  img_byte_array = io.BytesIO()
  st.session_state["edit_image"].save(img_byte_array, format='PNG')
  img_byte_array = img_byte_array.getvalue()

  # st.write("ファイル名を入力してください")
  st.text_input(
      label="Please Input download filename and Enter to Apply",
      value=f"{image_name}_edited",
      key="download_name"
  )
  st.download_button(
      label="Download Image",
      data=img_byte_array,
      file_name=f'{st.session_state["download_name"]}.{image_type}'
  )
else:
  st.session_state["count"] = 0
  st.session_state["remove_flag"] = False
