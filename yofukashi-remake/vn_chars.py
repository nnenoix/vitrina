"""Character art for the visual-novel scene, drawn from scratch with vector
paths: Nazuna close-up (foreground), Nazuna full body with crossed arms and
Kou leaning towards her (background)."""
import math

from draw import (INK, layer, to_rgba, smooth, poly, fill_stroke, shape, ellipse,
                  line, clip_shape, lin_grad, rad_grad, braid, c255)

# ---------------------------------------------------------------- palette
HAIR = (214, 198, 220)
HAIR_SH = (168, 146, 186)
HAIR_DEEP = (126, 104, 150)
HAIR_HI = (242, 236, 246)
SKIN = (250, 232, 228)
SKIN_SH = (222, 178, 204)
SKIN_DEEP = (186, 130, 178)
EYE_TOP = (30, 92, 160)
EYE_MID = (66, 168, 226)
EYE_BOT = (166, 236, 252)
COAT = (30, 28, 44)
COAT_SH = (18, 16, 28)
COAT_HI = (70, 64, 100)
RIM = (150, 110, 220)
COLLAR = (178, 178, 198)
COLLAR_SH = (118, 116, 146)
TOP = (26, 24, 38)
TOP_HI = (64, 60, 92)
BLUSH = (240, 120, 160)

K_HAIR = (26, 26, 40)
K_HAIR_HI = (70, 82, 132)
K_SKIN = (246, 222, 206)
K_SKIN_SH = (206, 166, 182)
K_JACKET = (48, 48, 62)
K_JACKET_SH = (30, 30, 42)
K_STRIPE = (226, 226, 238)
K_TEE = (232, 232, 242)
K_TEE_SH = (186, 182, 206)
K_SHORTS = (28, 28, 38)
K_SHOE = (238, 238, 246)


# ================================================================ close-up
def _eye(ctx, cx, cy, mirror, blink, look=(1.5, 0.5)):
    s = -1 if mirror else 1  # mirror horizontally for the right eye

    def P(x, y):
        return (cx + s * x, cy + y)

    if blink >= 0.95:
        # closed, smug curve
        line(ctx, [P(-14, -1), P(-7, 2.5), P(2, 3), P(10, 0)], INK, 2.0)
        line(ctx, [P(-15, -1), P(-18, -3)], INK, 1.2)
        line(ctx, [P(-6, 6), P(4, 5.5)], (190, 110, 140), 0.8)
        return
    lid = 5.5 + 3.0 * blink  # heavy, half-lidded smug eyes
    white = [P(-14, 1), P(-9, -3 + lid * 0.6), P(1, -3.5 + lid * 0.7), P(9, -1 + lid * 0.4),
             P(11, 3), P(6, 7.5), P(-4, 8.5), P(-11, 5.5)]
    shape(ctx, white, fill=(248, 244, 252), stroke=None)
    ctx.save()
    clip_shape(ctx, white)
    ix, iy = cx + s * (-1.5) + look[0], cy + 3 + look[1]
    ctx.save()
    ctx.translate(ix, iy)
    ctx.scale(6.2, 7.6)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source(lin_grad(ix, iy - 7, ix, iy + 7,
                            [(0, EYE_TOP, 1), (0.55, EYE_MID, 1), (1, EYE_BOT, 1)]))
    ctx.fill()
    ellipse(ctx, ix, iy, 6.2, 7.6, fill=None, stroke=(24, 54, 100), lw=0.8)
    ellipse(ctx, ix, iy + 0.5, 2.4, 3.6, fill=(18, 34, 70), stroke=None)
    ellipse(ctx, ix, iy + 4.2, 3.4, 1.6, fill=(200, 246, 255), stroke=None, alpha=0.6)
    # lid shadow over the top of the eye (half lidded)
    ctx.rectangle(cx - 20, cy - 10, 40, 4.5 + lid * 0.7)
    ctx.set_source_rgba(*c255((120, 80, 150), 0.45))
    ctx.fill()
    ellipse(ctx, ix - s * 2.2, iy - 2.2, 1.9, 1.6, fill=(255, 255, 255), stroke=None)
    ellipse(ctx, ix + s * 2.0, iy + 2.6, 0.9, 0.9, fill=(255, 255, 255), stroke=None)
    ctx.restore()
    # upper lash line
    up = [P(-15, 2), P(-10, -3 + lid * 0.6), P(1, -4 + lid * 0.7), P(9.5, -1.5 + lid * 0.4), P(12, 2.5)]
    line(ctx, up, INK, 2.4)
    line(ctx, [P(-14, 1.5), P(-18, -1.5)], INK, 1.4)        # outer flick
    line(ctx, [P(-15, 3.5), P(-17.5, 3.5)], INK, 0.9)
    # lower lid + tired eye bags (Nazuna's look)
    line(ctx, [P(-10, 6.5), P(-3, 9), P(6, 8)], (176, 96, 132), 0.9)
    line(ctx, [P(-8, 11), P(0, 12.2), P(6, 11)], (214, 150, 182), 0.8, alpha=0.8)


