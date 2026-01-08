import numpy as np
import logging

logger = logging.getLogger(__name__)

class SlippageModel:
    """
    Simulates the market impact of placing an order.
    """
    
    def __init__(self, base_bps: float = 5.0):
        """
        Args:
            base_bps: Base basis points of slippage (5 bps = 0.05%)
        """
        self.base_slippage = base_bps / 10000.0

    def calculate_fill_price(self, target_price: float, side: str, volatility: float = None) -> float:
        """
        Adjusts the execution price to account for slippage.
        
        Args:
            volatility: (Optional) Recent volatility (e.g., ATR / Price). 
                        If provided, slippage scales with volatility.
        """
        
        # Base Slippage
        impact = self.base_slippage
        
        # Volatility Penalty (Advanced)
        # If volatility is high (>1%), we double the slippage estimate
        if volatility and volatility > 0.01:
            impact *= 2.0
            
        # Apply impact
        # Buy Orders fill HIGHER than target
        # Sell Orders fill LOWER than target
        if side == "BUY":
            fill_price = target_price * (1 + impact)
        else: # SELL
            fill_price = target_price * (1 - impact)
            
        logger.debug(f"Slippage Calc: Target {target_price} -> Fill {fill_price} (Impact: {impact:.4%})")
        return fill_price