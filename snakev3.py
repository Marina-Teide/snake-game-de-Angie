import pygame
import sys
import random
import requests
import threading
import json
import os

def cargar(path):
    img = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (20, 20))
    img.set_colorkey((0, 0, 0))
    return img

# ─── MEMORIA PERSISTENTE ─────────────────────────────────────────────────────
MEMORIA_PATH = "memoria_snake.json"

def cargar_memoria():
    if os.path.exists(MEMORIA_PATH):
        with open(MEMORIA_PATH, "r") as f:
            return json.load(f)
    return {
        "partidas": 0,
        "mejor_puntuacion": 0,
        "muertes_ia": 0,
        "muertes_manual": 0,
        "fallo_direccion": {"UP": 0, "DOWN": 0, "LEFT": 0, "RIGHT": 0},
        "dificultad": "facil"
    }

def guardar_memoria(mem):
    with open(MEMORIA_PATH, "w") as f:
        json.dump(mem, f, indent=2)

def actualizar_dificultad(mem):
    muertes = mem["muertes_ia"] + mem["muertes_manual"]
    puntuacion = mem["mejor_puntuacion"]
    if puntuacion > 10 and muertes < 5:
        mem["dificultad"] = "dificil"
    elif puntuacion > 5 or muertes > 10:
        mem["dificultad"] = "media"
    else:
        mem["dificultad"] = "facil"

# ─── MAPA ASCII ───────────────────────────────────────────────────────────────
def generar_mapa_ascii(serpiente, comida, obstaculos, direccion, ancho=480, alto=400, celda=20):
    DIR_CHAR = {0: ">", 1: "v", 2: "<", 3: "^"}
    cols = ancho // celda
    filas = (alto - 40) // celda

    mapa = [["." for _ in range(cols)] for _ in range(filas)]

    for ox, oy in obstaculos:
        c, f = ox // celda, (oy - 40) // celda
        if 0 <= c < cols and 0 <= f < filas:
            mapa[f][c] = "X"

    fc, ff = comida[0] // celda, (comida[1] - 40) // celda
    if 0 <= fc < cols and 0 <= ff < filas:
        mapa[ff][fc] = "F"

    for i, (sx, sy) in enumerate(serpiente):
        sc, sf = sx // celda, (sy - 40) // celda
        if 0 <= sc < cols and 0 <= sf < filas:
            mapa[sf][sc] = DIR_CHAR[direccion] if i == 0 else "S"

    borde = "#" * (cols + 2)
    filas_str = [borde]
    for fila in mapa:
        filas_str.append("#" + "".join(fila) + "#")
    filas_str.append(borde)

    return "\n".join(filas_str)

# ─── OLLAMA ───────────────────────────────────────────────────────────────────
def llamar_ollama(modelo, prompt, callback):
    def _llamar():
        try:
            r = requests.post("http://localhost:11434/api/generate", json={
                "model": modelo,
                "prompt": prompt,
                "stream": False
            }, timeout=15)
            callback(r.json()["response"])
        except:
            callback(None)
    threading.Thread(target=_llamar, daemon=True).start()

def llamar_ollama_sync(modelo, prompt):
    try:
        r = requests.post("http://localhost:11434/api/generate", json={
            "model": modelo,
            "prompt": prompt,
            "stream": False
        }, timeout=15)
        return r.json()["response"]
    except:
        return None

def parsear_direccion(texto):
    if texto is None:
        return None
    texto = texto.upper()
    for d in ["UP", "DOWN", "LEFT", "RIGHT"]:
        if d in texto:
            return d
    return None

def parsear_obstaculos(texto):
    if texto is None:
        return []
    try:
        start = texto.find("[")
        end = texto.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        data = json.loads(texto[start:end])
        obstaculos = []
        for item in data:
            if isinstance(item, list) and len(item) == 2:
                x = round(item[0] / 20) * 20
                y = round(item[1] / 20) * 20
                x = max(0, min(460, x))
                y = max(40, min(380, y))
                obstaculos.append((x, y))
        return obstaculos[:6]
    except:
        return []

