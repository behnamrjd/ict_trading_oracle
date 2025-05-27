# Payment Processing 
"""
Payment Processing System
Supports ZarinPal (Iran) and CryptAPI (Crypto)
"""

import asyncio
import hashlib
import hmac
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import sqlite3
import logging

from config.settings import ZARINPAL_MERCHANT_ID, CRYPTAPI_CALLBACK_URL
from config.database import DatabaseManager

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """پردازشگر پرداخت چندگانه"""
    
    def __init__(self):
        self.zarinpal = ZarinPalGateway()
        self.cryptapi = CryptAPIGateway()
        self.db_manager = DatabaseManager()
    
    async def create_payment(self, user_id: int, plan: str, method: str) -> Dict:
        """ایجاد پرداخت جدید"""
        try:
            # تعیین مبلغ بر اساس پلان
            amounts = {
                'premium': {'irr': 2450000, 'usd': 49},  # $49 = 2,450,000 ریال
                'vip': {'irr': 7350000, 'usd': 149}      # $149 = 7,350,000 ریال
            }
            
            if method == 'zarinpal':
                return await self.zarinpal.create_payment(
                    user_id, amounts[plan]['irr'], 'IRR', plan
                )
            elif method == 'crypto':
                return await self.cryptapi.create_payment(
                    user_id, amounts[plan]['usd'], 'USD', plan
                )
            else:
                return {'success': False, 'error': 'Invalid payment method'}
                
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return {'success': False, 'error': str(e)}
    
    async def verify_payment(self, payment_id: str, method: str) -> Dict:
        """تأیید پرداخت"""
        try:
            if method == 'zarinpal':
                return await self.zarinpal.verify_payment(payment_id)
            elif method == 'crypto':
                return await self.cryptapi.verify_payment(payment_id)
            else:
                return {'success': False, 'error': 'Invalid payment method'}
                
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return {'success': False, 'error': str(e)}

