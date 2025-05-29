"""
Real ICT (Inner Circle Trading) Analysis System
"""

import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RealICTAnalyzer:
    def __init__(self):
        self.symbol = "GC=F"  # Gold futures
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        
    def get_multi_timeframe_data(self):
        """Get data from multiple timeframes"""
        data = {}
        try:
            ticker = yf.Ticker(self.symbol)
            
            # Get different timeframe data
            data['1m'] = ticker.history(period="1d", interval="1m")
            data['5m'] = ticker.history(period="5d", interval="5m")
            data['15m'] = ticker.history(period="5d", interval="15m")
            data['1h'] = ticker.history(period="30d", interval="1h")
            data['4h'] = ticker.history(period="60d", interval="1h")  # Resample to 4h
            data['1d'] = ticker.history(period="1y", interval="1d")
            
            # Resample 1h to 4h
            if not data['4h'].empty:
                data['4h'] = data['4h'].resample('4H').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
            
            return data
        except Exception as e:
            logger.error(f"Error getting multi-timeframe data: {e}")
            return {}
    
    def identify_market_structure(self, data):
        """Identify ICT Market Structure"""
        if data.empty:
            return "UNKNOWN"
        
        # Calculate swing highs and lows
        high_rolling = data['High'].rolling(window=10, center=True)
        low_rolling = data['Low'].rolling(window=10, center=True)
        
        # Find swing points
        swing_highs = data['High'][
            (data['High'] == high_rolling.max()) & 
            (data['High'].shift(5) < data['High']) & 
            (data['High'].shift(-5) < data['High'])
        ].dropna()
        
        swing_lows = data['Low'][
            (data['Low'] == low_rolling.min()) & 
            (data['Low'].shift(5) > data['Low']) & 
            (data['Low'].shift(-5) > data['Low'])
        ].dropna()
        
        # Determine trend based on swing points
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            recent_highs = swing_highs.tail(2)
            recent_lows = swing_lows.tail(2)
            
            higher_highs = recent_highs.iloc[-1] > recent_highs.iloc[-2]
            higher_lows = recent_lows.iloc[-1] > recent_lows.iloc[-2]
            
            if higher_highs and higher_lows:
                return "BULLISH"
            elif not higher_highs and not higher_lows:
                return "BEARISH"
            else:
                return "RANGING"
        
        return "UNKNOWN"
    
    def find_order_blocks(self, data, timeframe='1h'):
        """Find ICT Order Blocks"""
        order_blocks = []
        
        if data.empty:
            return order_blocks
        
        # Look for strong moves (displacement)
        data['body_size'] = abs(data['Close'] - data['Open'])
        data['range_size'] = data['High'] - data['Low']
        data['displacement'] = data['body_size'] / data['range_size']
        
        # Find displacement candles (strong moves)
        displacement_threshold = 0.7  # 70% body to range ratio
        strong_moves = data[data['displacement'] > displacement_threshold]
        
        for idx, candle in strong_moves.iterrows():
            # Bullish order block (before strong up move)
            if candle['Close'] > candle['Open']:
                # Look for the last down candle before this move
                prev_candles = data.loc[:idx].tail(10)
                down_candles = prev_candles[prev_candles['Close'] < prev_candles['Open']]
                
                if not down_candles.empty:
                    last_down = down_candles.iloc[-1]
                    order_blocks.append({
                        'type': 'BULLISH_OB',
                        'high': last_down['High'],
                        'low': last_down['Low'],
                        'timestamp': last_down.name,
                        'timeframe': timeframe
                    })
            
            # Bearish order block (before strong down move)
            else:
                prev_candles = data.loc[:idx].tail(10)
                up_candles = prev_candles[prev_candles['Close'] > prev_candles['Open']]
                
                if not up_candles.empty:
                    last_up = up_candles.iloc[-1]
                    order_blocks.append({
                        'type': 'BEARISH_OB',
                        'high': last_up['High'],
                        'low': last_up['Low'],
                        'timestamp': last_up.name,
                        'timeframe': timeframe
                    })
        
        return order_blocks[-5:]  # Return last 5 order blocks
    
    def find_fair_value_gaps(self, data):
        """Find ICT Fair Value Gaps (FVG)"""
        fvgs = []
        
        if len(data) < 3:
            return fvgs
        
        for i in range(1, len(data) - 1):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            next_candle = data.iloc[i+1]
            
            # Bullish FVG: prev_low > next_high (gap up)
            if prev['Low'] > next_candle['High']:
                fvgs.append({
                    'type': 'BULLISH_FVG',
                    'high': prev['Low'],
                    'low': next_candle['High'],
                    'timestamp': current.name,
                    'filled': False
                })
            
            # Bearish FVG: prev_high < next_low (gap down)
            elif prev['High'] < next_candle['Low']:
                fvgs.append({
                    'type': 'BEARISH_FVG',
                    'high': next_candle['Low'],
                    'low': prev['High'],
                    'timestamp': current.name,
                    'filled': False
                })
        
        return fvgs[-3:]  # Return last 3 FVGs
    
    def find_liquidity_pools(self, data):
        """Find Liquidity Pools (Equal Highs/Lows)"""
        liquidity_pools = []
        
        if len(data) < 20:
            return liquidity_pools
        
        # Find equal highs (resistance liquidity)
        highs = data['High'].rolling(window=5, center=True).max()
        equal_highs = []
        
        for i in range(5, len(data) - 5):
            current_high = data['High'].iloc[i]
            if current_high == highs.iloc[i]:
                # Check for equal highs within 0.1% range
                similar_highs = data['High'][
                    (data['High'] >= current_high * 0.999) & 
                    (data['High'] <= current_high * 1.001)
                ]
                
                if len(similar_highs) >= 2:
                    equal_highs.append({
                        'type': 'SELL_SIDE_LIQUIDITY',
                        'level': current_high,
                        'timestamp': data.index[i],
                        'count': len(similar_highs)
                    })
        
        # Find equal lows (support liquidity)
        lows = data['Low'].rolling(window=5, center=True).min()
        equal_lows = []
        
        for i in range(5, len(data) - 5):
            current_low = data['Low'].iloc[i]
            if current_low == lows.iloc[i]:
                similar_lows = data['Low'][
                    (data['Low'] >= current_low * 0.999) & 
                    (data['Low'] <= current_low * 1.001)
                ]
                
                if len(similar_lows) >= 2:
                    equal_lows.append({
                        'type': 'BUY_SIDE_LIQUIDITY',
                        'level': current_low,
                        'timestamp': data.index[i],
                        'count': len(similar_lows)
                    })
        
        return equal_highs[-2:] + equal_lows[-2:]
    
    def calculate_technical_indicators(self, data):
        """Calculate all technical indicators"""
        if data.empty:
            return {}
        
        indicators = {}
        
        try:
            # Trend Indicators
            indicators['sma_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator().iloc[-1]
            indicators['sma_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator().iloc[-1]
            indicators['ema_12'] = ta.trend.EMAIndicator(data['Close'], window=12).ema_indicator().iloc[-1]
            indicators['ema_26'] = ta.trend.EMAIndicator(data['Close'], window=26).ema_indicator().iloc[-1]
            
            # MACD
            macd = ta.trend.MACD(data['Close'])
            indicators['macd'] = macd.macd().iloc[-1]
            indicators['macd_signal'] = macd.macd_signal().iloc[-1]
            indicators['macd_histogram'] = macd.macd_diff().iloc[-1]
            
            # Momentum Indicators
            indicators['rsi'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi().iloc[-1]
            indicators['stoch'] = ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close']).stoch().iloc[-1]
            
            # Volatility Indicators
            bb = ta.volatility.BollingerBands(data['Close'])
            indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
            indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']
            
            # ATR
            indicators['atr'] = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close']).average_true_range().iloc[-1]
            
            # Volume Indicators
            if 'Volume' in data.columns:
                indicators['volume_sma'] = data['Volume'].rolling(20).mean().iloc[-1]
                indicators['volume_ratio'] = data['Volume'].iloc[-1] / indicators['volume_sma']
                indicators['obv'] = ta.volume.OnBalanceVolumeIndicator(data['Close'], data['Volume']).on_balance_volume().iloc[-1]
            
            # Support/Resistance
            indicators['pivot_point'] = (data['High'].iloc[-1] + data['Low'].iloc[-1] + data['Close'].iloc[-1]) / 3
            indicators['resistance_1'] = 2 * indicators['pivot_point'] - data['Low'].iloc[-1]
            indicators['support_1'] = 2 * indicators['pivot_point'] - data['High'].iloc[-1]
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return indicators
    
    def generate_real_ict_signal(self):
        """Generate real ICT trading signal"""
        try:
            # Get multi-timeframe data
            mtf_data = self.get_multi_timeframe_data()
            
            if not mtf_data or '1h' not in mtf_data or mtf_data['1h'].empty:
                return self._get_fallback_signal()
            
            # Use 1H as main timeframe
            main_data = mtf_data['1h']
            current_price = main_data['Close'].iloc[-1]
            
            # ICT Analysis
            market_structure = self.identify_market_structure(main_data)
            order_blocks = self.find_order_blocks(main_data)
            fvgs = self.find_fair_value_gaps(main_data)
            liquidity_pools = self.find_liquidity_pools(main_data)
            
            # Technical Indicators
            indicators = self.calculate_technical_indicators(main_data)
            
            # Signal Generation Logic
            signal_strength = 0
            signal_direction = "HOLD"
            reasons = []
            
            # Market Structure Analysis
            if market_structure == "BULLISH":
                signal_strength += 20
                reasons.append("Bullish market structure")
            elif market_structure == "BEARISH":
                signal_strength -= 20
                reasons.append("Bearish market structure")
            
            # Order Block Analysis
            for ob in order_blocks:
                if ob['type'] == 'BULLISH_OB' and current_price >= ob['low'] and current_price <= ob['high']:
                    signal_strength += 25
                    reasons.append("Price at bullish order block")
                elif ob['type'] == 'BEARISH_OB' and current_price >= ob['low'] and current_price <= ob['high']:
                    signal_strength -= 25
                    reasons.append("Price at bearish order block")
            
            # FVG Analysis
            for fvg in fvgs:
                if fvg['type'] == 'BULLISH_FVG' and current_price >= fvg['low'] and current_price <= fvg['high']:
                    signal_strength += 15
                    reasons.append("Price in bullish FVG")
                elif fvg['type'] == 'BEARISH_FVG' and current_price >= fvg['low'] and current_price <= fvg['high']:
                    signal_strength -= 15
                    reasons.append("Price in bearish FVG")
            
            # Technical Indicators
            if 'rsi' in indicators:
                if indicators['rsi'] < 30:
                    signal_strength += 10
                    reasons.append("RSI oversold")
                elif indicators['rsi'] > 70:
                    signal_strength -= 10
                    reasons.append("RSI overbought")
            
            if 'macd_histogram' in indicators:
                if indicators['macd_histogram'] > 0:
                    signal_strength += 5
                    reasons.append("MACD bullish")
                else:
                    signal_strength -= 5
                    reasons.append("MACD bearish")
            
            # Determine final signal
            if signal_strength >= 30:
                signal_direction = "BUY"
                confidence = min(signal_strength + 40, 95)
            elif signal_strength <= -30:
                signal_direction = "SELL"
                confidence = min(abs(signal_strength) + 40, 95)
            else:
                signal_direction = "HOLD"
                confidence = 50
            
            return {
                'signal': signal_direction,
                'confidence': confidence,
                'current_price': round(current_price, 2),
                'market_structure': market_structure,
                'order_blocks': len(order_blocks),
                'fair_value_gaps': len(fvgs),
                'liquidity_pools': len(liquidity_pools),
                'technical_score': signal_strength,
                'reasons': reasons[:3],  # Top 3 reasons
                'indicators': {
                    'rsi': round(indicators.get('rsi', 50), 2),
                    'macd': round(indicators.get('macd', 0), 4),
                    'bb_position': self._get_bb_position(current_price, indicators),
                    'volume_strength': self._get_volume_strength(indicators)
                },
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timeframe': '1H',
                'data_quality': 'REAL'
            }
            
        except Exception as e:
            logger.error(f"Error in real ICT analysis: {e}")
            return self._get_fallback_signal()
    
    def _get_bb_position(self, price, indicators):
        """Get Bollinger Bands position"""
        if 'bb_upper' in indicators and 'bb_lower' in indicators:
            bb_range = indicators['bb_upper'] - indicators['bb_lower']
            position = (price - indicators['bb_lower']) / bb_range
            
            if position > 0.8:
                return "UPPER"
            elif position < 0.2:
                return "LOWER"
            else:
                return "MIDDLE"
        return "UNKNOWN"
    
    def _get_volume_strength(self, indicators):
        """Get volume strength"""
        if 'volume_ratio' in indicators:
            ratio = indicators['volume_ratio']
            if ratio > 1.5:
                return "HIGH"
            elif ratio > 1.2:
                return "ABOVE_AVERAGE"
            elif ratio < 0.8:
                return "LOW"
            else:
                return "AVERAGE"
        return "UNKNOWN"
    
    def _get_fallback_signal(self):
        """Fallback signal when real analysis fails"""
        return {
            'signal': 'HOLD',
            'confidence': 50,
            'current_price': 3280.0,
            'market_structure': 'UNKNOWN',
            'order_blocks': 0,
            'fair_value_gaps': 0,
            'liquidity_pools': 0,
            'technical_score': 0,
            'reasons': ['Data unavailable'],
            'indicators': {
                'rsi': 50.0,
                'macd': 0.0,
                'bb_position': 'UNKNOWN',
                'volume_strength': 'UNKNOWN'
            },
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timeframe': 'FALLBACK',
            'data_quality': 'SIMULATED'
        }

# Alias for backward compatibility
TechnicalAnalyzer = RealICTAnalyzer
