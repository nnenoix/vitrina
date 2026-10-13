"""Scene 1: top-down pixel-art corridor. Everything is painted pixel by pixel
on a 240x427 grid and scaled 3x (nearest) to 720x1280."""
import numpy as np
from PIL import Image, ImageDraw

import font

AW, AH, SC = 240, 427, 3
OUTLINE = (26, 16, 34, 255)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


# --------------------------------------------------------------- floor
def make_floor(seed=7):
    rng = np.random.default_rng(seed)
    img = np.zeros((AH, AW, 3), np.float32)
    light = np.array([83, 66, 98], np.float32)
    dark = np.array([71, 56, 89], np.float32)
    bands = [(0, 28, 'd'), (28, 118, 'l'), (118, 170, 'd'), (170, 263, 'l'),
             (263, 318, 'd'), (318, 408, 'l'), (408, AH, 'd')]
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    for y0, y1, k in bands:
        img[y0:y1] = light if k == 'l' else dark
        if k == 'l':
            # top lip highlight and soft shade on the lower edge
            img[y0] = light + 6
            img[y1 - 2:y1] = light - 5
            # dithered shadow fading in from the wall on the left
            for x in range(14, 42):
                t = (x - 14) / 28.0
                for y in range(y0 + 1, y1 - 2):
                    if bayer[y % 4, x % 4] > t:
                        img[y, x] = dark - 2
        else:
            img[y0] = dark - 6
            for x in range(14, 30):
                t = (x - 14) / 16.0
                for y in range(y0 + 1, y1):
                    if bayer[y % 4, x % 4] > t + 0.25:
                        img[y, x] = dark - 7
    # wall strip on the left with protruding pillars in the dark bands
    wall_l = np.array([40, 32, 51], np.float32)
    wall_d = np.array([32, 23, 45], np.float32)
    img[:, 0:13] = wall_l
    img[:, 12] = wall_l - 8
    for y0, y1, k in bands:
        if k == 'd':
            img[y0:y1, 0:16] = wall_d
            img[y0:y1, 16] = wall_d - 6
            img[y0, 0:16] = wall_d + 10
    # sparse specks of dust
    for _ in range(140):
        x, y = rng.integers(20, AW), rng.integers(0, AH)
        img[y, x] -= rng.integers(6, 14)
    for _ in range(40):
        x, y = rng.integers(20, AW), rng.integers(0, AH)
        img[y, x] += 8
    return np.clip(img, 0, 255).astype(np.uint8)


# --------------------------------------------------------------- sprite tools
class _Shift:
    """ImageDraw wrapper that translates every coordinate."""

    def __init__(self, d, ox, oy):
        self._d, self.ox, self.oy = d, ox, oy

    def _p(self, pts):
        if len(pts) == 4 and not isinstance(pts[0], tuple):
            x0, y0, x1, y1 = pts
            return [x0 + self.ox, y0 + self.oy, x1 + self.ox, y1 + self.oy]
        return [(x + self.ox, y + self.oy) for x, y in pts]

    def rectangle(self, pts, **kw):
        self._d.rectangle(self._p(pts), **kw)

    def ellipse(self, pts, **kw):
        self._d.ellipse(self._p(pts), **kw)

    def polygon(self, pts, **kw):
        self._d.polygon(self._p(pts), **kw)

    def line(self, pts, **kw):
        self._d.line(self._p(pts), **kw)

class Sprite:
    def __init__(self, w, h, ox=0, oy=0):
        self.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.ox, self.oy = ox, oy
        self.d = _Shift(self.d, ox, oy)

    def rect(self, x0, y0, x1, y1, c):
        self.d.rectangle([x0, y0, x1, y1], fill=rgba(c))

    def ell(self, x0, y0, x1, y1, c):
        self.d.ellipse([x0, y0, x1, y1], fill=rgba(c))

    def poly(self, pts, c):
        self.d.polygon(pts, fill=rgba(c))

    def px(self, x, y, c):
        x, y = x + self.ox, y + self.oy
        if 0 <= x < self.im.width and 0 <= y < self.im.height:
            self.im.putpixel((x, y), rgba(c))

    def line(self, pts, c, w=1):
        self.d.line(pts, fill=rgba(c), width=w)

    def outlined(self, col=OUTLINE):
        a = np.array(self.im)
        m = a[:, :, 3] > 0
        g = np.zeros_like(m)
        g[1:] |= m[:-1]
        g[:-1] |= m[1:]
        g[:, 1:] |= m[:, :-1]
        g[:, :-1] |= m[:, 1:]
        edge = g & ~m
        a[edge] = col
        return Image.fromarray(a)


