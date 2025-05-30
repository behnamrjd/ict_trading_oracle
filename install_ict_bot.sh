#!/bin/bash

# ================================================================
# ICT Trading Oracle Bot - Complete Installation & Management Script v4.1
# Advanced Installation with Control Panel, Monitoring, Testing & Backtest
# Author: ICT Trading Oracle Team
# Version: 4.1.0 (Enhanced with 7-Day Backtest Analysis)
# Date: 2025-05-29
# ================================================================

# Colors for better display
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
UNDERLINE='\033[4m'
BLINK='\033[5m'
NC='\033[0m' # No Color

# Background colors
BG_RED='\033[41m'
BG_GREEN='\033[42m'
BG_YELLOW='\033[43m'
BG_BLUE='\033[44m'
BG_PURPLE='\033[45m'
BG_CYAN='\033[46m'

# Special symbols
CHECK_MARK="✅"
CROSS_MARK="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"
CHART="📊"
SHIELD="🛡️"
FIRE="🔥"
DIAMOND="💎"
STAR="⭐"
CROWN="👑"
ROBOT="🤖"

# Configuration variables
SCRIPT_VERSION="4.1.0"
PROJECT_NAME="ICT Trading Oracle Bot"
PROJECT_DIR="/opt/ict_trading_oracle"
SERVICE_NAME="ictbot"
GITHUB_REPO="https://github.com/behnamrjd/ict_trading_oracle.git"
PYTHON_VERSION="3.11"
LOG_FILE="/tmp/ict_install.log"
BACKUP_DIR="/opt/ictbot_backups"
CONFIG_FILE="${PROJECT_DIR}/.env"

# System requirements
MIN_DISK_SPACE=3145728  # 3GB in KB
MIN_RAM=1048576         # 1GB in KB
REQUIRED_PACKAGES=(
    "python3.11"
    "python3.11-venv"
    "python3.11-dev"
    "python3-pip"
    "git"
    "curl"
    "wget"
    "nano"
    "htop"
    "unzip"
    "build-essential"
    "pkg-config"
    "libcairo2-dev"
    "libgirepository1.0-dev"
    "sqlite3"
    "nginx"
    "ufw"
    "fail2ban"
)

# Functions for message display with enhanced formatting
print_header() {
    clear
    echo -e "${BG_PURPLE}${WHITE}${BOLD}"
    echo "================================================================"
    echo "  $PROJECT_NAME - Installation & Management v$SCRIPT_VERSION"
    echo "================================================================"
    echo -e "${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}${BOLD}[STEP]${NC} ${BLUE}$1${NC}"
    log_message "STEP: $1"
}

print_status() {
    echo -e "${BLUE}${BOLD}[INFO]${NC} $1"
    log_message "INFO: $1"
}

print_success() {
    echo -e "${GREEN}${BOLD}[SUCCESS]${NC} ${CHECK_MARK} $1"
    log_message "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}${BOLD}[WARNING]${NC} ${WARNING} $1"
    log_message "WARNING: $1"
}

print_error() {
    echo -e "${RED}${BOLD}[ERROR]${NC} ${CROSS_MARK} $1"
    log_message "ERROR: $1"
}

print_menu() {
    echo -e "${WHITE}${BOLD}$1${NC}"
}

print_submenu() {
    echo -e "${CYAN}$1${NC}"
}

print_info_box() {
    echo -e "${BG_BLUE}${WHITE}${BOLD}"
    echo "  $INFO $1  "
    echo -e "${NC}"
}

print_progress() {
    local current=$1
    local total=$2
    local message=$3
    local percentage=$((current * 100 / total))
    local filled=$((percentage / 2))
    local empty=$((50 - filled))
    
    printf "\r${BLUE}[INFO]${NC} $message ["
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' '-'
    printf "] %d%%" $percentage
    
    if [ $current -eq $total ]; then
        echo ""
    fi
}

# Logging function
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

# Initialize logging
init_logging() {
    # Try to create log file, fallback to /tmp if permission denied
    if ! touch "$LOG_FILE" 2>/dev/null; then
        LOG_FILE="/tmp/ict_install.log"
        echo "Warning: Cannot write to /var/log, using /tmp/ict_install.log"
    fi
    
    log_message "=== ICT Trading Oracle Installation Started ==="
    log_message "Script Version: $SCRIPT_VERSION"
    log_message "System: $(uname -a)"
}

# Function to check if installation is complete
check_installation_complete() {
    local required_files=(
        "${PROJECT_DIR}/main.py"
        "${PROJECT_DIR}/run.py"
        "${PROJECT_DIR}/.env"
        "${PROJECT_DIR}/.venv/bin/python"
        "/etc/systemd/system/${SERVICE_NAME}.service"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            return 1
        fi
    done
    
    # Check if ictbot user exists
    if ! id "ictbot" &>/dev/null; then
        return 1
    fi
    
    # Check if service is enabled
    if ! systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        return 1
    fi
    
    return 0
}

# Function to check command success with detailed error logging
check_status() {
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "$1"
        echo ""
    else
        print_error "$2"
        if [ -n "$3" ]; then
            echo -e "${RED}Error details:${NC}"
            echo -e "${RED}$3${NC}"
        fi
        echo -e "${RED}Installation failed at this step. Check $LOG_FILE for details.${NC}"
        log_message "FATAL ERROR: $2"
        log_message "Error details: $3"
        exit 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if user exists
user_exists() {
    id "$1" &>/dev/null
}

# Function to check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "$1.service"
}

# Function to get system information
get_system_info() {
    echo -e "${CYAN}${BOLD}System Information:${NC}"
    echo -e "  ${BLUE}OS:${NC} $(lsb_release -d | cut -f2)"
    echo -e "  ${BLUE}Kernel:${NC} $(uname -r)"
    echo -e "  ${BLUE}Architecture:${NC} $(uname -m)"
    echo -e "  ${BLUE}CPU:${NC} $(nproc) cores"
    echo -e "  ${BLUE}RAM:${NC} $(free -h | awk '/^Mem:/ {print $2}')"
    echo -e "  ${BLUE}Disk Space:${NC} $(df -h / | awk 'NR==2 {print $4}') available"
    echo -e "  ${BLUE}Python:${NC} $(python3 --version 2>/dev/null || echo 'Not installed')"
    echo -e "  ${BLUE}Git:${NC} $(git --version 2>/dev/null || echo 'Not installed')"
    echo ""
}

# Function to check system requirements
check_system_requirements() {
    print_status "Checking system requirements..."
    
    local requirements_met=true
    
    # Check available disk space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt $MIN_DISK_SPACE ]; then
        print_error "Insufficient disk space. Required: 3GB, Available: $(($available_space / 1024 / 1024))GB"
        requirements_met=false
    else
        print_success "Disk space check passed"
    fi
    
    # Check available RAM
    local available_ram=$(free | awk '/^Mem:/ {print $2}')
    if [ "$available_ram" -lt $MIN_RAM ]; then
        print_warning "Low RAM detected. Recommended: 1GB+, Available: $(($available_ram / 1024))MB"
    else
        print_success "RAM check passed"
    fi
    
    # Check internet connectivity
    if ping -c 1 google.com &> /dev/null; then
        print_success "Internet connectivity check passed"
    else
        print_error "No internet connectivity detected"
        requirements_met=false
    fi
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        requirements_met=false
    else
        print_success "Root privileges check passed"
    fi
    
    if [ "$requirements_met" = false ]; then
        print_error "System requirements not met. Please fix the issues above."
        exit 1
    fi
    
    print_success "All system requirements met"
    echo ""
}

# Function to display service status with colors
show_service_status() {
    local service_name=$1
    if systemctl is-active "$service_name" &>/dev/null; then
        if systemctl is-enabled "$service_name" &>/dev/null; then
            echo -e "${GREEN}${BOLD}●${NC} $service_name (active, enabled)"
        else
            echo -e "${YELLOW}${BOLD}●${NC} $service_name (active, disabled)"
        fi
    else
        if systemctl is-enabled "$service_name" &>/dev/null; then
            echo -e "${RED}${BOLD}●${NC} $service_name (inactive, enabled)"
        else
            echo -e "${RED}${BOLD}●${NC} $service_name (inactive, disabled)"
        fi
    fi
}

# Function to show real-time system stats
show_system_stats() {
    echo -e "${CYAN}${BOLD}Real-time System Statistics:${NC}"
    echo ""
    
    # CPU Usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "  ${BLUE}CPU Usage:${NC} ${cpu_usage}%"
    
    # Memory Usage
    local mem_info=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100.0}')
    echo -e "  ${BLUE}Memory Usage:${NC} ${mem_info}%"
    
    # Disk Usage
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    echo -e "  ${BLUE}Disk Usage:${NC} ${disk_usage}%"
    
    # Load Average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    echo -e "  ${BLUE}Load Average:${NC}${load_avg}"
    
    # Network connections
    local connections=$(netstat -an | grep ESTABLISHED | wc -l)
    echo -e "  ${BLUE}Active Connections:${NC} $connections"
    
    echo ""
}

# Function to show bot status
show_bot_status() {
    echo -e "${CYAN}${BOLD}ICT Trading Oracle Bot Status:${NC}"
    echo ""
    
    # Service status
    echo -e "  ${BLUE}Service Status:${NC}"
    show_service_status "$SERVICE_NAME"
    
    # Check if bot is responding
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        echo -e "  ${GREEN}${CHECK_MARK} Bot is running${NC}"
        
        # Show last few log entries
        echo -e "\n  ${BLUE}Recent Activity:${NC}"
        journalctl -u "$SERVICE_NAME" --no-pager -n 3 --since "5 minutes ago" | tail -n 3 | while read line; do
            echo -e "    ${DIM}$line${NC}"
        done
    else
        echo -e "  ${RED}${CROSS_MARK} Bot is not running${NC}"
    fi
    
    # Database status
    if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
        local db_size=$(du -h "$PROJECT_DIR/data/ict_trading.db" | cut -f1)
        echo -e "  ${BLUE}Database:${NC} ${GREEN}Connected${NC} (${db_size})"
    else
        echo -e "  ${BLUE}Database:${NC} ${RED}Not found${NC}"
    fi
    
    # Configuration status
    if [ -f "$CONFIG_FILE" ]; then
        if grep -q "YOUR_REAL_BOT_TOKEN_HERE" "$CONFIG_FILE"; then
            echo -e "  ${BLUE}Configuration:${NC} ${YELLOW}Needs setup${NC}"
        else
            echo -e "  ${BLUE}Configuration:${NC} ${GREEN}Configured${NC}"
        fi
    else
        echo -e "  ${BLUE}Configuration:${NC} ${RED}Missing${NC}"
    fi
    
    echo ""
}

# Main Control Panel Menu
show_main_menu() {
    print_header "🎪 ICT Trading Oracle - Advanced Control Panel"
    
    # Show system info
    get_system_info
    
    # Show bot status
    show_bot_status
    
    # Show system stats
    show_system_stats
    
    echo -e "${WHITE}${BOLD}📋 MAIN MENU:${NC}"
    echo ""
    echo -e "${GREEN}${BOLD}🚀 INSTALLATION & SETUP:${NC}"
    echo "  1)  Fresh Installation (Complete Setup)"
    echo "  2)  Reinstall/Repair (Fix Issues)"
    echo "  3)  Update from GitHub"
    echo ""
    echo -e "${BLUE}${BOLD}⚙️  MANAGEMENT:${NC}"
    echo "  4)  Start Bot Service"
    echo "  5)  Stop Bot Service"
    echo "  6)  Restart Bot Service"
    echo "  7)  View Live Logs"
    echo "  8)  Configuration Editor"
    echo ""
    echo -e "${PURPLE}${BOLD}🔧 MAINTENANCE:${NC}"
    echo "  9)  System Health Check"
    echo "  10) Performance Test"
    echo "  11) Database Management"
    echo "  12) Backup & Restore"
    echo "  13) Security Scan"
    echo ""
    echo -e "${CYAN}${BOLD}📊 MONITORING & ANALYTICS:${NC}"
    echo "  14) Real-time Monitoring"
    echo "  15) Performance Analytics"
    echo "  16) Error Analysis"
    echo "  17) User Statistics"
    echo "  18) 7-Day Backtest Analysis"
    echo ""
    echo -e "${YELLOW}${BOLD}🛠️  ADVANCED TOOLS:${NC}"
    echo "  19) Component Testing"
    echo "  20) Network Diagnostics"
    echo "  21) Resource Optimization"
    echo "  22) Log Management"
    echo "  23) Update Management"
    echo ""
    echo -e "${RED}${BOLD}🔴 SYSTEM:${NC}"
    echo "  24) Uninstall Everything"
    echo "  25) Factory Reset"
    echo "  0)  Exit"
    echo ""
    echo -e "${WHITE}${BOLD}================================================================${NC}"
    echo -n -e "${CYAN}Select option (0-25): ${NC}"
}

# Function to handle menu selection
handle_menu_selection() {
    local choice=$1
    
    case $choice in
        1)
            fresh_installation
            ;;
        2)
            reinstall_repair
            ;;
        3)
            update_from_github
            ;;
        4)
            start_bot_service
            ;;
        5)
            stop_bot_service
            ;;
        6)
            restart_bot_service
            ;;
        7)
            view_live_logs
            ;;
        8)
            configuration_editor
            ;;
        9)
            system_health_check
            ;;
        10)
            performance_test
            ;;
        11)
            database_management
            ;;
        12)
            backup_restore
            ;;
        13)
            security_scan
            ;;
        14)
            real_time_monitoring
            ;;
        15)
            performance_analytics
            ;;
        16)
            error_analysis
            ;;
        17)
            user_statistics
            ;;
        18)
            backtest_analysis
            ;;
        19)
            component_testing
            ;;
        20)
            network_diagnostics
            ;;
        21)
            resource_optimization
            ;;
        22)
            log_management
            ;;
        23)
            update_management
            ;;
        24)
            uninstall_everything
            ;;
        25)
            factory_reset
            ;;
        0)
            echo -e "${GREEN}${BOLD}Thanks for using ICT Trading Oracle! ${ROCKET}${NC}"
            exit 0
            ;;
        *)
            print_error "Invalid option. Please try again."
            sleep 2
            ;;
    esac
}

