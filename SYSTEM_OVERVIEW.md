# 🎀 Mommy AI - Complete System Overview

## What Was Built Today

I've created a **complete desktop-to-network AI system** that allows you and Brandon to chat with Mommy AI from any device on your network. Here's what's new:

---

## 📦 New Components Created

### 1. **Desktop Launcher** (`Mommy-AI.desktop`)
   - **Location**: Desktop + `/home/hailey/Documents/GitHub/Mommy-AI/`
   - **Purpose**: One-click startup of entire system
   - **Action**: Double-click to start
   - **Result**: Opens terminal showing startup progress

### 2. **Startup Script** (`start_mommy_ai.sh`)
   - **Handles**:
     1. Checks and starts Ollama daemon (port 11434)
     2. Verifies Python virtual environment
     3. Installs/updates all Python dependencies
     4. Validates `.env` configuration
     5. Starts Flask server on port 5000
   - **Features**: Colored status messages, error handling, retry logic
   - **Run**: `./start_mommy_ai.sh` or double-click desktop icon

### 3. **Web Chat Interface** (`mommy_ai_chat.html`)
   - **Locations**: 
     - Desktop: `Mommy-AI-Chat.html`
     - Repository: `/mommy_ai_chat.html`
   - **Features**:
     - Modern purple gradient design
     - User selection dropdown
     - Real-time typing indicators
     - Message timestamps
     - Connection status indicator
     - Responsive (works on phone/tablet)
     - Stores server URL in browser
   - **Access**:
     - Local: `http://localhost:5000`
     - Network: `http://<YOUR_IP>:5000`

### 4. **Setup Assistant** (`setup_mommy_ai.sh`)
   - **Purpose**: Automated first-time configuration
   - **Does**:
     - Creates Python virtual environment
     - Installs dependencies
     - Creates `.env` file
     - Sets up user profiles
     - Places desktop shortcuts
   - **Run**: `./setup_mommy_ai.sh`

### 5. **Updated Server** (`mommy_ai.py`)
   - **New Endpoints**:
     - `GET /` - Serves web chat UI
     - `GET /system/status` - Server health & user list
     - `POST /user/profile` - Create/update user profiles
     - `GET /user/profile/<username>` - Get user profile
   - **New Features**:
     - User profile system (remember Hailey vs Brandon)
     - CORS enabled (network access)
     - Personalized prompts per user
     - Profile-based age fallback for NSFW gating
   - **Dependencies Added**:
     - `flask-cors` - Enable cross-network requests

### 6. **User Profiles** (`services/user_profiles.json`)
   - Pre-configured for: **Hailey** and **Brandon**
   - Each profile stores:
     - `display_name` - How Mommy AI addresses them
     - `age` - Used for NSFW gating
     - `pronouns` - For personalization
   - Automatically loaded and used by server

### 7. **Documentation**
   - **`STARTUP_GUIDE.md`** - Comprehensive setup & troubleshooting
   - **`QUICK_START.md`** - Quick reference card
   - **`README.md`** - Will be updated with new system info

---

## 🎯 How Everything Works Together

```
Your Computer (Linux)                 Other Devices on Network
┌─────────────────────────┐           ┌──────────────────────┐
│  Desktop Icon (Double  │           │  Browser              │
│      Click)            │           │  http://<IP>:5000     │
└───────────┬─────────────┘           └──────────┬───────────┘
            │                                    │
            ↓                                    │
   ┌────────────────────┐                       │
   │ start_mommy_ai.sh  │                       │
   └─────────┬──────────┘                       │
             │                                  │
    ┌────────┴────────┬────────────┐            │
    ↓                 ↓            ↓            │
  Ollama      Python venv    Dependencies     │
 Daemon        & venv         (pip install)   │
    │                 │            │           │
    └─────────────────┴────────────┘           │
             ↓                                  │
    ┌─────────────────────┐                    │
    │ mommy_ai.py         │                    │
    │ Flask Server        │                    │
    │ Port 5000           │                    │
    │ 0.0.0.0 (network)   │                    │
    └──────────┬──────────┘                    │
        ┌──────┴──────┐                        │
        │             │                        │
        ↓             ↓                        │
   GET /       (Web UI)                       │
   POST /ask                                   │
   User Profiles ←─────────────────────────────┘
   Knowledge Base
   Ollama Fallback
```

---

## 🚀 Quick Start

### **Absolute Simplest Way**
1. Look at Desktop
2. Double-click **"Mommy-AI"** icon
3. Wait for terminal to show "Running on http://0.0.0.0:5000"
4. Open browser to http://localhost:5000
5. Select "Hailey" or "Brandon" from dropdown
6. Start chatting!

### **From Another Device (Same Network)**
1. Get your computer's IP: `hostname -I`
2. On other device, open: `http://192.168.8.211:5000` (example IP)
3. Select user
4. Chat!

### **Manual Startup**
```bash
cd ~/Documents/GitHub/Mommy-AI
./start_mommy_ai.sh
```

---

## 👥 User Recognition System

**Hailey** and **Brandon** are now fully recognized as distinct users.

When either of you chats, Mommy AI:
- ✅ Knows which user is talking
- ✅ Uses their display name and pronouns
- ✅ Personalizes responses
- ✅ Remembers their profile information
- ✅ Uses their age for NSFW gating (if configured)

### Add/Edit Users
Edit `services/user_profiles.json`:
```json
{
  "username": {
    "display_name": "Display Name",
    "age": 25,
    "pronouns": "they/them"
  }
}
```

