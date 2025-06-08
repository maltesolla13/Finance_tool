import yfinance as yf


def fetch_low_yfinance(ticker: str, period: str = "6mo", interval: str = "1d"):
    """
    Holt für das gegebene Ticker-Symbol die Historie und
    gibt eine Liste von {date, price_low}-Dicts zurück.
    """
    tk = yf.Ticker(ticker)
    hist = tk.history(period=period, interval=interval)

    # hist ist ein pandas.DataFrame mit Index = DatetimeIndex
    return [
        {"date": idx.strftime("%Y-%m-%d"), "price_low": row["Low"]}
        for idx, row in hist.iterrows()
    ]
