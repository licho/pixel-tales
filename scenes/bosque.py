"""Bosque con sendero de lodo que se pierde entre los árboles. Reutilizable para cualquier historia.

Parámetros:
  hora     'tarde' | 'noche'   (default noche)
  niebla   bool (default true)
  huellas  bool  huellas grandes de felino en el lodo (default false)
  orilla   bool  agua en la parte baja (llegada a una isla / orilla de lago) (default false)
  fogata   [x, y, ancho]  fogata en el suelo (x, y relativos; ancho en px, ej. 22)
  luna     intensidad de la luz de luna de noche (default 1.0; baja a 0.3 para que mande la fogata)
  semilla  int

Puntos útiles (relativos a W x H; pies):
  sendero cerca: (0.5 W, 0.95 H) personaje de ~0.25 H ; sendero medio: (0.5 W, 0.75 H) ~0.12 H
  entre los árboles (figuras al fondo): x 0.25-0.75 W, y 0.62-0.66 H, alto ~0.12-0.18 H
  con orilla=true: agua y 0.84-1.0 H; lancha en (0.45 W, 0.97 H)
"""
import numpy as np
from PIL import Image, ImageDraw

from pixel_tales.core import Light, fbm, smooth, vnoise
from pixel_tales.pintura import estrellas, fogata
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")

    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        rng = np.random.default_rng(30 + self.seed)
        tarde = p.get("hora", "noche") == "tarde"
        hy = 0.62 * H
        vx = 0.5 * W

        # cielo entre las copas
        t = np.clip(yy / hy, 0, 1)[..., None]
        if tarde:
            sky = np.array([30, 26, 48], np.float32) * (1 - t) + np.array([200, 110, 50], np.float32) * t
        else:
            sky = np.array([6, 9, 16], np.float32) * (1 - t) + np.array([30, 42, 58], np.float32) * t
            estrellas(self, sky, 0.004, 0.5, self.seed, (170, 180, 190))
        self.sky = sky

        # lejos: troncos delgados en la niebla
        far = Image.new("L", (W, H), 0)
        fd = ImageDraw.Draw(far)
        for _ in range(int(W / 6)):
            x0 = rng.uniform(-5, W)
            w = rng.uniform(1.5, 4.5)
            fd.rectangle([x0, 0, x0 + w, hy + 2], fill=255)
            fd.ellipse([x0 - w * 5, -10, x0 + w * 6, rng.uniform(0.12, 0.3) * H], fill=255)
        self.far_a = np.asarray(far) > 127
        fog = np.array([60, 72, 86] if not tarde else [150, 96, 70], np.float32)
        self.far = np.array([20, 30, 28], np.float32) * 0.5 + fog * 0.5 * smooth(0, hy, yy)[..., None]

        # capa media: suelo, sendero, troncos cercanos, copa
        img = Image.new("RGB", (W, H))
        mk = Image.new("L", (W, H), 0)
        d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mk)
        d.rectangle([0, hy, W, H], fill=(34, 44, 30))
        dm.rectangle([0, hy, W, H], fill=255)
        # sendero de lodo en perspectiva
        u = np.clip((yy - hy) / (H - hy), 0, 1)
        half = 0.02 * W + 0.30 * W * u
        path = (yy > hy) & (np.abs(xx - vx - np.sin(u * 3) * 0.05 * W) < half)
        floor = np.asarray(img, np.float32).copy()
        mud = np.array([50, 38, 26], np.float32) * (0.7 + 0.5 * vnoise(W, H, 3, 7 + self.seed))[..., None]
        mud *= (0.55 + 0.45 * u)[..., None]          # el sendero se oscurece a lo lejos
        floor[path] = mud[path]
        moss = (yy > hy) & ~path
        floor[moss] *= (0.75 + 0.5 * fbm(W, H, 40 + self.seed, (12, 6, 3)))[moss][..., None]
        img = Image.fromarray(np.clip(floor, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)

        if p.get("huellas", False):
            z = 1.0
            side = 1
            while True:
                y = hy + (H - hy) / z
                if y < hy + 4:
                    break
                s = 4.5 / z
                x = vx + side * 0.06 * W / z + np.sin((y - hy) / (H - hy) * 3) * 0.05 * W
                d.ellipse([x - 1.6 * s, y - s, x + 1.6 * s, y + s], fill=(36, 24, 16))
                for k in (-1.4, -0.5, 0.5, 1.4):
                    d.ellipse([x + k * s - 0.5 * s, y - 2.2 * s, x + k * s + 0.5 * s, y - 1.3 * s], fill=(36, 24, 16))
                z += 0.55
                side = -side

        # troncos cercanos con corteza y raíces
        for x0, w in ((0.06, 0.13), (0.30, 0.06), (0.66, 0.08), (0.86, 0.15), (0.44, 0.035), (0.56, 0.03)):
            X, Wt = x0 * W, w * W
            base = H if w > 0.1 else hy + (H - hy) * (0.25 if w < 0.05 else 0.5)
            pts = [(X, -5), (X + Wt, -5), (X + Wt * 1.05, base), (X + Wt * 1.35, base + 2), (X - Wt * 0.3, base + 2), (X - Wt * 0.05, base)]
            d.polygon(pts, fill=(36, 30, 24))
            dm.polygon(pts, fill=255)
            for k in range(int(Wt / 3)):
                lx = X + rng.uniform(0.1, 0.9) * Wt
                d.line([(lx, rng.uniform(0, base * 0.4)), (lx + rng.uniform(-1, 1), base)], fill=(24, 20, 16))
            d.line([(X + Wt * 0.8, 0), (X + Wt * 0.85, base)], fill=(58, 50, 40))
        # copa
        for _ in range(60):
            cx_, cy_ = rng.uniform(-10, W + 10), rng.uniform(-20, 0.16 * H)
            r = rng.uniform(0.05, 0.12) * W
            d.ellipse([cx_ - r, cy_ - r * 0.7, cx_ + r, cy_ + r * 0.7], fill=(18, 30, 22))
            dm.ellipse([cx_ - r, cy_ - r * 0.7, cx_ + r, cy_ + r * 0.7], fill=255)
        # helechos
        for _ in range(26):
            fx, fy = rng.uniform(0, W), rng.uniform(hy + 4, H)
            if abs(fx - vx) < (0.02 * W + 0.30 * W * (fy - hy) / (H - hy)):
                continue
            s = 2 + 8 * (fy - hy) / (H - hy)
            for a in np.linspace(-1.2, 1.2, 5):
                d.line([(fx, fy), (fx + np.sin(a) * s * 1.6, fy - np.cos(a) * s)], fill=(40, 64, 40), width=1)

        if p.get("orilla", False):
            wy = 0.84 * H
            water = Image.new("RGB", (W, H))
            wd = ImageDraw.Draw(water)
            wd.rectangle([0, wy, W, H], fill=(16, 24, 34))
            for k in range(30):
                ry = rng.uniform(wy + 2, H)
                rx = rng.uniform(0, W)
                wd.line([(rx, ry), (rx + rng.uniform(6, 20), ry)], fill=(40, 52, 66))
            wm = Image.new("L", (W, H), 0)
            ImageDraw.Draw(wm).polygon([(0, wy + 4)] + [(x, wy + 3 * np.sin(x * 0.2)) for x in range(0, W + 8, 8)] + [(W, H), (0, H)], fill=255)
            img.paste(water, (0, 0), wm)
            dm.rectangle([0, wy - 4, W, H], fill=255)
            self.water = np.asarray(wm) > 127
        else:
            self.water = None

        self.mid_alb = np.asarray(img, np.float32).copy()
        self.mid_a = np.asarray(mk) > 127
        if p.get("niebla", True):
            n = fbm(W, H, 60 + self.seed, (32, 16, 8))
            k = smooth(hy - 0.25 * H, hy + 0.05 * H, yy) * (1 - smooth(hy + 0.05 * H, hy + 0.25 * H, yy)) * (0.4 + 0.6 * n)
            self.mid_alb = self.mid_alb * (1 - 0.5 * k[..., None]) + fog * 0.5 * k[..., None]
            self.fog_k = k

        if tarde:
            self.lights.append(Light("ocaso", self.point(vx, hy - 0.12 * H, 0.42 * W, 0.7), (1.0, 0.6, 0.35)))
        else:
            self.lights.append(Light("luna", self.point(0.55 * W, 0.35 * H, 0.7 * W, float(p.get("luna", 1.0))), (0.6, 0.72, 0.95)))

        # primer plano: hojas colgando arriba y pasto abajo
        def fg(dr):
            for k in range(14):
                x = rng.uniform(0, W)
                dr.ellipse([x - 12, -14, x + 14, rng.uniform(4, 0.06 * H)], fill=255)
            for x in range(0, W, 2):
                h = rng.uniform(2, 7)
                dr.line([(x, H), (x + rng.uniform(-2, 2), H - h)], fill=255)
        self.fg_a = self.mask(fg)
        self.fg_alb[:] = (12, 20, 16)

        if p.get("fogata"):
            fx, fy, fw = p["fogata"]
            fogata(self, fx * W, fy * H, fw)

    def animar(self, col, t):
        if self.water is not None:
            m = self.water
            _, yy = self.grid()
            s = np.sin(yy[m] * 0.9 + t * 2.0 + np.cos(yy[m] * 0.3) * 3)
            col[m] = np.where((s > 0.93)[..., None], col[m] * 1.6 + 6, col[m])
