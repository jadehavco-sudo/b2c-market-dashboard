# Data contract

Tài liệu này mô tả hợp đồng dữ liệu giữa **automation cập nhật dữ liệu** và **dashboard (frontend)** — dashboard điều hành B2C, có module thị trường Camera và theo dõi đối thủ phục vụ FPT Camera.

## Nguyên tắc chính

- Dashboard **chỉ đọc duy nhất** file `data/latest.json`. Không đọc file nào khác, không gọi API nào khác.
- `data/latest.json` luôn là **phiên bản mới nhất** của bản tin.
- Mỗi lần cập nhật, một bản sao y hệt được lưu vào `data/archive/` để giữ lịch sử.
- Cấu trúc dữ liệu phải **ổn định**: automation chỉ thay đổi *giá trị*, không đổi tên field, không đổi kiểu dữ liệu, không bỏ field bắt buộc. Nhờ vậy frontend không phải sửa mỗi ngày.
- Mọi thay đổi cấu trúc (breaking change) phải tăng `schema_version` và cập nhật tài liệu này, script validate và frontend có review của con người.

## Luồng dữ liệu

```
Claude scheduled research → data/latest.json + data/archive/<timestamp>.json → GitHub Pages dashboard
```

## Vị trí file

| File | Vai trò |
| --- | --- |
| `data/latest.json` | Bản tin mới nhất. Dashboard đọc file này. |
| `data/archive/<timestamp>.json` | Bản lưu lịch sử, nội dung giống hệt `latest.json` tại thời điểm cập nhật. |
| `scripts/validate_data.py` | Kiểm tra file dữ liệu tuân thủ hợp đồng này. |

Tên file archive dùng timestamp UTC lấy từ `updated_at`, định dạng `YYYY-MM-DDTHHMMSSZ.json`, ví dụ `2026-09-23T060000Z.json` (bỏ dấu `:` để tương thích mọi hệ điều hành). Validator kiểm tra tên file khớp `updated_at`. File archive đã tạo thì không sửa lại.

## Phiên bản schema

| `schema_version` | Trạng thái |
| --- | --- |
| `2.0` | **Hiện hành.** Mọi dữ liệu mới (`latest.json` và archive mới) phải dùng phiên bản này. |
| `1.0` | Cũ. Chỉ còn trong các file archive đã tạo trước khi nâng cấp; kiểm tra bằng `--allow-legacy`. |

## Quy ước chung

### Trạng thái bản tin và mức bắt buộc

`edition.status` là `"placeholder"`, `"draft"` hoặc `"published"`. Mọi key liệt kê trong tài liệu này **phải có mặt** (trừ khi ghi *tùy chọn*). Giá trị thì chia 3 mức:

| Ký hiệu | Ý nghĩa |
| --- | --- |
| **luôn** | Không được null/rỗng ở mọi trạng thái (ví dụ `id`). |
| **pub** | Được null khi `placeholder`/`draft`; **bắt buộc có giá trị (không null, không chuỗi rỗng, không list rỗng)** khi `published`. |
| *null được* | Luôn được phép null. Dùng khi không tìm được số liệu — **không bịa**. |

### Kiểu dữ liệu

| Kiểu | Mô tả |
| --- | --- |
| `text` | chuỗi hoặc null |
| `number` | số (int/float, không phải boolean) hoặc null |
| `date` | chuỗi ISO 8601: `YYYY-MM-DD` hoặc datetime có múi giờ, ví dụ `2026-09-23T14:00:00+07:00` |
| `enum(a\|b)` | một trong các giá trị liệt kê, hoặc null |
| `text[]` | list chuỗi |
| `source_ids` | list `id` trong `sources`; **khi `published` không được rỗng** |

### Enum dùng chung

