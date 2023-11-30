import streamlit as st
from PIL import Image
from gtts import gTTS
import os
import base64
import langdetect
import requests
import io
from io import BytesIO
import boto3
import json


# 画像URLを指定
image_url = "https://imgur.com/3ZfMAyY.jpg"

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


# シークレットから秘密情報を取得する
access_key = st.secrets["access_key"]
secret_key = st.secrets["secret_key"]
region_name = st.secrets["region_name"] 

session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region_name)
comprehend = session.client('comprehend')
translate = session.client('translate')
polly = session.client('polly')

# 現在のスクリプトのディレクトリを取得
script_directory = os.path.dirname(os.path.abspath(__file__))  

# JSONファイルからデータを読み込む
with open(os.path.join(script_directory, 'languages_data.json'), "r", encoding="utf-8") as json_file:
    loaded_languages_data = json.load(json_file)

if 'mapping' not in st.session_state:  # 初期化
    st.session_state['mapping'] = loaded_languages_data["before_languages"]


if 'select_languages' not in st.session_state:  # 初期化
    st.session_state['select_languages'] = loaded_languages_data["after_languages"]

if 'selected_languages' not in st.session_state:  # 初期化
    st.session_state['selected_languages'] = st.session_state['select_languages']
if "honyaku_mode" not in st.session_state:  # 初期化
    st.session_state["honyaku_mode"] = False

text_area = st.empty()
button_area = st.empty()
# cols = st.columns([3, 7])

if 'voices' not in st.session_state:  # 初期化
  st.session_state['voices'] = loaded_languages_data["voice_languages"]

if "language_code" not in st.session_state:  # 初期化
    st.session_state['language_code'] = ""

if "input_language" not in st.session_state:  # 初期化
    st.session_state['input_language'] = ""

def nlp():
    if st.session_state["tab3_input_text"] != "":
        st.session_state["honyaku_mode"] = True
        st.session_state['input_language'] = ""
        response = comprehend.detect_dominant_language(Text=st.session_state["tab3_input_text"])
        st.session_state["language_code"] = response['Languages'][0]['LanguageCode']

        # マッピングから言語名を取得
        st.session_state["language_name"] = st.session_state["mapping"][st.session_state["language_code"]]
        st.session_state['selected_languages'] = [lang if lang != st.session_state['language_name'] else f"{lang}(Original)" for lang in st.session_state['select_languages']]
        # "original" を含む要素がある場合、それを先頭に移動
        st.session_state['selected_languages'].sort(key=lambda x: "Original" not in x)
        # st.session_state['selected_languages'] = [lang if lang != st.session_state['language_name'] else f"{lang} (元言語)" for lang in st.session_state['select_languages']]
        # st.session_state['selected_languages'] = [lang for lang in st.session_state['select_languages'] if lang != st.session_state['language_name']]

    else:
        st.session_state["honyaku_mode"] = False
        st.session_state["language_code"] = ""
        st.session_state["language_name"] = ""
        st.session_state['selected_languages'] = st.session_state['select_languages']
        st.session_state['translated_text'] = ""


def honyaku():
    reverse_mapping = {v: k for k, v in st.session_state['mapping'].items()}
    try:
        input_language = st.session_state["input_language"].replace("(Original)", "")

        response = translate.translate_text(
            Text=st.session_state["tab3_input_text"],
            SourceLanguageCode= st.session_state["language_code"],
            TargetLanguageCode=reverse_mapping[input_language]
        )
        st.session_state["translated_text"] = response['TranslatedText']
        response = polly.synthesize_speech(
            Text=st.session_state["translated_text"],
            OutputFormat='mp3',
            VoiceId=st.session_state['voices'][input_language]
        )
        st.session_state['audio_stream'] = response['AudioStream'].read()

        # st.session_state["cols"][1].write(f"言語：{st.session_state['input_language']}")
        # st.session_state["cols"][1].write(f"テキスト：{st.session_state['translated_text']}")
        # # 音声をバイナリストリームとして再生する
        # st.session_state["cols"][1].audio(BytesIO(audio_stream), format='audio/mp3')

    except Exception as e:
        st.session_state['audio_stream'] = ""
        # error_message = str(e)
        # st.error(error_message)

def start():
    if st.session_state["tab3_input_text"] != "":
        button_area.button(label="Go!", on_click=nlp)
        st.session_state["honyaku_mode"] = True

st.write('# VoiceTranslate Hub')

with st.expander("Explanation"):
    st.markdown("""
      - Can translate input text into a specified language
      - The translated text can be downloaded in mp3 format after being converted to audio
    """)
    # st.write("Can translate input text into a specified language")
    # st.write("The translated text can be downloaded in mp3 format after being converted to audio")

    response2 = requests.get("https://imgur.com/YLszTa4.png")
    image_example2 = Image.open(BytesIO(response2.content))
    st.image(image_example2)

st.text_area(label="Please enter the sentence to be translated",
                key="tab3_input_text",
                height=200,
                value="おはようございます")
st.button(label="Go to Translate!", on_click=nlp, key="tab3")

# st.session_state["cols"] = st.columns([3, 7])
if st.session_state["honyaku_mode"]:
    st.selectbox(
                label="Please select the language you wish to interpret",
                options=[""]+ st.session_state['selected_languages'],
                key="input_language",
                on_change=honyaku
            )
if st.session_state["input_language"] != "" and st.session_state["audio_stream"] != "":
    # st.write(f"言語：{st.session_state['input_language']}")
    with st.expander("Post-translation text"):
      st.text_area(label="Post-translation text", height=200, value=st.session_state["translated_text"], disabled=True)

    # 音声をバイナリストリームとして再生する
    # audio_stream から BytesIO オブジェクトを作成する
    audio_bytes = BytesIO(st.session_state['audio_stream'])
    st.audio(audio_bytes, format='audio/mp3')

    input_language = st.session_state["input_language"].replace("(Original)", "")
    response2 = translate.translate_text(
        Text=input_language,
        SourceLanguageCode= "ja",
        TargetLanguageCode= "en"
    )

    # st.write("ファイル名を入力してください")
    st.text_input(
        label="Press Input download filename and Enter to Apply",
        value=f"output_{response2['TranslatedText']}",
        key="tab3_download_name"
    )
    st.download_button(
        label="Download MP3 files",
        data=audio_bytes.read(),
        file_name=f'{st.session_state["tab3_download_name"]}.mp3',
        key="tab3_downloader"
    )
