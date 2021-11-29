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
            print(self.path, 'goog')
            dic = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
            ticker = dic["ticker"]
            expirationDateStr = dic["expiry"]  # 03/15/2019

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # get current price.
            latestPrice = get_live_price(ticker)

            # todayDateStr = datetime.today().strftime('%d-%m-%Y')
            expirationDate = datetime.strptime(expirationDateStr, '%m/%d/%Y')
            daysLeft = expirationDate - datetime.today()

            options_chain = ops.get_options_chain(ticker, expirationDateStr)
            df = options_chain["puts"]

            # build offset and percentage columns
            df["Offset"] = (df["Strike"] - latestPrice) / latestPrice * 100
            df["Percentage"] = df["Last Price"] / df["Strike"] * 100

            # filter by offset price
            # df_filter = df[(df['Offset'] > -1000) & (df['Offset'] < 100)]
            df_filter = df[(df['Offset'] > -70) & (df['Offset'] < 0)]

            json_string = json.dumps(
                {"ticker": ticker, "daysLeft": daysLeft.days, "price": latestPrice, "put-option-chain": df_filter.to_json()})
            self.wfile.write(json_string.encode(encoding='utf_8'))

        except Exception as e:
            print(e)
            self.send_response(400, e)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str(e).encode(encoding='utf_8'))

        return
