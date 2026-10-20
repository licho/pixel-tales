"""Efectos animados: lluvia, ceniza/brasas, flamas, humo."""
import math

import numpy as np

from .core import grid


class Rain:
    """Lluvia pixelada en espacio de pantalla."""

    def __init__(self, vw, vh, cantidad=180, seed=1):
        rng = np.random.default_rng(seed)
        self.vw, self.vh = vw, vh
        self.drops = rng.random((int(cantidad * vw * vh / (384 * 216)), 4)) * [vw, vh, 1, 1]

    def masks(self, t, fi):
        vw, vh = self.vw, self.vh
        streak = np.zeros((vh, vw), bool)
        for rx, ry, sp, ln in self.drops:
            y = (ry + t * (150 + 70 * sp)) % (vh + 10) - 5
            x = (rx - (y - ry) * 0.25) % vw
            for k in range(3 + int(ln * 3)):
                yy, xx = int(y + k), int(x + k * 0.25)
                if 0 <= yy < vh and 0 <= xx < vw:
                    streak[yy, xx] = True
        splash = np.zeros((vh, vw), bool)
        rng = np.random.default_rng(fi)
        splash[rng.integers(int(vh * 0.7), vh, 18), rng.integers(0, vw, 18)] = True
        return streak, splash


class Ash:
    """Ceniza y brasas flotando (espacio de pantalla). Devuelve lista de (mask, color_idx)."""

    def __init__(self, vw, vh, cantidad=70, brasas=0.25, seed=3):
        rng = np.random.default_rng(seed)
        n = int(cantidad * vw * vh / (216 * 384))
        self.vw, self.vh = vw, vh
        self.p = np.column_stack([rng.random(n) * vw, rng.random(n) * vh, rng.random(n), rng.random(n) < brasas])

    def masks(self, t):
        ash = np.zeros((self.vh, self.vw), bool)
        ember = np.zeros_like(ash)
        for x, y, r, is_ember in self.p:
            yy = (y - t * (4 + 10 * r) * (1 if is_ember else -0.6)) % self.vh
            xx = (x + math.sin(t * (0.6 + r) + r * 9) * 6 + t * 3 * r) % self.vw
            if is_ember:
                if math.sin(t * 5 + r * 20) > -0.3:
                    ember[int(yy), int(xx)] = True
            else:
                ash[int(yy), int(xx)] = True
        return ash, ember


FLAME = np.array([(255, 232, 170), (246, 190, 96), (222, 140, 48), (170, 92, 32)], np.uint8)


def draw_flames(rgb, alpha, fire, k, fi):
    """Dibuja flamas sobre la capa ya cuantizada (colores fijos de fuego)."""
    rng = np.random.default_rng(fi + fire["x0"] * 7)
    x0, x1, y = fire["x0"], fire["x1"], fire["y"]
    w = max(x1 - x0, 1)
    tam = fire.get("tam", 1.0)
    for x in range(x0, x1):
        if not 0 <= x < rgb.shape[1]:
            continue
        hgt = int((3 + 9 * math.sin((x - x0 + 0.5) / w * math.pi)) * k * tam + rng.integers(0, 1 + int(4 * tam)))
        for j in range(hgt):
            yy = y - j
            if yy < 0 or yy >= rgb.shape[0]:
                break
            f = j / max(hgt, 1)
            rgb[yy, x] = FLAME[0 if f < 0.25 else 1 if f < 0.5 else 2 if f < 0.75 else 3]
            alpha[yy, x] = True


class Smoke:
    """Humo que sube desde una fuente; se mezcla en el color antes de cuantizar."""

    def __init__(self, x, y, seed=0, color=(70, 84, 84), escala=1.0):
        rng = np.random.default_rng(seed)
        self.x, self.y, self.color, self.k = x, y, np.array(color, np.float32), escala
        self.parts = [(rng.uniform(0, 3.0), rng.uniform(-3, 3), rng.uniform(4, 7)) for _ in range(20)]

    def apply(self, col, t):
        h, w = col.shape[:2]
        xx, yy = grid(w, h)
        k = self.k
        for t0, dx, r in self.parts:
            age = (t + t0) % 3.0
            sx = self.x + (dx + age * 6 + math.sin(age * 3 + dx) * 2) * k
            sy = self.y - age * 26 * k
            rr = (r + age * 4) * k
            ya, yb = max(0, int(sy - 3 * rr)), min(h, int(sy + 3 * rr) + 1)
            xa, xb = max(0, int(sx - 3 * rr)), min(w, int(sx + 3 * rr) + 1)
            if ya >= yb or xa >= xb:
                continue
            m = np.exp(-((xx[ya:yb, xa:xb] - sx) ** 2 + (yy[ya:yb, xa:xb] - sy) ** 2) / (2 * rr ** 2))
            m = (m * (1 - age / 3.0) * 0.32)[..., None]
            col[ya:yb, xa:xb] = col[ya:yb, xa:xb] * (1 - m) + self.color * m
