"""Fotografía antigua (sepia) sobre una mesa, bajo la luz de una lámpara.

Parámetros:
  contenido   'hombre_jaguar' | 'abuelo' | 'bebe' | 'reverso'   (default hombre_jaguar)
  texto       (solo reverso) líneas escritas a mano, separadas por '|'
  superficie  'mesa' | 'lancha'    madera oscura o tablas de lancha (default mesa)
  giro        grados de inclinación de la foto (default -4)
  semilla     int

Puntos útiles (relativos a W x H):
  centro de la foto: (0.5 W, 0.46 H); ancho ~0.70 W
  en 'bebe', los ojos del fondo de la foto quedan en (0.62 W, 0.38 H) -> pon ahí un actor 'ojos' para que brillen
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pixel_tales.core import Light, fbm, vnoise
from pixel_tales.scene import Scene

SEPIA_D, SEPIA_L = np.array([40, 28, 18], np.float32), np.array([226, 204, 160], np.float32)
FONT = Path(__file__).resolve().parent.parent / "fonts" / "PixelifySans-Bold.woff"


def persona(d, x, y, h, sombrero=True, tono=200, ropa=150, pantalon=70):
    """Persona de frente en escala de grises (x, y = pies)."""
    d.rectangle([x - h * .09, y - h * .48, x - h * .02, y], fill=pantalon)
    d.rectangle([x + h * .02, y - h * .48, x + h * .09, y], fill=pantalon)
    d.polygon([(x - h * .15, y - h * .82), (x + h * .15, y - h * .82), (x + h * .12, y - h * .45), (x - h * .12, y - h * .45)], fill=ropa)
    d.line([(x - h * .15, y - h * .80), (x - h * .19, y - h * .50)], fill=ropa, width=max(1, int(h * .06)))
    d.line([(x + h * .15, y - h * .80), (x + h * .19, y - h * .50)], fill=ropa, width=max(1, int(h * .06)))
    d.ellipse([x - h * .075, y - h * .97, x + h * .075, y - h * .81], fill=tono)
    d.point([(x - h * .03, y - h * .90), (x + h * .03, y - h * .90)], fill=30)
    if sombrero:
        d.ellipse([x - h * .17, y - h * .97, x + h * .17, y - h * .92], fill=60)
        d.rectangle([x - h * .07, y - h * 1.05, x + h * .07, y - h * .95], fill=60)


def jaguar_foto(d, x, y, s, ojos=True):
    """Jaguar entre árboles, de perfil, en escala de grises (x, y = patas)."""
    d.ellipse([x - 14 * s, y - 13 * s, x + 12 * s, y - 3 * s], fill=175)
    for dx in (-10, -6, 6, 10):
        d.rectangle([x + dx * s - 1, y - 6 * s, x + dx * s + 1, y], fill=100)
    d.ellipse([x - 21 * s, y - 16 * s, x - 11 * s, y - 7 * s], fill=185)
    d.polygon([(x - 19 * s, y - 15 * s), (x - 18 * s, y - 19 * s), (x - 16 * s, y - 15 * s)], fill=110)
    d.line([(x + 12 * s, y - 9 * s), (x + 20 * s, y - 14 * s)], fill=100, width=max(1, int(s * 2)))
    rng = np.random.default_rng(int(x * 3))
    for _ in range(int(14 * s)):
        sx, sy = rng.uniform(x - 12 * s, x + 10 * s), rng.uniform(y - 12 * s, y - 4 * s)
        d.point((sx, sy), fill=40)
    if ojos:
        d.point([(x - 18 * s, y - 12 * s), (x - 15 * s, y - 12 * s)], fill=245)


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.2, "far": 0.4, "mid": 0.7, "fg": 1.0}

    def build(self):
        W, H = self.W, self.H
        xx, yy = self.grid()
        p = self.p
        rng = np.random.default_rng(10 + self.seed)

        # superficie de madera
        lancha = p.get("superficie", "mesa") == "lancha"
        base = np.array([96, 72, 50] if lancha else [70, 46, 30], np.float32)
        tabla = 0.11 * H if lancha else 0.16 * H
        idx = np.floor(yy / tabla)
        grain = vnoise(W, H, 3, 4 + self.seed) * 0.5 + np.sin(xx * 0.08 + idx * 7 + vnoise(W, H, 12, 5) * 6) * 0.15
        wood = base * (0.75 + 0.35 * grain + 0.1 * ((idx * 3.7) % 1))[..., None]
        wood[(yy % tabla) < (2 if lancha else 1)] *= 0.35
        self.mid_alb = wood
        self.mid_a[:] = True

        # foto
        pw = int(0.70 * min(W, H * 1.2))
        ph = int(pw * 0.78)
        photo = self._foto(pw, ph, p.get("contenido", "hombre_jaguar"), p.get("texto", ""), rng)
        photo = photo.rotate(p.get("giro", -4), resample=Image.NEAREST, expand=True)
        cx, cy = int(0.5 * W), int(0.46 * H)
        ox, oy = cx - photo.width // 2, cy - photo.height // 2
        sh = Image.new("L", photo.size, 0)
        sh.paste(255, (0, 0), photo.getchannel("A"))
        alb = Image.fromarray(np.clip(self.mid_alb, 0, 255).astype(np.uint8))
        alb.paste((10, 6, 4), (ox + 3, oy + 4), sh)                # sombra
        alb.paste(photo.convert("RGB"), (ox, oy), photo.getchannel("A"))
        # otras fotos asomando por los bordes
        for k in range(3):
            q = self._foto(int(pw * 0.6), int(pw * 0.46), "hombre_jaguar", "", rng).rotate(rng.uniform(-25, 25), expand=True)
            qx = int(rng.choice([-0.35, 0.7]) * W + rng.uniform(-10, 10))
            qy = int(rng.uniform(0.70, 0.9) * H)
            alb.paste((10, 6, 4), (qx + 3, qy + 4), q.getchannel("A"))
            alb.paste(q.convert("RGB"), (qx, qy), q.getchannel("A"))
        self.mid_alb = np.asarray(alb, np.float32).copy()

        # luz de lámpara (cálida) desde arriba
        self.lights.append(Light("lampara", self.point(0.5 * W, 0.42 * H, 0.45 * min(W, H), 1.5), (1.0, 0.78, 0.5)))
        self.sky[:] = (4, 4, 6)

    def _foto(self, w, h, contenido, texto, rng):
        """Devuelve una foto vieja RGBA (borde crema, imagen sepia, manchas)."""
        b = max(3, w // 18)
        im = Image.new("L", (w - 2 * b, h - 2 * b), 0)
        d = ImageDraw.Draw(im)
        iw, ih = im.size
        if contenido == "reverso":
            paper = Image.new("RGB", (w, h), (214, 198, 160))
            pd = ImageDraw.Draw(paper)
            pd.fontmode = "1"
            f = ImageFont.truetype(str(FONT), max(8, h // 9))
            for i, line in enumerate((texto or "").split("|")):
                pd.text((w * 0.1, h * 0.2 + i * h * 0.16), line.strip(), font=f, fill=(60, 40, 30))
            arr = np.asarray(paper, np.float32).copy()
        else:
            y = np.linspace(0, 1, ih)[:, None]
            sky = (215 - 45 * y) * np.ones((1, iw))
            im = Image.fromarray(sky.astype(np.uint8))
            d = ImageDraw.Draw(im)
            ground = int(ih * 0.82)
            d.rectangle([0, ground, iw, ih], fill=90)
            for k in range(9):                                 # árboles
                tx = rng.uniform(0, iw)
                tw = rng.uniform(0.03, 0.07) * iw
                d.rectangle([tx, ih * 0.05, tx + tw, ground], fill=int(rng.uniform(120, 150)))
                d.ellipse([tx - tw * 2, ih * 0.0, tx + tw * 3, ih * 0.35], fill=int(rng.uniform(125, 155)))
            if contenido in ("hombre_jaguar", "abuelo"):
                persona(d, iw * 0.38, ground + 2, ih * 0.72, sombrero=True, tono=225 if contenido == "abuelo" else 210, ropa=60, pantalon=30)
                jaguar_foto(d, iw * 0.80, ground - ih * 0.06, ih / 70)
            elif contenido == "bebe":
                persona(d, iw * 0.40, ground + 2, ih * 0.74, sombrero=False, tono=205, ropa=50, pantalon=25)
                d.ellipse([iw * 0.40 - ih * .09, ih * 0.42, iw * 0.40 + ih * .09, ih * 0.54], fill=235)   # bebé en brazos
                d.ellipse([iw * 0.40 + ih * .02, ih * 0.43, iw * 0.40 + ih * .08, ih * 0.48], fill=205)
                d.rectangle([iw * 0.62, ih * 0.25, iw * 0.80, ih * 0.6], fill=40)                           # oscuridad
            n = vnoise(iw, ih, 6, int(rng.integers(0, 999))) - 0.5
            g = np.asarray(im, np.float32) + n * 30
            yy, xx = np.mgrid[0:ih, 0:iw]
            vig = 1 - 0.5 * (((xx - iw / 2) / (iw / 2)) ** 2 + ((yy - ih / 2) / (ih / 2)) ** 2)
            g = np.clip(g * np.clip(vig, 0.4, 1), 0, 255) / 255
            sep = SEPIA_D + (SEPIA_L - SEPIA_D) * g[..., None]
            arr = np.zeros((h, w, 3), np.float32)
            arr[:] = (220, 206, 172)                           # borde
            arr[b:b + ih, b:b + iw] = sep
        # manchas y rayones
        st = fbm(w, h, int(rng.integers(0, 999)), (16, 8, 4))
        arr *= (1 - 0.22 * np.clip((st - 0.66) * 5, 0, 1))[..., None]
        for _ in range(4):
            x0 = rng.uniform(0, w)
            arr[:, int(x0) % w] *= 0.85
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        # esquina doblada
        dd = ImageDraw.Draw(out)
        c = max(3, w // 12)
        dd.polygon([(w - c, 0), (w, 0), (w, c)], fill=(0, 0, 0, 0))
        return out
