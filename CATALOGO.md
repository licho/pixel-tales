# Catálogo de pixel-tales

Todo lo disponible para armar episodios. **Mantener este archivo corto y al día**: es lo único que hace falta leer para escribir un episodio nuevo.

## Estilos (`styles/`)
| Nombre | Look |
|---|---|
| `survival` | Noche postapocalíptica: teal oscuro, carbón, ámbar de fuego, amarillo de traje |

## Escenas / fondos (`scenes/`)
| Nombre | Descripción | Parámetros | Dónde poner actores (x, y = pies) |
|---|---|---|---|
| `calle` | Calle urbana abandonada en perspectiva, rascacielos en niebla | `semilla`, `farol`, `barril`, `carro`, `cables` (bool, default true) | banqueta izq. x 60-130 y 195-212; calle media x 200-320 y 140-170 |

## Sprites (`sprites/`)
| Ruta | Descripción | Tamaño |
|---|---|---|
| `survival/sobreviviente_traje` | Traje amarillo, máscara antigás, rifle, mirando a la derecha | 102 px de alto |

## Actores procedurales
| Tipo | Opciones |
|---|---|
| `zombi` | `pos: [x, y]`, `altura` (px, 10-30 según distancia), `fase`, `ropa: [r, g, b]`, `avanza: [dx, dy]` (px/seg) |

## Efectos (`efectos: [...]` en cada panel)
| Nombre | Qué hace |
|---|---|
| `lluvia` | Lluvia pixelada con salpicaduras |
| `relampago` | Destello del cielo a mitad del panel (y cada 7 s) |
| `parpadeo` | El farol falla de vez en cuando |
| *(automático)* | El fuego siempre se anima y echa humo; luces con contraluz iluminan el borde de los personajes |

## Formato de un panel
```yaml
- escena: calle
  params: {farol: false, semilla: 3}
  efectos: [lluvia, relampago]
  camara: {pan: 18}            # desplazamiento lateral (0 = fija, máx 25)
  actores:
    - sprite: survival/sobreviviente_traje
      pos: [96, 208]
      escala: 1.0                # opcional
      espejo: false              # opcional, voltea horizontal
    - zombi: {pos: [272, 162], altura: 26}
  texto: "Narración de este panel"   # reparte la duración cuando hay voz
  duracion: 7                    # opcional; sin esto, se calcula con la voz
```
