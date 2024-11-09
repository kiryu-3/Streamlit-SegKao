import streamlit as st

pages = {
    "Your account": [
        st.Page("prokiso.py", title="gg"),
    ]
}

pg = st.navigation(pages)
pg.run()
