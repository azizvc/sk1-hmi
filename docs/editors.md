# Editors

## Nextion Editor (optional / prototype)

Useful for UI prototyping only. For the SK1 TJC panel, the final flash must be built with **USART HMI**.

A portable copy may live under `tools/editors/nextion/` if you extract it locally (not required for contributors).

## USART HMI (TJC) — required for SK1

Install from the vendor wiki:

http://wiki.tjc1688.com/download/usart_hmi.html

Default Windows path after install:

`C:\Program Files (x86)\USART HMI`

Helper script (optional):

```powershell
.\tools\install_usart_hmi.ps1
```

Workflow: open USART HMI → follow [`hmi/BUILD.md`](../hmi/BUILD.md) → export `hmi/export/sk1-hmi.tft`.
