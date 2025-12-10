# How to Run the Observability Agent Project

## Prerequisites

1. **Python 3.7+** installed and accessible
2. **Node.js** installed (for the VS Code extension)

## Step 1: Install Python Dependencies

```bash
# Install Flask and Flask-CORS
pip install flask flask-cors

# Or if pip is not in PATH:
python -m pip install flask flask-cors
# Or on Windows:
py -m pip install flask flask-cors
```

## Step 2: Start the Backend API Server

Open a terminal and run:

```bash
python src/api_server.py
```

Or:

```bash
python -m src.api_server
```

You should see:
```
============================================================
Observability Agent API Server
============================================================
Starting server on http://localhost:8000
Endpoints:
  POST http://localhost:8000/ask
  GET  http://localhost:8000/health
============================================================
 * Running on http://localhost:8000
```

**Keep this terminal open** - the server needs to keep running.

## Step 3: Test the API (Optional)

In another terminal, test the API:

```bash
# Health check
curl http://localhost:8000/health

# Test question
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"Why is my app slow?\"}"
```

## Step 4: Run the VS Code Extension

### Option A: Extension Development Host (Recommended for Testing)

1. Open the `extension` folder in VS Code:
   ```bash
   cd extension
   code .
   ```

2. Press `F5` (or go to Run > Start Debugging)
   - This opens a new **Extension Development Host** window

3. In the new window:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type: **"Observability Agent: Open Chat"**
   - Press Enter

4. The chat panel will open on the side

5. Type a question like: **"Why is my app slow?"**
   - Press Enter or click Send
   - You should see the response with a score

### Option B: Install in Main Workspace

1. Package the extension:
   ```bash
   cd extension
   npm install -g @vscode/vsce
   npm run compile
   vsce package
   ```

2. Install the `.vsix` file:
   - In VS Code: `Ctrl+Shift+P` → "Extensions: Install from VSIX..."
   - Select the generated `.vsix` file

3. Reload VS Code

4. Press `Ctrl+Shift+P` → "Observability Agent: Open Chat"

## Troubleshooting

### Backend Issues

- **Port 8000 already in use**: Change the port in `src/api_server.py` (last line)
- **Module not found**: Make sure you're in the project root directory
- **Flask not found**: Run `pip install flask flask-cors`

### Extension Issues

- **Extension doesn't open**: Check the Debug Console in VS Code for errors
- **"Could not reach service"**: Make sure the backend is running on port 8000
- **Compilation errors**: Run `npm run compile` in the `extension` folder

## Quick Test Commands

```bash
# Test backend health
curl http://localhost:8000/health

# Test with a performance question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Why is my app slow?\"}"

# Test with a generic question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"How do I troubleshoot errors?\"}"
```

## Project Structure

```
Observability-agent/
├── src/
│   ├── api_server.py      # HTTP API server (NEW)
│   ├── main.py            # CLI entry point
│   └── ...                # Pipeline modules
├── extension/             # VS Code extension
│   └── src/
│       └── extension.ts   # Extension code
└── requirements.txt       # Python dependencies
```

