import os
import json
import threading
import time
import io
import shutil
import webbrowser
import sys
from datetime import datetime

# Ghi lai loi neu co
def log_error(e):
    try:
        with open("crash.log", "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now()}] ERROR: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
            f.write("\n" + "="*50 + "\n")
    except: pass

try:
    import requests
    from PIL import Image, ImageTk
    import customtkinter as ctk
    import yt_dlp
    from tkinter import filedialog, messagebox
except ImportError as e:
    log_error(e)
    print(f"Lỗi: Thiếu thư viện. Vui lòng chạy run.bat để cài đặt: {e}")
    sys.exit(1)

# Chế độ: "System" (Mặc định), "Dark", "Light"
ctk.set_appearance_mode("System")
# Chủ đề màu: "blue" (Mặc định), "green", "dark-blue"
ctk.set_default_color_theme("blue")

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Cấu hình cửa sổ ---
        self.title("YT-D")
        self.geometry("1000x700")
        self.minsize(950, 680)
        
        # --- Khởi tạo dữ liệu ---
        self.history_file = "history.json"
        self.config_file = "config.json"
        self.last_update_time = 0
        self.ffmpeg_available = False
        self.history = self.load_history()
        self.save_dir = self.load_config()
        self._thumbnail_image_ref = None

        # --- Bố cục chính (Sidebar + Content) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR (Navigation & Options)
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(15, weight=1) # Spacer

        self.logo_label = ctk.CTkLabel(self.sidebar, text="📥", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=30, pady=(40, 30), sticky="w")

        self.setup_sidebar_widgets()

        # 2. MAIN CONTENT AREA
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=35, pady=(35, 10))
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(3, weight=1)

        # Tiêu đề & Lời chào
        self.welcome_label = ctk.CTkLabel(self.main_container, text="Bắt đầu tải nội dung mới", font=ctk.CTkFont(size=28, weight="bold"))
        self.welcome_label.grid(row=0, column=0, sticky="w", pady=(0, 25))

        # --- Khu vực nhập URL ---
        self.setup_url_section()

        # --- Khu vực Xem trước thông tin ---
        self.setup_preview_section()

        # --- Danh sách tác vụ đang tải ---
        self.setup_tasks_section()

        # --- Thanh trạng thái & Thư mục lưu (Bottom) ---
        self.setup_bottom_bar()

        # Cài đặt ban đầu
        self.check_ffmpeg()
        self.bind("<FocusIn>", self.on_focus_in)

    def setup_sidebar_widgets(self):
        # --- CẤU HÌNH TẢI ---
        ctk.CTkLabel(self.sidebar, text="CẤU HÌNH TẢI", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=1, column=0, padx=30, pady=(10, 5), sticky="w")
        
        self.format_var = ctk.StringVar(value="Video (MP4)")
        self.format_combobox = ctk.CTkComboBox(self.sidebar, values=["Video (MP4)", "Âm thanh (MP3)"], variable=self.format_var, command=self.on_format_change, height=35)
        self.format_combobox.grid(row=2, column=0, padx=25, pady=10, sticky="ew")

        self.quality_var = ctk.StringVar(value="Tốt nhất (Khuyên dùng)")
        self.quality_combobox = ctk.CTkComboBox(self.sidebar, values=["Tốt nhất (Khuyên dùng)", "1080p", "720p", "480p", "360p"], variable=self.quality_var, height=35)
        self.quality_combobox.grid(row=3, column=0, padx=25, pady=10, sticky="ew")

        self.playlist_var = ctk.BooleanVar(value=False)
        self.playlist_switch = ctk.CTkSwitch(self.sidebar, text="Tải cả Playlist (nếu có)", variable=self.playlist_var)
        self.playlist_switch.grid(row=4, column=0, padx=30, pady=15, sticky="w")

        # --- Cookie/Hội viên ---
        ctk.CTkLabel(self.sidebar, text="DÙNG BROWSER COOKIE", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=5, column=0, padx=30, pady=(20, 5), sticky="w")
        self.cookie_var = ctk.StringVar(value="Không dùng")
        self.cookie_combobox = ctk.CTkComboBox(self.sidebar, values=["Không dùng", "chrome", "edge", "firefox", "brave", "opera", "vivaldi"], variable=self.cookie_var, height=35)
        self.cookie_combobox.grid(row=6, column=0, padx=25, pady=10, sticky="ew")

        # --- Quản lý ---
        ctk.CTkLabel(self.sidebar, text="CÔNG CỤ", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=7, column=0, padx=30, pady=(20, 5), sticky="w")
        self.history_button = ctk.CTkButton(self.sidebar, text="📜 Lịch sử tải", height=35, fg_color="transparent", border_width=1, anchor="w", command=self.open_history_window)
        self.history_button.grid(row=8, column=0, padx=25, pady=10, sticky="ew")

        self.ffmpeg_button = ctk.CTkButton(self.sidebar, text="⚙️ Tải FFmpeg", height=35, fg_color="transparent", border_width=1, anchor="w", command=self.open_ffmpeg_download_page)
        self.ffmpeg_button.grid(row=9, column=0, padx=25, pady=10, sticky="ew")
        self.ffmpeg_button.configure(state="disabled")

        self.ffmpeg_notice_label = ctk.CTkLabel(self.sidebar, text="", text_color="orange", font=ctk.CTkFont(size=11), wraplength=220, justify="left")
        self.ffmpeg_notice_label.grid(row=14, column=0, padx=30, pady=20, sticky="s")

    def setup_url_section(self):
        self.url_section = ctk.CTkFrame(self.main_container, corner_radius=15, fg_color=("gray95", "#242424"), border_width=1, border_color=("gray85", "#333333"))
        self.url_section.grid(row=1, column=0, sticky="ew", pady=10)
        self.url_section.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(self.url_section, placeholder_text="Dán link YouTube hoặc nhập tên bài hát cần tìm...", height=55, border_width=0, fg_color="transparent", font=ctk.CTkFont(size=15))
        self.url_entry.grid(row=0, column=0, padx=(20, 10), pady=12, sticky="ew")

        self.preview_button = ctk.CTkButton(self.url_section, text="🔍 Kiểm tra", width=130, height=45, corner_radius=10, font=ctk.CTkFont(weight="bold"), command=self.preview_info)
        self.preview_button.grid(row=0, column=1, padx=20, pady=12)

    def setup_preview_section(self):
        self.preview_card = ctk.CTkFrame(self.main_container, corner_radius=15, height=180, fg_color=("white", "#2b2b2b"), border_width=1, border_color=("gray90", "#3d3d3d"))
        self.preview_card.grid(row=2, column=0, sticky="ew", pady=20)
        
        # Dung grid bên trong preview_card để an toàn hơn place
        self.preview_card.grid_columnconfigure(1, weight=1)
        self.preview_card.grid_columnconfigure(2, weight=0)

        # Thumbnail
        self.thumbnail_label = ctk.CTkLabel(self.preview_card, text="🎬", font=ctk.CTkFont(size=50), width=220, height=130, fg_color=("gray90", "#1e1e1e"), corner_radius=10)
        self.thumbnail_label.grid(row=0, column=0, rowspan=3, padx=25, pady=25)

        # Thông tin
        self.video_title_label = ctk.CTkLabel(self.preview_card, text="Thông tin video sẽ hiện ở đây", font=ctk.CTkFont(size=16, weight="bold"), anchor="w", justify="left")
        self.video_title_label.grid(row=0, column=1, sticky="w", pady=(30, 0))

        self.video_channel_label = ctk.CTkLabel(self.preview_card, text="Kênh: ---", text_color="gray", anchor="w")
        self.video_channel_label.grid(row=1, column=1, sticky="w", pady=(5, 0))

        self.video_duration_label = ctk.CTkLabel(self.preview_card, text="Thời lượng: ---", text_color="gray", anchor="w")
        self.video_duration_label.grid(row=2, column=1, sticky="w", pady=(5, 30))

        # Nút Tải chính
        self.download_button = ctk.CTkButton(self.preview_card, text="TẢI XUỐNG NGAY", width=180, height=50, corner_radius=25, font=ctk.CTkFont(size=14, weight="bold"), command=self.start_download)
        self.download_button.grid(row=0, column=2, rowspan=3, padx=25, sticky="e")

    def setup_tasks_section(self):
        self.tasks_header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.tasks_header_frame.grid(row=3, column=0, sticky="sw", pady=(20, 8))
        
        ctk.CTkLabel(self.tasks_header_frame, text="Danh sách đang tải", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        self.tasks_frame = ctk.CTkScrollableFrame(self.main_container, fg_color=("gray95", "#1e1e1e"), corner_radius=15, height=250)
        self.tasks_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))

    def setup_bottom_bar(self):
        self.bottom_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        self.bottom_bar.grid(row=1, column=1, sticky="ew", padx=35)
        
        self.dir_label = ctk.CTkLabel(self.bottom_bar, text=f"📂 {self.save_dir}", font=ctk.CTkFont(size=12), text_color="gray", cursor="hand2")
        self.dir_label.pack(side="left", pady=10)
        self.dir_label.bind("<Button-1>", lambda e: self.choose_directory())

        self.status_label = ctk.CTkLabel(self.bottom_bar, text="Sẵn sàng.", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.status_label.pack(side="right", pady=10)

        self.progress_bar = ctk.CTkProgressBar(self, height=4, corner_radius=0)
        self.progress_bar.place(relx=0.28, rely=0.99, relwidth=0.72)
        self.progress_bar.set(0)

    # --- LOGIC XỬ LÝ (GIỮ NGUYÊN VÀ KIỂM TRA LỖI) ---

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
                    if saved_dir and os.path.isdir(saved_dir): return saved_dir
            except Exception: pass
        return default_dir

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list): return data
            except Exception: pass
        return []

    def save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception: pass

    def add_history_entry(self, title, filename):
        if not filename: return
        entry = {
            "title": title or os.path.basename(filename),
            "file": os.path.abspath(filename),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.history.insert(0, entry)
        self.history = self.history[:200]
        self.save_history()

    def format_duration(self, seconds):
        if seconds is None: return "Không rõ"
        try:
            seconds = int(seconds)
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
        except Exception: return "Không rõ"

    def check_ffmpeg(self):
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        if self.ffmpeg_available:
            self.ffmpeg_notice_label.configure(text="✅ FFmpeg đã được cài đặt.", text_color="green")
            self.ffmpeg_button.configure(state="disabled")
        else:
            self.ffmpeg_notice_label.configure(text="⚠️ Cảnh báo: Thiếu FFmpeg. Tải video 1080p/MP3 có thể lỗi.")
            self.ffmpeg_button.configure(state="normal")

    def open_ffmpeg_download_page(self):
        try: webbrowser.open("https://ffmpeg.org/download.html")
        except: messagebox.showerror("Lỗi", "Vui lòng truy cập ffmpeg.org.")

    def clear_preview(self):
        self._thumbnail_image_ref = None
        self.thumbnail_label.configure(image=None, text="🎬")
        self.video_title_label.configure(text="Đang chờ kiểm tra...")
        self.video_channel_label.configure(text="Kênh: ---")
        self.video_duration_label.configure(text="Thời lượng: ---")

    def on_focus_in(self, event):
        try:
            clip = self.clipboard_get().strip()
            if clip and ("youtube.com" in clip.lower() or "youtu.be" in clip.lower()):
                current = self.url_entry.get().strip()
                if not current:
                    self.url_entry.delete(0, "end")
                    self.url_entry.insert(0, clip)
        except: pass

    def preview_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showinfo("Thiếu thông tin", "Vui lòng dán link hoặc nhập tên bài hát.")
            return

        search_mode = not (url.startswith("http") or url.startswith("www."))
        if search_mode: url = f"ytsearch1:{url}"

        self.update_status("Đang lấy thông tin...", "white")
        self.progress_bar.set(0)
        self.clear_preview()

        def worker():
            try:
                ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': not self.playlist_var.get()}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                first_entry = info['entries'][0] if info.get('_type') == 'playlist' and info.get('entries') else info
                title = first_entry.get('title', 'Không rõ')
                channel = first_entry.get('uploader') or first_entry.get('channel') or "Không rõ"
                duration_text = self.format_duration(first_entry.get('duration'))
                thumb_url = first_entry.get('thumbnails')[-1].get('url') if first_entry.get('thumbnails') else first_entry.get('thumbnail')

                img_ref = None
                if thumb_url:
                    try:
                        resp = requests.get(thumb_url, timeout=10)
                        pil_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                        pil_img.thumbnail((220, 130))
                        img_ref = ImageTk.PhotoImage(pil_img)
                    except: pass

                def on_ui():
                    if img_ref:
                        self._thumbnail_image_ref = img_ref
                        self.thumbnail_label.configure(image=self._thumbnail_image_ref, text="")
                    self.video_title_label.configure(text=title)
                    self.video_channel_label.configure(text=f"Kênh: {channel}")
                    
                    final_dur = f"Thời lượng: {duration_text}"
                    if info.get('_type') == 'playlist':
                        count = len(info.get('entries') or [])
                        if count: final_dur += f" | 📂 Playlist: {count} video"
                    self.video_duration_label.configure(text=final_dur)

                    if search_mode and first_entry.get('webpage_url'):
                        self.url_entry.delete(0, "end")
                        self.url_entry.insert(0, first_entry['webpage_url'])

                    self.update_status("Sẵn sàng tải.", "green")
                    self.progress_bar.set(0)

                self.after(0, on_ui)
            except Exception as e:
                self.after(0, self.update_status, f"Lỗi: {str(e)[:50]}...", "red")

        threading.Thread(target=worker, daemon=True).start()

    def create_task_ui(self, title_display):
        frame = ctk.CTkFrame(self.tasks_frame, fg_color=("white", "#2b2b2b"), border_width=1, border_color=("gray90", "#333333"))
        frame.pack(fill="x", pady=6, padx=10)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 5))

        lbl = ctk.CTkLabel(header, text=title_display[:60]+"..." if len(title_display)>60 else title_display, font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        lbl.pack(side="left", fill="x", expand=True)

        stop = ctk.CTkButton(header, text="✕", width=28, height=28, corner_radius=14, fg_color="transparent", hover_color="#cc3300", text_color=("black", "white"), command=lambda: self.remove_task(task))
        stop.pack(side="right")

        status = ctk.CTkLabel(frame, text="Đang chờ...", font=ctk.CTkFont(size=11), text_color="gray")
        status.pack(anchor="w", padx=15, pady=(0, 5))

        bar = ctk.CTkProgressBar(frame, height=8, corner_radius=4)
        bar.pack(fill="x", padx=15, pady=(0, 15))
        bar.set(0)

        task = {"frame": frame, "status_label": status, "bar": bar, "cancelled": False}
        return task

    def remove_task(self, task):
        task["cancelled"] = True
        try: task["frame"].destroy()
        except: pass
        self.progress_bar.set(0)
        self.update_status("Sẵn sàng.", "gray")

    def open_history_window(self):
        if not self.history:
            messagebox.showinfo("Lịch sử tải", "Chưa có mục tải nào.")
            return
        win = ctk.CTkToplevel(self)
        win.title("Lịch sử tải")
        win.geometry("800x500")
        win.after(100, lambda: win.focus()) # Fix focus
        
        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        for entry in self.history:
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", pady=6, padx=10)
            ctk.CTkLabel(row, text=f"{entry.get('time', '')} - {entry.get('title', '')}", anchor="w", justify="left").pack(side="left", fill="x", expand=True, padx=15)
            file_path = entry.get("file")
            ctk.CTkButton(row, text="Mở file", width=90, command=lambda p=file_path: os.startfile(p) if os.path.exists(p) else messagebox.showerror("Lỗi", "File không tồn tại")).pack(side="right", padx=10, pady=10)

    def choose_directory(self):
        dir_path = filedialog.askdirectory(initialdir=self.save_dir)
        if dir_path:
            self.save_dir = dir_path
            self.dir_label.configure(text=f"📂 {self.save_dir}")
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump({"save_dir": self.save_dir}, f, ensure_ascii=False, indent=4)
            except: pass

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total
                current_time = time.time()
                if current_time - self.last_update_time > 0.1 or percent >= 1.0:
                    self.last_update_time = current_time
                    self.after(0, self.update_progress, percent, f"{d.get('_percent_str', 'N/A')} • {d.get('_speed_str', 'N/A')}")
        elif d['status'] == 'finished':
            self.after(0, self.update_status, "Đang xử lý/Ghép file...", "orange")

    def update_progress(self, percent, text):
        self.progress_bar.set(percent)
        self.status_label.configure(text=f"Đang tải: {text}", text_color="#1f538d")

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def download_thread(self, url, is_audio, browser_cookie, quality, task_ui):
        def task_hook(d):
            if task_ui.get("cancelled"): raise Exception("Cancelled")
            if d.get("status") == "downloading":
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total:
                    p = d.get('downloaded_bytes', 0) / total
                    self.after(0, lambda: [task_ui["bar"].set(p), task_ui["status_label"].configure(text=f"{d.get('_percent_str')} • Tốc độ: {d.get('_speed_str')}")])
                try: self.progress_hook(d)
                except: pass
            elif d.get("status") == "finished":
                self.after(0, lambda: [task_ui["bar"].set(1), task_ui["status_label"].configure(text="✅ Hoàn tất!", text_color="green"), self.add_history_entry(d.get("info_dict", {}).get("title") or url, d.get("filename"))])

        try:
            ydl_opts = {'outtmpl': os.path.join(self.save_dir, '%(title)s.%(ext)s'), 'progress_hooks': [task_hook], 'noplaylist': not self.playlist_var.get()}
            if browser_cookie != "Không dùng": ydl_opts['cookiesfrombrowser'] = (browser_cookie,)
            
            if is_audio:
                bitrate = quality.split()[0] if quality[0].isdigit() else "320"
                ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': bitrate}]})
            else:
                res = ''.join(c for c in quality if c.isdigit())
                if res: ydl_opts['format'] = f'bestvideo[ext=mp4][height<={res}]+bestaudio[ext=m4a]/best[ext=mp4][height<={res}]/best'
                else: ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
            self.after(0, self.update_status, "Tải xuống hoàn tất!", "green")
            self.after(0, self.progress_bar.set, 1)
        except Exception as e:
            if not task_ui.get("cancelled"): self.after(0, self.update_status, f"Lỗi: {str(e)[:50]}", "red")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url: return
        if not url.startswith("http"): url = f"ytsearch1:{url}"
        
        is_audio = "Âm thanh" in self.format_var.get()
        quality = self.quality_var.get()
        task_ui = self.create_task_ui(self.url_entry.get().strip() or url)
        threading.Thread(target=self.download_thread, args=(url, is_audio, self.cookie_var.get(), quality, task_ui), daemon=True).start()

if __name__ == "__main__":
    try:
        app = YouTubeDownloaderApp()
        app.mainloop()
    except Exception as e:
        log_error(e)
        print(f"Ứng dụng gặp lỗi khi khởi động. Chi tiết đã được ghi vào crash.log")
        input("Nhấn Enter để thoát...")
