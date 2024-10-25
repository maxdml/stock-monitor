# Stock prices

# This app uses DBOS to periodically fetch stock prices from Yahoo Finance, store them into Postgres
# and display them using Streamlit.

# This part of the app uses Streamlit for data visualization.
# The ingestion code using DBOS Transact is in main.py.
# We separate the Streamlit script from the DBOS ingestion code
# because Streamlit re-runs the entire script every time it's viewed.

# First, let's do imports and configure Streamlit with a title and some custom CSS.

import dbos
import pandas as pd
import streamlit as st
import plotly.express as px
from schema import stock_prices
from sqlalchemy import create_engine, desc, select

st.set_page_config(page_title="Stock Prices", page_icon=":chart_with_upwards_trend:")

st.markdown(
    """
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
        </style>
        """,
    unsafe_allow_html=True,
)
st.title("Stock Prices")
st.markdown(
    "This app uses DBOS to fetch stock prices from Yahoo Finance, store them into Postgres, and display them using Streamlit."
)

# Then, let's load database connection information from dbos-config.yaml
# and use it to create a database connection using sqlalchemy.

def load_data():
    database_url = dbos.get_dbos_database_url()
    engine = create_engine(database_url)
    query = (
        select(stock_prices)
        .order_by(desc(stock_prices.c.timestamp))
        .limit(10000)
    )
    df = pd.read_sql(query, engine)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.drop(columns=["id"])

df = load_data()

# Create a sidebar with a dropdown filter for stock symbols
with st.sidebar:
    st.header("Filters")
    stock_symbols = ["All"] + df['stock_symbol'].unique().tolist()
    stock_symbol_filter = st.selectbox(
        "Select Stock Symbol",
        options=stock_symbols,
        index=0 # Select "All" by default
    )
if stock_symbol_filter == "All":
    filtered_df = df
else:
    filtered_df = df[df['stock_symbol'] == stock_symbol_filter]

# Calculate the maximum stock price in the DataFrame
max_stock_price = filtered_df['stock_price'].max()
# Define a buffer above the maximum value for the y-axis limit
buffer = 0.05 * max_stock_price  # 5% above the maximum
y_max_limit = max_stock_price + buffer

# Now let's group the stock prices by stock symbol and plot them using Plotly Express.
st.write("### Stock Prices by Symbol")
fig = px.line(
    filtered_df, x='timestamp', y='stock_price', color='stock_symbol',
    markers=True, title='Stock Prices by Symbol'
)

# Update the y-axis limit
fig.update_yaxes(range=[0, y_max_limit])

# Display the plot in Streamlit
st.plotly_chart(fig)