"""
ASUS ROG Per-Key RGB Control (Windows)

Lightweight per-key RGB control for ASUS ROG laptops via HID,
without Armoury Crate. Uses the 0xFF31 Aura USB interface.

Tested on: ASUS ROG Strix G17 G713PV (N-KEY Device 0B05:19B6)
Should work on other ROG laptops with the same HID interface.

Usage:
    python keyboard-led.py                  # Apply colors from config.yaml
    python keyboard-led.py --off            # Turn all LEDs off
    python keyboard-led.py --all FF00FF     # Set all keys to hex color
    python keyboard-led.py -c myconfig.yaml # Use custom config file

Requires: pip install hidapi pyyaml
"""

import hid
import os
import sys
import time

# ──── Device config ────────────────────────────────────────────────
VID = 0x0B05
PID = 0x19B6
REPORT_ID = 0x5D
CMD_DIRECT = 0xBC
PACKET_SIZE = 64
KEY_SET = 167
LED_COUNT = 178

# Maps position index → LED index in the HID report.
# Derived from asusctl rog-aura (https://gitlab.com/asus-linux/asusctl)
PACKET_MAP = [
    2, 3, 4, 5, 6,
    21, 23, 24, 25, 26, 28, 29, 30, 31, 33, 34, 35, 36,
    37, 38, 39, 40, 41,
    42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54,
    55, 56, 57,
    58, 59, 60, 61, 62,
    63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
    79, 80, 81, 82, 83,
    84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96,
    97, 98, 99,
    100, 101, 102, 103, 104,
    105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116,
    117, 118, 119,
    139,
    121, 122, 123, 124, 125,
    126, 127, 128, 129, 131, 135, 136, 137,
    159, 160, 161,
    142,
    144, 145, 146,
    174, 173, 172,
    120, 140, 141, 143,
    171, 170, 169,
    0,
    167,
    176, 177,
]

# ──── Key position map (QWERTZ, German layout) ────────────────────
# Verified empirically on G713PV. The PACKET_MAP has two interleaved
# sections per row: a 5-entry numpad group and a 12-14 entry main group.
KEY = {
    # Row 0 -Macro keys (pos 0-4)
    'M1': 0, 'M2': 1, 'M3': 2, 'M4': 3, 'M5': 4,
    # Row 1 -Function row (pos 5-17)
    'ESC': 5, 'F1': 6, 'F2': 7, 'F3': 8, 'F4': 9,
    'F5': 10, 'F6': 11, 'F7': 12, 'F8': 13,
    'F9': 14, 'F10': 15, 'F11': 16, 'F12': 17,
    # Row 2 -Nav cluster (pos 19-22)
    'DEL': 19, 'INS': 19,        # Entf / Einfg
    'PAUSE': 20, 'BREAK': 20,    # Pause / Untbr
    'PRTSC': 21, 'SYSRQ': 21,    # Druck / S-Abf
    'HOME': 22, 'END': 22,        # Pos1 / Ende
    # Row 2 -Number row (pos 23-35)
    'CIRCUMFLEX': 23, '1': 24, '2': 25, '3': 26, '4': 27,
    '5': 28, '6': 29, '7': 30, '8': 31, '9': 32,
    '0': 33, 'SZLIG': 34, 'ACUTE': 35,
    # Row 2 -Backspace (3 LEDs, pos 36-38)
    'BACKSPACE': 36,
    'BACKSPACE_1': 36, 'BACKSPACE_2': 37, 'BACKSPACE_3': 38,
    # Row 3 -Numpad top (pos 40-43)
    'NUMLOCK': 40, 'KP_SLASH': 41, 'KP_STAR': 42, 'KP_MINUS': 43,
    # Row 3 -Tab row (pos 44-57)
    'TAB': 44, 'Q': 45, 'W': 46, 'E': 47, 'R': 48,
    'T': 49, 'Z': 50, 'U': 51, 'I': 52, 'O': 53,
    'P': 54, 'UUML': 55, 'PLUS': 56, 'HASH': 57,
    # Row 3 -Numpad (pos 59-62)
    'KP7': 59, 'KP8': 60, 'KP9': 61, 'KP_PLUS': 62,
    # Row 4 -Home row (pos 63-74)
    'CAPS': 63, 'A': 64, 'S': 65, 'D': 66, 'F': 67,
    'G': 68, 'H': 69, 'J': 70, 'K': 71, 'L': 72,
    'OUML': 73, 'AUML': 74,
    # Row 4 -Enter (3 LEDs, pos 76-78)
    'ENTER': 76,
    'ENTER_1': 76, 'ENTER_2': 77, 'ENTER_3': 78,
    # Row 4 -Numpad (pos 80-82)
    'KP4': 80, 'KP5': 81, 'KP6': 82,
    # Row 5 -Shift row (pos 84-95)
    'LSHIFT': 84, 'LESS': 85, 'Y': 86, 'X': 87, 'C': 88,
    'V': 89, 'B': 90, 'N': 91, 'M': 92,
    'COMMA': 93, 'PERIOD': 94, 'MINUS': 95,
    # Row 5 -RShift (2 LEDs) + Arrow (pos 98-99, 123)
    'RSHIFT': 98,
    'RSHIFT_1': 98, 'RSHIFT_2': 123,
    'UP': 99,
    # Row 5 -Numpad (pos 101-104)
    'KP1': 101, 'KP2': 102, 'KP3': 103, 'KP_ENTER': 104,
    # Row 6 -Bottom row (pos 105-112)
    'LCTRL': 105, 'FN': 106, 'LWIN': 107, 'LALT': 108,
    'SPACE': 109, 'RALT': 110, 'RCTRL': 112,
    # Row 6 -Arrows (pos 113-115)
    'LEFT': 113, 'DOWN': 114, 'RIGHT': 115,
    # Row 6 -Numpad (pos 117-118)
    'KP0': 117, 'KP_COMMA': 118,
}

