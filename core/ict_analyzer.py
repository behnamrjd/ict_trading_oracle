# ICT Analyzer 
"""
ICT Analysis Core Module
Contains all ICT-specific analysis functions
"""

import pandas as pd
import numpy as np
import ta
from datetime import datetime
import pytz
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ICTAnalyzer:
    """تحلیلگر اصلی ICT"""
    
    def __init__(self):
        self.symbol = "GC=F"
    
    def analyze_market_structure(self, data: pd.DataFrame) -> Dict:
        """تحلیل ساختار بازار"""
        try:
            swing_points = self._identify_swing_points(data)
            
            highs = swing_points['highs']
            lows = swing_points['lows']
            
            structure = 'NEUTRAL'
            strength = 50
            
            if len(highs) >= 2 and len(lows) >= 2:
                recent_highs = [h['price'] for h in highs[-2:]]
                recent_lows = [l['price'] for l in lows[-2:]]
                
                # Bullish Structure: HH + HL
                if (recent_highs[-1] > recent_highs[-2] and 
                    recent_lows[-1] > recent_lows[-2]):
                    structure = 'BULLISH'
                    strength = 80
                
                # Bearish Structure: LH + LL
                elif (recent_highs[-1] < recent_highs[-2] and 
                      recent_lows[-1] < recent_lows[-2]):
                    structure = 'BEARISH'
                    strength = 80
            
            return {
                'structure': structure,
                'strength': strength,
                'swing_highs': len(highs),
                'swing_lows': len(lows)
            }
            
        except Exception as e:
            logger.error(f"Error in market structure analysis: {e}")
            return {'structure': 'NEUTRAL', 'strength': 50}
    
    def detect_break_of_structure(self, data: pd.DataFrame) -> Dict:
        """تشخیص Break of Structure"""
        try:
            swing_points = self._identify_swing_points(data)
            current_price = data['Close'].iloc[-1]
            
            bos_detected = False
            bos_type = None
            
            # Bullish BOS
            if swing_points['highs']:
                last_high = swing_points['highs'][-1]['price']
                if current_price > last_high * 1.001:
                    bos_detected = True
                    bos_type = 'BULLISH_BOS'
            
            # Bearish BOS
            if swing_points['lows']:
                last_low = swing_points['lows'][-1]['price']
                if current_price < last_low * 0.999:
                    bos_detected = True
                    bos_type = 'BEARISH_BOS'
            
            return {
                'bos_detected': bos_detected,
                'bos_type': bos_type,
                'current_price': current_price
            }
            
        except Exception as e:
            logger.error(f"Error detecting BOS: {e}")
            return {'bos_detected': False, 'bos_type': None}
    
    def detect_order_blocks(self, data: pd.DataFrame) -> List[Dict]:
        """تشخیص Order Blocks"""
        try:
            order_blocks = []
            
            for i in range(3, len(data) - 1):
                current_candle = data.iloc[i]
                next_candle = data.iloc[i + 1]
                
                # Bullish Order Block
                if (current_candle['Close'] < current_candle['Open'] and
                    next_candle['Close'] > current_candle['High'] and
                    current_candle['Volume'] > data['Volume'].iloc[i-3:i].mean() * 1.2):
                    
                    order_blocks.append({
                        'type': 'bullish',
                        'level': current_candle['Low'],
                        'high': current_candle['High'],
                        'index': i,
                        'timestamp': data.index[i],
                        'quality': 'HIGH'
                    })
                
                # Bearish Order Block
                elif (current_candle['Close'] > current_candle['Open'] and
                      next_candle['Close'] < current_candle['Low'] and
                      current_candle['Volume'] > data['Volume'].iloc[i-3:i].mean() * 1.2):
                    
                    order_blocks.append({
                        'type': 'bearish',
                        'level': current_candle['High'],
                        'low': current_candle['Low'],
                        'index': i,
                        'timestamp': data.index[i],
                        'quality': 'HIGH'
                    })
            
            return order_blocks[-5:]
            
        except Exception as e:
            logger.error(f"Error detecting order blocks: {e}")
            return []
    
    def detect_fair_value_gaps(self, data: pd.DataFrame) -> List[Dict]:
        """تشخیص Fair Value Gaps"""
        try:
            fvgs = []
            
            for i in range(1, len(data) - 1):
                candle1 = data.iloc[i-1]
                candle2 = data.iloc[i]
                candle3 = data.iloc[i+1]
                
                # Bullish FVG
                if candle1['Low'] > candle3['High']:
                    gap_size = candle1['Low'] - candle3['High']
                    
                    fvgs.append({
                        'type': 'bullish',
                        'upper': candle1['Low'],
                        'lower': candle3['High'],
                        'size': gap_size,
                        'index': i,
                        'timestamp': data.index[i],
                        'filled': False
                    })
                
                # Bearish FVG
                elif candle1['High'] < candle3['Low']:
                    gap_size = candle3['Low'] - candle1['High']
                    
                    fvgs.append({
                        'type': 'bearish',
                        'upper': candle3['Low'],
                        'lower': candle1['High'],
                        'size': gap_size,
                        'index': i,
                        'timestamp': data.index[i],
                        'filled': False
                    })
            
            return fvgs[-8:]
            
        except Exception as e:
            logger.error(f"Error detecting FVGs: {e}")
            return []
    
    def analyze_kill_zones(self) -> Dict:
        """تحلیل Kill Zones"""
        try:
            now = datetime.now(pytz.UTC)
            hour = now.hour
            
            from config.settings import KILL_ZONES
            
            active_zones = []
            for zone, times in KILL_ZONES.items():
                if zone == 'asian_session':
                    if hour >= times['start'] or hour < times['end']:
                        active_zones.append(zone)
                else:
                    if times['start'] <= hour < times['end']:
                        active_zones.append(zone)
            
            # تعیین کیفیت جلسه
            if 'new_york_open' in active_zones:
                session_quality = 'PREMIUM'
            elif 'london_open' in active_zones:
                session_quality = 'HIGH'
            elif 'asian_session' in active_zones:
                session_quality = 'LOW'
            else:
                session_quality = 'MEDIUM'
            
            return {
                'active_zones': active_zones,
                'session_quality': session_quality,
                'optimal_time': session_quality in ['PREMIUM', 'HIGH']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing kill zones: {e}")
            return {'session_quality': 'MEDIUM', 'optimal_time': False}
    
    def calculate_optimal_trade_entry(self, data: pd.DataFrame) -> Dict:
        """محاسبه Optimal Trade Entry"""
        try:
            recent_data = data.tail(50)
            high = recent_data['High'].max()
            low = recent_data['Low'].min()
            diff = high - low
            
            ote_levels = {
                '61.8%': high - 0.618 * diff,
                '70.5%': high - 0.705 * diff,
                '78.6%': high - 0.786 * diff
            }
            
            current_price = data['Close'].iloc[-1]
            
            for level_name, level_price in ote_levels.items():
                distance = abs(current_price - level_price) / current_price
                if distance < 0.005:
                    return {
                        'in_ote_zone': True,
                        'level': level_name,
                        'price': level_price,
                        'distance': distance
                    }
            
            return {
                'in_ote_zone': False,
                'levels': ote_levels
            }
            
        except Exception as e:
            logger.error(f"Error calculating OTE: {e}")
            return {'in_ote_zone': False}
    
    def _identify_swing_points(self, data: pd.DataFrame, lookback: int = 5) -> Dict:
        """تشخیص Swing Points"""
        try:
            swing_highs = []
            swing_lows = []
            
            for i in range(lookback, len(data) - lookback):
                # Swing High
                is_swing_high = True
                for j in range(i - lookback, i + lookback + 1):
                    if j != i and data['High'].iloc[j] >= data['High'].iloc[i]:
                        is_swing_high = False
                        break
                
                if is_swing_high:
                    swing_highs.append({
                        'index': i,
                        'price': data['High'].iloc[i],
                        'timestamp': data.index[i]
                    })
                
                # Swing Low
                is_swing_low = True
                for j in range(i - lookback, i + lookback + 1):
                    if j != i and data['Low'].iloc[j] <= data['Low'].iloc[i]:
                        is_swing_low = False
                        break
                
                if is_swing_low:
                    swing_lows.append({
                        'index': i,
                        'price': data['Low'].iloc[i],
                        'timestamp': data.index[i]
                    })
            
            return {'highs': swing_highs[-5:], 'lows': swing_lows[-5:]}
            
        except Exception as e:
            logger.error(f"Error identifying swing points: {e}")
            return {'highs': [], 'lows': []}
