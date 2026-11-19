#!/usr/bin/env bash
# Stock Makerbase UART bring-up for TJC panel on SK1.
# Mirrors start.sh pinmux + gpio export. Never toggles gpio79 value.
set -euo pipefail

if [[ -x /root/io ]]; then
  /root/io -4 0xff100028 0x010000
else
  echo "uart-init: /root/io missing" >&2
fi

if [[ ! -d /sys/class/gpio/gpio79 ]]; then
  echo 79 > /sys/class/gpio/export || true
fi
if [[ -d /sys/class/gpio/gpio79 ]]; then
  echo out > /sys/class/gpio/gpio79/direction || true
  chmod 777 /sys/class/gpio/gpio79/value || true
fi
