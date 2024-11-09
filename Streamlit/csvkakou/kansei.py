import streamlit as st

# クエリパラメータを取得
query_params = st.experimental_get_query_params()
page = query_params.get("page", ["home"])[0]

# ページの内容を条件に応じて表示
if page == "home":
    st.title("Home Page")
    st.write("これはホームページです。")
elif page == "admin":
    st.title("Admin Page")
    st.write("管理者専用ページです。")

# サイドバーには「home」だけ表示する
if page == "home":
    st.experimental_set_query_params(page="home")
    st.sidebar.selectbox("ページ選択", ["home"])
