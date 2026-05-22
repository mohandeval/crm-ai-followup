@echo off
REM ─────────────────────────────────────────────────────────────
REM  git_setup.bat
REM  Run this ONCE from inside the crm-ai-followup folder
REM  to initialize git and make the first commit.
REM
REM  Usage:
REM    cd D:\AiCode\AICRMCode\crm-ai-followup
REM    scripts\git_setup.bat
REM ─────────────────────────────────────────────────────────────

echo === Initializing Git Repository ===
git init -b main
git config user.email "mohandeval@gmail.com"
git config user.name "Mohan"

echo === Adding all files ===
git add .

echo === Initial commit ===
git commit -m "feat: initial project skeleton — Phase 0 foundation

- Project structure: config, src/db, src/vector, src/agents, src/graph, src/utils, scripts, tests
- PostgreSQL connection module (psycopg2 + SQLAlchemy)
- Pinecone Serverless client stub
- requirements.txt with all dependencies
- .env.example with all required keys
- test_connections.py health check script"

echo.
echo === Done! Next steps: ===
echo 1. Create a repo on GitHub: https://github.com/new
echo 2. Run: git remote add origin https://github.com/YOUR_USERNAME/crm-ai-followup.git
echo 3. Run: git push -u origin main
echo.
pause