# Keys with multiple LEDs
MULTI_LED_KEYS = {
    'ENTER': ['ENTER_1', 'ENTER_2', 'ENTER_3'],
    'BACKSPACE': ['BACKSPACE_1', 'BACKSPACE_2', 'BACKSPACE_3'],
    'RSHIFT': ['RSHIFT_1', 'RSHIFT_2'],
}


# ──── Config loading ──────────────────────────────────────────────

def parse_color(value):
    """Parse a color from hex string or [R,G,B] list. Returns (R,G,B) tuple."""
    if isinstance(value, str):
        h = value.lstrip('#')
        if len(h) != 6:
            raise ValueError(f"Invalid hex color '{value}' -must be 6 hex digits (e.g. 'FF00FF')")
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            raise ValueError(f"Invalid hex color '{value}' -contains non-hex characters")
    elif isinstance(value, list):
        if len(value) != 3:
            raise ValueError(f"RGB color must have 3 values, got {len(value)}: {value}")
        for i, v in enumerate(value):
            if not isinstance(v, int) or v < 0 or v > 255:
                raise ValueError(f"RGB value {v} at index {i} must be an integer 0-255")
        return tuple(value)
    else:
        raise ValueError(f"Color must be hex string or [R,G,B] list, got {type(value).__name__}: {value}")


