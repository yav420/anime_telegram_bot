import requests
from config import API_URL

class AnimeAPIClient:
    @staticmethod
    def search_anime(query):
        """Поиск аниме по названию через API"""
        response = requests.get(f"{API_URL}/anime?q={query}&limit=5")
        return response.json().get('data', [])
    
    @staticmethod
    def get_anime_details(anime_id):
        """Получение детальной информации об аниме"""
        response = requests.get(f"{API_URL}/anime/{anime_id}/full")
        return response.json().get('data', {})
    
    @staticmethod
    def get_top_anime():
        """Получение топовых аниме"""
        response = requests.get(f"{API_URL}/top/anime")
        return response.json().get('data', [])
    
    @staticmethod
    def get_random_anime():
        """Получение случайного аниме"""
        response = requests.get(f"{API_URL}/random/anime")
        return response.json().get('data', {})