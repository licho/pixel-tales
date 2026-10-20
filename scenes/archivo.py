"""Cuarto de investigación de noche: pizarrón de corcho con fotos e hilos rojos, escritorio con
papeles y lámpara, cajas de archivo y una ventana con luna. Sirve para cualquier historia de misterio.

Parámetros:
  ventana   bool (default true)
  jaguar    bool  marca dos ojos claros en varias fotos del corcho (default true)
  semilla   int

Puntos útiles (relativos a W x H):
  silla frente al escritorio (personaje de espaldas): (0.52 W, 0.93 H)
  lámpara del escritorio: (0.20 W, 0.66 H)
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, vnoise
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical")
    parallax = {"sky": 0.2, "far": 0.3, "mid": 0.6, "fg": 1.1}

    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        rng = np.random.default_rng(20 + self.seed)
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)

        # pared con papel tapiz a rayas
        for x in range(0, W, 6):
            d.rectangle([x, 0, x + 5, H], fill=(46, 52, 62) if (x // 6) % 2 else (40, 46, 56))
        d.rectangle([0, 0.06 * H, W, 0.065 * H], fill=(30, 34, 40))

        # ventana con luna
        if p.get("ventana", True):
            wx0, wy0, wx1, wy1 = 0.06 * W, 0.10 * H, 0.30 * W, 0.34 * H
            d.rectangle([wx0, wy0, wx1, wy1], fill=(12, 18, 30))
            d.ellipse([wx0 + 0.13 * W, wy0 + 0.04 * H, wx0 + 0.19 * W, wy0 + 0.04 * H + 0.06 * W], fill=(200, 206, 200))
            d.rectangle([wx0, wy0, wx1, wy1], outline=(70, 50, 30), width=3)
            d.line([((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], fill=(70, 50, 30), width=2)
            d.line([(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], fill=(70, 50, 30), width=2)

        # corcho con fotos e hilos
        cx0, cy0, cx1, cy1 = 0.36 * W, 0.08 * H, 0.96 * W, 0.50 * H
        d.rectangle([cx0, cy0, cx1, cy1], fill=(136, 98, 60), outline=(70, 46, 28), width=3)
        pins = []
        for i in range(11):
            pw, ph = rng.uniform(0.09, 0.13) * W, rng.uniform(0.05, 0.07) * H
            x0 = rng.uniform(cx0 + 4, cx1 - pw - 4)
            y0 = rng.uniform(cy0 + 4, cy1 - ph - 4)
            sepia = tuple(int(v * rng.uniform(0.8, 1.05)) for v in (196, 168, 124))
            d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=(222, 210, 180))
            d.rectangle([x0 + 2, y0 + 2, x0 + pw - 2, y0 + ph - 2], fill=sepia)
            d.rectangle([x0 + pw * 0.4, y0 + ph * 0.3, x0 + pw * 0.55, y0 + ph - 2], fill=(80, 60, 40))   # persona
            d.ellipse([x0 + pw * 0.4, y0 + ph * 0.12, x0 + pw * 0.55, y0 + ph * 0.38], fill=(110, 86, 60))
            if p.get("jaguar", True) and i % 3 == 0:
                d.point([(x0 + pw * 0.78, y0 + ph * 0.45), (x0 + pw * 0.86, y0 + ph * 0.45)], fill=(250, 240, 200))
            px, py = x0 + pw / 2, y0 + 2
            d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill=(200, 40, 30))
            pins.append((px, py))
        for a, b in zip(pins, pins[2:] + pins[:1]):
            if rng.random() < 0.7:
                d.line([a, b], fill=(170, 30, 26))
        for i in range(5):                                          # notas adhesivas
            nx, ny = rng.uniform(cx0, cx1 - 0.06 * W), rng.uniform(cy0, cy1 - 0.04 * H)
            d.rectangle([nx, ny, nx + 0.06 * W, ny + 0.035 * H], fill=(220, 200, 110))

        # escritorio
        top = 0.64 * H
        d.rectangle([0, top, W, H], fill=(74, 50, 32))
        d.rectangle([0, top, W, top + 3], fill=(110, 78, 50))
        for i in range(8):                                          # papeles y fotos
            x0, y0 = rng.uniform(0.25, 0.85) * W, rng.uniform(0.67, 0.80) * H
            col = (210, 206, 192) if i % 2 else (190, 160, 118)
            d.polygon([(x0, y0), (x0 + 0.12 * W, y0 + rng.uniform(-3, 3)), (x0 + 0.12 * W, y0 + 0.05 * H),
                       (x0, y0 + 0.05 * H)], fill=col)
            if i % 2:
                for k in range(4):
                    d.line([(x0 + 3, y0 + 3 + k * 3), (x0 + 0.1 * W, y0 + 3 + k * 3)], fill=(120, 116, 110))
        # cajas de archivo
        for k in range(3):
            bx, by = 0.80 * W, top - (k + 1) * 0.07 * H
            d.rectangle([bx, by, bx + 0.18 * W, by + 0.07 * H], fill=(150, 124, 86), outline=(90, 70, 46))
            d.rectangle([bx + 0.06 * W, by + 0.02 * H, bx + 0.12 * W, by + 0.04 * H], fill=(220, 214, 196))
        # lámpara
        lx, ly = 0.20 * W, 0.62 * H
        d.line([(lx - 0.04 * W, top), (lx, ly)], fill=(30, 34, 30), width=3)
        d.polygon([(lx - 0.07 * W, ly + 0.01 * H), (lx + 0.03 * W, ly - 0.04 * H), (lx + 0.06 * W, ly), (lx - 0.03 * W, ly + 0.035 * H)],
                  fill=(40, 70, 50))
        d.ellipse([lx - 0.07 * W, top - 2, lx - 0.01 * W, top + 2], fill=(30, 34, 30))

        self.mid_alb = np.asarray(img, np.float32) * (0.9 + 0.2 * vnoise(W, H, 2, 3))[..., None]
        self.mid_a[:] = True
        self.mid_em[int(ly + 0.01 * H):int(ly + 0.025 * H), int(lx - 0.05 * W):int(lx + 0.02 * W)] = (255, 220, 150)
        self.lights.append(Light("lampara", self.point(lx + 0.05 * W, 0.70 * H, 0.38 * W, 1.6), (1.0, 0.75, 0.45)))
        self.lights.append(Light("luna", self.point(0.18 * W, 0.22 * H, 0.18 * W, 0.4), (0.6, 0.7, 0.9)))
        self.sky[:] = (4, 4, 6)
