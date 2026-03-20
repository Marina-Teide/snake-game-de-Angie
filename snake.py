import pygame
import sys
import random

# Inicializar Pygame
pygame.init()

# Configuración de la ventana
ancho, alto = 800, 600
ventana = pygame.display.set_mode((ancho, alto))
pygame.display.set_caption('Snake Game')

# Colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
VERDE = (0, 255, 0)
ROJO = (255, 0, 0)

# Configuración de la serpiente
tamano_cuadrado = 20
velocidad = 10

# Función para mostrar el puntaje
def mostrar_puntaje(puntaje):
    fuente = pygame.font.Font(None, 36)
    texto = fuente.render(f'Puntaje: {puntaje}', True, BLANCO)
    ventana.blit(texto, (10, 10))

# Función para dibujar la serpiente
def dibujar_serpiente(serpiente):
    for segmento in serpiente:
        pygame.draw.rect(ventana, VERDE, (segmento[0], segmento[1], tamano_cuadrado, tamano_cuadrado))

# Función para mover la serpiente
def mover_serpiente(serpiente):
    for i in range(len(serpiente) - 1, 0, -1):
        serpiente[i] = (serpiente[i - 1][0], serpiente[i - 1][1])
    if direccion == 'ARRIBA':
        serpiente[0] = (serpiente[0][0], serpiente[0][1] - velocidad)
    elif direccion == 'ABAJO':
        serpiente[0] = (serpiente[0][0], serpiente[0][1] + velocidad)
    elif direccion == 'IZQUIERDA':
        serpiente[0] = (serpiente[0][0] - velocidad, serpiente[0][1])
    elif direccion == 'DERECHA':
        serpiente[0] = (serpiente[0][0] + velocidad, serpiente[0][1])

# Función para agregar un segmento a la serpiente
def agregar_segmento(serpiente):
    serpiente.append((serpiente[-1][0] - tamano_cuadrado, serpiente[-1][1]))

# Función para comprobar si la serpiente ha chocado
def choco(serpiente):
    if serpiente[0][0] >= ancho or serpiente[0][0] < 0 or serpiente[0][1] >= alto or serpiente[0][1] < 0:
        return True
    for segmento in serpiente[1:]:
        if serpiente[0][0] == segmento[0] and serpiente[0][1] == segmento[1]:
            return True
    return False

# Configuración inicial de la serpiente
serpiente = [(ancho / 2, alto / 2)]
direccion = 'DERECHA'

# Inicializar la posición de la comida
comida = (random.randint(0, (ancho - tamano_cuadrado) // tamano_cuadrado) * tamano_cuadrado,
          random.randint(0, (alto - tamano_cuadrado) // tamano_cuadrado) * tamano_cuadrado)

# Configurar el reloj
reloj = pygame.time.Clock()

# Bucle principal del juego
while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP and direccion != 'ABAJO':
                direccion = 'ARRIBA'
            if evento.key == pygame.K_DOWN and direccion != 'ARRIBA':
                direccion = 'ABAJO'
            if evento.key == pygame.K_LEFT and direccion != 'DERECHA':
                direccion = 'IZQUIERDA'
            if evento.key == pygame.K_RIGHT and direccion != 'IZQUIERDA':
                direccion = 'DERECHA'

    # Mover la serpiente según la dirección
    mover_serpiente(serpiente)

    # Dibujar la serpiente
    ventana.fill(NEGRO)
    dibujar_serpiente(serpiente)

    # Mostrar el puntaje
    mostrar_puntaje(len(serpiente) - 1)

    # Mostrar la comida
    pygame.draw.rect(ventana, ROJO, (comida[0], comida[1], tamano_cuadrado, tamano_cuadrado))

    # Comprobar si la serpiente ha chocado con la comida
    if choco(serpiente):
        print("Game Over")
        pygame.quit()
        sys.exit()
    if serpiente[0][0] == comida[0] and serpiente[0][1] == comida[1]:
        agregar_segmento(serpiente)
        comida = (random.randint(0, (ancho - tamano_cuadrado) // tamano_cuadrado) * tamano_cuadrado,
                  random.randint(0, (alto - tamano_cuadrado) // tamano_cuadrado) * tamano_cuadrado)

    # Actualizar la pantalla
    pygame.display.update()

    # Configurar el reloj para que no vaya demasiado lento
    reloj.tick(10)  # 10 fps
