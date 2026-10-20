"""Genera la criatura colosal (estilo Cthulhu de Lovecraft, 1928, dominio público) con volumen real:
cada parte tiene un mapa de alturas, de ahí salen normales y se ilumina con luz fría de tormenta,
brillos de piel mojada, borde de contraluz y oclusión entre partes.

  python tools/sprite_primigenio.py      -> sprites/oceano/primigenio.png (270x192) y primigenio_xl.png (x1.3)
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "sprites" / "oceano"
OUT.mkdir(parents=True, exist_ok=True)

L = np.array([0.55, -0.62, 0.56]); L /= np.linalg.norm(L)          # luz principal: arriba a la derecha
HV = L + np.array([0, 0, 1.0]); HV /= np.linalg.norm(HV)            # vector medio (brillo especular)


def ruido(w, h, cell, seed):
    r = np.random.default_rng(seed)
    g = Image.fromarray((r.random((h // cell + 3, w // cell + 3)) * 255).astype(np.uint8))
    return np.asarray(g.resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC), np.float32)[:h, :w] / 255


class Lienzo:
    def __init__(self, W, H, S):
        self.W, self.H, self.S = W, H, S
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), bool)
        self.piel = (ruido(W, H, max(2, int(4 * S)), 5) - 0.5) * 0.55 + (ruido(W, H, max(1, int(2 * S)), 6) - 0.5) * 0.2

    def mascara(self, fn):
        im = Image.new("L", (self.W, self.H), 0)
        fn(ImageDraw.Draw(im))
        return np.asarray(im) > 127

    def altura(self, m, r):
        b = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
        return np.clip((b - 0.4) / 0.6, 0, 1) ** 0.6

    def pinta(self, m, base, r=4.0, relieve=6.0, bump=1.0, spec=0.7, dureza=22, amb=0.30, rim=(170, 196, 200),
              extra_h=None, oclusion=True):
        """Ilumina la parte m con volumen y la pinta encima de lo anterior."""
        S = self.S
        h = self.altura(m, r * S) * relieve * S
        if extra_h is not None:
            h = h + extra_h
        h = h + self.piel * bump * S
        gy, gx = np.gradient(h)
        n = np.stack([-gx, -gy, np.ones_like(h)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        dif = np.clip(n @ L, 0, 1)
        sp = np.clip(n @ HV, 0, 1) ** dureza * spec
        borde = (1 - n[..., 2]) ** 2.2 * np.clip(-n[..., 0] * 0.7 - n[..., 1] * 0.7, 0, 1)     # contraluz arriba-izq.
        col = np.array(base, np.float32) * (amb + 0.95 * dif)[..., None]
        col += sp[..., None] * np.array([190, 210, 215], np.float32)
        col += (borde * 1.2)[..., None] * np.array(rim, np.float32)
        if oclusion:                                                     # sombra sobre lo que queda detrás
            ao = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3 * S)),
                            np.float32) / 255
            detras = self.a & ~m
            self.rgb[detras] *= (1 - 0.55 * ao[detras])[..., None]
        self.rgb[m] = col[m]
        self.a |= m


def tubo(d, pts, r0, r1, fill=255):
    tot = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.7))
        tot += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    for i, (x, y) in enumerate(tot):
        r = r0 + (r1 - r0) * i / max(len(tot) - 1, 1)
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    return tot


def curva(p0, p1, c, n=14):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u ** 2 * p1[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u ** 2 * p1[1]) for u in np.linspace(0, 1, n)]


def primigenio(S=1.0, nombre="primigenio"):
    W, H = int(round(270 * S)), int(round(192 * S))
    cx, fy = W / 2, H - 1
    P = lambda x, y: (cx + x * S, y * S)                    # coordenadas base (x relativa al centro)
    lz = Lienzo(W, H, S)
    rng = np.random.default_rng(3)
    PIEL, PIEL_C, ALA, HUESO = (58, 84, 66), (70, 98, 76), (38, 50, 44), (70, 86, 72)

    # ------------------------------------------------------------------ alas (detrás)
    for s in (-1, 1):
        X = lambda x, y: P(s * x, y)
        hombro, codo, muneca = (32, 64), (80, 24), (102, 5)
        puntas = [(134, 2), (135, 58), (127, 106), (101, 124), (70, 114)]
        borde = [X(*hombro), X(*codo), X(*muneca)]
        prev = puntas[0]
        borde.append(X(*prev))
        for b in puntas[1:]:
            mx, my = (prev[0] + b[0]) / 2, (prev[1] + b[1]) / 2
            c = (mx + (muneca[0] - mx) * 0.5, my + (muneca[1] - my) * 0.5)
            arco = curva(prev, b, c, 12)
            for k, (x, y) in enumerate(arco[1:], 1):          # bordes rasgados
                j = rng.uniform(-1.5, 1.5) if 2 < k < 10 else 0
                borde.append(X(x + j * 0.6, y + j))
            prev = b
        borde += [X(*q) for q in curva(puntas[-1], (40, 112), (52, 100), 8)[1:]]
        mem = lz.mascara(lambda d: d.polygon(borde, fill=255))
        for _ in range(3):                                     # agujeros en la membrana
            hx, hy = rng.uniform(95, 125), rng.uniform(40, 100)
            r = rng.uniform(1.5, 3.5)
            hole = lz.mascara(lambda d: d.ellipse([*X(hx - r, hy - r * 1.6), *X(hx + r, hy + r * 1.6)] if s > 0 else
                                                   [*X(hx + r, hy - r * 1.6), *X(hx - r, hy + r * 1.6)], fill=255))
            mem &= ~hole
        # pliegues: crestas a lo largo de los dedos
        dedos = lz.mascara(lambda d: [tubo(d, [X(*muneca), X(*p)], 3.5 * S, 1.5 * S) for p in puntas])
        pl = lz.altura(dedos, 4 * S) * 3 * S
        lz.pinta(mem, ALA, r=6, relieve=2.5, bump=0.5, spec=0.25, amb=0.32, extra_h=pl, oclusion=False)
        venas = lz.mascara(lambda d: [d.line([X(*muneca), X((muneca[0] + p[0]) / 2 + 4, (muneca[1] + p[1]) / 2 + 5), X(*p)],
                                             fill=255, width=1) for p in puntas[1:]])
        lz.rgb[venas & mem] *= 0.7
        huesos = lz.mascara(lambda d: (tubo(d, [X(*hombro), X(*codo)], 4.0 * S, 3.0 * S),
                                       tubo(d, [X(*codo), X(*muneca)], 3.0 * S, 2.0 * S),
                                       [tubo(d, [X(*muneca), X(*p)], 1.7 * S, 0.6 * S) for p in puntas],
                                       d.ellipse([*X(codo[0] - 4, codo[1] - 4), *X(codo[0] + 4, codo[1] + 4)] if s > 0 else
                                                 [*X(codo[0] + 4, codo[1] - 4), *X(codo[0] - 4, codo[1] + 4)], fill=255)))
        lz.pinta(huesos, HUESO, r=1.5, relieve=3, bump=0.4, spec=0.5)
        garra = lz.mascara(lambda d: d.polygon([X(muneca[0], muneca[1] - 1), X(muneca[0] - 7, muneca[1] - 9),
                                                X(muneca[0] + 3, muneca[1] + 1)], fill=255))
        lz.pinta(garra, (40, 40, 36), r=1, relieve=2, spec=0.8)

    # ------------------------------------------------------------- torso y hombros
    torso = lz.mascara(lambda d: (
        d.polygon([P(-44, 66), P(-20, 52), P(20, 52), P(44, 66), P(54, 98), P(44, 146), P(40, 192), P(-40, 192),
                   P(-44, 146), P(-54, 98)], fill=255)))
    lz.pinta(torso, PIEL, r=10, relieve=9, bump=0.7)
    for s in (-1, 1):                                          # pectorales y abdomen con relieve propio
        pec = lz.mascara(lambda d: d.ellipse([*P(s * 4 if s > 0 else -40, 80), *P(40 if s > 0 else -4, 108)], fill=255))
        lz.pinta(pec & torso, PIEL, r=6, relieve=8, bump=0.6, oclusion=False)
    for k in range(4):
        ab = lz.mascara(lambda d: d.ellipse([*P(-22, 110 + k * 16), *P(22, 124 + k * 16)], fill=255))
        lz.pinta(ab & torso, PIEL, r=4, relieve=5, bump=0.6, oclusion=False)
    for s in (-1, 1):                                          # deltoides (hombros enormes)
        dl = lz.mascara(lambda d: d.ellipse([*P(s * 36 - 20, 60), *P(s * 36 + 20, 96)] if s > 0 else
                                            [*P(s * 36 - 20, 60), *P(s * 36 + 20, 96)], fill=255))
        lz.pinta(dl, PIEL, r=7, relieve=9, bump=0.7)

    # ------------------------------------------------------------- brazos y manos
    for s in (-1, 1):
        X = lambda x, y: P(s * x, y)
        hombro, codo, muneca = (46, 80), (90, 116), (78, 148)
        sup = lz.mascara(lambda d: tubo(d, [X(*hombro), X(68, 92), X(*codo)], 13 * S, 10.5 * S))
        lz.pinta(sup, PIEL, r=6, relieve=8, bump=0.7)
        ant = lz.mascara(lambda d: tubo(d, [X(*codo), X(86, 132), X(*muneca)], 10.5 * S, 12 * S))
        lz.pinta(ant, PIEL_C, r=6, relieve=8, bump=0.7)
        palma = lz.mascara(lambda d: d.ellipse([*X(muneca[0] - 13, muneca[1] - 6), *X(muneca[0] + 13, muneca[1] + 14)]
                                               if s > 0 else
                                               [*X(muneca[0] + 13, muneca[1] - 6), *X(muneca[0] - 13, muneca[1] + 14)], fill=255))
        lz.pinta(palma, PIEL_C, r=5, relieve=6, bump=1.0)
        for k, ang in enumerate((-58, -28, 2, 30)):             # dedos abiertos con garras
            a = math.radians(90 + ang)
            ax_, ay_ = math.cos(a), math.sin(a)
            p0 = (muneca[0] + ax_ * 9, muneca[1] + 6 + ay_ * 6)
            p1 = (p0[0] + ax_ * 13, p0[1] + ay_ * 13)
            p2 = (p1[0] + ax_ * 8 + 2, p1[1] + ay_ * 8 + 3)
            dedo = lz.mascara(lambda d: tubo(d, [X(*p0), X(*p1)], 3.6 * S, 2.8 * S))
            lz.pinta(dedo, PIEL_C, r=2, relieve=4, bump=0.8)
            una = lz.mascara(lambda d: tubo(d, [X(*p1), X(*p2)], 2.2 * S, 0.4 * S))
            lz.pinta(una, (34, 34, 30), r=1, relieve=3, spec=1.0, dureza=30)
        pulgar = lz.mascara(lambda d: tubo(d, [X(muneca[0] - 10, muneca[1] + 2), X(muneca[0] - 16, muneca[1] + 12)],
                                           3.4 * S, 2.4 * S))
        lz.pinta(pulgar, PIEL_C, r=2, relieve=4, bump=0.8)

    # ------------------------------------------------------------------- cabeza
    cabeza = lz.mascara(lambda d: (d.ellipse([*P(-26, -2), *P(26, 46)], fill=255),
                                   d.ellipse([*P(-20, 26), *P(20, 66)], fill=255)))
    xs_ = (np.arange(W)[None, :] - cx) / S
    surcos = -np.clip(np.cos(xs_ * 0.38 + lz.piel * 2.5), 0.7, 1.0) * 1.3 * S + 1.3 * S     # pliegues verticales
    surcos = surcos * (np.arange(H)[:, None] < 42 * S)
    lz.pinta(cabeza, (66, 84, 72), r=10, relieve=12, bump=0.8, extra_h=-surcos)
    cuencas = lz.mascara(lambda d: (d.ellipse([*P(-16, 47), *P(-4, 55)], fill=255), d.ellipse([*P(4, 47), *P(16, 55)], fill=255)))
    lz.rgb[cuencas] *= 0.3
    ceja = lz.mascara(lambda d: (d.polygon([P(-19, 42), P(-10, 44), P(-3, 48), P(-4, 50), P(-12, 47), P(-19, 46)], fill=255),
                                 d.polygon([P(19, 42), P(10, 44), P(3, 48), P(4, 50), P(12, 47), P(19, 46)], fill=255)))
    lz.pinta(ceja, (62, 78, 68), r=1.6, relieve=5, bump=0.5, spec=0.6)
    ojos = lz.mascara(lambda d: (d.polygon([P(-15, 49), P(-5, 51), P(-6, 53.5), P(-14, 52)], fill=255),
                                 d.polygon([P(15, 49), P(5, 51), P(6, 53.5), P(14, 52)], fill=255)))
    lz.rgb[ojos] = (30, 24, 8)
    halo = lz.mascara(lambda d: (d.ellipse([*P(-17, 47), *P(-3, 56)], fill=255), d.ellipse([*P(3, 47), *P(17, 56)], fill=255)))
    lz.rgb[halo & ~ojos & ~ceja] = lz.rgb[halo & ~ojos & ~ceja] * 0.6 + np.array([120, 104, 40]) * 0.4

    # --------------------------------------------------------------- tentáculos
    tents = []
    for k in range(9):
        off = (k - 4) * 4.0
        largo = 58 + rng.uniform(-8, 34) + (17 - abs(off)) * 1.5
        ph, fr, am = rng.uniform(0, 6.3), rng.uniform(4, 7), rng.uniform(5, 10)
        pts = []
        for i in range(26):
            u = i / 25
            x = off * (1 + 1.5 * u) + math.sin(u * fr + ph) * am * u
            pts.append((x, 61 + largo * u))
        giro = 1 if (off >= 0) ^ (k % 4 == 0) else -1
        x, y = pts[-1]
        n_rizo = 10 if k % 3 else 0                          # algunos terminan rectos
        for i in range(1, n_rizo + 1):                        # punta en gancho
            a = i / 10 * math.pi * 0.95
            r = 8
            pts.append((x + giro * (r - r * math.cos(a)), y + r * math.sin(a) - i * 0.5))
        tents.append(pts)
    for k, pts in enumerate(sorted(tents, key=lambda p: abs(p[0][0]), reverse=True)):
        tm = lz.mascara(lambda d: tubo(d, [P(*q) for q in pts], 5.8 * S, 1.3 * S))
        lz.pinta(tm, (70, 90, 74), r=2.2, relieve=5, bump=0.7, spec=0.9, dureza=26)
        for i in range(3, len(pts) - 10, 2):                   # ventosas
            x, y = P(*pts[i])
            lado = 1.5 * S if pts[i][0] < 0 else -1.5 * S
            xi, yi = int(x + lado), int(y)
            if 0 <= xi < W and 0 <= yi < H and tm[yi, xi]:
                lz.rgb[yi, xi] = (150, 162, 140)

    # ------------------------------------------------ agua agitada en la cintura
    xs_c = np.arange(W)
    linea = (168 + 5 * np.sin(xs_c / S * 0.21) + 3 * np.sin(xs_c / S * 0.57 + 1) + (ruido(W, 1, max(2, int(3 * S)), 9)[0] - 0.5) * 8) * S
    yy_c = np.arange(H)[:, None]
    bajo = (yy_c > linea[None, :]) & lz.a
    esp = ruido(W, H, max(1, int(1.5 * S)), 12)
    lz.a[bajo & (esp < 0.45)] = False                       # el agua "se come" la base
    espuma = bajo & lz.a
    lz.rgb[espuma] = np.array([170, 184, 188], np.float32) * (0.75 + 0.35 * esp[espuma])[..., None]
    for k in range(int(60 * S)):                            # salpicaduras sobre la línea del agua
        x = int(rng.uniform(cx - 50 * S, cx + 50 * S))
        y = int(linea[min(max(x, 0), W - 1)] - rng.uniform(0, 10) * S)
        if 0 <= x < W and 0 <= y < H:
            lz.rgb[y, x] = (190, 200, 204)
            lz.a[y, x] = True

    # ------------------------------------------------------- agua escurriendo
    ys, xs = np.nonzero(lz.a)
    for _ in range(int(160 * S)):
        i = rng.integers(0, len(ys))
        x, y = xs[i], ys[i]
        if y < 55 * S:
            continue
        for j in range(int(rng.uniform(6, 44) * S)):
            yy = y + j
            if yy >= H:
                break
            if lz.a[yy, x]:
                if rng.random() > 0.1:
                    lz.rgb[yy, x] = lz.rgb[yy, x] * 0.35 + np.array([150, 170, 176]) * 0.65
            elif rng.random() < 0.45:
                lz.rgb[yy, x] = (136, 154, 160)
                lz.a[yy, x] = True

    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(lz.rgb, 0, 255)
    out[..., 3] = lz.a * 255
    oy, ox = np.nonzero(ojos)
    brillos = [((int(x), int(y)), (255, 232, 120)) for x, y in zip(ox, oy)]
    Image.fromarray(out).save(OUT / f"{nombre}.png")
    (OUT / f"{nombre}.json").write_text(json.dumps(
        {"ancla": [int(cx), int(fy)], "brillos": [{"pos": list(p), "color": list(c)} for p, c in brillos],
         "notas": f"criatura colosal con volumen; generada a escala {S}; ancla = línea del agua"}, indent=2, ensure_ascii=False))
    print("Sprite:", nombre, (W, H))


if __name__ == "__main__":
    primigenio(1.0, "primigenio")
    primigenio(1.3, "primigenio_xl")
