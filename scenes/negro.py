"""Pantalla negra (para inicios, cortes y finales). Úsala con actores 'ojos' o con título.

Parámetros:
  niebla  bool  un poco de niebla muy tenue abajo (default false)
  luz     bool  luz neutra al centro para que se vean bien los actores (default false)
"""
import numpy as np

from pixel_tales.core import Light, fbm
from pixel_tales.scene import Scene


class Escena(Scene):
    formatos = ("horizontal", "vertical", "cuadrado")

    def build(self):
        self.sky[:] = (3, 4, 6)
        if self.p.get("luz", False):
            self.lights.append(Light("luz", self.point(self.W / 2, self.H * 0.6, 0.5 * self.W, 0.75), (1.0, 0.92, 0.85)))
        if self.p.get("niebla", False):
            xx, yy = self.grid()
            n = fbm(self.W, self.H, 5 + self.seed, (32, 16, 8))
            k = np.clip((yy / self.H - 0.6) / 0.4, 0, 1) * n * 0.6
            self.sky += (k * 30)[..., None]
