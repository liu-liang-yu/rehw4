from crawler import fetch_cabbage_price
from database import insert_price

date, price = fetch_cabbage_price()

if date and price:
    insert_price(date, price)
    print(f"成功寫入：{date} 的高麗菜價格 {price}")
else:
    print("沒抓到資料")

