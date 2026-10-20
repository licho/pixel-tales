"""Usa una imagen como fondo (por ejemplo, una ilustración generada con IA) y la pasa por la paleta y el
tramado del estilo, para que combine con el resto del canal. Encima funcionan lluvia, relámpago, ceniza,
cámara, zoom, ojos, sprites, etc.

Parámetros:
  archivo   ruta dentro del repo (ej. fondos/oceano/cthulhu_gemini.jpg)
  foco      [x, y] relativos: qué parte de la imagen conservar al recortar (default [0.5, 0.5])
  brillo    multiplica la luz de la imagen (default 1.0)

Limitación: es una sola capa, así que no tiene parallax por profundidad ni olas animadas.
"""
from pathlib import Path

import numpy as np
from PIL import Image

from pixel_tales.scene import Scene

ROOT = Path(__file__).resolve().parent.parent


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")
    parallax = {"sky": 0.0, "far": 0.0, "mid": 0.5, "fg": 1.0}

    def build(self):
        W, H = self.W, self.H
        im = Image.open(ROOT / self.p["archivo"]).convert("RGB")
        fx, fy = self.p.get("foco", [0.5, 0.5])
        s = max(W / im.width, H / im.height)
        nw, nh = int(round(im.width * s)), int(round(im.height * s))
        im = im.resize((nw, nh), Image.LANCZOS)
        x0 = int(min(max(fx * nw - W / 2, 0), nw - W))
        y0 = int(min(max(fy * nh - H / 2, 0), nh - H))
        arr = np.asarray(im.crop((x0, y0, x0 + W, y0 + H)), np.float32)
        self.mid_alb = arr / self.style.ambiente[None, None, :] * float(self.p.get("brillo", 1.0))
        self.mid_a[:] = True