| Tên | Giá trị |
| --- | --- |
| `direction` | `up`, `down`, `flat` |
| `strength` | `strong`, `moderate`, `weak` |
| `level` (impact, priority, urgency, importance, likelihood, threat_level) | `high`, `medium`, `low` |
| `sentiment` | `positive`, `neutral`, `negative`, `mixed` |
| `metric_category` | `fx`, `gold`, `equity`, `rates`, `commodity`, `crypto`, `macro`, `retail`, `ecommerce`, `consumer`, `camera`, `other` |
| `camera_segment` | `home` (hộ gia đình), `sme` (cửa hàng/doanh nghiệp nhỏ), `enterprise`, `all`, `other` |

### Kiểu `Metric` (chỉ số)

Dùng cho `market_dashboard`, `weekly_macro_watch.key_metrics`, `financial_markets.metrics`, `retail_consumer.metrics`, `camera_market_watch.key_metrics`. Kế thừa từ `market_metrics` của schema 1.0, thêm `category`, `direction`, `as_of`, `note`.

```jsonc
{
  "id": "usd-vnd-central-rate",   // luôn; duy nhất trong list
  "label": "Tỷ giá trung tâm USD/VND", // pub
  "category": "fx",               // enum(metric_category) — frontend dùng để nhóm/icon
  "value": 25635,                 // number; null nếu chưa có số liệu
  "unit": "VND/USD",              // text
  "change": -5,                   // number
  "change_unit": "VND",           // text, ví dụ "%", "pp", "% svck"
  "direction": "down",            // enum(direction) — mũi tên trên dashboard
  "period": "2026-09-23",         // text, kỳ số liệu
  "as_of": "2026-09-23",          // date, tùy chọn
  "note": null,                   // text, tùy chọn; BẮT BUỘC khi published mà value = null
  "source_ids": ["src-fx"]
}
```

## Cấu trúc `latest.json` (schema_version 2.0)

Thứ tự section dưới đây cũng là thứ tự gợi ý hiển thị trên dashboard.

### Metadata

```jsonc
{
  "schema_version": "2.0",               // luôn
  "updated_at": "2026-09-23T06:00:00Z",  // luôn; ISO 8601 có múi giờ (UTC)
  "edition": {
    "id": "2026-09-23-morning",          // luôn
    "number": 3,                         // luôn; số nguyên, 0 = placeholder
    "title": "…",                        // pub
    "status": "published",               // luôn; placeholder | draft | published
    "language": "vi",                    // text
    "session": "morning"                 // tùy chọn; enum(morning|afternoon|evening|adhoc)
  },
  …
}
```

### `executive_summary` — tóm tắt điều hành (object)

| Field | Kiểu | Mức | Ghi chú |
| --- | --- | --- | --- |
| `headline` | text | pub | Tiêu đề một câu. |
| `summary` | text | pub | Đoạn tóm tắt. |
| `key_points` | text[] | pub | 3–6 ý chính. |
| `overall_sentiment` | enum(sentiment) | null được | Sắc thái chung của thị trường B2C hôm nay. |
| `data_gaps` | text[] | | Liệt kê số liệu **không tìm được** (đang để null) và lý do. Rỗng nếu đủ dữ liệu. |

### `market_dashboard` — dải chỉ số đầu trang (list `Metric`)

Tối đa **12** chỉ số quan trọng nhất (tỷ giá, vàng, VN-Index, lãi suất, CPI, bán lẻ, TMĐT, chỉ số camera…). Khi `published` không được rỗng.

### `weekly_macro_watch` — vĩ mô trong tuần (object)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `period_start`, `period_end` | date | null được |
| `summary` | text | pub |
| `themes[]` | `{id, theme (pub), detail (pub), direction, impact: level, source_ids}` | |
| `key_metrics[]` | `Metric` | |
| `outlook` | text | null được — nhận định cho phần còn lại của tuần |

### `macro_24h` — diễn biến vĩ mô 24 giờ qua (object)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `summary` | text | pub |
| `items[]` | `{id, title (pub), detail (pub), category: text, impact: level, occurred_at: date, source_ids}` | |

