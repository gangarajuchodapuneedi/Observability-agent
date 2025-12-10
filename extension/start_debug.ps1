# Start Extension Development Host
Write-Host "Opening extension folder in VS Code..." -ForegroundColor Green
Start-Process code -ArgumentList "$PSScriptRoot"

Write-Host "Waiting for VS Code to open..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Extension folder opened in VS Code!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. In VS Code, press F5 to start debugging" -ForegroundColor White
Write-Host "2. Or go to Run > Start Debugging" -ForegroundColor White
Write-Host "3. Select 'Run Extension' from the debug dropdown" -ForegroundColor White
Write-Host ""
Write-Host "The Extension Development Host window will open automatically." -ForegroundColor Green
Write-Host ""

