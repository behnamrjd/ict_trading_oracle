# Signal Generator 
"""
Signal Generation Core Module
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional
import logging

from core.ict_analyzer import ICTAnalyzer
from core.market_data import MarketDataProvider
from ai_models.ensemble import EnsembleModel
from signals.queue import SignalQueue
from subscription.manager import SubscriptionManager

logger = logging.getLogger(__name__)

class SignalGenerator:
    """تولیدکننده سیگنال اصلی"""
    
    def __init__(self):
        self.ict_analyzer = ICTAnalyzer()
        self.market_data_provider = MarketDataProvider()
        self.ensemble_model = EnsembleModel()
        self.signal_queue = SignalQueue()
        self.subscription_manager = SubscriptionManager()
        
        self._background_task = None
        self._running = False
    
    async def initialize(self):
        """راه‌اندازی اولیه"""
        try:
            await self.market_data_provider.initialize()
            await self.ensemble_model.initialize()
            
            # شروع تولید سیگنال پس‌زمینه
            self._running = True
            self._background_task = asyncio.create_task(self._background_signal_generation())
            
            logger.info("Signal generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing signal generator: {e}")
            raise
    
    async def generate_signal_for_user(self, user_id: int) -> Dict:
        """تولید سیگنال برای کاربر خاص"""
        try:
            # بررسی اشتراک کاربر
            subscription = self.subscription_manager.get_user_subscription(user_id)
            
            if subscription['type'] == 'free':
                return await self._generate_free_user_signal(user_id)
            else:
                return await self._generate_premium_signal()
                
        except Exception as e:
            logger.error(f"Error generating signal for user {user_id}: {e}")
            return None
    
    async def _generate_free_user_signal(self, user_id: int) -> Optional[Dict]:
        """تولید سیگنال برای کاربر رایگان"""
        try:
            # ابتدا بررسی صف سیگنال‌های آماده
            queued_signal = self.signal_queue.get_best_signal()
            
            if queued_signal:
                # کاهش سهمیه کاربر
                self.subscription_manager.consume_signal_quota(user_id)
                return queued_signal['signal']
            
            # اگر سیگنال آماده نیست، بررسی شرایط فعلی
            current_conditions = await self._analyze_current_conditions()
            
            if current_conditions['quality_score'] >= 85:
                # تولید سیگنال جدید
                signal = await self._generate_premium_signal()
                if signal and signal['final_confidence'] >= 85:
                    self.subscription_manager.consume_signal_quota(user_id)
                    return signal
            
            # پیشنهاد زمان بهتر
            return {
                'type': 'timing_suggestion',
                'current_conditions': current_conditions,
                'message': 'بهتر است در زمان مناسب‌تری سیگنال درخواست کنید'
            }
            
        except Exception as e:
            logger.error(f"Error generating free user signal: {e}")
            return None
    
    async def _generate_premium_signal(self) -> Optional[Dict]:
        """تولید سیگنال پریمیوم"""
        try:
            # دریافت داده‌های بازار
            market_data = await self.market_data_provider.get_data()
            if market_data is None:
                return None
            
            # تحلیل ICT
            ict_analysis = await self._analyze_ict_comprehensive(market_data)
            
            # تحلیل تکنیکال
            technical_analysis = await self._analyze_technical_indicators(market_data)
            
            # ترکیب تحلیل‌ها
            final_signal = self._combine_analyses(ict_analysis, technical_analysis)
            
            return final_signal
            
        except Exception as e:
            logger.error(f"Error generating premium signal: {e}")
            return None
    
    async def _background_signal_generation(self):
        """تولید مداوم سیگنال در پس‌زمینه"""
        while self._running:
            try:
                # تولید سیگنال
                signal = await self._generate_premium_signal()
                
                if signal and signal['signal_quality'] == 'EXCELLENT':
                    # اضافه کردن به صف برای کاربران رایگان
                    self.signal_queue.add_signal(signal)
                
                # انتظار قبل از تولید بعدی
                await asyncio.sleep(300)  # 5 دقیقه
                
            except Exception as e:
                logger.error(f"Error in background signal generation: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_current_conditions(self) -> Dict:
        """تحلیل شرایط فعلی بازار"""
        try:
            kill_zones = self.ict_analyzer.analyze_kill_zones()
            market_data = await self.market_data_provider.get_data()
            
            quality_score = 50
            
            # Kill Zone Quality
            if kill_zones['session_quality'] == 'PREMIUM':
                quality_score += 30
            elif kill_zones['session_quality'] == 'HIGH':
                quality_score += 20
            
            # Market Data Quality
            if market_data is not None:
                volatility_score = self._calculate_volatility_score(market_data)
                quality_score += volatility_score * 20
            
            return {
                'quality_score': min(100, quality_score),
                'kill_zone_quality': kill_zones['session_quality'],
                'optimal_time': kill_zones['optimal_time']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing current conditions: {e}")
            return {'quality_score': 50}
    
    def _calculate_volatility_score(self, data) -> float:
        """محاسبه امتیاز نوسانات"""
        try:
            import ta
            
            if len(data) < 20:
                return 1.0
            
            atr = ta.volatility.AverageTrueRange(
                data['High'], data['Low'], data['Close']
            ).average_true_range()
            
            current_atr = atr.iloc[-1]
            avg_atr = atr.tail(20).mean()
            
            return min(2.0, current_atr / avg_atr if avg_atr > 0 else 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating volatility score: {e}")
            return 1.0
    
    async def _analyze_ict_comprehensive(self, data) -> Dict:
        """تحلیل جامع ICT"""
        try:
            current_price = data['Close'].iloc[-1]
            previous_close = data['Close'].iloc[-2]
            change = ((current_price - previous_close) / previous_close) * 100
            
            # تحلیل‌های ICT
            market_structure = self.ict_analyzer.analyze_market_structure(data)
            bos_analysis = self.ict_analyzer.detect_break_of_structure(data)
            liquidity_zones = self.ict_analyzer.identify_liquidity_zones(data)
            order_blocks = self.ict_analyzer.detect_order_blocks(data)
            fvgs = self.ict_analyzer.detect_fair_value_gaps(data)
            kill_zones = self.ict_analyzer.analyze_kill_zones()
            ote_analysis = self.ict_analyzer.calculate_optimal_trade_entry(data)
            
            # محاسبه امتیاز ICT
            ict_score = 0
            reasoning = []
            
            # Market Structure (25 امتیاز)
            if market_structure['structure'] == 'BULLISH':
                ict_score += 25
                reasoning.append('Bullish market structure')
            elif market_structure['structure'] == 'BEARISH':
                ict_score += 25
                reasoning.append('Bearish market structure')
            else:
                ict_score += 10
                reasoning.append('Neutral market structure')
            
            # Break of Structure (20 امتیاز)
            if bos_analysis['bos_detected']:
                ict_score += 20
                reasoning.append(f"{bos_analysis['bos_type']} detected")
            
            # Order Blocks (15 امتیاز)
            if order_blocks:
                for ob in order_blocks:
                    if abs(current_price - ob['level']) / current_price < 0.005:
                        ict_score += 15
                        reasoning.append(f"Near {ob['type']} order block")
                        break
            
            # Fair Value Gaps (15 امتیاز)
            for fvg in fvgs:
                if (current_price >= min(fvg['upper'], fvg['lower']) and 
                    current_price <= max(fvg['upper'], fvg['lower'])):
                    ict_score += 15
                    reasoning.append(f"Trading in {fvg['type']} FVG")
                    break
            
            # Kill Zones (10 امتیاز)
            if kill_zones['session_quality'] == 'PREMIUM':
                ict_score += 10
                reasoning.append('Premium kill zone active')
            elif kill_zones['session_quality'] == 'HIGH':
                ict_score += 7
                reasoning.append('High-quality kill zone')
            
            # OTE (10 امتیاز)
            if ote_analysis.get('in_ote_zone'):
                ict_score += 10
                reasoning.append(f"In OTE zone: {ote_analysis['level']}")
            
            # Liquidity (5 امتیاز)
            if liquidity_zones:
                ict_score += 5
                reasoning.append(f"{len(liquidity_zones)} liquidity zones identified")
            
            # تعیین سیگنال بر اساس ICT
            if market_structure['structure'] == 'BULLISH' and bos_analysis.get('bos_type') == 'BULLISH_BOS':
                ict_signal = 'BUY'
            elif market_structure['structure'] == 'BEARISH' and bos_analysis.get('bos_type') == 'BEARISH_BOS':
                ict_signal = 'SELL'
            else:
                ict_signal = 'HOLD'
            
            return {
                'signal': ict_signal,
                'score': min(100, ict_score),
                'reasoning': reasoning,
                'market_structure': market_structure,
                'bos_analysis': bos_analysis,
                'order_blocks': len(order_blocks),
                'fair_value_gaps': len(fvgs),
                'kill_zone_quality': kill_zones['session_quality'],
                'in_ote_zone': ote_analysis.get('in_ote_zone', False),
                'price': current_price,
                'change': change
            }
            
        except Exception as e:
            logger.error(f"Error in ICT analysis: {e}")
            return {'signal': 'HOLD', 'score': 50, 'reasoning': ['Error in analysis']}
    
    async def _analyze_technical_indicators(self, data) -> Dict:
        """تحلیل اندیکاتورهای تکنیکال ساده"""
        try:
            import ta
            
            # محاسبه اندیکاتورهای اصلی
            rsi = ta.momentum.RSIIndicator(data['Close'], window=14).rsi().iloc[-1]
            
            macd_indicator = ta.trend.MACD(data['Close'])
            macd = macd_indicator.macd().iloc[-1]
            macd_signal = macd_indicator.macd_signal().iloc[-1]
            
            # تحلیل ساده
            technical_score = 50
            reasoning = []
            
            # RSI Analysis
            if rsi < 30:
                technical_score += 20
                reasoning.append('RSI oversold')
            elif rsi > 70:
                technical_score += 20
                reasoning.append('RSI overbought')
            
            # MACD Analysis
            if macd > macd_signal:
                technical_score += 15
                reasoning.append('MACD bullish')
            else:
                technical_score -= 15
                reasoning.append('MACD bearish')
            
            # تعیین سیگنال
            if rsi < 30 and macd > macd_signal:
                tech_signal = 'BUY'
            elif rsi > 70 and macd < macd_signal:
                tech_signal = 'SELL'
            else:
                tech_signal = 'HOLD'
            
            return {
                'signal': tech_signal,
                'score': min(100, max(0, technical_score)),
                'reasoning': reasoning,
                'rsi': round(rsi, 1),
                'macd': round(macd, 4)
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
            return {'signal': 'HOLD', 'score': 50, 'reasoning': ['Error in analysis']}
    
    def _combine_analyses(self, ict_analysis, technical_analysis) -> Dict:
        """ترکیب تحلیل‌ها با وزن‌دهی بهینه"""
        try:
            # وزن‌های بهینه شده
            weights = {
                'ict': 0.70,      # ICT وزن اصلی
                'technical': 0.30  # تکنیکال
            }
            
            # امتیازدهی سیگنال‌ها
            signal_scores = {'BUY': 0, 'HOLD': 0, 'SELL': 0}
            
            # ICT Score
            ict_weight = weights['ict'] * (ict_analysis['score'] / 100)
            signal_scores[ict_analysis['signal']] += ict_weight
            
            # Technical Score
            tech_weight = weights['technical'] * (technical_analysis['score'] / 100)
            signal_scores[technical_analysis['signal']] += tech_weight
            
            # تعیین سیگنال نهایی
            final_signal = max(signal_scores, key=signal_scores.get)
            final_confidence = signal_scores[final_signal] * 100
            
            # محاسبه کیفیت سیگنال
            signal_agreement = 0
            if ict_analysis['signal'] == final_signal:
                signal_agreement += 70
            if technical_analysis['signal'] == final_signal:
                signal_agreement += 30
            
            # تعیین کیفیت
            if final_confidence > 75 and signal_agreement > 70:
                signal_quality = 'EXCELLENT'
            elif final_confidence > 60 and signal_agreement > 50:
                signal_quality = 'GOOD'
            elif final_confidence > 45:
                signal_quality = 'FAIR'
            else:
                signal_quality = 'POOR'
            
            # ترکیب دلایل
            all_reasoning = []
            all_reasoning.extend(ict_analysis['reasoning'])
            all_reasoning.extend(technical_analysis['reasoning'])
            
            return {
                'final_signal': final_signal,
                'final_confidence': round(final_confidence, 1),
                'signal_quality': signal_quality,
                'signal_agreement': round(signal_agreement, 1),
                'reasoning': ', '.join(all_reasoning),
                
                # تفکیک امتیازها
                'ict_contribution': round(ict_weight * 100, 1),
                'technical_contribution': round(tech_weight * 100, 1),
                
                # جزئیات ICT
                'market_structure': ict_analysis['market_structure']['structure'],
                'bos_detected': ict_analysis['bos_analysis']['bos_detected'],
                'order_blocks': ict_analysis['order_blocks'],
                'fair_value_gaps': ict_analysis['fair_value_gaps'],
                'kill_zone_quality': ict_analysis['kill_zone_quality'],
                'in_ote_zone': ict_analysis['in_ote_zone'],
                
                # داده‌های بازار
                'price': ict_analysis['price'],
                'change': ict_analysis['change'],
                'rsi': technical_analysis['rsi'],
                'macd': technical_analysis['macd'],
                
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return {
                'final_signal': 'HOLD',
                'final_confidence': 50,
                'signal_quality': 'POOR',
                'error': str(e)
            }
    
    async def stop(self):
        """توقف تولید سیگنال"""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
