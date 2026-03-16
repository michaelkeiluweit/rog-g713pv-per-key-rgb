"""
Interactive key verification tool.
Lights up one position at a time, asks for confirmation.
Logs results to verify-results.txt.
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

# Current KEY map to verify
KEY_MAP = {
    'ESC': 5, 'F1': 6, 'F2': 7, 'F3': 8, 'F4': 9,
    'F5': 10, 'F6': 11, 'F7': 12, 'F8': 13,
    'F9': 14, 'F10': 15, 'F11': 16, 'F12': 17,
    'CIRCUMFLEX': 23, '1': 24, '2': 25, '3': 26, '4': 27,
    '5': 28, '6': 29, '7': 30, '8': 31, '9': 32,
    '0': 33, 'SZLIG': 34, 'ACUTE': 35,
    'TAB': 44, 'Q': 45, 'W': 46, 'E': 47, 'R': 48,
    'T': 49, 'Z': 50, 'U': 51, 'I': 52, 'O': 53,
    'P': 54, 'UUML': 55, 'PLUS': 56,
    'CAPS': 63, 'A': 64, 'S': 65, 'D': 66, 'F': 67,
    'G': 68, 'H': 69, 'J': 70, 'K': 71, 'L': 72,
    'OUML': 73, 'AUML': 74, 'HASH': 75,
    'ENTER_1': 76, 'ENTER_2': 77, 'ENTER_3': 78,
    'LSHIFT': 84, 'LESS': 85, 'Y': 86, 'X': 87, 'C': 88,
    'V': 89, 'B': 90, 'N': 91, 'M': 92,
    'COMMA': 93, 'PERIOD': 94, 'MINUS': 95,
    'UP': 96,
    'LCTRL': 105, 'FN': 106, 'LWIN': 107, 'LALT': 108,
    'SPACE': 109, 'RALT': 110, 'RCTRL': 112,
    'LEFT': 117, 'DOWN': 118, 'RIGHT': 119,
}

# Already verified (skip these)
ALREADY_VERIFIED = {'ESC': 5, 'Q': 45, 'W': 46, 'E': 47, 'A': 64, 'S': 65,
                    'D': 66, 'T': 49, 'V': 89, 'ENTER_1': 76, 'ENTER_2': 77,
                    'ENTER_3': 78, 'LCTRL': 105}


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

def light_pos(devices, pos):
    led_buf = [0] * (LED_COUNT * 3)
    idx = PACKET_MAP[pos]
    led_buf[idx*3], led_buf[idx*3+1], led_buf[idx*3+2] = 255, 255, 255
    apply(devices, led_buf)


def main():
    devices = [(d['path'], d['usage']) for d in hid.enumerate(VID, PID) if d['usage_page'] == 0xFF31]
    if not devices:
        print("Keine Aura-Geraete gefunden!")
        return

    # Keys to test (skip already verified)
    to_test = [(name, pos) for name, pos in KEY_MAP.items() if name not in ALREADY_VERIFIED]

    results = []
    failed = []

    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'verify-results.txt')

    print(f"=== Key Verification ===")
    print(f"Bereits verifiziert: {', '.join(sorted(ALREADY_VERIFIED.keys()))}")
    print(f"Zu testen: {len(to_test)} Tasten")
    print(f"")
    print(f"Eingabe:  Enter = OK,  n = falsch,  q = abbrechen")
    print(f"Log: {log_path}")
    print(f"{'='*40}")

    for name, pos in to_test:
        light_pos(devices, pos)
        answer = input(f"  pos {pos:3d} = {name:12s} ? ").strip().lower()

        if answer == 'q':
            print("Abgebrochen.")
            break
        elif answer == 'n':
            results.append((name, pos, 'FALSCH', ''))
            failed.append((name, pos, ''))
            print(f"    -> FALSCH")
        else:
            results.append((name, pos, 'OK', ''))
            print(f"    -> OK")

    # Write log
    with open(log_path, 'w') as f:
        f.write("=== Key Verification Results ===\n\n")
        f.write("Already verified:\n")
        for name, pos in sorted(ALREADY_VERIFIED.items(), key=lambda x: x[1]):
            f.write(f"  {name:12s} = pos {pos:3d}  OK\n")
        f.write(f"\nNew tests:\n")
        for name, pos, status, actual in results:
            if status == 'OK':
                f.write(f"  {name:12s} = pos {pos:3d}  OK\n")
            else:
                f.write(f"  {name:12s} = pos {pos:3d}  FALSCH -> leuchtet bei: {actual}\n")

        if failed:
            f.write(f"\n=== FEHLGESCHLAGEN ({len(failed)}) ===\n")
            for name, pos, actual in failed:
                f.write(f"  {name:12s} = pos {pos:3d}  -> tatsaechlich: {actual}\n")

    ok_count = sum(1 for _, _, s, _ in results if s == 'OK')
    fail_count = len(failed)
    print(f"\n{'='*40}")
    print(f"Ergebnis: {ok_count} OK, {fail_count} falsch")
    if failed:
        print(f"\nFalsche Zuordnungen:")
        for name, pos, actual in failed:
            print(f"  {name} (pos {pos}) -> leuchtet bei: {actual}")
    print(f"\nLog gespeichert: {log_path}")


if __name__ == '__main__':
    main()
