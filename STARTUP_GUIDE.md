# Mommy AI - Startup & Web UI Guide

## Quick Start (Desktop)

**Double-click the Mommy AI icon on your desktop** to start the complete system:

1. **Ollama Service** - Starts automatically if not running
2. **Dependencies** - Installed/updated from `services/requirements.txt`
3. **Server** - Flask server launches on `http://localhost:5000`
4. **Web UI** - Available at `http://localhost:5000`

The startup script will:
- ✅ Check and start Ollama daemon
- ✅ Verify/create Python virtual environment
- ✅ Install/update Python dependencies
- ✅ Validate `.env` configuration
- ✅ Start the Mommy AI Flask server
- ✅ Launch the scheduler in background

---

## Using the Web Chat Interface

Once the server is running, you can chat with Mommy AI in two ways:

### Local Access
- **Direct**: Open browser to `http://localhost:5000`
- **Or**: Open `mommy_ai_chat.html` in browser and enter server URL

### Network Access (from another device)
- Get your computer's IP address:
  ```bash
  hostname -I
  ```
- On the other device, open browser to: `http://<YOUR_IP>:5000`
  - Example: `http://192.168.8.211:5000`

### Using the Chat UI

1. **Select a User** - Choose from dropdown (Hailey, Brandon, or custom users)
2. **Start Chatting** - Type in the message box and press Enter or click Send
3. **Profile Recognition** - Mommy AI recognizes which user is talking and personalizes responses

---

## Creating User Profiles

Profiles allow Mommy AI to remember who's talking and personalize responses.

### Method 1: Web UI
```bash
curl -X POST http://localhost:5000/user/profile \
  -H "Content-Type: application/json" \
  -d '{
    "username": "brandon",
    "display_name": "Brandon",
    "age": 30,
    "pronouns": "he/him"
  }'
```

### Method 2: Direct Profile File
Edit `services/user_profiles.json`:
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

---

## Advanced Configuration

### Enable NSFW Models
Edit `.env`:
```env
ALLOW_NSFW=true
OLLAMA_ENABLED=true
OLLAMA_MODEL=dolphin-nsfw
```

Then pull the model:
```bash
ollama pull dolphin-nsfw
```

### Change Server Port
Edit `mommy_ai.py` (last line, change port):
```python
app.run(host="0.0.0.0", port=5000, debug=True)
```

### Manual Startup (if not using desktop launcher)
```bash
./start_mommy_ai.sh
```

---

## Troubleshooting

### "Cannot connect to server"
- Ensure the desktop launcher finished (should see `Running on http://0.0.0.0:5000`)
- Check if port 5000 is already in use:
  ```bash
  lsof -i :5000
  ```
- Kill the process and retry:
  ```bash
  pkill -f "python3 mommy_ai.py"
  ```

### Web UI shows "Connecting..."
- Check your server URL matches where server is running
- If accessing from another device, use full IP address, not `localhost`
- Verify firewall allows port 5000

### Python dependencies fail to install
- Ensure `python3-dev` and `portaudio19-dev` are installed:
  ```bash
  sudo apt-get install -y python3-dev portaudio19-dev
  ```

### Ollama won't start
- Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
- Or manually start: `ollama serve`

---

## API Endpoints

### Chat
```
POST /ask
Body: {"user": "hailey", "query": "Hello Mommy"}
Response: {"response": "..."}
```

### User Profiles
```
POST /user/profile
GET /user/profile/<username>
```

### System
```
GET /system/status
POST /system/reload
GET / (serves web UI)
```

### Feedback (Self-Learning)
```
POST /feedback/effectiveness
Body: {"user": "hailey", "action_type": "Emotional Support", "communication_style": "Nurturing", "feedback": 1}
```

---

## Architecture

```
Desktop Launcher (Mommy-AI.desktop)
        ↓
Startup Script (start_mommy_ai.sh)
        ↓
┌───────┴───────────────┬─────────────────┐
│                       │                 │
Ollama Daemon      Dependency Check   Python venv
(port 11434)       & Install          & Flask Server
                                      (port 5000)
        ↓
    ┌───────────────────┬──────────────────┐
    │                   │                  │
Knowledge Base     Scheduler        Web Chat UI
(JSON/TXT/DB)      (Daemon)         (HTML/JS)
```

---

## Network Requirements

For accessing from another device on the same network:
- Both devices on same network
- Port 5000 accessible (check firewall)
- Use device's local IP, not hostname

Get your IP:
```bash
hostname -I  # Linux
ipconfig     # Windows
ifconfig     # Mac
```

Example network URL:
```
http://192.168.8.211:5000
```

---

Enjoy chatting with Mommy AI! 💕
