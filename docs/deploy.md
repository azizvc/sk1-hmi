# Deploy on the SK1

## 1. Backup

- eMMC image / `printer.cfg` / `moonraker.conf`
- Stock `LKS.tft`

## 2. Disable mksclient

```bash
sudo killall -9 mksclient || true
cd /home/mks/Desktop/myfile/klipper_twotree_sk1/build
sudo mv mksclient mksclient.disabled
```

Make sure no `start.sh` / cron job restarts the old client.

## 3. Install the bridge

```bash
sudo mkdir -p /opt/sk1-hmi /etc/sk1-hmi
sudo cp -r bridge/sk1_hmi /opt/sk1-hmi/
sudo cp bridge/requirements.txt /opt/sk1-hmi/
sudo python3 -m venv /opt/sk1-hmi/.venv
sudo /opt/sk1-hmi/.venv/bin/pip install -r /opt/sk1-hmi/requirements.txt
sudo cp packaging/config.example.toml /etc/sk1-hmi/config.toml
sudo cp packaging/sk1-hmi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sk1-hmi
sudo journalctl -u sk1-hmi -f
```

Adjust `serial` / Moonraker host in `/etc/sk1-hmi/config.toml`.

On some SK1 images the service uses Moonraker’s Python plus a `deps/` tree instead of a venv — match whatever already works on the board (see `packaging/sk1-hmi.service`).

## 4. Flash the HMI

Follow [flash-tft.md](flash-tft.md).

## 5. Smoke test

- Home shows live temps
- Pause / resume during a print
- Fans / case light
- Move blocked while printing
- Wi‑Fi icon → network page shows IP
- After killing the process, systemd brings the service back up
