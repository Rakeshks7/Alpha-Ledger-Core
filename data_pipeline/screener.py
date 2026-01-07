from fundamentals.forensics import ForensicAccountant
from macro.regime import MacroRegime
import pandas as pd

class UniverseSelector:
    """
    Filters the entire market down to a shortlist of quality candidates.
    Pipeline:
    All Stocks -> Fundamental Filter (Z-Score/M-Score) -> Macro Check -> Tradable List
    """
    
    def __init__(self, stock_list):
        self.stock_list = stock_list
        self.macro = MacroRegime()
        self.auditor = ForensicAccountant()

    def generate_shortlist(self):
        # 1. Check Macro First
        macro_state = self.macro.get_regime()
        if not macro_state['allow_longs']:
            print("MARKET ALERT: High VIX. Halting new Long positions.")
            return []

        shortlist = []
        
        # 2. Fundamental Audit Loop
        print(f"Auditing {len(self.stock_list)} companies...")
        
        for ticker in self.stock_list:
            # In a real app, you would fetch real fundamental data here.
            # We mock the data for demonstration.
            mock_financials = {
                'net_income': 100, 'operating_cashflow': 120, 'return_on_assets': 0.15,
                'prev_roa': 0.12, 'long_term_debt': 50, 'prev_long_term_debt': 60,
                'receivables': 1000, 'revenue': 5000, 'prev_receivables': 800, 'prev_revenue': 4000,
                'gross_margin': 0.3, 'prev_gross_margin': 0.28,
                'current_ratio': 1.5, 'prev_current_ratio': 1.4,
                'shares_outstanding': 100, 'prev_shares_outstanding': 100,
                'asset_turnover': 1.1, 'prev_asset_turnover': 1.0, 'leverage': 0.5, 'prev_leverage': 0.5
            }
            
            health_report = self.auditor.analyze_health(ticker, mock_financials)
            
            if health_report['verdict'] == "PASS":
                shortlist.append(ticker)
                print(f"[PASS] {ticker} (F-Score: {health_report['f_score']})")
            else:
                print(f"[REJECT] {ticker} - {health_report['verdict']}")

        return shortlist