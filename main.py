import argparse
import os
from src.youtube_scraper import YouTubeScraper
from src.data_cleaner import DataCleaner
from src.sentiment_analyzer import SentimentAnalyzer

def main():
    parser = argparse.ArgumentParser(description='YouTube Comments Scraper & Analyzer')
    parser.add_argument('--channel', help='ID del canal de YouTube')
    parser.add_argument('--video', help='ID de un video específico de YouTube')
    parser.add_argument('--videos', type=int, default=5, help='Número de videos a procesar (solo si usa --channel, default: 5)')
    parser.add_argument('--comments', type=int, default=100, help='Comentarios por video (default: 100)')
    
    args = parser.parse_args()
    
    if not args.channel and not args.video:
        print("Error: Debes proporcionar al menos --channel o --video")
        return
    
    # 1. Scraping
    scraper = YouTubeScraper()
    print(f"\n--- 1. INICIANDO SCRAPING ---")
    
    if args.video:
        print(f"Extrayendo comentarios del video: {args.video}...")
        raw_comments = scraper.get_video_comments(args.video, max_comments=args.comments)
    else:
        raw_comments = scraper.scrape_channel_comments(
            args.channel, 
            max_videos=args.videos, 
            comments_per_video=args.comments
        )
    
    if not raw_comments:
        print("No se encontraron comentarios. Verifica el Channel ID.")
        return

    raw_path = scraper.save_raw_data(raw_comments)
    
    # 2. Limpieza
    cleaner = DataCleaner()
    print(f"\n--- 2. LIMPIANDO DATOS ---")
    df_raw = cleaner.load_data(raw_path)
    df_clean = cleaner.clean_dataframe(df_raw)
    clean_path = cleaner.save_processed_data(df_clean)
    
    # 3. Análisis de Sentimientos
    analyzer = SentimentAnalyzer()
    print(f"\n--- 3. ANALIZANDO SENTIMIENTOS ---")
    df_final = analyzer.analyze_dataframe(df_clean)
    
    # Mostrar resumen
    summary = analyzer.get_summary(df_final)
    print("\nRESUMEN DE SENTIMIENTOS:")
    print(summary)
    
    # Guardar resultado final con sentimientos
    clean_path_with_sentiment = clean_path.replace('.csv', '_sentiment.csv')
    df_final.to_csv(clean_path_with_sentiment, index=False)
    print(f"\nAnálisis completado. Archivo final guardado en: {clean_path_with_sentiment}")

if __name__ == "__main__":
    main()
