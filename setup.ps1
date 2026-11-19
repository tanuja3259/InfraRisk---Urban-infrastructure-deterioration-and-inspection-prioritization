# One-shot setup for InfraRisk (Windows PowerShell)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== Backend setup ==" -ForegroundColor Cyan
Set-Location "$root\backend"
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python ml\generate_sample_data.py
.\.venv\Scripts\python ml\train_deterioration.py

Write-Host "== Frontend setup ==" -ForegroundColor Cyan
Set-Location "$root\frontend"
npm install

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Terminal 1: cd backend; .\.venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"
Write-Host "Terminal 2: cd frontend; npm run dev"
Write-Host "Open http://localhost:5173"
