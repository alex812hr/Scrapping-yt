import os
import re
import pandas as pd
import emoji

class DataCleaner:
    def __init__(self):
        pass

    def load_data(self, file_path):
        """Carga datos desde JSON o CSV."""
        if file_path.endswith('.json'):
            return pd.read_json(file_path)
        return pd.read_csv(file_path)

    def normalize_text(self, text):
        """Limpia el texto: minúsculas, espacios, carácteres especiales."""
        if not isinstance(text, str):
            return ""
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Eliminar URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Eliminar menciones (@user)
        text = re.sub(r'@\w+', '', text)
        
        # Eliminar emojis (opcional, podrías querer dejarlos para sentimiento)
        # Por ahora los quitamos para limpieza de texto pura
        text = emoji.replace_emoji(text, replace='')
        
        # Eliminar caracteres especiales y números (opcional, según necesidad)
        # text = re.sub(r'[^a-záéíóúñ\s]', '', text) 
        
        # Eliminar saltos de línea y espacios extra
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def clean_dataframe(self, df):
        """Aplica todo el pipeline de limpieza a un DataFrame."""
        # 1. Eliminar duplicados exactos
        df = df.drop_duplicates()
        
        # 2. Manejo de nulos en texto
        df = df.dropna(subset=['text'])
        
        # 3. Aplicar normalización
        df['clean_text'] = df['text'].apply(self.normalize_text)
        
        # 4. Eliminar filas donde el texto limpio quedó vacío (ej: solo emojis/URLs)
        df = df[df['clean_text'] != ""]
        
        # 5. Reset index
        df = df.reset_index(drop=True)
        
        return df

    def save_processed_data(self, df, filename='comments_clean.csv'):
        """Guarda los datos limpios en la carpeta data/processed/."""
        path = os.path.join('data', 'processed', filename)
        df.to_csv(path, index=False, encoding='utf-8')
        print(f"Datos limpios guardados en {path}")
        return path