class ZarinPalGateway:
    """درگاه زرین‌پال"""
    
    def __init__(self):
        self.merchant_id = ZARINPAL_MERCHANT_ID
        self.sandbox = False  # برای تست True کنید
        
        if self.sandbox:
            self.base_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/"
            self.payment_url = "https://sandbox.zarinpal.com/pg/StartPay/"
        else:
            self.base_url = "https://api.zarinpal.com/pg/rest/WebGate/"
            self.payment_url = "https://www.zarinpal.com/pg/StartPay/"
    
    async def create_payment(self, user_id: int, amount: int, currency: str, plan: str) -> Dict:
        """ایجاد پرداخت زرین‌پال"""
        try:
            # ذخیره پرداخت در دیتابیس
            payment_id = self.save_payment(user_id, amount, currency, plan)
            
            # درخواست به زرین‌پال
            data = {
                "merchant_id": self.merchant_id,
                "amount": amount,
                "currency": currency,
                "description": f"خرید اشتراک {plan} ربات ICT Trading",
                "callback_url": f"https://yourdomain.com/payment/zarinpal/verify/{payment_id}",
                "metadata": {
                    "email": f"user_{user_id}@ictbot.com",
                    "mobile": f"09{user_id}"
                }
            }
            
            response = requests.post(
                f"{self.base_url}PaymentRequest.json",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            result = response.json()
            
            if result['data']['code'] == 100:
                authority = result['data']['authority']
                
                # به‌روزرسانی payment_id در دیتابیس
                self.update_payment_authority(payment_id, authority)
                
                return {
                    'success': True,
                    'payment_url': f"{self.payment_url}{authority}",
                    'authority': authority,
                    'payment_id': payment_id,
                    'vpn_warning': True  # هشدار VPN
                }
            else:
                return {
                    'success': False,
                    'error': result['errors'][0] if 'errors' in result else 'Unknown error'
                }
                
        except Exception as e:
            logger.error(f"ZarinPal payment creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def verify_payment(self, authority: str) -> Dict:
        """تأیید پرداخت زرین‌پال"""
        try:
            # دریافت اطلاعات پرداخت از دیتابیس
            payment_info = self.get_payment_by_authority(authority)
            
            if not payment_info:
                return {'success': False, 'error': 'Payment not found'}
            
            data = {
                "merchant_id": self.merchant_id,
                "amount": payment_info['amount'],
                "authority": authority
            }
            
            response = requests.post(
                f"{self.base_url}PaymentVerification.json",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            result = response.json()
            
            if result['data']['code'] == 100:
                # پرداخت موفق
                ref_id = result['data']['ref_id']
                
                # به‌روزرسانی وضعیت پرداخت
                self.update_payment_status(authority, 'completed', ref_id)
                
                return {
                    'success': True,
                    'ref_id': ref_id,
                    'user_id': payment_info['user_id'],
                    'plan': payment_info['subscription_plan']
                }
            else:
                # پرداخت ناموفق
                self.update_payment_status(authority, 'failed')
                return {
                    'success': False,
                    'error': f"Payment failed: {result['data']['code']}"
                }
                
        except Exception as e:
            logger.error(f"ZarinPal verification error: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_payment(self, user_id: int, amount: int, currency: str, plan: str) -> str:
        """ذخیره پرداخت در دیتابیس"""
        try:
            conn = sqlite3.connect('data/ict_trading.db', check_same_thread=False)
            cursor = conn.cursor()
            
            payment_id = f"zp_{user_id}_{int(time.time())}"
            
            cursor.execute('''
                INSERT INTO payments 
                (user_id, payment_method, amount, currency, payment_id, subscription_plan, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 'zarinpal', amount, currency, payment_id, plan, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return payment_id
            
        except Exception as e:
            logger.error(f"Error saving payment: {e}")
            return None
    
    def update_payment_authority(self, payment_id: str, authority: str):
        """به‌روزرسانی authority پرداخت"""
        try:
            conn = sqlite3.connect('data/ict_trading.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE payments SET transaction_hash = ? WHERE payment_id = ?
            ''', (authority, payment_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating payment authority: {e}")
    
    def get_payment_by_authority(self, authority: str) -> Optional[Dict]:
        """دریافت اطلاعات پرداخت با authority"""
        try:
            conn = sqlite3.connect('data/ict_trading.db', check_same_thread=False)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, amount, subscription_plan, payment_id
                FROM payments 
                WHERE transaction_hash = ? AND payment_method = 'zarinpal'
            ''', (authority,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'amount': result[1],
                    'subscription_plan': result[2],
                    'payment_id': result[3]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting payment by authority: {e}")
            return None
    
    def update_payment_status(self, authority: str, status: str, ref_id: str = None):
        """به‌روزرسانی وضعیت پرداخت"""
        try:
            conn = sqlite3.connect('data/ict_trading.db', check_same_thread=False)
            cursor = conn.cursor()
            
            if ref_id:
                cursor.execute('''
                    UPDATE payments 
                    SET status = ?, completed_at = ?, payment_id = ?
                    WHERE transaction_hash = ?
                ''', (status, datetime.now().isoformat(), ref_id, authority))
            else:
                cursor.execute('''
                    UPDATE payments 
                    SET status = ?
                    WHERE transaction_hash = ?
                ''', (status, authority))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")

class CryptAPIGateway:
    """درگاه CryptAPI برای پرداخت کریپتو"""
    
    def __init__(self):
        self.base_url = "https://api.cryptapi.io"
        self.supported_coins = ['btc', 'eth', 'ltc', 'usdt', 'usdc', 'bnb']
    
    async def create_payment(self, user_id: int, amount_usd: float, currency: str, plan: str) -> Dict:
        """ایجاد پرداخت کریپتو"""
        try:
            # انتخاب ارز کریپتو (پیش‌فرض USDT)
            crypto_currency = 'usdt'
            
            # ذخیره پرداخت در دیتابیس
            payment_id = self.save_payment(user_id, amount_usd, crypto_currency, plan)
            
            # ایجاد آدرس پرداخت
            callback_url = f"{CRYPTAPI_CALLBACK_URL}/crypto/callback/{payment_id}"
            
            # درخواست به CryptAPI
            response = requests.get(
                f"{self.base_url}/{crypto_currency}/create/",
                params={
                    'callback': callback_url,
                    'address': self.get_our_wallet_address(crypto_currency),
                    'pending': 0,  # تأیید فوری
                    'confirmations': 1,  # یک تأیید کافی
                    'email': f'user_{user_id}@ictbot.com',
                    'post': 0
                },
                timeout=10
