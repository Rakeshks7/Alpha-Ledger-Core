import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """
    Calculates professional-grade risk metrics.
    Assumes input is a pandas Series of daily returns.
    """

    @staticmethod
    def calculate_cagr(total_return: float, years: float) -> float:
        if years <= 0: return 0.0
        # Formula: (End/Start)^(1/n) - 1
        return (1 + total_return) ** (1 / years) - 1

    @staticmethod
    def calculate_sharpe(daily_returns: pd.Series, risk_free_rate: float = 0.05) -> float:
        """
        Sharpe Ratio = (Rp - Rf) / sigma_p
        """
        if daily_returns.std() == 0: return 0.0
        
        # De-annualize risk free rate
        rf_daily = risk_free_rate / 252.0
        excess_returns = daily_returns - rf_daily
        
        # Annualized Sharpe
        return np.sqrt(252) * excess_returns.mean() / daily_returns.std()

    @staticmethod
    def calculate_sortino(daily_returns: pd.Series, target_return: float = 0.0) -> float:
        """
        Sortino Ratio = (Rp - Rf) / sigma_downside
        Only penalizes negative volatility.
        """
        downside_returns = daily_returns[daily_returns < target_return]
        downside_std = downside_returns.std()
        
        if downside_std == 0: return 0.0
        
        # Annualized Sortino
        return np.sqrt(252) * daily_returns.mean() / downside_std

    @staticmethod
    def calculate_max_drawdown(portfolio_values: pd.Series) -> float:
        """
        Calculates the deepest peak-to-valley decline.
        Returns a negative float (e.g., -0.15 for 15% drop).
        """
        # Calculate running maximum
        rolling_max = portfolio_values.cummax()
        drawdown = (portfolio_values - rolling_max) / rolling_max
        return drawdown.min()

    @staticmethod
    def calculate_win_rate(trades_df: pd.DataFrame) -> float:
        if trades_df.empty: return 0.0
        winning_trades = trades_df[trades_df['pnl'] > 0]
        return len(winning_trades) / len(trades_df)