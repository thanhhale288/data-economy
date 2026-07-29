# needGit — Agent / foundation

## 1. mattpocock/skills — DONE

```bash
npx skills add mattpocock/skills
```

Đã có `.agents/skills/`. Setup: `/setup-matt-pocock-skills` → local `.scratch/`, triage labels, `CONTEXT.md`.

## 2. CodeGraph MCP — chưa cài

```bash
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
codegraph install --target=cursor --yes
cd "/Users/hale/Code/AI in Data Economy" && codegraph init
```

Thay `codebase-memory-mcp` (không dùng). Restart Cursor sau khi cài.

## 3. AGENTS.md + CONTEXT.md

Luôn load. Domain / công thức chỉ từ đây + `docs/adr/`.
