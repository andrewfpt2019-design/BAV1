# Codex Video Workflow

Dùng Codex để lên kịch bản, xử lý clip và dựng trên timeline Concat. Mở Concat để xem, chỉnh và xuất video. Repo có sẵn quy trình làm việc trong [AGENTS.md](AGENTS.md), skill [video-tools](.agents/skills/video-tools/SKILL.md) và bài dựng thử.

## Cài trên Windows x64

1. Tải repo bằng **Code → Download ZIP** rồi giải nén, hoặc clone bằng Git.
2. Mở PowerShell tại thư mục vừa giải nén hoặc clone. Chạy lệnh dưới đây. Lần đầu cần Internet để tải công cụ và có thể mất vài phút. Script cài Node.js, Python và FFmpeg trong thư mục repo, lấy mã các công cụ theo phiên bản đã chốt, rồi dùng bản Concat đã có hoặc cài Concat 0.2.9 cho tài khoản Windows hiện tại.

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
   ```

3. Chạy bài dựng thử. Script tự tạo hai clip dọc có âm thanh, rồi tạo timeline gồm clip gốc, clip ghép, clip áp hiệu ứng và bản xem trước từ draft CapCut.

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\demo.ps1
   ```

4. Mở Concat và mở thư mục **Demo Concat** mà script in ở dòng cuối. Timeline có 4 clip với âm thanh và dài khoảng 10 giây.

## Dựng dự án của bạn

Mở thư mục repo làm workspace trong Codex. Gửi đường dẫn đến các clip cùng brief. Ví dụ:

> Dùng $video-tools dựng video dọc 30 giây từ các clip trong thư mục footage của tôi. Mở đầu bằng cảnh pha chế, tiếp theo là cảnh quán và kết bằng cảnh cận ly cà phê. Giữ từng cảnh trên timeline để tôi chỉnh trong Concat. Cho tôi đường dẫn project và kiểm tra âm thanh.

Bạn có thể sao chép [hồ sơ mẫu](PROFILE.example.md) thành `PROFILE.local.md` để Codex áp dụng ngôn ngữ, phong cách dựng và quy tắc làm việc của bạn.

| Việc cần làm | Lệnh hoặc thao tác | Kết quả mong đợi |
| --- | --- | --- |
| Kiểm tra bộ cài | `./video-tools/concat-desk.cmd doctor` | Hiện phiên bản Concat, Python và CapCut CLI. |
| Tạo timeline | `./video-tools/concat-desk.cmd new "outputs/Video moi"` | Tạo project dọc 1080×1920, 30 fps. Tạo thư mục `outputs` trước nếu chưa có. |
| Giữ từng cảnh để chỉnh | `./video-tools/concat-desk.cmd add "outputs/Video moi" "footage/canh-1.mp4"` | Thêm clip vào cuối timeline. Gọi lại cho mỗi cảnh. |
| Ghép hai clip | `./video-tools/concat-desk.cmd stitch "outputs/Video moi" "footage/canh-1.mp4" "footage/canh-2.mp4"` | Ghép bằng OpenMontage và thêm kết quả dưới dạng một clip. |
| Xem preset | `./video-tools/concat-desk.cmd effects` | Hiện danh sách hiệu ứng có thể render. |
| Áp hiệu ứng | `./video-tools/concat-desk.cmd effect "outputs/Video moi" moody "footage/canh-1.mp4"` | Render hiệu ứng và thêm clip kết quả. |
| Dùng draft CapCut | `./video-tools/concat-desk.cmd capcut "outputs/Video moi" "C:/duong-dan/draft"` | Render bản xem trước khi draft vượt qua kiểm tra. |
| Đọc timeline | `./video-tools/concat-desk.cmd inspect "outputs/Video moi"` | Hiện thông tin clip và thời lượng của timeline đã lưu. |
| Duyệt và xuất | Mở project trong Concat, xem hình và nghe tiếng rồi dùng **Export**. | Có timeline để chỉnh và tệp MP4 để chia sẻ. |

**Khi làm việc qua lại với Concat.** Đóng project trong Concat trước khi chạy lệnh đọc hoặc sửa project. Mở lại sau khi lệnh hoàn tất. Khi chuyển project sang máy khác, giữ nguyên thư mục `bridge-media` trong project. Dùng `--at 5` để đặt clip tại giây thứ 5 khi cần.

**Với CapCut.** Nếu draft có âm thanh nhúng trong clip nguồn hoặc bước kiểm tra thất bại, xuất MP4 từ CapCut rồi dùng `add`. Hiệu ứng từ công cụ ngoài được render vào clip. Bạn vẫn có thể cắt hoặc di chuyển clip trong Concat. Để đổi tham số hiệu ứng gốc, render lại ở công cụ đã tạo hiệu ứng.

**Phạm vi cài đặt.** Bộ cài tích hợp các lệnh dựng cục bộ trong bảng. Để dùng Codex, người nhận đăng nhập bằng tài khoản của họ. Tính năng đám mây của công cụ nguồn và CapCut Desktop có quy trình cài hoặc cấp quyền riêng.

## Thành phần và giấy phép

| Thành phần | Phiên bản | Giấy phép công bố bởi dự án |
| --- | --- | --- |
| [CapCut CLI](https://github.com/renezander030/capcut-cli/tree/0c93e8fd981db9d88a4013c675720ea5313c93e7) | 0.34.0 | MIT |
| [OpenMontage](https://github.com/OpenMontageInc/OpenMontage/tree/2e003e65fa99a0f329478a2c1cdcf26bc481933a) | `2e003e6` | AGPL-3.0 |
| [Claude Video Effects](https://github.com/Vibha-Ramprakash/claude-video-effects/tree/60840acc7e126a5e34068276a23e912ec4c8c34c) | `60840ac` | MIT |
| [Concat](https://github.com/jub0t/Concat/releases/tag/v0.2.9) | 0.2.9 | AGPL-3.0 với các điều khoản trong repo nguồn |

Script lấy thành phần từ nguồn gốc, trong đó có [FFmpeg Essentials cho Windows](https://github.com/GyanD/codexffmpeg/releases/tag/8.0.1). Mỗi thành phần giữ giấy phép đi kèm. Mã và tài liệu của repo này dùng [AGPL-3.0](LICENSE).
