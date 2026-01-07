import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RiskCompliance:
    """
    The 'CFO' of the system. Validates if a trade is safe to execute
    based on portfolio constraints.
    """

    def __init__(self, config: Dict):
        """
        Args:
            config: Dict containing limits.
            Example:
            {
                'max_drawdown_limit': 0.15,  # Pause trading if down 15%
                'max_sector_exposure': 0.30, # Max 30% of capital in one sector
                'max_positions': 10          # Max 10 active trades
            }
        """
        self.max_dd = config.get('max_drawdown_limit', 0.15)
        self.max_sector = config.get('max_sector_exposure', 0.30)
        self.max_pos = config.get('max_positions', 10)

    def check_trade_permission(self, current_portfolio: Dict, proposed_trade: Dict) -> Dict:
        """
        Validates a proposed trade against hard limits.
        
        Returns:
            {'allowed': bool, 'reason': str}
        """
        
        active_positions = len(current_portfolio.get('positions', {}))
        if active_positions >= self.max_pos and proposed_trade['side'] == 'ENTRY':
            msg = f"REJECTED: Max positions reached ({active_positions}/{self.max_pos})"
            logger.warning(msg)
            return {'allowed': False, 'reason': msg}

        current_dd = current_portfolio.get('current_drawdown', 0.0)
        if current_dd > self.max_dd:
            msg = f"REJECTED: Portfolio in critical drawdown ({current_dd:.1%} > {self.max_dd:.1%}). Trading Halted."
            logger.critical(msg)
            return {'allowed': False, 'reason': msg}

        target_sector = proposed_trade.get('sector')
        if target_sector:
            current_sector_alloc = current_portfolio.get('sector_allocation', {}).get(target_sector, 0.0)
            trade_impact = proposed_trade.get('capital_impact', 0.0)
            total_capital = current_portfolio.get('total_equity', 1.0)
            
            new_exposure = current_sector_alloc + (trade_impact / total_capital)
            
            if new_exposure > self.max_sector:
                msg = f"REJECTED: Sector Limit Exceeded for {target_sector}. New: {new_exposure:.1%}, Limit: {self.max_sector:.1%}"
                logger.warning(msg)
                return {'allowed': False, 'reason': msg}

        return {'allowed': True, 'reason': 'Compliance Checks Passed'}