def _mouth(ctx, cx, cy, open_):
    if open_ < 0.2:
        line(ctx, [(cx - 4, cy), (cx + 1, cy + 0.8), (cx + 5, cy)], (150, 70, 100), 1.0)
        return
    h = 1.5 + 3.0 * open_
    pts = [(cx - 4.5, cy), (cx + 1, cy - 0.6), (cx + 5.5, cy + 0.2), (cx + 2.5, cy + h), (cx - 2.5, cy + h * 0.85)]
    shape(ctx, pts, fill=(124, 40, 72), stroke=(80, 24, 52), lw=0.8)
    ellipse(ctx, cx + 0.5, cy + h * 0.75, 2.6, 1.1, fill=(222, 110, 136), stroke=None)
    # the vampire fang
    shape(ctx, [(cx - 3.2, cy - 0.1), (cx - 1.2, cy - 0.2), (cx - 2.3, cy + 2.6)], fill=(255, 255, 255),
          stroke=None, smooth_=False)


def closeup(phase=0.0, blink=0.0, blush=0.0, mouth=0.5):
    """Nazuna, bust shot. phase: 0..1 idle loop."""
    surf, ctx = layer()
    br = math.sin(phase * 2 * math.pi)
    bob = 0.6 * br
    sway = 0.012 * math.sin(phase * 2 * math.pi + 0.8)

    # ------------------------------------------------ body (behind head)
    ctx.save()
    ctx.translate(74, 250 + bob * 0.6)
    ctx.rotate(0.06)
    # coat: wide dark shoulders
    coat = [(-120, 20), (-96, -2), (-60, -14), (-30, -8), (0, 6), (36, -10), (70, -14), (96, 4),
            (110, 40), (116, 140), (-130, 140)]
    shape(ctx, coat, fill=COAT, lw=1.2)
    ctx.save()
    clip_shape(ctx, coat)
    # moonlight rim + folds
    line(ctx, [(68, -12), (94, 4), (106, 40), (110, 120)], RIM, 3.0, alpha=0.55)
    line(ctx, [(-96, 2), (-118, 26)], RIM, 2.0, alpha=0.4)
    line(ctx, [(84, 40), (88, 90), (86, 140)], COAT_SH, 2.2)
    line(ctx, [(-80, 40), (-84, 100), (-78, 140)], COAT_SH, 2.2)
    line(ctx, [(60, 50), (70, 140)], COAT_HI, 1.2, alpha=0.6)
    ctx.restore()
    # big grey coat collar / hood lining around the neck and down the front
    col = [(-76, -2), (-64, -38), (-36, -56), (0, -58), (36, -56), (64, -38), (76, -2), (66, 40), (54, 140),
           (-54, 140), (-66, 40)]
    shape(ctx, col, fill=COLLAR, lw=1.1)
    ctx.save()
    clip_shape(ctx, col)
    shape(ctx, [(-40, -50), (0, -54), (40, -50), (46, 20), (40, 140), (-40, 140), (-46, 20)], fill=COLLAR_SH,
          stroke=None)
    line(ctx, [(-62, -34), (-72, -2), (-62, 40), (-52, 120)], (234, 230, 244), 1.2, alpha=0.8)
    line(ctx, [(62, -34), (72, -2), (62, 40), (52, 120)], (234, 230, 244), 1.2, alpha=0.8)
    ctx.restore()
    # black high-neck crop top
    torso = [(-36, 6), (-20, -6), (20, -6), (36, 6), (46, 60), (40, 140), (-42, 140), (-48, 60)]
    shape(ctx, torso, fill=TOP, lw=1.0)
    ctx.save()
    clip_shape(ctx, torso)
    line(ctx, [(30, 10), (40, 56), (36, 120)], TOP_HI, 2.0, alpha=0.7)
    line(ctx, [(-30, 30), (-36, 80)], TOP_HI, 1.2, alpha=0.4)
    # bust contour + soft sheen on the fabric
    line(ctx, [(-44, 70), (-30, 96), (-8, 100), (0, 92)], TOP_HI, 1.2)
    line(ctx, [(44, 70), (30, 96), (8, 100), (0, 92)], TOP_HI, 1.2)
    line(ctx, [(-30, 100), (0, 104), (30, 100)], (12, 10, 20), 2.0, alpha=0.8)
    line(ctx, [(-34, 74), (-20, 84)], TOP_HI, 2.4, alpha=0.6)
    line(ctx, [(20, 72), (34, 82)], TOP_HI, 2.4, alpha=0.6)
    # keyhole cut-out on the chest
    shape(ctx, [(-7, 36), (0, 31), (7, 36), (6, 47), (0, 51), (-6, 47)], fill=SKIN, lw=0.9)
    line(ctx, [(0, 42), (0, 51)], SKIN_SH, 1.0)
    ctx.restore()
    # her left arm in the oversized coat sleeve, hanging on the right side
    sleeve = [(52, 2), (80, -6), (98, 10), (106, 60), (108, 140), (66, 140), (60, 70)]
    shape(ctx, sleeve, fill=(36, 34, 52), lw=1.1)
    ctx.save()
    clip_shape(ctx, sleeve)
    line(ctx, [(84, -2), (100, 30), (104, 90), (104, 140)], RIM, 2.4, alpha=0.6)
    line(ctx, [(70, 40), (78, 80), (76, 120)], COAT_SH, 1.6)
    line(ctx, [(86, 60), (92, 100)], COAT_HI, 1.0, alpha=0.7)
    ctx.restore()
    # neck & turtleneck collar
    shape(ctx, [(-13, -60), (13, -60), (14, -6), (-14, -6)], fill=SKIN, lw=1.0, smooth_=False)
    shape(ctx, [(-13, -56), (13, -56), (14, -30), (-14, -30)], fill=SKIN_SH, stroke=None, smooth_=False,
          alpha=0.85)
    shape(ctx, [(-15, -30), (15, -30), (19, 4), (-19, 4)], fill=TOP, lw=1.0, smooth_=False)
    line(ctx, [(-14, -24), (14, -24)], TOP_HI, 0.8)
    line(ctx, [(-15, -16), (15, -16)], TOP_HI, 0.8)
    line(ctx, [(-16, -8), (16, -8)], TOP_HI, 0.8)
    ctx.restore()

    # ------------------------------------------------ head
    ctx.save()
    ctx.translate(80, 170 + bob)
    ctx.rotate(0.17 + sway)

    # back hair mass
    back = [(-54, -30), (-60, 0), (-56, 28), (-48, 44), (-38, 48), (-30, 36), (30, 36), (38, 48), (48, 44),
            (56, 28), (60, 0), (54, -30), (38, -56), (0, -66), (-38, -56)]
    shape(ctx, back, fill=HAIR_DEEP, lw=1.1)

    # face
    face = [(-33, -28), (-34.5, 0), (-31, 16), (-22, 32), (-8, 43), (2, 46), (12, 42), (25, 30),
            (32, 14), (34, -2), (33, -28)]
    shape(ctx, face, fill=SKIN, lw=1.1)
    ctx.save()
    clip_shape(ctx, face)
    # shade under the bangs and on the shadow side
    ctx.rectangle(-40, -40, 80, 37)
    ctx.set_source(lin_grad(0, -10, 0, 0, [(0, SKIN_SH, 0.9), (1, SKIN_SH, 0.0)]))
    ctx.fill()
    shape(ctx, [(-40, -10), (-28, 10), (-22, 30), (-6, 46), (-40, 50)], fill=SKIN_SH, stroke=None, alpha=0.75)
    # blush
    if blush > 0:
        for bx in (-17, 17):
            ellipse(ctx, bx, 19, 9, 4.2, fill=BLUSH, stroke=None, alpha=0.45 * blush)
            for k in range(3):
                line(ctx, [(bx - 5 + k * 3.5, 21), (bx - 3 + k * 3.5, 17)], (220, 80, 120), 0.7,
                     smooth_=False, alpha=0.9 * blush)
    ctx.restore()

    # eyes / nose / mouth
    _eye(ctx, -16, 4, False, blink, look=(2.5, 0.8))
    _eye(ctx, 17, 4, True, blink, look=(2.5, 0.8))
    line(ctx, [(2.5, 18), (3.5, 21.5), (2, 22.5)], SKIN_DEEP, 0.9)
    _mouth(ctx, 3, 31, mouth)

    # braids hanging in front of the shoulders
    ctx.save()
    for side in (-1, 1):
        tie = (side * 54, -14)
        # little tuft above the tie
        shape(ctx, [(side * 50, -24), (side * 66, -36), (side * 74, -28), (side * 64, -14), (side * 54, -8)],
              fill=HAIR, lw=1.0)
        line(ctx, [(side * 56, -20), (side * 67, -28)], HAIR_SH, 0.8)
        pts = [tie, (side * 57, 14), (side * 56, 46), (side * 53, 80), (side * 51, 108), (side * 50, 128)]
        end = braid(ctx, pts, 13.5, HAIR, HAIR_SH, HAIR_HI)
        ex, ey, _ = end
        # tied end
        ellipse(ctx, ex, ey - 2, 3.6, 2.2, fill=(40, 30, 50), stroke=INK, lw=0.6)
        shape(ctx, [(ex - 4, ey), (ex + 4, ey), (ex + 6, ey + 12), (ex, ey + 9), (ex - 6, ey + 12)], fill=HAIR,
              lw=0.8)
        ellipse(ctx, tie[0], tie[1], 4.2, 3.0, fill=(40, 30, 50), stroke=INK, lw=0.6)
    ctx.restore()

    # side locks framing the face
    for side in (-1, 1):
        lock = [(side * 46, -14), (side * 37, 8), (side * 34, 28), (side * 37, 44), (side * 43, 34),
                (side * 50, 10), (side * 56, -10)]
        shape(ctx, lock, fill=HAIR, lw=1.0)
        line(ctx, [(side * 44, -6), (side * 40, 20), (side * 39, 36)], HAIR_SH, 0.8)

    # dome + blunt bangs
    dome = [(-55, -12), (-57, -34), (-42, -56), (-10, -66), (24, -63), (45, -52), (57, -32), (55, -12)]
    bangs_edge = [(44, -6), (36, -3), (29, -6), (22, -2), (13, -5), (5, -1.5), (-4, -5), (-13, -2),
                  (-22, -6), (-31, -2.5), (-40, -6), (-48, -10)]
    smooth(ctx, dome, closed=False)
    for p in bangs_edge:
        ctx.line_to(*p)
    ctx.close_path()
    fill_stroke(ctx, HAIR, INK, 1.1)
    ctx.save()
    smooth(ctx, dome, closed=False)
    for p in bangs_edge:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.clip()
    # shading: darker toward the bangs tips, shine ring on the crown
    ctx.rectangle(-70, -30, 140, 30)
    ctx.set_source(lin_grad(0, -26, 0, -2, [(0, HAIR_SH, 0.0), (1, HAIR_SH, 0.9)]))
    ctx.fill()
    for x0 in (-36, -20, -6, 9, 24, 38):
        line(ctx, [(x0 * 0.5, -60), (x0 * 0.85, -36), (x0, -8)], HAIR_SH, 0.9, alpha=0.9)
    shape(ctx, [(-40, -42), (-20, -51), (8, -53), (34, -46), (38, -41), (8, -46), (-20, -44), (-38, -37)],
          fill=HAIR_HI, stroke=None, alpha=0.95)
    for x0 in (-28, -10, 12, 28):
        shape(ctx, [(x0 - 3, -45), (x0 + 3, -46), (x0 + 1, -37)], fill=HAIR_HI, stroke=None, smooth_=False)
    ctx.restore()
    ctx.restore()

    return to_rgba(surf)


