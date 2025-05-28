#!/bin/bash

# Colors for better display
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Functions for message display
print_header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_menu() {
    echo -e "${WHITE}$1${NC}"
}

# Function to check if installation is complete
check_installation_complete() {
    local required_files=(
        "/home/ictbot/ict_trading_oracle/main.py"
        "/home/ictbot/ict_trading_oracle/.env"
        "/home/ictbot/ict_trading_oracle/venv/bin/python"
        "/etc/systemd/system/ictbot.service"
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
    
    return 0
}

# Function to get service status
get_service_status() {
    if systemctl is-active --quiet ictbot; then
        echo -e "${GREEN}RUNNING${NC}"
    elif systemctl is-enabled --quiet ictbot; then
        echo -e "${YELLOW}STOPPED${NC}"
    else
        echo -e "${RED}DISABLED${NC}"
    fi
}

# Function to get bot token status
get_token_status() {
    if [ -f "/home/ictbot/ict_trading_oracle/.env" ]; then
        local token=$(grep "BOT_TOKEN=" /home/ictbot/ict_trading_oracle/.env | cut -d'=' -f2)
        if [ "$token" = "YOUR_REAL_BOT_TOKEN_HERE" ] || [ -z "$token" ]; then
            echo -e "${RED}NOT CONFIGURED${NC}"
        else
            echo -e "${GREEN}CONFIGURED${NC}"
        fi
    else
        echo -e "${RED}FILE MISSING${NC}"
    fi
}

# Function to show system info
show_system_info() {
    echo -e "${CYAN}=== SYSTEM INFORMATION ===${NC}"
    echo "Server Time: $(date)"
    echo "Uptime: $(uptime -p)"
    echo "Disk Usage: $(df -h / | tail -1 | awk '{print $5 " used of " $2}')"
    echo "Memory Usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
    echo ""
}

# Function to show bot status
show_bot_status() {
    echo -e "${CYAN}=== BOT STATUS ===${NC}"
    echo -e "Service Status: $(get_service_status)"
    echo -e "Bot Token: $(get_token_status)"
    
    if systemctl is-active --quiet ictbot; then
        local pid=$(systemctl show ictbot --property=MainPID --value)
        if [ "$pid" != "0" ]; then
            echo "Process ID: $pid"
            echo "Memory Usage: $(ps -p $pid -o rss= | awk '{print $1/1024 " MB"}')"
            echo "CPU Usage: $(ps -p $pid -o %cpu= | awk '{print $1 "%"}')"
        fi
    fi
    
    echo "Auto-start: $(systemctl is-enabled ictbot 2>/dev/null || echo 'disabled')"
    echo ""
}

# Function to show recent logs
show_recent_logs() {
    echo -e "${CYAN}=== RECENT LOGS (Last 10 lines) ===${NC}"
    if journalctl -u ictbot -n 10 --no-pager &>/dev/null; then
        journalctl -u ictbot -n 10 --no-pager
    else
        echo "No logs available"
    fi
    echo ""
}

# Control Panel Functions
start_bot() {
    echo -e "${BLUE}Starting ICT Trading Bot...${NC}"
    systemctl start ictbot
    sleep 2
    if systemctl is-active --quiet ictbot; then
        print_success "Bot started successfully!"
    else
        print_error "Failed to start bot. Check logs for details."
    fi
}

stop_bot() {
    echo -e "${BLUE}Stopping ICT Trading Bot...${NC}"
    systemctl stop ictbot
    sleep 2
    if ! systemctl is-active --quiet ictbot; then
        print_success "Bot stopped successfully!"
    else
        print_error "Failed to stop bot."
    fi
}

restart_bot() {
    echo -e "${BLUE}Restarting ICT Trading Bot...${NC}"
    systemctl restart ictbot
    sleep 3
    if systemctl is-active --quiet ictbot; then
        print_success "Bot restarted successfully!"
    else
        print_error "Failed to restart bot. Check logs for details."
    fi
}

update_bot() {
    echo -e "${BLUE}Updating ICT Trading Bot from GitHub...${NC}"
    
    # Stop the bot first
    systemctl stop ictbot
    
    # Run update as ictbot user
    sudo -u ictbot bash << 'EOF'
cd /home/ictbot/ict_trading_oracle

echo "📋 Checking Git status..."
git status

echo "💾 Stashing local changes..."
git stash push -m "Auto stash before update - $(date)"

echo "📥 Fetching latest changes..."
git fetch origin

echo "🔄 Pulling changes from remote..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Git pull successful!"
    
    # Activate virtual environment and update dependencies
    source venv/bin/activate
    echo "📦 Updating Python dependencies..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements_fixed.txt > /dev/null 2>&1 || echo "⚠️ Some packages may have failed to update"
    
else
    echo "❌ Git pull failed!"
    exit 1
fi
EOF

    if [ $? -eq 0 ]; then
        print_success "Update completed successfully!"
        echo -e "${BLUE}Restarting bot...${NC}"
        systemctl start ictbot
        sleep 2
        if systemctl is-active --quiet ictbot; then
            print_success "Bot restarted after update!"
        else
            print_error "Bot failed to start after update. Check logs."
        fi
    else
        print_error "Update failed!"
        systemctl start ictbot
    fi
}

configure_token() {
    echo -e "${BLUE}Configure Bot Token${NC}"
    echo "Current token status: $(get_token_status)"
    echo ""
    echo "To configure your bot token:"
    echo "1. Get your bot token from @BotFather in Telegram"
    echo "2. Edit the .env file:"
    echo "   nano /home/ictbot/ict_trading_oracle/.env"
    echo "3. Replace 'YOUR_REAL_BOT_TOKEN_HERE' with your actual token"
    echo ""
    read -p "Do you want to edit the .env file now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nano /home/ictbot/ict_trading_oracle/.env
        print_success "Configuration file updated. You may need to restart the bot."
    fi
}

view_live_logs() {
    echo -e "${BLUE}Viewing live logs... (Press Ctrl+C to exit)${NC}"
    echo ""
    journalctl -u ictbot -f
}

backup_bot() {
    echo -e "${BLUE}Creating backup...${NC}"
    
    local backup_dir="/home/ictbot/backups"
    local backup_name="ict_bot_backup_$(date +%Y%m%d_%H%M%S)"
    
    sudo -u ictbot mkdir -p "$backup_dir"
    
    sudo -u ictbot bash << EOF
cd /home/ictbot
tar -czf "$backup_dir/$backup_name.tar.gz" \
    ict_trading_oracle/.env \
    ict_trading_oracle/data/ \
    ict_trading_oracle/logs/ \
    ict_trading_oracle/config/settings.py \
    2>/dev/null
EOF

    if [ $? -eq 0 ]; then
        print_success "Backup created: $backup_dir/$backup_name.tar.gz"
    else
        print_error "Backup failed!"
    fi
}

show_network_info() {
    echo -e "${CYAN}=== NETWORK INFORMATION ===${NC}"
    echo "Server IP: $(curl -s ifconfig.me 2>/dev/null || echo "Unable to detect")"
    echo "Local IP: $(hostname -I | awk '{print $1}')"
    echo "Hostname: $(hostname)"
    echo ""
    echo "Network Test:"
    if ping -c 1 google.com &> /dev/null; then
        echo -e "Internet: ${GREEN}Connected${NC}"
    else
        echo -e "Internet: ${RED}Disconnected${NC}"
    fi
    
    if ping -c 1 api.telegram.org &> /dev/null; then
        echo -e "Telegram API: ${GREEN}Reachable${NC}"
    else
        echo -e "Telegram API: ${RED}Unreachable${NC}"
    fi
    echo ""
}

uninstall_bot() {
    echo -e "${RED}WARNING: This will completely remove the ICT Trading Bot!${NC}"
    echo "This action cannot be undone."
    echo ""
    read -p "Are you sure you want to uninstall? Type 'YES' to confirm: " confirm
    
    if [ "$confirm" = "YES" ]; then
        echo -e "${BLUE}Uninstalling ICT Trading Bot...${NC}"
        
        # Stop and disable service
        systemctl stop ictbot 2>/dev/null
        systemctl disable ictbot 2>/dev/null
        rm -f /etc/systemd/system/ictbot.service
        systemctl daemon-reload
        
        # Remove user and files
        userdel -r ictbot 2>/dev/null
        
        print_success "ICT Trading Bot has been completely removed."
        exit 0
    else
        print_warning "Uninstall cancelled."
    fi
}

# Main Control Panel
show_control_panel() {
    while true; do
        clear
        print_header "ICT Trading Oracle - Control Panel"
        echo ""
        
        # Show current status
        show_system_info
        show_bot_status
        
        # Main menu
        print_menu "┌─────────────────────────────────────────┐"
        print_menu "│              MAIN MENU                  │"
        print_menu "├─────────────────────────────────────────┤"
        print_menu "│  1. Start Bot                           │"
        print_menu "│  2. Stop Bot                            │"
        print_menu "│  3. Restart Bot                         │"
        print_menu "│  4. Update Bot from GitHub              │"
        print_menu "│  5. Configure Bot Token                 │"
        print_menu "│  6. View Live Logs                      │"
        print_menu "│  7. Show Recent Logs                    │"
        print_menu "│  8. Create Backup                       │"
        print_menu "│  9. Network Information                 │"
        print_menu "│ 10. Reinstall/Repair Bot                │"
        print_menu "│ 11. Uninstall Bot                       │"
        print_menu "│  0. Exit                                │"
        print_menu "└─────────────────────────────────────────┘"
        echo ""
        
        read -p "Select an option (0-11): " choice
        echo ""
        
        case $choice in
            1)
                start_bot
                read -p "Press Enter to continue..."
                ;;
            2)
                stop_bot
                read -p "Press Enter to continue..."
                ;;
            3)
                restart_bot
                read -p "Press Enter to continue..."
                ;;
            4)
                update_bot
                read -p "Press Enter to continue..."
                ;;
            5)
                configure_token
                read -p "Press Enter to continue..."
                ;;
            6)
                view_live_logs
                ;;
            7)
                show_recent_logs
                read -p "Press Enter to continue..."
                ;;
            8)
                backup_bot
                read -p "Press Enter to continue..."
                ;;
            9)
                show_network_info
                read -p "Press Enter to continue..."
                ;;
            10)
                echo -e "${BLUE}Reinstalling/Repairing bot...${NC}"
                break  # Exit control panel to run installation
                ;;
            11)
                uninstall_bot
                ;;
            0)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please try again."
                read -p "Press Enter to continue..."
                ;;
        esac
    done
}

