"""
Sentiment Analysis for ICT Trading Oracle
"""

import requests
import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
    def analyze_news_sentiment(self, news_articles):
        """Analyze sentiment of news articles"""
        try:
            if not news_articles:
                return self._default_sentiment()
            
            sentiments = []
            
            for article in news_articles:
                title = article.get('title', '')
                description = article.get('description', '')
                
                # Combine title and description
                text = f"{title} {description}"
                
                # Clean text
                text = self._clean_text(text)
                
                if text:
                    sentiment = self._analyze_text_sentiment(text)
                    sentiments.append(sentiment)
            
            if not sentiments:
                return self._default_sentiment()
            
            # Calculate average sentiment
            avg_sentiment = {
                'compound': sum(s['compound'] for s in sentiments) / len(sentiments),
                'positive': sum(s['positive'] for s in sentiments) / len(sentiments),
                'negative': sum(s['negative'] for s in sentiments) / len(sentiments),
                'neutral': sum(s['neutral'] for s in sentiments) / len(sentiments),
                'polarity': sum(s['polarity'] for s in sentiments) / len(sentiments),
                'subjectivity': sum(s['subjectivity'] for s in sentiments) / len(sentiments)
            }
            
            # Determine overall sentiment
            if avg_sentiment['compound'] >= 0.05:
                overall = 'BULLISH'
                impact = 'POSITIVE'
            elif avg_sentiment['compound'] <= -0.05:
                overall = 'BEARISH'
                impact = 'NEGATIVE'
            else:
                overall = 'NEUTRAL'
                impact = 'NEUTRAL'
            
            return {
                'overall_sentiment': overall,
                'market_impact': impact,
                'confidence': abs(avg_sentiment['compound']),
                'sentiment_score': round(avg_sentiment['compound'], 3),
                'positive_ratio': round(avg_sentiment['positive'], 3),
                'negative_ratio': round(avg_sentiment['negative'], 3),
                'polarity': round(avg_sentiment['polarity'], 3),
                'subjectivity': round(avg_sentiment['subjectivity'], 3),
                'articles_analyzed': len(sentiments),
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return self._default_sentiment()
    
    def _analyze_text_sentiment(self, text):
        """Analyze sentiment of a single text"""
        try:
            # VADER sentiment analysis
            vader_scores = self.vader_analyzer.polarity_scores(text)
            
            # TextBlob sentiment analysis
            blob = TextBlob(text)
            
            return {
                'compound': vader_scores['compound'],
                'positive': vader_scores['pos'],
                'negative': vader_scores['neg'],
                'neutral': vader_scores['neu'],
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text sentiment: {e}")
            return {
                'compound': 0,
                'positive': 0.33,
                'negative': 0.33,
                'neutral': 0.33,
                'polarity': 0,
                'subjectivity': 0.5
            }
    
    def _clean_text(self, text):
        """Clean and preprocess text"""
        try:
            if not text:
                return ""
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Remove URLs
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except:
            return ""
    
    def _default_sentiment(self):
        """Default sentiment when analysis fails"""
        return {
            'overall_sentiment': 'NEUTRAL',
            'market_impact': 'NEUTRAL',
            'confidence': 0.5,
            'sentiment_score': 0.0,
            'positive_ratio': 0.33,
            'negative_ratio': 0.33,
            'polarity': 0.0,
            'subjectivity': 0.5,
            'articles_analyzed': 0,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_market_sentiment_signal(self, sentiment_data):
        """Convert sentiment to trading signal"""
        try:
            sentiment_score = sentiment_data['sentiment_score']
            confidence = sentiment_data['confidence']
            
            # Strong positive sentiment
            if sentiment_score > 0.3 and confidence > 0.7:
                return {
                    'signal': 'BUY',
                    'strength': 'STRONG',
                    'confidence': min(confidence * 100, 95),
                    'reason': 'Strong positive market sentiment'
                }
            
            # Moderate positive sentiment
            elif sentiment_score > 0.1 and confidence > 0.5:
                return {
                    'signal': 'BUY',
                    'strength': 'MODERATE',
                    'confidence': min(confidence * 80, 85),
                    'reason': 'Moderate positive market sentiment'
                }
            
            # Strong negative sentiment
            elif sentiment_score < -0.3 and confidence > 0.7:
                return {
                    'signal': 'SELL',
                    'strength': 'STRONG',
                    'confidence': min(confidence * 100, 95),
                    'reason': 'Strong negative market sentiment'
                }
            
            # Moderate negative sentiment
            elif sentiment_score < -0.1 and confidence > 0.5:
                return {
                    'signal': 'SELL',
                    'strength': 'MODERATE',
                    'confidence': min(confidence * 80, 85),
                    'reason': 'Moderate negative market sentiment'
                }
            
            # Neutral sentiment
            else:
                return {
                    'signal': 'HOLD',
                    'strength': 'WEAK',
                    'confidence': 50,
                    'reason': 'Neutral market sentiment'
                }
                
        except Exception as e:
            logger.error(f"Error generating sentiment signal: {e}")
            return {
                'signal': 'HOLD',
                'strength': 'WEAK',
                'confidence': 50,
                'reason': 'Sentiment analysis unavailable'
            }
