"""Cancha del juego de pelota de noche, vista a lo largo: talud, muros con aros de piedra,
antorchas y templos al fondo.

Parámetros:
  aros       bool (default true)
  antorchas  bool (default true)
  luna       bool (default true)
  semilla    int

Puntos útiles (relativos a W x H; pies):
  centro de la cancha, cerca: (0.5 W, 0.94 H) (personajes ~0.28 H)
  dos personajes lado a lado: (0.40 W, 0.95 H) y (0.60 W, 0.95 H)
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light
from pixel_tales.pintura import antorcha, estrellas, niebla_profundidad, piedra_bloques
from pixel_tales.scene import Scene

Z_FIN = 7.0   # profundidad donde termina la cancha


class Escena(Scene):
    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        vx, vy = 0.5 * W, 0.52 * H

        def P(x, y, z):
            """Punto de la sección cercana (x, y relativos) llevado a la profundidad z."""
            return (vx + (x * W - vx) / z, vy + (y * H - vy) / z)

        # cielo
        t = np.clip(yy / (0.56 * H), 0, 1)[..., None]
        sky = np.array([6, 5, 9], np.float32) * (1 - t) + np.array([64, 20, 22], np.float32) * t
        estrellas(self, sky, 0.006, 0.45, self.seed)
        if p.get("luna", True):
            d = np.hypot(xx - 0.74 * W, yy - 0.12 * H)
            sky += (np.exp(-d / 22) * 50)[..., None] * np.array([0.9, 0.85, 0.7])
            sky[d < 0.06 * W] = (206, 196, 164)
            sky[(d < 0.06 * W) & (np.hypot(xx - 0.72 * W, yy - 0.11 * H) < 0.014 * W)] = (176, 166, 136)
        self.sky = sky

        # templos al fondo
        far = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(far)
        base = vy + 0.01 * H
        for cx, w, h in ((0.5, 0.26, 0.17), (0.16, 0.20, 0.10), (0.84, 0.22, 0.12)):
            for k in range(5):
                ww = w * (1 - k * 0.16)
                fd.rectangle([W * (cx - ww / 2), base - H * h * (k + 1) / 5, W * (cx + ww / 2), base], fill=255)
            fd.rectangle([W * (cx - w * 0.12), base - H * h * 1.3, W * (cx + w * 0.12), base - H * h], fill=255)
        self.far_a = np.asarray(far) > 127
        self.far[:] = (22, 15, 17)
        for cx, h in ((0.5, 0.17), (0.16, 0.10), (0.84, 0.12)):
            self.far[int(base - H * h * 1.15), int(W * cx)] = (236, 150, 60)

        # sección cercana (relativa): piso 0.28-0.72, talud hasta 0.08 / 0.86 H, muro hasta 0.60 H
        floor_l, floor_r = 0.28, 0.72
        tal_x_l, tal_x_r, tal_y = 0.08, 0.92, 0.86
        wall_y = 0.60

        stone = piedra_bloques(self, (96, 86, 72), 12, 6, self.seed)
        img = Image.fromarray(np.clip(stone, 0, 255).astype(np.uint8))
        mk = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mk)

        def quad(pts, fill, shade=None):
            dm.polygon(pts, fill=255)
            if fill is not None:
                d.polygon(pts, fill=fill)

        zf = Z_FIN
        # fondo de la cancha (muro final bajo)
        quad([P(floor_l, 1, zf), P(floor_r, 1, zf), P(floor_r, wall_y + 0.1, zf), P(floor_l, wall_y + 0.1, zf)], (60, 52, 44))
        # piso
        quad([P(floor_l, 1, 1), P(floor_r, 1, 1), P(floor_r, 1, zf), P(floor_l, 1, zf)], (86, 72, 58))
        for z in np.arange(1.4, zf, 0.7):     # juntas del piso
            d.line([P(floor_l, 1, z), P(floor_r, 1, z)], fill=(62, 52, 42))
        d.line([P(0.5, 1, 1), P(0.5, 1, zf)], fill=(62, 52, 42))
        for s in (0, 1):
            fx = floor_l if s == 0 else floor_r
            tx = tal_x_l if s == 0 else tal_x_r
            out = -0.3 if s == 0 else 1.3
            # talud (inclinado, más claro) y muro vertical
            dm.polygon([P(fx, 1, 1), P(tx, tal_y, 1), P(tx, tal_y, zf), P(fx, 1, zf)], fill=255)
            # muro
            dm.polygon([P(tx, tal_y, 1), P(tx, wall_y, 1), P(tx, wall_y, zf), P(tx, tal_y, zf)], fill=255)
            d.polygon([P(tx, tal_y, 1), P(tx, wall_y, 1), P(tx, wall_y, zf), P(tx, tal_y, zf)], fill=None,
                      outline=(40, 34, 30))
            # parte superior del muro hacia afuera
            quad([P(tx, wall_y, 1), P(out, wall_y, 1), P(out, wall_y, zf), P(tx, wall_y, zf)], (70, 62, 54))
            d.line([P(fx, 1, 1), P(fx, 1, zf)], fill=(40, 34, 30))
            d.line([P(tx, tal_y, 1), P(tx, tal_y, zf)], fill=(150, 136, 110))
            # cara frontal (corte) de la estructura, mirando a la cámara
            edge = 0 if s == 0 else 1
            quad([(edge * W, wall_y * H), (tx * W, wall_y * H), (tx * W, tal_y * H), (fx * W, H), (edge * W, H)],
                 (54, 46, 40))
            if p.get("aros", True):
                z = 2.6
                cx, cy = P(tx, (tal_y + wall_y) / 2 - 0.02, z)
                rw, rh = 0.022 * W / z * 2.2, 0.06 * H / z * 2.2
                d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(160, 148, 120), outline=(40, 34, 30))
                d.ellipse([cx - rw * 0.45, cy - rh * 0.5, cx + rw * 0.45, cy + rh * 0.5], fill=(10, 8, 10))

        alb = np.asarray(img, np.float32).copy()
        a = np.asarray(mk) > 127
        # el talud recibe más luz que el muro
        niebla_profundidad(self, alb, vx, vy, 0.45, 0.12)
        self.mid_alb, self.mid_a = alb, a

        if p.get("antorchas", True):
            for s in (0, 1):
                tx = tal_x_l if s == 0 else tal_x_r
                for z, k in ((1.35, 1.3), (2.6, 0.8), (4.5, 0.5)):
                    x, y = P(tx, wall_y, z)
                    antorcha(self, x + (6 if s == 0 else -6) * k, y - 1, k, radio=40, intensidad=0.9)
        self.lights.append(Light("luna", self.point(vx, 0.92 * H, 0.45 * W, 0.4), (0.7, 0.7, 0.6)))
