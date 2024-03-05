import time 
import sqlite3 

import bcrypt
from PIL import Image
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from datetime import datetime, timedelta
import os
import pytz

def setup_database():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                 (date TEXT, group_name TEXT, username TEXT, comment TEXT)''')
    conn.commit()
    return conn, c

def select_group_and_username():
    def get_japan_time():
        # 日本時間のタイムゾーンを設定
        jst = pytz.timezone('Asia/Tokyo')
        # 現在のUTC時間を取得
        utc_now = datetime.utcnow()
        # UTC時間にタイムゾーンを設定し、日本時間に変換
        japan_now = utc_now.replace(tzinfo=pytz.utc).astimezone(jst)
        return japan_now
    
    def get_last_year_date():
        # 現在の日本時間を取得
        japan_now = get_japan_time()
        # 一年前の日付を計算
        last_year_date = japan_now - timedelta(days=365)
        return last_year_date
        
    # 関数を使用して今日の日付と一年前の日付を取得
    today = get_japan_time()
    lastday = get_last_year_date()

    # 日付を選択する入力ウィジェットを表示し、ユーザーが日付を選択する
    date = st.sidebar.date_input(
        label="日付を選択してください",
        value=today,  # 初期値を今日の日付に設定
        min_value=lastday,  # 一年前の日付を最小値に設定
        max_value=today  # 今日の日付を最大値に設定
    )

    group = st.sidebar.selectbox('グループを選択してください', ['グループA', 'グループB', 'グループC', 'グループD', 'グループE', 'グループF', 'グループG'])
    username = st.sidebar.text_input('ユーザー名を入力してください')

    st.session_state["date"] = date
    st.session_state["group"] = group
    st.session_state["username"] = username
    

    st.sidebar.write(f'date：{st.session_state["date"]}')
    st.sidebar.write(f'group：{st.session_state["group"]}')
    st.sidebar.write(f'username：{st.session_state["username"]}')
    
    return date, group, username

def create_input_form():
    mode = st.radio(
            label='送信したいデータを選択してください',
            options=["number", "text"],
            index=0,
            horizontal=True,
        )
    with st.form("info_form"):
        if mode == "number":
            # 数値入力フィールドを表示し、ユーザーが月を入力する
            comment = st.number_input(
                label="点数を選択してください",
                min_value=1,
                max_value=5,
                value=3,
            )
        else:
            comment = st.text_area('コメントを入力してください')
        
        # submitボタンの生成
        submit_btn = st.form_submit_button("送信")

    return comment, submit_btn

def save_comment_to_database(conn, c, date, group, username, comment):
    if comment:
        c.execute("INSERT INTO chats (date, group_name, username, comment) VALUES (?, ?, ?, ?)", (date, group, username, comment))
        conn.commit()

def display_chat_input(c, date, group):
    chat_rows = c.execute("SELECT username, comment FROM chats WHERE group_name=? AND date=?", (group, date))

    for row in chat_rows:
        if row[0] == st.session_state["username"]:
            st.chat_message("user").write(f"{row[0]}:\n {row[1]}")
        else:
            st.chat_message("assistant").write(f"{row[0]}:\n {row[1]}")

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

def process_authentication(authentication_status):
    if authentication_status:
        conn, c = setup_database()
        date, group, username = select_group_and_username()

        if len(username) != 0:
            form_info = create_input_form()
            comment = form_info[0]
            if form_info[1]:
                save_comment_to_database(conn, c, date, group, username, comment)
            display_chat_input(c, date, group)
    elif authentication_status == False:
        st.sidebar.error('Username/password is incorrect')
    elif authentication_status == None:
        st.sidebar.warning('Please enter your username and password')

# yaml_pathファイルのパス
yaml_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
names, usernames, passwords, cookie_name, key, expiry_days = load_credentials(yaml_path)
authenticator = authenticate(names, usernames, passwords, cookie_name, key, expiry_days)
name, authentication_status, username = login(authenticator)
if authentication_status:
    logout()
process_authentication(authentication_status)
