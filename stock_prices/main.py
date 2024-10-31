# Welcome to DBOS!

# This is a DBOS port of the stock prices monitoring app showcased in
# https://python.plainenglish.io/building-and-deploying-a-stock-price-monitoring-system-with-aws-lambda-rds-postgresql-and-4abef0b3968a

# It periodically fetches stock prices from Yahoo Finance and stores them in a Postgres database.

# First, let's do imports, and initialize DBOS.

from dbos import DBOS
from schema import stock_prices
import yfinance as yf
from twilio.rest import Client
import os
import pytz
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
    DBOS.logger.info(f"Stock price for {symbol} is {data['Close'].iloc[0]}")
    return data['Close'].iloc[0]

# Next, let's write a function that saves stock prices to a Postgres database.
@DBOS.transaction()
def save_to_db(symbol, price):
    DBOS.sql_session.execute(stock_prices.insert().values(stock_symbol=symbol, stock_price=price))

# Now, let's write a function that will send a SMS to our number whenever a stock price goes above a certain threshold.
# We will use Twilio for this. You can sign up for a free Twilio account at https://www.twilio.com/try-twilio
# We will use environment variables to store our Twilio account SID, auth token, phone number, and our own phone number.
# See dbos-config.yaml
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
my_phone_number = os.environ.get('MY_PHONE_NUMBER')
# Define a list of stock symbols to monitor and their respective alert thresholds.
symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'TSLA', 'NVDA']
tresholds = {'MSFT': 1000 } # Time to sell ;)
@DBOS.step()
def send_sms(symbol, price):
    if symbol in tresholds and price > tresholds[symbol]:
        client = Client(twilio_account_sid, twilio_auth_token)
        message = client.messages.create(
            body=f"{symbol} stock price is {price}.",
            from_=twilio_phone_number,
            to=my_phone_number
        )
        DBOS.logger.info(f"SMS sent: {message.sid}")

# Then, let's write a scheduled job that fetches stock prices for a list of symbols every minute (except weekends).
# The @DBOS.scheduled() decorator tells DBOS to run this function on a cron schedule.
# The @DBOS.workflow() decorator tells DBOS to run this function as a reliable workflow,
# so it runs exactly-once per minute and you'll never record a duplicate.
@DBOS.scheduled('* * * * 1-5')
@DBOS.workflow()
def fetch_stock_prices_workflow(scheduled_time: datetime, actual_time: datetime):
    if is_trading_hours():
        for symbol in symbols:
            price = fetch_stock_price(symbol)
            save_to_db(symbol, price)
            send_sms(symbol, price)

# Finally, in our main function, let's launch DBOS, then sleep the main thread forever
# while the background threads run.
if __name__ == "__main__":
    DBOS.launch()
    threading.Event().wait()
# To deploy this app to the cloud as a persistent cron job, run `dbos-cloud app deploy`


### HELPERS

# A utility function to check whether we are in trading hours
def is_trading_hours():
    # Define the timezone for the stock exchange (Eastern Time)
    eastern = pytz.timezone('America/New_York')
    # Get the current time in Eastern Time
    now = datetime.now(eastern)
    if now.hour < 9 or (now.hour == 9 and now.minute < 30):  # Before 9:30 AM
        return False
    if now.hour > 16 or (now.hour == 16 and now.minute > 0):  # After 4:00 PM
        return False
    return True