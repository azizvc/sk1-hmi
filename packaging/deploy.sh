#!/usr/bin/env bash
set -euo pipefail
HOST="${1:?usage: deploy.sh user@printer-ip}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

rsync -av --delete \
  "$ROOT/bridge/sk1_hmi" \
  "$ROOT/bridge/requirements.txt" \
  "$ROOT/packaging/config.example.toml" \
  "$ROOT/packaging/config.printer.toml" \
  "$ROOT/packaging/sk1-hmi.service" \
  "$ROOT/packaging/disable-mksclient.sh" \
  "$HOST:/tmp/sk1-hmi-stage/"

ssh "$HOST" bash -s <<'EOF'
set -euo pipefail
sudo mkdir -p /opt/sk1-hmi /etc/sk1-hmi
sudo cp -r /tmp/sk1-hmi-stage/sk1_hmi /opt/sk1-hmi/
sudo cp /tmp/sk1-hmi-stage/requirements.txt /opt/sk1-hmi/
if [[ ! -d /opt/sk1-hmi/.venv ]]; then
  sudo python3 -m venv /opt/sk1-hmi/.venv
fi
sudo /opt/sk1-hmi/.venv/bin/pip install -r /opt/sk1-hmi/requirements.txt
if [[ ! -f /etc/sk1-hmi/config.toml ]]; then
  if [[ -f /tmp/sk1-hmi-stage/config.printer.toml ]]; then
    sudo cp /tmp/sk1-hmi-stage/config.printer.toml /etc/sk1-hmi/config.toml
  else
    sudo cp /tmp/sk1-hmi-stage/config.example.toml /etc/sk1-hmi/config.toml
    sudo sed -i 's/dry_run = true/dry_run = false/' /etc/sk1-hmi/config.toml
  fi
fi
sudo cp /tmp/sk1-hmi-stage/sk1-hmi.service /etc/systemd/system/
bash /tmp/sk1-hmi-stage/disable-mksclient.sh || true
sudo systemctl daemon-reload
sudo systemctl enable --now sk1-hmi
sudo systemctl restart sk1-hmi
sudo systemctl --no-pager status sk1-hmi || true
EOF
