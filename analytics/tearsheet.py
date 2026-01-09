import pandas as pd
from .metrics import PerformanceMetrics
from .ledger import TradeLedger

class TearsheetGenerator:
    """
    Generates a professional performance report.
    """
    
    def __init__(self, portfolio_series: pd.Series, ledger: TradeLedger):
        self.equity_curve = portfolio_series
        self.ledger = ledger

    def create_report(self):
        """
        Prints a structured report to the console.
        """
        # Prepare Data
        daily_returns = self.equity_curve.pct_change().dropna()
        trades_df = self.ledger.get_ledger_df()
        
        # Calculate Metrics
        total_return = (self.equity_curve.iloc[-1] / self.equity_curve.iloc[0]) - 1
        days = (self.equity_curve.index[-1] - self.equity_curve.index[0]).days
        years = days / 365.25
        
        cagr = PerformanceMetrics.calculate_cagr(total_return, years)
        sharpe = PerformanceMetrics.calculate_sharpe(daily_returns)
        sortino = PerformanceMetrics.calculate_sortino(daily_returns)
        max_dd = PerformanceMetrics.calculate_max_drawdown(self.equity_curve)
        win_rate = PerformanceMetrics.calculate_win_rate(trades_df)
        
        # Generate Output
        print("\n" + "="*40)
        print("   ALPHA LEDGER - PERFORMANCE REPORT")
        print("="*40)
        
        print(f"\n--- Return Metrics ---")
        print(f"Total Return : {total_return:.2%}")
        print(f"CAGR         : {cagr:.2%}")
        
        print(f"\n--- Risk Metrics ---")
        print(f"Volatility   : {daily_returns.std() * (252**0.5):.2%}")
        print(f"Sharpe Ratio : {sharpe:.2f}")
        print(f"Sortino Ratio: {sortino:.2f}")
        print(f"Max Drawdown : {max_dd:.2%}")
        
        print(f"\n--- Trade Analysis ---")
        if not trades_df.empty:
            print(f"Total Trades : {len(trades_df)}")
            print(f"Win Rate     : {win_rate:.2%}")
            print(f"Avg Profit   : ₹{trades_df[trades_df['net_pnl']>0]['net_pnl'].mean():.2f}")
            print(f"Avg Loss     : ₹{trades_df[trades_df['net_pnl']<0]['net_pnl'].mean():.2f}")
            print(f"Profit Factor: {abs(trades_df[trades_df['net_pnl']>0]['net_pnl'].sum() / trades_df[trades_df['net_pnl']<0]['net_pnl'].sum()):.2f}")
        else:
            print("No trades recorded.")
            
        print("="*40 + "\n")