### `financial_markets` — thị trường tài chính (object)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `summary` | text | pub |
| `metrics[]` | `Metric` (category `fx`/`gold`/`equity`/`rates`/`commodity`/`crypto`) | |
| `highlights[]` | `{id, title (pub), detail (pub), impact: level, source_ids}` | |

### `retail_consumer` — bán lẻ & tiêu dùng (object)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `summary` | text | pub |
| `metrics[]` | `Metric` (category `retail`/`ecommerce`/`consumer`) | |
| `trends[]` | `{id, trend (pub), detail (pub), direction, strength, source_ids}` — thay thế `b2c_signals` của 1.0 | |

### `b2c_traffic_lights` — đèn tín hiệu B2C (list)

| Field | Kiểu | Mức | Ghi chú |
| --- | --- | --- | --- |
| `id` | text | luôn | |
| `name` | text | pub | Tên chỉ báo, ví dụ "Sức cầu tiêu dùng". |
| `status` | enum(`green`\|`yellow`\|`red`) | pub | |
| `trend` | enum(`improving`\|`stable`\|`worsening`) | null được | So với bản tin trước. |
| `explanation` | text | pub | Vì sao đèn màu này. |
| `action` | text | pub | Việc cần làm. |
| `source_ids` | source_ids | | |

Bộ đèn gợi ý (giữ `id` ổn định giữa các bản tin để frontend so sánh): `consumer-demand`, `pricing-pressure`, `online-channel`, `camera-demand`, `competitive-pressure`.

### `recommendations` — khuyến nghị hành động (list)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `priority` | enum(level) | pub |
| `issue` | text | pub — vấn đề |
| `evidence` | text | pub — bằng chứng, số liệu có nguồn |
| `action` | text | pub — hành động đề xuất |
| `owner` | text | pub — bộ phận chịu trách nhiệm (ví dụ "Marketing", "Kinh doanh online") |
| `deadline` | date | pub |
| `kpi` | text | pub — cách đo kết quả |
| `source_ids` | source_ids | |

### `scenarios_7d` — kịch bản 7 ngày (list, **đúng 3 phần tử**)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn (gợi ý `base`, `upside`, `downside`) |
| `type` | enum(`base`\|`upside`\|`downside`) | pub; không trùng nhau; khi published phải đủ cả 3 |
| `scenario` | text | pub — tên/mô tả kịch bản |
| `likelihood` | enum(level) | null được |
| `conditions` | text | pub — điều kiện kích hoạt |
| `consumer_impact` | text | pub |
| `b2c_impact` | text | pub |
| `fpt_camera_impact` | text | null được |
| `action` | text | pub |
| `source_ids` | source_ids | |

### `must_read` — bài nên đọc (list, **tối đa 5**)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `title` | text | pub |
| `publisher` | text | pub |
| `url` | URL http(s) | pub |
| `published_at` | date | null được |
| `summary` | text | pub |
| `why_read` | text | pub — vì sao lãnh đạo nên đọc |

### `events_next_24h` — sự kiện 24 giờ tới (list)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `event` | text | pub |
| `scheduled_at` | date | null được (datetime có múi giờ nếu biết giờ) |
| `category` | text | null được |
| `importance` | enum(level) | pub |
| `why_it_matters` | text | pub |
| `watch_for` | text | null được — cần theo dõi con số/diễn biến gì |
| `source_ids` | source_ids | |

### `decisions_today` — quyết định cần đưa ra hôm nay (list)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `decision` | text | pub |
| `context` | text | pub |
| `options` | text[] | |
| `recommended_option` | text | null được |
| `owner` | text | pub |
| `deadline` | date | pub |
| `urgency` | enum(level) | pub |
| `source_ids` | source_ids | |

### `camera_market_watch` — thị trường Camera (object)

Phục vụ FPT Camera: tình hình thị trường, xu hướng người tiêu dùng camera / smart home / security, biến động giá & khuyến mãi, kênh bán, nhu cầu, và tác động tổng hợp.

