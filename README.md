# YT-D

Ứng dụng tải video và âm thanh từ YouTube — hỗ trợ playlist, nội dung hội viên, tải song song, giao diện Dark Mode.

---

## Tính năng

- Tải video MP4 (360p → 1080p) và âm thanh MP3 (128–320 kbps)
- Tải toàn bộ playlist, chọn range (ví dụ: video 10–50)
- Bỏ qua video đã tải (download archive)
- Tải song song tối đa 16 luồng
- Hỗ trợ nội dung hội viên qua cookies.txt
- Xem trước thông tin video/playlist trước khi tải
- Lịch sử tải, Dark/Light Mode

---

## Yêu cầu

| Thành phần | Ghi chú |
|---|---|
| [FFmpeg](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip) | Bắt buộc để ghép video+audio (HD/4K) |
| [Node.js ≥ 20](https://nodejs.org) | Bắt buộc để giải n-challenge của YouTube |

Đặt `ffmpeg.exe` và `node.exe` vào PATH, hoặc cùng thư mục với `YT-D.exe`.

---

## Cài đặt

**Dùng bản release (khuyên dùng):**
```
Releases → tải YT-D.exe → chạy thẳng, không cần cài Python
```

---

## Tải nội dung hội viên

1. Mở trình duyệt, vào `youtube.com` và đảm bảo đang đăng nhập có hội viên
2. Cài extension **[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)**
3. Trên trang YouTube, nhấn extension → **Export** → lưu file `.txt`
4. Trong app: nhấn **"Chọn file cookies.txt"** → chọn file vừa lưu

> Cookie hết hạn sau vài tuần. Nếu gặp lỗi xác thực, export lại.

---

## License

MIT
