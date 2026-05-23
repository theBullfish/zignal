#!/usr/bin/env bash
# Resume-trigger for the LISTS surface after Temple outage.
# Closes L1.14 + L1.16 by deploying the post-audit fixes and
# verifying the timer fires cleanly.
#
# Usage:  bash scripts/resume_when_temple_up.sh
# Exit:   0 on successful deploy+verify; non-zero if Temple still
#         down or any step failed. Wrap in a loop / cron if needed:
#           until bash scripts/resume_when_temple_up.sh; do sleep 60; done

set -u

TEMPLE_TS_NAME="pop-os"
TEMPLE_HOST="watchdog@100.79.198.99"
TEMPLE_SSH_PASS="Santana@11"
LISTS_DIR="/home/z13/zignal/zignal/lists"
SVC_FILE="/home/z13/zignal/zignal-lists.service"

echo "[resume] checking Temple via Tailscale..."
status_line=$(tailscale status 2>/dev/null | grep " ${TEMPLE_TS_NAME} " || true)
if [[ -z "$status_line" ]]; then
  echo "[resume] FAIL — Temple ($TEMPLE_TS_NAME) not in tailscale status"
  exit 2
fi
if echo "$status_line" | grep -q "offline"; then
  echo "[resume] WAIT — Temple still offline: $status_line"
  exit 3
fi
echo "[resume] OK — Temple is up:"
echo "         $status_line"

echo "[resume] rsync zignal/lists -> Temple..."
sshpass -p "$TEMPLE_SSH_PASS" rsync -az --delete \
  "$LISTS_DIR/" "$TEMPLE_HOST:/mnt/work/zignal/zignal/lists/" || {
    echo "[resume] FAIL — rsync zignal/lists"; exit 4; }

echo "[resume] rsync zignal-lists.service -> Temple /tmp..."
sshpass -p "$TEMPLE_SSH_PASS" rsync -az \
  "$SVC_FILE" "$TEMPLE_HOST:/tmp/zignal-lists.service" || {
    echo "[resume] FAIL — rsync service file"; exit 5; }

echo "[resume] install + reload + restart timer on Temple..."
sshpass -p "$TEMPLE_SSH_PASS" ssh "$TEMPLE_HOST" "
  echo $TEMPLE_SSH_PASS | sudo -S cp /tmp/zignal-lists.service /etc/systemd/system/ &&
  sudo systemctl daemon-reload &&
  sudo systemctl restart zignal-lists.timer &&
  sudo systemctl start zignal-lists.service
" || { echo "[resume] FAIL — systemd ops"; exit 6; }

echo "[resume] tail journalctl..."
sshpass -p "$TEMPLE_SSH_PASS" ssh "$TEMPLE_HOST" \
  'journalctl -u zignal-lists.service -n 20 --no-pager' || true

echo "[resume] inspect lists.json..."
sshpass -p "$TEMPLE_SSH_PASS" ssh "$TEMPLE_HOST" \
  'python3 -c "
import json
d = json.load(open(\"/mnt/work/zignal/state/lists.json\"))
print(\"count:\", d[\"count\"])
print(\"remote_status:\", d.get(\"remote_status\"))
print(\"emit_status:\", d.get(\"emit_status\"))
print(\"generated_at:\", d.get(\"generated_at\"))
"' || { echo "[resume] FAIL — lists.json read"; exit 7; }

echo "[resume] DONE — deploy + first fire successful."
exit 0
