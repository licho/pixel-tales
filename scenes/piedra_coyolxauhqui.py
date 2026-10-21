"""La gran piedra de Coyolxauhqui (relieve de la diosa desmembrada, 3.4 m de diámetro).

Parámetros:
  vista     'cenital' (la piedra vista desde arriba, llena el cuadro) | 'escalinata' (al pie de la
            escalinata del Templo Mayor, con los dos templos arriba y braseros)   (default cenital)
  luz       'lamparas' (blanca, 1978) | 'antorchas'   (default antorchas)
  semilla   int

Puntos útiles (vertical 256x384):
  cenital: centro de la piedra (0.5 W, 0.5 H)
  escalinata: cima de la escalera (0.5 W, 0.22 H) para ojos o figuras; piedra en (0.5 W, 0.83 H)
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from pixel_tales.core import Light, fbm
from pixel_tales.pintura import antorcha, brasero, roca
from pixel_tales.scene import Scene

PIEDRA = np.array([120, 108, 92], np.float32)


def relieve(n, seed=0):
    """Pinta el relieve circular (n x n). Devuelve (rgb, alpha)."""
    def mk(fn):
        im = Image.new("L", (n, n), 0)
        fn(ImageDraw.Draw(im))
        return np.asarray(im, np.float32) / 255

    c, R = n / 2, n / 2 - 1
    s = n / 100
    P = lambda x, y: (c + x * s, c + y * s)
    disco = mk(lambda d: d.ellipse([1, 1, n - 2, n - 2], fill=255))
    figura = mk(lambda d: (
        d.ellipse([*P(-32, -40), *P(-6, -14)], fill=255),                       # cabeza
        d.polygon([P(-30, -46), P(-4, -44), P(-10, -36), P(-30, -38)], fill=255),  # tocado
        d.polygon([P(-8, -12), P(14, -16), P(18, 12), P(-4, 16)], fill=255),       # torso
        d.line([P(-10, -10), P(-30, 4), P(-36, 22)], fill=255, width=int(7 * s)),  # brazo
        d.line([P(16, -12), P(34, -24), P(40, -8)], fill=255, width=int(7 * s)),   # brazo
        d.line([P(-2, 18), P(-16, 34), P(-6, 44)], fill=255, width=int(8 * s)),    # pierna
        d.line([P(16, 14), P(32, 26), P(26, 42)], fill=255, width=int(8 * s)),     # pierna
        d.ellipse([*P(-40, 18), *P(-30, 28)], fill=255), d.ellipse([*P(36, -14), *P(46, -4)], fill=255),
        d.ellipse([*P(-12, 40), *P(0, 48)], fill=255), d.ellipse([*P(20, 38), *P(32, 46)], fill=255)))
    detalle = mk(lambda d: (
        d.ellipse([*P(-14, -30), *P(-10, -26)], fill=255),                      # cascabel en la mejilla
        d.ellipse([*P(-18, -24), *P(-14, -20)], fill=255),
        d.ellipse([*P(-2, -4), *P(8, 6)], fill=255),                              # calavera en la cintura
        d.line([P(-6, 10), P(16, 6)], fill=255, width=int(2 * s)),                # cinturón de serpientes
        d.arc([*P(-34, -8), *P(-24, 2)], 0, 300, fill=255, width=int(2 * s)),
        d.arc([*P(26, 26), *P(36, 36)], 0, 300, fill=255, width=int(2 * s))))
    h = np.asarray(Image.fromarray((figura * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6 * s)), np.float32) / 255 * 6
    h += detalle * 2 + disco * 1.5
    h += (fbm(n, n, 300 + seed, (12, 6, 3)) - 0.5) * 1.4
    gy, gx = np.gradient(h)
    L = np.array([-0.5, -0.6, 0.62])
    nrm = np.stack([-gx, -gy, np.ones_like(h)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    lam = np.clip(nrm @ L / np.linalg.norm(L), 0, 1)
    rgb = PIEDRA * (0.45 + 0.75 * lam)[..., None]
    borde = (disco > 0.5) & (np.hypot(*(np.mgrid[0:n, 0:n] - c)) > R - 3 * s)
    rgb[borde] *= 0.8
    rgb *= (0.92 + 0.15 * fbm(n, n, 301 + seed, (20, 8)))[..., None]
    return rgb, disco > 0.5


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.1, "far": 0.25, "mid": 0.5, "fg": 1.1}

    def build(self):
        W, H = self.W, self.H
        p = self.p
        xx, yy = self.grid()
        vista = p.get("vista", "cenital")
        lamparas = p.get("luz", "antorchas") == "lamparas"
        self.sky[:] = (6, 5, 7)
        alb = roca(self, (70, 62, 54), self.seed, 0.6) * 0.8
        a = np.ones((H, W), bool)
        if vista == "cenital":
            n = int(min(W, H) * 0.92)
            rgb, m = relieve(n, self.seed)
            x0, y0 = int(W / 2 - n / 2), int(H / 2 - n / 2)
            sub = alb[y0:y0 + n, x0:x0 + n]
            sub[m] = rgb[m]
            self.mid_alb, self.mid_a = alb, a
            if lamparas:
                for k, (lx, ly) in enumerate(((0.15, 0.2), (0.85, 0.25), (0.5, 0.92))):
                    self.lights.append(Light(f"lampara{k}", self.point(lx * W, ly * H, 0.6 * H, 0.3), (1.0, 0.96, 0.85)))
            else:
                for k, (lx, ly) in enumerate(((0.12, 0.12), (0.88, 0.12), (0.12, 0.88), (0.88, 0.88))):
                    antorcha(self, lx * W, ly * H, tam=1.4, radio=110, intensidad=1.0)
            alb = self.mid_alb
        else:
            # escalinata del Templo Mayor que sube hacia el fondo
            top, base = 0.22 * H, 0.66 * H
            for k in range(28):
                v0, v1 = k / 28, (k + 1) / 28
                ya, yb = top + (base - top) * v0, top + (base - top) * v1
                wa, wb = 0.18 * W + 0.32 * W * v0, 0.18 * W + 0.32 * W * v1
                c = 120 + 30 * (k % 2)
                im_m = self.mask(lambda d, ya=ya, yb=yb, wa=wa, wb=wb: d.polygon(
                    [(W / 2 - wa, ya), (W / 2 + wa, ya), (W / 2 + wb, yb), (W / 2 - wb, yb)], fill=255))
                alb[im_m] = np.array([c, c * 0.92, c * 0.8], np.float32) * (0.7 + 0.3 * v0)
            # alfardas (rampas laterales) con cabezas de serpiente al pie
            for s in (-1, 1):
                m = self.mask(lambda d, s=s: d.polygon([(W / 2 + s * 0.18 * W, top), (W / 2 + s * 0.24 * W, top),
                                                        (W / 2 + s * 0.58 * W, base), (W / 2 + s * 0.50 * W, base)], fill=255))
                alb[m] = (96, 88, 76)
                m = self.mask(lambda d, s=s: d.ellipse([W / 2 + s * 0.54 * W - 10, base - 8, W / 2 + s * 0.54 * W + 10, base + 8], fill=255))
                alb[m] = (130, 118, 96)
            # los dos templos arriba (Tláloc azul, Huitzilopochtli rojo)
            for s, col in ((-1, (60, 90, 130)), (1, (150, 40, 32))):
                m = self.mask(lambda d, s=s: d.rectangle([W / 2 + s * 0.2 * W - 22, top - 44, W / 2 + s * 0.2 * W + 22, top], fill=255))
                alb[m] = col
                m = self.mask(lambda d, s=s: d.rectangle([W / 2 + s * 0.2 * W - 8, top - 26, W / 2 + s * 0.2 * W + 8, top], fill=255))
                alb[m] = (14, 10, 10)
                m = self.mask(lambda d, s=s: d.polygon([(W / 2 + s * 0.2 * W - 26, top - 44), (W / 2 + s * 0.2 * W + 26, top - 44),
                                                        (W / 2 + s * 0.2 * W, top - 64)], fill=255))
                alb[m] = np.array(col, np.float32) * 0.7
            a = yy > top - 66
            # piedra al pie, vista en perspectiva (elipse aplastada)
            n = int(W * 0.95)
            rgb, m = relieve(n, self.seed)
            hh = int(n * 0.36)
            rgb_s = np.asarray(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((n, hh), Image.NEAREST), np.float32)
            m_s = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((n, hh), Image.NEAREST)) > 127
            x0, y0 = int(W / 2 - n / 2), int(0.83 * H - hh / 2)
            x0c, x1c = max(0, x0), min(W, x0 + n)
            sub = alb[y0:y0 + hh, x0c:x1c]
            mm = m_s[:, x0c - x0:x1c - x0]
            sub[mm] = rgb_s[:, x0c - x0:x1c - x0][mm]
            self.mid_alb, self.mid_a = alb, a
            for s in (-1, 1):
                brasero(self, W / 2 + s * 0.40 * W, 0.68 * H, tam=1.3, intensidad=1.2)
                antorcha(self, W / 2 + s * 0.22 * W, top - 6, tam=0.8, radio=40, intensidad=0.8)
            alb = self.mid_alb
            self.sky[:] = (8, 6, 12)
            ys = (np.random.default_rng(5).random((H, W)) < 0.003) & (yy < top - 70)
            self.sky[ys] = (180, 170, 160)
        self.mid_alb, self.mid_a = alb, self.mid_a | a
