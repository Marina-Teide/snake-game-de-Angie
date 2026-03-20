import requests
import sys
import shutil
from datetime import datetime

OLLAMA = "http://localhost:11434/api/generate"

def llamar_modelo(modelo, prompt):
    print(f"\n⏳ Consultando {modelo}...")
    try:
        respuesta = requests.post(OLLAMA, json={
            "model": modelo,
            "prompt": prompt,
            "stream": False
        }, timeout=120)
        return respuesta.json()["response"]
    except requests.exceptions.Timeout:
        print("❌ El modelo tardó demasiado. Intenta de nuevo.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error conectando con Ollama: {e}")
        sys.exit(1)

def hacer_backup(archivo):
    timestamp = datetime.now().strftime("%H%M%S")
    backup = f"{archivo}.backup_{timestamp}"
    shutil.copy(archivo, backup)
    return backup

def limpiar_codigo(texto):
    """Elimina bloques markdown que deepseek a veces agrega"""
    lineas = texto.split("\n")
    resultado = []
    dentro_bloque = False
    for linea in lineas:
        if linea.strip().startswith("```python"):
            dentro_bloque = True
            continue
        elif linea.strip() == "```" and dentro_bloque:
            dentro_bloque = False
            continue
        elif linea.strip().startswith("```") and not dentro_bloque:
            continue
        resultado.append(linea)
    codigo = "\n".join(resultado).strip()
    if "import pygame" in codigo:
        return codigo
    return texto

def main():
    print("🐍 Agente Snake — llama3.1:8b + deepseek-coder-v2:16b")
    print("=" * 55)

    archivo = "snakev2.py"
    try:
        with open(archivo, "r") as f:
            codigo = f.read()
    except FileNotFoundError:
        print(f"❌ No se encontró {archivo} en esta carpeta")
        sys.exit(1)

    print(f"✅ Código cargado ({len(codigo.splitlines())} líneas)")

    print("\n¿Qué quieres cambiar o agregar al juego?")
    idea = input("👉 ")

    # Paso 1: llama genera el prompt técnico
    prompt_llama = f"""Eres un experto en Python y Pygame.
Tu tarea es escribir un prompt técnico y preciso para que deepseek-coder haga exactamente el cambio que el usuario quiere en este Snake Game.

REGLAS ESTRICTAS:
- Sé muy específico: indica el bloque exacto a cambiar con el texto actual y el texto nuevo
- NO inventes código nuevo innecesario
- NO cambies la lógica que ya funciona
- Termina SIEMPRE con: "NO cambies nada más. Devuelve SOLO el código Python completo y funcional, sin explicaciones ni bloques markdown."
- Escribe el prompt en español

CÓDIGO ACTUAL:
{codigo}

CAMBIO QUE QUIERE EL USUARIO:
{idea}

Escribe SOLO el prompt para deepseek-coder:"""

    prompt_tecnico = llamar_modelo("llama3.1:8b", prompt_llama)

    print("\n📝 Prompt generado por llama:")
    print("-" * 55)
    print(prompt_tecnico)
    print("-" * 55)

    confirmar = input("\n¿Enviar este prompt a deepseek-coder? (s/n): ")
    if confirmar.lower() != "s":
        print("Cancelado. El código no fue modificado.")
        sys.exit(0)

    # Backup automático antes de modificar
    backup = hacer_backup(archivo)
    print(f"\n💾 Backup guardado en: {backup}")

    # Paso 2: deepseek ejecuta el cambio
    prompt_deepseek = f"{prompt_tecnico}\n\nCÓDIGO ACTUAL:\n{codigo}"
    codigo_nuevo = llamar_modelo("deepseek-coder-v2:16b", prompt_deepseek)
    codigo_limpio = limpiar_codigo(codigo_nuevo)

    # Verificar que el resultado parece código válido
    if "import pygame" not in codigo_limpio:
        print("\n⚠️  El resultado no parece código válido.")
        print("El archivo NO fue modificado. Backup disponible en:", backup)
        sys.exit(1)

    with open(archivo, "w") as f:
        f.write(codigo_limpio)

    print(f"\n✅ Código actualizado en {archivo}")
    print(f"🔙 Si algo salió mal: cp {backup} {archivo}")
    print(f"▶️  Para probar: python3 {archivo}")

if __name__ == "__main__":
    main()
