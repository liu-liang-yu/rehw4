CREATE TABLE IF NOT EXISTS cabbage_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    item_name TEXT DEFAULT '高麗菜',
    price INTEGER NOT NULL,
    source TEXT
);