# Ensemble Models 
"""
Ensemble Models for Signal Generation
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class EnsembleModel:
    """مدل‌های Ensemble"""
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.is_trained = False
        
    async def initialize(self):
        """راه‌اندازی اولیه"""
        try:
            # در پیاده‌سازی واقعی، مدل‌های از پیش آموزش دیده بارگذاری می‌شوند
            logger.info("Ensemble model initialized")
            
        except Exception as e:
            logger.error(f"Error initializing ensemble model: {e}")
    
    def train_models(self, X: np.ndarray, y: np.ndarray) -> bool:
        """آموزش مدل‌های ensemble"""
        try:
            # Scale data
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Random Forest
            rf_model = RandomForestClassifier(
                n_estimators=100, 
                random_state=42,
                max_depth=10,
                min_samples_split=5
            )
            rf_model.fit(X_scaled, y)
            self.models['random_forest'] = rf_model
            
            # Train XGBoost
            xgb_model = xgb.XGBClassifier(
                n_estimators=100, 
                random_state=42,
                max_depth=6,
                learning_rate=0.1
            )
            xgb_model.fit(X_scaled, y)
            self.models['xgboost'] = xgb_model
            
            self.is_trained = True
            logger.info("Ensemble models trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training ensemble models: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> Dict:
        """پیش‌بینی با ensemble"""
        try:
            if not self.is_trained or not self.models:
                return {'signal': 'HOLD', 'confidence': 50}
            
            X_scaled = self.scaler.transform(X.reshape(1, -1))
            
            predictions = {}
            confidences = {}
            
            # Random Forest prediction
            if 'random_forest' in self.models:
                rf_pred = self.models['random_forest'].predict(X_scaled)[0]
                rf_proba = self.models['random_forest'].predict_proba(X_scaled)[0]
                predictions['random_forest'] = rf_pred
                confidences['random_forest'] = max(rf_proba)
            
            # XGBoost prediction
            if 'xgboost' in self.models:
                xgb_pred = self.models['xgboost'].predict(X_scaled)[0]
                xgb_proba = self.models['xgboost'].predict_proba(X_scaled)[0]
                predictions['xgboost'] = xgb_pred
                confidences['xgboost'] = max(xgb_proba)
            
            # Weighted voting
            signal_votes = {'BUY': 0, 'HOLD': 0, 'SELL': 0}
            signal_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
            
            total_weight = 0
            for model, pred in predictions.items():
                signal = signal_map[pred]
                weight = confidences[model]
                signal_votes[signal] += weight
                total_weight += weight
            
            # Final signal
            final_signal = max(signal_votes, key=signal_votes.get)
            confidence = (signal_votes[final_signal] / total_weight * 100) if total_weight > 0 else 50
            
            return {
                'signal': final_signal,
                'confidence': min(95, max(10, confidence)),
                'model_votes': signal_votes,
                'individual_predictions': predictions
            }
            
        except Exception as e:
            logger.error(f"Error in ensemble prediction: {e}")
            return {'signal': 'HOLD', 'confidence': 50}
