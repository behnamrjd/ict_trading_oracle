#!/usr/bin/env python3
"""
ICT Trading Oracle Bot Runner - Enhanced Version
"""

import sys
import os
import time
import logging
from pathlib import Path
import asyncio

# Add current directory to Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def check_environment():
    """Check if environment is properly configured"""
    issues = []
    
    # Check if .env file exists
    env_file = current_dir / '.env'
    if not env_file.exists():
        issues.append("❌ .env file not found")
    else:
        # Check if bot token is configured
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if 'YOUR_REAL_BOT_TOKEN_HERE' in content:
                    issues.append("⚠️ Bot token not configured in .env")
        except Exception as e:
            issues.append(f"❌ Cannot read .env file: {e}")
    
    # Check if logs directory exists
    logs_dir = current_dir / 'logs'
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(exist_ok=True)
            print("✅ Created logs directory")
        except Exception as e:
            issues.append(f"❌ Cannot create logs directory: {e}")
    
    # Check if data directory exists
    data_dir = current_dir / 'data'
    if not data_dir.exists():
        try:
            data_dir.mkdir(exist_ok=True)
            print("✅ Created data directory")
        except Exception as e:
            issues.append(f"❌ Cannot create data directory: {e}")
    
    return issues

def main():
    """Enhanced main function with environment checks"""
    print("🚀 ICT Trading Oracle Bot - Starting via run.py...")
    print(f"📁 Working directory: {current_dir}")
    
    # Check environment
    print("🔍 Checking environment...")
    issues = check_environment()
    
    if issues:
        print("\n⚠️ Environment Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        
        if any("❌" in issue for issue in issues):
            print("\n❌ Critical issues found. Please fix them before running the bot.")
            return 1
        else:
            print("\n⚠️ Warnings found, but continuing...")
    
    print("✅ Environment check completed")
    
    # Import and run main
    try:
        print("📦 Importing main module entrypoint...")
        from main import main as main_bot_entrypoint
        
        print("🤖 Starting ICT Trading Oracle Bot logic from main.py...")
        # Run the main async function from main.py
        asyncio.run(main_bot_entrypoint())
        print("✅ Bot execution finished (if it wasn't set to run indefinitely or handled shutdown internally).")
        return 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logging.error(f"Unexpected error in run.py: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
