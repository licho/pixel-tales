"""Genera los sprites de la serie de leyendas (Xibalbá) en sprites/xibalba/.

  hun_came, vucub_came   señores supremos sentados (esqueléticos, tocado de plumas)
  senor_a, senor_b       señores de pie (capa larga, máscara de hueso, bastón)
  gemelo                 jugador de pelota visto de espaldas
  sombra                 figura agazapada con cuchillo de obsidiana

Colores base sin luz; los ojos se marcan como 'brillos' en el .json (brillan solos).
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "sprites" / "xibalba"
OUT.mkdir(parents=True, exist_ok=True)

HUESO, HUESO_S, HUECO = (212, 200, 168), (150, 138, 112), (14, 10, 12)
JADE, JADE_D = (60, 130, 90), (30, 70, 50)
ROJO, ROJO_D = (170, 40, 30), (90, 18, 16)
OCRE = (190, 140, 60)
OJO = [255, 60, 36]


def save(name, im, ancla, brillos=(), notas=""):
    im.save(OUT / f"{name}.png")
    (OUT / f"{name}.json").write_text(json.dumps(
        {"ancla": list(ancla), "brillos": [{"pos": list(b), "color": OJO} for b in brillos], "notas": notas},
        indent=2, ensure_ascii=False))
    print("Sprite:", name, im.size)


def plumas(d, cx, cy, radio, color, oscuro, n=9, a0=-160, a1=-20):
    for k in range(n):
        a = math.radians(a0 + (a1 - a0) * k / (n - 1))
        r = radio * (0.85 + 0.15 * math.sin(k * 1.7))
        tip = (cx + r * math.cos(a), cy + r * math.sin(a))
        perp = (math.cos(a + math.pi / 2) * 2.2, math.sin(a + math.pi / 2) * 2.2)
        d.polygon([(cx - perp[0], cy - perp[1]), tip, (cx + perp[0], cy + perp[1])], fill=color if k % 2 else oscuro)


def senor_sentado(name, pluma, pluma_d, capa):
    W, H = 52, 66
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fx, fy = 26, 65
    # capa detrás de los hombros
    d.polygon([(fx - 14, fy - 42), (fx + 14, fy - 42), (fx + 19, fy - 12), (fx - 19, fy - 12)], fill=capa)
    # tocado: abanico de plumas
    plumas(d, fx, fy - 52, 20, pluma, pluma_d)
    # espinillas y pies
    for s in (-1, 1):
        d.rectangle([fx + s * 7 - 1, fy - 15, fx + s * 7 + 1, fy - 2], fill=HUESO)
        d.rectangle([fx + s * 7 - 3, fy - 2, fx + s * 7 + 3, fy], fill=HUESO_S)
        d.ellipse([fx + s * 7 - 3, fy - 19, fx + s * 7 + 3, fy - 13], fill=HUESO)      # rodillas
    # taparrabo
    d.polygon([(fx - 5, fy - 20), (fx + 5, fy - 20), (fx + 3, fy - 6), (fx - 3, fy - 6)], fill=pluma_d)
    # caja torácica
    d.ellipse([fx - 9, fy - 41, fx + 9, fy - 20], fill=HUESO)
    for k in range(5):
        y = fy - 37 + k * 3.5
        d.line([(fx - 7, y), (fx + 7, y)], fill=HUESO_S)
    d.line([(fx, fy - 40), (fx, fy - 20)], fill=HUESO_S)
    # brazos sobre las rodillas
    for s in (-1, 1):
        d.line([(fx + s * 10, fy - 39), (fx + s * 13, fy - 27)], fill=HUESO, width=2)
        d.line([(fx + s * 13, fy - 27), (fx + s * 8, fy - 19)], fill=HUESO, width=2)
        d.ellipse([fx + s * 8 - 2, fy - 21, fx + s * 8 + 2, fy - 17], fill=HUESO_S)
    # collar de jade
    for k in range(7):
        a = math.pi * (0.15 + 0.7 * k / 6)
        bx, by = fx + 9 * math.cos(a), fy - 42 + 4 * math.sin(a)
        d.ellipse([bx - 1.5, by - 1.5, bx + 1.5, by + 1.5], fill=JADE)
    # cráneo
    d.ellipse([fx - 7, fy - 56, fx + 7, fy - 42], fill=HUESO)
    d.rectangle([fx - 5, fy - 46, fx + 5, fy - 41], fill=HUESO)
    d.rectangle([fx - 5, fy - 51, fx - 2, fy - 48], fill=HUECO)
    d.rectangle([fx + 2, fy - 51, fx + 5, fy - 48], fill=HUECO)
    d.point([(fx, fy - 46)], fill=HUECO)
    for k in range(-4, 5, 2):
        d.line([(fx + k, fy - 44), (fx + k, fy - 41)], fill=HUECO)
    # banda del tocado y orejeras
    d.rectangle([fx - 8, fy - 57, fx + 8, fy - 54], fill=OCRE)
    d.ellipse([fx - 2, fy - 59, fx + 2, fy - 55], fill=JADE)
    for s in (-1, 1):
        d.ellipse([fx + s * 8 - 2, fy - 50, fx + s * 8 + 2, fy - 46], fill=OCRE)
    save(name, im, (fx, fy), [(fx - 4, fy - 50), (fx + 3, fy - 50)], "señor sentado; pies en el ancla")


def senor_pie(name, capa, capa_d, baston=True, pluma=ROJO):
    W, H = 46, 80
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fx, fy = 22, 79
    plumas(d, fx, fy - 64, 14, pluma, ROJO_D, 7, -150, -30)
    # capa larga
    d.polygon([(fx - 9, fy - 58), (fx + 9, fy - 58), (fx + 15, fy), (fx - 15, fy)], fill=capa)
    d.polygon([(fx - 3, fy - 56), (fx + 3, fy - 56), (fx + 2, fy), (fx - 2, fy)], fill=capa_d)
    for k in range(4):
        d.line([(fx - 15 + k * 8, fy), (fx - 11 + k * 6, fy - 40)], fill=capa_d)
    # brazo huesudo con bastón o garras
    if baston:
        d.line([(fx + 8, fy - 54), (fx + 15, fy - 40)], fill=HUESO, width=2)
        d.line([(fx + 17, fy - 62), (fx + 17, fy)], fill=(92, 64, 40), width=2)
        d.ellipse([fx + 14, fy - 67, fx + 20, fy - 61], fill=HUESO)
        d.ellipse([fx + 14, fy - 42, fx + 18, fy - 38], fill=HUESO_S)
    else:
        for s in (-1, 1):
            d.line([(fx + s * 8, fy - 54), (fx + s * 16, fy - 44)], fill=HUESO, width=2)
            for k in range(3):
                d.line([(fx + s * 16, fy - 44), (fx + s * (17 + k), fy - 40 + k)], fill=HUESO)
    # máscara/cráneo con colmillos
    d.ellipse([fx - 7, fy - 70, fx + 7, fy - 55], fill=HUESO)
    d.rectangle([fx - 5, fy - 66, fx - 2, fy - 63], fill=HUECO)
    d.rectangle([fx + 2, fy - 66, fx + 5, fy - 63], fill=HUECO)
    d.polygon([(fx - 4, fy - 58), (fx - 3, fy - 53), (fx - 2, fy - 58)], fill=HUESO)
    d.polygon([(fx + 2, fy - 58), (fx + 3, fy - 53), (fx + 4, fy - 58)], fill=HUESO)
    d.rectangle([fx - 8, fy - 71, fx + 8, fy - 68], fill=OCRE)
    save(name, im, (fx, fy), [(fx - 4, fy - 65), (fx + 3, fy - 65)], "señor de pie con capa")


def gemelo(name, banda=JADE):
    W, H = 34, 90
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fx, fy = 17, 89
    PIEL, PIEL_D, PELO = (128, 80, 50), (96, 58, 36), (16, 12, 12)
    for s in (-1, 1):
        d.polygon([(fx + s * 2, fy - 40), (fx + s * 8, fy - 40), (fx + s * 7, fy - 2), (fx + s * 3, fy - 2)], fill=PIEL_D)
        d.rectangle([min(fx + s * 2, fx + s * 8), fy - 22, max(fx + s * 2, fx + s * 8), fy - 17], fill=(200, 188, 160))  # rodillera
        d.rectangle([min(fx + s * 3, fx + s * 8), fy - 2, max(fx + s * 3, fx + s * 8), fy], fill=(70, 50, 30))
    # protector de cadera y yugo
    d.polygon([(fx - 10, fy - 46), (fx + 10, fy - 46), (fx + 9, fy - 36), (fx - 9, fy - 36)], fill=(200, 188, 160))
    d.rectangle([fx - 11, fy - 50, fx + 11, fy - 45], fill=(110, 70, 34))
    d.line([(fx - 11, fy - 48), (fx + 11, fy - 48)], fill=(170, 120, 50))
    # espalda y brazos
    d.polygon([(fx - 10, fy - 72), (fx + 10, fy - 72), (fx + 8, fy - 50), (fx - 8, fy - 50)], fill=PIEL)
    d.line([(fx, fy - 70), (fx, fy - 52)], fill=PIEL_D)
    for s in (-1, 1):
        d.polygon([(fx + s * 10, fy - 72), (fx + s * 14, fy - 66), (fx + s * 13, fy - 46), (fx + s * 10, fy - 46),
                   (fx + s * 10, fy - 64)], fill=PIEL)
        d.ellipse([fx + s * 12 - 2, fy - 47, fx + s * 12 + 2, fy - 43], fill=PIEL_D)
    # cabeza de espaldas: cabello largo amarrado y banda con pluma
    d.ellipse([fx - 7, fy - 86, fx + 7, fy - 72], fill=PELO)
    d.polygon([(fx - 3, fy - 74), (fx + 3, fy - 74), (fx + 2, fy - 60), (fx - 2, fy - 60)], fill=PELO)
    d.rectangle([fx - 7, fy - 82, fx + 7, fy - 80], fill=banda)
    d.polygon([(fx + 5, fy - 82), (fx + 9, fy - 89), (fx + 7, fy - 81)], fill=banda)
    save(name, im, (fx, fy), [], "jugador de pelota de espaldas; usar espejo para el hermano")


def sombra(name):
    W, H = 44, 42
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fx, fy = 20, 41
    C, C2 = (18, 12, 14), (28, 20, 22)
    d.polygon([(fx - 14, fy), (fx - 12, fy - 18), (fx - 4, fy - 30), (fx + 8, fy - 28), (fx + 12, fy - 14),
               (fx + 14, fy)], fill=C)
    d.ellipse([fx - 6, fy - 38, fx + 6, fy - 26], fill=C2)
    # brazo levantado con cuchillo de obsidiana
    d.line([(fx + 8, fy - 26), (fx + 16, fy - 34)], fill=C2, width=3)
    d.polygon([(fx + 15, fy - 35), (fx + 24, fy - 41), (fx + 18, fy - 32)], fill=(8, 8, 12))
    d.line([(fx + 16, fy - 35), (fx + 23, fy - 40)], fill=(60, 64, 70))
    save(name, im, (fx, fy), [(fx - 3, fy - 33), (fx + 2, fy - 33), (fx + 22, fy - 40)],
         "figura agazapada en la oscuridad; ojos y filo brillan")


if __name__ == "__main__":
    senor_sentado("hun_came", JADE, JADE_D, (60, 20, 22))
    senor_sentado("vucub_came", ROJO, ROJO_D, (34, 26, 30))
    senor_pie("senor_a", (54, 24, 22), (34, 14, 14), baston=True, pluma=ROJO)
    senor_pie("senor_b", (30, 40, 34), (18, 26, 22), baston=False, pluma=JADE)
    gemelo("gemelo", JADE)
    sombra("sombra")
