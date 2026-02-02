"""
Pipeline de Orquestación con Prefect
=====================================
Este archivo define un flujo de trabajo (flow) que orquesta el proceso completo
de scraping, limpieza y análisis de sentimientos de comentarios de YouTube.

Características:
- Reintentos automáticos en caso de fallos de API
- Logs detallados de cada paso
- Monitoreo via dashboard local (localhost:4200)

Uso:
    # Ejecutar el flow directamente:
    python pipeline.py --video 59GrCryltng --comments 50
    
    # Iniciar el servidor de Prefect para ver el dashboard:
    prefect server start
"""

import argparse
from datetime import timedelta
import pandas as pd
from prefect import flow, task
from prefect.logging import get_run_logger
from prefect.blocks.system import Secret
from prefect.artifacts import create_markdown_artifact

from src.youtube_scraper import YouTubeScraper
from src.data_cleaner import DataCleaner
from src.sentiment_analyzer import SentimentAnalyzer


def static_cache_key(context, parameters):
    """Genera una clave de cache basada en los parámetros de entrada."""
    return f"{parameters['video_id']}-{parameters['max_comments']}"


@task(
    retries=3, 
    retry_delay_seconds=30, 
    log_prints=True,
    cache_key_fn=static_cache_key,
    cache_expiration=timedelta(hours=24)
)
def scrape_comments(video_id: str, max_comments: int = 100) -> list:
    """
    Task: Extrae comentarios de un video de YouTube.
    Reintenta hasta 3 veces si la API falla.
    """
    logger = get_run_logger()
    logger.info(f"🔍 Extrayendo comentarios del video: {video_id}")
    
    # Cargar API Key desde Prefect Secret Block
    try:
        api_key_block = Secret.load("youtube-api-key")
        api_key = api_key_block.get()
        logger.info("🔑 API Key cargada desde Prefect Secret Block")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo cargar el bloque 'youtube-api-key': {e}")
        api_key = None

    scraper = YouTubeScraper(api_key=api_key)
    comments = scraper.get_video_comments(video_id, max_comments=max_comments)
    
    logger.info(f"✅ Se extrajeron {len(comments)} comentarios")
    return comments


@task(log_prints=True)
def clean_comments(raw_comments: list) -> pd.DataFrame:
    """
    Task: Limpia y normaliza los comentarios extraídos.
    """
    logger = get_run_logger()
    logger.info(f"🧹 Limpiando {len(raw_comments)} comentarios...")
    
    cleaner = DataCleaner()
    df_raw = pd.DataFrame(raw_comments)
    df_clean = cleaner.clean_dataframe(df_raw)
    
    logger.info(f"✅ Comentarios limpios: {len(df_clean)}")
    return df_clean


