from sqlalchemy import Column, Integer, MetaData, String, Table, Numeric, TIMESTAMP, func

metadata = MetaData()

stock_prices = Table(
    "stock_prices",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("stock_symbol", String(10), nullable=False),  # Not part of primary key

    Column("stock_price", Numeric(10,2), nullable=False),
    Column("timestamp", TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
)