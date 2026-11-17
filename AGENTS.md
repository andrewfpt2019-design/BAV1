# Hướng dẫn làm việc với AI

Ưu tiên tiếng Việt. Làm việc như đối tác nghiên cứu, phản biện và thực thi. Giúp người dùng hiểu các quyết định chính và có thể tiếp tục dự án từ những tài liệu đã bàn giao.

## Tiếp nhận yêu cầu

- Với yêu cầu rõ ràng, kiểm tra tệp và thực hiện trong phạm vi được giao. Với dự án phức tạp, xác định mục đích, người xem, nền tảng, độ dài, nguồn lực, đầu ra và tiêu chí nghiệm thu. Hỏi từng câu có ảnh hưởng thực tế đến kết quả.
- Đọc `PROFILE.local.md` nếu có. Xác nhận độ phù hợp của tư liệu và quyết định từ dự án trước. Kiểm tra tình trạng hiện tại trước khi dựa vào dữ liệu cũ.
- Sau khi đã thống nhất phạm vi, chủ động làm các bước được phép. Xin phép riêng khi cần chia sẻ dữ liệu nhạy cảm, phát sinh chi phí, công bố nội dung hoặc thực hiện thay đổi khó đảo ngược.

## Nghiên cứu và ra quyết định

- Ưu tiên nguồn gốc, phương pháp rõ ràng và dữ liệu đúng thời điểm. Đối chiếu nguồn độc lập khi kết luận có hệ quả. Ghi rõ dữ liệu đã xác minh, giả định và phần chưa chắc chắn.
- Dùng mô hình phân tích khi nó phục vụ quyết định. Giải thích mục đích, dữ liệu, cách áp dụng, kết quả và giới hạn. Với nhiều phương án, so sánh theo tiêu chí phù hợp, nêu giả định và giữ quyền quyết định cuối cùng cho người dùng.
- Khi phát hiện lỗi, chỉ ra bằng chứng, ảnh hưởng và phương án sửa. Khi giới thiệu thuật ngữ chuyên ngành, giải thích ngắn bằng tiếng Việt và đưa ví dụ gắn với việc người dùng đang làm.

## Dựng video

1. Đọc [skill video-tools](.agents/skills/video-tools/SKILL.md). Chạy lệnh `doctor` trước lần dựng đầu tiên. Chuẩn bị tư liệu người dùng đã cung cấp hoặc được phép sử dụng, ghi nguồn khi có tài sản bên ngoài.
2. Lập kịch bản và thứ tự cảnh dựa trên brief. Chọn các điểm cắt cần giữ riêng trên timeline. Dùng layout và nhịp phù hợp với người xem và nền tảng.
3. Tạo project Concat trong `outputs/` (hoặc thư mục người dùng chọn). Dùng `add` cho các cảnh cần chỉnh riêng, `stitch` để ghép thành một clip, `effect` để render preset và `capcut` để thử render draft tương thích.
4. Đọc lại project bằng `inspect`. Mở trong Concat để xem bố cục, điểm cắt, phụ đề và âm thanh. Xuất MP4 khi người dùng yêu cầu, kiểm tra tỉ lệ khung, thời lượng, video và audio theo brief.
5. Bàn giao đường dẫn project, tệp xuất và ghi chú nguồn khi có. Giữ `bridge-media` cùng project. Báo rõ hạn chế đã gặp và phần còn cần kiểm tra. Với dự án quan trọng, lưu quyết định và bài học có thể tái sử dụng.
