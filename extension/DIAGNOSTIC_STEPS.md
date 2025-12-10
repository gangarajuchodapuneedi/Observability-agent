# Diagnostic Steps for Extension Not Loading

## Step 1: Complete Cursor Restart
1. **Close ALL Cursor windows completely**
2. Wait 5 seconds
3. Reopen Cursor
4. Wait 10-15 seconds for extensions to load

## Step 2: Check Extension Host Logs
1. Press `Ctrl+Shift+P`
2. Type: "Developer: Show Extension Host Log"
3. Press Enter
4. Look for:
   - `[observability-agent]` messages
   - Any RED errors mentioning "observability-agent"
   - Messages about "activation" or "loading"

## Step 3: Check Extension is Recognized
1. Press `Ctrl+Shift+X` (Extensions view)
2. Click the "..." menu (top right)
3. Select "Show Built-in Extensions" or "Show Installed Extensions"
4. Search for "observability"
5. Check if "Observability Agent" appears in the list

## Step 4: Manual Command Execution
1. Press `Ctrl+Shift+P`
2. Type: "Developer: Toggle Developer Tools"
3. Go to "Console" tab
4. Paste this and press Enter:
```javascript
vscode.commands.getCommands().then(cmds => {
  const obs = cmds.filter(c => c.includes('observability'));
  console.log('Observability commands:', obs);
  if (obs.length === 0) {
    console.log('Extension not loaded. Checking extension host...');
    console.log('All commands:', cmds.slice(0, 50));
  }
});
```

## Step 5: Check Extension Path
The extension should be at:
`C:\Users\SHAIK\.cursor\extensions\observability-agent-0.0.1`

Verify these files exist:
- `package.json` ✓
- `out/extension.js` ✓
- `out/extension.js` should start with `const vscode = require('vscode');`

## Step 6: Force Extension Reload
If the extension still doesn't work:
1. Close Cursor completely
2. Delete: `C:\Users\SHAIK\.cursor\extensions\observability-agent-0.0.1`
3. Reinstall using the installation script
4. Restart Cursor

