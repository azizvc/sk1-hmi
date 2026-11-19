#!/usr/bin/env bash
set -euo pipefail
sudo systemctl stop makerbase-client 2>/dev/null || true
sudo systemctl disable makerbase-client 2>/dev/null || true
sudo killall -9 mksclient 2>/dev/null || true
TARGET="/home/mks/Desktop/myfile/klipper_twotree_sk1/build/mksclient"
if [[ -f "$TARGET" ]]; then
  sudo mv "$TARGET" "${TARGET}.disabled"
  echo "disabled $TARGET"
else
  echo "mksclient binary not found at $TARGET (ok if already disabled)"
fi
echo "makerbase-client stopped/disabled"
