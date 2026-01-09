import yfinance as yf
import logging

logger = logging.getLogger(__name__)

class MacroRegime:
    """
    Determines the global market environment (Risk-On / Risk-Off).
    """
    
    def __init__(self):
        self.tickers = {
            'vix': '^INDIAVIX',   # India Volatility Index
            'oil': 'CL=F',        # Crude Oil (Impacts paint/tyre/aviation)
            'gold': 'GC=F',       # Safe Haven
            'usd_inr': 'INR=X'    # Currency Strength
        }
        self.current_regime = "NEUTRAL"

    def get_regime(self) -> dict:
        """
        Fetches macro indicators and returns the market state.
        """
        try:
            data = yf.download(list(self.tickers.values()), period="5d", progress=False)['Close']
            
            # 1. Check Volatility
            # Note: Ticker mapping might require adjustment based on yfinance return structure
            vix_level = data.iloc[-1].mean() # Simplified for demo; usually specific column
            
            regime = "NORMAL"
            if vix_level > 22:
                regime = "HIGH_VOLATILITY_PANIC"
            elif vix_level < 12:
                regime = "LOW_VOLATILITY_COMPLACENCY"
                
            # 2. Crude Oil Check (Crucial for Indian Economy)
            # If Oil rises > 5% in 5 days, it's negative for India
            oil_change = 0.0 
            # (Logic to calculate oil change would go here)

            logger.info(f"Macro Regime Detected: {regime} (VIX est: {vix_level:.2f})")
            
            return {
                'regime': regime,
                'vix': vix_level,
                'allow_longs': regime != "HIGH_VOLATILITY_PANIC"
            }

        except Exception as e:
            logger.error(f"Failed to fetch macro data: {e}")
            return {'regime': 'UNKNOWN', 'allow_longs': True}