# CLAUDE.md

Hướng dẫn cho Claude và mọi automation cập nhật dữ liệu trong repository này.

## Phạm vi được phép

- **Chỉ cập nhật dữ liệu**: `data/latest.json` và thêm file mới trong `data/archive/`.
- **Không tự sửa dashboard/frontend** (HTML, CSS, JS, cấu hình GitHub Pages), `scripts/`, `docs/` hay file này. Những thay đổi đó cần con người yêu cầu rõ ràng.
- Không thay đổi cấu trúc dữ liệu. Cấu trúc được định nghĩa trong `docs/data-contract.md` (hiện hành: **`schema_version` `"2.0"`**).

## Tính trung thực

- **Không bịa số liệu hoặc nguồn.** Mọi con số, insight, tín hiệu, khuyến nghị, giá, khuyến mãi, hoạt động đối thủ phải có nguồn thật, kiểm chứng được, nằm trong `sources` với URL thật, và được trỏ tới qua `source_ids`.
- Không tìm được số liệu thì để `null`, ghi rõ vào `executive_summary.data_gaps` (và `note` của chỉ số), không ước đoán rồi trình bày như sự thật. List không có mục nào thì để rỗng `[]`.
- Nhận định/khuyến nghị (traffic light, recommendations, scenarios, decisions, tác động đến FPT Camera) là suy luận của bản tin, nhưng phải dựa trên bằng chứng có nguồn và nêu bằng chứng đó.
- Không thêm API key, secret, hay dịch vụ trả phí vào repository.

## Nội dung mỗi bản tin (schema 2.0)

Mọi section sau phải có mặt; chi tiết field, enum và mức bắt buộc xem `docs/data-contract.md`.

| Section | Cần điền |
| --- | --- |
| `edition` | `id` (ví dụ `2026-09-24-morning`), `number` tăng dần, `title`, `status` = `published`, `session`. |
| `executive_summary` | `headline`, `summary`, 3–6 `key_points`, `overall_sentiment`, `data_gaps`. |
| `market_dashboard` | ≤ 12 chỉ số đầu trang (tỷ giá, vàng, VN-Index, lãi suất, CPI, bán lẻ, TMĐT, camera…), có `category`, `direction`. |
| `weekly_macro_watch` | Vĩ mô trong tuần: `period_start/end`, `summary`, `themes`, `key_metrics`, `outlook`. |
| `macro_24h` | Tin vĩ mô 24 giờ qua. |
| `financial_markets` | Tỷ giá, vàng, chứng khoán, lãi suất, hàng hóa (`metrics`) + `highlights`. |
| `retail_consumer` | Bán lẻ, TMĐT, hành vi tiêu dùng (`metrics`, `trends`). |
| `b2c_traffic_lights` | Đèn `green`/`yellow`/`red` cho các chỉ báo B2C; giữ `id` ổn định (`consumer-demand`, `pricing-pressure`, `online-channel`, `camera-demand`, `competitive-pressure`). |
| `recommendations` | `issue`, `evidence`, `action`, `owner`, `deadline`, `kpi`, `priority`. |
| `scenarios_7d` | **Đúng 3** kịch bản `base`, `upside`, `downside`. |
| `must_read` | **Tối đa 5** bài, URL thật, `why_read`. |
| `events_next_24h` | Sự kiện sắp diễn ra (lịch công bố số liệu, họp NHNN/Fed, sự kiện bán lẻ, mega sale…). |
| `decisions_today` | Quyết định cần đưa ra hôm nay, có `owner`, `deadline`, `urgency`. |
| `camera_market_watch` | Thị trường camera / smart home / security: `summary`, `market_status`, `key_metrics`, `signals` (xu hướng thị trường & người tiêu dùng), `pricing_watch` (giá & khuyến mãi quan sát được), `channel_watch`, `demand_watch`, `fpt_camera_impact`. |
| `competitor_watch` | Mỗi diễn biến của đối thủ camera là một item: `competitor`, `development`, `channel`, `pricing_or_promo`, `threat_level`, `implication_for_fpt_camera`. |
| `sources` | Mọi nguồn được trích dẫn. |

Gợi ý nghiên cứu cho Camera / đối thủ: các thương hiệu camera phổ biến tại Việt Nam (ví dụ Imou, Ezviz, TP-Link Tapo, Xiaomi, Hikvision, Dahua, KBVision) và các nhà mạng/nhà cung cấp dịch vụ có camera; giá & khuyến mãi trên sàn TMĐT, chuỗi điện máy, website hãng; tin về an ninh gia đình, smart home, quyền riêng tư dữ liệu camera. Chỉ đưa vào những gì tìm được nguồn thật; không có diễn biến mới thì để list rỗng và ghi vào `data_gaps`.

## Quy trình mỗi lần cập nhật

1. Tạo nội dung bản tin mới theo đúng cấu trúc trong `docs/data-contract.md` (`schema_version` `"2.0"`), `updated_at` là thời điểm hiện tại (UTC, ISO 8601), `edition.status` là `"published"`.
2. Ghi vào `data/latest.json` — file này **luôn là phiên bản mới nhất**.
3. **Lưu một bản archive** giống hệt vào `data/archive/<YYYY-MM-DDTHHMMSSZ>.json` (timestamp lấy từ `updated_at`). Không sửa hay xóa file archive cũ.
4. Chạy `python3 scripts/validate_data.py data/latest.json data/archive/<file mới>.json`. Nếu lỗi thì sửa dữ liệu; không được commit dữ liệu không hợp lệ. (Không dùng `--allow-legacy` cho dữ liệu mới.)
5. Commit chỉ gồm `data/latest.json` và file archive mới, với message dạng `data: update edition <id>`.