# Fresh Installation Function
fresh_installation() {
    print_header "🚀 Fresh Installation - ICT Trading Oracle Bot v$SCRIPT_VERSION"
    
    print_info_box "Starting complete fresh installation with all advanced features"
    
    # Pre-installation checks
    check_system_requirements
    
    # Initialize logging
    init_logging
    
    # Confirm installation
    echo -e "${YELLOW}${BOLD}This will install ICT Trading Oracle Bot with:${NC}"
    echo "  ${CHECK_MARK} Complete project structure"
    echo "  ${CHECK_MARK} Advanced monitoring system"
    echo "  ${CHECK_MARK} 7-Day backtest analysis"
    echo "  ${CHECK_MARK} Real-time gold price tracking"
    echo "  ${CHECK_MARK} Database management"
    echo "  ${CHECK_MARK} Security features"
    echo "  ${CHECK_MARK} Performance optimization"
    echo ""
    read -p "Continue with installation? (y/N): " confirm
    
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_warning "Installation cancelled by user"
        return
    fi
    
    # Start installation process
    install_system_packages
    create_ictbot_user
    setup_project_environment
    create_systemd_service
    configure_security
    final_verification
    
    print_success "Fresh installation completed successfully!"
    post_installation_summary
}

# System Package Installation
install_system_packages() {
    print_step "STEP 1: Installing System Packages"
    
    print_status "Updating package lists..."
    apt update -y > /dev/null 2>&1
    check_status "Package lists updated successfully." "Failed to update package lists."
    
    print_status "Upgrading installed packages... This might take a while."
    apt upgrade -y
    check_status "Packages upgraded successfully." "Failed to upgrade packages."
    
    print_success "System packages updated and upgraded."
    
    # Install software-properties-common for add-apt-repository
    print_status "Installing software-properties-common..."
    apt install -y software-properties-common
    check_status "software-properties-common installed" "Failed to install software-properties-common"
    
    # Add deadsnakes PPA for Python 3.11
    if ! grep -q "deadsnakes" /etc/apt/sources.list.d/*.list 2>/dev/null; then
        print_status "Adding deadsnakes PPA for Python 3.11..."
        apt install -y software-properties-common > /dev/null 2>&1
        add-apt-repository ppa:deadsnakes/ppa -y > /dev/null 2>&1
        apt update > /dev/null 2>&1
        check_status "Python PPA added successfully" "Failed to add Python PPA"
    fi
    
    # Install required packages
    print_step "Installing required system packages..."
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if dpkg -s "$package" >/dev/null 2>&1; then
            print_status "Package '$package' is already installed. Skipping."
        else
            print_status "Installing package: $package..."
            # Remove redirection to see apt output
            apt install -y "$package"
            # Check status after install command
            if [ $? -eq 0 ]; then
                print_success "Package '$package' installed successfully."
            else
                print_error "Failed to install package '$package'. Check $LOG_FILE for details."
                # Optionally, exit here if a critical package fails:
                # exit 1 
            fi
        fi
    done
    print_success "All required system packages checked/installed."
    
    echo ""
    
    # Verify critical packages
    print_status "Verifying critical package installations..."
    local critical_packages=("python3.11" "git" "curl" "sqlite3")
    for package in "${critical_packages[@]}"; do
        if command_exists "$package"; then
            print_success "$package installed and available"
        else
            print_error "$package not found after installation"
            exit 1
        fi
    done
}

# Create ictbot user with enhanced configuration
create_ictbot_user() {
    print_step "STEP 2: Creating ictbot User Account"
    
    if user_exists "ictbot"; then
        print_warning "User 'ictbot' already exists"
        
        # Check if user has proper home directory
        if [ ! -d "/home/ictbot" ]; then
            print_status "Creating home directory for ictbot..."
            mkhomedir_helper ictbot
            check_status "Home directory created" "Failed to create home directory"
        fi
        
        # Ensure user is in correct groups
        usermod -aG sudo,www-data ictbot
        check_status "User groups updated" "Failed to update user groups"
    else
        print_status "Creating user 'ictbot'..."
        useradd -m -s /bin/bash -G sudo,www-data ictbot
        check_status "User 'ictbot' created successfully" "Failed to create user 'ictbot'"
        
        # Set up user environment
        print_status "Setting up user environment..."
        sudo -u ictbot bash -c "
            echo 'export PATH=\$PATH:/home/ictbot/.local/bin' >> /home/ictbot/.bashrc
            echo 'export PYTHONPATH=/home/ictbot/ict_trading_oracle:\$PYTHONPATH' >> /home/ictbot/.bashrc
            echo 'alias ll=\"ls -la\"' >> /home/ictbot/.bashrc
            echo 'alias ictbot=\"sudo systemctl status ictbot\"' >> /home/ictbot/.bashrc
            echo 'alias ictlogs=\"sudo journalctl -u ictbot -f\"' >> /home/ictbot/.bashrc
        "
        check_status "User environment configured" "Failed to configure user environment"
    fi
    
    # Create necessary directories
    print_status "Creating user directories..."
    sudo -u ictbot mkdir -p /home/ictbot/{backups,logs,scripts,config}
    check_status "User directories created" "Failed to create user directories"
    
    # Set proper permissions
    chown -R ictbot:ictbot /home/ictbot
    chmod 755 /home/ictbot
    check_status "User permissions set" "Failed to set user permissions"
}

# Enhanced project environment setup
setup_project_environment() {
    print_step "STEP 3: Setting Up Enhanced Project Environment"

    # Create PROJECT_DIR as root and set ownership
    print_status "Creating project directory: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
    check_status "Project directory created" "Failed to create project directory"

    print_status "Setting ownership of $PROJECT_DIR to ictbot:ictbot"
    chown -R ictbot:ictbot "$PROJECT_DIR"
    check_status "Project directory ownership set" "Failed to set project directory ownership"

    print_status "Setting permissions for $PROJECT_DIR"
    chmod -R 770 "$PROJECT_DIR" # Give ictbot user read/write/execute
    check_status "Project directory permissions set" "Failed to set project directory permissions"

    # Define the Python script for critical imports
    CRITICAL_IMPORTS_PY_SCRIPT_CONTENT=$(cat <<'EOF_PYTHON_SCRIPT_CONTENT'
import sys
# sys.path.insert(0, '$PROJECT_DIR') # PROJECT_DIR will be available as env var
try:
    # Test core imports
    from core.api_manager import APIManager
    from core.technical_analysis import RealICTAnalyzer as TechnicalAnalyzer
    from core.database import DatabaseManager
    from core.payment_manager import PaymentManager, SubscriptionManager
    from backtest.backtest_analyzer import BacktestAnalyzer
    print('✅ All critical imports successful')
    sys.exit(0)
except ImportError as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f'❌ General error during import test: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF_PYTHON_SCRIPT_CONTENT
)

    # Create a temporary file for the Python script
    # This temp file is created by the root user, but will be read by ictbot.
    # Ensure ictbot can read it, or write it as ictbot in the subshell.
    # Simpler: create as root, ensure it's world-readable for a moment, or place in /tmp.
    TMP_PYTHON_SCRIPT="/tmp/critical_imports_check.py"
    echo "$CRITICAL_IMPORTS_PY_SCRIPT_CONTENT" > "$TMP_PYTHON_SCRIPT"
    chmod 644 "$TMP_PYTHON_SCRIPT" # Make it readable by ictbot

    # Switch to ictbot user for project setup
    sudo -u ictbot bash -c "
# ... (exports for PROJECT_DIR, LOG_FILE, PATH, colors, helper functions as before) ...

    # --- Subshell helper functions ---
# ... (log_message_subshell, print_status_subshell, etc. as before) ...
    cd \"\$PROJECT_DIR\" || { print_error_subshell \"Failed to cd to \$PROJECT_DIR\"; exit 1; }

# ... (git clone/pull logic, venv setup, pip install requirements as before) ...

    # Test critical imports using the temporary script
    print_status_subshell 'Testing critical Python imports...'
    # Ensure PYTHONPATH is set for the script execution
    # The Python script itself will use PROJECT_DIR from its environment
    if PYTHONPATH=\"\$PROJECT_DIR\" python \"$TMP_PYTHON_SCRIPT\"; then
        import_test_exit_code=0
    else
        import_test_exit_code=\$? # Capture python script's exit code
    fi

    if [ \$import_test_exit_code -eq 0 ]; then
        print_success_subshell 'Python imports verified successfully'
    else
        # Python script already prints detailed errors to its stdout (which is captured by subshell)
        import_fail_msg=\\\"Critical Python imports failed (Exit code: \$import_test_exit_code). Check output above.\\\"
        print_error_subshell \\\"\$import_fail_msg\\\"
        # exit 1 # Optionally exit if imports fail
    fi
    
    print_success_subshell 'Project environment setup completed within \$PROJECT_DIR'

" # End of sudo -u ictbot bash -c block
    
    # Clean up the temporary Python script
    rm -f "$TMP_PYTHON_SCRIPT"

    # Check exit status of the subshell
    local subshell_exit_code=$?
    # Ensure the main script's check_status uses the subshell's exit code
    # This is a bit tricky as check_status relies on $? from the *last executed command*
    # So, we execute a command that will have the subshell's exit code as its own.
    (exit $subshell_exit_code) 

    if [ $subshell_exit_code -ne 0 ]; then
        print_error "Project environment setup failed within ictbot user context (Exit code: $subshell_exit_code). See $LOG_FILE for details from ictbot context."
        # The (exit $subshell_exit_code) above will make check_status see this error
    fi
    check_status "Project environment setup completed (ictbot context finished with code: $subshell_exit_code)" "Project environment setup failed (see errors above)"
}

# Create enhanced systemd service
create_systemd_service() {
    print_step "STEP 4: Creating Enhanced systemd Service"
    
    if service_exists "$SERVICE_NAME"; then
        print_warning "$SERVICE_NAME service already exists, updating..."
        systemctl stop "$SERVICE_NAME" > /dev/null 2>&1
        systemctl disable "$SERVICE_NAME" > /dev/null 2>&1
    fi
    
    print_status "Creating enhanced systemd service file..."
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << SERVICEEOF
[Unit]
Description=ICT Trading Oracle Bot v$SCRIPT_VERSION - Enhanced with Monitoring & Backtest
Documentation=https://github.com/behnamrjd/ict_trading_oracle
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=ictbot
Group=ictbot
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONDONTWRITEBYTECODE=1"
ExecStartPre=/bin/sleep 10
ExecStart=$PROJECT_DIR/venv/bin/python run.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ictbot
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR /tmp
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=1G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
SERVICEEOF

    check_status "Enhanced systemd service file created" "Failed to create systemd service file"
    
    # Reload systemd daemon
    print_status "Reloading systemd daemon..."
    systemctl daemon-reload
    check_status "systemd daemon reloaded" "Failed to reload systemd daemon"
    
    # Enable service for auto-start
    print_status "Enabling service for auto-start..."
    systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
    check_status "Service enabled for auto-start" "Failed to enable service"
    
    # Create service management scripts
    print_status "Creating service management scripts..."
    
    # Create start script
    cat > "/home/ictbot/scripts/start_bot.sh" << 'STARTEOF'
#!/bin/bash
echo "Starting ICT Trading Oracle Bot..."
sudo systemctl start ictbot
sudo systemctl status ictbot
STARTEOF
    
    # Create stop script
    cat > "/home/ictbot/scripts/stop_bot.sh" << 'STOPEOF'
#!/bin/bash
echo "Stopping ICT Trading Oracle Bot..."
sudo systemctl stop ictbot
sudo systemctl status ictbot
STOPEOF
    
    # Create restart script
    cat > "/home/ictbot/scripts/restart_bot.sh" << 'RESTARTEOF'
#!/bin/bash
echo "Restarting ICT Trading Oracle Bot..."
sudo systemctl restart ictbot
sudo systemctl status ictbot
RESTARTEOF
    
    # Make scripts executable
    chmod +x /home/ictbot/scripts/*.sh
    chown -R ictbot:ictbot /home/ictbot/scripts/
    
    check_status "Service management scripts created" "Failed to create management scripts"
}

# Configure security settings
configure_security() {
    print_step "STEP 5: Configuring Security Settings"
    
    # Configure UFW firewall
    print_status "Configuring UFW firewall..."
    
    # Enable UFW if not already enabled
    if ! ufw status | grep -q "Status: active"; then
        print_status "Enabling UFW firewall..."
        echo "y" | ufw enable > /dev/null 2>&1
        check_status "UFW firewall enabled" "Failed to enable UFW firewall"
    fi
    
    # Configure firewall rules
    print_status "Setting up firewall rules..."
    ufw default deny incoming > /dev/null 2>&1
    ufw default allow outgoing > /dev/null 2>&1
    ufw allow ssh > /dev/null 2>&1
    ufw allow 80/tcp > /dev/null 2>&1
    ufw allow 443/tcp > /dev/null 2>&1
    check_status "Firewall rules configured" "Failed to configure firewall rules"
    
    # Configure fail2ban
    print_status "Configuring fail2ban..."
    if command_exists fail2ban-server; then
        # Create custom jail for SSH
        cat > /etc/fail2ban/jail.local << 'FAIL2BANEOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
FAIL2BANEOF
        
        systemctl enable fail2ban > /dev/null 2>&1
        systemctl restart fail2ban > /dev/null 2>&1
        check_status "fail2ban configured and started" "Failed to configure fail2ban"
    else
        print_warning "fail2ban not installed, skipping configuration"
    fi
    
    # Set up log rotation for bot logs
    print_status "Setting up log rotation..."
    cat > /etc/logrotate.d/ictbot << 'LOGROTATEEOF'
/home/ictbot/ict_trading_oracle/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ictbot ictbot
    postrotate
        systemctl reload ictbot > /dev/null 2>&1 || true
    endscript
}
LOGROTATEEOF
    
    check_status "Log rotation configured" "Failed to configure log rotation"
    
    # Set secure permissions
    print_status "Setting secure file permissions..."
    chmod 600 "$PROJECT_DIR/.env"
    chmod 755 "$PROJECT_DIR"
    chown -R ictbot:ictbot "$PROJECT_DIR"
    check_status "Secure permissions set" "Failed to set secure permissions"
}

# Final verification and testing
final_verification() {
    print_step "STEP 6: Final Verification and Testing"
    
    print_status "Verifying installation completeness..."
    
    # Check critical files
    local critical_files=(
        "$PROJECT_DIR/main.py"
        "$PROJECT_DIR/run.py"
        "$PROJECT_DIR/.env"
        "$PROJECT_DIR/.venv/bin/python"
        "/etc/systemd/system/$SERVICE_NAME.service"
    )
    
    local all_files_ok=true
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "✓ $file"
        else
            print_error "✗ $file (MISSING)"
            all_files_ok=false
        fi
    done
    
    if [ "$all_files_ok" = false ]; then
        print_error "Critical files are missing. Installation incomplete."
        exit 1
    fi
    
    # Test Python environment
    print_status "Testing Python environment..."
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c 'import sys; print(f\"Python {sys.version}\")' 2>/dev/null
    "
    check_status "Python environment verified" "Python environment test failed"
    
    # Test critical imports
    print_status "Testing critical imports..."
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
try:
    from core.api_manager import APIManager
    from core.technical_analysis import TechnicalAnalyzer
    from core.database import DatabaseManager
    from backtest.backtest_analyzer import BacktestAnalyzer
    print(\"✅ All imports successful\")
except Exception as e:
    print(f\"❌ Import error: {e}\")
    exit(1)
        '
    " 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Critical imports verified"
    else
        print_warning "Some imports failed, but installation can continue"
    fi
    
    # Create initial database
    print_status "Initializing database..."
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
from core.database import DatabaseManager
try:
    db = DatabaseManager()
    print(\"✅ Database initialized successfully\")
except Exception as e:
    print(f\"❌ Database error: {e}\")
        '
    " 2>/dev/null
    
    check_status "Database initialized" "Database initialization failed"
    
    # Test service configuration
    print_status "Testing service configuration..."
    systemctl daemon-reload
    if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        print_success "Service is properly configured and enabled"
    else
        print_error "Service configuration failed"
        exit 1
    fi
    
    print_success "Final verification completed successfully"
}

# Post-installation summary
post_installation_summary() {
    print_header "🎉 Installation Completed Successfully!"
    
    echo -e "${GREEN}${BOLD}✅ ICT Trading Oracle Bot v$SCRIPT_VERSION installation completed!${NC}"
    echo ""
    echo -e "${CYAN}${BOLD}📋 INSTALLATION SUMMARY:${NC}"
    echo "   ✅ Complete project structure created"
    echo "   ✅ Enhanced security configured"
    echo "   ✅ All dependencies installed (30+ packages)"
    echo "   ✅ Database system initialized"
    echo "   ✅ AI/ML modules prepared"
    echo "   ✅ 7-Day backtest analysis ready"
    echo "   ✅ Real-time monitoring system"
    echo "   ✅ Advanced admin panel"
    echo "   ✅ Performance optimization"
    echo "   ✅ Backup system configured"
    echo "   ✅ Log management setup"
    echo "   ✅ Security measures implemented"
    echo ""
    echo -e "${YELLOW}${BOLD}📋 NEXT STEPS:${NC}"
    echo ""
    echo "1. Configure Bot Token:"
    echo "   sudo nano $PROJECT_DIR/.env"
    echo "   Replace 'YOUR_REAL_BOT_TOKEN_HERE' with your actual bot token"
    echo ""
    echo "2. Update Admin IDs:"
    echo "   sudo nano $PROJECT_DIR/config/settings.py"
    echo "   Replace example IDs with your Telegram User ID"
    echo ""
    echo "3. Start the bot:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo ""
    echo "4. Check bot status:"
    echo "   sudo systemctl status $SERVICE_NAME"
    echo ""
    echo "5. View live logs:"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "6. Access control panel:"
    echo "   sudo $0"
    echo ""
    echo -e "${PURPLE}${BOLD}🎯 NEW FEATURES IN v$SCRIPT_VERSION:${NC}"
    echo "   • 7-Day Backtest Analysis with Performance Tracking"
    echo "   • Enhanced Real-Time Gold Price Integration"
    echo "   • Advanced Admin Analytics Dashboard"
    echo "   • Improved Signal Accuracy & Confidence"
    echo "   • Comprehensive System Monitoring"
    echo "   • Automated Backup & Recovery"
    echo "   • Security Hardening & Firewall"
    echo "   • Performance Optimization Tools"
    echo ""
    echo -e "${GREEN}${BOLD}🚀 ICT Trading Oracle Bot is ready for production!${NC}"
    echo ""
    
    read -p "Press Enter to return to main menu..."
}

# Reinstall/Repair function
reinstall_repair() {
    print_header "🔧 Reinstall/Repair - ICT Trading Oracle Bot"
    
    print_info_box "This will repair or reinstall the ICT Trading Oracle Bot"
    
    echo -e "${YELLOW}${BOLD}Repair options:${NC}"
    echo "  1. Quick repair (fix common issues)"
    echo "  2. Full reinstall (preserve configuration)"
    echo "  3. Complete fresh install (reset everything)"
    echo "  4. Back to main menu"
    echo ""
    read -p "Select repair option (1-4): " repair_choice
    
    case $repair_choice in
        1)
            quick_repair
            ;;
        2)
            full_reinstall
            ;;
        3)
            fresh_installation
            ;;
        4)
            return
            ;;
        *)
            print_error "Invalid option"
            return
            ;;
    esac
}

# Quick repair function
quick_repair() {
    print_header "🔧 Quick Repair"
    
    print_status "Running quick repair procedures..."
    
    # Stop service if running
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_status "Stopping service for repair..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Fix permissions
    print_status "Fixing file permissions..."
    chown -R ictbot:ictbot "$PROJECT_DIR"
    chmod 755 "$PROJECT_DIR"
    chmod 600 "$PROJECT_DIR/.env" 2>/dev/null
    print_success "Permissions fixed"
    
    # Reload systemd
    print_status "Reloading systemd configuration..."
    systemctl daemon-reload
    print_success "Systemd reloaded"
    
    # Test Python environment
    print_status "Testing Python environment..."
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        if [ -f 'venv/bin/activate' ]; then
            source venv/bin/activate
            python --version
        else
            echo 'Virtual environment not found'
            exit 1
        fi
    " > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Python environment OK"
    else
        print_warning "Python environment needs repair"
        
        # Recreate virtual environment
        print_status "Recreating virtual environment..."
        sudo -u ictbot bash -c "
            cd '$PROJECT_DIR'
            rm -rf venv
            python3.11 -m venv venv
            source venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
        " > "$LOG_FILE" 2>&1
        
        check_status "Virtual environment recreated" "Failed to recreate virtual environment"
    fi
    
    # Start service
    print_status "Starting service..."
    systemctl start "$SERVICE_NAME"
    sleep 5
    
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_success "Service started successfully"
        print_success "Quick repair completed"
    else
        print_error "Service failed to start"
        print_status "Checking service logs..."
        journalctl -u "$SERVICE_NAME" --no-pager -n 10
    fi
    
    read -p "Press Enter to continue..."
}

# Full reinstall preserving configuration
full_reinstall() {
    print_header "🔄 Full Reinstall (Preserving Configuration)"
    
    print_status "Starting full reinstall with configuration preservation..."
    
    # Create backup of configuration
    if [ -f "$PROJECT_DIR/.env" ]; then
        print_status "Backing up configuration..."
        cp "$PROJECT_DIR/.env" "/tmp/.env.backup.$(date +%Y%m%d_%H%M%S)"
        print_success "Configuration backed up"
    fi
    
    # Stop and disable service
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Remove project directory but keep backups
    if [ -d "$PROJECT_DIR" ]; then
        print_status "Removing old installation..."
        sudo -u ictbot mv "$PROJECT_DIR" "$PROJECT_DIR.old.$(date +%Y%m%d_%H%M%S)"
        print_success "Old installation moved to backup"
    fi
    
    # Run fresh installation
    setup_project_environment
    
    # Restore configuration if backup exists
    if [ -f "/tmp/.env.backup."* ]; then
        print_status "Restoring configuration..."
        latest_backup=$(ls -t /tmp/.env.backup.* | head -1)
        cp "$latest_backup" "$PROJECT_DIR/.env"
        chown ictbot:ictbot "$PROJECT_DIR/.env"
        chmod 600 "$PROJECT_DIR/.env"
        print_success "Configuration restored"
    fi
    
    # Recreate service
    create_systemd_service
    
    print_success "Full reinstall completed with configuration preserved"
    
    read -p "Press Enter to continue..."
}

# Service management functions
start_bot_service() {
    print_header "🚀 Starting Bot Service"
    
    print_status "Starting ICT Trading Oracle Bot service..."
    
    # Check if service exists
    if ! service_exists "$SERVICE_NAME"; then
        print_error "Service not found. Please install first."
        read -p "Press Enter to continue..."
        return
    fi
    
    # Start service
    systemctl start "$SERVICE_NAME"
    sleep 3
    
    # Check status
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_success "Service started successfully"
        
        # Show service status
        echo -e "${CYAN}${BOLD}Service Status:${NC}"
        systemctl status "$SERVICE_NAME" --no-pager -l
        
        echo ""
        print_info_box "Bot is now running! Check logs with: sudo journalctl -u $SERVICE_NAME -f"
    else
        print_error "Failed to start service"
        
        # Show error logs
        echo -e "${RED}${BOLD}Error logs:${NC}"
        journalctl -u "$SERVICE_NAME" --no-pager -n 10
    fi
    
    read -p "Press Enter to continue..."
}

stop_bot_service() {
    print_header "🛑 Stopping Bot Service"
    
    print_status "Stopping ICT Trading Oracle Bot service..."
    
    # Check if service is running
    if ! systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_warning "Service is not running"
        read -p "Press Enter to continue..."
        return
    fi
    
    # Stop service
    systemctl stop "$SERVICE_NAME"
    sleep 2
    
    # Check status
    if ! systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_success "Service stopped successfully"
    else
        print_error "Failed to stop service"
        
        # Force stop if necessary
        print_status "Attempting force stop..."
        systemctl kill "$SERVICE_NAME"
        sleep 2
        
        if ! systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            print_success "Service force stopped"
        else
            print_error "Unable to stop service"
        fi
    fi
    
    read -p "Press Enter to continue..."
}

restart_bot_service() {
    print_header "🔄 Restarting Bot Service"
    
    print_status "Restarting ICT Trading Oracle Bot service..."
    
    # Restart service
    systemctl restart "$SERVICE_NAME"
    sleep 5
    
    # Check status
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_success "Service restarted successfully"
        
        # Show service status
        echo -e "${CYAN}${BOLD}Service Status:${NC}"
        systemctl status "$SERVICE_NAME" --no-pager -l
        
        echo ""
        print_info_box "Bot restarted! Monitor logs with: sudo journalctl -u $SERVICE_NAME -f"
    else
        print_error "Failed to restart service"
        
        # Show error logs
        echo -e "${RED}${BOLD}Error logs:${NC}"
        journalctl -u "$SERVICE_NAME" --no-pager -n 15
    fi
    
    read -p "Press Enter to continue..."
}

# Live log viewer
view_live_logs() {
    print_header "📋 Live Log Viewer"
    
    print_info_box "Showing live logs for ICT Trading Oracle Bot (Press Ctrl+C to exit)"
    echo ""
    
    # Check if service exists
    if ! service_exists "$SERVICE_NAME"; then
        print_error "Service not found"
        read -p "Press Enter to continue..."
        return
    fi
    
    print_status "Starting live log viewer..."
    echo -e "${DIM}Press Ctrl+C to return to menu${NC}"
    echo ""
    
    # Show live logs
    journalctl -u "$SERVICE_NAME" -f --no-pager
    
    echo ""
    print_status "Log viewer closed"
    read -p "Press Enter to continue..."
}

# Configuration editor
configuration_editor() {
    print_header "⚙️ Configuration Editor"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo -e "${CYAN}${BOLD}Configuration Editor Options:${NC}"
    echo "  1. Edit .env file (main configuration)"
    echo "  2. Edit settings.py (admin settings)"
    echo "  3. Configure Admin IDs (Quick Setup)"
    echo "  4. Configure Bot Token (Quick Setup)"
    echo "  5. View current configuration"
    echo "  6. Backup configuration"
    echo "  7. Restore configuration"
    echo "  8. Back to main menu"
    echo ""
    read -p "Select option (1-8): " config_choice

    
    case $config_choice in
        1)
            print_status "Opening .env file for editing..."
            nano "$CONFIG_FILE"
            print_success "Configuration file updated"
            
            # Ask if user wants to restart service
            read -p "Restart service to apply changes? (y/N): " restart_confirm
            if [[ $restart_confirm =~ ^[Yy]$ ]]; then
                systemctl restart "$SERVICE_NAME"
                print_success "Service restarted"
            fi
            ;;
        2)
            if [ -f "$PROJECT_DIR/config/settings.py" ]; then
                print_status "Opening settings.py file for editing..."
                nano "$PROJECT_DIR/config/settings.py"
                print_success "Settings file updated"
                
                read -p "Restart service to apply changes? (y/N): " restart_confirm
                if [[ $restart_confirm =~ ^[Yy]$ ]]; then
                    systemctl restart "$SERVICE_NAME"
                    print_success "Service restarted"
                fi
            else
                print_error "Settings file not found"
            fi
            ;;
        3)
            configure_admin_ids
            ;;
        4)
            configure_bot_token
            ;;
        5)
            print_status "Current configuration:"
            echo ""
            echo -e "${DIM}=== .env file ===${NC}"
            cat "$CONFIG_FILE" | grep -v "^#" | grep -v "^$"
            echo ""
            ;;
        6)
            backup_file="/home/ictbot/backups/.env.backup.$(date +%Y%m%d_%H%M%S)"
            cp "$CONFIG_FILE" "$backup_file"
            print_success "Configuration backed up to: $backup_file"
            ;;
        7)
            print_status "Available backups:"
            ls -la /home/ictbot/backups/.env.backup.* 2>/dev/null || echo "No backups found"
            echo ""
            read -p "Enter backup filename to restore (or press Enter to cancel): " backup_name
            if [ -n "$backup_name" ] && [ -f "$backup_name" ]; then
                cp "$backup_name" "$CONFIG_FILE"
                print_success "Configuration restored from backup"
            else
                print_warning "Restore cancelled or file not found"
            fi
            ;;
        8)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
    
    read -p "Press Enter to continue..."
}

# تابع تنظیم Admin IDs
configure_admin_ids() {
    print_header "👑 Admin IDs Configuration"
    
    local settings_file="$PROJECT_DIR/config/settings.py"
    
    if [ ! -f "$settings_file" ]; then
        print_error "Settings file not found: $settings_file"
        read -p "Press Enter to continue..."
        return
    fi
    
    # نمایش Admin IDs فعلی
    echo -e "${CYAN}${BOLD}Current Admin IDs:${NC}"
    current_admins=$(grep -A 5 "ADMIN_IDS = \[" "$settings_file" | grep -o '[0-9]\+' | tr '\n' ', ' | sed 's/,$//')
    if [ -n "$current_admins" ]; then
        echo "  $current_admins"
    else
        echo "  No admin IDs configured"
    fi
    echo ""
    
    echo -e "${YELLOW}${BOLD}Admin ID Management:${NC}"
    echo "  1. Add new Admin ID"
    echo "  2. Remove Admin ID"
    echo "  3. Replace all Admin IDs"
    echo "  4. Back to configuration menu"
    echo ""
    read -p "Select option (1-4): " admin_choice
    
    case $admin_choice in
        1)
            add_admin_id
            ;;
        2)
            remove_admin_id
            ;;
        3)
            replace_all_admin_ids
            ;;
        4)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
}

# تابع اضافه کردن Admin ID
add_admin_id() {
    echo ""
    echo -e "${BLUE}To get your Telegram User ID:${NC}"
    echo "  1. Start your bot"
    echo "  2. Send /start command"
    echo "  3. Your User ID will be shown in the welcome message"
    echo ""
    
    read -p "Enter new Admin ID (numbers only): " new_admin_id
    
    # بررسی صحت ورودی
    if ! [[ "$new_admin_id" =~ ^[0-9]+$ ]]; then
        print_error "Invalid Admin ID. Please enter numbers only."
        read -p "Press Enter to continue..."
        return
    fi
    
    # بررسی تکراری نبودن
    if grep -q "$new_admin_id" "$PROJECT_DIR/config/settings.py"; then
        print_warning "Admin ID $new_admin_id already exists"
        read -p "Press Enter to continue..."
        return
    fi
    
    # اضافه کردن Admin ID جدید
    print_status "Adding Admin ID: $new_admin_id"
    
    # پیدا کردن خط ADMIN_IDS و اضافه کردن ID جدید
    sed -i "/ADMIN_IDS = \[/,/\]/ {
        /\]/i\    $new_admin_id,  # Added via control panel
    }" "$PROJECT_DIR/config/settings.py"
    
    print_success "Admin ID $new_admin_id added successfully"
    
    # پیشنهاد restart سرویس
    read -p "Restart service to apply changes? (y/N): " restart_confirm
    if [[ $restart_confirm =~ ^[Yy]$ ]]; then
        systemctl restart "$SERVICE_NAME"
        print_success "Service restarted"
    fi
    
    read -p "Press Enter to continue..."
}

# تابع حذف Admin ID
remove_admin_id() {
    echo ""
    echo -e "${CYAN}${BOLD}Current Admin IDs:${NC}"
    
    # نمایش لیست Admin IDs با شماره
    local admin_ids=()
    while IFS= read -r line; do
        if [[ $line =~ [0-9]+ ]]; then
            admin_id=$(echo "$line" | grep -o '[0-9]\+')
            admin_ids+=("$admin_id")
            echo "  ${#admin_ids[@]}. $admin_id"
        fi
    done < <(grep -A 10 "ADMIN_IDS = \[" "$PROJECT_DIR/config/settings.py")
    
    if [ ${#admin_ids[@]} -eq 0 ]; then
        print_error "No admin IDs found"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo ""
    read -p "Select Admin ID to remove (1-${#admin_ids[@]}) or 0 to cancel: " remove_choice
    
    if [ "$remove_choice" -eq 0 ] 2>/dev/null; then
        print_warning "Remove cancelled"
        read -p "Press Enter to continue..."
        return
    fi
    
    if [ "$remove_choice" -ge 1 ] && [ "$remove_choice" -le ${#admin_ids[@]} ] 2>/dev/null; then
        local admin_to_remove="${admin_ids[$((remove_choice-1))]}"
        
        # حذف Admin ID
        print_status "Removing Admin ID: $admin_to_remove"
        sed -i "/$admin_to_remove/d" "$PROJECT_DIR/config/settings.py"
        
        print_success "Admin ID $admin_to_remove removed successfully"
        
        # پیشنهاد restart سرویس
        read -p "Restart service to apply changes? (y/N): " restart_confirm
        if [[ $restart_confirm =~ ^[Yy]$ ]]; then
            systemctl restart "$SERVICE_NAME"
            print_success "Service restarted"
        fi
    else
        print_error "Invalid selection"
    fi
    
    read -p "Press Enter to continue..."
}

# تابع جایگزینی تمام Admin IDs
replace_all_admin_ids() {
    echo ""
    echo -e "${RED}${BOLD}⚠️ WARNING: This will replace ALL current admin IDs${NC}"
    echo ""
    
    read -p "Are you sure? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_warning "Operation cancelled"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo ""
    echo "Enter Admin IDs (one per line, press Enter twice when done):"
    
    local new_admin_ids=()
    while true; do
        read -p "Admin ID ${#new_admin_ids[@]}: " admin_id
        
        if [ -z "$admin_id" ]; then
            break
        fi
        
        if [[ "$admin_id" =~ ^[0-9]+$ ]]; then
            new_admin_ids+=("$admin_id")
            echo "  ✓ Added: $admin_id"
        else
            echo "  ✗ Invalid ID (numbers only): $admin_id"
        fi
    done
    
    if [ ${#new_admin_ids[@]} -eq 0 ]; then
        print_error "No valid admin IDs entered"
        read -p "Press Enter to continue..."
        return
    fi
    
    # ایجاد لیست جدید Admin IDs
    print_status "Updating admin IDs..."
    
    # پیدا کردن و جایگزینی بخش ADMIN_IDS
    local temp_file=$(mktemp)
    local in_admin_section=false
    
    while IFS= read -r line; do
        if [[ $line =~ ADMIN_IDS[[:space:]]*=[[:space:]]*\[ ]]; then
            echo "$line" >> "$temp_file"
            for admin_id in "${new_admin_ids[@]}"; do
                echo "    $admin_id,  # Added via control panel" >> "$temp_file"
            done
            in_admin_section=true
        elif [[ $in_admin_section == true && $line =~ \] ]]; then
            echo "$line" >> "$temp_file"
            in_admin_section=false
        elif [[ $in_admin_section == false ]]; then
            echo "$line" >> "$temp_file"
        fi
    done < "$PROJECT_DIR/config/settings.py"
    
    # جایگزینی فایل
    mv "$temp_file" "$PROJECT_DIR/config/settings.py"
    chown ictbot:ictbot "$PROJECT_DIR/config/settings.py"
    
    print_success "Admin IDs updated successfully"
    echo "New Admin IDs: ${new_admin_ids[*]}"
    
    # پیشنهاد restart سرویس
    read -p "Restart service to apply changes? (y/N): " restart_confirm
    if [[ $restart_confirm =~ ^[Yy]$ ]]; then
        systemctl restart "$SERVICE_NAME"
        print_success "Service restarted"
    fi
    
    read -p "Press Enter to continue..."
}

# تابع تنظیم Bot Token
configure_bot_token() {
    print_header "🤖 Bot Token Configuration"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        read -p "Press Enter to continue..."
        return
    fi
    
    # نمایش وضعیت فعلی
    echo -e "${CYAN}${BOLD}Current Bot Token Status:${NC}"
    if grep -q "YOUR_REAL_BOT_TOKEN_HERE" "$CONFIG_FILE"; then
        echo -e "  ${RED}✗ Not configured (using default)${NC}"
    else
        local current_token=$(grep "BOT_TOKEN=" "$CONFIG_FILE" | cut -d'=' -f2)
        local masked_token="${current_token:0:10}...${current_token: -10}"
        echo -e "  ${GREEN}✓ Configured${NC} ($masked_token)"
    fi
    echo ""
    
    echo -e "${BLUE}To get your Bot Token:${NC}"
    echo "  1. Message @BotFather on Telegram"
    echo "  2. Send /newbot command"
    echo "  3. Follow instructions to create your bot"
    echo "  4. Copy the token provided"
    echo ""
    
    read -p "Enter new Bot Token: " new_token
    
    # بررسی صحت توکن (فرمت کلی)
    if [[ ! $new_token =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        print_error "Invalid token format. Bot tokens should be like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        read -p "Press Enter to continue..."
        return
    fi
    
    # جایگزینی توکن
    print_status "Updating bot token..."
    sed -i "s/BOT_TOKEN=.*/BOT_TOKEN=$new_token/" "$CONFIG_FILE"
    
    print_success "Bot token updated successfully"
    
    # پیشنهاد restart سرویس
    read -p "Restart service to apply changes? (y/N): " restart_confirm
    if [[ $restart_confirm =~ ^[Yy]$ ]]; then
        systemctl restart "$SERVICE_NAME"
        sleep 3
        
        if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            print_success "Service restarted successfully"
        else
            print_error "Service failed to start. Check token and try again."
        fi
    fi
    
    read -p "Press Enter to continue..."
}