# ================================================================ background pair
def _bg_eye(ctx, x, y, w, half=True, col=EYE_MID, closed=False):
    if closed:
        line(ctx, [(x - w, y), (x, y + 1.2), (x + w, y)], INK, 1.0)
        return
    ellipse(ctx, x + 0.4, y + 1.2, w * 0.62, 1.7, fill=col, stroke=None)
    ellipse(ctx, x + 0.8, y + 1.4, 0.6, 0.9, fill=(20, 30, 60), stroke=None)
    line(ctx, [(x - w, y + (0.6 if half else 0)), (x, y - 0.4 + (0.8 if half else 0)), (x + w, y + 0.4)],
         INK, 1.2)


def bg_nazuna(ctx, phase=0.0, blink=0.0):
    """Nazuna standing with crossed arms, smug, looking at Kou."""
    br = math.sin(phase * 2 * math.pi)
    b = 0.45 * br  # breathing lift for the upper body
    # ---- coat hanging behind
    shape(ctx, [(176, 156 + b), (226, 156 + b), (236, 200), (244, 250), (226, 254), (200, 250), (172, 254),
                (158, 248), (166, 200)], fill=COAT, lw=1.0)
    line(ctx, [(232, 200), (240, 246)], RIM, 1.4, alpha=0.6)
    line(ctx, [(186, 210), (182, 250)], COAT_SH, 1.2)
    # ---- legs (thigh-high boots)
    # weight leg (viewer right)
    shape(ctx, [(202, 222), (214, 222), (213, 240), (212, 298), (216, 303), (205, 305), (203, 296), (203, 240)],
          fill=COAT_SH, lw=0.9)
    shape(ctx, [(202, 222), (214, 222), (213, 236), (203, 236)], fill=SKIN, lw=0.8, smooth_=False)
    line(ctx, [(209, 244), (209, 292)], TOP_HI, 1.0, alpha=0.8)
    # relaxed leg
    shape(ctx, [(188, 222), (200, 222), (198, 238), (194, 262), (192, 298), (196, 304), (184, 305), (184, 296),
                (186, 262), (188, 238)], fill=COAT_SH, lw=0.9)
    shape(ctx, [(188, 222), (200, 222), (199, 234), (189, 234)], fill=SKIN, lw=0.8, smooth_=False)
    line(ctx, [(191, 244), (189, 292)], TOP_HI, 1.0, alpha=0.8)
    # ---- shorts + belt
    shape(ctx, [(186, 208), (216, 208), (218, 226), (204, 226), (202, 220), (198, 226), (185, 226)],
          fill=(34, 34, 52), lw=0.9, smooth_=False)
    line(ctx, [(185, 224), (199, 224)], (60, 60, 86), 1.0, smooth_=False)
    line(ctx, [(203, 224), (218, 224)], (60, 60, 86), 1.0, smooth_=False)
    shape(ctx, [(186, 207), (216, 207), (216, 211), (186, 211)], fill=(16, 16, 24), stroke=None, smooth_=False)
    shape(ctx, [(199, 207), (204, 207), (204, 211), (199, 211)], fill=(150, 146, 170), stroke=None, smooth_=False)
    # ---- midriff
    shape(ctx, [(188, 192 + b), (214, 192 + b), (216, 208), (186, 208)], fill=SKIN, lw=0.9, smooth_=False)
    line(ctx, [(201, 199 + b), (201, 203 + b)], SKIN_SH, 0.8)
    shape(ctx, [(188, 192 + b), (214, 192 + b), (214, 196 + b), (188, 196 + b)], fill=SKIN_SH, stroke=None,
          smooth_=False, alpha=0.6)
    # ---- torso (crop top)
    shape(ctx, [(186, 160 + b), (216, 160 + b), (218, 176 + b), (214, 194 + b), (188, 194 + b), (184, 176 + b)],
          fill=TOP, lw=0.9)
    # ---- collar on the shoulders
    shape(ctx, [(196, 146 + b), (207, 146 + b), (208, 162 + b), (195, 162 + b)], fill=TOP, lw=0.8, smooth_=False)
    line(ctx, [(196, 151 + b), (207, 151 + b)], TOP_HI, 0.6, smooth_=False)
    for sx in (-1, 1):
        cx = 201.5
        shape(ctx, [(cx + sx * 7, 150 + b), (cx + sx * 16, 152 + b), (cx + sx * 24, 158 + b), (cx + sx * 19, 168 + b),
                    (cx + sx * 12, 176 + b), (cx + sx * 9, 162 + b)], fill=COLLAR, lw=0.8)
        line(ctx, [(cx + sx * 10, 156 + b), (cx + sx * 12, 170 + b)], COLLAR_SH, 1.0)
    # ---- crossed arms in oversized coat sleeves
    shape(ctx, [(178, 166 + b), (186, 174 + b), (208, 180 + b), (224, 178 + b), (228, 186 + b), (214, 194 + b),
                (190, 192 + b), (176, 186 + b)], fill=COAT, lw=1.0)
    shape(ctx, [(224, 160 + b), (230, 172 + b), (222, 184 + b), (196, 184 + b), (180, 186 + b), (182, 178 + b),
                (200, 174 + b), (216, 170 + b)], fill=(40, 38, 58), lw=1.0)
    line(ctx, [(186, 182 + b), (204, 179 + b), (218, 176 + b)], COAT_HI, 1.0, alpha=0.8)
    line(ctx, [(226, 166 + b), (229, 178 + b)], RIM, 1.2, alpha=0.7)
    ellipse(ctx, 181, 184 + b, 3.0, 2.2, fill=SKIN, lw=0.7)      # fingers peeking out
    # ---- braids
    for bx, sx in ((185, -1), (217, 1)):
        braid(ctx, [(bx, 136 + b), (bx + sx * 1.5, 152 + b), (bx + sx * 1, 172 + b)], 5.0, HAIR, HAIR_SH,
              HAIR_HI, lw=0.6)
    # ---- head (turned towards Kou on the right)
    ctx.save()
    ctx.translate(202, 134 + b)
    ctx.rotate(-0.06)
    shape(ctx, [(-15, -4), (-16, 8), (-12, 14), (12, 14), (16, 8), (15, -4), (8, -16), (-8, -16)],
          fill=HAIR_DEEP, lw=0.9)
    shape(ctx, [(-3, 12), (3, 12), (3, 20), (-3, 20)], fill=SKIN_SH, lw=0.8, smooth_=False)
    face = [(-10, -6), (-10, 4), (-6, 11), (1, 15), (8, 11), (12, 4), (12, -6)]
    shape(ctx, face, fill=SKIN, lw=0.9)
    _bg_eye(ctx, -2.5, 3, 3.0, closed=blink > 0.8)
    _bg_eye(ctx, 7.5, 3, 3.0, closed=blink > 0.8)
    line(ctx, [(3.5, 11), (6.5, 10.4)], (150, 60, 90), 0.8, smooth_=False)
    shape(ctx, [(4.0, 10.8), (5.0, 10.8), (4.5, 12.2)], fill=(255, 255, 255), stroke=None, smooth_=False)
    # tufts + dome + blunt bangs
    for sx in (-1, 1):
        shape(ctx, [(sx * 13, -8), (sx * 19, -14), (sx * 21, -9), (sx * 16, -3)], fill=HAIR, lw=0.7)
    smooth(ctx, [(-15, 0), (-16, -10), (-9, -19), (2, -21), (12, -18), (16, -10), (15, 0)], closed=False)
    for p in [(12, 1), (8, 0), (4, 1.5), (0, 0), (-4, 1.5), (-8, 0), (-12, 1.5)]:
        ctx.line_to(*p)
    ctx.close_path()
    fill_stroke(ctx, HAIR, INK, 0.9)
    shape(ctx, [(-10, -13), (0, -17), (10, -14), (0, -14.5)], fill=HAIR_HI, stroke=None)
    for sx in (-1, 1):
        shape(ctx, [(sx * 12, -3), (sx * 10, 6), (sx * 11, 12), (sx * 15, 6), (sx * 15, -3)], fill=HAIR, lw=0.7)
    ctx.restore()


