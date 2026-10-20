# Catálogo de pixel-tales

Todo lo disponible para armar episodios. **Mantener este archivo corto y al día**: es lo único que hace falta leer para escribir un episodio nuevo.

Tamaño de capa (coordenadas de actores): **horizontal 424 x 216** · **vertical 256 x 384** (la cámara ve 384x216 / 216x384).
Formatos de marca: `cuadrado` (perfil 1080), `portada_fb` (1640x624), `banner_yt` (2560x1440) — ver `tools/portada.py`.

## Estilos (`styles/`)
| Nombre | Look |
|---|---|
| `survival` | Noche postapocalíptica: teal oscuro, carbón, ámbar de fuego, amarillo de traje |
| `xibalba` | Inframundo maya: obsidiana, rojo sangre, hueso, ocre, jade apagado, antorcha |
| `pixeltales` | Marca del canal: mezcla de survival y xibalba (portadas, piezas de marca) |

## Escenas / fondos (`scenes/`)
Coordenadas relativas: multiplica por W x H del formato. (V) = vertical, (H) = horizontal.

| Nombre | Formatos | Descripción | Parámetros | Dónde poner actores (pies) |
|---|---|---|---|---|
| `calle` | H | Calle urbana abandonada, rascacielos en niebla | `farol`, `barril`, `carro`, `cables` (bool), `semilla` | banqueta izq. x 60-130 y 195-212 (px); calle x 200-320 y 140-170 |
| `cueva` | H, V | Túnel con escalinata hacia un resplandor | `resplandor` (rojo/jade/ocre/[rgb]), `antorchas`, `escalera`, `calaveras`, `semilla` | escalones x 0.35-0.65 W, y 0.85-0.97 H; fondo (0.5 W, 0.40 H); murciélagos [0.1W,0.05H,0.9W,0.45H] |
| `rio` | H, V | Río subterráneo serpenteando (también lago/río normal) | `agua` (sangre/pus/agua/noche/[rgb]), `brillo`, `antorcha`, `semilla` | orillas x 0.02-0.28 W y 0.72-0.98 W, y 0.75-0.97 H |
| `salon_tronos` | H, V | Templo: plataforma con 2 tronos, mascarón, tzompantli, braseros | `tronos`, `tzompantli`, `braseros`, `semilla` | tronos (0.40 W, 0.535 H) y (0.60 W, 0.535 H); piso x 0.15-0.85 W, y 0.74-0.95 H |
| `casa_interior` | H, V | Casa maya de noche: palma, bajareque, puerta con luna, hamaca, fogón | `fogon`, `puerta_luna`, `hamaca`, `rincon_oscuro`, `semilla` | rincón oscuro (0.74 W, 0.79 H); piso x 0.10-0.80 W, y 0.80-0.97 H |
| `panorama` | todos | Marca: ciudad en ruinas, pirámide bajo luna roja, bosque, fogata | `horizonte` (0-1), `escala` (px), `luna_roja`, `fogata` | ver `tools/portada.py` |
| `juego_pelota` | H, V | Cancha de pelota de noche, aros, templos, luna | `aros`, `antorchas`, `luna`, `semilla` | dos personajes (0.40 W, 0.97 H) y (0.60 W, 0.97 H) |

## Sprites (`sprites/`)
| Ruta | Descripción | Alto |
|---|---|---|
| `survival/sobreviviente_traje` | Traje amarillo, máscara antigás, rifle, mira a la derecha | 102 px |
| `xibalba/hun_came` | Señor supremo sentado, esquelético, plumas de jade, ojos rojos | 66 px |
| `xibalba/vucub_came` | Igual, plumas rojas | 66 px |
| `xibalba/senor_a` | Señor de pie, capa roja oscura, bastón de hueso | 80 px |
| `xibalba/senor_b` | Señor de pie, capa verde oscuro, brazos con garras | 80 px |
| `xibalba/gemelo` | Jugador de pelota de espaldas (usar `espejo` para el hermano) | 90 px |
| `xibalba/sombra` | Figura agazapada con cuchillo de obsidiana; ojos y filo brillan | 42 px |

## Actores animados
| Tipo | Opciones |
|---|---|
| `zombi` | `pos`, `altura` (10-30), `fase`, `ropa: [r,g,b]`, `avanza: [dx, dy]` px/seg |
| `murcielagos` | `cantidad`, `zona: [x0,y0,x1,y1]`, `tam`, `semilla` |
| `escorpiones` | `cantidad`, `zona: [x0,y0,x1,y1]`, `tam`, `semilla` |
| `ojos` | `pos`, `color` (default rojo), `separacion`, `tam`, `aparece` (segundo) — brillan en la oscuridad |

## Efectos (`efectos: [...]`)
| Nombre | Qué hace |
|---|---|
| `lluvia` | Lluvia pixelada con salpicaduras |
| `ceniza` | Ceniza y brasas flotando |
| `relampago` | Destello del cielo a mitad del panel |
| `parpadeo` | El farol de la `calle` falla de vez en cuando |
| *(automático)* | Fuego animado con humo; antorchas parpadean; contraluz en personajes cerca de fuego |

## Episodio
```yaml
estilo: xibalba
formato: vertical          # o horizontal (default)
subtitulos: true           # default true en vertical
voz: ep01.mp3              # opcional; reparte el audio entre paneles según su texto
palabras: ep01.palabras.json  # opcional; tiempos por palabra de ElevenLabs -> cortes y subtítulos exactos
paneles:
  - escena: cueva
    params: {resplandor: jade}
    efectos: [ceniza]
    camara: {pan: 8}       # desplazamiento lateral (0 fija, máx 25)
    titulo: "TEXTO GRANDE"  # opcional, arriba
    subtitulos_y: 0.80     # opcional, posición vertical del subtítulo (0-1)
    actores:
      - sprite: xibalba/gemelo
        pos: [104, 372]
        escala: 1.0
        espejo: false
      - ojos: {pos: [128, 150], aparece: 2}
    texto: "Narración de este panel"
    duracion: 7            # opcional; sin voz se estima por el texto
```
