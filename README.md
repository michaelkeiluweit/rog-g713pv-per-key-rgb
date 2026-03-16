# ASUS ROG Per-Key RGB Control (Windows)

Lightweight per-key RGB keyboard control for ASUS ROG laptops via HID, without Armoury Crate.

## Why?

Armoury Crate is bloated and uses excessive resources just to set some keyboard colors. This script talks directly to the keyboard's HID interface using Python and `hidapi`.

## Tested on

| Model | PID | Status |
|-------|-----|--------|
| ROG Strix G17 G713PV | `0x19B6` | Working |

Should work on other ROG laptops with the same N-KEY Device (VID `0x0B05`, Usage Page `0xFF31`). See [Compatibility](#compatibility) below.

## Requirements

- Python 3.8+
- `hidapi` library

```bash
pip install hidapi pyyaml
```

## Usage

```bash
# Apply colors from config.yaml
python keyboard-led.py

# Use a custom config file
python keyboard-led.py -c myconfig.yaml

# Turn all LEDs off
python keyboard-led.py --off

# Set all keys to a single color (hex)
python keyboard-led.py --all FF00FF
```

### Configuration

Edit `config.yaml` (placed next to the script):

```yaml
# Base color for all keys
base: "00FF00"

# Per-key color overrides
keys:
  ENTER: "FF0000"
  LCTRL: "FF0000"
  W: "8000FF"
  A: "8000FF"
  S: "8000FF"
  D: "8000FF"
```

Colors can be hex strings (`"FF00FF"`) or RGB arrays (`[255, 0, 255]`).

The config is validated on startup:if a key name is unknown or a color is invalid,
you get a clear error message instead of a crash.

Available key names are listed in the [Key Position Map](#key-position-map) below. Use `scan-keys.py` to find positions for keys not yet mapped.

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

### QWERTZ (German) Layout:G713PV

The PACKET_MAP interleaves numpad groups (5 entries each) with main keyboard groups
(12-14 entries). Positions verified empirically on G713PV.

```
Row 0:Macro keys (pos 0-4)
┌────┬────┬────┬────┬────┐
│ M1 │ M2 │ M3 │ M4 │ M5 │
│  0 │  1 │  2 │  3 │  4 │
└────┴────┴────┴────┴────┘

Row 1:Function (pos 5-17)
┌─────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ ESC │ F1 │ F2 │ F3 │ F4 │ F5 │ F6 │ F7 │ F8 │ F9 │F10 │F11 │F12 │
│  5  │  6 │  7 │  8 │  9 │ 10 │ 11 │ 12 │ 13 │ 14 │ 15 │ 16 │ 17 │
└─────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

Row 2:Number row (pos 23-35)          Nav (pos 19-22)     Numpad (pos 40-43)
┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬─────────┐ ┌─────┬─────┬──────┬──────┐ ┌────┬───┬───┬───┐
│ ^ │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │ 0 │ ß │ ´ │Backsp   │ │ Del │Pause│PrtSc │ Home │ │NmLk│ / │ * │ - │
│23 │24 │25 │26 │27 │28 │29 │30 │31 │32 │33 │34 │35 │36,37,38 │ │ 19  │ 20  │  21  │  22  │ │ 40 │41 │42 │43 │
└───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴─────────┘ └─────┴─────┴──────┴──────┘ └────┴───┴───┴───┘

Row 3:Tab row (pos 44-57)                                Numpad (pos 59-62)
┌─────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐ ┌───┬───┬───┬───┐
│ Tab │ Q │ W │ E │ R │ T │ Z │ U │ I │ O │ P │ Ü │ + │ # │ │ 7 │ 8 │ 9 │ + │
│ 44  │45 │46 │47 │48 │49 │50 │51 │52 │53 │54 │55 │56 │57 │ │59 │60 │61 │62 │
└─────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘ └───┴───┴───┴───┘

Row 4:Home row (pos 63-74)                                   Numpad (pos 80-82)
┌──────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬────────┐ ┌───┬───┬───┐
│ Caps │ A │ S │ D │ F │ G │ H │ J │ K │ L │ Ö │ Ä │ Enter  │ │ 4 │ 5 │ 6 │
│  63  │64 │65 │66 │67 │68 │69 │70 │71 │72 │73 │74 │76,77,78│ │80 │81 │82 │
└──────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴────────┘ └───┴───┴───┘

Row 5:Shift row (pos 84-95)                              Numpad (pos 101-104)
┌───────┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬────────┬────┐ ┌───┬───┬───┬─────┐
│LShift │ < │ Y │ X │ C │ V │ B │ N │ M │ , │ . │ - │ RShift │ ↑  │ │ 1 │ 2 │ 3 │KpEnt│
│  84   │85 │86 │87 │88 │89 │90 │91 │92 │93 │94 │95 │   98   │ 99 │ │101│102│103│ 104 │
└───────┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴────────┴────┘ └───┴───┴───┴─────┘

Row 6:Bottom row (pos 105-112)                           Numpad (pos 117-118)
┌──────┬────┬─────┬──────┬──────────┬──────┬──────┬────┬────┬────┐ ┌─────┬───┐
│LCtrl │ Fn │ Win │ LAlt │  Space   │ RAlt │RCtrl │ ←  │ ↓  │ >  │ │  0  │ , │
│ 105  │106 │ 107 │ 108  │   109    │ 110  │ 112  │113 │114 │115 │ │ 117 │118│
└──────┴────┴─────┴──────┴──────────┴──────┴──────┴────┴────┴────┘ └─────┴───┘
```

> **Note:** Some positions (e.g., 18, 39, 58, 75, 79, 96, 97, 100) are invisible/unused
> on the G713PV. Use `scan-keys.py` to map keys on other models.

## How it works

1. Opens the HID device at Usage Page `0xFF31` (ASUS Aura)
2. Sends the Aura init handshake (`0xB9` > `"ASUS Tech.Inc."` > mode set)
3. Enters Direct LED mode (`0xBC`)
4. Sends per-key RGB data in 16-key packets
5. Repeats on both FF31 interfaces (Col04 + Col05)

The protocol is reverse-engineered from [asusctl/rog-aura](https://gitlab.com/asus-linux/asusctl) (Linux) and adapted for Windows via `hidapi`.

## Compatibility

Run this in PowerShell to check if your laptop has the Aura keyboard interface:

```powershell
Get-PnpDevice | Where-Object { $_.InstanceId -match 'VID_0B05.*COL04' }
```

If it returns a result, you're good. If nothing shows up, your laptop doesn't have the per-key RGB interface.

For other ROG models with a different PID, update the `PID` value in `keyboard-led.py`
and use `scan-keys.py` to map your key positions.

The key positions are specific to the G713PV. For other models you'll need to run `scan-keys.py`
to map your layout and update the `KEY` dictionary.

## Credits

- [asusctl / rog-aura](https://gitlab.com/asus-linux/asusctl) for the reverse-engineered Aura protocol
- [OpenRGB](https://gitlab.com/CalcProgrammer1/OpenRGB) for general RGB control reference
- [rogauracore](https://github.com/wroberts/rogauracore) for early ROG Aura reverse engineering

## License

CC BY-NC 4.0 (free to use, no commercial use)
