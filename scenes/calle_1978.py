"""Calle del centro de la Ciudad de México de noche (1978): fachadas coloniales, una zanja de obra con
montones de tierra, lámparas de trabajo y, dentro de la zanja, el borde de una piedra tallada.

Parámetros:
  lamparas  int   lámparas de obra (default 2)
  piedra    bool  borde de piedra tallada asomando en la zanja (default true)
  semilla   int

Puntos útiles (vertical 256x384): trabajadores junto a la zanja (0.2 W, 0.80 H) y (0.78 W, 0.82 H), escala 1.3;
  dentro de la zanja (0.5 W, 0.78 H)
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, vnoise
from pixel_tales.pintura import roca
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical")
    parallax = {"sky": 0.08, "far": 0.25, "mid": 0.6, "fg": 1.2}

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        rng = np.random.default_rng(60 + self.seed)
        self.sky[:] = (10, 10, 18)
        hy = 0.52 * H
        # fachadas coloniales (capa lejana)
        far = Image.new("RGB", (W, H))
        fm = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(far), ImageDraw.Draw(fm)
        x = -10
        while x < W + 10:
            w = rng.uniform(50, 90)
            top = rng.uniform(0.12, 0.25) * H
            col = tuple(int(c * rng.uniform(0.8, 1.1)) for c in (70, 50, 46))
            d.rectangle([x, top, x + w, hy], fill=col)
            dm.rectangle([x, top - 6, x + w, hy], fill=255)
            d.rectangle([x, top - 6, x + w, top], fill=tuple(int(c * 0.7) for c in col))
            for wy in np.arange(top + 14, hy - 20, 34):
                for wx in np.arange(x + 8, x + w - 12, 20):
                    lit = rng.random() < 0.25
                    d.rectangle([wx, wy, wx + 9, wy + 18], fill=(230, 190, 110) if lit else (20, 18, 24))
                    d.rectangle([wx - 1, wy + 18, wx + 10, wy + 20], fill=(40, 34, 34))
            x += w + 2
        self.far = np.asarray(far, np.float32).copy()
        self.far_a = np.asarray(fm) > 0
        self.far_win = (self.far[..., 0] > 200)
        # calle
        alb = np.zeros((H, W, 3), np.float32)
        u = np.clip((yy - hy) / (H - hy), 0, 1)
        asfalto = np.array([46, 46, 52], np.float32) * (0.8 + 0.3 * fbm(W, H, 61 + self.seed, (16, 8, 4)))[..., None]
        alb[:] = asfalto
        img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        d.rectangle([0, hy, W, hy + 8], fill=(90, 86, 80))               # banqueta del fondo
        # zanja
        zx0, zx1, zy0, zy1 = 0.18 * W, 0.82 * W, 0.66 * H, 0.90 * H
        d.polygon([(zx0 + 10, zy0), (zx1 - 10, zy0), (zx1, zy1), (zx0, zy1)], fill=(30, 22, 16))
        d.polygon([(zx0 + 10, zy0), (zx1 - 10, zy0), (zx1 - 14, zy0 + 10), (zx0 + 14, zy0 + 10)], fill=(70, 52, 34))
        # montones de tierra
        for cx in (0.1 * W, 0.92 * W):
            d.pieslice([cx - 34, 0.60 * H, cx + 34, 0.74 * H], 180, 360, fill=(96, 72, 46))
        # vallas rayadas
        for bx in (0.30 * W, 0.70 * W):
            d.rectangle([bx - 18, 0.60 * H, bx + 18, 0.625 * H], fill=(220, 200, 60))
            for k in range(4):
                d.polygon([(bx - 18 + k * 10, 0.60 * H), (bx - 13 + k * 10, 0.60 * H), (bx - 18 + k * 10 + 5, 0.625 * H), (bx - 23 + k * 10 + 5, 0.625 * H)], fill=(30, 28, 26))
            d.line([(bx - 14, 0.625 * H), (bx - 16, 0.66 * H)], fill=(160, 160, 160))
            d.line([(bx + 14, 0.625 * H), (bx + 16, 0.66 * H)], fill=(160, 160, 160))
        alb = np.asarray(img, np.float32).copy()
        if p.get("piedra", True):                                         # borde curvo de piedra tallada
            m = ((xx - 0.5 * W) / (0.36 * W)) ** 2 + ((yy - 0.97 * H) / (0.16 * H)) ** 2 < 1
            m &= (yy > zy0 + 12) & (yy < zy1)
            n = fbm(W, H, 71 + self.seed, (8, 4))
            alb[m] = np.array([150, 138, 116], np.float32) * (0.75 + 0.4 * n[m])[..., None]
            ring = m & (((xx - 0.5 * W) / (0.36 * W)) ** 2 + ((yy - 0.97 * H) / (0.16 * H)) ** 2 > 0.8)
            alb[ring] *= 0.7
            rel = m & (np.abs(np.sin(xx * 0.4) + np.cos(yy * 0.5)) < 0.25)
            alb[rel] *= 0.75
        self.mid_alb = alb
        self.mid_a = yy >= hy
        # lámparas de obra en tripié
        n = int(p.get("lamparas", 2))
        for k in range(n):
            lx = W * (0.25 + 0.5 * k / max(n - 1, 1))
            ly = 0.60 * H
            m = self.mask(lambda dd, lx=lx, ly=ly: (dd.line([(lx, ly), (lx - 8, ly + 26)], fill=255), dd.line([(lx, ly), (lx + 8, ly + 26)], fill=255),
                                                    dd.line([(lx, ly), (lx, ly + 26)], fill=255), dd.rectangle([lx - 5, ly - 6, lx + 5, ly], fill=255)))
            self.mid_alb[m] = (60, 60, 64)
            m2 = self.mask(lambda dd, lx=lx, ly=ly: dd.rectangle([lx - 4, ly - 5, lx + 4, ly - 1], fill=255))
            self.mid_em[m2] = (255, 240, 200)
            self.lights.append(Light(f"lampara{k}", self.point(lx, ly + 20, 0.55 * H, 1.0), (1.0, 0.95, 0.8), contraluz=True))
        self.lights.append(Light("calle", self.point(0.5 * W, 0, 1.2 * H, 0.25), (0.6, 0.6, 0.8)))
