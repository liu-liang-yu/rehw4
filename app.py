# noinspection PyInterpreter
from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DB_NAME = 'cabbage.db'
app.secret_key = 'your_secret_key_here'  # 請改為安全的隨機字串

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        with open('schema.sql', 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        # 自動補齊 password 欄位
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cur.fetchall()]
        if 'password' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN password TEXT')
            conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

# 用戶註冊
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute('SELECT id FROM users WHERE username=?', (username,))
            if cur.fetchone():
                flash('用戶名已存在')
                return redirect(url_for('register'))
            password_hash = generate_password_hash(password)
            cur.execute('INSERT INTO users (username, password_hash, password) VALUES (?, ?, ?)', (username, password_hash, password))
            conn.commit()
        flash('註冊成功，請登入')
        return redirect(url_for('login'))
    return render_template('register.html')

# 用戶登入
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute('SELECT id, password_hash FROM users WHERE username=?', (username,))
            user = cur.fetchone()
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['username'] = username
                flash('登入成功')
                return redirect(url_for('index'))
            else:
                flash('帳號或密碼錯誤')
    return render_template('login.html')

# 用戶登出
@app.route('/logout')
def logout():
    session.clear()
    flash('已登出')
    return redirect(url_for('index'))

# 儀表板
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    def format_query_content(content):
        try:
            import ast
            # 先嘗試解析為 dict
            d = None
            if isinstance(content, str):
                try:
                    d = ast.literal_eval(content)
                except Exception:
                    d = None
            if not isinstance(d, dict):
                # 嘗試解析 key=value 形式
                d = {}
                for part in str(content).split(','):
                    if '=' in part:
                        k, v = part.strip().split('=', 1)
                        d[k.strip()] = v.strip()
            # 取得欄位
            start_date = d.get('start_date')
            end_date = d.get('end_date')
            min_price = d.get('min_price')
            max_price = d.get('max_price')
            # 判斷是否為 None 或空
            def is_empty(val):
                return val is None or val == '' or str(val).lower() == 'none'
            # 價格區間
            if (not is_empty(min_price)) or (not is_empty(max_price)):
                if (not is_empty(min_price)) and (not is_empty(max_price)):
                    return f"價格 {min_price} ~ {max_price} 元/斤"
                elif not is_empty(min_price):
                    return f"價格 {min_price} 元/斤以上"
                elif not is_empty(max_price):
                    return f"價格 {max_price} 元/斤以下"
            # 日期區間
            if (not is_empty(start_date)) or (not is_empty(end_date)):
                if (not is_empty(start_date)) and (not is_empty(end_date)):
                    return f"日期 {start_date} ~ {end_date}"
                elif not is_empty(start_date):
                    return f"{start_date} 之後"
                elif not is_empty(end_date):
                    return f"{end_date} 之前"
            # 都沒指定
            return "全部資料"
        except Exception:
            return str(content)
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute('SELECT query_time, query_content FROM user_queries WHERE user_id=? ORDER BY query_time DESC', (session['user_id'],))
        records = cur.fetchall()
        # 將查詢內容格式化
        records = [(r[0], format_query_content(r[1])) for r in records]
    return render_template('dashboard.html', records=records)

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

# 修改查詢，記錄用戶查詢紀錄
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

    # 構建查詢範圍描述
    query_range = None
    if start_date or end_date:
        if start_date and end_date:
            query_range = f"{start_date} ~ {end_date}"
        elif start_date:
            query_range = f"{start_date} 之後"
        elif end_date:
            query_range = f"{end_date} 之前"
    elif min_price or max_price:
        if min_price and max_price:
            query_range = f"{min_price} ~ {max_price} 元/斤"
        elif min_price:
            query_range = f"{min_price} 元/斤以上"
        elif max_price:
            query_range = f"{max_price} 元/斤以下"

    # 查詢紀錄內容
    query_content = f"start_date={start_date}, end_date={end_date}, min_price={min_price}, max_price={max_price}"
    if 'user_id' in session:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO user_queries (user_id, query_content) VALUES (?, ?)', (session['user_id'], query_content))
            conn.commit()

    return render_template('query.html', rows=rows, query_range=query_range)

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

@app.route('/users')
def show_users():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute('SELECT username, password_hash, password FROM users')
        users = cur.fetchall()
    return render_template('users.html', users=users)

@app.route('/clear_users', methods=['POST'])
def clear_users():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM users')
        conn.commit()
    flash('所有使用者資料已清空')
    return redirect(url_for('show_users'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
