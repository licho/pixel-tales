"""Efectos animados: lluvia, flamas, humo."""
import math

import numpy as np

from .core import VW, VH, grid


class Rain:
    """Lluvia pixelada en espacio de pantalla."""

    def __init__(self, cantidad=180, seed=1):
        rng = np.random.default_rng(seed)
        self.drops = rng.random((cantidad, 4)) * [VW, VH, 1, 1]

    def masks(self, t, fi):
        streak = np.zeros((VH, VW), bool)
        for rx, ry, sp, ln in self.drops:
            y = (ry + t * (150 + 70 * sp)) % (VH + 10) - 5
            x = (rx - (y - ry) * 0.25) % VW
            for k in range(3 + int(ln * 3)):
                yy, xx = int(y + k), int(x + k * 0.25)
                if 0 <= yy < VH and 0 <= xx < VW:
                    streak[yy, xx] = True
        splash = np.zeros((VH, VW), bool)
        rng = np.random.default_rng(fi)
        splash[rng.integers(150, VH, 18), rng.integers(0, VW, 18)] = True
        return streak, splash


FLAME = np.array([(255, 232, 170), (246, 190, 96), (222, 140, 48), (170, 92, 32)], np.uint8)


def draw_flames(rgb, alpha, fire, k, fi):
    """Dibuja flamas sobre la capa ya cuantizada (colores fijos de fuego)."""
    rng = np.random.default_rng(fi)
    x0, x1, y = fire["x0"], fire["x1"], fire["y"]
    w = x1 - x0
    for x in range(x0, x1):
        hgt = int((5 + 9 * math.sin((x - x0) / w * math.pi)) * k * fire.get("tam", 1.0) + rng.integers(0, 5))
        for j in range(hgt):
            yy = y - j
            if yy < 0:
                break
            f = j / max(hgt, 1)
            rgb[yy, x] = FLAME[0 if f < 0.25 else 1 if f < 0.5 else 2 if f < 0.75 else 3]
            alpha[yy, x] = True


class Smoke:
    """Humo que sube desde una fuente; se mezcla en el color antes de cuantizar."""

    def __init__(self, x, y, seed=0, color=(70, 84, 84)):
        rng = np.random.default_rng(seed)
        self.x, self.y, self.color = x, y, np.array(color, np.float32)
        self.parts = [(rng.uniform(0, 3.0), rng.uniform(-3, 3), rng.uniform(4, 7)) for _ in range(26)]

    def apply(self, col, t):
        xx, yy = grid()
        h, w = col.shape[:2]
        for t0, dx, r in self.parts:
            age = (t + t0) % 3.0
            sx = self.x + dx + age * 6 + math.sin(age * 3 + dx) * 2
            sy = self.y - age * 26
            rr = r + age * 4
            ya, yb = max(0, int(sy - 3 * rr)), min(h, int(sy + 3 * rr) + 1)
            xa, xb = max(0, int(sx - 3 * rr)), min(w, int(sx + 3 * rr) + 1)
            if ya >= yb or xa >= xb:
                continue
            m = np.exp(-((xx[ya:yb, xa:xb] - sx) ** 2 + (yy[ya:yb, xa:xb] - sy) ** 2) / (2 * rr ** 2))
            m = (m * (1 - age / 3.0) * 0.32)[..., None]
            col[ya:yb, xa:xb] = col[ya:yb, xa:xb] * (1 - m) + self.color * m
