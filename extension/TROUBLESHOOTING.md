# Troubleshooting Extension Not Showing

## Steps to Fix:

### 1. Complete Restart
- **Close Cursor completely** (not just reload)
- Reopen Cursor
- Wait a few seconds for extensions to load

### 2. Check Extension is Installed
- Press `Ctrl+Shift+X` to open Extensions view
- Search for "observability" or "Observability Agent"
- Check if it appears in the list

### 3. Check Developer Console for Errors
- Press `Ctrl+Shift+P`
- Type: "Developer: Toggle Developer Tools"
- Go to "Console" tab
- Look for any red error messages related to the extension

### 4. Verify Extension Path
The extension should be at:
`C:\Users\SHAIK\.cursor\extensions\observability-agent-0.0.1`

### 5. Try Alternative: Use Workspace Extension
If the installed extension doesn't work, we can try using the extension directly from the workspace folder.

### 6. Check Command Registration
- In Developer Tools Console, type:
  ```javascript
  vscode.commands.getCommands().then(commands => console.log(commands.filter(c => c.includes('observability'))))
  ```
- This will show if the command is registered

## Current Status:
- ✅ Extension files copied to extensions folder
- ✅ Activation event set to "*" (activates on startup)
- ✅ Compiled extension.js exists
- ⚠️ Need to verify Cursor recognizes it