# ─── PYGAME ───────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init()
ancho, alto = 480, 400
ventana = pygame.display.set_mode((ancho, alto))
clock = pygame.time.Clock()

def estado_inicial():
    return {
        "serpiente": [(120, 200), (100, 200), (80, 200)],
        "direccion": 0,
        "siguiente_direccion": 0,
        "comida": (random.randint(0, 23)*20, random.randint(4, 18)*20),
        "nivel": 1,
        "obstaculos": [],
        "modo": None,
        "ia_direccion": None,
        "ia_pensando": False,
        "ia_contador": 0,
        "generando_nivel": True,
        "ia_lista": False,
        "puntuacion": 0,
        "movimientos_sin_comer": 0,
        "usando_fallback": False
    }

estado = estado_inicial()

# Carga de imágenes
cabeza_img = {
    0: cargar("assets/head_right.png"),
    1: cargar("assets/head_down.png"),
    2: pygame.transform.flip(cargar("assets/head_left.png"), True, False),
    3: cargar("assets/head_up.png")
}
cola_img = {
    0: cargar("assets/tail_right.png"),
    1: cargar("assets/tail_down.png"),
    2: cargar("assets/tail_left.png"),
    3: cargar("assets/tail_up.png")
}
cuerpo_img = {
    "horizontal": cargar("assets/body_horizontal.png"),
    "vertical":   cargar("assets/body_vertical.png")
}
giro_img = {
    "tl": pygame.transform.rotate(cargar("assets/body_right_turn.png"), 0),
    "tr": pygame.transform.rotate(cargar("assets/body_left_turn.png"), 0),
    "bl": pygame.transform.rotate(cargar("assets/body_right_turn.png"), 90),
    "br": pygame.transform.rotate(cargar("assets/body_left_turn.png"), 90)
}
fondo_verde = pygame.transform.scale(pygame.image.load("assets/fondo.jpg").convert(), (20, 20))
comida_img  = pygame.transform.scale(pygame.image.load("assets/chuleta.png").convert_alpha(), (30, 30))
tronco_img  = pygame.transform.scale(pygame.image.load("assets/tronco.png").convert_alpha(), (40, 40))
sonido_muerte = pygame.mixer.Sound("assets/gameover.mp3")

DIR_MAP   = {"UP": 3, "DOWN": 1, "LEFT": 2, "RIGHT": 0}
DIR_NAMES = {0: "RIGHT", 1: "DOWN", 2: "LEFT", 3: "UP"}
OPUESTO   = {0: 2, 1: 3, 2: 0, 3: 1}

# ─── FUNCIONES IA ─────────────────────────────────────────────────────────────
def pedir_obstaculos(e, memoria):
    dificultad = memoria["dificultad"]
    num_obs = {"facil": 3, "media": 5, "dificil": 7}.get(dificultad, 4)
    mejor = memoria["mejor_puntuacion"]
    muertes = memoria["muertes_ia"] + memoria["muertes_manual"]

    prompt = f"""Eres el generador de niveles de un Snake Game.
Tablero: 480x400. Zona de juego: y entre 40 y 400.
Serpiente inicial: {e["serpiente"]}.
Historial: mejor puntuacion {mejor}, muertes {muertes}, dificultad {dificultad}.
Genera exactamente {num_obs} obstaculos en posiciones multiplos de 20.
No pongas obstaculos a menos de 80px de la serpiente.
Responde SOLO con un array JSON. Ejemplo: [[100, 120], [300, 200], [200, 340]]"""

    def callback(resp):
        obs = parsear_obstaculos(resp)
        if len(obs) < 2:
            obs = [(random.randint(0,23)*20, random.randint(4,18)*20) for _ in range(num_obs)]
        e["obstaculos"] = obs
        e["generando_nivel"] = False

    e["generando_nivel"] = True
    llamar_ollama("llama3.1:8b", prompt, callback)

