# ASUS ROG Per-Key RGB Control (Windows)

Lightweight per-key RGB keyboard control for ASUS ROG laptops via HID — no Armoury Crate needed.

## Why?

ASUS Armoury Crate is bloated, buggy, and uses excessive resources. This script talks directly to the keyboard's HID interface to set per-key colors, using only Python and `hidapi`.

## Tested on

| Model | PID | Status |
|-------|-----|--------|
| ROG Strix G17 G713PV | `0x19B6` | Working |

Should work on other ROG laptops with the same N-KEY Device (VID `0x0B05`, Usage Page `0xFF31`). See [Compatibility](#compatibility) below.

## Requirements

- Python 3.8+
- `hidapi` library

```bash
pip install hidapi
```

## Usage

```bash
# Apply default color scheme (green + custom highlights)
python keyboard-led.py

# Turn all LEDs off
python keyboard-led.py --off

# Set all keys to a single color (hex)
python keyboard-led.py --all FF00FF
```

### Customizing colors

Edit the `main()` function in `keyboard-led.py`:

```python
base_color = (0, 255, 0)         # All keys: green
accent_color = (255, 0, 0)       # Enter + LCtrl: red
highlight_color = (128, 0, 255)  # Highlighted keys: purple
highlight_keys = ['V', 'A', 'L', 'E', 'N', 'T', 'I']  # Keys to highlight
```

Available key names are defined in the `KEY` dictionary. See [Key Position Map](#key-position-map) for the full list.

### Run at login (Windows)

Create a scheduled task to apply colors automatically:

```powershell
$python = "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe"
$script = "C:\path\to\keyboard-led.py"
schtasks /Create /TN "ASUS Keyboard LED" /TR "$python $script" /SC ONLOGON /RL HIGHEST /F
```

Remove it:
```powershell
schtasks /Delete /TN "ASUS Keyboard LED" /F
```

## Finding key positions for your keyboard

If your keyboard layout or model differs, use `scan-keys.py` to identify positions:

```bash
# Show all groups in different colors to identify rows
python scan-keys.py all

# Light up a single position
python scan-keys.py pos 42

# Sweep through a range interactively
python scan-keys.py sweep 39 57
```

## Key Position Map

The `PACKET_MAP` translates a position index to an LED index in the HID report. The `KEY` dictionary maps human-readable key names to position indices.

### QWERTZ (German) Layout

```
Row 0 — Lightbar (pos 0-4)
┌───┬───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │ 4 │  (decorative LEDs above keyboard)
└───┴───┴───┴───┴───┘

Row 1 — Function (pos 5-17)
┌─────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ ESC │ F1 │ F2 │ F3 │ F4 │ F5 │ F6 │ F7 │ F8 │ F9 │F10 │F11 │F12 │
│  5  │  6 │  7 │  8 │  9 │ 10 │ 11 │ 12 │ 13 │ 14 │ 15 │ 16 │ 17 │
└─────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

Row 2 — Number row (pos 18-38)
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬─────┬─────┬─────┬─────┐
│ ^ │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │ 0 │ ß │ ´ │ BS  │ Ins │Home │PgUp│
│18 │19 │20 │21 │22 │23 │24 │25 │26 │27 │28 │29 │30 │ 31  │ 32  │ 33  │ 34  │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴─────┴─────┴─────┴─────┘

Row 3 — Tab row (pos 39-57)
┌─────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬─────┬─────┬─────┐
│ Tab │ Q │ W │ E │ R │ T │ Z │ U │ I │ O │ P │ Ü │ + │ Del │ End │PgDn│
│ 39  │40 │41 │42 │43 │44 │45 │46 │47 │48 │49 │50 │51 │ 52  │ 53  │ 54  │
└─────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴─────┴─────┴─────┘

Row 4 — Home row (pos 58-78)
┌──────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬────────┐
│ Caps │ A │ S │ D │ F │ G │ H │ J │ K │ L │ Ö │ Ä │ # │ Enter  │
│  58  │59 │60 │61 │62 │63 │64 │65 │66 │67 │68 │69 │70 │76,77,78│
└──────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴────────┘

Row 5 — Shift row (pos 79-98)
┌───────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬────────┬────┐
│LShift │ < │ Y │ X │ C │ V │ B │ N │ M │ , │ . │ - │ RShift │ ↑  │
│  79   │80 │81 │82 │83 │84 │85 │86 │87 │88 │89 │90 │   91   │ 96 │
└───────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴────────┴────┘

Row 6 — Bottom row (pos 99-119)
┌──────┬────┬─────┬──────┬───────────────┬──────┬──────┬────┬────┬────┐
│LCtrl │ Fn │ Win │ LAlt │    Space      │ RAlt │RCtrl │ ←  │ ↓  │ →  │
│ 105  │106 │ 107 │ 108  │     109       │ 110  │ 112  │117 │118 │119 │
└──────┴────┴─────┴──────┴───────────────┴──────┴──────┴────┴────┴────┘
```

> **Note:** Some positions (e.g., 35-38, 55-57, 71-75, 92-95) may map to numpad keys on
> keyboards that have one, or to unused LEDs on tenkeyless models. Use `scan-keys.py` to check.

## How it works

1. Opens the HID device at Usage Page `0xFF31` (ASUS Aura)
2. Sends the Aura init handshake (`0xB9` → `"ASUS Tech.Inc."` → mode set)
3. Enters Direct LED mode (`0xBC`)
4. Sends per-key RGB data in 16-key packets
5. Repeats on both FF31 interfaces (Col04 + Col05)

The protocol is reverse-engineered from [asusctl/rog-aura](https://gitlab.com/asus-linux/asusctl) (Linux) and adapted for Windows via `hidapi`.

## Compatibility

To check if your ROG laptop is compatible:

```python
import hid
for d in hid.enumerate(0x0B05):
    if d['usage_page'] == 0xFF31:
        print(f"Found: {d['product_string']} (PID 0x{d['product_id']:04X})")
```

If you see a device with Usage Page `0xFF31`, it should work. You may need to:
1. Update `PID` in the script
2. Use `scan-keys.py` to map your keyboard layout
3. Update the `KEY` dictionary

### Known compatible PIDs

| PID | Model |
|-----|-------|
| `0x19B6` | ROG Strix G17 G713PV |

PRs welcome for other models!

## Credits

- [asusctl / rog-aura](https://gitlab.com/asus-linux/asusctl) — reverse-engineered Aura protocol and key mappings
- [OpenRGB](https://gitlab.com/CalcProgrammer1/OpenRGB) — general RGB control reference
- [rogauracore](https://github.com/wroberts/rogauracore) — early ROG Aura reverse engineering

## License

MIT
