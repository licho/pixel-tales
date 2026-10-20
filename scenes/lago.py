"""Lago rodeado de montañas y bosque, con niebla sobre el agua. Vista desde la orilla o aérea.

Parámetros:
  vista    'orilla' | 'aerea'          (default orilla)
  hora     'anochecer' | 'noche'       (default anochecer)
  isla     bool  isla con árboles en medio del lago (default: true en aérea, false en orilla)
  niebla   bool (default true)
  semilla  int

Puntos útiles (relativos a W x H; pies/base):
  orilla: lancha en la orilla cercana (0.45 W, 0.93 H); personaje en la orilla (0.25 W, 0.97 H)
  aérea: lancha pequeña (escala ~0.35) en el agua x 0.4-0.6 W, y 0.55-0.85 H; isla en (0.5 W, 0.30 H)
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import estrellas
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")

    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        rng = np.random.default_rng(40 + self.seed)
        aerea = p.get("vista", "orilla") == "aerea"
        noche = p.get("hora", "anochecer") == "noche"
        hy = (0.13 if aerea else 0.44) * H

        # cielo
        t = np.clip(yy / hy, 0, 1)[..., None]
        top = np.array([8, 12, 24], np.float32)
        hor = np.array([40, 52, 72] if noche else [150, 86, 70], np.float32)
        sky = top * (1 - t) + hor * t
        estrellas(self, sky, 0.004 if noche else 0.0015, hy / H * 0.8, self.seed, (180, 188, 196))
        self.sky = sky

        # montañas (capa lejana)
        far = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(far)
        for layer, (amp, col) in enumerate(((0.16, 1), (0.09, 2))):
            pts = [(-5, hy + 1)]
            for x in np.linspace(-5, W + 5, 30):
                pts.append((x, hy - (amp * H if not aerea else amp * H * 0.4) * (0.5 + 0.5 * np.sin(x * 0.03 + layer * 2 + self.seed))
                            * (0.6 + 0.4 * np.cos(x * 0.011 + layer))))
            pts.append((W + 5, hy + 1))
            fd.polygon(pts, fill=80 + layer * 80)
        fa = np.asarray(far)
        self.far_a = fa > 0
        self.far = np.where((fa > 120)[..., None], np.array([22, 30, 34], np.float32), np.array([34, 44, 56], np.float32))

        # agua: reflejo del cielo, más oscura hacia la cámara
        img = Image.new("RGB", (W, H))
        mk = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mk)
        u = np.clip((yy - hy) / (H - hy), 0, 1)
        water = (hor * (1 - u[..., None]) * 0.35 + np.array([18, 28, 42], np.float32) * (0.5 + u[..., None] * 0.5))
        n = vnoise(W, H, 4, 9 + self.seed)
        water *= (0.9 + 0.2 * n)[..., None]
        arr = np.zeros((H, W, 3), np.float32)
        arr[yy >= hy] = water[yy >= hy]
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        dm.rectangle([0, hy, W, H], fill=255)
        # línea de bosque en la orilla lejana
        x = -4.0
        while x < W + 4:
            h = rng.uniform(0.012, 0.03) * H * (0.5 if aerea else 1)
            w = h * 0.6
            d.polygon([(x, hy - h), (x - w, hy + 1), (x + w, hy + 1)], fill=(14, 22, 18))
            dm.polygon([(x, hy - h), (x - w, hy + 1), (x + w, hy + 1)], fill=255)
            x += w * 0.8

        if p.get("isla", aerea):
            ix, iy = 0.5 * W, (0.30 if aerea else 0.48) * H
            iw, ih = (0.55 if aerea else 0.25) * W, (0.10 if aerea else 0.02) * H
            d.ellipse([ix - iw / 2, iy - ih / 2, ix + iw / 2, iy + ih / 2], fill=(30, 26, 20))
            for _ in range(int(60 if aerea else 25)):
                tx = rng.uniform(ix - iw * 0.45, ix + iw * 0.45)
                ty = rng.uniform(iy - ih * 0.4, iy + ih * 0.2)
                r = rng.uniform(0.02, 0.04) * W
                hh = r * (1.0 if aerea else 2.4)
                d.ellipse([tx - r, ty - hh, tx + r, ty + r * 0.4], fill=tuple(int(c * rng.uniform(0.7, 1.1)) for c in (18, 32, 24)))
                dm.ellipse([tx - r, ty - hh, tx + r, ty + r * 0.4], fill=255)

        if not aerea:  # orilla cercana con piedras y tule
            sy = 0.86 * H
            shore = [(0, H), (0, sy)] + [(x, sy + 5 * np.sin(x * 0.07) + 3 * np.sin(x * 0.23)) for x in range(0, W + 6, 6)] + [(W, H)]
            d.polygon(shore, fill=(44, 34, 24))
            for _ in range(18):
                sx, s_y = rng.uniform(0, W), rng.uniform(sy + 4, H)
                r = rng.uniform(2, 6)
                d.ellipse([sx - r, s_y - r * 0.6, sx + r, s_y + r * 0.6], fill=(70, 68, 62))
            for _ in range(30):
                rx = rng.choice([rng.uniform(0, 0.25 * W), rng.uniform(0.75 * W, W)])
                h = rng.uniform(10, 30)
                d.line([(rx, sy + 4), (rx + rng.uniform(-3, 3), sy + 4 - h)], fill=(40, 52, 34))

        alb = np.asarray(img, np.float32).copy()
        self.chop = vnoise(W, H, 5, 99 + self.seed)
        self.water = (yy > hy + 1) & (np.asarray(mk) > 0) & (alb.sum(-1) < 400)
        if p.get("niebla", True):
            nf = fbm(W, H, 70 + self.seed, (48, 24, 12))
            band = (hy + (0.03 if not aerea else 0.25) * H)
            k = np.exp(-((yy - band) / (0.08 * H)) ** 2) * (0.3 + 0.7 * nf)
            if aerea:  # jirones de niebla alargados sobre el agua
                small = fbm(W // 6 + 1, H, 80 + self.seed, (8, 4, 2))
                streak = np.repeat(small, 6, axis=1)[:, :W]
                k = np.maximum(k, smooth(0.58, 0.75, streak) * 0.45 * (yy > hy))
            fogc = np.array([110, 118, 128], np.float32)
            alb = alb * (1 - 0.55 * k[..., None]) + fogc * 0.55 * k[..., None]
        self.mid_alb, self.mid_a = alb, np.asarray(mk) > 0

        self.lights.append(Light("cielo", self.point(0.5 * W, hy, 0.9 * W, 0.6), tuple(hor / 160)))

    def animar(self, col, t):
        m = self.water
        xx, yy = self.grid()
        s = np.sin(yy[m] * 1.7 + t * 1.5 + self.chop[m] * 9)
        hi = (s > 0.9) & (self.chop[m] > 0.62)
        col[m] = np.where(hi[..., None], col[m] * 1.45 + 8, col[m])
