CREATE TABLE IF NOT EXISTS cabbage_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    item_name TEXT DEFAULT '高麗菜',
    price INTEGER NOT NULL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    password TEXT
);

CREATE TABLE IF NOT EXISTS user_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    query_content TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

