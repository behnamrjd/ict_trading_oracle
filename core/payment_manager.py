"""
Payment Manager for ICT Trading Oracle - ZarinPal Integration
"""

import requests
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PaymentManager:
    def __init__(self):
        self.merchant_id = os.getenv('ZARINPAL_MERCHANT_ID', 'YOUR_ZARINPAL_MERCHANT')
        self.sandbox = True  # Set to False for production
        
        if self.sandbox:
            self.base_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/"
        else:
            self.base_url = "https://payment.zarinpal.com/pg/rest/WebGate/"
    
    def create_payment_request(self, amount, description, user_id, subscription_type):
        """Create payment request"""
        try:
            callback_url = f"https://yourdomain.com/payment/callback/{user_id}"
            
            data = {
                "MerchantID": self.merchant_id,
                "Amount": amount,
                "Description": description,
                "CallbackURL": callback_url,
                "Mobile": "",
                "Email": ""
            }
            
            response = requests.post(
                f"{self.base_url}PaymentRequest.json",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['Status'] == 100:
                    authority = result['Authority']
                    
                    if self.sandbox:
                        payment_url = f"https://sandbox.zarinpal.com/pg/StartPay/{authority}"
                    else:
                        payment_url = f"https://payment.zarinpal.com/pg/StartPay/{authority}"
                    
                    return {
                        'success': True,
                        'authority': authority,
                        'payment_url': payment_url
                    }
                else:
                    return {
                        'success': False,
                        'error': f"ZarinPal Error: {result.get('Status', 'Unknown')}"
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP Error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Payment request error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, authority, amount):
        """Verify payment"""
        try:
            data = {
                "MerchantID": self.merchant_id,
                "Amount": amount,
                "Authority": authority
            }
            
            response = requests.post(
                f"{self.base_url}PaymentVerification.json",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['Status'] == 100:
                    return {
                        'success': True,
                        'ref_id': result['RefID']
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Verification failed: {result.get('Status', 'Unknown')}"
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP Error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class SubscriptionManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.plans = {
            'premium': {
                'name': 'Premium',
                'price': 49000,  # 49,000 Toman
                'duration_days': 30,
                'daily_signals': 50,
                'features': ['50 daily signals', 'Premium analysis', 'Email support']
            },
            'vip': {
                'name': 'VIP',
                'price': 149000,  # 149,000 Toman
                'duration_days': 30,
                'daily_signals': -1,  # Unlimited
                'features': ['Unlimited signals', 'Premium analysis', 'Priority support', 'Custom alerts']
            }
        }
    
    def get_plan_info(self, plan_type):
        """Get subscription plan information"""
        return self.plans.get(plan_type)
    
    def create_subscription_invoice(self, user_id, plan_type):
        """Create subscription invoice"""
        plan = self.get_plan_info(plan_type)
        if not plan:
            return None
        
        user = self.db.get_user(user_id)
        if not user:
            return None
        
        invoice = {
            'user_id': user_id,
            'plan_type': plan_type,
            'amount': plan['price'],
            'duration_days': plan['duration_days'],
            'description': f"ICT Trading Oracle - {plan['name']} Subscription",
            'created_at': datetime.now().isoformat()
        }
        
        return invoice
    
    def activate_subscription(self, user_id, plan_type, duration_days=30):
        """Activate user subscription"""
        try:
            expires_date = datetime.now() + timedelta(days=duration_days)
            
            success = self.db.upgrade_user_subscription(user_id, plan_type, duration_days)
            
            if success:
                # Reset daily signals counter
                self.db.reset_daily_signals(user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error activating subscription: {e}")
            return False
