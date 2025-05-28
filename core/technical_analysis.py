"""
Enhanced Technical Analysis with AI for ICT Trading
"""

import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta
import logging
from ai_models.ml_predictor import MLPredictor
from ai_models.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

class EnhancedTechnicalAnalyzer:
    def __init__(self):
        self.symbol = "GC=F"  # Gold futures
        self.ml_predictor = MLPredictor()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def get_market_data(self, period="5d"):
        """Get market data for analysis"""
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period=period, interval="1h")
            return data
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    def analyze_market_with_ai(self, news_data=None):
        """Enhanced market analysis with AI"""
        try:
            # Get market data
            data = self.get_market_data("10d")  # More data for AI
            if data is None or data.empty:
                return self._get_fallback_analysis()
            
            # Traditional technical analysis
            traditional_analysis = self._traditional_analysis(data)
            
            # AI-powered prediction
            ai_prediction = self.ml_predictor.predict(data)
            
            # Sentiment analysis
            sentiment_analysis = None
            if news_data:
                sentiment_analysis = self.sentiment_analyzer.analyze_news_sentiment(news_data)
            
            # Combine all analyses
            combined_analysis = self._combine_analyses(
                traditional_analysis, 
                ai_prediction, 
                sentiment_analysis
            )
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {e}")
            return self._get_fallback_analysis()
    
    def _traditional_analysis(self, data):
        """Traditional technical analysis"""
        try:
            # Calculate technical indicators
            data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
            data['MACD'] = ta.trend.MACD(data['Close']).macd()
            data['MACD_Signal'] = ta.trend.MACD(data['Close']).macd_signal()
            data['BB_upper'] = ta.volatility.BollingerBands(data['Close']).bollinger_hband()
            data['BB_lower'] = ta.volatility.BollingerBands(data['Close']).bollinger_lband()
            data['BB_middle'] = ta.volatility.BollingerBands(data['Close']).bollinger_mavg()
            
            current_price = data['Close'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            macd = data['MACD'].iloc[-1]
            macd_signal = data['MACD_Signal'].iloc[-1]
            bb_upper = data['BB_upper'].iloc[-1]
            bb_lower = data['BB_lower'].iloc[-1]
            bb_middle = data['BB_middle'].iloc[-1]
            
            # Market structure analysis
            sma_20 = data['Close'].rolling(20).mean().iloc[-1]
            market_structure = "BULLISH" if current_price > sma_20 else "BEARISH"
            
            # Order block detection (simplified)
            volume_avg = data['Volume'].rolling(20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            order_block = "STRONG" if current_volume > volume_avg * 1.5 else "WEAK"
            
            # Fair Value Gap detection
            gap_threshold = current_price * 0.001  # 0.1% gap
            prev_high = data['High'].iloc[-2]
            current_low = data['Low'].iloc[-1]
            fvg_status = "ACTIVE" if current_low > prev_high + gap_threshold else "NEUTRAL"
            
            # Generate signal based on multiple indicators
            signals = []
            
            # RSI signals
            if rsi < 30:
                signals.append(('BUY', 70))
            elif rsi > 70:
                signals.append(('SELL', 70))
            
            # MACD signals
            if macd > macd_signal and macd > 0:
                signals.append(('BUY', 65))
            elif macd < macd_signal and macd < 0:
                signals.append(('SELL', 65))
            
            # Bollinger Bands signals
            if current_price < bb_lower:
                signals.append(('BUY', 60))
            elif current_price > bb_upper:
                signals.append(('SELL', 60))
            
            # Determine final signal
            if signals:
                buy_signals = [s for s in signals if s[0] == 'BUY']
                sell_signals = [s for s in signals if s[0] == 'SELL']
                
                if len(buy_signals) > len(sell_signals):
                    signal = 'BUY'
                    confidence = sum(s[1] for s in buy_signals) / len(buy_signals)
                elif len(sell_signals) > len(buy_signals):
                    signal = 'SELL'
                    confidence = sum(s[1] for s in sell_signals) / len(sell_signals)
                else:
                    signal = 'HOLD'
                    confidence = 50
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'signal': signal,
                'confidence': round(confidence, 1),
                'current_price': round(current_price, 2),
                'market_structure': market_structure,
                'order_block': order_block,
                'fvg_status': fvg_status,
                'technical_indicators': {
                    'rsi': round(rsi, 2),
                    'macd': round(macd, 4),
                    'bb_position': round((current_price - bb_lower) / (bb_upper - bb_lower), 3),
                    'volume_ratio': round(current_volume / volume_avg, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in traditional analysis: {e}")
            return self._get_fallback_analysis()
    
    def _combine_analyses(self, traditional, ai_prediction, sentiment):
        """Combine traditional, AI, and sentiment analyses"""
        try:
            # Start with traditional analysis
            final_analysis = traditional.copy()
            
            # Weight the signals
            traditional_weight = 0.4
            ai_weight = 0.4
            sentiment_weight = 0.2
            
            signals = []
            confidences = []
            
            # Traditional signal
            if traditional['signal'] != 'HOLD':
                signals.append((traditional['signal'], traditional['confidence'] * traditional_weight))
                confidences.append(traditional['confidence'] * traditional_weight)
            
            # AI signal
            if ai_prediction and ai_prediction['signal_direction'] != 'HOLD':
                signals.append((ai_prediction['signal_direction'], ai_prediction['confidence'] * ai_weight))
                confidences.append(ai_prediction['confidence'] * ai_weight)
            
            # Sentiment signal
            if sentiment:
                sentiment_signal = self.sentiment_analyzer.get_market_sentiment_signal(sentiment)
                if sentiment_signal['signal'] != 'HOLD':
                    signals.append((sentiment_signal['signal'], sentiment_signal['confidence'] * sentiment_weight))
                    confidences.append(sentiment_signal['confidence'] * sentiment_weight)
            
            # Determine final signal
            if signals:
                buy_signals = [s for s in signals if s[0] == 'BUY']
                sell_signals = [s for s in signals if s[0] == 'SELL']
                
                buy_strength = sum(s[1] for s in buy_signals)
                sell_strength = sum(s[1] for s in sell_signals)
                
                if buy_strength > sell_strength and buy_strength > 30:
                    final_signal = 'BUY'
                    final_confidence = min(buy_strength, 95)
                elif sell_strength > buy_strength and sell_strength > 30:
                    final_signal = 'SELL'
                    final_confidence = min(sell_strength, 95)
                else:
                    final_signal = 'HOLD'
                    final_confidence = 50
            else:
                final_signal = traditional['signal']
                final_confidence = traditional['confidence']
            
            # Update final analysis
            final_analysis.update({
                'signal': final_signal,
                'confidence': round(final_confidence, 1),
                'analysis_type': 'AI_ENHANCED',
                'ai_prediction': ai_prediction,
                'sentiment_analysis': sentiment,
                'signal_breakdown': {
                    'traditional': {
                        'signal': traditional['signal'],
                        'confidence': traditional['confidence'],
                        'weight': traditional_weight
                    },
                    'ai': {
                        'signal': ai_prediction['signal_direction'] if ai_prediction else 'HOLD',
                        'confidence': ai_prediction['confidence'] if ai_prediction else 50,
                        'weight': ai_weight
                    },
                    'sentiment': {
                        'signal': sentiment_signal['signal'] if sentiment else 'HOLD',
                        'confidence': sentiment_signal['confidence'] if sentiment else 50,
                        'weight': sentiment_weight
                    }
                },
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            return final_analysis
            
        except Exception as e:
            logger.error(f"Error combining analyses: {e}")
            return traditional
    
    def _get_fallback_analysis(self):
        """Fallback analysis when all methods fail"""
        return {
            'signal': 'HOLD',
            'confidence': 50,
            'current_price': 2350.25,
            'market_structure': 'NEUTRAL',
            'order_block': 'WEAK',
            'fvg_status': 'NEUTRAL',
            'analysis_type': 'FALLBACK',
            'technical_indicators': {
                'rsi': 50,
                'macd': 0,
                'bb_position': 0.5,
                'volume_ratio': 1.0
            },
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
