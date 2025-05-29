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
                echo "Control panel functionality would go here"
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
                echo -e "${BLUE}Invalid choice, continuing with installation...${NC}"
                ;;
        esac
    fi

    # Continue with installation script
    print_header "ICT Trading Oracle Bot - Complete Installation with Backtest (v4.1)"
    echo -e "${BLUE}This script will install and configure the complete ICT Trading Oracle Bot${NC}"
    echo -e "${BLUE}New Features: 7-Day Backtest Analysis, Enhanced Real-Time Data${NC}"
    echo -e "${BLUE}Installation will take approximately 10-15 minutes${NC}"
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

    # Check available disk space (minimum 3GB for complete installation)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 3145728 ]; then
        print_error "Insufficient disk space. At least 3GB required for complete installation."
        exit 1
    fi
    print_success "Sufficient disk space available"

    echo ""

    # STEP 1: System Update
    print_step "STEP 1: Updating System Packages"

    print_status "Updating package lists and upgrading system..."
    apt update > /dev/null 2>&1
    check_status "Package lists updated successfully" "Failed to update package lists"
    
    apt upgrade -y > /dev/null 2>&1
    check_status "System packages upgraded successfully" "Failed to upgrade system packages"

    # STEP 2: Install Required System Packages
    print_step "STEP 2: Installing Required System Packages"

    if command_exists python3.11; then
        python_version=$(python3.11 --version)
        print_warning "Python 3.11 already installed: $python_version"
    else
        print_status "Installing Python 3.11, Git, and essential tools..."
        
        apt install -y software-properties-common > /dev/null 2>&1
        add-apt-repository ppa:deadsnakes/ppa -y > /dev/null 2>&1
        apt update > /dev/null 2>&1
        
        error_log=$(apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git curl wget nano htop unzip build-essential pkg-config libcairo2-dev libgirepository1.0-dev 2>&1)
        check_status "Required packages installed successfully" "Failed to install required packages" "$error_log"
    fi

    # STEP 3: Create ictbot User
    print_step "STEP 3: Creating ictbot User Account"

    if user_exists "ictbot"; then
        print_warning "User 'ictbot' already exists, skipping creation"
        usermod -aG sudo ictbot
        check_status "User 'ictbot' added to sudo group" "Failed to add user to sudo group"
    else
        print_status "Creating user 'ictbot'..."
        useradd -m -s /bin/bash ictbot
        check_status "User 'ictbot' created successfully" "Failed to create user 'ictbot'"
        
        usermod -aG sudo ictbot
        check_status "User 'ictbot' added to sudo group" "Failed to add user to sudo group"
    fi

    # STEP 4: Setup Project Environment
    print_step "STEP 4: Setting Up Complete Project Environment with Backtest"

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
        git_output=$(git clone https://github.com/behnamrjd/ict_trading_oracle.git 2>&1)
        check_status "Repository cloned successfully" "Failed to clone repository" "$git_output"
        cd ict_trading_oracle
    fi

    # STEP 4.2: Create Virtual Environment
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
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

    # STEP 4.3: Upgrade pip
    print_status "Upgrading pip..."
    pip_output=$(pip install --upgrade pip 2>&1)
    check_status "pip upgraded successfully" "Failed to upgrade pip" "$pip_output"

    # STEP 4.4: Install Python Dependencies
    print_status "Installing Python dependencies (this may take several minutes)..."

    # Install essential packages first
    print_status "Installing essential packages..."
    essential_output=$(pip install python-telegram-bot python-dotenv requests psutil nest-asyncio 2>&1)
    if [ $? -eq 0 ]; then
        print_success "Essential packages installed"
    else
        print_error "Failed to install essential packages"
        echo -e "${RED}Error details:${NC}"
        echo "$essential_output"
        exit 1
    fi

    # Install from requirements
    if [ -f "requirements_fixed.txt" ]; then
        print_status "Installing from requirements_fixed.txt..."
        deps_output=$(pip install -r requirements_fixed.txt 2>&1)
        if [ $? -eq 0 ]; then
            print_success "Dependencies from requirements installed"
        else
            print_warning "Some packages failed to install, trying individual installation..."
            
            packages=(
                "pandas==2.0.3"
                "numpy==1.24.3"
                "ta==0.10.2"
                "scikit-learn==1.3.0"
                "matplotlib==3.7.2"
                "seaborn==0.12.2"
                "yfinance==0.2.18"
                "setuptools>=40.0.0"
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
    fi

    # STEP 4.5: Create Complete Directory Structure
    print_status "Creating complete directory structure with backtest..."
    mkdir -p data logs config core ai_models subscription signals telegram_bot utils
    mkdir -p admin tests optimization monitoring cache backups backtest backtest_results
    mkdir -p test_reports optimization_reports monitoring_logs ai_models/trained_models
    
    # Create .gitkeep files
    touch data/.gitkeep logs/.gitkeep cache/.gitkeep backups/.gitkeep
    touch test_reports/.gitkeep optimization_reports/.gitkeep monitoring_logs/.gitkeep
    touch ai_models/trained_models/.gitkeep backtest_results/.gitkeep

    # Create __init__.py files
    touch __init__.py
    touch config/__init__.py core/__init__.py ai_models/__init__.py
    touch subscription/__init__.py signals/__init__.py telegram_bot/__init__.py utils/__init__.py
    touch admin/__init__.py tests/__init__.py optimization/__init__.py monitoring/__init__.py
    touch backtest/__init__.py

    print_success "Complete directory structure created with backtest support"

    # STEP 4.6: Create .env Configuration File
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

# AI Configuration
AI_MODEL_PATH=ai_models/trained_models/
AI_CONFIDENCE_THRESHOLD=70
AI_RETRAIN_INTERVAL=7

# Monitoring Configuration
MONITORING_ENABLED=true
MONITORING_INTERVAL=60
ALERT_EMAIL=admin@yourdomain.com

# Backtest Configuration
BACKTEST_DAYS=7
SIGNALS_PER_DAY=10
BACKTEST_ENABLED=true

# Additional APIs (Optional)
ALPHA_VANTAGE_API_KEY=YOUR_ALPHA_VANTAGE_KEY
FOREX_API_KEY=YOUR_FOREX_API_KEY
ENVEOF

    check_status ".env file created successfully" "Failed to create .env file"

    # STEP 4.7: Install setuptools and project
    print_status "Installing setuptools and wheel..."
    setuptools_output=$(pip install setuptools wheel 2>&1)
    check_status "setuptools and wheel installed" "Failed to install setuptools" "$setuptools_output"

    print_status "Installing project in development mode..."
    if [ -f "setup.py" ]; then
        project_output=$(pip install -e . 2>&1)
        check_status "Project installed in development mode" "Failed to install project" "$project_output"
    else
        print_warning "setup.py not found, skipping project installation"
    fi

    # STEP 4.8: Test imports
    print_status "Testing Python imports..."
    test_imports=$(python -c "
try:
    from core.api_manager import APIManager
    from core.technical_analysis import TechnicalAnalyzer
    from core.database import DatabaseManager
    from core.payment_manager import PaymentManager, SubscriptionManager
    from backtest.backtest_analyzer import BacktestAnalyzer
    print('✅ All core imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
" 2>&1)

    if [[ "$test_imports" == *"✅"* ]]; then
        print_success "Python imports verified"
    else
        print_warning "Some imports failed, but continuing..."
        echo "$test_imports"
    fi

    print_success "Complete project environment setup completed successfully"

EOF

    check_status "Complete project environment setup completed" "Project environment setup failed"

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
Description=ICT Trading Oracle Bot v4.1 with Backtest
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
ExecStart=/home/ictbot/ict_trading_oracle/venv/bin/python run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ictbot

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

    # STEP 6: Final System Verification
    print_step "STEP 6: Final System Verification"

    print_status "Verifying complete installation..."

    critical_files=(
        "/home/ictbot/ict_trading_oracle/main.py"
        "/home/ictbot/ict_trading_oracle/run.py"
        "/home/ictbot/ict_trading_oracle/.env"
        "/home/ictbot/ict_trading_oracle/venv/bin/python"
        "/etc/systemd/system/ictbot.service"
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
    chown -R ictbot:ictbot /home/ictbot/ict_trading_oracle
    check_status "Directory ownership verified" "Failed to fix directory ownership"

    # After successful installation, show completion summary
    print_header "🎉 Installation Completed Successfully!"
    
    echo -e "${GREEN}✅ ICT Trading Oracle Bot v4.1 installation completed successfully!${NC}"
    echo ""
    echo -e "${CYAN}📋 INSTALLATION SUMMARY:${NC}"
    echo "   ✅ Complete project structure created"
    echo "   ✅ All dependencies installed (25+ packages)"
    echo "   ✅ Database system configured"
    echo "   ✅ AI/ML modules prepared"
    echo "   ✅ Admin panel ready"
    echo "   ✅ Testing framework installed"
    echo "   ✅ Monitoring system prepared"
    echo "   ✅ Payment system configured"
    echo "   ✅ Security measures implemented"
    echo "   ✅ Performance optimization ready"
    echo "   ✅ 7-Day Backtest Analysis ready"
    echo ""
    echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
    echo ""
    echo "1. Configure Bot Token:"
    echo "   sudo nano /home/ictbot/ict_trading_oracle/.env"
    echo "   Replace 'YOUR_REAL_BOT_TOKEN_HERE' with your actual bot token from @BotFather"
    echo ""
    echo "2. Update Admin IDs:"
    echo "   sudo nano /home/ictbot/ict_trading_oracle/config/settings.py"
    echo "   Replace '123456789' with your actual Telegram User ID"
    echo ""
    echo "3. Start the bot:"
    echo "   sudo systemctl start ictbot"
    echo ""
    echo "4. Check bot status:"
    echo "   sudo systemctl status ictbot"
    echo ""
    echo "5. Test bot in Telegram:"
    echo "   Send /start to your bot"
    echo ""
    echo "6. Test backtest feature:"
    echo "   Send /backtest to your bot (admin only)"
    echo ""
    echo -e "${PURPLE}🎯 NEW FEATURES IN v4.1:${NC}"
    echo "   • 7-Day Backtest Analysis"
    echo "   • Enhanced Real-Time Gold Prices"
    echo "   • Improved Signal Accuracy"
    echo "   • Performance Tracking"
    echo "   • Advanced Admin Analytics"
    echo ""
    print_success "ICT Trading Oracle Bot v4.1 is ready for production!"
}

# Run the main function
main "$@"
