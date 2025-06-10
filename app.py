# noinspection PyInterpreter
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'cabbage.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        with open('schema.sql', 'r', encoding='utf-8') as f:
            conn.executescript(f.read())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_price():
    date = request.form['date']
    price = request.form['price']
    source = request.form['source']
    # 將日期格式 yyyy-mm-dd 轉為 yyyy/mm/dd，與查詢一致
    if date:
        date = date.replace('-', '/')
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        # 檢查是否已存在相同資料，避免重複
        cur.execute("SELECT COUNT(*) FROM cabbage_prices WHERE date=? AND price=? AND source=?", (date, price, source))
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO cabbage_prices (date, price, source) VALUES (?, ?, ?)", (date, price, source))
            conn.commit()
    return redirect('/query')

@app.route('/query')
def query():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    # 將日期格式 yyyy-mm-dd 轉為 yyyy/mm/dd
    if start_date:
        start_date = start_date.replace('-', '/')
    if end_date:
        end_date = end_date.replace('-', '/')
    query = "SELECT date, price, source FROM cabbage_prices"
    params = []
    conditions = []
    if start_date and end_date:
        conditions.append("date BETWEEN ? AND ?")
        params.extend([start_date, end_date])
    elif start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    elif end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if min_price:
        conditions.append("price >= ?")
        params.append(min_price)
    if max_price:
        conditions.append("price <= ?")
        params.append(max_price)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date DESC"
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
    return render_template('query.html', rows=rows)

@app.route('/clear', methods=['POST'])
def clear():
    from database import clear_all_prices
    clear_all_prices()
    return redirect('/')

@app.route('/restore', methods=['POST'])
def restore():
    from database import restore_last_clear
    restore_last_clear()
    return redirect('/query')

@app.route('/show_raw', methods=['POST'])
def show_raw():
    raw_rows = []
    with open('原始記錄.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                date = parts[0]
                price = parts[1]
                url = parts[2]
                raw_rows.append((date, price, url))
    # 先清空主表，再插入原始紀錄.txt的數據
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM cabbage_prices')
        for row in raw_rows:
            cur.execute("INSERT INTO cabbage_prices (date, price, source) VALUES (?, ?, ?)", row)
        conn.commit()
    return redirect('/query')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
