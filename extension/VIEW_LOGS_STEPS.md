# How to View Extension Host Logs

## Step 1: Open Extension Host Log
1. Press `Ctrl+Shift+P`
2. Type: **"Developer: Show Extension Host Log"**
3. Press Enter

## Step 2: Select Extension Host
You'll see a dialog asking "Pick extension host"
- Select: **"LocalProcess pid: XXXX ext: cursor-agent-exec"** (the one with the IP address)
- Press Enter or click it

## Step 3: View the Logs
After selecting, the Output panel will open showing the Extension Host Log

## Step 4: Search for Observability
1. In the Output panel, press `Ctrl+F`
2. Type: **"observability"**
3. Press Enter
4. Check if any matches appear

## Step 5: What to Look For

### Good Signs:
- `[observability-agent]` - Extension is loading
- `Activating extension 'observability-agent'` - Extension is activating
- `Extension 'observability-agent' is now active` - Extension is working!

### Errors:
- `Cannot find module` - Missing file
- `SyntaxError` - Code error  
- `Activating extension 'observability-agent' failed` - Activation failed
- `Error: Cannot find module './out/extension.js'` - File path issue

## Step 6: If No Results
If searching for "observability" shows no results:
1. Scroll to the TOP of the Extension Host Log
2. Look for any RED error messages
3. Look for messages about "extension" or "activation"
4. Copy the last 20-30 lines of the log

## What to Share
After selecting LocalProcess and viewing the logs:
1. Search for "observability" - do you see any matches?
2. Are there any RED error messages?
3. What do the last 10-20 lines of the log say?

