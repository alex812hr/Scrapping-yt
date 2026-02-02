"""
Script para crear el bloque de secreto en Prefect.
Ejecuta esto una sola vez para registrar tu API Key en la base de datos de Prefect.
"""
import os
from dotenv import load_dotenv
from prefect.blocks.system import Secret

load_dotenv()

def create_youtube_secret_block():
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        print("❌ Error: No se encontró YOUTUBE_API_KEY en el archivo .env")
        return

    # Crear el bloque de tipo Secreto
    secret_block = Secret(value=api_key)
    
    # Guardarlo con un nombre único
    secret_block.save(name="youtube-api-key", overwrite=True)
    
    print("✅ Bloque de secreto 'youtube-api-key' creado exitosamente en Prefect.")
    print("🚀 Ahora puedes acceder a él desde el Dashboard (sección Blocks).")

if __name__ == "__main__":
    create_youtube_secret_block()
