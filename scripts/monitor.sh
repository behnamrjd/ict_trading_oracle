#!/bin/bash
# ICT Trading Oracle Monitoring Script

SERVICE_NAME="ictbot"
PROJECT_DIR="/home/ictbot/ict_trading_oracle"
ALERT_EMAIL="admin@yourdomain.com"

# Function to send alert
send_alert() {
    local message="$1"
    echo "🚨 ALERT: $message"
    logger "ICT Bot Alert: $message"
    
    # Send email if mail is configured
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "ICT Bot Alert" $ALERT_EMAIL
    fi
}

# Check if service is running
if ! systemctl is-active $SERVICE_NAME >/dev/null 2>&1; then
    send_alert "ICT Trading Oracle Bot service is not running"
    
    # Try to restart
    echo "🔄 Attempting to restart service..."
    systemctl restart $SERVICE_NAME
    sleep 10
    
    if systemctl is-active $SERVICE_NAME >/dev/null 2>&1; then
        send_alert "ICT Trading Oracle Bot service restarted successfully"
    else
        send_alert "Failed to restart ICT Trading Oracle Bot service"
    fi
fi

# Check memory usage
MEMORY_USAGE=$(ps -o rss -C python | grep -v RSS | awk '{sum+=$1} END {print sum}')
if [ -n "$MEMORY_USAGE" ]; then
    MEMORY_MB=$((MEMORY_USAGE / 1024))
    if [ $MEMORY_MB -gt 1000 ]; then
        send_alert "High memory usage: ${MEMORY_MB}MB"
    fi
fi

# Check disk space
DISK_USAGE=$(df $PROJECT_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    send_alert "Low disk space: ${DISK_USAGE}% used"
fi

# Check for errors in logs
if [ -f "$PROJECT_DIR/logs/ict_errors.log" ]; then
    RECENT_ERRORS=$(find "$PROJECT_DIR/logs/ict_errors.log" -mmin -10 -exec wc -l {} \; 2>/dev/null | awk '{print $1}')
    if [ -n "$RECENT_ERRORS" ] && [ $RECENT_ERRORS -gt 0 ]; then
        send_alert "Recent errors detected: $RECENT_ERRORS errors in last 10 minutes"
    fi
fi
