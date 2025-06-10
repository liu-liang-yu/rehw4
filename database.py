import sqlite3

def insert_price(date, price):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO prices (date, price) VALUES (?, ?)', (date, price))
    conn.commit()
    conn.close()

def clear_all_prices():
    conn = sqlite3.connect('cabbage.db')
    c = conn.cursor()
    # 備份現有資料到 backup_cabbage_prices
    c.execute('''CREATE TABLE IF NOT EXISTS backup_cabbage_prices AS SELECT * FROM cabbage_prices WHERE 0''')
    c.execute('DELETE FROM backup_cabbage_prices')
    c.execute('INSERT INTO backup_cabbage_prices SELECT * FROM cabbage_prices')
    # 清空主表
    c.execute('DELETE FROM cabbage_prices')
    conn.commit()
    conn.close()

def restore_last_clear():
    conn = sqlite3.connect('cabbage.db')
    c = conn.cursor()
    # 將備份資料還原到主表
    c.execute('INSERT INTO cabbage_prices SELECT * FROM backup_cabbage_prices')
    c.execute('DELETE FROM backup_cabbage_prices')
    conn.commit()
    conn.close()

