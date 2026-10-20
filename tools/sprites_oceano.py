"""Genera los sprites de la serie del océano en sprites/oceano/.

  primigenio   criatura colosal alada con tentáculos (estilo Cthulhu de Lovecraft, 1928, dominio público)
  pesquero     barco pesquero de arrastre (proa a la derecha), con farol encendido

Colores base sin luz; la escena los ilumina. Los ojos y el farol brillan solos ('brillos' en el .json).
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "sprites" / "oceano"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, im, ancla, brillos=(), notas=""):
    im.save(OUT / f"{name}.png")
    (OUT / f"{name}.json").write_text(json.dumps(
        {"ancla": list(ancla), "brillos": [{"pos": list(p), "color": list(c)} for p, c in brillos], "notas": notas},
        indent=2, ensure_ascii=False))
    print("Sprite:", name, im.size)


def noise(w, h, cell, seed):
    r = np.random.default_rng(seed)
    g = Image.fromarray((r.random((h // cell + 3, w // cell + 3)) * 255).astype(np.uint8))
    return np.asarray(g.resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC), np.float32)[:h, :w] / 255


def tubo(d, pts, r0, r1, fill=255, pasos=6):
    """Línea gruesa que se adelgaza de r0 a r1 siguiendo una lista de puntos."""
    total = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        pasos = max(pasos, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.8))
        for k in range(1, pasos + 1):
            u = k / pasos
            total.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    n = len(total) - 1
    for i, (x, y) in enumerate(total):
        r = r0 + (r1 - r0) * i / max(n, 1)
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def curva(p0, p1, c, n=12):
    """Curva cuadrática de p0 a p1 con punto de control c."""
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u ** 2 * p1[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u ** 2 * p1[1]) for u in np.linspace(0, 1, n)]


def sombrear(rgb, m, base, luz=(1, -1), rim=(170, 186, 168), tex=0.3, seed=0, escamas=False):
    """Pinta la máscara m con color base, gradiente de luz desde arriba, borde iluminado y textura."""
    H, W = m.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ys, xs_ = np.nonzero(m)
    if len(ys) == 0:
        return
    top, bot = ys.min(), ys.max()
    grad = 1.15 - 0.55 * np.clip((yy - top) / max(bot - top, 1), 0, 1)
    n = noise(W, H, 3, seed)
    col = np.array(base, np.float32)[None, None, :] * (grad * (1 - tex / 2 + tex * n))[..., None]
    if escamas:
        s = noise(W, H, 2, seed + 50)
        col *= (1 - 0.35 * ((s > 0.62) & (s < 0.7)))[..., None]
    dx, dy = luz
    for k, a in ((1, 0.9), (2, 0.45)):                         # borde iluminado (luz desde arriba-derecha)
        sh = np.roll(np.roll(m, -dy * k, axis=0), -dx * k, axis=1)
        e = m & ~sh
        col[e] = col[e] * (1 - a) + np.array(rim, np.float32) * a
    for k, a in ((1, 0.45),):                                  # borde de sombra opuesto
        sh = np.roll(np.roll(m, dy * k, axis=0), dx * k, axis=1)
        e = m & ~sh
        col[e] *= (1 - a)
    rgb[m] = col[m]


def primigenio():
    W, H = 270, 192
    cx, fy = 135, 191
    rgb = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), bool)
    VERDE, VERDE_C, ALA, HUESO = (40, 52, 42), (58, 72, 56), (30, 38, 32), (58, 70, 56)

    def mascara(fn):
        im = Image.new("L", (W, H), 0)
        fn(ImageDraw.Draw(im))
        return np.asarray(im) > 127

    def pinta(m, *a, **k):
        sombrear(rgb, m, *a, **k)
        alpha[:] |= m

    # ------------------------------------------------------------ alas
    for s in (-1, 1):
        X = lambda x: cx + s * (cx - x)              # refleja respecto al centro (definido para el ala izquierda)
        hombro, codo, muneca = (112, 66), (74, 30), (48, 8)
        puntas = [(2, 0), (0, 58), (10, 112), (54, 118)]
        borde = []
        prev = muneca
        borde += [hombro, codo, muneca, puntas[0]]
        for a, b in zip(puntas, puntas[1:]):
            c = ((a[0] + b[0]) / 2 + (muneca[0] - (a[0] + b[0]) / 2) * 0.55,
                 (a[1] + b[1]) / 2 + (muneca[1] - (a[1] + b[1]) / 2) * 0.55)
            borde += curva(a, b, c, 10)[1:]
        borde += curva(puntas[-1], (104, 104), (88, 96), 8)[1:]
        poly = [(X(x), y) for x, y in borde]
        mem = mascara(lambda d: d.polygon(poly, fill=255))
        pinta(mem, ALA, luz=(1 if s > 0 else -1, -1), rim=(96, 110, 96), tex=0.25, seed=3 + s)
        # venas de la membrana
        im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        for p_ in puntas[1:]:
            mid = ((muneca[0] + p_[0]) / 2 + 6, (muneca[1] + p_[1]) / 2)
            d.line([(X(muneca[0]), muneca[1]), (X(mid[0]), mid[1] + 6), (X(p_[0]), p_[1])], fill=(24, 30, 26))
        rgb[:] = np.asarray(im, np.float32)
        rgb[~alpha] = 0
        # huesos: brazo y dedos
        hm = mascara(lambda d: (tubo(d, [(X(hombro[0]), hombro[1]), (X(codo[0]), codo[1])], 3.6, 2.6),
                                tubo(d, [(X(codo[0]), codo[1]), (X(muneca[0]), muneca[1])], 2.6, 1.8),
                                [tubo(d, [(X(muneca[0]), muneca[1]), (X(p_[0]), p_[1])], 1.4, 0.5) for p_ in puntas]))
        pinta(hm, HUESO, luz=(1 if s > 0 else -1, -1), rim=(120, 136, 112), tex=0.2, seed=9)
        garra = mascara(lambda d: d.polygon([(X(muneca[0]), muneca[1] - 2), (X(muneca[0] - 6), muneca[1] - 9),
                                             (X(muneca[0] + 3), muneca[1] - 1)], fill=255))
        pinta(garra, (110, 112, 96), tex=0.1)

    # ------------------------------------------------------- torso y hombros
    torso = mascara(lambda d: (d.polygon([(cx - 46, 64), (cx - 20, 50), (cx + 20, 50), (cx + 46, 64), (cx + 52, 100),
                                          (cx + 40, 150), (cx + 36, H), (cx - 36, H), (cx - 40, 150), (cx - 52, 100)],
                                         fill=255),
                               d.ellipse([cx - 58, 56, cx - 24, 84], fill=255), d.ellipse([cx + 24, 56, cx + 58, 84], fill=255)))
    pinta(torso, VERDE, rim=(140, 160, 138), tex=0.45, seed=21, escamas=True)
    pec = mascara(lambda d: (d.arc([cx - 40, 74, cx, 112], 20, 160, fill=255, width=2),
                             d.arc([cx, 74, cx + 40, 112], 20, 160, fill=255, width=2)))
    rgb[pec & alpha] *= 0.55

    # ----------------------------------------------------------- brazos
    for s in (-1, 1):
        X = lambda x: cx + s * (cx - x)
        hombro, codo, muneca = (96, 70), (60, 108), (72, 146)
        sup = mascara(lambda d: tubo(d, [(X(hombro[0]), hombro[1]), (X(codo[0]), codo[1])], 13, 10))
        pinta(sup, VERDE, luz=(1 if s > 0 else -1, -1), rim=(140, 160, 138), tex=0.45, seed=30 + s, escamas=True)
        ant = mascara(lambda d: tubo(d, [(X(codo[0]), codo[1]), (X(muneca[0]), muneca[1])], 10, 8))
        pinta(ant, VERDE_C, luz=(1 if s > 0 else -1, -1), rim=(150, 170, 146), tex=0.45, seed=40 + s, escamas=True)
        mano = mascara(lambda d: d.ellipse([X(muneca[0]) - 10, muneca[1] - 4, X(muneca[0]) + 10, muneca[1] + 12], fill=255))
        pinta(mano, VERDE_C, rim=(150, 170, 146), tex=0.4, seed=50 + s)
        for k, ang in enumerate((-40, -15, 10, 35)):
            a = math.radians(90 + ang * s)
            p0 = (X(muneca[0]) + math.cos(a) * 6, muneca[1] + 8)
            p1 = (p0[0] + math.cos(a) * 12, p0[1] + 14)
            p2 = (p1[0] + math.cos(a) * 4 - s * 2, p1[1] + 7)
            dedo = mascara(lambda d: tubo(d, [p0, p1], 3, 2))
            pinta(dedo, VERDE_C, rim=(150, 170, 146), tex=0.3, seed=60 + k)
            una = mascara(lambda d: tubo(d, [p1, p2], 1.8, 0.5))
            pinta(una, (26, 28, 24), rim=(120, 124, 110), tex=0.1)

    # ------------------------------------------------------------ cabeza
    cabeza = mascara(lambda d: (d.ellipse([cx - 23, 4, cx + 23, 58], fill=255),
                                d.ellipse([cx - 19, 38, cx + 19, 66], fill=255)))
    pinta(cabeza, (60, 76, 62), rim=(160, 180, 156), tex=0.5, seed=70, escamas=True)
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for k in range(5):                                           # pliegues del manto
        d.arc([cx - 18 + k, 6 + k * 3, cx + 18 - k, 40 + k * 2], 200, 340, fill=(36, 46, 38))
    d.polygon([(cx - 17, 40), (cx - 3, 46), (cx - 4, 49), (cx - 18, 44)], fill=(20, 26, 22))   # cejas
    d.polygon([(cx + 17, 40), (cx + 3, 46), (cx + 4, 49), (cx + 18, 44)], fill=(20, 26, 22))
    for s in (-1, 1):                                            # ojos
        ex = cx + s * 10
        d.polygon([(ex - 5 * s, 46), (ex + 4 * s, 48), (ex + 3 * s, 51), (ex - 4 * s, 50)], fill=(250, 226, 110))
        d.point((ex, 49), fill=(60, 40, 10))
    rgb[:] = np.asarray(im, np.float32)

    # --------------------------------------------------------- tentáculos
    tents = []
    for k in range(8):
        off = (k - 3.5) * 4.6
        L = 62 + rng.uniform(-10, 34) + (16 - abs(off)) * 1.4
        ph, fr, am = rng.uniform(0, 6.3), rng.uniform(5, 8), rng.uniform(5, 9)
        pts = []
        for i in range(22):
            u = i / 21
            x = cx + off * (1 + 1.3 * u) + math.sin(u * fr + ph) * am * u ** 0.8
            y = 61 + L * u
            pts.append((x, y))
        curl = 1 if (off >= 0) ^ (k % 3 == 0) else -1             # rizo final
        x, y = pts[-1]
        for i in range(1, 9):
            a = i / 8 * math.pi * 1.6
            r_ = 6 - i * 0.35
            pts.append((x + curl * (r_ - r_ * math.cos(a)), y + r_ * math.sin(a) - i * 0.6))
        tents.append(pts)
    for k, pts in enumerate(sorted(tents, key=lambda p: abs(p[0][0] - cx), reverse=True)):
        tm = mascara(lambda d: tubo(d, pts, 5.2, 0.8, pasos=3))
        pinta(tm, (70, 92, 70), rim=(170, 192, 160), tex=0.35, seed=80 + k)
        for i in range(2, len(pts) - 8, 2):                       # ventosas en la cara interna
            x, y = pts[i]
            xi, yi = int(x + (1 if pts[i][0] < cx else -2)), int(y)
            if 0 <= xi < W and 0 <= yi < H and alpha[yi, xi]:
                rgb[yi, xi] = (150, 160, 132)

    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.polygon([(cx - 17, 40), (cx - 3, 46), (cx - 4, 49), (cx - 18, 44)], fill=(20, 26, 22))
    d.polygon([(cx + 17, 40), (cx + 3, 46), (cx + 4, 49), (cx + 18, 44)], fill=(20, 26, 22))
    for s_ in (-1, 1):
        ex = cx + s_ * 10
        d.polygon([(ex - 5 * s_, 46), (ex + 4 * s_, 48), (ex + 3 * s_, 52), (ex - 4 * s_, 51)], fill=(250, 226, 110))
        d.point((ex, 49), fill=(60, 40, 10))
    rgb[:] = np.asarray(im, np.float32)
    rgb[~alpha] = 0

    # ---------------------------------------------------- agua escurriendo
    ys, xs_ = np.nonzero(alpha)
    for _ in range(120):
        i = rng.integers(0, len(ys))
        x, y = xs_[i], ys[i]
        if y < 60:
            continue
        L = int(rng.uniform(6, 40))
        for j in range(L):
            yy_ = y + j
            if yy_ >= H:
                break
            if alpha[yy_, x] and rng.random() > 0.08:
                rgb[yy_, x] = rgb[yy_, x] * 0.3 + np.array([150, 168, 172]) * 0.7
            elif not alpha[yy_, x] and rng.random() < 0.5:        # gotas que caen
                rgb[yy_, x] = (140, 158, 164)
                alpha[yy_, x] = True

    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = alpha * 255
    ojos = [((cx + s * 10 + dx, 49 + dy), (250, 226, 110)) for s in (-1, 1) for dx in (-2, 0, 2) for dy in (-1, 0)]
    save("primigenio", Image.fromarray(out), (cx, fy), ojos,
         "criatura colosal alada con tentáculos; ancla = línea del agua; la parte baja queda tapada por olas y espuma")


def pesquero():
    W, H = 62, 50
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wl = 42                                                       # línea del agua
    # mástiles y aparejos
    d.line([(20, wl - 12), (20, 2)], fill=(40, 36, 32), width=1)
    d.line([(34, wl - 12), (34, 6)], fill=(40, 36, 32), width=1)
    d.line([(16, 8), (24, 8)], fill=(40, 36, 32))
    d.line([(30, 12), (38, 12)], fill=(40, 36, 32))
    d.line([(20, 3), (4, wl - 8)], fill=(70, 66, 60))            # cables
    d.line([(20, 3), (34, 6), (58, wl - 9)], fill=(70, 66, 60))
    d.line([(34, 8), (50, 26)], fill=(40, 36, 32), width=1)       # pluma
    d.line([(20, 10), (2, 20)], fill=(40, 36, 32))                # tangón
    # casco
    d.polygon([(2, wl - 10), (60, wl - 12), (56, wl), (52, wl + 4), (8, wl + 4), (4, wl - 2)], fill=(120, 34, 28))
    d.polygon([(2, wl - 10), (60, wl - 12), (59, wl - 9), (3, wl - 7)], fill=(30, 26, 24))
    d.line([(6, wl - 3), (55, wl - 4)], fill=(190, 184, 170))     # franja
    d.text((40, wl - 9), "", fill=(200, 196, 186))
    # cabina
    d.rectangle([24, wl - 22, 44, wl - 10], fill=(190, 184, 170))
    d.rectangle([26, wl - 27, 40, wl - 22], fill=(170, 164, 150))
    for x in (27, 32, 37):
        d.rectangle([x, wl - 19, x + 3, wl - 16], fill=(30, 36, 40))
    d.rectangle([24, wl - 23, 44, wl - 22], fill=(110, 34, 28))
    d.rectangle([12, wl - 15, 22, wl - 11], fill=(92, 70, 50))    # carga / redes
    arr = np.asarray(im).copy()
    save("pesquero", Image.fromarray(arr), (31, wl), [((20, 2), (250, 220, 120)), ((39, wl - 18), (240, 200, 100))],
         "barco pesquero de arrastre, proa a la derecha; ancla = línea del agua; usar con flota y balanceo")


if __name__ == "__main__":
    primigenio()
    pesquero()
