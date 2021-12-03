from http.server import BaseHTTPRequestHandler
from urllib import parse
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
from numpy import int64
from yahoo_fin.stock_info import get_data, get_live_price
import yahoo_fin.options as ops

import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):

        try:
            # querystring ?ticker=xxx
            dic = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
            ticker = dic["ticker"]

            print(ticker)

            # get current price.
            latestPrice = get_live_price(ticker)

            print(latestPrice)

            # get the historical data.
            three_yrs_ago = datetime.now() - relativedelta(years=3)

            df_prices = get_data(
                ticker, start_date=three_yrs_ago, index_as_date=False)

            # convert date to epoch-secs integer type so that json can handle it.
            df_prices['date'] = [time.mktime(
                t.timetuple()) for t in df_prices.date]
            df_prices['date'] = df_prices['date'].astype(int)
            # df_prices['date'] = df_prices['date'].dt.strftime(
            #     '%Y%m%d%H%M%S')

            # only interested with 2 columns.
            prices_dict = df_prices[[
                "date", "adjclose"]].to_dict('records')

            # get all expiry dates in Jan 01, YYYY format.
            # convert this is MM/DD/YYYY
            friendlyExpirationDates = []
            expiration_dates = ops.get_expiration_dates(ticker)
            for expiration_date in expiration_dates:
                expirationDate = datetime.strptime(
                    expiration_date, '%B %d, %Y')
                friendlyExpirationDates.append(
                    expirationDate.strftime('%m-%d-%Y'))

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            json_string = json.dumps(
                {"ticker": ticker, "price": latestPrice, "expirationDates": friendlyExpirationDates, "historicalPrices": prices_dict})
            self.wfile.write(json_string.encode(encoding='utf_8'))

        except Exception as e:
            print(e)
            self.send_response(400, e)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str(e).encode(encoding='utf_8'))

        return
