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

# Chế độ giao diện và màu chủ đề
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

LANG = {
    "vi": {
        "title": "YT-D",
        "welcome": "Bắt đầu tải nội dung mới",
        "url_placeholder": "Dán link YouTube hoặc nhập tên bài hát cần tìm...",
        "btn_check": "🔍 Kiểm tra",
        "btn_download": "TẢI XUỐNG NGAY",
        "preview_default": "Thông tin video sẽ hiện ở đây",
        "channel": "Kênh: ---",
        "duration": "Thời lượng: ---",
        "tasks_header": "Danh sách đang tải",
        "ready": "Sẵn sàng.",
        "section_config": "CẤU HÌNH TẢI",
        "fmt_video": "Video (MP4)",
        "fmt_audio": "Âm thanh (MP3)",
        "quality_best": "Tốt nhất (Khuyên dùng)",
        "quality_values_video": ["Tốt nhất (Khuyên dùng)", "1440p", "1080p", "720p", "480p", "360p"],
        "quality_values_audio": ["320 kbps (Tốt nhất)", "256 kbps", "192 kbps (Tiêu chuẩn)", "128 kbps"],
        "playlist_switch": "Tải cả Playlist (nếu có)",
        "from_video": "Từ video:",
        "to_video": "đến:",
        "to_placeholder": "cuối",
        "archive_switch": "⏭ Bỏ qua video đã tải",
        "concurrent_label": "Tải song song:",
        "concurrent_values": ["1 luồng", "4 luồng", "8 luồng", "16 luồng"],
        "concurrent_default": "4 luồng",
        "section_cookie": "DÙNG BROWSER COOKIE",
        "cookie_none": "Không dùng",
        "cookie_file_btn": "📄 Hoặc chọn file cookies.txt",
        "section_tools": "CÔNG CỤ",
        "btn_history": "📜 Lịch sử tải",
        "btn_ffmpeg": "⚙️ Tải FFmpeg",
        "btn_ytdlp": "🔄 Cập nhật yt-dlp",
        "btn_nodejs": "📦 Cài Node.js (tự động)",
        "history_title": "Lịch sử tải",
        "history_empty": "Chưa có mục tải nào.",
        "history_open": "Mở file",
        "checking": "Đang lấy thông tin...",
        "dl_ready": "Sẵn sàng tải.",
        "dl_done": "Tải xuống hoàn tất!",
        "dl_done_playlist": "✅ Tải xong! Đã tải {n} video",
        "dl_skipped": "(Bỏ qua {n} video lỗi)",
    },
    "en": {
        "title": "YT-D",
        "welcome": "Start downloading new content",
        "url_placeholder": "Paste YouTube link or enter song name...",
        "btn_check": "🔍 Check",
        "btn_download": "DOWNLOAD NOW",
        "preview_default": "Video info will appear here",
        "channel": "Channel: ---",
        "duration": "Duration: ---",
        "tasks_header": "Download queue",
        "ready": "Ready.",
        "section_config": "DOWNLOAD CONFIG",
        "fmt_video": "Video (MP4)",
        "fmt_audio": "Audio (MP3)",
        "quality_best": "Best (Recommended)",
        "quality_values_video": ["Best (Recommended)", "1440p", "1080p", "720p", "480p", "360p"],
        "quality_values_audio": ["320 kbps (Best)", "256 kbps", "192 kbps (Standard)", "128 kbps"],
        "playlist_switch": "Download full Playlist",
        "from_video": "From:",
        "to_video": "To:",
        "to_placeholder": "end",
        "archive_switch": "⏭ Skip already downloaded",
        "concurrent_label": "Parallel streams:",
        "concurrent_values": ["1 stream", "4 streams", "8 streams", "16 streams"],
        "concurrent_default": "4 streams",
        "section_cookie": "BROWSER COOKIE",
        "cookie_none": "None",
        "cookie_file_btn": "📄 Or choose cookies.txt file",
        "section_tools": "TOOLS",
        "btn_history": "📜 Download history",
        "btn_ffmpeg": "⚙️ Download FFmpeg",
        "btn_ytdlp": "🔄 Update yt-dlp",
        "btn_nodejs": "📦 Install Node.js (auto)",
        "history_title": "Download history",
        "history_empty": "No downloads yet.",
        "history_open": "Open file",
        "checking": "Fetching info...",
        "dl_ready": "Ready to download.",
        "dl_done": "Download complete!",
        "dl_done_playlist": "✅ Done! Downloaded {n} videos",
        "dl_skipped": "(Skipped {n} errors)",
    },
}

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
        self.save_dir, self.cookie_file_path = self.load_config()
        self._thumbnail_image_ref = None

        # Ngôn ngữ — load trước khi tạo UI
        self.lang = "vi"
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as _f:
                    if json.load(_f).get("lang") == "en":
                        self.lang = "en"
            except Exception:
                pass

        # --- Bố cục chính (Sidebar + Content) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR
        self.sidebar = ctk.CTkScrollableFrame(self, width=260, corner_radius=0, fg_color=("gray92", "gray17"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="ew")
        self.logo_label.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.logo_label, text="📥", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w")
        _lang_btn_text = "🌐 VI" if self.lang == "en" else "🌐 EN"
        self.lang_button = ctk.CTkButton(
            self.logo_label, text=_lang_btn_text, width=54, height=28,
            corner_radius=14, fg_color="transparent", border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._toggle_lang
        )
        self.lang_button.grid(row=0, column=1, sticky="e")

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

        # Áp ngôn ngữ sau khi tất cả widget đã tạo
        self._apply_lang()

        # Cài đặt ban đầu
        self.check_ffmpeg()
        self.check_nodejs()
        # Khôi phục label cookie file nếu đã lưu
        if self.cookie_file_path and os.path.isfile(self.cookie_file_path):
            self.cookie_file_label.configure(text=f"✅ {os.path.basename(self.cookie_file_path)}")
            self.cookie_var.set("Không dùng")
        self.bind("<FocusIn>", self.on_focus_in)

    def setup_sidebar_widgets(self):
        # --- CẤU HÌNH TẢI ---
        self.lbl_section_config = ctk.CTkLabel(self.sidebar, text="CẤU HÌNH TẢI", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.lbl_section_config.grid(row=1, column=0, padx=30, pady=(10, 5), sticky="w")
        
        self.format_var = ctk.StringVar(value="Video (MP4)")
        self.format_combobox = ctk.CTkComboBox(self.sidebar, values=["Video (MP4)", "Âm thanh (MP3)"], variable=self.format_var, command=self.on_format_change, height=35)
        self.format_combobox.grid(row=2, column=0, padx=25, pady=10, sticky="ew")

        self.quality_var = ctk.StringVar(value="Tốt nhất (Khuyên dùng)")
        self.quality_combobox = ctk.CTkComboBox(self.sidebar, values=["Tốt nhất (Khuyên dùng)", "1080p", "720p", "480p", "360p"], variable=self.quality_var, height=35)
        self.quality_combobox.grid(row=3, column=0, padx=25, pady=10, sticky="ew")

        self.playlist_var = ctk.BooleanVar(value=False)
        self.playlist_switch = ctk.CTkSwitch(self.sidebar, text="Tải cả Playlist (nếu có)",
                                              variable=self.playlist_var, command=self._on_playlist_toggle)
        self.playlist_switch.grid(row=4, column=0, padx=30, pady=(15, 5), sticky="w")

        # --- Playlist range (ẩn khi tắt playlist) ---
        self.playlist_range_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.playlist_range_frame.grid(row=5, column=0, padx=25, pady=(0, 10), sticky="ew")
        self.playlist_range_frame.grid_columnconfigure(1, weight=1)
        self.playlist_range_frame.grid_columnconfigure(3, weight=1)
        self.lbl_from_video = ctk.CTkLabel(self.playlist_range_frame, text="Từ video:", font=ctk.CTkFont(size=11))
        self.lbl_from_video.grid(row=0, column=0, padx=(5, 4), sticky="w")
        self.playlist_start_var = ctk.StringVar(value="1")
        self.playlist_start_entry = ctk.CTkEntry(self.playlist_range_frame, textvariable=self.playlist_start_var,
                                                  width=55, height=28, justify="center")
        self.playlist_start_entry.grid(row=0, column=1, padx=(0, 8), sticky="ew")
        self.lbl_to_video = ctk.CTkLabel(self.playlist_range_frame, text="đến:", font=ctk.CTkFont(size=11))
        self.lbl_to_video.grid(row=0, column=2, padx=(0, 4), sticky="w")
        self.playlist_end_var = ctk.StringVar(value="")
        self.playlist_end_entry = ctk.CTkEntry(self.playlist_range_frame, textvariable=self.playlist_end_var,
                                                width=55, height=28, justify="center",
                                                placeholder_text="cuối")
        self.playlist_end_entry.grid(row=0, column=3, sticky="ew")
        self.playlist_range_frame.grid_remove()  # ẩn mặc định

        # Bỏ qua video đã tải
        self.archive_var = ctk.BooleanVar(value=True)
        self.archive_switch = ctk.CTkSwitch(self.sidebar, text="⏭ Bỏ qua video đã tải",
                                            variable=self.archive_var)
        self.archive_switch.grid(row=6, column=0, padx=30, pady=(5, 5), sticky="w")

        # Tải song song (concurrent_fragments)
        concurrent_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        concurrent_frame.grid(row=7, column=0, padx=25, pady=(0, 10), sticky="ew")
        concurrent_frame.grid_columnconfigure(1, weight=1)
        self.lbl_concurrent = ctk.CTkLabel(concurrent_frame, text="Tải song song:", font=ctk.CTkFont(size=11))
        self.lbl_concurrent.grid(row=0, column=0, padx=(5, 8), sticky="w")
        self.concurrent_var = ctk.StringVar(value="4 luồng")
        self.concurrent_combobox = ctk.CTkComboBox(concurrent_frame, values=["1 luồng", "4 luồng", "8 luồng", "16 luồng"],
                        variable=self.concurrent_var, height=28)
        self.concurrent_combobox.grid(row=0, column=1, sticky="ew")

        # --- Cookie/Hội viên ---
        self.lbl_section_cookie = ctk.CTkLabel(self.sidebar, text="DÙNG BROWSER COOKIE", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.lbl_section_cookie.grid(row=8, column=0, padx=30, pady=(20, 5), sticky="w")
        self.cookie_var = ctk.StringVar(value="Không dùng")
        self.cookie_combobox = ctk.CTkComboBox(self.sidebar, values=["Không dùng", "chrome", "edge", "firefox", "brave", "opera", "vivaldi"], variable=self.cookie_var, height=35)
        self.cookie_combobox.grid(row=9, column=0, padx=25, pady=10, sticky="ew")

        self.cookie_file_button = ctk.CTkButton(self.sidebar, text="📄 Hoặc chọn file cookies.txt", height=32, fg_color="transparent", border_width=1, anchor="w", font=ctk.CTkFont(size=11), command=self.choose_cookie_file)
        self.cookie_file_button.grid(row=10, column=0, padx=25, pady=(0, 5), sticky="ew")

        self.cookie_file_label = ctk.CTkLabel(self.sidebar, text="", text_color="#4A9EFF", font=ctk.CTkFont(size=10), wraplength=220, justify="left", anchor="w")
        self.cookie_file_label.grid(row=11, column=0, padx=28, pady=(0, 5), sticky="w")

        # --- Quản lý ---
        self.lbl_section_tools = ctk.CTkLabel(self.sidebar, text="CÔNG CỤ", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.lbl_section_tools.grid(row=12, column=0, padx=30, pady=(15, 5), sticky="w")
        self.history_button = ctk.CTkButton(self.sidebar, text="📜 Lịch sử tải", height=35, fg_color="transparent", border_width=1, anchor="w", command=self.open_history_window)
        self.history_button.grid(row=13, column=0, padx=25, pady=10, sticky="ew")

        self.ffmpeg_button = ctk.CTkButton(self.sidebar, text="⚙️ Tải FFmpeg", height=35, fg_color="transparent", border_width=1, anchor="w", command=self.open_ffmpeg_download_page)
        self.ffmpeg_button.grid(row=14, column=0, padx=25, pady=10, sticky="ew")
        self.ffmpeg_button.configure(state="disabled")

        self.ytdlp_update_button = ctk.CTkButton(self.sidebar, text="🔄 Cập nhật yt-dlp", height=35, fg_color="transparent", border_width=1, anchor="w", command=self.update_ytdlp)
        self.ytdlp_update_button.grid(row=15, column=0, padx=25, pady=10, sticky="ew")

        self.nodejs_button = ctk.CTkButton(self.sidebar, text="📦 Cài Node.js (tự động)", height=35, fg_color="transparent", border_width=1, anchor="w", command=self.install_nodejs)
        self.nodejs_button.grid(row=16, column=0, padx=25, pady=10, sticky="ew")
        self.nodejs_button.configure(state="disabled")

        self.ffmpeg_notice_label = ctk.CTkLabel(self.sidebar, text="", text_color="orange", font=ctk.CTkFont(size=11), wraplength=220, justify="left")
        self.ffmpeg_notice_label.grid(row=17, column=0, padx=30, pady=(2, 0), sticky="w")

        self.nodejs_notice_label = ctk.CTkLabel(self.sidebar, text="", text_color="orange", font=ctk.CTkFont(size=11), wraplength=220, justify="left")
        self.nodejs_notice_label.grid(row=18, column=0, padx=30, pady=(0, 20), sticky="w")

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
        
        self.tasks_header_label = ctk.CTkLabel(self.tasks_header_frame, text="Danh sách đang tải", font=ctk.CTkFont(size=15, weight="bold"))
        self.tasks_header_label.pack(side="left")

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

    def _toggle_lang(self):
        self.lang = "en" if self.lang == "vi" else "vi"
        self.lang_button.configure(text="🌐 VI" if self.lang == "en" else "🌐 EN")
        self._apply_lang()
        self._save_config()

    def _t(self, key):
        """Shortcut lấy string theo ngôn ngữ hiện tại."""
        return LANG[self.lang].get(key, LANG["vi"][key])

    def _apply_lang(self):
        L = LANG[self.lang]
        self.welcome_label.configure(text=L["welcome"])
        self.url_entry.configure(placeholder_text=L["url_placeholder"])
        self.preview_button.configure(text=L["btn_check"])
        self.download_button.configure(text=L["btn_download"])
        self.video_title_label.configure(text=L["preview_default"])
        self.video_channel_label.configure(text=L["channel"])
        self.video_duration_label.configure(text=L["duration"])
        self.tasks_header_label.configure(text=L["tasks_header"])
        self.status_label.configure(text=L["ready"])
        # Sidebar labels
        self.lbl_section_config.configure(text=L["section_config"])
        self.lbl_section_cookie.configure(text=L["section_cookie"])
        self.lbl_section_tools.configure(text=L["section_tools"])
        self.lbl_from_video.configure(text=L["from_video"])
        self.lbl_to_video.configure(text=L["to_video"])
        self.lbl_concurrent.configure(text=L["concurrent_label"])
        self.playlist_end_entry.configure(placeholder_text=L["to_placeholder"])
        self.playlist_switch.configure(text=L["playlist_switch"])
        self.archive_switch.configure(text=L["archive_switch"])
        self.cookie_file_button.configure(text=L["cookie_file_btn"])
        self.history_button.configure(text=L["btn_history"])
        self.ffmpeg_button.configure(text=L["btn_ffmpeg"])
        self.ytdlp_update_button.configure(text=L["btn_ytdlp"])
        self.nodejs_button.configure(text=L["btn_nodejs"])
        # Format/quality comboboxes
        is_audio = "MP3" in self.format_var.get() or "Audio" in self.format_var.get()
        self.format_combobox.configure(values=[L["fmt_video"], L["fmt_audio"]])
        self.format_var.set(L["fmt_audio"] if is_audio else L["fmt_video"])
        q_vals = L["quality_values_audio"] if is_audio else L["quality_values_video"]
        self.quality_combobox.configure(values=q_vals)
        self.quality_var.set(q_vals[0])
        # Concurrent combobox
        c_vals = L["concurrent_values"]
        self.concurrent_combobox.configure(values=c_vals)
        self.concurrent_var.set(c_vals[1])  # default 4 streams / 4 luồng
        # Cookie combobox: đổi giá trị đầu tiên
        cur_browser = self.cookie_var.get()
        browsers = ["chrome", "edge", "firefox", "brave", "opera", "vivaldi"]
        new_none = L["cookie_none"]
        self.cookie_combobox.configure(values=[new_none] + browsers)
        if cur_browser not in browsers:
            self.cookie_var.set(new_none)

    def _on_playlist_toggle(self):
        if self.playlist_var.get():
            self.playlist_range_frame.grid()
        else:
            self.playlist_range_frame.grid_remove()

    def on_format_change(self, choice):
        L = LANG[self.lang]
        if "MP3" in choice or "Audio" in choice:
            self.quality_combobox.configure(values=L["quality_values_audio"])
            self.quality_var.set(L["quality_values_audio"][0])
        else:
            self.quality_combobox.configure(values=L["quality_values_video"])
            self.quality_var.set(L["quality_values_video"][0])
            
    def load_config(self):
        default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        save_dir = default_dir
        cookie_file = None
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    d = data.get("save_dir", "")
                    if d and os.path.isdir(d): save_dir = d
                    c = data.get("cookie_file", "")
                    if c and os.path.isfile(c): cookie_file = c
            except Exception: pass
        return save_dir, cookie_file

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

    def check_nodejs(self):
        nodejs_available = shutil.which("node") is not None
        if nodejs_available:
            self.nodejs_notice_label.configure(text="✅ Node.js đã cài. Video hội viên sẽ tải được.", text_color="green")
            self.nodejs_button.configure(state="disabled")
        else:
            self.nodejs_notice_label.configure(
                text="❌ Cần Node.js để tải video hội viên. Bấm nút bên trên để cài tự động.",
                text_color="#FF6B6B"
            )
            self.nodejs_button.configure(state="normal")

    def install_nodejs(self):
        self.nodejs_button.configure(state="disabled", text="⏳ Đang cài Node.js...")
        self.update_status("Đang cài Node.js...", "orange")
        def do_install():
            try:
                import subprocess
                # Thử dùng winget (có sẵn trên Windows 10/11)
                result = subprocess.run(
                    ["winget", "install", "--id", "OpenJS.NodeJS.LTS",
                     "--accept-package-agreements", "--accept-source-agreements", "--silent"],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    self.after(0, lambda: [
                        self.nodejs_button.configure(state="disabled", text="📦 Cài Node.js (tự động)"),
                        self.nodejs_notice_label.configure(text="✅ Đã cài Node.js! Hãy khởi động lại app.", text_color="green"),
                        self.update_status("✅ Node.js đã cài xong! Vui lòng khởi động lại ứng dụng.", "green"),
                        messagebox.showinfo("Cài đặt thành công",
                            "Node.js đã được cài đặt!\n\n"
                            "Vui lòng đóng và mở lại ứng dụng để \n"
                            "bắt đầu tải được video hội viên.")
                    ])
                else:
                    # winget không có hoặc lỗi → mở trang tải thủ công
                    self.after(0, lambda: [
                        self.nodejs_button.configure(state="normal", text="📦 Cài Node.js (tự động)"),
                        self.update_status("winget không khả dụng, mở trang tải thủ công...", "orange"),
                        webbrowser.open("https://nodejs.org/en/download")
                    ])
            except FileNotFoundError:
                # winget chưa có → mở trang tải thủ công
                self.after(0, lambda: [
                    self.nodejs_button.configure(state="normal", text="📦 Cài Node.js (tự động)"),
                    self.update_status("Mở trang cài Node.js...", "orange"),
                    webbrowser.open("https://nodejs.org/en/download")
                ])
            except Exception as e:
                self.after(0, lambda: [
                    self.nodejs_button.configure(state="normal", text="📦 Cài Node.js (tự động)"),
                    self.update_status(f"Lỗi cài Node.js: {str(e)[:40]}", "red")
                ])
        threading.Thread(target=do_install, daemon=True).start()

    def open_ffmpeg_download_page(self):
        try: webbrowser.open("https://ffmpeg.org/download.html")
        except: messagebox.showerror("Lỗi", "Vui lòng truy cập ffmpeg.org.")

    def update_ytdlp(self):
        self.ytdlp_update_button.configure(state="disabled", text="⏳ Đang cập nhật...")
        self.update_status("Đang cập nhật yt-dlp...", "orange")
        def do_update():
            try:
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    self.after(0, lambda: [
                        self.ytdlp_update_button.configure(state="normal", text="🔄 Cập nhật yt-dlp"),
                        self.update_status("✅ yt-dlp đã được cập nhật! Hãy khởi động lại app.", "green"),
                        messagebox.showinfo("Cập nhật thành công",
                            "yt-dlp đã được cập nhật lên phiên bản mới nhất.\n"
                            "Vui lòng khởi động lại ứng dụng để áp dụng.")
                    ])
                else:
                    self.after(0, lambda: [
                        self.ytdlp_update_button.configure(state="normal", text="🔄 Cập nhật yt-dlp"),
                        self.update_status("Cập nhật thất bại. Kiểm tra kết nối mạng.", "red")
                    ])
            except Exception as e:
                self.after(0, lambda: [
                    self.ytdlp_update_button.configure(state="normal", text="🔄 Cập nhật yt-dlp"),
                    self.update_status(f"Lỗi cập nhật: {str(e)[:40]}", "red")
                ])
        threading.Thread(target=do_update, daemon=True).start()

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
                browser_cookie = self.cookie_var.get()
                cookie_opts = self._build_cookie_opts()
                extra_args = self._build_ytdlp_extra_args()

                # Bước 1: Lấy thông tin playlist nhanh (chỉ đếm số video, không fetch từng video)
                flat_opts = {'quiet': True, 'skip_download': True, 'noplaylist': False, 'extract_flat': 'in_playlist',
                             **extra_args, **cookie_opts}
                with yt_dlp.YoutubeDL(flat_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                is_playlist = info.get('_type') == 'playlist'
                playlist_count = 0

                if is_playlist:
                    raw_entries = info.get('entries') or []
                    # Dedup theo video ID để tránh đếm trùng do pagination
                    seen_ids = set()
                    entries = []
                    for e in raw_entries:
                        if e is None:
                            continue
                        vid_id = e.get('id') or e.get('url', '')
                        if vid_id and vid_id not in seen_ids:
                            seen_ids.add(vid_id)
                            entries.append(e)
                    playlist_count = len(entries)
                    playlist_title = info.get('title', f'Playlist ({playlist_count} video)')
                    channel = info.get('uploader') or info.get('channel') or "Không rõ"
                    # Lấy thumbnail từ video đầu tiên
                    first_entry_url = entries[0].get('url') or entries[0].get('id') if entries else None
                    thumb_url = None
                    duration_text = None
                    title = playlist_title

                    # Bước 2: Lấy thêm thông tin video đầu tiên (thumbnail, duration)
                    if first_entry_url:
                        try:
                            full_url = f"https://www.youtube.com/watch?v={first_entry_url}" if not first_entry_url.startswith("http") else first_entry_url
                            detail_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True, **extra_args, **cookie_opts}
                            with yt_dlp.YoutubeDL(detail_opts) as ydl2:
                                first_info = ydl2.extract_info(full_url, download=False)
                            thumb_url = first_info.get('thumbnails')[-1].get('url') if first_info.get('thumbnails') else first_info.get('thumbnail')
                            duration_text = self.format_duration(first_info.get('duration'))
                            if not channel or channel == "Không rõ":
                                channel = first_info.get('uploader') or first_info.get('channel') or "Không rõ"
                        except: pass
                else:
                    first_entry = info
                    title = first_entry.get('title', 'Không rõ')
                    channel = first_entry.get('uploader') or first_entry.get('channel') or "Không rõ"
                    duration_text = self.format_duration(first_entry.get('duration'))
                    thumb_url = first_entry.get('thumbnails')[-1].get('url') if first_entry.get('thumbnails') else first_entry.get('thumbnail')

                pil_img_ref = None
                if thumb_url:
                    try:
                        resp = requests.get(thumb_url, timeout=10)
                        pil_img_ref = Image.open(io.BytesIO(resp.content)).convert("RGB")
                        pil_img_ref.thumbnail((220, 130))
                    except: pass

                def on_ui(pil=pil_img_ref):
                    if pil:
                        # Tạo ImageTk trong main thread để tránh lỗi pyimage
                        self._thumbnail_image_ref = ImageTk.PhotoImage(pil)
                        self.thumbnail_label.configure(image=self._thumbnail_image_ref, text="")
                    self.video_title_label.configure(text=title)
                    self.video_channel_label.configure(text=f"Kênh: {channel}")

                    if is_playlist:
                        dur_line = f"📂 Playlist: {playlist_count} video"
                        if duration_text:
                            dur_line += f"  |  Video đầu: {duration_text}"
                        if browser_cookie == "Không dùng":
                            dur_line += "  ⚠️ Chưa chọn Cookie"
                    else:
                        dur_line = f"Thời lượng: {duration_text}"
                    self.video_duration_label.configure(text=dur_line)

                    if search_mode and not is_playlist:
                        first_entry = info
                        if first_entry.get('webpage_url'):
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

    def _save_config(self):
        try:
            data = {'save_dir': self.save_dir, 'lang': self.lang}
            if self.cookie_file_path:
                data['cookie_file'] = self.cookie_file_path
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except: pass

    def choose_cookie_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file cookies.txt",
            filetypes=[("Cookie file", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.cookie_file_path = file_path
            short_name = os.path.basename(file_path)
            self.cookie_file_label.configure(text=f"✅ {short_name}")
            self.cookie_var.set("Không dùng")  # Tắt browser cookie khi dùng file
            self._save_config()  # Lưu vào config
        else:
            if not self.cookie_file_path:
                self.cookie_file_label.configure(text="")

    def _build_ytdlp_extra_args(self):
        """Trả về js_runtimes top-level param với node path nếu có."""
        node_path = shutil.which("node")
        if node_path:
            return {'js_runtimes': {'node': {'path': node_path}}}
        return {}

    def _build_cookie_opts(self):
        """Trả về dict cookie options cho yt-dlp."""
        if self.cookie_file_path and os.path.isfile(self.cookie_file_path):
            return {'cookiefile': self.cookie_file_path}
        browser = self.cookie_var.get()
        if browser != "Không dùng":
            return {'cookiesfrombrowser': (browser,)}
        return {}

    def choose_directory(self):
        dir_path = filedialog.askdirectory(initialdir=self.save_dir)
        if dir_path:
            self.save_dir = dir_path
            self.dir_label.configure(text=f"📂 {self.save_dir}")
            self._save_config()

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

    def download_thread(self, url, is_audio, quality, task_ui):
        download_count = [0]  # Đếm số video đã tải trong playlist (unique)
        error_count = [0]     # Đếm số lỗi
        seen_dl_ids = set()   # Tránh đếm trùng: video adaptive fire 'finished' 2 lần (video+audio stream)
        
        def task_hook(d):
            if task_ui.get("cancelled"): raise Exception("Cancelled")
            if d.get("status") == "downloading":
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total:
                    p = d.get('downloaded_bytes', 0) / total
                    playlist_info = f" (Video {download_count[0] + 1})" if self.playlist_var.get() else ""
                    self.after(0, lambda info=playlist_info: [task_ui["bar"].set(p), task_ui["status_label"].configure(text=f"{d.get('_percent_str')} • Tốc độ: {d.get('_speed_str')}{info}")])
                try: self.progress_hook(d)
                except: pass
            elif d.get("status") == "finished":
                info_dict = d.get("info_dict", {})
                vid_id = info_dict.get("id") or d.get("filename", "")
                # Chỉ đếm lần đầu gặp video ID này (tránh đếm 2 lần do stream video+audio)
                if vid_id not in seen_dl_ids:
                    seen_dl_ids.add(vid_id)
                    download_count[0] += 1
                    title = info_dict.get("title") or url
                    filename = d.get("filename")
                    self.after(0, lambda t=title, f=filename: self.add_history_entry(t, f))
                
                if self.playlist_var.get():
                    self.after(0, lambda: [task_ui["bar"].set(1), task_ui["status_label"].configure(text=f"✅ Đã tải {download_count[0]} video!", text_color="green")])
                else:
                    self.after(0, lambda: [task_ui["bar"].set(1), task_ui["status_label"].configure(text="✅ Hoàn tất!", text_color="green")])

        class WarningLogger:
            """Bắt cảnh báo n-challenge và đếm lỗi."""
            def __init__(self, app, task_ui):
                self.app = app
                self.task_ui = task_ui
            def debug(self, msg): pass
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg):
                if 'ERROR:' in msg:
                    error_count[0] += 1

        try:
            # Xây dựng playlist_items nếu có range
            playlist_items_opt = {}
            if self.playlist_var.get():
                try:
                    start = int(self.playlist_start_var.get() or 1)
                except ValueError:
                    start = 1
                end_str = self.playlist_end_var.get().strip()
                try:
                    end = int(end_str) if end_str else None
                except ValueError:
                    end = None
                if start != 1 or end is not None:
                    playlist_items_opt['playlist_items'] = f"{start}:{end if end else ''}"

            # concurrent_fragments
            try:
                concurrent = int(self.concurrent_var.get().split()[0])
            except Exception:
                concurrent = 4

            # download_archive
            archive_opt = {}
            if self.archive_var.get():
                archive_path = os.path.join(self.save_dir, 'yt-dlp-archive.txt')
                archive_opt['download_archive'] = archive_path

            ydl_opts = {
                'outtmpl': os.path.join(self.save_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [task_hook],
                'logger': WarningLogger(self, task_ui),
                'noplaylist': not self.playlist_var.get(),
                'ignoreerrors': True,
                'no_warnings': False,
                'extract_flat': False,
                'concurrent_fragments': concurrent,
                'throttledratelimit': 102400,  # re-extract URL nếu tốc độ < 100KB/s (tránh throttle/bot)
                **playlist_items_opt,
                **archive_opt,
                **self._build_ytdlp_extra_args(),
                **self._build_cookie_opts(),
            }
            
            if is_audio:
                bitrate = quality.split()[0] if quality[0].isdigit() else "320"
                ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': bitrate}]})
            else:
                res = ''.join(c for c in quality if c.isdigit())
                if res:
                    ydl_opts['format'] = (
                        f'bestvideo[ext=mp4][height<={res}]+bestaudio[ext=m4a]'
                        f'/bestvideo[height<={res}]+bestaudio'
                        f'/best[height<={res}]'
                        f'/bestvideo[ext=mp4]+bestaudio[ext=m4a]'
                        f'/bestvideo+bestaudio'
                        f'/best'
                    )
                else:
                    ydl_opts['format'] = (
                        'bestvideo[ext=mp4]+bestaudio[ext=m4a]'
                        '/bestvideo+bestaudio'
                        '/best'
                    )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
                ydl.download([url])
            
            # Hiển thị kết quả cuối cùng
            if self.playlist_var.get():
                result_msg = f"✅ Tải xong! Đã tải {download_count[0]} video"
                if error_count[0] > 0:
                    result_msg += f" (Bỏ qua {error_count[0]} video lỗi)"
                self.after(0, self.update_status, result_msg, "green")
            else:
                self.after(0, self.update_status, "Tải xuống hoàn tất!", "green")
            self.after(0, self.progress_bar.set, 1)
        except Exception as e:
            if not task_ui.get("cancelled"):
                err_str = str(e)
                if "Could not copy" in err_str and "cookie" in err_str.lower():
                    self.after(0, lambda: messagebox.showerror(
                        "Lỗi Cookie Browser",
                        "Không thể đọc cookie từ trình duyệt.\n\n"
                        "Nguyên nhân thường gặp: trình duyệt đang mở và khóa file cookie.\n\n"
                        "Cách khắc phục:\n"
                        "1. Đóng hoàn toàn trình duyệt rồi thử lại\n"
                        "2. Hoặc xuất cookies.txt bằng extension\n"
                        "   'Get cookies.txt LOCALLY' rồi chọn file đó thay thế."
                    ))
                    self.after(0, self.update_status, "Lỗi: Không đọc được cookie browser.", "red")
                elif "sign in" in err_str.lower() or "confirm you're not a bot" in err_str.lower() or "cookies" in err_str.lower() and "authentication" in err_str.lower():
                    self.after(0, lambda: messagebox.showerror(
                        "Yêu cầu Xác thực",
                        "YouTube yêu cầu đăng nhập để xác nhận không phải bot.\n\n"
                        "Nguyên nhân: File cookies.txt đã hết hạn hoặc không hợp lệ.\n\n"
                        "Cách khắc phục:\n"
                        "1. Mở trình duyệt, vào youtube.com và đảm bảo đang đăng nhập\n"
                        "2. Dùng extension 'Get cookies.txt LOCALLY' \u2192 Export\n"
                        "3. Chọn lại file mới trong mục 'Chọn file cookies.txt'"
                    ))
                    self.after(0, self.update_status, "Lỗi: Cookie hết hạn — cần xuất lại.", "red")
                else:
                    error_msg = f"Lỗi: {err_str[:60]}"
                    if download_count[0] > 0:
                        error_msg += f" (Đã tải được {download_count[0]} video)"
                    self.after(0, self.update_status, error_msg, "orange")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url: return
        if not url.startswith("http"): url = f"ytsearch1:{url}"
        
        is_audio = "MP3" in self.format_var.get() or "Audio" in self.format_var.get()
        quality = self.quality_var.get()
        task_ui = self.create_task_ui(self.url_entry.get().strip() or url)
        threading.Thread(target=self.download_thread, args=(url, is_audio, quality, task_ui), daemon=True).start()

if __name__ == "__main__":
    try:
        app = YouTubeDownloaderApp()
        app.mainloop()
    except Exception as e:
        log_error(e)
        print(f"Ứng dụng gặp lỗi khi khởi động. Chi tiết đã được ghi vào crash.log")
        input("Nhấn Enter để thoát...")
