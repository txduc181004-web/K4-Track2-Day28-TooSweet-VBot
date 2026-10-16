# VBot Workplace: Production Capstone

Kiến trúc và báo giá cho VBot (2.000 DAU) trên Google Cloud asia-southeast1. Tổng **$11,896.84/tháng ($5.95/DAU)**.

## Bài nộp

| File | Nội dung |
|---|---|
| `deliverables/G09_slide.pdf` | 15 slide nội dung (16:9) + 2 trang phụ lục |
| `deliverables/G09_baogia.xlsx` | Sheet `BaoGia` (41 dòng + TOTAL), `BangChung` (E01–E34, có ảnh ở cột E), `GiaDinh` (sizing) |

Mã nhóm: G09.

## Dựng lại sau khi đổi giả định

Mọi con số nằm trong `model/vbot_model.py` (giả định ở đầu file: `A`, `TIERS`, `SANDBOX`, `STORAGE`; đơn giá ở `P`).

```bash
python3 model/vbot_model.py                 # in tổng theo component
python3 model/scenarios.py                  # đòn bẩy tiết kiệm, DAU x2, giá token ±
.venv/bin/python model/build_quote.py G09   # -> deliverables/G09_baogia.xlsx
(cd tools && node check_quote.js ../deliverables/G09_baogia.xlsx)   # validator trích nguyên văn từ trang đề
python3 slides/build_slides.py G09
node tools/render_pdf.js slides/slides.html deliverables/G09_slide.pdf
```

Chụp lại bằng chứng (Chrome headless, chọn region Singapore, khoanh đỏ dòng giá): `node tools/capture.js [E01 ...]` → `evidence/screenshots/`.

## Quyết định chính

- **LLM qua API Vertex AI, routing theo cấp**: Gemini 3.1 Flash-Lite (cấp 1, 2, 5, executor cấp 4), gpt-oss-120b (cấp 3, planner cấp 4), Gemini 3.8 Flash là model tham chiếu và leo thang. Gemini 3.8 Flash tính theo giá Standard $1.50/$7.50 (không dùng giá giới thiệu tới hết 2026).
- **Global endpoint**: các model trên chưa có regional Singapore (E19). Dữ liệu lưu trữ vẫn ở asia-southeast1.
- **GKE Autopilot** regional cho mọi service; sandbox dùng gVisor + Spot Pod.
- **Cloud SQL PostgreSQL HA + pgvector**, Redis Standard, Pub/Sub, GCS multi-region ASIA.

## Giả định hội đồng sẽ hỏi

| Giả định | Giá trị | Ở đâu |
|---|---|---|
| Request/người/ngày | 25 | `A['req_per_user_day']` |
| Tỉ lệ cấp 1–5 | 52/22/12/9/5% | `TIERS[*].share` |
| Cache prefix | 25–60% theo cấp | `TIERS[*].calls[*].cache` |
| Leo thang lên model tham chiếu | 5% / 10% / 8% / 15% | `TIERS` |
| Flex cho agent nền | 90% | `TIERS` L4 |
| Spot cho sandbox | 80% | `SANDBOX['spot_share']` |
| CUD 1 năm | pod nền + Cloud SQL HA | `P['*_cud1']` |
| Nhân sự | 1,5 FTE × $2,800 | `ops_labor` |

## Phân vai khi bảo vệ (7 phút)

| Vai | Slide |
|---|---|
| Kiến trúc sư trưởng | 1–4, 13 (tổng, chi phí) |
| Model serving | 6, 7 |
| Data và workspace | 3, 8, 9 (workspace) |
| Sandbox, bảo mật, governance | 9 (sandbox), 10 |
| Cloud, HA, vận hành | 11, 12, 14 |

Slide 15 là đáp án ngắn cho 6 câu hỏi mẫu của hội đồng.
