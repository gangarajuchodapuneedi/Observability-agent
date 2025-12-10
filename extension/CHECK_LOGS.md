# How to Check Extension Host Logs

## Step 1: Open Extension Host Log
1. Press `Ctrl+Shift+P`
2. Type: **"Developer: Show Extension Host Log"**
3. Press Enter
4. A new output panel will open at the bottom

## Step 2: Search for Observability Extension
1. In the Extension Host Log output panel, press `Ctrl+F` to search
2. Type: **"observability"**
3. Press Enter
4. Look for any matches

## Step 3: What to Look For

### If you see messages like:
- `[observability-agent]` - Extension is loading
- `Activating extension 'observability-agent'` - Extension is activating
- `Extension 'observability-agent' is now active` - Extension is working!

### If you see errors like:
- `Cannot find module` - Missing file
- `SyntaxError` - Code error
- `Activating extension 'observability-agent' failed` - Activation failed
- `Error: Cannot find module './out/extension.js'` - File path issue

## Step 4: Check All Messages
If you don't see "observability" in the logs:
1. Scroll to the top of the Extension Host Log
2. Look for any RED error messages
3. Look for messages about "extension" or "activation"
4. Copy any error messages you see

## Step 5: Alternative - Check Output Panel
1. Press `Ctrl+Shift+P`
2. Type: **"View: Toggle Output"**
3. In the dropdown (top right of output panel), select **"Extension Host"**
4. Search for "observability"

## What to Share
Please share:
1. Any messages containing "observability" or "observability-agent"
2. Any RED error messages
3. Whether you see "Activating extension" messages
4. The last few lines of the Extension Host Log

