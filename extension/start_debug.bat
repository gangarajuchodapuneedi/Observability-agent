@echo off
echo Opening extension folder in VS Code...
start "" code "%CD%"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Extension folder opened in VS Code!
echo ========================================
echo.
echo Next steps:
echo 1. In VS Code, press F5 to start debugging
echo 2. Or go to Run ^> Start Debugging
echo 3. Select 'Run Extension' from the debug dropdown
echo.
echo The Extension Development Host window will open automatically.
echo.
pause

