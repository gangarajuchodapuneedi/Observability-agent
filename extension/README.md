# Observability Agent VS Code Extension

A VS Code extension that provides a side chat panel for interacting with the Observability Agent backend API.

## Features

- **Side Chat Panel**: Open a dockable chat panel in VS Code
- **Observability Agent Integration**: Connect to the local Observability Agent backend at `http://localhost:8000/ask`
- **Simple Chat UI**: Clean, dark-theme compatible chat interface with message bubbles
- **Real-time Responses**: Get answers with confidence scores from the observability pipeline

## Usage

1. **Start the Observability Agent backend** (Python service running on `http://localhost:8000`)

2. **Open the chat panel**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Observability Agent: Open Chat"
   - Press Enter

3. **Ask questions**:
   - Type your observability question in the input field
   - Press Enter (or Shift+Enter for new line) to send
   - Or click the "Send" button

## Development

### Building

```bash
cd extension
npm install
npm run compile
```

### Running in Development

1. Open this folder in VS Code
2. Press `F5` to open a new Extension Development Host window
3. The extension will be active in the new window

## Requirements

- VS Code 1.74.0 or higher
- Observability Agent backend running on `http://localhost:8000`

## API Integration

The extension communicates with the backend via:

- **Endpoint**: `POST http://localhost:8000/ask`
- **Request**: `{ "question": "<string>" }`
- **Response**: `{ "answer": "<string>", "score": <number|null>, "trace": {} }`

