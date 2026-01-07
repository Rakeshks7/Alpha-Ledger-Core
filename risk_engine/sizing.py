import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PositionSizer:
    """
    Determines the exact quantity to trade based on volatility targeting.
    Formula:
    Position Size ($) = (Target Risk % * Capital) / (Asset Volatility)
    """

    def __init__(self, target_volatility_annual: float = 0.20):
        """
        Args:
            target_volatility_annual: The annualized volatility we want for this position (e.g., 20%)
        """
        self.target_vol = target_volatility_annual

    def calculate_quantity(self, capital: float, price: float, recent_volatility_daily: float) -> int:
        """
        Calculates number of shares to buy.
        
        Args:
            capital: Account equity available (e.g., 1,000,000 INR)
            price: Current asset price
            recent_volatility_daily: 20-day standard deviation of returns (decimal)
        """
        if recent_volatility_daily <= 0:
            logger.error("Invalid volatility input (<=0). Defaulting to 0 quantity.")
            return 0

        target_daily_vol = self.target_vol / np.sqrt(252)

        vol_scalar = target_daily_vol / recent_volatility_daily

        vol_scalar = min(vol_scalar, 1.0)

        allocation_amount = capital * vol_scalar

        quantity = int(allocation_amount // price)

        logger.info(f"Sizing: Price={price}, DailyVol={recent_volatility_daily:.4f}, Scalar={vol_scalar:.2f} -> Qty: {quantity}")
        return quantity