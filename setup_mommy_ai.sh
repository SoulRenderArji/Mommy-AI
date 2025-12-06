#!/bin/bash
# Mommy AI Setup Assistant
# Helps with first-time configuration

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎀 Welcome to Mommy AI Setup Assistant${NC}"
echo ""

# Step 1: Create virtual environment if needed
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Step 2: Install dependencies
echo ""
echo -e "${YELLOW}Installing Python dependencies...${NC}"
source "$VENV_PATH/bin/activate"
pip install -q -r "$PROJECT_ROOT/services/requirements.txt"
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Check Ollama
echo ""
echo -e "${YELLOW}Checking Ollama installation...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
else
    echo -e "${RED}⚠ Ollama not found. Install from https://ollama.com/download${NC}"
fi

# Step 4: Setup .env
echo ""
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}Setting up .env file...${NC}"
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
    echo -e "${YELLOW}✓ Created .env file${NC}"
    echo -e "${RED}⚠ Please edit .env and add your GEMINI_API_KEY${NC}"
    echo -e "  Edit: $PROJECT_ROOT/.env"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
    if grep -q "GEMINI_API_KEY=your_api_key_here" "$PROJECT_ROOT/.env"; then
        echo -e "${RED}⚠ GEMINI_API_KEY not configured in .env${NC}"
    else
        echo -e "${GREEN}✓ GEMINI_API_KEY is configured${NC}"
    fi
fi

# Step 5: Create sample user profiles
echo ""
echo -e "${YELLOW}Setting up user profiles...${NC}"
cat > "$PROJECT_ROOT/services/user_profiles.json" << 'EOF'
{
  "hailey": {
    "display_name": "Hailey",
    "age": null,
    "pronouns": "she/her"
  },
  "brandon": {
    "display_name": "Brandon",
    "age": null,
    "pronouns": "he/him"
  }
}
EOF
echo -e "${GREEN}✓ User profiles created${NC}"

# Step 6: Desktop shortcuts
echo ""
echo -e "${YELLOW}Setting up desktop shortcuts...${NC}"
DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")

if [ ! -d "$DESKTOP_DIR" ]; then
    echo -e "${RED}⚠ Could not find Desktop directory. Skipping shortcut creation.${NC}"
else
    # Create a symbolic link to the chat UI for easy access
    ln -sf "$PROJECT_ROOT/mommy_ai_chat.html" "$DESKTOP_DIR/Mommy-AI-Chat.html"
    echo -e "${GREEN}✓ Chat UI shortcut created on Desktop${NC}"

    # Dynamically create the .desktop file to ensure paths are correct
    LAUNCHER_PATH="$DESKTOP_DIR/Mommy-AI.desktop"
    echo -e "${YELLOW}Creating application launcher...${NC}"
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

    # Make the launcher executable
    chmod +x "$LAUNCHER_PATH"
    echo -e "${GREEN}✓ Startup launcher created on Desktop${NC}"
    echo -e "${BLUE}Note: You may need to right-click the 'Mommy AI' icon and 'Allow Launching' the first time.${NC}"
fi


# Step 7: Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Edit your .env file to add GEMINI_API_KEY:"
echo -e "   ${YELLOW}$PROJECT_ROOT/.env${NC}"
echo ""
echo "2. (Optional) Install Ollama for local NSFW fallback:"
echo -e "   ${YELLOW}curl -fsSL https://ollama.com/install.sh | sh${NC}"
echo ""
echo "3. Start Mommy AI by double-clicking the desktop icon:"
echo -e "   ${YELLOW}Mommy-AI.desktop${NC}"
echo ""
echo "4. Or start manually:"
echo -e "   ${YELLOW}$PROJECT_ROOT/start_mommy_ai.sh${NC}"
echo ""
echo "5. Open web browser to http://localhost:5000"
echo ""
echo -e "${GREEN}For more help, see: STARTUP_GUIDE.md${NC}"
echo ""
