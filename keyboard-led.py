"""
ASUS ROG Per-Key RGB Control (Windows)

Lightweight per-key RGB control for ASUS ROG laptops via HID,
without Armoury Crate. Uses the 0xFF31 Aura USB interface.

Tested on: ASUS ROG Strix G17 G713PV (N-KEY Device 0B05:19B6)
Should work on other ROG laptops with the same HID interface.

Usage:
    python keyboard-led.py                  # Apply default color scheme
    python keyboard-led.py --off            # Turn all LEDs off
    python keyboard-led.py --all FF00FF     # Set all keys to hex color

Requires: pip install hidapi
"""

import hid
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
# Position index in PACKET_MAP for each key.
# See KEY_POSITIONS.md for the full map and how to find positions
# for your layout.
KEY = {
    # Row 0 — Decorative / Lightbar (pos 0-4)
    # Row 1 — Function row (pos 5-17)
    'ESC': 5, 'F1': 6, 'F2': 7, 'F3': 8, 'F4': 9,
    'F5': 10, 'F6': 11, 'F7': 12, 'F8': 13,
    'F9': 14, 'F10': 15, 'F11': 16, 'F12': 17,
    # Row 2 — Number row (pos 18-38)
    'CIRCUMFLEX': 18, '1': 19, '2': 20, '3': 21, '4': 22,
    '5': 23, '6': 24, '7': 25, '8': 26, '9': 27,
    '0': 28, 'SZLIG': 29, 'ACUTE': 30, 'BACKSPACE': 31,
    'INS': 32, 'HOME': 33, 'PGUP': 34,
    'NUMLOCK': 35, 'KP_SLASH': 36, 'KP_STAR': 37, 'KP_MINUS': 38,
    # Row 3 — Tab row (pos 39-57)
    'TAB': 39, 'Q': 40, 'W': 41, 'E': 42, 'R': 43,
    'T': 44, 'Z': 45, 'U': 46, 'I': 47, 'O': 48,
    'P': 49, 'UUML': 50, 'PLUS': 51,
    'DEL': 52, 'END': 53, 'PGDN': 54,
    'KP7': 55, 'KP8': 56, 'KP9': 57,
    # Row 4 — Home row (pos 58-78)
    'CAPS': 58, 'A': 59, 'S': 60, 'D': 61, 'F': 62,
    'G': 63, 'H': 64, 'J': 65, 'K': 66, 'L': 67,
    'OUML': 68, 'AUML': 69, 'HASH': 70,
    'KP4': 71, 'KP5': 72, 'KP6': 73, 'KP_PLUS': 74,
    # pos 75 = unknown
    'ENTER_1': 76, 'ENTER_2': 77, 'ENTER_3': 78,  # Enter has 3 LEDs
    # Row 5 — Shift row (pos 79-98)
    'LSHIFT': 79, 'LESS': 80, 'Y': 81, 'X': 82, 'C': 83,
    'V': 84, 'B': 85, 'N': 86, 'M': 87,
    'COMMA': 88, 'PERIOD': 89, 'MINUS': 90, 'RSHIFT': 91,
    'KP1': 92, 'KP2': 93, 'KP3': 94,
    # pos 95 = unknown
    'UP': 96, 'KP_ENTER_1': 97, 'KP_ENTER_2': 98,
    # Row 6 — Bottom row (pos 99-119)
    # pos 99 = unknown
    'LCTRL': 105, 'FN': 106, 'LWIN': 107, 'LALT': 108,
    'SPACE': 109,
    'RALT': 110, 'RCTRL': 112,
    'KP0_1': 113, 'KP0_2': 114, 'KP_DOT': 115,
    'LEFT': 117, 'DOWN': 118, 'RIGHT': 119,
}


# ──── Helpers ──────────────────────────────────────────────────────

def hex_to_rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


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
    base_color = (0, 255, 0)       # Green
    accent_color = (255, 0, 0)     # Red for Enter + LCtrl
    highlight_color = (128, 0, 255)  # Purple for highlighted keys

    # Keys to highlight (set to empty list to disable)
    highlight_keys = ['V', 'A', 'L', 'E', 'N', 'T', 'I']

    if len(sys.argv) > 1:
        if sys.argv[1] == '--off':
            base_color = (0, 0, 0)
            accent_color = (0, 0, 0)
            highlight_color = (0, 0, 0)
        elif sys.argv[1] == '--all' and len(sys.argv) > 2:
            base_color = hex_to_rgb(sys.argv[2])
            accent_color = base_color
            highlight_color = base_color

    # Build LED buffer
    led_buf = [0] * (LED_COUNT * 3)
    for i in range(len(PACKET_MAP)):
        set_pos_color(led_buf, i, *base_color)

    # Accent keys
    for pos in [KEY['ENTER_1'], KEY['ENTER_2'], KEY['ENTER_3']]:
        set_pos_color(led_buf, pos, *accent_color)
    set_pos_color(led_buf, KEY['LCTRL'], *accent_color)

    # Highlighted keys
    for key_name in highlight_keys:
        if key_name in KEY:
            set_pos_color(led_buf, KEY[key_name], *highlight_color)

    # Find and apply on all FF31 interfaces
    devices = find_aura_devices()
    print(f"Found {len(devices)} Aura interfaces")
    for path, usage in devices:
        print(f"  Usage 0x{usage:04X}: {path}")

    for path, usage in devices:
        apply_on_device(path, led_buf, f"0x{usage:04X}")
        time.sleep(0.05)

    print(f"\nDone! Base={base_color}, Accent={accent_color}, Highlight={highlight_color}")


if __name__ == '__main__':
    main()
