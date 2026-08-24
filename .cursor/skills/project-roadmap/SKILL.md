---
name: project-roadmap
description: Dẫn dắt task tiếp theo theo docs/evol-1.md (OBEC / thiết bị đo TMĐT). Dùng khi hỏi "task tiếp theo", "làm gì bây giờ", "tiến độ dự án", "roadmap", hoặc triển khai evol-1.
disable-model-invocation: true
---

# Project Roadmap — Evol-1 (proposal-v4)

Skill này dẫn backlog **`docs/evol-1.md`** — không còn dùng checklist Epic 1–5 (xem `docs/archive/plan-archive.md` nếu cần lịch sử).

## Nguyên tắc

- **Nguồn sự thật:** `docs/evol-1.md` + `docs/proposal-v4.md` + `CONTEXT.md` + `AGENTS.md`
- **Git:** 1 task = 1 branch = 1 PR — branch name ghi trong evol-1 (vd. `cursor/evol1-task01-remove-invalid-kpis`)
- Làm theo **dependency** trong evol-1 (T08 phụ thuộc T03, v.v.)
- Không bịa số GSO/OECD; không cào listing sàn hàng loạt; không dùng API đóng cho con số vào bài báo

## Quy trình mỗi lần chạy

1. Đọc `docs/evol-1.md` — xác định task chưa xong đầu tiên trong Nhóm A (hoặc Nhóm B sau GVHD).
2. Trình bày: mục tiêu · việc làm · DoD · branch · phụ thuộc.
3. Hỏi user: **guide** hay **implement**.
4. Sau khi xong: tóm tắt + testing + task kế tiếp.

## Thứ tự ưu tiên (tóm tắt)

**Nhóm A — trước GVHD:** T01 → T02, T03 → (T04 → T05) → T07; T08 sau T03.

**Nhóm B — sau GVHD:** T09 công văn → T12 khung VN → T13 gold 500 → T14–T19 ước lượng → T20–T21 báo cáo.

Chi tiết đầy đủ, effort, và kịch bản 15 phút GVHD: **`docs/evol-1.md`**.

## Deliverable 12/2026

Đối chiếu mục 10 `docs/proposal-v4.md`: báo cáo NCKH, bản thảo Anh, dataset/codebook, web demo chỉ tiêu ± CI, pipeline tái lập.
