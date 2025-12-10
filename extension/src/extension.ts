import * as vscode from 'vscode';
import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';

/**
 * Manages webview panels for displaying ArchDrift pages
 */
class ArchDriftPanel {
    private static panels: Map<string, vscode.WebviewPanel> = new Map();
    private static readonly ARCHDRIFT_URL = 'https://arch-drift.vercel.app/';

    public static createOrShow() {
        const panelKey = 'archdrift-main';

        // If panel already exists, reveal it
        if (ArchDriftPanel.panels.has(panelKey)) {
            const existingPanel = ArchDriftPanel.panels.get(panelKey);
            if (existingPanel) {
                existingPanel.reveal();
                return;
            }
        }

        // Create new panel
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        const panel = vscode.window.createWebviewPanel(
            'archDriftViewer',
            'Architecture Drift',
            column || vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
            }
        );

        // Set webview content to load the ArchDrift URL
        panel.webview.html = ArchDriftPanel.getHtmlForUrl(ArchDriftPanel.ARCHDRIFT_URL);

        // Clean up when panel is disposed
        panel.onDidDispose(() => {
            ArchDriftPanel.panels.delete(panelKey);
        });

        ArchDriftPanel.panels.set(panelKey, panel);
    }

    private static getHtmlForUrl(url: string): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src * 'unsafe-inline' 'unsafe-eval'; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline';">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Architecture Drift</title>
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        iframe { width: 100%; height: 100vh; border: none; }
    </style>
</head>
<body>
    <iframe src="${url}" sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-top-navigation"></iframe>
