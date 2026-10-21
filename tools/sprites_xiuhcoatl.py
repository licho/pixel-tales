"""Sprites de la leyenda de la Xiuhcóatl (sprites/xiuhcoatl/), pintados con volumen.

  huitzilopochtli  dios solar mexica de frente: casco de colibrí, pintura azul, escudo con plumas
  xiuhcoatl        serpiente de fuego volando a la izquierda (hocico doblado hacia atrás, cuerpo segmentado,
                   cola en rayo); usar con `emite` para que brille
  coatlicue        Coatlicue barriendo, falda de serpientes, mira a la derecha
  coyolxauhqui     guerrera con cascabeles en las mejillas, mira a la derecha
  trabajador       trabajador de 1978 con casco y pala
  plumas           bola de plumas (pequeña)

  python tools/sprites_xiuhcoatl.py
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "sprites" / "xiuhcoatl"
OUT.mkdir(parents=True, exist_ok=True)
OJO = [255, 150, 50]

L = np.array([0.35, -0.75, 0.56]); L /= np.linalg.norm(L)       # luz desde arriba (abertura del cenote / cielo)
HV = L + np.array([0, 0, 1.0]); HV /= np.linalg.norm(HV)

ESCAMA, ESCAMA_D, VIENTRE = (70, 66, 44), (40, 36, 26), (150, 140, 100)
PLUMA, PLUMA_D, PLUMA_L = (52, 132, 84), (24, 66, 50), (110, 190, 140)
AZUL, AZUL_D = (58, 118, 156), (34, 76, 112)
JADE, BLANCO, ORO = (60, 150, 90), (220, 214, 196), (236, 200, 70)



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



AZUL, AZUL_D = (56, 96, 168), (34, 60, 120)
AMAR, ROJO, ROJO_D = (236, 196, 70), (176, 44, 32), (110, 26, 22)
VERDE, VERDE_L = (40, 120, 80), (90, 180, 120)
PIEL, PIEL_D = (150, 100, 66), (110, 72, 46)
BLANCO, ORO, NEGRO = (226, 220, 200), (236, 200, 70), (24, 18, 16)
FUEGO = [(255, 240, 170), (255, 196, 80), (240, 120, 40), (180, 50, 30)]
CALIDO = (255, 170, 90)


def plumas_abanico(lz, cx, cy, n, largo, a0, a1, cols, ancho=0.09):
    for k in range(n):
        a = math.radians(a0 + (a1 - a0) * k / max(n - 1, 1))
        tip = (cx + math.cos(a) * largo, cy + math.sin(a) * largo)
        px, py = -math.sin(a) * largo * ancho, math.cos(a) * largo * ancho
        poly = [(cx, cy), (cx + math.cos(a) * largo * 0.5 + px, cy + math.sin(a) * largo * 0.5 + py), tip,
                (cx + math.cos(a) * largo * 0.5 - px, cy + math.sin(a) * largo * 0.5 - py)]
        m = lz.mascara(lambda d: d.polygon(poly, fill=255))
        lz.pinta(m, cols[k % len(cols)], r=1, relieve=1.5, oclusion=False)


def huitzilopochtli():
    lz = Lienzo(84, 112)
    cx, by = 42, 111
    X = lambda dx, dy: (cx + dx, by + dy)
    plumas_abanico(lz, *X(0, -86), 13, 30, -175, -5, [VERDE, VERDE_L, (60, 140, 170)])      # tocado
    for s in (-1, 1):                                                     # piernas
        m = lz.mascara(lambda d: d.polygon([X(s * 3, -40), X(s * 11, -40), X(s * 10, -2), X(s * 4, -2)], fill=255))
        lz.pinta(m, AZUL, r=2, relieve=4)
        m = lz.mascara(lambda d: d.rectangle([*X(min(s * 3, s * 12), -4), *X(max(s * 3, s * 12), 0)], fill=255))
        lz.plano(m, (90, 60, 34))
        m = lz.mascara(lambda d: d.rectangle([*X(min(s * 4, s * 11), -16), *X(max(s * 4, s * 11), -13)], fill=255))
        lz.plano(m, ORO)
    tor = lz.mascara(lambda d: d.polygon([X(-13, -70), X(13, -70), X(11, -38), X(-11, -38)], fill=255))
    lz.pinta(tor, AZUL, r=4, relieve=6)
    tap = lz.mascara(lambda d: d.polygon([X(-12, -42), X(12, -42), X(9, -28), X(-9, -28)], fill=255))
    lz.pinta(tap, BLANCO, r=2, relieve=2, oclusion=False)
    pec = lz.mascara(lambda d: d.chord([*X(-12, -74), *X(12, -60)], 0, 180, fill=255))
    lz.pinta(pec, ORO, r=1.5, relieve=2, spec=0.8, oclusion=False)
    for s in (-1, 1):                                                     # brazos
        m = lz.mascara(lambda d: d.polygon([X(s * 13, -70), X(s * 18, -68), X(s * 20, -48), X(s * 15, -48)], fill=255))
        lz.pinta(m, AZUL, r=2, relieve=4)
    cab = lz.mascara(lambda d: d.ellipse([*X(-8, -90), *X(8, -72)], fill=255))
    lz.pinta(cab, AZUL_D, r=3, relieve=5)
    for y in (-84, -80):                                                  # franjas amarillas en la cara
        m = lz.mascara(lambda d: d.line([X(-7, y), X(7, y)], fill=255))
        lz.rgb[m & cab] = AMAR
    for s in (-1, 1):
        m = lz.mascara(lambda d: d.rectangle([*X(s * 3 - 1, -83), *X(s * 3 + 1, -82)], fill=255))
        lz.plano(m, NEGRO)
    casco = lz.mascara(lambda d: d.pieslice([*X(-10, -96), *X(10, -78)], 180, 360, fill=255))
    lz.pinta(casco, VERDE, r=2, relieve=3, spec=0.6)
    pico = lz.mascara(lambda d: d.polygon([X(-2, -92), X(2, -92), X(0, -104)], fill=255))
    lz.pinta(pico, (60, 50, 40), r=1, relieve=2, oclusion=False)
    # escudo (chimalli) en el brazo izquierdo, con 5 bolas de plumón
    esc = lz.mascara(lambda d: d.ellipse([*X(-36, -70), *X(-10, -44)], fill=255))
    lz.pinta(esc, (60, 100, 150), r=4, relieve=5, spec=0.5)
    for dx, dy in ((-23, -63), (-30, -57), (-16, -57), (-27, -50), (-19, -50)):
        m = lz.mascara(lambda d: d.ellipse([*X(dx - 2, dy - 2), *X(dx + 2, dy + 2)], fill=255))
        lz.pinta(m, BLANCO, r=1, relieve=1.5, oclusion=False)
    for k in range(5):                                                    # plumas colgando del escudo
        m = lz.mascara(lambda d: d.line([X(-30 + k * 4, -45), X(-31 + k * 4, -36)], fill=255, width=2))
        lz.pinta(m, ROJO if k % 2 else ORO, r=1, relieve=1, oclusion=False)
    lz.guarda("huitzilopochtli", (cx, by), notas="Huitzilopochtli de frente. Mano derecha (para la Xiuhcóatl) en (60, 63) del sprite.")


def xiuhcoatl():
    lz = Lienzo(200, 76)
    pts = [(28 + 160 * u, 40 + 12 * math.sin(u * 2 * math.pi * 1.2 + 0.6) * (0.3 + 0.7 * u)) for u in np.linspace(0, 1, 100)]
    tot = camino(pts)
    n = len(tot)
    radios = [9 - 6 * (i / n) for i in range(n)]                         # cabeza a la izquierda, gruesa
    body = lz.mascara(lambda d: tubo(d, tot, radios))
    lz.pinta(body, FUEGO[2], r=3, relieve=6, bump=0.6, rim=CALIDO)
    for i in range(0, n, 9):                                             # segmentos
        (x0, y0), (x1, y1), r = tot[max(i - 2, 0)], tot[min(i + 2, n - 1)], radios[i]
        dx, dy = x1 - x0, y1 - y0
        nn = math.hypot(dx, dy) or 1
        px, py = -dy / nn, dx / nn
        x, y = tot[i]
        m = lz.mascara(lambda d: d.line([(x - px * r, y - py * r), (x + px * r, y + py * r)], fill=255, width=2))
        lz.rgb[m & body] = FUEGO[3]
    lomo = lz.mascara(lambda d: tubo(d, tot, radios, dy=-0.35, k=0.45)) & body
    lz.rgb[lomo] = lz.rgb[lomo] * 0.4 + np.array(FUEGO[1], np.float32) * 0.7
    # llamas saliendo del lomo
    rng = np.random.default_rng(3)
    for i in range(6, n - 6, 6):
        x, y = tot[i]
        r = radios[i]
        h = r * rng.uniform(1.2, 2.2)
        m = lz.mascara(lambda d: d.polygon([(x - r * 0.4, y - r * 0.6), (x + r * 0.5, y - r * 0.6), (x + r * 0.9, y - r * 0.6 - h)], fill=255))
        lz.plano(m, FUEGO[1] if i % 12 else FUEGO[0])
    # cola: signo del año (trapecio y rayo)
    tx, ty = tot[-1]
    m = lz.mascara(lambda d: d.polygon([(tx - 2, ty - 6), (tx + 6, ty - 9), (tx + 6, ty + 9), (tx - 2, ty + 6)], fill=255))
    lz.pinta(m, FUEGO[1], r=1, relieve=2, rim=CALIDO)
    m = lz.mascara(lambda d: d.polygon([(tx + 6, ty - 3), (tx + 12, ty - 1), (tx + 9, ty + 1), (tx + 14, ty + 4), (tx + 6, ty + 3)], fill=255))
    lz.plano(m, FUEGO[0])
    # cabeza con hocico doblado hacia atrás (hacia arriba)
    hx, hy = tot[0]
    cab = lz.mascara(lambda d: d.polygon([(hx + 6, hy - 9), (hx - 10, hy - 8), (hx - 18, hy - 2), (hx - 16, hy + 6), (hx + 6, hy + 9)], fill=255))
    lz.pinta(cab, FUEGO[2], r=2, relieve=4, rim=CALIDO)
    hoc = lz.mascara(lambda d: d.polygon([(hx - 18, hy - 2), (hx - 24, hy - 6), (hx - 22, hy - 16), (hx - 16, hy - 12), (hx - 12, hy - 7)], fill=255))
    lz.pinta(hoc, FUEGO[1], r=1.5, relieve=3, rim=CALIDO)
    boca = lz.mascara(lambda d: d.polygon([(hx - 17, hy + 1), (hx - 2, hy + 2), (hx - 15, hy + 6)], fill=255))
    lz.plano(boca, FUEGO[3])
    for fx in (-14, -9, -5):
        m = lz.mascara(lambda d: d.polygon([(hx + fx, hy + 2), (hx + fx + 2, hy + 2), (hx + fx + 1, hy + 5)], fill=255))
        lz.plano(m, FUEGO[0])
    ojo = (round(hx - 6), round(hy - 4))
    m = lz.mascara(lambda d: d.ellipse([ojo[0] - 2, ojo[1] - 1.5, ojo[0] + 2, ojo[1] + 1.5], fill=255))
    lz.plano(m, FUEGO[0])
    lz.guarda("xiuhcoatl", (100, 75), brillos=[ojo], notas="Serpiente de fuego volando a la izquierda. Usa `emite: 1.0` para que brille.")


def coatlicue():
    lz = Lienzo(60, 84)
    fx, by = 26, 83
    X = lambda dx, dy: (fx + dx, by + dy)
    falda = lz.mascara(lambda d: d.polygon([X(-12, -40), X(10, -40), X(14, 0), X(-14, 0)], fill=255))
    lz.pinta(falda, (70, 96, 60), r=3, relieve=4)
    for k in range(5):                                                   # falda de serpientes entrelazadas
        y = -36 + k * 7
        m = lz.mascara(lambda d: d.line([X(-13 + k * 0.5, y), X(-4, y + 3), X(4, y), X(12 + k * 0.5, y + 3)], fill=255, width=2))
        lz.rgb[m & falda] = (130, 150, 80)
    m = lz.mascara(lambda d: d.line([X(-14, -1), X(14, -1)], fill=255, width=2))
    lz.rgb[m & falda] = (200, 180, 120)
    tor = lz.mascara(lambda d: d.polygon([X(-8, -62), X(6, -62), X(8, -40), X(-9, -40)], fill=255))
    lz.pinta(tor, PIEL, r=3, relieve=4)
    hui = lz.mascara(lambda d: d.polygon([X(-9, -60), X(7, -60), X(8, -44), X(-9, -44)], fill=255))
    lz.pinta(hui, BLANCO, r=2, relieve=2, oclusion=False)
    cab = lz.mascara(lambda d: d.ellipse([*X(-6, -76), *X(6, -62)], fill=255))
    lz.pinta(cab, PIEL, r=2, relieve=4, oclusion=False)
    pelo = lz.mascara(lambda d: (d.pieslice([*X(-7, -78), *X(7, -64)], 160, 380, fill=255), d.rectangle([*X(-7, -72), *X(-4, -58)], fill=255)))
    lz.pinta(pelo, NEGRO, r=1, relieve=2, oclusion=False)
    ojo = lz.mascara(lambda d: d.point(X(3, -70), fill=255))
    lz.plano(ojo, NEGRO)
    # escoba de varas, inclinada hacia adelante
    br = lz.mascara(lambda d: d.line([X(6, -56), X(18, -6)], fill=255, width=2))
    lz.plano(br, (110, 80, 44))
    esc = lz.mascara(lambda d: d.polygon([X(15, -10), X(21, -10), X(30, 0), X(12, 0)], fill=255))
    lz.pinta(esc, (176, 150, 90), r=1, relieve=2, oclusion=False)
    brazo = lz.mascara(lambda d: d.line([X(2, -58), X(10, -46), X(12, -38)], fill=255, width=3))
    lz.pinta(brazo, PIEL, r=1, relieve=2, oclusion=False)
    lz.guarda("coatlicue", (fx, by), notas="Coatlicue barriendo con falda de serpientes, mira a la derecha.")


def coyolxauhqui():
    lz = Lienzo(56, 84)
    fx, by = 24, 83
    X = lambda dx, dy: (fx + dx, by + dy)
    for s, c in ((-1, PIEL_D), (1, PIEL)):
        m = lz.mascara(lambda d: d.polygon([X(s * 2, -34), X(s * 8, -34), X(s * 9 + 4, -2), X(s * 4 + 4, -2)], fill=255))
        lz.pinta(m, c, r=2, relieve=3)
    falda = lz.mascara(lambda d: d.polygon([X(-10, -44), X(10, -44), X(12, -28), X(-12, -28)], fill=255))
    lz.pinta(falda, ROJO, r=2, relieve=3)
    tor = lz.mascara(lambda d: d.polygon([X(-8, -64), X(8, -64), X(9, -44), X(-9, -44)], fill=255))
    lz.pinta(tor, PIEL, r=3, relieve=4)
    cin = lz.mascara(lambda d: d.rectangle([*X(-9, -46), *X(9, -43)], fill=255))
    lz.plano(cin, (60, 100, 70))
    cab = lz.mascara(lambda d: d.ellipse([*X(-6, -78), *X(7, -64)], fill=255))
    lz.pinta(cab, PIEL, r=2, relieve=4, oclusion=False)
    for dx, dy in ((5, -68), (3, -66)):                                  # cascabeles dorados en la mejilla
        m = lz.mascara(lambda d: d.ellipse([*X(dx - 1.5, dy - 1.5), *X(dx + 1.5, dy + 1.5)], fill=255))
        lz.pinta(m, ORO, r=1, relieve=1, spec=0.9, oclusion=False)
    tocado = lz.mascara(lambda d: d.pieslice([*X(-8, -82), *X(8, -68)], 180, 360, fill=255))
    lz.pinta(tocado, (220, 220, 210), r=1, relieve=2, oclusion=False)
    for k in range(3):
        m = lz.mascara(lambda d: d.ellipse([*X(-6 + k * 5, -84), *X(-2 + k * 5, -80)], fill=255))
        lz.pinta(m, BLANCO, r=1, relieve=1, oclusion=False)
    ojo = lz.mascara(lambda d: d.point(X(4, -72), fill=255))
    lz.plano(ojo, NEGRO)
    esc = lz.mascara(lambda d: d.ellipse([*X(-18, -64), *X(-4, -46)], fill=255))
    lz.pinta(esc, (200, 170, 100), r=2, relieve=3)
    arma = lz.mascara(lambda d: d.line([X(8, -60), X(20, -76)], fill=255, width=2))
    lz.plano(arma, (100, 70, 40))
    for k in range(4):                                                   # navajas de obsidiana del macuahuitl
        m = lz.mascara(lambda d: d.point(X(10 + k * 3 + 1, -64 - k * 4), fill=255))
        lz.plano(m, NEGRO)
    lz.guarda("coyolxauhqui", (fx, by), notas="Coyolxauhqui guerrera, cascabeles en la mejilla, mira a la derecha.")


def trabajador():
    lz = Lienzo(40, 64)
    fx, by = 18, 63
    X = lambda dx, dy: (fx + dx, by + dy)
    OVER, OVER_D = (70, 80, 110), (50, 56, 80)
    for s, c in ((-1, OVER_D), (1, OVER)):
        m = lz.mascara(lambda d: d.polygon([X(s * 1, -26), X(s * 7, -26), X(s * 6, -2), X(s * 2, -2)], fill=255))
        lz.pinta(m, c, r=1.5, relieve=3)
        m = lz.mascara(lambda d: d.rectangle([*X(min(s * 1, s * 8), -3), *X(max(s * 1, s * 8), 0)], fill=255))
        lz.plano(m, (40, 30, 24))
    tor = lz.mascara(lambda d: d.polygon([X(-8, -46), X(8, -46), X(7, -26), X(-7, -26)], fill=255))
    lz.pinta(tor, OVER, r=3, relieve=4)
    cab = lz.mascara(lambda d: d.ellipse([*X(-5, -56), *X(5, -46)], fill=255))
    lz.pinta(cab, PIEL, r=2, relieve=3, oclusion=False)
    casco = lz.mascara(lambda d: (d.pieslice([*X(-6, -60), *X(6, -48)], 180, 360, fill=255), d.rectangle([*X(-7, -54), *X(7, -53)], fill=255)))
    lz.pinta(casco, (230, 190, 50), r=1.5, relieve=3, spec=0.8, oclusion=False)
    pala = lz.mascara(lambda d: d.line([X(10, -50), X(4, -6)], fill=255, width=2))
    lz.plano(pala, (120, 90, 50))
    hoja = lz.mascara(lambda d: d.polygon([X(1, -8), X(7, -8), X(6, 0), X(2, 0)], fill=255))
    lz.pinta(hoja, (130, 132, 136), r=1, relieve=2, spec=0.9, oclusion=False)
    brazo = lz.mascara(lambda d: d.line([X(6, -44), X(9, -34), X(7, -28)], fill=255, width=3))
    lz.pinta(brazo, OVER, r=1, relieve=2, oclusion=False)
    lz.guarda("trabajador", (fx, by), notas="Trabajador de 1978 con casco amarillo y pala.")


def plumas():
    lz = Lienzo(16, 16)
    m = lz.mascara(lambda d: d.ellipse([3, 3, 13, 13], fill=255))
    lz.pinta(m, (226, 226, 220), r=2, relieve=3)
    for a in range(0, 360, 45):
        r = math.radians(a)
        m = lz.mascara(lambda d: d.line([(8, 8), (8 + math.cos(r) * 7, 8 + math.sin(r) * 7)], fill=255))
        lz.plano(m, (240, 240, 236) if a % 90 else (180, 210, 220))
    lz.guarda("plumas", (8, 15), notas="Bola de plumas que cae del cielo.")


if __name__ == "__main__":
    huitzilopochtli()
    xiuhcoatl()
    coatlicue()
    coyolxauhqui()
    trabajador()
    plumas()
