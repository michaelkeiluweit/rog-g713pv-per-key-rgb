"""
ASUS ROG Keyboard LED Position Scanner

Helps identify which PACKET_MAP position corresponds to which physical key.
Useful for mapping keys on untested keyboard layouts.

Usage:
    python scan-keys.py all          # All groups in different colors
    python scan-keys.py row 3        # Light up one group in white
    python scan-keys.py pos 42       # Light up a single position in white
    python scan-keys.py sweep        # Sweep through all positions one by one
    python scan-keys.py sweep 40 60  # Sweep through positions 40-60
"""

import hid
import sys
import time

VID = 0x0B05
PID = 0x19B6
REPORT_ID = 0x5D
CMD_DIRECT = 0xBC
PACKET_SIZE = 64
KEY_SET = 167
LED_COUNT = 178

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

# Groups as defined in the PACKET_MAP layout
GROUPS = [
    ("Row 0 - Lightbar",      list(range(0, 5))),
    ("Row 1 - Function",      list(range(5, 18))),
    ("Row 2L - Numbers left",  list(range(18, 23))),
    ("Row 2R - Numbers right", list(range(23, 36))),
    ("Row 2N - Numpad top",    list(range(36, 39))),
    ("Row 3L - Tab left",      list(range(39, 44))),
    ("Row 3R - Tab right",     list(range(44, 58))),
    ("Row 4L - Home left",     list(range(58, 63))),
    ("Row 4R - Home right",    list(range(63, 76))),
    ("Row 4E - Enter",         list(range(76, 79))),
    ("Row 5L - Shift left",    list(range(79, 84))),
    ("Row 5R - Shift right",   list(range(84, 96))),
    ("Row 5A - Arrows+",       list(range(96, 99))),
    ("Row 6X",                 [99]),
    ("Row 6L - Ctrl left",     list(range(100, 105))),
    ("Row 6R - Ctrl right",    list(range(105, 117))),
    ("Row 6A - Arrows",        list(range(117, 120))),
    ("Extra 1",                [120]),
    ("Extra 2",                list(range(121, 124))),
    ("Extra 3",                list(range(124, 127))),
    ("Extra 4",                list(range(127, 131))),
    ("Extra 5",                list(range(131, 134))),
]

COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (255, 128, 0), (128, 0, 255),
    (255, 255, 255), (0, 128, 255), (255, 0, 128),
]


def send(dev, data):
    padded = list(data) + [0] * (PACKET_SIZE - len(data))
    dev.send_feature_report(padded)


def find_aura_devices():
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


def apply_leds(devices, led_buf):
    for path, usage in devices:
        try:
            dev = hid.device()
            dev.open_path(path)
            send(dev, [REPORT_ID, 0xB9])
            time.sleep(0.02)
            send(dev, list(b"\x5dASUS Tech.Inc."))
            time.sleep(0.02)
            send(dev, [REPORT_ID, 0x05, 0x20, 0x31, 0x00, 0x1A])
            time.sleep(0.02)
            send(dev, [REPORT_ID, CMD_DIRECT])
            time.sleep(0.02)
            for start in range(0, KEY_SET, 16):
                count = min(16, KEY_SET - start)
                packet = [REPORT_ID, CMD_DIRECT, 0x00, 0x01, 0x01, 0x01,
                          start, count, 0x00]
                packet += led_buf[start*3 : start*3 + count*3]
                send(dev, packet)
                time.sleep(0.003)
            packet = [REPORT_ID, CMD_DIRECT, 0x00, 0x01, 0x04, 0x00,
                      0x00, 0x00, 0x00]
            packet += led_buf[KEY_SET*3 : LED_COUNT*3]
            send(dev, packet)
            dev.close()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.05)


def main():
    devices = find_aura_devices()
    if not devices:
        print("No Aura devices found!")
        return

    print(f"Found {len(devices)} Aura interfaces")
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "all":
        # All groups in different colors
        led_buf = [0] * (LED_COUNT * 3)
        for idx, (name, positions) in enumerate(GROUPS):
            color = COLORS[idx % len(COLORS)]
            color_names = ["Red","Green","Blue","Yellow","Magenta","Cyan",
                          "Orange","Purple","White","LightBlue","Pink"]
            print(f"  {name}: pos {positions[0]}-{positions[-1]} = {color_names[idx % 11]}")
            for pos in positions:
                if pos < len(PACKET_MAP):
                    set_pos_color(led_buf, pos, *color)
        apply_leds(devices, led_buf)

    elif mode == "row":
        # Light up one group
        group_idx = int(sys.argv[2])
        name, positions = GROUPS[group_idx]
        print(f"Lighting: {name} (pos {positions[0]}-{positions[-1]})")
        led_buf = [0] * (LED_COUNT * 3)
        for pos in positions:
            if pos < len(PACKET_MAP):
                set_pos_color(led_buf, pos, 255, 255, 255)
        apply_leds(devices, led_buf)

    elif mode == "pos":
        # Single position
        pos = int(sys.argv[2])
        print(f"Lighting position {pos}")
        led_buf = [0] * (LED_COUNT * 3)
        set_pos_color(led_buf, pos, 255, 255, 255)
        apply_leds(devices, led_buf)

    elif mode == "sweep":
        # Sweep through positions one by one
        start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        end = int(sys.argv[3]) if len(sys.argv) > 3 else len(PACKET_MAP) - 1
        print(f"Sweeping positions {start}-{end}. Press Enter for next, 'q' to quit.")
        for pos in range(start, min(end + 1, len(PACKET_MAP))):
            led_buf = [0] * (LED_COUNT * 3)
            set_pos_color(led_buf, pos, 255, 255, 255)
            apply_leds(devices, led_buf)
            resp = input(f"  pos {pos} (LED {PACKET_MAP[pos]}) → which key? ")
            if resp.lower() == 'q':
                break

    print("Done!")


if __name__ == '__main__':
    main()
