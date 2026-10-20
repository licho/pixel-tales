"""Clase base de los fondos. Cada archivo en scenes/ define `class Escena(Scene)`."""
import numpy as np

from .core import FORMATOS, grid, mask, point_light, pool_light


class Scene:
    """Un fondo reutilizable con 4 capas y luces.

    Tamaño de las capas: self.W x self.H (depende del formato). La cámara ve self.VW x self.VH.
    Para que una escena sirva en vertical y horizontal, usa coordenadas relativas (self.W * 0.5…).

    En `build()` la escena debe llenar:
      sky        color final del cielo / fondo (H, W, 3)
      far        color final de la capa lejana; far_a = alpha booleana
      mid_alb    color base (sin luz) de la capa principal; mid_a, mid_em (emisión: ventanas, focos)
      fg_alb     color base del primer plano; fg_a
      lights     lista de core.Light
      fires      lista de dicts {x0, x1, y, humo, tam} para flamas animadas
    Opcional: `animar(col, t)` modifica el color de la capa principal cada cuadro (agua, etc.).
    Los colores están en RGB 0-255 "reales"; la paleta del estilo se aplica al final.
    """

    parallax = {"sky": 0.12, "far": 0.3, "mid": 0.75, "fg": 1.25}
    formatos = ("horizontal", "vertical")

    def __init__(self, params, style, formato="horizontal"):
        if formato not in self.formatos:
            raise ValueError(f"La escena {type(self).__module__} no soporta formato {formato}")
        self.p = dict(params or {})
        self.style = style
        self.formato = formato
        self.W, self.H, self.VW, self.VH = FORMATOS[formato]
        self.seed = int(self.p.get("semilla", 1))
        z3 = lambda: np.zeros((self.H, self.W, 3), np.float32)
        zb = lambda: np.zeros((self.H, self.W), bool)
        self.sky = z3()
        self.far, self.far_a = z3(), zb()
        self.mid_alb, self.mid_a, self.mid_em = z3(), zb(), z3()
        self.fg_alb, self.fg_a = z3(), zb()
        self.lights, self.fires = [], []

    # atajos con el tamaño correcto
    def grid(self):
        return grid(self.W, self.H)

    def mask(self, fn):
        return mask(fn, self.W, self.H)

    def point(self, x, y, radio, intensidad):
        return point_light(x, y, radio, intensidad, self.W, self.H)

    def pool(self, x, y, rx, ry, intensidad, y_min=0):
        return pool_light(x, y, rx, ry, intensidad, y_min, self.W, self.H)

    def build(self):
        raise NotImplementedError

    def animar(self, col, t):
        pass
