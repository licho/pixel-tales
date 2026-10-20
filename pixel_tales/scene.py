"""Clase base de los fondos. Cada archivo en scenes/ define `class Escena(Scene)`."""
import numpy as np

from .core import LW, LH


class Scene:
    """Un fondo reutilizable con 4 capas y luces.

    En `build()` la escena debe llenar:
      sky        color final del cielo (LH, LW, 3)
      far        color final de la capa lejana; far_a = alpha booleana
      mid_alb    color base (sin luz) de la capa principal; mid_a, mid_em (emisión: ventanas, focos)
      fg_alb     color base del primer plano; fg_a
      lights     lista de core.Light
      fires      lista de dicts {x0, x1, y, humo} para flamas animadas
      suelo(x)   (opcional) devuelve la 'y' del piso en esa x para colocar actores
    Los colores están en RGB 0-255 "reales"; la paleta del estilo se aplica al final.
    """

    parallax = {"sky": 0.12, "far": 0.3, "mid": 0.75, "fg": 1.25}

    def __init__(self, params, style):
        self.p = dict(params or {})
        self.style = style
        self.seed = int(self.p.get("semilla", 1))
        z3 = lambda: np.zeros((LH, LW, 3), np.float32)
        zb = lambda: np.zeros((LH, LW), bool)
        self.sky = z3()
        self.far, self.far_a = z3(), zb()
        self.mid_alb, self.mid_a, self.mid_em = z3(), zb(), z3()
        self.fg_alb, self.fg_a = z3(), zb()
        self.lights, self.fires = [], []

    def build(self):
        raise NotImplementedError
