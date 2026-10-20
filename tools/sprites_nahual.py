"""Genera los sprites de la serie de nahuales en sprites/nahual/.

  chico_camara, chico_escritorio, chico_tendido, chico_doble, doble_cuatro_patas,
  jaguar, jaguar_rostro, nahual_silueta, lancha, lancha_aerea, sombra_agua
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "sprites" / "nahual"
OUT.mkdir(parents=True, exist_ok=True)

PIEL, PIEL_D = (156, 108, 76), (112, 76, 52)
PELO = (22, 16, 14)
SUD, SUD_D = (48, 70, 56), (32, 48, 38)          # sudadera verde
JEAN, JEAN_D = (44, 58, 84), (30, 40, 60)
TENIS = (210, 206, 196)
JAG, JAG_L, JAG_D = (200, 140, 56), (232, 200, 140), (40, 26, 16)
ORO = [240, 200, 70]


def save(name, im, ancla, brillos=(), notas="", color=ORO):
    im.save(OUT / f"{name}.png")
    (OUT / f"{name}.json").write_text(json.dumps(
        {"ancla": list(ancla), "brillos": [{"pos": list(b), "color": color} for b in brillos], "notas": notas},
        indent=2, ensure_ascii=False))
    print("Sprite:", name, im.size)


def canvas(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def rosetas(d, box, n, rng, s=1.0):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = s * rng.uniform(1.0, 1.8)
        d.ellipse([x - r, y - r, x + r, y + r], outline=JAG_D)
        d.point((x, y), fill=(150, 96, 34))


def chico_camara():
    im, d = canvas(34, 66)
    fx, fy = 14, 65
    d.polygon([(fx - 5, fy - 30), (fx, fy - 30), (fx - 1, fy - 2), (fx - 6, fy - 2)], fill=JEAN_D)
    d.polygon([(fx + 1, fy - 30), (fx + 6, fy - 30), (fx + 8, fy - 2), (fx + 3, fy - 2)], fill=JEAN)
    d.rectangle([fx - 7, fy - 3, fx - 1, fy], fill=TENIS)
    d.rectangle([fx + 3, fy - 3, fx + 10, fy], fill=TENIS)
    d.polygon([(fx - 7, fy - 52), (fx + 6, fy - 52), (fx + 8, fy - 30), (fx - 8, fy - 30)], fill=SUD)
    d.rounded_rectangle([fx - 11, fy - 52, fx - 5, fy - 36], 2, fill=(70, 50, 34))                 # mochila
    d.ellipse([fx - 5, fy - 63, fx + 6, fy - 52], fill=PIEL)
    d.pieslice([fx - 6, fy - 64, fx + 6, fy - 54], 180, 360, fill=PELO)
    d.rectangle([fx - 6, fy - 59, fx - 3, fy - 55], fill=PELO)
    d.polygon([(fx + 2, fy - 50), (fx + 6, fy - 51), (fx + 13, fy - 56), (fx + 11, fy - 59), (fx + 4, fy - 55)], fill=SUD_D)  # brazos
    d.rectangle([fx + 8, fy - 62, fx + 18, fy - 55], fill=(24, 24, 26))                           # cámara
    d.rectangle([fx + 18, fy - 61, fx + 21, fy - 56], fill=(50, 52, 56))
    d.point((fx + 20, fy - 59), fill=(120, 140, 170))
    d.point((fx + 9, fy - 61), fill=(200, 40, 30))
    save("chico_camara", im, (fx, fy), [], "joven investigador grabando con cámara de video, mira a la derecha")


def chico_escritorio():
    im, d = canvas(40, 50)
    fx, fy = 20, 49
    d.rectangle([fx - 12, fy - 22, fx + 12, fy - 19], fill=(60, 40, 26))                          # respaldo
    d.line([(fx - 10, fy - 19), (fx - 10, fy)], fill=(50, 34, 22), width=2)
    d.line([(fx + 10, fy - 19), (fx + 10, fy)], fill=(50, 34, 22), width=2)
    d.polygon([(fx - 11, fy - 38), (fx + 11, fy - 38), (fx + 12, fy - 18), (fx - 12, fy - 18)], fill=SUD)
    d.line([(fx, fy - 37), (fx, fy - 20)], fill=SUD_D)
    d.ellipse([fx - 6, fy - 49, fx + 6, fy - 37], fill=PELO)
    d.ellipse([fx - 7, fy - 45, fx - 5, fy - 41], fill=PIEL_D)
    d.ellipse([fx + 5, fy - 45, fx + 7, fy - 41], fill=PIEL_D)
    for s in (-1, 1):
        d.line([(fx + s * 11, fy - 36), (fx + s * 14, fy - 26)], fill=SUD, width=3)
    save("chico_escritorio", im, (fx, fy), [], "de espaldas, sentado frente al escritorio")


def chico_tendido():
    im, d = canvas(60, 16)
    fy = 15
    d.rectangle([2, fy - 6, 14, fy - 2], fill=JEAN)                     # piernas
    d.rectangle([0, fy - 7, 3, fy - 1], fill=TENIS)
    d.rectangle([14, fy - 9, 38, fy - 1], fill=SUD)
    d.ellipse([38, fy - 11, 49, fy - 1], fill=PIEL)
    d.pieslice([40, fy - 12, 51, fy - 1], 270, 450, fill=PELO)
    d.line([(20, fy - 9), (30, fy - 11)], fill=SUD_D, width=2)          # brazo sobre el pecho
    save("chico_tendido", im, (30, fy), [], "acostado boca arriba (inconsciente), cabeza a la derecha")


def chico_doble():
    im, d = canvas(28, 66)
    fx, fy = 14, 65
    d.rectangle([fx - 6, fy - 30, fx - 1, fy - 2], fill=JEAN)
    d.rectangle([fx + 1, fy - 30, fx + 6, fy - 2], fill=JEAN)
    d.rectangle([fx - 7, fy - 3, fx - 1, fy], fill=TENIS)
    d.rectangle([fx + 1, fy - 3, fx + 7, fy], fill=TENIS)
    d.polygon([(fx - 8, fy - 52), (fx + 8, fy - 52), (fx + 9, fy - 30), (fx - 9, fy - 30)], fill=SUD)
    d.line([(fx - 8, fy - 51), (fx - 11, fy - 30)], fill=SUD_D, width=3)     # brazos colgando, quieto
    d.line([(fx + 8, fy - 51), (fx + 11, fy - 30)], fill=SUD_D, width=3)
    d.ellipse([fx - 6, fy - 64, fx + 6, fy - 52], fill=PIEL)
    d.pieslice([fx - 6, fy - 65, fx + 6, fy - 55], 180, 360, fill=PELO)
    d.point([(fx - 3, fy - 58), (fx + 2, fy - 58)], fill=(20, 16, 12))
    d.line([(fx - 3, fy - 55), (fx - 1, fy - 54), (fx + 1, fy - 54), (fx + 3, fy - 55)], fill=(110, 30, 26))   # sonrisa
    save("chico_doble", im, (fx, fy), [(fx - 3, fy - 58), (fx + 2, fy - 58)], "el doble: idéntico al chico, de frente, inmóvil, sonríe")


def doble_cuatro_patas():
    im, d = canvas(56, 32)
    fy = 31
    d.line([(12, fy - 14), (8, fy)], fill=JEAN, width=3)               # piernas
    d.line([(16, fy - 14), (18, fy)], fill=JEAN_D, width=3)
    d.rectangle([6, fy - 2, 10, fy], fill=TENIS)
    d.polygon([(10, fy - 20), (40, fy - 23), (42, fy - 14), (12, fy - 11)], fill=SUD)
    d.line([(38, fy - 17), (42, fy)], fill=SUD_D, width=3)             # brazos
    d.line([(34, fy - 16), (34, fy)], fill=SUD, width=3)
    d.ellipse([40, fy - 22, 51, fy - 11], fill=PIEL)
    d.pieslice([40, fy - 23, 52, fy - 13], 200, 360, fill=PELO)
    save("doble_cuatro_patas", im, (28, fy), [(48, fy - 17)], "el doble a cuatro patas, avanza a la derecha")


def jaguar():
    rng = np.random.default_rng(3)
    im, d = canvas(80, 40)
    fy = 39
    d.line([(66, fy - 22), (74, fy - 28), (78, fy - 22)], fill=JAG, width=3)               # cola
    for x, dx in ((60, 2), (52, -1), (24, 1), (16, -2)):
        d.line([(x, fy - 14), (x + dx, fy)], fill=JAG if x % 3 else (170, 116, 44), width=4)
    d.ellipse([12, fy - 30, 68, fy - 10], fill=JAG)
    d.ellipse([18, fy - 18, 62, fy - 9], fill=JAG_L)
    rosetas(d, (16, fy - 28, 64, fy - 16), 26, rng, 1.2)
    d.ellipse([0, fy - 33, 18, fy - 17], fill=JAG)                                           # cabeza
    d.polygon([(3, fy - 31), (4, fy - 37), (8, fy - 32)], fill=JAG)
    d.ellipse([0, fy - 24, 8, fy - 18], fill=JAG_L)
    d.point((1, fy - 22), fill=JAG_D)
    rosetas(d, (6, fy - 31, 16, fy - 25), 4, rng, 0.8)
    save("jaguar", im, (40, fy), [(5, fy - 27)], "jaguar de perfil, mira a la izquierda; ojo brilla")


def jaguar_rostro():
    rng = np.random.default_rng(9)
    im, d = canvas(84, 84)
    c = 42
    d.polygon([(10, 22), (16, 4), (28, 16)], fill=JAG)                                        # orejas
    d.polygon([(74, 22), (68, 4), (56, 16)], fill=JAG)
    d.polygon([(14, 18), (17, 9), (24, 16)], fill=JAG_D)
    d.polygon([(70, 18), (67, 9), (60, 16)], fill=JAG_D)
    d.ellipse([4, 8, 80, 82], fill=JAG)
    rosetas(d, (6, 10, 78, 40), 30, rng, 1.6)
    rosetas(d, (6, 40, 20, 70), 6, rng, 1.4)
    rosetas(d, (64, 40, 78, 70), 6, rng, 1.4)
    # rostro humano en el centro
    d.ellipse([c - 18, 24, c + 18, 76], fill=PIEL)
    d.ellipse([c - 18, 24, c + 18, 76], outline=PIEL_D)
    for s in (-1, 1):
        ex = c + s * 8
        d.line([(ex - 5, 38), (ex + 5, 37 if s > 0 else 39)], fill=(50, 34, 24), width=2)    # cejas
        d.ellipse([ex - 4, 42, ex + 4, 47], fill=(226, 220, 206))
        d.ellipse([ex - 2, 42, ex + 2, 47], fill=(70, 46, 28))
        d.point((ex, 44), fill=(10, 8, 8))
    d.polygon([(c - 2, 48), (c + 2, 48), (c + 4, 57), (c - 4, 57)], fill=PIEL_D)
    d.line([(c - 6, 64), (c, 65), (c + 6, 64)], fill=(110, 50, 40), width=2)
    d.ellipse([c - 6, 70, c + 6, 80], fill=JAG_L)                                             # mentón de jaguar
    for s in (-1, 1):
        for k in range(3):
            d.line([(c + s * 12, 60 + k * 3), (c + s * 30, 56 + k * 5)], fill=(236, 230, 214))  # bigotes
    save("jaguar_rostro", im, (c, 83), [], "close-up: cabeza de jaguar con rostro humano (el del chico)")


def nahual_silueta():
    im, d = canvas(40, 78)
    fx, fy = 20, 77
    C, C2 = (14, 16, 18), (24, 26, 28)
    d.polygon([(fx - 6, fy - 36), (fx - 1, fy - 36), (fx - 3, fy), (fx - 8, fy)], fill=C)
    d.polygon([(fx + 1, fy - 36), (fx + 6, fy - 36), (fx + 8, fy), (fx + 3, fy)], fill=C)
    d.polygon([(fx - 10, fy - 60), (fx + 10, fy - 60), (fx + 8, fy - 34), (fx - 8, fy - 34)], fill=C2)
    d.line([(fx - 10, fy - 58), (fx - 15, fy - 26)], fill=C, width=3)           # brazos largos
    d.line([(fx + 10, fy - 58), (fx + 15, fy - 26)], fill=C, width=3)
    for s in (-1, 1):
        for k in range(3):
            d.line([(fx + s * 15, fy - 26), (fx + s * (15 + k), fy - 22)], fill=C)
    d.ellipse([fx - 8, fy - 74, fx + 8, fy - 58], fill=C)                        # cabeza felina
    d.polygon([(fx - 7, fy - 70), (fx - 6, fy - 78), (fx - 2, fy - 72)], fill=C)
    d.polygon([(fx + 7, fy - 70), (fx + 6, fy - 78), (fx + 2, fy - 72)], fill=C)
    d.ellipse([fx - 4, fy - 64, fx + 4, fy - 58], fill=C2)                       # hocico
    save("nahual_silueta", im, (fx, fy), [(fx - 3, fy - 67), (fx + 3, fy - 67)], "silueta humana con cabeza de jaguar")


def lancha():
    im, d = canvas(86, 26)
    fy = 25
    d.polygon([(2, 6), (84, 6), (76, 22), (10, 22)], fill=(84, 60, 38))
    d.polygon([(2, 6), (84, 6), (82, 9), (4, 9)], fill=(130, 98, 62))
    for k in range(3):
        d.line([(6 + k * 2, 12 + k * 4), (80 - k * 2, 12 + k * 4)], fill=(60, 42, 26))
    d.rectangle([36, 3, 50, 6], fill=(110, 82, 52))                               # asiento
    save("lancha", im, (43, 22), [], "lancha de madera de lado; el ancla es la línea del agua")


def lancha_aerea():
    im, d = canvas(30, 70)
    d.polygon([(15, 0), (27, 16), (27, 62), (22, 69), (8, 69), (3, 62), (3, 16)], fill=(84, 60, 38))
    d.polygon([(15, 4), (24, 17), (24, 60), (20, 66), (10, 66), (6, 60), (6, 17)], fill=(58, 40, 26))
    d.rectangle([6, 28, 24, 31], fill=(110, 82, 52))
    d.rectangle([6, 52, 24, 55], fill=(110, 82, 52))
    # chico tendido dentro (visto desde arriba)
    d.ellipse([11, 14, 19, 22], fill=PELO)
    d.rectangle([9, 22, 21, 40], fill=SUD)
    d.rectangle([10, 40, 14, 56], fill=JEAN)
    d.rectangle([16, 40, 20, 56], fill=JEAN_D)
    save("lancha_aerea", im, (15, 69), [], "lancha vista desde arriba con el chico tendido; proa hacia arriba")


def sombra_agua():
    im, d = canvas(40, 90)
    S = (12, 18, 26)
    d.ellipse([8, 18, 32, 72], fill=S)
    d.ellipse([11, 2, 29, 22], fill=S)
    d.polygon([(12, 6), (13, 0), (17, 4)], fill=S)
    d.polygon([(28, 6), (27, 0), (23, 4)], fill=S)
    for x, y in ((6, 26), (34, 26), (6, 62), (34, 62)):
        d.ellipse([x - 4, y - 6, x + 4, y + 6], fill=S)
    d.line([(20, 72), (24, 82), (18, 89)], fill=S, width=4)
    save("sombra_agua", im, (20, 89), [], "sombra enorme de jaguar bajo el agua (vista desde arriba)")


if __name__ == "__main__":
    for fn in (chico_camara, chico_escritorio, chico_tendido, chico_doble, doble_cuatro_patas, jaguar,
               jaguar_rostro, nahual_silueta, lancha, lancha_aerea, sombra_agua):
        fn()


def jaguar_asomado():
    """Jaguar asomándose detrás de un tronco con el rostro del chico, pálido, mirando fijo (para zoom)."""
    rng = np.random.default_rng(21)
    im, d = canvas(34, 34)
    PIEL_P, PIEL_S = (178, 156, 134), (132, 112, 96)
    d.polygon([(4, 9), (2, 4), (9, 6)], fill=JAG)                      # orejas echadas hacia atrás
    d.polygon([(19, 6), (25, 3), (24, 9)], fill=JAG)
    d.ellipse([1, 4, 28, 31], fill=JAG)
    for _ in range(14):                                                 # manchas sólidas
        x, y = rng.uniform(2, 26), rng.uniform(5, 28)
        if 6 < x < 22 and y > 10:
            continue
        d.rectangle([x, y, x + 1, y + 1], fill=JAG_D)
    d.ellipse([6, 10, 22, 31], fill=PIEL_P)                             # rostro humano
    for y in range(10, 31):                                             # sombra del lado izq.
        for x in range(6, 10):
            if im.getpixel((x, y))[:3] == PIEL_P:
                d.point((x, y), fill=PIEL_S)
    d.polygon([(7, 13), (9, 11), (13, 10), (18, 10), (21, 12), (19, 13), (16, 12), (13, 14), (10, 12)], fill=PELO)   # fleco
    for ex in (8, 15):                                                  # ojos muy abiertos, pupila diminuta
        d.rectangle([ex, 16, ex + 3, 18], fill=(236, 232, 220))
        d.point((ex + 1, 17), fill=(14, 10, 8))
        d.line([(ex, 19), (ex + 3, 19)], fill=(98, 80, 68))
    d.rectangle([12, 20, 13, 23], fill=PIEL_S)                          # nariz
    d.ellipse([10, 25, 16, 28], fill=(30, 14, 14))                      # boca abierta, oscura
    d.ellipse([10, 29, 17, 32], fill=JAG_L)
    d.rectangle([22, 0, 33, 33], fill=(36, 30, 24))                     # tronco que lo tapa
    for x in (24, 27, 30):
        d.line([(x, 0), (x + 1, 33)], fill=(24, 20, 16))
    brillos = [(9, 16), (11, 16), (9, 18), (11, 18), (16, 16), (18, 16), (16, 18), (18, 18)]
    save("jaguar_asomado", im, (12, 33), brillos, "jaguar asomándose tras un tronco con el rostro del chico; usar con zoom",
         color=[236, 232, 220])


if __name__ == "__main__":
    jaguar_asomado()
