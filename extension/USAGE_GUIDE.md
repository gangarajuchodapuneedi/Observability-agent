# How to Use Observability Agent Extension

## ✅ Extension is Now Installed!

## Step 1: Open the Chat Panel

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: **"Open Chat"** or **"Observability Agent"**
3. Select: **"Observability Agent: Open Chat"**
4. Press Enter

The chat panel should open on the side of your workspace!

## Step 2: Make Sure Backend is Running

Before using the chat, ensure the Python API server is running:

```bash
python src/api_server.py
```

You should see:
```
============================================================
Observability Agent API Server
============================================================
Starting server on http://localhost:8000
...
```

## Step 3: Ask Questions

In the chat panel:
1. Type your question in the input field
2. Press **Enter** (or **Shift+Enter** for new line)
3. Or click the **"Send"** button

### Example Questions:

**Performance-related (will get detailed 5-step guide, score: 0.95):**
- "Why is my app slow?"
- "How do I check latency?"
- "Performance issues reported"

**Generic questions (will get troubleshooting guide, score: 0.8):**
- "How do I troubleshoot errors?"
- "What should I check in logs?"
- "How to use metrics and traces?"

## Step 4: Understanding the Responses

- **User messages**: Blue bubbles, right-aligned
- **Agent messages**: Grey bubbles, left-aligned
- **Error messages**: Red bubbles (if backend not running)
- **Score**: Shown below agent messages (0.95 for performance, 0.8 for generic)

## Troubleshooting

### "Could not reach the observability service"
- Make sure the backend server is running on port 8000
- Check: `curl http://localhost:8000/health`

### Chat panel doesn't open
- Try reloading Cursor: `Ctrl+Shift+P` → "Developer: Reload Window"
- Check Extension Host logs for errors

### No response from backend
- Verify the API server is running
- Check the terminal where you started `python src/api_server.py`
- Look for any error messages

## Quick Start Commands

```bash
# Terminal 1: Start backend
python src/api_server.py

# In Cursor: Open chat
Ctrl+Shift+P → "Open Chat"
```

Enjoy using the Observability Agent! 🚀

