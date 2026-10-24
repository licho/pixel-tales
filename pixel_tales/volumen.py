"""Sombreado con volumen para escenas: mapa de alturas -> normales -> luz. También muros de bloques irregulares.

  sombrear(mascara, base, luz, radio, relieve, ruido, ambiente, brillo)  -> rgb (H, W, 3)
  bloques(W, H, alto, ancho, semilla)  -> (ids, info) muro de piedra con bloques irregulares
  pintar_bloques(ids, info, base, semilla) -> rgb con bisel, juntas, bloques faltantes
  nubes_volumen(densidad, luz_xy, ...) -> (rgb, alpha) nubes con panza oscura y bordes plateados
"""
import numpy as np
from PIL import Image, ImageFilter


def _blur(m, r):
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def normales(h):
    gy, gx = np.gradient(h)
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def sombrear(mascara, base, luz=(-0.6, -0.65, 0.5), radio=3.0, relieve=4.0, ruido=None, ambiente=0.35,
             brillo=0.25, dureza=14, color_luz=(1.0, 1.0, 1.0)):
    """Ilumina una forma plana como si tuviera volumen (bordes redondeados) más un relieve opcional."""
    L = np.array(luz, np.float32)
    L /= np.linalg.norm(L)
    h = np.clip((_blur(mascara.astype(np.float32), radio) - 0.35) / 0.65, 0, 1) ** 0.6 * relieve
    if ruido is not None:
        h = h + ruido
    n = normales(h)
    dif = np.clip(n @ L, 0, 1)
    hv = L + np.array([0, 0, 1.0], np.float32)
    hv /= np.linalg.norm(hv)
    sp = np.clip(n @ hv, 0, 1) ** dureza * brillo
    base = np.asarray(base, np.float32)
    col = base * (ambiente + (1 - ambiente) * 1.15 * dif)[..., None] * np.array(color_luz, np.float32)
    return col + (sp * 255)[..., None] * np.array(color_luz, np.float32)


def bloques(W, H, alto=(3, 6), ancho=(5, 12), semilla=0):
    """Muro de bloques irregulares en hileras. Devuelve ids (H, W) y el número de bloques."""
    rng = np.random.default_rng(semilla)
    ids = np.zeros((H, W), np.int32)
    y, k = 0, 1
    while y < H:
        h = int(rng.integers(alto[0], alto[1] + 1))
        x = -int(rng.integers(0, ancho[1]))
        while x < W:
            w = int(rng.integers(ancho[0], ancho[1] + 1))
            ids[y:y + h, max(0, x):max(0, x + w)] = k
            k += 1
            x += w
        y += h
    return ids, k


def bordes(ids):
    arr = ids
    arriba = np.zeros_like(arr, bool); arriba[1:] = arr[1:] != arr[:-1]
    abajo = np.zeros_like(arr, bool); abajo[:-1] = arr[:-1] != arr[1:]
    izq = np.zeros_like(arr, bool); izq[:, 1:] = arr[:, 1:] != arr[:, :-1]
    der = np.zeros_like(arr, bool); der[:, :-1] = arr[:, :-1] != arr[:, 1:]
    return arriba, abajo, izq, der


def pintar_bloques(ids, n, base, semilla=0, faltan=0.05, variacion=0.22, ruido=None):
    """Colorea cada bloque con su tono, bisel (luz arriba-izq., sombra abajo-der.), juntas y huecos."""
    rng = np.random.default_rng(semilla + 7)
    tono = 1 + rng.uniform(-variacion, variacion, n)
    tinte = rng.uniform(-0.06, 0.06, (n, 3))
    hueco = rng.random(n) < faltan
    base = np.asarray(base, np.float32)
    col = base * (tono[ids])[..., None] * (1 + tinte[ids])
    if ruido is not None:
        col *= (0.85 + 0.3 * ruido)[..., None]
    ar, ab, iz, de = bordes(ids)
    h = hueco[ids]
    # bisel normal
    col[(ar | iz) & ~h] = col[(ar | iz) & ~h] * 1.35 + 12
    col[(ab | de) & ~h] *= 0.55
    # juntas (línea de mortero)
    junta = np.zeros_like(ab); junta[:-1] = ab[:-1]
    col[ab] = col[ab] * 0.35
    col[de] = col[de] * 0.45
    # bloques faltantes: hundidos y oscuros, con sombra arriba-izquierda
    col[h] *= 0.38
    col[h & (ar | iz)] *= 0.6
    col[h & (ab | de)] = col[h & (ab | de)] * 1.6 + 6
    return col, hueco


def nubes_volumen(densidad, luz_xy, color_sombra=(36, 42, 54), color_luz=(220, 230, 214), relieve=10.0,
                  falloff=0.5, escala=1.0, umbral=(0.45, 0.62)):
    """Nubes con volumen: panza oscura, cara hacia la luna clara y borde plateado. densidad: (H, W) 0-1."""
    H, W = densidad.shape
    a = np.clip((densidad - umbral[0]) / (umbral[1] - umbral[0]), 0, 1)
    h = _blur(a, 2.0 * escala) * relieve
    n = normales(h)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lx, ly = luz_xy[0] - xx, luz_xy[1] - yy
    dist = np.hypot(lx, ly) + 1e-3
    L = np.stack([lx / dist * 0.8, ly / dist * 0.8, np.full_like(lx, 0.55)], -1)
    L /= np.linalg.norm(L, axis=-1, keepdims=True)
    dif = np.clip(np.sum(n * L, -1), 0, 1)
    cerca = np.exp(-dist / (falloff * max(W, H)))
    borde = np.clip(a - _blur(a, 1.2 * escala), 0, 1) * 3                  # contorno fino
    lado = np.clip(np.sum(n[..., :2] * L[..., :2], -1), 0, 1)
    plata = np.clip(borde * lado * (0.3 + cerca), 0, 1)
    k = np.clip(0.15 + dif ** 1.6 * (0.35 + 0.9 * cerca), 0, 1)
    col = np.array(color_sombra, np.float32) * (1 - k[..., None]) + np.array(color_luz, np.float32) * k[..., None]
    col = col * (1 - plata[..., None]) + np.array([245, 250, 236], np.float32) * plata[..., None]
    return col, a
