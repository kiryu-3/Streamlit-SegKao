# Streamlit
import streamlit as st
# EDA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.figure as figure
# ML
from pycaret.regression import *

import re
import requests
from PIL import Image
import io
from io import BytesIO

# 画像URLを指定
image_url = "https://imgur.com/C32lMvR.jpg"

# 画像をダウンロードしPILのImageオブジェクトとして読み込む
response = requests.get(image_url)
image = Image.open(BytesIO(response.content))

# Streamlit ページの設定
st.set_page_config(
    page_title="回帰モデル",
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

def reduce_mem_usage(df, verbose=True):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    start_mem = df.memory_usage().sum() / 1024**2
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
    end_mem = df.memory_usage().sum() / 1024**2
    return df

def upload_csv():
    # csvがアップロードされたとき
    if st.session_state['upload_csvfile'] is not None:
        if 'df' not in st.session_state:
            # アップロードされたファイルデータを読み込む
            file_data = st.session_state['upload_csvfile'].read()
            # バイナリデータからPandas DataFrameを作成
            try:
                df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8", engine="python")
                st.session_state["ja_honyaku"] = False
            except UnicodeDecodeError:
                # UTF-8で読み取れない場合はShift-JISエンコーディングで再試行
                df = pd.read_csv(io.BytesIO(file_data), encoding="shift-jis", engine="python")
                st.session_state["ja_honyaku"] = True
    
            # カラムの型を自動で適切に変換
            st.session_state['df'] = reduce_mem_usage(df)
        else:
            st.session_state['df'] = pd.DataFrame()

def load_and_explore_data():
        st.file_uploader("CSVファイルをアップロード",
                       type=["csv"],
                       key="upload_csvfile",
                       on_change=upload_csv
                       )

    # if uploaded_file:
    #     # キャッシュからデータを取得し、存在しない場合は新たにデータをロードしてキャッシュに保存
    #     if "data_cache" in st.session_state:
    #         data = st.session_state.data_cache
    #     else:
    #         data = pd.read_csv(uploaded_file)
    #         st.session_state.data_cache = data
        try:
            data = st.session_state['df'].copy()
    
            st.write('データの確認')
            st.write(data)
    
            target = select_target(data)
            
            # if st.button('回帰モデルの構築'):
            train_and_tune_regression_model(data, target)
        except:
            pass

def select_target(data):
    st.write("初めにターゲットを選択してください")
    target = st.selectbox("ターゲットを選択", data.columns)
    return target

def train_and_tune_regression_model(data, target):
    st.sidebar.subheader("モデルのトレーニング/チューニング")

    if st.sidebar.button("回帰モデルをトレーニング"):
        st.header("回帰モデルの評価")

        # PyCaret Regression Setup
        reg_setup = setup(data, target=target, session_id=0)

        model_results = train_regression_model()
        st.session_state.model_results = model_results

    # session_stateにモデルの結果が保存されている場合、その結果を表示する
    if "model_results" in st.session_state:
        st.subheader("モデル評価結果")
        st.write(st.session_state.model_results)

        # 利用可能なモデルの略称とフルネームを定義
        abbreviations = ["lr", "lasso", "ridge", "en", "lar", "llar", "omp", "br", "par", "huber", "knn", "dt", "rf", "et", "ada", "gbr", "lightgbm", "dummy"]
        model_names = ["Linear Regression", "Lasso Regression", "Ridge Regression", "Elastic Net", "Least Angle Regression", "Lasso Least Angle Regression", "Orthogonal Matching Pursuit", "Bayesian Ridge", "Passive Aggressive Regressor", "Huber Regressor", "K Neighbors Regressor", "Decision Tree Regressor", "Random Forest Regressor", "Extra Trees Regressor", "AdaBoost Regressor", "Gradient Boosting Regressor", "Light Gradient Boosting Machine", "Dummy Regressor"]

        # モデルの略称とフルネームを対応させる辞書を作成
        model_dict = dict(zip(abbreviations, model_names))

        selected_model_abbreviation = st.selectbox("チューニング対象のモデルを選択し、サイドバーの「モデルをチューニング」ボタンを押してください", abbreviations)
        st.session_state.selected_model_abbreviation = selected_model_abbreviation

        if st.sidebar.button("モデルをチューニング"):
            st.session_state.selected_model = create_model(st.session_state.selected_model_abbreviation)
            tuned_results = tune_regression_model(st.session_state.selected_model)
            st.session_state.tuned_results = tuned_results

        if "tuned_results" in st.session_state:
            st.subheader("チューニング結果")
            st.write(st.session_state.tuned_results)

            selected_models = select_model()
            st.session_state.final_regressioned_model = finalize_regression_model(selected_models)

            if st.sidebar.button("モデルの可視化"):
                display_model(selected_models)

            if st.sidebar.button("検証用データの予測"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    return_prediction_model = prediction_model(st.session_state.final_regressioned_model)
                with col2:
                    st.pyplot(display_prediction(return_prediction_model))
            



def train_regression_model():
    # モデルトレーニングと比較 (すべてのモデルを評価)
    with st.spinner("モデルトレーニング中..."):
        compare_model = compare_models()
        st.write("モデルのトレーニングが完了しました！")

    # モデルの評価と結果
    model_results = pull()
    st.write("モデル評価完了")

    return model_results

def tune_regression_model(model):
    with st.spinner("モデルチューニング中..."):
        st.session_state.tuned_model = tune_model(model)
        st.write("モデルのチューニングが完了しました！")

    # チューニング結果を取得
    tuned_results = pull()

    return tuned_results

def select_model():
    st.write("元のモデルか、チューニング後のモデルか選択してください。可視化をする場合はサイドバーの「モデルの可視化」ボタンを押してください。")
    model_choices = ["元のモデル", "チューニング後のモデル"]
    selected_choice = st.selectbox("モデルを選択", model_choices)

    # 選択に応じてモデルを返す
    if selected_choice == "元のモデル":
        return st.session_state.selected_model
    else:
        return st.session_state.tuned_model

def finalize_regression_model(model):
    with st.spinner("モデル構築中"):
        st.session_state.final_regression_model = finalize_model(model)
        st.write("モデルの構築が完了しました！")
    return st.session_state.final_regression_model

def prediction_model(model):
    st.header('検証用データの予測結果')
    prediction = predict_model(model)
    model_evaluation = pull()
    st.write(model_evaluation)
    st.write(prediction)
    return prediction

def display_model(model):
    st.header('モデルの可視化')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('残差プロット')
        plot_model(model, scale = 1, display_format="streamlit")
    
    with col2:
        st.subheader('予測誤差プロット(横軸：真値、縦軸：予測値)')
        plot_model(model, plot='error', display_format="streamlit")
    
    plot_model(model, plot='feature', display_format="streamlit")


def display_prediction(prediction):
    st.header('検証用データの予測と正解のプロット')
    y_test = get_config('y_test')
    plt.rcParams['font.size'] = 5
    plt.figure(figsize=figure.figaspect(1))
    plt.scatter(y_test, prediction.iloc[:, -1])
    y_max = max(y_test.max(), prediction.iloc[:, -1].max()) 
    y_min = min(y_test.min(), prediction.iloc[:, -1].min()) 
    y_upper = y_max + 0.05 * (y_max - y_min) 
    y_lower = y_min - 0.05 * (y_max - y_min) 
    plt.plot([y_lower, y_upper], [y_lower, y_upper], 'k-') 
    plt.ylim(y_lower, y_upper) 
    plt.xlim(y_lower, y_upper) 
    plt.xlabel('actual y')
    plt.ylabel('estimated y')
    return plt

def estimate_model(model, test_data):
    estimate_target = predict_model(model, test_data)
    return estimate_target

# Streamlitアプリケーションの実行
# st.set_page_config(page_title='回帰モデル', layout='wide')
# st.set_option('deprecation.showPyplotGlobalUse', False)
st.title('回帰モデル')
load_and_explore_data()