# palettes ------------------------------------------------------------
K_HAIR, K_HAIR_HI, K_HAIR_SH = (28, 27, 44), (62, 70, 112), (16, 15, 26)
SKIN, SKIN_SH = (246, 216, 196), (214, 168, 158)
JACKET, JACKET_SH, STRIPE = (52, 52, 64), (36, 36, 46), (226, 226, 236)
TEE, TEE_SH = (236, 236, 244), (190, 190, 210)
COLLAR = (170, 168, 182)
SHORTS = (30, 30, 38)
SHOE, SHOE_SH = (244, 244, 250), (170, 170, 186)

N_HAIR, N_HAIR_HI, N_HAIR_SH = (212, 196, 214), (236, 226, 238), (160, 140, 172)
N_EYE, N_EYE_D = (94, 200, 240), (40, 110, 170)
COAT, COAT_SH, COAT_HI = (30, 30, 44), (20, 20, 30), (60, 60, 84)
N_COLLAR, N_COLLAR_SH = (196, 192, 206), (140, 136, 156)
BOOT, BOOT_HI = (24, 24, 36), (70, 70, 96)


def kou_front(phase):
    """Kou walking towards the camera. phase 0..3"""
    s = Sprite(44, 68, 2, 3)
    bob = 1 if phase in (1, 3) else 0
    lift_l = 2 if phase == 1 else 0
    lift_r = 2 if phase == 3 else 0
    oy = -bob
    # legs
    s.rect(14, 52 + oy, 17, 57 - lift_l, SKIN)
    s.rect(23, 52 + oy, 26, 57 - lift_r, SKIN)
    s.rect(13, 57 - lift_l, 18, 60 - lift_l, SHOE)
    s.rect(13, 60 - lift_l, 18, 60 - lift_l, SHOE_SH)
    s.rect(22, 57 - lift_r, 27, 60 - lift_r, SHOE)
    s.rect(22, 60 - lift_r, 27, 60 - lift_r, SHOE_SH)
    # shorts
    s.rect(12, 46 + oy, 28, 53 + oy, SHORTS)
    s.rect(20, 49 + oy, 20, 53 + oy, (18, 18, 24))
    # arms (swing opposite to legs)
    swing = {0: 0, 1: 1, 2: 0, 3: -1}[phase]
    s.rect(8, 33 + oy, 11, 45 + oy + swing, JACKET)
    s.rect(8, 33 + oy, 8, 45 + oy + swing, STRIPE)
    s.rect(9, 46 + oy + swing, 11, 47 + oy + swing, SKIN)
    s.rect(29, 33 + oy, 32, 45 + oy - swing, JACKET)
    s.rect(32, 33 + oy, 32, 45 + oy - swing, STRIPE)
    s.rect(29, 46 + oy - swing, 31, 47 + oy - swing, SKIN)
    # torso: open track jacket over a white tee
    s.rect(11, 32 + oy, 29, 47 + oy, JACKET)
    s.rect(11, 44 + oy, 29, 47 + oy, JACKET_SH)
    s.rect(16, 32 + oy, 24, 47 + oy, TEE)
    s.rect(16, 32 + oy, 16, 47 + oy, TEE_SH)
    s.rect(24, 32 + oy, 24, 47 + oy, TEE_SH)
    s.rect(15, 33 + oy, 15, 47 + oy, (210, 210, 220))   # zipper line
    s.rect(25, 33 + oy, 25, 47 + oy, (210, 210, 220))
    s.poly([(12, 30 + oy), (17, 31 + oy), (15, 36 + oy), (12, 34 + oy)], COLLAR)
    s.poly([(28, 30 + oy), (23, 31 + oy), (25, 36 + oy), (28, 34 + oy)], COLLAR)
    # neck
    s.rect(18, 29 + oy, 22, 32 + oy, SKIN_SH)
    # head
    s.ell(4, 3 + oy, 36, 31 + oy, K_HAIR)
    # messy spikes sticking out of the silhouette
    for pts in [[(4, 12), (0, 15), (5, 18)], [(4, 20), (1, 25), (7, 24)],
                [(36, 12), (40, 14), (35, 18)], [(36, 20), (39, 26), (33, 24)],
                [(10, 6), (7, 1), (14, 4)], [(28, 5), (33, 1), (31, 8)],
                [(17, 3), (19, -2), (23, 3)]]:
        s.poly([(x, y + oy) for x, y in pts], K_HAIR)
    s.ell(9, 11 + oy, 31, 31 + oy, SKIN)
    s.rect(9, 22 + oy, 31, 26 + oy, SKIN)
    s.rect(9, 26 + oy, 31, 27 + oy, SKIN_SH)
    # messy bangs
    bang = [(6, 10), (9, 22), (11, 14), (14, 21), (16, 13), (19, 20), (21, 12),
            (24, 21), (26, 13), (29, 22), (31, 12), (34, 20), (35, 8), (6, 8)]
    s.poly([(x, y + oy) for x, y in bang], K_HAIR)
    s.rect(4, 15 + oy, 8, 29 + oy, K_HAIR)
    s.rect(32, 15 + oy, 36, 29 + oy, K_HAIR)
    s.px(8, 30 + oy, K_HAIR)
    s.px(32, 30 + oy, K_HAIR)
    # blue sheen
    s.line([(9, 9 + oy), (14, 6 + oy), (21, 5 + oy)], K_HAIR_HI)
    s.line([(25, 6 + oy), (30, 9 + oy)], K_HAIR_HI)
    s.line([(5, 18 + oy), (5, 24 + oy)], K_HAIR_HI)
    # eyes: big whites, tiny grey pupils - the tired insomniac stare
    for ex in (12, 23):
        s.rect(ex, 21 + oy, ex + 4, 25 + oy, (250, 250, 255))
        s.rect(ex - 1, 20 + oy, ex + 5, 20 + oy, K_HAIR_SH)
        s.rect(ex + 1, 22 + oy, ex + 3, 24 + oy, (96, 90, 110))
        s.px(ex + 2, 23 + oy, (40, 36, 52))
        s.px(ex + 1, 22 + oy, (255, 255, 255))
    s.rect(12, 26 + oy, 13, 26 + oy, (236, 170, 170))
    s.rect(27, 26 + oy, 28, 26 + oy, (236, 170, 170))
    s.rect(19, 28 + oy, 21, 28 + oy, (170, 110, 110))
    out = s.outlined()
    return rim_light(out)


