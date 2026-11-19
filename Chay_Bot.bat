@echo off
title SHARKMMO Telegram Bot & Backend
chcp 65001 >nul
cd /d "%~dp0"

echo ===================================================
echo     SHARKMMO - HỆ SINH THÁI SẢN PHẨM MMO TỰ ĐỘNG
echo ===================================================
echo.
echo Đang kiểm tra môi trường Python...
python --version
if errorlevel 1 (
    echo [LỖI] Không tìm thấy Python! Vui lòng cài Python 3.11+.
    pause
    exit /b
)

echo Đang khởi động SHARKMMO Backend & Telegram Bot...
echo Bot Telegram: @sharkkmmo_ai
echo API Docs: http://localhost:8000/docs
echo.

set PYTHONPATH=.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
