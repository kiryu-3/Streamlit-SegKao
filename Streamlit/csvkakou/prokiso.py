import pandas as pd

# CSVファイルの読み込み
df = pd.read_csv('your_file.csv')

# "クラス"カラムの値が"2C"ではないものの"出席番号"を90にする
df.loc[df['クラス'] != '2C', '出席番号'] = 90

# "回答内容"列の「~したい」で要求数を数え、新しい"要求数"カラムを作成
df['要求数'] = df['回答内容'].str.count('~したい')

# 要求数を元にグループ分け
# 要求数でソート
df_sorted = df.sort_values(by='要求数')

# グループ分け
group_size = 4  # 4人組のグループ
num_groups = len(df_sorted) // group_size + (len(df_sorted) % group_size > 0)

# グループ番号を追加
df_sorted['グループ番号'] = (df_sorted.index // group_size) + 1

# 元のデータフレームにグループ番号を戻す
df['グループ番号'] = df_sorted['グループ番号'].values

# 結果をCSVに保存
df.to_csv('output_file.csv', index=False)

print("処理が完了しました。")
