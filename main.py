import os
import json
import threading
import time
import customtkinter as ctk
import yt_dlp
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("System")  # Chế độ: "System" (Mặc định), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Chủ đề màu: "blue" (Mặc định), "green", "dark-blue"

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Trình Tải YouTube Cá Nhân")
        self.geometry("650x550")
        self.minsize(500, 450)
        self.last_update_time = 0
        
        # Tiêu đề
        self.title_label = ctk.CTkLabel(self, text="Tải Video/Audio YouTube", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=20)
        
        # Khung nhập URL
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.url_frame.pack(pady=5, padx=20, fill="x")
        
        self.url_label = ctk.CTkLabel(self.url_frame, text="Đường dẫn (URL) HOẶC Tên bài hát:", font=ctk.CTkFont(size=14))
        self.url_label.pack(anchor="w")
        
        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text="Dán link YouTube hoặc nhập tên bài hát để tự tìm và tải...")
        self.url_entry.pack(fill="x", pady=(5, 10))
        
        # Khung tùy chọn
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(pady=5, padx=20, fill="x")
        
        # Grid config
        self.options_frame.columnconfigure(1, weight=1)
        
        # Định dạng
        self.format_label = ctk.CTkLabel(self.options_frame, text="Định dạng tải:")
        self.format_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.format_var = ctk.StringVar(value="Video (MP4)")
        self.format_combobox = ctk.CTkComboBox(self.options_frame, values=[
            "Video (MP4)", 
            "Âm thanh (MP3)"
        ], variable=self.format_var, command=self.on_format_change)
        self.format_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Chất lượng
        self.quality_label = ctk.CTkLabel(self.options_frame, text="Chất lượng:")
        self.quality_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.quality_var = ctk.StringVar(value="Tốt nhất (Khuyên dùng)")
        self.quality_combobox = ctk.CTkComboBox(self.options_frame, values=[
            "Tốt nhất (Khuyên dùng)",
            "1080p",
            "720p",
            "480p",
            "360p"
        ], variable=self.quality_var)
        self.quality_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Thư mục lưu
        self.config_file = "config.json"
        self.save_dir = self.load_config()
        
        self.dir_button = ctk.CTkButton(self.options_frame, text="Chọn Thư Mục", command=self.choose_directory, width=120)
        self.dir_button.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.dir_label = ctk.CTkLabel(self.options_frame, text=f"{self.save_dir}", text_color="gray")
        self.dir_label.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Trình duyệt (Cookies)
        self.cookie_label = ctk.CTkLabel(self.options_frame, text="Video Hội Viên (Cookie từ):")
        self.cookie_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        self.cookie_var = ctk.StringVar(value="Không dùng")
        self.cookie_combobox = ctk.CTkComboBox(self.options_frame, values=[
            "Không dùng", 
            "chrome", 
            "edge", 
            "firefox",
            "brave",
            "opera",
            "vivaldi"
        ], variable=self.cookie_var)
        self.cookie_combobox.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        
        # Khung tiến trình
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Sẵn sàng.", font=ctk.CTkFont(size=13))
        self.status_label.pack(anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)
        
        # Nút Tải
        self.download_button = ctk.CTkButton(self, text="TẢI XUỐNG", command=self.start_download, font=ctk.CTkFont(size=16, weight="bold"), height=40)
        self.download_button.pack(pady=15)
        
    def on_format_change(self, choice):
        if choice == "Âm thanh (MP3)":
            self.quality_combobox.configure(values=["320 kbps (Tốt nhất)", "256 kbps", "192 kbps (Tiêu chuẩn)", "128 kbps"])
            self.quality_var.set("320 kbps (Tốt nhất)")
        else:
            self.quality_combobox.configure(values=["Tốt nhất (Khuyên dùng)", "1440p", "1080p", "720p", "480p", "360p"])
            self.quality_var.set("Tốt nhất (Khuyên dùng)")
            
    def load_config(self):
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_dir = data.get("save_dir", "")
                    if saved_dir and os.path.isdir(saved_dir):
                        return saved_dir
            except Exception:
                pass
        return default_dir

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"save_dir": self.save_dir}, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def choose_directory(self):
        dir_path = filedialog.askdirectory(initialdir=self.save_dir)
        if dir_path:
            self.save_dir = dir_path
            self.dir_label.configure(text=self.save_dir)
            self.save_config()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Calculate progress
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if total_bytes:
                    percent = downloaded / total_bytes
                    percent_str = d.get('_percent_str', 'N/A')
                    speed_str = d.get('_speed_str', 'N/A')
                    
                    # Throttle UI updates to prevent UI from freezing
                    current_time = time.time()
                    if current_time - getattr(self, "last_update_time", 0) > 0.1 or percent >= 1.0:
                        self.last_update_time = current_time
                        self.after(0, self.update_progress, percent, percent_str, speed_str)
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.after(0, self.update_status, "Đang xử lý/Ghép file... (Vui lòng đợi)\nLưu ý: yt-dlp cần FFmpeg để xử lý video chất lượng cao.", "orange")

    def update_progress(self, percent, percent_str, speed_str):
        self.progress_bar.set(percent)
        self.status_label.configure(text=f"Đang tải... {percent_str} (Tốc độ: {speed_str})", text_color="#1f538d")

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def download_thread(self, url, is_audio, browser_cookie, quality):
        self.after(0, lambda: self.download_button.configure(state="disabled"))
        
        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.save_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'noplaylist': True,
                # Nếu không có ffmpeg, yt-dlp có thể báo lỗi nu cố ghép audio+video
                # Bạn cài thêm ffmpeg vào system path để yt-dlp hoạt động tốt nhất.
            }

            if browser_cookie != "Không dùng":
                ydl_opts['cookiesfrombrowser'] = (browser_cookie, )
            
            if is_audio:
                # Xử lý chọn bitrate cho âm thanh
                bitrate = "320"
                if "256" in quality: bitrate = "256"
                elif "192" in quality: bitrate = "192"
                elif "128" in quality: bitrate = "128"
                
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }]
            else:
                # Xử lý chọn độ phân giải video
                if quality == "Tốt nhất (Khuyên dùng)":
                    ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                else:
                    # Lọc lấy số (VD: 1080, 720)
                    res = ''.join([c for c in quality if c.isdigit()])
                    # Cú pháp yt-dlp: tải độ phân giải nhỏ hơn hoặc bằng res
                    ydl_opts['format'] = f'bestvideo[ext=mp4][height<={res}]+bestaudio[ext=m4a]/best[ext=mp4][height<={res}]/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            self.after(0, self.update_status, f"Tải xuống hoàn tất! Đã lưu tại:\n{self.save_dir}", "green")
            self.after(0, self.progress_bar.set, 1)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Lỗi: {error_msg}")
            self.after(0, self.update_status, f"Lỗi: {error_msg}", "red")
        finally:
            self.after(0, lambda: self.download_button.configure(state="normal"))

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng dán đường dẫn hoặc nhập tên bài hát cần tải!")
            return
            
        # Nếu người dùng nhập tên bài hát thay vì link, sử dụng ytsearch1: để tải kết quả tìm kiếm đầu tiên
        if not url.startswith("http") and not url.startswith("www."):
            url = f"ytsearch1:{url}"
            
        is_audio = "Âm thanh" in self.format_var.get()
        browser_cookie = self.cookie_var.get()
        quality_choice = self.quality_var.get()
        
        self.status_label.configure(text="Đang lấy thông tin.. Nếu dùng cookie, yt-dlp cần thời gian đọc trình duyệt!", text_color="white")
        self.progress_bar.set(0)
        
        # Chạy luồng riêng biệt để không làm đơ giao diện
        thread = threading.Thread(target=self.download_thread, args=(url, is_audio, browser_cookie, quality_choice), daemon=True)
        thread.start()

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
