#!/usr/bin/env python3
"""
ICT Trading Oracle Bot Runner
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run main
if __name__ == "__main__":
    try:
        from main import run_bot
        run_bot()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed")
        sys.exit(1)
