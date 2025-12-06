#!/bin/bash
# Comprehensive startup script for Mommy AI
# Starts Ollama, verifies dependencies, and launches the server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_PATH="$PROJECT_ROOT/.venv"

# Color output for user feedback
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_shortcuts_if_missing() {
    log_info "Checking for desktop shortcuts..."
    # Find desktop directory reliably
    DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")

    if [ ! -d "$DESKTOP_DIR" ]; then
        log_warn "Could not find Desktop directory. Skipping shortcut check."
        return
    fi

    LAUNCHER_PATH="$DESKTOP_DIR/Mommy-AI.desktop"
    CHAT_SHORTCUT_PATH="$DESKTOP_DIR/Mommy-AI-Chat.html"

    # If both shortcuts already exist, do nothing.
    if [ -f "$LAUNCHER_PATH" ] && [ -L "$CHAT_SHORTCUT_PATH" ]; then
        return
    fi

    log_warn "One or more desktop shortcuts are missing. Creating them now..."

    # Create symbolic link to the chat UI
    ln -sf "$PROJECT_ROOT/mommy_ai_chat.html" "$CHAT_SHORTCUT_PATH"

    # Dynamically create the .desktop file
    cat > "$LAUNCHER_PATH" << EOF
[Desktop Entry]
Version=1.0
Name=Mommy AI
Comment=Start the Mommy AI Server
Exec=gnome-terminal -- bash -c "'$PROJECT_ROOT/start_mommy_ai.sh'; exec bash"
Icon=system-run
Terminal=false
Type=Application
Categories=Utility;
EOF
    chmod +x "$LAUNCHER_PATH"
    log_success "Desktop shortcuts created. You may need to right-click 'Mommy AI' and 'Allow Launching'."
}

# Step 1: Check and start Ollama
log_info "Step 1: Checking Ollama service..."
if systemctl --user is-active --quiet ollama.service; then
    log_success "Ollama service is running."
elif systemctl --user list-unit-files | grep -q ollama.service; then
    log_info "Ollama service found but not running. Starting it now..."
    systemctl --user start ollama.service
    sleep 2 # Give it a moment to start
    if systemctl --user is-active --quiet ollama.service; then
        log_success "Ollama service started successfully."
    else
        log_error "Failed to start Ollama service. Please check with 'systemctl --user status ollama.service'."
        exit 1
    fi
else
    log_warn "Ollama systemd service not found. Attempting manual start as a fallback."
    if command -v ollama &> /dev/null; then
        if curl -s http://127.0.0.1:11434/api/version &> /dev/null; then
            log_success "Ollama daemon is already running."
            sleep 2 # Add a small delay to ensure it's fully ready
        else
            log_info "Starting Ollama daemon manually..."
            ollama serve &> /tmp/ollama.log &
            # Wait for Ollama to be ready (up to 30 seconds)
            for i in {1..30}; do
                if curl -s http://127.0.0.1:11434/api/version &> /dev/null; then
                    log_success "Ollama daemon started successfully."
                    break
                fi
                sleep 1
            done
        fi
    else
        log_error "Ollama command not found. Please install Ollama from https://ollama.com/download"
        exit 1
    fi
fi

# Step 1a: Check for required Ollama model from .env
OLLAMA_MODEL="dolphin-llama3:70b" # Default to the new model
if [ -f "$PROJECT_ROOT/.env" ]; then
    # Safely read the OLLAMA_MODEL from the .env file
    MODEL_FROM_ENV=$(grep -E '^OLLAMA_MODEL=' "$PROJECT_ROOT/.env" | cut -d '=' -f2-)
    if [ -n "$MODEL_FROM_ENV" ]; then
        OLLAMA_MODEL=$MODEL_FROM_ENV
    fi
fi
log_info "Step 1a: Checking for required Ollama model ('$OLLAMA_MODEL')..."
if ollama list | grep -q "$OLLAMA_MODEL"; then
    log_success "Ollama model '$OLLAMA_MODEL' is available."
else
    log_warn "Ollama model '$OLLAMA_MODEL' not found."
    log_info "Attempting to download '$OLLAMA_MODEL'. This may take a few minutes..."
    if ollama pull "$OLLAMA_MODEL"; then
        log_success "Successfully downloaded '$OLLAMA_MODEL' model."
    else
        log_error "Failed to download '$OLLAMA_MODEL' model. Please check your internet connection and run 'ollama pull $OLLAMA_MODEL' manually."
        exit 1
    fi
fi

# Step 2: Check virtual environment
log_info "Step 2: Checking Python virtual environment..."
if [ ! -d "$VENV_PATH" ]; then
    log_warn "Virtual environment not found at $VENV_PATH"
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    log_success "Virtual environment created"
fi

# Step 3: Activate virtualenv and install/update dependencies
log_info "Step 3: Installing Python dependencies..."
source "$VENV_PATH/bin/activate"

if [ -f "$PROJECT_ROOT/services/requirements.txt" ]; then
    pip install -q -r "$PROJECT_ROOT/services/requirements.txt"
    log_success "Dependencies installed/updated"
else
    log_warn "requirements.txt not found; skipping pip install"
fi

# Step 4: Verify .env file
log_info "Step 4: Checking environment configuration..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_warn ".env file not found"
    log_info "Creating minimal .env file (you must add GEMINI_API_KEY)"
    cat > "$PROJECT_ROOT/.env" << 'EOF'
# Gemini API Configuration
GEMINI_API_KEY=your_api_key_here

# Ollama Configuration (optional)
OLLAMA_ENABLED=true
OLLAMA_MODEL=dolphin-llama3:70b
OLLAMA_HOST=127.0.0.1:11434

# NSFW Model Gating (set to true only if desired)
ALLOW_NSFW=false
EOF
    log_warn "Please update .env with your GEMINI_API_KEY"
fi

# Verify GEMINI_API_KEY is set (but not necessarily valid here, as it's checked at runtime)
if grep -q "GEMINI_API_KEY=your_api_key_here" "$PROJECT_ROOT/.env"; then
    log_error "GEMINI_API_KEY is not configured in .env file"
    log_info "Please update .env with your actual Gemini API key before continuing"
    exit 1
fi

log_success "Environment configuration verified"

# Step 4a: Create desktop shortcuts if they don't exist
create_shortcuts_if_missing

# Step 5: Start the Mommy AI Flask server
log_info "Step 5: Starting Mommy AI server..."
log_info "Server will be available at http://localhost:5000"
log_info "Press Ctrl+C to stop the server"

cd "$PROJECT_ROOT"

if [[ "$1" == "--debug" ]]; then
    log_warn "Running in DEBUG mode."
    export MOMMY_AI_DEBUG=true
fi
python3 mommy_ai.py "$@"

# Keep script running if server exits
log_warn "Mommy AI server has stopped"