def rim_light(im, col=(176, 120, 230), side=1):
    """Thin violet rim light on one side, like moonlight hitting the sprite."""
    a = np.array(im)
    m = a[:, :, 3] > 0
    if side > 0:
        edge = m & ~np.roll(m, -1, axis=1)
    else:
        edge = m & ~np.roll(m, 1, axis=1)
    # step one pixel inward so the dark outline survives
    inner = np.roll(edge, -side, axis=1) & m
    dark = a[:, :, :3].sum(axis=2) < 140
    sel = inner & dark
    a[sel, :3] = (a[sel, :3] * 0.4 + np.array(col) * 0.6).astype(np.uint8)
    return Image.fromarray(a)


def nazuna_side():
    """Nazuna seen from the side, facing right."""
    s = Sprite(36, 62)
    # boots
    s.rect(12, 46, 16, 58, BOOT)
    s.rect(18, 46, 22, 58, BOOT)
    s.rect(18, 57, 25, 59, BOOT)
    s.rect(12, 57, 19, 59, BOOT)
    s.rect(19, 47, 19, 55, BOOT_HI)
    s.rect(12, 43, 16, 46, SKIN)
    s.rect(18, 43, 22, 46, SKIN)
    # coat (long, open, oversized sleeves)
    s.poly([(9, 27), (25, 27), (28, 44), (24, 46), (10, 46), (6, 44)], COAT)
    s.poly([(7, 40), (10, 46), (6, 46)], COAT_SH)
    s.rect(23, 30, 25, 44, COAT_SH)
    # sleeve hanging in front
    s.poly([(19, 29), (25, 30), (27, 43), (21, 44)], COAT_HI)
    s.poly([(20, 31), (24, 31), (26, 42), (22, 43)], COAT)
    # big grey collar
    s.poly([(8, 25), (14, 23), (22, 25), (24, 30), (16, 31), (9, 30)], N_COLLAR)
    s.poly([(9, 28), (16, 29), (22, 29), (16, 31), (9, 30)], N_COLLAR_SH)
    # head
    s.ell(5, 3, 31, 29, N_HAIR)
    # face (profile on the right)
    s.poly([(18, 12), (29, 13), (30, 22), (28, 26), (23, 28), (18, 26)], SKIN)
    s.px(30, 21, SKIN)
    # blunt bangs
    s.rect(17, 7, 29, 15, N_HAIR)
    s.rect(18, 15, 29, 15, N_HAIR_SH)
    # side braid tied at the back
    for i, y in enumerate(range(18, 40, 3)):
        c = N_HAIR if i % 2 == 0 else N_HAIR_SH
        s.ell(3 - (i % 2), y, 9 - (i % 2), y + 3, c)
    s.ell(4, 6, 10, 12, N_HAIR_HI)
    s.line([(9, 6), (15, 4), (21, 5)], N_HAIR_HI)
    s.rect(7, 13, 10, 25, N_HAIR_SH)
    # eye
    s.rect(24, 17, 27, 20, N_EYE)
    s.rect(24, 16, 28, 16, OUTLINE[:3])
    s.rect(25, 19, 26, 20, N_EYE_D)
    s.px(26, 17, (255, 255, 255))
    s.rect(24, 21, 27, 21, (200, 150, 170))   # tired under-eye
    s.px(28, 24, (170, 90, 110))
    s.px(29, 25, (250, 250, 250))             # little fang
    return rim_light(s.outlined())