def construir_prompt_ia(e):
    mapa = generar_mapa_ascii(
        e["serpiente"], e["comida"], e["obstaculos"], e["direccion"]
    )
    dir_actual = DIR_NAMES[e["direccion"]]
    return f"""Eres el cerebro de una serpiente en Snake.
Tablero (# bordes, S cuerpo, cabeza con direccion {dir_actual}, F comida, X obstaculos):

{mapa}

Direccion actual: {dir_actual}. NO puedes ir en direccion contraria.
Elige la mejor direccion para llegar a F evitando # X y S.
Responde SOLO con una palabra: UP DOWN LEFT RIGHT"""

def direccion_fallback(serpiente, comida, obstaculos, direccion_actual):
    cx, cy = serpiente[0]
    fx, fy = comida

    candidatas = []
    if fx > cx: candidatas.append(0)
    if fx < cx: candidatas.append(2)
    if fy > cy: candidatas.append(1)
    if fy < cy: candidatas.append(3)

    for d in candidatas:
        if d == OPUESTO[direccion_actual]:
            continue
        if d == 0: nueva = (cx+20, cy)
        elif d == 1: nueva = (cx, cy+20)
        elif d == 2: nueva = (cx-20, cy)
        else: nueva = (cx, cy-20)
        if (nueva not in serpiente and
            nueva not in obstaculos and
            0 <= nueva[0] < 480 and
            40 <= nueva[1] < 400):
            return d
    return direccion_actual