</body>
</html>`;
    }
}

/**
 * Manages the Observability Agent webview panel
 */
export class ObservabilityPanel {
    public static currentPanel: ObservabilityPanel | undefined;

    public static readonly viewType = 'observabilityAgent';

    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (ObservabilityPanel.currentPanel) {
            ObservabilityPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            ObservabilityPanel.viewType,
            'Observability Agent',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
            }
        );

        ObservabilityPanel.currentPanel = new ObservabilityPanel(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        // Set the webview's initial html content
        this._update();

        // Listen for when the panel is disposed
        // This happens when the user closes the panel or when the panel is closed programmatically
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                console.log('[OBS-AGENT] message from webview', message?.type);
                switch (message.type) {
                    case 'ask':
                        await this.handleAsk(message.text);
                        return;
                    case 'openArchDrift': {
                        if (message.url) {
                            vscode.env.openExternal(vscode.Uri.parse(message.url));
                        }
                        break;
                    }
                }
            },
            null,
            this._disposables
        );
    }

    private async handleAsk(question: string) {
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
            console.log('[OBS-AGENT] posting to API');
            const data = await postJson('http://localhost:8000/ask', { question: trimmedQuestion }) as {
                answer?: string;
                score?: number | null;
                trace?: any;
                mode?: string;
                drift_data?: any;
            };

            // Check if this is an architecture drift response (mode flag or known link text)
            const isArchDrift =
                data.mode === 'arch_drift' ||
                (typeof data.answer === 'string' &&
                    data.answer.toLowerCase().includes('archdrift ui'));

            if (isArchDrift) {
                // Open ArchDrift page automatically without showing text answer
                ArchDriftPanel.createOrShow();
                return;
            }

            // Send answer back to webview for non-arch-drift responses
            this._panel.webview.postMessage({
                type: 'answer',
                question: trimmedQuestion,
                answer: data.answer ?? '',
                score: data.score ?? null,
                trace: data.trace ?? null,
                mode: data.mode ?? null,
                drift_data: data.drift_data ?? null,
            });
        } catch (err: any) {
            console.error('[OBS-AGENT] ask failed', err);
            // Send error back to webview
            this._panel.webview.postMessage({
                type: 'error',
                question: trimmedQuestion,
                message:
                    'Could not reach the observability service at http://localhost:8000/ask. Is it running?\n\n' +
                    (err?.message ?? String(err)),
            });
        }
    }

    public dispose() {
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

    private _update() {
        const webview = this._panel.webview;
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        const nonce = getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}'; connect-src http://localhost:8000 https://localhost:8000;">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Observability Agent</title>
    <style>
        body { margin: 0; padding: 0; background: var(--vscode-editor-background); color: var(--vscode-foreground); font-family: var(--vscode-font-family); display: flex; flex-direction: column; height: 100vh; }
        #messages { flex: 1; padding: 12px; overflow-y: auto; }
        .message { padding: 8px 10px; margin-bottom: 8px; border-radius: 8px; white-space: pre-wrap; word-wrap: break-word; }
        .user { background: #007acc; color: white; }
        .agent { background: var(--vscode-input-background); border: 1px solid var(--vscode-input-border); }
        #inputBar { display: flex; gap: 8px; padding: 8px; border-top: 1px solid var(--vscode-panel-border); }
        #input { flex: 1; min-height: 32px; padding: 6px 8px; }
        #send { padding: 6px 12px; }
    </style>
</head>
<body>
    <div id="messages"></div>
    <div id="inputBar">
        <textarea id="input" placeholder="Ask the observability agent..." rows="1"></textarea>
        <button id="send">Send</button>
    </div>
    <script nonce="${nonce}">
        (function () {
            const vscode = acquireVsCodeApi();
            const input = document.getElementById('input');
            const sendButton = document.getElementById('send');
            const chatContainer = document.getElementById('messages');

            function appendMessage(role, text) {
                if (!chatContainer) return;
                const div = document.createElement('div');
                div.className = 'message ' + (role || 'agent');
                div.textContent = text || '';
                chatContainer.appendChild(div);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            function sendCurrentInput() {
                if (!input) return;
                const value = (input.value || '').trim();
                if (!value) return;
                appendMessage('user', value);
                vscode.postMessage({ type: 'ask', text: value });
                input.value = '';
            }

            window.addEventListener('message', event => {
                const msg = event.data || {};
                if (msg.type === 'answer') {
                    appendMessage('agent', msg.answer || '');
                } else if (msg.type === 'error') {
                    appendMessage('agent', msg.message || 'Error');
                } else if (msg.type === 'status') {
                    appendMessage('agent', msg.message || 'Thinking...');
                }
            });

            if (sendButton) sendButton.addEventListener('click', sendCurrentInput);
            if (input) {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendCurrentInput();
                    }
                });
            }
            console.log('[OBS-AGENT] Webview script initialized (minimal)');
        })();
    </script>
</body>
</html>`;
    }
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

/**
 * Simple JSON POST helper that works in the extension host without relying on global fetch.
 */
async function postJson(urlString: string, body: Record<string, any>): Promise<any> {
    return new Promise((resolve, reject) => {
        try {
            const target = new URL(urlString);
            const isHttps = target.protocol === 'https:';
            const client = isHttps ? https : http;

            const requestBody = JSON.stringify(body ?? {});
            const options: http.RequestOptions = {
                method: 'POST',
                hostname: target.hostname,
                port: target.port || (isHttps ? 443 : 80),
                path: target.pathname,
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(requestBody),
                },
            };

            const req = client.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                res.on('end', () => {
                    if (res.statusCode && res.statusCode >= 400) {
                        return reject(new Error(`HTTP error! status: ${res.statusCode}`));
                    }
                    try {
                        const parsed = data ? JSON.parse(data) : {};
                        resolve(parsed);
                    } catch (err) {
                        reject(err);
                    }
                });
            });

            req.on('error', (err) => reject(err));
            req.write(requestBody);
            req.end();
        } catch (err) {
            reject(err);
        }
    });
}

export function activate(context: vscode.ExtensionContext) {
    // Register the command
    const disposable = vscode.commands.registerCommand('observabilityAgent.openChat', () => {
        ObservabilityPanel.createOrShow(context.extensionUri);
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}

