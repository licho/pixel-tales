"""Salón del consejo en un templo: plataforma escalonada con dos tronos, mascarón de muerte,
tzompantli (estantes de cráneos), braseros con copal y columnas en primer plano.

Parámetros:
  tronos       bool (default true)
  tzompantli   bool (default true)
  braseros     bool (default true)
  semilla      int

Puntos útiles (relativos a W x H; pies de los personajes):
  trono izquierdo: (0.40 W, 0.535 H)     trono derecho: (0.60 W, 0.535 H)
  piso frente a la plataforma: x 0.15-0.85 W, y 0.74-0.95 H (personajes de pie ~0.18 H)
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.pintura import antorcha, brasero, calavera, niebla_profundidad, piedra_bloques, roca
from pixel_tales.scene import Scene


class Escena(Scene):
    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        self.sky[:] = (8, 6, 8)

        wall = piedra_bloques(self, (74, 64, 58), 16, 8, self.seed)
        alb = wall.copy()
        self.mid_a[:] = True

        img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        dark, carve, light = (30, 24, 24), (52, 44, 40), (112, 100, 88)

        # friso con greca escalonada
        y0, y1 = 0.07 * H, 0.12 * H
        d.rectangle([0, y0, W, y1], fill=carve)
        step = (y1 - y0) / 2
        x = 0
        while x < W:
            d.line([(x, y1 - 1), (x, y0 + step), (x + step, y0 + step), (x + step, y0 + 1),
                    (x + 2 * step, y0 + 1), (x + 2 * step, y1 - 1)], fill=light, width=1)
            x += 3 * step

        # mascarón de la muerte sobre los tronos
        cx, cy, r = 0.5 * W, 0.26 * H, 0.15 * W
        d.ellipse([cx - r, cy - r * 0.95, cx + r, cy + r * 0.8], fill=(96, 86, 76), outline=dark)
        d.rectangle([cx - r * 0.6, cy + r * 0.5, cx + r * 0.6, cy + r * 1.05], fill=(96, 86, 76), outline=dark)
        for ex in (-0.42, 0.42):
            d.ellipse([cx + ex * r - r * 0.26, cy - r * 0.2, cx + ex * r + r * 0.26, cy + r * 0.3], fill=dark)
        d.polygon([(cx - r * 0.1, cy + r * 0.45), (cx + r * 0.1, cy + r * 0.45), (cx, cy + r * 0.25)], fill=dark)
        for k in range(7):
            tx = cx - r * 0.5 + k * r / 6
            d.line([(tx, cy + r * 0.62), (tx, cy + r * 0.98)], fill=dark)
        d.line([(cx - r * 0.6, cy + r * 0.8), (cx + r * 0.6, cy + r * 0.8)], fill=dark)

        # plataforma de tres niveles con escalinata central
        tiers = [(0.62, 0.70, 0.84), (0.555, 0.62, 0.66), (0.50, 0.555, 0.50)]
        for top, bot, wd in tiers:
            d.rectangle([W * (0.5 - wd / 2), H * top, W * (0.5 + wd / 2), H * bot], fill=(84, 74, 66))
            d.line([(W * (0.5 - wd / 2), H * top), (W * (0.5 + wd / 2), H * top)], fill=light)
            d.line([(W * (0.5 - wd / 2), H * bot), (W * (0.5 + wd / 2), H * bot)], fill=dark)
        sw = 0.16 * W
        for k in range(10):
            yk = 0.50 * H + k * 0.02 * H
            d.rectangle([0.5 * W - sw / 2, yk, 0.5 * W + sw / 2, yk + 0.02 * H], fill=(96, 86, 76))
            d.line([(0.5 * W - sw / 2, yk), (0.5 * W + sw / 2, yk)], fill=light)

        # tronos
        if p.get("tronos", True):
            for tx in (0.40, 0.60):
                x0 = tx * W
                d.rectangle([x0 - 0.065 * W, 0.405 * H, x0 + 0.065 * W, 0.50 * H], fill=(60, 50, 46), outline=dark)
                d.rectangle([x0 - 0.05 * W, 0.42 * H, x0 + 0.05 * W, 0.44 * H], fill=(124, 28, 22))
                d.rectangle([x0 - 0.075 * W, 0.49 * H, x0 + 0.075 * W, 0.505 * H], fill=(96, 86, 76), outline=dark)
                calavera(d, x0, 0.395 * H, 1.2)

        # piso de losas en perspectiva
        vx, vy = 0.5 * W, 0.45 * H
        floor_top = 0.70 * H
        d.rectangle([0, floor_top, W, H], fill=(64, 56, 50))
        for k in range(-8, 9):
            d.line([(vx + k * 0.04 * W, floor_top), (vx + k * 0.30 * W, H)], fill=(40, 34, 32))
        z = 1.0
        while True:
            y = vy + (H - vy) / z
            if y < floor_top:
                break
            d.line([(0, y), (W, y)], fill=(40, 34, 32))
            z += 0.25

        # tzompantli: estantes de cráneos a los lados
        if p.get("tzompantli", True):
            for x0, x1 in ((0.13 * W, 0.27 * W), (0.73 * W, 0.87 * W)):
                d.line([(x0, 0.36 * H), (x0, 0.70 * H)], fill=(58, 40, 28), width=2)
                d.line([(x1, 0.36 * H), (x1, 0.70 * H)], fill=(58, 40, 28), width=2)
                for row in range(6):
                    yr = 0.39 * H + row * 0.05 * H
                    d.line([(x0, yr), (x1, yr)], fill=(70, 50, 34))
                    n = 4
                    for c in range(n):
                        calavera(d, x0 + (c + 0.5) * (x1 - x0) / n, yr + 0.012 * H, 1.1)

        alb = np.asarray(img, np.float32).copy()
        niebla_profundidad(self, alb, 0.5 * W, 0.30 * H, 0.9, 0.55)
        self.mid_alb = alb

        if p.get("braseros", True):
            brasero(self, 0.22 * W, 0.80 * H, 1.3)
            brasero(self, 0.78 * W, 0.80 * H, 1.3)
        antorcha(self, 0.30 * W, 0.40 * H, 0.9, radio=34, intensidad=0.8)
        antorcha(self, 0.70 * W, 0.40 * H, 0.9, radio=34, intensidad=0.8)

        # columnas en primer plano
        def cols(dr):
            dr.rectangle([0, 0, 0.09 * W, H], fill=255)
            dr.rectangle([0.91 * W, 0, W, H], fill=255)
        self.fg_a = self.mask(cols)
        fg = roca(self, (70, 58, 52), self.seed + 4, 0.4, grietas=False)
        fg[(yy.astype(int) % 40) < 3] *= 0.5
        self.fg_alb = fg
