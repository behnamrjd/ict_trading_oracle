# Market Data Provider 
"""
Market Data Provider
"""

import yfinance as yf
import pandas as pd
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MarketDataProvider:
    """ارائه‌دهنده داده‌های بازار"""
    
    def __init__(self):
        self.symbol = "GC=F"
        self.cache = {}
        self.cache_timeout = 60  # 1 minute cache
        
    async def initialize(self):
        """راه‌اندازی اولیه"""
        try:
            # تست اتصال
            test_data = await self.get_data(period="1d", interval="1h")
            if test_data is not None:
                logger.info("Market data provider initialized successfully")
            else:
                logger.warning("Market data provider test failed")
                
        except Exception as e:
            logger.error(f"Error initializing market data provider: {e}")
    
    async def get_data(self, period="30d", interval="1h") -> Optional[pd.DataFrame]:
        """دریافت داده‌های بازار"""
        try:
            cache_key = f"{self.symbol}_{period}_{interval}"
            
            # بررسی cache
            if cache_key in self.cache:
                cache_data, cache_time = self.cache[cache_key]
                if (pd.Timestamp.now() - cache_time).total_seconds() < self.cache_timeout:
                    return cache_data
            
            # دریافت داده جدید
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                self._fetch_data_sync, 
                period, 
                interval
            )
            
            if data is not None and not data.empty:
                # ذخیره در cache
                self.cache[cache_key] = (data, pd.Timestamp.now())
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    def _fetch_data_sync(self, period: str, interval: str) -> Optional[pd.DataFrame]:
        """دریافت همزمان داده‌ها"""
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data received for {self.symbol}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Error in sync data fetch: {e}")
            return None
    
    async def get_current_price(self) -> Optional[float]:
        """دریافت قیمت فعلی"""
        try:
            data = await self.get_data(period="1d", interval="1m")
            if data is not None and not data.empty:
                return float(data['Close'].iloc[-1])
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    def clear_cache(self):
        """پاک کردن cache"""
        self.cache.clear()
