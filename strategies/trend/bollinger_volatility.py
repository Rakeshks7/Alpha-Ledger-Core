import pandas as pd
import numpy as np

class BollingerTrendStrategy(BaseStrategy):
    """
    Real-Life Logic:
    1. Calculate Bollinger Bands.
    2. Filter: Check ADX (Trend Strength) to avoid 'whipsaws' in ranging markets.
    3. Signal: Long if Close > Upper Band AND ADX > Threshold.
    """

    def __init__(self, params=None):
        defaults = {
            'window': 20,
            'std_dev': 2.0,
            'adx_threshold': 25,  
            'adx_window': 14
        }
        if params:
            defaults.update(params)

        super().__init__("Bollinger_ADX_Trend", defaults)

    def _calculate_adx(self, df: pd.DataFrame, window: int) -> pd.Series:
        """Helper to calculate ADX for regime filtering."""
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['close'].shift(1))
        df['tr3'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

        df['up_move'] = df['high'] - df['high'].shift(1)
        df['down_move'] = df['low'].shift(1) - df['low']

        df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
        df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)

        tr_smooth = df['tr'].rolling(window).sum()
        plus_di = 100 * (df['plus_dm'].rolling(window).sum() / tr_smooth)
        minus_di = 100 * (df['minus_dm'].rolling(window).sum() / tr_smooth)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window).mean()

        df.drop(['tr1', 'tr2', 'tr3', 'tr', 'up_move', 'down_move', 'plus_dm', 'minus_dm'], axis=1, inplace=True)
        return adx

    def generate_signals(self) -> pd.DataFrame:
        if self.data is None:
            raise ValueError("Data not loaded.")

        df = self.data.copy()
        p = self.params

        df['ma'] = df['close'].rolling(window=p['window']).mean()
        df['std'] = df['close'].rolling(window=p['window']).std()
        df['upper_band'] = df['ma'] + (df['std'] * p['std_dev'])
        df['lower_band'] = df['ma'] - (df['std'] * p['std_dev'])

        df['adx'] = self._calculate_adx(df, p['adx_window'])

        df['signal'] = 0

        long_condition = (df['close'] > df['upper_band']) & (df['adx'] > p['adx_threshold'])

        short_condition = (df['close'] < df['lower_band']) & (df['adx'] > p['adx_threshold'])

        df.loc[long_condition, 'signal'] = 1
        df.loc[short_condition, 'signal'] = -1


        self.signals = df[['signal', 'close', 'upper_band', 'lower_band', 'adx']]
        return self.signals