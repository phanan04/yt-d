@echo off
setlocal
cd /d %~dp0

echo ==============================================
echo Dang chuan bi build file EXE cho YT-D...
echo ==============================================
echo.

:: Kich hoat moi truong ao neu co
if exist venv\Scripts\activate.bat (
    echo [1/3] Dang dung moi truong venv...
    call venv\Scripts\activate.bat
)

:: Cai dat PyInstaller neu chua co
echo [2/3] Dang kiem tra/cai dat PyInstaller...
python -m pip install pyinstaller

:: Chay PyInstaller
echo [3/3] Dang tien hanh đóng gói (Co the mat vai phut)...
echo.

:: --noconsole: Khong hien man hinh den khi mo app
:: --onefile: Dong goi tat ca vao 1 file duy nhat
:: --name: Ten file exe
:: --collect-all customtkinter: Dam bao giao dien hoat dong dung
pyinstaller --noconsole --onefile --name "YT-D" --collect-all customtkinter main.py

if %errorlevel% equ 0 (
    echo.
    echo ==============================================
    echo [THANH CONG] File EXE cua ban nam trong thu muc: dist
    echo ==============================================
) else (
    echo.
    echo [LOI] Co loi xay ra trong qua trinh build.
)

pause
exit /b
