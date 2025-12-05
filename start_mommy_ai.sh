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

# Step 1: Check and start Ollama
log_info "Step 1: Checking Ollama service..."
if command -v ollama &> /dev/null; then
    log_success "Ollama is installed"
    
    # Check if Ollama daemon is running
    if curl -s http://127.0.0.1:11434/api/version &> /dev/null; then
        log_success "Ollama daemon is already running on 127.0.0.1:11434"
    else
        log_info "Starting Ollama daemon..."
        ollama serve &> /tmp/ollama.log &
        sleep 3
        
        # Wait for Ollama to be ready (max 30 seconds)
        for i in {1..30}; do
            if curl -s http://127.0.0.1:11434/api/version &> /dev/null; then
                log_success "Ollama daemon started successfully"
                break
            fi
            if [ $i -eq 30 ]; then
                log_warn "Ollama took a long time to start; continuing anyway"
            fi
            sleep 1
        done
    fi
else
    log_warn "Ollama is not installed. Install from https://ollama.com/download"
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
OLLAMA_MODEL=dolphin-nsfw
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

# Step 5: Start the Mommy AI Flask server
log_info "Step 5: Starting Mommy AI server..."
log_info "Server will be available at http://localhost:5000"
log_info "Press Ctrl+C to stop the server"

cd "$PROJECT_ROOT"
python3 mommy_ai.py

# Keep script running if server exits
log_warn "Mommy AI server has stopped"