@task(log_prints=True)
def analyze_sentiments(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Task: Analiza el sentimiento de cada comentario.
    """
    logger = get_run_logger()
    logger.info("🧠 Analizando sentimientos...")
    
    analyzer = SentimentAnalyzer()
    df_final = analyzer.analyze_dataframe(df_clean)
    
    # Resumen
    summary = df_final['sentiment'].value_counts()
    for sentiment, count in summary.items():
        pct = (count / len(df_final)) * 100
        logger.info(f"   {sentiment}: {count} ({pct:.1f}%)")
    
    return df_final


@task(log_prints=True)
def generate_analysis_artifact(df: pd.DataFrame, video_id: str):
    """
    Task: Genera un reporte Markdown (Artifact) en el dashboard de Prefect.
    """
    logger = get_run_logger()
    logger.info("📊 Generando Artifact de Prefect...")
    
    # Calcular estadísticas
    stats = df['sentiment'].value_counts()
    pos_pct = (stats.get('Positivo', 0) / len(df)) * 100
    neu_pct = (stats.get('Neutro', 0) / len(df)) * 100
    neg_pct = (stats.get('Negativo', 0) / len(df)) * 100
    
    # Crear tabla Markdown
    markdown_report = f"""
# Resumen de Análisis de YouTube 🎬
**Video ID:** `{video_id}`
**Total de Comentarios:** {len(df)}

## 📊 Distribución de Sentimientos

| Sentimiento | Cantidad | Porcentaje |
|-------------|----------|------------|
| 🟢 Positivo  | {stats.get('Positivo', 0)} | {pos_pct:.1f}% |
| ⚪ Neutro    | {stats.get('Neutro', 0)} | {neu_pct:.1f}% |
| 🔴 Negativo  | {stats.get('Negativo', 0)} | {neg_pct:.1f}% |

## 📝 Top 5 Comentarios (Referencia)
"""
    # Agregar algunos comentarios de ejemplo
    sample_comments = df.head(5)
    for _, row in sample_comments.iterrows():
        markdown_report += f"- **[{row['sentiment']}]** {row['clean_text'][:100]}...\n"

    # Publicar el Artifact
    create_markdown_artifact(
        key="youtube-sentiment-report",
        markdown=markdown_report,
        description=f"Reporte de sentimientos para el video {video_id}"
    )
    
    logger.info("✅ Artifact publicado en el Dashboard")


def notify_on_failure(flow, flow_run, state):
    """Función que se ejecuta automáticamente si el flow falla."""
    print(f"\n⚠️¡ATENCIÓN! El flow '{flow.name}' ha fallado.")
    print(f"ID de ejecución: {flow_run.id}")
    print(f"Estado final: {state.message}\n")


@task(log_prints=True)
def save_results(df: pd.DataFrame, filename: str = "comments_analyzed.csv") -> str:
    """
    Task: Guarda los resultados en un archivo CSV.
    """
    logger = get_run_logger()
    path = f"data/processed/{filename}"
    df.to_csv(path, index=False, encoding='utf-8')
    logger.info(f"💾 Resultados guardados en: {path}")
    return path


@flow(name="YouTube Comments Analysis", log_prints=True, on_failure=[notify_on_failure])
def youtube_analysis_flow(video_id: str, max_comments: int = 100):
    """
    Flow principal: Orquesta todo el pipeline de análisis de comentarios.
    
    Args:
        video_id: ID del video de YouTube (ej: '59GrCryltng')
        max_comments: Número máximo de comentarios a extraer
    
    Returns:
        Ruta al archivo CSV con los resultados
    """
    # Paso 1: Scraping
    raw_comments = scrape_comments(video_id, max_comments)
    
    if not raw_comments:
        raise ValueError("No se encontraron comentarios para este video")
    
    # Paso 2: Limpieza
    df_clean = clean_comments(raw_comments)
    
    # Paso 3: Análisis
    df_analyzed = analyze_sentiments(df_clean)
    
    # Paso 4: Generar Artifact (Reporte Visual)
    generate_analysis_artifact(df_analyzed, video_id)
    
    # Paso 5: Guardar
    output_path = save_results(df_analyzed)
    
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YouTube Comments Pipeline (Prefect)')
    parser.add_argument('--video', help='ID del video de YouTube')
    parser.add_argument('--comments', type=int, default=100, help='Número de comentarios')
    parser.add_argument('--serve', action='store_true', help='Iniciar el flujo como un servicio programado')
    
    args = parser.parse_args()
    
    if args.serve:
        # Forma moderna de Prefect 3.0 para programar tareas
        print("\n🚀 Iniciando el flow como servicio (corre cada día a las 6 AM)...")
        youtube_analysis_flow.serve(
            name="YouTube Daily Analysis",
            cron="0 6 * * *", # Formato cron (6:00 AM todos los días)
            parameters={
                "video_id": args.video or "59GrCryltng",
                "max_comments": args.comments
            }
        )
    else:
        if not args.video:
            print("Error: Debes proporcionar --video o usar --serve")
        else:
            # Ejecutar el flow una sola vez manualmente
            result = youtube_analysis_flow(args.video, args.comments)
            print(f"\n✅ Pipeline completado. Archivo: {result}")
