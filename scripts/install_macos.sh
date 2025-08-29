#!/bin/bash
"""
Nova Daemon Installation Script for macOS
Sets up the complete Home Starter Mode system
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NOVA_HOME="$HOME/nova"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.nova.daemon.plist"
DAEMON_SCRIPT="daemon/novad.py"
CLI_SCRIPT="cli/nova.py"

echo -e "${BLUE}🚀 Nova Daemon Installation Script${NC}"
echo "=================================================="
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is for macOS only"
    exit 1
fi

print_status "Detected macOS $(sw_vers -productVersion)"

# Check if Nova directory exists
if [[ ! -d "$NOVA_HOME" ]]; then
    print_error "Nova directory not found at $NOVA_HOME"
    print_error "Please run this script from the Nova project directory"
    exit 1
fi

print_status "Nova directory found at $NOVA_HOME"

# Check if we're in the right directory
if [[ ! -f "$NOVA_HOME/$DAEMON_SCRIPT" ]]; then
    print_error "Daemon script not found at $DAEMON_SCRIPT"
    print_error "Please run this script from the Nova project directory"
    exit 1
fi

print_status "Daemon script found"

# Check if we're in the right directory
if [[ ! -f "$NOVA_HOME/$CLI_SCRIPT" ]]; then
    print_error "CLI script not found at $CLI_SCRIPT"
    print_error "Please run this script from the Nova project directory"
    exit 1
fi

print_status "CLI script found"

# Check Python environment
echo ""
echo -e "${BLUE}🐍 Checking Python Environment${NC}"
echo "----------------------------------------"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    print_error "Please install Python 3.8+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
print_status "Python found: $PYTHON_VERSION"

# Check virtual environment
if [[ -d "$NOVA_HOME/.venv" ]]; then
    print_status "Virtual environment found"
    
    # Activate virtual environment
    source "$NOVA_HOME/.venv/bin/activate"
    print_status "Virtual environment activated"
else
    print_warning "Virtual environment not found"
    print_warning "Please create and activate a virtual environment first"
fi

# Check dependencies
echo ""
echo -e "${BLUE}📦 Checking Dependencies${NC}"
echo "----------------------------------------"

# Check Spotify integration
if python3 -c "import spotipy" 2>/dev/null; then
    print_status "Spotify integration available"
else
    print_warning "Spotify integration not available"
    print_warning "Run: pip install spotipy"
fi

# Check other dependencies
REQUIRED_DEPS=("google-auth" "google-auth-oauthlib" "google-auth-httplib2" "google-api-python-client")
for dep in "${REQUIRED_DEPS[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        print_status "$dep available"
    else
        print_warning "$dep not available"
    fi
done

# Create LaunchAgents directory if it doesn't exist
if [[ ! -d "$LAUNCH_AGENTS_DIR" ]]; then
    mkdir -p "$LAUNCH_AGENTS_DIR"
    print_status "Created LaunchAgents directory"
fi

# Copy plist file
echo ""
echo -e "${BLUE}🔧 Installing Launch Agent${NC}"
echo "----------------------------------------"

PLIST_SOURCE="$NOVA_HOME/config/$PLIST_NAME"
PLIST_DEST="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

if [[ -f "$PLIST_SOURCE" ]]; then
    cp "$PLIST_SOURCE" "$PLIST_DEST"
    print_status "Launch agent plist copied to $PLIST_DEST"
else
    print_error "Launch agent plist not found at $PLIST_SOURCE"
    exit 1
fi

# Update plist with correct paths
echo ""
echo -e "${BLUE}🔧 Updating Launch Agent Configuration${NC}"
echo "----------------------------------------"

# Get absolute paths
NOVA_HOME_ABS=$(cd "$NOVA_HOME" && pwd)
PYTHON_PATH=$(which python3)

# Update plist with correct paths
sed -i.bak "s|/Users/mouhamed23/nova|$NOVA_HOME_ABS|g" "$PLIST_DEST"
sed -i.bak "s|/usr/bin/python3|$PYTHON_PATH|g" "$PLIST_DEST"

print_status "Launch agent paths updated"
print_status "Nova home: $NOVA_HOME_ABS"
print_status "Python path: $PYTHON_PATH"

# Make scripts executable
echo ""
echo -e "${BLUE}🔧 Setting Permissions${NC}"
echo "----------------------------------------"

chmod +x "$NOVA_HOME/$DAEMON_SCRIPT"
chmod +x "$NOVA_HOME/$CLI_SCRIPT"
print_status "Scripts made executable"

# Test the daemon
echo ""
echo -e "${BLUE}🧪 Testing Daemon${NC}"
echo "----------------------------------------"

print_status "Starting daemon test..."

# Start daemon in background
cd "$NOVA_HOME"
python3 "$DAEMON_SCRIPT" &
DAEMON_PID=$!

# Wait for daemon to start
sleep 5

# Check if daemon is running
if kill -0 $DAEMON_PID 2>/dev/null; then
    print_status "Daemon started successfully (PID: $DAEMON_PID)"
    
    # Test IPC communication
    if [[ -S "/tmp/nova.sock" ]]; then
        print_status "IPC socket created"
        
        # Test status command
        if python3 "$CLI_SCRIPT" status >/dev/null 2>&1; then
            print_status "IPC communication working"
        else
            print_warning "IPC communication test failed"
        fi
    else
        print_warning "IPC socket not created"
    fi
    
    # Stop test daemon
    kill $DAEMON_PID 2>/dev/null || true
    print_status "Test daemon stopped"
else
    print_error "Daemon failed to start"
    exit 1
fi

# Install CLI to PATH
echo ""
echo -e "${BLUE}🔧 Installing CLI${NC}"
echo "----------------------------------------"

# Create symlink in /usr/local/bin if it exists
if [[ -d "/usr/local/bin" ]]; then
    CLI_LINK="/usr/local/bin/nova"
    if [[ -L "$CLI_LINK" ]]; then
        rm "$CLI_LINK"
    fi
    ln -s "$NOVA_HOME/$CLI_SCRIPT" "$CLI_LINK"
    print_status "CLI installed to /usr/local/bin/nova"
else
    print_warning "Could not install CLI to /usr/local/bin"
    print_warning "You can run it directly: python3 $NOVA_HOME/$CLI_SCRIPT"
fi

# Final setup
echo ""
echo -e "${BLUE}🎯 Final Setup${NC}"
echo "----------------------------------------"

print_status "Installation completed successfully!"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Enable auto-start: nova enable"
echo "2. Start daemon: nova start"
echo "3. Check status: nova status"
echo "4. View logs: nova logs"
echo "5. Run diagnostics: nova doctor"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo "nova status     - Check daemon status"
echo "nova health     - Check daemon health"
echo "nova start      - Start daemon manually"
echo "nova stop       - Stop daemon"
echo "nova restart    - Restart daemon"
echo "nova enable     - Enable auto-start at login"
echo "nova disable    - Disable auto-start at login"
echo "nova logs       - View daemon logs"
echo "nova doctor     - Run diagnostic checks"
echo ""

# Check if user wants to enable auto-start
read -p "Would you like to enable Nova to start automatically at login? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}🔧 Enabling Auto-Start${NC}"
    echo "----------------------------------------"
    
    if python3 "$CLI_SCRIPT" enable; then
        print_status "Auto-start enabled successfully!"
        print_status "Nova will now start automatically when you log in"
    else
        print_error "Failed to enable auto-start"
        print_warning "You can enable it manually later with: nova enable"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Nova Daemon Installation Complete!${NC}"
echo "=================================================="
echo ""
echo "Your futuristic smart home AI is ready to serve!"
echo "Welcome to the future, Sir! 🚀"
