# Check Extension Host Logs

The extension might be loading but failing silently. Follow these steps:

## Step 1: Open Extension Host Logs
1. Press `Ctrl+Shift+P`
2. Type: **"Developer: Show Extension Host Log"**
3. Press Enter
4. A new output panel will open

## Step 2: Look for These Messages
Search for (Ctrl+F):
- `observability-agent`
- `observabilityAgent`
- `Observability Agent`
- `activation`
- Any RED error messages

## Step 3: Check for Activation Errors
Look for lines like:
- `[Extension Host] Activating extension 'observability-agent' failed`
- `[Extension Host] Error activating extension`
- `Cannot find module`
- `SyntaxError`

## Step 4: If You See Errors
Copy the error message and share it. Common issues:
- Module not found errors
- Syntax errors in extension.js
- Missing dependencies

## Step 5: Alternative - Check Output Panel
1. Press `Ctrl+Shift+P`
2. Type: **"View: Toggle Output"**
3. In the dropdown, select **"Extension Host"**
4. Look for observability-agent messages

## Step 6: Force Extension Discovery
Sometimes Cursor needs to be told to rescan extensions:
1. Close Cursor completely
2. Delete: `C:\Users\SHAIK\.cursor\extensions\observability-agent-0.0.1`
3. Reopen Cursor
4. Reinstall the extension
5. Restart Cursor again

