# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

## Overview

Kanata keyboard remapping configuration for macOS (Apple Silicon). Kanata intercepts physical key events and remaps them via a virtual HID device using the Karabiner DriverKit driver.

## Running

```sh
sudo ./kanata_macos_arm64 --cfg layouts/qwerty.cfg
```

- Requires the Karabiner DriverKit VirtualHIDDevice system extension to be installed and approved in System Settings.
- **Karabiner Elements must not be running** — it conflicts for exclusive keyboard access. Quit it before starting kanata.
- Emergency exit while running: `lctl + spc + esc` (physical key positions, before remapping).
- Prefer `kanata_macos_arm64`, the standard build without external command execution support.
- The `kanata_macos_cmd_allowed_arm64` variant supports executing external programs via `cmd` actions when `danger-enable-cmd yes` is set. This is unrelated to the macOS Command (⌘) key. None of the current configs require it. Commands run with Kanata's privileges, so enabling this while running with `sudo` is a security risk.

## Config format

Configs live in `layouts/`: `colemak-dh.cfg` and `qwerty.cfg`. They use Kanata's S-expression format. The README documents setup and layout behavior. Binaries and machine-local agent settings must not be committed.

Validate changes with `./kanata_macos_arm64 --check --cfg layouts/qwerty.cfg` (and likewise for Colemak-DH). After layout changes, regenerate SVGs with `python3 images/generate-layouts.py` and PNGs with `rsvg-convert`; see the README.

Key blocks:

- `defcfg` — global settings (e.g., `process-unmapped-keys`)
- `defsrc` — declares which physical keys are intercepted
- `deflayer` — defines what each key does on a given layer (use `_` for passthrough)
- `defalias` — named key behaviors like `tap-hold-press` and `layer-toggle`

Kanata docs: https://github.com/jtroo/kanata
