# Streamlit
import streamlit as st
# EDA
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

@st.cache_data()
def load_data(uploaded_file):
    return pd.read_csv(uploaded_file)

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
            pass

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

        data = st.session_state['df'].copy()

        st.write('データの確認')
        st.write(data)

        st.subheader('散布図')
        x_col = st.selectbox("X軸の列を選択", data.columns)
        y_col = st.selectbox("Y軸の列を選択", data.columns)
        z_col = st.selectbox("Z軸の列を選択", data.columns)
        color_col = st.selectbox("色の列を選択", data.columns)

        plot_scatter(data, x_col, y_col, z_col, color_col)

        target = select_target(data)

        if st.button('EDAの実行'):
            explore_data(data, target)

def plot_scatter(data, x_col, y_col, z_col, color_col):
    fig = px.scatter_3d(data, x=x_col, y=y_col, z=z_col, color=color_col)
    st.plotly_chart(fig)

def select_target(data):
    st.write("初めにターゲットを選択してください")
    target = st.selectbox("ターゲットを選択", data.columns)
    return target

def explore_data(data, target):
    st.header('EDA')
    st.write('データの行数列数')
    st.write(data.shape)
    
    column1, column2 = st.columns(2)
    
    with column1:
        st.write('データの欠損値')
        st.write(data.isnull().sum())

    with column2:
        st.write('データの型')
        st.write(data.dtypes)

    st.write('統計値')
    st.write(data.describe().T
              .style.bar(subset=['mean'], color=px.colors.qualitative.G10[1])
              .background_gradient(subset=['std'], cmap='Greens')
              .background_gradient(subset='50%', cmap='BuGn')
              )

    cols = data.select_dtypes(include=['int', 'float']).columns

    st.subheader('ヒートマップ（数値型データのみ）')
    st.pyplot(heat(data, cols))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('ヒストグラム（数値型データのみ）')
        for col in cols:
            st.pyplot(create_histogram(data, col))

    with col2:
        st.subheader('相関係数上位5つとターゲットのペアプロット（数値型データのみ）')
        st.pyplot(pair_plot(data, target, cols))

def heat(data, cols):
    corr = data[cols].corr().round(2)
    plt.figure(figsize=(20, 20))
    sns.heatmap(corr, linewidths=0.1, vmax=1, square=True, annot=True, cmap='coolwarm', linecolor='white', annot_kws={'fontsize': 16, 'color':'black'})
    return plt

def create_histogram(data, col):
    plt.figure(figsize=(10, 5))
    data[col].plot(kind='hist', bins=50, color='blue')
    plt.title(col + ' / train')
    return plt

def pair_plot(data, target, cols):
    correlation_matrix = data[cols].corr()
    top_features = correlation_matrix[target].sort_values(ascending=False)[1:6]
    selected_features = top_features.index.tolist() + [target]
    sns.pairplot(data[selected_features])


# Streamlitアプリケーションの実行
st.set_page_config(page_title='データ解析', layout='wide')
st.set_option('deprecation.showPyplotGlobalUse', False)
st.title('データ解析')
load_and_explore_data()

