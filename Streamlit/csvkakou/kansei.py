import streamlit as st

def page_2():
    st.title("Page 2")

def page_3():
    st.title("Page 3")

pages = {
    "Your account": [
        st.Page(page_2),
        st.Page(page_3),
        st.Page("prokiso.py", title="gg"),
    ]
}

pg = st.navigation(pages)
pg.run()
