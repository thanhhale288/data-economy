---
name: plain-task-close
description: >-
  Mandatory default closing message after every completed task (any chat, not only
  lazy-to-complete): plain Vietnamese summary with what changed, how it was done,
  limitations, and jargon explained inline. Runs automatically when implementation
  is done — user does not need to ask. No generic bullets or unexplained abbreviations.
---

# Plain task close — giải thích tự động sau mỗi task

**Mặc định bắt buộc:** Mỗi khi agent **hoàn thành một task** (code, docs, fix, PR…) và sắp gửi tin nhắn kết thúc cho user → **phải** viết theo skill này **ngay trong tin nhắn đó**. User **không** cần hỏi “giải thích dễ hiểu”.

**Announce** (dòng đầu phần đóng task):  
`Đang dùng skill plain-task-close — tóm tắt dễ hiểu.`

Skill này **chỉ viết lời giải thích** (không implement thêm). Khác `what-i-dont-know` (tour nhiều task cũ, read-only, khi user chủ động hỏi catch-up).

## Khi nào chạy (bắt buộc)

| Tình huống | plain-task-close |
|------------|------------------|
| Vừa xong task — bất kỳ chat nào | **Có — mặc định, không đợi user hỏi** |
| Cuối task trong lazy-to-complete (W4 Ship) | **Có** |
| User chỉ hỏi câu hỏi, chưa làm task | Không |
| Giữa task đang code | Không |
| Tour nhiều task đã bỏ qua (catch-up) | Dùng `what-i-dont-know` |

**Thứ tự tin nhắn cuối task:** plain-task-close → testing results → Git/PR (nếu có) → STOP.  
Không thay bằng bullet “đã xong / tests pass” rồi chờ user hỏi thêm.

## Giọng bắt buộc

- **Tiếng Việt** trừ khi user yêu cầu ngôn ngữ khác.
- Viết cho người **không cần mở lại code** để hiểu đã làm gì.
- Mỗi ý = **cụ thể** (trang/API/hành vi / dữ liệu thật vs thiếu), không câu chung chung.

### Cấm

- Bullet kiểu “đã cập nhật backend”, “đã fix bug”, “tests passed” **không** nói rõ hậu quả.
- Viết tắt / thuật ngữ English **không** giải thích lần đầu (PR, AC, E2E, OCR, parquet, registry…).
- Dump diff, log dài, list file không kèm *vì sao user quan tâm*.
- Copy nguyên handoff kỹ thuật không diễn giải.
- Kết thúc task rồi **chỉ** nói “xong rồi” / “đã merge” — user phải tự explore.

### Thuật ngữ

Lần đầu gặp trong bản tóm tắt:

```text
<Thuật ngữ> (<nghĩa ngắn>) — trong task này: <1 câu ví dụ>
```

Ưu tiên nghĩa từ `CONTEXT.md` / `AGENTS.md`. **Không** đọc `docs/knowledge.md`.

## Output bắt buộc (mỗi task)

Dùng đúng khung — chi tiết mẫu: [reference.md](reference.md).

```markdown
## Task #<N> — <tên dễ hiểu, không mã task>

### Một câu
<1 câu: sau task này app/pipeline/demo thay đổi gì>

### Bạn sẽ thấy gì (đã làm được gì)
- …

### Làm thế nào (step-by-step, không code)
1. …
2. …

### Hạn chế / chưa làm được
- …

### Thuật ngữ trong task này (nếu có)
- …

### Git (một dòng)
Branch `…` · PR …
```

**Một câu** và **Bạn sẽ thấy gì** là bắt buộc. **Làm thế nào** ít nhất 3 bước nếu task không trivial.

Task nhỏ (1 file, 1 câu hỏi đã trả lời): vẫn có **Một câu** + **Bạn sẽ thấy gì**; có thể rút gọn các mục còn lại nhưng **không** bỏ hẳn giải thích.

## Chất lượng — tự kiểm trước khi gửi

- [ ] Người không đọc repo vẫn hiểu *đã giao được gì*.
- [ ] Mọi viết tắt lần đầu đều có nghĩa trong ngoặc.
- [ ] Có ít nhất 1 câu *dữ liệu thật vs placeholder / thiếu nguồn* nếu task đụng số liệu.
- [ ] **Hạn chế** nói rõ phần cố ý chưa làm — user không phải explore để đoán.

## Anti-patterns

- Template rỗng / placeholder `…` gửi user.
- Chỉ liệt kê file path không giải thích hành vi.
- Dùng “implemented”, “refactored”, “integrated” không nói *cái gì*.
- Coi plain-task-close là “khi user hỏi mới viết”.
