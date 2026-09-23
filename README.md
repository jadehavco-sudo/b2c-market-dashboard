# b2c-market-dashboard
Automated B2C market intelligence dashboard — dashboard điều hành B2C, có module thị trường Camera và theo dõi đối thủ phục vụ FPT Camera.

## Luồng dữ liệu

```
Claude scheduled research → latest.json + archive → GitHub Pages dashboard
```

- `data/latest.json` — bản tin mới nhất, dashboard chỉ đọc file này.
- `data/archive/` — mỗi lần cập nhật lưu một bản theo timestamp.
- `scripts/validate_data.py` — kiểm tra dữ liệu (Python standard library): `python3 scripts/validate_data.py`
- `docs/data-contract.md` — cấu trúc dữ liệu cố định giữa automation và dashboard.
- `CLAUDE.md` — nguyên tắc cho automation.

## Schema dữ liệu (2.0)

`data/latest.json` dùng `schema_version` `"2.0"` với các section:

| Nhóm | Section |
| --- | --- |
| Điều hành | `executive_summary`, `market_dashboard`, `b2c_traffic_lights`, `recommendations`, `decisions_today` |
| Vĩ mô & thị trường | `weekly_macro_watch`, `macro_24h`, `financial_markets`, `retail_consumer` |
| Nhìn trước | `scenarios_7d`, `events_next_24h`, `must_read` |
| Camera / FPT Camera | `camera_market_watch`, `competitor_watch` |
| Nguồn | `sources` |

Chi tiết field xem `docs/data-contract.md`. Các file archive cũ dùng schema 1.0; kiểm tra toàn bộ archive bằng:

```bash
python3 scripts/validate_data.py --allow-legacy data/archive/*.json
```
