@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo ==============================================
echo Tool Tai Video/Audio YouTube - Kiem tra loi
echo ==============================================
echo.

:: Tim phuong thuc chay Python
set PY_CMD=
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set PY_CMD=python
    )
)

if "%PY_CMD%"=="" (
    echo [LOI] Khong tim thay Python tren he thong!
    pause
    exit /b
)

:: Tao venv
if not exist venv (
    echo [1/3] Dang tao moi truong ao...
    !PY_CMD! -m venv venv
)

:: Kich hoat va kiem tra
echo [2/3] Dang kich hoat moi truong ao...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo [3/3] Kiem tra va cai dat thu vien...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ==============================================
echo Dang khoi dong ung dung...
echo (Neu cua so bi dong ngay, hay kiem tra thong tin o day)
echo ==============================================
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo ==============================================
    echo [LOI] Ung dung da dung lai voi ma loi: %errorlevel%
    echo Vui long chup anh man hinh nay de duoc ho tro.
    echo ==============================================
    pause
) else (
    echo.
    echo Ung dung da dong binh thuong.
    pause
)

exit /b