def load_config(config_path):
    """Load and validate config.yaml. Returns (base_color, key_colors) or exits with error."""
    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required for config files.")
        print("Install it with: pip install pyyaml")
        sys.exit(1)

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {config_path}:")
        print(f"  {e}")
        sys.exit(1)

    if config is None:
        print(f"Error: Config file is empty: {config_path}")
        sys.exit(1)

    if not isinstance(config, dict):
        print(f"Error: Config must be a YAML mapping, got {type(config).__name__}")
        sys.exit(1)

    errors = []

    # Parse base color
    base_color = (0, 0, 0)
    if 'base' in config:
        try:
            base_color = parse_color(config['base'])
        except ValueError as e:
            errors.append(f"base: {e}")

    # Parse per-key colors
    key_colors = {}
    if 'keys' in config:
        if not isinstance(config['keys'], dict):
            errors.append(f"'keys' must be a mapping, got {type(config['keys']).__name__}")
        else:
            for key_name, color_val in config['keys'].items():
                key_upper = str(key_name).upper()
                if key_upper not in KEY and key_upper not in MULTI_LED_KEYS:
                    errors.append(f"keys.{key_name}: Unknown key '{key_name}'. "
                                  f"Use scan-keys.py to find positions, or check README.md for valid names.")
                    continue
                try:
                    key_colors[key_upper] = parse_color(color_val)
                except ValueError as e:
                    errors.append(f"keys.{key_name}: {e}")

    if errors:
        print(f"Error: Invalid config in {config_path}:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    return base_color, key_colors


# ──── HID helpers ─────────────────────────────────────────────────

def send(dev, data):
    padded = list(data) + [0] * (PACKET_SIZE - len(data))
    dev.send_feature_report(padded)


def find_aura_devices():
    """Find all FF31 HID paths."""
    paths = []
    for d in hid.enumerate(VID, PID):
        if d['usage_page'] == 0xFF31:
            paths.append((d['path'], d['usage']))
    return paths


def set_pos_color(led_buf, pos_idx, r, g, b):
    led_idx = PACKET_MAP[pos_idx]
    led_buf[led_idx * 3]     = r
    led_buf[led_idx * 3 + 1] = g
    led_buf[led_idx * 3 + 2] = b


def apply_on_device(path, led_buf, label):
    try:
        dev = hid.device()
        dev.open_path(path)
        print(f"[{label}] Connected: {dev.get_product_string()}")

        # Init handshake
        send(dev, [REPORT_ID, 0xB9])
        time.sleep(0.02)
        send(dev, list(b"\x5dASUS Tech.Inc."))
        time.sleep(0.02)
        send(dev, [REPORT_ID, 0x05, 0x20, 0x31, 0x00, 0x1A])
        time.sleep(0.02)

        # Direct mode init
        send(dev, [REPORT_ID, CMD_DIRECT])
        time.sleep(0.02)

        # Keyboard zone
        for start in range(0, KEY_SET, 16):
            count = min(16, KEY_SET - start)
            packet = [REPORT_ID, CMD_DIRECT, 0x00, 0x01, 0x01, 0x01,
                      start, count, 0x00]
            packet += led_buf[start*3 : start*3 + count*3]
            send(dev, packet)
            time.sleep(0.003)

        # Supplementary zone
        packet = [REPORT_ID, CMD_DIRECT, 0x00, 0x01, 0x04, 0x00,
                  0x00, 0x00, 0x00]
        packet += led_buf[KEY_SET*3 : LED_COUNT*3]
        send(dev, packet)

        print(f"[{label}] Done!")
        dev.close()
        return True
    except Exception as e:
        print(f"[{label}] Error: {e}")
        return False


# ──── Main ─────────────────────────────────────────────────────────

def main():
    # Determine config file path (next to script by default)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.yaml')

    # Parse CLI args
    if len(sys.argv) > 1:
        if sys.argv[1] == '--off':
            base_color = (0, 0, 0)
            key_colors = {}
        elif sys.argv[1] == '--all' and len(sys.argv) > 2:
            base_color = parse_color(sys.argv[2])
            key_colors = {}
        elif sys.argv[1] == '-c' and len(sys.argv) > 2:
            config_path = sys.argv[2]
            base_color, key_colors = load_config(config_path)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage: keyboard-led.py [--off | --all RRGGBB | -c config.yaml]")
            sys.exit(1)
    else:
        if os.path.exists(config_path):
            base_color, key_colors = load_config(config_path)
        else:
            print(f"No config.yaml found in {script_dir}")
            print("Create one or use: keyboard-led.py --all RRGGBB")
            sys.exit(1)

    # Build LED buffer
    led_buf = [0] * (LED_COUNT * 3)
    for i in range(len(PACKET_MAP)):
        set_pos_color(led_buf, i, *base_color)

    # Apply per-key colors
    for key_name, color in key_colors.items():
        if key_name in MULTI_LED_KEYS:
            for sub_key in MULTI_LED_KEYS[key_name]:
                set_pos_color(led_buf, KEY[sub_key], *color)
        else:
            set_pos_color(led_buf, KEY[key_name], *color)

    # Find and apply on all FF31 interfaces
    devices = find_aura_devices()
    if not devices:
        print("Error: No ASUS Aura keyboard found (VID 0x0B05, Usage Page 0xFF31).")
        print("Make sure the keyboard is connected and no other software is using it.")
        sys.exit(1)

    print(f"Found {len(devices)} Aura interfaces")
    for path, usage in devices:
        apply_on_device(path, led_buf, f"0x{usage:04X}")
        time.sleep(0.05)

    key_count = len(key_colors)
    print(f"\nDone! Base={base_color}, {key_count} key override(s)")


if __name__ == '__main__':
    main()
