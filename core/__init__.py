"""
Core module for ICT Trading Oracle
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import all core modules
try:
    from .api_manager import APIManager
except ImportError:
    APIManager = None

try:
    from .technical_analysis import TechnicalAnalyzer
except ImportError:
    TechnicalAnalyzer = None

try:
    from .database import DatabaseManager
except ImportError:
    DatabaseManager = None

try:
    from .payment_manager import PaymentManager, SubscriptionManager
except ImportError:
    PaymentManager = None
    SubscriptionManager = None

__all__ = ['APIManager', 'TechnicalAnalyzer', 'DatabaseManager', 'PaymentManager', 'SubscriptionManager']
