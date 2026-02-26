@echo off
echo Đang cài đặt thư viện đóng gói...
call venv\Scripts\activate
pip install pyinstaller

echo.
echo Đang tiến hành đóng gói ứng dụng (Tạo file EXE)...
echo Quá trình này có thể mất vài phút, vui lòng chờ...

pyinstaller --noconfirm --onefile --windowed --name "YouTubeDownloader" --add-data "venv/Lib/site-packages/customtkinter;customtkinter/" main.py

echo.
echo =======================================================
echo HOAN THANH! File EXE cua ban nam trong thu muc 'dist'.
echo =======================================================
pause
