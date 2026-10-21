"""Sprites de la leyenda de Tzukán (sprites/tzukan/), pintados con volumen (mapa de alturas -> normales -> luz).

  tronco          Tzukán dormida en el fondo: parece un tronco (cabeza a la derecha, ojos cerrados)
  alzada          Tzukán levantándose con las alas abiertas y la boca abierta, mira a la izquierda
  vuelo           Tzukán volando a la derecha con Chaac montado en el cuello
  vuelo_sola      igual, sin Chaac
  chaac_espalda   Chaac caminando, visto de espaldas (hacha en la mano)
  chaac_sentado   Chaac sentado de perfil, mira a la derecha
  jaguar          Jaguar grande de perfil mirando a la derecha, la montura de Chaac

  python tools/sprites_tzukan.py
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "sprites" / "tzukan"
OUT.mkdir(parents=True, exist_ok=True)

L = np.array([0.35, -0.75, 0.56]); L /= np.linalg.norm(L)       # luz desde arriba (abertura del cenote / cielo)
HV = L + np.array([0, 0, 1.0]); HV /= np.linalg.norm(HV)

ESCAMA, ESCAMA_D, VIENTRE = (70, 66, 44), (40, 36, 26), (150, 140, 100)
PLUMA, PLUMA_D, PLUMA_L = (52, 132, 84), (24, 66, 50), (110, 190, 140)
AZUL, AZUL_D = (58, 118, 156), (34, 76, 112)
JADE, BLANCO, ORO = (60, 150, 90), (220, 214, 196), (236, 200, 70)
OJO = [255, 220, 80]


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


def cuerpo(lz, tot, radios, seed=1, corteza=False):
    """Cuerpo de serpiente con volumen, vientre claro y manchas en rombo en el lomo."""
    body = lz.mascara(lambda d: tubo(d, tot, radios))
    lz.pinta(body, ESCAMA, r=max(radios) * 0.5, relieve=max(radios) * 0.9, bump=1.2 if corteza else 0.7)
    vien = lz.mascara(lambda d: tubo(d, tot, radios, dy=0.62, k=0.42 if corteza else 0.5)) & body
    lz.pinta(vien, VIENTRE, r=max(radios) * 0.3, relieve=max(radios) * 0.4, bump=0.4, oclusion=False)
    bandas = []
    for i in range(4, len(tot) - 2, 10):                       # bandas del vientre, perpendiculares al cuerpo
        (x0, y0), (x1, y1), r = tot[i - 2], tot[i + 2], radios[i]
        dx, dy = x1 - x0, y1 - y0
        nn = math.hypot(dx, dy) or 1
        px, py = -dy / nn, dx / nn
        x, y = tot[i]
        bandas.append([(x - px * r, y - py * r), (x + px * r, y + py * r)])
    bm = lz.mascara(lambda d: [d.line(b, fill=255) for b in bandas])
    lz.rgb[bm & vien] *= 0.72
    rng = np.random.default_rng(seed)
    sp = lz.mascara(lambda d: [d.polygon([(x - r * 0.5, y - r * 0.35), (x, y - r * 0.75), (x + r * 0.5, y - r * 0.35),
                                          (x, y + r * 0.05)], fill=255) for (x, y), r in list(zip(tot, radios))[6:-10:18]])
    lz.rgb[sp & body & ~vien] *= 0.5
    if corteza:                                                # surcos como de corteza
        g = ruido(lz.W, lz.H, 2, seed + 3)
        surco = body & ~vien & (np.abs(np.sin(np.arange(lz.H)[:, None] * 1.3 + g * 9)) < 0.18)
        lz.rgb[surco] *= 0.65
        musgo = body & (ruido(lz.W, lz.H, 4, seed + 4) > 0.68) & ~vien
        lz.rgb[musgo] = lz.rgb[musgo] * 0.5 + np.array([60, 90, 40], np.float32) * 0.5
    return body


def cabeza(lz, x, y, s, dir_=1, boca=0.0, ojo_abierto=True):
    """Cabeza de serpiente (x, y = centro del cráneo). dir_=1 mira a la derecha. Devuelve la posición del ojo."""
    X = lambda dx, dy: (x + dir_ * dx * s, y + dy * s)
    sup = lz.mascara(lambda d: d.polygon([X(-9, -5), X(0, -7), X(10, -5), X(17, -2 - boca * 4), X(18, 1 - boca * 3),
                                          X(6, 2 - boca), X(-9, 5)], fill=255))
    lz.pinta(sup, ESCAMA, r=2.5 * s, relieve=4 * s, bump=0.6)
    if boca > 0:
        interior = lz.mascara(lambda d: d.polygon([X(4, 1), X(18, 1 - boca * 3), X(17, 4 + boca * 6), X(4, 4)], fill=255))
        lz.plano(interior, (110, 26, 26))
        inf = lz.mascara(lambda d: d.polygon([X(-6, 3), X(4, 3), X(16, 5 + boca * 7), X(15, 8 + boca * 7), X(-6, 7)], fill=255))
        lz.pinta(inf, VIENTRE, r=1.5 * s, relieve=2 * s, oclusion=False)
        for fx in (8, 14):                                     # colmillos
            col = lz.mascara(lambda d: d.polygon([X(fx, 0 - boca * (fx - 4) * 0.25), X(fx + 1.5, 0 - boca * (fx - 4) * 0.25),
                                                  X(fx + 0.7, 4 + boca)], fill=255))
            lz.plano(col, (236, 230, 210))
    else:
        inf = lz.mascara(lambda d: d.polygon([X(-6, 3), X(6, 2), X(17, 1), X(14, 5), X(-6, 6)], fill=255))
        lz.pinta(inf, VIENTRE, r=1.5 * s, relieve=2 * s, oclusion=False)
    ceja = lz.mascara(lambda d: d.polygon([X(-2, -6), X(8, -6), X(10, -3), X(0, -3)], fill=255))
    lz.pinta(ceja, ESCAMA_D, r=1 * s, relieve=3 * s, oclusion=False)
    ex, ey = X(5, -3)
    if ojo_abierto:
        o = lz.mascara(lambda d: d.ellipse([ex - 1.8 * s, ey - 1.3 * s, ex + 1.8 * s, ey + 1.3 * s], fill=255))
        lz.plano(o, (255, 214, 70))
        pu = lz.mascara(lambda d: d.line([(ex, ey - 1.2 * s), (ex, ey + 1.2 * s)], fill=255, width=max(1, int(s * 0.7))))
        lz.plano(pu, (20, 12, 8))
    else:
        o = lz.mascara(lambda d: d.line([(ex - 2 * s, ey), (ex + 2 * s, ey)], fill=255))
        lz.plano(o, (24, 20, 14))
    # cresta de plumas detrás de la cabeza
    for k in range(5):
        a = math.radians(200 + k * 18) if dir_ > 0 else math.radians(-20 - k * 18)
        px, py = X(-7, -4)
        q = lz.mascara(lambda d: d.polygon([(px, py), (px + math.cos(a) * 10 * s, py + math.sin(a) * 10 * s),
                                            (px + math.cos(a + 0.25) * 9 * s, py + math.sin(a + 0.25) * 9 * s)], fill=255))
        lz.pinta(q, PLUMA if k % 2 else PLUMA_L, r=1, relieve=1.5, oclusion=False)
    return (round(ex), round(ey))


def ala(lz, raiz, ang0, largo, abierta=1.0, dir_=1, n=9):
    """Ala de plumas verdes: abanico de plumas largas desde la raíz."""
    rx, ry = raiz
    for k in range(n):
        u = k / (n - 1)
        a = math.radians(ang0 + dir_ * (-70 * abierta) * u)
        Lk = largo * (1.0 - 0.35 * abs(u - 0.35))
        tip = (rx + math.cos(a) * Lk, ry + math.sin(a) * Lk)
        perp = (-math.sin(a), math.cos(a))
        w = largo * 0.09
        poly = [(rx, ry), (rx + math.cos(a) * Lk * 0.5 + perp[0] * w, ry + math.sin(a) * Lk * 0.5 + perp[1] * w),
                tip, (rx + math.cos(a) * Lk * 0.5 - perp[0] * w, ry + math.sin(a) * Lk * 0.5 - perp[1] * w)]
        m = lz.mascara(lambda d: d.polygon(poly, fill=255))
        lz.pinta(m, PLUMA if k % 2 else PLUMA_D, r=1.2, relieve=2.0, bump=0.3, spec=0.2, oclusion=k == 0)
        punta = lz.mascara(lambda d: d.polygon([tip, (tip[0] - math.cos(a) * Lk * 0.18 + perp[0] * w * 0.6,
                                                      tip[1] - math.sin(a) * Lk * 0.18 + perp[1] * w * 0.6),
                                                (tip[0] - math.cos(a) * Lk * 0.18 - perp[0] * w * 0.6,
                                                 tip[1] - math.sin(a) * Lk * 0.18 - perp[1] * w * 0.6)], fill=255))
        lz.rgb[punta & lz.a] = lz.rgb[punta & lz.a] * 0.4 + np.array(ORO, np.float32) * 0.35
    hueso = lz.mascara(lambda d: d.line([(rx, ry), (rx + math.cos(math.radians(ang0 - dir_ * 20)) * largo * 0.55,
                                                    ry + math.sin(math.radians(ang0 - dir_ * 20)) * largo * 0.55)], fill=255, width=3))
    lz.pinta(hueso, PLUMA_D, r=1, relieve=2, oclusion=False)


# ---------------------------------------------------------------------------------------------- serpiente
def tronco():
    lz = Lienzo(176, 34)
    pts = bezier([(4, 22), (50, 16), (110, 26), (150, 18)], 140)
    tot = camino(pts)
    n = len(tot)
    radios = [2 + 9 * min(1, i / (n * 0.35)) * (1 - 0.15 * max(0, (i - n * 0.8) / (n * 0.2))) for i in range(n)]
    cuerpo(lz, tot, radios, seed=2, corteza=True)
    for bx, by, ang in ((60, 10, -1.2), (100, 15, -1.9)):     # muñones de rama (escamas levantadas)
        m = lz.mascara(lambda d: d.line([(bx, by + 4), (bx + math.cos(ang) * 6, by + 4 + math.sin(ang) * 6)], fill=255, width=3))
        lz.pinta(m, ESCAMA_D, r=1, relieve=2)
    eye = cabeza(lz, 156, 19, 0.85, 1, boca=0.0, ojo_abierto=False)
    lz.guarda("tronco", (88, 33), notas=f"Tzukán dormida como tronco. Ojo (cerrado) en {eye}: pon ahí el actor 'ojos'.")
    return eye


def alzada():
    lz = Lienzo(150, 190)
    # enrollada en el suelo
    rollo = []
    for k in range(70):
        a = k / 70 * 2 * math.pi * 1.2
        rollo.append((86 + math.cos(a) * 40, 176 + math.sin(a) * 9))
    tot_r = camino(rollo)
    cuerpo(lz, tot_r, [9] * len(tot_r), seed=3)
    # alas detrás del cuerpo
    ala(lz, (90, 96), -95, 72, 1.0, dir_=1)
    ala(lz, (100, 98), -85, 66, 1.0, dir_=-1)
    pts = bezier([(120, 170), (140, 120), (60, 120), (80, 70), (100, 40), (70, 26)], 160)
    tot = camino(pts)
    n = len(tot)
    radios = [13 - 5 * (i / n) for i in range(n)]
    cuerpo(lz, tot, radios, seed=4)
    eye = cabeza(lz, 60, 26, 1.6, -1, boca=1.0)
    lz.guarda("alzada", (86, 186), brillos=[eye], notas="Tzukán alzándose, alas abiertas, boca abierta hacia la izquierda.")


def chaac_cuerpo(lz, x, y, s, montado=False):
    """Chaac pequeño de perfil (mirando a la derecha) para ir montado. x, y = cadera."""
    X = lambda dx, dy: (x + dx * s, y + dy * s)
    pierna = lz.mascara(lambda d: d.polygon([X(-2, 0), X(4, 0), X(8, 7), X(6, 12), X(2, 12), X(3, 7)], fill=255))
    lz.pinta(pierna, AZUL, r=1, relieve=2)
    tor = lz.mascara(lambda d: d.polygon([X(-4, -14), X(4, -14), X(5, 0), X(-4, 0)], fill=255))
    lz.pinta(tor, AZUL, r=1.5, relieve=3)
    tap = lz.mascara(lambda d: d.polygon([X(-5, -2), X(5, -2), X(6, 3), X(-5, 3)], fill=255))
    lz.pinta(tap, BLANCO, r=1, relieve=1.5, oclusion=False)
    cab = lz.mascara(lambda d: d.ellipse([*X(-4, -22), *X(5, -13)], fill=255))
    lz.pinta(cab, AZUL, r=1.5, relieve=3, oclusion=False)
    nariz = lz.mascara(lambda d: d.line([X(4, -18), X(8, -19), X(10, -16), X(8, -14)], fill=255, width=max(1, int(2 * s))))
    lz.pinta(nariz, AZUL_D, r=1, relieve=1.5, oclusion=False)
    orej = lz.mascara(lambda d: d.ellipse([*X(-2, -18), *X(1, -15)], fill=255))
    lz.plano(orej, JADE)
    for k in range(5):                                          # tocado de plumas
        a = math.radians(-150 + k * 22)
        px, py = X(0, -21)
        q = lz.mascara(lambda d: d.polygon([(px, py), (px + math.cos(a) * 11 * s, py + math.sin(a) * 11 * s),
                                            (px + math.cos(a + 0.2) * 10 * s, py + math.sin(a + 0.2) * 10 * s)], fill=255))
        lz.pinta(q, PLUMA if k % 2 else PLUMA_L, r=1, relieve=1, oclusion=False)
    ojo = lz.mascara(lambda d: d.point(X(3, -18), fill=255))
    lz.plano(ojo, (16, 12, 10))
    brazo = lz.mascara(lambda d: d.line([X(1, -12), X(7, -8), X(11, -10)], fill=255, width=max(1, int(2 * s))))
    lz.pinta(brazo, AZUL, r=1, relieve=1.5, oclusion=False)
    # hacha (rayo) levantada
    mango = lz.mascara(lambda d: d.line([X(-2, -12), X(-6, -26)], fill=255, width=max(1, int(1.5 * s))))
    lz.plano(mango, (96, 70, 40))
    hoja = lz.mascara(lambda d: d.polygon([X(-6, -26), X(-12, -30), X(-11, -23)], fill=255))
    lz.pinta(hoja, (176, 178, 186), r=1, relieve=1.5, spec=0.9, oclusion=False)


def vuelo(chaac=True):
    lz = Lienzo(240, 110)
    pts = [(10 + 200 * u, 72 + 14 * math.sin(u * 2 * math.pi * 1.3 + 0.8) * (0.4 + 0.6 * u)) for u in np.linspace(0, 1, 120)]
    tot = camino(pts)
    n = len(tot)
    radios = [1.5 + 9 * min(1, (i / n) / 0.55) for i in range(n)]
    ala(lz, (150, 66), -160, 74, 1.0, dir_=-1)
    cuerpo(lz, tot, radios, seed=5)
    ala(lz, (160, 70), -130, 66, 0.9, dir_=-1)
    eye = cabeza(lz, 216, 72, 1.15, 1, boca=0.3)
    if chaac:
        chaac_cuerpo(lz, 184, 60, 1.25, montado=True)
        lz.guarda("vuelo", (120, 108), brillos=[eye], notas="Tzukán volando a la derecha con Chaac montado. Ancla abajo al centro.")
    else:
        lz.guarda("vuelo_sola", (120, 108), brillos=[eye], notas="Tzukán volando a la derecha, sin jinete.")


# ---------------------------------------------------------------------------------------------- Chaac
def chaac_espalda():
    lz = Lienzo(48, 80)
    fx, fy = 22, 79
    X = lambda dx, dy: (fx + dx, fy + dy)
    for s, c in ((-1, AZUL_D), (1, AZUL)):
        pierna = lz.mascara(lambda d: d.polygon([X(s * 1, -26), X(s * 7, -26), X(s * 6, 0), X(s * 2, 0)], fill=255))
        lz.pinta(pierna, c, r=1.5, relieve=3)
        sand = lz.mascara(lambda d: d.rectangle([*X(min(s * 1, s * 7), -2), *X(max(s * 1, s * 7), 0)], fill=255))
        lz.plano(sand, (80, 56, 34))
    tor = lz.mascara(lambda d: d.polygon([X(-9, -50), X(9, -50), X(7, -25), X(-7, -25)], fill=255))
    lz.pinta(tor, AZUL, r=3, relieve=5)
    espalda = lz.mascara(lambda d: d.line([X(0, -48), X(0, -28)], fill=255))
    lz.rgb[espalda] *= 0.75
    tap = lz.mascara(lambda d: d.polygon([X(-8, -28), X(8, -28), X(7, -18), X(-7, -18)], fill=255))
    lz.pinta(tap, BLANCO, r=1.5, relieve=2, oclusion=False)
    cola = lz.mascara(lambda d: d.polygon([X(-2, -20), X(2, -20), X(1, -10), X(-1, -10)], fill=255))
    lz.pinta(cola, JADE, r=1, relieve=1.5, oclusion=False)
    for s in (-1, 1):
        brazo = lz.mascara(lambda d: d.polygon([X(s * 9, -49), X(s * 12, -47), X(s * 12, -30), X(s * 9, -30)], fill=255))
        lz.pinta(brazo, AZUL, r=1.5, relieve=3)
        pul = lz.mascara(lambda d: d.rectangle([*X(min(s * 9, s * 12), -36), *X(max(s * 9, s * 12), -34)], fill=255))
        lz.plano(pul, JADE)
    cab = lz.mascara(lambda d: d.ellipse([*X(-6, -62), *X(6, -49)], fill=255))
    lz.pinta(cab, AZUL_D, r=2, relieve=4)
    for s in (-1, 1):
        o = lz.mascara(lambda d: d.ellipse([*X(s * 6 - 2, -58), *X(s * 6 + 2, -54)], fill=255))
        lz.pinta(o, JADE, r=1, relieve=1.5, oclusion=False)
    for k in range(9):                                           # tocado de plumas en abanico
        a = math.radians(-160 + k * 17.5)
        px, py = X(0, -60)
        Lk = 16 + 4 * math.sin(k / 8 * math.pi)
        q = lz.mascara(lambda d: d.polygon([(px, py), (px + math.cos(a - 0.08) * Lk, py + math.sin(a - 0.08) * Lk),
                                            (px + math.cos(a + 0.08) * Lk, py + math.sin(a + 0.08) * Lk)], fill=255))
        lz.pinta(q, PLUMA if k % 2 else PLUMA_L, r=1, relieve=1.5, oclusion=False)
    banda = lz.mascara(lambda d: d.rectangle([*X(-6, -60), *X(6, -58)], fill=255))
    lz.plano(banda, ORO)
    # hacha colgando en la mano derecha
    mango = lz.mascara(lambda d: d.line([X(12, -32), X(16, -14)], fill=255, width=2))
    lz.plano(mango, (96, 70, 40))
    hoja = lz.mascara(lambda d: d.polygon([X(16, -14), X(21, -10), X(19, -17)], fill=255))
    lz.pinta(hoja, (176, 178, 186), r=1, relieve=1.5, spec=0.9, oclusion=False)
    lz.guarda("chaac_espalda", (fx, fy), notas="Chaac caminando de espaldas, hacha en la mano derecha.")


def chaac_sentado():
    lz = Lienzo(56, 66)
    hx, hy = 22, 50                                              # cadera
    X = lambda dx, dy: (hx + dx, hy + dy)
    muslo = lz.mascara(lambda d: d.polygon([X(-4, -4), X(14, -4), X(15, 3), X(-4, 3)], fill=255))
    lz.pinta(muslo, AZUL, r=2, relieve=3)
    pierna = lz.mascara(lambda d: d.polygon([X(11, -2), X(16, -2), X(17, 15), X(12, 15)], fill=255))
    lz.pinta(pierna, AZUL_D, r=1.5, relieve=3)
    sand = lz.mascara(lambda d: d.rectangle([*X(11, 13), *X(20, 15)], fill=255))
    lz.plano(sand, (80, 56, 34))
    tor = lz.mascara(lambda d: d.polygon([X(-6, -26), X(6, -26), X(7, 0), X(-6, 0)], fill=255))
    lz.pinta(tor, AZUL, r=3, relieve=5)
    tap = lz.mascara(lambda d: d.polygon([X(-6, -3), X(8, -3), X(12, 3), X(-6, 3)], fill=255))
    lz.pinta(tap, BLANCO, r=1.5, relieve=2, oclusion=False)
    collar = lz.mascara(lambda d: d.chord([*X(-6, -30), *X(7, -20)], 0, 180, fill=255))
    lz.pinta(collar, JADE, r=1, relieve=2, oclusion=False)
    cab = lz.mascara(lambda d: d.ellipse([*X(-6, -40), *X(7, -26)], fill=255))
    lz.pinta(cab, AZUL, r=2, relieve=4, oclusion=False)
    nariz = lz.mascara(lambda d: d.line([X(6, -35), X(11, -36), X(13, -32), X(11, -29), X(9, -30)], fill=255, width=2))
    lz.pinta(nariz, AZUL_D, r=1, relieve=2, oclusion=False)
    colm = lz.mascara(lambda d: d.polygon([X(5, -29), X(7, -29), X(6, -25)], fill=255))
    lz.plano(colm, (236, 230, 210))
    orej = lz.mascara(lambda d: d.ellipse([*X(-3, -35), *X(2, -30)], fill=255))
    lz.pinta(orej, JADE, r=1, relieve=1.5, oclusion=False)
    ojo = lz.mascara(lambda d: d.rectangle([*X(3, -35), *X(4, -34)], fill=255))
    lz.plano(ojo, (16, 12, 10))
    for k in range(7):
        a = math.radians(-170 + k * 20)
        px, py = X(-1, -39)
        q = lz.mascara(lambda d: d.polygon([(px, py), (px + math.cos(a - 0.1) * 15, py + math.sin(a - 0.1) * 15),
                                            (px + math.cos(a + 0.1) * 15, py + math.sin(a + 0.1) * 15)], fill=255))
        lz.pinta(q, PLUMA if k % 2 else PLUMA_L, r=1, relieve=1.5, oclusion=False)
    banda = lz.mascara(lambda d: d.rectangle([*X(-6, -40), *X(6, -38)], fill=255))
    lz.plano(banda, ORO)
    brazo = lz.mascara(lambda d: d.polygon([X(2, -24), X(6, -24), X(12, -10), X(9, -8)], fill=255))
    lz.pinta(brazo, AZUL, r=1.5, relieve=3, oclusion=False)
    mango = lz.mascara(lambda d: d.line([X(11, -9), X(16, -22)], fill=255, width=2))
    lz.plano(mango, (96, 70, 40))
    hoja = lz.mascara(lambda d: d.polygon([X(16, -22), X(22, -25), X(20, -18)], fill=255))
    lz.pinta(hoja, (176, 178, 186), r=1, relieve=1.5, spec=0.9, oclusion=False)
    lz.guarda("chaac_sentado", (hx, hy + 3), notas="Chaac sentado de perfil mirando a la derecha. Ancla = asiento (pon y sobre el tronco).")


def jaguar():
    """Jaguar grande de perfil mirando a la derecha: la montura de Chaac en esta versión."""
    lz = Lienzo(96, 60)
    JAG, JAG_D, CREMA, NEGRO = (206, 146, 60), (150, 100, 40), (226, 206, 160), (34, 24, 16)
    by = 59
    for x in (20, 60):                                            # patas de atrás (sombra)
        m = lz.mascara(lambda d: d.polygon([(x, 36), (x + 8, 36), (x + 7, by), (x + 1, by)], fill=255))
        lz.pinta(m, JAG_D, r=1.5, relieve=3)
    cola = lz.mascara(lambda d: d.line([(14, 30), (6, 22), (4, 12), (8, 6)], fill=255, width=4))
    lz.pinta(cola, JAG, r=1.5, relieve=2)
    cuerpo_m = lz.mascara(lambda d: (d.ellipse([8, 22, 76, 44], fill=255), d.ellipse([54, 18, 80, 42], fill=255)))
    lz.pinta(cuerpo_m, JAG, r=5, relieve=7)
    vien = lz.mascara(lambda d: d.ellipse([18, 37, 70, 47], fill=255)) & cuerpo_m
    lz.pinta(vien, CREMA, r=2, relieve=2, oclusion=False)
    for x, dx in ((26, -3), (66, 3)):                             # patas de adelante (en marcha)
        m = lz.mascara(lambda d: d.polygon([(x, 36), (x + 9, 36), (x + 8 + dx, by), (x + dx, by)], fill=255))
        lz.pinta(m, JAG, r=1.5, relieve=3)
        g = lz.mascara(lambda d: d.rectangle([x - 1 + dx, by - 2, x + 9 + dx, by], fill=255))
        lz.pinta(g, CREMA, r=1, relieve=1, oclusion=False)
    cab = lz.mascara(lambda d: (d.ellipse([72, 18, 90, 34], fill=255), d.polygon([(82, 22), (95, 27), (94, 33), (82, 33)], fill=255)))
    lz.pinta(cab, JAG, r=3, relieve=5)
    hocico = lz.mascara(lambda d: d.ellipse([86, 27, 95, 34], fill=255))
    lz.pinta(hocico, CREMA, r=1.5, relieve=2, oclusion=False)
    nariz = lz.mascara(lambda d: d.polygon([(92, 26), (95, 27), (94, 29)], fill=255))
    lz.plano(nariz, (60, 30, 26))
    for ex in (75, 79):                                           # orejas (echadas hacia atrás)
        o = lz.mascara(lambda d: d.ellipse([ex - 2, 16, ex + 2, 21], fill=255))
        lz.pinta(o, JAG_D, r=1, relieve=2, oclusion=False)
    rng = np.random.default_rng(11)
    zona = cuerpo_m & ~vien
    for _ in range(46):                                           # rosetas
        x, y = rng.uniform(12, 78), rng.uniform(18, 42)
        r = rng.uniform(1.6, 2.6)
        ros = lz.mascara(lambda d: d.ellipse([x - r, y - r, x + r, y + r], outline=255))
        lz.rgb[ros & zona] = NEGRO
        c = lz.mascara(lambda d: d.point((x, y), fill=255))
        lz.rgb[c & zona] *= 0.75
    for _ in range(14):                                           # manchas de cabeza y patas
        x, y = rng.uniform(73, 88), rng.uniform(20, 30)
        m = lz.mascara(lambda d: d.point((x, y), fill=255))
        lz.rgb[m & cab & ~hocico] = NEGRO
    for k in range(4):
        m = lz.mascara(lambda d: d.line([(4 + k, 12 + k * 4), (8 + k, 12 + k * 4)], fill=255))
        lz.rgb[m & cola] = NEGRO
    ojo = (84, 23)
    o = lz.mascara(lambda d: d.ellipse([ojo[0] - 1.5, ojo[1] - 1, ojo[0] + 1.5, ojo[1] + 1], fill=255))
    lz.plano(o, (240, 200, 70))
    lz.guarda("jaguar", (46, by), brillos=[ojo], notas="Jaguar grande de perfil mirando a la derecha (montura de Chaac). Ojo brilla.")

if __name__ == "__main__":
    tronco()
    alzada()
    vuelo()
    vuelo(chaac=False)
    chaac_espalda()
    chaac_sentado()
    jaguar()
