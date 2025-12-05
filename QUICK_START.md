# 🎀 Mommy AI - Quick Reference Card

## What I Just Built For You

### 1. **Desktop Launcher** 
   - **Icon**: `Mommy-AI.desktop` (on your Desktop)
   - **Action**: Double-click to start everything automatically
   - **Does**: Starts Ollama → Checks dependencies → Launches server → Web UI ready

### 2. **Startup Script** (`start_mommy_ai.sh`)
   - Orchestrates the complete startup sequence
   - Handles Ollama daemon, venv, pip install, .env validation
   - Shows colored status messages
   - Ctrl+C to stop the server

### 3. **Web Chat UI** (`mommy_ai_chat.html`)
   - Beautiful modern chat interface
   - User selection dropdown (Hailey, Brandon, or custom)
   - Works on **any device** on your network
   - Typing indicators, message timestamps, responsive design
   - Stored server URL for convenience

### 4. **Network-Ready Server**
   - Server listens on `0.0.0.0:5000` (accessible from network)
   - CORS enabled (cross-origin requests allowed)
   - User profiles persist in `services/user_profiles.json`
   - Personalized responses based on who's talking

### 5. **Setup Assistant** (`setup_mommy_ai.sh`)
   - Creates virtual environment
   - Installs/updates dependencies
   - Initializes `.env` and user profiles
   - Places shortcuts on Desktop

---

## How To Use It

### **Easiest Way (One Click)**
```
1. Double-click "Mommy-AI" icon on Desktop
2. Wait ~5-10 seconds for server to start
3. Browser opens automatically (or go to http://localhost:5000)
4. Select user (Hailey or Brandon)
5. Start chatting!
```

### **From Command Line**
```bash
~/Documents/GitHub/Mommy-AI/start_mommy_ai.sh
```

### **From Another Device on Network**
```
1. Get your computer's IP: hostname -I
2. On other device, open: http://<YOUR_IP>:5000
   Example: http://192.168.8.211:5000
3. Select user and chat
```

---

## File Structure
```
Mommy-AI/
├── start_mommy_ai.sh           # Main startup script
├── setup_mommy_ai.sh           # Setup wizard
├── Mommy-AI.desktop            # Desktop launcher
├── mommy_ai_chat.html          # Web UI (also on Desktop)
├── mommy_ai.py                 # Main Flask server
├── services/
│   ├── requirements.txt        # Python dependencies
│   ├── user_profiles.json      # User profiles storage
│   └── [knowledge files]
├── STARTUP_GUIDE.md            # Full documentation
└── .env                        # Config (GEMINI_API_KEY, etc)
```

---

## Creating User Profiles

Brandon and you are already recognized as separate users. To customize:

### Edit `services/user_profiles.json`:
```json
{
  "hailey": {
    "display_name": "Hailey",
    "age": null,
    "pronouns": "she/her"
  },
  "brandon": {
    "display_name": "Brandon",
    "age": 30,
    "pronouns": "he/him"
  }
}
```

### Or via API:
```bash
curl -X POST http://localhost:5000/user/profile \
  -H "Content-Type: application/json" \
  -d '{"username":"brandon","display_name":"Brandon","age":30,"pronouns":"he/him"}'
```

---

## Key Features

✅ **Dual-User Recognition** - Mommy AI knows if it's you or Brandon talking  
✅ **Personalized Responses** - Different tone and context for each user  
✅ **Network Chat** - Chat from any device on your network  
✅ **Modern Web UI** - Beautiful responsive interface  
✅ **Desktop Launcher** - One-click startup  
✅ **Automatic Dependencies** - Handles venv, pip install, etc.  
✅ **Ollama Integration** - Starts Ollama daemon if needed  
✅ **Profile Persistence** - Remembers user preferences  
✅ **CORS Enabled** - Works cross-network  

---

## Troubleshooting

### "Mommy AI icon doesn't work"
→ Make sure `start_mommy_ai.sh` is executable:
```bash
chmod +x ~/Documents/GitHub/Mommy-AI/start_mommy_ai.sh
```

### "Cannot connect to server from another device"
→ Use **local IP** not hostname:
```bash
hostname -I  # Get your IP
# Then use http://192.168.X.X:5000
```

### "Web UI keeps saying 'Connecting...'"
→ Check server console output (should show "Running on..." message)
→ Make sure GEMINI_API_KEY is in `.env`

### "Port 5000 already in use"
```bash
pkill -f "python3 mommy_ai.py"
```

---

## What Each Script Does

| Script | Purpose | How to Run |
|--------|---------|-----------|
| `start_mommy_ai.sh` | Main startup (Ollama + deps + server) | `./start_mommy_ai.sh` or double-click icon |
| `setup_mommy_ai.sh` | First-time configuration | `./setup_mommy_ai.sh` |
| `mommy_ai_chat.html` | Web UI | Open in browser or double-click |
| `mommy_ai.py` | Flask server | Runs automatically via startup script |

---

## API Endpoints (For Developers)

```
Chat:
  POST /ask
  Body: {"user": "hailey", "query": "Hello"}

Profiles:
  POST /user/profile
  GET /user/profile/<username>

System:
  GET /system/status
  GET / (serves chat UI)

Feedback:
  POST /feedback/effectiveness
```

---

## Network Access Setup

### Local Machine
- Go to: `http://localhost:5000`

### Same Network
- Get IP: `hostname -I`
- Go to: `http://192.168.X.X:5000`

### Different Network (requires port forwarding)
- Port forward 5000 → 5000 on your router
- Use your public IP

---

## Next Steps

1. ✅ **Setup is complete!** Run setup assistant if you haven't:
   ```bash
   ~/Documents/GitHub/Mommy-AI/setup_mommy_ai.sh
   ```

2. 📋 **Double-click the Mommy-AI icon** on your Desktop to start

3. 🌐 **Open the web interface** in your browser at `http://localhost:5000`

4. 💬 **Start chatting** - Select "Hailey" or "Brandon" and begin!

---

**Questions?** Check `STARTUP_GUIDE.md` for detailed documentation.

Enjoy! 🎀💕
