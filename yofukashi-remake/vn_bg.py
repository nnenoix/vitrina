"""Scene 2 background: night corridor with tall gothic windows.

Painted procedurally with cairo shapes + numpy masks on a 360x362 art grid
(rendered at 2x for clean edges, then reduced to the pixel grid)."""
import math
import numpy as np
import cairo

AW, AH = 360, 362
SS = 2  # supersampling used for every VN layer


def new_surface(fmt=cairo.FORMAT_ARGB32):
    surf = cairo.ImageSurface(fmt, AW * SS, AH * SS)
    ctx = cairo.Context(surf)
    ctx.scale(SS, SS)
    return surf, ctx


def to_mask(draw):
    """Run draw(ctx) and return float alpha mask at art resolution."""
    surf, ctx = new_surface(cairo.FORMAT_A8)
    draw(ctx)
    ctx.fill()
    surf.flush()
    stride = surf.get_stride()
    a = np.frombuffer(surf.get_data(), np.uint8).reshape(AH * SS, stride)[:, :AW * SS]
    a = a.astype(np.float32) / 255.0
    return a.reshape(AH, SS, AW, SS).mean(axis=(1, 3))


def lancet(ctx, cx, hw, bottom, spring, tip):
    """Pointed (gothic) arch: two circular arcs meeting at the tip."""
    # circle centres lie on the spring line; radius chosen so arcs meet at tip
    h = spring - tip
    r = (hw * hw + h * h) / (2 * hw)
    ctx.move_to(cx - hw, bottom)
    ctx.line_to(cx - hw, spring)
    # left arc: centre at (cx - hw + r, spring)
    lcx = cx - hw + r
    steps = 24
    pts_l = []
    for i in range(steps + 1):
        # parametrise by y from spring to tip
        y = spring - h * i / steps
        dx = math.sqrt(max(r * r - (y - spring) ** 2, 0))
        pts_l.append((lcx - dx, y))
    rcx = cx + hw - r
    pts_r = []
    for i in range(steps + 1):
        y = tip + h * i / steps
        dx = math.sqrt(max(r * r - (y - spring) ** 2, 0))
        pts_r.append((rcx + dx, y))
    for p in pts_l:
        ctx.line_to(*p)
    ctx.line_to(cx, tip)
    for p in pts_r:
        ctx.line_to(*p)
    ctx.line_to(cx + hw, bottom)
    ctx.close_path()


def rect(ctx, x0, y0, x1, y1):
    ctx.rectangle(x0, y0, x1 - x0, y1 - y0)


def lerp(a, b, t):
    return a + (b - a) * t


def paint(img, mask, color, alpha=1.0):
    c = np.array(color, np.float32)
    m = (mask * alpha)[..., None]
    img[:] = img * (1 - m) + c * m


def blur(a, r):
    """Cheap separable box blur (applied twice) for soft shading."""
    out = a.copy()
    for _ in range(2):
        k = 2 * r + 1
        p = np.pad(out, ((r, r), (0, 0)), mode='edge')
        c = np.cumsum(p, axis=0)
        c = np.vstack([np.zeros((1, out.shape[1])), c])
        out = (c[k:] - c[:-k]) / k
        p = np.pad(out, ((0, 0), (r, r)), mode='edge')
        c = np.cumsum(p, axis=1)
        c = np.hstack([np.zeros((out.shape[0], 1)), c])
        out = (c[:, k:] - c[:, :-k]) / k
    return out


BAYS = [  # centre x, half width of window
    (45, 26), (120, 28), (198, 28), (338, 26)]
PIER = (232, 306)
SILL_Y, FLOOR_Y = 223, 272
WIN_SPRING, WIN_TIP = 128, 80