def nazuna_back():
    """Nazuna seen from behind (facing up the corridor)."""
    s = Sprite(36, 62)
    s.rect(11, 46, 15, 59, BOOT)
    s.rect(20, 46, 24, 59, BOOT)
    s.rect(11, 43, 15, 46, SKIN)
    s.rect(20, 43, 24, 46, SKIN)
    s.rect(12, 48, 12, 56, BOOT_HI)
    s.rect(21, 48, 21, 56, BOOT_HI)
    s.poly([(8, 27), (27, 27), (31, 45), (4, 45)], COAT)
    s.poly([(4, 45), (8, 33), (10, 45)], COAT_SH)
    s.poly([(31, 45), (27, 33), (25, 45)], COAT_SH)
    s.rect(17, 31, 18, 45, COAT_SH)
    s.poly([(7, 26), (17, 23), (28, 26), (29, 31), (6, 31)], N_COLLAR)
    s.rect(6, 30, 29, 31, N_COLLAR_SH)
    s.ell(5, 2, 30, 29, N_HAIR)
    s.ell(8, 4, 27, 16, N_HAIR_HI)
    s.ell(9, 6, 26, 18, N_HAIR)
    s.line([(17, 4), (17, 27)], N_HAIR_SH)
    s.line([(11, 8), (10, 24)], N_HAIR_SH)
    s.line([(24, 8), (25, 24)], N_HAIR_SH)
    # two braids falling over the coat
    for side in (0, 1):
        bx = 6 if side == 0 else 24
        s.ell(bx - 1, 9, bx + 6, 15, N_HAIR)   # little side tufts
        for i, y in enumerate(range(24, 42, 3)):
            c = N_HAIR if i % 2 == 0 else N_HAIR_SH
            s.ell(bx + (i % 2), y, bx + 5 + (i % 2), y + 3, c)
    return rim_light(s.outlined())


