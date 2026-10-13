"""Builds the whole remake frame by frame and muxes it with the audio track
pulled from the reference clip.

    python3 render.py REFERENCE.mp4 OUT.mp4          # full video
    python3 render.py --frames OUTDIR 1.0 6.5 ...    # preview stills
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image

import font
import pixel_scene
import vn_bg
import vn_chars

W, H, FPS = 720, 1280, 30
N_FRAMES = 533                     # 17.767 s, same as the reference
PIC_Y = 212                        # top of the VN picture on screen

# ------------------------------------------------------------------ timing
# visible band while the pixel scene switches off like an old CRT (frame -> top, bottom)
COLLAPSE = {109: (0, 1280), 110: (3, 1280), 111: (34, 1280), 112: (128, 1186), 113: (188, 1115),
            114: (217, 1081), 115: (298, 987), 116: (346, 930), 117: (368, 904), 118: (429, 833),
            119: (464, 792), 120: (480, 775), 121: (520, 728), 122: (544, 698), 123: (554, 687),
            124: (576, 656), 125: (594, 640), 126: (600, 633)}
# ...and while the VN picture switches on (picture squashed into the band)
REVEAL = {131: (598, 627), 132: (584, 636), 133: (554, 664), 134: (532, 680), 135: (520, 687),
          136: (492, 712), 137: (472, 725), 138: (464, 736), 139: (437, 752), 140: (420, 766),
          141: (411, 772), 142: (387, 792), 143: (372, 803), 144: (365, 809), 145: (344, 825),
          146: (331, 835), 147: (325, 840), 148: (306, 854), 149: (296, 864), 150: (290, 867),
          151: (275, 879), 152: (266, 886), 153: (262, 889), 154: (250, 898), 155: (243, 904),
          156: (240, 906), 157: (231, 913), 158: (225, 917), 159: (224, 919), 160: (218, 923),
          161: (215, 926), 162: (214, 926), 163: (212, 929), 164: (212, 930), 165: (212, 930)}
T_PIXEL_END = 4.21
T_VN_START = 131 / FPS
T_FADE_OUT = (15.50, 16.45)

NAME = "NAZUNA"
LINES = [
    # (segments [(start time, text, seconds per char)], arrow time, clear time)
    ([(5.97, "So", 1 / 30), (6.03, "...", 0.1), (6.50, " looks like you can't sleep tonight either,", 1 / 30),
      (8.47, " Kou-kun!", 1 / 30)], 8.57, 10.13),
    ([(10.13, "I suppose I can keep you company.", 1 / 30)], 11.13, 13.03),
    ([(13.03, "See you tonight", 1 / 30), (13.57, "...", 0.1), (14.43, " Kou-kuun~", 1 / 30)], 14.43, 99),
]
BLINKS = [5.55, 7.70, 9.80, 11.95, 13.55]
NAZ_BG_BLINKS = [6.9, 9.2, 12.5, 14.9]


def ease_out(x, p=3):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** p


def blink_amount(t, times, dur=0.16):
    for b in times:
        d = t - b
        if 0 <= d < dur:
            k = d / dur
            return 1.0 if 0.2 < k < 0.8 else 0.6
    return 0.0


def typed_text(t):
    """Returns (full text of current line, number of visible chars, arrow visible)."""
    current = None
    for segs, arrow_t, clear_t in LINES:
        if segs[0][0] <= t < clear_t:
            current = (segs, arrow_t)
    if current is None:
        return "", 0, False
    segs, arrow_t = current
    full = "".join(s[1] for s in segs)
    n = 0
    for start, text, per in segs:
        if t >= start:
            n += min(len(text), int((t - start) / per + 1e-6) + 1)
    return full, n, t >= arrow_t


def is_typing(t):
    full, n, _ = typed_text(t)
    return 0 < n < len(full)


# ------------------------------------------------------------------ dialog UI
BOX = (116, 1000, 589, 1134)   # x0, y0, x1, y1


def blit_text(frame, s, x, y, scale, color, max_chars=None):
    if max_chars is not None:
        s = s[:max_chars]
    if not s:
        return
    m = font.render_mask(s)
    m = np.kron(m, np.ones((scale, scale), bool))
    h, w = m.shape
    y0, x0 = max(y, 0), max(x, 0)
    y1, x1 = min(y + h, frame.shape[0]), min(x + w, frame.shape[1])
    if y1 <= y0 or x1 <= x0:
        return
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
    frame[y0:y1, x0:x1][sub] = color


def draw_dialog(frame, t, offset, show_name):
    x0, y0, x1, y1 = BOX
    y0 += offset
    y1 += offset
    if y0 >= H:
        return
    yy0, yy1 = max(y0, 0), min(y1, H)
    g = np.linspace(0, 1, y1 - y0)[:, None]
    fill = (np.array([38, 26, 66]) * (1 - g) + np.array([50, 37, 78]) * g)
    frame[yy0:yy1, x0:x1] = fill[yy0 - y0:yy1 - y0, None, :].astype(np.uint8)
    border = (118, 92, 206)
    frame[yy0:min(y0 + 2, H), x0:x1] = border
    frame[max(y1 - 2, 0):yy1, x0:x1] = border
    frame[yy0:yy1, x0:x0 + 2] = border
    frame[yy0:yy1, x1 - 2:x1] = border
    if show_name:
        blit_text(frame, NAME, x0, y0 - 19, 2, (213, 214, 217))
    full, n, arrow = typed_text(t)
    if full:
        lines = font.wrap(full, 176)
        lh = 9 * 2 + 4
        total = len(lines) * lh - 4
        ty = (y0 + y1) // 2 - total // 2 - 2
        left = n
        for ln in lines:
            w = font.text_width(ln) * 2
            tx = (x0 + x1) // 2 - w // 2
            blit_text(frame, ln, tx, ty, 2, (230, 228, 238), max_chars=max(0, left))
            left -= len(ln) + 1
            ty += lh
    if arrow:
        bobv = 2 if (int(t * 30) // 9) % 2 else 0
        ax, ay = x1 - 26, y1 - 18 + bobv
        for i in range(7):
            frame[ay + i, ax + i:ax + 14 - i] = (240, 238, 250)


# ------------------------------------------------------------------ VN picture
class VN:
    def __init__(self):
        self.bg = vn_bg.build_background().astype(np.float32)
        self.cache = {}

    def layer(self, key, fn):
        if key not in self.cache:
            self.cache[key] = fn()
        return self.cache[key]

    def picture(self, t):
        """720x724 RGB picture of the VN scene at time t."""
        step = math.floor(t * 10) / 10          # idle animation runs on 10 fps steps
        phase = ((step - T_VN_START) % 2.0) / 2.0
        phase = round(phase * 20) / 20
        nb = blink_amount(t, NAZ_BG_BLINKS)
        pair = self.layer(('pair', phase, nb), lambda: vn_chars.background_pair(phase, nb))
        blink = blink_amount(t, BLINKS)
        blush = round(min(max((t - 12.95) / 0.45, 0), 1) * 4) / 4
        if is_typing(t):
            mouth = 0.75 if (int(t * 10) % 2 == 0) else 0.3
        else:
            mouth = 0.45
        cu = self.layer(('cu', phase, blink, blush, mouth),
                        lambda: vn_chars.closeup(phase, blink, blush, mouth))
        img = self.bg.copy()
        a = pair[..., 3:4]
        img = img * (1 - a) + pair[..., :3] * a * np.array([0.92, 0.88, 1.0])
        # close-up slides in from the bottom left
        kx = ease_out((t - 4.97) / 0.73)
        ky = ease_out((t - 4.97) / 0.40, 2)
        dx = int(round(-165 * (1 - kx)))
        dy = int(round(170 * (1 - ky)))
        if t >= 4.97:
            cu_s = np.zeros_like(cu)
            hh, ww = cu.shape[:2]
            sx0, sy0 = max(0, -dx), max(0, -dy)
            tx0, ty0 = max(0, dx), max(0, dy)
            w_ = ww - abs(dx)
            h_ = hh - abs(dy)
            if w_ > 0 and h_ > 0:
                cu_s[ty0:ty0 + h_, tx0:tx0 + w_] = cu[sy0:sy0 + h_, sx0:sx0 + w_]
            a = cu_s[..., 3:4]
            img = img * (1 - a) + cu_s[..., :3] * a
        img = np.clip(img, 0, 255).astype(np.uint8)
        return np.kron(img, np.ones((2, 2, 1), np.uint8))   # pixel grid -> screen


# ------------------------------------------------------------------ frames
def frame_at(i, vn):
    t = i / FPS
    frame = np.zeros((H, W, 3), np.uint8)
    if t < T_PIXEL_END:
        px = pixel_scene.render(t).astype(np.float32)
        # fade in from black at the start
        px *= ease_out(t / 0.85, 2) if t < 0.85 else 1.0
        if i in COLLAPSE:
            top, bot = COLLAPSE[i]
            k = 1.0 - 0.25 * (i - 109) / 17
            band = np.zeros_like(px)
            band[top:bot] = px[top:bot] * k
            px = band
        elif i > 126:
            px[:] = 0
        frame = px.astype(np.uint8)
    elif t >= T_VN_START:
        pic = vn.picture(t)
        if i in REVEAL and i < 165:
            top, bot = REVEAL[i]
            hgt = max(bot - top, 2)
            squashed = np.array(Image.fromarray(pic).resize((W, hgt), Image.NEAREST)).astype(np.float32)
            squashed *= 0.55 + 0.45 * ease_out((i - 131) / 32, 2)
            frame[top:top + hgt] = squashed.astype(np.uint8)
        else:
            frame[PIC_Y:PIC_Y + pic.shape[0]] = pic
        if t >= 4.93:
            off = int(round(280 * (1 - ease_out((t - 4.93) / 0.95, 3))))
            draw_dialog(frame, t, off, show_name=t >= 5.53)
        f0, f1 = T_FADE_OUT
        if t >= f0:
            k = max(0.0, 1 - (t - f0) / (f1 - f0))
            frame = (frame.astype(np.float32) * k).astype(np.uint8)
    return frame


def main():
    pixel_scene.init()
    vn = VN()
    if sys.argv[1] == '--frames':
        out = sys.argv[2]
        for ts in sys.argv[3:]:
            i = int(round(float(ts) * FPS))
            Image.fromarray(frame_at(i, vn)).save(os.path.join(out, f'frame_{float(ts):05.2f}.png'))
        return
    ref, out = sys.argv[1], sys.argv[2]
    cmd = ['ffmpeg', '-v', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', ref, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
           '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N_FRAMES):
        p.stdin.write(frame_at(i, vn).tobytes())
        if i % 60 == 0:
            print(f'frame {i}/{N_FRAMES}', flush=True)
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    main()
