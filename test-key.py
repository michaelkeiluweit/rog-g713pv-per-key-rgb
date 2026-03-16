"""Light up a single position in white, everything else off."""
import hid, time, sys

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

pos = int(sys.argv[1])
devices = [(d['path'], d['usage']) for d in hid.enumerate(VID, PID) if d['usage_page'] == 0xFF31]
led_buf = [0] * (LED_COUNT * 3)
idx = PACKET_MAP[pos]
led_buf[idx*3], led_buf[idx*3+1], led_buf[idx*3+2] = 255, 255, 255
apply(devices, led_buf)
print(f"pos {pos} leuchtet weiss")
