@echo off
echo ==============================================
echo Tool Tai Video/Audio YouTube Ca Nhan
echo ==============================================
echo.

if not exist venv (
    echo [1/3] Dang tao moi truong ao...
    python -m venv venv
)

echo [2/3] Dang kich hoat moi truong ao...
call venv\Scripts\activate

echo [3/3] Dang kiem tra va cai dat thu vien...
pip install -r requirements.txt

echo.
echo ==============================================
echo Khoi dong ung dung...
echo ==============================================
python main.py
pause