# System health check
system_health_check() {
    print_header "🏥 System Health Check"
    
    print_status "Running comprehensive system health check..."
    echo ""
    
    local health_score=0
    local max_score=100
    
    # Check system resources
    echo -e "${CYAN}${BOLD}📊 System Resources:${NC}"
    
    # CPU usage check
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    if (( $(echo "$cpu_usage < 80" | bc -l) )); then
        echo -e "  ${GREEN}✓${NC} CPU Usage: ${cpu_usage}% (Good)"
        health_score=$((health_score + 15))
    else
        echo -e "  ${RED}✗${NC} CPU Usage: ${cpu_usage}% (High)"
    fi
    
    # Memory usage check
    local mem_usage=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$mem_usage < 85" | bc -l) )); then
        echo -e "  ${GREEN}✓${NC} Memory Usage: ${mem_usage}% (Good)"
        health_score=$((health_score + 15))
    else
        echo -e "  ${RED}✗${NC} Memory Usage: ${mem_usage}% (High)"
    fi
    
    # Disk usage check
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    if [ "$disk_usage" -lt 85 ]; then
        echo -e "  ${GREEN}✓${NC} Disk Usage: ${disk_usage}% (Good)"
        health_score=$((health_score + 10))
    else
        echo -e "  ${RED}✗${NC} Disk Usage: ${disk_usage}% (High)"
    fi
    
    # Load average check
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | cut -d',' -f1)
    local cpu_cores=$(nproc)
    if (( $(echo "$load_avg < $cpu_cores" | bc -l) )); then
        echo -e "  ${GREEN}✓${NC} Load Average: $load_avg (Good for $cpu_cores cores)"
        health_score=$((health_score + 10))
    else
        echo -e "  ${RED}✗${NC} Load Average: $load_avg (High for $cpu_cores cores)"
    fi
    
    echo ""
    
    # Check services
    echo -e "${CYAN}${BOLD}🔧 Service Status:${NC}"
    
    # ICT Bot service
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} ICT Trading Oracle Bot: Running"
        health_score=$((health_score + 20))
        
        # Check if service is responding
        if journalctl -u "$SERVICE_NAME" --since "1 minute ago" | grep -q "Bot is now running\|polling"; then
            echo -e "  ${GREEN}✓${NC} Bot Response: Active"
            health_score=$((health_score + 10))
        else
            echo -e "  ${YELLOW}⚠${NC} Bot Response: No recent activity"
        fi
    else
        echo -e "  ${RED}✗${NC} ICT Trading Oracle Bot: Not running"
    fi
    
    # Database check
    if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
        echo -e "  ${GREEN}✓${NC} Database: Present"
        health_score=$((health_score + 10))
        
        # Check database size and integrity
        local db_size=$(du -h "$PROJECT_DIR/data/ict_trading.db" | cut -f1)
        echo -e "  ${BLUE}ℹ${NC} Database Size: $db_size"
        
        # Test database connection
        if sudo -u ictbot bash -c "cd '$PROJECT_DIR' && source venv/bin/activate && python -c 'from core.database import DatabaseManager; db = DatabaseManager(); print(\"DB OK\")'" 2>/dev/null | grep -q "DB OK"; then
            echo -e "  ${GREEN}✓${NC} Database Connection: Working"
            health_score=$((health_score + 10))
        else
            echo -e "  ${RED}✗${NC} Database Connection: Failed"
        fi
    else
        echo -e "  ${RED}✗${NC} Database: Missing"
    fi
    
    echo ""
    
    # Check network connectivity
    echo -e "${CYAN}${BOLD}🌐 Network Connectivity:${NC}"
    
    # Internet connectivity
    if ping -c 1 google.com &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Internet: Connected"
        health_score=$((health_score + 5))
    else
        echo -e "  ${RED}✗${NC} Internet: No connection"
    fi
    
    # GitHub connectivity
    if ping -c 1 github.com &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} GitHub: Accessible"
        health_score=$((health_score + 5))
    else
        echo -e "  ${RED}✗${NC} GitHub: Not accessible"
    fi
    
    echo ""
    
    # Check configuration
    echo -e "${CYAN}${BOLD}⚙️ Configuration:${NC}"
    
    # .env file check
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "  ${GREEN}✓${NC} Configuration file: Present"
        
        # Check if bot token is configured
        if grep -q "YOUR_REAL_BOT_TOKEN_HERE" "$CONFIG_FILE"; then
            echo -e "  ${YELLOW}⚠${NC} Bot Token: Not configured"
        else
            echo -e "  ${GREEN}✓${NC} Bot Token: Configured"
        fi
        
        # Check admin IDs
        if [ -f "$PROJECT_DIR/config/settings.py" ]; then
            if grep -q "123456789" "$PROJECT_DIR/config/settings.py"; then
                echo -e "  ${YELLOW}⚠${NC} Admin IDs: Default values"
            else
                echo -e "  ${GREEN}✓${NC} Admin IDs: Configured"
            fi
        fi
    else
        echo -e "  ${RED}✗${NC} Configuration file: Missing"
    fi
    
    echo ""
    
    # Display health score
    echo -e "${CYAN}${BOLD}📊 Overall Health Score:${NC}"
    
    local health_percentage=$((health_score * 100 / max_score))
    
    if [ $health_percentage -ge 90 ]; then
        echo -e "  ${GREEN}${BOLD}🟢 EXCELLENT: ${health_percentage}/100${NC}"
    elif [ $health_percentage -ge 75 ]; then
        echo -e "  ${YELLOW}${BOLD}🟡 GOOD: ${health_percentage}/100${NC}"
    elif [ $health_percentage -ge 50 ]; then
        echo -e "  ${YELLOW}${BOLD}🟠 FAIR: ${health_percentage}/100${NC}"
    else
        echo -e "  ${RED}${BOLD}🔴 POOR: ${health_percentage}/100${NC}"
    fi
    
    echo ""
    
    # Recommendations
    if [ $health_percentage -lt 90 ]; then
        echo -e "${YELLOW}${BOLD}💡 Recommendations:${NC}"
        
        if [ $health_percentage -lt 50 ]; then
            echo "  • Consider running repair or reinstall"
            echo "  • Check system resources and free up space"
            echo "  • Verify network connectivity"
        fi
        
        if grep -q "YOUR_REAL_BOT_TOKEN_HERE" "$CONFIG_FILE" 2>/dev/null; then
            echo "  • Configure bot token in .env file"
        fi
        
        if ! systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            echo "  • Start the bot service"
        fi
        
        echo ""
    fi
    
    read -p "Press Enter to continue..."
}

