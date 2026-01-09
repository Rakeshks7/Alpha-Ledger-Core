import pandas as pd
import logging
from datetime import datetime

# --- Import our Custom Modules ---
from data_pipeline.manager import PipelineManager
from strategies.trend.bollinger_volatility import BollingerTrendStrategy
from risk_engine.compliance import RiskCompliance
from risk_engine.sizing import PositionSizer
from execution.order_manager import OrderManager, Order
from analytics.ledger import TradeLedger
from analytics.tearsheet import TearsheetGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self, ticker, start_date, end_date, initial_capital=1_000_000):
        self.ticker = ticker
        self.start = start_date
        self.end = end_date
        
        # Portfolio State
        self.cash = initial_capital
        self.equity = 0.0
        self.holdings = 0 # Number of shares
        self.portfolio_history = [] # To track value over time
        
        # Initialize Components
        self.data_pipe = PipelineManager()
        self.strategy = BollingerTrendStrategy(params={'window': 20, 'std_dev': 2, 'adx_threshold': 25})
        
        self.compliance = RiskCompliance(config={'max_drawdown_limit': 0.20, 'max_sector_exposure': 1.0})
        self.sizer = PositionSizer(target_volatility_annual=0.20)
        
        self.oms = OrderManager() # Order Management System
        self.ledger = TradeLedger()

    def run(self):
        logger.info(f"--- Starting Backtest for {self.ticker} ---")
        
        # 1. DATA PHASE
        # Fetch and prepare data
        self.data_pipe.run_pipeline([self.ticker], self.start, self.end)
        df = self.data_pipe.get_data(self.ticker)
        
        if df is None or df.empty:
            logger.error("No data found. Aborting.")
            return

        # 2. STRATEGY PHASE (Vectorized Pre-calculation)
        # We calculate signals first, then iterate for execution (Hybrid Approach)
        self.strategy.load_data(df)
        signals_df = self.strategy.generate_signals()
        
        # Merge signals with price data for easy looping
        backtest_df = df.join(signals_df[['signal', 'adx']], rsuffix='_sig')
        
        # 3. SIMULATION LOOP (Day by Day)
        logger.info("Starting Event Loop...")
        
        for date, row in backtest_df.iterrows():
            current_price = row['close']
            high = row['high']
            low = row['low']
            open_p = row['open']
            
            # A. MARKET SIMULATION
            # Send today's OHLC data to Order Manager to see if yesterday's orders fill
            market_snapshot = {
                self.ticker: {'open': open_p, 'high': high, 'low': low, 'close': current_price}
            }
            self.oms.process_orders(market_snapshot)
            
            # Check for newly filled orders and update portfolio
            while self.oms.filled_orders:
                filled_order = self.oms.filled_orders.pop(0) # Process queue
                self._handle_fill(filled_order)

            # B. PORTFOLIO MARK-TO-MARKET
            self.equity = self.cash + (self.holdings * current_price)
            self.portfolio_history.append({'date': date, 'equity': self.equity})

            # C. TRADING LOGIC
            # Only trade if we have no pending orders (simple mode)
            if not self.oms.open_orders:
                signal = row['signal']
                
                # ENTRY LOGIC
                if signal == 1 and self.holdings == 0:
                    self._place_entry_order(current_price, row, "LONG")
                
                elif signal == -1 and self.holdings == 0:
                    pass # We are skipping Short Selling for this simple equity example
                    
                # EXIT LOGIC
                elif self.holdings > 0:
                    # Simple Exit: If Price < Moving Average (or signal flips)
                    # For this demo, let's exit if signal becomes -1 (Bearish)
                    if signal == -1:
                        self._place_exit_order(current_price, "SELL")

        # 4. REPORTING PHASE
        self._generate_report()

    def _place_entry_order(self, price, row_data, side):
        """Calculates size, checks compliance, and places order."""
        
        # 1. Risk Sizing (Volatility Targeting)
        # Calculate daily volatility (approximate using 20-day std dev of % change)
        # In a real app, this would be pre-calculated. We'll use a dummy 1.5% here if missing.
        vol = 0.015 
        
        target_qty = self.sizer.calculate_quantity(self.equity, price, vol)
        
        # 2. Compliance Check
        portfolio_state = {
            'positions': {'dummy': 1} if self.holdings > 0 else {},
            'current_drawdown': 0.0, # Need to calculate dynamic DD
            'total_equity': self.equity
        }
        trade_proposal = {'side': 'ENTRY', 'sector': 'Tech', 'capital_impact': target_qty * price}
        
        check = self.compliance.check_trade_permission(portfolio_state, trade_proposal)
        
        if check['allowed'] and target_qty > 0:
            # Place Market Order (Keep it simple for V1)
            order = Order(symbol=self.ticker, quantity=target_qty, side="BUY", order_type="MARKET")
            self.oms.place_order(order)
            
    def _place_exit_order(self, price, side):
        order = Order(symbol=self.ticker, quantity=self.holdings, side="SELL", order_type="MARKET")
        self.oms.place_order(order)

    def _handle_fill(self, order):
        """Update cash and holdings based on execution."""
        cost = order.quantity * order.fill_price
        
        if order.side == "BUY":
            self.cash -= (cost + order.fees)
            self.holdings += order.quantity
            # Log for tearsheet (Partial logging for entry)
            self.last_entry_price = order.fill_price
            self.last_entry_date = order.fill_time
            
        elif order.side == "SELL":
            self.cash += (cost - order.fees)
            self.holdings -= order.quantity
            
            # Log complete trade
            self.ledger.log_trade(
                ticker=self.ticker,
                entry_date=self.last_entry_date,
                exit_date=order.fill_time,
                entry_price=self.last_entry_price,
                exit_price=order.fill_price,
                quantity=order.quantity,
                side="LONG",
                fees=order.fees # Note: This sums both buy/sell fees in a real engine
            )

    def _generate_report(self):
        # Convert history to Series
        history_df = pd.DataFrame(self.portfolio_history).set_index('date')
        
        # Run Analytics
        reporter = TearsheetGenerator(history_df['equity'], self.ledger)
        reporter.create_report()

# --- ENTRY POINT ---
if __name__ == "__main__":
    # Test on a Nifty 50 stock
    engine = BacktestEngine("RELIANCE.NS", "2020-01-01", "2023-12-31")
    engine.run()