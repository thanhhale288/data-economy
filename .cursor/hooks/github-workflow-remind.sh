#!/usr/bin/env bash
# Reminds the agent to follow .cursor/skills/github-workflow/SKILL.md
# on git/gh commands. Always allows the command.
set -euo pipefail

input="$(cat)"
command="$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("command") or "")' 2>/dev/null || true)"

if printf '%s' "$command" | grep -Eq 'git commit|git push|gh pr |gh release|gh issue|github-bootstrap'; then
  python3 -c 'import json; print(json.dumps({
    "permission": "allow",
    "agent_message": "Follow project skill .cursor/skills/github-workflow/SKILL.md: no secrets; HEREDOC commit message (why); PR uses .github/PULL_REQUEST_TEMPLATE.md + .scratch links; prefer gh; after phase merge create release; tickets stay in .scratch/."
  }))'
  exit 0
fi

echo '{ "permission": "allow" }'
exit 0
