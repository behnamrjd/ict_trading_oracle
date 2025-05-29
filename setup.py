"""
Configuration module for ICT Trading Oracle
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from .settings import *
except ImportError as e:
    print(f"Warning: Could not import settings: {e}")
    # Default settings
    ADMIN_IDS = [123456789]
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