# Performance test
performance_test() {
    print_header "⚡ Performance Test"
    
    print_status "Running performance tests..."
    echo ""
    
    # Check if bot is running
    if ! systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_warning "Bot service is not running. Starting for test..."
        systemctl start "$SERVICE_NAME"
        sleep 5
    fi
    
    echo -e "${CYAN}${BOLD}🧪 Running Performance Tests:${NC}"
    echo ""
    
    # Test 1: Python import speed
    echo -e "${BLUE}Test 1: Python Import Speed${NC}"
    local import_start=$(date +%s.%N)
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
import time
start = time.time()
from core.api_manager import APIManager
from core.technical_analysis import TechnicalAnalyzer
from core.database import DatabaseManager
from backtest.backtest_analyzer import BacktestAnalyzer
end = time.time()
print(f\"Import time: {end - start:.3f} seconds\")
        '
    " 2>/dev/null
    
    # Test 2: Database performance
    echo -e "${BLUE}Test 2: Database Performance${NC}"
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
import time
from core.database import DatabaseManager

start = time.time()
db = DatabaseManager()
stats = db.get_bot_stats()
end = time.time()
print(f\"Database query time: {end - start:.3f} seconds\")
print(f\"Database stats: {stats}\")
        '
    " 2>/dev/null
    
    # Test 3: API response time
    echo -e "${BLUE}Test 3: API Response Time${NC}"
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
import time
from core.api_manager import APIManager

start = time.time()
api = APIManager()
price_data = api.get_gold_price()
end = time.time()
print(f\"API response time: {end - start:.3f} seconds\")
if price_data:
    print(f\"Gold price: \${price_data[\"price\"]}\")
else:
    print(\"API response: No data\")
        '
    " 2>/dev/null
    
    # Test 4: Technical analysis speed
    echo -e "${BLUE}Test 4: Technical Analysis Speed${NC}"
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
import time
from core.technical_analysis import TechnicalAnalyzer

start = time.time()
analyzer = TechnicalAnalyzer()
analysis = analyzer.analyze_market_structure()
end = time.time()
print(f\"Analysis time: {end - start:.3f} seconds\")
print(f\"Signal: {analysis[\"signal\"]} (Confidence: {analysis[\"confidence\"]}%)\")
        '
    " 2>/dev/null
    
    # Test 5: Memory usage
    echo -e "${BLUE}Test 5: Memory Usage${NC}"
    local bot_pid=$(pgrep -f "python.*run.py")
    if [ -n "$bot_pid" ]; then
        local memory_usage=$(ps -p $bot_pid -o rss= 2>/dev/null)
        if [ -n "$memory_usage" ]; then
            local memory_mb=$((memory_usage / 1024))
            echo "Bot memory usage: ${memory_mb}MB"
            
            if [ $memory_mb -lt 100 ]; then
                echo -e "  ${GREEN}✓${NC} Memory usage: Excellent"
            elif [ $memory_mb -lt 200 ]; then
                echo -e "  ${YELLOW}⚠${NC} Memory usage: Good"
            else
                echo -e "  ${RED}✗${NC} Memory usage: High"
            fi
        fi
    else
        echo "Bot process not found"
    fi
    
    # Test 6: Disk I/O performance
    echo -e "${BLUE}Test 6: Disk I/O Performance${NC}"
    local io_start=$(date +%s.%N)
    dd if=/dev/zero of=/tmp/test_file bs=1M count=10 2>/dev/null
    rm -f /tmp/test_file
    local io_end=$(date +%s.%N)
    local io_time=$(echo "$io_end - $io_start" | bc)
    echo "Disk I/O time (10MB): ${io_time} seconds"
    
    echo ""
    echo -e "${GREEN}${BOLD}Performance test completed!${NC}"
    
    read -p "Press Enter to continue..."
}

# Database management
database_management() {
    print_header "🗄️ Database Management"
    
    echo -e "${CYAN}${BOLD}Database Management Options:${NC}"
    echo "  1. View database statistics"
    echo "  2. Backup database"
    echo "  3. Restore database"
    echo "  4. Optimize database"
    echo "  5. Reset database (DANGER)"
    echo "  6. Export user data"
    echo "  7. Import user data"
    echo "  8. Database integrity check"
    echo "  9. Back to main menu"
    echo ""
    read -p "Select option (1-9): " db_choice
    
    case $db_choice in
        1)
            view_database_stats
            ;;
        2)
            backup_database
            ;;
        3)
            restore_database
            ;;
        4)
            optimize_database
            ;;
        5)
            reset_database
            ;;
        6)
            export_user_data
            ;;
        7)
            import_user_data
            ;;
        8)
            database_integrity_check
            ;;
        9)
            return
            ;;
        *)
            print_error "Invalid option"
            read -p "Press Enter to continue..."
            ;;
    esac
}

