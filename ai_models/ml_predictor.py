"""
Machine Learning Predictor for ICT Trading Oracle
"""

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import ta
import pickle
import os
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self):
        self.price_model = None
        self.signal_model = None
        self.scaler = StandardScaler()
        self.price_scaler = MinMaxScaler()
        self.model_path = "ai_models/trained_models/"
        self.ensure_model_directory()
        
    def ensure_model_directory(self):
        """Create model directory if it doesn't exist"""
        os.makedirs(self.model_path, exist_ok=True)
    
    def fetch_training_data(self, symbol="GC=F", period="2y"):
        """Fetch historical data for training"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval="1h")
            
            if data.empty:
                logger.error("No data fetched for training")
                return None
            
            return data
        except Exception as e:
            logger.error(f"Error fetching training data: {e}")
            return None
    
    def create_features(self, data):
        """Create technical indicators as features"""
        try:
            df = data.copy()
            
            # Price-based features
            df['price_change'] = df['Close'].pct_change()
            df['high_low_ratio'] = df['High'] / df['Low']
            df['volume_price_trend'] = df['Volume'] * df['price_change']
            
            # Moving averages
            df['sma_5'] = df['Close'].rolling(window=5).mean()
            df['sma_10'] = df['Close'].rolling(window=10).mean()
            df['sma_20'] = df['Close'].rolling(window=20).mean()
            df['ema_12'] = df['Close'].ewm(span=12).mean()
            df['ema_26'] = df['Close'].ewm(span=26).mean()
            
            # Technical indicators
            df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            df['macd'] = ta.trend.MACD(df['Close']).macd()
            df['macd_signal'] = ta.trend.MACD(df['Close']).macd_signal()
            df['macd_histogram'] = ta.trend.MACD(df['Close']).macd_diff()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['Close'])
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_middle'] = bb.bollinger_mavg()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close']).williams_r()
            
            # Average True Range
            df['atr'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()
            
            # Volume indicators
            df['volume_sma'] = df['Volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['Volume'] / df['volume_sma']
            
            # ICT-specific features
            df['market_structure'] = self._calculate_market_structure(df)
            df['liquidity_zones'] = self._identify_liquidity_zones(df)
            df['fair_value_gaps'] = self._detect_fair_value_gaps(df)
            df['order_blocks'] = self._detect_order_blocks(df)
            
            # Time-based features
            df['hour'] = df.index.hour
            df['day_of_week'] = df.index.dayofweek
            df['is_london_session'] = ((df.index.hour >= 8) & (df.index.hour <= 16)).astype(int)
            df['is_ny_session'] = ((df.index.hour >= 13) & (df.index.hour <= 21)).astype(int)
            df['is_asian_session'] = ((df.index.hour >= 0) & (df.index.hour <= 8)).astype(int)
            
            # Future price for prediction (target variable)
            df['future_price'] = df['Close'].shift(-1)
            df['price_direction'] = (df['future_price'] > df['Close']).astype(int)
            
            # Drop NaN values
            df = df.dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"Error creating features: {e}")
            return None
    
    def _calculate_market_structure(self, df):
        """Calculate market structure (simplified ICT concept)"""
        try:
            # Higher highs and higher lows = bullish structure
            # Lower highs and lower lows = bearish structure
            
            highs = df['High'].rolling(window=10).max()
            lows = df['Low'].rolling(window=10).min()
            
            higher_highs = (df['High'] > highs.shift(1)).astype(int)
            higher_lows = (df['Low'] > lows.shift(1)).astype(int)
            
            # Bullish = 1, Bearish = -1, Neutral = 0
            market_structure = higher_highs + higher_lows - 1
            
            return market_structure
        except:
            return pd.Series(0, index=df.index)
    
    def _identify_liquidity_zones(self, df):
        """Identify liquidity zones (simplified)"""
        try:
            # Areas where price has been rejected multiple times
            resistance_levels = df['High'].rolling(window=20).quantile(0.9)
            support_levels = df['Low'].rolling(window=20).quantile(0.1)
            
            near_resistance = (df['Close'] >= resistance_levels * 0.99).astype(int)
            near_support = (df['Close'] <= support_levels * 1.01).astype(int)
            
            return near_resistance + near_support
        except:
            return pd.Series(0, index=df.index)
    
    def _detect_fair_value_gaps(self, df):
        """Detect Fair Value Gaps (simplified)"""
        try:
            # Gap between previous high and current low (or vice versa)
            gap_up = (df['Low'] > df['High'].shift(1)).astype(int)
            gap_down = (df['High'] < df['Low'].shift(1)).astype(int)
            
            return gap_up - gap_down
        except:
            return pd.Series(0, index=df.index)
    
    def _detect_order_blocks(self, df):
        """Detect Order Blocks (simplified)"""
        try:
            # Areas of high volume with significant price movement
            volume_threshold = df['Volume'].rolling(window=20).quantile(0.8)
            price_movement = abs(df['Close'].pct_change())
            movement_threshold = price_movement.rolling(window=20).quantile(0.8)
            
            order_blocks = ((df['Volume'] > volume_threshold) & 
                          (price_movement > movement_threshold)).astype(int)
            
            return order_blocks
        except:
            return pd.Series(0, index=df.index)
    
    def train_models(self):
        """Train ML models"""
        try:
            logger.info("Starting model training...")
            
            # Fetch training data
            data = self.fetch_training_data()
            if data is None:
                return False
            
            # Create features
            df = self.create_features(data)
            if df is None:
                return False
            
            # Prepare features for training
            feature_columns = [
                'price_change', 'high_low_ratio', 'volume_price_trend',
                'sma_5', 'sma_10', 'sma_20', 'ema_12', 'ema_26',
                'rsi', 'macd', 'macd_signal', 'macd_histogram',
                'bb_width', 'bb_position', 'stoch_k', 'stoch_d',
                'williams_r', 'atr', 'volume_ratio',
                'market_structure', 'liquidity_zones', 'fair_value_gaps', 'order_blocks',
                'hour', 'day_of_week', 'is_london_session', 'is_ny_session', 'is_asian_session'
            ]
            
            # Remove any columns that don't exist
            available_features = [col for col in feature_columns if col in df.columns]
            
            X = df[available_features].values
            y_price = df['future_price'].values
            y_direction = df['price_direction'].values
            
            # Remove any remaining NaN values
            mask = ~(np.isnan(X).any(axis=1) | np.isnan(y_price) | np.isnan(y_direction))
            X = X[mask]
            y_price = y_price[mask]
            y_direction = y_direction[mask]
            
            if len(X) < 100:
                logger.error("Insufficient training data")
                return False
            
            # Split data
            X_train, X_test, y_price_train, y_price_test, y_dir_train, y_dir_test = train_test_split(
                X, y_price, y_direction, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Scale prices
            y_price_train_scaled = self.price_scaler.fit_transform(y_price_train.reshape(-1, 1)).flatten()
            
            # Train price prediction model
            logger.info("Training price prediction model...")
            self.price_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.price_model.fit(X_train_scaled, y_price_train_scaled)
            
            # Train signal classification model
            logger.info("Training signal classification model...")
            self.signal_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            )
            self.signal_model.fit(X_train_scaled, y_dir_train)
            
            # Evaluate models
            price_pred = self.price_scaler.inverse_transform(
                self.price_model.predict(X_test_scaled).reshape(-1, 1)
            ).flatten()
            signal_pred = self.signal_model.predict(X_test_scaled)
            
            price_mse = mean_squared_error(y_price_test, price_pred)
            signal_accuracy = accuracy_score(y_dir_test, signal_pred)
            
            logger.info(f"Price prediction MSE: {price_mse:.4f}")
            logger.info(f"Signal accuracy: {signal_accuracy:.4f}")
            
            # Save models
            self.save_models()
            
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def save_models(self):
        """Save trained models"""
        try:
            with open(f"{self.model_path}price_model.pkl", 'wb') as f:
                pickle.dump(self.price_model, f)
            
            with open(f"{self.model_path}signal_model.pkl", 'wb') as f:
                pickle.dump(self.signal_model, f)
            
            with open(f"{self.model_path}scaler.pkl", 'wb') as f:
                pickle.dump(self.scaler, f)
            
            with open(f"{self.model_path}price_scaler.pkl", 'wb') as f:
                pickle.dump(self.price_scaler, f)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def load_models(self):
        """Load trained models"""
        try:
            with open(f"{self.model_path}price_model.pkl", 'rb') as f:
                self.price_model = pickle.load(f)
            
            with open(f"{self.model_path}signal_model.pkl", 'rb') as f:
                self.signal_model = pickle.load(f)
            
            with open(f"{self.model_path}scaler.pkl", 'rb') as f:
                self.scaler = pickle.load(f)
            
            with open(f"{self.model_path}price_scaler.pkl", 'rb') as f:
                self.price_scaler = pickle.load(f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    def predict(self, current_data):
        """Make predictions using trained models"""
        try:
            # Load models if not already loaded
            if self.price_model is None or self.signal_model is None:
                if not self.load_models():
                    # Train models if they don't exist
                    if not self.train_models():
                        return None
            
            # Create features from current data
            df = self.create_features(current_data)
            if df is None or df.empty:
                return None
            
            # Get the latest features
            latest_features = df.iloc[-1]
            
            feature_columns = [
                'price_change', 'high_low_ratio', 'volume_price_trend',
                'sma_5', 'sma_10', 'sma_20', 'ema_12', 'ema_26',
                'rsi', 'macd', 'macd_signal', 'macd_histogram',
                'bb_width', 'bb_position', 'stoch_k', 'stoch_d',
                'williams_r', 'atr', 'volume_ratio',
                'market_structure', 'liquidity_zones', 'fair_value_gaps', 'order_blocks',
                'hour', 'day_of_week', 'is_london_session', 'is_ny_session', 'is_asian_session'
            ]
            
            # Extract available features
            available_features = [col for col in feature_columns if col in latest_features.index]
            X = latest_features[available_features].values.reshape(1, -1)
            
            # Check for NaN values
            if np.isnan(X).any():
                logger.warning("NaN values in features, using fallback prediction")
                return self._fallback_prediction(current_data)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            price_pred_scaled = self.price_model.predict(X_scaled)
            price_pred = self.price_scaler.inverse_transform(price_pred_scaled.reshape(-1, 1))[0][0]
            
            signal_prob = self.signal_model.predict_proba(X_scaled)[0]
            signal_direction = 'BUY' if signal_prob[1] > 0.6 else 'SELL' if signal_prob[0] > 0.6 else 'HOLD'
            confidence = max(signal_prob) * 100
            
            current_price = current_data['Close'].iloc[-1]
            price_change_pred = ((price_pred - current_price) / current_price) * 100
            
            return {
                'predicted_price': round(price_pred, 2),
                'current_price': round(current_price, 2),
                'price_change_percent': round(price_change_pred, 2),
                'signal_direction': signal_direction,
                'confidence': round(confidence, 1),
                'ml_features': {
                    'rsi': round(latest_features.get('rsi', 50), 2),
                    'macd': round(latest_features.get('macd', 0), 4),
                    'bb_position': round(latest_features.get('bb_position', 0.5), 3),
                    'market_structure': latest_features.get('market_structure', 0),
                    'liquidity_zones': latest_features.get('liquidity_zones', 0),
                    'fair_value_gaps': latest_features.get('fair_value_gaps', 0),
                    'order_blocks': latest_features.get('order_blocks', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return self._fallback_prediction(current_data)
    
    def _fallback_prediction(self, data):
        """Fallback prediction when ML models fail"""
        try:
            current_price = data['Close'].iloc[-1]
            price_change = data['Close'].pct_change().iloc[-1] * 100
            
            # Simple trend-based prediction
            if price_change > 1:
                signal = 'BUY'
                confidence = 65
            elif price_change < -1:
                signal = 'SELL'
                confidence = 65
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'predicted_price': round(current_price * 1.001, 2),
                'current_price': round(current_price, 2),
                'price_change_percent': 0.1,
                'signal_direction': signal,
                'confidence': confidence,
                'ml_features': {
                    'rsi': 50,
                    'macd': 0,
                    'bb_position': 0.5,
                    'market_structure': 0,
                    'liquidity_zones': 0,
                    'fair_value_gaps': 0,
                    'order_blocks': 0
                }
            }
        except:
            return None
