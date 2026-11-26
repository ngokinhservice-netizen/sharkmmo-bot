@echo off
title SHARK Telegram Bot & SePay Notifier
chcp 65001 >nul
cd /d "%~dp0"

echo ===================================================
echo     SHARK - SEPAY ALERT & QR PAYMENT BOT
echo ===================================================
echo.
echo Đang kiểm tra môi trường Python...
python --version
if errorlevel 1 (
    echo [LỖI] Không tìm thấy Python! Vui lòng cài Python 3.11+.
    pause
    exit /b
)

echo Đang khởi động SHARK SePay Webhook & Telegram Bot...
echo Bot Telegram: @sharklearningbot_bot
echo Webhook SePay: http://localhost:8000/api/v1/webhooks/sepay
echo.

set PYTHONPATH=.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
