from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradeCost:
    total_cost: float
    breakdown: dict

class CostModel(ABC):
    @abstractmethod
    def calculate(self, price: float, quantity: int, side: str, asset_type: str = "EQUITY") -> TradeCost:
        pass

class IndianTaxModel(CostModel):
    """
    Implements the cost structure for Indian Equity Markets (NSE).
    Includes: Brokerage, STT, Exchange Txn Charges, SEBI Fees, Stamp Duty, GST.
    """
    
    def __init__(self, brokerage_per_order: float = 20.0):
        self.brokerage = brokerage_per_order
    
    def calculate(self, price: float, quantity: int, side: str, asset_type: str = "EQUITY") -> TradeCost:
        """
        Calculates the exact cost of a trade.
        Args:
            side: 'BUY' or 'SELL'
            asset_type: 'EQUITY' (Delivery) or 'INTRADAY'
        """
        turnover = price * quantity
        
        # 1. Brokerage (Flat fee model - e.g., Zerodha/Upstox)
        # Max brokerage is usually capped or flat. Let's assume flat ₹20.
        # But for small trades, it might be lower (0.03% or ₹20 whichever is lower).
        brokerage = min(turnover * 0.0003, self.brokerage)
        
        # 2. STT (Securities Transaction Tax)
        # Equity Delivery: 0.1% on Buy & Sell
        # Intraday: 0.025% on Sell only
        stt = 0.0
        if asset_type == "EQUITY":
            stt = turnover * 0.001
        elif asset_type == "INTRADAY" and side == "SELL":
            stt = turnover * 0.00025
            
        # 3. Exchange Transaction Charges (NSE ~ 0.00325% to 0.00345%)
        # Using 0.00345% as a safe estimate
        exchange_charges = turnover * 0.0000345
        
        # 4. SEBI Turnover Fees (0.0001% or ₹10 per crore)
        sebi_charges = turnover * 0.000001
        
        # 5. Stamp Duty (0.015% on Buy orders only for delivery)
        stamp_duty = 0.0
        if side == "BUY":
            stamp_duty = turnover * 0.00015
            
        # 6. GST (18% on Brokerage + Exchange Charges + SEBI Fees)
        # Note: STT and Stamp Duty are taxes, so no GST on them.
        gst = (brokerage + exchange_charges + sebi_charges) * 0.18
        
        total_tax_and_fees = brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst
        
        return TradeCost(
            total_cost=total_tax_and_fees,
            breakdown={
                "Turnover": turnover,
                "Brokerage": brokerage,
                "STT": stt,
                "Exchange_Charges": exchange_charges,
                "Stamp_Duty": stamp_duty,
                "GST": gst,
                "Total_Charges": total_tax_and_fees
            }
        )