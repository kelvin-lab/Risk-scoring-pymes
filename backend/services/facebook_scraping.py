import requests
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv

load_dotenv()

def get_facebook_stats(business_name):
    """
        The `get_facebook_stats` function retrieves Facebook statistics, such as the number of followers, 
        total posts, and likes, for a given business name.
        
        :param business_name: 
            Takes a business name as a parameter and retrieves that user's Facebook statistics.
        :return: 
            Dictionary with information about a specific company's Facebook statistics.
    """
    base_url = os.getenv("FACEBOOK_BASE_URL", "https://www.facebook.com")
    url = f"{base_url}/{business_name}/?__a=1"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = soup.find('meta', property='og:description')
        if metadata:
            metadata_content = metadata['content']
            
            stats = {}

            liked_match = re.search(r'([\d,.]+) Me gusta', metadata_content)
            if liked_match:
                stats['likes'] = int(liked_match.group(1).replace('.', '').replace(',', ''))

            posts_match = re.search(r'(\d+) publicaciones', metadata_content)
            if posts_match:
                stats['posts'] = int(posts_match.group(1))

            body_content = str(soup.find('body'))
            followers_match = re.search(r'([\d,.]+) seguidores', body_content, re.IGNORECASE)
            if followers_match:
                stats['followers'] = int(followers_match.group(1).replace('.', '').replace(',', ''))

            return {
                "source": "facebook",
                "business_name": business_name,
                "stats": stats
            }
    return {
        "source": "facebook",
        "business_name": business_name,
        "stats": None
    }
