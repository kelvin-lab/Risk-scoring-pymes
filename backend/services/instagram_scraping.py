import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def get_instagram_stats(username):
    """
        The function `get_instagram_stats` search Instagram statistics such as followers
        count, total posts, and last post date for a given username.
        
        :param username: The function `get_instagram_stats(username)` takes a username as a parameter and
        retrieves Instagram statistics for that user. It makes a request to the Instagram profile page of
        the provided username, extracts information such as followers count, total posts, and the date of
        the last post
    """
    
    base_url = os.getenv("INSTAGRAM_BASE_URL", "https://www.instagram.com")
    url = f"{base_url}/{username}/?__a=1"
    
    response = requests.get(url)
    

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = soup.find('meta', property='og:description')

        if metadata:
            metadata_content = metadata['content']
            followers_count = metadata_content.split(' ')[0]
            post = metadata_content.split(' ')[4]
            print(f"Followers count for {username}: {followers_count}")
            print(f"Total posts for {username}: {post}")

if __name__ == "__main__":
    get_instagram_stats('alfanetecuador')   
