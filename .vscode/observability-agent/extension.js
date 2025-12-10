const vscode = require('vscode');
/**
 * Manages the Observability Agent webview panel
 */
class ObservabilityPanel {
    static createOrShow(extensionUri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;
        // If we already have a panel, show it
        if (ObservabilityPanel.currentPanel) {
            ObservabilityPanel.currentPanel._panel.reveal(column);
            return;
        }
        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(ObservabilityPanel.viewType, 'Observability Agent', column || vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true,
        });
        ObservabilityPanel.currentPanel = new ObservabilityPanel(panel, extensionUri);
    }
    constructor(panel, extensionUri) {
        this._disposables = [];
        this._panel = panel;
        this._extensionUri = extensionUri;
        // Set the webview's initial html content
        this._update();
        // Listen for when the panel is disposed
        // This happens when the user closes the panel or when the panel is closed programmatically
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.type) {
                case 'ask':
                    await this.handleAsk(message.text);
                    return;
            }
        }, null, this._disposables);
    }
    async handleAsk(question) {
        const trimmedQuestion = question.trim();
        if (!trimmedQuestion) {
            return;
        }
        // Send status message
        this._panel.webview.postMessage({
            type: 'status',
            message: 'Thinking...'
        });
        try {
            const response = await fetch('http://localhost:8000/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: trimmedQuestion }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            // Send answer back to webview
            this._panel.webview.postMessage({
                type: 'answer',
                question: trimmedQuestion,
                answer: data.answer ?? '',
                score: data.score ?? null,
                trace: data.trace ?? null,
            });
        }
        catch (err) {
            // Send error back to webview
            this._panel.webview.postMessage({
                type: 'error',
                question: trimmedQuestion,
                message: 'Could not reach the observability service at http://localhost:8000/ask. Is it running?\n\n' +
                    (err?.message ?? String(err)),
            });
        }
    }
    dispose() {
        ObservabilityPanel.currentPanel = undefined;
        // Clean up our resources
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
    _update() {
        const webview = this._panel.webview;
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }
    _getHtmlForWebview(webview) {
        const nonce = getNonce();
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Observability Agent</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        #container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background-color: var(--vscode-editor-background);
        }

        .message {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            word-wrap: break-word;
            line-height: 1.4;
        }

        .message.user {
            align-self: flex-end;
            background-color: #007acc;
            color: white;
            margin-left: auto;
        }

        .message.agent {
            align-self: flex-start;
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
        }

        .message.error {
            align-self: flex-start;
            background-color: rgba(255, 0, 0, 0.1);
            color: #ff6b6b;
            border: 1px solid #ff6b6b;
        }

        .message.status {
            align-self: flex-start;
            background-color: transparent;
            color: var(--vscode-descriptionForeground);
            font-style: italic;
            padding: 4px 8px;
            font-size: 0.9em;
        }

        .score {
            font-size: 0.85em;
            color: var(--vscode-descriptionForeground);
            margin-top: 6px;
            font-style: italic;
        }

        #inputBar {
            display: flex;
            padding: 12px;
            border-top: 1px solid var(--vscode-panel-border);
            background-color: var(--vscode-editor-background);
            gap: 8px;
        }

        #input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid var(--vscode-input-border);
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            resize: none;
            min-height: 40px;
            max-height: 120px;
        }

        #input:focus {
            outline: 1px solid var(--vscode-focusBorder);
            outline-offset: -1px;
        }

        #input:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        #send {
            padding: 8px 16px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: var(--vscode-font-size);
            height: 40px;
        }

        #send:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        #send:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        /* Scrollbar styling */
        #messages::-webkit-scrollbar {
            width: 8px;
        }

        #messages::-webkit-scrollbar-track {
            background: var(--vscode-scrollbarSlider-background);
        }

        #messages::-webkit-scrollbar-thumb {
            background: var(--vscode-scrollbarSlider-activeBackground);
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="messages"></div>
        <div id="inputBar">
            <textarea id="input" placeholder="Ask the observability agent..." rows="1"></textarea>
            <button id="send">Send</button>
        </div>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        const messagesContainer = document.getElementById('messages');
        const input = document.getElementById('input');
        const sendButton = document.getElementById('send');

        function appendMessage(role, text, meta) {
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${role}\`;
            
            if (role === 'status') {
                messageDiv.textContent = text;
            } else {
                const textNode = document.createTextNode(text);
                messageDiv.appendChild(textNode);
                
                if (meta && meta.score !== null && meta.score !== undefined) {
                    const scoreDiv = document.createElement('div');
                    scoreDiv.className = 'score';
                    scoreDiv.textContent = \`Score: \${meta.score}\`;
                    messageDiv.appendChild(scoreDiv);
                }
            }
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function setBusy(busy) {
            sendButton.disabled = busy;
            input.disabled = busy;
            if (!busy) {
                input.focus();
            }
        }

        function sendMessage() {
            const question = input.value.trim();
            if (!question) {
                return;
            }

            // Append user message
            appendMessage('user', question);

            // Clear input
            input.value = '';
            input.style.height = 'auto';

            // Set busy state
            setBusy(true);

            // Send message to extension
            vscode.postMessage({
                type: 'ask',
                text: question
            });
        }

        // Send button click
        sendButton.addEventListener('click', sendMessage);

        // Enter key handling
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });

        // Handle messages from extension
        window.addEventListener('message', (event) => {
            const message = event.data;

            switch (message.type) {
                case 'answer':
                    appendMessage('agent', message.answer, { score: message.score });
                    setBusy(false);
                    break;

                case 'error':
                    appendMessage('error', message.message);
                    setBusy(false);
                    break;

                case 'status':
                    appendMessage('status', message.message);
                    break;
            }
        });

        // Focus input on load
        input.focus();
    </script>
</body>
</html>`;
    }
}
ObservabilityPanel.viewType = 'observabilityAgent';
ObservabilityPanel.currentPanel = undefined;

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

function activate(context) {
    // Register the command
    const disposable = vscode.commands.registerCommand('observabilityAgent.openChat', () => {
        ObservabilityPanel.createOrShow(context.extensionUri);
    });
    context.subscriptions.push(disposable);
}

function deactivate() { }

module.exports = {
    activate,
    deactivate
};

