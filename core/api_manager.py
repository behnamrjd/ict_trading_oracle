"""
API Manager for ICT Trading Oracle
"""

import requests
import yfinance as yf
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.tgju_api_url = os.getenv('TGJU_API_URL')
    
    def get_gold_price(self):
        """Get live gold price from Yahoo Finance"""
        try:
            # Get gold futures data (GC=F)
            gold = yf.Ticker("GC=F")
            hist = gold.history(period="1d")
            
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Open'].iloc[-1]
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            return {
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"Error fetching gold price: {e}")
            return None
    
    def get_gold_news(self):
        """Get gold-related news from NewsAPI"""
        try:
            if not self.news_api_key or self.news_api_key == "YOUR_NEWSAPI_KEY_FROM_NEWSAPI_ORG":
                return self._get_sample_news()
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'gold trading market price',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 5,
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('articles', [])[:3]  # Return top 3 news
            else:
                return self._get_sample_news()
                
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return self._get_sample_news()
    
    def _get_sample_news(self):
        """Sample news when API is not available"""
        return [
            {
                'title': 'Gold Prices Rise Amid Market Uncertainty',
                'description': 'Gold futures climb as investors seek safe-haven assets...',
                'url': 'https://example.com/news1',
                'publishedAt': datetime.now().isoformat()
            },
            {
                'title': 'Federal Reserve Policy Impact on Gold',
                'description': 'Latest Fed decisions affecting precious metals market...',
                'url': 'https://example.com/news2',
                'publishedAt': datetime.now().isoformat()
            }
        ]
    
    def get_tgju_data(self):
        """Get data from TGJU API (Iranian gold prices)"""
        try:
            if not self.tgju_api_url:
                return None
            
            response = requests.get(self.tgju_api_url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching TGJU data: {e}")
            return None
