from abc import ABC, abstractmethod
import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    Enforces a strict interface for data ingestion and signal generation.
    """

    def __init__(self, name: str, params: Dict[str, Any]):
        """
        Args:
            name: Unique name for the strategy instance.
            params: Dictionary of parameters (e.g., {'window': 20, 'std_dev': 2})
        """
        self.name = name
        self.params = params
        self.data = None
        self.signals = None

    def load_data(self, data: pd.DataFrame):
        """
        Ingests the standardized data from the pipeline.
        Expected format: Index=Date, Columns=[open, high, low, close, volume]
        """
        if data.empty:
            logger.error(f"Strategy {self.name} received empty data.")
            return
        
        self.data = data.copy()
        logger.info(f"Strategy {self.name} loaded {len(self.data)} rows of data.")

    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        """
        CORE LOGIC: Must return a DataFrame with at least a 'signal' column.
        Signal convention:
        +1: Long
        -1: Short
         0: Neutral/Exit
        """
        pass

    def get_analysis(self) -> Dict:
        """
        Optional: Returns metadata about the run (e.g., indicators used).
        """
        return {"params": self.params}