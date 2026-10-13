"""Small vector-drawing toolkit on top of cairo used by the character art."""
import math
import numpy as np
import cairo

from vn_bg import AW, AH, SS

INK = (34, 20, 42)


def c255(c, a=1.0):
    return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, a)


def layer():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, AW * SS, AH * SS)
    ctx = cairo.Context(surf)
    ctx.scale(SS, SS)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    return surf, ctx


def to_rgba(surf):
    """cairo ARGB32 (premultiplied BGRA) -> straight RGBA float at art res."""
    surf.flush()
    stride = surf.get_stride()
    a = np.frombuffer(surf.get_data(), np.uint8).reshape(AH * SS, stride // 4, 4)[:, :AW * SS]
    a = a.astype(np.float32)
    # reduce supersampling (premultiplied average is correct)
    a = a.reshape(AH, SS, AW, SS, 4).mean(axis=(1, 3))
    alpha = a[..., 3:4] / 255.0
    rgb = np.where(alpha > 0, a[..., [2, 1, 0]] / np.maximum(alpha, 1e-6), 0)
    return np.concatenate([rgb, alpha], -1)


def smooth(ctx, pts, closed=True, tension=0.5):
    """Catmull-Rom spline through pts, emitted as cubic beziers."""
    n = len(pts)
    if n < 2:
        return
    P = [tuple(map(float, p)) for p in pts]
    ctx.move_to(*P[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = P[(i - 1) % n] if (closed or i > 0) else P[i]
        p1 = P[i]
        p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (closed or i + 2 < n) else p2
        k = tension / 3.0 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def poly(ctx, pts, closed=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if closed:
        ctx.close_path()


def fill_stroke(ctx, fill=None, stroke=INK, lw=1.0, alpha=1.0):
    if fill is not None:
        ctx.set_source_rgba(*c255(fill, alpha))
        if stroke is not None:
            ctx.fill_preserve()
        else:
            ctx.fill()
    if stroke is not None:
        ctx.set_source_rgba(*c255(stroke, alpha))
        ctx.set_line_width(lw)
        ctx.stroke()


def shape(ctx, pts, fill=None, stroke=INK, lw=1.0, smooth_=True, closed=True, alpha=1.0):
    if smooth_:
        smooth(ctx, pts, closed)
    else:
        poly(ctx, pts, closed)
    fill_stroke(ctx, fill, stroke if stroke else None, lw, alpha)


def ellipse(ctx, cx, cy, rx, ry, fill=None, stroke=INK, lw=1.0, rot=0.0, alpha=1.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(rx, ry)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    fill_stroke(ctx, fill, stroke, lw, alpha)


def line(ctx, pts, col=INK, lw=1.0, smooth_=True, alpha=1.0):
    if smooth_ and len(pts) > 2:
        smooth(ctx, pts, closed=False)
    else:
        poly(ctx, pts, closed=False)
    ctx.set_source_rgba(*c255(col, alpha))
    ctx.set_line_width(lw)
    ctx.stroke()


def clip_shape(ctx, pts, smooth_=True):
    if smooth_:
        smooth(ctx, pts, True)
    else:
        poly(ctx, pts, True)
    ctx.clip()


def lin_grad(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, col, a in stops:
        g.add_color_stop_rgba(off, *c255(col, a)[:3], a)
    return g


def rad_grad(cx, cy, r, stops):
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    for off, col, a in stops:
        g.add_color_stop_rgba(off, *c255(col, a)[:3], a)
    return g


def braid(ctx, pts, w, base, shade, hi, lw=0.9):
    """A three-strand braid following polyline pts."""
    segs = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        segs.append((x0, y0, x1, y1))
    L = [math.hypot(x1 - x0, y1 - y0) for x0, y0, x1, y1 in segs]
    total = sum(L)

    def at(d):
        for (x0, y0, x1, y1), l in zip(segs, L):
            if d <= l:
                t = d / l if l else 0
                return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, math.atan2(y1 - y0, x1 - x0)
            d -= l
        x0, y0, x1, y1 = segs[-1]
        return x1, y1, math.atan2(y1 - y0, x1 - x0)

    # tube underneath so lobes never leave gaps
    tube = [at(total * k / 30)[:2] for k in range(31)]
    smooth(ctx, tube, closed=False)
    ctx.set_source_rgba(*c255(INK))
    ctx.set_line_width(w * 0.8 + 1.6)
    ctx.stroke()
    smooth(ctx, tube, closed=False)
    ctx.set_source_rgba(*c255(shade))
    ctx.set_line_width(w * 0.8)
    ctx.stroke()
    step = w * 0.55
    n = max(2, int(total / step))
    for i in range(n):
        d = (i + 0.5) * step
        x, y, ang = at(d)
        taper = 1.0 - 0.3 * (i / n)
        side = 1 if i % 2 == 0 else -1
        nx, ny = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
        ox, oy = nx * w * 0.16 * side, ny * w * 0.16 * side
        rot = ang - side * 0.75
        ellipse(ctx, x + ox, y + oy, w * 0.56 * taper, w * 0.34 * taper, fill=base, stroke=INK, lw=lw, rot=rot)
        ellipse(ctx, x + ox * 1.4, y + oy * 1.4, w * 0.26 * taper, w * 0.1 * taper,
                fill=hi, stroke=None, rot=rot)
    return at(total)
