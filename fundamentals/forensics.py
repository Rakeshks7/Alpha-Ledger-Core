import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ForensicAccountant:
    """
    Applies forensic accounting ratios to detect fraud or financial distress.
    """

    @staticmethod
    def calculate_piotroski_f_score(financials: dict) -> int:
        """
        Calculates the 0-9 Piotroski F-Score.
        Higher is better. 7-9 is strong.
        """
        score = 0
        try:
            # Unpack data (Assume standard Yahoo Finance dict structure)
            net_income = financials['net_income']
            op_cash_flow = financials['operating_cashflow']
            roa = financials['return_on_assets']
            long_term_debt = financials['long_term_debt']
            current_ratio = financials['current_ratio']
            shares_outstanding = financials['shares_outstanding']
            gross_margin = financials['gross_margin']
            asset_turnover = financials['asset_turnover']
            
            # --- Profitability ---
            score += 1 if net_income > 0 else 0
            score += 1 if op_cash_flow > 0 else 0
            score += 1 if roa > financials['prev_roa'] else 0
            score += 1 if op_cash_flow > net_income else 0 # Earnings Quality check

            # --- Leverage/Liquidity ---
            score += 1 if long_term_debt < financials['prev_long_term_debt'] else 0
            score += 1 if current_ratio > financials['prev_current_ratio'] else 0
            score += 1 if shares_outstanding <= financials['prev_shares_outstanding'] else 0 # No dilution

            # --- Operating Efficiency ---
            score += 1 if gross_margin > financials['prev_gross_margin'] else 0
            score += 1 if asset_turnover > financials['prev_asset_turnover'] else 0

        except KeyError as e:
            logger.warning(f"Missing data for F-Score: {e}")
            return 0 # Conservative fail
            
        return score

    @staticmethod
    def calculate_beneish_m_score(financials: dict) -> float:
        """
        Calculates Beneish M-Score to detect earnings manipulation.
        Formula: -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + ...
        
        Threshold:
        > -1.78 : High probability of manipulation (RED FLAG)
        < -1.78 : Low probability (SAFE)
        """
        try:
            # Simplified implementation of the 8 variables
            # DSRI: Days Sales in Receivables Index
            dsri = (financials['receivables'] / financials['revenue']) / \
                   (financials['prev_receivables'] / financials['prev_revenue'])
            
            # GMI: Gross Margin Index (If margin is shrinking, manipulation is more likely)
            gmi = financials['prev_gross_margin'] / financials['gross_margin']
            
            # SGI: Sales Growth Index
            sgi = financials['revenue'] / financials['prev_revenue']
            
            # LVGI: Leverage Index
            lvgi = financials['leverage'] / financials['prev_leverage']

            # Standard Coefficients (from M.D. Beneish, 1999)
            m_score = -4.84 + (0.92 * dsri) + (0.528 * gmi) + (0.892 * sgi) + (0.462 * lvgi)
            
            return m_score

        except Exception:
            return 0.0 # Neutral return if data missing

    @staticmethod
    def analyze_health(ticker: str, financials: dict) -> dict:
        f_score = ForensicAccountant.calculate_piotroski_f_score(financials)
        m_score = ForensicAccountant.calculate_beneish_m_score(financials)
        
        verdict = "PASS"
        if f_score < 4: verdict = "WEAK_FUNDAMENTALS"
        if m_score > -1.78: verdict = "POSSIBLE_FRAUD"
        
        return {
            'ticker': ticker,
            'f_score': f_score,
            'm_score': round(m_score, 2),
            'verdict': verdict
        }