def shadow(w):
    s = Image.new('RGBA', (w, 5), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse([0, 0, w - 1, 4], fill=(20, 10, 30, 90))
    return s


# --------------------------------------------------------------- bubble
def draw_bubble(frame, x0, y0, lines):
    """Speech bubble in screen space (pixel size 3, text pixel size 4)."""
    P = 3
    bw, bh = 78, 44              # in 3px cells
    W, H = bw * P, bh * P
    cell = np.zeros((bh + 6, bw), np.uint8)   # 0 none 1 white 2 shade 3 outline-shadow
    cell[0:bh, 0:bw] = 1
    for (cx, cy) in [(0, 0), (bw - 1, 0), (0, bh - 1), (bw - 1, bh - 1)]:
        cell[cy, cx] = 0
    cell[bh - 4:bh, 1:bw - 1] = 2
    cell[bh - 1, 0] = cell[bh - 1, bw - 1] = 0
    # tail
    tx = 58
    for i in range(5):
        cell[bh + i, tx - 3 + i:tx + 3 - i] = 2 if i < 4 else 2
        cell[bh + i, tx + 3 - i - 1] = 2
    big = np.kron(cell, np.ones((P, P), np.uint8))
    h, w = big.shape
    region = frame[y0:y0 + h, x0:x0 + w]
    region[big == 1] = (251, 249, 250)
    region[big == 2] = (198, 221, 230)
    # text
    T = 4
    total_h = len(lines) * 9 * T + (len(lines) - 1) * 2 * T
    ty = y0 + (bh * P - 4 * P - total_h) // 2 + 6
    for ln in lines:
        m = font.render_mask(ln, spacing=1, bold=True)
        mb = np.kron(m, np.ones((T, T), bool))
        tx0 = x0 + (W - mb.shape[1]) // 2
        sub = frame[ty:ty + mb.shape[0], tx0:tx0 + mb.shape[1]]
        sub[mb] = (16, 12, 20)
        ty += 9 * T + 0
    return frame


# --------------------------------------------------------------- scene state
FLOOR = None
SPR = {}


def init():
    global FLOOR
    FLOOR = make_floor()
    SPR['kou'] = [kou_front(p) for p in range(4)]  # 44x68, origin offset (2,3)
    SPR['naz_side'] = nazuna_side()
    SPR['naz_back'] = nazuna_back()
    SPR['shadow_k'] = shadow(22)
    SPR['shadow_n'] = shadow(20)


def kou_pos(t):
    """Top-left of Kou's sprite in art pixels; walks straight down."""
    x = 129 - 20
    y_start, y_end = 16, 168
    t0, t1 = 0.0, 2.72
    if t <= t1:
        y = y_start + (y_end - y_start) * (t - t0) / (t1 - t0)
        walking = True
    else:
        y = y_end
        walking = False
    return int(round(x)), int(round(y)), walking


def render(t):
    """Return a 720x1280 RGB frame of the pixel scene at time t."""
    canvas = Image.fromarray(FLOOR).convert('RGBA')
    # Nazuna stands at the left
    nx, ny = 88 - 18, 266 - 60
    canvas.alpha_composite(SPR['shadow_n'], (nx + 8, ny + 57))
    kx, ky, walking = kou_pos(t)
    phase = int(t / 0.125) % 4 if walking else 0
    kou = SPR['kou'][phase]
    sprites = [(ky + 64, SPR['shadow_k'], (kx + 9, ky + 58)),
               (ky + 64, kou, (kx - 2, ky - 3))]
    naz = SPR['naz_back'] if t >= 2.80 else SPR['naz_side']
    sprites.append((ny + 62, naz, (nx, ny)))
    for _, im, pos in sorted(sprites, key=lambda s: s[0]):
        canvas.alpha_composite(im, pos)
    big = canvas.convert('RGB').resize((AW * SC, AH * SC), Image.NEAREST)
    frame = np.array(big)[:1280].copy()
    if t >= 2.80:
        draw_bubble(frame, 66, 447, ["HEY", "KOU-KUN!"])
    return frame


if __name__ == '__main__':
    import sys
    init()
    for t in map(float, sys.argv[1:]):
        Image.fromarray(render(t)).save(f'{__import__("os").environ.get("OUT", ".")}/px_{t}.png')
