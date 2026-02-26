import os
import json
import threading
import time
import io
import shutil
import webbrowser
from datetime import datetime

import requests
from PIL import Image, ImageTk
import customtkinter as ctk
import yt_dlp
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("System")  # Chế độ: "System" (Mặc định), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Chủ đề màu: "blue" (Mặc định), "green", "dark-blue"

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Trình Tải YouTube Cá Nhân")
        self.geometry("750x650")
        self.minsize(650, 550)
        self.last_update_time = 0
        self.ffmpeg_available = False
        self.history_file = "history.json"
        self.history = self.load_history()
        
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
        self.bind("<FocusIn>", self.on_focus_in)

        # Nút xem trước thông tin
        self.preview_button = ctk.CTkButton(self.url_frame, text="Xem thông tin", width=120, command=self.preview_info)
        self.preview_button.pack(anchor="e", pady=(0, 10))

        # Khung hiển thị thông tin & thumbnail
        self.preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.preview_frame.pack(pady=5, padx=20, fill="x")

        self.thumbnail_label = ctk.CTkLabel(self.preview_frame, text="")
        self.thumbnail_label.grid(row=0, column=0, rowspan=3, padx=(0, 10), pady=5, sticky="w")

        self.video_title_label = ctk.CTkLabel(self.preview_frame, text="", anchor="w", justify="left")
        self.video_title_label.grid(row=0, column=1, sticky="w")

        self.video_channel_label = ctk.CTkLabel(self.preview_frame, text="", anchor="w", justify="left")
        self.video_channel_label.grid(row=1, column=1, sticky="w")

        self.video_duration_label = ctk.CTkLabel(self.preview_frame, text="", anchor="w", justify="left")
        self.video_duration_label.grid(row=2, column=1, sticky="w")

        self._thumbnail_image_ref = None
        
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

        # Công tắc tải playlist
        self.playlist_var = ctk.BooleanVar(value=False)
        self.playlist_switch = ctk.CTkSwitch(self.options_frame, text="Tải cả Playlist (nếu có)", variable=self.playlist_var)
        self.playlist_switch.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Khung tiến trình
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(self.progress_frame, text="Sẵn sàng.", font=ctk.CTkFont(size=13))
        self.status_label.pack(anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        # Vùng danh sách các tác vụ tải (đa luồng)
        self.tasks_label = ctk.CTkLabel(self, text="Danh sách tải:", font=ctk.CTkFont(size=14, weight="bold"))
        self.tasks_label.pack(anchor="w", padx=20, pady=(0, 5))

        self.tasks_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=200)
        self.tasks_frame.pack(fill="both", expand=True, padx=20)
        
        # Nút Tải
        self.download_button = ctk.CTkButton(self, text="TẢI XUỐNG", command=self.start_download, font=ctk.CTkFont(size=16, weight="bold"), height=40)
        self.download_button.pack(pady=(10, 5))

        # Nút lịch sử
        self.history_button = ctk.CTkButton(self, text="Lịch sử tải", command=self.open_history_window, height=32)
        self.history_button.pack(pady=(0, 10))

        # Cảnh báo FFmpeg (nếu cần)
        self.ffmpeg_notice_label = ctk.CTkLabel(self, text="", text_color="orange", wraplength=680, justify="left")
        self.ffmpeg_notice_label.pack(pady=(0, 5), padx=20, anchor="w")

        self.ffmpeg_button = ctk.CTkButton(self, text="Tải FFmpeg", command=self.open_ffmpeg_download_page, height=28)
        self.ffmpeg_button.pack(pady=(0, 10))
        self.ffmpeg_button.configure(state="disabled")

        # Kiểm tra FFmpeg khi khởi động
        self.check_ffmpeg()
        
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

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
        return []

    def save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def add_history_entry(self, title, filename):
        if not filename:
            return
        entry = {
            "title": title or os.path.basename(filename),
            "file": os.path.abspath(filename),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.history.insert(0, entry)
        # Giới hạn lịch sử, ví dụ 200 mục gần nhất
        self.history = self.history[:200]
        self.save_history()

    def format_duration(self, seconds):
        if seconds is None:
            return "Thời lượng: Không rõ"
        try:
            seconds = int(seconds)
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            if h > 0:
                return f"Thời lượng: {h:02d}:{m:02d}:{s:02d}"
            return f"Thời lượng: {m:02d}:{s:02d}"
        except Exception:
            return "Thời lượng: Không rõ"

    def check_ffmpeg(self):
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        if self.ffmpeg_available:
            self.ffmpeg_notice_label.configure(text="FFmpeg đã được phát hiện. Bạn có thể tải video chất lượng cao và chuyển đổi MP3.")
            self.ffmpeg_button.configure(state="disabled")
        else:
            self.ffmpeg_notice_label.configure(
                text="Không tìm thấy FFmpeg trên hệ thống. Một số định dạng/độ phân giải cao và chuyển đổi MP3 cần FFmpeg để hoạt động ổn định."
            )
            self.ffmpeg_button.configure(state="normal")

    def open_ffmpeg_download_page(self):
        try:
            webbrowser.open("https://ffmpeg.org/download.html")
        except Exception:
            messagebox.showerror("Lỗi", "Không thể mở trang tải FFmpeg. Vui lòng truy cập ffmpeg.org bằng trình duyệt của bạn.")

    def clear_preview(self):
        self._thumbnail_image_ref = None
        self.thumbnail_label.configure(image=None, text="")
        self.video_title_label.configure(text="")
        self.video_channel_label.configure(text="")
        self.video_duration_label.configure(text="")

    def on_focus_in(self, event):
        # Tự động bắt link từ clipboard nếu là link YouTube
        try:
            clip = self.clipboard_get().strip()
        except Exception:
            clip = ""
        if not clip:
            return
        lower = clip.lower()
        is_youtube = (
            lower.startswith("http")
            and ("youtube.com" in lower or "youtu.be" in lower)
        )
        if is_youtube:
            current = self.url_entry.get().strip()
            if not current:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, clip)

    def preview_info(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showinfo("Thiếu thông tin", "Vui lòng dán link hoặc nhập tên bài hát trước khi xem thông tin.")
            return

        # Hỗ trợ tìm kiếm theo tên bài hát
        search_mode = False
        if not url.startswith("http") and not url.startswith("www."):
            url = f"ytsearch1:{url}"
            search_mode = True

        self.update_status("Đang lấy thông tin video...", "white")
        self.progress_bar.set(0)
        self.clear_preview()

        def worker():
            try:
                ydl_opts = {
                    'quiet': True,
                    'skip_download': True,
                    'noplaylist': not self.playlist_var.get(),
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                # Nếu là kết quả tìm kiếm, info có thể là một dict chứa 'entries'
                if info.get('_type') == 'playlist' and info.get('entries'):
                    first_entry = info['entries'][0]
                else:
                    first_entry = info

                title = first_entry.get('title', 'Không rõ tiêu đề')
                channel = first_entry.get('uploader') or first_entry.get('channel') or "Không rõ kênh"
                duration_text = self.format_duration(first_entry.get('duration'))
                thumb_url = None

                # Thử lấy thumbnail tốt nhất
                if first_entry.get('thumbnails'):
                    thumb_url = first_entry['thumbnails'][-1].get('url')
                else:
                    thumb_url = first_entry.get('thumbnail')

                img_ref = None
                if thumb_url:
                    try:
                        resp = requests.get(thumb_url, timeout=10)
                        resp.raise_for_status()
                        img_data = resp.content
                        pil_img = Image.open(io.BytesIO(img_data)).convert("RGB")
                        pil_img.thumbnail((160, 90))
                        img_ref = ImageTk.PhotoImage(pil_img)
                    except Exception:
                        img_ref = None

                def on_ui():
                    if img_ref is not None:
                        self._thumbnail_image_ref = img_ref
                        self.thumbnail_label.configure(image=self._thumbnail_image_ref, text="")
                    else:
                        self.clear_preview()
                    self.video_title_label.configure(text=f"Tiêu đề: {title}")
                    self.video_channel_label.configure(text=f"Kênh: {channel}")
                    self.video_duration_label.configure(text=duration_text)

                    # Nếu là playlist, hiển thị số lượng video
                    if info.get('_type') == 'playlist':
                        count = len(info.get('entries') or [])
                        if count:
                            self.video_duration_label.configure(
                                text=f"{duration_text} | Playlist: {count} video"
                            )

                    if search_mode:
                        # Gán lại URL chính xác cho ô nhập
                        real_url = first_entry.get('webpage_url')
                        if real_url:
                            self.url_entry.delete(0, "end")
                            self.url_entry.insert(0, real_url)

                    self.update_status("Đã lấy thông tin xong, sẵn sàng tải.", "green")
                    self.progress_bar.set(0)

                self.after(0, on_ui)
            except Exception as e:
                err = str(e)
                self.after(0, self.clear_preview)
                self.after(0, self.update_status, f"Lỗi khi lấy thông tin: {err}", "red")

        threading.Thread(target=worker, daemon=True).start()

    def create_task_ui(self, title_display):
        frame = ctk.CTkFrame(self.tasks_frame)
        frame.pack(fill="x", pady=4)

        title_label = ctk.CTkLabel(frame, text=title_display, anchor="w", justify="left")
        title_label.pack(anchor="w", padx=5, pady=(3, 0))

        status_label = ctk.CTkLabel(frame, text="Đang chờ bắt đầu...", anchor="w", justify="left", font=ctk.CTkFont(size=12))
        status_label.pack(anchor="w", padx=5)

        bar = ctk.CTkProgressBar(frame)
        bar.pack(fill="x", padx=5, pady=(0, 5))
        bar.set(0)

        return {
            "frame": frame,
            "title_label": title_label,
            "status_label": status_label,
            "bar": bar,
        }

    def open_history_window(self):
        if not self.history:
            messagebox.showinfo("Lịch sử tải", "Chưa có mục tải nào được lưu.")
            return

        win = ctk.CTkToplevel(self)
        win.title("Lịch sử tải")
        win.geometry("700x400")

        frame = ctk.CTkScrollableFrame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        for entry in self.history:
            row = ctk.CTkFrame(frame)
            row.pack(fill="x", pady=4)

            info_text = f"{entry.get('time', '')} - {entry.get('title', '')}"
            info_label = ctk.CTkLabel(row, text=info_text, anchor="w", justify="left")
            info_label.pack(side="left", fill="x", expand=True, padx=5)

            file_path = entry.get("file")

            open_btn = ctk.CTkButton(row, text="Mở file", width=80, command=lambda p=file_path: self.open_file(p))
            open_btn.pack(side="right", padx=5)

            folder_btn = ctk.CTkButton(row, text="Mở thư mục", width=100, command=lambda p=file_path: self.open_folder(p))
            folder_btn.pack(side="right", padx=5)

    def open_file(self, path):
        if not path or not os.path.exists(path):
            messagebox.showerror("Lỗi", "File không tồn tại nữa.")
            return
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở file: {e}")

    def open_folder(self, path):
        if not path or not os.path.exists(path):
            messagebox.showerror("Lỗi", "File không tồn tại nữa.")
            return
        folder = os.path.dirname(path)
        try:
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {e}")

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

                    # Thông tin playlist (nếu có)
                    playlist_index = d.get('info_dict', {}).get('playlist_index')
                    playlist_count = d.get('info_dict', {}).get('n_entries')
                    playlist_text = ""
                    if playlist_index and playlist_count:
                        playlist_text = f" | Video {playlist_index}/{playlist_count}"
                    
                    # Throttle UI updates to prevent UI from freezing
                    current_time = time.time()
                    if current_time - getattr(self, "last_update_time", 0) > 0.1 or percent >= 1.0:
                        self.last_update_time = current_time
                        self.after(0, self.update_progress, percent, percent_str + playlist_text, speed_str)
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.after(0, self.update_status, "Đang xử lý/Ghép file... (Vui lòng đợi)\nLưu ý: yt-dlp cần FFmpeg để xử lý video chất lượng cao.", "orange")

    def update_progress(self, percent, percent_str, speed_str):
        self.progress_bar.set(percent)
        self.status_label.configure(text=f"Đang tải... {percent_str} (Tốc độ: {speed_str})", text_color="#1f538d")

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def download_thread(self, url, is_audio, browser_cookie, quality, task_ui):
        def task_hook(d):
            status = d.get("status")
            info = d.get("info_dict") or {}
            title = info.get("title") or url

            if status == "downloading":
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if not total_bytes:
                    return
                percent = downloaded / total_bytes
                percent_str = d.get('_percent_str', 'N/A')
                speed_str = d.get('_speed_str', 'N/A')

                playlist_index = info.get('playlist_index')
                playlist_count = info.get('n_entries')
                playlist_text = ""
                if playlist_index and playlist_count:
                    playlist_text = f" | Video {playlist_index}/{playlist_count}"

                def ui_update():
                    task_ui["bar"].set(percent)
                    task_ui["status_label"].configure(
                        text=f"{percent_str}{playlist_text} (Tốc độ: {speed_str})"
                    )
                self.after(0, ui_update)

                # Cập nhật thanh tổng quan
                try:
                    self.progress_hook(d)
                except Exception:
                    pass

            elif status == "finished":
                filename = d.get("filename")
                def ui_finish():
                    task_ui["bar"].set(1)
                    task_ui["status_label"].configure(text="Hoàn tất!")
                    self.add_history_entry(title, filename)
                self.after(0, ui_finish)

        try:
            ydl_opts = {
                'outtmpl': os.path.join(self.save_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [task_hook],
                'noplaylist': not self.playlist_var.get(),
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

        # Cảnh báo nếu thiếu FFmpeg mà chọn chế độ cần xử lý
        if not self.ffmpeg_available and (is_audio or "1080" in quality_choice or "1440" in quality_choice or "Tốt nhất" in quality_choice):
            messagebox.showwarning(
                "Thiếu FFmpeg",
                "Bạn đang chọn định dạng/chất lượng cần FFmpeg (MP3 hoặc video trên 720p).\n"
                "Vui lòng cài FFmpeg để đảm bảo tải và ghép file không lỗi."
            )
        
        self.status_label.configure(text="Đang lấy thông tin.. Nếu dùng cookie, yt-dlp cần thời gian đọc trình duyệt!", text_color="white")
        self.progress_bar.set(0)

        # Tạo UI riêng cho tác vụ này
        task_title = self.url_entry.get().strip() or url
        task_ui = self.create_task_ui(task_title)

        # Chạy luồng riêng biệt để không làm đơ giao diện
        thread = threading.Thread(target=self.download_thread, args=(url, is_audio, browser_cookie, quality_choice, task_ui), daemon=True)
        thread.start()

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