def bg_kou(ctx, phase=0.0, blink=0.0):
    """Kou leaning towards Nazuna with his hands in his jacket pockets."""
    br = math.sin(phase * 2 * math.pi + 1.3)
    b = 0.45 * br
    # ---- legs + sneakers
    for x0, x1 in ((267, 276), (284, 293)):
        shape(ctx, [(x0, 250), (x1, 250), (x1 - 0.8, 288), (x0 + 0.8, 288)], fill=K_SKIN, lw=0.8, smooth_=False)
        line(ctx, [(x0 + 1.8, 256), (x0 + 1.8, 284)], K_SKIN_SH, 1.0)
    for x0 in (262, 282):
        shape(ctx, [(x0 + 4, 286), (x0 + 14, 286), (x0 + 15, 296), (x0 + 16, 303), (x0 - 2, 304), (x0 - 1, 298),
                    (x0 + 4, 296)], fill=K_SHOE, lw=0.9, smooth_=False)
        line(ctx, [(x0 - 1, 302), (x0 + 15, 302)], (176, 176, 196), 1.0, smooth_=False)
        line(ctx, [(x0 + 6, 290), (x0 + 12, 290)], (160, 160, 184), 0.8, smooth_=False)
    # ---- shorts (knee length)
    shape(ctx, [(264, 222), (296, 222), (298, 256), (282, 256), (280, 240), (278, 256), (262, 256)],
          fill=K_SHORTS, lw=0.9, smooth_=False)
    line(ctx, [(290, 228), (292, 252)], (54, 54, 70), 1.0)
    # ---- leaning upper body
    ctx.save()
    ctx.translate(280, 224)
    ctx.rotate(-0.36 + 0.01 * br)
    # back arm (viewer right)
    shape(ctx, [(10, -58), (17, -54), (19, -20), (15, 2), (8, 2), (9, -22)], fill=K_JACKET_SH, lw=0.9)
    line(ctx, [(17, -54), (19, -22), (16, 0)], K_STRIPE, 1.2)
    # torso
    shape(ctx, [(-12, -60 + b), (12, -60 + b), (15, -30), (14, 4), (-14, 4), (-15, -30)], fill=K_JACKET, lw=0.9)
    shape(ctx, [(-5, -58 + b), (5, -58 + b), (6, 2), (-6, 2)], fill=K_TEE, lw=0.8, smooth_=False)
    line(ctx, [(-5, -50 + b), (-6, 0)], K_TEE_SH, 1.0, smooth_=False)
    line(ctx, [(-6, -56 + b), (-7, 3)], (200, 200, 214), 0.8, smooth_=False)
    line(ctx, [(6, -56 + b), (7, 3)], (200, 200, 214), 0.8, smooth_=False)
    # collar
    shape(ctx, [(-10, -62 + b), (-4, -58 + b), (-6, -50 + b), (-11, -54 + b)], fill=(170, 168, 186), lw=0.7)
    shape(ctx, [(10, -62 + b), (4, -58 + b), (6, -50 + b), (11, -54 + b)], fill=(170, 168, 186), lw=0.7)
    # front arm, hand in the pocket
    shape(ctx, [(-16, -56 + b), (-9, -54 + b), (-8, -24), (-5, -4), (-14, -2), (-19, -24)], fill=K_JACKET, lw=0.9)
    line(ctx, [(-17, -52 + b), (-19, -24), (-15, -3)], K_STRIPE, 1.2)
    line(ctx, [(-14, -40), (-12, -10)], RIM, 1.0, alpha=0.5)
    ctx.restore()
    # ---- head, pushed forward towards Nazuna
    ctx.save()
    ctx.translate(253, 151 + b)
    ctx.rotate(-0.32)
    shape(ctx, [(-2, 10), (4, 10), (5, 18), (-2, 18)], fill=K_SKIN_SH, lw=0.8, smooth_=False)
    face = [(-10, -5), (-11, 4), (-7, 11), (-1, 14), (6, 11), (10, 4), (10, -5)]
    shape(ctx, face, fill=K_SKIN, lw=0.9)
    shape(ctx, [(8, -2), (12, -1), (12, 5), (8, 6)], fill=K_SKIN, lw=0.7)    # ear
    # wide, startled eyes with tiny pupils + blush
    for ex in (-6.5, 1.5):
        ellipse(ctx, ex, 3.2, 2.6, 1.9, fill=(250, 250, 255), stroke=None)
        ellipse(ctx, ex - 0.8, 3.4, 0.9, 0.9, fill=(60, 56, 72), stroke=None)
        line(ctx, [(ex - 3, 2.2), (ex, 1.0), (ex + 3, 2.0)], INK, 1.1)
    line(ctx, [(-9, -1.6), (-4, -2.4)], INK, 0.7, smooth_=False)
    line(ctx, [(-1, -2.4), (4, -1.8)], INK, 0.7, smooth_=False)
    for ex in (-7, 2):
        line(ctx, [(ex - 2, 8), (ex - 1, 6.8)], (230, 110, 140), 0.6, smooth_=False)
        line(ctx, [(ex + 0.5, 8), (ex + 1.5, 6.8)], (230, 110, 140), 0.6, smooth_=False)
    line(ctx, [(-4, 10.5), (-1, 10)], (150, 90, 100), 0.7, smooth_=False)
    # messy black hair
    hair = [(-13, 2), (-15, -6), (-12, -14), (-6, -19), (2, -20), (9, -17), (14, -11), (16, -3), (14, 4),
            (11, -2), (9, 2), (6, -5), (3, 1), (0, -5), (-3, 2), (-6, -5), (-9, 3), (-10, -3)]
    shape(ctx, hair, fill=K_HAIR, lw=0.9, smooth_=False)
    for pts in [[(-12, -14), (-18, -16), (-14, -9)], [(2, -20), (4, -26), (7, -18)], [(14, -11), (20, -12), (15, -5)],
                [(-6, -19), (-9, -24), (-2, -20)]]:
        shape(ctx, pts, fill=K_HAIR, lw=0.8, smooth_=False)
    line(ctx, [(-8, -14), (0, -17), (8, -14)], K_HAIR_HI, 1.0)
    ctx.restore()


def background_pair(phase=0.0, blink=0.0):
    surf, ctx = layer()
    bg_kou(ctx, phase, blink)
    bg_nazuna(ctx, phase, blink)
    return to_rgba(surf)


if __name__ == '__main__':
    import os
    import numpy as np
    from PIL import Image
    from vn_bg import build_background
    out = os.environ.get('OUT', '.')
    bg = build_background().astype(np.float32)
    img = bg
    for lay in (background_pair(0.0), closeup(0.0, 0.0, 0.0)):
        a = lay[..., 3:4]
        img = img * (1 - a) + lay[..., :3] * a
    Image.fromarray(img.astype(np.uint8)).resize((720, 724), Image.NEAREST).save(out + '/cu.png')
