# CLAUDE.md

Hướng dẫn cho Claude và mọi automation cập nhật dữ liệu trong repository này.

## Phạm vi được phép

- **Chỉ cập nhật dữ liệu**: `data/latest.json` và thêm file mới trong `data/archive/`.
- **Không tự sửa dashboard/frontend** (HTML, CSS, JS, cấu hình GitHub Pages), `scripts/`, `docs/` hay file này. Những thay đổi đó cần con người yêu cầu rõ ràng.
- Không thay đổi cấu trúc dữ liệu. Cấu trúc được định nghĩa trong `docs/data-contract.md`.

## Tính trung thực

- **Không bịa số liệu hoặc nguồn.** Mọi con số, insight, tín hiệu phải có nguồn thật, kiểm chứng được, nằm trong `sources` với URL thật.
- Không tìm được số liệu thì để `null` và nói rõ trong `executive_summary`, không ước đoán rồi trình bày như sự thật.
- Không thêm API key, secret, hay dịch vụ trả phí vào repository.

## Quy trình mỗi lần cập nhật

1. Tạo nội dung bản tin mới theo đúng cấu trúc trong `docs/data-contract.md`, `updated_at` là thời điểm hiện tại (UTC, ISO 8601).
2. Ghi vào `data/latest.json` — file này **luôn là phiên bản mới nhất**.
3. **Lưu một bản archive** giống hệt vào `data/archive/<YYYY-MM-DDTHHMMSSZ>.json` (timestamp lấy từ `updated_at`). Không sửa hay xóa file archive cũ.
4. Chạy `python3 scripts/validate_data.py data/latest.json data/archive/<file mới>.json`. Nếu lỗi thì sửa dữ liệu; không được commit dữ liệu không hợp lệ.
5. Commit chỉ gồm `data/latest.json` và file archive mới, với message dạng `data: update edition <id>`.
