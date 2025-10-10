# PowerShell script to stop all Streamlit/Python processes
Write-Host "Stopping all Python and Streamlit processes..." -ForegroundColor Yellow

# Kill Python processes
Get-Process | Where-Object {$_.ProcessName -eq "python"} | ForEach-Object {
    Write-Host "Stopping Python process $($_.Id)" -ForegroundColor Red
    Stop-Process -Id $_.Id -Force
}

# Kill Streamlit processes specifically
Get-Process | Where-Object {$_.ProcessName -like "*streamlit*"} | ForEach-Object {
    Write-Host "Stopping Streamlit process $($_.Id)" -ForegroundColor Red
    Stop-Process -Id $_.Id -Force
}

# Wait a moment and check if port 8501 is free
Start-Sleep -Seconds 2
$connection = Test-NetConnection -ComputerName localhost -Port 8501 -WarningAction SilentlyContinue

if ($connection.TcpTestSucceeded) {
    Write-Host "WARNING: Port 8501 is still in use!" -ForegroundColor Red
} else {
    Write-Host "SUCCESS: Port 8501 is now free!" -ForegroundColor Green
}

Write-Host "Done!" -ForegroundColor Green