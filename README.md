# YouTube Downloader

Một ứng dụng máy tính giúp bạn có thể tải Video và Âm thanh từ YouTube cực kỳ đơn giản, trực quan và dễ sử dụng.

## 🚀 Dành cho người dùng (Chỉ việc tải về và dùng)
Bạn không cần phải biết lập trình để sử dụng phần mềm này! Mọi thứ đã được đóng gói sẵn.

1. Chuyển đến phần **[Releases](https://github.com/phanan04/yt-d/releases)** ở góc phải của trang GitHub này.
2. Tìm phiên bản mới nhất và tải xuống tệp `YouTubeDownloader.exe` (hoặc bộ cài đặt).
3. Mở phần mềm lên, dán đường dẫn (Link) YouTube hoặc nhập tên bài hát bạn muốn tải.
4. Chọn định dạng (MP4/MP3), chất lượng rồi nhấn nút **"TẢI XUỐNG"**. Xong!

## ✨ Tính năng nổi bật
*   **Giao diện trực quan:** Đơn giản, đẹp mắt (Responsive, tự động co giãn) với Dark/Light Mode.
*   **Tải đa định dạng:** Hỗ trợ tải Video (có hình và tiếng) hoặc chỉ tải file Âm thanh (MP3).
*   **Tùy chọn chất lượng:** Tự do tùy chỉnh độ phân giải từ 360p lên đến xịn nhất (1080p, 1440p, v.v.) hoặc chất lượng bit-rate âm thanh.
*   **Xem trước thông tin & thumbnail:** Dán link hoặc gõ tên bài hát, ứng dụng sẽ hiển thị ảnh bìa, tiêu đề, tên kênh và thời lượng trước khi tải.
*   **Hỗ trợ Playlist:** Công tắc "Tải cả Playlist" cho phép tải lần lượt toàn bộ video trong danh sách phát, có hiển thị tiến trình `Video i/n`.
*   **Tải nhiều video cùng lúc:** Mỗi lần bấm "TẢI XUỐNG" sẽ tạo một thẻ tiến trình riêng, cho phép tải song song nhiều video kèm trạng thái chi tiết.
*   **Tự bắt link từ Clipboard:** Khi chuyển focus sang ứng dụng, nếu clipboard đang có link YouTube thì ô nhập link sẽ tự động điền giúp bạn.
*   **Lịch sử tải xuống:** Lưu lại các video đã tải (tiêu đề, thời gian, đường dẫn), kèm nút "Mở file" và "Mở thư mục" để truy cập nhanh.
*   **Video Hội viên:** Tính năng trích xuất Cookie từ trình duyệt web đang dùng (Chrome, Edge...) để tải được cả các video giới hạn/video riêng tư/hội viên.
*   **Siêu nhẹ & Nhanh:** Được viết bằng Python (với thư viện customtkinter và yt-dlp) giúp tải luồng tốc độ cao.

---

## 💻 Dành cho Lập trình viên / Developer
Nếu bạn muốn chạy trực tiếp từ mã nguồn hoặc chỉnh sửa thêm tính năng:

### 1. Yêu cầu hệ thống:
*   Python 3.8 trở lên.
*   Nên có sẵn FFmpeg trên máy (để ghép video hình chất lượng cao và âm thanh).

### 2. Cài đặt thư viện:
Tải repo về và cài đặt các thư viện phụ thuộc:
```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng:
```bash
python main.py
```

Hoặc trên Windows có thể double-click file:

```bat
run.bat
```

### 4. Cách đóng gói lại thành file .EXE:
Tôi đã chuẩn bị sẵn các cấu hình để build mã nguồn này thành ứng dụng riêng lẻ trên Windows.
*   Chạy **`build_exe.bat`** để tạo ra ngay một file `.exe` chạy thẳng.
*   Dùng **`setup_installer.iss`** biên dịch bằng *Inno Setup* nếu mong muốn tạo bộ cài đặt chuyên nghiệp có "Next > Next".
