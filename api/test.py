from urllib import parse
from datetime import datetime
import traceback
from yahoo_fin.stock_info import get_data, get_live_price
import yahoo_fin.options as ops
import pandas as pd
import math

import json


class TestClass:
    def test(self):
        try:
            ticker = "TSLA"
            expirationDateStr = "04-28-2023"  # 03-15-2019

            # self.send_response(200)
            # self.send_header("Content-type", "application/json")
            # self.end_headers()

            # get current price.
            latestPrice = get_live_price(ticker)

            # todayDateStr = datetime.today().strftime('%d-%m-%Y')
            expirationDate = datetime.strptime(expirationDateStr, "%m-%d-%Y")

            options_chain = ops.get_options_chain(ticker, expirationDateStr)
            df = options_chain["puts"]

            print(df.tail(5))

            # build offset and percentage columns
            df["Offset"] = round((df["Strike"] - latestPrice) / latestPrice * 100, 0)
            df["Percentage"] = round(df["Last Price"] / df["Strike"] * 100, 2)

            # filter by offset price
            df_filter = df[(df["Offset"] > -100) & (df["Offset"] < 0)]

            # filter columns of interest only.
            df_filter.rename(
                columns={
                    "Open Interest": "OpenInterest",
                    "Last Price": "LastPrice",
                    "Implied Volatility": "IV",
                },
                inplace=True,
            )

            # build the probability column.
            days_left = (expirationDate - datetime.now()).days
            df_filter["Prob"] = df_filter.apply(
                self.calculate,
                args=(
                    latestPrice,
                    days_left,
                ),
                axis=1,
            )

            jsonData = df_filter[
                [
                    "Strike",
                    "Offset",
                    "Percentage",
                    "Bid",
                    "Ask",
                    "LastPrice",
                    "Volume",
                    "OpenInterest",
                    "IV",
                    "Prob",
                ]
            ].to_json(orient="records")

            # self.wfile.write(jsonData.encode(encoding="utf_8"))

        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            # self.send_response(400, tb)
            # self.send_header("Content-type", "application/json")
            # self.end_headers()
            # self.wfile.write(str(e).encode(encoding="utf_8"))

        return

    def calculate(self, row, currPrice, days):
        print(row)
        strikePrice = row["Strike"]
        iv = float(row["IV"].strip("%")) / 100
        vt = iv * math.sqrt(days)
        impg = math.log(strikePrice / currPrice)
        d1 = impg / vt
        y = math.floor(1 / (1 + 0.2316419 * abs(d1)) * 100000) / 100000
        z = math.floor(0.3989423 * math.exp(-((d1 * d1) / 2)) * 100000) / 100000
        y5 = 1.330274 * math.pow(y, 5)
        y4 = 1.821256 * math.pow(y, 4)
        y3 = 1.781478 * math.pow(y, 3)
        y2 = 0.356538 * math.pow(y, 2)
        y1 = 0.3193815 * y
        x = 1 - z * (y5 - y4 + y3 - y2 + y1)
        x = math.floor(x * 100000) / 100000

        if d1 < 0:
            x = 1 - x

        pbelow = math.floor(x * 1000) / 10  # for put
        pabove = math.floor((1 - x) * 1000) / 10  # for call
        return pbelow


myObj = TestClass()
myObj.test()