def build_background(seed=3):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:AH, 0:AW].astype(np.float32)
    img = np.zeros((AH, AW, 3), np.float32)

    # ---------------------------------------------------------- night sky
    t = yy / 230.0
    sky = np.stack([lerp(34, 58, t), lerp(26, 44, t), lerp(78, 104, t)], -1)
    img[:] = sky
    # stars
    for _ in range(260):
        x, y = rng.integers(0, AW), rng.integers(0, 225)
        b = rng.uniform(0.35, 1.0)
        img[y, x] = img[y, x] * (1 - b) + np.array([210, 205, 255]) * b
    for _ in range(14):
        x, y = rng.integers(2, AW - 2), rng.integers(2, 200)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            img[y + dy, x + dx] = (230, 225, 255) if dx == dy == 0 else (150, 140, 210)
    # the moon (seen through the last window)
    moon = to_mask(lambda c: c.arc(346, 112, 15, 0, 2 * math.pi))
    glow = blur(moon, 8)
    paint(img, glow, (160, 140, 200), 0.35)
    paint(img, moon, (238, 226, 214))
    crater = to_mask(lambda c: (c.arc(341, 108, 4, 0, 7), c.new_sub_path(), c.arc(351, 118, 3, 0, 7)))
    paint(img, crater * moon, (214, 198, 196))
    # distant city at the bottom of the windows: Call of the Night is a city
    # story, so the night outside glitters
    city = np.zeros((AH, AW), np.float32)
    x = 0
    while x < AW:
        w = int(rng.integers(6, 16))
        h = int(rng.integers(8, 34))
        city[SILL_Y - h:SILL_Y, x:x + w] = 1.0
        for wy in range(SILL_Y - h + 3, SILL_Y - 2, 4):
            for wx in range(x + 2, x + w - 1, 3):
                if rng.random() < 0.35:
                    col = [(255, 214, 140), (255, 150, 200), (170, 220, 255)][rng.integers(0, 3)]
                    img[wy, wx] = col
                    city[wy, wx] = 0.0
        x += w
    paint(img, city, (30, 22, 58))
    haze = np.clip((yy - 170) / 55.0, 0, 1)
    paint(img, haze, (120, 70, 140), 0.18)

    # ---------------------------------------------------------- stone masks
    def win_holes(c, grow=0.0):
        for cx, hw in BAYS:
            lancet(c, cx, hw + grow, SILL_Y + 1, WIN_SPRING, WIN_TIP - grow * 1.3)

    windows = to_mask(lambda c: win_holes(c))
    win_frame = to_mask(lambda c: win_holes(c, 5))

    # upper tracery: big arches spanning the bays with sky between the ribs
    def big_arches(c, grow=0.0):
        for cx, hw in BAYS:
            lancet(c, cx, hw + 9 + grow, WIN_SPRING, 96, -6 - grow)

    big = to_mask(lambda c: big_arches(c, -5))
    big_frame = to_mask(lambda c: big_arches(c, 3))
    ribs = to_mask(lambda c: [rect(c, cx - 3.5, -10, cx + 3.5, WIN_TIP) for cx, _ in BAYS])
    # diagonal ribs from the window tip to the corners (Y tracery)
    def diag(c):
        for cx, hw in BAYS:
            for s in (-1, 1):
                c.move_to(cx - 3, WIN_TIP + 2)
                c.line_to(cx + 3, WIN_TIP + 2)
                c.line_to(cx + s * (hw + 4) + 3, 22)
                c.line_to(cx + s * (hw + 4) - 3, 22)
                c.close_path()
    ribs = np.maximum(ribs, to_mask(diag))
    tracery = np.clip(big - win_frame - ribs, 0, 1) * (yy < WIN_TIP + 30)
    holes = np.clip(windows + tracery, 0, 1)

    stone = np.ones((AH, AW), np.float32)
    stone[FLOOR_Y:] = 0
    stone = np.clip(stone - holes, 0, 1)

    # ---------------------------------------------------------- stone colour
    base = np.stack([lerp(70, 58, yy / 272), lerp(44, 36, yy / 272), lerp(74, 66, yy / 272)], -1)
    stone_img = base.copy()
    # frames around windows are lighter (lit by moonlight)
    rim = np.clip(win_frame - windows, 0, 1)
    rim_hi = np.clip(to_mask(lambda c: win_holes(c, 2)) - windows, 0, 1)
    paint(stone_img, rim, (88, 58, 92))
    paint(stone_img, rim_hi, (112, 76, 112))
    arch_rim = np.clip(big_frame - big, 0, 1)
    paint(stone_img, arch_rim, (96, 64, 98))
    paint(stone_img, ribs * (yy < WIN_TIP + 2), (92, 60, 96))
    # ambient occlusion: darker stone near the openings
    ao = blur(holes, 4)
    stone_img *= (1 - 0.25 * np.clip(ao * 2 - 0.2, 0, 1))[..., None]
    # sill ledge
    sill = ((yy >= SILL_Y) & (yy < SILL_Y + 9)).astype(np.float32)
    paint(stone_img, sill, (84, 56, 88))
    paint(stone_img, ((yy >= SILL_Y) & (yy < SILL_Y + 2)).astype(np.float32), (118, 82, 118))
    paint(stone_img, ((yy >= SILL_Y + 8) & (yy < SILL_Y + 10)).astype(np.float32), (40, 26, 48))
    # lower wall panels
    lw = ((yy >= SILL_Y + 10) & (yy < FLOOR_Y)).astype(np.float32)
    paint(stone_img, lw, (56, 36, 62))
    for px in range(8, AW, 38):
        paint(stone_img, ((xx >= px) & (xx < px + 1) & (lw > 0)).astype(np.float32), (40, 26, 48))
    img = img * (1 - stone[..., None]) + stone_img * stone[..., None]

    # ---------------------------------------------------------- pier (column)
    p0, p1 = PIER
    pier = to_mask(lambda c: rect(c, p0, 30, p1, FLOOR_Y + 4))
    pier_img = np.zeros_like(img)
    pier_img[:] = (78, 52, 84)
    side = (xx < p0 + 12)
    pier_img[side] = (60, 40, 68)
    pier_img[(xx >= p1 - 6)] = (66, 44, 72)
    # recessed niche in the middle
    niche = (xx > p0 + 26) & (xx < p1 - 22) & (yy > 92) & (yy < FLOOR_Y - 6)
    pier_img[niche] = (66, 44, 72)
    pier_img[niche & (xx < p0 + 30)] = (50, 32, 58)
    # mortar lines
    for by in range(36, FLOOR_Y, 17):
        pier_img[(yy >= by) & (yy < by + 1)] = (52, 34, 60)
        off = 0 if (by // 17) % 2 == 0 else 14
        for bx in range(p0 + 12 + off, p1, 28):
            pier_img[(yy >= by) & (yy < by + 17) & (xx >= bx) & (xx < bx + 1)] = (52, 34, 60)
    pier_img[(yy < 40)] = (90, 60, 94)
    pier_img *= (0.85 + 0.15 * (1 - yy / AH))[..., None]
    img = img * (1 - pier[..., None]) + pier_img * pier[..., None]

    # ---------------------------------------------------------- floor
    fl = (yy >= FLOOR_Y).astype(np.float32)
    ft = (yy - FLOOR_Y) / (AH - FLOOR_Y)
    floor = np.stack([lerp(56, 74, ft), lerp(42, 56, ft), lerp(74, 92, ft)], -1)
    img = img * (1 - fl[..., None]) + floor * fl[..., None]
    paint(img, ((yy >= FLOOR_Y) & (yy < FLOOR_Y + 2)).astype(np.float32), (36, 24, 44))
    # moonlight shafts falling through the windows
    def shafts(c):
        for cx, hw in BAYS:
            c.move_to(cx - hw + 6, FLOOR_Y + 2)
            c.line_to(cx + hw - 6, FLOOR_Y + 2)
            c.line_to(cx + hw - 50, AH)
            c.line_to(cx - hw - 70, AH)
            c.close_path()
    sh = to_mask(shafts) * fl
    paint(img, blur(sh, 2), (110, 92, 140), 0.32)
    # pier casts a shadow onto the floor
    pshadow = to_mask(lambda c: (c.move_to(p0, FLOOR_Y), c.line_to(p1, FLOOR_Y),
                                 c.line_to(p1 - 30, AH), c.line_to(p0 - 60, AH), c.close_path()))
    paint(img, blur(pshadow * fl, 3), (36, 24, 50), 0.35)

    # global grade: cool vignette
    vig = ((xx - AW / 2) / AW) ** 2 + ((yy - AH / 2) / AH) ** 2
    img *= (1 - 0.35 * vig)[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


if __name__ == '__main__':
    import os
    from PIL import Image
    bg = build_background()
    Image.fromarray(bg).resize((720, 724), Image.NEAREST).save(os.environ.get('OUT', '.') + '/bg.png')
