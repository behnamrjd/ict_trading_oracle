#!/bin/bash
# ICT Trading Oracle Health Check Script

PROJECT_DIR="/home/ictbot/ict_trading_oracle"
SERVICE_NAME="ictbot"

echo "🏥 ICT Trading Oracle Health Check"
echo "=================================="

# Check service status
echo "🔍 Checking service status..."
if systemctl is-active $SERVICE_NAME >/dev/null 2>&1; then
    echo "✅ Service is running"
else
    echo "❌ Service is not running"
    exit 1
fi

# Check if bot is responding
echo "🔍 Checking bot responsiveness..."
if journalctl -u $SERVICE_NAME --since "2 minutes ago" | grep -q "polling\|update\|message" >/dev/null 2>&1; then
    echo "✅ Bot is responding to updates"
else
    echo "⚠️ No recent bot activity detected"
fi

# Check memory usage
echo "🔍 Checking memory usage..."
MEMORY_USAGE=$(ps -o pid,rss,cmd -C python | grep run.py | awk '{print $2}')
if [ -n "$MEMORY_USAGE" ]; then
    MEMORY_MB=$((MEMORY_USAGE / 1024))
    echo "📊 Memory usage: ${MEMORY_MB}MB"
    
    if [ $MEMORY_MB -gt 500 ]; then
        echo "⚠️ High memory usage detected"
    else
        echo "✅ Memory usage normal"
    fi
else
    echo "❌ Cannot determine memory usage"
fi

# Check disk space
echo "🔍 Checking disk space..."
DISK_USAGE=$(df $PROJECT_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
echo "📊 Disk usage: ${DISK_USAGE}%"

if [ $DISK_USAGE -gt 90 ]; then
    echo "❌ Critical disk space"
    exit 1
elif [ $DISK_USAGE -gt 80 ]; then
    echo "⚠️ Low disk space"
else
    echo "✅ Disk space OK"
fi

# Check log files
echo "🔍 Checking log files..."
if [ -f "$PROJECT_DIR/logs/ict_trading.log" ]; then
    LOG_SIZE=$(du -h "$PROJECT_DIR/logs/ict_trading.log" | cut -f1)
    echo "📊 Main log size: $LOG_SIZE"
    
    # Check for recent errors
    ERROR_COUNT=$(tail -100 "$PROJECT_DIR/logs/ict_trading.log" | grep -c "ERROR\|CRITICAL")
    if [ $ERROR_COUNT -gt 5 ]; then
        echo "⚠️ Multiple recent errors detected ($ERROR_COUNT)"
    else
        echo "✅ Error rate normal"
    fi
else
    echo "⚠️ Main log file not found"
fi

echo "=================================="
echo "🏥 Health check completed"
