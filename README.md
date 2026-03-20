# 🐍 Snake Game con IA Local

Snake Game en Python/Pygame donde la IA juega sola usando modelos locales via Ollama.

## Modelos usados
- **LLaMA 3.1 8B** — genera los niveles con obstáculos
- **Qwen 2.5 7B** — controla la serpiente en modo IA

## Requisitos
- Python 3.9+
- Pygame
- Ollama con llama3.1:8b y qwen2.5:7b instalados

## Instalación
```bash
pip3 install pygame requests
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama create snakeai -f SnakeAI
```

## Ejecutar
```bash
python3 snakev3.py
```

## Modos
- **JUGAR TÚ** — juegas tú, LLaMA genera los obstáculos
- **MODO IA** — Qwen juega solo viendo el tablero en ASCII