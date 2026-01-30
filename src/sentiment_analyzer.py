from textblob import TextBlob
import pandas as pd

class SentimentAnalyzer:
    def __init__(self):
        pass

    def get_sentiment(self, text):
        """Analiza el sentimiento y retorna una categoría."""
        analysis = TextBlob(text)
        # La polaridad va de -1 (muy negativo) a 1 (muy positivo)
        if analysis.sentiment.polarity > 0.05:
            return 'Positivo'
        elif analysis.sentiment.polarity < -0.05:
            return 'Negativo'
        else:
            return 'Neutro'

    def analyze_dataframe(self, df, text_column='clean_text'):
        """Aplica el análisis a todo el DataFrame."""
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in DataFrame")
        
        df['sentiment'] = df[text_column].apply(self.get_sentiment)
        df['polarity'] = df[text_column].apply(lambda x: TextBlob(x).sentiment.polarity)
        return df

    def get_summary(self, df):
        """Retorna un resumen de los sentimientos."""
        summary = df['sentiment'].value_counts()
        percentage = (df['sentiment'].value_counts(normalize=True) * 100).round(2)
        
        report = pd.DataFrame({
            'Total': summary,
            'Percentage (%)': percentage
        })
        return report
