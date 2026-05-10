@echo off
setlocal

cd /d "%~dp0"

call .venv\Scripts\activate

taskkill /F /IM python.exe

del /f /q data\salesforce\objects\ContentDocumentLink\*.*
del /f /q data\salesforce\objects\ContentVersion\*.*
del /f /q data\salesforce\objects\ContentVersionData\*.*
del /f /q data\salesforce\objects\DownloadMaster__c\*.*
del /f /q data\salesforce\objects\DownloadMasterWork__c\*.*

del /f /q data\storage\logs\*.log
del /f /q data\storage\queue\accepted\*.json
del /f /q data\storage\queue\processing\*.json
del /f /q data\storage\queue\completed\*.json
del /f /q data\storage\queue\error\*.json


echo ============================================
echo   Starting storage_server (port 8080)
echo ============================================
start "storage_server" cmd /k uvicorn apps.storage_app.server.main:app --port 8080

REM 少し待つ
ping -n 2 127.0.0.1 >nul

echo ============================================
echo   Starting salesforce_server (port 8000)
echo ============================================
start "salesforce_server" cmd /k uvicorn apps.salesforce_app.server.main:app --port 8000

REM 少し待つ
ping -n 2 127.0.0.1 >nul

python -m run_send_data

echo ============================================
echo   Starting storage_worker
echo ============================================
start "storage_worker" cmd /k python -m apps.storage_app.client.worker_loop

echo ============================================
echo   All servers + worker started
echo ============================================

endlocal
