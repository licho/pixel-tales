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
| `nahual` | Terror mexicano nocturno: azul noche, bosque, niebla, sepia de fotos, lámpara ámbar, ojos dorados |
| `oceano` | Tormenta en el mar: grises pizarra, azul acero, verde abisal, espuma, ojos amarillos, rayo violeta |
| `ruinas` | Fantasía oscura bajo la luna: pizarra, azul noche, piedra fría, musgo, tierra pálida, ramas secas, matorral rojizo |
| `antiguo` | Mundo antiguo épico: atardecer naranja, ocre/polvo, bronce, rojo legionario, negro Qin, azul persa, hueso. `ceniza` = polvo dorado |

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
| `negro` | todos | Pantalla negra para inicios/cortes/finales | `niebla`, `luz` (luz neutra para actores) | cualquier punto; ideal con `ojos` |
| `foto_mesa` | H, V | Foto antigua sepia sobre mesa o lancha, bajo lámpara | `contenido` (hombre_jaguar/abuelo/bebe/reverso), `texto` (reverso, líneas con \|), `superficie` (mesa/lancha), `giro` | centro foto (0.5 W, 0.46 H); ojos del 'bebe' en (0.62 W, 0.38 H) |
| `archivo` | H, V | Cuarto de investigación: corcho con fotos e hilos rojos, escritorio, lámpara | `ventana`, `jaguar` | silla (0.52 W, 0.93 H) |
| `bosque` | todos | Bosque con sendero de lodo y niebla | `hora` (tarde/noche), `niebla`, `huellas`, `orilla` (agua abajo), `fogata` [x, y, ancho], `luna` (intensidad, 0.35 con fogata), `semilla` | sendero cerca (0.5 W, 0.95 H); entre árboles x 0.25-0.75 W, y 0.62-0.66 H; lancha (0.45 W, 0.97 H) con orilla |
| `lago` | todos | Lago con montañas, bosque y niebla | `vista` (orilla/aerea), `hora` (anochecer/noche), `isla`, `niebla` | orilla: lancha (0.45 W, 0.93 H); aérea: lancha escala ~0.6 en x 0.4-0.6 W |
| `mar_tormenta` | todos | Mar en tormenta: nubes, cortinas de lluvia, olas animadas con espuma, niebla, rayo (con `relampago`). Las olas tapan a los actores según su profundidad | `horizonte`, `olas` (0.2 calma – 1.5 fuerte), `claro` [x,y], `niebla`, `espuma` [[x,y,ancho]...] (salpicaduras), `semilla` | barco (0.35 W, 0.86-0.9 H) con `flota` y `balanceo`; criatura (0.5 W, 0.78-0.86 H) |
| `imagen` | todos | Usa una imagen (ej. de IA) como fondo y la pasa por la paleta del estilo; encima funcionan lluvia, relámpago, ojos, zoom… Sin parallax ni olas animadas | `archivo` (ruta en el repo, ej. `fondos/...`), `foco` [x,y], `brillo` | coordenadas = píxeles de la capa |
| `ruinas` | todos | Ruinas de castillo bajo la luna llena (versión detallada: bloques irregulares con bisel, silueta desmoronada, nubes con volumen, rocas y árbol sombreados): muro con gran arco, torres rotas con musgo, árbol seco, rocas, escalones y camino iluminado | `luna` [x,y], `nubes` (0-1), `arbol`, `antorchas`, `semilla` | bajo el arco (0.53 W, 0.80 H) ~0.18 H; camino cerca (0.5 W, 0.95 H) ~0.35 H; murciélagos [0.4W, 0.05H, 0.95W, 0.45H] |
| `llanura` | todos | Llanura del mundo antiguo: cielo, sol bajo, montañas, polvo; extras: cauce seco, estrecho de mar con puentes de barcos, ciudad amurallada (china), campo de huesos y lanzas rotas | `hora` (atardecer/polvo/anochecer/noche/tormenta), `horizonte` (0.42), `sol`, `sol_x`, `montanas`, `rio_seco`, `estrecho` [y0,y1], `puentes` [y...], `ciudad` {x,ancho,alto,tipo}, `huesos`, `lanzas_rotas` (n), `niebla`, `semilla` | horizonte y≈0.42 H; ejército en suelo zona [0, 0.43H, W, 0.97H]; sobre puente en y=f·H: zona [0, yb-3, W, yb] con alto 4-8; elefantes cerca (x, 0.92 H, escala ~1.1), lejos (0.69 H, escala 0.55); estandartes pos [x, 0.97 H] alto 150-165 (la tela queda arriba del subtítulo) |
| `muralla_romana` | H, V | Muralla de frontera de noche: adarve que se aleja, parapeto con almenas, antorchas, luna, colinas y niebla | `antorchas` (n), `niebla`, `luna`, `semilla` | legionarios: lejos (0.57 W, 0.505 H, esc 0.4), medio (0.46 W, 0.66 H, esc 0.85), cerca (0.59 W, 0.98 H, esc 1.9) — usar `subtitulos_y: 0.13` si el de cerca tapa el texto |
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
| `nahual/chico_camara` | Joven investigador grabando con cámara, mira a la derecha | 66 px |
| `nahual/chico_escritorio` | El chico de espaldas, sentado | 50 px |
| `nahual/chico_tendido` | El chico acostado, inconsciente (ancho 60) | 16 px |
| `nahual/chico_doble` | El doble: idéntico, de frente, inmóvil, sonríe, ojos dorados | 66 px |
| `nahual/doble_cuatro_patas` | El doble a cuatro patas, avanza a la derecha | 32 px |
| `nahual/jaguar` | Jaguar de perfil, mira a la izquierda; ojo brilla | 40 px |
| `nahual/jaguar_rostro` | Close-up: cabeza de jaguar con rostro humano | 84 px |
| `nahual/nahual_silueta` | Silueta humana con cabeza de jaguar, ojos dorados | 78 px |
| `nahual/lancha` | Lancha de madera de lado (ancla = línea del agua) | 26 px |
| `nahual/lancha_aerea` | Lancha vista desde arriba con el chico tendido | 70 px |
| `nahual/sombra_agua` | Sombra de jaguar bajo el agua (vista desde arriba) | 90 px |
| `oceano/primigenio` | Criatura colosal alada con tentáculos, ojos amarillos que brillan; ancla = línea del agua (ancho 270) | 192 px |
| `antiguo/elefante` | Elefante de guerra con armadura roja, torre (howdah) con soldados, mira a la derecha (ancho 96) | 84 px |
| `antiguo/legionario` | Legionario romano: lorica, scutum rojo, pilum, cresta; mira a la derecha | 64 px |
| `fantasia/guerrero_sentado` | Guerrero encapuchado sentado en una piedra, inclinado hacia el fuego (a su derecha), espada clavada; ojo refleja el fuego | 92 px |
| `oceano/pesquero` | Barco pesquero, proa a la derecha, farol encendido; ancla = línea del agua | 50 px |

