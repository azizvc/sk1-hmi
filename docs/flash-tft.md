# Flashing the `.tft` to the panel

1. Back up the stock `LKS.tft`.
2. In **USART HMI** (required for TJC), compile the project → produce `sk1-hmi.tft`.  
   (Nextion Editor is fine for prototyping only — do not flash a Nextion-only `.tft` to the SK1 panel.)
3. Format a microSD card as **FAT32** and copy the `.tft` to the root (exactly one `.tft` file).
4. Power off the printer / panel.
5. Open the panel and insert the microSD into the rear slot.
6. Power on (cable + supply). Wait for **Update finished** (or equivalent).
7. Power off, remove the card, reassemble.
8. Confirm the UI matches the build you just flashed (e.g. network `t_ip` exists after adding it).

If the flash fails: editor model ≠ panel label, card not FAT32, or a pure Nextion `.tft` on a TJC panel without conversion.