```jsonc
"camera_market_watch": {
  "summary": "…",                 // pub — tình hình thị trường camera
  "market_status": "expanding",   // enum(expanding|stable|contracting|mixed)
  "key_metrics": [ Metric ],      // chỉ số thị trường camera/smart home (category "camera")
  "signals": [ … ],               // xu hướng thị trường & người tiêu dùng
  "pricing_watch": [ … ],         // giá & khuyến mãi quan sát được
  "channel_watch": [ … ],         // diễn biến kênh bán
  "demand_watch": [ … ],          // động lực / chỉ báo nhu cầu
  "fpt_camera_impact": { … }      // tác động tổng hợp đến FPT Camera
}
```

**`signals[]`** — xu hướng thị trường và người tiêu dùng

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `signal` | text | pub |
| `detail` | text | pub |
| `theme` | enum(`camera`\|`smart_home`\|`security`\|`privacy`\|`technology`\|`regulation`\|`other`) | pub |
| `signal_type` | enum(`market`\|`consumer`\|`technology`\|`regulation`\|`supply`\|`other`) | null được |
| `segment` | enum(camera_segment) | null được |
| `direction` | enum(direction) | null được |
| `strength` | enum(strength) | null được |
| `source_ids` | source_ids | |

**`pricing_watch[]`** — biến động giá / khuyến mãi (của mọi thương hiệu, kể cả FPT Camera)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `brand` | text | pub |
| `product` | text | pub |
| `segment` | enum(camera_segment) | null được |
| `channel` | text | null được — nơi quan sát (sàn, chuỗi, website hãng…) |
| `price` | number | null được — giá bán quan sát được |
| `previous_price` | number | null được |
| `currency` | text | null được (mặc định hiểu là `VND`) |
| `change_pct` | number | null được |
| `promo` | text | null được — nội dung khuyến mãi |
| `promo_type` | enum(`discount`\|`bundle`\|`gift`\|`installment`\|`free_installation`\|`free_cloud`\|`voucher`\|`flash_sale`\|`other`) | null được |
| `valid_until` | date | null được |
| `observed_at` | date | pub |
| `source_ids` | source_ids | |

Khi `published`, mỗi item phải có ít nhất `price` hoặc `promo`.

**`channel_watch[]`** — kênh bán

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `channel` | text | pub — ví dụ "Shopee", "TikTok Shop", "chuỗi điện máy" |
| `channel_type` | enum(`ecommerce`\|`social_commerce`\|`retail_chain`\|`telco`\|`installer`\|`direct`\|`other`) | null được |
| `development` | text | pub |
| `direction` | enum(direction) | null được |
| `implication_for_fpt_camera` | text | pub |
| `source_ids` | source_ids | |

**`demand_watch[]`** — nhu cầu

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn |
| `indicator` | text | pub — ví dụ "Quan tâm tìm kiếm camera an ninh", "Mùa cao điểm cuối năm" |
| `detail` | text | pub |
| `segment` | enum(camera_segment) | null được |
| `value` | number | null được |
| `unit` | text | null được |
| `period` | text | null được |
| `direction` | enum(direction) | null được |
| `strength` | enum(strength) | null được |
| `source_ids` | source_ids | |

**`fpt_camera_impact`** — tác động đến FPT Camera (object)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `overall` | enum(sentiment) | pub |
| `summary` | text | pub |
| `opportunities` | text[] | |
| `risks` | text[] | |
| `source_ids` | source_ids | |

### `competitor_watch` — theo dõi đối thủ (list)

Mỗi item là **một diễn biến** của một đối thủ (một đối thủ có thể có nhiều item). Giữ tên `competitor` nhất quán giữa các bản tin để frontend nhóm theo đối thủ.

