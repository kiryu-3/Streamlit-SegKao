import streamlit as st

def page_2():
    st.title("Page 2")

pages = {
    "Your account": [
        st.Page(page_2),
        st.Page("prokiso.py", title="gg"),
    ]
}

pg = st.navigation(pages)
pg.run()
