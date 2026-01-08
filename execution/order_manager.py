from dataclasses import dataclass, field
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import logging

# Import the modules we built previously
from .slippage_model import SlippageModel
from .transaction_cost import IndianTaxModel

logger = logging.getLogger(__name__)

@dataclass
class Order:
    symbol: str
    quantity: int
    side: str          # 'BUY' or 'SELL'
    order_type: str    # 'MARKET', 'LIMIT', 'STOP'
    price: Optional[float] = None  # Required for LIMIT/STOP
    
    # Internal State
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: str = 'OPEN'           # OPEN, FILLED, CANCELLED, REJECTED
    fill_price: float = 0.0
    fill_time: Optional[datetime] = None
    fees: float = 0.0

class OrderManager:
    """
    Simulates the Exchange Matching Engine.
    Holds open orders and checks if market price action triggers a fill.
    """
    
    def __init__(self):
        self.open_orders: List[Order] = []
        self.filled_orders: List[Order] = []
        
        # Initialize helper engines
        self.slippage_engine = SlippageModel(base_bps=5.0)
        self.cost_engine = IndianTaxModel()

    def place_order(self, order: Order) -> str:
        """
        Receives a new order and adds it to the book.
        """
        if order.quantity <= 0:
            order.status = 'REJECTED'
            logger.warning(f"Order {order.id} rejected: Invalid Quantity")
            return order.id

        logger.info(f"Order Placed: {order.side} {order.quantity} {order.symbol} @ {order.order_type}")
        self.open_orders.append(order)
        return order.id

    def process_orders(self, market_data: Dict[str, Dict]):
        """
        The Core Loop: Checks all open orders against the current candle's High/Low.
        
        Args:
            market_data: Dict containing current candle info for symbols.
                         e.g. {'RELIANCE': {'open': 2500, 'high': 2520, 'low': 2490, 'close': 2510}}
        """
        for order in self.open_orders[:]: # Copy list to safely modify during iteration
            
            ticker_data = market_data.get(order.symbol)
            if not ticker_data:
                continue

            current_price = ticker_data['close']
            high_price = ticker_data['high']
            low_price = ticker_data['low']
            
            is_fillable = False
            execution_price = 0.0

            # --- LOGIC: Check if Order fills ---
            
            # 1. MARKET ORDER: Fills immediately at Close (adjusted for slippage)
            if order.order_type == 'MARKET':
                is_fillable = True
                # Simulate slippage on the 'close' price
                execution_price = self.slippage_engine.calculate_fill_price(
                    current_price, order.side
                )

            # 2. LIMIT BUY: Fills if Market LOW <= Limit Price
            elif order.order_type == 'LIMIT' and order.side == 'BUY':
                if low_price <= order.price:
                    is_fillable = True
                    # Fill at Limit Price (guaranteed price, uncertain fill) 
                    # OR fill at Open if Open < Limit (Gap Down)
                    execution_price = min(order.price, ticker_data['open'])

            # 3. LIMIT SELL: Fills if Market HIGH >= Limit Price
            elif order.order_type == 'LIMIT' and order.side == 'SELL':
                if high_price >= order.price:
                    is_fillable = True
                    # Fill at Limit or Open if Open > Limit (Gap Up)
                    execution_price = max(order.price, ticker_data['open'])

            # 4. STOP LOSS (Trigger): Becomes Market Order when triggered
            elif order.order_type == 'STOP':
                # Stop Buy (e.g. Breakout): Trigger if High >= Stop Price
                if order.side == 'BUY' and high_price >= order.price:
                    is_fillable = True
                    execution_price = self.slippage_engine.calculate_fill_price(order.price, 'BUY')
                
                # Stop Sell (e.g. Stop Loss): Trigger if Low <= Stop Price
                elif order.side == 'SELL' and low_price <= order.price:
                    is_fillable = True
                    # In a crash, you might fill well below your stop. 
                    # We simulate filling at the Stop Price + Slippage
                    execution_price = self.slippage_engine.calculate_fill_price(order.price, 'SELL')

            # --- EXECUTION ---
            if is_fillable:
                self._execute_fill(order, execution_price)

    def _execute_fill(self, order: Order, price: float):
        """
        Finalizes the trade, calculates taxes, and moves order to 'filled'.
        """
        # 1. Calculate Costs
        cost_report = self.cost_engine.calculate(price, order.quantity, order.side)
        
        # 2. Update Order State
        order.status = 'FILLED'
        order.fill_price = price
        order.fees = cost_report.total_cost
        order.fill_time = datetime.now() # In backtest, use simulation time
        
        # 3. Move to filled list
        self.open_orders.remove(order)
        self.filled_orders.append(order)
        
        logger.info(f"FILLED: {order.side} {order.symbol} @ {price:.2f} (Fees: {order.fees:.2f})")