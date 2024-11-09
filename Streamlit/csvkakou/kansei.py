import streamlit as st

pages = {
    "Your account": [
        st.Page("02_grouping.py", title="gg"),
    ]
}

pg = st.navigation(pages)
pg.run()
