import yfinance as yf
from datetime import datetime, timedelta
from decimal import Decimal


def fetch_low_yfinance_on_date(
    ticker: str,
    date: datetime,          # z.B. datetime(2025, 6, 6)
    interval: str = "1d",
) -> Decimal:
    """
    Description:
        Fetch the low price for the given ticker on the specified date.
        If no data is found for that date, retry with date+1, up to 7
        consecutive days.
    Input:
        ticker   -- the stock ticker symbol
        date     -- the starting date (datetime)
        interval -- data interval for yfinance (default "1d")
    Output:
        Decimal low price for the first date with data,
        or raises ValueError if none found within 7 days.
    """
    current_date = date
    # Try up to 7 days in a row
    for attempt in range(7):
        # build yfinance date strings
        start_str = current_date.strftime("%Y-%m-%d")
        end_str = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

        tk_obj = yf.Ticker(ticker)
        hist = tk_obj.history(start=start_str, end=end_str, interval=interval)
        print("hist: ", hist)

        if not hist.empty:
            # return the low of that day
            low = hist["Low"].iloc[0]
            return Decimal(str(low))

        # no data for this date → try next day
        current_date += timedelta(days=1)

    # after 7 attempts still nothing → error
    raise ValueError(
        f"No low price for {ticker} found between "
        f"{date.strftime('%Y-%m-%d')} and "
        f"{(date + timedelta(days=6)).strftime('%Y-%m-%d')}."
    )
