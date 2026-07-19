#!/usr/bin/env bash
# One-shot GitHub setup for this repo: labels, milestones, umbrella issues,
# phase releases, and main branch protection (requires CI check names).
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-thanhhale288/data-economy}"

need_gh() {
  if ! command -v gh >/dev/null 2>&1; then
    echo "gh CLI not found. Install: https://cli.github.com/" >&2
    exit 1
  fi
  if ! gh auth status -h github.com >/dev/null 2>&1; then
    echo "gh is not authenticated. Run: gh auth login" >&2
    exit 1
  fi
}

ensure_label() {
  local name="$1" color="$2" desc="$3"
  if gh label list --repo "$REPO" --json name --jq '.[].name' | grep -Fxq "$name"; then
    echo "label exists: $name" >&2
  else
    gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" >&2
    echo "label created: $name" >&2
  fi
}

ensure_milestone() {
  local title="$1" desc="$2"
  local existing
  existing="$(gh api "repos/$REPO/milestones?state=all" --jq ".[] | select(.title==\"$title\") | .number" | head -1 || true)"
  if [[ -n "$existing" ]]; then
    echo "milestone exists: $title (#$existing)" >&2
    printf '%s\n' "$existing"
  else
    gh api "repos/$REPO/milestones" -f title="$title" -f description="$desc" --jq '.number'
  fi
}

ensure_umbrella_issue() {
  local title="$1" milestone_title="$2" body="$3"
  local existing
  existing="$(gh issue list --repo "$REPO" --state all --json number,title --jq ".[] | select(.title==\"$title\") | .number" | head -1 || true)"
  if [[ -n "$existing" ]]; then
    echo "issue exists: $title (#$existing)" >&2
  else
    gh issue create --repo "$REPO" --title "$title" --milestone "$milestone_title" --label "ready-for-agent" --body "$body" >&2
  fi
}

ensure_release() {
  local tag="$1" target="$2" title="$3" notes="$4"
  if gh release view "$tag" --repo "$REPO" >/dev/null 2>&1; then
    echo "release exists: $tag" >&2
  else
    gh release create "$tag" --repo "$REPO" --target "$target" --title "$title" --notes "$notes" >&2
    echo "release created: $tag" >&2
  fi
}

protect_main() {
  # Requires admin. Job names must match .github/workflows/ci.yml
  gh api -X PUT "repos/$REPO/branches/main/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Backend tests", "Frontend build"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
  echo "branch protection applied on main (require CI)" >&2
}

main() {
  need_gh
  local with_protection=0
  if [[ "${1:-}" == "--with-protection" ]]; then
    with_protection=1
  fi
  echo "Bootstrapping GitHub for $REPO"

  ensure_label "ready-for-agent" "0E8A16" "Agent can implement without more human input"
  ensure_label "needs-human" "D93F0B" "Needs a human decision"
  ensure_label "needs-triage" "FBCA04" "Not yet classified"
  ensure_label "needs-info" "C5DEF5" "Waiting on more information"
  ensure_label "wontfix" "FFFFFF" "Will not implement"
  ensure_label "phase-1" "5319E7" "Phase 1 macro crawlers"
  ensure_label "phase-2" "1D76DB" "Phase 2 enterprise digital"
  ensure_label "phase-3" "BFDADC" "Phase 3 clean / features / ML"

  m1="$(ensure_milestone "Phase 1 — Macro crawlers" "GSO/NSO IIP + OECD INDIGO@VNM + EA20 peer. Done on main via PR #1.")"
  m2="$(ensure_milestone "Phase 2 — Enterprise digital" "Listed companies, CafeF BCTC, digital metrics, shop matcher. Done via PR #2.")"
  m3="$(ensure_milestone "Phase 3 — Clean, features & ML" "Cleaning pipeline, feature engineering, ARIMA/XGBoost/LSTM for IIP Section C.")"
  echo "milestones: phase1=#$m1 phase2=#$m2 phase3=#$m3" >&2

  # Close completed milestones if open
  for num in "$m1" "$m2"; do
    state="$(gh api "repos/$REPO/milestones/$num" --jq '.state')"
    if [[ "$state" == "open" ]]; then
      gh api -X PATCH "repos/$REPO/milestones/$num" -f state=closed >/dev/null
      echo "closed milestone #$num" >&2
    fi
  done

  ensure_umbrella_issue "Phase 3 umbrella — Clean, features & ML" "Phase 3 — Clean, features & ML" "$(cat <<'EOF'
Tracking issue for Phase 3 (roadmap tasks 10–12).

Detailed tickets stay in local markdown (do not duplicate):
- `.scratch/handoff-phase3.md`
- `.scratch/phase3/` (when created)
- `.cursor/skills/project-roadmap/SKILL.md` tasks 10–12

Scope:
1. Cleaning pipeline / DAGs
2. Feature engineering (no fake MEI_BCI)
3. Train + evaluate ARIMA / XGBoost|LightGBM / LSTM; model registry + API

Constraints: no invented GSO/OECD/CafeF numbers; Digital VA locked; 10 tickers including BMP (not BWE).
EOF
)"

  # Releases point at merge commits on main
  ensure_release "v0.1.0-phase1" "410f3731a314b8595d3368e695c0ef802e9e4d37" \
    "v0.1.0 — Phase 1 macro crawlers" \
    "GSO/NSO IIP + PX-Web; OECD INDIGO@VNM + MEI_IP@EA20 peer; ADR-0001. Merged via PR #1."

  ensure_release "v0.2.0-phase2" "d8762bfd900cd213906c3a20ca1b6b509b2e593d" \
    "v0.2.0 — Phase 2 enterprise digital" \
    "10 listed firms (BMP not BWE); CafeF quarterly BCTC; digital metrics; shop matcher. Marketplace live deferred. Merged via PR #2."

  if [[ "$with_protection" -eq 1 ]]; then
    echo
    echo "Applying branch protection (may fail without admin)..." >&2
    if ! protect_main; then
      echo "WARN: branch protection failed. Enable manually: Settings → Branches → Require status checks: Backend tests, Frontend build" >&2
    fi
  else
    echo
    echo "Skipped branch protection (pass --with-protection to apply)." >&2
    echo "Manual: Settings → Branches → Protect main → require checks: Backend tests, Frontend build" >&2
  fi

  echo
  echo "Done. Repo: https://github.com/$REPO"
}

main "$@"
