"""Túnel de cueva con escalinata que desciende hacia un resplandor.

Parámetros:
  resplandor  'rojo' | 'jade' | 'ocre' | [r, g, b]   color de la luz del fondo (default rojo)
  antorchas   bool (default true)
  escalera    bool (default true)
  calaveras   bool (default true)
  semilla     int

Puntos útiles (relativos a W x H):
  escalones cercanos: x 0.35-0.65 W, y 0.85-0.97 H (personajes de ~0.2 H)
  fondo del túnel: (0.5 W, 0.40 H)
  zona para murciélagos: [0.1 W, 0.05 H, 0.9 W, 0.45 H]
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, vnoise
from pixel_tales.pintura import antorcha, calavera, estalactitas, niebla_profundidad, roca
from pixel_tales.scene import Scene

COLORES = {"rojo": (196, 44, 30), "jade": (60, 150, 96), "ocre": (210, 130, 50)}


class Escena(Scene):
    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        glow = p.get("resplandor", "rojo")
        glow = np.array(COLORES.get(glow, glow) if isinstance(glow, str) else glow, np.float32)
        vx, vy = 0.5 * W, 0.40 * H

        # fondo: oscuridad con resplandor
        d = np.hypot((xx - vx) / W, (yy - vy) / H)
        self.sky = np.array([6, 4, 6], np.float32) + glow * (np.exp(-d / 0.09) * 0.85)[..., None]

        # boca del túnel (irregular) -> se ve el fondo
        n = vnoise(W, H, 6, 40 + self.seed)
        ox, oy = 0.105 * W, 0.075 * H
        opening = (((xx - vx) / ox) ** 2 + ((yy - vy + 0.01 * H) / oy) ** 2 < 1 + 0.5 * (n - 0.5)) & (yy < vy + 0.06 * H)

        alb = roca(self, (62, 48, 46), self.seed)
        fx0, fx1, fy1 = vx - 0.10 * W, vx + 0.10 * W, vy + 0.06 * H
        nx0, nx1 = -0.02 * W, 1.02 * W
        u = np.clip((yy - fy1) / (H - fy1), 0, 1)
        lx, rx = fx0 + (nx0 - fx0) * u, fx1 + (nx1 - fx1) * u
        floor = (yy >= fy1) & (xx >= lx) & (xx <= rx)

        # techo más oscuro, paredes medias
        alb[yy < vy - 0.08 * H] *= 0.7

        if p.get("escalera", True):
            stone = np.array([92, 82, 72], np.float32) * (0.85 + 0.3 * vnoise(W, H, 3, 7 + self.seed))[..., None]
            alb[floor] = stone[floor]
            z = 1.0
            while True:
                y = vy + (H - vy) / z
                if y < fy1 + 1:
                    break
                band = floor & (yy >= y - max(1.0, 3.0 / z)) & (yy < y)
                alb[band] *= 0.45                      # sombra del borde del escalón
                edge = floor & (yy >= y) & (yy < y + max(1.0, 1.5 / z))
                alb[edge] = alb[edge] * 1.25 + 8      # filo iluminado
                z += 0.38
            side = floor & ((xx < lx + 0.04 * W * (0.3 + u)) | (xx > rx - 0.04 * W * (0.3 + u)))
            alb[side] *= 0.7

        niebla_profundidad(self, alb, vx, vy, 0.33, 0.04)
        self.mid_alb = alb
        self.mid_a = ~opening

        if p.get("calaveras", True):
            img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
            dr = ImageDraw.Draw(img)
            rng = np.random.default_rng(5 + self.seed)
            for _ in range(7):
                yv = rng.uniform(0.62, 0.95)
                uu = (yv * H - fy1) / (H - fy1)
                side = rng.choice([-1, 1])
                xe = (fx0 + (nx0 - fx0) * uu) if side < 0 else (fx1 + (nx1 - fx1) * uu)
                x = xe - side * rng.uniform(0.04, 0.10) * W * (0.4 + uu)
                calavera(dr, x, yv * H, max(0.6, 1.6 * uu))
            self.mid_alb = np.asarray(img, np.float32).copy()

        self.lights.append(Light("resplandor", self.point(vx, vy + 0.03 * H, 0.13 * W, 0.9), tuple(glow / 150)))
        if p.get("antorchas", True):
            antorcha(self, 0.15 * W, 0.47 * H, 1.4, radio=40)
            antorcha(self, 0.85 * W, 0.47 * H, 1.4, radio=40)
            antorcha(self, 0.38 * W, 0.405 * H, 0.6, radio=30, intensidad=0.8)
            antorcha(self, 0.62 * W, 0.405 * H, 0.6, radio=30, intensidad=0.8)

        # primer plano: estalactitas arriba y rocas abajo en las esquinas
        def fg(dr):
            dr.rectangle([0, 0, W, 0.02 * H], fill=255)
            estalactitas(self, dr, 0.02 * H, 0, W, 0.12 * H, self.seed)
            dr.polygon([(0, H), (0, 0.80 * H), (0.08 * W, 0.86 * H), (0.13 * W, 0.95 * H), (0.16 * W, H)], fill=255)
            dr.polygon([(W, H), (W, 0.78 * H), (0.93 * W, 0.84 * H), (0.88 * W, 0.94 * H), (0.84 * W, H)], fill=255)
        self.fg_a = self.mask(fg)
        self.fg_alb[:] = (34, 26, 26)