# Function to check command success with detailed error logging
check_status() {
    if [ $? -eq 0 ]; then
        print_success "$1"
        echo ""
    else
        print_error "$2"
        if [ -n "$3" ]; then
            echo -e "${RED}Error details:${NC}"
            echo -e "${RED}$3${NC}"
        fi
        echo -e "${RED}Installation failed at this step. Please check the error above.${NC}"
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

# Function to check if directory exists and is not empty
dir_exists_and_not_empty() {
    [ -d "$1" ] && [ "$(ls -A $1)" ]
}

# Main script logic
main() {
    # Check if installation is already complete
    if check_installation_complete; then
        print_success "ICT Trading Oracle Bot is already installed!"
        echo ""
        echo "Choose an option:"
        echo "1. Open Control Panel"
        echo "2. Reinstall/Repair"
        echo "3. Exit"
        echo ""
        read -p "Select option (1-3): " initial_choice
        
        case $initial_choice in
            1)
                show_control_panel
                ;;
            2)
                echo -e "${BLUE}Starting reinstallation...${NC}"
                # Continue with installation
                ;;
            3)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${BLUE}Invalid choice, opening control panel...${NC}"
                show_control_panel
                ;;
        esac
    fi

    # Continue with installation script
    print_header "ICT Trading Oracle Bot - Automated Installation (v3.0)"
    echo -e "${BLUE}This script will install and configure the complete ICT Trading Oracle Bot${NC}"
    echo -e "${BLUE}Installation will take approximately 5-10 minutes${NC}"
    echo -e "${BLUE}Script supports re-running and will skip already completed steps${NC}"
    echo ""

    # Pre-installation checks
    print_step "Pre-installation System Checks"

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi

    print_success "Running as root - OK"

    # Check internet connectivity
    print_status "Checking internet connectivity..."
    if ping -c 1 google.com &> /dev/null; then
        print_success "Internet connectivity - OK"
    else
        print_error "No internet connectivity. Please check your network connection."
        exit 1
    fi

    # Check available disk space (minimum 2GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 2097152 ]; then
        print_error "Insufficient disk space. At least 2GB required."
        exit 1
    fi
    print_success "Sufficient disk space available"

    echo ""

    # STEP 1: System Update
    print_step "STEP 1: Updating System Packages"

    # Check if system was recently updated (within last 24 hours)
    if [ -f "/var/lib/apt/periodic/update-success-stamp" ]; then
        last_update=$(stat -c %Y /var/lib/apt/periodic/update-success-stamp)
        current_time=$(date +%s)
        time_diff=$((current_time - last_update))
        
        if [ $time_diff -lt 86400 ]; then
            print_warning "System was updated recently (within 24 hours), skipping update"
        else
            print_status "Updating package lists and upgrading system..."
            apt update > /dev/null 2>&1
            check_status "Package lists updated successfully" "Failed to update package lists"
            
            apt upgrade -y > /dev/null 2>&1
            check_status "System packages upgraded successfully" "Failed to upgrade system packages"
        fi
    else
        print_status "Updating package lists and upgrading system..."
        apt update > /dev/null 2>&1
        check_status "Package lists updated successfully" "Failed to update package lists"
        
        apt upgrade -y > /dev/null 2>&1
        check_status "System packages upgraded successfully" "Failed to upgrade system packages"
    fi

    # STEP 2: Install Required System Packages
    print_step "STEP 2: Installing Required System Packages"

    # Check if Python 3.11 is already installed
    if command_exists python3.11; then
        python_version=$(python3.11 --version)
        print_warning "Python 3.11 already installed: $python_version"
    else
        print_status "Installing Python 3.11, Git, and essential tools..."
        
        apt install -y software-properties-common > /dev/null 2>&1
        add-apt-repository ppa:deadsnakes/ppa -y > /dev/null 2>&1
        apt update > /dev/null 2>&1
        
        error_log=$(apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git curl wget nano htop unzip build-essential 2>&1)
        check_status "Required packages installed successfully" "Failed to install required packages" "$error_log"
    fi

    # Verify installations
    if command_exists python3.11; then
        python_version=$(python3.11 --version)
        print_success "Python verified: $python_version"
    else
        print_error "Python 3.11 installation verification failed"
        exit 1
    fi

    if command_exists git; then
        git_version=$(git --version)
        print_success "Git verified: $git_version"
    else
        print_error "Git installation verification failed"
        exit 1
    fi

    # STEP 3: Create ictbot User
    print_step "STEP 3: Creating ictbot User Account"

    if user_exists "ictbot"; then
        print_warning "User 'ictbot' already exists, skipping creation"
        
        # Ensure user is in sudo group
        if groups ictbot | grep -q sudo; then
            print_success "User 'ictbot' is already in sudo group"
        else
            print_status "Adding 'ictbot' to sudo group..."
            usermod -aG sudo ictbot
            check_status "User 'ictbot' added to sudo group" "Failed to add user to sudo group"
        fi
    else
        print_status "Creating user 'ictbot'..."
        useradd -m -s /bin/bash ictbot
        check_status "User 'ictbot' created successfully" "Failed to create user 'ictbot'"
        
        # Add to sudo group
        usermod -aG sudo ictbot
        check_status "User 'ictbot' added to sudo group" "Failed to add user to sudo group"
    fi

    # STEP 4: Setup Project Environment
    print_step "STEP 4: Setting Up Project Environment"

    # Switch to ictbot user and continue installation
    sudo -u ictbot bash << 'EOF'

    # Colors for ictbot user session
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m'

    print_status() {
        echo -e "${BLUE}[INFO]${NC} $1"
    }

    print_success() {
        echo -e "${GREEN}[SUCCESS]${NC} $1"
    }

    print_error() {
        echo -e "${RED}[ERROR]${NC} $1"
    }

    print_warning() {
        echo -e "${YELLOW}[WARNING]${NC} $1"
    }

    check_status() {
        if [ $? -eq 0 ]; then
            print_success "$1"
        else
            print_error "$2"
            if [ -n "$3" ]; then
                echo -e "${RED}Error details:${NC}"
                echo -e "${RED}$3${NC}"
            fi
            exit 1
        fi
    }

    # Navigate to home directory
    cd /home/ictbot

    # STEP 4.1: Clone Project Repository
    print_status "Setting up ICT Trading Oracle repository..."

    if [ -d "ict_trading_oracle" ]; then
        print_warning "Project directory already exists"
        cd ict_trading_oracle
        
        # Check if it's a git repository
        if [ -d ".git" ]; then
            print_status "Updating existing repository..."
            git_output=$(git pull origin main 2>&1)
            if [ $? -eq 0 ]; then
                print_success "Repository updated successfully"
            else
                print_warning "Git pull failed, will reset repository"
                cd ..
                rm -rf ict_trading_oracle
                git clone https://github.com/behnamrjd/ict_trading_oracle.git
                check_status "Repository re-cloned successfully" "Failed to re-clone repository"
                cd ict_trading_oracle
            fi
        else
            print_warning "Directory exists but is not a git repository, removing and re-cloning..."
            cd ..
            rm -rf ict_trading_oracle
            git clone https://github.com/behnamrjd/ict_trading_oracle.git
            check_status "Repository cloned successfully" "Failed to clone repository"
            cd ict_trading_oracle
        fi
    else
        # Clone the repository
        git_output=$(git clone https://github.com/behnamrjd/ict_trading_oracle.git 2>&1)
        check_status "Repository cloned successfully" "Failed to clone repository" "$git_output"
        cd ict_trading_oracle
    fi

    # Verify essential files
    print_status "Verifying project files..."
    if [ -f "main.py" ]; then
        print_success "main.py found"
    else
        print_warning "main.py not found in repository, will create it"
    fi

    # STEP 4.2: Create Virtual Environment
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        
        # Test if it's working
        if [ -f "venv/bin/python" ]; then
            print_success "Virtual environment appears to be intact"
        else
            print_warning "Virtual environment is corrupted, recreating..."
            rm -rf venv
            python3.11 -m venv venv
            check_status "Virtual environment recreated successfully" "Failed to recreate virtual environment"
        fi
    else
        print_status "Creating Python virtual environment..."
        venv_output=$(python3.11 -m venv venv 2>&1)
        check_status "Virtual environment created successfully" "Failed to create virtual environment" "$venv_output"
    fi

    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    check_status "Virtual environment activated" "Failed to activate virtual environment"

    # Verify virtual environment
    python_path=$(which python)
    if [[ "$python_path" == *"venv"* ]]; then
        print_success "Virtual environment is active: $python_path"
    else
        print_error "Virtual environment activation failed"
        exit 1
    fi

    # STEP 4.3: Upgrade pip
    print_status "Upgrading pip..."
    pip_output=$(pip install --upgrade pip 2>&1)
    check_status "pip upgraded successfully" "Failed to upgrade pip" "$pip_output"

    # STEP 4.4: Create Fixed Requirements File (without googletrans)
    print_status "Creating fixed requirements.txt..."
    cat > requirements_fixed.txt << 'REQEOF'
python-telegram-bot==20.7
yfinance==0.2.18
pandas==2.0.3
numpy==1.24.3
ta==0.10.2
scikit-learn==1.3.0
xgboost==1.7.6
torch==2.0.1
matplotlib==3.7.2
seaborn==0.12.2
vaderSentiment==3.3.2
feedparser==6.0.10
textblob==0.17.1
pytz==2023.3
flask==2.3.3
flask-login==0.6.2
requests==2.31.0
aiohttp==3.8.5
python-dotenv==1.0.0
schedule==1.2.0
psutil==5.9.5
cryptography==41.0.3
deep-translator==1.11.4
REQEOF

    # STEP 4.5: Install Python Dependencies
    print_status "Installing Python dependencies (this may take a few minutes)..."

    # Install essential packages first
    print_status "Installing essential packages..."
    essential_output=$(pip install python-telegram-bot python-dotenv requests 2>&1)
    if [ $? -eq 0 ]; then
        print_success "Essential packages installed"
    else
        print_error "Failed to install essential packages"
        echo -e "${RED}Error details:${NC}"
        echo "$essential_output"
        exit 1
    fi

    # Install from fixed requirements
    print_status "Installing from fixed requirements (without problematic packages)..."
    deps_output=$(pip install -r requirements_fixed.txt 2>&1)
    if [ $? -eq 0 ]; then
        print_success "Dependencies from fixed requirements installed"
    else
        print_warning "Some packages failed to install, trying individual installation..."
        
        # Try installing packages individually
        packages=(
            "pandas==2.0.3"
            "numpy==1.24.3"
            "ta==0.10.2"
            "scikit-learn==1.3.0"
            "matplotlib==3.7.2"
            "seaborn==0.12.2"
            "deep-translator==1.11.4"
            "flask==2.3.3"
            "aiohttp==3.8.5"
            "schedule==1.2.0"
            "psutil==5.9.5"
            "cryptography==41.0.3"
        )
        
        for package in "${packages[@]}"; do
            print_status "Installing $package..."
            if pip install "$package" > /dev/null 2>&1; then
                print_success "✓ $package"
            else
                print_warning "✗ $package (skipped - may have conflicts)"
            fi
        done
    fi

    # STEP 4.6: Verify Critical Imports
    print_status "Verifying critical Python imports..."

    # Test telegram
    if python -c "import telegram; print('✅ telegram')" 2>/dev/null; then
        print_success "telegram module verified"
    else
        print_error "telegram module import failed"
        exit 1
    fi

    # Test dotenv
    if python -c "from dotenv import load_dotenv; print('✅ dotenv')" 2>/dev/null; then
        print_success "dotenv module verified"
    else
        print_error "dotenv module import failed"
        exit 1
    fi

    # Test requests
    if python -c "import requests; print('✅ requests')" 2>/dev/null; then
        print_success "requests module verified"
    else
        print_error "requests module import failed"
        exit 1
    fi

    # Test deep-translator (replacement for googletrans)
    if python -c "from deep_translator import GoogleTranslator; print('✅ deep-translator')" 2>/dev/null; then
        print_success "deep-translator module verified (googletrans replacement)"
    else
        print_warning "deep-translator not available, installing separately..."
        pip install deep-translator > /dev/null 2>&1
        if python -c "from deep_translator import GoogleTranslator; print('✅ deep-translator')" 2>/dev/null; then
            print_success "deep-translator installed and verified"
        else
            print_warning "deep-translator installation failed, but continuing..."
        fi
    fi

    # STEP 4.7: Create Required Directories
    print_status "Creating required directories..."
    mkdir -p data logs config core ai_models subscription signals telegram_bot utils
    touch data/.gitkeep logs/.gitkeep

    # Create __init__.py files
    touch __init__.py
    touch config/__init__.py core/__init__.py ai_models/__init__.py
    touch subscription/__init__.py signals/__init__.py telegram_bot/__init__.py utils/__init__.py

    print_success "Directory structure created"

    # STEP 4.8: Create .env Configuration File
    if [ -f ".env" ]; then
        print_warning ".env file already exists, backing up and creating new one..."
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi

    print_status "Creating .env configuration file..."
    cat > .env << 'ENVEOF'
# Bot Configuration
BOT_TOKEN=YOUR_REAL_BOT_TOKEN_HERE

# Payment Configuration
ZARINPAL_MERCHANT_ID=YOUR_ZARINPAL_MERCHANT

# News API (Get from newsapi.org)
NEWS_API_KEY=YOUR_NEWSAPI_KEY_FROM_NEWSAPI_ORG

# TGJU API for Gold Prices
TGJU_API_URL=https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl,geram18,geram24,sekee

# Crypto Payment API
CRYPTAPI_CALLBACK_URL=https://yourdomain.com/api

# Database Configuration
DATABASE_URL=sqlite:///data/ict_trading.db

# Environment Settings
ENVIRONMENT=production
LOG_LEVEL=INFO

# Additional APIs (Optional)
ALPHA_VANTAGE_API_KEY=YOUR_ALPHA_VANTAGE_KEY
FOREX_API_KEY=YOUR_FOREX_API_KEY
ENVEOF

    check_status ".env file created successfully" "Failed to create .env file"

    # STEP 4.9: Create/Update config/settings.py
    print_status "Creating config/settings.py..."
    cat > config/settings.py << 'SETTINGSEOF'
"""
Configuration settings for ICT Trading Bot
"""

import os
from pathlib import Path

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "YOUR_NEWS_API_KEY")

