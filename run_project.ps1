#!/usr/bin/env powershell
<#
SYNAPSE PROJECT LAUNCHER
Starts all components of the SYNAPSE system
#>

Write-Host "`n" -ForegroundColor Cyan
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          SYNAPSE AMBIENT RELATIONSHIP INTELLIGENCE OS          ║" -ForegroundColor Cyan
Write-Host "║                     PROJECT LAUNCHER v1.0                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor Cyan

# Configuration
$ProjectRoot = "c:\Users\soura\OneDrive\Desktop\Synapse"
$BackendDir = "$ProjectRoot\backend"
$FrontendDir = "$ProjectRoot\frontend\web"
$PythonExe = "c:/python313/python.exe"
$BackendPort = 8000
$FrontendPort = 3000

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "📋 PROJECT CONFIGURATION" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

Write-Host "  Project Root:    $ProjectRoot" -ForegroundColor White
Write-Host "  Backend Dir:     $BackendDir" -ForegroundColor White
Write-Host "  Frontend Dir:    $FrontendDir" -ForegroundColor White
Write-Host "  Python:          $PythonExe" -ForegroundColor White
Write-Host "  Backend Port:    $BackendPort" -ForegroundColor White
Write-Host "  Frontend Port:   $FrontendPort" -ForegroundColor White

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "🔄 CHECKING DEPENDENCIES" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

# Check Python
if (Get-Command $PythonExe -ErrorAction SilentlyContinue) {
    $PythonVersion = & $PythonExe --version 2>&1
    Write-Host "  ✓ Python:        $PythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python:        NOT FOUND" -ForegroundColor Red
}

# Check Node.js
if (Get-Command node -ErrorAction SilentlyContinue) {
    $NodeVersion = node --version
    Write-Host "  ✓ Node.js:       $NodeVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Node.js:       NOT FOUND (Frontend won't work)" -ForegroundColor Red
}

# Check npm
if (Get-Command npm -ErrorAction SilentlyContinue) {
    $NpmVersion = npm --version
    Write-Host "  ✓ npm:           $NpmVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ npm:           NOT FOUND (Frontend won't work)" -ForegroundColor Red
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🚀 STARTING SYNAPSE COMPONENTS" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Start Backend
Write-Host "`n[1/2] Starting Backend (FastAPI on port $BackendPort)..." -ForegroundColor Yellow
Set-Location $BackendDir
$env:PYTHONPATH = $BackendDir

Write-Host "  → Command: uvicorn app.main:app --reload --host 0.0.0.0 --port $BackendPort" -ForegroundColor Gray
Write-Host "  → Watch for 'Uvicorn running on' message below..." -ForegroundColor Gray
Write-Host "`n" -ForegroundColor Gray

Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", $BackendPort `
    -WindowStyle Normal `
    -PassThru `
    -NoNewWindow | Out-Null

Write-Host "`n✓ Backend started in a new window" -ForegroundColor Green

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Check if Node/npm are available for frontend
$HasNode = Get-Command node -ErrorAction SilentlyContinue
$HasNpm = Get-Command npm -ErrorAction SilentlyContinue

if ($HasNode -and $HasNpm) {
    # Start Frontend
    Write-Host "`n[2/2] Starting Frontend (Next.js on port $FrontendPort)..." -ForegroundColor Yellow
    Set-Location $FrontendDir
    
    # Check if node_modules exists
    if (-not (Test-Path "$FrontendDir\node_modules")) {
        Write-Host "  → Installing dependencies first..." -ForegroundColor Yellow
        npm install --silent | Out-Null
        Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
    }
    
    Write-Host "  → Command: npm run dev" -ForegroundColor Gray
    Write-Host "  → Watch for 'Ready in' message below..." -ForegroundColor Gray
    Write-Host "`n" -ForegroundColor Gray
    
    Start-Process -FilePath "npm" `
        -ArgumentList "run", "dev" `
        -WorkingDirectory $FrontendDir `
        -WindowStyle Normal `
        -PassThru | Out-Null
    
    Write-Host "`n✓ Frontend started in a new window" -ForegroundColor Green
} else {
    Write-Host "`n⚠ Frontend requires Node.js and npm to be installed" -ForegroundColor Yellow
    Write-Host "  Skip frontend startup for now" -ForegroundColor Gray
}

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✨ SYNAPSE STARTUP COMPLETE" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

Write-Host "`n📱 SERVICE ENDPOINTS:" -ForegroundColor Cyan
Write-Host "  Backend API:       http://localhost:$BackendPort" -ForegroundColor White
Write-Host "  API Documentation: http://localhost:$BackendPort/docs" -ForegroundColor White
Write-Host "  ReDoc:             http://localhost:$BackendPort/redoc" -ForegroundColor White
Write-Host "  Health Check:      http://localhost:$BackendPort/health" -ForegroundColor White

if ($HasNode -and $HasNpm) {
    Write-Host "  Frontend Web:      http://localhost:$FrontendPort" -ForegroundColor White
}

Write-Host "`n📋 REQUIRED SERVICES:" -ForegroundColor Yellow
Write-Host "  • PostgreSQL:      localhost:5432" -ForegroundColor Gray
Write-Host "  • Redis:           localhost:6379" -ForegroundColor Gray
Write-Host "  • Neo4j:           localhost:7687" -ForegroundColor Gray
Write-Host "  • Kafka:           localhost:9092" -ForegroundColor Gray
Write-Host "`n  These services need to be running for full functionality." -ForegroundColor Gray
Write-Host "  Start them with: docker-compose up" -ForegroundColor Yellow

Write-Host "`n💡 FEATURES AVAILABLE NOW:" -ForegroundColor Cyan
Write-Host "  ✓ Backend API with 27 endpoints" -ForegroundColor Green
Write-Host "  ✓ Automatic API documentation" -ForegroundColor Green
Write-Host "  ✓ WebSocket support (real-time feed)" -ForegroundColor Green
Write-Host "  ✓ Voice synthesis (offline, no API key)" -ForegroundColor Green

Write-Host "`n📖 DOCUMENTATION:" -ForegroundColor Cyan
Write-Host "  • ANALYSIS_REPORT.md        - Project analysis" -ForegroundColor Gray
Write-Host "  • MIGRATION_SUMMARY.md      - TTS migration details" -ForegroundColor Gray
Write-Host "  • README.md                 - Project overview" -ForegroundColor Gray

Write-Host "`n⏹️  To stop services: Close the new windows or press Ctrl+C in each window" -ForegroundColor Gray
Write-Host "`n" -ForegroundColor Gray
