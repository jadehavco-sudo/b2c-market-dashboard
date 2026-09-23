# Data contract

Tài liệu này mô tả hợp đồng dữ liệu giữa **automation cập nhật dữ liệu** và **dashboard (frontend)**.

## Nguyên tắc chính

- Dashboard **chỉ đọc duy nhất** file `data/latest.json`. Không đọc file nào khác, không gọi API nào khác.
- `data/latest.json` luôn là **phiên bản mới nhất** của bản tin.
- Mỗi lần cập nhật, một bản sao y hệt được lưu vào `data/archive/` để giữ lịch sử.
- Cấu trúc dữ liệu phải **ổn định**: automation chỉ thay đổi *giá trị*, không đổi tên field, không đổi kiểu dữ liệu, không bỏ field bắt buộc. Nhờ vậy frontend không phải sửa mỗi ngày.
- Mọi thay đổi cấu trúc (breaking change) phải tăng `schema_version` và cập nhật tài liệu này, script validate và frontend trong cùng một thay đổi có review của con người.

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

Tên file archive dùng timestamp UTC lấy từ `updated_at`, định dạng `YYYY-MM-DDTHHMMSSZ.json`, ví dụ `2026-09-23T060000Z.json` (bỏ dấu `:` để tương thích mọi hệ điều hành). File archive đã tạo thì không sửa lại.

## Cấu trúc `latest.json` (schema_version 1.0)

```jsonc
{
  "schema_version": "1.0",               // string, bắt buộc
  "updated_at": "2026-09-23T06:00:00Z",  // ISO 8601 có múi giờ (UTC), bắt buộc
  "edition": {                           // object, bắt buộc
    "id": "2026-09-23",                  // định danh bản tin
    "number": 1,                         // số thứ tự bản tin (0 = placeholder)
    "title": "…",
    "status": "published",               // "placeholder" | "draft" | "published"
    "language": "vi"
  },
  "executive_summary": {                 // object, bắt buộc
    "headline": "…",                     // string
    "summary": "…",                      // string
    "key_points": ["…"]                  // list string
  },
  "market_metrics": [                    // list, bắt buộc
    {
      "id": "…",                         // duy nhất trong list
      "label": "…",
      "value": 12.3,                     // number hoặc null nếu chưa có
      "unit": "%",                       // string hoặc null
      "change": 1.2,                     // number hoặc null
      "change_unit": "pp",               // string hoặc null
      "period": "2026-Q3",               // string hoặc null
      "source_ids": ["src-1"]            // id trong `sources`
    }
  ],
  "insights": [                          // list, bắt buộc
    {
      "id": "…", "title": "…", "description": "…",
      "category": "…",                   // string hoặc null
      "impact": "high",                  // "high" | "medium" | "low" | null
      "source_ids": ["src-1"]
    }
  ],
  "b2c_signals": [                       // list, bắt buộc
    {
      "id": "…", "signal": "…", "description": "…",
      "direction": "up",                 // "up" | "down" | "flat" | null
      "strength": "strong",              // "strong" | "moderate" | "weak" | null
      "source_ids": ["src-1"]
    }
  ],
  "sources": [                           // list, bắt buộc
    {
      "id": "src-1",
      "title": "…",
      "publisher": "…",
      "url": "https://…",
      "accessed_at": "2026-09-23"
    }
  ]
}
```

## Quy tắc toàn vẹn

1. Mọi `source_ids` phải trỏ tới một `id` có thật trong `sources`.
2. `id` trong mỗi list phải duy nhất.
3. Khi `edition.status` là `"published"`:
   - `sources` không được rỗng, mỗi nguồn có `url` http(s) thật;
   - mọi `market_metrics` phải có `value` khác null và có `source_ids`;
   - mọi `insights` và `b2c_signals` phải có `source_ids`.
4. Không có số liệu thì để `null`, **không bịa**. Frontend phải hiển thị `null` là "chưa có dữ liệu".
5. Field mới (không bắt buộc) có thể được thêm vào mà không cần đổi `schema_version`; frontend phải bỏ qua field nó không biết.

## Kiểm tra

```bash
python3 scripts/validate_data.py                       # kiểm tra data/latest.json
python3 scripts/validate_data.py data/archive/*.json   # kiểm tra file archive
```

Script chỉ dùng Python standard library, trả exit code `0` nếu hợp lệ, `1` nếu có lỗi.
