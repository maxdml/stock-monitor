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

# Then let's write a function that fetches stock prices from Yahoo Finance.
# We annotate this function with `@DBOS.step` so we can call it from a durable workflow later on.
@DBOS.step()
def fetch_stock_price(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    if data.empty:
        raise ValueError("No stock data found for the symbol.")
    print(f"Stock price for {symbol} is {data['Close'].iloc[0]}")
    return data['Close'].iloc[0]

# Next, let's write a function that saves stock prices to a Postgres database.
@DBOS.transaction()
def save_to_db(symbol, price):
    DBOS.sql_session.execute(stock_prices.insert().values(stock_symbol=symbol, stock_price=price))

# Then, let's write a scheduled job that fetches stock prices for a list of symbols every minute
# The @DBOS.scheduled() decorator tells DBOS to run this function on a cron schedule.
# The @DBOS.workflow() decorator tells DBOS to run this function as a reliable workflow,
# so it runs exactly-once per minute and you'll never record a duplicate.
@DBOS.scheduled('* * * * *')
@DBOS.workflow()
def fetch_stock_prices_workflow(scheduled_time: datetime, actual_time: datetime):
    symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA']
    for symbol in symbols:
        price = fetch_stock_price(symbol)
        save_to_db(symbol, price)
        # If wanted, push to cloudwatch using boto3

# Finally, in our main function, let's launch DBOS, then sleep the main thread forever
# while the background threads run.
if __name__ == "__main__":
    DBOS.launch()
    threading.Event().wait()

# To deploy this app to the cloud as a persistent cron job, run `dbos-cloud app deploy`