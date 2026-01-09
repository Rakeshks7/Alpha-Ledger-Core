import pandas as pd
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class TradeLedger:
    """
    Records all completed trades and maintains the audit trail.
    """
    
    def __init__(self):
        self.trades: List[Dict] = []

    def log_trade(self, 
                  ticker: str, 
                  entry_date: datetime, 
                  exit_date: datetime, 
                  entry_price: float, 
                  exit_price: float, 
                  quantity: int, 
                  side: str,
                  fees: float = 0.0):
        
        # Calculate PnL
        # Long: (Exit - Entry) * Qty - Fees
        # Short: (Entry - Exit) * Qty - Fees
        
        gross_pnl = (exit_price - entry_price) * quantity if side == "LONG" else (entry_price - exit_price) * quantity
        net_pnl = gross_pnl - fees
        return_pct = (net_pnl / (entry_price * quantity)) if entry_price > 0 else 0

        record = {
            'ticker': ticker,
            'side': side,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'fees': fees,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'return_pct': return_pct
        }
        
        self.trades.append(record)
        
    def get_ledger_df(self) -> pd.DataFrame:
        """Returns the ledger as a standardized DataFrame."""
        if not self.trades:
            return pd.DataFrame()
            
        df = pd.DataFrame(self.trades)
        df['entry_date'] = pd.to_datetime(df['entry_date'])
        df['exit_date'] = pd.to_datetime(df['exit_date'])
        return df