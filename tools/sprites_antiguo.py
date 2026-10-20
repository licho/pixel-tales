"""Genera los sprites del mundo antiguo en sprites/antiguo/.

  elefante   elefante de guerra con armadura y torre (howdah), de perfil mirando a la derecha
  legionario legionario romano de pie con escudo (scutum) y pilum, mirando a la derecha
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "sprites" / "antiguo"
OUT.mkdir(parents=True, exist_ok=True)

GRIS, GRIS_D, GRIS_L = (104, 96, 92), (70, 64, 62), (134, 126, 118)
BRONCE, BRONCE_D = (190, 148, 64), (140, 104, 44)
ROJO, ROJO_D = (164, 38, 30), (116, 26, 22)
MADERA = (96, 70, 30)
PIEL = (150, 104, 70)
ACERO = (150, 150, 156)
MARFIL = (232, 224, 200)


def save(name, im, ancla, notas=""):
    im.save(OUT / f"{name}.png")
    (OUT / f"{name}.json").write_text(json.dumps({"ancla": list(ancla), "notas": notas}, indent=2, ensure_ascii=False))
    print("Sprite:", name, im.size)


def elefante():
    im = Image.new("RGBA", (96, 84), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    by = 83
    # patas traseras (más oscuras, al fondo)
    for x in (18, 56):
        d.rounded_rectangle([x, 50, x + 10, by], 3, fill=GRIS_D)
    # cuerpo
    d.ellipse([8, 26, 78, 64], fill=GRIS)
    d.ellipse([12, 28, 74, 46], fill=GRIS_L)
    # patas delanteras
    for x in (26, 64):
        d.rounded_rectangle([x, 50, x + 11, by], 3, fill=GRIS)
        d.rectangle([x, by - 3, x + 11, by], fill=GRIS_D)
    # cabeza
    d.ellipse([64, 18, 92, 48], fill=GRIS)
    d.ellipse([60, 22, 76, 46], fill=GRIS_D)                      # oreja
    # trompa
    d.line([(88, 38), (92, 50), (90, 62), (86, 70), (88, 74)], fill=GRIS, width=6)
    d.line([(90, 64), (86, 70), (88, 74)], fill=GRIS_D, width=3)
    # colmillo con punta de bronce
    d.line([(84, 44), (92, 52), (95, 50)], fill=MARFIL, width=2)
    d.point((95, 49), fill=BRONCE)
    d.point((82, 30), fill=(16, 12, 12))                          # ojo
    # armadura: testera y manta roja con bordes de bronce
    d.polygon([(70, 18), (88, 22), (90, 34), (78, 32)], fill=BRONCE_D)
    d.line([(70, 18), (88, 22)], fill=BRONCE)
    d.polygon([(16, 30), (70, 28), (72, 54), (14, 54)], fill=ROJO)
    d.line([(14, 54), (72, 54)], fill=BRONCE, width=2)
    for x in range(18, 70, 8):
        d.point((x, 56), fill=BRONCE)
        d.point((x + 2, 42), fill=ROJO_D)
    # torre (howdah)
    d.rectangle([24, 10, 58, 28], fill=MADERA)
    d.rectangle([24, 10, 58, 12], fill=BRONCE)
    for x in range(26, 58, 6):
        d.line([(x, 13), (x, 27)], fill=(70, 50, 22))
    # soldados en la torre y lanzas
    for x in (31, 43, 52):
        d.ellipse([x - 3, 2, x + 3, 9], fill=PIEL)
        d.pieslice([x - 3, 1, x + 3, 7], 180, 360, fill=BRONCE_D)
        d.line([(x + 4, -2), (x + 4, 14)], fill=(150, 120, 80))
    d.polygon([(35, -4), (37, -4), (36, -8)], fill=ACERO)
    # mahout (conductor) en el cuello
    d.ellipse([70, 12, 76, 19], fill=PIEL)
    d.rectangle([69, 18, 77, 26], fill=(220, 200, 160))
    # cola
    d.line([(9, 38), (4, 52), (5, 58)], fill=GRIS_D, width=2)
    save("elefante", im, (48, by), "Elefante de guerra indio. Mirando a la derecha. Pies en (48, 83).")


def legionario():
    im = Image.new("RGBA", (34, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fx, fy = 14, 63
    d.rectangle([fx - 5, fy - 18, fx - 1, fy], fill=(120, 84, 60))          # piernas
    d.rectangle([fx + 1, fy - 18, fx + 5, fy], fill=(104, 72, 52))
    d.rectangle([fx - 6, fy - 2, fx - 1, fy], fill=(60, 40, 26))            # sandalias
    d.rectangle([fx + 1, fy - 2, fx + 7, fy], fill=(60, 40, 26))
    d.polygon([(fx - 7, fy - 22), (fx + 7, fy - 22), (fx + 8, fy - 15), (fx - 8, fy - 15)], fill=ROJO)   # falda túnica
    for x in range(fx - 6, fx + 7, 3):
        d.line([(x, fy - 21), (x, fy - 15)], fill=ROJO_D)
    d.rectangle([fx - 7, fy - 40, fx + 7, fy - 22], fill=ACERO)             # lorica segmentata
    for y in range(fy - 38, fy - 22, 4):
        d.line([(fx - 7, y), (fx + 7, y)], fill=(96, 98, 104))
    d.rectangle([fx - 8, fy - 41, fx + 8, fy - 38], fill=(176, 178, 180))   # hombreras
    d.ellipse([fx - 5, fy - 52, fx + 5, fy - 41], fill=PIEL)                # cabeza
    d.pieslice([fx - 6, fy - 54, fx + 6, fy - 44], 180, 360, fill=ACERO)    # casco
    d.rectangle([fx - 6, fy - 49, fx - 4, fy - 43], fill=ACERO)             # carrillera
    d.rectangle([fx - 1, fy - 60, fx + 1, fy - 53], fill=ROJO)              # cresta
    d.rectangle([fx - 4, fy - 61, fx + 4, fy - 58], fill=ROJO)
    d.point((fx + 3, fy - 47), fill=(16, 12, 12))                           # ojo
    # pilum
    d.line([(fx + 11, fy - 63), (fx + 11, fy - 4)], fill=MADERA, width=1)
    d.line([(fx + 11, fy - 63), (fx + 11, fy - 52)], fill=ACERO, width=1)
    # scutum (escudo rojo curvo, de frente al espectador, a la izquierda del cuerpo)
    d.rounded_rectangle([fx - 3, fy - 42, fx + 10, fy - 12], 2, fill=ROJO)
    d.rounded_rectangle([fx - 3, fy - 42, fx + 10, fy - 12], 2, outline=BRONCE)
    d.ellipse([fx + 1, fy - 30, fx + 6, fy - 25], fill=BRONCE)              # umbo
    d.line([(fx + 3, fy - 40), (fx + 3, fy - 14)], fill=BRONCE_D)
    save("legionario", im, (fx, fy), "Legionario romano mirando a la derecha. Pies en (14, 63).")


if __name__ == "__main__":
    elefante()
    legionario()
