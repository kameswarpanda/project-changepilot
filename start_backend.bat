@echo off
echo ===========================================================================
echo  Starting ChangePilot FastAPI Backend Server
echo ===========================================================================
cd /d %~dp0
call .\.venv\Scripts\activate.bat
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
