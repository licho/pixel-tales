"""Genera sprites/survival/sobreviviente_traje.png (+ .json con el ancla de los pies).

Se corre una sola vez. El PNG guarda colores base (sin luz); la escena lo ilumina.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "sprites" / "survival" / "sobreviviente_traje.png"
W, H = 72, 106
fx, fy = 26, 104        # pies dentro del lienzo

im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
SUIT, SUIT_D, BOOT, GLOVE = (196, 172, 82), (160, 138, 62), (34, 30, 26), (58, 50, 34)
METAL, WOOD = (26, 30, 30), (102, 60, 30)

d.rounded_rectangle([fx - 23, fy - 82, fx - 10, fy - 50], 3, fill=(72, 82, 58))                          # mochila
d.polygon([(fx - 11, fy - 44), (fx - 2, fy - 44), (fx - 4, fy - 4), (fx - 13, fy - 4)], fill=SUIT_D)       # pierna
d.polygon([(fx + 1, fy - 44), (fx + 10, fy - 44), (fx + 12, fy - 4), (fx + 3, fy - 4)], fill=SUIT)
d.rectangle([fx - 15, fy - 6, fx - 3, fy], fill=BOOT)
d.rectangle([fx + 2, fy - 6, fx + 15, fy], fill=BOOT)
d.polygon([(fx - 13, fy - 81), (fx + 12, fy - 81), (fx + 14, fy - 60), (fx + 12, fy - 42),
           (fx - 12, fy - 42), (fx - 14, fy - 60)], fill=SUIT)                                              # torso
d.rectangle([fx - 12, fy - 47, fx + 12, fy - 43], fill=(60, 44, 30))                                       # cinturón
d.polygon([(fx - 10, fy - 77), (fx - 4, fy - 76), (fx + 6, fy - 58), (fx + 1, fy - 56)], fill=SUIT_D)      # brazo lejano
d.ellipse([fx - 12, fy - 102, fx + 9, fy - 78], fill=(180, 158, 74))                                       # capucha
d.ellipse([fx - 3, fy - 97, fx + 11, fy - 82], fill=(44, 52, 54))                                          # máscara
d.ellipse([fx + 4, fy - 86, fx + 10, fy - 80], fill=(24, 28, 30))                                          # filtro
d.point([(fx + 3, fy - 93), (fx + 4, fy - 93), (fx + 7, fy - 93), (fx + 8, fy - 93)], fill=(150, 170, 160))  # lentes
d.polygon([(fx - 9, fy - 63), (fx + 30, fy - 51), (fx + 44, fy - 47), (fx + 44, fy - 45),
           (fx + 30, fy - 47), (fx - 9, fy - 58)], fill=METAL)                                              # rifle
d.polygon([(fx + 14, fy - 54), (fx + 18, fy - 53), (fx + 22, fy - 45), (fx + 18, fy - 44)], fill=METAL)
d.polygon([(fx - 9, fy - 63), (fx + 2, fy - 60), (fx + 2, fy - 56), (fx - 9, fy - 58)], fill=WOOD)
d.polygon([(fx + 22, fy - 53), (fx + 29, fy - 51), (fx + 29, fy - 48), (fx + 22, fy - 50)], fill=WOOD)
d.polygon([(fx + 8, fy - 79), (fx + 14, fy - 77), (fx + 20, fy - 57), (fx + 14, fy - 55)], fill=SUIT)      # brazo cercano
d.ellipse([fx + 13, fy - 58, fx + 20, fy - 51], fill=GLOVE)
d.ellipse([fx, fy - 61, fx + 6, fy - 55], fill=GLOVE)

# volumen: más oscuro abajo y a la derecha
arr = np.asarray(im, np.float32).copy()
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
shade = 1 - 0.25 * np.clip((yy - (fy - 100)) / 100, 0, 1) - 0.15 * np.clip((xx - fx) / 20, 0, 1)
arr[..., :3] *= shade[..., None]
OUT.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(OUT)
OUT.with_suffix(".json").write_text(json.dumps({"ancla": [fx, fy], "altura_px": 102,
                                                "notas": "traje amarillo, máscara antigás, rifle"}, indent=2))
print("Sprite:", OUT)
