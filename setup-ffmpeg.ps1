# PowerShell script to permanently add FFmpeg to system PATH
# Run this script as Administrator for system-wide installation

Write-Host "Setting up FFmpeg for Multimodal RAG System..." -ForegroundColor Cyan

# Find FFmpeg installation
$ffmpegPath = $null
$wingetPaths = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ffmpeg.exe" -Recurse -ErrorAction SilentlyContinue

if ($wingetPaths) {
    $ffmpegPath = Split-Path -Parent $wingetPaths[0].FullName
    Write-Host "Found FFmpeg at: $ffmpegPath" -ForegroundColor Green
} else {
    Write-Host "FFmpeg not found. Installing via WinGet..." -ForegroundColor Yellow
    winget install Gyan.FFmpeg
    
    # Search again after installation
    Start-Sleep -Seconds 3
    $wingetPaths = Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "ffmpeg.exe" -Recurse -ErrorAction SilentlyContinue
    if ($wingetPaths) {
        $ffmpegPath = Split-Path -Parent $wingetPaths[0].FullName
    }
}

if ($ffmpegPath) {
    # Check if already in PATH
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    
    if ($currentPath -notlike "*$ffmpegPath*") {
        Write-Host "Adding FFmpeg to user PATH..." -ForegroundColor Yellow
        
        # Add to user PATH (no admin required)
        $newPath = "$ffmpegPath;$currentPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        
        # Also update current session
        $env:PATH = "$ffmpegPath;$env:PATH"
        
        Write-Host "✓ FFmpeg added to PATH successfully!" -ForegroundColor Green
        Write-Host "✓ You may need to restart your terminal or IDE for changes to take effect." -ForegroundColor Yellow
    } else {
        Write-Host "✓ FFmpeg is already in PATH" -ForegroundColor Green
    }
    
    # Test FFmpeg
    Write-Host "`nTesting FFmpeg installation..." -ForegroundColor Cyan
    & "$ffmpegPath\ffmpeg.exe" -version | Select-Object -First 1
    
    Write-Host "`n✓ Setup complete! Your Multimodal RAG System can now process videos." -ForegroundColor Green
} else {
    Write-Host "✗ Failed to find or install FFmpeg. Please install manually." -ForegroundColor Red
    Write-Host "Visit: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Yellow
}