---

## 🌐 Network Access

The system is **fully network-accessible**:

### From Same Network
- Use computer's local IP + port 5000
- Example: `http://192.168.8.211:5000`

### From Same Computer
- `http://localhost:5000`

### Configuration
- Server binds to `0.0.0.0:5000` (listens on all interfaces)
- CORS enabled (cross-origin requests allowed)
- No authentication required (internal network only)

---

## 📊 File Changes Summary

### New Files Created
| File | Purpose |
|------|---------|
| `start_mommy_ai.sh` | Orchestrates startup sequence |
| `setup_mommy_ai.sh` | Configuration wizard |
| `Mommy-AI.desktop` | Desktop launcher icon |
| `mommy_ai_chat.html` | Web UI for chatting |
| `STARTUP_GUIDE.md` | Comprehensive documentation |
| `QUICK_START.md` | Quick reference |
| `services/user_profiles.json` | User profile storage |

### Modified Files
| File | Changes |
|------|---------|
| `mommy_ai.py` | Added endpoints, CORS, user profiles, personalization |
| `services/requirements.txt` | Added `flask-cors` |

### Desktop Files
| File | Location |
|------|----------|
| `Mommy-AI.desktop` | Desktop + `/Mommy-AI.desktop` |
| `Mommy-AI-Chat.html` | Desktop + `/mommy_ai_chat.html` |

---

## 🔧 What Each Startup Stage Does

### Stage 1: Ollama Service
```
✓ Check if Ollama installed
✓ Check if daemon already running
✓ If not, start: ollama serve
✓ Wait for API to respond (max 30 sec)
```

### Stage 2: Python Environment
```
✓ Verify .venv exists (create if not)
✓ Activate virtual environment
✓ Install/update pip packages
```

### Stage 3: Configuration
```
✓ Check .env file exists
✓ Validate GEMINI_API_KEY is set
✓ Load user profiles
```

### Stage 4: Server Start
```
✓ Start Flask server on 0.0.0.0:5000
✓ Load knowledge base
✓ Start scheduler daemon thread
✓ Show startup logs
```

---

## 📱 Web UI Features

The browser interface includes:

- **User Selection** - Dropdown to choose Hailey or Brandon
- **Real-Time Status** - Shows if connected/offline
- **Message Display** - User messages on right (purple), AI on left (gray)
- **Typing Indicator** - Animated dots while Mommy is thinking
- **Timestamps** - Each message shows time sent
- **Auto-Scroll** - Chat scrolls to latest message
- **Server URL Storage** - Remembers where server is
- **Error Handling** - Shows connection issues with troubleshooting tips
- **Responsive Design** - Works on desktop, tablet, phone

---

## 🔐 Security Notes

- ✅ No authentication required (assumes local/trusted network)
- ✅ NSFW gating still enforced (`ALLOW_NSFW` + request-level checks)
- ✅ User profiles are just preferences (not secure identities)
- ✅ All data stored locally (`services/user_profiles.json`, etc.)
- ⚠️ Not suitable for untrusted networks without adding auth

---

## 🐛 Troubleshooting

### Icon doesn't work
→ Make script executable: `chmod +x ~/Documents/GitHub/Mommy-AI/start_mommy_ai.sh`

### "Cannot connect from another device"
→ Use your **local IP**, not hostname
→ Get IP: `hostname -I`

### Server won't start
→ Port 5000 in use? `pkill -f "python3 mommy_ai.py"`
→ Check GEMINI_API_KEY in `.env`

### Web UI keeps connecting...
→ Check terminal output for errors
→ Verify `.env` has valid GEMINI_API_KEY

---

## 📚 Documentation Files

| File | What's Inside |
|------|----------------|
| `QUICK_START.md` | 📋 Quick reference and shortcuts |
| `STARTUP_GUIDE.md` | 📖 Complete guide with API docs |
| `README.md` | 📘 Main project documentation |
| This file | 🎯 System overview |

---

## ✨ What's Unique About This Setup

1. **One-Click Launch** - Desktop icon starts everything automatically
2. **Network-Ready** - Chat from any device on your network
3. **Dual-User Support** - Recognizes Hailey vs Brandon automatically
4. **Personalized Responses** - Different treatment based on who's talking
5. **Beautiful UI** - Modern, responsive chat interface
6. **Automated Dependencies** - No manual pip install needed
7. **Ollama Integration** - Automatically starts and manages Ollama daemon
8. **Profile System** - Persistent user preferences and information

---

## 🎓 Learning More

**Want to modify something?**
1. Check `STARTUP_GUIDE.md` for API endpoints
2. Edit files in `services/` for knowledge base
3. Update `mommy_ai_chat.html` to change UI
4. Modify `mommy_ai.py` for server logic

**Want to add features?**
1. Profiles already support custom fields (just add to JSON)
2. Web UI can be customized (HTML/CSS/JavaScript)
3. Server endpoints can be easily added
4. User recognition system is extensible

---

## 🎉 You're All Set!

Everything is configured and ready to go. Just:

1. **Double-click "Mommy-AI" on Desktop** to start
2. **Open browser to http://localhost:5000** (or your network IP)
3. **Select a user** and start chatting!

Questions? Check `QUICK_START.md` or `STARTUP_GUIDE.md` 💕

---

**Created**: December 5, 2025  
**System**: Mommy AI v1.0 with Network Web Interface  
**Users Supported**: Hailey, Brandon (extensible)  
**Access**: Local + Network  
**Status**: Ready to use! 🎀
