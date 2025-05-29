"""
Core module for ICT Trading Oracle
"""

# sys.path manipulations removed for standard import behavior
# import sys 
# import os

# # Add parent directory to path
# parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if parent_dir not in sys.path:
#     sys.path.insert(0, parent_dir)

# Import all core modules
try:
    from .api_manager import APIManager
except ImportError:
    APIManager = None

RealICTAnalyzer = None # Initialize to None
TechnicalAnalyzer = None # Initialize alias to None
try:
    from .technical_analysis import RealICTAnalyzer
    TechnicalAnalyzer = RealICTAnalyzer  # Alias for broader compatibility
except ImportError:
    # RealICTAnalyzer and TechnicalAnalyzer remain None if import fails
    pass 

try:
    from .database import DatabaseManager
except ImportError:
    DatabaseManager = None

PaymentManager = None # Initialize to None
SubscriptionManager = None # Initialize to None
try:
    from .payment_manager import PaymentManager, SubscriptionManager
except ImportError:
    # PaymentManager and SubscriptionManager remain None if import fails
    pass

__all__ = [
    'APIManager', 
    'RealICTAnalyzer', # Exporting the real name
    'TechnicalAnalyzer', # Exporting the alias
    'DatabaseManager', 
    'PaymentManager', 
    'SubscriptionManager'
]
