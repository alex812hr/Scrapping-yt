import os
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class YouTubeScraper:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("No API Key found. Set YOUTUBE_API_KEY in .env file.")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_channel_videos(self, channel_id):
        """Obtiene todos los video IDs de un canal."""
        videos = []
        # Primero obtener el playlist ID de 'uploads' del canal
        res = self.youtube.channels().list(id=channel_id, part='contentDetails').execute()
        if not res.get('items'):
            return []
        
        uploads_playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        next_page_token = None
        while True:
            res = self.youtube.playlistItems().list(
                playlistId=uploads_playlist_id,
                part='snippet',
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for item in res['items']:
                videos.append({
                    'video_id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt']
                })
            
            next_page_token = res.get('nextPageToken')
            if not next_page_token:
                break
        
        return videos

    def get_video_comments(self, video_id, max_comments=100):
        """Obtiene comentarios de un video específico."""
        comments = []
        try:
            next_page_token = None
            while len(comments) < max_comments:
                res = self.youtube.commentThreads().list(
                    videoId=video_id,
                    part='snippet',
                    maxResults=100,
                    pageToken=next_page_token,
                    textFormat='plainText'
                ).execute()
                
                for item in res['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'like_count': comment['likeCount'],
                        'published_at': comment['publishedAt'],
                        'video_id': video_id
                    })
                
                next_page_token = res.get('nextPageToken')
                if not next_page_token or len(comments) >= max_comments:
                    break
                    
        except Exception as e:
            print(f"Error fetching comments for video {video_id}: {e}")
            
        return comments[:max_comments]

    def scrape_channel_comments(self, channel_id, max_videos=5, comments_per_video=50):
        """Orquestador para scrapear comentarios de múltiples videos de un canal."""
        print(f"Buscando videos para el canal: {channel_id}...")
        videos = self.get_channel_videos(channel_id)
        print(f"Se encontraron {len(videos)} videos. Procesando los primeros {max_videos}...")
        
        all_comments = []
        for v in videos[:max_videos]:
            print(f"  Extrayendo comentarios de: {v['title']}...")
            video_comments = self.get_video_comments(v['video_id'], max_comments=comments_per_video)
            all_comments.extend(video_comments)
            
        return all_comments

    def save_raw_data(self, data, filename='comments_raw.json'):
        """Guarda los datos crudos en la carpeta data/raw/."""
        path = os.path.join('data', 'raw', filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Datos guardados en {path}")
        return path
