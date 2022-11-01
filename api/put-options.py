from http.server import BaseHTTPRequestHandler
from urllib import parse
from datetime import datetime
from yahoo_fin.stock_info import get_data, get_live_price
import yahoo_fin.options as ops
import pandas as pd

import json


class handler(BaseHTTPRequestHandler):

    # GET /api/put-options?ticker=xxx%expiry=MM/dd/yyyy
    def do_GET(self):

        try:
            # querystring ?ticker=xxx&expiry=xx-xx-xxxx
            dic = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
            ticker = dic["ticker"]
            expirationDateStr = dic["expiry"]  # 03/15/2019

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # get current price.
            latestPrice = get_live_price(ticker)

            # todayDateStr = datetime.today().strftime('%d-%m-%Y')
            expirationDate = datetime.strptime(expirationDateStr, '%m-%d-%Y')

            options_chain = ops.get_options_chain(ticker, expirationDateStr)
            df = options_chain["puts"]

            # build offset and percentage columns
            df["Offset"] = round(
                (df["Strike"] - latestPrice) / latestPrice * 100, 0)
            df["Percentage"] = round(df["Last Price"] / df["Strike"] * 100, 2)

            # filter by offset price
            df_filter = df[(df['Offset'] > -100) & (df['Offset'] < 0)]

            # filter columns of interest only.
            df_filter.rename(
                columns={"Open Interest": "OpenInterest", "Last Price": "LastPrice", "Implied Volatility": "IV"}, inplace=True)
            jsonData = df_filter[[
                "Strike", "Offset", "Percentage", "LastPrice", "OpenInterest", "IV"]].to_json(orient='records')
            self.wfile.write(jsonData.encode(encoding='utf_8'))

        except Exception as e:
            print(e)
            self.send_response(400, e)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str(e).encode(encoding='utf_8'))

        return
