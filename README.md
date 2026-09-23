# b2c-market-dashboard
Automated B2C market intelligence dashboard

## Luồng dữ liệu

```
Claude scheduled research → latest.json + archive → GitHub Pages dashboard
```

- `data/latest.json` — bản tin mới nhất, dashboard chỉ đọc file này.
- `data/archive/` — mỗi lần cập nhật lưu một bản theo timestamp.
- `scripts/validate_data.py` — kiểm tra dữ liệu (Python standard library): `python3 scripts/validate_data.py`
- `docs/data-contract.md` — cấu trúc dữ liệu cố định giữa automation và dashboard.
- `CLAUDE.md` — nguyên tắc cho automation.
