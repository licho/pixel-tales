"""Panorama nocturno del canal: ciudad en ruinas (izq.), pirámide maya bajo luna roja (centro),
bosque con ojos (der.) y una fogata al frente. Pensada para portadas y piezas de marca.

Parámetros:
  horizonte  posición del horizonte, 0-1 de la altura (default 0.70)
  escala     tamaño de los elementos en pixeles de arte (default = alto de la capa)
  luna_roja  bool (default true)
  fogata     bool (default true)
  semilla    int
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import FUEGO, antorcha, estrellas
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado", "portada_fb", "banner_yt")
    parallax = {"sky": 0.1, "far": 0.25, "mid": 0.6, "fg": 1.0}

    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        k = float(p.get("escala", H))           # unidad de tamaño
        hy = float(p.get("horizonte", 0.70)) * H
        cx = W / 2
        rng = np.random.default_rng(3 + self.seed)

        # ---------- cielo: noche teal arriba, resplandor rojo al centro del horizonte
        t = np.clip(yy / hy, 0, 1)[..., None]
        sky = np.array([8, 12, 16], np.float32) * (1 - t) + np.array([30, 40, 44], np.float32) * t
        glow = np.exp(-(((xx - cx) / (0.9 * k)) ** 2 + ((yy - hy) / (0.45 * k)) ** 2))
        sky += glow[..., None] * np.array([70, 16, 14], np.float32)
        cl = smooth(0.5, 0.72, fbm(W, H, 20 + self.seed, (48, 24, 12, 6)))
        sky = sky * (1 - 0.3 * cl[..., None]) + np.array([40, 52, 54], np.float32) * (cl * 0.45)[..., None]
        estrellas(self, sky, 0.006, (hy - 0.15 * k) / H, self.seed)
        mr = 0.13 * k
        my = hy - 0.50 * k
        d = np.hypot(xx - cx, yy - my)
        moon_col = np.array([200, 60, 40] if p.get("luna_roja", True) else [206, 196, 164], np.float32)
        sky += (np.exp(-np.maximum(d - mr, 0) / (0.12 * k)) * 0.5)[..., None] * moon_col * 0.5
        crater = vnoise(W, H, 3, 7)
        moon = d < mr
        sky[moon] = moon_col * (0.85 + 0.25 * crater[moon])[..., None]
        self.sky = sky

        # ---------- lejos: ciudad (izq.), montañas y bosque (der.)
        far = Image.new("RGB", (W, H), (0, 0, 0))
        fm = Image.new("L", (W, H), 0)
        fd, fmd = ImageDraw.Draw(far), ImageDraw.Draw(fm)
        x = -5.0
        while x < cx - 0.55 * k:
            bw = rng.uniform(0.05, 0.12) * k
            top = hy - rng.uniform(0.15, 0.48) * k
            pts = [(x, hy + 2), (x, top)]
            if rng.random() < 0.6:
                for i in range(1, 4):
                    pts.append((x + bw * i / 4, top + rng.uniform(-3, 6)))
            pts += [(x + bw, top + rng.uniform(0, 4)), (x + bw, hy + 2)]
            fd.polygon(pts, fill=(22, 30, 34))
            fmd.polygon(pts, fill=255)
            for _ in range(int(bw * (hy - top) / 60)):
                wx, wy = rng.uniform(x + 1, x + bw - 1), rng.uniform(top + 2, hy - 2)
                if rng.random() < 0.25:
                    fd.point((wx, wy), fill=(170, 92, 32))
            x += bw + rng.uniform(-2, 1)
        # montañas a la derecha
        mx = np.linspace(cx + 0.4 * k, W + 5, 40)
        ridge = [(float(v), float(hy - (0.18 + 0.12 * math.sin(i * 0.7) + 0.05 * math.sin(i * 2.3)) * k))
                 for i, v in enumerate(mx)]
        poly = [(cx + 0.4 * k, hy + 2)] + ridge + [(W + 5, hy + 2)]
        fd.polygon(poly, fill=(18, 30, 26))
        fmd.polygon(poly, fill=255)
        self.far = np.asarray(far, np.float32).copy()
        self.far_a = np.asarray(fm) > 127
        fog = smooth(hy - 0.3 * k, hy, yy)[..., None]
        self.far = self.far * (1 - 0.4 * fog) + np.array([40, 52, 54], np.float32) * 0.4 * fog

        # ---------- capa media: pirámide, suelo, bosque cercano, ruinas
        img = Image.new("RGB", (W, H), (0, 0, 0))
        mk = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mk)

        def poly(pts, col):
            d.polygon(pts, fill=col)
            dm.polygon(pts, fill=255)

        # suelo
        poly([(0, hy), (W, hy), (W, H), (0, H)], (40, 38, 34))
        # pirámide escalonada con templo
        base_w, ph = 0.95 * k, 0.40 * k
        steps = 6
        for i in range(steps):
            w = base_w * (1 - i / steps * 0.72)
            y0 = hy - ph * (i + 1) / steps
            y1 = hy - ph * i / steps + 1
            poly([(cx - w / 2, y1), (cx - w / 2, y0), (cx + w / 2, y0), (cx + w / 2, y1)], (74, 64, 56))
            d.line([(cx - w / 2, y0), (cx + w / 2, y0)], fill=(112, 100, 86))
        sw = base_w * 0.13
        for i in range(int(ph / 2)):           # escalinata central
            y = hy - i * 2
            d.line([(cx - sw / 2, y), (cx + sw / 2, y)], fill=(96, 86, 76) if i % 2 else (60, 52, 46))
        tw, th = base_w * 0.2, 0.12 * k
        ty = hy - ph
        poly([(cx - tw / 2, ty), (cx - tw / 2, ty - th), (cx + tw / 2, ty - th), (cx + tw / 2, ty)], (66, 56, 50))
        poly([(cx - tw * 0.62, ty - th), (cx + tw * 0.62, ty - th), (cx + tw * 0.45, ty - th * 1.45),
              (cx - tw * 0.45, ty - th * 1.45)], (58, 48, 44))
        d.rectangle([cx - tw * 0.16, ty - th * 0.75, cx + tw * 0.16, ty], fill=(12, 8, 10))
        # ruinas y carro a la izquierda
        for i in range(5):
            rx = cx - 0.75 * k - i * 0.13 * k
            rw, rh = rng.uniform(0.04, 0.09) * k, rng.uniform(0.04, 0.18) * k
            poly([(rx, hy + 1), (rx, hy - rh), (rx + rw * 0.6, hy - rh * rng.uniform(0.6, 1)), (rx + rw, hy - rh * 0.5),
                  (rx + rw, hy + 1)], (34, 40, 44))
        # bosque cercano a la derecha (pinos)
        x = cx + 0.62 * k
        while x < W + 10:
            th_ = rng.uniform(0.18, 0.36) * k
            tw_ = th_ * 0.38
            poly([(x, hy - th_), (x - tw_ / 2, hy + 1), (x + tw_ / 2, hy + 1)], (16, 28, 22))
            x += tw_ * rng.uniform(0.45, 0.8)
        self.mid_alb = np.asarray(img, np.float32).copy()
        self.mid_a = np.asarray(mk) > 127

        # luces: antorchas en la pirámide, fogata al frente
        antorcha(self, cx - base_w * 0.18, hy - ph * 0.55, 0.5 * k / 100, radio=0.12 * k, intensidad=0.9)
        antorcha(self, cx + base_w * 0.18, hy - ph * 0.55, 0.5 * k / 100, radio=0.12 * k, intensidad=0.9)
        self.lights.append(Light("luna", self.point(cx, my, 0.6 * k, 0.45), tuple(moon_col / 220)))
        if p.get("fogata", True):
            fy = min(hy + 0.15 * k, H - 3)
            fw = 0.10 * k
            self._fogata(cx, fy, fw)

        # primer plano: pasto oscuro en el borde inferior
        for x0 in range(0, W, 2):
            hgt = int(2 + 3 * abs(math.sin(x0 * 0.21)) + rng.integers(0, 3))
            self.fg_a[H - hgt:, x0:x0 + 2] = True
        self.fg_alb[:] = (10, 14, 14)

    def _fogata(self, x, y, w):
        m = self.mask(lambda d: (d.line([(x - w / 2, y), (x + w / 2, y - w * 0.15)], fill=255, width=max(1, int(w / 6))),
                                 d.line([(x - w / 2, y - w * 0.15), (x + w / 2, y)], fill=255, width=max(1, int(w / 6)))))
        self.mid_alb[m] = (70, 44, 26)
        self.mid_a |= m
        for i in range(7):
            a = math.pi * i / 6
            sx, sy = x + math.cos(a) * w * 0.65, y + 1 + math.sin(a) * w * 0.12
            st = self.mask(lambda d: d.ellipse([sx - w * 0.08, sy - w * 0.06, sx + w * 0.08, sy + w * 0.06], fill=255))
            self.mid_alb[st] = (90, 86, 80)
            self.mid_a |= st
        self.fires.append({"x0": int(x - w * 0.35), "x1": int(x + w * 0.35) + 1, "y": int(y - w * 0.12),
                           "tam": w / 12, "humo": True})
        self.lights.append(Light("fogata", self.point(x, y - w * 0.3, w * 4.0, 1.3), FUEGO, parpadeo="fuego",
                                 contraluz=True))
