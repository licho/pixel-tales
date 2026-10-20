"""Interior de una casa maya tradicional de noche: techo de palma, muros de bajareque,
puerta con luz de luna, hamaca, fogón de tres piedras y un rincón muy oscuro.
Sirve para leyendas y terror moderno (nahuales, aluxes, apariciones).

Parámetros:
  fogon          bool (default true)
  puerta_luna    bool (default true)
  hamaca         bool (default true)
  rincon_oscuro  bool (default true)   oscurece la esquina derecha
  semilla        int

Puntos útiles (relativos a W x H):
  rincón oscuro: (0.86 W, 0.62-0.80 H)  -> buen lugar para 'ojos' y la sombra
  piso: x 0.10-0.80 W, y 0.80-0.97 H (personajes de pie ~0.25 H)
  fogón: (0.60 W, 0.88 H)
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.scene import Scene


class Escena(Scene):
    parallax = {"sky": 0.2, "far": 0.3, "mid": 0.6, "fg": 1.2}

    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        rng = np.random.default_rng(4 + self.seed)

        # afuera (se ve por la puerta): noche con luna y siluetas de árboles
        self.sky = np.array([16, 26, 24], np.float32) + (np.exp(-np.hypot(xx - 0.40 * W, yy - 0.43 * H) / 18) * 60)[..., None]
        trees = vnoise(W, H, 10, 8 + self.seed)
        self.far_a = yy > 0.60 * H - trees * 0.08 * H
        self.far[:] = (10, 18, 16)

        img = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(img)
        wall_top, floor_y = 0.30 * H, 0.76 * H

        # muro de bajareque: palos verticales con lodo
        x = 0
        while x < W:
            w = rng.uniform(3, 5)
            c = rng.uniform(0.75, 1.1)
            d.rectangle([x, wall_top, x + w - 1, floor_y], fill=tuple(int(v * c) for v in (88, 62, 40)))
            x += w
        mud = fbm(W, H, 50 + self.seed, (8, 4, 2)) > 0.55
        arr = np.asarray(img, np.float32).copy()
        zone = (yy >= wall_top) & (yy <= floor_y)
        arr[mud & zone] = np.array([100, 76, 52], np.float32) * (0.9 + 0.2 * vnoise(W, H, 2, 9))[mud & zone][..., None]
        img = Image.fromarray(arr.astype(np.uint8))
        d = ImageDraw.Draw(img)

        # techo de palma con vigas
        d.rectangle([0, 0, W, wall_top], fill=(60, 46, 28))
        for k in range(int(W * H * 0.02)):
            x0, y0 = rng.uniform(0, W), rng.uniform(0, wall_top)
            L = rng.uniform(4, 10)
            c = tuple(int(v * rng.uniform(0.6, 1.2)) for v in (96, 76, 44))
            d.line([(x0, y0), (x0 + L * 0.8, y0 + L * 0.6)], fill=c)
        d.line([(0, wall_top), (W, wall_top)], fill=(40, 28, 20), width=3)
        for xv in np.linspace(-0.2 * W, 1.2 * W, 7):
            d.line([(0.5 * W, -0.15 * H), (xv, wall_top)], fill=(46, 32, 22), width=2)

        # piso de tierra
        d.rectangle([0, floor_y, W, H], fill=(70, 54, 38))

        # puerta abierta (se ve la noche)
        door = (0.30 * W, 0.42 * H, 0.48 * W, floor_y)
        if p.get("puerta_luna", True):
            d.rectangle([door[0] - 2, door[1] - 3, door[2] + 2, door[1]], fill=(50, 36, 24))
            d.rectangle([door[0] - 2, door[1], door[0], door[3]], fill=(50, 36, 24))
            d.rectangle([door[2], door[1], door[2] + 2, door[3]], fill=(50, 36, 24))

        # ollas de barro
        for ox, s in ((0.10, 1.0), (0.17, 0.75)):
            cx, cy = ox * W, floor_y + 0.03 * H
            r = 0.035 * W * s
            d.ellipse([cx - r, cy - 2 * r, cx + r, cy], fill=(120, 64, 34))
            d.rectangle([cx - r * 0.5, cy - 2.3 * r, cx + r * 0.5, cy - 1.8 * r], fill=(100, 52, 28))

        # fogón: tres piedras y comal
        if p.get("fogon", True):
            fx, fy = 0.60 * W, 0.885 * H
            for dx in (-0.06, 0.0, 0.06):
                d.ellipse([fx + dx * W - 5, fy - 4, fx + dx * W + 5, fy + 3], fill=(70, 64, 58))
            d.ellipse([fx - 0.08 * W, fy - 9, fx + 0.08 * W, fy - 5], fill=(36, 30, 28))

        # hamaca colgando de pared a pared
        if p.get("hamaca", True):
            xs = np.linspace(0.52 * W, W, 30)
            f = (xs - 0.52 * W) / (0.48 * W)
            pts_top = [(x, 0.50 * H + 0.10 * H * 4 * q * (1 - q)) for x, q in zip(xs, f)]
            pts_bot = [(x, 0.505 * H + 0.14 * H * 4 * q * (1 - q)) for x, q in zip(xs, f)]
            d.line([(0.52 * W, 0.50 * H), (0.52 * W - 6, 0.46 * H)], fill=(160, 130, 90))
            poly = pts_top + pts_bot[::-1]
            d.polygon(poly, fill=(150, 56, 40))
            for k, (a, b) in enumerate(zip(pts_top, pts_bot)):
                if k % 3 == 0:
                    d.line([a, b], fill=(200, 160, 100))

        alb = np.asarray(img, np.float32).copy()
        alb[(yy < 0.3 * H)] *= 0.8
        if p.get("rincon_oscuro", True):
            k = 1 - 0.85 * smooth(0.70 * W, 0.86 * W, xx) * smooth(0.25 * H, 0.45 * H, yy)
            alb *= k[..., None]
        self.mid_alb = alb
        a = np.ones((H, W), bool)
        if p.get("puerta_luna", True):
            a &= ~((xx > door[0]) & (xx < door[2]) & (yy > door[1]) & (yy < door[3]))
        self.mid_a = a

        luna = (0.55, 0.75, 0.65)
        if p.get("puerta_luna", True):
            pool = self.pool(0.40 * W, 0.86 * H, 0.10 * W, 0.08 * H, 0.9, floor_y)
            self.lights.append(Light("luna", pool + self.point(0.39 * W, 0.6 * H, 0.10 * W, 0.4), luna))
        if p.get("fogon", True):
            self.fires.append({"x0": int(0.55 * W), "x1": int(0.65 * W), "y": int(0.875 * H), "tam": 0.6, "humo": True})
            self.lights.append(Light("fogon", self.point(0.60 * W, 0.80 * H, 0.17 * W, 1.25), (1.0, 0.55, 0.25),
                                     parpadeo="fuego", contraluz=True))

        # primer plano: horcón (poste) y manojos colgando del techo
        def fg(dr):
            dr.rectangle([0, 0, 0.05 * W, H], fill=255)
            for hx in (0.22, 0.70, 0.80):
                dr.line([(hx * W, 0), (hx * W, 0.06 * H)], fill=255)
                dr.polygon([(hx * W - 4, 0.06 * H), (hx * W + 4, 0.06 * H), (hx * W + 2, 0.13 * H),
                            (hx * W - 2, 0.13 * H)], fill=255)
        self.fg_a = self.mask(fg)
        self.fg_alb[:] = (60, 42, 26)