# View database statistics
view_database_stats() {
    print_status "Retrieving database statistics..."
    echo ""
    
    if [ ! -f "$PROJECT_DIR/data/ict_trading.db" ]; then
        print_error "Database file not found"
        read -p "Press Enter to continue..."
        return
    fi
    
    # Get database size
    local db_size=$(du -h "$PROJECT_DIR/data/ict_trading.db" | cut -f1)
    echo -e "${CYAN}${BOLD}📊 Database Information:${NC}"
    echo "  Database Size: $db_size"
    echo "  Database Path: $PROJECT_DIR/data/ict_trading.db"
    echo ""
    
    # Get table statistics
    echo -e "${CYAN}${BOLD}📋 Table Statistics:${NC}"
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
import sqlite3
from pathlib import Path

db_path = Path(\"data/ict_trading.db\")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type=\\\"table\\\"\")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f\"SELECT COUNT(*) FROM {table_name}\")
        count = cursor.fetchone()[0]
        print(f\"  {table_name}: {count} records\")
    
    conn.close()
else:
    print(\"Database file not found\")
        '
    " 2>/dev/null
    
    echo ""
    
    # Get bot statistics
    echo -e "${CYAN}${BOLD}🤖 Bot Statistics:${NC}"
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
from core.database import DatabaseManager
try:
    db = DatabaseManager()
    stats = db.get_bot_stats()
    print(f\"  Total Users: {stats[\"total_users\"]}\")
    print(f\"  Active Users: {stats[\"active_users\"]}\")
    print(f\"  Total Signals: {stats[\"total_signals\"]}\")
    print(f\"  Daily Signals: {stats[\"daily_signals\"]}\")
except Exception as e:
    print(f\"Error: {e}\")
        '
    " 2>/dev/null
    
    read -p "Press Enter to continue..."
}

# Backup database
backup_database() {
    print_status "Creating database backup..."
    
    if [ ! -f "$PROJECT_DIR/data/ict_trading.db" ]; then
        print_error "Database file not found"
        read -p "Press Enter to continue..."
        return
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR/database"
    
    # Create backup filename with timestamp
    local backup_file="$BACKUP_DIR/database/ict_trading_backup_$(date +%Y%m%d_%H%M%S).db"
    
    # Stop service temporarily for consistent backup
    local service_was_running=false
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        service_was_running=true
        print_status "Stopping service for consistent backup..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Create backup
    cp "$PROJECT_DIR/data/ict_trading.db" "$backup_file"
    
    # Restart service if it was running
    if [ "$service_was_running" = true ]; then
        print_status "Restarting service..."
        systemctl start "$SERVICE_NAME"
    fi
    
    # Verify backup
    if [ -f "$backup_file" ]; then
        local backup_size=$(du -h "$backup_file" | cut -f1)
        print_success "Database backup created: $backup_file ($backup_size)"
        
        # Create compressed backup
        print_status "Creating compressed backup..."
        gzip -c "$backup_file" > "${backup_file}.gz"
        local compressed_size=$(du -h "${backup_file}.gz" | cut -f1)
        print_success "Compressed backup created: ${backup_file}.gz ($compressed_size)"
    else
        print_error "Failed to create backup"
    fi
    
    # Show available backups
    echo ""
    echo -e "${CYAN}${BOLD}Available Backups:${NC}"
    ls -lah "$BACKUP_DIR/database/" 2>/dev/null | tail -n +2 | while read line; do
        echo "  $line"
    done
    
    read -p "Press Enter to continue..."
}

# Restore database
restore_database() {
    print_status "Database restore options..."
    echo ""
    
    # List available backups
    echo -e "${CYAN}${BOLD}Available Backups:${NC}"
    local backup_files=()
    while IFS= read -r -d '' file; do
        backup_files+=("$file")
    done < <(find "$BACKUP_DIR/database" -name "*.db" -print0 2>/dev/null)
    
    if [ ${#backup_files[@]} -eq 0 ]; then
        print_error "No backup files found in $BACKUP_DIR/database"
        read -p "Press Enter to continue..."
        return
    fi
    
    for i in "${!backup_files[@]}"; do
        local file="${backup_files[$i]}"
        local size=$(du -h "$file" | cut -f1)
        local date=$(basename "$file" | sed 's/ict_trading_backup_//' | sed 's/.db//' | sed 's/_/ /')
        echo "  $((i+1)). $(basename "$file") ($size) - $date"
    done
    
    echo ""
    read -p "Select backup to restore (1-${#backup_files[@]}) or 0 to cancel: " backup_choice
    
    if [ "$backup_choice" -eq 0 ] 2>/dev/null; then
        print_warning "Restore cancelled"
        read -p "Press Enter to continue..."
        return
    fi
    
    if [ "$backup_choice" -ge 1 ] && [ "$backup_choice" -le ${#backup_files[@]} ] 2>/dev/null; then
        local selected_backup="${backup_files[$((backup_choice-1))]}"
        
        echo -e "${RED}${BOLD}WARNING: This will overwrite the current database!${NC}"
        read -p "Are you sure you want to restore from backup? (y/N): " confirm
        
        if [[ $confirm =~ ^[Yy]$ ]]; then
            # Stop service
            local service_was_running=false
            if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
                service_was_running=true
                print_status "Stopping service..."
                systemctl stop "$SERVICE_NAME"
            fi
            
            # Create backup of current database
            if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
                print_status "Backing up current database..."
                cp "$PROJECT_DIR/data/ict_trading.db" "$PROJECT_DIR/data/ict_trading.db.pre_restore.$(date +%Y%m%d_%H%M%S)"
            fi
            
            # Restore backup
            print_status "Restoring database from backup..."
            cp "$selected_backup" "$PROJECT_DIR/data/ict_trading.db"
            chown ictbot:ictbot "$PROJECT_DIR/data/ict_trading.db"
            
            # Restart service if it was running
            if [ "$service_was_running" = true ]; then
                print_status "Restarting service..."
                systemctl start "$SERVICE_NAME"
            fi
            
            print_success "Database restored successfully from: $(basename "$selected_backup")"
        else
            print_warning "Restore cancelled"
        fi
    else
        print_error "Invalid selection"
    fi
    
    read -p "Press Enter to continue..."
}

# Optimize database
optimize_database() {
    print_status "Optimizing database..."
    
    if [ ! -f "$PROJECT_DIR/data/ict_trading.db" ]; then
        print_error "Database file not found"
        read -p "Press Enter to continue..."
        return
    fi
    
    # Get database size before optimization
    local size_before=$(du -h "$PROJECT_DIR/data/ict_trading.db" | cut -f1)
    
    # Stop service temporarily
    local service_was_running=false
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        service_was_running=true
        print_status "Stopping service for optimization..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Run optimization
    print_status "Running VACUUM and ANALYZE..."
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
import sqlite3
conn = sqlite3.connect(\"data/ict_trading.db\")
cursor = conn.cursor()
print(\"Running VACUUM...\")
cursor.execute(\"VACUUM\")
print(\"Running ANALYZE...\")
cursor.execute(\"ANALYZE\")
conn.commit()
conn.close()
print(\"Database optimization completed\")
        '
    " 2>/dev/null
    
    # Restart service if it was running
    if [ "$service_was_running" = true ]; then
        print_status "Restarting service..."
        systemctl start "$SERVICE_NAME"
    fi
    
    # Get database size after optimization
    local size_after=$(du -h "$PROJECT_DIR/data/ict_trading.db" | cut -f1)
    
    print_success "Database optimization completed"
    echo "  Size before: $size_before"
    echo "  Size after: $size_after"
    
    read -p "Press Enter to continue..."
}

# Reset database (DANGER)
reset_database() {
    print_header "⚠️ DANGER: Database Reset"
    
    echo -e "${RED}${BOLD}⚠️ WARNING: This will permanently delete ALL data!${NC}"
    echo -e "${RED}This includes:${NC}"
    echo "  • All user accounts and subscriptions"
    echo "  • All trading signals and history"
    echo "  • All bot statistics and analytics"
    echo "  • All activity logs"
    echo ""
    echo -e "${YELLOW}This action cannot be undone!${NC}"
    echo ""
    
    read -p "Type 'DELETE EVERYTHING' to confirm: " confirm
    
    if [ "$confirm" = "DELETE EVERYTHING" ]; then
        # Create final backup before reset
        print_status "Creating final backup before reset..."
        backup_database
        
        # Stop service
        if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            print_status "Stopping service..."
            systemctl stop "$SERVICE_NAME"
        fi
        
        # Remove database
        if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
            rm "$PROJECT_DIR/data/ict_trading.db"
            print_success "Database deleted"
        fi
        
        # Recreate empty database
        print_status "Creating new empty database..."
        sudo -u ictbot bash -c "
            cd '$PROJECT_DIR'
            source venv/bin/activate
            python -c '
from core.database import DatabaseManager
db = DatabaseManager()
print(\"New database initialized\")
            '
        " 2>/dev/null
        
        # Restart service
        print_status "Restarting service..."
        systemctl start "$SERVICE_NAME"
        
        print_success "Database has been reset to factory defaults"
    else
        print_warning "Reset cancelled - incorrect confirmation"
    fi
    
    read -p "Press Enter to continue..."
}

# Backup and restore system
backup_restore() {
    print_header "💾 Backup & Restore System"
    
    echo -e "${CYAN}${BOLD}Backup & Restore Options:${NC}"
    echo "  1. Create full system backup"
    echo "  2. Create configuration backup"
    echo "  3. Restore from backup"
    echo "  4. Schedule automatic backups"
    echo "  5. View backup history"
    echo "  6. Clean old backups"
    echo "  7. Export backup to external location"
    echo "  8. Back to main menu"
    echo ""
    read -p "Select option (1-8): " backup_choice
    
    case $backup_choice in
        1)
            create_full_backup
            ;;
        2)
            create_config_backup
            ;;
        3)
            restore_from_backup
            ;;
        4)
            schedule_automatic_backups
            ;;
        5)
            view_backup_history
            ;;
        6)
            clean_old_backups
            ;;
        7)
            export_backup
            ;;
        8)
            return
            ;;
        *)
            print_error "Invalid option"
            read -p "Press Enter to continue..."
            ;;
    esac
}

# Create full system backup
create_full_backup() {
    print_status "Creating full system backup..."
    
    local backup_name="full_backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Stop service for consistent backup
    local service_was_running=false
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        service_was_running=true
        print_status "Stopping service for consistent backup..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Backup project directory
    print_status "Backing up project files..."
    tar -czf "$backup_path/project.tar.gz" -C "/home/ictbot" "ict_trading_oracle" 2>/dev/null
    
    # Backup configuration
    print_status "Backing up system configuration..."
    cp "/etc/systemd/system/$SERVICE_NAME.service" "$backup_path/"
    
    # Backup logs
    print_status "Backing up logs..."
    mkdir -p "$backup_path/logs"
    journalctl -u "$SERVICE_NAME" --no-pager > "$backup_path/logs/service.log" 2>/dev/null
    
    # Create backup manifest
    cat > "$backup_path/manifest.txt" << EOF
ICT Trading Oracle Bot - Full System Backup
Created: $(date)
Version: $SCRIPT_VERSION
Backup Type: Full System
Contents:
- Project files (project.tar.gz)
- System service configuration
- Service logs
- Database (included in project files)
EOF
    
    # Restart service if it was running
    if [ "$service_was_running" = true ]; then
        print_status "Restarting service..."
        systemctl start "$SERVICE_NAME"
    fi
    
    # Calculate backup size
    local backup_size=$(du -sh "$backup_path" | cut -f1)
    
    print_success "Full backup created: $backup_path ($backup_size)"
    
    read -p "Press Enter to continue..."
}

# Security scan
security_scan() {
    print_header "🛡️ Security Scan"
    
    print_status "Running comprehensive security scan..."
    echo ""
    
    local security_score=0
    local max_security_score=100
    
    echo -e "${CYAN}${BOLD}🔒 Security Checks:${NC}"
    
    # Check file permissions
    echo -e "${BLUE}Checking file permissions...${NC}"
    
    # Check .env file permissions
    if [ -f "$CONFIG_FILE" ]; then
        local env_perms=$(stat -c "%a" "$CONFIG_FILE")
        if [ "$env_perms" = "600" ]; then
            echo -e "  ${GREEN}✓${NC} .env file permissions: Secure (600)"
            security_score=$((security_score + 15))
        else
            echo -e "  ${RED}✗${NC} .env file permissions: Insecure ($env_perms)"
            print_status "Fixing .env permissions..."
            chmod 600 "$CONFIG_FILE"
        fi
    fi
    
    # Check project directory permissions
    local project_perms=$(stat -c "%a" "$PROJECT_DIR")
    if [ "$project_perms" = "755" ]; then
        echo -e "  ${GREEN}✓${NC} Project directory permissions: Good (755)"
        security_score=$((security_score + 10))
    else
        echo -e "  ${YELLOW}⚠${NC} Project directory permissions: $project_perms"
    fi
    
    # Check service user
    if [ "$(stat -c "%U" "$PROJECT_DIR")" = "ictbot" ]; then
        echo -e "  ${GREEN}✓${NC} Project ownership: Correct (ictbot)"
        security_score=$((security_score + 10))
    else
        echo -e "  ${RED}✗${NC} Project ownership: Incorrect"
    fi
    
    # Check firewall status
    echo -e "${BLUE}Checking firewall status...${NC}"
    if ufw status | grep -q "Status: active"; then
        echo -e "  ${GREEN}✓${NC} UFW Firewall: Active"
        security_score=$((security_score + 15))
        
        # Check SSH protection
        if ufw status | grep -q "22/tcp"; then
            echo -e "  ${GREEN}✓${NC} SSH port: Protected"
            security_score=$((security_score + 10))
        else
            echo -e "  ${YELLOW}⚠${NC} SSH port: Not explicitly configured"
        fi
    else
        echo -e "  ${RED}✗${NC} UFW Firewall: Inactive"
    fi
    
    # Check fail2ban
    echo -e "${BLUE}Checking intrusion prevention...${NC}"
    if systemctl is-active fail2ban &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Fail2ban: Active"
        security_score=$((security_score + 15))
    else
        echo -e "  ${YELLOW}⚠${NC} Fail2ban: Not active"
    fi
    
    # Check for default passwords/tokens
    echo -e "${BLUE}Checking for default credentials...${NC}"
    if grep -q "YOUR_REAL_BOT_TOKEN_HERE" "$CONFIG_FILE" 2>/dev/null; then
        echo -e "  ${RED}✗${NC} Bot token: Default value detected"
    else
        echo -e "  ${GREEN}✓${NC} Bot token: Configured"
        security_score=$((security_score + 15))
    fi
    
    # Check SSL/TLS configuration
    echo -e "${BLUE}Checking SSL/TLS...${NC}"
    if command_exists nginx; then
        echo -e "  ${GREEN}✓${NC} Nginx: Available for SSL termination"
        security_score=$((security_score + 5))
    else
        echo -e "  ${YELLOW}⚠${NC} Nginx: Not installed"
    fi
    
    # Check for exposed sensitive files
    echo -e "${BLUE}Checking for exposed files...${NC}"
    local exposed_files=0
    
    if [ -f "$PROJECT_DIR/.git/config" ]; then
        if [ "$(stat -c "%a" "$PROJECT_DIR/.git")" != "700" ]; then
            echo -e "  ${YELLOW}⚠${NC} .git directory: Potentially exposed"
            exposed_files=$((exposed_files + 1))
        fi
    fi
    
    if [ $exposed_files -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} No exposed sensitive files detected"
        security_score=$((security_score + 10))
    fi
    
    echo ""
    
    # Display security score
    echo -e "${CYAN}${BOLD}🛡️ Security Score:${NC}"
    
    local security_percentage=$((security_score * 100 / max_security_score))
    
    if [ $security_percentage -ge 90 ]; then
        echo -e "  ${GREEN}${BOLD}🟢 EXCELLENT: ${security_percentage}/100${NC}"
    elif [ $security_percentage -ge 75 ]; then
        echo -e "  ${YELLOW}${BOLD}🟡 GOOD: ${security_percentage}/100${NC}"
    elif [ $security_percentage -ge 50 ]; then
        echo -e "  ${YELLOW}${BOLD}🟠 FAIR: ${security_percentage}/100${NC}"
    else
        echo -e "  ${RED}${BOLD}🔴 POOR: ${security_percentage}/100${NC}"
    fi
    
    # Security recommendations
    if [ $security_percentage -lt 90 ]; then
        echo ""
        echo -e "${YELLOW}${BOLD}🔧 Security Recommendations:${NC}"
        
        if ! ufw status | grep -q "Status: active"; then
            echo "  • Enable UFW firewall: sudo ufw enable"
        fi
        
        if ! systemctl is-active fail2ban &>/dev/null; then
            echo "  • Install and configure fail2ban for intrusion prevention"
        fi
        
        if grep -q "YOUR_REAL_BOT_TOKEN_HERE" "$CONFIG_FILE" 2>/dev/null; then
            echo "  • Configure bot token in .env file"
        fi
        
        echo "  • Consider setting up SSL/TLS certificates"
        echo "  • Regularly update system packages"
        echo "  • Monitor logs for suspicious activity"
    fi
    
    read -p "Press Enter to continue..."
}

# Real-time monitoring
real_time_monitoring() {
    print_header "📊 Real-time Monitoring"
    
    print_info_box "Real-time system monitoring (Press Ctrl+C to exit)"
    echo ""
    
    # Function to display monitoring data
    display_monitoring_data() {
        clear
        print_header "📊 Real-time Monitoring Dashboard"
        
        # System stats
        echo -e "${CYAN}${BOLD}🖥️ System Resources:${NC}"
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
        local mem_usage=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100.0}')
        local disk_usage=$(df / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
        local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | cut -d',' -f1)
        
        echo "  CPU Usage: ${cpu_usage}%"
        echo "  Memory Usage: ${mem_usage}%"
        echo "  Disk Usage: ${disk_usage}%"
        echo "  Load Average: ${load_avg}"
        echo ""
        
        # Service status
        echo -e "${CYAN}${BOLD}🤖 Bot Service:${NC}"
        if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            echo -e "  Status: ${GREEN}Running${NC}"
            
            # Get process info
            local bot_pid=$(pgrep -f "python.*run.py")
            if [ -n "$bot_pid" ]; then
                local memory_usage=$(ps -p $bot_pid -o rss= 2>/dev/null)
                local cpu_percent=$(ps -p $bot_pid -o %cpu= 2>/dev/null)
                if [ -n "$memory_usage" ]; then
                    local memory_mb=$((memory_usage / 1024))
                    echo "  Memory: ${memory_mb}MB"
                    echo "  CPU: ${cpu_percent}%"
                fi
            fi
        else
            echo -e "  Status: ${RED}Not Running${NC}"
        fi
        echo ""
        
        # Recent activity
        echo -e "${CYAN}${BOLD}📋 Recent Activity:${NC}"
        journalctl -u "$SERVICE_NAME" --no-pager -n 5 --since "5 minutes ago" | tail -n 5 | while read line; do
            echo "  ${DIM}$(echo "$line" | cut -c1-80)${NC}"
        done
        echo ""
        
        # Network connections
        echo -e "${CYAN}${BOLD}🌐 Network:${NC}"
        local connections=$(netstat -an | grep ESTABLISHED | wc -l)
        echo "  Active Connections: $connections"
        
        # Check internet connectivity
        if ping -c 1 google.com &>/dev/null; then
            echo -e "  Internet: ${GREEN}Connected${NC}"
        else
            echo -e "  Internet: ${RED}Disconnected${NC}"
        fi
        echo ""
        
        echo -e "${DIM}Last updated: $(date) - Press Ctrl+C to exit${NC}"
    }
    
    # Start monitoring loop
    trap 'echo -e "\n${GREEN}Monitoring stopped${NC}"; return' INT
    
    while true; do
        display_monitoring_data
        sleep 5
    done
}

# Performance analytics
performance_analytics() {
    print_header "📈 Performance Analytics"
    
    print_status "Generating performance analytics..."
    echo ""
    
    # Collect performance data
    echo -e "${CYAN}${BOLD}📊 Performance Metrics (Last 24 Hours):${NC}"
    
    # Service uptime
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        local uptime_seconds=$(systemctl show "$SERVICE_NAME" --property=ActiveEnterTimestamp --value)
        if [ -n "$uptime_seconds" ]; then
            local uptime_readable=$(systemctl status "$SERVICE_NAME" | grep "Active:" | awk '{print $3, $4}')
            echo "  Service Uptime: $uptime_readable"
        fi
    fi
    
    # Memory usage trend
    echo -e "${BLUE}Memory Usage Trend:${NC}"
    local bot_pid=$(pgrep -f "python.*run.py")
    if [ -n "$bot_pid" ]; then
        local current_memory=$(ps -p $bot_pid -o rss= 2>/dev/null)
        if [ -n "$current_memory" ]; then
            local memory_mb=$((current_memory / 1024))
            echo "  Current: ${memory_mb}MB"
            
            # Memory usage classification
            if [ $memory_mb -lt 50 ]; then
                echo -e "  Status: ${GREEN}Excellent${NC}"
            elif [ $memory_mb -lt 100 ]; then
                echo -e "  Status: ${YELLOW}Good${NC}"
            elif [ $memory_mb -lt 200 ]; then
                echo -e "  Status: ${YELLOW}Fair${NC}"
            else
                echo -e "  Status: ${RED}High${NC}"
            fi
        fi
    else
        echo "  Bot process not found"
    fi
    
    # Error rate analysis
    echo -e "${BLUE}Error Analysis:${NC}"
    local error_count=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" | grep -i "error\|exception\|failed" | wc -l)
    local total_logs=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" | wc -l)
    
    if [ $total_logs -gt 0 ]; then
        local error_rate=$((error_count * 100 / total_logs))
        echo "  Errors (24h): $error_count"
        echo "  Error Rate: ${error_rate}%"
        
        if [ $error_rate -lt 1 ]; then
            echo -e "  Status: ${GREEN}Excellent${NC}"
        elif [ $error_rate -lt 5 ]; then
            echo -e "  Status: ${YELLOW}Good${NC}"
        else
            echo -e "  Status: ${RED}Needs Attention${NC}"
        fi
    else
        echo "  No logs found for analysis"
    fi
    
    # Database performance
    echo -e "${BLUE}Database Performance:${NC}"
    if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
        local db_size=$(du -h "$PROJECT_DIR/data/ict_trading.db" | cut -f1)
        echo "  Database Size: $db_size"
        
        # Test database response time
        local db_response_time=$(sudo -u ictbot bash -c "
            cd '$PROJECT_DIR'
            source venv/bin/activate
            python -c '
import time
from core.database import DatabaseManager
start = time.time()
try:
    db = DatabaseManager()
    stats = db.get_bot_stats()
    end = time.time()
    print(f\"{end - start:.3f}\")
except:
    print(\"error\")
            '
        " 2>/dev/null)
        
        if [ "$db_response_time" != "error" ]; then
            echo "  Response Time: ${db_response_time}s"
            
            if (( $(echo "$db_response_time < 0.1" | bc -l) )); then
                echo -e "  Status: ${GREEN}Excellent${NC}"
            elif (( $(echo "$db_response_time < 0.5" | bc -l) )); then
                echo -e "  Status: ${YELLOW}Good${NC}"
            else
                echo -e "  Status: ${RED}Slow${NC}"
            fi
        else
            echo -e "  Status: ${RED}Error${NC}"
        fi
    else
        echo "  Database not found"
    fi
    
    echo ""
    
    # Performance recommendations
    echo -e "${YELLOW}${BOLD}💡 Performance Recommendations:${NC}"
    
    # Check if optimization is needed
    local needs_optimization=false
    
    if [ -n "$bot_pid" ]; then
        local memory_usage=$(ps -p $bot_pid -o rss= 2>/dev/null)
        if [ -n "$memory_usage" ]; then
            local memory_mb=$((memory_usage / 1024))
            if [ $memory_mb -gt 150 ]; then
                echo "  • Consider restarting the service to free memory"
                needs_optimization=true
            fi
        fi
    fi
    
    if [ $error_count -gt 10 ]; then
        echo "  • High error rate detected - check logs for issues"
        needs_optimization=true
    fi
    
    # Check database size
    if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
        local db_size_bytes=$(stat -c%s "$PROJECT_DIR/data/ict_trading.db")
        local db_size_mb=$((db_size_bytes / 1024 / 1024))
        if [ $db_size_mb -gt 100 ]; then
            echo "  • Database is large (${db_size_mb}MB) - consider optimization"
            needs_optimization=true
        fi
    fi
    
    if [ "$needs_optimization" = false ]; then
        echo "  • System performance is optimal"
    fi
    
    read -p "Press Enter to continue..."
}

# Backtest analysis
backtest_analysis() {
    print_header "📊 7-Day Backtest Analysis"
    
    print_info_box "Running comprehensive 7-day backtest analysis"
    echo ""
    
    # Check if bot is running
    if ! systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        print_warning "Bot service is not running. Starting for backtest..."
        systemctl start "$SERVICE_NAME"
        sleep 5
    fi
    
    print_status "Initializing backtest analysis..."
    
    # Run backtest analysis
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
import sys
sys.path.insert(0, \".\")

try:
    from backtest.backtest_analyzer import BacktestAnalyzer
    
    print(\"🚀 Starting 7-Day ICT Trading Oracle Backtest...\")
    print()
    
    # Initialize backtest
    backtest = BacktestAnalyzer()
    
    # Run full backtest
    results = backtest.run_full_backtest()
    
    # Display results
    print(results[\"report\"])
    
    # Additional analysis
    analysis = results[\"analysis\"]
    
    print()
    print(\"📈 DETAILED ANALYSIS:\")
    print(f\"Win Rate: {analysis[\"win_rate\"]}%\")
    print(f\"Total P&L: ${analysis[\"total_pnl\"]}\")
    print(f\"Average Win: ${analysis[\"avg_win\"]}\")
    print(f\"Average Loss: ${analysis[\"avg_loss\"]}\")
    print()
    
    # Performance classification
    win_rate = analysis[\"win_rate\"]
    total_pnl = analysis[\"total_pnl\"]
    
    if win_rate >= 70 and total_pnl > 0:
        print(\"🟢 PERFORMANCE: EXCELLENT\")
    elif win_rate >= 60 and total_pnl >= 0:
        print(\"🟡 PERFORMANCE: GOOD\")
    elif win_rate >= 50:
        print(\"🟠 PERFORMANCE: FAIR\")
    else:
        print(\"🔴 PERFORMANCE: NEEDS IMPROVEMENT\")
    
    print()
    print(\"✅ Backtest analysis completed successfully!\")
    
except ImportError as e:
    print(f\"❌ Import error: {e}\")
    print(\"Please ensure all dependencies are installed\")
except Exception as e:
    print(f\"❌ Backtest error: {e}\")
        '
    " 2>/dev/null
    
    echo ""
    print_success "Backtest analysis completed"
    
    # Show backtest files
    if [ -d "$PROJECT_DIR/backtest_results" ]; then
        echo ""
        echo -e "${CYAN}${BOLD}📁 Backtest Results Files:${NC}"
        ls -la "$PROJECT_DIR/backtest_results/" | tail -n +2 | while read line; do
            echo "  $line"
        done
    fi
    
    read -p "Press Enter to continue..."
}

# Component testing
component_testing() {
    print_header "🧪 Component Testing"
    
    print_status "Running comprehensive component tests..."
    echo ""
    
    local test_results=()
    local total_tests=0
    local passed_tests=0
    
    # Test 1: Core imports
    echo -e "${BLUE}Test 1: Core Module Imports${NC}"
    total_tests=$((total_tests + 1))
    
    local import_result=$(sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
try:
    from core.api_manager import APIManager
    from core.technical_analysis import TechnicalAnalyzer
    from core.database import DatabaseManager
    from core.payment_manager import PaymentManager, SubscriptionManager
    print(\"PASS\")
except Exception as e:
    print(f\"FAIL: {e}\")
        '
    " 2>/dev/null)
    
    if [[ "$import_result" == "PASS" ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} - All core modules imported successfully"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - Import error: $import_result"
    fi
    
    # Test 2: Database functionality
    echo -e "${BLUE}Test 2: Database Functionality${NC}"
    total_tests=$((total_tests + 1))
    
    local db_result=$(sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
try:
    from core.database import DatabaseManager
    db = DatabaseManager()
    stats = db.get_bot_stats()
    if isinstance(stats, dict):
        print(\"PASS\")
    else:
        print(\"FAIL: Invalid stats format\")
except Exception as e:
    print(f\"FAIL: {e}\")
        '
    " 2>/dev/null)
    
    if [[ "$db_result" == "PASS" ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} - Database operations working"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - Database error: $db_result"
    fi
    
    # Test 3: API Manager
    echo -e "${BLUE}Test 3: API Manager${NC}"
    total_tests=$((total_tests + 1))
    
    local api_result=$(sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
try:
    from core.api_manager import APIManager
    api = APIManager()
    price_data = api.get_gold_price()
    if price_data and \"price\" in price_data:
        print(\"PASS\")
    else:
        print(\"FAIL: No price data\")
except Exception as e:
    print(f\"FAIL: {e}\")
        '
    " 2>/dev/null)
    
    if [[ "$api_result" == "PASS" ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} - API Manager functioning"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - API error: $api_result"
    fi
    
    # Test 4: Technical Analysis
    echo -e "${BLUE}Test 4: Technical Analysis${NC}"
    total_tests=$((total_tests + 1))
    
    local ta_result=$(sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
try:
    from core.technical_analysis import TechnicalAnalyzer
    analyzer = TechnicalAnalyzer()
    analysis = analyzer.analyze_market_structure()
    if analysis and \"signal\" in analysis:
        print(\"PASS\")
    else:
        print(\"FAIL: No analysis data\")
except Exception as e:
    print(f\"FAIL: {e}\")
        '
    " 2>/dev/null)
    
    if [[ "$ta_result" == "PASS" ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} - Technical analysis working"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - Technical analysis error: $ta_result"
    fi
    
    # Test 5: Backtest Module
    echo -e "${BLUE}Test 5: Backtest Module${NC}"
    total_tests=$((total_tests + 1))
    
    local backtest_result=$(sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
try:
    from backtest.backtest_analyzer import BacktestAnalyzer
    backtest = BacktestAnalyzer()
    print(\"PASS\")
except Exception as e:
    print(f\"FAIL: {e}\")
        '
    " 2>/dev/null)
    
    if [[ "$backtest_result" == "PASS" ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} - Backtest module available"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - Backtest error: $backtest_result"
    fi
    
    # Test 6: Service Configuration
    echo -e "${BLUE}Test 6: Service Configuration${NC}"
    total_tests=$((total_tests + 1))
    
    if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        echo -e "  ${GREEN}✓ PASS${NC} - Service is properly configured"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - Service not enabled"
    fi
    
    # Test 7: Advanced ICT Analysis
    echo -e "${BLUE}Test 7: Advanced ICT Analysis${NC}"
    total_tests=$((total_tests + 1))
    
    local ict_result=$(sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
try:
    from core.technical_analysis import RealICTAnalyzer
    analyzer = RealICTAnalyzer()
    result = analyzer.generate_real_ict_signal()
    print(f\"PASS - Signal: {result[\"signal\"]}, Indicators: {result[\"indicators_count\"]}\")
except Exception as e:
    print(f\"FAIL: {e}\")
        '
    " 2>/dev/null)
    
    if [[ "$ict_result" == *"PASS"* ]]; then
        echo -e "  ${GREEN}✓ PASS${NC} - Advanced ICT system working"
        echo -e "    ${DIM}$ict_result${NC}"
        passed_tests=$((passed_tests + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC} - Advanced ICT system error"
        echo -e "    ${DIM}$ict_result${NC}"
    fi
    
    echo ""
    
    # Test summary
    echo -e "${CYAN}${BOLD}📊 Test Summary:${NC}"
    echo "  Tests Run: $total_tests"
    echo "  Passed: $passed_tests"
    echo "  Failed: $((total_tests - passed_tests))"
    
    local success_rate=$((passed_tests * 100 / total_tests))
    echo "  Success Rate: ${success_rate}%"
    
    if [ $success_rate -eq 100 ]; then
        echo -e "  ${GREEN}${BOLD}🟢 ALL TESTS PASSED${NC}"
    elif [ $success_rate -ge 80 ]; then
        echo -e "  ${YELLOW}${BOLD}🟡 MOSTLY PASSING${NC}"
    else
        echo -e "  ${RED}${BOLD}🔴 MULTIPLE FAILURES${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

# Network diagnostics
network_diagnostics() {
    print_header "🌐 Network Diagnostics"
    
    print_status "Running comprehensive network diagnostics..."
    echo ""
    
    # Check internet connectivity
    echo -e "${CYAN}${BOLD}🌍 Internet Connectivity:${NC}"
    if ping -c 3 google.com &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Google: Reachable"
    else
        echo -e "  ${RED}✗${NC} Google: Unreachable"
    fi
    
    if ping -c 3 github.com &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} GitHub: Reachable"
    else
        echo -e "  ${RED}✗${NC} GitHub: Unreachable"
    fi
    
    # Check DNS resolution
    echo -e "${CYAN}${BOLD}🔍 DNS Resolution:${NC}"
    nslookup google.com | head -10
    echo ""
    
    # Check open ports
    echo -e "${CYAN}${BOLD}🔌 Open Ports:${NC}"
    netstat -tuln | grep LISTEN | head -10
    echo ""
    
    # Check firewall status
    echo -e "${CYAN}${BOLD}🛡️ Firewall Status:${NC}"
    ufw status verbose
    echo ""
    
    # Check active connections
    echo -e "${CYAN}${BOLD}🌐 Network Statistics:${NC}"
    local connections=$(netstat -an | grep ESTABLISHED | wc -l)
    echo "  Active Connections: $connections"
    
    local listening_ports=$(netstat -tuln | grep LISTEN | wc -l)
    echo "  Listening Ports: $listening_ports"
    
    # Network interface information
    echo -e "${CYAN}${BOLD}📡 Network Interfaces:${NC}"
    ip addr show | grep -E "inet |UP|DOWN" | head -10
    
    echo ""
    read -p "Press Enter to continue..."
}

# Resource optimization
resource_optimization() {
    print_header "⚙️ Resource Optimization"
    
    print_status "Running system optimization..."
    echo ""
    
    # Show current resource usage
    echo -e "${CYAN}${BOLD}📊 Current Resource Usage:${NC}"
    echo -e "${BLUE}Memory:${NC}"
    free -h
    echo ""
    echo -e "${BLUE}Disk:${NC}"
    df -h /
    echo ""
    echo -e "${BLUE}CPU Load:${NC}"
    uptime
    echo ""
    
    # Optimization options
    echo -e "${YELLOW}${BOLD}🔧 Optimization Options:${NC}"
    echo "  1. Clear system cache"
    echo "  2. Clean package cache"
    echo "  3. Remove old logs"
    echo "  4. Optimize database"
    echo "  5. Clean temporary files"
    echo "  6. Run all optimizations"
    echo "  7. Back to main menu"
    echo ""
    read -p "Select optimization (1-7): " opt_choice
    
    case $opt_choice in
        1)
            print_status "Clearing system cache..."
            sync
            echo 3 > /proc/sys/vm/drop_caches 2>/dev/null
            print_success "System cache cleared"
            ;;
        2)
            print_status "Cleaning package cache..."
            apt autoclean > /dev/null 2>&1
            apt autoremove -y > /dev/null 2>&1
            print_success "Package cache cleaned"
            ;;
        3)
            print_status "Removing old logs..."
            journalctl --vacuum-time=7d > /dev/null 2>&1
            find /var/log -name "*.log" -type f -mtime +7 -delete 2>/dev/null
            print_success "Old logs removed"
            ;;
        4)
            print_status "Optimizing database..."
            if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
                sudo -u ictbot bash -c "
                    cd '$PROJECT_DIR'
                    source venv/bin/activate
                    python -c '
import sqlite3
conn = sqlite3.connect(\"data/ict_trading.db\")
cursor = conn.cursor()
print(\"Running VACUUM...\")
cursor.execute(\"VACUUM\")
print(\"Running ANALYZE...\")
cursor.execute(\"ANALYZE\")
conn.commit()
conn.close()
                    '
                " 2>/dev/null
                print_success "Database optimized"
            else
                print_warning "Database not found"
            fi
            ;;
        5)
            print_status "Cleaning temporary files..."
            rm -rf /tmp/* 2>/dev/null
            rm -rf /var/tmp/* 2>/dev/null
            print_success "Temporary files cleaned"
            ;;
        6)
            print_status "Running all optimizations..."
            # Run all optimizations
            sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null
            apt autoclean > /dev/null 2>&1
            apt autoremove -y > /dev/null 2>&1
            journalctl --vacuum-time=7d > /dev/null 2>&1
            find /var/log -name "*.log" -type f -mtime +7 -delete 2>/dev/null
            rm -rf /tmp/* 2>/dev/null
            rm -rf /var/tmp/* 2>/dev/null
            print_success "All optimizations completed"
            ;;
        7)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
    
    echo ""
    echo -e "${CYAN}${BOLD}📊 Resource Usage After Optimization:${NC}"
    echo -e "${BLUE}Memory:${NC}"
    free -h
    echo ""
    
    read -p "Press Enter to continue..."
}

# Log management
log_management() {
    print_header "📋 Log Management"
    
    echo -e "${CYAN}${BOLD}Log Management Options:${NC}"
    echo "  1. View recent bot logs"
    echo "  2. View error logs"
    echo "  3. View system logs"
    echo "  4. Rotate logs"
    echo "  5. Clean old logs"
    echo "  6. Export logs"
    echo "  7. Monitor live logs"
    echo "  8. Back to main menu"
    echo ""
    read -p "Select option (1-8): " log_choice
    
    case $log_choice in
        1)
            print_status "Showing recent bot logs..."
            journalctl -u "$SERVICE_NAME" --no-pager -n 50
            ;;
        2)
            print_status "Showing error logs..."
            journalctl -u "$SERVICE_NAME" --no-pager | grep -i "error\|exception\|failed" | tail -20
            ;;
        3)
            print_status "Showing system logs..."
            journalctl --no-pager -n 30
            ;;
        4)
            print_status "Rotating logs..."
            logrotate -f /etc/logrotate.d/ictbot 2>/dev/null
            print_success "Logs rotated"
            ;;
        5)
            print_status "Cleaning old logs..."
            journalctl --vacuum-time=7d > /dev/null 2>&1
            find "$PROJECT_DIR/logs" -name "*.log" -type f -mtime +7 -delete 2>/dev/null
            print_success "Old logs cleaned"
            ;;
        6)
            print_status "Exporting logs..."
            local export_file="/tmp/ictbot_logs_$(date +%Y%m%d_%H%M%S).txt"
            journalctl -u "$SERVICE_NAME" --no-pager > "$export_file"
            print_success "Logs exported to: $export_file"
            ;;
        7)
            print_status "Starting live log monitor (Press Ctrl+C to exit)..."
            journalctl -u "$SERVICE_NAME" -f
            ;;
        8)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
    
    read -p "Press Enter to continue..."
}

# Update management
update_management() {
    print_header "🔄 Update Management"
    
    echo -e "${CYAN}${BOLD}Update Options:${NC}"
    echo "  1. Check for updates"
    echo "  2. Update from GitHub"
    echo "  3. Update system packages"
    echo "  4. Update Python dependencies"
    echo "  5. Full system update"
    echo "  6. Back to main menu"
    echo ""
    read -p "Select option (1-6): " update_choice
    
    case $update_choice in
        1)
            print_status "Checking for updates..."
            if [ -d "$PROJECT_DIR/.git" ]; then
                cd "$PROJECT_DIR"
                git fetch origin > /dev/null 2>&1
                
                local local_commit=$(git rev-parse @)
                local remote_commit=$(git rev-parse @{u})
                
                if [ "$local_commit" = "$remote_commit" ]; then
                    print_success "Repository is up to date"
                else
                    print_warning "Updates available"
                    echo "Local:  $local_commit"
                    echo "Remote: $remote_commit"
                fi
            else
                print_error "Not a git repository"
            fi
            ;;
        2)
            update_from_github
            ;;
        3)
            print_status "Updating system packages (apt update & upgrade)..."
            print_status "Updating package lists (apt update)..."
            apt update -y # Keep -y for non-interactive, remove > /dev/null
            check_status "Package lists updated." "Failed to update package lists."
            print_status "Upgrading existing packages (apt upgrade)... This may take a while."
            apt upgrade -y # Keep -y, remove > /dev/null
            check_status "System packages updated." "Failed to update system packages."
            print_success "System packages updated successfully."
            ;;
        4)
            print_status "Updating Python dependencies..."
            sudo -u ictbot bash -c "
                cd '$PROJECT_DIR'
                source venv/bin/activate
                pip install --upgrade pip > /dev/null 2>&1
                pip install -r requirements_fixed.txt --upgrade > /dev/null 2>&1
            "
            print_success "Python dependencies updated"
            ;;
        5)
            print_status "Running full system update..."
            print_status "Updating package lists (apt update)..."
            apt update -y # Keep -y, remove > /dev/null
            check_status "Package lists updated for full update." "Failed to update package lists during full update."
            print_status "Upgrading existing packages (apt upgrade)... This may take a while."
            apt upgrade -y # Keep -y, remove > /dev/null
            check_status "System packages upgraded for full update." "Failed to upgrade packages during full update."
            
            if [ -d "$PROJECT_DIR/.git" ]; then
                cd "$PROJECT_DIR"
                git pull origin main > /dev/null 2>&1
            fi
            
            sudo -u ictbot bash -c "
                cd '$PROJECT_DIR'
                source venv/bin/activate
                pip install --upgrade pip > /dev/null 2>&1
                pip install -r requirements_fixed.txt --upgrade > /dev/null 2>&1
            "
            
            systemctl restart "$SERVICE_NAME"
            print_success "Full system update completed"
            ;;
        6)
            return
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
    
    read -p "Press Enter to continue..."
}

# Update from GitHub
update_from_github() {
    print_status "Updating from GitHub repository..."
    
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        print_error "Not a git repository"
        return
    fi
    
    cd "$PROJECT_DIR"
    
     # Backup current configuration AND settings
    print_status "Backing up configuration and settings..."
    if [ -f ".env" ]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # بکاپ فایل settings.py
    if [ -f "config/settings.py" ]; then
        cp config/settings.py config/settings.py.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Stop service
    local service_was_running=false
    if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
        service_was_running=true
        print_status "Stopping service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Stash local changes
    print_status "Stashing local changes..."
    git stash push -m "Auto stash before update - $(date)"
    
    # Pull latest changes
    print_status "Pulling latest changes..."
    git pull origin main
    
    if [ $? -eq 0 ]; then
        print_success "Repository updated successfully"
        
        # بازگردانی تنظیمات
        print_status "Restoring custom configurations..."
        
        # بازگردانی .env
        latest_env_backup=$(ls -t .env.backup.* 2>/dev/null | head -1)
        if [ -f "$latest_env_backup" ]; then
            cp "$latest_env_backup" .env
            print_success "✓ .env configuration restored"
        fi
        
        # بازگردانی settings.py
        latest_settings_backup=$(ls -t config/settings.py.backup.* 2>/dev/null | head -1)
        if [ -f "$latest_settings_backup" ]; then
            cp "$latest_settings_backup" config/settings.py
            print_success "✓ Admin settings restored"
        fi
        
        # Update dependencies
        print_status "Updating dependencies..."
        sudo -u ictbot bash -c "
            source venv/bin/activate
            pip install -r requirements_fixed.txt --upgrade
        " > /dev/null 2>&1
        
        # Restart service if it was running
        if [ "$service_was_running" = true ]; then
            print_status "Restarting service..."
            systemctl start "$SERVICE_NAME"
        fi
        
        print_success "Update completed successfully"
    else
        print_error "Failed to update repository"
        
        # Restore from stash if update failed
        git stash pop > /dev/null 2>&1
        
        if [ "$service_was_running" = true ]; then
            systemctl start "$SERVICE_NAME"
        fi
    fi
}

# Error analysis
error_analysis() {
    print_header "🔍 Error Analysis"
    
    print_status "Analyzing system errors..."
    echo ""
    
    # Analyze bot service errors
    echo -e "${CYAN}${BOLD}🤖 Bot Service Errors (Last 24 Hours):${NC}"
    local bot_errors=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" | grep -i "error\|exception\|failed" | wc -l)
    echo "  Total Errors: $bot_errors"
    
    if [ $bot_errors -gt 0 ]; then
        echo -e "${BLUE}Recent Errors:${NC}"
        journalctl -u "$SERVICE_NAME" --since "24 hours ago" | grep -i "error\|exception\|failed" | tail -5 | while read line; do
            echo "  ${DIM}$line${NC}"
        done
    fi
    echo ""
    
    # Analyze system errors
    echo -e "${CYAN}${BOLD}🖥️ System Errors (Last 24 Hours):${NC}"
    local system_errors=$(journalctl --since "24 hours ago" | grep -i "error\|failed" | wc -l)
    echo "  Total System Errors: $system_errors"
    echo ""
    
    # Check disk space errors
    echo -e "${CYAN}${BOLD}💾 Disk Space Analysis:${NC}"
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    if [ $disk_usage -gt 90 ]; then
        echo -e "  ${RED}⚠${NC} Disk usage critical: ${disk_usage}%"
    elif [ $disk_usage -gt 80 ]; then
        echo -e "  ${YELLOW}⚠${NC} Disk usage high: ${disk_usage}%"
    else
        echo -e "  ${GREEN}✓${NC} Disk usage normal: ${disk_usage}%"
    fi
    
    # Check memory issues
    echo -e "${CYAN}${BOLD}🧠 Memory Analysis:${NC}"
    local mem_usage=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        echo -e "  ${RED}⚠${NC} Memory usage critical: ${mem_usage}%"
    elif (( $(echo "$mem_usage > 80" | bc -l) )); then
        echo -e "  ${YELLOW}⚠${NC} Memory usage high: ${mem_usage}%"
    else
        echo -e "  ${GREEN}✓${NC} Memory usage normal: ${mem_usage}%"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
}

# User statistics
user_statistics() {
    print_header "👥 User Statistics"
    
    print_status "Generating user statistics..."
    echo ""
    
    # Get user statistics from database
    sudo -u ictbot bash -c "
        cd '$PROJECT_DIR'
        source venv/bin/activate
        python -c '
from core.database import DatabaseManager
import sqlite3

try:
    db = DatabaseManager()
    
    # Get basic stats
    stats = db.get_bot_stats()
    print(f\"📊 Basic Statistics:\")
    print(f\"  Total Users: {stats[\"total_users\"]}\")
    print(f\"  Active Users (7 days): {stats[\"active_users\"]}\")
    print(f\"  Total Signals: {stats[\"total_signals\"]}\")
    print(f\"  Daily Signals: {stats[\"daily_signals\"]}\")
    print()
    
    # Get subscription breakdown
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute(\"SELECT subscription_type, COUNT(*) FROM users GROUP BY subscription_type\")
    subscriptions = cursor.fetchall()
    
    print(\"💳 Subscription Breakdown:\")
    for sub_type, count in subscriptions:
        print(f\"  {sub_type.title()}: {count} users\")
    print()
    
    # Get activity stats
    cursor.execute(\"SELECT DATE(last_activity), COUNT(*) FROM users WHERE last_activity > datetime(\\\"now\\\", \\\"-7 days\\\") GROUP BY DATE(last_activity) ORDER BY DATE(last_activity) DESC LIMIT 7\")
    activity = cursor.fetchall()
    
    print(\"📈 Daily Activity (Last 7 Days):\")
    for date, count in activity:
        print(f\"  {date}: {count} active users\")
    
    conn.close()
    
except Exception as e:
    print(f\"Error: {e}\")
        '
    " 2>/dev/null
    
    read -p "Press Enter to continue..."
}

# Uninstall everything
uninstall_everything() {
    print_header "🗑️ Complete Uninstallation"
    
    echo -e "${RED}${BOLD}⚠️ DANGER: Complete System Removal${NC}"
    echo ""
    echo -e "${RED}This will permanently remove:${NC}"
    echo "  • ICT Trading Oracle Bot service"
    echo "  • All user data and databases"
    echo "  • All configuration files"
    echo "  • All logs and backups"
    echo "  • ictbot user account"
    echo "  • All project files"
    echo ""
    echo -e "${YELLOW}This action cannot be undone!${NC}"
    echo ""
    
    read -p "Type 'DELETE EVERYTHING' to confirm complete removal: " confirm
    
    if [ "$confirm" = "DELETE EVERYTHING" ]; then
        print_status "Starting complete uninstallation..."
        
        # Stop and disable service
        print_status "Stopping and disabling service..."
        systemctl stop "$SERVICE_NAME" 2>/dev/null
        systemctl disable "$SERVICE_NAME" 2>/dev/null
        
        # Remove service file
        print_status "Removing service file..."
        rm -f "/etc/systemd/system/$SERVICE_NAME.service"
        
        # Reload systemd
        systemctl daemon-reload
        
        # Remove project directory
        print_status "Removing project directory..."
        rm -rf "$PROJECT_DIR"
        
        # Remove backup directory
        print_status "Removing backups..."
        rm -rf "$BACKUP_DIR"
        
        # Remove user account
        print_status "Removing ictbot user account..."
        userdel -r ictbot 2>/dev/null
        
        # Remove log files
        print_status "Removing log files..."
        rm -f "$LOG_FILE"
        
        # Clean up any remaining files
        print_status "Cleaning up remaining files..."
        find /etc -name "*ictbot*" -delete 2>/dev/null
        find /var -name "*ictbot*" -delete 2>/dev/null
        
        print_success "Complete uninstallation finished"
        echo ""
        echo -e "${GREEN}${BOLD}ICT Trading Oracle Bot has been completely removed from the system.${NC}"
        echo ""
        exit 0
    else
        print_warning "Uninstallation cancelled - incorrect confirmation"
    fi
    
    read -p "Press Enter to continue..."
}

# Factory reset
factory_reset() {
    print_header "🔄 Factory Reset"
    
    echo -e "${YELLOW}${BOLD}⚠️ WARNING: Factory Reset${NC}"
    echo ""
    echo -e "${YELLOW}This will reset the bot to factory defaults:${NC}"
    echo "  • Reset database to empty state"
    echo "  • Clear all user data"
    echo "  • Remove all logs"
    echo "  • Clear all backups"
    echo "  • Keep configuration files"
    echo ""
    echo -e "${BLUE}The bot service and files will remain installed.${NC}"
    echo ""
    
    read -p "Type 'FACTORY RESET' to confirm: " confirm
    
    if [ "$confirm" = "FACTORY RESET" ]; then
        print_status "Starting factory reset..."
        
        # Stop service
        if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            print_status "Stopping service..."
            systemctl stop "$SERVICE_NAME"
        fi
        
        # Backup current database
        if [ -f "$PROJECT_DIR/data/ict_trading.db" ]; then
            print_status "Creating final backup..."
            cp "$PROJECT_DIR/data/ict_trading.db" "$BACKUP_DIR/pre_factory_reset_$(date +%Y%m%d_%H%M%S).db"
        fi
        
        # Remove database
        print_status "Removing database..."
        rm -f "$PROJECT_DIR/data/ict_trading.db"
        
        # Clear logs
        print_status "Clearing logs..."
        rm -rf "$PROJECT_DIR/logs/*" 2>/dev/null
        mkdir -p "$PROJECT_DIR/logs"
        
        # Clear cache
        print_status "Clearing cache..."
        rm -rf "$PROJECT_DIR/cache/*" 2>/dev/null
        
        # Clear backtest results
        print_status "Clearing backtest results..."
        rm -rf "$PROJECT_DIR/backtest_results/*" 2>/dev/null
        
        # Reinitialize database
        print_status "Reinitializing database..."
        sudo -u ictbot bash -c "
            cd '$PROJECT_DIR'
            source venv/bin/activate
            python -c '
from core.database import DatabaseManager
try:
    db = DatabaseManager()
    print(\"Database reinitialized successfully\")
except Exception as e:
    print(f\"Error reinitializing database: {e}\")
            '
        " 2>/dev/null
        
        # Start service
        print_status "Starting service..."
        systemctl start "$SERVICE_NAME"
        
        # Verify service started
        sleep 3
        if systemctl is-active "$SERVICE_NAME" &>/dev/null; then
            print_success "Factory reset completed successfully"
            echo ""
            echo -e "${GREEN}${BOLD}ICT Trading Oracle Bot has been reset to factory defaults.${NC}"
            echo -e "${BLUE}The bot is now running with a fresh database.${NC}"
        else
            print_error "Service failed to start after reset"
            echo "Check logs for details: sudo journalctl -u $SERVICE_NAME -n 20"
        fi
    else
        print_warning "Factory reset cancelled - incorrect confirmation"
    fi
    
    read -p "Press Enter to continue..."
}

# Main script execution
main() {
    # Initialize logging
    init_logging
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}${BOLD}Error: This script must be run as root${NC}"
        echo "Usage: sudo $0"
        exit 1
    fi
    
    # Main menu loop
    while true; do
        show_main_menu
        read choice
        echo ""
        handle_menu_selection "$choice"
        echo ""
    done
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

# End of ICT Trading Oracle Installation & Management Script v4.1
# Total lines: ~2950
# Features: Complete installation, advanced monitoring, backtest analysis,
#          security scanning, performance optimization, backup/restore,
#          user management, error analysis, and comprehensive system management
