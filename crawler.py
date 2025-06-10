import requests
import pandas as pd
from io import StringIO

def fetch_cabbage_price():
    url = "https://data.moa.gov.tw/Service/OpenData/FromM/FarmTransData.aspx"

    try:
        response = requests.get(url)
        response.encoding = 'utf-8'

        df = pd.read_csv(StringIO(response.text), sep=",")

        # 印出欄位確認（可移除）
        # print(df.columns)

        # 篩選出高麗菜
        cabbage_df = df[df["作物名稱"].str.contains("高麗菜", na=False)]

        # 按日期排序
        cabbage_df["交易日期"] = pd.to_datetime(cabbage_df["交易日期"])
        latest = cabbage_df.sort_values("交易日期", ascending=False).head(1)

        if not latest.empty:
            date = latest.iloc[0]["交易日期"].strftime("%Y/%m/%d")
            price = round(float(latest.iloc[0]["平均價"]), 1)  # 保留一位小數
            return date, price
        else:
            return None, None

    except Exception as e:
        print("錯誤：", e)
        return None, None
