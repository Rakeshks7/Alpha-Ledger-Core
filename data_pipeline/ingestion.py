import yfinance as yf
import pandas as pd
import logging
from typing import List, Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataFetcher:
    """
    Handles the fetching of historical market data from external APIs.
    Currently supports: Yahoo Finance (yfinance)
    """

    def __init__(self, retry_count: int = 3):
        self.retry_count = retry_count

    def fetch_history(self, tickers: List[str], start_date: str, end_date: str, interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Fetches historical data for a list of tickers.
        
        Args:
            tickers: List of ticker symbols (e.g., ['RELIANCE.NS', 'TCS.NS'])
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            interval: Data interval (1d, 1h, 5m)
        
        Returns:
            Dictionary where Key = Ticker and Value = DataFrame
        """
        data_map = {}
        
        if not tickers:
            logger.warning("No tickers provided for fetching.")
            return {}

        logger.info(f"Starting download for {len(tickers)} tickers from {start_date} to {end_date}...")

        try:
            raw_data = yf.download(
                tickers, 
                start=start_date, 
                end=end_date, 
                interval=interval, 
                group_by='ticker', 
                threads=True,
                progress=False 
            )
            
            if len(tickers) == 1:
                data_map[tickers[0]] = self._clean_dataframe(raw_data)
            else:
                for ticker in tickers:
                    df = raw_data[ticker].copy()
                    if not df.empty:
                        data_map[ticker] = self._clean_dataframe(df)
                    else:
                        logger.warning(f"No data found for {ticker}")

            logger.info(f"Successfully downloaded data for {len(data_map)}/{len(tickers)} tickers.")
            return data_map

        except Exception as e:
            logger.error(f"Critical error during bulk download: {e}")
            return {}

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardizes the DataFrame structure."""
        df.columns = [c.lower() for c in df.columns]
        
        df.dropna(how='all', inplace=True)
        
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
            
        return df