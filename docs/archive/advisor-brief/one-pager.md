# One-pager — Đo tham gia TMĐT ngành chế tạo từ dữ liệu web

**Buổi gặp GVHD · bộ tài liệu Evol-1 T07 · số liệu cắt tại merge T05 (`main`)**  
In 1 tờ A4 · mọi khẳng định dưới đây có file đứng sau (xem cuối trang).

---

## Một câu định vị (proposal-v4)

Xây **thiết bị đo** tỷ lệ doanh nghiệp chế biến–chế tạo (VSIC ngành C) tham gia thương mại điện tử từ website; **hiệu chuẩn nơi có nhãn quy mô lớn** (dữ liệu mở Nhật), **triển khai nơi thiếu nhãn** (Việt Nam), và **định lượng độ chính xác mất đi khi không còn nhãn**.

Khác v2 (Digital VA / dự báo IIP): sau audit 20–21/8 đã gỡ KPI không bảo vệ được; đề tài neo Eurostat OBEC / thống kê thực nghiệm.

## Đã chạy được *không cần* công văn

| Việc | Kết quả thật | Giới hạn nói rõ |
|------|--------------|-----------------|
| Khung mẫu pilot (T02) | **800 DN** từ nguồn công khai (masothue), 3 division: **10 / 22 / 25** = 300 / 250 / 250 | Không suy rộng quốc gia Section C |
| URL-finder v0 (T03) | Blind trên **28** DN đã biết website: hit **12/28 (42.9%)**; precision khi quyết định **66.7%**; abstain **35.7%** | Search HTML bị chặn → ứng viên chủ yếu suy domain; châu Âu công bố ~83–88% trên mẫu khác — **không so ngang** |
| Thác trích chỉ tiêu v0 (T05) | Cohort **128** site · tải được **89 (69.5%)**; tầng luật: catalog **74%**, giỏ hàng **52%**, MXH **53%**, thanh toán / link sàn **~7%** (*trên fetch_ok*) | Mô tả pilot, **chưa** trọng số / CI; chưa đối chiếu nhãn tay (T06 đang làm) |

## Điểm xin duyệt hôm nay

1. **Duyệt proposal-v4** (thân bài VN + nhánh hiệu chuẩn Nhật trong phạm vi 1 tuần công).  
2. **Ký 2 công văn** đã soạn sẵn: GSO (khung mẫu + bảng A5.2 nếu được) và iDEA (danh bạ website TMĐT).  
3. **Làm rõ nghiệm thu tháng 12** của lab → chỉnh đích sản phẩm.  
4. **Ý kiến nhánh Nhật:** nằm trong đề tài cấp trường, hay chỉ Phụ lục C / hướng phát triển?  
5. Lab có **SV hỗ trợ gán nhãn** (sau khi có handbook T06) không?

## Câu trả lời sẵn nếu bị hỏi “số yếu”

- Hit URL 42.9% là **số thật có phân tích lỗi**, không vá ảo; cải thiện search + LLM decide nằm backlog, không chặn khoa học đo lường.  
- Chưa có P/R vs nhãn vàng vì **đúng quy trình**: handbook + gán tay trước, rồi mới công bố độ chính xác tầng luật / LLM.  
- Nhật chưa chạy (T08): nếu kịp trước báo cáo sẽ có bảng P/R n≈300; nếu không, vẫn còn con số VN + thiết kế hiệu chuẩn trong proposal.

## File đứng sau (đừng bị hỏi “số lấy đâu”)

- Proposal: `docs/proposal-v4.md`  
- Khung: `data/raw/frame_pilot/PROVENANCE.md`  
- URL-finder: `data/processed/url_finder/metrics.json`  
- Chỉ tiêu thô: `data/processed/extraction_cascade/summary.json`  
- Công văn in: `docs/advisor-brief/cong-van-a-gso.md`, `cong-van-b-idea.md`
