"""
Sweep through all unmapped/failed positions.
Shows expected key name. User confirms or corrects.
"""
import hid, time, sys, os

VID, PID = 0x0B05, 0x19B6
REPORT_ID, CMD_DIRECT, PACKET_SIZE = 0x5D, 0xBC, 64
KEY_SET, LED_COUNT = 167, 178

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
    117, 118, 119, 139,
    121, 122, 123, 124, 125,
    126, 127, 128, 129, 131, 135, 136, 137,
    159, 160, 161, 142, 144, 145, 146,
    174, 173, 172, 120, 140, 141, 143,
    171, 170, 169, 0, 167, 176, 177,
]

# Positions to test with expected key names
# Format: (pos, expected_name)
TO_TEST = [
    # Lightbar (pos 0-4)
    (0, "LIGHTBAR_1"), (1, "LIGHTBAR_2"), (2, "LIGHTBAR_3"), (3, "LIGHTBAR_4"), (4, "LIGHTBAR_5"),
    # Unknown group (pos 18-22) — maybe Backspace, Delete, nav keys?
    (18, "BACKSPACE?"), (19, "ENTF?"), (20, "EINFG?"), (21, "POS1?"), (22, "BILD_HOCH?"),
    # Unknown group (pos 36-38)
    (36, "BILD_RUNTER?"), (37, "DRUCK?"), (38, "PAUSE?"),
    # Numpad top (pos 39-43)
    (39, "NUMLOCK"), (40, "NUM_SLASH"), (41, "NUM_STAR"), (42, "NUM_MINUS"), (43, "???"),
    # pos 57 — end of Tab row
    (57, "BACKSPACE?"),
    # Numpad 789+ (pos 58-62)
    (58, "NUM_7"), (59, "NUM_8"), (60, "NUM_9"), (61, "NUM_PLUS_1"), (62, "NUM_PLUS_2?"),
    # HASH failed at pos 75
    (75, "HASH (#)"),
    # Numpad 456 (pos 79-83)
    (79, "NUM_4"), (80, "NUM_5"), (81, "NUM_6"), (82, "???"), (83, "???"),
    # Arrows + extras (pos 96-99)
    (96, "PFEIL_HOCH"), (97, "RSHIFT?"), (98, "???"), (99, "???"),
    # Numpad 123 Enter (pos 100-104)
    (100, "NUM_1"), (101, "NUM_2"), (102, "NUM_3"), (103, "NUM_ENTER_1?"), (104, "NUM_ENTER_2?"),
    # Unknown in bottom row (pos 111, 113-116)
    (111, "???"), (113, "NUM_0_1?"), (114, "NUM_0_2?"), (115, "NUM_KOMMA?"), (116, "???"),
    # Arrow keys (failed)
    (117, "PFEIL_LINKS"), (118, "PFEIL_RUNTER"), (119, "PFEIL_RECHTS"),
    # Extra positions (pos 120-133) — maybe M1-M5, macro keys?
    (120, "M1?"), (121, "M2?"), (122, "M3?"), (123, "M4?"), (124, "M5?"),
    (125, "???"), (126, "???"), (127, "???"), (128, "???"), (129, "???"),
    (130, "???"), (131, "???"), (132, "???"), (133, "???"),
]

def send(dev, data):
    dev.send_feature_report(list(data) + [0] * (PACKET_SIZE - len(data)))

def apply(devices, led_buf):
    for path, _ in devices:
        dev = hid.device(); dev.open_path(path)
        send(dev, [REPORT_ID, 0xB9]); time.sleep(0.02)
        send(dev, list(b"\x5dASUS Tech.Inc.")); time.sleep(0.02)
        send(dev, [REPORT_ID, 0x05, 0x20, 0x31, 0x00, 0x1A]); time.sleep(0.02)
        send(dev, [REPORT_ID, CMD_DIRECT]); time.sleep(0.02)
        for s in range(0, KEY_SET, 16):
            c = min(16, KEY_SET - s)
            send(dev, [REPORT_ID, CMD_DIRECT, 0, 1, 1, 1, s, c, 0] + led_buf[s*3:s*3+c*3])
            time.sleep(0.003)
        send(dev, [REPORT_ID, CMD_DIRECT, 0, 1, 4, 0, 0, 0, 0] + led_buf[KEY_SET*3:LED_COUNT*3])
        dev.close(); time.sleep(0.05)

def main():
    devices = [(d['path'], d['usage']) for d in hid.enumerate(VID, PID) if d['usage_page'] == 0xFF31]
    if not devices:
        print("Keine Aura-Geraete gefunden!")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'sweep-results.txt')

    print(f"=== Tasten-Identifikation ===")
    print(f"{len(TO_TEST)} Tasten zu pruefen")
    print(f"")
    print(f"  Enter       = Ja, das ist die angezeigte Taste")
    print(f"  n           = Nichts leuchtet / nicht sichtbar")
    print(f"  Tastenname  = Andere Taste leuchtet (z.B. ENTF, NUM7)")
    print(f"  q           = Abbrechen")
    print(f"{'='*50}")

    results = []
    for pos, expected in TO_TEST:
        led_buf = [0] * (LED_COUNT * 3)
        idx = PACKET_MAP[pos]
        led_buf[idx*3], led_buf[idx*3+1], led_buf[idx*3+2] = 255, 255, 255
        apply(devices, led_buf)

        answer = input(f"  Ist das {expected:16s} ? ").strip()

        if answer.lower() == 'q':
            print("Abgebrochen.")
            break
        elif answer == '':
            # Confirmed
            results.append((pos, expected.rstrip('?'), 'OK'))
            print(f"    -> {expected} = OK")
        elif answer.lower() == 'n':
            results.append((pos, expected, 'UNSICHTBAR'))
        else:
            # User typed actual key name
            results.append((pos, answer, 'KORREKTUR'))
            print(f"    -> Tatsaechlich: {answer}")

    # Write log
    with open(log_path, 'w') as f:
        f.write("=== Sweep Results ===\n\n")
        f.write("Bestaetigte Tasten:\n")
        for pos, key, status in results:
            if status == 'OK':
                f.write(f"  pos {pos:3d}  =  {key}\n")
        f.write(f"\nKorrekturen:\n")
        for pos, key, status in results:
            if status == 'KORREKTUR':
                f.write(f"  pos {pos:3d}  =  {key}\n")
        f.write(f"\nUnsichtbar/nicht vorhanden:\n")
        for pos, key, status in results:
            if status == 'UNSICHTBAR':
                f.write(f"  pos {pos:3d}  (erwartet: {key})\n")

    found = sum(1 for _, _, s in results if s in ('OK', 'KORREKTUR'))
    print(f"\n{'='*50}")
    print(f"{found} Tasten identifiziert")
    print(f"Log: {log_path}")

if __name__ == '__main__':
    main()