| Field | Kiểu | Mức | Ghi chú |
| --- | --- | --- | --- |
| `id` | text | luôn | |
| `competitor` | text | pub | Tên thương hiệu/doanh nghiệp. |
| `development` | text | pub | Diễn biến mới. |
| `development_type` | enum(`product_launch`\|`pricing`\|`promotion`\|`channel`\|`partnership`\|`marketing`\|`service`\|`financial`\|`other`) | null được | Frontend dùng làm badge/lọc. |
| `channel` | text | null được | Kênh liên quan. |
| `pricing_or_promo` | text | null được | Giá/khuyến mãi nếu có. |
| `threat_level` | enum(level) | pub | Mức đe dọa với FPT Camera. |
| `implication_for_fpt_camera` | text | pub | |
| `suggested_response` | text | null được | Phản ứng đề xuất. |
| `observed_at` | date | null được | |
| `source_ids` | source_ids | | |

### `sources` — nguồn (list)

| Field | Kiểu | Mức |
| --- | --- | --- |
| `id` | text | luôn; duy nhất |
| `title` | text | pub |
| `publisher` | text | pub |
| `url` | URL http(s) | pub |
| `published_at` | date | tùy chọn, null được |
| `accessed_at` | date | pub |

Khi `published`, `sources` không được rỗng.

## Chuyển đổi từ schema 1.0

| 1.0 | 2.0 |
| --- | --- |
| `executive_summary` | Giữ nguyên, thêm `overall_sentiment`, `data_gaps`. |
| `market_metrics[]` | `market_dashboard[]` (kiểu `Metric`, thêm `category`, `direction`, `note`). Chỉ số chi tiết chuyển vào `financial_markets.metrics` / `retail_consumer.metrics` / `weekly_macro_watch.key_metrics`. |
| `insights[]` | `macro_24h.items`, `financial_markets.highlights`, `weekly_macro_watch.themes` tùy chủ đề. |
| `b2c_signals[]` | `retail_consumer.trends` và `b2c_traffic_lights`. |
| `sources[]` | Giữ nguyên, thêm `published_at` (tùy chọn). |
| `edition.session` | Chính thức hóa: `morning`/`afternoon`/`evening`/`adhoc`. |

## Quy tắc toàn vẹn

1. Mọi `source_ids` (ở bất kỳ đâu trong file) phải trỏ tới một `id` có thật trong `sources`.
2. `id` trong mỗi list phải duy nhất.
3. Giới hạn số phần tử: `market_dashboard` ≤ 12, `must_read` ≤ 5, `scenarios_7d` đúng 3.
4. Khi `edition.status` là `"published"`:
   - mọi field **pub** phải có giá trị; `sources` không rỗng, mỗi nguồn có `url` http(s);
   - mọi `source_ids` không được rỗng — **mọi con số, insight, tín hiệu, khuyến nghị phải có nguồn**;
   - `Metric` có `value` null phải có `note` giải thích;
   - `scenarios_7d` đủ 3 loại `base`, `upside`, `downside`;
   - mỗi `pricing_watch` có `price` hoặc `promo`.
5. Không có số liệu thì để `null`, **không bịa**, và ghi vào `executive_summary.data_gaps`. Frontend phải hiển thị `null` là "chưa có dữ liệu" và list rỗng là "chưa có mục nào".
6. Field mới (không bắt buộc) có thể được thêm vào mà không cần đổi `schema_version`; frontend và validator bỏ qua field không biết.

## Kiểm tra

```bash
python3 scripts/validate_data.py                                      # kiểm tra data/latest.json
python3 scripts/validate_data.py data/latest.json data/archive/X.json # kiểm tra file cụ thể
python3 scripts/validate_data.py --allow-legacy data/archive/*.json   # kiểm tra toàn bộ archive (gồm file 1.0 cũ)
```

Script chỉ dùng Python standard library, trả exit code `0` nếu hợp lệ, `1` nếu có lỗi. Không có `--allow-legacy` thì file `schema_version` 1.0 bị từ chối, để dữ liệu mới luôn theo 2.0.
