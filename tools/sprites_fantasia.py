"""Sprites de fantasía oscura (sprites/fantasia/), pintados con volumen.

  guerrero_sentado  guerrero con capa y capucha, sentado junto al fuego, mira a la derecha, espada clavada al lado

  python tools/sprites_fantasia.py
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "sprites" / "fantasia"
OUT.mkdir(parents=True, exist_ok=True)
OJO = [255, 200, 120]
L = np.array([0.75, -0.35, 0.56]); L /= np.linalg.norm(L)       # luz desde la derecha (la fogata)
HV = L + np.array([0, 0, 1.0]); HV /= np.linalg.norm(HV)


def ruido(w, h, cell, seed):
    r = np.random.default_rng(seed)
    g = Image.fromarray((r.random((h // cell + 3, w // cell + 3)) * 255).astype(np.uint8))
    return np.asarray(g.resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC), np.float32)[:h, :w] / 255


class Lienzo:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), bool)
        self.piel = (ruido(W, H, 3, 5) - 0.5) * 0.6 + (ruido(W, H, 1, 6) - 0.5) * 0.25

    def mascara(self, fn):
        im = Image.new("L", (self.W, self.H), 0)
        fn(ImageDraw.Draw(im))
        return np.asarray(im) > 127

    def altura(self, m, r):
        b = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
        return np.clip((b - 0.4) / 0.6, 0, 1) ** 0.6

    def pinta(self, m, base, r=3.0, relieve=5.0, bump=0.8, spec=0.35, dureza=18, amb=0.38, rim=(120, 200, 190),
              extra_h=None, oclusion=True):
        h = self.altura(m, r) * relieve
        if extra_h is not None:
            h = h + extra_h
        h = h + self.piel * bump
        gy, gx = np.gradient(h)
        n = np.stack([-gx, -gy, np.ones_like(h)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        dif = np.clip(n @ L, 0, 1)
        sp = np.clip(n @ HV, 0, 1) ** dureza * spec
        borde = (1 - n[..., 2]) ** 2.2 * np.clip(n[..., 0] * 0.4 - n[..., 1] * 0.9, 0, 1)
        col = np.array(base, np.float32) * (amb + 0.9 * dif)[..., None]
        col += sp[..., None] * np.array([200, 220, 210], np.float32)
        col += (borde * 0.9)[..., None] * np.array(rim, np.float32)
        if oclusion:
            ao = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
            detras = self.a & ~m
            self.rgb[detras] *= (1 - 0.5 * ao[detras])[..., None]
        self.rgb[m] = col[m]
        self.a |= m

    def plano(self, m, color):
        self.rgb[m] = color
        self.a |= m

    def guarda(self, nombre, ancla, brillos=(), notas=""):
        arr = np.zeros((self.H, self.W, 4), np.uint8)
        arr[..., :3] = np.clip(self.rgb, 0, 255).astype(np.uint8)
        arr[..., 3] = self.a * 255
        Image.fromarray(arr).save(OUT / f"{nombre}.png")
        (OUT / f"{nombre}.json").write_text(json.dumps(
            {"ancla": list(ancla), "brillos": [{"pos": list(b), "color": OJO} for b in brillos], "notas": notas},
            indent=2, ensure_ascii=False))
        print("Sprite:", nombre, (self.W, self.H))


def camino(pts, paso=0.7):
    tot = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / paso))
        tot += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    return tot


def tubo(d, tot, radios, dy=0.0, k=1.0):
    for (x, y), r in zip(tot, radios):
        rr = r * k
        d.ellipse([x - rr, y - rr + dy * r, x + rr, y + rr + dy * r], fill=255)


def bezier(ps, n=60):
    out = []
    for u in np.linspace(0, 1, n):
        pts = list(ps)
        while len(pts) > 1:
            pts = [((1 - u) * a[0] + u * b[0], (1 - u) * a[1] + u * b[1]) for a, b in zip(pts, pts[1:])]
        out.append(pts[0])
    return out



CAPA, CAPA_D = (46, 52, 50), (28, 32, 32)
ACERO, ACERO_D = (120, 124, 130), (70, 72, 78)
CUERO = (78, 54, 36)
PIEL = (150, 104, 76)


def guerrero_sentado():
    lz = Lienzo(84, 92)
    hx, by = 34, 91                                            # cadera sobre una piedra, pies en by
    X = lambda dx, dy: (hx + dx, by + dy)
    # espada clavada en el suelo, detrás (a la izquierda)
    hoja = lz.mascara(lambda d: d.polygon([X(-26, -58), X(-23, -58), X(-23, 0), X(-24.5, 3), X(-26, 0)], fill=255))
    lz.pinta(hoja, ACERO, r=1, relieve=2, spec=1.0, dureza=30, rim=(255, 170, 90))
    guarda = lz.mascara(lambda d: d.rectangle([*X(-31, -60), *X(-18, -58)], fill=255))
    lz.pinta(guarda, ACERO_D, r=1, relieve=1.5, spec=0.8)
    puno = lz.mascara(lambda d: (d.rectangle([*X(-26, -70), *X(-23, -60)], fill=255), d.ellipse([*X(-27, -74), *X(-22, -69)], fill=255)))
    lz.pinta(puno, CUERO, r=1, relieve=1.5)
    # piedra donde está sentado
    pied = lz.mascara(lambda d: d.ellipse([*X(-16, -16), *X(14, 2)], fill=255))
    lz.pinta(pied, (70, 70, 72), r=3, relieve=4, bump=1.2)
    # pierna de atrás y de adelante (rodilla arriba)
    for dx, col in ((4, CUERO), (0, (96, 66, 44))):
        mus = lz.mascara(lambda d: d.polygon([X(-6 + dx, -26), X(4 + dx, -30), X(22 + dx, -34), X(24 + dx, -26), X(2 + dx, -16)], fill=255))
        lz.pinta(mus, col, r=2, relieve=4)
        pan = lz.mascara(lambda d: d.polygon([X(18 + dx, -34), X(25 + dx, -32), X(26 + dx, -2), X(19 + dx, -2)], fill=255))
        lz.pinta(pan, col, r=2, relieve=3)
        bota = lz.mascara(lambda d: d.polygon([X(17 + dx, -12), X(26 + dx, -12), X(32 + dx, 0), X(17 + dx, 0)], fill=255))
        lz.pinta(bota, (40, 30, 24), r=1.5, relieve=3, spec=0.5)
        rod = lz.mascara(lambda d: d.ellipse([*X(18 + dx, -38), *X(26 + dx, -30)], fill=255))
        lz.pinta(rod, ACERO, r=1, relieve=2.5, spec=0.9, rim=(255, 170, 90))
    # capa que cae por la espalda hasta el suelo
    capa = lz.mascara(lambda d: d.polygon([X(-4, -66), X(6, -68), X(4, -40), X(-2, -14), X(-18, 0), X(-22, -2), X(-14, -30)], fill=255))
    lz.pinta(capa, CAPA_D, r=4, relieve=6, bump=0.8)
    pl = lz.mascara(lambda d: [d.line([X(-6 - k * 3, -56 + k * 4), X(-14 - k * 2, -4)], fill=255) for k in range(3)])
    lz.rgb[pl & capa] *= 0.7
    # torso inclinado hacia el fuego, cota de malla y peto
    tor = lz.mascara(lambda d: d.polygon([X(-4, -64), X(10, -66), X(18, -46), X(10, -24), X(-4, -24)], fill=255))
    lz.pinta(tor, (84, 86, 90), r=3, relieve=5, bump=1.4, spec=0.4)
    peto = lz.mascara(lambda d: d.polygon([X(2, -60), X(12, -62), X(17, -46), X(10, -34), X(2, -36)], fill=255))
    lz.pinta(peto, ACERO, r=2, relieve=4, spec=0.9, dureza=24, rim=(255, 170, 90), oclusion=False)
    cin = lz.mascara(lambda d: d.polygon([X(-4, -28), X(11, -30), X(11, -25), X(-4, -23)], fill=255))
    lz.pinta(cin, CUERO, r=1, relieve=1.5, oclusion=False)
    hom = lz.mascara(lambda d: d.ellipse([*X(-2, -70), *X(14, -56)], fill=255))
    lz.pinta(hom, ACERO_D, r=2, relieve=4, spec=0.9, rim=(255, 170, 90), oclusion=False)
    # brazo apoyado en la rodilla, manos al fuego
    brazo = lz.mascara(lambda d: d.line([X(8, -62), X(16, -46), X(26, -40)], fill=255, width=5))
    lz.pinta(brazo, CAPA, r=1.5, relieve=3, oclusion=False)
    mano = lz.mascara(lambda d: d.ellipse([*X(25, -43), *X(31, -37)], fill=255))
    lz.pinta(mano, (60, 44, 32), r=1, relieve=2, oclusion=False)
    # capucha con la cara en sombra
    cap = lz.mascara(lambda d: d.polygon([X(-2, -84), X(8, -88), X(18, -80), X(20, -68), X(12, -62), X(0, -62), X(-6, -72)], fill=255))
    lz.pinta(cap, CAPA, r=3, relieve=5, bump=0.6)
    cara = lz.mascara(lambda d: d.polygon([X(10, -80), X(18, -78), X(19, -68), X(12, -64), X(9, -70)], fill=255))
    lz.plano(cara, (16, 12, 12))
    lit = lz.mascara(lambda d: d.polygon([X(15, -76), X(19, -74), X(19, -68), X(15, -66)], fill=255))
    lz.pinta(lit, PIEL, r=1, relieve=2, rim=(255, 170, 90), oclusion=False)
    barba = lz.mascara(lambda d: d.polygon([X(13, -68), X(19, -68), X(16, -63)], fill=255))
    lz.plano(barba, (40, 30, 26))
    ojo = (hx + 16, by - 73)
    lz.guarda("guerrero_sentado", (hx, by), brillos=[ojo],
              notas="Guerrero sentado en una piedra, inclinado hacia la fogata (a su derecha). El ojo refleja el fuego.")


if __name__ == "__main__":
    guerrero_sentado()