def pedir_primera_direccion(e):
    ventana.fill((0, 30, 0))
    msg = pygame.font.SysFont(None, 36).render("Qwen calculando primer movimiento...", True, (0, 220, 0))
    ventana.blit(msg, (240 - msg.get_width()//2, 190))
    pygame.display.flip()

    resp = llamar_ollama_sync("snakeai", construir_prompt_ia(e))
    d = parsear_direccion(resp)
    if d and DIR_MAP[d] != OPUESTO[e["direccion"]]:
        e["siguiente_direccion"] = DIR_MAP[d]
        e["direccion"] = DIR_MAP[d]
    e["ia_lista"] = True

def pedir_direccion_ia(e):
    if e["ia_pensando"]:
        return
    e["ia_pensando"] = True

    def callback(resp):
        d = parsear_direccion(resp)
        if d and DIR_MAP[d] != OPUESTO[e["direccion"]]:
            e["ia_direccion"] = DIR_MAP[d]
        e["ia_pensando"] = False

    llamar_ollama("snakeai", construir_prompt_ia(e), callback)

# ─── PANTALLAS ────────────────────────────────────────────────────────────────
def pantalla_inicio(memoria):
    pygame.mixer.music.load("assets/start.mp3")
    pygame.mixer.music.play(-1)
    while True:
        ventana.fill((0, 50, 0))

        titulo = pygame.font.SysFont(None, 64).render("SNAKE GAME", True, (0, 255, 0))
        ventana.blit(titulo, (240 - titulo.get_width()//2, 60))

        sub = pygame.font.SysFont(None, 24).render("con Inteligencia Artificial Local", True, (150, 220, 150))
        ventana.blit(sub, (240 - sub.get_width()//2, 125))

        mejor = pygame.font.SysFont(None, 22).render(
            f"Record: {memoria['mejor_puntuacion']}   Partidas: {memoria['partidas']}   Dificultad: {memoria['dificultad'].upper()}",
            True, (100, 200, 100)
        )
        ventana.blit(mejor, (240 - mejor.get_width()//2, 165))

        btn_manual = pygame.Rect(60, 220, 160, 50)
        btn_ia     = pygame.Rect(260, 220, 160, 50)
        pygame.draw.rect(ventana, (0, 150, 0), btn_manual, border_radius=8)
        pygame.draw.rect(ventana, (0, 80, 180), btn_ia, border_radius=8)

        t1 = pygame.font.SysFont(None, 30).render("JUGAR TU", True, (255, 255, 255))
        t2 = pygame.font.SysFont(None, 30).render("MODO IA", True, (255, 255, 255))
        ventana.blit(t1, (btn_manual.x + btn_manual.w//2 - t1.get_width()//2, btn_manual.y + 13))
        ventana.blit(t2, (btn_ia.x + btn_ia.w//2 - t2.get_width()//2, btn_ia.y + 13))

        nota = pygame.font.SysFont(None, 20).render(
            "LLaMA genera niveles  |  Qwen ve el tablero y decide",
            True, (100, 180, 100)
        )
        ventana.blit(nota, (240 - nota.get_width()//2, 295))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_manual.collidepoint(pygame.mouse.get_pos()):
                    pygame.mixer.music.stop()
                    return "manual"
                if btn_ia.collidepoint(pygame.mouse.get_pos()):
                    pygame.mixer.music.stop()
                    return "ia"

def dibujar_juego(e, memoria):
    ventana.fill((34, 85, 34))
    for y in range(40, 400, 20):
        for x in range(0, 480, 20):
            ventana.blit(fondo_verde, (x, y))

    for obs in e["obstaculos"]:
        ventana.blit(tronco_img, (obs[0]-10, obs[1]-10))

    ventana.blit(comida_img, e["comida"])

    for i, seg in enumerate(e["serpiente"]):
        if i == 0:
            ventana.blit(cabeza_img[e["direccion"]], seg)
        elif i == len(e["serpiente"]) - 1:
            s, p = e["serpiente"][-1], e["serpiente"][-2]
            if s[0] < p[0]: ventana.blit(cola_img[2], seg)
            elif s[0] > p[0]: ventana.blit(cola_img[0], seg)
            elif s[1] < p[1]: ventana.blit(cola_img[3], seg)
            elif s[1] > p[1]: ventana.blit(cola_img[1], seg)
        else:
            prev = e["serpiente"][i-1]
            nxt  = e["serpiente"][i+1]
            if prev[0] == nxt[0]:
                ventana.blit(cuerpo_img["vertical"], seg)
            elif prev[1] == nxt[1]:
                ventana.blit(cuerpo_img["horizontal"], seg)
            else:
                vi = prev[0] < seg[0] or nxt[0] < seg[0]
                vd = prev[0] > seg[0] or nxt[0] > seg[0]
                va = prev[1] < seg[1] or nxt[1] < seg[1]
                vb = prev[1] > seg[1] or nxt[1] > seg[1]
                if vi and va: ventana.blit(giro_img["tl"], seg)
                elif vd and va: ventana.blit(giro_img["tr"], seg)
                elif vi and vb: ventana.blit(giro_img["bl"], seg)
                elif vd and vb: ventana.blit(giro_img["br"], seg)

    ventana.fill((34, 85, 34), (0, 0, 480, 40))
    puntaje = pygame.font.SysFont(None, 36).render(
        f'Puntaje: {e["puntuacion"]}  Record: {memoria["mejor_puntuacion"]}',
        True, (255,255,255)
    )
    ventana.blit(puntaje, (10, 10))

    if e["modo"] == "ia":
        label = "Fallback" if e.get("usando_fallback") else "Qwen jugando"
        color = (255, 200, 0) if e.get("usando_fallback") else (100, 200, 255)
        tag = pygame.font.SysFont(None, 22).render(label, True, color)
        ventana.blit(tag, (ancho - tag.get_width() - 10, 13))

# ─── BUCLE PRINCIPAL ─────────────────────────────────────────────────────────
memoria = cargar_memoria()
modo = pantalla_inicio(memoria)
estado["modo"] = modo
pedir_obstaculos(estado, memoria)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN and estado["modo"] == "manual":
            d = estado["direccion"]
            if event.key == pygame.K_UP and d != 1: estado["siguiente_direccion"] = 3
            elif event.key == pygame.K_DOWN and d != 3: estado["siguiente_direccion"] = 1
            elif event.key == pygame.K_LEFT and d != 0: estado["siguiente_direccion"] = 2
            elif event.key == pygame.K_RIGHT and d != 2: estado["siguiente_direccion"] = 0

    if estado["generando_nivel"]:
        ventana.fill((0, 30, 0))
        msg = pygame.font.SysFont(None, 36).render("LLaMA generando nivel...", True, (0, 220, 0))
        ventana.blit(msg, (240 - msg.get_width()//2, 180))
        dif = pygame.font.SysFont(None, 26).render(
            f"Dificultad: {memoria['dificultad'].upper()}  |  Record: {memoria['mejor_puntuacion']}",
            True, (100, 180, 100)
        )
        ventana.blit(dif, (240 - dif.get_width()//2, 225))
        pygame.display.flip()
        clock.tick(10)
        continue

    if estado["modo"] == "ia" and not estado["ia_lista"]:
        pedir_primera_direccion(estado)
        continue

    if estado["modo"] == "ia":
        estado["ia_contador"] += 1
        if estado["ia_contador"] >= 3:
            estado["ia_contador"] = 0
            if estado["movimientos_sin_comer"] < 7:
                pedir_direccion_ia(estado)
            else:
                estado["usando_fallback"] = True

        if estado["usando_fallback"]:
            estado["siguiente_direccion"] = direccion_fallback(
                estado["serpiente"], estado["comida"],
                estado["obstaculos"], estado["direccion"]
            )
        elif estado["ia_direccion"] is not None:
            estado["siguiente_direccion"] = estado["ia_direccion"]
            estado["ia_direccion"] = None

    estado["direccion"] = estado["siguiente_direccion"]

    d = estado["direccion"]
    cx, cy = estado["serpiente"][0]
    if d == 3: nueva = (cx, cy - 20)
    elif d == 1: nueva = (cx, cy + 20)
    elif d == 2: nueva = (cx - 20, cy)
    else: nueva = (cx + 20, cy)

    estado["serpiente"].insert(0, nueva)

    if estado["serpiente"][0] == estado["comida"]:
        estado["puntuacion"] += 1
        estado["movimientos_sin_comer"] = 0
        estado["usando_fallback"] = False
        nueva_comida = (random.randint(0,23)*20, random.randint(4,18)*20)
        while nueva_comida in estado["obstaculos"]:
            nueva_comida = (random.randint(0,23)*20, random.randint(4,18)*20)
        estado["comida"] = nueva_comida
    else:
        estado["serpiente"].pop()
        estado["movimientos_sin_comer"] += 1

    cab = estado["serpiente"][0]
    if (cab[0] < 0 or cab[0] >= 480 or cab[1] < 40 or cab[1] >= 400 or
            cab in estado["serpiente"][1:] or cab in estado["obstaculos"]):

        memoria["partidas"] += 1
        if estado["puntuacion"] > memoria["mejor_puntuacion"]:
            memoria["mejor_puntuacion"] = estado["puntuacion"]
        if estado["modo"] == "ia":
            memoria["muertes_ia"] += 1
        else:
            memoria["muertes_manual"] += 1
        actualizar_dificultad(memoria)
        guardar_memoria(memoria)

        sonido_muerte.play()
        fuente = pygame.font.SysFont(None, 72)
        texto = fuente.render("GAME OVER", True, (255, 0, 0))
        sub = pygame.font.SysFont(None, 30).render(
            f"Puntuacion: {estado['puntuacion']}  |  Record: {memoria['mejor_puntuacion']}",
            True, (255, 255, 255)
        )
        ventana.fill((34, 85, 34))
        ventana.blit(texto, (240 - texto.get_width()//2, 170))
        ventana.blit(sub, (240 - sub.get_width()//2, 250))
        pygame.display.flip()
        pygame.time.delay(2500)

        modo = pantalla_inicio(memoria)
        estado = estado_inicial()
        estado["modo"] = modo
        pedir_obstaculos(estado, memoria)
        continue

    dibujar_juego(estado, memoria)
    pygame.display.flip()
    clock.tick(6)