## Actores animados
| Tipo | Opciones |
|---|---|
| `zombi` | `pos`, `altura` (10-30), `fase`, `ropa: [r,g,b]`, `avanza: [dx, dy]` px/seg |
| `murcielagos` | `cantidad`, `zona: [x0,y0,x1,y1]`, `tam`, `semilla` |
| `escorpiones` | `cantidad`, `zona: [x0,y0,x1,y1]`, `tam`, `semilla` |
| `ojos` | `pos`, `color` (default rojo), `separacion`, `tam`, `aparece` (segundo) — brillan en la oscuridad |
| `ejercito` | Miles de soldados en perspectiva: `zona` [x0, y_lejos, x1, y_cerca], `tipo` (persa/qin/romano/indio), `alto_lejos`, `alto_cerca` (px), `avance` (px/seg, + derecha, 0 = quietos), `marcha`, `bloques` [soldados, hueco], `estandartes` (cada N), `densidad`, `bruma` [rgb], `poligono` (recorte), `semilla` |
| `estandarte` | Bandera que ondea: `pos` (pie del asta), `alto`, `ancho`, `color`, `color2`, `simbolo` (sol/rueda/dragon/aguila/nada), `fase` |
| sprite en sombra | cualquier `sprite` con `brillo: 0.5` (más oscuro; sus ojos siguen brillando) y `contraluz: false` |
| sprite animado | cualquier `sprite` con `aparece`, `desaparece` (seg), `movimiento: [dx, dy]` (px/seg), `flota` (px) o `balanceo` (grados) |

## Efectos (`efectos: [...]`)
| Nombre | Qué hace |
|---|---|
| `lluvia` | Lluvia pixelada. Opcional en el panel: `lluvia: {cantidad: 380, viento: -0.18, largo: 1.7, salpicaduras: false}` |
| `ceniza` | Ceniza y brasas flotando |
| `relampago` | Destello del cielo a mitad del panel |
| `parpadeo` | El farol de la `calle` falla de vez en cuando |
| `grabacion` | Interfaz de cámara de video: esquinas, REC parpadeando, contador (`grabacion_inicio` en seg) |
| `pausa` | Igual pero en PAUSA; combínalo con `congelado: true` en el panel para detener la animación |
| *(panel)* `zoom` | `zoom: {centro: [x, y], factor: 3, factor_final: 5}` zoom digital pixelado (con acercamiento lento opcional) |
| *(automático)* | Fuego animado con humo; antorchas parpadean; contraluz en personajes cerca de fuego |

Herramientas para escenas detalladas: `pixel_tales/volumen.py` → `sombrear()` (volumen con mapa de alturas), `bloques()` + `pintar_bloques()` (muros de piedra irregulares), `nubes_volumen()` (nubes con panza oscura y bordes plateados).

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
