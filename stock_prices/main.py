# Welcome to DBOS!

# This is a DBOS port of the stock prices monitoring app showcased in
# https://python.plainenglish.io/building-and-deploying-a-stock-price-monitoring-system-with-aws-lambda-rds-postgresql-and-4abef0b3968a

# It periodically fetches stock prices from Yahoo Finance and stores them in a Postgres database.

# First, let's do imports, and initialize DBOS.

from dbos import DBOS

from schema import stock_prices

import yfinance as yf
import datetime
import threading

DBOS()

# Configure a job to periodically fetch stock prices
@DBOS.scheduled('* * * * *')
@DBOS.workflow()
def fetch_stock_prices_workflow(scheduled_time: datetime, actual_time: datetime):
    symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA']
    for symbol in symbols:
        price = fetch_stock_price(symbol)
        save_to_db(symbol, price)
        # If wanted, push to cloudwatch using boto3

@DBOS.step()
def fetch_stock_price(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    if data.empty:
        raise ValueError("No stock data found for the symbol.")
    print(data)
    return data['Close'][0]

@DBOS.transaction()
def save_to_db(symbol, price):
    DBOS.sql_session.execute(stock_prices.insert().values(stock_symbol=symbol, stock_price=price))

# Finally, in our main function, let's launch DBOS, then sleep the main thread forever
# while the background threads run.
if __name__ == "__main__":
    DBOS.launch()
    threading.Event().wait()

# To deploy this app to DBOS Cloud:
# - "npm i -g @dbos-inc/dbos-cloud@latest" to install the Cloud CLI (requires Node)
# - "dbos-cloud app deploy" to deploy your app
# - Deploy outputs a URL--visit it to see your app!


# To run this app locally:
# - Make sure you have a Postgres database to connect to
# - "dbos migrate" to set up your database tables
# - "dbos start" to start the app
# - Visit localhost:8000 to see your app!
