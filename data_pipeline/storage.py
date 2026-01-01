import pandas as pd
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DataStore:
    """
    Manages local storage of market data using Parquet files.
    """
    
    def __init__(self, base_path: str = "data_store"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            logger.info(f"Created data storage directory at: {self.base_path}")

    def save_ticker_data(self, ticker: str, df: pd.DataFrame):
        """Saves a single ticker's dataframe to parquet."""
        if df.empty:
            logger.warning(f"Attempted to save empty data for {ticker}. Skipping.")
            return

        file_path = self._get_file_path(ticker)
        try:
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
            logger.debug(f"Saved {ticker} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save data for {ticker}: {e}")

    def load_ticker_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Loads a single ticker's data from disk."""
        file_path = self._get_file_path(ticker)
        
        if not os.path.exists(file_path):
            logger.warning(f"No data found on disk for {ticker}")
            return None
            
        try:
            df = pd.read_parquet(file_path, engine='pyarrow')
            return df
        except Exception as e:
            logger.error(f"Failed to load data for {ticker}: {e}")
            return None

    def _get_file_path(self, ticker: str) -> str:
        safe_ticker = ticker.replace("^", "").replace(".", "_")
        return os.path.join(self.base_path, f"{safe_ticker}.parquet")