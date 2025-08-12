import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def get_instagram_stats(business_name):
    """
        The `get_instagram_stats` function retrieves Instagram statistics, such as the number of followers, 
        total posts, and last post date, for a given business name.
        
        :param business_name: 
            Takes a business name as a parameter and retrieves that user's Instagram statistics.
        :return: 
            Dictionary with information about a specific company's Instagram statistics.
    """
    
    base_url = os.getenv("INSTAGRAM_BASE_URL", "https://www.instagram.com")
    url = f"{base_url}/{business_name}/?__a=1"
    
    response = requests.get(url)
    

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = soup.find('meta', property='og:description')

        if metadata:
            metadata_content = metadata['content']
            stats = {}
            
            parts = metadata_content.split(' ')
            if len(parts) > 4:
                stats['followers'] = parts[0]
                stats['posts'] = parts[4]

            return {
                "source": "instagram",
                "business_name": business_name,
                "stats": stats
            }
    return {
        "source": "instagram", 
        "business_name": business_name, 
        "stats": None
    }
