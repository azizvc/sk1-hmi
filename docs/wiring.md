# Wiring and UART

## On the SK1 (production)

The stock panel is already wired to `/dev/ttyS1` on the MKS SKIPR Mini SoC. The TFT (USART HMI) runs at **115200** baud — the same value in `Program.s` / compile settings and in `/etc/sk1-hmi/config.toml`.

```toml
[hmi]
serial = "/dev/ttyS1"
baud = 115200
```

## Bench setup (PC + USB-TTL)

| Panel | USB-TTL 3.3 V |
|-------|----------------|
| 5V    | 5V (capable supply; USB-TTL alone often cannot power the panel) |
| GND   | GND |
| TX    | RX |
| RX    | TX |

**Never** use a 5 V TTL adapter on the data pins.

## Conflict with mksclient

Only one process can open `/dev/ttyS1`. Before running the bridge:

```bash
sudo killall -9 mksclient || true
# and rename/disable the TwoTrees binary or start.sh
```

See [deploy.md](deploy.md).
