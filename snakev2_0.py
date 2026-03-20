import pygame
import sys
import random

def cargar(path):
  img = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (20, 20))
  img.set_colorkey((0, 0, 0))
  return img

pygame.init()
pygame.mixer.init()
ancho, alto = 480, 400
ventana = pygame.display.set_mode((ancho, alto))
clock = pygame.time.Clock()

# Variables iniciales
serpiente = [(60, 100), (40, 100), (20, 100)]
direccion = 0
siguiente_direccion = 0
comida = (random.randint(0, 23)*20, random.randint(4, 18)*20)
nivel = 1

def generar_obstaculos():
    obstaculos = []
    intentos = 0
    while len(obstaculos) < 4 and intentos < 200:
        ox = random.randint(0, 23) * 20
        oy = random.randint(4, 18) * 20
        pos = (ox, oy)
        if pos not in [(60,100),(40,100),(20,100)] and pos != comida and pos not in obstaculos:
            obstaculos.append(pos)
        intentos += 1
    return obstaculos

obstaculos = generar_obstaculos()

# Carga de imágenes
cabeza_img = {0: cargar("assets/head_right.png"),
            1: cargar("assets/head_down.png"),
            2: pygame.transform.flip(cargar("assets/head_left.png"), True, False),
            3: cargar("assets/head_up.png")}

cola_img = {0: cargar("assets/tail_right.png"),
         1: cargar("assets/tail_down.png"),
         2: cargar("assets/tail_left.png"),
         3: cargar("assets/tail_up.png")}

cuerpo_img = {"horizontal": cargar("assets/body_horizontal.png"),
            "vertical": cargar("assets/body_vertical.png")}

giro_img = {
  "tl": pygame.transform.rotate(cargar("assets/body_right_turn.png"), 0),
  "tr": pygame.transform.rotate(cargar("assets/body_left_turn.png"), 0),
  "bl": pygame.transform.rotate(cargar("assets/body_right_turn.png"), 90),
  "br": pygame.transform.rotate(cargar("assets/body_left_turn.png"), 90)
}

fondo_verde = pygame.transform.scale(pygame.image.load("assets/fondo.jpg").convert(), (20, 20))
comida_img = pygame.transform.scale(pygame.image.load("assets/chuleta.png").convert_alpha(), (30, 30))
tronco_img = pygame.transform.scale(pygame.image.load("assets/tronco.png").convert_alpha(), (40, 40))

# Carga de sonidos
sonido_muerte = pygame.mixer.Sound("assets/gameover.mp3")

