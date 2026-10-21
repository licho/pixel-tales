"""El cerro de Coatepec ("cerro de la serpiente") con un pequeño templo en la cima.

Parámetros:
  vista      'lejos' (todo el cerro con el valle) | 'cima' (la plataforma del templo, de cerca)  (default lejos)
  hora       'atardecer' | 'noche' | 'amanecer'   (default noche)
  estallido  bool  explosión de luz en la cima (nacimiento de Huitzilopochtli)
  antorchas  int   antorchas subiendo por el camino y al pie del cerro (los 400)  (default 0)
  luna       bool  (default true de noche y al amanecer)
  semilla    int

Puntos útiles (vertical 256x384):
  lejos: cima/templo (0.5 W, 0.30 H); ladera (siluetas rodando) x 0.3-0.7 W, y 0.35-0.65 H;
         multitud al pie: zona [0, 0.70 H, W, 0.98 H]
  cima: personaje en la plataforma (0.5 W, 0.90 H), escala 1.6-2; templo detrás en (0.5 W, 0.55 H)
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import antorcha, brasero, estrellas, roca
from pixel_tales.scene import Scene

CIELOS = {
    "atardecer": ((40, 26, 40), (150, 60, 40), (236, 150, 70)),
    "noche": ((6, 6, 12), (18, 16, 30), (36, 30, 44)),
    "amanecer": ((20, 20, 44), (120, 70, 80), (250, 170, 90)),
}


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.08, "far": 0.2, "mid": 0.6, "fg": 1.2}

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        rng = np.random.default_rng(80 + self.seed)
        hora = p.get("hora", "noche")
        vista = p.get("vista", "lejos")
        top, mid, hor = (np.array(c, np.float32) for c in CIELOS[hora])
        hy = (0.78 if vista == "lejos" else 0.60) * H
        t = np.clip(yy / hy, 0, 1)[..., None]
        sky = np.where(t < 0.6, top * (1 - t / 0.6) + mid * (t / 0.6), mid * (1 - (t - 0.6) / 0.4) + hor * ((t - 0.6) / 0.4))
        if hora != "atardecer":
            estrellas(self, sky, 0.005 if hora == "noche" else 0.0025, 0.45, self.seed, (210, 200, 190))
        if p.get("luna", hora != "atardecer"):
            lx, ly = 0.22 * W, 0.12 * H
            dd = np.hypot(xx - lx, yy - ly)
            k = 0.45 if hora == "amanecer" else 1.0
            sky += (np.exp(-dd / (0.1 * W)) * 30 * k)[..., None]
            sky[dd < 10] = sky[dd < 10] * (1 - k) + np.array([220, 214, 200], np.float32) * k
        if hora == "amanecer":                                       # sol saliendo detrás del cerro
            sx, sy = (0.84 * W, 0.42 * H) if vista == "lejos" else (0.68 * W, hy)
            dd = np.hypot(xx - sx, yy - sy)
            sky += (np.exp(-dd / (0.3 * W)) * 90)[..., None] * np.array([1.0, 0.7, 0.35], np.float32)
            sky[dd < 0.07 * W] = (255, 230, 160)
        self.cx, self.cy = 0.5 * W, (0.30 if vista == "lejos" else 0.55) * H
        if p.get("estallido"):
            dd = np.hypot(xx - self.cx, yy - self.cy)
            sky += (np.exp(-dd / (0.35 * W)) * 160)[..., None] * np.array([1.0, 0.85, 0.5], np.float32)
            for k in range(14):                                      # rayos de luz
                a = k / 14 * 2 * math.pi
                ang = np.arctan2(yy - self.cy, xx - self.cx)
                ray = (np.abs(np.angle(np.exp(1j * (ang - a)))) < 0.04) * np.exp(-dd / (0.6 * W))
                sky += (ray * 120)[..., None] * np.array([1.0, 0.9, 0.6], np.float32)
        self.sky = sky

        # valle / montañas lejanas
        far = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(far)
        pts = [(-5, hy + 2)] + [(x, hy - 0.04 * H * (0.5 + 0.5 * math.sin(x * 0.05 + self.seed))) for x in np.linspace(-5, W + 5, 30)] + [(W + 5, hy + 2)]
        fd.polygon(pts, fill=255)
        self.far_a = np.asarray(far) > 0
        self.far = np.broadcast_to(hor * 0.35 + top * 0.3, (H, W, 3)).astype(np.float32).copy()

        alb = roca(self, (96, 80, 62), self.seed, 0.6)
        img = Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8))
        mk = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mk)
        if vista == "lejos":
            # suelo del valle
            dm.rectangle([0, hy, W, H], fill=255)
            # el cerro
            cerro = [(-0.1 * W, H), (0.1 * W, 0.62 * H), (0.36 * W, 0.36 * H), (0.44 * W, 0.32 * H), (0.56 * W, 0.32 * H),
                     (0.64 * W, 0.36 * H), (0.9 * W, 0.62 * H), (1.1 * W, H)]
            cerro = [(x + rng.uniform(-2, 2), y + rng.uniform(-2, 2)) for x, y in cerro]
            dm.polygon(cerro, fill=255)
            # vegetación seca y piedras
            for _ in range(160):
                x, y = rng.uniform(0, W), rng.uniform(0.34, 1.0) * H
                d.point((x, y), fill=(60, 70, 40))
            # camino en zigzag
            self.camino = []
            for k in range(9):
                v = k / 8
                y = 0.33 * H + (0.95 - 0.33) * H * v
                x = W * (0.5 + 0.22 * (1 if k % 2 else -1) * v)
                self.camino.append((x, y))
            d.line(self.camino, fill=(140, 116, 84), width=3)
            # templo en la cima
            cx, cy = self.cx, 0.32 * H
            d.rectangle([cx - 20, cy - 10, cx + 20, cy], fill=(130, 110, 90))
            d.rectangle([cx - 10, cy - 24, cx + 10, cy - 10], fill=(150, 50, 36))
            d.polygon([(cx - 13, cy - 24), (cx + 13, cy - 24), (cx, cy - 34)], fill=(110, 40, 30))
            d.rectangle([cx - 3, cy - 18, cx + 3, cy - 10], fill=(14, 10, 10))
            dm.rectangle([cx - 20, cy - 24, cx + 20, cy], fill=255)
            dm.polygon([(cx - 13, cy - 24), (cx + 13, cy - 24), (cx, cy - 34)], fill=255)
        else:
            # plataforma de piedra de la cima, en perspectiva
            dm.rectangle([0, hy, W, H], fill=255)
            for k in range(14):
                y = hy + (H - hy) * (k / 14) ** 1.4
                d.line([(0, y), (W, y)], fill=(70, 58, 46))
            for k in range(-8, 9):
                d.line([(W / 2 + k * 6, hy), (W / 2 + k * 40, H)], fill=(70, 58, 46))
            # templo detrás
            cx, cy = self.cx, hy + 2
            d.rectangle([cx - 46, cy - 70, cx + 46, cy], fill=(140, 118, 96))
            d.rectangle([cx - 30, cy - 120, cx + 30, cy - 70], fill=(150, 50, 36))
            d.polygon([(cx - 38, cy - 120), (cx + 38, cy - 120), (cx, cy - 160)], fill=(110, 40, 30))
            d.rectangle([cx - 11, cy - 104, cx + 11, cy - 70], fill=(14, 10, 10))
            for k in range(8):
                y = cy - 70 + k * 9
                d.line([(cx - 46, y), (cx + 46, y)], fill=(110, 92, 74))
            dm.rectangle([cx - 46, cy - 70, cx + 46, cy], fill=255)
            dm.rectangle([cx - 30, cy - 120, cx + 30, cy - 70], fill=255)
            dm.polygon([(cx - 38, cy - 120), (cx + 38, cy - 120), (cx, cy - 160)], fill=255)
        self.mid_alb = np.asarray(img, np.float32).copy()
        self.mid_a = np.asarray(mk) > 0
        if vista == "cima" and hora != "amanecer":
            for s in (-1, 1):
                brasero(self, self.cx + s * 70, hy + 30, tam=1.2, intensidad=1.0)

        # antorchas de los 400 (subiendo por el camino y al pie del cerro)
        n = int(p.get("antorchas", 0))
        if n and vista == "lejos":
            for k in range(n):
                if k < n * 0.45:                                     # por el camino
                    u = rng.uniform(0.25, 1.0)
                    i = min(int(u * 8), 7)
                    f = u * 8 - i
                    (x0, y0), (x1, y1) = self.camino[i], self.camino[i + 1]
                    x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                else:                                                # al pie
                    x, y = rng.uniform(0, W), rng.uniform(0.80, 0.98) * H
                tam = 0.2 + 0.35 * (y / H)
                self.fires.append({"x0": int(x - 1), "x1": int(x + 2), "y": int(y - 4 * tam), "tam": tam, "humo": False})
            self.lights.append(Light("antorchas", self.pool(W / 2, 0.88 * H, 0.7 * W, 0.12 * H, 0.9), (1.0, 0.55, 0.22),
                                     parpadeo="fuego"))
            self.lights.append(Light("camino", self.pool(W / 2, 0.62 * H, 0.35 * W, 0.25 * H, 0.45), (1.0, 0.55, 0.22),
                                     parpadeo="fuego"))

        if p.get("estallido"):
            self.lights.append(Light("estallido", self.point(self.cx, self.cy, 0.9 * H, 0.85), (1.0, 0.85, 0.55),
                                     contraluz=True))
        elif hora == "atardecer":
            self.lights.append(Light("sol", self.point(0.5 * W, hy, 1.2 * H, 0.55), (1.0, 0.7, 0.45)))
        elif hora == "amanecer":
            self.lights.append(Light("sol", self.point(0.68 * W, 0.4 * H, 1.2 * H, 0.75), (1.0, 0.75, 0.5)))
        else:
            self.lights.append(Light("luna", self.point(0.22 * W, 0, 1.3 * H, 0.35), (0.6, 0.6, 0.85)))
