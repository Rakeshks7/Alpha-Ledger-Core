import pandas as pd
import os
import logging
from typing import List, Dict

class MarketDataFetcher:
    def fetch_history(self, tickers: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        logging.info(f"Simulating fetching history for {tickers} from {start_date} to {end_date}")
        data_map = {}
        for ticker in tickers:
            dates = pd.date_range(start=start_date, end=end_date, freq='B') 
            df = pd.DataFrame({
                'Date': dates,
                'Open': [100 + i for i in range(len(dates))],
                'High': [105 + i for i in range(len(dates))],
                'Low': [98 + i for i in range(len(dates))],
                'Close': [102 + i for i in range(len(dates))],
                'Volume': [100000 + i * 1000 for i in range(len(dates))]
            })
            df.set_index('Date', inplace=True)
            data_map[ticker] = df
        return data_map

class DataStore:
    def __init__(self, base_path: str = "data_store"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save_ticker_data(self, ticker: str, df: pd.DataFrame):
        file_path = os.path.join(self.base_path, f"{ticker.replace('.', '_')}.csv")
        df.to_csv(file_path)
        logging.info(f"Saved data for {ticker} to {file_path}")

    def load_ticker_data(self, ticker: str) -> pd.DataFrame:
        file_path = os.path.join(self.base_path, f"{ticker.replace('.', '_')}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
            logging.info(f"Loaded data for {ticker} from {file_path}")
            return df
        else:
            logging.warning(f"No data found for {ticker} at {file_path}")
            return pd.DataFrame()



from typing import List
import logging

logger = logging.getLogger(__name__)

class PipelineManager:
    """
    High-level controller to manage data ingestion and storage.
    """

    def __init__(self, data_path: str = "data_store"):
        self.fetcher = MarketDataFetcher()
        self.store = DataStore(base_path=data_path)

    def run_pipeline(self, tickers: List[str], start_date: str, end_date: str):
        """
        Full workflow: Fetch -> Clean -> Save
        """
        logger.info("Starting Data Pipeline...")

        data_map = self.fetcher.fetch_history(tickers, start_date, end_date)

        for ticker, df in data_map.items():
            self.store.save_ticker_data(ticker, df)

        logger.info("Pipeline Execution Completed.")

    def get_data(self, ticker: str):
        """Retrieve data for a strategy."""
        return self.store.load_ticker_data(ticker)

if __name__ == "__main__":
    universe = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "^NSEI"]

    pipeline = PipelineManager()

    pipeline.run_pipeline(universe, "2020-01-01", "2023-12-31")

    df = pipeline.get_data("RELIANCE.NS")
    print(f"\nLoaded RELIANCE Data Head:\n{df.head()}")