def pantalla_inicio():
    pygame.mixer.music.load("assets/start.mp3")
    pygame.mixer.music.play(-1)
    while True:
        ventana.fill((0, 50, 0))
        titulo = pygame.font.SysFont(None, 64).render("SNAKE GAME", True, (0, 255, 0))
        ventana.blit(titulo, (240 - titulo.get_width()//2, 120))
        boton = pygame.Rect(165, 220, 150, 45)
        pygame.draw.rect(ventana, (0, 180, 0), boton)
        texto = pygame.font.SysFont(None, 36).render("JUGAR", True, (0, 0, 0))
        ventana.blit(texto, (boton.x + 75 - texto.get_width()//2, boton.y + 10))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boton.collidepoint(pygame.mouse.get_pos()):
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return

pantalla_inicio()
pygame.mixer.music.stop()

while True:
  for event in pygame.event.get():
      if event.type == pygame.QUIT:
          pygame.quit()
          sys.exit()
      elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_UP and direccion != 1:
              siguiente_direccion = 3
          elif event.key == pygame.K_DOWN and direccion != 3:
              siguiente_direccion = 1
          elif event.key == pygame.K_LEFT and direccion != 0:
              siguiente_direccion = 2
          elif event.key == pygame.K_RIGHT and direccion != 2:
              siguiente_direccion = 0

  direccion = siguiente_direccion

  if direccion == 3:
      nueva_cabeza = (serpiente[0][0], serpiente[0][1] - 20)
  elif direccion == 1:
      nueva_cabeza = (serpiente[0][0], serpiente[0][1] + 20)
  elif direccion == 2:
      nueva_cabeza = (serpiente[0][0] - 20, serpiente[0][1])
  elif direccion == 0:
      nueva_cabeza = (serpiente[0][0] + 20, serpiente[0][1])

  serpiente.insert(0, nueva_cabeza)

  if serpiente[0] == comida:
      comida = (random.randint(0, 23)*20, random.randint(4, 18)*20)
      while comida in obstaculos:
          comida = (random.randint(0, 23)*20, random.randint(4, 18)*20)
  else:
      serpiente.pop()

  if (serpiente[0][0] < 0 or serpiente[0][0] >= 480 or
      serpiente[0][1] < 40 or serpiente[0][1] >= 400 or
      serpiente[0] in serpiente[1:] or
      serpiente[0] in obstaculos):
      sonido_muerte.play()
      fuente = pygame.font.SysFont(None, 72)
      texto = fuente.render("GAME OVER", True, (255, 0, 0))
      ventana.fill((34, 85, 34))
      ventana.blit(texto, (240 - texto.get_width()//2, 200 - texto.get_height()//2))
      pygame.display.flip()
      pygame.time.delay(2000)
      serpiente = [(60, 100), (40, 100), (20, 100)]
      direccion = 0
      siguiente_direccion = 0
      comida = (random.randint(0, 23)*20, random.randint(4, 18)*20)
      nivel = 1
      obstaculos = generar_obstaculos()

  ventana.fill((34, 85, 34))
  for y in range(40, 400, 20):
      for x in range(0, 480, 20):
          ventana.blit(fondo_verde, (x, y))

  for obs in obstaculos:
      ventana.blit(tronco_img, (obs[0] - 10, obs[1] - 10))

  ventana.blit(comida_img, comida)

  for i, segmento in enumerate(serpiente):
      if i == 0:
          ventana.blit(cabeza_img[direccion], segmento)
      elif i == len(serpiente) - 1:
          if serpiente[-1][0] < serpiente[-2][0]: ventana.blit(cola_img[2], segmento)
          elif serpiente[-1][0] > serpiente[-2][0]: ventana.blit(cola_img[0], segmento)
          elif serpiente[-1][1] < serpiente[-2][1]: ventana.blit(cola_img[3], segmento)
          elif serpiente[-1][1] > serpiente[-2][1]: ventana.blit(cola_img[1], segmento)
      else:
          prev = serpiente[i-1]
          next = serpiente[i+1]
          if prev[0] == next[0]:
              ventana.blit(cuerpo_img["vertical"], segmento)
          elif prev[1] == next[1]:
              ventana.blit(cuerpo_img["horizontal"], segmento)
          else:
              if prev[0] < next[0] and prev[1] < next[1]: ventana.blit(giro_img["bl"], segmento)
              elif prev[0] > next[0] and prev[1] < next[1]: ventana.blit(giro_img["br"], segmento)
              elif prev[0] < next[0] and prev[1] > next[1]: ventana.blit(giro_img["tr"], segmento)
              elif prev[0] > next[0] and prev[1] > next[1]: ventana.blit(giro_img["tr"], segmento)

  ventana.fill((34, 85, 34), (0, 0, 480, 40))
  marcador_texto = pygame.font.SysFont(None, 36).render(f'Puntaje: {len(serpiente) - 3}', True, (255, 255, 255))
  ventana.blit(marcador_texto, (10, 10))
  nivel_texto = pygame.font.SysFont(None, 36).render(f'Nivel: {nivel}', True, (255, 255, 255))
  ventana.blit(nivel_texto, (ancho - 90, 10))

  pygame.display.flip()
  clock.tick(6)
  