import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import os

from src.youtube_scraper import YouTubeScraper
from src.data_cleaner import DataCleaner
from src.sentiment_analyzer import SentimentAnalyzer

# Configuración de la página
st.set_page_config(
    page_title="YouTube Comments Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para un diseño más atractivo
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ff0000, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stButton > button {
        background: linear-gradient(90deg, #ff0000, #cc0000);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 0.5rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(255,0,0,0.4);
    }
    .sidebar .stTextInput > div > div > input {
        background-color: #262730;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def extract_video_id(url_or_id):
    """Extrae el ID del video de una URL de YouTube o retorna el ID si ya es válido."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 YouTube Comments Analyzer</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #888; margin-bottom: 2rem;">Analiza el sentimiento de los comentarios de cualquier video de YouTube</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg", width=150)
        st.markdown("---")
        st.markdown("### ⚙️ Configuración")
        
        input_type = st.radio("Tipo de análisis:", ["Video específico", "Canal completo"])
        
        if input_type == "Video específico":
            video_input = st.text_input(
                "🔗 URL o ID del video:",
                placeholder="https://youtube.com/watch?v=... o ID"
            )
        else:
            channel_input = st.text_input(
                "📺 ID del canal:",
                placeholder="UCxxxxxx..."
            )
            num_videos = st.slider("Número de videos:", 1, 10, 3)
        
        max_comments = st.slider("Comentarios a extraer:", 10, 500, 100, step=10)
        
        st.markdown("---")
        analyze_button = st.button("🚀 Analizar Comentarios", use_container_width=True)
    
    # Contenido principal
    if analyze_button:
        try:
            scraper = YouTubeScraper()
            cleaner = DataCleaner()
            analyzer = SentimentAnalyzer()
            
            with st.spinner("🔍 Extrayendo comentarios..."):
                if input_type == "Video específico":
                    video_id = extract_video_id(video_input)
                    if not video_id:
                        st.error("❌ URL o ID de video inválido")
                        return
                    raw_comments = scraper.get_video_comments(video_id, max_comments=max_comments)
                else:
                    raw_comments = scraper.scrape_channel_comments(
                        channel_input,
                        max_videos=num_videos,
                        comments_per_video=max_comments
                    )
            
            if not raw_comments:
                st.warning("⚠️ No se encontraron comentarios.")
                return
            
            with st.spinner("🧹 Limpiando datos..."):
                df_raw = pd.DataFrame(raw_comments)
                df_clean = cleaner.clean_dataframe(df_raw)
            
            with st.spinner("🧠 Analizando sentimientos..."):
                df_final = analyzer.analyze_dataframe(df_clean)
            
            # Métricas principales
            st.markdown("### 📊 Resumen del Análisis")
            col1, col2, col3, col4 = st.columns(4)
            
            total = len(df_final)
            positivos = len(df_final[df_final['sentiment'] == 'Positivo'])
            negativos = len(df_final[df_final['sentiment'] == 'Negativo'])
            neutros = len(df_final[df_final['sentiment'] == 'Neutro'])
            
            with col1:
                st.metric("📝 Total Comentarios", total)
            with col2:
                st.metric("😊 Positivos", f"{positivos} ({positivos/total*100:.1f}%)")
            with col3:
                st.metric("😐 Neutros", f"{neutros} ({neutros/total*100:.1f}%)")
            with col4:
                st.metric("😠 Negativos", f"{negativos} ({negativos/total*100:.1f}%)")
            
            st.markdown("---")
            
            # Gráficos
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("#### 🥧 Distribución de Sentimientos")
                sentiment_counts = df_final['sentiment'].value_counts()
                colors = {'Positivo': '#00cc66', 'Neutro': '#ffcc00', 'Negativo': '#ff4444'}
                fig_pie = px.pie(
                    values=sentiment_counts.values,
                    names=sentiment_counts.index,
                    color=sentiment_counts.index,
                    color_discrete_map=colors,
                    hole=0.4
                )
                fig_pie.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_chart2:
                st.markdown("#### 📈 Polaridad de Comentarios")
                fig_hist = px.histogram(
                    df_final, 
                    x='polarity',
                    nbins=30,
                    color_discrete_sequence=['#ff6b6b']
                )
                fig_hist.update_layout(
                    xaxis_title="Polaridad (-1 a 1)",
                    yaxis_title="Cantidad",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            st.markdown("---")
            
            # Tabla de datos
            st.markdown("### 📋 Comentarios Analizados")
            
            # Filtro de sentimiento
            filter_sentiment = st.multiselect(
                "Filtrar por sentimiento:",
                options=['Positivo', 'Neutro', 'Negativo'],
                default=['Positivo', 'Neutro', 'Negativo']
            )
            
            df_display = df_final[df_final['sentiment'].isin(filter_sentiment)][
                ['author', 'text', 'clean_text', 'sentiment', 'polarity', 'like_count']
            ].rename(columns={
                'author': 'Autor',
                'text': 'Comentario Original',
                'clean_text': 'Texto Limpio',
                'sentiment': 'Sentimiento',
                'polarity': 'Polaridad',
                'like_count': 'Likes'
            })
            
            st.dataframe(df_display, use_container_width=True, height=400)
            
            # Botón de descarga
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV Completo",
                data=csv,
                file_name="youtube_comments_analysis.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Verifica que tu API Key esté configurada correctamente en el archivo .env")
    
    else:
        # Estado inicial
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 1rem; margin: 2rem 0;">
            <h3 style="color: #ff6b6b;">👈 Ingresa un video o canal para comenzar</h3>
            <p style="color: #888;">Configura las opciones en el panel lateral y presiona "Analizar Comentarios"</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Features
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem;">
                <h1>🔍</h1>
                <h4>Extracción</h4>
                <p style="color: #888;">Obtén comentarios de cualquier video público</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem;">
                <h1>🧹</h1>
                <h4>Limpieza</h4>
                <p style="color: #888;">Procesamiento automático de texto</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem;">
                <h1>📊</h1>
                <h4>Análisis</h4>
                <p style="color: #888;">Clasificación de sentimientos con IA</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
