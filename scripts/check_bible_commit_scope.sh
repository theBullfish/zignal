#!/usr/bin/env bash
# Pre-commit / commit-msg hook: enforces BIBLE rule 7
# ("Commits reference the item") plus L1.10 retro lesson:
# "the L#.## listed in the commit message must actually be [DONE]
#  (or [PARTIAL], [SKIPPED], [BLOCKED], [SUPERSEDED]) in the diff,
#  not still [PENDING]/[DOING]."
#
# Install: ln -s ../../scripts/check_bible_commit_scope.sh
#          .git/hooks/commit-msg
# Or call from another commit-msg hook with $1.
#
# Exit 0 if the message has no L#.## references (BIBLE rule 7
# may not apply to this commit — caller may want to enforce
# "every commit has an L#.##" separately).
# Exit 0 if every L#.## in the message is closed in the staged diff.
# Exit non-zero with a clear error if any referenced L#.## is
# still [PENDING] or [DOING] in the staged plan diff.

set -u

MSG_FILE="${1:-}"
if [[ -z "$MSG_FILE" || ! -f "$MSG_FILE" ]]; then
  echo "[bible-scope] usage: $0 <commit-msg-file>" >&2
  exit 2
fi

# Extract all L#.## refs (allow letter suffixes for branched items).
refs=$(grep -oE 'L[0-9]+\.[0-9]+[a-z]?' "$MSG_FILE" | sort -u || true)
if [[ -z "$refs" ]]; then
  exit 0
fi

# Get staged diff lines that ADD a status appendix.
added=$(git diff --cached --no-color -U0 -- '*BUILD_PLAN.md' '*NOTES.md' \
        '*_BUILD_PLAN.md' '*_NOTES.md' BUILD_PLAN.md NOTES.md \
        2>/dev/null | grep -E '^\+L[0-9]+\.[0-9]+' || true)

if [[ -z "$added" ]]; then
  echo "[bible-scope] WARN — commit references $(echo $refs | tr '\n' ' ')" >&2
  echo "[bible-scope] but no plan/notes diff in staged changes." >&2
  echo "[bible-scope] If this commit closes items, the status lines" >&2
  echo "[bible-scope] should be in the same commit. (continuing)" >&2
  exit 0
fi

closed_statuses='\[(DONE|PARTIAL|SKIPPED|BLOCKED|SUPERSEDED)\]'
fail=0
for ref in $refs; do
  # Did this commit ADD a closing-status line for $ref?
  if ! echo "$added" | grep -qE "^\+${ref}[[:space:]]+${closed_statuses}"; then
    # Maybe $ref was already closed before this commit; check the
    # current plan files for it.
    if git ls-files -- '*BUILD_PLAN.md' '*_BUILD_PLAN.md' BUILD_PLAN.md 2>/dev/null \
         | xargs -r grep -hE "^${ref}[[:space:]]+${closed_statuses}" >/dev/null 2>&1; then
      continue
    fi
    echo "[bible-scope] FAIL — commit message lists ${ref} but" >&2
    echo "             no closing-status line ([DONE]/[PARTIAL]/" >&2
    echo "             [SKIPPED]/[BLOCKED]/[SUPERSEDED]) is in the" >&2
    echo "             staged plan diff and none exists in HEAD." >&2
    echo "             Per L1.10 retro: commit messages must not lie" >&2
    echo "             about closure scope." >&2
    fail=1
  fi
done

exit $fail