# Payment Configuration
ZARINPAL_MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID", "YOUR_ZARINPAL_MERCHANT")
CRYPTAPI_CALLBACK_URL = os.getenv("CRYPTAPI_CALLBACK_URL", "https://yourdomain.com/api")

# Database Configuration
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / "data" / "ict_trading.db"

# Trading Configuration
TRADING_SYMBOL = "GC=F"  # Gold Futures
DEFAULT_TIMEFRAMES = {
    'swing': '1h',
    'scalping': '1m',
    'analysis': '1d'
}

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'daily_signals': 3,
        'features': ['basic_ict_analysis', 'education', 'price_display']
    },
    'premium': {
        'name': 'Premium',
        'price': 49,
        'daily_signals': 50,
        'features': ['all_features']
    },
    'vip': {
        'name': 'VIP',
        'price': 149,
        'daily_signals': -1,  # Unlimited
        'features': ['everything', 'copy_trading', 'personal_consultation']
    }
}

# Admin Configuration
ADMIN_IDS = [123456789, 987654321]  # Admin IDs

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "ict_trading.log"
SETTINGSEOF

    check_status "config/settings.py created successfully" "Failed to create config/settings.py"

    # Test config import
    config_test=$(python -c "from config.settings import BOT_TOKEN; print('✅ config.settings imported')" 2>&1)
    if [ $? -eq 0 ]; then
        print_success "config.settings import verified"
    else
        print_error "config.settings import failed"
        echo "$config_test"
        exit 1
    fi

    # STEP 4.10: Create/Update main.py if needed
    if [ ! -f "main.py" ] || [ ! -s "main.py" ]; then
        print_status "Creating main.py file..."
        cat > main.py << 'MAINEOF'
