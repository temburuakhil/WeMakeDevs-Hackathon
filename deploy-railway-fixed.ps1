#!/usr/bin/env pwsh
# Railway Deployment Helper Script

Write-Host "🚂 Railway Deployment Helper" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check if git is installed
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed. Please install Git first." -ForegroundColor Red
    exit 1
}

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "⚠️  Not a git repository. Initializing..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
}

# Check for uncommitted changes
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📝 You have uncommitted changes:" -ForegroundColor Yellow
    git status --short
    Write-Host "`nCommitting changes..." -ForegroundColor Yellow
    git add .
    git commit -m "Prepare for Railway deployment"
}

# Check if remote exists
$remotes = git remote -v
if (-not $remotes) {
    Write-Host "`n🔗 No git remote found." -ForegroundColor Yellow
    Write-Host "Please add your GitHub repository URL:" -ForegroundColor Cyan
    Write-Host "Example: git remote add origin https://github.com/yourusername/WeMakeDevs-Hackathon.git" -ForegroundColor Gray
    $remoteUrl = Read-Host "`nEnter your GitHub repository URL (or press Enter to skip)"
    
    if ($remoteUrl) {
        git remote add origin $remoteUrl
        Write-Host "✅ Remote added!" -ForegroundColor Green
    }
}

# Push to GitHub
Write-Host "`n📤 Pushing to GitHub..." -ForegroundColor Cyan
try {
    git push -u origin main 2>$null
    if ($LASTEXITCODE -ne 0) {
        git push -u origin master 2>$null
    }
    Write-Host "✅ Code pushed to GitHub!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not push to GitHub. You may need to push manually." -ForegroundColor Yellow
}

# Check if Railway CLI is installed
Write-Host "`n🔍 Checking for Railway CLI..." -ForegroundColor Cyan
$railwayCLI = Get-Command railway -ErrorAction SilentlyContinue

if (-not $railwayCLI) {
    Write-Host "❌ Railway CLI not found." -ForegroundColor Yellow
    Write-Host "`nWould you like to install it? (Requires Node.js)" -ForegroundColor Cyan
    Write-Host "1. Yes, install Railway CLI" -ForegroundColor Gray
    Write-Host "2. No, I will deploy via web interface" -ForegroundColor Gray
    $choice = Read-Host "`nChoice (1/2)"
    
    if ($choice -eq "1") {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            Write-Host "`nInstalling Railway CLI..." -ForegroundColor Yellow
            npm install -g @railway/cli
            Write-Host "✅ Railway CLI installed!" -ForegroundColor Green
            $railwayCLI = $true
        } else {
            Write-Host "❌ Node.js/npm not found. Please install Node.js first." -ForegroundColor Red
            Write-Host "Visit: https://nodejs.org/" -ForegroundColor Cyan
            $railwayCLI = $false
        }
    } else {
        $railwayCLI = $false
    }
}

# Deployment options
Write-Host "`n🚀 Deployment Options:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

if ($railwayCLI) {
    Write-Host "`n✅ Railway CLI is available!" -ForegroundColor Green
    Write-Host "`nDeployment steps:" -ForegroundColor Cyan
    Write-Host "1. railway login" -ForegroundColor Yellow
    Write-Host "2. railway init" -ForegroundColor Yellow
    Write-Host "3. railway up" -ForegroundColor Yellow
    
    Write-Host "`nWould you like to deploy now? (y/n)" -ForegroundColor Cyan
    $deploy = Read-Host
    
    if ($deploy -eq "y" -or $deploy -eq "Y") {
        Write-Host "`n🔐 Logging into Railway..." -ForegroundColor Cyan
        railway login
        
        Write-Host "`n📦 Initializing project..." -ForegroundColor Cyan
        railway init
        
        # Get Cerebras API key
        Write-Host "`n🔑 Please enter your Cerebras API key:" -ForegroundColor Cyan
        Write-Host "(Get one at: https://cerebras.ai/api)" -ForegroundColor Gray
        $apiKey = Read-Host -MaskInput
        
        if ($apiKey) {
            railway variables set CEREBRAS_API_KEY=$apiKey
            railway variables set PORT=8000
            railway variables set DEBUG=false
            railway variables set PYTHONUNBUFFERED=1
            Write-Host "✅ Environment variables set!" -ForegroundColor Green
        }
        
        Write-Host "`n🚀 Deploying to Railway..." -ForegroundColor Cyan
        railway up
        
        Write-Host "`n✨ Deployment initiated!" -ForegroundColor Green
        Write-Host "Check Railway dashboard for build progress." -ForegroundColor Cyan
    }
} else {
    Write-Host "`n📱 Deploy via Web Interface:" -ForegroundColor Cyan
    Write-Host "1. Visit: https://railway.app/new" -ForegroundColor Yellow
    Write-Host "2. Click Deploy from GitHub repo" -ForegroundColor Yellow
    Write-Host "3. Select your repository" -ForegroundColor Yellow
    Write-Host "4. Add environment variable: CEREBRAS_API_KEY" -ForegroundColor Yellow
    Write-Host "5. Deploy!" -ForegroundColor Yellow
}

# Configuration checklist
Write-Host "`n✅ Deployment Checklist:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "□ Code pushed to GitHub" -ForegroundColor Yellow
Write-Host "□ Cerebras API key ready" -ForegroundColor Yellow
Write-Host "□ Railway account created" -ForegroundColor Yellow
Write-Host "□ Repository connected in Railway" -ForegroundColor Yellow
Write-Host "□ Environment variables configured" -ForegroundColor Yellow
Write-Host "□ Deployment initiated" -ForegroundColor Yellow

# Show next steps
Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "- Quick Start: QUICKSTART.md" -ForegroundColor Gray
Write-Host "- Full Guide: RAILWAY_DEPLOYMENT.md" -ForegroundColor Gray
Write-Host "- Cerebras API: https://cerebras.ai/api" -ForegroundColor Gray

Write-Host "`n🎉 Good luck with your deployment!" -ForegroundColor Green
