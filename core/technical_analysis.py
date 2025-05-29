"""
Real ICT (Inner Circle Trading) Analysis System v2.0
Advanced Technical Analysis with 25+ Indicators
"""

import yfinance as yf
import pandas as pd
import numpy as np
import ta
from ta import trend as ta_trend
from ta import volatility as ta_volatility
from ta import momentum as ta_momentum
from ta import volume as ta_volume
from datetime import datetime, timedelta
import logging
import warnings
import time
import gc
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class RealICTAnalyzer:
    def __init__(self):
        self.symbol = "GC=F"  # Gold futures
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.min_data_points = 50  # Minimum data points for analysis
        self.max_retries = 3
        self.retry_delay = 2
        
        # Setup robust HTTP session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Data limits for memory management
        self.data_limits = {
            '1m': 200,   # 3+ hours
            '5m': 500,   # ~2 days  
            '15m': 500,  # ~5 days
            '1h': 720,   # 30 days
            '4h': 720,   # 120 days
            '1d': 365    # 1 year
        }
        
    def get_multi_timeframe_data(self):
        """Get comprehensive multi-timeframe data with error recovery"""
        data = {}
        
        for attempt in range(self.max_retries):
            try:
                ticker = yf.Ticker(self.symbol)
                
                # Get different timeframe data with proper periods and limits
                timeframe_config = {
                    '1m': {'period': '1d', 'interval': '1m'},
                    '5m': {'period': '5d', 'interval': '5m'},
                    '15m': {'period': '5d', 'interval': '15m'},
                    '1h': {'period': '30d', 'interval': '1h'},
                    '1d': {'period': '1y', 'interval': '1d'}
                }
                
                for tf, config in timeframe_config.items():
                    try:
                        logger.info(f"📊 Fetching {tf} data (attempt {attempt + 1})...")
                        
                        # Get data with timeout
                        df = ticker.history(
                            period=config['period'], 
                            interval=config['interval'],
                            timeout=30
                        )
                        
                        if not df.empty and len(df) >= 10:
                            # Limit data size for memory management
                            max_rows = self.data_limits.get(tf, 500)
                            if len(df) > max_rows:
                                df = df.tail(max_rows)
                            
                            data[tf] = df
                            logger.info(f"✅ {tf} data: {len(df)} candles")
                        else:
                            logger.warning(f"⚠️ {tf} data: insufficient data ({len(df)} candles)")
                            
                    except Exception as tf_error:
                        logger.error(f"❌ Error getting {tf} data: {tf_error}")
                        continue
                
                # Create 4H data by resampling 1H if available
                if '1h' in data and not data['1h'].empty:
                    try:
                        data['4h'] = data['1h'].resample('4H').agg({
                            'Open': 'first',
                            'High': 'max',
                            'Low': 'min',
                            'Close': 'last',
                            'Volume': 'sum'
                        }).dropna()
                        
                        # Limit 4H data
                        max_4h = self.data_limits.get('4h', 720)
                        if len(data['4h']) > max_4h:
                            data['4h'] = data['4h'].tail(max_4h)
                        
                        logger.info(f"✅ 4h data: {len(data['4h'])} candles (resampled)")
                    except Exception as resample_error:
                        logger.error(f"❌ Error creating 4H data: {resample_error}")
                
                # Memory cleanup
                gc.collect()
                
                # If we got at least one timeframe, consider it success
                if data:
                    logger.info(f"🎯 Successfully loaded {len(data)} timeframes")
                    return data
                else:
                    raise Exception("No timeframe data available")
                    
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay ** attempt
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error("❌ All attempts failed, returning empty data")
                    return {}
        
        return {}
        
    def identify_market_structure(self, data):
        """Advanced ICT Market Structure Analysis"""
        if data.empty or len(data) < 20:
            return {"structure": "UNKNOWN", "strength": 0, "details": "Insufficient data"}
        
        try:
            # Calculate swing points with different periods
            swing_period = min(10, len(data) // 4)
            
            # Find swing highs and lows
            data['swing_high'] = data['High'].rolling(window=swing_period*2+1, center=True).max() == data['High']
            data['swing_low'] = data['Low'].rolling(window=swing_period*2+1, center=True).min() == data['Low']
            
            # Get actual swing points
            swing_highs = data[data['swing_high']]['High'].dropna()
            swing_lows = data[data['swing_low']]['Low'].dropna()
            
            if len(swing_highs) < 2 or len(swing_lows) < 2:
                return {"structure": "RANGING", "strength": 30, "details": "Limited swing points"}
            
            # Analyze recent swing points (last 4 of each)
            recent_highs = swing_highs.tail(4)
            recent_lows = swing_lows.tail(4)
            
            # Check for higher highs and higher lows (bullish structure)
            hh_count = 0
            hl_count = 0
            
            if len(recent_highs) >= 2:
                for i in range(1, len(recent_highs)):
                    if recent_highs.iloc[i] > recent_highs.iloc[i-1]:
                        hh_count += 1
            
            if len(recent_lows) >= 2:
                for i in range(1, len(recent_lows)):
                    if recent_lows.iloc[i] > recent_lows.iloc[i-1]:
                        hl_count += 1
            
            # Check for lower highs and lower lows (bearish structure)
            lh_count = 0
            ll_count = 0
            
            if len(recent_highs) >= 2:
                for i in range(1, len(recent_highs)):
                    if recent_highs.iloc[i] < recent_highs.iloc[i-1]:
                        lh_count += 1
            
            if len(recent_lows) >= 2:
                for i in range(1, len(recent_lows)):
                    if recent_lows.iloc[i] < recent_lows.iloc[i-1]:
                        ll_count += 1
            
            # Determine structure
            bullish_score = hh_count + hl_count
            bearish_score = lh_count + ll_count
            
            if bullish_score > bearish_score and bullish_score >= 2:
                structure = "BULLISH"
                strength = min(bullish_score * 25, 100)
                details = f"HH: {hh_count}, HL: {hl_count}"
            elif bearish_score > bullish_score and bearish_score >= 2:
                structure = "BEARISH"
                strength = min(bearish_score * 25, 100)
                details = f"LH: {lh_count}, LL: {ll_count}"
            else:
                structure = "RANGING"
                strength = 40
                details = "Mixed signals"
            
            return {
                "structure": structure,
                "strength": strength,
                "details": details,
                "swing_highs": len(swing_highs),
                "swing_lows": len(swing_lows)
            }
            
        except Exception as e:
            logger.error(f"Error in market structure analysis: {e}")
            return {"structure": "UNKNOWN", "strength": 0, "details": f"Error: {str(e)}"}
    
    def find_order_blocks(self, data, lookback=50):
        """Advanced ICT Order Block Detection"""
        order_blocks = []
        
        if data.empty or len(data) < 20:
            return order_blocks
        
        try:
            # Calculate candle properties
            data['body_size'] = abs(data['Close'] - data['Open'])
            data['upper_wick'] = data['High'] - data[['Open', 'Close']].max(axis=1)
            data['lower_wick'] = data[['Open', 'Close']].min(axis=1) - data['Low']
            data['total_range'] = data['High'] - data['Low']
            data['body_ratio'] = data['body_size'] / data['total_range']
            
            # Find displacement candles (strong institutional moves)
            displacement_threshold = 0.6  # 60% body to range ratio
            min_body_size = data['body_size'].quantile(0.7)  # Top 30% of candles
            
            displacement_candles = data[
                (data['body_ratio'] > displacement_threshold) & 
                (data['body_size'] > min_body_size)
            ]
            
            for idx in displacement_candles.index[-10:]:  # Last 10 displacement candles
                try:
                    candle = data.loc[idx]
                    
                    # Get previous candles for order block identification
                    prev_data = data.loc[:idx].tail(15)
                    
                    if candle['Close'] > candle['Open']:  # Bullish displacement
                        # Find the last bearish candle before this move
                        bearish_candles = prev_data[prev_data['Close'] < prev_data['Open']]
                        
                        if not bearish_candles.empty:
                            last_bearish = bearish_candles.iloc[-1]
                            
                            # Validate order block
                            if self._validate_order_block(data, idx, last_bearish.name, 'BULLISH'):
                                order_blocks.append({
                                    'type': 'BULLISH_OB',
                                    'high': last_bearish['High'],
                                    'low': last_bearish['Low'],
                                    'open': last_bearish['Open'],
                                    'close': last_bearish['Close'],
                                    'timestamp': last_bearish.name,
                                    'displacement_candle': idx,
                                    'strength': self._calculate_ob_strength(data, last_bearish.name, idx),
                                    'tested': False
                                })
                    
                    else:  # Bearish displacement
                        # Find the last bullish candle before this move
                        bullish_candles = prev_data[prev_data['Close'] > prev_data['Open']]
                        
                        if not bullish_candles.empty:
                            last_bullish = bullish_candles.iloc[-1]
                            
                            if self._validate_order_block(data, idx, last_bullish.name, 'BEARISH'):
                                order_blocks.append({
                                    'type': 'BEARISH_OB',
                                    'high': last_bullish['High'],
                                    'low': last_bullish['Low'],
                                    'open': last_bullish['Open'],
                                    'close': last_bullish['Close'],
                                    'timestamp': last_bullish.name,
                                    'displacement_candle': idx,
                                    'strength': self._calculate_ob_strength(data, last_bullish.name, idx),
                                    'tested': False
                                })
                
                except Exception as e:
                    logger.error(f"Error processing displacement candle {idx}: {e}")
                    continue
            
            # Sort by strength and return top 5
            order_blocks.sort(key=lambda x: x['strength'], reverse=True)
            return order_blocks[:5]
            
        except Exception as e:
            logger.error(f"Error in order block detection: {e}")
            return []
    
    def _validate_order_block(self, data, displacement_idx, ob_idx, ob_type):
        """Validate order block quality"""
        try:
            # Check if there's enough separation between OB and displacement
            time_diff = displacement_idx - ob_idx
            if time_diff < 1 or time_diff > 20:
                return False
            
            # Check if price moved significantly after displacement
            displacement_candle = data.loc[displacement_idx]
            ob_candle = data.loc[ob_idx]
            
            if ob_type == 'BULLISH':
                price_move = displacement_candle['Close'] - ob_candle['High']
                min_move = ob_candle['total_range'] * 2  # At least 2x the OB range
            else:
                price_move = ob_candle['Low'] - displacement_candle['Close']
                min_move = ob_candle['total_range'] * 2
            
            return price_move > min_move
            
        except Exception:
            return False
    
    def _calculate_ob_strength(self, data, ob_idx, displacement_idx):
        """Calculate order block strength (0-100)"""
        try:
            ob_candle = data.loc[ob_idx]
            displacement_candle = data.loc[displacement_idx]
            
            strength = 50  # Base strength
            
            # Volume factor (if available)
            if 'Volume' in data.columns:
                avg_volume = data['Volume'].rolling(20).mean().loc[ob_idx]
                if ob_candle['Volume'] > avg_volume * 1.5:
                    strength += 20
            
            # Body size factor
            if ob_candle['body_ratio'] > 0.7:
                strength += 15
            
            # Displacement strength
            if displacement_candle['body_ratio'] > 0.8:
                strength += 15
            
            return min(strength, 100)
            
        except Exception:
            return 50
    def find_fair_value_gaps(self, data, min_gap_size=0.1):
        """Advanced ICT Fair Value Gap Detection"""
        fvgs = []
        
        if data.empty or len(data) < 3:
            return fvgs
        
        try:
            # Calculate average true range for gap size validation
            atr = ta_volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], window=14).average_true_range()
            min_gap_threshold = atr.iloc[-1] * min_gap_size if not atr.empty else 1.0
            
            for i in range(1, len(data) - 1):
                try:
                    prev_candle = data.iloc[i-1]
                    current_candle = data.iloc[i]
                    next_candle = data.iloc[i+1]
                    
                    # Bullish FVG: Previous low > Next high (gap up)
                    if prev_candle['Low'] > next_candle['High']:
                        gap_size = prev_candle['Low'] - next_candle['High']
                        
                        if gap_size >= min_gap_threshold:
                            # Check for strong bullish momentum
                            momentum_strength = self._calculate_fvg_momentum(data, i, 'BULLISH')
                            
                            fvgs.append({
                                'type': 'BULLISH_FVG',
                                'high': prev_candle['Low'],
                                'low': next_candle['High'],
                                'gap_size': round(gap_size, 2),
                                'timestamp': current_candle.name,
                                'momentum_strength': momentum_strength,
                                'filled': False,
                                'fill_percentage': 0,
                                'created_by': {
                                    'prev_candle': prev_candle.name,
                                    'current_candle': current_candle.name,
                                    'next_candle': next_candle.name
                                }
                            })
                    
                    # Bearish FVG: Previous high < Next low (gap down)
                    elif prev_candle['High'] < next_candle['Low']:
                        gap_size = next_candle['Low'] - prev_candle['High']
                        
                        if gap_size >= min_gap_threshold:
                            momentum_strength = self._calculate_fvg_momentum(data, i, 'BEARISH')
                            
                            fvgs.append({
                                'type': 'BEARISH_FVG',
                                'high': next_candle['Low'],
                                'low': prev_candle['High'],
                                'gap_size': round(gap_size, 2),
                                'timestamp': current_candle.name,
                                'momentum_strength': momentum_strength,
                                'filled': False,
                                'fill_percentage': 0,
                                'created_by': {
                                    'prev_candle': prev_candle.name,
                                    'current_candle': current_candle.name,
                                    'next_candle': next_candle.name
                                }
                            })
                
                except Exception as e:
                    logger.error(f"Error processing FVG at index {i}: {e}")
                    continue
            
            # Check which FVGs have been filled
            current_price = data['Close'].iloc[-1]
            for fvg in fvgs:
                fvg['fill_percentage'] = self._calculate_fvg_fill_percentage(fvg, current_price)
                fvg['filled'] = fvg['fill_percentage'] >= 100
            
            # Sort by momentum strength and return recent unfilled FVGs
            unfilled_fvgs = [fvg for fvg in fvgs if not fvg['filled']]
            unfilled_fvgs.sort(key=lambda x: x['momentum_strength'], reverse=True)
            
            return unfilled_fvgs[-5:]  # Return last 5 unfilled FVGs
            
        except Exception as e:
            logger.error(f"Error in FVG detection: {e}")
            return []
    
    def _calculate_fvg_momentum(self, data, gap_index, gap_type):
        """Calculate momentum strength that created the FVG"""
        try:
            # Look at 3 candles before and after the gap
            start_idx = max(0, gap_index - 3)
            end_idx = min(len(data), gap_index + 4)
            momentum_data = data.iloc[start_idx:end_idx]
            
            if gap_type == 'BULLISH':
                # Calculate upward momentum
                price_change = momentum_data['Close'].iloc[-1] - momentum_data['Open'].iloc[0]
                bullish_candles = len(momentum_data[momentum_data['Close'] > momentum_data['Open']])
                momentum = (price_change / momentum_data['Open'].iloc[0]) * 100 * (bullish_candles / len(momentum_data))
            else:
                # Calculate downward momentum
                price_change = momentum_data['Open'].iloc[0] - momentum_data['Close'].iloc[-1]
                bearish_candles = len(momentum_data[momentum_data['Close'] < momentum_data['Open']])
                momentum = (price_change / momentum_data['Open'].iloc[0]) * 100 * (bearish_candles / len(momentum_data))
            
            return max(0, min(100, momentum * 10))  # Scale to 0-100
            
        except Exception:
            return 50
    
    def _calculate_fvg_fill_percentage(self, fvg, current_price):
        """Calculate how much of the FVG has been filled"""
        try:
            gap_range = fvg['high'] - fvg['low']
            
            if fvg['type'] == 'BULLISH_FVG':
                if current_price <= fvg['low']:
                    return 0
                elif current_price >= fvg['high']:
                    return 100
                else:
                    return ((current_price - fvg['low']) / gap_range) * 100
            else:  # BEARISH_FVG
                if current_price >= fvg['high']:
                    return 0
                elif current_price <= fvg['low']:
                    return 100
                else:
                    return ((fvg['high'] - current_price) / gap_range) * 100
        except Exception:
            return 0
    
    def find_liquidity_pools(self, data, tolerance=0.001):
        """Advanced Liquidity Pool Detection"""
        liquidity_pools = []
        
        if data.empty or len(data) < 30:
            return liquidity_pools
        
        try:
            # Find swing highs and lows first
            swing_window = min(5, len(data) // 10)
            
            # Detect swing highs
            data['is_swing_high'] = (
                data['High'].rolling(window=swing_window*2+1, center=True).max() == data['High']
            )
            
            # Detect swing lows
            data['is_swing_low'] = (
                data['Low'].rolling(window=swing_window*2+1, center=True).min() == data['Low']
            )
            
            swing_highs = data[data['is_swing_high']]['High'].dropna()
            swing_lows = data[data['is_swing_low']]['Low'].dropna()
            
            # Find equal highs (sell-side liquidity)
            equal_highs = self._find_equal_levels(swing_highs, tolerance, 'HIGH')
            for level_info in equal_highs:
                liquidity_pools.append({
                    'type': 'SELL_SIDE_LIQUIDITY',
                    'level': level_info['level'],
                    'touches': level_info['touches'],
                    'timestamps': level_info['timestamps'],
                    'strength': level_info['strength'],
                    'volume_profile': self._calculate_volume_at_level(data, level_info['level'], 'HIGH'),
                    'last_touch': level_info['timestamps'][-1],
                    'swept': False
                })
            
            # Find equal lows (buy-side liquidity)
            equal_lows = self._find_equal_levels(swing_lows, tolerance, 'LOW')
            for level_info in equal_lows:
                liquidity_pools.append({
                    'type': 'BUY_SIDE_LIQUIDITY',
                    'level': level_info['level'],
                    'touches': level_info['touches'],
                    'timestamps': level_info['timestamps'],
                    'strength': level_info['strength'],
                    'volume_profile': self._calculate_volume_at_level(data, level_info['level'], 'LOW'),
                    'last_touch': level_info['timestamps'][-1],
                    'swept': False
                })
            
            # Check for swept liquidity
            current_price = data['Close'].iloc[-1]
            for pool in liquidity_pools:
                pool['swept'] = self._check_liquidity_swept(pool, current_price, data)
            
            # Sort by strength and return top pools
            active_pools = [pool for pool in liquidity_pools if not pool['swept']]
            active_pools.sort(key=lambda x: x['strength'], reverse=True)
            
            return active_pools[:6]  # Return top 6 liquidity pools
            
        except Exception as e:
            logger.error(f"Error in liquidity pool detection: {e}")
            return []
    
    def _find_equal_levels(self, price_series, tolerance, level_type):
        """Find equal price levels within tolerance"""
        equal_levels = []
        
        if len(price_series) < 2:
            return equal_levels
        
        try:
            prices = price_series.values
            timestamps = price_series.index
            
            processed_indices = set()
            
            for i, price in enumerate(prices):
                if i in processed_indices:
                    continue
                
                # Find all prices within tolerance
                similar_indices = []
                for j, other_price in enumerate(prices):
                    if j in processed_indices:
                        continue
                    
                    if abs(price - other_price) <= price * tolerance:
                        similar_indices.append(j)
                
                if len(similar_indices) >= 2:  # At least 2 touches
                    level_prices = [prices[idx] for idx in similar_indices]
                    level_timestamps = [timestamps[idx] for idx in similar_indices]
                    
                    avg_level = np.mean(level_prices)
                    touches = len(similar_indices)
                    
                    # Calculate strength based on touches and time span
                    time_span = (max(level_timestamps) - min(level_timestamps)).total_seconds() / 3600  # hours
                    strength = min(100, touches * 20 + min(time_span / 24, 10))  # Max 100
                    
                    equal_levels.append({
                        'level': round(avg_level, 2),
                        'touches': touches,
                        'timestamps': level_timestamps,
                        'strength': round(strength, 1),
                        'price_range': {
                            'min': min(level_prices),
                            'max': max(level_prices)
                        }
                    })
                    
                    # Mark these indices as processed
                    processed_indices.update(similar_indices)
            
            return equal_levels
            
        except Exception as e:
            logger.error(f"Error finding equal levels: {e}")
            return []
    
    def _calculate_volume_at_level(self, data, level, level_type):
        """Calculate volume profile at specific level"""
        try:
            if 'Volume' not in data.columns:
                return {'total_volume': 0, 'avg_volume': 0, 'volume_strength': 'UNKNOWN'}
            
            # Find candles that touched this level
            tolerance = level * 0.001  # 0.1% tolerance
            
            if level_type == 'HIGH':
                touching_candles = data[
                    (data['High'] >= level - tolerance) & 
                    (data['High'] <= level + tolerance)
                ]
            else:  # LOW
                touching_candles = data[
                    (data['Low'] >= level - tolerance) & 
                    (data['Low'] <= level + tolerance)
                ]
            
            if touching_candles.empty:
                return {'total_volume': 0, 'avg_volume': 0, 'volume_strength': 'LOW'}
            
            total_volume = touching_candles['Volume'].sum()
            avg_volume = touching_candles['Volume'].mean()
            overall_avg = data['Volume'].mean()
            
            if avg_volume > overall_avg * 1.5:
                volume_strength = 'HIGH'
            elif avg_volume > overall_avg * 1.2:
                volume_strength = 'MEDIUM'
            else:
                volume_strength = 'LOW'
            
            return {
                'total_volume': int(total_volume),
                'avg_volume': int(avg_volume),
                'volume_strength': volume_strength
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume at level: {e}")
            return {'total_volume': 0, 'avg_volume': 0, 'volume_strength': 'UNKNOWN'}
    
    def _check_liquidity_swept(self, pool, current_price, data):
        """Check if liquidity has been swept"""
        try:
            level = pool['level']
            last_touch = pool['last_touch']
            
            # Get data after last touch
            recent_data = data[data.index > last_touch]
            
            if recent_data.empty:
                return False
            
            if pool['type'] == 'SELL_SIDE_LIQUIDITY':
                # Check if price broke above the level significantly
                max_price_after = recent_data['High'].max()
                return max_price_after > level * 1.001  # 0.1% above
            else:  # BUY_SIDE_LIQUIDITY
                # Check if price broke below the level significantly
                min_price_after = recent_data['Low'].min()
                return min_price_after < level * 0.999  # 0.1% below
            
        except Exception:
            return False
    def calculate_comprehensive_indicators(self, data):
        """Calculate 25+ Technical Indicators"""
        if data.empty or len(data) < 50:
            return self._get_minimal_indicators(data)
        
        indicators = {}
        
        try:
            # === TREND INDICATORS ===
            
            # Moving Averages
            indicators['sma_9'] = ta_trend.SMAIndicator(data['Close'], window=9).sma_indicator().iloc[-1]
            indicators['sma_20'] = ta_trend.SMAIndicator(data['Close'], window=20).sma_indicator().iloc[-1]
            indicators['sma_50'] = ta_trend.SMAIndicator(data['Close'], window=50).sma_indicator().iloc[-1]
            indicators['sma_200'] = ta_trend.SMAIndicator(data['Close'], window=min(200, len(data))).sma_indicator().iloc[-1]
            
            # Exponential Moving Averages
            indicators['ema_9'] = ta_trend.EMAIndicator(data['Close'], window=9).ema_indicator().iloc[-1]
            indicators['ema_12'] = ta_trend.EMAIndicator(data['Close'], window=12).ema_indicator().iloc[-1]
            indicators['ema_21'] = ta_trend.EMAIndicator(data['Close'], window=21).ema_indicator().iloc[-1]
            indicators['ema_26'] = ta_trend.EMAIndicator(data['Close'], window=26).ema_indicator().iloc[-1]
            indicators['ema_50'] = ta_trend.EMAIndicator(data['Close'], window=50).ema_indicator().iloc[-1]
            
            # MACD Family
            macd = ta_trend.MACD(data['Close'], window_slow=26, window_fast=12, window_sign=9)
            indicators['macd'] = macd.macd().iloc[-1]
            indicators['macd_signal'] = macd.macd_signal().iloc[-1]
            indicators['macd_histogram'] = macd.macd_diff().iloc[-1]
            
            # ADX (Average Directional Index)
            adx = ta_trend.ADXIndicator(data['High'], data['Low'], data['Close'], window=14)
            indicators['adx'] = adx.adx().iloc[-1]
            indicators['adx_pos'] = adx.adx_pos().iloc[-1]
            indicators['adx_neg'] = adx.adx_neg().iloc[-1]
            
            # Parabolic SAR
            psar = ta_trend.PSARIndicator(data['High'], data['Low'], data['Close'])
            indicators['psar'] = psar.psar().iloc[-1]
            indicators['psar_up'] = psar.psar_up().iloc[-1] if not pd.isna(psar.psar_up().iloc[-1]) else None
            indicators['psar_down'] = psar.psar_down().iloc[-1] if not pd.isna(psar.psar_down().iloc[-1]) else None
            
            # === MOMENTUM INDICATORS ===
            
            # RSI (Relative Strength Index)
            indicators['rsi_14'] = ta_momentum.RSIIndicator(data['Close'], window=14).rsi().iloc[-1]
            indicators['rsi_21'] = ta_momentum.RSIIndicator(data['Close'], window=21).rsi().iloc[-1]
            
            # Stochastic Oscillator
            stoch = ta_momentum.StochasticOscillator(data['High'], data['Low'], data['Close'])
            indicators['stoch_k'] = stoch.stoch().iloc[-1]
            indicators['stoch_d'] = stoch.stoch_signal().iloc[-1]
            
            # Williams %R
            indicators['williams_r'] = ta_momentum.WilliamsRIndicator(data['High'], data['Low'], data['Close']).williams_r().iloc[-1]
            
            # ROC (Rate of Change)
            indicators['roc_12'] = ta_momentum.ROCIndicator(data['Close'], window=12).roc().iloc[-1]
            indicators['roc_25'] = ta_momentum.ROCIndicator(data['Close'], window=25).roc().iloc[-1]
            
            # CCI (Commodity Channel Index)
            indicators['cci'] = ta_trend.CCIIndicator(data['High'], data['Low'], data['Close']).cci().iloc[-1]
            
            # === VOLATILITY INDICATORS ===
            
            # Bollinger Bands
            bb = ta_volatility.BollingerBands(data['Close'], window=20, window_dev=2)
            indicators['bb_upper'] = bb.bollinger_hband().iloc[-1]
            indicators['bb_middle'] = bb.bollinger_mavg().iloc[-1]
            indicators['bb_lower'] = bb.bollinger_lband().iloc[-1]
            indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'] * 100
            indicators['bb_percent'] = ((data['Close'].iloc[-1] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])) * 100
            
            # ATR (Average True Range)
            indicators['atr_14'] = ta_volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], window=14).average_true_range().iloc[-1]
            indicators['atr_21'] = ta_volatility.AverageTrueRange(data['High'], data['Low'], data['Close'], window=21).average_true_range().iloc[-1]
            
            # Keltner Channels
            kc = ta_volatility.KeltnerChannel(data['High'], data['Low'], data['Close'])
            indicators['kc_upper'] = kc.keltner_channel_hband().iloc[-1]
            indicators['kc_middle'] = kc.keltner_channel_mband().iloc[-1]
            indicators['kc_lower'] = kc.keltner_channel_lband().iloc[-1]
            
            # Donchian Channels
            dc = ta_volatility.DonchianChannel(data['High'], data['Low'], data['Close'])
            indicators['dc_upper'] = dc.donchian_channel_hband().iloc[-1]
            indicators['dc_middle'] = dc.donchian_channel_mband().iloc[-1]
            indicators['dc_lower'] = dc.donchian_channel_lband().iloc[-1]
            
            # === VOLUME INDICATORS ===
            if 'Volume' in data.columns and data['Volume'].sum() > 0:
                
                # Volume SMA
                indicators['volume_sma'] = data['Volume'].rolling(20).mean().iloc[-1]
                indicators['volume_ratio'] = data['Volume'].iloc[-1] / indicators['volume_sma']
                
                # On Balance Volume
                indicators['obv'] = ta_volume.OnBalanceVolumeIndicator(data['Close'], data['Volume']).on_balance_volume().iloc[-1]
                
                # Volume Price Trend
                indicators['vpt'] = ta_volume.VolumePriceTrendIndicator(data['Close'], data['Volume']).volume_price_trend().iloc[-1]
                
                # Accumulation/Distribution Line
                indicators['ad_line'] = ta_volume.AccDistIndexIndicator(data['High'], data['Low'], data['Close'], data['Volume']).acc_dist_index().iloc[-1]
                
                # Chaikin Money Flow
                indicators['cmf'] = ta_volume.ChaikinMoneyFlowIndicator(data['High'], data['Low'], data['Close'], data['Volume']).chaikin_money_flow().iloc[-1]
                
                # Volume Weighted Average Price (VWAP)
                indicators['vwap'] = self._calculate_vwap(data)
                
            else:
                # Default volume indicators when no volume data
                indicators.update({
                    'volume_sma': 0, 'volume_ratio': 1, 'obv': 0, 'vpt': 0,
                    'ad_line': 0, 'cmf': 0, 'vwap': data['Close'].iloc[-1]
                })
            
            # === SUPPORT/RESISTANCE LEVELS ===
            
            # Pivot Points
            high = data['High'].iloc[-1]
            low = data['Low'].iloc[-1]
            close = data['Close'].iloc[-1]
            
            indicators['pivot_point'] = (high + low + close) / 3
            indicators['resistance_1'] = 2 * indicators['pivot_point'] - low
            indicators['support_1'] = 2 * indicators['pivot_point'] - high
            indicators['resistance_2'] = indicators['pivot_point'] + (high - low)
            indicators['support_2'] = indicators['pivot_point'] - (high - low)
            indicators['resistance_3'] = high + 2 * (indicators['pivot_point'] - low)
            indicators['support_3'] = low - 2 * (high - indicators['pivot_point'])
            
            # === FIBONACCI LEVELS ===
            indicators.update(self._calculate_fibonacci_levels(data))
            
            # === CUSTOM ICT INDICATORS ===
            
            # Market Structure Score
            indicators['market_structure_score'] = self._calculate_market_structure_score(data)
            
            # Momentum Strength
            indicators['momentum_strength'] = self._calculate_momentum_strength(data)
            
            # Volatility Rank
            indicators['volatility_rank'] = self._calculate_volatility_rank(data)
            
            # Trend Strength
            indicators['trend_strength'] = self._calculate_trend_strength(indicators)
            
            # === ROUND VALUES ===
            for key, value in indicators.items():
                if isinstance(value, (int, float)) and not pd.isna(value):
                    indicators[key] = round(float(value), 4)
                elif pd.isna(value):
                    indicators[key] = 0.0
            
            logger.info(f"✅ Calculated {len(indicators)} technical indicators")
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive indicators: {e}")
            return self._get_minimal_indicators(data)
    
    def _calculate_vwap(self, data):
        """Calculate Volume Weighted Average Price"""
        try:
            if 'Volume' not in data.columns or data['Volume'].sum() == 0:
                return data['Close'].iloc[-1]
            
            # Calculate typical price
            typical_price = (data['High'] + data['Low'] + data['Close']) / 3
            
            # Calculate VWAP for last 20 periods
            recent_data = data.tail(20)
            typical_recent = (recent_data['High'] + recent_data['Low'] + recent_data['Close']) / 3
            
            vwap = (typical_recent * recent_data['Volume']).sum() / recent_data['Volume'].sum()
            return vwap
            
        except Exception:
            return data['Close'].iloc[-1]
    
    def _calculate_fibonacci_levels(self, data):
        """Calculate Fibonacci Retracement Levels"""
        try:
            # Find recent swing high and low
            lookback = min(50, len(data))
            recent_data = data.tail(lookback)
            
            swing_high = recent_data['High'].max()
            swing_low = recent_data['Low'].min()
            
            diff = swing_high - swing_low
            
            # Calculate Fibonacci levels
            fib_levels = {
                'fib_0': swing_high,
                'fib_236': swing_high - 0.236 * diff,
                'fib_382': swing_high - 0.382 * diff,
                'fib_500': swing_high - 0.500 * diff,
                'fib_618': swing_high - 0.618 * diff,
                'fib_786': swing_high - 0.786 * diff,
                'fib_100': swing_low,
                'fib_1272': swing_low - 0.272 * diff,  # Extension
                'fib_1618': swing_low - 0.618 * diff   # Extension
            }
            
            return fib_levels
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci levels: {e}")
            current_price = data['Close'].iloc[-1]
            return {f'fib_{level}': current_price for level in ['0', '236', '382', '500', '618', '786', '100', '1272', '1618']}
    
    def _calculate_market_structure_score(self, data):
        """Calculate overall market structure strength score"""
        try:
            if len(data) < 20:
                return 50
            
            score = 50  # Neutral base
            
            # Recent price action (last 10 candles)
            recent = data.tail(10)
            
            # Bullish candles ratio
            bullish_ratio = len(recent[recent['Close'] > recent['Open']]) / len(recent)
            score += (bullish_ratio - 0.5) * 40  # +/- 20 points
            
            # Higher highs and higher lows
            highs = recent['High'].values
            lows = recent['Low'].values
            
            hh_count = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
            hl_count = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
            
            structure_score = (hh_count + hl_count) / (len(highs) - 1)
            score += (structure_score - 0.5) * 30  # +/- 15 points
            
            return max(0, min(100, score))
            
        except Exception:
            return 50
    
    def _calculate_momentum_strength(self, data):
        """Calculate momentum strength (0-100)"""
        try:
            if len(data) < 10:
                return 50
            
            # Price momentum
            price_change = (data['Close'].iloc[-1] - data['Close'].iloc[-10]) / data['Close'].iloc[-10] * 100
            
            # Volume momentum (if available)
            volume_momentum = 0
            if 'Volume' in data.columns and data['Volume'].sum() > 0:
                recent_vol = data['Volume'].tail(5).mean()
                prev_vol = data['Volume'].tail(15).head(10).mean()
                if prev_vol > 0:
                    volume_momentum = (recent_vol - prev_vol) / prev_vol * 100
            
            # Combine momentum factors
            momentum = (price_change * 2 + volume_momentum) / 3
            
            # Scale to 0-100
            momentum_score = 50 + momentum * 2
            return max(0, min(100, momentum_score))
            
        except Exception:
            return 50
    
    def _calculate_volatility_rank(self, data):
        """Calculate volatility rank (0-100)"""
        try:
            if len(data) < 30:
                return 50
            
            # Calculate recent volatility (ATR)
            recent_atr = ta_volatility.AverageTrueRange(
                data['High'].tail(14), 
                data['Low'].tail(14), 
                data['Close'].tail(14)
            ).average_true_range().iloc[-1]
            
            # Calculate historical volatility (last 30 periods)
            historical_atr = ta_volatility.AverageTrueRange(
                data['High'].tail(30), 
                data['Low'].tail(30), 
                data['Close'].tail(30)
            ).average_true_range()
            
            # Rank current volatility
            rank = (historical_atr < recent_atr).sum() / len(historical_atr) * 100
            
            return max(0, min(100, rank))
            
        except Exception:
            return 50
    
    def _calculate_trend_strength(self, indicators):
        """Calculate overall trend strength from multiple indicators"""
        try:
            strength = 50  # Neutral
            
            # Moving average alignment
            if indicators['ema_12'] > indicators['ema_26']:
                strength += 10
            else:
                strength -= 10
            
            # MACD signal
            if indicators['macd'] > indicators['macd_signal']:
                strength += 8
            else:
                strength -= 8
            
            # ADX strength
            if indicators['adx'] > 25:
                if indicators['adx_pos'] > indicators['adx_neg']:
                    strength += 12
                else:
                    strength -= 12
            
            # RSI position
            if 30 < indicators['rsi_14'] < 70:
                strength += 5  # Healthy trend
            elif indicators['rsi_14'] > 70:
                strength += 3  # Overbought but trending
            elif indicators['rsi_14'] < 30:
                strength -= 3  # Oversold
            
            return max(0, min(100, strength))
            
        except Exception:
            return 50
    
    def _get_minimal_indicators(self, data):
        """Fallback minimal indicators when calculation fails"""
        try:
            if data.empty:
                current_price = 3280.0
            else:
                current_price = data['Close'].iloc[-1]
            
            return {
                'sma_20': current_price,
                'ema_12': current_price,
                'rsi_14': 50.0,
                'macd': 0.0,
                'macd_signal': 0.0,
                'bb_upper': current_price * 1.02,
                'bb_lower': current_price * 0.98,
                'atr_14': current_price * 0.01,
                'volume_ratio': 1.0,
                'trend_strength': 50.0,
                'momentum_strength': 50.0,
                'volatility_rank': 50.0
            }
        except Exception:
            return {'error': 'Unable to calculate indicators'}
    def generate_real_ict_signal(self):
        """Generate comprehensive ICT trading signal with 25+ indicators"""
        try:
            logger.info("🚀 Starting Real ICT Signal Generation...")
            
            # Get multi-timeframe data
            mtf_data = self.get_multi_timeframe_data()
            
            if not mtf_data:
                logger.warning("No market data available, using fallback")
                return self._get_enhanced_fallback_signal()
            
            # Use 1H as primary timeframe, 15m for entry refinement
            primary_tf = '1h' if '1h' in mtf_data else '15m' if '15m' in mtf_data else list(mtf_data.keys())[0]
            main_data = mtf_data[primary_tf]
            
            if main_data.empty or len(main_data) < 20:
                logger.warning(f"Insufficient data in {primary_tf} timeframe")
                return self._get_enhanced_fallback_signal()
            
            current_price = main_data['Close'].iloc[-1]
            logger.info(f"📊 Analyzing {len(main_data)} candles on {primary_tf} timeframe")
            logger.info(f"💰 Current Gold Price: ${current_price:.2f}")
            
            # === ICT ANALYSIS ===
            logger.info("🔍 Running ICT Structure Analysis...")
            
            # Market Structure
            market_structure = self.identify_market_structure(main_data)
            logger.info(f"📈 Market Structure: {market_structure['structure']} (Strength: {market_structure['strength']}%)")
            
            # Order Blocks
            order_blocks = self.find_order_blocks(main_data)
            logger.info(f"📦 Found {len(order_blocks)} Order Blocks")
            
            # Fair Value Gaps
            fvgs = self.find_fair_value_gaps(main_data)
            logger.info(f"⚡ Found {len(fvgs)} Fair Value Gaps")
            
            # Liquidity Pools
            liquidity_pools = self.find_liquidity_pools(main_data)
            logger.info(f"💧 Found {len(liquidity_pools)} Liquidity Pools")
            
            # === TECHNICAL ANALYSIS ===
            logger.info("📊 Calculating 25+ Technical Indicators...")
            indicators = self.calculate_comprehensive_indicators(main_data)
            logger.info(f"✅ Calculated {len(indicators)} indicators")
            
            # === MULTI-TIMEFRAME CONFIRMATION ===
            mtf_bias = self._get_multi_timeframe_bias(mtf_data)
            logger.info(f"🕐 Multi-Timeframe Bias: {mtf_bias['overall_bias']} (Strength: {mtf_bias['strength']}%)")
            
            # === SIGNAL GENERATION ===
            logger.info("🎯 Generating Trading Signal...")
            
            signal_data = self._calculate_signal_components(
                current_price, market_structure, order_blocks, 
                fvgs, liquidity_pools, indicators, mtf_bias
            )
            
            # Final signal decision
            final_signal = self._make_final_signal_decision(signal_data, current_price, indicators, mtf_bias)
            
            # === BUILD COMPREHENSIVE RESPONSE ===
            response = {
                'signal': final_signal['direction'],
                'confidence': final_signal['confidence'],
                'current_price': round(current_price, 2),
                
                # ICT Analysis
                'ict_analysis': {
                    'market_structure': market_structure['structure'],
                    'structure_strength': market_structure['strength'],
                    'order_blocks_count': len(order_blocks),
                    'active_order_blocks': self._get_active_order_blocks(order_blocks, current_price),
                    'fair_value_gaps': len(fvgs),
                    'active_fvgs': self._get_active_fvgs(fvgs, current_price),
                    'liquidity_pools': len(liquidity_pools),
                    'nearest_liquidity': self._get_nearest_liquidity(liquidity_pools, current_price)
                },
                
                # Technical Indicators Summary
                'technical_summary': {
                    'trend_direction': self._get_trend_direction(indicators),
                    'trend_strength': indicators.get('trend_strength', 50),
                    'momentum_strength': indicators.get('momentum_strength', 50),
                    'volatility_rank': indicators.get('volatility_rank', 50),
                    'rsi_14': indicators.get('rsi_14', 50),
                    'macd_signal': 'BULLISH' if indicators.get('macd', 0) > indicators.get('macd_signal', 0) else 'BEARISH',
                    'bb_position': self._get_bb_position_detailed(current_price, indicators)
                },
                
                # Multi-Timeframe Analysis
                'multi_timeframe': {
                    'overall_bias': mtf_bias['overall_bias'],
                    'strength': mtf_bias['strength'],
                    'timeframes_analyzed': list(mtf_data.keys()),
                    'primary_timeframe': primary_tf
                },
                
                # Trading Levels
                'trading_levels': {
                    'entry_zone': final_signal['entry_zone'],
                    'stop_loss': final_signal['stop_loss'],
                    'take_profit_1': final_signal['tp1'],
                    'take_profit_2': final_signal['tp2'],
                    'risk_reward_ratio': final_signal['risk_reward']
                },
                
                # Signal Reasoning
                'signal_reasoning': final_signal['reasons'],
                'confluence_factors': signal_data['confluence_count'],
                'signal_quality': self._assess_signal_quality(final_signal['confidence'], signal_data['confluence_count']),
                
                # Key Levels
                'key_levels': {
                    'support_levels': self._get_support_levels(indicators, liquidity_pools),
                    'resistance_levels': self._get_resistance_levels(indicators, liquidity_pools),
                    'pivot_point': indicators.get('pivot_point', current_price)
                },
                
                # Market Context
                'market_context': {
                    'session': self._get_trading_session(),
                    'volatility_environment': self._classify_volatility(indicators.get('volatility_rank', 50)),
                    'trend_environment': self._classify_trend(indicators.get('trend_strength', 50))
                },
                
                # Metadata
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'timeframe_used': primary_tf,
                'data_quality': 'REAL_MARKET_DATA',
                'indicators_count': len(indicators),
                'version': 'ICT_REAL_v2.0'
            }
            
            logger.info(f"🎯 Signal Generated: {final_signal['direction']} (Confidence: {final_signal['confidence']}%)")
            logger.info(f"🔗 Confluence Factors: {signal_data['confluence_count']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in generate_real_ict_signal: {e}")
            return self._get_enhanced_fallback_signal()
    
    def _get_multi_timeframe_bias(self, mtf_data):
        """Analyze bias across multiple timeframes"""
        try:
            timeframe_scores = {}
            
            for tf, data in mtf_data.items():
                if data.empty or len(data) < 10:
                    continue
                
                # Simple trend analysis for each timeframe
                sma_20 = data['Close'].rolling(min(20, len(data))).mean().iloc[-1]
                current_price = data['Close'].iloc[-1]
                
                # Price vs SMA
                if current_price > sma_20:
                    score = 60 + min(((current_price - sma_20) / sma_20) * 1000, 30)
                else:
                    score = 40 - min(((sma_20 - current_price) / sma_20) * 1000, 30)
                
                timeframe_scores[tf] = max(0, min(100, score))
            
            if not timeframe_scores:
                return {'overall_bias': 'NEUTRAL', 'strength': 50, 'details': timeframe_scores}
            
            # Weight timeframes (higher timeframes get more weight)
            weights = {'1d': 3, '4h': 2.5, '1h': 2, '15m': 1.5, '5m': 1, '1m': 0.5}
            
            weighted_score = 0
            total_weight = 0
            
            for tf, score in timeframe_scores.items():
                weight = weights.get(tf, 1)
                weighted_score += score * weight
                total_weight += weight
            
            overall_score = weighted_score / total_weight if total_weight > 0 else 50
            
            if overall_score > 60:
                bias = 'BULLISH'
            elif overall_score < 40:
                bias = 'BEARISH'
            else:
                bias = 'NEUTRAL'
            
            return {
                'overall_bias': bias,
                'strength': round(abs(overall_score - 50) * 2, 1),
                'details': timeframe_scores
            }
            
        except Exception as e:
            logger.error(f"Error in multi-timeframe analysis: {e}")
            return {'overall_bias': 'NEUTRAL', 'strength': 50, 'details': {}}
    
    def _calculate_signal_components(self, current_price, market_structure, order_blocks, fvgs, liquidity_pools, indicators, mtf_bias):
        """Calculate all signal components and confluence"""
        signal_score = 50  # Start neutral
        confluence_factors = []
        reasons = []
        
        try:
            # === ICT STRUCTURE SCORING ===
            
            # Market Structure (20 points max)
            if market_structure['structure'] == 'BULLISH':
                structure_points = market_structure['strength'] * 0.2
                signal_score += structure_points
                confluence_factors.append('BULLISH_STRUCTURE')
                reasons.append(f"Bullish market structure ({market_structure['strength']}%)")
            elif market_structure['structure'] == 'BEARISH':
                structure_points = market_structure['strength'] * 0.2
                signal_score -= structure_points
                confluence_factors.append('BEARISH_STRUCTURE')
                reasons.append(f"Bearish market structure ({market_structure['strength']}%)")
            
            # Order Blocks (15 points max)
            active_obs = self._get_active_order_blocks(order_blocks, current_price)
            for ob in active_obs:
                if ob['type'] == 'BULLISH_OB':
                    signal_score += min(ob['strength'] * 0.15, 15)
                    confluence_factors.append('BULLISH_ORDER_BLOCK')
                    reasons.append("Price at bullish order block")
                elif ob['type'] == 'BEARISH_OB':
                    signal_score -= min(ob['strength'] * 0.15, 15)
                    confluence_factors.append('BEARISH_ORDER_BLOCK')
                    reasons.append("Price at bearish order block")
            
            # Fair Value Gaps (10 points max)
            active_fvgs = self._get_active_fvgs(fvgs, current_price)
            for fvg in active_fvgs:
                if fvg['type'] == 'BULLISH_FVG':
                    signal_score += min(fvg['momentum_strength'] * 0.1, 10)
                    confluence_factors.append('BULLISH_FVG')
                    reasons.append("Price in bullish FVG")
                elif fvg['type'] == 'BEARISH_FVG':
                    signal_score -= min(fvg['momentum_strength'] * 0.1, 10)
                    confluence_factors.append('BEARISH_FVG')
                    reasons.append("Price in bearish FVG")
            
            # === TECHNICAL INDICATORS SCORING ===
            
            # Trend Indicators (15 points max)
            if indicators.get('ema_12', 0) > indicators.get('ema_26', 0):
                signal_score += 8
                confluence_factors.append('EMA_BULLISH')
                reasons.append("EMAs aligned bullish")
            else:
                signal_score -= 8
                confluence_factors.append('EMA_BEARISH')
                reasons.append("EMAs aligned bearish")
            
            # MACD (10 points max)
            if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
                signal_score += 5
                confluence_factors.append('MACD_BULLISH')
            else:
                signal_score -= 5
                confluence_factors.append('MACD_BEARISH')
            
            # RSI (10 points max)
            rsi = indicators.get('rsi_14', 50)
            if rsi < 30:
                signal_score += 10
                confluence_factors.append('RSI_OVERSOLD')
                reasons.append("RSI oversold")
            elif rsi > 70:
                signal_score -= 10
                confluence_factors.append('RSI_OVERBOUGHT')
                reasons.append("RSI overbought")
            elif 40 < rsi < 60:
                signal_score += 2  # Neutral RSI is slightly positive
            
            # === MULTI-TIMEFRAME BIAS ===
            # Increased impact of MTF bias
            mtf_strength_factor = 0.25 # Max impact of 25 points (100 * 0.25)
            if mtf_bias['overall_bias'] == 'BULLISH':
                bias_points = mtf_bias['strength'] * mtf_strength_factor
                signal_score += bias_points
                confluence_factors.append('MTF_BULLISH')
                reasons.append(f"Multi-timeframe bullish bias (strength: {mtf_bias['strength']}%)")
            elif mtf_bias['overall_bias'] == 'BEARISH':
                bias_points = mtf_bias['strength'] * mtf_strength_factor
                signal_score -= bias_points
                confluence_factors.append('MTF_BEARISH')
                reasons.append(f"Multi-timeframe bearish bias (strength: {mtf_bias['strength']}%)")
            else: # Neutral MTF bias
                reasons.append("Multi-timeframe bias is neutral.")
                # Optionally, slightly penalize for neutral MTF if clarity is desired
                # signal_score -= 5 

            # Check for strong MTF opposition to developing signal direction
            # This check is more about dampening a signal if MTF strongly opposes it.
            # The _make_final_signal_decision will also check this, but we can preemptively adjust score here.
            developing_bullish = signal_score > 55 # Tentatively bullish
            developing_bearish = signal_score < 45 # Tentatively bearish

            if developing_bullish and mtf_bias['overall_bias'] == 'BEARISH' and mtf_bias['strength'] > 60:
                signal_score -= 20 # Strong penalty for HTF opposing a bullish setup
                reasons.append("Strong bearish MTF opposes developing bullish signal.")
            elif developing_bearish and mtf_bias['overall_bias'] == 'BULLISH' and mtf_bias['strength'] > 60:
                signal_score += 20 # Effectively a penalty for bearish (moves score towards neutral/bullish)
                reasons.append("Strong bullish MTF opposes developing bearish signal.")

            # === VOLUME CONFIRMATION ===
            volume_ratio = indicators.get('volume_ratio', 1)
            if volume_ratio > 1.5:
                signal_score += 5
                confluence_factors.append('HIGH_VOLUME')
                reasons.append("High volume confirmation")
            elif volume_ratio < 0.7:
                signal_score -= 3
                confluence_factors.append('LOW_VOLUME')
            
            return {
                'signal_score': max(0, min(100, signal_score)),
                'confluence_count': len(set(confluence_factors)),
                'confluence_factors': confluence_factors,
                'reasons': reasons[:5]  # Top 5 reasons
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal components: {e}")
            return {
                'signal_score': 50,
                'confluence_count': 0,
                'confluence_factors': [],
                'reasons': ['Error in analysis']
            }
    
    def _make_final_signal_decision(self, signal_data, current_price_real, indicators_real, mtf_bias_real):
        """Make final trading signal decision with risk management"""
        MIN_RR_RATIO = 1.5  # Minimum acceptable Risk/Reward ratio
        NEUTRAL_MTF_CONFIDENCE_PENALTY = 15 # Penalty for neutral MTF
        OPPOSING_MTF_CONFIDENCE_PENALTY = 30 # Penalty for opposing MTF

        try:
            score = signal_data['signal_score']
            confluence = signal_data['confluence_count']
            
            # Determine signal direction
            if score >= 65 and confluence >= 3:
                direction = 'BUY'
                confidence = min(score + confluence * 2, 95)
            elif score <= 35 and confluence >= 3:
                direction = 'SELL'
                confidence = min((100 - score) + confluence * 2, 95)
            elif score >= 60: # Looser condition for BUY
                direction = 'BUY'
                confidence = min(score + confluence, 85)
            elif score <= 40: # Looser condition for SELL
                direction = 'SELL'
                confidence = min((100 - score) + confluence, 85)
            else:
                direction = 'HOLD'
                confidence = 50
            
            # Apply MTF Bias to confidence
            if direction != 'HOLD':
                if mtf_bias_real['overall_bias'] == 'NEUTRAL':
                    confidence -= NEUTRAL_MTF_CONFIDENCE_PENALTY
                    signal_data['reasons'].append("Neutral MTF bias reduced confidence.")
                elif (direction == 'BUY' and mtf_bias_real['overall_bias'] == 'BEARISH') or \
                     (direction == 'SELL' and mtf_bias_real['overall_bias'] == 'BULLISH'):
                    confidence -= OPPOSING_MTF_CONFIDENCE_PENALTY
                    signal_data['reasons'].append("Opposing MTF bias significantly reduced confidence.")
            
            confidence = max(0, min(confidence, 95)) # Ensure confidence is within bounds

            # Calculate trading levels
            # Use real current_price and ATR from indicators if available
            current_price = current_price_real
            atr = indicators_real.get('atr_14', current_price * 0.01) # Default ATR to 1% of price if not found
            
            if atr is None or atr == 0: # Ensure ATR is a valid positive number
                atr = current_price * 0.01 # Fallback if ATR is zero or None

            entry_low = current_price * 0.999
            entry_high = current_price * 1.001
            
            if direction == 'BUY':
                entry_zone = {'low': round(entry_low, 2), 'high': round(entry_high, 2)}
                stop_loss = current_price - (atr * 1.5)
                tp1 = current_price + (atr * 2)
                tp2 = current_price + (atr * 3.5)
            elif direction == 'SELL':
                entry_zone = {'low': round(entry_low, 2), 'high': round(entry_high, 2)}
                stop_loss = current_price + (atr * 1.5)
                tp1 = current_price - (atr * 2)
                tp2 = current_price - (atr * 3.5)
            else: # HOLD
                entry_zone = {'low': round(current_price, 2), 'high': round(current_price, 2)}
                stop_loss = current_price
                tp1 = current_price
                tp2 = current_price
            
            # Calculate risk-reward ratio
            risk_reward = 0
            if direction != 'HOLD':
                risk = abs(current_price - stop_loss)
                reward = abs(tp1 - current_price)
                risk_reward = round(reward / risk, 2) if risk > 0.00001 else 0 # Avoid division by zero for very small risk

                # Apply RR Filter
                if risk_reward < MIN_RR_RATIO:
                    original_direction = direction
                    direction = 'HOLD'
                    # Reduce confidence significantly if RR is poor, but not to zero unless it was already very low
                    confidence = max(0, confidence - 40) 
                    signal_data['reasons'].append(f"Poor Risk/Reward ({risk_reward:.2f} < {MIN_RR_RATIO}). Original: {original_direction}.")
                    if confidence < 30 and original_direction != 'HOLD': # If confidence drops very low due to RR
                         signal_data['reasons'].append("Signal changed to HOLD due to very low confidence after RR filter.")


            # If confidence is too low after all checks, set to HOLD
            if confidence < 40 and direction != 'HOLD':
                signal_data['reasons'].append(f"Confidence ({confidence:.1f}%) too low. Signal changed to HOLD.")
                direction = 'HOLD'

            return {
                'direction': direction,
                'confidence': round(confidence, 1),
                'entry_zone': entry_zone,
                'stop_loss': round(stop_loss, 2),
                'tp1': round(tp1, 2),
                'tp2': round(tp2, 2),
                'risk_reward': risk_reward,
                'reasons': signal_data['reasons']
            }
            
        except Exception as e:
            logger.error(f"Error making final signal decision: {e}")
            return {
                'direction': 'HOLD',
                'confidence': 50,
                'entry_zone': {'low': 3280, 'high': 3280},
                'stop_loss': 3280,
                'tp1': 3280,
                'tp2': 3280,
                'risk_reward': 0,
                'reasons': ['Error in signal calculation']
            }
    def _get_active_order_blocks(self, order_blocks, current_price):
        """Get active order blocks based on current price"""
        active_obs = []
        tolerance = current_price * 0.001  # 0.1% tolerance
        
        for ob in order_blocks:
            if (ob['low'] - tolerance) <= current_price <= (ob['high'] + tolerance):
                # Calculate distance from current price
                distance = min(
                    abs(current_price - ob['low']),
                    abs(current_price - ob['high'])
                )
                ob['distance'] = distance
                ob['proximity_score'] = max(0, 100 - (distance / current_price * 10000))
                active_obs.append(ob)
        
        # Sort by proximity and strength
        active_obs.sort(key=lambda x: (x['proximity_score'], x['strength']), reverse=True)
        return active_obs[:3]  # Return top 3 most relevant
    
    def _get_active_fvgs(self, fvgs, current_price):
        """Get active Fair Value Gaps based on current price"""
        active_fvgs = []
        tolerance = current_price * 0.0005  # 0.05% tolerance
        
        for fvg in fvgs:
            if not fvg['filled'] and (fvg['low'] - tolerance) <= current_price <= (fvg['high'] + tolerance):
                # Calculate how much of the gap is filled
                fill_percentage = self._calculate_fvg_fill_percentage(fvg, current_price)
                fvg['current_fill'] = fill_percentage
                
                # Only include if less than 80% filled
                if fill_percentage < 80:
                    active_fvgs.append(fvg)
        
        # Sort by momentum strength and fill percentage
        active_fvgs.sort(key=lambda x: (x['momentum_strength'], 100 - x['current_fill']), reverse=True)
        return active_fvgs[:2]  # Return top 2 most relevant
    
    def _get_nearest_liquidity(self, liquidity_pools, current_price):
        """Find nearest liquidity pool to current price"""
        if not liquidity_pools:
            return None
        
        # Calculate distance and add proximity info
        for pool in liquidity_pools:
            pool['distance'] = abs(pool['level'] - current_price)
            pool['distance_percentage'] = (pool['distance'] / current_price) * 100
        
        # Find nearest pool
        nearest = min(liquidity_pools, key=lambda x: x['distance'])
        
        # Only return if within reasonable distance (< 2%)
        if nearest['distance_percentage'] < 2.0:
            return {
                'type': nearest['type'],
                'level': nearest['level'],
                'distance': round(nearest['distance'], 2),
                'distance_percentage': round(nearest['distance_percentage'], 3),
                'strength': nearest['strength'],
                'touches': nearest['touches']
            }
        
        return None
    
    def _get_trend_direction(self, indicators):
        """Determine trend direction from multiple indicators"""
        bullish_signals = 0
        bearish_signals = 0
        
        # EMA alignment
        if indicators.get('ema_12', 0) > indicators.get('ema_26', 0):
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # SMA comparison
        if indicators.get('sma_20', 0) > indicators.get('sma_50', 0):
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # MACD
        if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        # ADX direction
        if indicators.get('adx_pos', 0) > indicators.get('adx_neg', 0):
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        if bullish_signals > bearish_signals:
            return 'BULLISH'
        elif bearish_signals > bullish_signals:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _get_bb_position_detailed(self, price, indicators):
        """Get detailed Bollinger Bands position"""
        try:
            bb_upper = indicators.get('bb_upper')
            bb_lower = indicators.get('bb_lower')
            bb_middle = indicators.get('bb_middle')
            
            if not all([bb_upper, bb_lower, bb_middle]):
                return {'position': 'UNKNOWN', 'percentage': 50}
            
            # Calculate position percentage
            bb_range = bb_upper - bb_lower
            position_percentage = ((price - bb_lower) / bb_range) * 100
            
            # Determine position
            if position_percentage > 80:
                position = 'UPPER'
            elif position_percentage < 20:
                position = 'LOWER'
            elif 45 <= position_percentage <= 55:
                position = 'MIDDLE'
            elif position_percentage > 55:
                position = 'UPPER_MIDDLE'
            else:
                position = 'LOWER_MIDDLE'
            
            return {
                'position': position,
                'percentage': round(position_percentage, 1),
                'squeeze': indicators.get('bb_width', 0) < 2.0  # Tight bands
            }
            
        except Exception:
            return {'position': 'UNKNOWN', 'percentage': 50, 'squeeze': False}
    
    def _get_support_levels(self, indicators, liquidity_pools):
        """Get comprehensive support levels"""
        supports = []
        
        # Pivot supports
        for level in ['support_1', 'support_2', 'support_3']:
            if level in indicators and indicators[level] > 0:
                supports.append({
                    'level': round(indicators[level], 2),
                    'type': 'PIVOT',
                    'strength': 60
                })
        
        # Fibonacci supports
        for fib_level in ['fib_382', 'fib_500', 'fib_618']:
            if fib_level in indicators:
                supports.append({
                    'level': round(indicators[fib_level], 2),
                    'type': 'FIBONACCI',
                    'strength': 70
                })
        
        # Liquidity supports
        for pool in liquidity_pools:
            if pool['type'] == 'BUY_SIDE_LIQUIDITY' and not pool.get('swept', False):
                supports.append({
                    'level': round(pool['level'], 2),
                    'type': 'LIQUIDITY',
                    'strength': min(pool['strength'], 90),
                    'touches': pool['touches']
                })
        
        # Remove duplicates and sort by level
        unique_supports = []
        seen_levels = set()
        
        for support in supports:
            level_key = round(support['level'], 1)  # Group similar levels
            if level_key not in seen_levels:
                seen_levels.add(level_key)
                unique_supports.append(support)
        
        return sorted(unique_supports, key=lambda x: x['level'], reverse=True)[:5]
    
    def _get_resistance_levels(self, indicators, liquidity_pools):
        """Get comprehensive resistance levels"""
        resistances = []
        
        # Pivot resistances
        for level in ['resistance_1', 'resistance_2', 'resistance_3']:
            if level in indicators and indicators[level] > 0:
                resistances.append({
                    'level': round(indicators[level], 2),
                    'type': 'PIVOT',
                    'strength': 60
                })
        
        # Fibonacci resistances
        for fib_level in ['fib_236', 'fib_382', 'fib_618']:
            if fib_level in indicators:
                resistances.append({
                    'level': round(indicators[fib_level], 2),
                    'type': 'FIBONACCI',
                    'strength': 70
                })
        
        # Liquidity resistances
        for pool in liquidity_pools:
            if pool['type'] == 'SELL_SIDE_LIQUIDITY' and not pool.get('swept', False):
                resistances.append({
                    'level': round(pool['level'], 2),
                    'type': 'LIQUIDITY',
                    'strength': min(pool['strength'], 90),
                    'touches': pool['touches']
                })
        
        # Remove duplicates and sort by level
        unique_resistances = []
        seen_levels = set()
        
        for resistance in resistances:
            level_key = round(resistance['level'], 1)
            if level_key not in seen_levels:
                seen_levels.add(level_key)
                unique_resistances.append(resistance)
        
        return sorted(unique_resistances, key=lambda x: x['level'])[:5]
    
    def _get_trading_session(self):
        """Determine current trading session"""
        try:
            now = datetime.utcnow().time()
            
            # Define session times (UTC)
            sessions = {
                'SYDNEY': (datetime.strptime('21:00', '%H:%M').time(), datetime.strptime('06:00', '%H:%M').time()),
                'TOKYO': (datetime.strptime('00:00', '%H:%M').time(), datetime.strptime('09:00', '%H:%M').time()),
                'LONDON': (datetime.strptime('08:00', '%H:%M').time(), datetime.strptime('17:00', '%H:%M').time()),
                'NEW_YORK': (datetime.strptime('13:00', '%H:%M').time(), datetime.strptime('22:00', '%H:%M').time())
            }
            
            # Check which session is active
            for session, (start, end) in sessions.items():
                if start <= end:  # Same day
                    if start <= now <= end:
                        return session
                else:  # Crosses midnight
                    if now >= start or now <= end:
                        return session
            
            return 'OFF_HOURS'
            
        except Exception:
            return 'UNKNOWN'
    
    def _classify_volatility(self, volatility_rank):
        """Classify volatility environment"""
        if volatility_rank > 80:
            return 'EXTREMELY_HIGH'
        elif volatility_rank > 60:
            return 'HIGH'
        elif volatility_rank > 40:
            return 'MEDIUM'
        elif volatility_rank > 20:
            return 'LOW'
        else:
            return 'EXTREMELY_LOW'
    
    def _classify_trend(self, trend_strength):
        """Classify trend environment"""
        if trend_strength > 80:
            return 'VERY_STRONG'
        elif trend_strength > 60:
            return 'STRONG'
        elif trend_strength > 40:
            return 'MODERATE'
        elif trend_strength > 20:
            return 'WEAK'
        else:
            return 'VERY_WEAK'
    
    def _assess_signal_quality(self, confidence, confluence_count):
        """Assess overall signal quality"""
        if confidence >= 85 and confluence_count >= 5:
            return 'EXCELLENT'
        elif confidence >= 75 and confluence_count >= 4:
            return 'VERY_GOOD'
        elif confidence >= 65 and confluence_count >= 3:
            return 'GOOD'
        elif confidence >= 55 and confluence_count >= 2:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _get_enhanced_fallback_signal(self):
        """Enhanced fallback signal when real analysis fails"""
        current_time = datetime.now()
        
        # Generate realistic fallback based on time and basic patterns
        base_price = 3280.0
        
        # Add some realistic variation based on time
        time_factor = (current_time.hour * 60 + current_time.minute) / 1440  # 0-1
        price_variation = (time_factor - 0.5) * 20  # +/- 10
        
        fallback_price = base_price + price_variation
        
        return {
            'signal': 'HOLD',
            'confidence': 50,
            'current_price': round(fallback_price, 2),
            
            'ict_analysis': {
                'market_structure': 'UNKNOWN',
                'structure_strength': 0,
                'order_blocks_count': 0,
                'active_order_blocks': [],
                'fair_value_gaps': 0,
                'active_fvgs': [],
                'liquidity_pools': 0,
                'nearest_liquidity': None
            },
            
            'technical_summary': {
                'trend_direction': 'NEUTRAL',
                'trend_strength': 50,
                'momentum_strength': 50,
                'volatility_rank': 50,
                'rsi_14': 50,
                'macd_signal': 'NEUTRAL',
                'bb_position': {'position': 'MIDDLE', 'percentage': 50}
            },
            
            'multi_timeframe': {
                'overall_bias': 'NEUTRAL',
                'strength': 0,
                'timeframes_analyzed': [],
                'primary_timeframe': 'FALLBACK'
            },
            
            'trading_levels': {
                'entry_zone': {'low': fallback_price, 'high': fallback_price},
                'stop_loss': fallback_price,
                'take_profit_1': fallback_price,
                'take_profit_2': fallback_price,
                'risk_reward_ratio': 0
            },
            
            'signal_reasoning': ['Market data unavailable', 'Using fallback analysis'],
            'confluence_factors': 0,
            'signal_quality': 'POOR',
            
            'key_levels': {
                'support_levels': [],
                'resistance_levels': [],
                'pivot_point': fallback_price
            },
            
            'market_context': {
                'session': self._get_trading_session(),
                'volatility_environment': 'UNKNOWN',
                'trend_environment': 'UNKNOWN'
            },
            
            'analysis_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'timeframe_used': 'FALLBACK',
            'data_quality': 'FALLBACK_MODE',
            'indicators_count': 0,
            'version': 'ICT_REAL_v2.0_FALLBACK'
        }

# Backward compatibility alias
TechnicalAnalyzer = RealICTAnalyzer

# For direct usage
def analyze_market_structure():
    """Direct function for market analysis"""
    analyzer = RealICTAnalyzer()
    return analyzer.generate_real_ict_signal()