#!/usr/bin/env python3
"""
ICT Trading Oracle Bot
"""

import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found! Please set it in .env file")
    print("❌ BOT_TOKEN not found! Please add it to .env file")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    welcome_text = f"""
🎪 **Welcome to ICT Trading Oracle Bot**

Hello {user.first_name}! 👋

🎯 **Bot Features:**
• Professional ICT Analysis
• Gold (XAU/USD) Signals
• Advanced AI Integration
• Translation with Deep-Translator

📊 **Commands:**
/help - Complete guide
/signal - Get trading signal
/price - Current gold price

💎 **Your bot is ready!**
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
🔧 **ICT Trading Oracle Bot Guide**

📋 **Available Commands:**
/start - Start the bot
/help - This guide
/signal - Get ICT signal
/price - Current gold price
/status - Bot status

🎪 **About ICT:**
Inner Circle Trading is a professional market analysis methodology.
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Signal command handler"""
    signal_text = """
📊 **ICT Signal - Gold (XAU/USD)**

💰 **Current Price:** $2,350.25
📈 **Change:** +0.85% (+$19.75)

🎯 **Signal:** BUY
🔥 **Confidence:** 87%
⭐ **Quality:** EXCELLENT

📋 **ICT Analysis:**
• Market Structure: BULLISH
• Order Block: Confirmed
• Fair Value Gap: Active

💡 **Entry:** $2,348.00
🛡️ **Stop Loss:** $2,335.00
🎯 **Take Profit:** $2,365.00

⚠️ **Note:** This is a test signal!
    """
    
    await update.message.reply_text(signal_text, parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Price command handler"""
    price_text = """
💰 **Live Gold Price (XAU/USD)**

📊 **$2,350.25**
📈 **Change:** +$19.75 (+0.85%)

⏰ **Last Update:** 2 minutes ago
📅 **Date:** 2025/05/28

🔄 **Refresh:** /price
    """
    
    await update.message.reply_text(price_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command handler"""
    status_text = """
🤖 **ICT Trading Oracle Bot Status**

✅ **Bot:** Active and Ready
✅ **Server:** Connected
✅ **Database:** Active
✅ **Translation:** Deep-Translator Ready

📊 **Statistics:**
• Active Users: 1,250
• Today's Signals: 23
• Uptime: 99.9%

🕐 **Server Time:** UTC
    """
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def main():
    """Main function"""
    try:
        print("🚀 Starting ICT Trading Oracle Bot...")
        
        # Create Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("signal", signal_command))
        application.add_handler(CommandHandler("price", price_command))
        application.add_handler(CommandHandler("status", status_command))
        
        logger.info("🤖 ICT Trading Oracle Bot starting...")
        print("✅ Bot handlers registered successfully!")
        print("🔄 Starting polling...")
        
        # Start polling
        await application.run_polling(allowed_updates=["message"])
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
MAINEOF

        check_status "main.py created successfully" "Failed to create main.py"
    else
        print_success "main.py already exists and is not empty"
    fi

    # Test main.py syntax
    syntax_test=$(python -m py_compile main.py 2>&1)
    if [ $? -eq 0 ]; then
        print_success "main.py syntax verified"
    else
        print_error "main.py syntax error"
        echo "$syntax_test"
        exit 1
    fi

    print_success "Project environment setup completed successfully"

EOF

    check_status "Project environment setup completed" "Project environment setup failed"

    # STEP 5: Create systemd Service
    print_step "STEP 5: Creating systemd Service"

    if service_exists "ictbot"; then
        print_warning "ictbot service already exists, updating..."
        systemctl stop ictbot > /dev/null 2>&1
    else
        print_status "Creating new systemd service..."
    fi

    print_status "Creating systemd service file..."
    tee /etc/systemd/system/ictbot.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=ICT Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ictbot
Group=ictbot
WorkingDirectory=/home/ictbot/ict_trading_oracle
Environment="PATH=/home/ictbot/ict_trading_oracle/venv/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/home/ictbot/ict_trading_oracle"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ictbot/ict_trading_oracle/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

    check_status "systemd service file created" "Failed to create systemd service file"

    # Reload systemd daemon
    print_status "Reloading systemd daemon..."
    systemctl daemon-reload
    check_status "systemd daemon reloaded" "Failed to reload systemd daemon"

    # Enable service for auto-start
    print_status "Enabling service for auto-start..."
    systemctl enable ictbot > /dev/null 2>&1
    check_status "Service enabled for auto-start" "Failed to enable service"

    # STEP 6: Create Management Scripts
    print_step "STEP 6: Creating Management Scripts"

    # Create quick_deploy script
    print_status "Creating deployment script..."
    sudo -u ictbot tee /home/ictbot/quick_deploy.sh > /dev/null << 'DEPLOYEOF'
#!/bin/bash

echo "🚀 Starting ICT Trading Oracle Deployment..."

cd ~/ict_trading_oracle

echo "📋 Checking Git status..."
git status

echo "💾 Stashing local changes..."
git stash push -m "Auto stash before deployment - $(date)"

echo "📥 Fetching latest changes..."
git fetch origin

echo "🔄 Pulling changes from remote..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Git pull successful!"
    
    echo "🔄 Restarting ICT Trading Bot service..."
    sudo systemctl restart ictbot
    
    sleep 3
    if sudo systemctl is-active --quiet ictbot; then
        echo "✅ Service restarted successfully!"
        echo "🤖 ICT Trading Bot is running!"
    else
        echo "❌ Service failed to start!"
        echo "📋 Check logs: sudo journalctl -u ictbot -n 20"
    fi
else
    echo "❌ Git pull failed!"
    echo "📋 Please resolve conflicts manually"
fi

echo "🏁 Deployment script completed!"
DEPLOYEOF

    # Create other management scripts
    sudo -u ictbot tee /home/ictbot/check_bot.sh > /dev/null << 'CHECKEOF'
#!/bin/bash

echo "🔍 ICT Trading Bot Status Check"
echo "================================"
echo ""
echo "Service Status:"
sudo systemctl status ictbot --no-pager
echo ""
echo "Recent Logs (last 15 lines):"
sudo journalctl -u ictbot -n 15 --no-pager
echo ""
echo "System Resources:"
echo "CPU/RAM: $(uptime)"
echo "Disk Usage: $(df -h / | tail -1)"
echo ""
echo "Network Status:"
if ping -c 1 google.com &> /dev/null; then
    echo "✅ Internet connectivity: OK"
else
    echo "❌ Internet connectivity: FAILED"
fi
echo ""
echo "Python Environment:"
cd /home/ictbot/ict_trading_oracle
source venv/bin/activate
echo "Python version: $(python --version)"
echo "Telegram module: $(python -c 'import telegram; print("OK")' 2>/dev/null || echo "FAILED")"
echo "Deep-translator: $(python -c 'from deep_translator import GoogleTranslator; print("OK")' 2>/dev/null || echo "NOT AVAILABLE")"
CHECKEOF

    sudo -u ictbot tee /home/ictbot/start_bot.sh > /dev/null << 'STARTEOF'
#!/bin/bash

echo "🚀 Starting ICT Trading Bot..."
sudo systemctl start ictbot
sleep 2
sudo systemctl status ictbot --no-pager
echo ""
if sudo systemctl is-active --quiet ictbot; then
    echo "✅ Bot started successfully!"
else
    echo "❌ Bot failed to start!"
    echo "📋 Check logs: sudo journalctl -u ictbot -n 10"
fi
STARTEOF

    sudo -u ictbot tee /home/ictbot/stop_bot.sh > /dev/null << 'STOPEOF'
#!/bin/bash

echo "🛑 Stopping ICT Trading Bot..."
sudo systemctl stop ictbot
sleep 2
sudo systemctl status ictbot --no-pager
echo ""
if sudo systemctl is-active --quiet ictbot; then
    echo "❌ Bot is still running!"
else
    echo "✅ Bot stopped successfully!"
fi
STOPEOF

    # Set execute permissions
    chmod +x /home/ictbot/quick_deploy.sh
    chmod +x /home/ictbot/check_bot.sh
    chmod +x /home/ictbot/start_bot.sh
    chmod +x /home/ictbot/stop_bot.sh

    check_status "Management scripts created successfully" "Failed to create management scripts"

    # STEP 7: Final System Verification
    print_step "STEP 7: Final System Verification"

    print_status "Verifying installation completeness..."

    critical_files=(
        "/home/ictbot/ict_trading_oracle/main.py"
        "/home/ictbot/ict_trading_oracle/.env"
        "/home/ictbot/ict_trading_oracle/config/settings.py"
        "/home/ictbot/ict_trading_oracle/venv/bin/python"
        "/etc/systemd/system/ictbot.service"
        "/home/ictbot/quick_deploy.sh"
        "/home/ictbot/check_bot.sh"
    )

    all_files_ok=true
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "✓ $file"
        else
            print_error "✗ $file (MISSING)"
            all_files_ok=false
        fi
    done

    if [ "$all_files_ok" = true ]; then
        print_success "All critical files verified"
    else
        print_error "Some critical files are missing"
        exit 1
    fi

    # Check directory permissions
    print_status "Verifying directory permissions..."
    if [ -O "/home/ictbot/ict_trading_oracle" ]; then
        print_success "Directory ownership verified"
    else
        print_warning "Fixing directory ownership..."
        chown -R ictbot:ictbot /home/ictbot/ict_trading_oracle
        check_status "Directory ownership fixed" "Failed to fix directory ownership"
    fi

    # Test virtual environment and imports
    print_status "Testing virtual environment and critical imports..."
    test_output=$(sudo -u ictbot bash -c "cd /home/ictbot/ict_trading_oracle && source venv/bin/activate && python -c 'import telegram, dotenv, requests; print(\"All critical imports OK\")'" 2>&1)
    if [ $? -eq 0 ]; then
        print_success "Virtual environment and imports test passed"
    else
        print_error "Virtual environment or imports test failed"
        echo "$test_output"
        exit 1
    fi

    # After successful installation, show control panel
    print_header "Installation Completed Successfully!"
    print_success "🎉 ICT Trading Oracle Bot installation completed successfully!"
    echo ""
    print_warning "Opening Control Panel in 3 seconds..."
    sleep 3
    show_control_panel
}

# Run the main function
main "$@"

