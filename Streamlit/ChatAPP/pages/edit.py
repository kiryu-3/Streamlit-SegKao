import streamlit as st
import streamlit_authenticator as stauth
import yaml
import sqlite3
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet
import os

def setup_database():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                 (date TEXT, group_name TEXT, username TEXT, comment TEXT, target_username TEXT, memo TEXT)''')
    conn.commit()
    return conn, c

def load_credentials(filepath):
    with open(filepath, 'r') as file:
        data = yaml.safe_load(file)

    names = [data['credentials']['usernames'][key]['name'] for key in data['credentials']['usernames']]
    usernames = list(data['credentials']['usernames'].keys())
    passwords = [data['credentials']['usernames'][key]['password'] for key in data['credentials']['usernames']]
    return names, usernames, passwords, data['cookie']['name'], data['cookie']['key'], data['cookie']['expiry_days']

def authenticate(names, usernames, passwords, cookie_name, key, expiry_days):
    authenticator = stauth.Authenticate(
        names=names,
        usernames=usernames,
        passwords=passwords,
        cookie_name=cookie_name,
        key=key,
        cookie_expiry_days=expiry_days,
    )
    return authenticator

def login(authenticator):
    name, authentication_status, username = authenticator.login('Login', 'sidebar')
    st.session_state.name = name
    st.session_state.authentication_status = authentication_status
    st.session_state.username = username
    return name, authentication_status, username

def logout():
    if st.sidebar.button("Logout"):
        st.session_state['authentication_status'] = None
        st.rerun()

def execute_query_and_display_data(conn):
    # SQL クエリを実行してデータを取得し、DataFrame に読み込む
    df = pd.read_sql_query("SELECT * FROM chats", conn)

    # DataFrame をセッションステートに保存
    st.session_state['df'] = df.copy()

    try: 
        if len(st.session_state['df']) != 0:
            final_dfs, code = spreadsheet(st.session_state['df'])

            # データを表示する
            st.caption("data")
            st.dataframe(pd.DataFrame(final_dfs["df1"]))

            # ファイルのダウンロード
            download_name = st.text_input(
                label="ファイル名を入力してください",
                value="chat_filtered",
                key="download_name"
            )
            download_df = pd.DataFrame(final_dfs["df1"])
            csv_file = download_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_file,
                file_name=f'{download_name}.csv'
            )

            st.divider()

            # コードを表示する
            with st.expander("Code"):
                st.code(code)

            # DataFrame をテーブルに書き込む
            download_df.to_sql('chat.db', conn, if_exists='replace', index=False)

            # 接続を閉じる
            conn.close()
    except Exception as e:
        pass

# yaml_pathファイルのパス
yaml_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
names, usernames, passwords, cookie_name, key, expiry_days = load_credentials(yaml_path)
authenticator = authenticate(names, usernames, passwords, cookie_name, key, expiry_days)
name, authentication_status, username = login(authenticator)
if authentication_status:
    logout()
    if name=="admin":
        conn, c = setup_database()
        execute_query_and_display_data(conn)
    else:
        st.sidebar.warning('Please login with administrator accounts.')
elif authentication_status == False:
    st.sidebar.error('Username/password is incorrect')
elif authentication_status == None:
    st.sidebar.warning('Please enter your username and password')
