# YouTube Comments Scraper & Analyzer

Proyecto para extraer, limpiar y analizar sentimientos de comentarios de un canal de YouTube.

## 🚀 Instalación

1. Clona el repositorio o descarga los archivos.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuración

1. Crea un archivo `.env` en la raíz (puedes copiar `.env.example`).
2. Agrega tu API Key de YouTube:
   ```env
   YOUTUBE_API_KEY=tu_api_key_aqui
   ```

## 🛠️ Uso

Ejecuta el script principal pasando el ID del canal que quieres scrapear:

```bash
python main.py --channel ID_DEL_CANAL
```

### Argumentos opcionales:

- `--video ID`: Analiza un video específico en lugar de un canal.
- `--videos N`: Número de videos a procesar (default: 5)
- `--comments N`: Comentarios por video (default: 100)

---

## 🌐 Interfaz Web

También puedes usar la interfaz gráfica con Streamlit:

```bash
streamlit run app.py
```

La interfaz te permite:

- Analizar videos o canales de forma visual.
- Ver gráficos interactivos de sentimientos.
- Descargar los resultados en CSV.

---

## 📁 Estructura de Salida

- `data/raw/`: Backup de los comentarios crudos extraídos de la API.
- `data/processed/`: CSV con los datos limpios y el análisis de sentimientos.

## 🧹 Limpieza Realizada

- Eliminación de duplicados.
- Normalización a minúsculas.
- Eliminación de URLs y menciones.
- Limpieza de emojis y caracteres especiales.
- Eliminación de comentarios vacíos tras la limpieza.

## 📊 Análisis de Sentimientos

Utiliza la librería `TextBlob` para categorizar cada comentario en:

- **Positivo**
- **Neutro**
- **Negativo**
